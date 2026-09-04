"""
Generate Phase 3H Subject Exclusivity Workflows (29, 30, 31, 32)
================================================================
Generates:
- 29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE.json
- 30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE.json
- 31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE.json
- 32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE.json

Prompt Scope Separation:
- Global Style: "manga illustration, monochrome expressive linework, high quality" (appended to all)
- Base Scene (Exclusive Base): "manga illustration, monochrome expressive linework, high quality, clean empty white background, simple blank manga background, no focal subject"
- Base Negative: "worst quality, low quality, blurry, bad anatomy, person, human, girl, boy, extra character, face, body, animal, dog, cat"
- Regional Negative: "worst quality, low quality, blurry, bad anatomy" (Does NOT suppress dog/cat)
- Regional Subjects:
  - Dog: "manga illustration, monochrome expressive linework, high quality, a white dog, full body"
  - Cat: "manga illustration, monochrome expressive linework, high quality, a black cat, full body"

Parity Invariants:
- Fixed 1024x1024, Seed 42, 20 steps, Euler/Normal, CFG 7.0, Impact Regional Backend (12 widgets)
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOWS_DIR = os.path.join(PROJECT_ROOT, "workflows")

GLOBAL_STYLE = "manga illustration, monochrome expressive linework, high quality"
BASE_POSITIVE = f"{GLOBAL_STYLE}, clean empty white background, simple blank manga background, no focal subject"
BASE_NEGATIVE = "worst quality, low quality, blurry, bad anatomy, person, human, girl, boy, extra character, face, body, animal, dog, cat"
REGIONAL_NEGATIVE = "worst quality, low quality, blurry, bad anatomy"

DOG_PROMPT = f"{GLOBAL_STYLE}, a white dog, full body"
CAT_PROMPT = f"{GLOBAL_STYLE}, a black cat, full body"


def build_exclusive_base_two_region_workflow(
    wf_filename: str,
    title: str,
    description: str,
    save_prefix: str,
    spec_data: dict,
    prompt_a: str,
    prompt_b: str
):
    spec_json = json.dumps(spec_data, indent=2, ensure_ascii=False)

    nodes = [
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
                {"name": "MODEL", "type": "MODEL", "links": [1, 2, 3], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [4, 5, 6, 7, 30, 31, 32, 33], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [8, 9, 10, 11], "slot_index": 2}
            ],
            "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
        },
        # Node 2: Empty Latent
        {
            "id": 2,
            "type": "EmptyLatentImage",
            "pos": [40, 240],
            "size": [320, 110],
            "flags": {},
            "order": 1,
            "mode": 0,
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [12], "slot_index": 0}],
            "widgets_values": [1024, 1024, 1]
        },
        # Node 3: Two Region Editor (Oracle)
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
                1024,
                1024,
                BASE_POSITIVE,
                BASE_NEGATIVE,
                prompt_a,
                "",
                prompt_b,
                "",
                spec_json
            ]
        },
        # Node 4: Oracle Preview
        {
            "id": 4,
            "type": "PreviewImage",
            "pos": [400, 840],
            "size": [400, 360],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 14}],
            "widgets_values": []
        },

        # --- CONDITIONING NODES ---
        # Node 5: Base Positive (Exclusive Base)
        {
            "id": 5,
            "type": "CLIPTextEncode",
            "pos": [820, 80],
            "size": [360, 100],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 4}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [15], "slot_index": 0}],
            "widgets_values": [BASE_POSITIVE]
        },
        # Node 6: Base Negative (Subject-Suppressed Negative)
        {
            "id": 6,
            "type": "CLIPTextEncode",
            "pos": [820, 220],
            "size": [360, 110],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 5}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [16], "slot_index": 0}],
            "widgets_values": [BASE_NEGATIVE]
        },
        # Node 7: Region A Positive
        {
            "id": 7,
            "type": "CLIPTextEncode",
            "pos": [820, 370],
            "size": [360, 100],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 6}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [19], "slot_index": 0}],
            "widgets_values": [prompt_a]
        },
        # Node 8: Region B Positive
        {
            "id": 8,
            "type": "CLIPTextEncode",
            "pos": [820, 510],
            "size": [360, 100],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 7}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [20], "slot_index": 0}],
            "widgets_values": [prompt_b]
        },
        # Node 19: Regional Negative (Clean - does not suppress dog/cat)
        {
            "id": 19,
            "type": "CLIPTextEncode",
            "pos": [820, 650],
            "size": [360, 90],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 33}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [17, 18], "slot_index": 0}],
            "widgets_values": [REGIONAL_NEGATIVE]
        },

        # --- IMPACT PIPELINES ---
        # Node 9: ToBasicPipe (Base)
        {
            "id": 9,
            "type": "ToBasicPipe",
            "pos": [1240, 80],
            "size": [260, 140],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": 30},
                {"name": "vae", "type": "VAE", "link": 8},
                {"name": "positive", "type": "CONDITIONING", "link": 15},
                {"name": "negative", "type": "CONDITIONING", "link": 16}
            ],
            "outputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "links": [21], "slot_index": 0}],
            "widgets_values": []
        },
        # Node 10: ToBasicPipe (Region A)
        {
            "id": 10,
            "type": "ToBasicPipe",
            "pos": [1240, 260],
            "size": [260, 140],
            "flags": {},
            "order": 10,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 2},
                {"name": "clip", "type": "CLIP", "link": 31},
                {"name": "vae", "type": "VAE", "link": 9},
                {"name": "positive", "type": "CONDITIONING", "link": 19},
                {"name": "negative", "type": "CONDITIONING", "link": 17}
            ],
            "outputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "links": [22], "slot_index": 0}],
            "widgets_values": []
        },
        # Node 11: ToBasicPipe (Region B)
        {
            "id": 11,
            "type": "ToBasicPipe",
            "pos": [1240, 440],
            "size": [260, 140],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 3},
                {"name": "clip", "type": "CLIP", "link": 32},
                {"name": "vae", "type": "VAE", "link": 10},
                {"name": "positive", "type": "CONDITIONING", "link": 20},
                {"name": "negative", "type": "CONDITIONING", "link": 18}
            ],
            "outputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "links": [23], "slot_index": 0}],
            "widgets_values": []
        },
        # Node 12: Base Sampler Provider
        {
            "id": 12,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 80],
            "size": [280, 140],
            "flags": {},
            "order": 12,
            "mode": 0,
            "inputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "link": 21}],
            "outputs": [{"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [24], "slot_index": 0}],
            "widgets_values": [7.0, "euler", "normal", 1.0]
        },
        # Node 13: Region A Sampler Provider
        {
            "id": 13,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 260],
            "size": [280, 140],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "link": 22}],
            "outputs": [{"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [25], "slot_index": 0}],
            "widgets_values": [7.0, "euler", "normal", 1.0]
        },
        # Node 14: Region B Sampler Provider
        {
            "id": 14,
            "type": "KSamplerAdvancedProvider",
            "pos": [1540, 440],
            "size": [280, 140],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "link": 23}],
            "outputs": [{"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [26], "slot_index": 0}],
            "widgets_values": [7.0, "euler", "normal", 1.0]
        },
        # Node 15: Impact Adapter
        {
            "id": 15,
            "type": "TegakiTwoRegionImpactAdapter",
            "pos": [1860, 260],
            "size": [320, 200],
            "flags": {},
            "order": 15,
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
        # Node 16: RegionalSampler (12 WIDGETS PARITY)
        {
            "id": 16,
            "type": "RegionalSampler",
            "pos": [2220, 80],
            "size": [360, 360],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 12},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 24},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 27}
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [28], "slot_index": 0}],
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
        # Node 17: VAEDecode
        {
            "id": 17,
            "type": "VAEDecode",
            "pos": [2620, 80],
            "size": [220, 120],
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 28},
                {"name": "vae", "type": "VAE", "link": 11}
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [29], "slot_index": 0}],
            "widgets_values": []
        },
        # Node 18: SaveImage
        {
            "id": 18,
            "type": "SaveImage",
            "pos": [2880, 80],
            "size": [380, 440],
            "flags": {},
            "order": 18,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 29}],
            "widgets_values": [save_prefix]
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
        [17, 19, 0, 10, 4, "CONDITIONING"],
        [18, 19, 0, 11, 4, "CONDITIONING"],
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
        [29, 17, 0, 18, 0, "IMAGE"],
        [30, 1, 1, 9, 1, "CLIP"],
        [31, 1, 1, 10, 1, "CLIP"],
        [32, 1, 1, 11, 1, "CLIP"],
        [33, 1, 1, 19, 0, "CLIP"]
    ]

    workflow_json = {
        "last_node_id": 19,
        "last_link_id": 33,
        "nodes": nodes,
        "links": links,
        "groups": [
            {
                "title": "CHECKPOINT & CANVAS",
                "bounding": [20, 20, 360, 360],
                "color": "#3f3f46",
                "font_size": 22
            },
            {
                "title": "TWO REGION ORACLE EDITOR",
                "bounding": [380, 20, 420, 1020],
                "color": "#ea580c",
                "font_size": 22
            },
            {
                "title": "EXCLUSIVE BASE & PROMPT CONDITIONING",
                "bounding": [800, 20, 400, 740],
                "color": "#16a34a",
                "font_size": 22
            },
            {
                "title": "IMPACT REGIONAL PIPES & SAMPLER",
                "bounding": [1220, 20, 1380, 640],
                "color": "#2563eb",
                "font_size": 22
            },
            {
                "title": "OUTPUT",
                "bounding": [2600, 20, 680, 520],
                "color": "#0d9488",
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


def generate_all_exclusive_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)

    # 1. WF29: Single A Top-Left Exclusive Base
    spec_29 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "label": "White Dog (Top-Left)",
                "enabled": True,
                "x": 0.05,
                "y": 0.05,
                "w": 0.45,
                "h": 0.45
            },
            {
                "id": "B",
                "label": "Disabled",
                "enabled": False,
                "x": 0.50,
                "y": 0.50,
                "w": 0.45,
                "h": 0.45
            }
        ]
    }
    build_exclusive_base_two_region_workflow(
        wf_filename="29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE.json",
        title="29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE",
        description="Phase 3H Exclusive Base Oracle: White Dog placed at Top-Left [0.05, 0.05, 0.45, 0.45] with Base suppression of unprompted background subjects (seed 42).",
        save_prefix="Phase3H_Canonical_29_SingleA_TopLeft_ExclusiveBase",
        spec_data=spec_29,
        prompt_a=DOG_PROMPT,
        prompt_b="disabled"
    )

    # 2. WF30: Single A Bottom-Right Exclusive Base
    spec_30 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "label": "White Dog (Bottom-Right)",
                "enabled": True,
                "x": 0.50,
                "y": 0.50,
                "w": 0.45,
                "h": 0.45
            },
            {
                "id": "B",
                "label": "Disabled",
                "enabled": False,
                "x": 0.05,
                "y": 0.05,
                "w": 0.45,
                "h": 0.45
            }
        ]
    }
    build_exclusive_base_two_region_workflow(
        wf_filename="30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE.json",
        title="30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE",
        description="Phase 3H Exclusive Base Oracle: White Dog placed at Bottom-Right [0.50, 0.50, 0.45, 0.45] with Base suppression of unprompted background subjects (seed 42).",
        save_prefix="Phase3H_Canonical_30_SingleA_BottomRight_ExclusiveBase",
        spec_data=spec_30,
        prompt_a=DOG_PROMPT,
        prompt_b="disabled"
    )

    # 3. WF31: Two Region Dog Left / Cat Right Exclusive Base
    spec_31 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "label": "White Dog (Left)",
                "enabled": True,
                "x": 0.05,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            },
            {
                "id": "B",
                "label": "Black Cat (Right)",
                "enabled": True,
                "x": 0.50,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            }
        ]
    }
    build_exclusive_base_two_region_workflow(
        wf_filename="31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE.json",
        title="31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE",
        description="Phase 3H Exclusive Base Oracle: White Dog Left [0.05, 0.15, 0.45, 0.70], Black Cat Right [0.50, 0.15, 0.45, 0.70] with Base suppression of unprompted background subjects (seed 42).",
        save_prefix="Phase3H_Canonical_31_DogCat_LR_ExclusiveBase",
        spec_data=spec_31,
        prompt_a=DOG_PROMPT,
        prompt_b=CAT_PROMPT
    )

    # 4. WF32: Two Region Dog Right / Cat Left SWAP Exclusive Base
    spec_32 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "label": "White Dog (Right - SWAP)",
                "enabled": True,
                "x": 0.50,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            },
            {
                "id": "B",
                "label": "Black Cat (Left - SWAP)",
                "enabled": True,
                "x": 0.05,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            }
        ]
    }
    build_exclusive_base_two_region_workflow(
        wf_filename="32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE.json",
        title="32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE",
        description="Phase 3H Exclusive Base Oracle: White Dog Right [0.50, 0.15, 0.45, 0.70], Black Cat Left [0.05, 0.15, 0.45, 0.70] with Base suppression of unprompted background subjects (seed 42).",
        save_prefix="Phase3H_Canonical_32_DogCat_Swap_ExclusiveBase",
        spec_data=spec_32,
        prompt_a=DOG_PROMPT,
        prompt_b=CAT_PROMPT
    )


if __name__ == "__main__":
    generate_all_exclusive_workflows()
