import json
import os

workflows_dir = os.path.abspath("workflows")
os.makedirs(workflows_dir, exist_ok=True)

def create_txt2img_workflow():
    wf = {
        "last_node_id": 10,
        "last_link_id": 10,
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
                    {"name": "VAE", "type": "VAE", "links": [7], "slot_index": 2}
                ],
                "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [400, 220],
                "flags": {},
                "order": 1,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2},
                    {"name": "optional_lora_stack", "type": "LORA_STACK", "link": None}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [3], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [4, 5], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [6], "slot_index": 2},
                    {"name": "lora_stack", "type": "LORA_STACK", "links": None, "slot_index": 3}
                ],
                "widgets_values": [
                    "masterpiece, best quality, 1girl, solo, manga frame, expressive pose, dynamic angle, highly detailed,\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.7>"
                ]
            },
            {
                "id": 3,
                "type": "CLIPTextEncode",
                "pos": [840, 80],
                "size": [400, 160],
                "flags": {},
                "order": 2,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 4},
                    {"name": "text", "type": "STRING", "link": 6, "widget": {"name": "text"}}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [8], "slot_index": 0}
                ],
                "widgets_values": [""]
            },
            {
                "id": 4,
                "type": "CLIPTextEncode",
                "pos": [840, 280],
                "size": [400, 140],
                "flags": {},
                "order": 3,
                "mode": 0,
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 5}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [9], "slot_index": 0}
                ],
                "widgets_values": [
                    "worst quality, low quality, bad anatomy, bad hands, missing fingers, extra digits, watermark, text"
                ]
            },
            {
                "id": 5,
                "type": "EmptyLatentImage",
                "pos": [840, 460],
                "size": [300, 110],
                "flags": {},
                "order": 4,
                "mode": 0,
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [10], "slot_index": 0}
                ],
                "widgets_values": [832, 1216, 1]
            },
            {
                "id": 6,
                "type": "KSampler",
                "pos": [1280, 80],
                "size": [320, 470],
                "flags": {},
                "order": 5,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 3},
                    {"name": "positive", "type": "CONDITIONING", "link": 8},
                    {"name": "negative", "type": "CONDITIONING", "link": 9},
                    {"name": "latent_image", "type": "LATENT", "link": 10}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [11], "slot_index": 0}
                ],
                "widgets_values": [
                    42, "randomize", 28, 6.0, "euler_ancestral", "normal", 1.0
                ]
            },
            {
                "id": 7,
                "type": "VAEDecode",
                "pos": [1640, 80],
                "size": [210, 50],
                "flags": {},
                "order": 6,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 11},
                    {"name": "vae", "type": "VAE", "link": 7}
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [12], "slot_index": 0}
                ],
                "widgets_values": []
            },
            {
                "id": 8,
                "type": "SaveImage",
                "pos": [1880, 80],
                "size": [450, 500],
                "flags": {},
                "order": 7,
                "mode": 0,
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 12}
                ],
                "widgets_values": ["Tegaki/Txt2Img/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "MODEL"],
            [2, 1, 1, 2, 1, "CLIP"],
            [3, 2, 0, 6, 0, "MODEL"],
            [4, 2, 1, 3, 0, "CLIP"],
            [5, 2, 1, 4, 0, "CLIP"],
            [6, 2, 2, 3, 1, "STRING"],
            [7, 1, 2, 7, 1, "VAE"],
            [8, 3, 0, 6, 1, "CONDITIONING"],
            [9, 4, 0, 6, 2, "CONDITIONING"],
            [10, 5, 0, 6, 3, "LATENT"],
            [11, 6, 0, 7, 0, "LATENT"],
            [12, 7, 0, 8, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Model & LoRA Syntax", "bounding": [20, 20, 790, 560], "color": "#3f789e"},
            {"title": "2. Prompts & Latent", "bounding": [820, 20, 430, 560], "color": "#8f6b3e"},
            {"title": "3. Sampling & Output", "bounding": [1260, 20, 1100, 600], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "01_BASIC_ILLUSTRIOUS_TXT2IMG.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 01_BASIC_ILLUSTRIOUS_TXT2IMG.json")

def create_i2i_workflow():
    wf = {
        "last_node_id": 12,
        "last_link_id": 14,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [40, 80],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [3, 4], "slot_index": 2}
                ],
                "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "LoadImage",
                "pos": [40, 240],
                "size": [320, 320],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [5], "slot_index": 0},
                    {"name": "MASK", "type": "MASK", "links": None, "slot_index": 1}
                ],
                "widgets_values": ["example.png", "image"]
            },
            {
                "id": 3,
                "type": "VAEEncode",
                "pos": [400, 360],
                "size": [210, 50],
                "inputs": [
                    {"name": "pixels", "type": "IMAGE", "link": 5},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [6], "slot_index": 0}
                ]
            },
            {
                "id": 4,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [400, 220],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [7], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [8, 9], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [10], "slot_index": 2}
                ],
                "widgets_values": [
                    "masterpiece, best quality, refined linework, detailed manga art, highres"
                ]
            },
            {
                "id": 5,
                "type": "CLIPTextEncode",
                "pos": [840, 80],
                "size": [400, 140],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 8},
                    {"name": "text", "type": "STRING", "link": 10, "widget": {"name": "text"}}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [11], "slot_index": 0}
                ],
                "widgets_values": [""]
            },
            {
                "id": 6,
                "type": "CLIPTextEncode",
                "pos": [840, 260],
                "size": [400, 140],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 9}
                ],
                "outputs": [
                    {"name": "CONDITIONING", "type": "CONDITIONING", "links": [12], "slot_index": 0}
                ],
                "widgets_values": ["worst quality, low quality, blurry, deformed"]
            },
            {
                "id": 7,
                "type": "KSampler",
                "pos": [1280, 80],
                "size": [320, 470],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 7},
                    {"name": "positive", "type": "CONDITIONING", "link": 11},
                    {"name": "negative", "type": "CONDITIONING", "link": 12},
                    {"name": "latent_image", "type": "LATENT", "link": 6}
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [13], "slot_index": 0}
                ],
                "widgets_values": [
                    42, "randomize", 28, 6.0, "euler_ancestral", "normal", 0.60
                ]
            },
            {
                "id": 8,
                "type": "VAEDecode",
                "pos": [1640, 80],
                "size": [210, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 13},
                    {"name": "vae", "type": "VAE", "link": 4}
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [14], "slot_index": 0}
                ]
            },
            {
                "id": 9,
                "type": "SaveImage",
                "pos": [1880, 80],
                "size": [450, 500],
                "inputs": [
                    {"name": "images", "type": "IMAGE", "link": 14}
                ],
                "widgets_values": ["Tegaki/I2I/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 4, 0, "MODEL"],
            [2, 1, 1, 4, 1, "CLIP"],
            [3, 1, 2, 3, 1, "VAE"],
            [4, 1, 2, 8, 1, "VAE"],
            [5, 2, 0, 3, 0, "IMAGE"],
            [6, 3, 0, 7, 3, "LATENT"],
            [7, 4, 0, 7, 0, "MODEL"],
            [8, 4, 1, 5, 0, "CLIP"],
            [9, 4, 1, 6, 0, "CLIP"],
            [10, 4, 2, 5, 1, "STRING"],
            [11, 5, 0, 7, 1, "CONDITIONING"],
            [12, 6, 0, 7, 2, "CONDITIONING"],
            [13, 7, 0, 8, 0, "LATENT"],
            [14, 8, 0, 9, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Source Image & VAE Encode", "bounding": [20, 20, 360, 560], "color": "#7a5c3e"},
            {"title": "2. LoRA / Prompt / Denoise", "bounding": [380, 20, 880, 560], "color": "#3f789e"},
            {"title": "3. Sampling & I2I Result", "bounding": [1260, 20, 1100, 600], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "02_ILLUSTRIOUS_I2I.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 02_ILLUSTRIOUS_I2I.json")

def create_regional_prompt_workflow():
    # Regional Prompt using Conditioning (Set Mask)
    wf = {
        "last_node_id": 16,
        "last_link_id": 20,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [40, 80],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [15], "slot_index": 2}
                ],
                "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [380, 160],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [3], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [4, 5, 6, 7], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": None, "slot_index": 2}
                ],
                "widgets_values": ["<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.6>"]
            },
            # Base global prompt
            {
                "id": 3,
                "type": "CLIPTextEncode",
                "pos": [820, 60],
                "size": [360, 110],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 4}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [8], "slot_index": 0}],
                "widgets_values": ["manga page, monochrome tone, classroom background, cinematic composition"]
            },
            # Region A (Left Panel / Character 1)
            {
                "id": 4,
                "type": "CLIPTextEncode",
                "pos": [820, 200],
                "size": [360, 110],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 5}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [9], "slot_index": 0}],
                "widgets_values": ["1girl, black hair, smiling, school uniform, looking right"]
            },
            {
                "id": 5,
                "type": "SolidMask",
                "pos": [820, 340],
                "size": [240, 130],
                "outputs": [{"name": "MASK", "type": "MASK", "links": [10], "slot_index": 0}],
                "widgets_values": [1.0, 416, 1216]
            },
            {
                "id": 6,
                "type": "ConditioningSetMask",
                "pos": [1100, 200],
                "size": [240, 110],
                "inputs": [
                    {"name": "conditioning", "type": "CONDITIONING", "link": 9},
                    {"name": "mask", "type": "MASK", "link": 10}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [11], "slot_index": 0}],
                "widgets_values": [0.9, "default"]
            },
            # Region B (Right Panel / Character 2)
            {
                "id": 7,
                "type": "CLIPTextEncode",
                "pos": [820, 500],
                "size": [360, 110],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 6}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [12], "slot_index": 0}],
                "widgets_values": ["1boy, blonde hair, surprised expression, school blazer, looking left"]
            },
            {
                "id": 8,
                "type": "SolidMask",
                "pos": [820, 640],
                "size": [240, 130],
                "outputs": [{"name": "MASK", "type": "MASK", "links": [13], "slot_index": 0}],
                "widgets_values": [1.0, 416, 1216]
            },
            {
                "id": 9,
                "type": "ConditioningSetMask",
                "pos": [1100, 500],
                "size": [240, 110],
                "inputs": [
                    {"name": "conditioning", "type": "CONDITIONING", "link": 12},
                    {"name": "mask", "type": "MASK", "link": 13}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [14], "slot_index": 0}],
                "widgets_values": [0.9, "default"]
            },
            # Conditioning Combine
            {
                "id": 10,
                "type": "ConditioningCombine",
                "pos": [1380, 80],
                "size": [210, 60],
                "inputs": [
                    {"name": "conditioning_1", "type": "CONDITIONING", "link": 8},
                    {"name": "conditioning_2", "type": "CONDITIONING", "link": 11}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [16], "slot_index": 0}]
            },
            {
                "id": 11,
                "type": "ConditioningCombine",
                "pos": [1380, 180],
                "size": [210, 60],
                "inputs": [
                    {"name": "conditioning_1", "type": "CONDITIONING", "link": 16},
                    {"name": "conditioning_2", "type": "CONDITIONING", "link": 14}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [17], "slot_index": 0}]
            },
            # Negative
            {
                "id": 12,
                "type": "CLIPTextEncode",
                "pos": [1380, 280],
                "size": [320, 110],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 7}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [18], "slot_index": 0}],
                "widgets_values": ["worst quality, low quality, bad anatomy, deformed"]
            },
            {
                "id": 13,
                "type": "EmptyLatentImage",
                "pos": [1380, 420],
                "size": [280, 110],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [19], "slot_index": 0}],
                "widgets_values": [832, 1216, 1]
            },
            {
                "id": 14,
                "type": "KSampler",
                "pos": [1740, 80],
                "size": [320, 470],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 3},
                    {"name": "positive", "type": "CONDITIONING", "link": 17},
                    {"name": "negative", "type": "CONDITIONING", "link": 18},
                    {"name": "latent_image", "type": "LATENT", "link": 19}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [20], "slot_index": 0}],
                "widgets_values": [42, "randomize", 28, 6.0, "euler_ancestral", "normal", 1.0]
            },
            {
                "id": 15,
                "type": "VAEDecode",
                "pos": [2100, 80],
                "size": [210, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 20},
                    {"name": "vae", "type": "VAE", "link": 15}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [21], "slot_index": 0}]
            },
            {
                "id": 16,
                "type": "SaveImage",
                "pos": [2340, 80],
                "size": [450, 500],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 21}],
                "widgets_values": ["Tegaki/Regional/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "MODEL"],
            [2, 1, 1, 2, 1, "CLIP"],
            [3, 2, 0, 14, 0, "MODEL"],
            [4, 2, 1, 3, 0, "CLIP"],
            [5, 2, 1, 4, 0, "CLIP"],
            [6, 2, 1, 7, 0, "CLIP"],
            [7, 2, 1, 12, 0, "CLIP"],
            [8, 3, 0, 10, 0, "CONDITIONING"],
            [9, 4, 0, 6, 0, "CONDITIONING"],
            [10, 5, 0, 6, 1, "MASK"],
            [11, 6, 0, 10, 1, "CONDITIONING"],
            [12, 7, 0, 9, 0, "CONDITIONING"],
            [13, 8, 0, 9, 1, "MASK"],
            [14, 9, 0, 11, 1, "CONDITIONING"],
            [15, 1, 2, 15, 1, "VAE"],
            [16, 10, 0, 11, 0, "CONDITIONING"],
            [17, 11, 0, 14, 1, "CONDITIONING"],
            [18, 12, 0, 14, 2, "CONDITIONING"],
            [19, 13, 0, 14, 3, "LATENT"],
            [20, 14, 0, 15, 0, "LATENT"],
            [21, 15, 0, 16, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Base Model & LoRA", "bounding": [20, 20, 770, 480], "color": "#3f789e"},
            {"title": "2. Multi-Region Prompt & Masks (Panels)", "bounding": [800, 20, 900, 800], "color": "#8f6b3e"},
            {"title": "3. Sampling & Render", "bounding": [1720, 20, 1100, 600], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "03_MANGA_REGIONAL_PROMPT.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 03_MANGA_REGIONAL_PROMPT.json")

def create_regional_lora_workflow():
    # Regional LoRA Experiment Workflow (RLL先行実験)
    # Inspire Pack / Impact Pack RegionalSampler or Regional Conditioning with separated patched models
    wf = {
        "last_node_id": 14,
        "last_link_id": 18,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [40, 80],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1, 2], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [3, 4], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [5], "slot_index": 2}
                ],
                "widgets_values": ["♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"]
            },
            # LoRA A for Region A
            {
                "id": 2,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [360, 200],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 3}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [6], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [7], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [8], "slot_index": 2},
                    {"name": "lora_stack", "type": "LORA_STACK", "links": [9], "slot_index": 3}
                ],
                "widgets_values": ["1girl, warrior armor, dynamic sword action,\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.8>"]
            },
            # LoRA B for Region B
            {
                "id": 3,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 320],
                "size": [360, 200],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 2},
                    {"name": "clip", "type": "CLIP", "link": 4}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [10], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [11], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [12], "slot_index": 2},
                    {"name": "lora_stack", "type": "LORA_STACK", "links": [13], "slot_index": 3}
                ],
                "widgets_values": ["1girl, wizard robe, spell casting magic circle,\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"]
            },
            # Conditioning & Mask for Region A
            {
                "id": 4,
                "type": "CLIPTextEncode",
                "pos": [800, 80],
                "size": [320, 100],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 7},
                    {"name": "text", "type": "STRING", "link": 8, "widget": {"name": "text"}}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [14], "slot_index": 0}]
            },
            # Conditioning & Mask for Region B
            {
                "id": 5,
                "type": "CLIPTextEncode",
                "pos": [800, 320],
                "size": [320, 100],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 11},
                    {"name": "text", "type": "STRING", "link": 12, "widget": {"name": "text"}}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [15], "slot_index": 0}]
            },
            # Negative
            {
                "id": 6,
                "type": "CLIPTextEncode",
                "pos": [800, 460],
                "size": [320, 100],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 7}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [16], "slot_index": 0}],
                "widgets_values": ["worst quality, low quality, bad anatomy"]
            },
            {
                "id": 7,
                "type": "EmptyLatentImage",
                "pos": [800, 580],
                "size": [280, 100],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [17], "slot_index": 0}],
                "widgets_values": [832, 1216, 1]
            },
            # Sampler
            {
                "id": 8,
                "type": "KSampler",
                "pos": [1200, 80],
                "size": [320, 470],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 6},
                    {"name": "positive", "type": "CONDITIONING", "link": 14},
                    {"name": "negative", "type": "CONDITIONING", "link": 16},
                    {"name": "latent_image", "type": "LATENT", "link": 17}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [18], "slot_index": 0}],
                "widgets_values": [42, "randomize", 28, 6.0, "euler_ancestral", "normal", 1.0]
            },
            {
                "id": 9,
                "type": "VAEDecode",
                "pos": [1560, 80],
                "size": [210, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 18},
                    {"name": "vae", "type": "VAE", "link": 5}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [19], "slot_index": 0}]
            },
            {
                "id": 10,
                "type": "SaveImage",
                "pos": [1800, 80],
                "size": [450, 500],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 19}],
                "widgets_values": ["Tegaki/RegionalLoRA/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "MODEL"],
            [2, 1, 0, 3, 0, "MODEL"],
            [3, 1, 1, 2, 1, "CLIP"],
            [4, 1, 1, 3, 1, "CLIP"],
            [5, 1, 2, 9, 1, "VAE"],
            [6, 2, 0, 8, 0, "MODEL"],
            [7, 2, 1, 4, 0, "CLIP"],
            [8, 2, 2, 4, 1, "STRING"],
            [9, 2, 3, None, 0, "LORA_STACK"],
            [10, 3, 0, None, 0, "MODEL"],
            [11, 3, 1, 5, 0, "CLIP"],
            [12, 3, 2, 5, 1, "STRING"],
            [13, 3, 3, None, 0, "LORA_STACK"],
            [14, 4, 0, 8, 1, "CONDITIONING"],
            [15, 5, 0, None, 0, "CONDITIONING"],
            [16, 6, 0, 8, 2, "CONDITIONING"],
            [17, 7, 0, 8, 3, "LATENT"],
            [18, 8, 0, 9, 0, "LATENT"],
            [19, 9, 0, 10, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Base Checkpoint", "bounding": [20, 20, 360, 480], "color": "#3f789e"},
            {"title": "2. Region-Specific LoRA Stacks (RLL Lab)", "bounding": [380, 20, 390, 600], "color": "#7a3e9e"},
            {"title": "3. Regional Conditioning & Sampling", "bounding": [780, 20, 1500, 700], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "04_REGIONAL_LORA_EXPERIMENT.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 04_REGIONAL_LORA_EXPERIMENT.json")

def create_controlnet_workflow():
    wf = {
        "last_node_id": 12,
        "last_link_id": 16,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [40, 80],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [3], "slot_index": 2}
                ],
                "widgets_values": ["waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "ControlNetLoader",
                "pos": [40, 220],
                "size": [320, 80],
                "outputs": [{"name": "CONTROL_NET", "type": "CONTROL_NET", "links": [4], "slot_index": 0}],
                "widgets_values": ["controlnet_xl.safetensors"]
            },
            {
                "id": 3,
                "type": "LoadImage",
                "pos": [40, 340],
                "size": [320, 320],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [5], "slot_index": 0}
                ],
                "widgets_values": ["pose_guide.png", "image"]
            },
            {
                "id": 4,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [380, 160],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [6], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [7, 8], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [9], "slot_index": 2}
                ],
                "widgets_values": ["masterpiece, manga composition, dynamic angle, high contrast"]
            },
            {
                "id": 5,
                "type": "CLIPTextEncode",
                "pos": [800, 80],
                "size": [360, 120],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 7},
                    {"name": "text", "type": "STRING", "link": 9, "widget": {"name": "text"}}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [10], "slot_index": 0}]
            },
            {
                "id": 6,
                "type": "ControlNetApplyAdvanced",
                "pos": [800, 240],
                "size": [360, 180],
                "inputs": [
                    {"name": "positive", "type": "CONDITIONING", "link": 10},
                    {"name": "negative", "type": "CONDITIONING", "link": 11},
                    {"name": "control_net", "type": "CONTROL_NET", "link": 4},
                    {"name": "image", "type": "IMAGE", "link": 5}
                ],
                "outputs": [
                    {"name": "positive", "type": "CONDITIONING", "links": [12], "slot_index": 0},
                    {"name": "negative", "type": "CONDITIONING", "links": [13], "slot_index": 1}
                ],
                "widgets_values": [0.85, 0.0, 0.75]
            },
            {
                "id": 7,
                "type": "CLIPTextEncode",
                "pos": [800, 460],
                "size": [360, 100],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 8}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [11], "slot_index": 0}],
                "widgets_values": ["worst quality, low quality, bad anatomy"]
            },
            {
                "id": 8,
                "type": "EmptyLatentImage",
                "pos": [800, 580],
                "size": [280, 100],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [14], "slot_index": 0}],
                "widgets_values": [832, 1216, 1]
            },
            {
                "id": 9,
                "type": "KSampler",
                "pos": [1200, 80],
                "size": [320, 470],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 6},
                    {"name": "positive", "type": "CONDITIONING", "link": 12},
                    {"name": "negative", "type": "CONDITIONING", "link": 13},
                    {"name": "latent_image", "type": "LATENT", "link": 14}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [15], "slot_index": 0}],
                "widgets_values": [42, "randomize", 28, 6.0, "euler_ancestral", "normal", 1.0]
            },
            {
                "id": 10,
                "type": "VAEDecode",
                "pos": [1560, 80],
                "size": [210, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 15},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [16], "slot_index": 0}]
            },
            {
                "id": 11,
                "type": "SaveImage",
                "pos": [1800, 80],
                "size": [450, 500],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 16}],
                "widgets_values": ["Tegaki/ControlNet/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 4, 0, "MODEL"],
            [2, 1, 1, 4, 1, "CLIP"],
            [3, 1, 2, 10, 1, "VAE"],
            [4, 2, 0, 6, 2, "CONTROL_NET"],
            [5, 3, 0, 6, 3, "IMAGE"],
            [6, 4, 0, 9, 0, "MODEL"],
            [7, 4, 1, 5, 0, "CLIP"],
            [8, 4, 1, 7, 0, "CLIP"],
            [9, 4, 2, 5, 1, "STRING"],
            [10, 5, 0, 6, 0, "CONDITIONING"],
            [11, 7, 0, 6, 1, "CONDITIONING"],
            [12, 6, 0, 9, 1, "CONDITIONING"],
            [13, 6, 1, 9, 2, "CONDITIONING"],
            [14, 8, 0, 9, 3, "LATENT"],
            [15, 9, 0, 10, 0, "LATENT"],
            [16, 10, 0, 11, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Model & ControlNet Guide", "bounding": [20, 20, 360, 660], "color": "#3f789e"},
            {"title": "2. Advanced ControlNet Conditioning", "bounding": [780, 20, 400, 680], "color": "#8f5b3e"},
            {"title": "3. Sampling & Save", "bounding": [1180, 20, 1100, 600], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "05_CONTROLNET_COMPOSITION.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 05_CONTROLNET_COMPOSITION.json")

def create_lora_mix_workflow():
    wf = {
        "last_node_id": 10,
        "last_link_id": 12,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [40, 80],
                "size": [320, 100],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [3], "slot_index": 2}
                ],
                "widgets_values": ["waiIllustriousSDXL_v170.safetensors"]
            },
            {
                "id": 2,
                "type": "TegakiLoraPromptLoader",
                "pos": [400, 80],
                "size": [440, 280],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "clip", "type": "CLIP", "link": 2}
                ],
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [4], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [5, 6], "slot_index": 1},
                    {"name": "clean_text", "type": "STRING", "links": [7], "slot_index": 2},
                    {"name": "lora_stack", "type": "LORA_STACK", "links": [8], "slot_index": 3}
                ],
                "widgets_values": [
                    "masterpiece, best quality, 1girl, highly expressive, retro manga aesthetic,\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.25>"
                ]
            },
            {
                "id": 3,
                "type": "TegakiLoraStackToPrompt",
                "pos": [400, 390],
                "size": [440, 140],
                "inputs": [{"name": "lora_stack", "type": "LORA_STACK", "link": 8}],
                "outputs": [{"name": "lora_prompt_text", "type": "STRING", "links": None, "slot_index": 0}]
            },
            {
                "id": 4,
                "type": "CLIPTextEncode",
                "pos": [880, 80],
                "size": [380, 140],
                "inputs": [
                    {"name": "clip", "type": "CLIP", "link": 5},
                    {"name": "text", "type": "STRING", "link": 7, "widget": {"name": "text"}}
                ],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [9], "slot_index": 0}]
            },
            {
                "id": 5,
                "type": "CLIPTextEncode",
                "pos": [880, 260],
                "size": [380, 120],
                "inputs": [{"name": "clip", "type": "CLIP", "link": 6}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [10], "slot_index": 0}],
                "widgets_values": ["worst quality, low quality, bad anatomy"]
            },
            {
                "id": 6,
                "type": "EmptyLatentImage",
                "pos": [880, 420],
                "size": [280, 100],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [11], "slot_index": 0}],
                "widgets_values": [832, 1216, 1]
            },
            {
                "id": 7,
                "type": "KSampler",
                "pos": [1300, 80],
                "size": [320, 470],
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 4},
                    {"name": "positive", "type": "CONDITIONING", "link": 9},
                    {"name": "negative", "type": "CONDITIONING", "link": 10},
                    {"name": "latent_image", "type": "LATENT", "link": 11}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [12], "slot_index": 0}],
                "widgets_values": [12345, "randomize", 28, 6.0, "euler_ancestral", "normal", 1.0]
            },
            {
                "id": 8,
                "type": "VAEDecode",
                "pos": [1660, 80],
                "size": [210, 50],
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 12},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [13], "slot_index": 0}]
            },
            {
                "id": 9,
                "type": "SaveImage",
                "pos": [1900, 80],
                "size": [450, 500],
                "inputs": [{"name": "images", "type": "IMAGE", "link": 13}],
                "widgets_values": ["Tegaki/LoraMix/Illustrious"]
            }
        ],
        "links": [
            [1, 1, 0, 2, 0, "MODEL"],
            [2, 1, 1, 2, 1, "CLIP"],
            [3, 1, 2, 8, 1, "VAE"],
            [4, 2, 0, 7, 0, "MODEL"],
            [5, 2, 1, 4, 0, "CLIP"],
            [6, 2, 1, 5, 0, "CLIP"],
            [7, 2, 2, 4, 1, "STRING"],
            [8, 2, 3, 3, 0, "LORA_STACK"],
            [9, 4, 0, 7, 1, "CONDITIONING"],
            [10, 5, 0, 7, 2, "CONDITIONING"],
            [11, 6, 0, 7, 3, "LATENT"],
            [12, 7, 0, 8, 0, "LATENT"],
            [13, 8, 0, 9, 0, "IMAGE"]
        ],
        "groups": [
            {"title": "1. Multi-LoRA Mix Lab", "bounding": [20, 20, 840, 560], "color": "#7a3e9e"},
            {"title": "2. Prompt & Canvas", "bounding": [860, 20, 410, 560], "color": "#8f6b3e"},
            {"title": "3. Sampling & Output", "bounding": [1280, 20, 1100, 600], "color": "#3f8e5b"}
        ],
        "version": 0.4
    }
    with open(os.path.join(workflows_dir, "06_LORA_MIX_EXPERIMENT.json"), "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print("Created 06_LORA_MIX_EXPERIMENT.json")

if __name__ == "__main__":
    create_txt2img_workflow()
    create_i2i_workflow()
    create_regional_prompt_workflow()
    create_regional_lora_workflow()
    create_controlnet_workflow()
    create_lora_mix_workflow()
    print("All 6 workflows generated successfully!")
