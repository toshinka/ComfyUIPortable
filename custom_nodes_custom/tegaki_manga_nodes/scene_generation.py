"""PLAY5 Scene Layout compile contract.

This module is compile-only.  It turns the canonical authoring document into
one validated PAGE_COMPILE_PLAN and a small core ComfyUI graph.  It never
loads a model, queues a prompt, or writes an output.
"""

from __future__ import annotations

import copy
import json
import math
import re
from typing import Any, Callable

from .authoring_execution_bridge import (
    compile_document_to_page_plan,
    validate_authoring_execution_document,
)
from .authoring_contract import (
    validate_asset_reference,
    validate_reference_asset_reference,
)
from .basic_generation import (
    CORE_NODES,
    GenerationContractError,
    LORA_RE,
    REQUEST_ID_RE,
    PRODUCT_BOUNDS,
    SEED_RE,
    _compile_prompt,
    _derive_dynamic_seed,
    _digest,
    _expand_dynamic_prompt,
)
from .scene_spec import validate_page_compile_plan


SCENE_REQUEST_FIELDS = frozenset({
    "request_id", "mode", "checkpoint_id", "authoring_document", "page_index",
    "sampler_id", "scheduler_id", "steps", "cfg", "seed_requested",
    "capability_revision", "mask_feather", "panel_strength", "controlnet_strength",
    "controlnet_start_percent", "controlnet_end_percent",
    "reference_weight", "reference_start", "reference_end",
    "reference_start_at", "reference_end_at",
})
SCENE_REQUIRED_FIELDS = SCENE_REQUEST_FIELDS - {
    "mask_feather", "panel_strength", "controlnet_strength",
    "controlnet_start_percent", "controlnet_end_percent",
    "reference_weight", "reference_start", "reference_end",
    "reference_start_at", "reference_end_at",
}
SCENE_REQUIRED_NODES = (
    "TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder",
)
SCENE_REFERENCE_REQUIRED_NODES = (
    "LoadImage", "CLIPVisionLoader", "IPAdapterModelLoader", "IPAdapterAdvanced",
)
SCENE_CONTROLNET_REQUIRED_NODES = (
    "ControlNetLoader", "ControlNetApplyAdvanced", "LoadImage",
)
CONTROLNET_DEFAULT_MODEL = r"CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors"
CONTROLNET_DEFAULT_STRENGTH = 0.35
CONTROLNET_START_PERCENT = 0.0
CONTROLNET_END_PERCENT = 1.0
REFERENCE_CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
REFERENCE_IPADAPTER = "ip-adapter-plus_sdxl_vit-h.safetensors"
# This is the one checkpoint whose live safetensors architecture and
# IP-Adapter Plus SDXL cross-attention dimensions were verified for this path.
REFERENCE_SUPPORTED_CHECKPOINT = r"!新規SDモデル\comicBookIllustrious_illustriousV11.safetensors"
REFERENCE_WEIGHT = 0.70
REFERENCE_WEIGHT_TYPE = "linear"
REFERENCE_COMBINE_EMBEDS = "concat"
REFERENCE_START_AT = 0.0
REFERENCE_END_AT = 1.0
REFERENCE_EMBEDS_SCALING = "V only"
SCENE_LORA_RE = re.compile(r"<lora:", re.IGNORECASE)
INCOMPATIBLE_CHECKPOINT_SUBSTRINGS = (
    "sd15", "sd_1.5", "sd-1.5", "v1-5", "v1.5", "sd21", "sd_2.1", "sd-2.1", "flux", "cascade",
)
COMPATIBLE_CHECKPOINT_SUBSTRINGS = ("illustrious", "sdxl")


def is_illustrious_sdxl_checkpoint(checkpoint_id: str, catalog: dict | None = None) -> bool:
    """Validate whether checkpoint is an Illustrious / SDXL compatible model."""
    if not isinstance(checkpoint_id, str) or not checkpoint_id:
        return False
    if checkpoint_id == REFERENCE_SUPPORTED_CHECKPOINT:
        return True
    if isinstance(catalog, dict):
        for entry in catalog.get("checkpoints", []):
            if isinstance(entry, dict) and entry.get("id") == checkpoint_id:
                family = str(entry.get("family", "")).lower()
                if family in ("illustrious", "sdxl"):
                    return True
                if family in ("sd15", "v1-5", "sd21", "v2-1", "flux", "cascade", "auraflow", "sd3"):
                    return False
                break
    lower = checkpoint_id.lower()
    if any(sub in lower for sub in INCOMPATIBLE_CHECKPOINT_SUBSTRINGS):
        return False
    return any(sub in lower for sub in COMPATIBLE_CHECKPOINT_SUBSTRINGS)



def _fail(code: str, message: str) -> None:
    raise GenerationContractError(code, message)


