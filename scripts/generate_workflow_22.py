"""
Generate Workflow 22: Single Panel Multi-Scene Same-Cast Oracle (Phase 3E)
==========================================================================
Builds workflows/22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json.

Hostile Stress-Test:
- 1 visible panel (full page / single panel).
- 2 internal semantic scenes (Scene A Left: Conflict/Arguing vs Scene B Right: Friendly/Handshake).
- Recurrent Alice (x2) and Bob (x2) across subscenes within the SAME visible panel.
- Zero directional prompt tokens ("left", "right").
- Impact RegionalSampler + TegakiSinglePanelMultiSceneImpactAdapter.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json")


def build_workflow_22():
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

    # 2. Panel Layout Spec JSON (Single Panel 1024x1024)
    layout_data = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "vertices": [
            {"id": "v0", "x": 0.05, "y": 0.05},
            {"id": "v1", "x": 0.95, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.95},
            {"id": "v3", "x": 0.05, "y": 0.95}
        ],
        "panels": [
            {"id": "p1", "vertex_ids": ["v0", "v1", "v2", "v3"]}
        ]
    }

    nodes = [
        # --- GLOBAL SETUP ---
        # 1: Checkpoint
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
        # 2: Empty Latent
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
        # 3: Global Pos
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
            "widgets_values": ["masterpiece, high quality, manga illustration, split composition, contrasting scenes"]
        },
        # 4: Global Neg
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
            "widgets_values": ["worst quality, low quality, bad anatomy, blurry"]
        },
        # 5: ToBasicPipe
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
        # 6: KSamplerAdvancedProvider
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

        # --- CAST & LAYOUT ---
        # 7: Cast Master
        {
            "id": 7,
            "type": "TegakiMangaCastMaster",
            "pos": [40, 420],
            "size": [360, 480],
            "flags": {},
            "order": 6,
            "mode": 0,
            "outputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "links": [13], "slot_index": 0},
                {"name": "cast_spec_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "selected_character_id", "type": "STRING", "links": None, "slot_index": 2},
                {"name": "character_count", "type": "INT", "links": None, "slot_index": 3}
            ],
            "widgets_values": [
                json.dumps(cast_data, indent=2, ensure_ascii=False)
            ]
        },
        # 8: Panel Layout Editor (1 Panel)
        {
            "id": 8,
            "type": "TegakiMangaPanelLayoutEditor",
            "pos": [440, 420],
            "size": [380, 420],
            "flags": {},
            "order": 7,
            "mode": 0,
            "outputs": [
                {"name": "layout_image", "type": "IMAGE", "links": None, "slot_index": 0},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [14], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [
                1024, 1024, 4, json.dumps(layout_data, indent=2, ensure_ascii=False)
            ]
        },

        # --- HOSTILE MULTI-SCENE ADAPTER ---
        # 9: Single Panel Multi-Scene Impact Adapter
        {
            "id": 9,
            "type": "TegakiSinglePanelMultiSceneImpactAdapter",
            "pos": [860, 480],
            "size": [400, 480],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 14},
                {"name": "cast_spec", "type": "CAST_SPEC", "link": 13},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 11},
                {"name": "clip", "type": "CLIP", "link": 4}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [15], "slot_index": 0},
                {"name": "region_masks", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "preview_image", "type": "IMAGE", "links": [16], "slot_index": 2},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 3}
            ],
            "widgets_values": [
                "school gate, afternoon sunset, dramatic shadows",
                "arguing intensely, both looking away from each other, frustrated expression",
                "school garden, blooming flowers, soft sunlight",
                "friendly handshake, facing each other, happy smiling expression",
                0.50,
                0.05,
                0.25,
                0,
                0,
                0.0,
                "linear"
            ]
        },

        # --- SAMPLING & OUTPUT ---
        # 10: Staging Preview
        {
            "id": 10,
            "type": "PreviewImage",
            "pos": [1300, 80],
            "size": [360, 360],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 16}],
            "widgets_values": []
        },
        # 11: Impact RegionalSampler
        {
            "id": 11,
            "type": "RegionalSampler",
            "pos": [1300, 480],
            "size": [380, 360],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 7},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 12},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 15}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [17], "slot_index": 0}
            ],
            "widgets_values": [
                42, 0, "ignore", 20, 2, 1.0, 10, True, "ratio between", "AUTO", 0.3
            ]
        },
        # 12: VAE Decode
        {
            "id": 12,
            "type": "VAEDecode",
            "pos": [1720, 480],
            "size": [220, 100],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 17},
                {"name": "vae", "type": "VAE", "link": 6}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [18], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 13: Save Image
        {
            "id": 13,
            "type": "SaveImage",
            "pos": [1980, 480],
            "size": [360, 400],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 18}],
            "widgets_values": ["Tegaki/Phase3E/single_panel_multiscene_hostile"]
        }
    ]

    links = [
        [1, 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 3, 0, "CLIP"],
        [3, 1, 1, 4, 0, "CLIP"],
        [4, 1, 1, 9, 3, "CLIP"],
        [5, 1, 2, 5, 2, "VAE"],
        [6, 1, 2, 12, 1, "VAE"],
        [7, 2, 0, 11, 0, "LATENT"],
        [8, 3, 0, 5, 3, "CONDITIONING"],
        [9, 4, 0, 5, 4, "CONDITIONING"],
        [10, 5, 0, 6, 0, "BASIC_PIPE"],
        [11, 6, 0, 9, 2, "KSAMPLER_ADVANCED"],
        [12, 6, 0, 11, 1, "KSAMPLER_ADVANCED"],
        [13, 7, 0, 9, 1, "CAST_SPEC"],
        [14, 8, 1, 9, 0, "PANEL_LAYOUT_SPEC"],
        [15, 9, 0, 11, 2, "REGIONAL_PROMPTS"],
        [16, 9, 2, 10, 0, "IMAGE"],
        [17, 11, 0, 12, 0, "LATENT"],
        [18, 12, 0, 13, 0, "IMAGE"]
    ]

    groups = [
        {"title": "01 GLOBAL & MODEL SETUP", "bounding": [20, 20, 1040, 360], "color": "#2a363b"},
        {"title": "02 CAST & PANEL SPEC", "bounding": [20, 400, 820, 520], "color": "#3f51b5"},
        {"title": "03 HOSTILE MULTI-SCENE ENGINE", "bounding": [850, 420, 420, 560], "color": "#e91e63"},
        {"title": "04 PREVIEW & OUTPUT", "bounding": [1280, 20, 1080, 880], "color": "#4caf50"}
    ]

    workflow = {
        "last_node_id": 13,
        "last_link_id": 18,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "manga_edition": "Phase 3E Hostile Multi-Scene Oracle",
            "experimental": True
        },
        "version": 0.4
    }

    os.makedirs(os.path.dirname(WORKFLOW_FILE), exist_ok=True)
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"[Workflow22] Generated successfully: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_22()
