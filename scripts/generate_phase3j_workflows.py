"""
Generate Phase 3J Canonical Workflows (48, 49, 50, 51, 52, 53)
================================================================
Generates:
- 48_VERIFY_BASE_BACKGROUND_ONLY_CHARACTER_PRESENCE.json:
    Canonical Base v2 (Background-only Base: empty courtyard, no students) + Alice L / Bob R (Hyper12, Base-Only CN)
- 49_VERIFY_ALICE_LEFT_ONLY_HYPER12.json:
    Single-Character Side Bias A1: Alice Left only (Hyper12, Background-only Base)
- 50_VERIFY_ALICE_RIGHT_ONLY_HYPER12.json:
    Single-Character Side Bias A2: Alice Right only (Hyper12, Background-only Base)
- 51_VERIFY_BOB_LEFT_ONLY_HYPER12.json:
    Single-Character Side Bias B1: Bob Left only (Hyper12, Background-only Base)
- 52_VERIFY_BOB_RIGHT_ONLY_HYPER12.json:
    Single-Character Side Bias B2: Bob Right only (Hyper12, Background-only Base)
- 53_VERIFY_HYPER12_PER_REGION_HINT_SWAP.json:
    Phase 3J Primary Oracle: Bob Left / Alice Right + Clean Per-Region Hint v2 (no-box, 0.35 str, 0.60 end, Hyper12)
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
# Canonical Base v2: Strictly background/style only. NO character/student/person mentions!
CANONICAL_BASE_V2 = f"{GLOBAL_STYLE}, empty school courtyard, clear open foreground, simple architectural background"
LEGACY_BASE_PROMPT = f"{GLOBAL_STYLE}, simple school courtyard, two students standing"
PANEL_SCENE_PROMPT = "school courtyard background, open walkway, afternoon"
GLOBAL_NEGATIVE = "worst quality, low quality, bad anatomy, blurry"


def build_phase3j_workflow(
    wf_filename: str,
    title: str,
    save_prefix: str,
    characters: list,
    attending_chars: list,
    staging_overrides: dict,
    fast_draft_12: bool = True,
    steps: int = 12,
    cfg: float = 6.0,
    base_only_steps: int = 2,
    base_prompt: str = CANONICAL_BASE_V2,
    panel_scene_prompt: str = PANEL_SCENE_PROMPT,
    guide_style: str = "mannequin_capsule",
    include_character_bbox_outline: bool = True,
    controlnet_strength: float = 0.75,
    controlnet_start: float = 0.0,
    controlnet_end: float = 0.80,
    propagate_controlnet_to_regions: bool = False,
    regional_control_mode: str = "off",
    regional_control_strength: float = 0.35,
    regional_control_end_percent: float = 0.60,
    ordering_mode: str = "scene_first",
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
                "prompt": panel_scene_prompt if panel_scene_prompt else PANEL_SCENE_PROMPT,
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
        # 3. CLIPTextEncode Global Scene Positive (Base Positive)
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
            "widgets_values": [base_prompt]
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
        # 31. TegakiMangaLayoutGuideGenerator (Phase 3J)
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
                {"name": "guide_image", "type": "IMAGE", "links": [302, 305], "slot_index": 0},
                {"name": "layout_mask", "type": "MASK", "links": [], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": [], "slot_index": 2}
            ],
            "widgets_values": [1, guide_style, "Black on White", 4, True, 1024, 1024, include_character_bbox_outline]
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
                ordering_mode, "scene_composed", True, False, 0, 0, 0.0, "linear",
                propagate_controlnet_to_regions,
                regional_control_mode,
                regional_control_strength,
                regional_control_end_percent
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
        },
        # 33. SaveImage (Auxiliary Layout Guide)
        {
            "id": 33,
            "type": "SaveImage",
            "pos": [1120, 500],
            "size": [300, 120],
            "flags": {},
            "order": 20,
            "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 305}],
            "widgets_values": [f"{save_prefix}_guide"]
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
        [304, 32, 1, 5, 4, "CONDITIONING"],
        [305, 31, 0, 33, 0, "IMAGE"]
    ]

    if fast_draft_12:
        links.extend([
            [101, 1, 0, 40, 0, "MODEL"],
            [102, 40, 1, 3, 0, "CLIP"]
        ])

    wf = {
        "last_node_id": 45,
        "last_link_id": 310,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {
            "ds": {"scale": 1.0, "offset": [0, 0]},
            "title": title
        },
        "version": 0.4
    }

    out_path = os.path.join(WORKFLOWS_DIR, wf_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print(f"Generated Phase 3J workflow: {wf_filename}")
    return out_path


def generate_all_phase3j_workflows():
    cast_characters = [
        {
            "id": "char_alice",
            "name": "Alice",
            "gender": "female",
            "appearance": "1girl, solo, dark hair, twintails, school uniform, blazer, pleated skirt",
            "negative_prompt": "1boy, male, duplicate, blurry"
        },
        {
            "id": "char_bob",
            "name": "Bob",
            "gender": "male",
            "appearance": "1boy, solo, short spiky hair, school uniform, standing",
            "negative_prompt": "1girl, female, duplicate, blurry"
        }
    ]

    alice_left = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    alice_right = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    bob_left = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    bob_right = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}

    # 48: Background-Only Base + Two Characters (Alice L / Bob R)
    build_phase3j_workflow(
        wf_filename="48_VERIFY_BASE_BACKGROUND_ONLY_CHARACTER_PRESENCE.json",
        title="Verify Base Background-Only Character Presence (Workflow 48)",
        save_prefix="Tegaki/Phase3J/WF48_BackgroundOnlyBase_AliceL_BobR",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_alice", "acting": "standing calmly on left", "importance": "primary", "area": alice_left},
            {"character_id": "char_bob", "acting": "standing listening on right", "importance": "secondary", "area": bob_right}
        ],
        staging_overrides={
            "char_alice": {"area": alice_left, "pose_preset": "standing_neutral"},
            "char_bob": {"area": bob_right, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        regional_control_mode="off"
    )

    # 49: Alice Left Only (Single Character Side Bias A1)
    build_phase3j_workflow(
        wf_filename="49_VERIFY_ALICE_LEFT_ONLY_HYPER12.json",
        title="Verify Alice Left Only Hyper12 (Workflow 49)",
        save_prefix="Tegaki/Phase3J/WF49_Alice_Left_Only",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_alice", "acting": "standing calmly on left", "importance": "primary", "area": alice_left}
        ],
        staging_overrides={
            "char_alice": {"area": alice_left, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        regional_control_mode="off"
    )

    # 50: Alice Right Only (Single Character Side Bias A2)
    build_phase3j_workflow(
        wf_filename="50_VERIFY_ALICE_RIGHT_ONLY_HYPER12.json",
        title="Verify Alice Right Only Hyper12 (Workflow 50)",
        save_prefix="Tegaki/Phase3J/WF50_Alice_Right_Only",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_alice", "acting": "standing calmly on right", "importance": "primary", "area": alice_right}
        ],
        staging_overrides={
            "char_alice": {"area": alice_right, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        regional_control_mode="off"
    )

    # 51: Bob Left Only (Single Character Side Bias B1)
    build_phase3j_workflow(
        wf_filename="51_VERIFY_BOB_LEFT_ONLY_HYPER12.json",
        title="Verify Bob Left Only Hyper12 (Workflow 51)",
        save_prefix="Tegaki/Phase3J/WF51_Bob_Left_Only",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_bob", "acting": "standing on left", "importance": "primary", "area": bob_left}
        ],
        staging_overrides={
            "char_bob": {"area": bob_left, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        regional_control_mode="off"
    )

    # 52: Bob Right Only (Single Character Side Bias B2)
    build_phase3j_workflow(
        wf_filename="52_VERIFY_BOB_RIGHT_ONLY_HYPER12.json",
        title="Verify Bob Right Only Hyper12 (Workflow 52)",
        save_prefix="Tegaki/Phase3J/WF52_Bob_Right_Only",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_bob", "acting": "standing on right", "importance": "primary", "area": bob_right}
        ],
        staging_overrides={
            "char_bob": {"area": bob_right, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        regional_control_mode="off"
    )

    # 53: Primary Oracle: Bob Left / Alice Right + Clean Per-Region Hint v2
    build_phase3j_workflow(
        wf_filename="53_VERIFY_HYPER12_PER_REGION_HINT_SWAP.json",
        title="Verify Hyper12 Per-Region Hint Swap (Workflow 53)",
        save_prefix="Tegaki/Phase3J/WF53_Hyper12_PRH_v2_BobL_AliceR",
        characters=cast_characters,
        attending_chars=[
            {"character_id": "char_bob", "acting": "standing on left", "importance": "secondary", "area": bob_left},
            {"character_id": "char_alice", "acting": "standing calmly on right", "importance": "primary", "area": alice_right}
        ],
        staging_overrides={
            "char_bob": {"area": bob_left, "pose_preset": "standing_neutral"},
            "char_alice": {"area": alice_right, "pose_preset": "standing_neutral"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        base_prompt=CANONICAL_BASE_V2,
        include_character_bbox_outline=False,
        regional_control_mode="per_region_hint",
        regional_control_strength=0.35,
        regional_control_end_percent=0.60
    )


if __name__ == "__main__":
    generate_all_phase3j_workflows()