def _check_int(value: Any, label: str, lower: int, upper: int, step: int = 1) -> int:
    if type(value) is not int or not lower <= value <= upper or value % step:
        _fail("INVALID_PARAMETER", f"{label} must be an integer in {lower}..{upper} with step {step}")
    return value


def _scene_text(raw: Any, label: str) -> str:
    if not isinstance(raw, str):
        _fail("INVALID_DOCUMENT", f"{label} must be a string")
    if len(raw) > 16000:
        _fail("INVALID_DOCUMENT", f"{label} exceeds 16000 characters")
    return raw


def _scene_lora_guard(raw: str, expanded: str, label: str) -> None:
    # Scene prompts are intentionally simple-only.  Reject both authored tags
    # and wildcard-emitted tags before the global LoRA resolver can run.
    if SCENE_LORA_RE.search(raw) or SCENE_LORA_RE.search(expanded):
        _fail("SCENE_LORA_UNSUPPORTED", f"{label} cannot contain LoRA prompt notation in PLAY5 Scene mode")


def _catalog_scene_nodes(catalog: dict) -> None:
    available = catalog.get("scene_generation", {})
    if available.get("available") is not True:
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", "Scene generation nodes are unavailable")
    required = available.get("required_nodes")
    if required != list(SCENE_REQUIRED_NODES):
        _fail("BACKEND_CAPABILITY_UNAVAILABLE", "Scene generation node capability is incomplete")


def _validate_scene_document(document: Any, page_index: int) -> tuple[dict, dict | None]:
    if not isinstance(document, dict):
        _fail("INVALID_DOCUMENT", "authoring_document must be a JSON object")
    pages = document.get("pages")
    if not isinstance(pages, list) or not pages:
        _fail("INVALID_DOCUMENT", "authoring_document must contain a non-empty pages list")
    if type(page_index) is not int or page_index < 0 or page_index >= len(pages):
        _fail("INVALID_PAGE_INDEX", f"page_index {page_index!r} is outside the authoring document")
    page = pages[page_index]
    if not isinstance(page, dict):
        _fail("INVALID_DOCUMENT", "Selected authoring page must be an object")
    scenes = page.get("scenes")
    if not isinstance(scenes, list):
        _fail("INVALID_DOCUMENT", "Selected authoring page scenes must be a list")

    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            _fail("INVALID_DOCUMENT", f"Scene at index {index} must be an object")

    cast_list = page.get("cast", [])
    instances = page.get("character_instances", [])
    if not isinstance(cast_list, list) or not isinstance(instances, list):
        # The authoring bridge owns detailed schema errors; keep this gate
        # deterministic before it can accidentally enter a dormant CAST path.
        _fail("SCENE_CAST_UNSUPPORTED", "CAST execution requires canonical cast and character_instances lists")

    # Unplaced CAST definitions are authoring data, not active conditions.
    # Keep simple Scene compilation independent of them.
    if not instances:
        for scene in scenes:
            if scene.get("input_mode", "simple") != "simple":
                _fail("SCENE_CAST_UNSUPPORTED", f"Scene {scene.get('scene_id', '?')!r} requires a placed Character Instance")
        try:
            validate_authoring_execution_document(document, page_index, allow_cast=False)
        except GenerationContractError:
            raise
        except ValueError as exc:
            _fail("INVALID_DOCUMENT", str(exc))
        return page, None

    # The active text-conditioning path supports up to two placed Character Instances
    # across CAST-enabled Scenes. Other Scenes must use simple mode.
    if len(instances) > 2:
        _fail("SCENE_CAST_UNSUPPORTED", "Scenes generation currently supports at most two placed Character Instances")

    cast_by_id = {entry.get("cast_id"): entry for entry in cast_list if isinstance(entry, dict)}
    scene_by_id = {s.get("scene_id"): s for s in scenes if isinstance(s, dict)}

    scenes_with_instances = set()
    referenced_assets = set()
    primary_reference_asset = None
    for instance in instances:
        instance_scene_id = instance.get("scene_id")
        parent_scene = scene_by_id.get(instance_scene_id)
        if parent_scene is None:
            _fail("INVALID_DOCUMENT", f"Character instance references unknown scene_id '{instance_scene_id}'")
        if parent_scene.get("input_mode", "simple") != "cast":
            _fail("SCENE_CAST_UNSUPPORTED", "Character execution requires a cast Scene")
        scenes_with_instances.add(instance_scene_id)

        cid = instance.get("cast_id")
        cast = cast_by_id.get(cid)
        if cast is None:
            _fail("INVALID_DOCUMENT", f"Character instance references unknown cast_id '{cid}'")

        if not _rect_area_within(parent_scene.get("area"), instance.get("area")):
            _fail("SCENE_CHARACTER_AREA_INVALID", "Character instance area must be a normalized rectangle inside its parent Scene")

        ref = cast.get("reference_asset")
        if ref:
            referenced_assets.add(ref)
            if primary_reference_asset is None:
                primary_reference_asset = ref

    if len(referenced_assets) > 1:
        _fail("REFERENCE_MULTI_ASSET_UNSUPPORTED", "Only one unique active Character Reference asset is supported across instances")

    for s in scenes:
        if isinstance(s, dict) and s.get("scene_id") not in scenes_with_instances:
            if s.get("input_mode", "simple") != "simple":
                _fail("SCENE_CAST_UNSUPPORTED", f"Scene {s.get('scene_id', '?')!r} requires a placed Character Instance")

    try:
        validate_authoring_execution_document(document, page_index, allow_cast=True)
    except GenerationContractError:
        raise
    except ValueError as exc:
        _fail("INVALID_DOCUMENT", str(exc))

    return page, {
        "reference_asset": primary_reference_asset,
        "instance_count": len(instances),
    }


