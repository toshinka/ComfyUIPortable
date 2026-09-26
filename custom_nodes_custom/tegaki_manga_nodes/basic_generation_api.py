"""PLAY1a read/compile-only Manga HTTP endpoints on the existing ComfyUI server."""

from __future__ import annotations

import json
import logging
import os

from aiohttp import web

from .basic_generation import (
    CORE_NODES, NODE_IDENTITY, WILDCARD_ENV, GenerationContractError,
    _digest, _dynamic_prompt_api, _safe_wildcard_name, _wildcard_root, build_catalog, compile_basic,
    expand_wildcard_text,
)
from .scene_generation import (
    CONTROLNET_DEFAULT_MODEL,
    CONTROLNET_DEFAULT_STRENGTH,
    CONTROLNET_END_PERCENT,
    CONTROLNET_START_PERCENT,
    REFERENCE_CLIP_VISION,
    REFERENCE_COMBINE_EMBEDS,
    REFERENCE_EMBEDS_SCALING,
    REFERENCE_END_AT,
    REFERENCE_IPADAPTER,
    REFERENCE_START_AT,
    REFERENCE_WEIGHT,
    REFERENCE_WEIGHT_TYPE,
    SCENE_CONTROLNET_REQUIRED_NODES,
    SCENE_REFERENCE_REQUIRED_NODES,
    SCENE_REQUIRED_NODES,
    compile_scene,
)
try:
    from .isolated_scene_plan import (
        create_isolated_scene_plan,
        IsolatedScenePlanError,
    )
    from .isolated_scene_compile import (
        compile_isolated_scene_plan,
        IsolatedSceneCompileError,
    )
except (ImportError, ValueError):
    from isolated_scene_plan import (
        create_isolated_scene_plan,
        IsolatedScenePlanError,
    )
    from isolated_scene_compile import (
        compile_isolated_scene_plan,
        IsolatedSceneCompileError,
    )

try:
    from .page_pixel_compositor import compose_page_pixels, PagePixelCompositorError
except (ImportError, ValueError):
    from page_pixel_compositor import compose_page_pixels, PagePixelCompositorError

try:
    from .engine_resources import ResourceContractError, browse_lora_payload, lora_preview_path, preview_mime, build_trusted_lora_index, lora_index_payload, resolve_resource_root, validate_lora_request
except (ImportError, ValueError):
    from engine_resources import ResourceContractError, browse_lora_payload, lora_preview_path, preview_mime, build_trusted_lora_index, lora_index_payload, resolve_resource_root, validate_lora_request

MAX_REQUEST_BYTES = 256 * 1024


def package_source_digest(directory: str | None = None) -> str:
    """sha256 over this package's top-level *.py files (name + bytes), sorted by name.

    Computed once at import so /tegaki/manga/runtime/source-identity reports the
    source this process actually loaded.  run_manga.mjs computes the same digest
    from disk and refuses to reuse a backend whose loaded source is stale.
    """
    import hashlib

    folder = os.path.realpath(directory or os.path.dirname(os.path.abspath(__file__)))
    digest = hashlib.sha256()
    for name in sorted(n for n in os.listdir(folder) if n.endswith(".py")):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as handle:
            data = handle.read()
        digest.update(name.encode("utf-8") + b"\0" + data + b"\0")
    return digest.hexdigest()


try:
    LOADED_SOURCE_DIGEST = package_source_digest()
except OSError:
    LOADED_SOURCE_DIGEST = None

try:
    from server import PromptServer
    routes = PromptServer.instance.routes
except Exception as exc:
    logging.warning("[MangaBasicGenerationAPI] PromptServer unavailable: %s", exc)
    routes = None


