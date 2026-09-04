"""
Generate Phase 3H Progressive Authoring Causality Workflows (33 & 34)
====================================================================
Generates:
- 33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT.json
- 34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT.json

Verifies:
- The production authoring pipeline (Cast -> Panel Content -> Character Staging -> Impact)
  causally controls final character placement via Character Staging geometry alone.
- Workflow 33 places Alice on Left [0.05, 0.15, 0.42, 0.70] and Bob on Right [0.53, 0.15, 0.42, 0.70].
- Workflow 34 swaps Staging geometry: Alice on Right [0.53, 0.15, 0.42, 0.70] and Bob on Left [0.05, 0.15, 0.42, 0.70].
- All other parameters (prompts, seed 42, sampler, scene) remain 100% invariant with NO directional words.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec

WORKFLOWS_DIR = os.path.join(PROJECT_ROOT, "workflows")

GLOBAL_STYLE = "manga illustration, monochrome expressive linework, high quality"
SCENE_PROMPT = f"{GLOBAL_STYLE}, simple school courtyard, two students standing"
GLOBAL_NEGATIVE = "worst quality, low quality, bad anatomy, blurry"


def build_authoring_causality_workflow(
    wf_filename: str,
    title: str,
    description: str,
    save_prefix: str,
    alice_area: list,
    bob_area: list
):
    # 1. Cast Master Data
    cast_data = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde hair, twin tails, blue eyes, school uniform, white shirt, red necktie, pleated skirt",
                "negative_prompt": "worst quality, low quality, bad anatomy, duplicate girl",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short black hair, dark eyes, school uniform, black gakuran jacket, male student",
                "negative_prompt": "worst quality, low quality, bad anatomy, duplicate boy",
                "loras": []
            }
        ]
    }
    cast_json = json.dumps(cast_data, indent=2, ensure_ascii=False)

    # 2. Panel Content Data (1 visible panel, both attending, acting calmly)
    panel_content_data = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "panel_count": 1,
        "global_prompt": "manga illustration, monochrome expressive linework, high quality",
        "global_negative_prompt": GLOBAL_NEGATIVE,
        "panels": [
            {
                "id": 1,
                "name": "Panel 1",
                "enabled": True,
                "prompt": SCENE_PROMPT,
                "negative_prompt": "blurry",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "standing calmly",
                        "negative_prompt_override": "",
                        "area": alice_area
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "standing calmly",
                        "negative_prompt_override": "",
                        "area": bob_area
                    }
                ],
                "subscenes": []
            }
        ]
    }
    panel_content_json = json.dumps(panel_content_data, indent=2, ensure_ascii=False)

    # 3. Panel Layout Data (1 visible panel full layout)
    layout_data = get_default_panel_layout_spec(1024, 1024, preset="1_full")
    layout_json = json.dumps(layout_data, indent=2, ensure_ascii=False)

    # 4. Character Staging Overrides (The Causal Variable)
    staging_overrides = {
        "1": {
            "char_alice": {
                "area": alice_area
            },
            "char_bob": {
                "area": bob_area
            }
        },
        "panel_1": {
            "char_alice": {
                "area": alice_area
            },
            "char_bob": {
                "area": bob_area
            }
        }
    }
    staging_overrides_json = json.dumps(staging_overrides, indent=2, ensure_ascii=False)

    nodes = [
        # --- 01 GLOBAL PIPELINE ---
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
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}],
            "widgets_values": [1024, 1024, 1]
        },
        # Node 3: CLIPTextEncode Global Positive
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
            "widgets_values": [SCENE_PROMPT]
        },
        # Node 4: CLIPTextEncode Global Negative
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
            "widgets_values": [GLOBAL_NEGATIVE]
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
            "outputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "links": [8], "slot_index": 0}],
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
            "outputs": [{"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [9], "slot_index": 0}],
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
            "inputs": [{"name": "cast_spec", "type": "CAST_SPEC", "link": 21}],
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [12], "slot_index": 0},
                {"name": "content_data_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "panel_count", "type": "INT", "links": None, "slot_index": 2}
            ],
            "widgets_values": [panel_content_json]
        },

        # --- 04 PANEL LAYOUT ---
        # Node 9: Panel Layout Editor (1-Full)
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
            "widgets_values": [1024, 1024, 1, layout_json]
        },

        # --- 05 CHARACTER STAGING ---
        # Node 10: Character Staging Editor (Transactional Overrides)
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
            "widgets_values": [staging_overrides_json]
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
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 9},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 17}
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}],
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
            "size": [220, 120],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 19},
                {"name": "vae", "type": "VAE", "link": 18}
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [23], "slot_index": 0}],
            "widgets_values": []
        },

        # --- 06 GENERATE / OUTPUT ---
        # Node 16: SaveImage
        {
            "id": 16,
            "type": "SaveImage",
            "pos": [2700, 80],
            "size": [360, 440],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 23}],
            "widgets_values": [save_prefix]
        }
    ]

    links = [
        [1, 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 3, 0, "CLIP"],
        [3, 1, 1, 4, 0, "CLIP"],
        [4, 1, 2, 5, 2, "VAE"],
        [5, 2, 0, 14, 0, "LATENT"],
        [6, 3, 0, 5, 3, "CONDITIONING"],
        [7, 4, 0, 5, 4, "CONDITIONING"],
        [8, 5, 0, 6, 0, "BASIC_PIPE"],
        [9, 6, 0, 12, 2, "KSAMPLER_ADVANCED"],
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
        [24, 1, 1, 12, 3, "CLIP"]
    ]

    workflow_json = {
        "last_node_id": 16,
        "last_link_id": 24,
        "nodes": nodes,
        "links": links,
        "groups": [
            {
                "title": "01 GLOBAL PIPELINE",
                "bounding": [20, 20, 1040, 440],
                "color": "#3f3f46",
                "font_size": 22
            },
            {
                "title": "02 CAST MASTER",
                "bounding": [20, 470, 400, 580],
                "color": "#9333ea",
                "font_size": 22
            },
            {
                "title": "03 PANEL CONTENT",
                "bounding": [430, 470, 440, 580],
                "color": "#eab308",
                "font_size": 22
            },
            {
                "title": "04 PANEL LAYOUT",
                "bounding": [880, 470, 420, 580],
                "color": "#06b6d4",
                "font_size": 22
            },
            {
                "title": "05 CHARACTER STAGING",
                "bounding": [1310, 470, 830, 580],
                "color": "#f97316",
                "font_size": 22
            },
            {
                "title": "INTERNAL REGIONAL ENGINE",
                "bounding": [1080, 20, 1340, 440],
                "color": "#2563eb",
                "font_size": 22
            },
            {
                "title": "06 GENERATE",
                "bounding": [2430, 20, 650, 520],
                "color": "#16a34a",
                "font_size": 22
            }
        ],
        "config": {},
        "extra": {
            "title": title,
            "description": description
        },
        "version": 0.4
    }

    out_path = os.path.join(WORKFLOWS_DIR, wf_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow_json, f, indent=2, ensure_ascii=False)
    print(f"[Generated] {wf_filename}")


def generate_all_authoring_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)

    # Alice Left, Bob Right
    area_alice_left = {"x": 0.05, "y": 0.15, "w": 0.42, "h": 0.70}
    area_bob_right = {"x": 0.53, "y": 0.15, "w": 0.42, "h": 0.70}

    build_authoring_causality_workflow(
        wf_filename="33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT.json",
        title="33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT",
        description="Phase 3H Progressive Authoring Causality: 1 Panel, Alice Left [0.05, 0.15, 0.42, 0.70], Bob Right [0.53, 0.15, 0.42, 0.70] via Character Staging overrides alone (seed 42).",
        save_prefix="Phase3H_Authoring_33_AliceLeft_BobRight",
        alice_area=area_alice_left,
        bob_area=area_bob_right
    )

    # Alice Right, Bob Left (SWAP)
    area_alice_right = {"x": 0.53, "y": 0.15, "w": 0.42, "h": 0.70}
    area_bob_left = {"x": 0.05, "y": 0.15, "w": 0.42, "h": 0.70}

    build_authoring_causality_workflow(
        wf_filename="34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT.json",
        title="34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT",
        description="Phase 3H Progressive Authoring Causality: 1 Panel, Alice Right [0.53, 0.15, 0.42, 0.70], Bob Left [0.05, 0.15, 0.42, 0.70] via Character Staging overrides alone (seed 42, exact swap).",
        save_prefix="Phase3H_Authoring_34_AliceRight_BobLeft",
        alice_area=area_alice_right,
        bob_area=area_bob_left
    )


if __name__ == "__main__":
    generate_all_authoring_workflows()
