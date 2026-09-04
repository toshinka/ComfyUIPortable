"""
Generate Workflow 18: Single Region Placement Core vs Impact Oracle (Phase 3D.2)
================================================================================
Builds workflows/18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json.
Contains:
- Unified Checkpoint + Latent + Single-Region TegakiTwoRegionCoupleEditor (A=Top-Left, B=Disabled)
- Branch 1: Core Masked Conditioning (TegakiTwoRegionCoreConditioner + KSampler + VAE + SaveImage)
- Branch 2: Impact RegionalSampler (ToBasicPipe + KSamplerAdvancedProvider + TegakiTwoRegionImpactAdapter + RegionalSampler + VAE + SaveImage)
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json")


def build_workflow_18():
    spec_tl = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": "masterpiece, simple clean outdoor background, full composition",
        "global_negative_prompt": "worst quality, bad anatomy, duplicate subject",
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.05,
                "w": 0.35,
                "h": 0.45
            },
            {
                "id": "B",
                "enabled": False,
                "prompt": "",
                "negative_prompt": "",
                "x": 0.55,
                "y": 0.50,
                "w": 0.35,
                "h": 0.45
            }
        ],
        "metadata": {"oracle_mode": "single_region_placement", "preset": "single_tl"}
    }
    spec_json = json.dumps(spec_tl, indent=2, ensure_ascii=False)

    nodes = [
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
                {"name": "MODEL", "type": "MODEL", "links": [1, 2, 3], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [4, 5, 6, 7], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [8, 9], "slot_index": 2}
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
                {"name": "LATENT", "type": "LATENT", "links": [10, 11], "slot_index": 0}
            ],
            "widgets_values": [832, 1216, 1]
        },
        # 3: Region Editor (Single Region: TL)
        {
            "id": 3,
            "type": "TegakiTwoRegionCoupleEditor",
            "pos": [400, 80],
            "size": [400, 720],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "links": [12, 13], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "combined_preview", "type": "IMAGE", "links": [14], "slot_index": 3},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 4}
            ],
            "widgets_values": [
                832,
                1216,
                "masterpiece, simple clean outdoor background, full composition",
                "worst quality, bad anatomy, duplicate subject",
                "a white dog, full body",
                "",
                "",
                "",
                spec_json
            ]
        },
        # 4: Preview Image
        {
            "id": 4,
            "type": "PreviewImage",
            "pos": [400, 840],
            "size": [400, 360],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 14}
            ],
            "widgets_values": []
        },

        # --- CORE BRANCH (Nodes 5 - 8) ---
        # 5: Core Conditioner
        {
            "id": 5,
            "type": "TegakiTwoRegionCoreConditioner",
            "pos": [860, 80],
            "size": [340, 220],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 4},
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "link": 12}
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": [15], "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": [16], "slot_index": 1},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 3},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 4}
            ],
            "widgets_values": [1.0, 1.0, "default", 0]
        },
        # 6: KSampler (Core)
        {
            "id": 6,
            "type": "KSampler",
            "pos": [1240, 80],
            "size": [320, 480],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "positive", "type": "CONDITIONING", "link": 15},
                {"name": "negative", "type": "CONDITIONING", "link": 16},
                {"name": "latent_image", "type": "LATENT", "link": 10}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [17], "slot_index": 0}
            ],
            "widgets_values": [42, "fixed", 15, 6.0, "euler", "normal", 1.0]
        },
        # 7: VAEDecode (Core)
        {
            "id": 7,
            "type": "VAEDecode",
            "pos": [1600, 80],
            "size": [220, 120],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 17},
                {"name": "vae", "type": "VAE", "link": 8}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [18], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 8: SaveImage (Core)
        {
            "id": 8,
            "type": "SaveImage",
            "pos": [1860, 80],
            "size": [340, 480],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 18}
            ],
            "widgets_values": ["Tegaki/Phase3D2/SingleRegion/Core"]
        },

        # --- IMPACT BRANCH (Nodes 9 - 19) ---
        # 9: CLIPTextEncode (Global Pos)
        {
            "id": 9,
            "type": "CLIPTextEncode",
            "pos": [860, 360],
            "size": [340, 100],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 5}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [19], "slot_index": 0}
            ],
            "widgets_values": ["masterpiece, simple clean outdoor background, full composition"]
        },
        # 10: CLIPTextEncode (Global Neg)
        {
            "id": 10,
            "type": "CLIPTextEncode",
            "pos": [860, 500],
            "size": [340, 100],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 6}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [20, 21], "slot_index": 0}
            ],
            "widgets_values": ["worst quality, bad anatomy, duplicate subject"]
        },
        # 11: CLIPTextEncode (Region A Pos)
        {
            "id": 11,
            "type": "CLIPTextEncode",
            "pos": [860, 640],
            "size": [340, 100],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 7}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [22], "slot_index": 0}
            ],
            "widgets_values": ["a white dog, full body"]
        },
        # 12: ToBasicPipe (Global)
        {
            "id": 12,
            "type": "ToBasicPipe",
            "pos": [1240, 600],
            "size": [260, 140],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 2},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": None},
                {"name": "positive", "type": "CONDITIONING", "link": 19},
                {"name": "negative", "type": "CONDITIONING", "link": 20}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [23], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 13: ToBasicPipe (Region A)
        {
            "id": 13,
            "type": "ToBasicPipe",
            "pos": [1240, 780],
            "size": [260, 140],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 3},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": None},
                {"name": "positive", "type": "CONDITIONING", "link": 22},
                {"name": "negative", "type": "CONDITIONING", "link": 21}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [24], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 14: KSamplerAdvancedProvider (Base)
        {
            "id": 14,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 600],
            "size": [280, 140],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 23}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [25], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 15: KSamplerAdvancedProvider (Region A)
        {
            "id": 15,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 780],
            "size": [280, 140],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 24}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [26], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 16: TegakiTwoRegionImpactAdapter
        {
            "id": 16,
            "type": "TegakiTwoRegionImpactAdapter",
            "pos": [1860, 600],
            "size": [320, 200],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "link": 13},
                {"name": "sampler_A", "type": "KSAMPLER_ADVANCED", "link": 26},
                {"name": "sampler_B", "type": "KSAMPLER_ADVANCED", "link": None}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [27], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 3}
            ],
            "widgets_values": [0, 0.0, "linear"]
        },
        # 17: RegionalSampler
        {
            "id": 17,
            "type": "RegionalSampler",
            "pos": [2220, 600],
            "size": [340, 520],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 11},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 25},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 27}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [28], "slot_index": 0}
            ],
            "widgets_values": [42, 0, "ignore", 15, 2, 1.0, 10, True, "ratio between", "AUTO", 0.3]
        },
        # 18: VAEDecode (Impact)
        {
            "id": 18,
            "type": "VAEDecode",
            "pos": [2600, 600],
            "size": [220, 120],
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 28},
                {"name": "vae", "type": "VAE", "link": 9}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [29], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 19: SaveImage (Impact)
        {
            "id": 19,
            "type": "SaveImage",
            "pos": [2860, 600],
            "size": [340, 480],
            "flags": {},
            "order": 18,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 29}
            ],
            "widgets_values": ["Tegaki/Phase3D2/SingleRegion/Impact"]
        }
    ]

    links = [
        [1, 1, 0, 6, 0, "MODEL"],
        [2, 1, 0, 12, 0, "MODEL"],
        [3, 1, 0, 13, 0, "MODEL"],
        [4, 1, 1, 5, 0, "CLIP"],
        [5, 1, 1, 9, 0, "CLIP"],
        [6, 1, 1, 10, 0, "CLIP"],
        [7, 1, 1, 11, 0, "CLIP"],
        [8, 1, 2, 7, 1, "VAE"],
        [9, 1, 2, 18, 1, "VAE"],
        [10, 2, 0, 6, 3, "LATENT"],
        [11, 2, 0, 17, 0, "LATENT"],
        [12, 3, 0, 5, 1, "TWO_REGION_SPEC"],
        [13, 3, 0, 16, 0, "TWO_REGION_SPEC"],
        [14, 3, 3, 4, 0, "IMAGE"],
        [15, 5, 0, 6, 1, "CONDITIONING"],
        [16, 5, 1, 6, 2, "CONDITIONING"],
        [17, 6, 0, 7, 0, "LATENT"],
        [18, 7, 0, 8, 0, "IMAGE"],
        [19, 9, 0, 12, 3, "CONDITIONING"],
        [20, 10, 0, 12, 4, "CONDITIONING"],
        [21, 10, 0, 13, 4, "CONDITIONING"],
        [22, 11, 0, 13, 3, "CONDITIONING"],
        [23, 12, 0, 14, 0, "BASIC_PIPE"],
        [24, 13, 0, 15, 0, "BASIC_PIPE"],
        [25, 14, 0, 17, 1, "KSAMPLER_ADVANCED"],
        [26, 15, 0, 16, 1, "KSAMPLER_ADVANCED"],
        [27, 16, 0, 17, 2, "REGIONAL_PROMPTS"],
        [28, 17, 0, 18, 0, "LATENT"],
        [29, 18, 0, 19, 0, "IMAGE"]
    ]

    workflow = {
        "last_node_id": 19,
        "last_link_id": 29,
        "nodes": nodes,
        "links": links
    }

    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"[Workflow 18] Generated: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_18()