def _live_catalog():
    # Runtime registry is authoritative; this inspection never instantiates a loader or model.
    import folder_paths
    import nodes

    registry = nodes.NODE_CLASS_MAPPINGS
    required = CORE_NODES + (NODE_IDENTITY,)
    if any(name not in registry for name in required):
        raise GenerationContractError("BACKEND_CAPABILITY_UNAVAILABLE", "Manga identity or required core nodes are missing")
    inputs = {name: registry[name].INPUT_TYPES() for name in required}
    checkpoints = folder_paths.get_filename_list("checkpoints")
    loras = folder_paths.get_filename_list("loras")

    def is_available(kind, name):
        resolved = folder_paths.get_full_path(kind, name)
        return resolved is not None and os.path.isfile(resolved)

    catalog = build_catalog(checkpoints, loras, inputs, is_available)
    # Dynamic Prompt capability is part of Manga's backend contract.  The
    # package/root are checked here as well as at compile time so a missing
    # runtime asset cannot present a misleading READY catalog.
    _dynamic, _command, _wildcard_command, _generator, _parse, _manager, version = _dynamic_prompt_api()
    root = _wildcard_root()
    catalog["dynamic_prompts"] = {
        "available": True,
        "version": version,
        "wildcard_root": str(root),
        "override_env": WILDCARD_ENV,
        "supported_syntax": ["__wildcard__", "{a|b}", "nested", "weighted", "escaped_braces"],
    }
    scene_available = all(name in registry for name in SCENE_REQUIRED_NODES)
    reference_nodes_available = all(name in registry for name in SCENE_REFERENCE_REQUIRED_NODES)
    controlnet_nodes_available = all(name in registry for name in SCENE_CONTROLNET_REQUIRED_NODES)

    def model_available(kind, name):
        try:
            resolved = folder_paths.get_full_path(kind, name)
        except Exception:
            return False
        return resolved is not None and os.path.isfile(resolved)

    reference_assets = []
    reference_root = os.path.join(folder_paths.get_input_directory(), "tegaki_manga_references")
    if os.path.isdir(reference_root):
        for name in sorted(os.listdir(reference_root)):
            path = os.path.join(reference_root, name)
            if os.path.isfile(path) and os.path.splitext(name)[1].lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                reference_assets.append(f"tegaki_manga_references/{name}")

    controlnet_model = None
    for candidate in (
        r"CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors",
        "CN-anytest4_illustrious2_A.safetensors",
    ):
        if model_available("controlnet", candidate):
            controlnet_model = candidate
            break

    guide_assets = []
    guide_root = os.path.join(folder_paths.get_input_directory(), "tegaki_manga_guides")
    if os.path.isdir(guide_root):
        for name in sorted(os.listdir(guide_root)):
            path = os.path.join(guide_root, name)
            if os.path.isfile(path) and os.path.splitext(name)[1].lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                guide_assets.append(f"tegaki_manga_guides/{name}")

    catalog["scene_generation"] = {
        "available": scene_available,
        "required_nodes": list(SCENE_REQUIRED_NODES),
        "conditioning": "TegakiMangaConditioningBuilder",
        "page_plan_adapter": "TegakiMangaPagePlanFromJSON",
        "supported_scene_count": {"min": 1, "max": 6},
        "mask_feather": {"default": 16, "min": 0, "max": 64},
        "panel_strength": {"default": 1.0, "min": 0.0, "max": 2.0},
        "reference": {
            "available": reference_nodes_available and
                model_available("clip_vision", REFERENCE_CLIP_VISION) and
                model_available("ipadapter", REFERENCE_IPADAPTER),
            "required_nodes": list(SCENE_REFERENCE_REQUIRED_NODES),
            "clip_vision": REFERENCE_CLIP_VISION,
            "ipadapter": REFERENCE_IPADAPTER,
            "weight": REFERENCE_WEIGHT,
            "weight_type": REFERENCE_WEIGHT_TYPE,
            "combine_embeds": REFERENCE_COMBINE_EMBEDS,
            "start_at": REFERENCE_START_AT,
            "end_at": REFERENCE_END_AT,
            "embeds_scaling": REFERENCE_EMBEDS_SCALING,
            "reference_assets": reference_assets,
        },
        "controlnet": {
            "available": bool(controlnet_nodes_available and controlnet_model is not None),
            "required_nodes": list(SCENE_CONTROLNET_REQUIRED_NODES),
            "model": controlnet_model,
            "default_strength": CONTROLNET_DEFAULT_STRENGTH,
            "start_percent": CONTROLNET_START_PERCENT,
            "end_percent": CONTROLNET_END_PERCENT,
            "guide_assets": guide_assets,
        },
    }
    catalog["revision"] = _digest(catalog)
    return catalog