def _rect_area_within(parent: Any, child: Any) -> bool:
    def read(area: Any) -> dict | None:
        if not isinstance(area, dict) or area.get("shape_type", "rect") != "rect":
            return None
        values = [area.get(key) for key in ("x", "y", "w", "h")]
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in values):
            return None
        x, y, w, h = map(float, values)
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.0001 or y + h > 1.0001:
            return None
        return {"x": x, "y": y, "w": w, "h": h}

    parent_rect = read(parent)
    child_rect = read(child)
    if parent_rect is None or child_rect is None:
        return False
    tolerance = 0.0001
    return (
        child_rect["x"] >= parent_rect["x"] - tolerance
        and child_rect["y"] >= parent_rect["y"] - tolerance
        and child_rect["x"] + child_rect["w"] <= parent_rect["x"] + parent_rect["w"] + tolerance
        and child_rect["y"] + child_rect["h"] <= parent_rect["y"] + parent_rect["h"] + tolerance
    )


def _reference_character(plan: dict) -> dict | None:
    """Return the single top-level compiled reference character, if any."""
    references = []
    for panel in plan.get("panels", []):
        for character in panel.get("characters", []):
            # The top-level PAGE_COMPILE_PLAN field is authoritative.  Metadata
            # is intentionally ignored so a stale audit value cannot activate
            # a runtime Reference graph.
            asset = character.get("reference_asset")
            if asset:
                if validate_reference_asset_reference(asset, "PAGE_COMPILE_PLAN.characters[].reference_asset"):
                    _fail("REFERENCE_ASSET_INVALID", f"Reference asset '{asset}' is not a canonical Manga reference")
                references.append(character)
    if not references:
        return None
    unique_assets = {r.get("reference_asset") for r in references}
    if len(unique_assets) > 1:
        _fail("REFERENCE_MULTI_ASSET_UNSUPPORTED", "Only one unique active Character Reference asset is supported across instances")
    return references[0]


def _catalog_reference(catalog: dict, asset: str, checkpoint_id: str) -> None:
    capability = catalog.get("scene_generation", {}).get("reference")
    if not isinstance(capability, dict) or capability.get("available") is not True:
        _fail("REFERENCE_RUNTIME_UNAVAILABLE", "Manga Reference runtime support is unavailable")
    if capability.get("required_nodes") != list(SCENE_REFERENCE_REQUIRED_NODES):
        _fail("REFERENCE_RUNTIME_UNAVAILABLE", "Manga Reference node capability is incomplete")
    if capability.get("clip_vision") != REFERENCE_CLIP_VISION or capability.get("ipadapter") != REFERENCE_IPADAPTER:
        _fail("REFERENCE_RUNTIME_UNAVAILABLE", "Manga Reference model selectors are not the reviewed fixed pair")
    if (
        capability.get("weight") != REFERENCE_WEIGHT or
        capability.get("weight_type") != REFERENCE_WEIGHT_TYPE or
        capability.get("combine_embeds") != REFERENCE_COMBINE_EMBEDS or
        capability.get("start_at") != REFERENCE_START_AT or
        capability.get("end_at") != REFERENCE_END_AT or
        capability.get("embeds_scaling") != REFERENCE_EMBEDS_SCALING
    ):
        _fail("REFERENCE_RUNTIME_UNAVAILABLE", "Manga Reference weight configuration is not the reviewed fixed pair")
    assets = capability.get("reference_assets")
    if not isinstance(assets, list) or asset not in assets:
        _fail("REFERENCE_ASSET_UNAVAILABLE", f"Reference asset '{asset}' is unavailable")


