"""
authoring_execution_bridge.py — M1 Authoring Execution Bridge
=============================================================
Bridges TEGAKI_AUTHORING_DOCUMENT (v1.0.0) to executable backend plans.
In M1, compiles simple scene documents to PAGE_COMPILE_PLAN v1 for
consumption by TegakiMangaConditioningBuilder and ComfyUI Core KSampler.

Core principles:
- TEGAKI_AUTHORING_DOCUMENT is the single source of truth.
- Visual Panel Frames are NOT represented in semantic scene conditioning.
- Simple-only mode: all scenes must have input_mode == "simple".
- Fail-closed on 0 scenes or scenes exceeding backend limit (max 6).
- Renders color-coded scene regions preview tensor [1, H, W, 3].
- Emits structured debug JSON for verification provenance.
"""
import copy
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from .authoring_contract import (
    SCHEMA_ID,
    SCHEMA_VERSION,
    validate_document,
    validate_area,
    ValidationResult,
)
from .scene_spec import (
    validate_page_compile_plan,
    validate_compile_plan,
    SUPPORTED_COMPILE_PLAN_VERSION,
    SUPPORTED_PAGE_COMPILE_PLAN_VERSION,
)
from .spatial_hint_compiler import (
    compile_scene_spatial_hints,
    SUPPORTED_HINT_MODES,
)

logger = logging.getLogger(__name__)

BACKEND_PANEL_LIMIT = 6

# Color palette for scene region previews (high contrast, distinct hues)
SCENE_PREVIEW_PALETTE = [
    {"name": "Scene 1", "hex": "#3b82f6", "rgb": (59, 130, 246), "fill": (59, 130, 246, 60)},
    {"name": "Scene 2", "hex": "#f97316", "rgb": (249, 115, 22), "fill": (249, 115, 22, 60)},
    {"name": "Scene 3", "hex": "#10b981", "rgb": (16, 185, 129), "fill": (16, 185, 129, 60)},
    {"name": "Scene 4", "hex": "#8b5cf6", "rgb": (139, 92, 246), "fill": (139, 92, 246, 60)},
    {"name": "Scene 5", "hex": "#f43f5e", "rgb": (244, 63, 94), "fill": (244, 63, 94, 60)},
    {"name": "Scene 6", "hex": "#14b8a6", "rgb": (20, 184, 166), "fill": (20, 184, 166, 60)},
]

# Color palette for character rough region previews (Card §59)
CHARACTER_PREVIEW_PALETTE = [
    {"name": "Char 1", "hex": "#06b6d4", "rgb": (6, 182, 212), "fill": (6, 182, 212, 70)},
    {"name": "Char 2", "hex": "#eab308", "rgb": (234, 179, 8), "fill": (234, 179, 8, 70)},
    {"name": "Char 3", "hex": "#ec4899", "rgb": (236, 72, 153), "fill": (236, 72, 153, 70)},
    {"name": "Char 4", "hex": "#a855f7", "rgb": (168, 85, 247), "fill": (168, 85, 247, 70)},
    {"name": "Char 5", "hex": "#22c55e", "rgb": (34, 197, 94), "fill": (34, 197, 94, 70)},
    {"name": "Char 6", "hex": "#f97316", "rgb": (249, 115, 22), "fill": (249, 115, 22, 70)},
]


