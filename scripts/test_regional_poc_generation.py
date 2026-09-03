import json
import urllib.request
import urllib.parse
import time
import os
import sys

COMFY_URL = "http://127.0.0.1:8188"


def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
        return json.loads(resp.read().decode('utf-8'))


def wait_for_prompt(prompt_id, timeout=180):
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            return outputs
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout} seconds")


def build_poc_prompt(
    koma1_prompt="classroom, two people talking, medium shot",
    alice_prompt="1girl, blonde twin tails, blue eyes, school uniform",
    bob_prompt="1boy, short brown hair, school uniform",
    global_prompt="manga page, monochrome, expressive linework, high contrast, screentone shading",
    global_lora="<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>",
    save_prefix="Tegaki/RegionalPOC/POC",
    seed=42,
    steps=15
):
    # KOMA 1 の Prompt を反映
    region_spec_data = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": global_prompt,
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28,
                "prompt": koma1_prompt,
                "negative_prompt": "empty room, solo",
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
                "prompt": "school corridor, window sunlight, walking scene",
                "negative_prompt": "",
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
                "prompt": "sunset rooftop, sky and clouds, dramatic lighting, empty scenic",
                "negative_prompt": "people, person, character",
                "characters": []
            }
        ]
    }

    cast_spec_data = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": alice_prompt,
                "negative_prompt": "blurry, low quality",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": bob_prompt,
                "negative_prompt": "bad anatomy",
                "loras": []
            }
        ]
    }

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
            }
        },
        "2": {
            "class_type": "TegakiLoraPromptLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "text": global_lora
            }
        },
        "3": {
            "class_type": "TegakiMangaRegionEditor",
            "inputs": {
                "panel_count": 3,
                "canvas_width": 832,
                "canvas_height": 1216,
                "global_prompt": global_prompt,
                "region_spec_data": json.dumps(region_spec_data)
            }
        },
        "5": {
            "class_type": "TegakiMangaPageCompiler",
            "inputs": {
                "region_spec": ["3", 0],
                "cast_spec": json.dumps(cast_spec_data),
                "global_loras": global_lora
            }
        },
        "8": {
            "class_type": "TegakiMangaConditioningBuilder",
            "inputs": {
                "clip": ["2", 1],
                "page_compile_plan": ["5", 0],
                "panel_strength": 1.0,
                "character_strength": 1.0,
                "set_cond_area": "default"
            }
        },
        "9": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1
            }
        },
        "10": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["8", 0],
                "negative": ["8", 1],
                "latent_image": ["9", 0],
                "seed": seed,
                "control_after_generate": "fixed",
                "steps": steps,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["10", 0],
                "vae": ["1", 2]
            }
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["11", 0],
                "filename_prefix": save_prefix
            }
        }
    }
    return workflow


def run_ab_tests():
    print("================================================================================")
    print("Phase 3B End-to-End Manga Regional Generation A/B Verification")
    print("================================================================================")

    test_runs = [
        {
            "name": "Base_A (Baseline: Classroom, Alice=Blonde, Bob=Brown, MangaStyle, LoRA=ON)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Base_A",
            "params": {}
        },
        {
            "name": "Test1_Panel_B (KOMA 1 = Convenience store interior)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Test1_Panel_B",
            "params": {
                "koma1_prompt": "convenience store interior, brightly lit, shelves with items, two people talking, medium shot"
            }
        },
        {
            "name": "Test2_Alice_B (Alice = Blue twintails)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Test2_Alice_B",
            "params": {
                "alice_prompt": "1girl, blue twintails, blue eyes, school uniform"
            }
        },
        {
            "name": "Test3_Bob_B (Bob = Pink hair)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Test3_Bob_B",
            "params": {
                "bob_prompt": "1boy, pink hair, short hair, school uniform"
            }
        },
        {
            "name": "Test4_Global_B (Global = Vibrant watercolor)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Test4_Global_B",
            "params": {
                "global_prompt": "manga page, vibrant watercolor, colorful, soft pastel tones, artistic"
            }
        },
        {
            "name": "Test5_LoRA_B (Global LoRA = OFF)",
            "save_prefix": "Tegaki/RegionalPOC/POC_Test5_LoRA_B",
            "params": {
                "global_lora": ""
            }
        }
    ]

    results = []

    for idx, test in enumerate(test_runs):
        print(f"\n[{idx+1}/{len(test_runs)}] Queueing: {test['name']}...")
        wf = build_poc_prompt(save_prefix=test["save_prefix"], **test["params"])
        resp = queue_prompt(wf)
        pid = resp["prompt_id"]
        print(f"  Prompt ID: {pid}, Waiting for generation...")
        outputs = wait_for_prompt(pid)
        save_node_output = outputs.get("12", {}).get("images", [])
        saved_file = save_node_output[0]["filename"] if save_node_output else "Unknown"
        print(f"  [SUCCESS] Generated: {saved_file}")
        results.append({
            "test": test["name"],
            "prompt_id": pid,
            "filename": saved_file
        })

    print("\n================================================================================")
    print("A/B GENERATION RESULTS SUMMARY")
    print("================================================================================")
    for r in results:
        print(f"• {r['test']} -> {r['filename']}")
    print("================================================================================")
    return results


if __name__ == "__main__":
    run_ab_tests()
