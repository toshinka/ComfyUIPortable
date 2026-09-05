"""
Generate Canonical Workflows 60-65 for Phase 3K
=================================================
60: 60_VERIFY_POSE_FACING_EACH_OTHER.json
61: 61_VERIFY_POSE_FACING_OUTWARD.json
62: 62_VERIFY_POSE_SITTING_SINGLE.json
63: 63_VERIFY_INTERACTION_HANDSHAKE.json
64: 64_VERIFY_CAMERA_DISTANCE_NEAR.json
65: 65_VERIFY_CAMERA_DISTANCE_FAR.json

Key Phase 3K Upgrades:
- Directional poses: facing_left, facing_right
- Sitting pose: sitting with bent-leg horizontal lap
- Pair interaction: handshake midpoint anchor
- Camera distance contract: near, medium, far (explicit staging > camera default)
- Complete node/link schema parity with Workflows 54-59
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
CHECKPOINT_NAME = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
HYPERSD_LORA_NAME = "調整\\Hyper-SDXL-12steps-CFG-lora.safetensors"
CONTROLNET_NAME = "CN-anytest4_illustrious2_A.safetensors"

CANONICAL_BASE_V2 = "manga illustration, monochrome expressive linework, high quality, empty school courtyard, clear open foreground, simple architectural background"
BASE_NEGATIVE_PROMPT = "worst quality, low quality, bad anatomy, blurry, text, watermark"
PANEL_SCENE_PROMPT = "school courtyard background, open walkway, afternoon"


def make_canonical_character(
    char_id: str,
    name: str,
    gender: str,
    prompt: str,
    negative_prompt: str = "",
    loras=None,
    metadata=None
) -> Dict[str, Any]:
    assert prompt and prompt.strip(), f"Canonical character '{char_id}' must have a non-empty prompt!"
    return {
        "id": char_id,
        "name": name,
        "gender": gender,
        "enabled": True,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "loras": loras or [],
        "metadata": metadata or {}
    }


def make_character_binding(
    character_id: str,
    prompt_override: str = "",
    negative_prompt_override: str = "",
    area: Optional[Dict[str, float]] = None,
    shot_type: str = "full_body",
    pose_preset: str = "standing_neutral",
    interaction: Optional[str] = None,
    enabled: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    meta = metadata or {}
    meta["semantic_role"] = meta.get("semantic_role", "primary")
    if shot_type:
        meta["shot_type"] = shot_type
    if pose_preset:
        meta["pose_preset"] = pose_preset
    if interaction:
        meta["interaction"] = interaction

    binding = {
        "character_id": character_id,
        "enabled": enabled,
        "prompt_override": prompt_override,
        "negative_prompt_override": negative_prompt_override,
        "area": area,
        "shot_type": shot_type,
        "pose_preset": pose_preset,
        "interaction": interaction,
        "metadata": meta
    }
    return binding


ALICE_CANONICAL = make_canonical_character(
    char_id="char_alice",
    name="Alice",
    gender="female",
    prompt="1girl, blonde twin tails, blue eyes, school uniform, pleated skirt, full body",
    negative_prompt="1boy, male, duplicate person, blurry"
)

BOB_CANONICAL = make_canonical_character(
    char_id="char_bob",
    name="Bob",
    gender="male",
    prompt="1boy, short black hair, dark school uniform, male student, full body",
    negative_prompt="1girl, female, duplicate person, blurry"
)

ALICE_LEFT = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
ALICE_RIGHT = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
BOB_LEFT = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
BOB_RIGHT = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
SITTING_AREA = {"x": 0.25, "y": 0.25, "w": 0.50, "h": 0.65, "width": 0.50, "height": 0.65}


def build_phase3k_workflow(
    wf_filename: str,
    title: str,
    save_prefix: str,
    characters: List[Dict[str, Any]],
    attending_chars: List[Dict[str, Any]],
    staging_overrides: Dict[str, Any],
    camera_distance: str = "medium",
    fast_draft_12: bool = True,
    steps: int = 12,
    cfg: float = 6.0,
    base_only_steps: int = 2,
    seed: int = 42,
    base_prompt: str = CANONICAL_BASE_V2,
    character_prompt_mode: str = "standalone",
    remainder_mask_mode: bool = True,
    include_panel_border: bool = False,
    include_character_bbox_outline: bool = False,
    regional_control_mode: str = "off",
    regional_control_strength: float = 0.35,
    regional_control_end_percent: float = 0.60,
    include_panel_backgrounds: bool = True,
    ordering_mode: str = "scene_first"
) -> str:
    cast_data = {"version": 1, "characters": characters}
    cast_json = json.dumps(cast_data, indent=2, ensure_ascii=False)

    panel_content_data = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "panel_count": 1,
        "global_prompt": base_prompt,
        "global_negative_prompt": BASE_NEGATIVE_PROMPT,
        "panels": [
            {
                "id": 1,
                "name": "Panel 1",
                "enabled": True,
                "camera_distance": camera_distance,
                "prompt": PANEL_SCENE_PROMPT,
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

    controlnet_strength = 0.75
    controlnet_start = 0.0
    controlnet_end = 0.80

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
                {"name": "VAE", "type": "VAE", "links": [4], "slot_index": 2}
            ],
            "widgets_values": [CHECKPOINT_NAME]
        }
    ]

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
            "widgets_values": [HYPERSD_LORA_NAME, 1.0, 1.0]
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
        # 3. CLIPTextEncode Global Positive
        {
            "id": 3,
            "type": "CLIPTextEncode",
            "pos": [400, 80],
            "size": [340, 140],
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
            "pos": [400, 250],
            "size": [340, 140],
            "flags": {},
            "order": 4,
            "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [7], "slot_index": 0}],
            "widgets_values": [BASE_NEGATIVE_PROMPT]
        },
        # 30. ControlNetLoader
        {
            "id": 30,
            "type": "ControlNetLoader",
            "pos": [400, 420],
            "size": [340, 80],
            "flags": {},
            "order": 5,
            "mode": 0,
            "outputs": [{"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [301], "slot_index": 0}],
            "widgets_values": [CONTROLNET_NAME]
        },
        # 31. TegakiMangaLayoutGuideGenerator (Clean Guide)
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
            "widgets_values": [1, "mannequin_capsule", "Black on White", 4, include_panel_border, 1024, 1024, include_character_bbox_outline]
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
                ordering_mode,
                character_prompt_mode,
                include_panel_backgrounds,
                remainder_mask_mode,
                0,
                0,
                0.0,
                "linear",
                False,
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
            "size": [260, 180],
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
    print(f"Generated Phase 3K workflow: {wf_filename}")
    return out_path


def generate_all_phase3k_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)
    cast_characters = [ALICE_CANONICAL, BOB_CANONICAL]

    # 60: Two Characters Facing Each Other
    build_phase3k_workflow(
        wf_filename="60_VERIFY_POSE_FACING_EACH_OTHER.json",
        title="Verify Pose Facing Each Other (Workflow 60)",
        save_prefix="Tegaki/Phase3K/WF60_Facing_Each_Other",
        characters=cast_characters,
        attending_chars=[
            make_character_binding("char_alice", prompt_override="looking towards right, talking", area=ALICE_LEFT, pose_preset="facing_right"),
            make_character_binding("char_bob", prompt_override="looking towards left, listening", area=BOB_RIGHT, pose_preset="facing_left")
        ],
        staging_overrides={
            "char_alice": {"area": ALICE_LEFT, "pose_preset": "facing_right", "shot_type": "full_body"},
            "char_bob": {"area": BOB_RIGHT, "pose_preset": "facing_left", "shot_type": "full_body"}
        },
        camera_distance="medium",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )

    # 61: Two Characters Facing Outward
    build_phase3k_workflow(
        wf_filename="61_VERIFY_POSE_FACING_OUTWARD.json",
        title="Verify Pose Facing Outward (Workflow 61)",
        save_prefix="Tegaki/Phase3K/WF61_Facing_Outward",
        characters=cast_characters,
        attending_chars=[
            make_character_binding("char_alice", prompt_override="looking away towards left", area=ALICE_LEFT, pose_preset="facing_left"),
            make_character_binding("char_bob", prompt_override="looking away towards right", area=BOB_RIGHT, pose_preset="facing_right")
        ],
        staging_overrides={
            "char_alice": {"area": ALICE_LEFT, "pose_preset": "facing_left", "shot_type": "full_body"},
            "char_bob": {"area": BOB_RIGHT, "pose_preset": "facing_right", "shot_type": "full_body"}
        },
        camera_distance="medium",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )

    # 62: Single Character Sitting
    build_phase3k_workflow(
        wf_filename="62_VERIFY_POSE_SITTING_SINGLE.json",
        title="Verify Pose Sitting Single (Workflow 62)",
        save_prefix="Tegaki/Phase3K/WF62_Sitting_Single",
        characters=[ALICE_CANONICAL],
        attending_chars=[
            make_character_binding("char_alice", prompt_override="sitting relaxed on a bench", area=SITTING_AREA, pose_preset="sitting")
        ],
        staging_overrides={
            "char_alice": {"area": SITTING_AREA, "pose_preset": "sitting", "shot_type": "full_body"}
        },
        camera_distance="medium",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )

    # 63: Pair Interaction Handshake
    hs_alice_area = {"x": 0.15, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    hs_bob_area = {"x": 0.50, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    build_phase3k_workflow(
        wf_filename="63_VERIFY_INTERACTION_HANDSHAKE.json",
        title="Verify Interaction Handshake (Workflow 63)",
        save_prefix="Tegaki/Phase3K/WF63_Interaction_Handshake",
        characters=cast_characters,
        attending_chars=[
            make_character_binding("char_alice", prompt_override="reaching out right hand to shake hands", area=hs_alice_area, pose_preset="facing_right", interaction="handshake"),
            make_character_binding("char_bob", prompt_override="reaching out left hand to shake hands", area=hs_bob_area, pose_preset="facing_left", interaction="handshake")
        ],
        staging_overrides={
            "char_alice": {"area": hs_alice_area, "pose_preset": "facing_right", "interaction": "handshake", "shot_type": "full_body"},
            "char_bob": {"area": hs_bob_area, "pose_preset": "facing_left", "interaction": "handshake", "shot_type": "full_body"}
        },
        camera_distance="medium",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )

    # 64: Camera Distance Near (Default Staging Fallback)
    build_phase3k_workflow(
        wf_filename="64_VERIFY_CAMERA_DISTANCE_NEAR.json",
        title="Verify Camera Distance Near (Workflow 64)",
        save_prefix="Tegaki/Phase3K/WF64_Camera_Distance_Near",
        characters=[ALICE_CANONICAL],
        attending_chars=[
            make_character_binding("char_alice", prompt_override="standing near the viewer", area=None, shot_type="bust")
        ],
        staging_overrides={},
        camera_distance="near",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )

    # 65: Camera Distance Far (Default Staging Fallback)
    build_phase3k_workflow(
        wf_filename="65_VERIFY_CAMERA_DISTANCE_FAR.json",
        title="Verify Camera Distance Far (Workflow 65)",
        save_prefix="Tegaki/Phase3K/WF65_Camera_Distance_Far",
        characters=[ALICE_CANONICAL],
        attending_chars=[
            make_character_binding("char_alice", prompt_override="standing far in the courtyard", area=None, shot_type="full_body")
        ],
        staging_overrides={},
        camera_distance="far",
        fast_draft_12=True,
        steps=12,
        cfg=6.0,
        base_only_steps=2,
        character_prompt_mode="standalone",
        remainder_mask_mode=True
    )


if __name__ == "__main__":
    generate_all_phase3k_workflows()