def _active_guide(page: dict) -> dict | None:
    """Return the single active structural Guide, if any."""
    guides = page.get("guides")
    if guides is None:
        return None
    if not isinstance(guides, list):
        _fail("INVALID_DOCUMENT", "page.guides must be a list")
    active = []
    for idx, g in enumerate(guides):
        if not isinstance(g, dict):
            _fail("INVALID_DOCUMENT", f"page.guides[{idx}] must be an object")
        if g.get("enabled", True) is not False:
            active.append(g)
    if not active:
        return None
    if len(active) > 1:
        _fail("GUIDE_MULTI_INSTANCE_UNSUPPORTED", "Only one active structural guide is supported in PLAY5 Scene mode")
    guide = active[0]
    guide_type = guide.get("guide_type")
    if guide_type not in ("rough_manga", "frame_guide"):
        _fail("GUIDE_TYPE_UNSUPPORTED", f"Unsupported guide_type '{guide_type}'")
    asset = guide.get("asset_reference")
    if not isinstance(asset, str) or not asset.strip():
        _fail("GUIDE_ASSET_INVALID", "Active structural guide must specify asset_reference")
    asset = asset.strip()
    errors = validate_asset_reference(asset, "page.guides[].asset_reference")
    if errors:
        _fail("GUIDE_ASSET_INVALID", f"Invalid guide asset_reference '{asset}': {'; '.join(errors)}")
    return {
        "guide_id": guide.get("guide_id"),
        "guide_type": guide_type,
        "asset_reference": asset,
        "placement": copy.deepcopy(guide.get("placement")),
    }


def _catalog_controlnet(catalog: dict, asset: str, checkpoint_id: str) -> tuple[str, float]:
    capability = catalog.get("scene_generation", {}).get("controlnet")
    if not isinstance(capability, dict) or capability.get("available") is not True:
        _fail("CONTROLNET_RUNTIME_UNAVAILABLE", "Manga ControlNet runtime support is unavailable")
    if capability.get("required_nodes") != list(SCENE_CONTROLNET_REQUIRED_NODES):
        _fail("CONTROLNET_RUNTIME_UNAVAILABLE", "Manga ControlNet node capability is incomplete")
    model = capability.get("model")
    if not isinstance(model, str) or not model:
        _fail("CONTROLNET_MODEL_UNAVAILABLE", "Manga ControlNet model selector is unavailable in catalog")
    assets = capability.get("guide_assets")
    if isinstance(assets, list) and asset not in assets:
        _fail("GUIDE_ASSET_UNAVAILABLE", f"Guide asset '{asset}' is unavailable")
    strength = capability.get("default_strength", CONTROLNET_DEFAULT_STRENGTH)
    return model, float(strength)



def _resolve_seed(seed_text: Any, random_seed: Callable[[], int] | None) -> tuple[str, int]:
    if not isinstance(seed_text, str):
        _fail("INVALID_SEED", "seed_requested must be '-1' or a decimal string 0..4294967295")
    if seed_text == "-1":
        seed = (random_seed or (lambda: __import__("secrets").randbelow(1 << 32)))()
        _check_int(seed, "resolved seed", 0, PRODUCT_BOUNDS["seed"]["max"])
        return seed_text, seed
    if not SEED_RE.fullmatch(seed_text) or int(seed_text) > PRODUCT_BOUNDS["seed"]["max"]:
        _fail("INVALID_SEED", "seed_requested must be '-1' or a decimal string 0..4294967295")
    return seed_text, int(seed_text)


