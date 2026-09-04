"""
Generate Workflow 23: Manga Progressive Panel Authoring Impact (Phase 3F)
========================================================================
Builds workflows/23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json.

Architecture:
- 01 GLOBAL: CheckpointLoader, Latent, Global Prompts, ToBasicPipe (clip connected), KSamplerAdvancedProvider
- 02 CAST: TegakiMangaCastMaster
- 03 PANEL CONTENT: TegakiMangaPanelContentEditor (Simple Panel default, 4 panels)
- 04 PANEL LAYOUT: TegakiMangaPanelLayoutEditor (4-grid layout)
- 05 CHARACTER STAGING: TegakiMangaCharacterStagingEditor + Preview
- 06 GENERATE: Final Output (SaveImage)
- Protected INTERNAL ENGINE group: PageCompiler, ImpactRegionalAdapter, RegionalSampler (12 widgets), VAEDecode
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.panel_content_editor import DEFAULT_RECURRENT_PANELS_CONTENT

WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json")


def build_workflow_23():
    # 1. Cast Data
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

    # 2. Panel Content Data (4 panels simple recurrent cast)
    panel_content_json = json.dumps(DEFAULT_RECURRENT_PANELS_CONTENT, indent=2, ensure_ascii=False)

    # 3. Panel Layout Data (4-Grid)
    layout_data = get_default_panel_layout_spec(1024, 1024, preset="4_grid")
    layout_json = json.dumps(layout_data, indent=2, ensure_ascii=False)

    nodes = [
        # --- 01 GLOBAL PIPELINE ---
        # Node 1: Checkpoint
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
                {"name": "CLIP", "type": "CLIP", "links": [2, 3, 20, 24], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [4, 18], "slot_index": 2}
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
                {"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}
            ],
            "widgets_values": [1024, 1024, 1]
        },
        # Node 3: CLIPTextEncode Positive
        {
            "id": 3,
            "type": "CLIPTextEncode",
            "pos": [400, 80],
            "size": [340, 100],
            "flags": {},
            "order": 2,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "slot_index": 0}],
            "widgets_values": ["masterpiece, high quality, 4-panel manga page, comic strip"]
        },
        # Node 4: CLIPTextEncode Negative
        {
            "id": 4,
            "type": "CLIPTextEncode",
            "pos": [400, 240],
            "size": [340, 100],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [7], "slot_index": 0}],
            "widgets_values": ["worst quality, low quality, bad anatomy, blurry, duplicate character"]
        },
        # Node 5: ToBasicPipe (CLIP CONNECTED)
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
                {"name": "clip", "type": "CLIP", "link": 20},
                {"name": "vae", "type": "VAE", "link": 4},
                {"name": "positive", "type": "CONDITIONING", "link": 6},
                {"name": "negative", "type": "CONDITIONING", "link": 7}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [8], "slot_index": 0}
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
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 8},
                {"name": "sampler_opt", "type": "SAMPLER", "link": None},
                {"name": "scheduler_func_opt", "type": "SCHEDULER_FUNC", "link": None}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [9, 10], "slot_index": 0}
            ],
            "widgets_values": [7.0, "euler", "normal", 1.0]
        },

        # --- 02 CAST MASTER ---
        # Node 7: Cast Master
        {
            "id": 7,
            "type": "TegakiMangaCastMaster",
            "pos": [40, 480],
            "size": [360, 480],
            "flags": {},
            "order": 6,
            "mode": 0,
            "outputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "links": [21], "slot_index": 0},
                {"name": "cast_spec_json", "type": "STRING", "links": [11], "slot_index": 1},
                {"name": "selected_character_id", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "character_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [cast_json]
        },

        # --- 03 PANEL CONTENT ---
        # Node 8: Panel Content Editor
        {
            "id": 8,
            "type": "TegakiMangaPanelContentEditor",
            "pos": [440, 480],
            "size": [420, 560],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "link": 21}
            ],
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [12], "slot_index": 0},
                {"name": "content_data_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "panel_count", "type": "INT", "links": None, "slot_index": 2}
            ],
            "widgets_values": [panel_content_json]
        },

        # --- 04 PANEL LAYOUT ---
        # Node 9: Panel Layout Editor
        {
            "id": 9,
            "type": "TegakiMangaPanelLayoutEditor",
            "pos": [900, 480],
            "size": [380, 440],
            "flags": {},
            "order": 8,
            "mode": 0,
            "outputs": [
                {"name": "layout_image", "type": "IMAGE", "links": None, "slot_index": 0},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [13, 14], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [1024, 1024, 4, layout_json]
        },

        # --- 05 CHARACTER STAGING ---
        # Node 10: Character Staging Editor
        {
            "id": 10,
            "type": "TegakiMangaCharacterStagingEditor",
            "pos": [1320, 480],
            "size": [400, 480],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 12},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 13}
            ],
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [15], "slot_index": 0},
                {"name": "staging_preview", "type": "IMAGE", "links": [22], "slot_index": 1},
                {"name": "staging_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": ["{}"]
        },

        # Node 13: Staging Preview Image
        {
            "id": 13,
            "type": "PreviewImage",
            "pos": [1760, 480],
            "size": [360, 360],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 22}]
        },

        # --- INTERNAL ENGINE (PROTECTED) ---
        # Node 11: Page Compiler
        {
            "id": 11,
            "type": "TegakiMangaPageCompiler",
            "pos": [1280, 80],
            "size": [340, 200],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 15},
                {"name": "cast_spec", "type": "STRING", "link": 11}
            ],
            "outputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "links": [16], "slot_index": 0},
                {"name": "page_compile_plan_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "global_loras_text", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "active_panels_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [cast_json, ""]
        },
        # Node 12: Impact Regional Adapter
        {
            "id": 12,
            "type": "TegakiMangaImpactRegionalAdapter",
            "pos": [1660, 80],
            "size": [340, 220],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "link": 16},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 14},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 9},
                {"name": "clip", "type": "CLIP", "link": 24}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [17], "slot_index": 0},
                {"name": "staging_image", "type": "IMAGE", "links": None, "slot_index": 1}
            ],
            "widgets_values": ["scene_first", "scene_composed", True, False, 0]
        },
        # Node 14: RegionalSampler (12 WIDGETS PARITY)
        {
            "id": 14,
            "type": "RegionalSampler",
            "pos": [2040, 80],
            "size": [360, 360],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 5},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 10},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 17}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}
            ],
            "widgets_values": [
                42,
                "fixed",
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
        # Node 15: VAEDecode
        {
            "id": 15,
            "type": "VAEDecode",
            "pos": [2440, 80],
            "size": [240, 100],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 19},
                {"name": "vae", "type": "VAE", "link": 18}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [23], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # Node 16: SaveImage (06 GENERATE)
        {
            "id": 16,
            "type": "SaveImage",
            "pos": [2160, 480],
            "size": [380, 440],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 23}],
            "widgets_values": ["Tegaki/Phase3F/wf23_progressive_4panel"]
        }
    ]

    links = [
        # Model & Pipe
        [1, 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 3, 0, "CLIP"],
        [3, 1, 1, 4, 0, "CLIP"],
        [4, 1, 2, 5, 2, "VAE"],
        [5, 2, 0, 14, 0, "LATENT"],
        [6, 3, 0, 5, 3, "CONDITIONING"],
        [7, 4, 0, 5, 4, "CONDITIONING"],
        [8, 5, 0, 6, 0, "BASIC_PIPE"],
        [9, 6, 0, 12, 2, "KSAMPLER_ADVANCED"],
        [10, 6, 0, 14, 1, "KSAMPLER_ADVANCED"],
        # Progressive authoring links
        [11, 7, 1, 11, 1, "STRING"],
        [12, 8, 0, 10, 0, "REGION_SPEC"],
        [13, 9, 1, 10, 1, "PANEL_LAYOUT_SPEC"],
        [14, 9, 1, 12, 1, "PANEL_LAYOUT_SPEC"],
        [15, 10, 0, 11, 0, "REGION_SPEC"],
        [16, 11, 0, 12, 0, "PAGE_COMPILE_PLAN"],
        [17, 12, 0, 14, 2, "REGIONAL_PROMPTS"],
        [18, 1, 2, 15, 1, "VAE"],
        [19, 14, 0, 15, 0, "LATENT"],
        [20, 1, 1, 5, 1, "CLIP"],
        [21, 7, 0, 8, 0, "CAST_SPEC"],
        [22, 10, 1, 13, 0, "IMAGE"],
        [23, 15, 0, 16, 0, "IMAGE"],
        [24, 1, 1, 12, 3, "CLIP"],
    ]

    groups = [
        {
            "title": "01 GLOBAL — MODEL / PIPE / BASE SAMPLER",
            "bounding": [20, 20, 1040, 430],
            "color": "#3f3f46",
            "font_size": 22
        },
        {
            "title": "02 CAST — RECURRENT CHARACTER MASTER",
            "bounding": [20, 450, 400, 530],
            "color": "#2563eb",
            "font_size": 22
        },
        {
            "title": "03 PANEL CONTENT — SCENE & ATTENDANCE",
            "bounding": [430, 450, 440, 610],
            "color": "#ea580c",
            "font_size": 22
        },
        {
            "title": "04 PANEL LAYOUT — 4-GRID GEOMETRY",
            "bounding": [880, 450, 420, 490],
            "color": "#16a34a",
            "font_size": 22
        },
        {
            "title": "05 CHARACTER STAGING & PREVIEW",
            "bounding": [1310, 450, 820, 530],
            "color": "#9333ea",
            "font_size": 22
        },
        {
            "title": "06 GENERATE — FINAL OUTPUT",
            "bounding": [2150, 450, 400, 490],
            "color": "#0d9488",
            "font_size": 22
        },
        {
            "title": "INTERNAL ENGINE — DO NOT TOUCH",
            "bounding": [1260, 20, 1440, 430],
            "color": "#991b1b",
            "font_size": 22
        }
    ]

    workflow = {
        "last_node_id": 16,
        "last_link_id": len(links),
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "title": "23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT",
            "description": "Phase 3F Progressive Panel Authoring with Simple First flow and Impact Backend."
        },
        "version": 0.4
    }

    os.makedirs(os.path.dirname(WORKFLOW_FILE), exist_ok=True)
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"[Workflow 23] Successfully generated: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_23()