def _error(code, message, status, request_value=None):
    payload = {"ok": False, "error_code": code, "error": message}
    if request_value is not None:
        payload["request"] = request_value
    return web.json_response(payload, status=status)


async def api_manga_basic_capabilities(request: web.Request) -> web.Response:
    try:
        return web.json_response(_live_catalog())
    except GenerationContractError as exc:
        return _error(exc.code, str(exc), 503)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Capability enumeration failed")
        return _error("BACKEND_CAPABILITY_UNAVAILABLE", "Backend capability enumeration failed", 503)


async def api_manga_basic_compile(request: web.Request) -> web.Response:
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    raw = bytearray()
    async for chunk in request.content.iter_chunked(16384):
        raw.extend(chunk)
        if len(raw) > MAX_REQUEST_BYTES:
            return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    if request.content_type != "application/json":
        return _error("INVALID_CONTENT_TYPE", "Content-Type must be application/json", 415)
    try:
        def no_duplicate_keys(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"Duplicate JSON field: {key}")
                value[key] = item
            return value

        def no_nonfinite(value):
            raise ValueError(f"Non-finite JSON value: {value}")

        candidate = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys, parse_constant=no_nonfinite)
    except (UnicodeDecodeError, ValueError) as exc:
        return _error("INVALID_JSON", str(exc), 400)
    try:
        catalog = _live_catalog()
        return web.json_response(compile_basic(candidate, catalog))
    except GenerationContractError as exc:
        return _error(exc.code, str(exc), 422 if exc.code != "BACKEND_CAPABILITY_UNAVAILABLE" else 503, candidate)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Compile failed")
        return _error("BACKEND_CAPABILITY_UNAVAILABLE", "Backend compile capability failed", 503, candidate)


async def api_manga_scene_compile(request: web.Request) -> web.Response:
    """PLAY5 compile-only Scene Layout endpoint; no queue or model execution."""
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    raw = bytearray()
    async for chunk in request.content.iter_chunked(16384):
        raw.extend(chunk)
        if len(raw) > MAX_REQUEST_BYTES:
            return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    if request.content_type != "application/json":
        return _error("INVALID_CONTENT_TYPE", "Content-Type must be application/json", 415)
    try:
        def no_duplicate_keys(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"Duplicate JSON field: {key}")
                value[key] = item
            return value

        def no_nonfinite(value):
            raise ValueError(f"Non-finite JSON value: {value}")

        candidate = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys, parse_constant=no_nonfinite)
    except (UnicodeDecodeError, ValueError) as exc:
        return _error("INVALID_JSON", str(exc), 400)
    try:
        catalog = _live_catalog()
        return web.json_response(compile_scene(candidate, catalog))
    except GenerationContractError as exc:
        return _error(exc.code, str(exc), 422 if exc.code != "BACKEND_CAPABILITY_UNAVAILABLE" else 503, candidate)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Scene compile failed")
        return _error("BACKEND_CAPABILITY_UNAVAILABLE", "Scene compile capability failed", 503, candidate)


class IsolatedSceneEnvelopeError(GenerationContractError):
    """Validation error for isolated-Scene request envelope."""
    pass