def _effective_prompts(document: dict, page_index: int, effective_seed: int, catalog: dict) -> tuple[dict, dict, list[dict], dict]:
    effective = copy.deepcopy(document)
    page = effective["pages"][page_index]
    roots: list[str] = []
    versions: list[str] = []

    global_raw = _scene_text(page.get("style_prompt", ""), "page.style_prompt")
    global_neg_raw = _scene_text(page.get("style_negative_prompt", ""), "page.style_negative_prompt")
    global_expanded, global_root, global_version = _expand_dynamic_prompt(global_raw, effective_seed, "global:positive")
    global_neg_expanded, global_neg_root, _ = _expand_dynamic_prompt(global_neg_raw, effective_seed, "global:negative")
    if global_root != global_neg_root:
        _fail("WILDCARD_ROOT_UNAVAILABLE", "Global prompts resolved different wildcard roots")
    global_clean, positive_loras = _compile_prompt(global_expanded, catalog)
    global_neg_clean, negative_loras = _compile_prompt(global_neg_expanded, catalog)
    loras = positive_loras + negative_loras
    if len({item["id"] for item in loras}) != len(loras):
        _fail("LORA_DUPLICATE", "The same resolved LoRA appears more than once in global prompts")
    roots.append(global_root)
    versions.append(global_version)
    page["style_prompt"] = global_clean
    page["style_negative_prompt"] = global_neg_clean

    scenes_audit = []
    for scene in sorted(page.get("scenes", []), key=lambda item: item.get("order", 0)):
        scene_id = scene.get("scene_id")
        if not isinstance(scene_id, str) or not scene_id:
            _fail("INVALID_DOCUMENT", "Every simple Scene must have a non-empty scene_id")
        raw = _scene_text(scene.get("prompt", ""), f"Scene {scene_id} prompt")
        neg_raw = _scene_text(scene.get("negative_prompt", ""), f"Scene {scene_id} negative_prompt")
        expanded, root, version = _expand_dynamic_prompt(raw, effective_seed, f"scene:{scene_id}:positive")
        neg_expanded, neg_root, _ = _expand_dynamic_prompt(neg_raw, effective_seed, f"scene:{scene_id}:negative")
        if root != neg_root:
            _fail("WILDCARD_ROOT_UNAVAILABLE", f"Scene {scene_id!r} resolved different wildcard roots")
        _scene_lora_guard(raw, expanded, f"Scene {scene_id!r} positive prompt")
        _scene_lora_guard(neg_raw, neg_expanded, f"Scene {scene_id!r} negative prompt")
        clean, scene_loras = _compile_prompt(expanded, catalog)
        neg_clean, scene_neg_loras = _compile_prompt(neg_expanded, catalog)
        if scene_loras or scene_neg_loras:
            _fail("SCENE_LORA_UNSUPPORTED", f"Scene {scene_id!r} cannot contain LoRA prompt notation in PLAY5 Scene mode")
        roots.extend([root, neg_root])
        versions.append(version)
        scene["prompt"] = clean
        scene["negative_prompt"] = neg_clean
        scene_audit = {
            "scene_id": scene_id,
            "order": scene.get("order"),
            "positive": {"raw": raw, "expanded": expanded, "clean": clean},
            "negative": {"raw": neg_raw, "expanded": neg_expanded, "clean": neg_clean},
        }
        # Keep flat aliases for audit consumers while retaining the nested
        # positive/negative shape used by the workspace history surface.
        scene_audit.update({
            "raw_positive": raw, "expanded_positive": expanded, "clean_positive": clean,
            "raw_negative": neg_raw, "expanded_negative": neg_expanded, "clean_negative": neg_clean,
        })
        scenes_audit.append(scene_audit)

    if len(set(roots)) != 1:
        _fail("WILDCARD_ROOT_UNAVAILABLE", "Prompts resolved different wildcard roots")
    audit = {
        "global": {
            "positive": {"raw": global_raw, "expanded": global_expanded, "clean": global_clean},
            "negative": {"raw": global_neg_raw, "expanded": global_neg_expanded, "clean": global_neg_clean},
            "raw_positive": global_raw, "expanded_positive": global_expanded, "clean_positive": global_clean,
            "raw_negative": global_neg_raw, "expanded_negative": global_neg_expanded, "clean_negative": global_neg_clean,
        },
        "scenes": scenes_audit,
        "resolved_loras": copy.deepcopy(loras),
        "wildcard_root": global_root,
        "dynamicprompts_version": global_version,
        "dynamic_seed_domains": {
            "global_positive": _derive_dynamic_seed(effective_seed, "global:positive"),
            "global_negative": _derive_dynamic_seed(effective_seed, "global:negative"),
            **{
                f"scene:{entry['scene_id']}:positive": _derive_dynamic_seed(effective_seed, f"scene:{entry['scene_id']}:positive")
                for entry in scenes_audit
            },
            **{
                f"scene:{entry['scene_id']}:negative": _derive_dynamic_seed(effective_seed, f"scene:{entry['scene_id']}:negative")
                for entry in scenes_audit
            },
        },
    }
    return effective, audit, loras, {"roots": roots, "versions": versions}


