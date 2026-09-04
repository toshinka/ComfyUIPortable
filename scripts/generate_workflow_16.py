import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec

def build_workflow_16():
    layout_spec_3_basic = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    layout_spec_json = json.dumps(layout_spec_3_basic, indent=2, ensure_ascii=False)

    region_spec_data = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d, blurry",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28,
                "prompt": "classroom, two people talking, medium shot",
                "negative_prompt": "empty room, solo",
                "local_regions": [
                    {
                        "id": "lr_window_desks",
                        "name": "Window Desks",
                        "enabled": True,
                        "prompt": "school desks near the window, sunlight streaming, notebooks on desk",
                        "negative_prompt": "dark, shadow",
                        "area": {"x": 0.10, "y": 0.15, "w": 0.38, "h": 0.70}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "annoyed expression, looking right",
                        "negative_prompt_override": "happy, smiling",
                        "area": {"x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "laughing expression, looking left",
                        "negative_prompt_override": "crying, sad",
                        "area": {"x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                    }
                ]
            },
            {
                "id": 2,
                "name": "KOMA 2",
                "enabled": True,
                "x": 0.06, "y": 0.36, "w": 0.42, "h": 0.38,
                "prompt": "school corridor, walking scene",
                "negative_prompt": "",
                "local_regions": [
                    {
                        "id": "lr_wall_posters",
                        "name": "Wall Posters",
                        "enabled": True,
                        "prompt": "posters on school wall, bulletin board with flyers",
                        "negative_prompt": "",
                        "area": {"x": 0.55, "y": 0.10, "w": 0.40, "h": 0.45}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "walking away, back view",
                        "area": None
                    }
                ]
            },
            {
                "id": 3,
                "name": "KOMA 3",
                "enabled": True,
                "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.38,
                "prompt": "school grounds outside, boy waiting by fence, afternoon",
                "negative_prompt": "",
                "local_regions": [],
                "characters": [
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "standing by fence, looking up at sky",
                        "area": {"x": 0.20, "y": 0.10, "w": 0.60, "h": 0.80}
                    }
                ]
            }
        ]
    }
    region_spec_json = json.dumps(region_spec_data, indent=2, ensure_ascii=False)

    cast_spec_data = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
                "negative_prompt": "blurry, low quality",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short brown hair, school uniform",
                "negative_prompt": "bad anatomy",
                "loras": []
            }
        ]
    }
    cast_spec_json = json.dumps(cast_spec_data, indent=2, ensure_ascii=False)

    workflow = {
        "last_node_id": 16,
        "last_link_id": 21,
        "nodes": [
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
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [3], "slot_index": 2}
                ],
                "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "ControlNetLoader",
                "pos": [40, 220],
                "size": [320, 80],
                "flags": {},
                "order": 1,
                "mode": 0,
                "outputs": [
                    {"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [4], "slot_index": 0}
                ],
                "widgets_values": ["CN-anytest4_illustrious2_A.safetensors"]
            },
            {
                "id": 3,
                "type": "EmptyLatentImage",
                "pos": [40, 340],
                "size": [320, 110],
                "flags": {},
                "order": 2,
                "mode": 0,
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [5], "slot_index": 0}
                ],
                "widgets_values": [832, 1216, 1]
            },
            {
                "id": 4,
                "type": "TegakiLoraPromptLoader",
                "pos": [380, 80],
                "size": [380, 180],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2},
                    {"name": "optional_lora_stack", "type": "LORA_STACK", "link": None}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [6], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [7], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": None, "slot_index": 2},
                    {"name": "lora_stack", "type": "LORA_STACK", "links": None, "slot_index": 3}
                ],
                "widgets_values": ["<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"]
            },
            {
                "id": 5,
                "type": "TegakiMangaRegionEditor",
                "pos": [40, 490],
                "size": [540, 780],
                "flags": {},
                "order": 4,
                "mode": 0,
                "outputs": [
                    {"name": "region_spec", "type": "REGION_SPEC", "links": [8], "slot_index": 0},
                    {"name": "region_spec_json", "type": "STRING", "links": None, "slot_index": 1},
                    {"name": "global_prompt", "type": "STRING", "links": None, "slot_index": 2},
                    {"name": "preview_image", "type": "IMAGE", "links": [9], "slot_index": 3},
                    {"name": "mask_batch", "type": "MASK", "links": None, "slot_index": 4}
                ],
                "widgets_values": [
                    3,
                    832,
                    1216,
                    "manga page, monochrome, expressive linework, high contrast, screentone shading",
                    region_spec_json
                ]
            },
            {
                "id": 6,
                "type": "TegakiMangaPageCompiler",
                "pos": [600, 490],
                "size": [480, 520],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "region_spec", "type": "REGION_SPEC", "link": 8}
                ],
                "outputs": [
                    {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "links": [10], "slot_index": 0},
                    {"name": "page_compile_plan_json", "type": "STRING", "links": None, "slot_index": 1},
                    {"name": "global_loras_text", "type": "STRING", "links": None, "slot_index": 2},
                    {"name": "active_panels_count", "type": "INT", "links": None, "slot_index": 3}
                ],
                "widgets_values": [
                    cast_spec_json,
                    "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"
                ]
            },
            {
                "id": 7,
                "type": "TegakiMangaPanelLayoutEditor",
                "pos": [1100, 490],
                "size": [440, 520],
                "flags": {},
                "order": 6,
                "mode": 0,
                "outputs": [
                    {"name": "layout_image", "type": "IMAGE", "links": [11, 12], "slot_index": 0},
                    {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "links": [13], "slot_index": 1},
                    {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 2}
                ],
                "widgets_values": [
                    832,
                    1216,
                    4,
                    layout_spec_json
                ]
            },
            {
                "id": 8,
                "type": "TegakiMangaLayoutAwareConditioningBuilder",
                "pos": [1560, 80],
                "size": [420, 360],
                "flags": {},
                "order": 7,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 7},
                    {"name": "page_compile_plan", "type": "PAGE_COMPILE_PLAN", "link": 10},
                    {"name": "panel_layout_spec", "type": "PANEL_LAYOUT_SPEC", "link": 13}
                ],
                "outputs": [
                    {"name": "positive", "type": "CONDITIONING", "links": [14], "slot_index": 0},
                    {"name": "negative", "type": "CONDITIONING", "links": [15], "slot_index": 1},
                    {"name": "panel_masks", "type": "MASK", "links": None, "slot_index": 2},
                    {"name": "character_masks", "type": "MASK", "links": None, "slot_index": 3},
                    {"name": "mask_preview", "type": "IMAGE", "links": [16], "slot_index": 4},
                    {"name": "debug_json", "type": "STRING", "links": None, "slot_index": 5},
                    {"name": "local_region_masks", "type": "MASK", "links": None, "slot_index": 6}
                ],
                "widgets_values": [
                    1.0,
                    0.9,
                    "default",
                    0.8,
                    0
                ]
            },
            {
                "id": 9,
                "type": "ControlNetApplyAdvanced",
                "pos": [2000, 80],
                "size": [340, 260],
                "flags": {},
                "order": 8,
                "mode": 0,
                "inputs": [
                    {"name": "positive", "type": "CONDITIONING", "link": 14},
                    {"name": "negative", "type": "CONDITIONING", "link": 15},
                    {"name": "control_net", "type": "CONTROL_NET", "link": 4},
                    {"name": "image", "type": "IMAGE", "link": 11}
                ],
                "outputs": [
                    {"name": "positive", "type": "CONDITIONING", "links": [17], "slot_index": 0},
                    {"name": "negative", "type": "CONDITIONING", "links": [18], "slot_index": 1}
                ],
                "widgets_values": [
                    0.6,
                    0.0,
                    1.0
                ]
            },
            {
                "id": 10,
                "type": "KSampler",
                "pos": [2360, 80],
                "size": [320, 480],
                "flags": {},
                "order": 9,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 6},
                    {"name": "positive", "type": "CONDITIONING", "link": 17},
                    {"name": "negative", "type": "CONDITIONING", "link": 18},
                    {"name": "latent_image", "type": "LATENT", "link": 5}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}
                ],
                "widgets_values": [
                    42,
                    "fixed",
                    20,
                    6.0,
                    "euler",
                    "normal",
                    1.0
                ]
            },
            {
                "id": 11,
                "type": "VAEDecode",
                "pos": [2700, 80],
                "size": [240, 120],
                "flags": {},
                "order": 10,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 19},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [20, 21], "slot_index": 0}
                ],
                "widgets_values": []
            },
            {
                "id": 12,
                "type": "SaveImage",
                "pos": [2960, 80],
                "size": [380, 560],
                "flags": {},
                "order": 11,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 20}
                ],
                "widgets_values": [
                    "Tegaki/MangaLayoutFusion/WF16_POC"
                ]
            },
            {
                "id": 13,
                "type": "PreviewImage",
                "pos": [2700, 240],
                "size": [240, 320],
                "flags": {},
                "order": 12,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 21}
                ],
                "widgets_values": []
            },
            {
                "id": 14,
                "type": "PreviewImage",
                "pos": [1100, 1030],
                "size": [440, 400],
                "flags": {},
                "order": 13,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 12}
                ],
                "widgets_values": []
            },
            {
                "id": 15,
                "type": "PreviewImage",
                "pos": [1560, 460],
                "size": [420, 460],
                "flags": {},
                "order": 14,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 16}
                ],
                "widgets_values": []
            },
            {
                "id": 16,
                "type": "PreviewImage",
                "pos": [40, 1290],
                "size": [540, 400],
                "flags": {},
                "order": 15,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 9}
                ],
                "widgets_values": []
            }
        ],
        "links": [
            [1, 1, 0, 4, 0, "MODEL"],
            [2, 1, 1, 4, 1, "CLIP"],
            [3, 1, 2, 11, 1, "VAE"],
            [4, 2, 0, 9, 2, "CONTROL_NET"],
            [5, 3, 0, 10, 3, "LATENT"],
            [6, 4, 0, 10, 0, "MODEL"],
            [7, 4, 1, 8, 0, "CLIP"],
            [8, 5, 0, 6, 0, "REGION_SPEC"],
            [9, 5, 3, 16, 0, "IMAGE"],
            [10, 6, 0, 8, 1, "PAGE_COMPILE_PLAN"],
            [11, 7, 0, 9, 3, "IMAGE"],
            [12, 7, 0, 14, 0, "IMAGE"],
            [13, 7, 1, 8, 2, "PANEL_LAYOUT_SPEC"],
            [14, 8, 0, 9, 0, "CONDITIONING"],
            [15, 8, 1, 9, 1, "CONDITIONING"],
            [16, 8, 4, 15, 0, "IMAGE"],
            [17, 9, 0, 10, 1, "CONDITIONING"],
            [18, 9, 1, 10, 2, "CONDITIONING"],
            [19, 10, 0, 11, 0, "LATENT"],
            [20, 11, 0, 12, 0, "IMAGE"],
            [21, 11, 0, 13, 0, "IMAGE"]
        ],
        "groups": [],
        "config": {},
        "extra": {},
        "version": 0.4
    }

    out_path = os.path.join(PROJECT_ROOT, "workflows", "16_MANGA_VARIABLE_N_REGION_LAYOUT_FUSION_POC.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"Generated Workflow 16 at: {out_path}")

if __name__ == "__main__":
    build_workflow_16()