def compile_isolated_scene(
    candidate: dict,
    catalog: dict,
    random_seed=None,
) -> dict:
    """Compile an isolated Scene from an authoring document snapshot.

    Args:
        candidate: Request dictionary containing:
            - authoring_document (dict): Document snapshot.
            - scene_id (str): Target Scene ID.
            - generation_params (dict): Generation execution settings.
            - page_id (str, optional): Target Page ID override.
            - page_index (int, optional): Target Page index override.
            - page_selection (str|int, optional): Page selection.
            - local_dimensions (dict|tuple|list, optional): Local canvas dimensions.
        catalog: Backend capability catalog dict.
        random_seed: Optional random seed generator callable.

    Returns:
        Unified dictionary with plan and compilation outputs.
    """
    if not isinstance(candidate, dict):
        raise IsolatedSceneEnvelopeError("INVALID_REQUEST", "Request payload must be a dictionary")
    if "authoring_document" not in candidate or not isinstance(candidate["authoring_document"], dict):
        raise IsolatedSceneEnvelopeError("INVALID_REQUEST", "authoring_document must be a dictionary")
    if "scene_id" not in candidate or not isinstance(candidate["scene_id"], str) or not candidate["scene_id"].strip():
        raise IsolatedSceneEnvelopeError("INVALID_REQUEST", "scene_id must be a non-empty string")
    if "generation_params" not in candidate or not isinstance(candidate["generation_params"], dict):
        raise IsolatedSceneEnvelopeError("INVALID_REQUEST", "generation_params must be a dictionary")

    plan = create_isolated_scene_plan(
        candidate["authoring_document"],
        scene_id=candidate["scene_id"].strip(),
        page_selection=candidate.get("page_selection"),
        local_dimensions=candidate.get("local_dimensions"),
        page_id=candidate.get("page_id"),
        page_index=candidate.get("page_index"),
    )

    compiled = compile_isolated_scene_plan(
        plan=plan,
        generation_params=candidate["generation_params"],
        catalog=catalog,
        random_seed=random_seed,
    )

    return {
        "ok": True,
        "plan": plan,
        "graph": compiled["graph"],
        "graph_digest": compiled["graph_digest"],
        "save_node_id": compiled["save_node_id"],
        "page_compile_plan": compiled["page_compile_plan"],
        "page_compile_plan_digest": compiled["page_compile_plan_digest"],
        "compile_metadata": compiled["compile_metadata"],
        "audit_trail": compiled["audit_trail"],
    }


async def api_manga_isolated_scene_compile(request: web.Request) -> web.Response:
    """Compile-only isolated Scene endpoint; no queue or model execution."""
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    raw = bytearray()
    async for chunk in request.content.iter_chunked(16384):
        raw.extend(chunk)
        if len(raw) > MAX_REQUEST_BYTES:
            return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    if request.content_type != "application/json":
        return _error("INVALID_CONTENT_TYPE", "Content-Type must be application/json", 415)
    try:
        def no_duplicate_keys(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"Duplicate JSON field: {key}")
                value[key] = item
            return value

        def no_nonfinite(value):
            raise ValueError(f"Non-finite JSON value: {value}")

        candidate = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys, parse_constant=no_nonfinite)
    except (UnicodeDecodeError, ValueError) as exc:
        return _error("INVALID_JSON", str(exc), 400)
    try:
        catalog = _live_catalog()
        result = compile_isolated_scene(candidate, catalog)
        return web.json_response(result)
    except IsolatedSceneEnvelopeError as exc:
        return _error(exc.code, str(exc), 400, candidate)
    except IsolatedScenePlanError as exc:
        return _error(exc.code, str(exc), 422, candidate)
    except GenerationContractError as exc:
        return _error(exc.code, str(exc), 422 if exc.code != "BACKEND_CAPABILITY_UNAVAILABLE" else 503, candidate)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Isolated scene compile failed")
        return _error("BACKEND_CAPABILITY_UNAVAILABLE", "Isolated scene compile capability failed", 503, candidate)


async def api_manga_page_composite(request: web.Request) -> web.Response:
    """CPU pixel composition endpoint for TEGAKI_PAGE_COMPOSITION_PLAN."""
    max_bytes = 1024 * 1024
    if request.content_length is not None and request.content_length > max_bytes:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 1 MiB", 413)
    raw = bytearray()
    async for chunk in request.content.iter_chunked(16384):
        raw.extend(chunk)
        if len(raw) > max_bytes:
            return _error("REQUEST_TOO_LARGE", "Request exceeds 1 MiB", 413)
    if request.content_type != "application/json":
        return _error("INVALID_CONTENT_TYPE", "Content-Type must be application/json", 415)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return _error("INVALID_JSON", str(exc), 400)

    if not isinstance(data, dict):
        return _error("INVALID_REQUEST", "Request body must be a JSON object", 400)

    plan = data.get("composition_plan")
    if not isinstance(plan, dict):
        return _error("INVALID_COMPOSITION_PLAN", "Missing composition_plan in request body", 400)

    try:
        png_bytes = compose_page_pixels(plan)
        return web.Response(
            body=png_bytes,
            content_type="image/png",
            status=200,
        )
    except PagePixelCompositorError as exc:
        status_code = 404 if exc.code == "SOURCE_ARTIFACT_NOT_FOUND" else (
            400 if exc.code in ("INVALID_COMPOSITION_PLAN", "SOURCE_LOCATOR_INVALID") else 422
        )
        return _error(exc.code, exc.message, status_code)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Page pixel composition failed")
        return _error("IMAGE_COMPOSITE_FAILED", "Page pixel composition failed", 500)


