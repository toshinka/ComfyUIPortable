"""
Generate Workflow 17 (Phase 3D.1-D)
===================================
Generates workflows/17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json:
Integrated pipeline with:
- CheckpointLoaderSimple + TegakiLoraPromptLoader
- TegakiMangaCastMaster (Centralized Character Master)
- TegakiMangaRegionEditor (3-panel basic with Alice+Bob overlap in KOMA 1)
- TegakiMangaPageCompiler (Compiles scene plan linking Region Editor and Cast Master)
- TegakiMangaPanelLayoutEditor (3-panel basic geometry & ControlNet white guide)
- TegakiMangaLayoutAwareConditioningBuilder (4-tier conditioning)
- ControlNetApplyAdvanced (Strength 0.60)
- KSampler + VAEDecode + SaveImage + Previews
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.cast_master import get_default_cast_spec


def build_workflow_17():
    layout_spec_3_basic = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    layout_spec_json = json.dumps(layout_spec_3_basic, indent=2, ensure_ascii=False)

    cast_spec = get_default_cast_spec()
    cast_spec_json = json.dumps(cast_spec, indent=2, ensure_ascii=False)

    region_spec_data = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d, blurry",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40,
                "prompt": "classroom, two people talking, afternoon sunlight",
                "negative_prompt": "empty room, solo",
                "local_regions": [
                    {
                        "id": "lr_window_desks",
                        "name": "Window Desks",
                        "enabled": True,
                        "prompt": "school desks near the window, sunlight streaming, notebooks on desk",
                        "negative_prompt": "dark, shadow",
                        "area": {"x": 0.10, "y": 0.15, "w": 0.38, "h": 0.70}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "annoyed expression, looking right",
                        "negative_prompt_override": "happy, smiling",
                        "area": {"x": 0.05, "y": 0.08, "w": 0.62, "h": 0.84}
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "laughing expression, looking left",
                        "negative_prompt_override": "crying, sad",
                        "area": {"x": 0.33, "y": 0.08, "w": 0.62, "h": 0.84}
                    }
                ]
            },
            {
                "id": 2,
                "name": "KOMA 2",
                "enabled": True,
                "x": 0.05, "y": 0.45, "w": 0.45, "h": 0.50,
                "prompt": "school corridor, walking scene",
                "negative_prompt": "",
                "local_regions": [
                    {
                        "id": "lr_lockers",
                        "name": "Lockers",
                        "enabled": True,
                        "prompt": "school lockers along wall, hallway perspective",
                        "negative_prompt": "",
                        "area": {"x": 0.50, "y": 0.10, "w": 0.45, "h": 0.80}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "walking away, back view",
                        "area": None
                    }
                ]
            },
            {
                "id": 3,
                "name": "KOMA 3",
                "enabled": True,
                "x": 0.50, "y": 0.45, "w": 0.45, "h": 0.50,
                "prompt": "school grounds outside, boy waiting by fence, dusk sky",
                "negative_prompt": "",
                "local_regions": [],
                "characters": [
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "standing by fence, looking at sky",
                        "area": {"x": 0.20, "y": 0.10, "w": 0.60, "h": 0.80}
                    }
                ]
            }
        ]
    }
    region_spec_json = json.dumps(region_spec_data, indent=2, ensure_ascii=False)

    nodes = [
        {
            "id": 1,
            "type": "CheckpointLoaderSimple",
            "pos": [40, 80],
            "size": [320, 100],
            "flags": {},
            "order": 0,
            "mode": 0,
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [3], "slot_index": 2}
            ],
            "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
        },
        {
            "id": 2,
            "type": "ControlNetLoader",
            "pos": [40, 240],
            "size": [320, 60],
            "flags": {},
            "order": 1,
            "mode": 0,
            "outputs": [
                {"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [4], "slot_index": 0}
            ],
            "widgets_values": ["manga_line_controlnet"]
        },
        {
            "id": 3,
            "type": "EmptyLatentImage",
            "pos": [40, 360],
            "size": [320, 100],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}
            ],
            "widgets_values": [832, 1216, 1]
        },
        {
            "id": 4,
            "type": "TegakiLoraPromptLoader",
            "pos": [400, 80],
            "size": [360, 220],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": 2},
                {"name": "optional_lora_stack", "type": "LORA_STACK", "link": None}
            ],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [6], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [7], "slot_index": 1}
            ],
            "widgets_values": ["<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"]
        },
        {
            "id": 5,
            "type": "TegakiMangaCastMaster",
            "pos": [400, 360],
            "size": [360, 480],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 8}
            ],
            "outputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "links": None, "slot_index": 0},
                {"name": "cast_spec_json", "type": "STRING", "links": [9], "slot_index": 1},
                {"name": "selected_character_id", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "character_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [cast_spec_json]
        },
        {
            "id": 6,
            "type": "TegakiMangaRegionEditor",
            "pos": [800, 80],
            "size": [440, 520],
            "flags": {},
            "order": 5,
            "mode": 0,
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [8, 10], "slot_index": 0},
                {"name": "region_spec_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "global_prompt", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "preview_image", "type": "IMAGE", "links": [11], "slot_index": 3},
                {"name": "mask_batch", "type": "MASK", "links": None, "slot_index": 4}
            ],
            "widgets_values": [
                3,
                832,
                1216,
                "manga page, monochrome, expressive linework, high contrast, screentone shading",
                region_spec_json
            ]
        },
        {
            "id": 7,
            "type": "TegakiMangaPageCompiler",
            "pos": [800, 640],
            "size": [440, 420],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 10},
                {"name": "cast_spec", "type": "STRING", "link": 9}
            ],
            "outputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "links": [12], "slot_index": 0},
                {"name": "page_compile_plan_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "global_loras_text", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "active_panels_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [
                cast_spec_json,
                "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"
            ]
        },
        {
            "id": 8,
            "type": "TegakiMangaPanelLayoutEditor",
            "pos": [1280, 80],
            "size": [440, 520],
            "flags": {},
            "order": 7,
            "mode": 0,
            "outputs": [
                {"name": "layout_image", "type": "IMAGE", "links": [13, 14], "slot_index": 0},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [15], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [
                832,
                1216,
                4,
                layout_spec_json
            ]
        },
        {
            "id": 9,
            "type": "TegakiMangaLayoutAwareConditioningBuilder",
            "pos": [1280, 640],
            "size": [440, 360],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 7},
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "link": 12},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 15}
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": [16], "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": [17], "slot_index": 1},
                {"name": "panel_masks", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "character_masks", "type": "MASK", "links": None, "slot_index": 3},
                {"name": "mask_preview", "type": "IMAGE", "links": [18], "slot_index": 4},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 5},
                {"name": "local_region_masks", "type": "MASK", "links": None, "slot_index": 6}
            ],
            "widgets_values": [1.0, 0.9, "default", 0.8, 0]
        },
        {
            "id": 10,
            "type": "ControlNetApplyAdvanced",
            "pos": [1760, 80],
            "size": [360, 260],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "positive", "type": "CONDITIONING", "link": 16},
                {"name": "negative", "type": "CONDITIONING", "link": 17},
                {"name": "control_net", "type": "CONTROL_NET", "link": 4},
                {"name": "image", "type": "IMAGE", "link": 13}
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": [19], "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": [20], "slot_index": 1}
            ],
            "widgets_values": [0.60, 0.0, 1.0]
        },
        {
            "id": 11,
            "type": "KSampler",
            "pos": [1760, 380],
            "size": [360, 380],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 6},
                {"name": "positive", "type": "CONDITIONING", "link": 19},
                {"name": "negative", "type": "CONDITIONING", "link": 20},
                {"name": "latent_image", "type": "LATENT", "link": 5}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [21], "slot_index": 0}
            ],
            "widgets_values": [44, "fixed", 15, 7.0, "euler", "normal", 1.0]
        },
        {
            "id": 12,
            "type": "VAEDecode",
            "pos": [2160, 380],
            "size": [220, 60],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 21},
                {"name": "vae", "type": "VAE", "link": 3}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [22, 23], "slot_index": 0}
            ],
            "widgets_values": []
        },
        {
            "id": 13,
            "type": "SaveImage",
            "pos": [2420, 380],
            "size": [360, 320],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 22}
            ],
            "widgets_values": ["Tegaki/MangaCastLocality/Workflow17"]
        },
        {
            "id": 14,
            "type": "PreviewImage",
            "pos": [800, 1100],
            "size": [360, 320],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 11}
            ],
            "widgets_values": []
        },
        {
            "id": 15,
            "type": "PreviewImage",
            "pos": [1280, 1040],
            "size": [360, 320],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 14}
            ],
            "widgets_values": []
        },
        {
            "id": 16,
            "type": "PreviewImage",
            "pos": [1680, 800],
            "size": [360, 320],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 18}
            ],
            "widgets_values": []
        },
        {
            "id": 17,
            "type": "PreviewImage",
            "pos": [2160, 500],
            "size": [360, 320],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 23}
            ],
            "widgets_values": []
        }
    ]

    links = [
        [1, 1, 0, 4, 0, "MODEL"],
        [2, 1, 1, 4, 1, "CLIP"],
        [3, 1, 2, 12, 1, "VAE"],
        [4, 2, 0, 10, 2, "CONTROL_NET"],
        [5, 3, 0, 11, 3, "LATENT"],
        [6, 4, 0, 11, 0, "MODEL"],
        [7, 4, 1, 9, 0, "CLIP"],
        [8, 6, 0, 5, 0, "REGION_SPEC"],
        [9, 5, 1, 7, 1, "STRING"],
        [10, 6, 0, 7, 0, "REGION_SPEC"],
        [11, 6, 3, 14, 0, "IMAGE"],
        [12, 7, 0, 9, 1, "PAGE_COMPILE_PLAN"],
        [13, 8, 0, 10, 3, "IMAGE"],
        [14, 8, 0, 15, 0, "IMAGE"],
        [15, 8, 1, 9, 2, "PANEL_LAYOUT_SPEC"],
        [16, 9, 0, 10, 0, "CONDITIONING"],
        [17, 9, 1, 10, 1, "CONDITIONING"],
        [18, 9, 4, 16, 0, "IMAGE"],
        [19, 10, 0, 11, 1, "CONDITIONING"],
        [20, 10, 1, 11, 2, "CONDITIONING"],
        [21, 11, 0, 12, 0, "LATENT"],
        [22, 12, 0, 13, 0, "IMAGE"],
        [23, 12, 0, 17, 0, "IMAGE"]
    ]

    workflow = {
        "last_node_id": 17,
        "last_link_id": 23,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {},
        "version": 0.4
    }

    out_path = os.path.join(PROJECT_ROOT, "workflows", "17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"[Workflow 17] Generated successfully -> {out_path}")
    return out_path


if __name__ == "__main__":
    build_workflow_17()
