"""
Generate Workflow 19: Two Region Semantic Binding Oracle (Phase 3D.2)
====================================================================
Builds workflows/19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json.
Uses Impact RegionalSampler with:
- TegakiTwoRegionCoupleEditor (A=White Dog, B=Black Cat)
- Region A & Region B KSamplerAdvancedProviders
- TegakiTwoRegionImpactAdapter
- RegionalSampler + VAEDecode + SaveImage
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json")


def build_workflow_19():
    spec_lr = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": "simple park background, two subjects",
        "global_negative_prompt": "worst quality, bad anatomy, duplicate subject",
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.10,
                "w": 0.42,
                "h": 0.80
            },
            {
                "id": "B",
                "enabled": True,
                "prompt": "a black cat, full body",
                "negative_prompt": "",
                "x": 0.53,
                "y": 0.10,
                "w": 0.42,
                "h": 0.80
            }
        ],
        "metadata": {"oracle_mode": "two_region_semantic_binding", "preset": "horizontal"}
    }
    spec_json = json.dumps(spec_lr, indent=2, ensure_ascii=False)

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
                {"name": "VAE", "type": "VAE", "links": [8, 9, 10, 11], "slot_index": 2}
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
                {"name": "LATENT", "type": "LATENT", "links": [12], "slot_index": 0}
            ],
            "widgets_values": [832, 1216, 1]
        },
        # 3: Region Editor (Two Region: Left / Right)
        {
            "id": 3,
            "type": "TegakiTwoRegionCoupleEditor",
            "pos": [400, 80],
            "size": [400, 720],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "links": [13], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "combined_preview", "type": "IMAGE", "links": [14], "slot_index": 3},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 4}
            ],
            "widgets_values": [
                832,
                1216,
                "simple park background, two subjects",
                "worst quality, bad anatomy, duplicate subject",
                "a white dog, full body",
                "",
                "a black cat, full body",
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

        # --- CONDITIONING & PIPES ---
        # 5: CLIP Global Pos
        {
            "id": 5,
            "type": "CLIPTextEncode",
            "pos": [860, 80],
            "size": [340, 100],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 4}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [15], "slot_index": 0}
            ],
            "widgets_values": ["simple park background, two subjects"]
        },
        # 6: CLIP Global Neg
        {
            "id": 6,
            "type": "CLIPTextEncode",
            "pos": [860, 220],
            "size": [340, 100],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 5}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [16, 17, 18], "slot_index": 0}
            ],
            "widgets_values": ["worst quality, bad anatomy, duplicate subject"]
        },
        # 7: CLIP Region A Pos
        {
            "id": 7,
            "type": "CLIPTextEncode",
            "pos": [860, 360],
            "size": [340, 100],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 6}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [19], "slot_index": 0}
            ],
            "widgets_values": ["a white dog, full body"]
        },
        # 8: CLIP Region B Pos
        {
            "id": 8,
            "type": "CLIPTextEncode",
            "pos": [860, 500],
            "size": [340, 100],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 7}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [20], "slot_index": 0}
            ],
            "widgets_values": ["a black cat, full body"]
        },
        # 9: ToBasicPipe (Global)
        {
            "id": 9,
            "type": "ToBasicPipe",
            "pos": [1240, 80],
            "size": [260, 140],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 8},
                {"name": "positive", "type": "CONDITIONING", "link": 15},
                {"name": "negative", "type": "CONDITIONING", "link": 16}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [21], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 10: ToBasicPipe (Region A)
        {
            "id": 10,
            "type": "ToBasicPipe",
            "pos": [1240, 260],
            "size": [260, 140],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 2},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 9},
                {"name": "positive", "type": "CONDITIONING", "link": 19},
                {"name": "negative", "type": "CONDITIONING", "link": 17}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [22], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 11: ToBasicPipe (Region B)
        {
            "id": 11,
            "type": "ToBasicPipe",
            "pos": [1240, 440],
            "size": [260, 140],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 3},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 10},
                {"name": "positive", "type": "CONDITIONING", "link": 20},
                {"name": "negative", "type": "CONDITIONING", "link": 18}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [23], "slot_index": 0}
            ],
            "widgets_values": []
        },

        # --- ADVANCED SAMPLERS ---
        # 12: Base Sampler Provider
        {
            "id": 12,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 80],
            "size": [280, 140],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 21}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [24], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 13: Region A Sampler Provider
        {
            "id": 13,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 260],
            "size": [280, 140],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 22}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [25], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 14: Region B Sampler Provider
        {
            "id": 14,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 440],
            "size": [280, 140],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 23}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [26], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 15: Impact Adapter
        {
            "id": 15,
            "type": "TegakiTwoRegionImpactAdapter",
            "pos": [1860, 260],
            "size": [320, 200],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "link": 13},
                {"name": "sampler_A", "type": "KSAMPLER_ADVANCED", "link": 25},
                {"name": "sampler_B", "type": "KSAMPLER_ADVANCED", "link": 26}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [27], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 3}
            ],
            "widgets_values": [0, 0.0, "linear"]
        },
        # 16: RegionalSampler
        {
            "id": 16,
            "type": "RegionalSampler",
            "pos": [2220, 80],
            "size": [340, 520],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 12},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 24},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 27}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [28], "slot_index": 0}
            ],
            "widgets_values": [42, 0, "ignore", 15, 2, 1.0, 10, True, "ratio between", "AUTO", 0.3]
        },
        # 17: VAEDecode
        {
            "id": 17,
            "type": "VAEDecode",
            "pos": [2600, 80],
            "size": [220, 120],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 28},
                {"name": "vae", "type": "VAE", "link": 11}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [29], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 18: SaveImage
        {
            "id": 18,
            "type": "SaveImage",
            "pos": [2860, 80],
            "size": [340, 480],
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 29}
            ],
            "widgets_values": ["Tegaki/Phase3D2/TwoRegion/Impact"]
        }
    ]

    links = [
        [1, 1, 0, 9, 0, "MODEL"],
        [2, 1, 0, 10, 0, "MODEL"],
        [3, 1, 0, 11, 0, "MODEL"],
        [4, 1, 1, 5, 0, "CLIP"],
        [5, 1, 1, 6, 0, "CLIP"],
        [6, 1, 1, 7, 0, "CLIP"],
        [7, 1, 1, 8, 0, "CLIP"],
        [8, 1, 2, 9, 2, "VAE"],
        [9, 1, 2, 10, 2, "VAE"],
        [10, 1, 2, 11, 2, "VAE"],
        [11, 1, 2, 17, 1, "VAE"],
        [12, 2, 0, 16, 0, "LATENT"],
        [13, 3, 0, 15, 0, "TWO_REGION_SPEC"],
        [14, 3, 3, 4, 0, "IMAGE"],
        [15, 5, 0, 9, 3, "CONDITIONING"],
        [16, 6, 0, 9, 4, "CONDITIONING"],
        [17, 6, 0, 10, 4, "CONDITIONING"],
        [18, 6, 0, 11, 4, "CONDITIONING"],
        [19, 7, 0, 10, 3, "CONDITIONING"],
        [20, 8, 0, 11, 3, "CONDITIONING"],
        [21, 9, 0, 12, 0, "BASIC_PIPE"],
        [22, 10, 0, 13, 0, "BASIC_PIPE"],
        [23, 11, 0, 14, 0, "BASIC_PIPE"],
        [24, 12, 0, 16, 1, "KSAMPLER_ADVANCED"],
        [25, 13, 0, 15, 1, "KSAMPLER_ADVANCED"],
        [26, 14, 0, 15, 2, "KSAMPLER_ADVANCED"],
        [27, 15, 0, 16, 2, "REGIONAL_PROMPTS"],
        [28, 16, 0, 17, 0, "LATENT"],
        [29, 17, 0, 18, 0, "IMAGE"]
    ]

    workflow = {
        "last_node_id": 18,
        "last_link_id": 29,
        "nodes": nodes,
        "links": links
    }

    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"[Workflow 19] Generated: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_19()