RESOURCE_ERROR_STATUS = {
    "INVALID_REQUEST": 400,
    "RESOURCE_PREVIEW_NOT_FOUND": 404,
    "RESOURCE_PREVIEW_UNSUPPORTED": 404,
    "RESOURCE_UNSUPPORTED": 404,
    "RESOURCE_PATH_NOT_FOUND": 404,
    "RESOURCE_ROOT_UNAVAILABLE": 503,
    "RESOURCE_ROOT_UNREGISTERED": 503,
    "RESOURCE_PATH_UNREADABLE": 503,
}


def _comfy_trusted_lora_index(engine: str):
    """The same trusted-root index the generation resolver uses (cached per catalog)."""
    import folder_paths

    root = resolve_resource_root(engine, "lora", folder_paths.get_folder_paths("loras"))
    return build_trusted_lora_index(
        folder_paths.get_filename_list("loras"), root,
        comfy_full_path=lambda item: folder_paths.get_full_path("loras", item),
    )


def _comfy_lora_browse(engine: str, relative_dir: str) -> dict:
    """Lazy one-folder LoRA listing for an engine, via ComfyUI's registered folders."""
    import folder_paths

    index = _comfy_trusted_lora_index(engine)
    return browse_lora_payload(
        engine,
        relative_dir,
        folder_paths.get_folder_paths("loras"),
        extensions=folder_paths.supported_pt_extensions,
        comfy_full_path=lambda item: folder_paths.get_full_path("loras", item),
        token_for=index.token_for,
    )


async def api_manga_resource_lora_index(request: web.Request) -> web.Response:
    engine = request.match_info.get("engine", "")
    try:
        return web.json_response(lora_index_payload(engine, _comfy_trusted_lora_index(engine)))
    except ResourceContractError as exc:
        return _error(exc.code, str(exc), RESOURCE_ERROR_STATUS.get(exc.code, 400))
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] LoRA index failed")
        return _error("RESOURCE_INDEX_FAILED", "LoRA index failed", 500)


async def api_manga_resource_lora_validate(request: web.Request) -> web.Response:
    """Batch pre-generation LoRA diagnostics through the generation resolver."""
    engine = request.match_info.get("engine", "")
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    try:
        body = json.loads((await request.read()).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return _error("INVALID_JSON", "Request must be JSON", 400)
    try:
        return web.json_response(validate_lora_request(engine, body, _comfy_trusted_lora_index(engine)))
    except ResourceContractError as exc:
        return _error(exc.code, str(exc), RESOURCE_ERROR_STATUS.get(exc.code, 400))
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] LoRA validation failed")
        return _error("RESOURCE_VALIDATE_FAILED", "LoRA validation failed", 500)


async def api_manga_resource_lora_browse(request: web.Request) -> web.Response:
    engine = request.match_info.get("engine", "")
    relative_dir = request.query.get("dir", "")
    try:
        return web.json_response(_comfy_lora_browse(engine, relative_dir))
    except ResourceContractError as exc:
        return _error(exc.code, str(exc), RESOURCE_ERROR_STATUS.get(exc.code, 400))
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] LoRA browse failed")
        return _error("RESOURCE_BROWSE_FAILED", "LoRA browse failed", 500)


def _comfy_lora_preview(engine: str, lora_id: str) -> str:
    import folder_paths

    return lora_preview_path(
        engine, lora_id, folder_paths.get_folder_paths("loras"),
        extensions=folder_paths.supported_pt_extensions,
    )


