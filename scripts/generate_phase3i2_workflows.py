"""
Generate Phase 3I.2 Canonical Workflows (44, 45, 46, 47)
=========================================================
Generates:
- 44_VERIFY_NATIVE20_BASEONLY_ZERO.json:
    Native 20-step with base_only_steps=0 (Euler 20s, CFG 7.0, CN 0.75/0.80, base_only=0)
- 45_VERIFY_NATIVE12_CONTROL.json:
    Native 12-step Control (Euler 12s, CFG 6.0, No LoRA, base_only=2)
- 46_VERIFY_HYPER12_CAUSAL_CONTROL.json:
    Hyper12 Causal Control (Euler 12s, CFG 6.0, Hyper-SDXL LoRA, base_only=2)
- 47_VERIFY_PER_REGION_HINT_ATTENUATED.json:
    Per-Region Hint Attenuated (Euler 20s, CFG 7.0, per_region_hint 0.35, base_only=2)
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
CHECKPOINT_NAME = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
HYPER_SD_LORA_NAME = "調整\\Hyper-SDXL-12steps-CFG-lora.safetensors"
CONTROLNET_NAME = "CN-anytest4_illustrious2_A.safetensors"

GLOBAL_STYLE = "manga illustration, monochrome expressive linework, high quality"
COURTYARD_SCENE = f"{GLOBAL_STYLE}, simple school courtyard, two students standing"
GLOBAL_NEGATIVE = "worst quality, low quality, bad anatomy, blurry"


def build_phase3i2_workflow(
    wf_filename: str,
    title: str,
    save_prefix: str,
    characters: list,
    attending_chars: list,
    staging_overrides: dict,
    fast_draft_12: bool = False,
    steps: int = 20,
    cfg: float = 7.0,
    base_only_steps: int = 2,
    guide_style: str = "mannequin_capsule",
    controlnet_strength: float = 0.75,
    controlnet_start: float = 0.0,
    controlnet_end: float = 0.80,
    propagate_controlnet_to_regions: bool = False,
    regional_control_mode: str = "off",
    regional_control_strength: float = 0.35,
    panel_scene_prompt: str = None,
    seed: int = 42
):
    cast_data = {"version": 1, "characters": characters}
    cast_json = json.dumps(cast_data, indent=2, ensure_ascii=False)

    panel_content_data = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "panel_count": 1,
        "global_prompt": GLOBAL_STYLE,
        "global_negative_prompt": GLOBAL_NEGATIVE,
        "panels": [
            {
                "id": 1,
                "name": "Panel 1",
                "enabled": True,
                "prompt": panel_scene_prompt if panel_scene_prompt else COURTYARD_SCENE,
                "negative_prompt": "blurry",
                "characters": attending_chars,
                "subscenes": []
            }
        ]
    }
    panel_content_json = json.dumps(panel_content_data, indent=2, ensure_ascii=False)

    layout_data = get_default_panel_layout_spec(1024, 1024, preset="1_full")
    layout_json = json.dumps(layout_data, indent=2, ensure_ascii=False)
    staging_overrides_json = json.dumps(staging_overrides, indent=2, ensure_ascii=False)

    nodes = [
        # 1. CheckpointLoaderSimple
        {
            "id": 1,
            "type": "CheckpointLoaderSimple",
            "pos": [40, 80],
            "size": [320, 100],
            "flags": {},
            "order": 0,
            "mode": 0,
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [101 if fast_draft_12 else 1], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [2, 3, 20, 24], "slot_index": 1},
                {"name": "VAE", "type": "VAE", "links": [4, 18], "slot_index": 2}
            ],
            "widgets_values": [CHECKPOINT_NAME]
        }
    ]

    # Optional Fast Draft LoRA Node
    if fast_draft_12:
        nodes.append({
            "id": 40,
            "type": "LoraLoader",
            "pos": [40, 200],
            "size": [320, 100],
            "flags": {},
            "order": 1,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 101},
                {"name": "clip", "type": "CLIP", "link": 2}
            ],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                {"name": "CLIP", "type": "CLIP", "links": [102], "slot_index": 1}
            ],
            "widgets_values": [HYPER_SD_LORA_NAME, 1.0, 1.0]
        })

    nodes.extend([
        # 2. EmptyLatentImage
        {
            "id": 2,
            "type": "EmptyLatentImage",
            "pos": [40, 320 if fast_draft_12 else 240],
            "size": [320, 110],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}],
            "widgets_values": [1024, 1024, 1]
        },
        # 3. CLIPTextEncode Global Scene Positive
        {
            "id": 3,
            "type": "CLIPTextEncode",
            "pos": [400, 80],
            "size": [340, 100],
            "flags": {},
            "order": 3,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 102 if fast_draft_12 else 2}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "slot_index": 0}],
            "widgets_values": [panel_scene_prompt if panel_scene_prompt else COURTYARD_SCENE]
        },
        # 4. CLIPTextEncode Global Negative
        {
            "id": 4,
            "type": "CLIPTextEncode",
            "pos": [400, 240],
            "size": [340, 100],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [7], "slot_index": 0}],
            "widgets_values": [GLOBAL_NEGATIVE]
        },
        # 30. ControlNetLoader
        {
            "id": 30,
            "type": "ControlNetLoader",
            "pos": [400, 400],
            "size": [340, 80],
            "flags": {},
            "order": 5,
            "mode": 0,
            "outputs": [{"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [301], "slot_index": 0}],
            "widgets_values": [CONTROLNET_NAME]
        },
        # 31. TegakiMangaLayoutGuideGenerator
        {
            "id": 31,
            "type": "TegakiMangaLayoutGuideGenerator",
            "pos": [780, 400],
            "size": [320, 180],
            "flags": {},
            "order": 6,
            "mode": 0,
            "inputs": [{"name": "scene_plan", "type": "*", "link": 16}],
            "outputs": [
                {"name": "guide_image", "type": "IMAGE", "links": [302], "slot_index": 0},
                {"name": "layout_mask", "type": "MASK", "links": [], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": [], "slot_index": 2}
            ],
            "widgets_values": [1, guide_style, "Black on White", 4, True, 1024, 1024]
        },
        # 32. ControlNetApplyAdvanced
        {
            "id": 32,
            "type": "ControlNetApplyAdvanced",
            "pos": [780, 80],
            "size": [300, 180],
            "flags": {},
            "order": 7,
            "mode": 0,
            "inputs": [
                {"name": "positive", "type": "CONDITIONING", "link": 6},
                {"name": "negative", "type": "CONDITIONING", "link": 7},
                {"name": "control_net", "type": "CONTROL_NET", "link": 301},
                {"name": "image", "type": "IMAGE", "link": 302}
            ],
            "outputs": [
                {"name": "positive", "type": "CONDITIONING", "links": [303], "slot_index": 0},
                {"name": "negative", "type": "CONDITIONING", "links": [304], "slot_index": 1}
            ],
            "widgets_values": [controlnet_strength, controlnet_start, controlnet_end]
        },
        # 5. ToBasicPipe
        {
            "id": 5,
            "type": "ToBasicPipe",
            "pos": [1120, 80],
            "size": [260, 140],
            "flags": {},
            "order": 8,
            "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": 20},
                {"name": "vae", "type": "VAE", "link": 4},
                {"name": "positive", "type": "CONDITIONING", "link": 303},
                {"name": "negative", "type": "CONDITIONING", "link": 304}
            ],
            "outputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "links": [8], "slot_index": 0}],
            "widgets_values": []
        },
        # 6. KSamplerAdvancedProvider
        {
            "id": 6,
            "type": "KSamplerAdvancedProvider",
            "pos": [1120, 260],
            "size": [260, 180],
            "flags": {},
            "order": 9,
            "mode": 0,
            "inputs": [
                {"name": "basic_pipe", "type": "BASIC_PIPE", "link": 8},
                {"name": "sampler_opt", "type": "SAMPLER", "link": None},
                {"name": "scheduler_func_opt", "type": "SCHEDULER_FUNC", "link": None}
            ],
            "outputs": [{"name": "KSAMPLER_ADVANCED", "type": "KSAMPLER_ADVANCED", "links": [9], "slot_index": 0}],
            "widgets_values": [cfg, "euler", "normal", 1.0]
        },
        # 7. TegakiMangaCastMaster
        {
            "id": 7,
            "type": "TegakiMangaCastMaster",
            "pos": [40, 480],
            "size": [360, 320],
            "flags": {},
            "order": 10,
            "mode": 0,
            "outputs": [
                {"name": "cast_spec", "type": "CAST_SPEC", "links": [10], "slot_index": 0},
                {"name": "cast_spec_json", "type": "STRING", "links": [11], "slot_index": 1}
            ],
            "widgets_values": [cast_json]
        },
        # 8. TegakiMangaPanelContentEditor
        {
            "id": 8,
            "type": "TegakiMangaPanelContentEditor",
            "pos": [440, 480],
            "size": [380, 320],
            "flags": {},
            "order": 11,
            "mode": 0,
            "inputs": [{"name": "cast_spec", "type": "CAST_SPEC", "link": 10}],
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [12], "slot_index": 0},
                {"name": "content_data_json", "type": "STRING", "links": None, "slot_index": 1},
                {"name": "panel_count", "type": "INT", "links": None, "slot_index": 2}
            ],
            "widgets_values": [panel_content_json]
        },
        # 9. TegakiMangaPanelLayoutEditor
        {
            "id": 9,
            "type": "TegakiMangaPanelLayoutEditor",
            "pos": [900, 500],
            "size": [380, 440],
            "flags": {},
            "order": 12,
            "mode": 0,
            "outputs": [
                {"name": "layout_image", "type": "IMAGE", "links": None, "slot_index": 0},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [13, 14], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [1024, 1024, 1, layout_json]
        },
        # 10. TegakiMangaCharacterStagingEditor
        {
            "id": 10,
            "type": "TegakiMangaCharacterStagingEditor",
            "pos": [1260, 480],
            "size": [440, 380],
            "flags": {},
            "order": 13,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 12},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 13}
            ],
            "outputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "links": [15], "slot_index": 0},
                {"name": "staging_preview", "type": "IMAGE", "links": None, "slot_index": 1},
                {"name": "staging_json", "type": "STRING", "links": None, "slot_index": 2}
            ],
            "widgets_values": [staging_overrides_json]
        },
        # 11. TegakiMangaPageCompiler
        {
            "id": 11,
            "type": "TegakiMangaPageCompiler",
            "pos": [1740, 80],
            "size": [340, 240],
            "flags": {},
            "order": 14,
            "mode": 0,
            "inputs": [
                {"name": "region_spec", "type": "REGION_SPEC", "link": 15},
                {"name": "cast_spec", "type": "STRING", "link": 11}
            ],
            "outputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "links": [16, 22], "slot_index": 0},
                {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 1}
            ],
            "widgets_values": [""]
        },
        # 12. TegakiMangaImpactRegionalAdapter
        {
            "id": 12,
            "type": "TegakiMangaImpactRegionalAdapter",
            "pos": [1760, 480],
            "size": [360, 400],
            "flags": {},
            "order": 15,
            "mode": 0,
            "inputs": [
                {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "link": 22},
                {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 14},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 9},
                {"name": "clip", "type": "CLIP", "link": 24}
            ],
            "outputs": [
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "links": [17], "slot_index": 0},
                {"name": "staging_image", "type": "IMAGE", "links": None, "slot_index": 1}
            ],
            "widgets_values": [
                "scene_first", "scene_composed", True, False, 0, 0, 0.0, "linear",
                propagate_controlnet_to_regions,
                regional_control_mode,
                regional_control_strength
            ]
        },
        # 14. RegionalSampler
        {
            "id": 14,
            "type": "RegionalSampler",
            "pos": [2140, 80],
            "size": [360, 360],
            "flags": {},
            "order": 16,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 5},
                {"name": "base_sampler", "type": "KSAMPLER_ADVANCED", "link": 9},
                {"name": "regional_prompts", "type": "REGIONAL_PROMPTS", "link": 17}
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}],
            "widgets_values": [
                seed, "fixed", 0, "ignore", steps, base_only_steps, 1.0, 10, True, "ratio between", "AUTO", 0.3
            ]
        },
        # 16. FromBasicPipe
        {
            "id": 16,
            "type": "FromBasicPipe",
            "pos": [2140, 480],
            "size": [260, 140],
            "flags": {},
            "order": 17,
            "mode": 0,
            "inputs": [{"name": "basic_pipe", "type": "BASIC_PIPE", "link": 8}],
            "outputs": [
                {"name": "model", "type": "MODEL", "links": None, "slot_index": 0},
                {"name": "clip", "type": "CLIP", "links": None, "slot_index": 1},
                {"name": "vae", "type": "VAE", "links": [18], "slot_index": 2},
                {"name": "positive", "type": "CONDITIONING", "links": None, "slot_index": 3},
                {"name": "negative", "type": "CONDITIONING", "links": None, "slot_index": 4}
            ],
            "widgets_values": []
        },
        # 17. VAEDecode
        {
            "id": 17,
            "type": "VAEDecode",
            "pos": [2540, 80],
            "size": [220, 120],
            "flags": {},
            "order": 18,
            "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 19},
                {"name": "vae", "type": "VAE", "link": 18}
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [21], "slot_index": 0}],
            "widgets_values": []
        },
        # 18. SaveImage
        {
            "id": 18,
            "type": "SaveImage",
            "pos": [2800, 80],
            "size": [340, 280],
            "flags": {},
            "order": 19,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 21}],
            "widgets_values": [save_prefix]
        }
    ])

    links = [
        [1, 40 if fast_draft_12 else 1, 0, 5, 0, "MODEL"],
        [2, 1, 1, 40 if fast_draft_12 else 3, 1 if fast_draft_12 else 0, "CLIP"],
        [3, 1, 1, 4, 0, "CLIP"],
        [4, 1, 2, 5, 2, "VAE"],
        [5, 2, 0, 14, 0, "LATENT"],
        [6, 3, 0, 32, 0, "CONDITIONING"],
        [7, 4, 0, 32, 1, "CONDITIONING"],
        [8, 5, 0, 6, 0, "BASIC_PIPE"],
        [9, 6, 0, 12, 2, "KSAMPLER_ADVANCED"],
        [10, 7, 0, 8, 0, "CAST_SPEC"],
        [11, 7, 1, 11, 1, "STRING"],
        [12, 8, 0, 10, 0, "REGION_SPEC"],
        [13, 9, 1, 10, 1, "PANEL_LAYOUT_SPEC"],
        [14, 9, 1, 12, 1, "PANEL_LAYOUT_SPEC"],
        [15, 10, 0, 11, 0, "REGION_SPEC"],
        [16, 11, 0, 31, 0, "*"],
        [17, 12, 0, 14, 2, "REGIONAL_PROMPTS"],
        [18, 16, 2, 17, 1, "VAE"],
        [19, 14, 0, 17, 0, "LATENT"],
        [20, 1, 1, 5, 1, "CLIP"],
        [21, 17, 0, 18, 0, "IMAGE"],
        [22, 11, 0, 12, 0, "PAGE_COMPILE_PLAN"],
        [24, 1, 1, 12, 3, "CLIP"],
        [301, 30, 0, 32, 2, "CONTROL_NET"],
        [302, 31, 0, 32, 3, "IMAGE"],
        [303, 32, 0, 5, 3, "CONDITIONING"],
        [304, 32, 1, 5, 4, "CONDITIONING"]
    ]

    if fast_draft_12:
        links.extend([
            [101, 1, 0, 40, 0, "MODEL"],
            [102, 40, 1, 3, 0, "CLIP"]
        ])

    return {
        "last_node_id": 40 if fast_draft_12 else 32,
        "last_link_id": 304,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"title": title},
        "version": 0.4
    }


def generate_all_phase3i2_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)

    char_alice = {
        "id": "char_alice",
        "name": "Alice",
        "enabled": True,
        "prompt": "1girl, blonde hair, twin tails, blue eyes, school uniform, white shirt, red necktie, pleated skirt",
        "negative_prompt": "worst quality, low quality, bad anatomy, duplicate girl",
        "loras": []
    }
    char_bob = {
        "id": "char_bob",
        "name": "Bob",
        "enabled": True,
        "prompt": "1boy, short black hair, dark eyes, school uniform, black gakuran jacket, male student",
        "negative_prompt": "worst quality, low quality, bad anatomy, duplicate boy",
        "loras": []
    }

    standard_attending = [
        {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "standing calmly",
            "negative_prompt_override": "",
            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
        },
        {
            "character_id": "char_bob",
            "enabled": True,
            "prompt_override": "standing calmly",
            "negative_prompt_override": "",
            "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}
        }
    ]

    standard_overrides = {
        "1": {
            "char_alice": {"area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}},
            "char_bob": {"area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}}
        }
    }

    # 1. WF44: Native 20s with base_only_steps=0
    wf44 = build_phase3i2_workflow(
        wf_filename="44_VERIFY_NATIVE20_BASEONLY_ZERO.json",
        title="WF44: Native 20-step with base_only_steps=0 (Euler 20s, CFG 7.0, base_only=0)",
        save_prefix="Phase3I2_44_Native20_BaseOnly_Zero",
        characters=[char_alice, char_bob],
        attending_chars=standard_attending,
        staging_overrides=standard_overrides,
        fast_draft_12=False,
        steps=20,
        cfg=7.0,
        base_only_steps=0,
        guide_style="mannequin_capsule",
        controlnet_strength=0.75,
        controlnet_start=0.0,
        controlnet_end=0.80,
        propagate_controlnet_to_regions=False,
        regional_control_mode="off",
        regional_control_strength=0.35
    )
    p44 = os.path.join(WORKFLOWS_DIR, "44_VERIFY_NATIVE20_BASEONLY_ZERO.json")
    with open(p44, "w", encoding="utf-8") as f:
        json.dump(wf44, f, indent=2, ensure_ascii=False)
    print(f"Generated: {p44}")

    # 2. WF45: Native 12s Control (Euler 12s, CFG 6.0, No LoRA, base_only=2)
    wf45 = build_phase3i2_workflow(
        wf_filename="45_VERIFY_NATIVE12_CONTROL.json",
        title="WF45: Native 12-step Control (Euler 12s, CFG 6.0, No LoRA, base_only=2)",
        save_prefix="Phase3I2_45_Native12_Control",
        characters=[char_alice, char_bob],
        attending_chars=standard_attending,
        staging_overrides=standard_overrides,
        fast_draft_12=False,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        guide_style="mannequin_capsule",
        controlnet_strength=0.75,
        controlnet_start=0.0,
        controlnet_end=0.80,
        propagate_controlnet_to_regions=False,
        regional_control_mode="off",
        regional_control_strength=0.35
    )
    p45 = os.path.join(WORKFLOWS_DIR, "45_VERIFY_NATIVE12_CONTROL.json")
    with open(p45, "w", encoding="utf-8") as f:
        json.dump(wf45, f, indent=2, ensure_ascii=False)
    print(f"Generated: {p45}")

    # 3. WF46: Hyper12 Causal Control (Euler 12s, CFG 6.0, Hyper LoRA, base_only=2)
    wf46 = build_phase3i2_workflow(
        wf_filename="46_VERIFY_HYPER12_CAUSAL_CONTROL.json",
        title="WF46: Hyper12 Causal Control (Euler 12s, CFG 6.0, Hyper LoRA, base_only=2)",
        save_prefix="Phase3I2_46_Hyper12_Causal_Control",
        characters=[char_alice, char_bob],
        attending_chars=standard_attending,
        staging_overrides=standard_overrides,
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        guide_style="mannequin_capsule",
        controlnet_strength=0.75,
        controlnet_start=0.0,
        controlnet_end=0.80,
        propagate_controlnet_to_regions=False,
        regional_control_mode="off",
        regional_control_strength=0.35
    )
    p46 = os.path.join(WORKFLOWS_DIR, "46_VERIFY_HYPER12_CAUSAL_CONTROL.json")
    with open(p46, "w", encoding="utf-8") as f:
        json.dump(wf46, f, indent=2, ensure_ascii=False)
    print(f"Generated: {p46}")

    # 4. WF47: Per-Region Hint Attenuated (Euler 20s, CFG 7.0, per_region_hint 0.35, base_only=2)
    wf47 = build_phase3i2_workflow(
        wf_filename="47_VERIFY_PER_REGION_HINT_ATTENUATED.json",
        title="WF47: Per-Region Hint Attenuated (Euler 20s, CFG 7.0, per_region_hint 0.35, base_only=2)",
        save_prefix="Phase3I2_47_Per_Region_Hint_Attenuated",
        characters=[char_alice, char_bob],
        attending_chars=standard_attending,
        staging_overrides=standard_overrides,
        fast_draft_12=False,
        steps=20,
        cfg=7.0,
        base_only_steps=2,
        guide_style="mannequin_capsule",
        controlnet_strength=0.75,
        controlnet_start=0.0,
        controlnet_end=0.80,
        propagate_controlnet_to_regions=False,
        regional_control_mode="per_region_hint",
        regional_control_strength=0.35
    )
    p47 = os.path.join(WORKFLOWS_DIR, "47_VERIFY_PER_REGION_HINT_ATTENUATED.json")
    with open(p47, "w", encoding="utf-8") as f:
        json.dump(wf47, f, indent=2, ensure_ascii=False)
    print(f"Generated: {p47}")


if __name__ == "__main__":
    generate_all_phase3i2_workflows()
