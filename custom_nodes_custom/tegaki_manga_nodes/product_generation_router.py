"""
product_generation_router.py — Deterministic Minimum-Hand Manga Generation Router (M3B-PI2)
==========================================================================================
Evaluates the Authoring Document at queue-time to select between:
- STANDARD_NO_GUIDE: Canonical draft generation workflow (0 ControlNet nodes)
- GUIDED_CLEAN_GLOBAL: Qualified CLEAN GLOBAL ControlNet draft workflow

Semantic contract:
- GUIDED_CLEAN_GLOBAL is selected IF AND ONLY IF page contains >= 1 enabled
  guide_type == "rough_manga" AND >= 1 valid figure_regions[] entry.
- Everything else routes to STANDARD_NO_GUIDE.
- CAST presence, RAW asset presence, and seed do NOT alter routing.
- AnyTest model availability is verified only after GUIDED is selected.
- Pure logic: no direct ComfyUI server/UI coupling in this module.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict, List, Optional, Tuple

ROUTE_STANDARD = "STANDARD_NO_GUIDE"
ROUTE_GUIDED = "GUIDED_CLEAN_GLOBAL"

CONTROLNET_MODEL_SELECTOR = "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors"
DEFAULT_CHECKPOINT = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
DEFAULT_FILENAME_PREFIX = "MangaDraft_M1"

RESOLUTION_MAP = {
    (832, 1216): "Portrait 832x1216",
    (1216, 832): "Landscape 1216x832",
    (1024, 1024): "Square 1024x1024",
}


def evaluate_generation_route(
    document: Dict[str, Any], page_index: int = 0
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Pure evaluation of the Authoring Document to determine generation route.

    Returns:
        (route_enum, reason_string, route_meta_dict)
    """
    if not isinstance(document, dict):
        raise ValueError("Document must be a valid JSON dictionary")

    pages = document.get("pages")
    if not isinstance(pages, list) or len(pages) == 0:
        raise ValueError("Document must contain a non-empty 'pages' list")

    if page_index < 0 or page_index >= len(pages):
        raise IndexError(f"page_index {page_index} out of bounds (document has {len(pages)} pages)")

    page = pages[page_index]
    if not isinstance(page, dict):
        raise ValueError(f"Page at index {page_index} must be a dictionary")

    guides = page.get("guides")
    if not isinstance(guides, list) or len(guides) == 0:
        return (
            ROUTE_STANDARD,
            "No guides present on page",
            {
                "page_index": page_index,
                "eligible_guide_count": 0,
                "figure_count": 0,
                "guide_count": 0,
            },
        )

    eligible_guide_count = 0
    total_valid_figures = 0
    total_rough_guides = 0
    disabled_rough_guides = 0
    zero_figure_rough_guides = 0

    for g in guides:
        if not isinstance(g, dict):
            continue
        if g.get("guide_type") != "rough_manga":
            continue

        total_rough_guides += 1
        is_enabled = g.get("enabled", True) is not False
        if not is_enabled:
            disabled_rough_guides += 1
            continue

        fig_regions = g.get("figure_regions", [])
        if not isinstance(fig_regions, list):
            zero_figure_rough_guides += 1
            continue

        valid_figs = []
        for fig in fig_regions:
            if not isinstance(fig, dict):
                continue
            area = fig.get("area")
            if isinstance(area, dict):
                w = area.get("w", 0)
                h = area.get("h", 0)
                if isinstance(w, (int, float)) and isinstance(h, (int, float)) and w > 0 and h > 0:
                    valid_figs.append(fig)

        if len(valid_figs) > 0:
            eligible_guide_count += 1
            total_valid_figures += len(valid_figs)
        else:
            zero_figure_rough_guides += 1

    if eligible_guide_count > 0:
        return (
            ROUTE_GUIDED,
            f"Eligible rough_manga guide found with {total_valid_figures} figure region(s)",
            {
                "page_index": page_index,
                "eligible_guide_count": eligible_guide_count,
                "figure_count": total_valid_figures,
                "guide_count": len(guides),
            },
        )

    # Determine specific Standard reason
    if total_rough_guides == 0:
        reason = "No rough_manga guides present"
    elif disabled_rough_guides > 0 and eligible_guide_count == 0:
        reason = "Guide is disabled"
    elif zero_figure_rough_guides > 0 and eligible_guide_count == 0:
        reason = "Guide has zero figure regions"
    else:
        reason = "No eligible rough_manga guide with valid figures"

    return (
        ROUTE_STANDARD,
        reason,
        {
            "page_index": page_index,
            "eligible_guide_count": 0,
            "figure_count": 0,
            "guide_count": len(guides),
        },
    )