def validate_authoring_execution_document(
    doc: Dict[str, Any],
    page_index: int = 0,
    allow_cast: bool = True,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate document against TEGAKI_AUTHORING_DOCUMENT schema and execution constraints.
    Supports 'simple' scene mode and 'cast' character mode.
    Returns (page, warnings). Raises ValueError on hard validation failure.
    """
    v_res = validate_document(doc)
    if not v_res.valid:
        raise ValueError(
            f"Invalid authoring document: {'; '.join(v_res.errors)}"
        )

    pages = doc.get("pages", [])
    if not pages or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range (have {len(pages)} pages)")

    page = pages[page_index]
    scenes = page.get("scenes", [])

    # Constraint: at least 1 scene
    if not scenes:
        raise ValueError("No scenes to generate. Please add at least one scene.")

    # Constraint: max 6 scenes for backend bridge
    if len(scenes) > BACKEND_PANEL_LIMIT:
        raise ValueError(
            f"Document has {len(scenes)} scenes, exceeding backend execution limit of {BACKEND_PANEL_LIMIT} panels. "
            f"Fail closed."
        )

    # Validate scene modes
    for s_idx, scene in enumerate(scenes):
        mode = scene.get("input_mode", "simple")
        if mode == "simple":
            continue
        elif mode == "cast":
            if not allow_cast:
                raise ValueError(
                    f"Scene '{scene.get('scene_id', s_idx)}' has input_mode='{mode}'. "
                    f"M1 only supports 'simple' scene mode. CAST mode is deferred to M2."
                )
        else:
            raise ValueError(
                f"Scene '{scene.get('scene_id', s_idx)}' has invalid input_mode='{mode}'. "
                f"Expected 'simple' or 'cast'."
            )

    cast_list = page.get("cast", [])
    cast_by_id = {}
    for c_idx, c in enumerate(cast_list):
        cid = c.get("cast_id")
        if not cid or not isinstance(cid, str) or not cid.strip():
            raise ValueError(f"CAST entry at index {c_idx} missing valid 'cast_id'")
        if cid in cast_by_id:
            raise ValueError(f"Duplicate cast_id '{cid}' in page.cast")
        cast_by_id[cid] = c

    character_instances = page.get("character_instances", [])
    seen_instance_ids = set()
    scene_ids = {s.get("scene_id") for s in scenes if s.get("scene_id")}

    for i_idx, inst in enumerate(character_instances):
        iid = inst.get("instance_id")
        if not iid or not isinstance(iid, str) or not iid.strip():
            raise ValueError(f"Character instance at index {i_idx} missing valid 'instance_id'")
        if iid in seen_instance_ids:
            raise ValueError(f"Duplicate instance_id '{iid}' in character_instances (all instance_ids must be unique)")
        seen_instance_ids.add(iid)

        cid = inst.get("cast_id")
        if not cid or cid not in cast_by_id:
            raise ValueError(
                f"Character instance '{iid}' references unknown cast_id '{cid}' (CAST foreign key integrity failure)"
            )

        sid = inst.get("scene_id")
        if not sid or sid not in scene_ids:
            raise ValueError(
                f"Character instance '{iid}' references unknown scene_id '{sid}' (Scene foreign key integrity failure)"
            )

        area = inst.get("area")
        if area is not None:
            area_errs = validate_area(area, f"Character instance '{iid}' area")
            if area_errs:
                raise ValueError(f"Invalid area in character instance '{iid}': {'; '.join(area_errs)}")

    warnings = list(v_res.warnings)
    warnings.append(
        "Semantic Scene conditioning bridge active: Visual Panel Frames are not represented."
    )

    if not allow_cast and character_instances:
        logger.warning(
            "[M1 Bridge] Document has character_instances, but M1 simple mode executes scenes only. "
            "Instances are preserved in document but ignored for M1 execution."
        )

    return page, warnings


def validate_m1_execution_document(doc: Dict[str, Any], page_index: int = 0) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate document against strict M1 simple-mode constraints (for backward compatibility).
    """
    return validate_authoring_execution_document(doc, page_index=page_index, allow_cast=False)


def compile_document_to_page_plan(
    doc: Dict[str, Any],
    page_index: int = 0,
    allow_cast: bool = True,
    spatial_hint_mode: str = "auto",
) -> Dict[str, Any]:
    """
    Compile TEGAKI_AUTHORING_DOCUMENT into a validated PAGE_COMPILE_PLAN v1 dict.
    Supports both M1 simple scene documents and M2A CAST/Character Instance documents.
    In M2A.1, supports transparent compile-time spatial prompt hints without mutating doc SSOT.
    """
    page, warnings = validate_authoring_execution_document(doc, page_index, allow_cast=allow_cast)

    width = int(page.get("width_px", 832))
    height = int(page.get("height_px", 1216))
    style_prompt = page.get("style_prompt", "")
    style_neg = page.get("style_negative_prompt", "")

    scenes = sorted(page.get("scenes", []), key=lambda s: s.get("order", 0))
    cast_by_id = {c["cast_id"]: c for c in page.get("cast", []) if "cast_id" in c}

    instances_by_scene: Dict[str, List[Dict[str, Any]]] = {}
    for inst in page.get("character_instances", []):
        sid = inst.get("scene_id")
        if sid:
            instances_by_scene.setdefault(sid, []).append(inst)

    panels = []
    active_pids = []

    for slot_idx, scene in enumerate(scenes):
        pid = slot_idx + 1
        active_pids.append(pid)
        scene_id = scene.get("scene_id")
        input_mode = scene.get("input_mode", "simple")

        area = scene.get("area", {})
        px = float(area.get("x", 0.05))
        py = float(area.get("y", 0.05))
        pw = float(area.get("w", 0.9))
        ph = float(area.get("h", 0.9))

        scene_prompt = scene.get("prompt", "")
        scene_neg = scene.get("negative_prompt", "")

        compiled_characters = []
        scene_presence_hint = ""

        if allow_cast and input_mode == "cast":
            scene_insts = sorted(
                instances_by_scene.get(scene_id, []),
                key=lambda i: i.get("order", 0)
            )
            hint_map, scene_presence_hint = compile_scene_spatial_hints(
                scene=scene,
                instances=scene_insts,
                cast_by_id=cast_by_id,
                mode=spatial_hint_mode,
            )

            for inst in scene_insts:
                cast_master = cast_by_id[inst["cast_id"]]
                c_display_name = cast_master.get("display_name") or inst["cast_id"]
                hint_data = hint_map.get(inst.get("instance_id"), {})

                c_id_prompt = hint_data.get("raw_identity_prompt", cast_master.get("identity_prompt", "").strip())
                c_act_prompt = hint_data.get("raw_acting_prompt", inst.get("acting_prompt", "").strip())
                derived_spatial_hint = hint_data.get("derived_spatial_hint", "")
                effective_c_prompt = hint_data.get("effective_character_prompt")
                if effective_c_prompt is None:
                    c_pos_parts = [p for p in [c_id_prompt, c_act_prompt] if p]
                    effective_c_prompt = ", ".join(c_pos_parts)

                c_id_neg = cast_master.get("negative_prompt", "").strip()
                c_act_neg = inst.get("negative_prompt_override", "").strip()
                c_neg_parts = [p for p in [c_id_neg, c_act_neg] if p]
                combined_c_neg = ", ".join(c_neg_parts)

                inst_area = inst.get("area")
                compiled_c = {
                    "instance_id": inst.get("instance_id"),
                    "character_id": inst.get("cast_id"),
                    "name": c_display_name,
                    "base_prompt": c_id_prompt,
                    "override_prompt": c_act_prompt,
                    "combined_prompt": effective_c_prompt,
                    "raw_identity_prompt": c_id_prompt,
                    "raw_acting_prompt": c_act_prompt,
                    "derived_spatial_hint": derived_spatial_hint,
                    "scene_presence_hint": scene_presence_hint,
                    "effective_character_prompt": effective_c_prompt,
                    "derived_hints_metadata": hint_data.get("derived_hints_metadata", {}),
                    "base_negative_prompt": c_id_neg,
                    "override_negative_prompt": c_act_neg,
                    "combined_negative_prompt": combined_c_neg,
                    "area": inst_area,
                    "coordinate_space": "page",
                    "loras": list(cast_master.get("loras", [])),
                    "metadata": {
                        "instance_id": inst.get("instance_id"),
                        "cast_id": inst.get("cast_id"),
                        "scene_id": scene_id,
                        "order": inst.get("order", 0),
                        "display_name": c_display_name,
                        "spatial_hint_mode": spatial_hint_mode,
                    },
                }
                compiled_characters.append(compiled_c)

        prompt_parts = [p for p in [style_prompt, scene_prompt] if p]
        if scene_presence_hint:
            prompt_parts.append(scene_presence_hint)
        compiled_prompt = ", ".join(prompt_parts)
        neg_parts = [p for p in [style_neg, scene_neg] if p]
        compiled_neg = ", ".join(neg_parts)

        panel_plan = {
            "version": SUPPORTED_COMPILE_PLAN_VERSION,
            "status": "active",
            "target_panel_id": pid,
            "canvas": {"width": width, "height": height},
            "panel": {
                "id": pid,
                "enabled": True,
                "geometry": {
                    "x": round(px, 4),
                    "y": round(py, 4),
                    "w": round(pw, 4),
                    "h": round(ph, 4),
                },
                "prompt": scene_prompt,
                "negative_prompt": scene_neg,
                "local_regions": [],
                "subscenes": [],
                "camera_distance": "medium",
            },
            "global_prompt": style_prompt,
            "global_negative_prompt": style_neg,
            "compiled_prompt": compiled_prompt,
            "compiled_negative_prompt": compiled_neg,
            "characters": compiled_characters,
            "lora_plan": {
                "global_loras": [],
                "koma_loras": [],
                "character_loras": [],
            },
        }
        panels.append(validate_compile_plan(panel_plan))

    page_compile_plan = {
        "version": SUPPORTED_PAGE_COMPILE_PLAN_VERSION,
        "canvas": {"width": width, "height": height},
        "active_panel_ids": active_pids,
        "global_prompt": style_prompt,
        "global_negative_prompt": style_neg,
        "global_loras": [],
        "panels": panels,
    }

    validated_plan = validate_page_compile_plan(page_compile_plan)
    return validated_plan


def generate_scene_regions_preview_image(
    doc: Dict[str, Any],
    page_index: int = 0,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Image.Image:
    """
    Generate a visual PIL.Image previewing scene regions and character regions with colors, labels, and borders.
    """
    page, _ = validate_authoring_execution_document(doc, page_index, allow_cast=True)
    canvas_w = int(page.get("width_px", 832))
    canvas_h = int(page.get("height_px", 1216))

    target_w = width if width is not None and width > 0 else canvas_w
    target_h = height if height is not None and height > 0 else canvas_h

    base = Image.new("RGBA", (target_w, target_h), (30, 32, 40, 255))
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    grid_spacing = max(32, min(target_w, target_h) // 16)
    for x in range(0, target_w, grid_spacing):
        draw.line([(x, 0), (x, target_h)], fill=(45, 48, 60, 255), width=1)
    for y in range(0, target_h, grid_spacing):
        draw.line([(0, y), (target_w, y)], fill=(45, 48, 60, 255), width=1)

    scenes = sorted(page.get("scenes", []), key=lambda s: s.get("order", 0))

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # 1. Draw Scene Regions
    for idx, scene in enumerate(scenes):
        pal = SCENE_PREVIEW_PALETTE[idx % len(SCENE_PREVIEW_PALETTE)]
        area = scene.get("area", {})
        x0 = int(round(float(area.get("x", 0)) * target_w))
        y0 = int(round(float(area.get("y", 0)) * target_h))
        x1 = int(round((float(area.get("x", 0)) + float(area.get("w", 1))) * target_w))
        y1 = int(round((float(area.get("y", 0)) + float(area.get("h", 1))) * target_h))

        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(target_w, x1), min(target_h, y1)

        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=pal["fill"])
            draw.rectangle([x0, y0, x1, y1], outline=pal["rgb"], width=3)

            name = scene.get("name", f"Scene {idx + 1}")
            prompt_snip = scene.get("prompt", "").strip().replace("\n", " ")
            if len(prompt_snip) > 35:
                prompt_snip = prompt_snip[:32] + "..."
            label = f"[{name}] {prompt_snip}" if prompt_snip else f"[{name}]"

            badge_h = 24
            badge_w = min(x1 - x0, max(120, len(label) * 8 + 16))
            draw.rectangle([x0, y0, x0 + badge_w, y0 + badge_h], fill=pal["rgb"] + (220,))
            draw.text((x0 + 6, y0 + 5), label, fill=(255, 255, 255, 255), font=font)

    # 2. Draw Character Instance Regions (Card §59)
    cast_by_id = {c["cast_id"]: c for c in page.get("cast", []) if "cast_id" in c}
    character_instances = page.get("character_instances", [])

    for c_idx, inst in enumerate(character_instances):
        pal = CHARACTER_PREVIEW_PALETTE[c_idx % len(CHARACTER_PREVIEW_PALETTE)]
        area = inst.get("area", {})
        cx0 = int(round(float(area.get("x", 0)) * target_w))
        cy0 = int(round(float(area.get("y", 0)) * target_h))
        cx1 = int(round((float(area.get("x", 0)) + float(area.get("w", 1))) * target_w))
        cy1 = int(round((float(area.get("y", 0)) + float(area.get("h", 1))) * target_h))

        cx0, cy0 = max(0, cx0), max(0, cy0)
        cx1, cy1 = min(target_w, cx1), min(target_h, cy1)

        if cx1 > cx0 and cy1 > cy0:
            draw.rectangle([cx0, cy0, cx1, cy1], fill=pal["fill"])
            draw.rectangle([cx0, cy0, cx1, cy1], outline=pal["rgb"], width=2)

            cast_info = cast_by_id.get(inst.get("cast_id"), {})
            c_name = cast_info.get("display_name", inst.get("cast_id"))
            act_snip = inst.get("acting_prompt", "").strip().replace("\n", " ")
            if len(act_snip) > 25:
                act_snip = act_snip[:22] + "..."
            c_label = f"[{c_name}] {act_snip}" if act_snip else f"[{c_name}]"

            c_badge_h = 20
            c_badge_w = min(cx1 - cx0, max(80, len(c_label) * 7 + 12))
            draw.rectangle([cx0, cy0, cx0 + c_badge_w, cy0 + c_badge_h], fill=pal["rgb"] + (220,))
            draw.text((cx0 + 4, cy0 + 3), c_label, fill=(255, 255, 255, 255), font=font)

    composite = Image.alpha_composite(base, overlay).convert("RGB")
    return composite


def generate_scene_regions_preview_tensor(
    doc: Dict[str, Any],
    page_index: int = 0,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Any:
    """
    Generate ComfyUI compatible IMAGE tensor [1, H, W, 3] (float32 in [0, 1]).
    If torch is not available, returns numpy array [1, H, W, 3].
    """
    pil_img = generate_scene_regions_preview_image(doc, page_index, width=width, height=height)
    np_arr = np.array(pil_img).astype(np.float32) / 255.0  # [H, W, 3]
    np_arr = np.expand_dims(np_arr, axis=0)                # [1, H, W, 3]

    if HAS_TORCH:
        return torch.from_numpy(np_arr)
    return np_arr


def get_execution_debug_info(
    doc: Dict[str, Any],
    page_index: int = 0,
    seed: Optional[int] = None,
    spatial_hint_mode: str = "auto",
) -> Dict[str, Any]:
    """
    Extract execution debug info dictionary for verification manifest.
    In M2A.1, includes transparent provenance for derived spatial hints.
    """
    page, warnings = validate_authoring_execution_document(doc, page_index, allow_cast=True)
    scenes = page.get("scenes", [])
    gen = page.get("generation", {})
    cast_list = page.get("cast", [])
    instances = page.get("character_instances", [])

    w_px = int(page.get("width_px", 832))
    h_px = int(page.get("height_px", 1216))
    doc_seed = int(gen.get("seed", 42))
    effective_seed = seed if seed is not None else doc_seed

    plan = compile_document_to_page_plan(doc, page_index=page_index, allow_cast=True, spatial_hint_mode=spatial_hint_mode)
    compiled_characters_debug = []
    for p in plan.get("panels", []):
        for c in p.get("characters", []):
            compiled_characters_debug.append({
                "instance_id": c.get("instance_id"),
                "character_id": c.get("character_id"),
                "raw_identity_prompt": c.get("raw_identity_prompt"),
                "raw_acting_prompt": c.get("raw_acting_prompt"),
                "derived_spatial_hint": c.get("derived_spatial_hint"),
                "scene_presence_hint": c.get("scene_presence_hint"),
                "effective_character_prompt": c.get("effective_character_prompt"),
                "derived_hints_metadata": c.get("derived_hints_metadata", {}),
            })

    return {
        "schema_id": doc.get("schema_id", SCHEMA_ID),
        "schema_version": doc.get("schema_version", SCHEMA_VERSION),
        "document_seed": doc_seed,
        "effective_sampler_seed": effective_seed,
        "document_resolution": f"{w_px}x{h_px}",
        "effective_latent_width": w_px,
        "effective_latent_height": h_px,
        "effective_latent_resolution": f"{w_px}x{h_px}",
        "page_resolution": {
            "width": w_px,
            "height": h_px,
        },
        "scene_count": len(scenes),
        "scene_ids": [s.get("scene_id") for s in scenes],
        "scene_areas": [s.get("area") for s in scenes],
        "scenes": [
            {
                "scene_id": s.get("scene_id"),
                "name": s.get("name"),
                "prompt": s.get("prompt"),
                "area": s.get("area"),
                "order": s.get("order"),
                "input_mode": s.get("input_mode", "simple"),
            }
            for s in scenes
        ],
        "cast_count": len(cast_list),
        "cast": [
            {
                "cast_id": c.get("cast_id"),
                "display_name": c.get("display_name"),
                "identity_prompt": c.get("identity_prompt"),
            }
            for c in cast_list
        ],
        "character_instances_count": len(instances),
        "character_instances": [
            {
                "instance_id": i.get("instance_id"),
                "cast_id": i.get("cast_id"),
                "scene_id": i.get("scene_id"),
                "area": i.get("area"),
                "acting_prompt": i.get("acting_prompt"),
                "order": i.get("order"),
            }
            for i in instances
        ],
        "style_template": page.get("metadata", {}).get("style_template", "Manga Monochrome"),
        "spatial_hint_mode": spatial_hint_mode,
        "compiled_characters": compiled_characters_debug,
        "seed": effective_seed,
        "backend_path": "ComfyUI Core Masked Conditioning (PAGE_COMPILE_PLAN -> TegakiMangaConditioningBuilder -> KSampler)",
        "profile": "fast_draft_12 / reference",
        "warnings": warnings,
    }
