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


def build_expansion_prompt(
    with_local_regions=True,
    save_prefix="Tegaki/RegionalControl/Control",
    seed=42,
    steps=15
):
    if with_local_regions:
        k1_lrs = [
            {
                "id": "lr_window_desks",
                "name": "Window Desks",
                "enabled": True,
                "prompt": "school desks near the window, sunlight streaming, notebooks on desk",
                "negative_prompt": "dark, shadow",
                "area": {"x": 0.10, "y": 0.15, "w": 0.38, "h": 0.70}
            }
        ]
        k2_lrs = [
            {
                "id": "lr_wall_posters",
                "name": "Wall Posters",
                "enabled": True,
                "prompt": "posters on school wall, bulletin board with flyers",
                "negative_prompt": "",
                "area": {"x": 0.55, "y": 0.10, "w": 0.40, "h": 0.45}
            }
        ]
    else:
        k1_lrs = []
        k2_lrs = []

    region_spec_data = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28,
                "prompt": "classroom, two people talking, medium shot",
                "negative_prompt": "empty room, solo",
                "local_regions": k1_lrs,
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
                "local_regions": k2_lrs,
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
                "local_regions": [],
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

    global_lora = "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"

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
                "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
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
                "local_region_strength": 1.0,
                "set_cond_area": "default",
                "mask_feather": 0
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


def run_control_expansion_generation_tests():
    print("================================================================================")
    print("Phase 3B.1 Regional Control Expansion Generation Tests")
    print("================================================================================")

    test_runs = [
        {
            "name": "Test_Local_ON (Local Regions Active: K1 Window Desks, K2 Wall Posters)",
            "with_local_regions": True,
            "save_prefix": "Tegaki/RegionalControl/Control_Local_ON"
        },
        {
            "name": "Test_Local_OFF (Local Regions Inactive: Baseline without Local Regions)",
            "with_local_regions": False,
            "save_prefix": "Tegaki/RegionalControl/Control_Local_OFF"
        }
    ]

    results = []

    for idx, test in enumerate(test_runs):
        print(f"\n[{idx+1}/{len(test_runs)}] Queueing: {test['name']}...")
        wf = build_expansion_prompt(
            with_local_regions=test["with_local_regions"],
            save_prefix=test["save_prefix"]
        )
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
    print("REGIONAL CONTROL GENERATION RESULTS SUMMARY")
    print("================================================================================")
    for r in results:
        print(f"• {r['test']} -> {r['filename']}")
    print("================================================================================")
    return results


if __name__ == "__main__":
    run_control_expansion_generation_tests()