async def api_manga_resource_lora_preview(request: web.Request) -> web.Response:
    """Serve ONE <stem>.preview.png sidecar for a canonical LoRA ID (never a path)."""
    engine = request.match_info.get("engine", "")
    lora_id = request.query.get("id", "")
    try:
        path = _comfy_lora_preview(engine, lora_id)
    except ResourceContractError as exc:
        return _error(exc.code, str(exc), RESOURCE_ERROR_STATUS.get(exc.code, 400))
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] LoRA preview failed")
        return _error("RESOURCE_PREVIEW_FAILED", "LoRA preview failed", 500)
    # Content type follows the actual bytes: a legacy "*.preview.png" may be JPEG.
    return web.FileResponse(path, headers={
        "Content-Type": preview_mime(path) or "application/octet-stream", "Cache-Control": "private, max-age=300",
        "X-Content-Type-Options": "nosniff",
    })


async def api_manga_runtime_source_identity(request: web.Request) -> web.Response:
    """Which package source this backend process loaded (launcher freshness check)."""
    return web.json_response({"ok": True, "service": "tegaki_manga_nodes", "pid": os.getpid(),
                              "source_digest": LOADED_SOURCE_DIGEST}, headers={"Cache-Control": "no-store"})


def expand_one_wildcard(name: object) -> dict:
    """ONE concrete expansion of ``__name__`` through the existing dynamicprompts owner.

    Explicit Owner action (Wildcard preview "Expand").  Uses expand_wildcard_text,
    i.e. the same trusted root, sampler and validation as generation; never writes.
    """
    if not isinstance(name, str) or any(mark in name for mark in ("{", "}", "|", "__")):
        raise GenerationContractError("INVALID_WILDCARD_PATH", "Wildcard identifier must be a plain relative name")
    canonical = _safe_wildcard_name(name)
    result = expand_wildcard_text(f"__{canonical}__", domain="expand")
    if not result.get("ok"):
        error = (result.get("errors") or [{}])[0]
        raise GenerationContractError(error.get("code", "WILDCARD_EXPAND_FAILED"),
                                      error.get("message", "Wildcard expansion failed"))
    # No physical root or seeds leave the backend; the text is what the Owner edits.
    return {"ok": True, "name": canonical, "token": f"__{canonical}__",
            "expanded_text": result["expanded_text"], "used_wildcards": result.get("used_wildcards", [])}


async def api_manga_wildcard_expand(request: web.Request) -> web.Response:
    if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
        return _error("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413)
    try:
        body = json.loads((await request.read()).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return _error("INVALID_JSON", "Request must be JSON", 400)
    try:
        return web.json_response(expand_one_wildcard(body.get("name") if isinstance(body, dict) else None),
                                 headers={"Cache-Control": "no-store"})
    except GenerationContractError as exc:
        return _error(exc.code, str(exc), 404 if exc.code == "WILDCARD_NOT_FOUND" else 400)
    except Exception:
        logging.exception("[MangaBasicGenerationAPI] Wildcard expand failed")
        return _error("WILDCARD_EXPAND_FAILED", "Wildcard expansion failed", 500)


if routes is not None:
    routes.get("/tegaki/manga/runtime/source-identity")(api_manga_runtime_source_identity)
    routes.post("/tegaki/manga/wildcards/expand")(api_manga_wildcard_expand)
    routes.get("/tegaki/manga/resources/{engine}/lora")(api_manga_resource_lora_browse)
    routes.get("/tegaki/manga/resources/{engine}/lora/preview")(api_manga_resource_lora_preview)
    routes.get("/tegaki/manga/resources/{engine}/lora/index")(api_manga_resource_lora_index)
    routes.post("/tegaki/manga/resources/{engine}/lora/validate")(api_manga_resource_lora_validate)
    routes.get("/tegaki/manga/generation/capabilities")(api_manga_basic_capabilities)
    routes.post("/tegaki/manga/generation/compile-basic")(api_manga_basic_compile)
    routes.post("/tegaki/manga/generation/compile-scene")(api_manga_scene_compile)
    routes.post("/tegaki/manga/generation/compile-isolated-scene")(api_manga_isolated_scene_compile)
    routes.post("/tegaki/manga/page/composite")(api_manga_page_composite)

