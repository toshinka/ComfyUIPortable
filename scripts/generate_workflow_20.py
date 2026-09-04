"""
Generate Workflow 20: Two Region Layout Assist Oracle (Phase 3D.2)
==================================================================
Builds workflows/20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json.
Combines:
- Impact RegionalSampler
- TegakiTwoRegionLayoutGuide (generates simple black/white rectangular layout guide)
- ControlNetApplyAdvanced (with CN-anytest4_illustrious2_A.safetensors)
- Tests whether geometric layout assist improves spatial locality and bounding.
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_FILE = os.path.join(PROJECT_ROOT, "workflows", "20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json")


def build_workflow_20():
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
        "metadata": {"oracle_mode": "two_region_layout_assist"}
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
        # 2: ControlNet Loader
        {
            "id": 2,
            "type": "ControlNetLoader",
            "pos": [40, 220],
            "size": [320, 80],
            "flags": {},
            "order": 1,
            "mode": 0,
            "outputs": [
                {"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [12], "slot_index": 0}
            ],
            "widgets_values": ["CN-anytest4_illustrious2_A.safetensors"]
        },
        # 3: Empty Latent
        {
            "id": 3,
            "type": "EmptyLatentImage",
            "pos": [40, 340],
            "size": [320, 110],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [13], "slot_index": 0}
            ],
            "widgets_values": [832, 1216, 1]
        },
        # 4: Region Editor
        {
            "id": 4,
            "type": "TegakiTwoRegionCoupleEditor",
            "pos": [400, 80],
            "size": [400, 720],
            "flags": {},
            "order": 3,
            "mode": 0,
            "outputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "links": [14, 15], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "combined_preview", "type": "IMAGE", "links": [16], "slot_index": 3},
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
        # 5: Layout Guide
        {
            "id": 5,
            "type": "TegakiTwoRegionLayoutGuide",
            "pos": [860, 80],
            "size": [340, 160],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "link": 14}
            ],
            "outputs": [
                {"name": "guide_image", "type": "IMAGE", "links": [17], "slot_index": 0},
                {"name": "combined_mask", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": ["Panel Outline (White on Black)", 4]
        },
        # 6: CLIP Global Pos
        {
            "id": 6,
            "type": "CLIPTextEncode",
            "pos": [860, 280],
            "size": [340, 100],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 4}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [18], "slot_index": 0}
            ],
            "widgets_values": ["simple park background, two subjects"]
        },
        # 7: CLIP Global Neg
        {
            "id": 7,
            "type": "CLIPTextEncode",
            "pos": [860, 420],
            "size": [340, 100],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 5}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [19, 20, 21], "slot_index": 0}
            ],
            "widgets_values": ["worst quality, bad anatomy, duplicate subject"]
        },
        # 8: ControlNet Apply Advanced (on Global Conditioning)
        {
            "id": 8,
            "type": "ControlNetApplyAdvanced",
            "pos": [1240, 80],
            "size": [320, 240],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [
                {"name": "positive", "type": "CONDITIONING", "link": 18},
                {"name": "negative", "type": "CONDITIONING", "link": 19},
                {"name": "control_net", "type": "CONTROL_NET", "link": 12},
                {"name": "image", "type": "IMAGE", "link": 17}
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": [22], "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": [23], "slot_index": 1}
            ],
            "widgets_values": [0.40, 0.0, 0.60]
        },
        # 9: CLIP Region A Pos
        {
            "id": 9,
            "type": "CLIPTextEncode",
            "pos": [860, 560],
            "size": [340, 100],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 6}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [24], "slot_index": 0}
            ],
            "widgets_values": ["a white dog, full body"]
        },
        # 10: CLIP Region B Pos
        {
            "id": 10,
            "type": "CLIPTextEncode",
            "pos": [860, 700],
            "size": [340, 100],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 7}
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [25], "slot_index": 0}
            ],
            "widgets_values": ["a black cat, full body"]
        },
        # 11: ToBasicPipe (Global assisted by ControlNet)
        {
            "id": 11,
            "type": "ToBasicPipe",
            "pos": [1600, 80],
            "size": [260, 140],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 8},
                {"name": "positive", "type": "CONDITIONING", "link": 22},
                {"name": "negative", "type": "CONDITIONING", "link": 23}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [26], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 12: ToBasicPipe (Region A)
        {
            "id": 12,
            "type": "ToBasicPipe",
            "pos": [1600, 260],
            "size": [260, 140],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 2},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 9},
                {"name": "positive", "type": "CONDITIONING", "link": 24},
                {"name": "negative", "type": "CONDITIONING", "link": 20}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [27], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 13: ToBasicPipe (Region B)
        {
            "id": 13,
            "type": "ToBasicPipe",
            "pos": [1600, 440],
            "size": [260, 140],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 3},
                {"name": "clip", "type": "CLIP", "link": None},
                {"name": "vae", "type": "VAE", "link": 10},
                {"name": "positive", "type": "CONDITIONING", "link": 25},
                {"name": "negative", "type": "CONDITIONING", "link": 21}
            ],
            "outputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "links": [28], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 14: KSamplerAdvancedProvider (Base)
        {
            "id": 14,
            "type": "KSamplerAdvancedProvider",
            "pos": [1900, 80],
            "size": [280, 140],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 26}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [29], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 15: KSamplerAdvancedProvider (Region A)
        {
            "id": 15,
            "type": "KSamplerAdvancedProvider",
            "pos": [1900, 260],
            "size": [280, 140],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 27}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [30], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 16: KSamplerAdvancedProvider (Region B)
        {
            "id": 16,
            "type": "KSamplerAdvancedProvider",
            "pos": [1900, 440],
            "size": [280, 140],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 28}
            ],
            "outputs": [
                {"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [31], "slot_index": 0}
            ],
            "widgets_values": [6.0, "euler", "normal", 1.0]
        },
        # 17: Impact Adapter
        {
            "id": 17,
            "type": "TegakiTwoRegionImpactAdapter",
            "pos": [2220, 260],
            "size": [320, 200],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "two_region_spec", "type": "TWO_REGION_SPEC", "link": 15},
                {"name": "sampler_A", "type": "KSAMPLER_ADVANCED", "link": 30},
                {"name": "sampler_B", "type": "KSAMPLER_ADVANCED", "link": 31}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [32], "slot_index": 0},
                {"name": "mask_A", "type": "MASK", "links": None, "slot_index": 1},
                {"name": "mask_B", "type": "MASK", "links": None, "slot_index": 2},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 3}
            ],
            "widgets_values": [0, 0.0, "linear"]
        },
        # 18: RegionalSampler
        {
            "id": 18,
            "type": "RegionalSampler",
            "pos": [2580, 80],
            "size": [340, 520],
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 13},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 29},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 32}
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [33], "slot_index": 0}
            ],
            "widgets_values": [42, 0, "ignore", 15, 2, 1.0, 10, True, "ratio between", "AUTO", 0.3]
        },
        # 19: VAEDecode
        {
            "id": 19,
            "type": "VAEDecode",
            "pos": [2960, 80],
            "size": [220, 120],
            "flags": {},
            "order": 18,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 33},
                {"name": "vae", "type": "VAE", "link": 11}
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [34], "slot_index": 0}
            ],
            "widgets_values": []
        },
        # 20: SaveImage
        {
            "id": 20,
            "type": "SaveImage",
            "pos": [3220, 80],
            "size": [340, 480],
            "flags": {},
            "order": 19,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 34}
            ],
            "widgets_values": ["Tegaki/Phase3D2/LayoutAssist/Impact_CN"]
        },
        # 21: PreviewImage
        {
            "id": 21,
            "type": "PreviewImage",
            "pos": [400, 840],
            "size": [400, 360],
            "flags": {},
            "order": 20,
            "mode": 0,
            "inputs": [
                {"name": "images", "type": "IMAGE", "link": 16}
            ],
            "widgets_values": []
        }
    ]

    links = [
        [1, 1, 0, 11, 0, "MODEL"],
        [2, 1, 0, 12, 0, "MODEL"],
        [3, 1, 0, 13, 0, "MODEL"],
        [4, 1, 1, 6, 0, "CLIP"],
        [5, 1, 1, 7, 0, "CLIP"],
        [6, 1, 1, 9, 0, "CLIP"],
        [7, 1, 1, 10, 0, "CLIP"],
        [8, 1, 2, 11, 2, "VAE"],
        [9, 1, 2, 12, 2, "VAE"],
        [10, 1, 2, 13, 2, "VAE"],
        [11, 1, 2, 19, 1, "VAE"],
        [12, 2, 0, 8, 2, "CONTROL_NET"],
        [13, 3, 0, 18, 0, "LATENT"],
        [14, 4, 0, 5, 0, "TWO_REGION_SPEC"],
        [15, 4, 0, 17, 0, "TWO_REGION_SPEC"],
        [16, 4, 3, 21, 0, "IMAGE"],
        [17, 5, 0, 8, 3, "IMAGE"],
        [18, 6, 0, 8, 0, "CONDITIONING"],
        [19, 7, 0, 8, 1, "CONDITIONING"],
        [20, 7, 0, 12, 4, "CONDITIONING"],
        [21, 7, 0, 13, 4, "CONDITIONING"],
        [22, 8, 0, 11, 3, "CONDITIONING"],
        [23, 8, 1, 11, 4, "CONDITIONING"],
        [24, 9, 0, 12, 3, "CONDITIONING"],
        [25, 10, 0, 13, 3, "CONDITIONING"],
        [26, 11, 0, 14, 0, "BASIC_PIPE"],
        [27, 12, 0, 15, 0, "BASIC_PIPE"],
        [28, 13, 0, 16, 0, "BASIC_PIPE"],
        [29, 14, 0, 18, 1, "KSAMPLER_ADVANCED"],
        [30, 15, 0, 17, 1, "KSAMPLER_ADVANCED"],
        [31, 16, 0, 17, 2, "KSAMPLER_ADVANCED"],
        [32, 17, 0, 18, 2, "REGIONAL_PROMPTS"],
        [33, 18, 0, 19, 0, "LATENT"],
        [34, 19, 0, 20, 0, "IMAGE"]
    ]

    workflow = {
        "last_node_id": 21,
        "last_link_id": 34,
        "nodes": nodes,
        "links": links
    }

    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"[Workflow 20] Generated: {WORKFLOW_FILE}")


if __name__ == "__main__":
    build_workflow_20()