def is_controlnet_available(selector: str = CONTROLNET_MODEL_SELECTOR) -> bool:
    """
    Check whether the qualified ControlNet model is accessible in ComfyUI environment.
    Only called when GUIDED route is chosen. Never called for STANDARD.
    """
    try:
        import folder_paths

        path = folder_paths.get_full_path("controlnet", selector)
        if path and os.path.isfile(path):
            return True

        # In testing or standalone mode, try loading extra_model_paths.yaml if needed
        extra_cfg = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "ComfyUI", "extra_model_paths.yaml")
        )
        if os.path.isfile(extra_cfg):
            try:
                import utils.extra_config

                utils.extra_config.load_extra_path_config(extra_cfg)
                path = folder_paths.get_full_path("controlnet", selector)
                if path and os.path.isfile(path):
                    return True
            except Exception:
                pass
    except Exception:
        pass

    # Direct fallback search against known shared folders
    for base in [
        "E:/EasyReforge/Model/ControlNet",
        "E:/Data/Models/ControlNet",
        "D:/Models/ControlNet",
    ]:
        cand = os.path.normpath(os.path.join(base, selector))
        if os.path.isfile(cand):
            return True

    return False


def build_standard_prompt(
    doc: Dict[str, Any],
    page_index: int = 0,
    seed: int = 42,
    prefix: str = DEFAULT_FILENAME_PREFIX,
    checkpoint: str = DEFAULT_CHECKPOINT,
) -> Dict[str, Any]:
    """
    Builds the executable ComfyUI API prompt for STANDARD_NO_GUIDE.
    Guarantees ZERO ControlNet, ACN, or Bridge nodes.
    """
    page = doc["pages"][page_index]
    width = int(page.get("width_px", 832))
    height = int(page.get("height_px", 1216))
    style_template = page.get("metadata", {}).get("style_template", "Manga Monochrome")
    resolution_str = RESOLUTION_MAP.get((width, height), f"{width}x{height}")

    doc_copy = copy.deepcopy(doc)
    doc_json_str = json.dumps(doc_copy, ensure_ascii=False)

    prompt: Dict[str, Any] = {}

    # Node 1: TegakiMinimumHandSceneEditor
    prompt["1"] = {
        "class_type": "TegakiMinimumHandSceneEditor",
        "inputs": {
            "document_json": doc_json_str,
            "seed": seed,
            "style_template": style_template,
            "resolution": resolution_str,
        },
    }

    # Node 3: CheckpointLoaderSimple
    prompt["3"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": checkpoint,
        },
    }

    # Node 4: TegakiMangaConditioningBuilder
    prompt["4"] = {
        "class_type": "TegakiMangaConditioningBuilder",
        "inputs": {
            "clip": ["3", 1],
            "page_compile_plan": ["1", 0],
            "panel_strength": 1.0,
            "character_strength": 1.0,
            "set_cond_area": "default",
            "local_region_strength": 1.0,
            "mask_feather": 0,
        },
    }

    # Node 5: EmptyLatentImage
    prompt["5"] = {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": ["1", 3],
            "height": ["1", 4],
            "batch_size": 1,
        },
    }

    # Node 6: KSampler (Direct from ConditioningBuilder, 0 ControlNet)
    prompt["6"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["3", 0],
            "positive": ["4", 0],
            "negative": ["4", 1],
            "latent_image": ["5", 0],
            "seed": seed,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
        },
    }

    # Node 7: VAEDecode
    prompt["7"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["6", 0],
            "vae": ["3", 2],
        },
    }

    # Node 9: TegakiMangaFrameOverlay
    prompt["9"] = {
        "class_type": "TegakiMangaFrameOverlay",
        "inputs": {
            "image": ["7", 0],
            "authoring_document_json": ["1", 6],
            "line_thickness": 4,
            "page_index": page_index,
        },
    }

    # Node 8: SaveImage
    prompt["8"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["9", 0],
            "filename_prefix": prefix,
        },
    }

    return prompt


