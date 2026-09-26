"""isolated_scene_compile.py — Pure compiler adapter for isolated-Scene execution plans.

Adapts a validated isolated-Scene plan (emitted by create_isolated_scene_plan)
into an executable ComfyUI graph dictionary and compile metadata for a local canvas,
reusing the canonical compile_scene backend compiler without modifying existing full-page behavior.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from .scene_generation import (
        compile_scene,
        GenerationContractError,
        SCENE_REQUIRED_NODES,
        REFERENCE_SUPPORTED_CHECKPOINT,
    )
    from .isolated_scene_plan import IsolatedScenePlanError
    from .basic_generation import split_lora_directives
except (ImportError, ValueError):
    from scene_generation import (
        compile_scene,
        GenerationContractError,
        SCENE_REQUIRED_NODES,
        REFERENCE_SUPPORTED_CHECKPOINT,
    )
    from isolated_scene_plan import IsolatedScenePlanError
    from basic_generation import split_lora_directives


class IsolatedSceneCompileError(GenerationContractError):
    """Validation or contract error during isolated-Scene compilation."""
    pass


def compile_isolated_scene_plan(
    plan: Dict[str, Any],
    generation_params: Dict[str, Any],
    catalog: Dict[str, Any],
    random_seed: Optional[Callable[[], int]] = None,
) -> Dict[str, Any]:
    """Compile an isolated-Scene execution plan into an executable ComfyUI graph.

    Args:
        plan: Validated isolated-Scene plan dict from create_isolated_scene_plan.
        generation_params: Execution settings dict (checkpoint_id, sampler_id, etc.).
        catalog: Backend capability catalog dict.
        random_seed: Optional random seed generator callable.

    Returns:
        Dict containing executable ComfyUI graph and compile_metadata.

    Raises:
        IsolatedSceneCompileError: On any validation or compilation failure.
    """
    if not isinstance(plan, dict):
        raise IsolatedSceneCompileError("INVALID_PLAN", "plan must be a dictionary")
    if not isinstance(generation_params, dict):
        raise IsolatedSceneCompileError("INVALID_REQUEST", "generation_params must be a dictionary")
    if not isinstance(catalog, dict):
        raise IsolatedSceneCompileError("CATALOG_UNAVAILABLE", "catalog must be a dictionary")

    # 1. Validate isolated plan integrity
    scene = plan.get("scene")
    if not isinstance(scene, dict) or not scene.get("scene_id"):
        raise IsolatedSceneCompileError("INVALID_PLAN", "plan must contain a valid 'scene' dictionary with 'scene_id'")

    local_canvas = plan.get("local_canvas")
    if not isinstance(local_canvas, dict):
        raise IsolatedSceneCompileError("INVALID_PLAN", "plan must contain a valid 'local_canvas' dictionary")

    width = local_canvas.get("width")
    height = local_canvas.get("height")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise IsolatedSceneCompileError(
            "INVALID_LOCAL_DIMENSIONS",
            f"local_canvas dimensions must be positive integers, got width={width!r}, height={height!r}",
        )

    # Validate page context
    page_context = plan.get("page_context")
    if not isinstance(page_context, dict):
        raise IsolatedSceneCompileError("INVALID_PLAN", "plan must contain a valid 'page_context' dictionary")
    page_w = page_context.get("width_px")
    page_h = page_context.get("height_px")
    if type(page_w) is not int or type(page_h) is not int or page_w <= 0 or page_h <= 0:
        raise IsolatedSceneCompileError(
            "INVALID_PAGE_DIMENSIONS",
            f"page_context dimensions must be positive integers, got width_px={page_w!r}, height_px={page_h!r}",
        )

    # Validate placement mapping
    placement_mapping = plan.get("placement_mapping")
    if not isinstance(placement_mapping, dict):
        raise IsolatedSceneCompileError("INVALID_PLAN", "plan must contain a valid 'placement_mapping' dictionary")

    page_target_rect = placement_mapping.get("page_target_rect")
    local_source_rect = placement_mapping.get("local_source_rect")
    transform = placement_mapping.get("transform")

    if not isinstance(page_target_rect, dict) or not isinstance(local_source_rect, dict) or not isinstance(transform, dict):
        raise IsolatedSceneCompileError(
            "INVALID_PLAN",
            "placement_mapping must contain 'page_target_rect', 'local_source_rect', and 'transform' dictionaries",
        )

    for k in ("x", "y", "w", "h"):
        val = page_target_rect.get(k)
        if type(val) not in (int, float) or not math.isfinite(val):
            raise IsolatedSceneCompileError("INVALID_PLAN", f"page_target_rect '{k}' must be a finite number")
    if page_target_rect["w"] <= 0 or page_target_rect["h"] <= 0:
        raise IsolatedSceneCompileError("INVALID_PLAN", "page_target_rect width and height must be positive")

    px, py, pw, ph = float(page_target_rect["x"]), float(page_target_rect["y"]), float(page_target_rect["w"]), float(page_target_rect["h"])
    EPSILON = 0.001
    if px < -EPSILON or py < -EPSILON or (px + pw) > (1.0 + EPSILON) or (py + ph) > (1.0 + EPSILON):
        raise IsolatedSceneCompileError(
            "INVALID_PLAN",
            f"page_target_rect [{px}, {py}, {pw}, {ph}] extends outside normalized page bounds [0, 1]",
        )

    for k in ("x", "y", "w", "h"):
        val = local_source_rect.get(k)
        if type(val) not in (int, float) or not math.isfinite(val):
            raise IsolatedSceneCompileError("INVALID_PLAN", f"local_source_rect '{k}' must be a finite number")
    if local_source_rect["w"] <= 0 or local_source_rect["h"] <= 0:
        raise IsolatedSceneCompileError("INVALID_PLAN", "local_source_rect width and height must be positive")

    for k in ("scale_x", "scale_y", "offset_x", "offset_y"):
        val = transform.get(k)
        if type(val) not in (int, float) or not math.isfinite(val):
            raise IsolatedSceneCompileError("INVALID_PLAN", f"transform '{k}' must be a finite number")

    if (
        abs(float(transform["scale_x"]) - pw) > EPSILON
        or abs(float(transform["scale_y"]) - ph) > EPSILON
        or abs(float(transform["offset_x"]) - px) > EPSILON
        or abs(float(transform["offset_y"]) - py) > EPSILON
    ):
        raise IsolatedSceneCompileError(
            "INCONSISTENT_PLACEMENT",
            "placement_mapping transform is inconsistent with page_target_rect",
        )

    orig_scene_area = scene.get("original_page_area")
    if isinstance(orig_scene_area, dict) and all(k in orig_scene_area for k in ("x", "y", "w", "h")):
        if (
            abs(float(orig_scene_area["x"]) - px) > EPSILON
            or abs(float(orig_scene_area["y"]) - py) > EPSILON
            or abs(float(orig_scene_area["w"]) - pw) > EPSILON
            or abs(float(orig_scene_area["h"]) - ph) > EPSILON
        ):
            raise IsolatedSceneCompileError(
                "INCONSISTENT_PLACEMENT",
                "page_target_rect does not match scene original_page_area",
            )

    # 2. Guide boundary check: fail-closed if any active structural guide is present
    guides = plan.get("guides") or plan.get("page_context", {}).get("guides") or generation_params.get("guides")
    if isinstance(guides, list):
        for g in guides:
            if isinstance(g, dict) and g.get("enabled", True) is not False:
                if g.get("guide_type") in ("rough_manga", "frame_guide") and g.get("asset_reference"):
                    raise IsolatedSceneCompileError(
                        "ISOLATED_SCENE_GUIDE_UNSUPPORTED",
                        f"Active structural guide '{g.get('guide_id')}' is unsupported in isolated-Scene compilation",
                    )

    # 3. Required generation parameters check
    required_params = ("checkpoint_id", "sampler_id", "scheduler_id", "steps", "cfg")
    missing_params = [k for k in required_params if k not in generation_params]
    if missing_params:
        raise IsolatedSceneCompileError(
            "INVALID_REQUEST",
            f"Missing required generation settings: {missing_params}",
        )

    # 4. Synthesize single-scene local authoring document
    # Scene local area occupies complete local canvas [0, 0, 1, 1]
    scene_id = scene["scene_id"]
    page_context = plan.get("page_context", {})

    # An isolated Scene owns the whole local graph, so LoRA directives written
    # in its positive prompt apply to the whole MODEL/CLIP chain.  Hoist them
    # onto the page-level (global) prompt so the ONE canonical LoRA path in
    # compile_scene resolves them (catalog lookup, fail-closed, LoraLoader
    # chain before CLIP encoding).  Page-style LoRAs keep precedence in chain
    # order; Scene directives follow in prompt order.  No-LoRA text is unchanged.
    scene_prompt = scene.get("prompt", "")
    style_prompt = page_context.get("style_prompt", "")
    if isinstance(scene_prompt, str) and isinstance(style_prompt, str):
        scene_prompt, scene_lora_directives = split_lora_directives(scene_prompt)
        if scene_lora_directives:
            style_prompt = style_prompt + "".join(scene_lora_directives)

    local_page = {
        "page_id": page_context.get("page_id") or "page_isolated",
        "width_px": width,
        "height_px": height,
        "style_prompt": style_prompt,
        "style_negative_prompt": page_context.get("style_negative_prompt", ""),
        "scenes": [
            {
                "scene_id": scene_id,
                "order": 1,
                "name": scene.get("name", scene_id),
                "input_mode": scene.get("input_mode", "simple"),
                "prompt": scene_prompt,
                "negative_prompt": scene.get("negative_prompt", ""),
                "area": {
                    "shape_type": "rect",
                    "x": 0.0,
                    "y": 0.0,
                    "w": 1.0,
                    "h": 1.0,
                },
            }
        ],
        "cast": copy.deepcopy(plan.get("cast", [])),
        "character_instances": [
            {
                "instance_id": inst["instance_id"],
                "cast_id": inst["cast_id"],
                "scene_id": scene_id,
                "acting_prompt": inst.get("acting_prompt", ""),
                "area": copy.deepcopy(inst["area"]),
                **({"negative_prompt_override": inst["negative_prompt_override"]} if "negative_prompt_override" in inst else {}),
                **({"order": inst["order"]} if "order" in inst else {}),
            }
            for inst in plan.get("character_instances", [])
        ],
        "guides": [],
    }

    local_doc = {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
        "schema_version": "1.0.0",
        "document_id": plan.get("owner", {}).get("document_id") or "doc_isolated",
        "pages": [local_page],
    }

    # 5. Assemble standard scene generation request
    request_id = generation_params.get("request_id") or f"isolated_{scene_id}"
    req: Dict[str, Any] = {
        "request_id": request_id,
        "mode": "scene",
        "checkpoint_id": generation_params["checkpoint_id"],
        "authoring_document": local_doc,
        "page_index": 0,
        "sampler_id": generation_params["sampler_id"],
        "scheduler_id": generation_params["scheduler_id"],
        "steps": generation_params["steps"],
        "cfg": generation_params["cfg"],
        "seed_requested": str(generation_params.get("seed_requested", "0")),
        "capability_revision": catalog.get("revision", generation_params.get("capability_revision", "")),
        "mask_feather": generation_params.get("mask_feather", 16),
        "panel_strength": generation_params.get("panel_strength", 1.0),
    }

    # Optional ControlNet / Reference passthroughs
    if "controlnet_strength" in generation_params:
        req["controlnet_strength"] = generation_params["controlnet_strength"]
    if "controlnet_start_percent" in generation_params:
        req["controlnet_start_percent"] = generation_params["controlnet_start_percent"]
    if "controlnet_end_percent" in generation_params:
        req["controlnet_end_percent"] = generation_params["controlnet_end_percent"]

    if "reference_weight" in generation_params:
        req["reference_weight"] = generation_params["reference_weight"]
    if "reference_start" in generation_params or "reference_start_at" in generation_params:
        req["reference_start"] = generation_params.get("reference_start", generation_params.get("reference_start_at"))
    if "reference_end" in generation_params or "reference_end_at" in generation_params:
        req["reference_end"] = generation_params.get("reference_end", generation_params.get("reference_end_at"))

    # 6. Delegate to canonical compile_scene compiler
    try:
        compiled = compile_scene(req, catalog, random_seed=random_seed)
    except GenerationContractError as exc:
        raise IsolatedSceneCompileError(exc.code, str(exc)) from exc

    # 7. Construct result with graph and isolated compile metadata
    effective_settings: Dict[str, Any] = {
        "checkpoint_id": generation_params["checkpoint_id"],
        "sampler_id": generation_params["sampler_id"],
        "scheduler_id": generation_params["scheduler_id"],
        "steps": compiled["normalized_request"]["steps"],
        "cfg": compiled["normalized_request"]["cfg"],
        "seed_requested": compiled["requested_seed"],
        "effective_seed": compiled["effective_seed"],
        "mask_feather": compiled["normalized_request"].get("mask_feather", 16),
        "panel_strength": compiled["normalized_request"].get("panel_strength", 1.0),
    }

    ref_audit = compiled.get("audit_trail", {}).get("reference", {})
    if ref_audit.get("enabled"):
        effective_settings["reference_weight"] = float(ref_audit.get("weight", 0.70))
        effective_settings["reference_start"] = float(ref_audit.get("start_at", 0.0))
        effective_settings["reference_end"] = float(ref_audit.get("end_at", 1.0))
        for node in compiled.get("graph", {}).values():
            if isinstance(node, dict) and node.get("class_type") == "IPAdapterAdvanced":
                inputs = node.get("inputs", {})
                if "weight" in inputs and inputs["weight"] is not None:
                    effective_settings["reference_weight"] = float(inputs["weight"])
                if "start_at" in inputs and inputs["start_at"] is not None:
                    effective_settings["reference_start"] = float(inputs["start_at"])
                if "end_at" in inputs and inputs["end_at"] is not None:
                    effective_settings["reference_end"] = float(inputs["end_at"])
                break

    compile_metadata = {
        "scene_id": scene_id,
        "graph_digest": compiled["graph_digest"],
        "page_id": page_context.get("page_id"),
        "page_index": page_context.get("page_index"),
        "page_dimensions": {
            "width": page_w,
            "height": page_h,
        },
        "page_context": {
            "page_id": page_context.get("page_id"),
            "page_index": page_context.get("page_index"),
            "width_px": page_w,
            "height_px": page_h,
        },
        "local_dimensions": {
            "width": width,
            "height": height,
        },
        "placement_mapping": copy.deepcopy(placement_mapping),
        "page_target_rect": copy.deepcopy(page_target_rect),
        "local_source_rect": copy.deepcopy(local_source_rect),
        "transform": copy.deepcopy(transform),
        "selected_instances": [
            inst["instance_id"] for inst in plan.get("character_instances", [])
        ],
        "referenced_cast_ids": [
            c["cast_id"] for c in plan.get("cast", [])
        ],
        "reference": copy.deepcopy(plan.get("reference", {"enabled": False})),
        "guide_state": copy.deepcopy(plan.get("guide_state", {"enabled": False, "active": False})),
        "effective_settings": effective_settings,
        "page_compile_plan": compiled["page_compile_plan"],
        "page_compile_plan_digest": compiled["page_compile_plan_digest"],
        "audit_trail": compiled["audit_trail"],
    }

    return {
        "ok": True,
        "graph": compiled["graph"],
        "graph_digest": compiled["graph_digest"],
        "save_node_id": compiled["save_node_id"],
        "compile_metadata": compile_metadata,
        "page_compile_plan": compiled["page_compile_plan"],
        "page_compile_plan_digest": compiled["page_compile_plan_digest"],
        "audit_trail": compiled["audit_trail"],
    }
