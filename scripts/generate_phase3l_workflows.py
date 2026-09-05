"""
Generate Canonical Workflows 66-71 for Phase 3L
=================================================
66: 66_VERIFY_POSE_GUIDE_ONLY_INWARD.json
67: 67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json
68: 68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json
69: 69_VERIFY_MAINLINE_SUBSCENE_GEOMETRY_SWAP.json
70: 70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json
71: 71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json

Key Phase 3L Upgrades:
- Pure pose causality (zero directional prompt vocabulary)
- Canonical structured interaction dictionary & stable instance IDs
- Mainline SubScene integration (Hostile Oracle: 1 visible panel, 2 internal scenes)
- SubScene geometry swap test
- Mixed 4-panel page (1 complex panel with 2 subscenes, 3 simple panels)
- Prior-art backend adoption parity test (Inspire RegionalPromptSimple)
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.interaction_resolver import normalize_interaction

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
CHECKPOINT_NAME = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
HYPERSD_LORA_NAME = "調整\\Hyper-SDXL-12steps-CFG-lora.safetensors"
CONTROLNET_NAME = "CN-anytest4_illustrious2_A.safetensors"

CANONICAL_BASE_V2 = "manga illustration, monochrome expressive linework, high quality, school courtyard, simple architectural background"
BASE_NEGATIVE_PROMPT = "worst quality, low quality, bad anatomy, blurry, text, watermark"

ALICE_CANONICAL_PURE_PROMPT = "1girl, blonde twin tails, school uniform, standing calmly"
BOB_CANONICAL_PURE_PROMPT = "1boy, short dark hair, school uniform, standing calmly"


def make_canonical_character(
    char_id: str,
    name: str,
    gender: str,
    prompt: str,
    negative_prompt: str = "",
    loras=None,
    metadata=None
) -> Dict[str, Any]:
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
    instance_id: Optional[str] = None,
    prompt_override: str = "",
    negative_prompt_override: str = "",
    area: Optional[Dict[str, float]] = None,
    shot_type: str = "full_body",
    pose_preset: str = "standing_neutral",
    interaction: Optional[Any] = None,
    enabled: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    meta = dict(metadata or {})
    if shot_type:
        meta["shot_type"] = shot_type
    if pose_preset:
        meta["pose_preset"] = pose_preset
    if interaction:
        meta["interaction"] = normalize_interaction(interaction, source_instance_id=instance_id)
    if instance_id:
        meta["instance_id"] = instance_id

    return {
        "instance_id": instance_id,
        "character_id": character_id,
        "enabled": enabled,
        "prompt_override": prompt_override,
        "negative_prompt_override": negative_prompt_override,
        "area": area,
        "shot_type": shot_type,
        "pose_preset": pose_preset,
        "interaction": normalize_interaction(interaction, source_instance_id=instance_id),
        "metadata": meta
    }


ALICE_CANONICAL = make_canonical_character(
    char_id="char_alice",
    name="Alice",
    gender="female",
    prompt=ALICE_CANONICAL_PURE_PROMPT,
    negative_prompt="1boy, male, duplicate person, blurry"
)

BOB_CANONICAL = make_canonical_character(
    char_id="char_bob",
    name="Bob",
    gender="male",
    prompt=BOB_CANONICAL_PURE_PROMPT,
    negative_prompt="1girl, female, duplicate person, blurry"
)

ALICE_LEFT = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
ALICE_RIGHT = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
BOB_LEFT = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
BOB_RIGHT = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}


def build_phase3l_workflow(
    wf_filename: str,
    title: str,
    save_prefix: str,
    characters: List[Dict[str, Any]],
    panels: List[Dict[str, Any]],
    layout_preset: str = "1_full",
    layout_width: int = 1024,
    layout_height: int = 1024,
    staging_overrides: Optional[Dict[str, Any]] = None,
    fast_draft_12: bool = True,
    steps: int = 12,
    cfg: float = 6.0,
    base_only_steps: int = 2,
    seed: int = 42,
    base_prompt: str = CANONICAL_BASE_V2,
    character_prompt_mode: str = "standalone",
    remainder_mask_mode: bool = True,
    mask_feather: int = 0,
    ordering_mode: str = "scene_first",
    target_guide_panel_id: int = 1
) -> str:
    cast_data = {"version": 1, "characters": characters}
    cast_json = json.dumps(cast_data, indent=2, ensure_ascii=False)

    panel_content_data = {
        "version": 1,
        "canvas": {"width": layout_width, "height": layout_height},
        "panel_count": len(panels),
        "global_prompt": base_prompt,
        "global_negative_prompt": BASE_NEGATIVE_PROMPT,
        "panels": panels
    }
    panel_content_json = json.dumps(panel_content_data, indent=2, ensure_ascii=False)

    layout_data = get_default_panel_layout_spec(layout_width, layout_height, preset=layout_preset)
    layout_json = json.dumps(layout_data, indent=2, ensure_ascii=False)
    staging_overrides_json = json.dumps(staging_overrides or {}, indent=2, ensure_ascii=False)

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
            "widgets_values": [HYPERSD_LORA_NAME, 0.8, 0.8]
        })

    nodes.extend([
        # 2. EmptyLatentImage
        {
            "id": 2,
            "type": "EmptyLatentImage",
            "pos": [40, 320],
            "size": [320, 100],
            "flags": {},
            "order": 2,
            "mode": 0,
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}],
            "widgets_values": [layout_width, layout_height, 1]
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
                {"name": "guide_image", "type": "IMAGE", "links": [302, 305], "slot_index": 0},
                {"name": "layout_mask", "type": "MASK", "links": [], "slot_index": 1},
                {"name": "debug_json", "type": "STRING", "links": [], "slot_index": 2}
            ],
            "widgets_values": [target_guide_panel_id, "mannequin_capsule", "Black on White", 4, False, layout_width, layout_height, False]
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
            "widgets_values": [layout_width, layout_height, len(panels), layout_json]
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
                True,  # include_panel_backgrounds
                remainder_mask_mode,
                mask_feather,
                0,
                0.0,
                "linear",
                False,
                "off",  # regional_control_mode
                0.35,   # regional_control_strength
                0.60    # regional_control_end_percent
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
        [305, 31, 0, 33, 0, "IMAGE"],
    ]

    if fast_draft_12:
        links.extend([
            [101, 1, 0, 40, 0, "MODEL"],
            [102, 40, 1, 3, 0, "CLIP"]
        ])

    workflow = {
        "last_node_id": 45,
        "last_link_id": 310,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"title": title},
        "version": 0.4
    }

    out_path = os.path.join(WORKFLOWS_DIR, wf_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"Generated {wf_filename} -> {out_path}")
    return out_path


def generate_all_phase3l_workflows():
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)
    cast_characters = [ALICE_CANONICAL, BOB_CANONICAL]

    # 66: Verify Pose Guide-Only Inward
    # Alice on Left facing right, Bob on Right facing left. Prompts have ZERO directional tokens.
    p1_inward_chars = [
        make_character_binding(
            "char_alice",
            instance_id="p1_alice_01",
            prompt_override="standing calmly",
            area=ALICE_LEFT,
            pose_preset="facing_right"
        ),
        make_character_binding(
            "char_bob",
            instance_id="p1_bob_01",
            prompt_override="standing calmly",
            area=BOB_RIGHT,
            pose_preset="facing_left"
        )
    ]
    p1_inward = {
        "id": 1,
        "name": "Panel 1",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school courtyard walkway, afternoon",
        "negative_prompt": "blurry",
        "characters": p1_inward_chars,
        "subscenes": []
    }
    build_phase3l_workflow(
        wf_filename="66_VERIFY_POSE_GUIDE_ONLY_INWARD.json",
        title="Verify Pose Guide Only Inward (Workflow 66)",
        save_prefix="Tegaki/Phase3L/WF66_Pose_Guide_Only_Inward",
        characters=cast_characters,
        panels=[p1_inward],
        layout_preset="1_full",
        staging_overrides={
            "char_alice": {"area": ALICE_LEFT, "pose_preset": "facing_right", "shot_type": "full_body", "instance_id": "p1_alice_01"},
            "char_bob": {"area": BOB_RIGHT, "pose_preset": "facing_left", "shot_type": "full_body", "instance_id": "p1_bob_01"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )

    # 67: Verify Handshake Canonical Pair & Feather
    hs_alice_area = {"x": 0.15, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    hs_bob_area = {"x": 0.50, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    p1_handshake_chars = [
        make_character_binding(
            "char_alice",
            instance_id="p1_alice_01",
            prompt_override="reaching out right hand to shake hands",
            area=hs_alice_area,
            pose_preset="facing_right",
            interaction={
                "interaction_id": "int_handshake_p1",
                "type": "handshake",
                "role": "left_participant",
                "target_instance_id": "p1_bob_01"
            }
        ),
        make_character_binding(
            "char_bob",
            instance_id="p1_bob_01",
            prompt_override="reaching out left hand to shake hands",
            area=hs_bob_area,
            pose_preset="facing_left",
            interaction={
                "interaction_id": "int_handshake_p1",
                "type": "handshake",
                "role": "right_participant",
                "target_instance_id": "p1_alice_01"
            }
        )
    ]
    p1_handshake = {
        "id": 1,
        "name": "Panel 1",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school courtyard walkway, afternoon",
        "negative_prompt": "blurry",
        "characters": p1_handshake_chars,
        "subscenes": []
    }
    build_phase3l_workflow(
        wf_filename="67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json",
        title="Verify Handshake Canonical Pair and Feather (Workflow 67)",
        save_prefix="Tegaki/Phase3L/WF67_Handshake_Canonical_Pair",
        characters=cast_characters,
        panels=[p1_handshake],
        layout_preset="1_full",
        staging_overrides={
            "char_alice": {
                "area": hs_alice_area, "pose_preset": "facing_right", "shot_type": "full_body", "instance_id": "p1_alice_01",
                "interaction": {"interaction_id": "int_handshake_p1", "type": "handshake", "role": "left_participant", "target_instance_id": "p1_bob_01"}
            },
            "char_bob": {
                "area": hs_bob_area, "pose_preset": "facing_left", "shot_type": "full_body", "instance_id": "p1_bob_01",
                "interaction": {"interaction_id": "int_handshake_p1", "type": "handshake", "role": "right_participant", "target_instance_id": "p1_alice_01"}
            }
        },
        mask_feather=8,
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )

    # 68: Verify Mainline SubScene Conflict & Friendship (Hostile Oracle)
    # 1 visible panel, 2 internal SubScenes. Zero directional words in prompts.
    subscene_a_cf = {
        "id": "sub_a",
        "enabled": True,
        "prompt": "school gate background, tense confrontation",
        "negative_prompt": "smiling, laughing",
        "area": {"x": 0.0, "y": 0.0, "w": 0.50, "h": 1.0},
        "character_bindings": [
            make_character_binding(
                "char_alice",
                instance_id="p1_sub_a_alice_01",
                prompt_override="angry expression, arms crossed",
                area={"x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75},
                pose_preset="facing_left",
                interaction={
                    "interaction_id": "int_lookaway_sub_a",
                    "type": "look_away",
                    "role": "left_participant",
                    "target_instance_id": "p1_sub_a_bob_01"
                }
            ),
            make_character_binding(
                "char_bob",
                instance_id="p1_sub_a_bob_01",
                prompt_override="annoyed expression, looking away",
                area={"x": 0.55, "y": 0.15, "w": 0.40, "h": 0.75},
                pose_preset="facing_right",
                interaction={
                    "interaction_id": "int_lookaway_sub_a",
                    "type": "look_away",
                    "role": "right_participant",
                    "target_instance_id": "p1_sub_a_alice_01"
                }
            )
        ]
    }
    subscene_b_cf = {
        "id": "sub_b",
        "enabled": True,
        "prompt": "school garden background, blooming flowers, joyful atmosphere",
        "negative_prompt": "angry, conflict",
        "area": {"x": 0.50, "y": 0.0, "w": 0.50, "h": 1.0},
        "character_bindings": [
            make_character_binding(
                "char_alice",
                instance_id="p1_sub_b_alice_01",
                prompt_override="cheerful smiling expression, reaching hand out",
                area={"x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75},
                pose_preset="facing_right",
                interaction={
                    "interaction_id": "int_handshake_sub_b",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p1_sub_b_bob_01"
                }
            ),
            make_character_binding(
                "char_bob",
                instance_id="p1_sub_b_bob_01",
                prompt_override="happy smiling expression, reaching hand out",
                area={"x": 0.55, "y": 0.15, "w": 0.40, "h": 0.75},
                pose_preset="facing_left",
                interaction={
                    "interaction_id": "int_handshake_sub_b",
                    "type": "handshake",
                    "role": "right_participant",
                    "target_instance_id": "p1_sub_b_alice_01"
                }
            )
        ]
    }
    p1_subscenes_cf = {
        "id": 1,
        "name": "Panel 1",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school courtyard",
        "negative_prompt": "",
        "characters": [],
        "subscenes": [subscene_a_cf, subscene_b_cf]
    }
    build_phase3l_workflow(
        wf_filename="68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json",
        title="Verify Mainline SubScene Conflict & Friendship (Workflow 68)",
        save_prefix="Tegaki/Phase3L/WF68_Mainline_SubScene_Conflict_Friendship",
        characters=cast_characters,
        panels=[p1_subscenes_cf],
        layout_preset="1_full",
        staging_overrides={},
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )

    # 69: Verify Mainline SubScene Geometry Swap
    # Swap areas: SubScene A (Conflict) moved to Right (0.5..1.0), SubScene B (Friendship) moved to Left (0.0..0.5)
    subscene_a_swap = dict(subscene_a_cf)
    subscene_a_swap["area"] = {"x": 0.50, "y": 0.0, "w": 0.50, "h": 1.0}
    subscene_b_swap = dict(subscene_b_cf)
    subscene_b_swap["area"] = {"x": 0.0, "y": 0.0, "w": 0.50, "h": 1.0}

    p1_subscenes_swap = {
        "id": 1,
        "name": "Panel 1",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school courtyard",
        "negative_prompt": "",
        "characters": [],
        "subscenes": [subscene_a_swap, subscene_b_swap]
    }
    build_phase3l_workflow(
        wf_filename="69_VERIFY_MAINLINE_SUBSCENE_GEOMETRY_SWAP.json",
        title="Verify Mainline SubScene Geometry Swap (Workflow 69)",
        save_prefix="Tegaki/Phase3L/WF69_Mainline_SubScene_Geometry_Swap",
        characters=cast_characters,
        panels=[p1_subscenes_swap],
        layout_preset="1_full",
        staging_overrides={},
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )

    # 70: Verify 4-Panel Mixed Simple & Complex Page
    # 4 visible panels (4_grid layout), 5 internal scenes:
    # P1: Complex with 2 SubScenes (Conflict + Friendship)
    # P2: Simple (Alice watering flowers)
    # P3: Simple (Bob carrying plant)
    # P4: Simple (Alice + Bob conversation)
    mixed_p1 = {
        "id": 1,
        "name": "Panel 1",
        "enabled": True,
        "prompt": "school grounds",
        "negative_prompt": "",
        "characters": [],
        "subscenes": [subscene_a_cf, subscene_b_cf]
    }
    mixed_p2 = {
        "id": 2,
        "name": "Panel 2",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school botanical greenhouse",
        "negative_prompt": "",
        "characters": [
            make_character_binding(
                "char_alice",
                instance_id="p2_alice_01",
                prompt_override="watering blooming flowers with a watering can",
                area={"x": 0.20, "y": 0.15, "w": 0.60, "h": 0.75},
                pose_preset="standing_neutral"
            )
        ],
        "subscenes": []
    }
    mixed_p3 = {
        "id": 3,
        "name": "Panel 3",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school corridor, sunny day",
        "negative_prompt": "",
        "characters": [
            make_character_binding(
                "char_bob",
                instance_id="p3_bob_01",
                prompt_override="carrying a potted green plant carefully",
                area={"x": 0.20, "y": 0.15, "w": 0.60, "h": 0.75},
                pose_preset="standing_neutral"
            )
        ],
        "subscenes": []
    }
    mixed_p4 = {
        "id": 4,
        "name": "Panel 4",
        "enabled": True,
        "camera_distance": "medium",
        "prompt": "school courtyard bench, peaceful conversation",
        "negative_prompt": "",
        "characters": [
            make_character_binding(
                "char_alice",
                instance_id="p4_alice_01",
                prompt_override="smiling and talking cheerfully",
                area={"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75},
                pose_preset="facing_right"
            ),
            make_character_binding(
                "char_bob",
                instance_id="p4_bob_01",
                prompt_override="smiling and listening attentively",
                area={"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75},
                pose_preset="facing_left"
            )
        ],
        "subscenes": []
    }
    build_phase3l_workflow(
        wf_filename="70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json",
        title="Verify 4-Panel Mixed Simple & Complex Page (Workflow 70)",
        save_prefix="Tegaki/Phase3L/WF70_4Panel_Mixed_Simple_Complex_Page",
        characters=cast_characters,
        panels=[mixed_p1, mixed_p2, mixed_p3, mixed_p4],
        layout_preset="4_grid",
        staging_overrides={
            "char_alice": {"shot_type": "full_body"},
            "char_bob": {"shot_type": "full_body"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )

    # 71: Verify External Regional Backend Parity
    # Direct parity comparison workflow between Tegaki regional execution and Inspire RegionalPromptSimple
    build_phase3l_workflow(
        wf_filename="71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json",
        title="Verify External Regional Backend Parity (Workflow 71)",
        save_prefix="Tegaki/Phase3L/WF71_External_Regional_Backend_Parity",
        characters=cast_characters,
        panels=[p1_inward],
        layout_preset="1_full",
        staging_overrides={
            "char_alice": {"area": ALICE_LEFT, "pose_preset": "facing_right", "shot_type": "full_body"},
            "char_bob": {"area": BOB_RIGHT, "pose_preset": "facing_left", "shot_type": "full_body"}
        },
        fast_draft_12=True,
        steps=12,
        cfg=6.0
    )


if __name__ == "__main__":
    generate_all_phase3l_workflows()
