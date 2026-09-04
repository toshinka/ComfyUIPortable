"""
Generate Canonical Spatial Verification Workflows (Phase 3G)
===========================================================
Generates:
- 25_VERIFY_SINGLE_A_TOP_LEFT.json
- 26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json
- 27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json
- 28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json

All workflows follow:
- 1 Workflow = 1 hypothesis
- Fixed 1024x1024 canvas
- Fixed seed 42, 20 steps, CFG 7.0, Euler/Normal
- Impact Regional Backend (12 widgets parity, clip connected)
- Zero-Touch validation error 0
"""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOWS_DIR = os.path.join(PROJECT_ROOT, "workflows")


def build_two_region_impact_workflow(
    wf_filename: str,
    title: str,
    description: str,
    save_prefix: str,
    spec_data: dict,
    prompt_a: str,
    prompt_b: str,
    global_prompt: str = "manga illustration, simple clean background, white background, high quality",
    global_negative: str = "worst quality, low quality, blurry, bad anatomy"
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
                {"name": "CLIP", "type": "CLIP", "links": [4, 5, 6, 7, 30, 31, 32], "slot_index": 1},
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
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [12], "slot_index": 0}
            ],
            "widgets_values": [1024, 1024, 1]
        },
        # Node 3: Region Editor
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
                global_prompt,
                global_negative,
                prompt_a,
                "",
                prompt_b,
                "",
                spec_json
            ]
        },
        # Node 4: Preview Image
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
        # Node 5: Global Positive CLIPTextEncode
        {
            "id": 5,
            "type": "CLIPTextEncode",
            "pos": [840, 80],
            "size": [360, 110],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 4}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [15], "slot_index": 0}],
            "widgets_values": [global_prompt]
        },
        # Node 6: Global Negative CLIPTextEncode
        {
            "id": 6,
            "type": "CLIPTextEncode",
            "pos": [840, 230],
            "size": [360, 110],
            "flags": {},
            "order": 5,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 5}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [16, 17, 18], "slot_index": 0}],
            "widgets_values": [global_negative]
        },
        # Node 7: Region A Positive CLIPTextEncode
        {
            "id": 7,
            "type": "CLIPTextEncode",
            "pos": [840, 380],
            "size": [360, 110],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 6}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [19], "slot_index": 0}],
            "widgets_values": [prompt_a]
        },
        # Node 8: Region B Positive CLIPTextEncode
        {
            "id": 8,
            "type": "CLIPTextEncode",
            "pos": [840, 530],
            "size": [360, 110],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 7}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [20], "slot_index": 0}],
            "widgets_values": [prompt_b]
        },
        # Node 9: ToBasicPipe (Base)
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
            "order": 9,
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
            "order": 10,
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
            "order": 11,
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
            "order": 12,
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
            "order": 13,
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
        # Node 16: RegionalSampler (12 WIDGETS PARITY)
        {
            "id": 16,
            "type": "RegionalSampler",
            "pos": [2220, 80],
            "size": [360, 360],
            "flags": {},
            "order": 15,
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
            "order": 16,
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
            "order": 17,
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
        [29, 17, 0, 18, 0, "IMAGE"],
        [30, 1, 1, 9, 1, "CLIP"],
        [31, 1, 1, 10, 1, "CLIP"],
        [32, 1, 1, 11, 1, "CLIP"],
    ]

    workflow = {
        "last_node_id": 18,
        "last_link_id": len(links),
        "nodes": nodes,
        "links": links,
        "groups": [
            {
                "title": "GLOBAL & MODELS",
                "bounding": [20, 20, 360, 400],
                "color": "#3f3f46",
                "font_size": 22
            },
            {
                "title": "CANONICAL REGION GEOMETRY",
                "bounding": [380, 20, 440, 1200],
                "color": "#ea580c",
                "font_size": 22
            },
            {
                "title": "PROMPT CONDITIONING",
                "bounding": [820, 20, 400, 640],
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
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"[CanonicalWorkflow] Generated: {out_path}")
    return out_path


def generate_all_canonical_spatial_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)

    # 1. Workflow 25: Single A Top-Left
    spec_25 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.05,
                "w": 0.45,
                "h": 0.45
            },
            {
                "id": "B",
                "enabled": False,
                "prompt": "",
                "negative_prompt": "",
                "x": 0.50,
                "y": 0.50,
                "w": 0.45,
                "h": 0.45
            }
        ],
        "metadata": {"canonical_hypothesis": "single_region_top_left"}
    }
    build_two_region_impact_workflow(
        wf_filename="25_VERIFY_SINGLE_A_TOP_LEFT.json",
        title="25_VERIFY_SINGLE_A_TOP_LEFT",
        description="Canonical Spatial Oracle: White Dog placed strictly at Top-Left via region geometry alone (seed 42).",
        save_prefix="Tegaki/Phase3G/canonical/wf25_single_a_top_left",
        spec_data=spec_25,
        prompt_a="a white dog, full body",
        prompt_b=""
    )

    # 2. Workflow 26: Single A Bottom-Right
    spec_26 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.50,
                "y": 0.50,
                "w": 0.45,
                "h": 0.45
            },
            {
                "id": "B",
                "enabled": False,
                "prompt": "",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.05,
                "w": 0.45,
                "h": 0.45
            }
        ],
        "metadata": {"canonical_hypothesis": "single_region_bottom_right"}
    }
    build_two_region_impact_workflow(
        wf_filename="26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json",
        title="26_VERIFY_SINGLE_A_BOTTOM_RIGHT",
        description="Canonical Spatial Oracle: White Dog placed strictly at Bottom-Right via region geometry alone (seed 42).",
        save_prefix="Tegaki/Phase3G/canonical/wf26_single_a_bottom_right",
        spec_data=spec_26,
        prompt_a="a white dog, full body",
        prompt_b=""
    )

    # 3. Workflow 27: Two Region Dog Left / Cat Right
    spec_27 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            },
            {
                "id": "B",
                "enabled": True,
                "prompt": "a black cat, full body",
                "negative_prompt": "",
                "x": 0.50,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            }
        ],
        "metadata": {"canonical_hypothesis": "two_region_dog_left_cat_right"}
    }
    build_two_region_impact_workflow(
        wf_filename="27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json",
        title="27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT",
        description="Canonical Spatial Oracle: White Dog Left / Black Cat Right via geometry without directional words (seed 42).",
        save_prefix="Tegaki/Phase3G/canonical/wf27_two_region_dog_cat_lr",
        spec_data=spec_27,
        prompt_a="a white dog, full body",
        prompt_b="a black cat, full body"
    )

    # 4. Workflow 28: Two Region Dog Right / Cat Left (SWAP)
    spec_28 = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": 0.50,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            },
            {
                "id": "B",
                "enabled": True,
                "prompt": "a black cat, full body",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.15,
                "w": 0.45,
                "h": 0.70
            }
        ],
        "metadata": {"canonical_hypothesis": "two_region_dog_right_cat_left_swap"}
    }
    build_two_region_impact_workflow(
        wf_filename="28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json",
        title="28_VERIFY_TWO_REGION_DOG_CAT_SWAP",
        description="Canonical Spatial Oracle: White Dog Right / Black Cat Left (Geometry SWAP without directional words, seed 42).",
        save_prefix="Tegaki/Phase3G/canonical/wf28_two_region_dog_cat_swap",
        spec_data=spec_28,
        prompt_a="a white dog, full body",
        prompt_b="a black cat, full body"
    )


if __name__ == "__main__":
    generate_all_canonical_spatial_workflows()