def build_guided_prompt(
    doc: Dict[str, Any],
    page_index: int = 0,
    seed: int = 42,
    prefix: str = DEFAULT_FILENAME_PREFIX,
    checkpoint: str = DEFAULT_CHECKPOINT,
    controlnet_selector: str = CONTROLNET_MODEL_SELECTOR,
) -> Dict[str, Any]:
    """
    Builds the executable ComfyUI API prompt for GUIDED_CLEAN_GLOBAL.
    Uses ComfyUI core ControlNetApplyAdvanced with TegakiMangaGenerationGuideBridge.
    Guarantees 0 Advanced-ControlNet and 0 effect masks.
    """
    page = doc["pages"][page_index]
    width = int(page.get("width_px", 832))
    height = int(page.get("height_px", 1216))
    style_template = page.get("metadata", {}).get("style_template", "Manga Monochrome")
    resolution_str = RESOLUTION_MAP.get((width, height), f"{width}x{height}")

    doc_copy = copy.deepcopy(doc)
    doc_json_str = json.dumps(doc_copy, ensure_ascii=False)

    prompt: Dict[str, Any] = {}

    # Node 1: TegakiMinimumHandSceneEditor
    prompt["1"] = {
        "class_type": "TegakiMinimumHandSceneEditor",
        "inputs": {
            "document_json": doc_json_str,
            "seed": seed,
            "style_template": style_template,
            "resolution": resolution_str,
        },
    }

    # Node 3: CheckpointLoaderSimple
    prompt["3"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": checkpoint,
        },
    }

    # Node 4: TegakiMangaConditioningBuilder
    prompt["4"] = {
        "class_type": "TegakiMangaConditioningBuilder",
        "inputs": {
            "clip": ["3", 1],
            "page_compile_plan": ["1", 0],
            "panel_strength": 1.0,
            "character_strength": 1.0,
            "set_cond_area": "default",
            "local_region_strength": 1.0,
            "mask_feather": 0,
        },
    }

    # Node 5: EmptyLatentImage
    prompt["5"] = {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": ["1", 3],
            "height": ["1", 4],
            "batch_size": 1,
        },
    }

    # Node 12: TegakiMangaGenerationGuideBridge (Qualified CLEAN Guide)
    prompt["12"] = {
        "class_type": "TegakiMangaGenerationGuideBridge",
        "inputs": {
            "document_json": ["1", 6],
            "page_index": page_index,
        },
    }

    # Node 13: ControlNetLoader
    prompt["13"] = {
        "class_type": "ControlNetLoader",
        "inputs": {
            "control_net_name": controlnet_selector,
        },
    }

    # Node 14: ControlNetApplyAdvanced (Fixed production settings: strength 0.75, start 0.0, end 1.0)
    prompt["14"] = {
        "class_type": "ControlNetApplyAdvanced",
        "inputs": {
            "positive": ["4", 0],
            "negative": ["4", 1],
            "control_net": ["13", 0],
            "image": ["12", 0],
            "vae": ["3", 2],
            "strength": 0.75,
            "start_percent": 0.0,
            "end_percent": 1.0,
        },
    }

    # Node 6: KSampler (Positive and Negative conditioned through ControlNetApplyAdvanced)
    prompt["6"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["3", 0],
            "positive": ["14", 0],
            "negative": ["14", 1],
            "latent_image": ["5", 0],
            "seed": seed,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
        },
    }

    # Node 7: VAEDecode
    prompt["7"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["6", 0],
            "vae": ["3", 2],
        },
    }

    # Node 9: TegakiMangaFrameOverlay
    prompt["9"] = {
        "class_type": "TegakiMangaFrameOverlay",
        "inputs": {
            "image": ["7", 0],
            "authoring_document_json": ["1", 6],
            "line_thickness": 4,
            "page_index": page_index,
        },
    }

    # Node 8: SaveImage
    prompt["8"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["9", 0],
            "filename_prefix": prefix,
        },
    }

    return prompt


def prepare_generation_prompt(
    document: Dict[str, Any],
    page_index: int = 0,
    seed_override: Optional[int] = None,
    prefix: str = DEFAULT_FILENAME_PREFIX,
    checkpoint: str = DEFAULT_CHECKPOINT,
) -> Dict[str, Any]:
    """
    Validates the Authoring Document, evaluates route, validates prerequisites,
    and constructs the executable ComfyUI prompt.
    """
    route, reason, route_meta = evaluate_generation_route(document, page_index)

    page = document["pages"][page_index]
    if seed_override is not None:
        effective_seed = int(seed_override)
    elif "generation" in page and "seed" in page["generation"]:
        effective_seed = int(page["generation"]["seed"])
    else:
        effective_seed = 42

    if route == ROUTE_GUIDED:
        # Check ControlNet model availability ONLY after GUIDED is selected
        if not is_controlnet_available(CONTROLNET_MODEL_SELECTOR):
            return {
                "ok": False,
                "error": f"Guided ControlNet model not available: {CONTROLNET_MODEL_SELECTOR}",
                "error_code": "GUIDED_CONTROLNET_NOT_AVAILABLE",
                "route": route,
                "reason": reason,
                "route_meta": route_meta,
            }

        prompt = build_guided_prompt(
            doc=document,
            page_index=page_index,
            seed=effective_seed,
            prefix=prefix,
            checkpoint=checkpoint,
        )
    else:
        prompt = build_standard_prompt(
            doc=document,
            page_index=page_index,
            seed=effective_seed,
            prefix=prefix,
            checkpoint=checkpoint,
        )

    # Node class inventory
    node_classes = sorted(list(set(n["class_type"] for n in prompt.values())))
    has_cn_nodes = any("ControlNet" in c or "GenerationGuide" in c for c in node_classes)

    return {
        "ok": True,
        "route": route,
        "reason": reason,
        "prompt": prompt,
        "route_meta": {
            **route_meta,
            "seed": effective_seed,
            "prefix": prefix,
            "node_classes": node_classes,
            "has_controlnet_nodes": has_cn_nodes,
            "controlnet_apply_node": "ControlNetApplyAdvanced" if route == ROUTE_GUIDED else "NONE",
            "advanced_controlnet": False,
            "effect_mask": False,
        },
    }
