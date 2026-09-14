"""PLAY1a read/compile-only Manga HTTP endpoints on the existing ComfyUI server."""

from __future__ import annotations

import json
import logging
import os

from aiohttp import web

from .basic_generation import (
    CORE_NODES, NODE_IDENTITY, WILDCARD_ENV, GenerationContractError,
    _digest, _dynamic_prompt_api, _wildcard_root, build_catalog, compile_basic,
)

MAX_REQUEST_BYTES = 256 * 1024

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


if routes is not None:
    routes.get("/tegaki/manga/generation/capabilities")(api_manga_basic_capabilities)
    routes.post("/tegaki/manga/generation/compile-basic")(api_manga_basic_compile)
