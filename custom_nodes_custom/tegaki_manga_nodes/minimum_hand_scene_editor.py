"""
minimum_hand_scene_editor.py — M1 Minimum-Hand Scene Draft Editor Node
======================================================================
Provides the primary authoring node for M1 Scene-only Minimum-Hand Drafts.
Bridges frontend interactive canvas editing with the ComfyUI backend.

SSOT: TEGAKI_AUTHORING_DOCUMENT JSON stored in the document_json widget.
"""
import json
import logging
from typing import Dict, Any, Tuple

from .authoring_contract import (
    create_document,
    create_page,
    create_scene,
    make_area,
    validate_document,
)
from .authoring_execution_bridge import (
    compile_document_to_page_plan,
    generate_scene_regions_preview_tensor,
    get_execution_debug_info,
)

logger = logging.getLogger(__name__)

RESOLUTION_PRESETS = {
    "Portrait 832x1216": (832, 1216),
    "Landscape 1216x832": (1216, 832),
    "Square 1024x1024": (1024, 1024),
}

STYLE_TEMPLATES = {
    "Manga Monochrome": {
        "style_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "style_negative_prompt": "bad anatomy, blurry, photo, color, 3d render, watermark, text",
    },
    "Manga Color": {
        "style_prompt": "color manga page, rich vibrant digital watercolor and clean ink, anime aesthetic",
        "style_negative_prompt": "bad anatomy, blurry, lowres, photo, realistic 3d, watermark, text",
    },
}


def create_default_m1_document(
    width: int = 832,
    height: int = 1216,
    style_template_name: str = "Manga Monochrome",
    seed: int = 42,
) -> Dict[str, Any]:
    """Create a default 2-scene canonical document for M1."""
    tmpl = STYLE_TEMPLATES.get(style_template_name, STYLE_TEMPLATES["Manga Monochrome"])

    page = create_page(
        width_px=width,
        height_px=height,
        style_prompt=tmpl["style_prompt"],
        style_negative_prompt=tmpl["style_negative_prompt"],
        page_id="page_1",
    )
    page["metadata"]["style_template"] = style_template_name
    page["generation"] = {"seed": int(seed)}

    # Scene 1: Top scene
    page["scenes"].append(create_scene(
        name="Scene 1",
        prompt="school classroom, desks and chairs, a student reading quietly by the window, warm sunlight",
        negative_prompt="",
        input_mode="simple",
        area=make_area(0.08, 0.06, 0.84, 0.42),
        order=1,
        scene_id="scene_top",
    ))

    # Scene 2: Bottom scene
    page["scenes"].append(create_scene(
        name="Scene 2",
        prompt="outdoor train station platform, railway tracks, a commuter waiting with bicycle, afternoon sky",
        negative_prompt="",
        input_mode="simple",
        area=make_area(0.08, 0.52, 0.84, 0.42),
        order=2,
        scene_id="scene_bottom",
    ))

    return create_document(pages=[page])


class TegakiMinimumHandSceneEditor:
    """
    Tegaki Minimum-Hand Scene Editor (M1 / Phase 3M-1)
    Provides interactive Scene rectangle authoring, resolution selection, style template
    selection, and seed control. Emits PAGE_COMPILE_PLAN directly to standard conditioning.
    """
    @classmethod
    def INPUT_TYPES(cls):
        default_doc = create_default_m1_document()
        default_json = json.dumps(default_doc, indent=2, ensure_ascii=False)

        return {
            "required": {
                "document_json": ("STRING", {
                    "multiline": True,
                    "default": default_json,
                }),
                "seed": ("INT", {
                    "default": 42,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1,
                }),
            },
            "optional": {
                "style_template": (["Manga Monochrome", "Manga Color"], {
                    "default": "Manga Monochrome"
                }),
                "resolution": (["Portrait 832x1216", "Landscape 1216x832", "Square 1024x1024"], {
                    "default": "Portrait 832x1216"
                }),
            }
        }

    RETURN_TYPES = (
        "PAGE_COMPILE_PLAN",
        "IMAGE",
        "INT",
        "INT",
        "INT",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "page_compile_plan",
        "scene_regions_preview",
        "seed",
        "width",
        "height",
        "debug_json",
        "authoring_document_json",
    )
    FUNCTION = "edit_and_compile"
    CATEGORY = "tegaki/manga"

    def edit_and_compile(
        self,
        document_json: str,
        seed: int = 42,
        style_template: str = None,
        resolution: str = None,
    ) -> Tuple[Any, Any, int, int, int, str, str]:
        # Parse document JSON
        raw_text = (document_json or "").strip()
        if not raw_text:
            doc = create_default_m1_document(
                seed=seed,
                style_template_name=style_template or "Manga Monochrome",
            )
        else:
            try:
                doc = json.loads(raw_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"[TegakiSceneEditor] Invalid document JSON: {e}")

        # Basic document structure safety check
        if not isinstance(doc, dict) or "pages" not in doc or not doc["pages"]:
            raise ValueError("[TegakiSceneEditor] Authoring document must contain at least one page.")

        # Migrate any legacy 'dimensions' dialect to canonical page.width_px / page.height_px
        for p in doc.get("pages", []):
            if isinstance(p, dict) and "dimensions" in p:
                dims = p.pop("dimensions")
                if isinstance(dims, dict):
                    if "width_px" not in p:
                        p["width_px"] = dims.get("width_px", 832)
                    if "height_px" not in p:
                        p["height_px"] = dims.get("height_px", 1216)

        page = doc["pages"][0]

        # Resolution synchronization:
        if resolution is not None and resolution in RESOLUTION_PRESETS:
            res_w, res_h = RESOLUTION_PRESETS[resolution]
            page["width_px"] = res_w
            page["height_px"] = res_h
        else:
            res_w = int(page.get("width_px", 832))
            res_h = int(page.get("height_px", 1216))
            page["width_px"] = res_w
            page["height_px"] = res_h

        # Style template synchronization:
        if "metadata" not in page or not isinstance(page["metadata"], dict):
            page["metadata"] = {}

        if style_template is not None and style_template in STYLE_TEMPLATES:
            page["metadata"]["style_template"] = style_template
            tmpl = STYLE_TEMPLATES[style_template]
            if not page.get("style_prompt"):
                page["style_prompt"] = tmpl["style_prompt"]
            if not page.get("style_negative_prompt"):
                page["style_negative_prompt"] = tmpl["style_negative_prompt"]
        else:
            if not page.get("metadata", {}).get("style_template"):
                page["metadata"]["style_template"] = "Manga Monochrome"

        # Seed synchronization:
        if "generation" not in page or not isinstance(page["generation"], dict):
            page["generation"] = {}
        page["generation"]["seed"] = int(seed)
        effective_seed = int(seed)

        # Compile to PAGE_COMPILE_PLAN (validates M1 constraints: >=1 scene, <=6 scenes, simple mode)
        page_compile_plan = compile_document_to_page_plan(doc)

        # Generate preview image tensor [1, H, W, 3]
        preview_tensor = generate_scene_regions_preview_tensor(doc)

        # Generate debug json
        debug_info = get_execution_debug_info(doc, seed=effective_seed)
        debug_info["widget_seed"] = int(seed)
        debug_str = json.dumps(debug_info, indent=2, ensure_ascii=False)

        # Normalized document JSON
        normalized_doc_json = json.dumps(doc, indent=2, ensure_ascii=False)

        return (
            page_compile_plan,
            preview_tensor,
            effective_seed,
            res_w,
            res_h,
            debug_str,
            normalized_doc_json,
        )
