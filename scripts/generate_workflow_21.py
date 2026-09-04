"""
Generate Workflow 21: Manga Impact Recurrent Cast POC (Phase 3E)
================================================================
Builds workflows/21_MANGA_IMPACT_RECURRENT_CAST_POC.json.

Integrates:
- Tegaki Manga Cast Master (Alice & Bob definitions)
- Tegaki Manga Region Editor (4-Panel Region Spec with Recurrent Alice & Bob)
- Tegaki Manga Page Compiler (Compiles PAGE_COMPILE_PLAN)
- Tegaki Manga Panel Layout Editor (4-Grid Manga Panels, 1024x1024)
- Tegaki Manga Impact Regional Adapter (Dynamic N-Region Engine)
- Impact Pack RegionalSampler + SDXL (waiIllustriousSDXL_v170)
- Progressive Authoring Layout:
  01 GLOBAL -> 02 CAST -> 03 PANEL CONTENT -> 04 PANEL LAYOUT -> 05 STAGING PREVIEW -> 06 GENERATE
  Protected "INTERNAL ENGINE — DO NOT TOUCH" group for execution nodes.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.cast_master import get_default_cast_spec

WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "21_MANGA_IMPACT_RECURRENT_CAST_POC.json")


def build_workflow_21():
    # 1. Cast Spec JSON (Alice & Bob)
    cast_data = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes, school uniform, white shirt, red necktie, pleated skirt",
                "negative_prompt": "blurry, low quality, bad anatomy, duplicate girl",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short black hair, dark eyes, school uniform, black gakuran jacket, male student",
                "negative_prompt": "blurry, low quality, bad anatomy, duplicate boy",
                "loras": []
            }
        ]
    }
    cast_json = json.dumps(cast_data, indent=2, ensure_ascii=False)

    # 2. Panel Layout Spec JSON (4-Grid 1024x1024)
    layout_data = get_default_panel_layout_spec(1024, 1024, preset="4_grid")
    layout_json = json.dumps(layout_data, indent=2, ensure_ascii=False)

    # 3. 4-Panel Region Spec with Recurrent Alice & Bob instances
    region_spec_data = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "panel_count": 4,
        "global_prompt": "manga page, 4-panel comic, sequence of events, high quality",
        "global_negative_prompt": "blurry, low quality, bad anatomy",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.05, "y": 0.05, "w": 0.43, "h": 0.43,
                "prompt": "simple school garden, sunny afternoon, outdoor stone path",
                "negative_prompt": "blurry",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "smiling happily, friendly handshake, reaching hand forward",
                        "area": {"x": 0.08, "y": 0.15, "w": 0.45, "h": 0.80}
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "smiling warmly, friendly handshake, shaking hands",
                        "area": {"x": 0.47, "y": 0.15, "w": 0.45, "h": 0.80}
                    }
                ]
            },
            {
                "id": 2,
                "name": "KOMA 2",
                "enabled": True,
                "x": 0.52, "y": 0.05, "w": 0.43, "h": 0.43,
                "prompt": "school flower bed, colorful blooming flowers, soil, sunny morning",
                "negative_prompt": "blurry",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "watering flowers with a watering can, cheerful expression",
                        "area": {"x": 0.15, "y": 0.12, "w": 0.70, "h": 0.82}
                    }
                ]
            },
            {
                "id": 3,
                "name": "KOMA 3",
                "enabled": True,
                "x": 0.05, "y": 0.52, "w": 0.43, "h": 0.43,
                "prompt": "school garden stone path, trees in background",
                "negative_prompt": "blurry",
                "characters": [
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "carrying a large potted green plant with both hands, focused expression",
                        "area": {"x": 0.15, "y": 0.12, "w": 0.70, "h": 0.82}
                    }
                ]
            },
            {
                "id": 4,
                "name": "KOMA 4",
                "enabled": True,
                "x": 0.52, "y": 0.52, "w": 0.43, "h": 0.43,
                "prompt": "school iron gate in sunset, dramatic evening light, long shadows",
                "negative_prompt": "blurry",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "arguing, angry pout, looking away to the left with arms crossed",
                        "area": {"x": 0.08, "y": 0.15, "w": 0.45, "h": 0.80}
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "arguing, annoyed expression, looking away to the right",
                        "area": {"x": 0.47, "y": 0.15, "w": 0.45, "h": 0.80}
                    }
                ]
            }
        ]
    }
    region_spec_json = json.dumps(region_spec_data, indent=2, ensure_ascii=False)

    nodes = [
        # --- 01 GLOBAL & MODEL SETUP ---
        # Node 1: CheckpointLoaderSimple
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
                {"name": "CLIP", "type": "CLIP", "links": [2, 3, 4], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [5, 6], "slot_index": 2}
            ],
            "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
        },
        # Node 2: EmptyLatentImage
        {
            "id": 2,
            "type": "EmptyLatentImage",
            "pos": [40, 240],
            "size": [320, 110],
            "flags": {},
            "order": 1,
            "mode": 0,
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}
            ],
            "widgets_values": [1024, 1024, 1]
        },
        # Node 3: Global Positive
        {
            "id": 3,
            "type": "CLIPTextEncode",
            "pos": [400, 80],
            "size": [340, 100],
            "flags": {},
            "order": 2,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [8], "slot_index": 0}],
            "widgets_values": ["masterpiece, high quality, manga page, 4-panel comic, story sequence"]
        },
        # Node 4: Global Negative
        {
            "id": 4,
            "type": "CLIPTextEncode",
            "pos": [400, 220],
            "size": [340, 100],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [9], "slot_index": 0}],
            "widgets_values": ["worst quality, low quality, bad anatomy, blurry, duplicate character"]
        },
        # Node 5: ToBasicPipe
        {
            "id": 5,
            "type": "ToBasicPipe",
            "pos": [780, 80],
            "size": [260, 140],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 5},
                {"name": "positive", "type": "CONDITIONING", "link": 8},
                {"name": "negative", "type": "CONDITIONING", "link": 9}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [10], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # Node 6: KSamplerAdvancedProvider
        {
            "id": 6,
            "type": "KSamplerAdvancedProvider",
            "pos": [780, 260],
            "size": [260, 180],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 10},
                {"name": "sampler_opt", "type": "SAMPLER", "link": None},
                {"name": "scheduler_func_opt", "type": "SCHEDULER_FUNC", "link": None}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [11, 12], "slot_index": 0}
            ],
            "widgets_values": [7.0, "euler", "normal", 1.0]
        },

        # --- 02 CHARACTER CAST MASTER ---
        # Node 7: Cast Master
        {
            "id": 7,
            "type": "TegakiMangaCastMaster",
            "pos": [40, 420],
            "size": [360, 480],
            "flags": {},
            "order": 6,
            "mode": 0,
            "outputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "links": None, "slot_index": 0},
                {"name": "cast_spec_json", "type": "STRING", "links": [13], "slot_index": 1},
                {"name": "selected_character_id", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "character_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [
                cast_json
            ]
        },

        # --- 03 MANGA PANEL CONTENTS & REGION EDITOR ---
        # Node 8: Region Editor
        {
            "id": 8,
            "type": "TegakiMangaRegionEditor",
            "pos": [440, 420],
            "size": [380, 480],
            "flags": {},
            "order": 7,
            "mode": 0,
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [14], "slot_index": 0},
                {"name": "region_spec_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "global_prompt", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "preview_image", "type": "IMAGE", "links": None, "slot_index": 3},
                {"name": "mask_batch", "type": "MASK", "links": None, "slot_index": 4},
                {"name": "active_region_ids_json", "type": "STRING", "links": None, "slot_index": 5}
            ],
            "widgets_values": [
                4,
                1024,
                1024,
                "manga page, 4-panel comic",
                region_spec_json
            ]
        },
        # Node 9: Page Compiler
        {
            "id": 9,
            "type": "TegakiMangaPageCompiler",
            "pos": [860, 420],
            "size": [380, 480],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 14},
                {"name": "cast_spec", "type": "STRING", "link": 13}
            ],
            "outputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "links": [15], "slot_index": 0},
                {"name": "page_compile_plan_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "global_loras_text", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "active_panels_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [cast_json, ""]
        },

        # --- 04 PANEL GEOMETRY LAYOUT ---
        # Node 10: Panel Layout Editor
        {
            "id": 10,
            "type": "TegakiMangaPanelLayoutEditor",
            "pos": [1280, 420],
            "size": [380, 420],
            "flags": {},
            "order": 9,
            "mode": 0,
            "outputs": [
                {"name": "layout_image", "type": "IMAGE", "links": None, "slot_index": 0},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [16], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [
                1024,
                1024,
                4,
                layout_json
            ]
        },

        # --- 05 & INTERNAL ENGINE: REGIONAL ADAPTER & SAMPLER ---
        # Node 11: Tegaki Manga Impact Regional Adapter
        {
            "id": 11,
            "type": "TegakiMangaImpactRegionalAdapter",
            "pos": [1700, 80],
            "size": [380, 360],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "link": 15},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 16},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 11},
                {"name": "clip", "type": "CLIP", "link": 4}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [17], "slot_index": 0},
                {"name": "region_masks", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "preview_image", "type": "IMAGE", "links": [18], "slot_index": 2},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 3}
            ],
            "widgets_values": [
                "scene_first",
                "scene_composed",
                True,
                False,
                0,
                0,
                0.0,
                "linear"
            ]
        },
        # Node 12: Staging Preview
        {
            "id": 12,
            "type": "PreviewImage",
            "pos": [2120, 80],
            "size": [360, 360],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 18}
            ],
            "widgets_values": []
        },
        # Node 13: Impact RegionalSampler
        {
            "id": 13,
            "type": "RegionalSampler",
            "pos": [1700, 480],
            "size": [380, 360],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 7},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 12},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 17}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}
            ],
            "widgets_values": [
                42,
                0,
                "ignore",
                20,
                2,
                1.0,
                10,
                True,
                "ratio between",
                "AUTO",
                0.3
            ]
        },
        # Node 14: VAE Decode
        {
            "id": 14,
            "type": "VAEDecode",
            "pos": [2120, 480],
            "size": [220, 100],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 19},
                {"name": "vae", "type": "VAE", "link": 6}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [20], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # Node 15: Save Image (06 GENERATE)
        {
            "id": 15,
            "type": "SaveImage",
            "pos": [2380, 480],
            "size": [360, 400],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 20}
            ],
            "widgets_values": ["Tegaki/Phase3E/manga_recurrent_cast_4panel"]
        }
    ]

    links = [
        [1, 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 3, 0, "CLIP"],
        [3, 1, 1, 4, 0, "CLIP"],
        [4, 1, 1, 11, 3, "CLIP"],
        [5, 1, 2, 5, 2, "VAE"],
        [6, 1, 2, 14, 1, "VAE"],
        [7, 2, 0, 13, 0, "LATENT"],
        [8, 3, 0, 5, 3, "CONDITIONING"],
        [9, 4, 0, 5, 4, "CONDITIONING"],
        [10, 5, 0, 6, 0, "BASIC_PIPE"],
        [11, 6, 0, 11, 2, "KSAMPLER_ADVANCED"],
        [12, 6, 0, 13, 1, "KSAMPLER_ADVANCED"],
        [13, 7, 1, 9, 1, "STRING"],
        [14, 8, 0, 9, 0, "REGION_SPEC"],
        [15, 9, 0, 11, 0, "PAGE_COMPILE_PLAN"],
        [16, 10, 1, 11, 1, "PANEL_LAYOUT_SPEC"],
        [17, 11, 0, 13, 2, "REGIONAL_PROMPTS"],
        [18, 11, 2, 12, 0, "IMAGE"],
        [19, 13, 0, 14, 0, "LATENT"],
        [20, 14, 0, 15, 0, "IMAGE"]
    ]

    groups = [
        {"title": "01 GLOBAL & MODEL SETUP", "bounding": [20, 20, 1040, 360], "color": "#2a363b"},
        {"title": "02 CHARACTER CAST MASTER", "bounding": [20, 400, 390, 520], "color": "#3f51b5"},
        {"title": "03 MANGA PANEL CONTENTS", "bounding": [420, 400, 830, 520], "color": "#009688"},
        {"title": "04 PANEL GEOMETRY LAYOUT", "bounding": [1260, 400, 410, 520], "color": "#ff9800"},
        {"title": "05 REGIONAL STAGING PREVIEW", "bounding": [2100, 20, 400, 430], "color": "#4caf50"},
        {"title": "06 FINAL GENERATION OUTPUT", "bounding": [2100, 460, 660, 450], "color": "#e91e63"},
        {"title": "INTERNAL ENGINE — DO NOT TOUCH", "bounding": [1680, 20, 410, 840], "color": "#607d8b"}
    ]

    workflow = {
        "last_node_id": 15,
        "last_link_id": 20,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "manga_edition": "Phase 3E Recurrent Cast POC",
            "progressive_authoring": True
        },
        "version": 0.4
    }

    os.makedirs(os.path.dirname(WORKFLOW_FILE), exist_ok=True)
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"[Workflow21] Generated successfully: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_21()