def compile_scene(request: dict, catalog: dict, random_seed: Callable[[], int] | None = None) -> dict:
    """Compile one Scene Layout request; never queues or loads a model."""
    if not isinstance(request, dict):
        _fail("INVALID_REQUEST", "Request must be a JSON object")
    missing = SCENE_REQUIRED_FIELDS - request.keys()
    unknown = request.keys() - SCENE_REQUEST_FIELDS
    if missing or unknown:
        _fail("INVALID_REQUEST", f"Missing fields: {sorted(missing)}; unknown fields: {sorted(unknown)}")
    if not isinstance(catalog, dict) or catalog.get("ok") is not True or not isinstance(catalog.get("revision"), str):
        _fail("CATALOG_UNAVAILABLE", "Backend catalog is unavailable")
    if request["capability_revision"] != catalog["revision"]:
        _fail("CAPABILITY_CHANGED", "Backend capability revision changed; refresh the catalog")
    if not isinstance(request["request_id"], str) or not REQUEST_ID_RE.fullmatch(request["request_id"]):
        _fail("INVALID_REQUEST", "request_id must be 1..64 ASCII letters, digits, underscore, or hyphen")
    if request["mode"] != "scene":
        _fail("INVALID_REQUEST", "Scene compile requests must use mode='scene'")
    for key in ("checkpoint_id", "sampler_id", "scheduler_id"):
        if not isinstance(request[key], str) or not request[key]:
            _fail("INVALID_REQUEST", f"{key} must be a non-empty string")
    page_index = request["page_index"]
    if type(page_index) is not int:
        _fail("INVALID_PAGE_INDEX", "page_index must be an integer")
    _catalog_scene_nodes(catalog)
    selected = request["checkpoint_id"]
    if selected not in {entry["id"] for entry in catalog["checkpoints"] if entry.get("available") is True}:
        _fail("CHECKPOINT_UNAVAILABLE", f"Selected checkpoint '{selected}' is unavailable")
    if request["sampler_id"] not in catalog["samplers"] or request["scheduler_id"] not in catalog["schedulers"]:
        _fail("SAMPLING_UNAVAILABLE", "Selected sampler or scheduler is unavailable")

    bounds = catalog["backend_bounds"]
    steps = _check_int(request["steps"], "steps", max(1, int(bounds["steps"]["min"])), min(100, int(bounds["steps"]["max"])))
    cfg = request["cfg"]
    if type(cfg) not in (int, float) or not math.isfinite(cfg) or not max(0, bounds["cfg"]["min"]) <= cfg <= min(30, bounds["cfg"]["max"]):
        _fail("INVALID_PARAMETER", "cfg is outside finite product/backend bounds")
    cfg = float(cfg)
    seed_text, seed = _resolve_seed(request["seed_requested"], random_seed)
    if seed < bounds["seed"]["min"] or seed > int(bounds["seed"]["max"]):
        _fail("INVALID_SEED", "Seed is outside backend bounds")
    feather = request.get("mask_feather", 16)
    if type(feather) is not int or not 0 <= feather <= 64:
        _fail("INVALID_PARAMETER", "mask_feather must be an integer in 0..64")
    strength = request.get("panel_strength", 1.0)
    if type(strength) not in (int, float) or not math.isfinite(strength) or not 0 <= strength <= 2:
        _fail("INVALID_PARAMETER", "panel_strength must be a finite number in 0..2")
    strength = float(strength)
    cnet_strength = request.get("controlnet_strength")
    if cnet_strength is not None:
        if type(cnet_strength) not in (int, float) or not math.isfinite(cnet_strength) or not 0 <= cnet_strength <= 2:
            _fail("INVALID_PARAMETER", "controlnet_strength must be a finite number in 0..2")
        cnet_strength = float(cnet_strength)

    cnet_start = request.get("controlnet_start_percent")
    if cnet_start is not None:
        if type(cnet_start) not in (int, float) or not math.isfinite(cnet_start) or not 0.0 <= cnet_start <= 1.0:
            _fail("INVALID_PARAMETER", "controlnet_start_percent must be a finite number in 0..1")
        cnet_start = float(cnet_start)
    else:
        cnet_start = CONTROLNET_START_PERCENT

    cnet_end = request.get("controlnet_end_percent")
    if cnet_end is not None:
        if type(cnet_end) not in (int, float) or not math.isfinite(cnet_end) or not 0.0 <= cnet_end <= 1.0:
            _fail("INVALID_PARAMETER", "controlnet_end_percent must be a finite number in 0..1")
        cnet_end = float(cnet_end)
    else:
        cnet_end = CONTROLNET_END_PERCENT

    if cnet_start >= cnet_end:
        _fail("INVALID_PARAMETER", "controlnet_start_percent must be strictly less than controlnet_end_percent")

    ref_weight = request.get("reference_weight")
    if ref_weight is not None:
        if type(ref_weight) not in (int, float) or not math.isfinite(ref_weight) or not 0.0 <= ref_weight <= 2.0:
            _fail("INVALID_PARAMETER", "reference_weight must be a finite number in 0..2")
        ref_weight = float(ref_weight)
    else:
        ref_weight = REFERENCE_WEIGHT

    ref_start = request.get("reference_start") if "reference_start" in request else request.get("reference_start_at")
    if ref_start is not None:
        if type(ref_start) not in (int, float) or not math.isfinite(ref_start) or not 0.0 <= ref_start <= 1.0:
            _fail("INVALID_PARAMETER", "reference_start must be a finite number in 0..1")
        ref_start = float(ref_start)
    else:
        ref_start = REFERENCE_START_AT

    ref_end = request.get("reference_end") if "reference_end" in request else request.get("reference_end_at")
    if ref_end is not None:
        if type(ref_end) not in (int, float) or not math.isfinite(ref_end) or not 0.0 <= ref_end <= 1.0:
            _fail("INVALID_PARAMETER", "reference_end must be a finite number in 0..1")
        ref_end = float(ref_end)
    else:
        ref_end = REFERENCE_END_AT

    if ref_start >= ref_end:
        _fail("INVALID_PARAMETER", "reference_start must be strictly less than reference_end")

    page, cast_slice = _validate_scene_document(request["authoring_document"], page_index)
    active_guide = _active_guide(page)
    cnet_model = None
    if active_guide is not None:
        cnet_model, default_strength = _catalog_controlnet(catalog, active_guide["asset_reference"], selected)
        if cnet_strength is None:
            cnet_strength = default_strength
    width, height = page.get("width_px"), page.get("height_px")
    if type(width) is not int or type(height) is not int:
        _fail("INVALID_DOCUMENT", "Authoring page width_px and height_px must be integers")
    width = _check_int(width, "page.width_px", max(256, int(bounds["width"]["min"])), min(2048, int(bounds["width"]["max"])), 8)
    height = _check_int(height, "page.height_px", max(256, int(bounds["height"]["min"])), min(2048, int(bounds["height"]["max"])), 8)
    for dimension, value in (("width", width), ("height", height)):
        backend_step = bounds[dimension].get("step", 1)
        if type(backend_step) not in (int, float) or backend_step <= 0 or value % backend_step:
            _fail("INVALID_PARAMETER", f"{dimension} violates the backend step")
    if width * height > PRODUCT_BOUNDS["max_pixels"]:
        _fail("INVALID_PARAMETER", "Authoring page resolution exceeds the 2097152-pixel product limit")

    effective_doc, audit, loras, prompt_meta = _effective_prompts(request["authoring_document"], page_index, seed, catalog)
    plan = compile_document_to_page_plan(
        effective_doc, page_index=page_index, allow_cast=cast_slice is not None,
    )
    plan["global_loras"] = copy.deepcopy(loras)
    plan = validate_page_compile_plan(plan)
    reference_character = _reference_character(plan)
    if cast_slice is not None and cast_slice["reference_asset"] and reference_character is None:
        _fail("REFERENCE_ASSET_UNAVAILABLE", "The CAST reference was not carried into PAGE_COMPILE_PLAN")
    if reference_character is not None:
        _catalog_reference(catalog, reference_character["reference_asset"], selected)
    plan_json = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    page_plan_digest = _digest(plan)
    audit["effective_seed"] = seed
    audit["page_compile_plan_digest"] = page_plan_digest
    audit["scene_ids"] = [entry["scene_id"] for entry in audit["scenes"]]
    audit["resolution"] = {"width": width, "height": height}
    audit["reference"] = {"enabled": False}
    if reference_character is not None:
        audit["reference"] = {
            "enabled": True,
            "cast_id": reference_character.get("cast_id"),
            "instance_id": reference_character.get("instance_id"),
            "reference_asset": reference_character.get("reference_asset"),
            "area": copy.deepcopy(reference_character.get("area")),
            "clip_vision": REFERENCE_CLIP_VISION,
            "ipadapter": REFERENCE_IPADAPTER,
            "weight": ref_weight,
            "weight_type": REFERENCE_WEIGHT_TYPE,
            "combine_embeds": REFERENCE_COMBINE_EMBEDS,
            "start_at": ref_start,
            "end_at": ref_end,
            "embeds_scaling": REFERENCE_EMBEDS_SCALING,
        }
    audit["controlnet"] = {"enabled": False}
    if active_guide is not None:
        audit["controlnet"] = {
            "enabled": True,
            "guide_id": active_guide.get("guide_id"),
            "guide_type": active_guide.get("guide_type"),
            "asset_reference": active_guide["asset_reference"],
            "model": cnet_model,
            "strength": cnet_strength,
            "start_percent": cnet_start,
            "end_percent": cnet_end,
        }

    graph = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": selected}}}
    model, clip = ["1", 0], ["1", 1]
    next_id = 2
    for item in loras:
        node_id = str(next_id)
        graph[node_id] = {"class_type": "LoraLoader", "inputs": {
            "model": model, "clip": clip, "lora_name": item["id"],
            "strength_model": item["weight_model"], "strength_clip": item["weight_clip"],
        }}
        model, clip = [node_id, 0], [node_id, 1]
        next_id += 1
    adapter_id = str(next_id)
    conditioning_id = str(next_id + 1)
    latent_id = str(next_id + 2)
    sampler_id = str(next_id + 3)
    decode_id = str(next_id + 4)
    save_id = str(next_id + 5)
    graph[adapter_id] = {"class_type": "TegakiMangaPagePlanFromJSON", "inputs": {"page_compile_plan_json": plan_json}}
    graph[conditioning_id] = {"class_type": "TegakiMangaConditioningBuilder", "inputs": {
        "clip": clip, "page_compile_plan": [adapter_id, 0], "panel_strength": float(strength),
        "set_cond_area": "default", "mask_feather": feather,
    }}
    graph[latent_id] = {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}}
    last_id = int(save_id)
    sampler_model = model
    if reference_character is not None:
        ref_clip_id = str(last_id + 1)
        ref_model_id = str(last_id + 2)
        ref_image_id = str(last_id + 3)
        ref_apply_id = str(last_id + 4)
        last_id += 4
        graph[ref_clip_id] = {"class_type": "CLIPVisionLoader", "inputs": {
            "clip_name": REFERENCE_CLIP_VISION,
        }}
        graph[ref_model_id] = {"class_type": "IPAdapterModelLoader", "inputs": {
            "ipadapter_file": REFERENCE_IPADAPTER,
        }}
        graph[ref_image_id] = {"class_type": "LoadImage", "inputs": {
            "image": f"{reference_character['reference_asset']} [input]",
        }}
        graph[ref_apply_id] = {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": model,
            "ipadapter": [ref_model_id, 0],
            "image": [ref_image_id, 0],
            "weight": ref_weight,
            "weight_type": REFERENCE_WEIGHT_TYPE,
            "combine_embeds": REFERENCE_COMBINE_EMBEDS,
            "start_at": ref_start,
            "end_at": ref_end,
            "embeds_scaling": REFERENCE_EMBEDS_SCALING,
            "attn_mask": [conditioning_id, 6],
            "clip_vision": [ref_clip_id, 0],
        }}
        sampler_model = [ref_apply_id, 0]

    sampler_pos = [conditioning_id, 0]
    sampler_neg = [conditioning_id, 1]
    if active_guide is not None:
        cnet_model_id = str(last_id + 1)
        cnet_image_id = str(last_id + 2)
        cnet_apply_id = str(last_id + 3)
        last_id += 3
        graph[cnet_model_id] = {"class_type": "ControlNetLoader", "inputs": {
            "control_net_name": cnet_model,
        }}
        graph[cnet_image_id] = {"class_type": "LoadImage", "inputs": {
            "image": f"{active_guide['asset_reference']} [input]",
        }}
        graph[cnet_apply_id] = {"class_type": "ControlNetApplyAdvanced", "inputs": {
            "positive": [conditioning_id, 0],
            "negative": [conditioning_id, 1],
            "control_net": [cnet_model_id, 0],
            "image": [cnet_image_id, 0],
            "strength": float(cnet_strength),
            "start_percent": float(cnet_start),
            "end_percent": float(cnet_end),
            "vae": ["1", 2],
        }}
        sampler_pos = [cnet_apply_id, 0]
        sampler_neg = [cnet_apply_id, 1]

    graph[sampler_id] = {"class_type": "KSampler", "inputs": {
        "model": sampler_model, "seed": seed, "steps": steps, "cfg": cfg,
        "sampler_name": request["sampler_id"], "scheduler": request["scheduler_id"],
        "positive": sampler_pos, "negative": sampler_neg,
        "latent_image": [latent_id, 0], "denoise": 1.0,
    }}
    graph[decode_id] = {"class_type": "VAEDecode", "inputs": {"samples": [sampler_id, 0], "vae": ["1", 2]}}
    graph[save_id] = {"class_type": "SaveImage", "inputs": {"images": [decode_id, 0], "filename_prefix": "Manga/Playable/compiled"}}
    graph_digest = _digest(graph)
    audit["graph_digest"] = graph_digest
    normalized = dict(request)
    normalized["cfg"] = cfg
    normalized["seed_requested"] = seed_text
    normalized["mask_feather"] = feather
    normalized["panel_strength"] = float(strength)
    if cnet_strength is not None:
        normalized["controlnet_strength"] = float(cnet_strength)
    if "reference_weight" in request:
        normalized["reference_weight"] = float(ref_weight)
    if "reference_start" in request or "reference_start_at" in request:
        normalized["reference_start"] = float(ref_start)
    if "reference_end" in request or "reference_end_at" in request:
        normalized["reference_end"] = float(ref_end)
    normalized["authoring_document"] = copy.deepcopy(request["authoring_document"])
    return {
        "ok": True,
        "schema_version": "scene-1",
        "normalized_request": normalized,
        "requested_seed": seed_text,
        "effective_seed": seed,
        "effective_authoring_document": effective_doc,
        "page_compile_plan": plan,
        "page_compile_plan_json": plan_json,
        "page_compile_plan_digest": page_plan_digest,
        "audit_trail": audit,
        "resolved_loras": loras,
        "capability_revision": catalog["revision"],
        "graph": graph,
        "graph_digest": graph_digest,
        "scene_ids": audit["scene_ids"],
        "resolution": {"width": width, "height": height},
        "wildcard_root": prompt_meta["roots"][0],
        "dynamicprompts_version": prompt_meta["versions"][0],
        "dynamic_seed_domains": audit["dynamic_seed_domains"],
        "save_node_id": save_id,
    }
