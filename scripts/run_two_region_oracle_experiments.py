import json
import urllib.request
import urllib.parse
import time
import os
import sys

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "TwoRegionOracle")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[COMFY API ERROR 400] Response: {error_body}")
        raise


def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
        return json.loads(resp.read().decode('utf-8'))


def wait_for_prompt(prompt_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            return outputs
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout} seconds")


def build_core_oracle_prompt(
    spec_data: dict,
    save_prefix: str,
    seed: int = 42,
    steps: int = 15,
    cfg: float = 6.0,
    sampler_name: str = "euler",
    scheduler: str = "normal",
    strength_A: float = 1.0,
    strength_B: float = 1.0,
    set_cond_area: str = "default",
    mask_feather: int = 0,
    checkpoint: str = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
):
    W = spec_data["canvas"]["width"]
    H = spec_data["canvas"]["height"]

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint
            }
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": W,
                "height": H,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "TegakiTwoRegionCoupleEditor",
            "inputs": {
                "canvas_width": W,
                "canvas_height": H,
                "global_prompt": spec_data.get("global_prompt", ""),
                "global_negative_prompt": spec_data.get("global_negative_prompt", ""),
                "prompt_A": spec_data["regions"][0].get("prompt", "") if len(spec_data["regions"]) > 0 else "",
                "negative_prompt_A": spec_data["regions"][0].get("negative_prompt", "") if len(spec_data["regions"]) > 0 else "",
                "prompt_B": spec_data["regions"][1].get("prompt", "") if len(spec_data["regions"]) > 1 else "",
                "negative_prompt_B": spec_data["regions"][1].get("negative_prompt", "") if len(spec_data["regions"]) > 1 else "",
                "two_region_spec_data": json.dumps(spec_data)
            }
        },
        "4": {
            "class_type": "TegakiTwoRegionCoreConditioner",
            "inputs": {
                "clip": ["1", 1],
                "two_region_spec": ["3", 0],
                "strength_A": strength_A,
                "strength_B": strength_B,
                "set_cond_area": set_cond_area,
                "mask_feather": mask_feather
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["4", 1],
                "latent_image": ["2", 0],
                "seed": seed,
                "control_after_generate": "fixed",
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": 1.0
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": save_prefix
            }
        }
    }
    return workflow


def build_impact_oracle_prompt(
    spec_data: dict,
    save_prefix: str,
    seed: int = 42,
    steps: int = 15,
    base_only_steps: int = 2,
    cfg: float = 6.0,
    sampler_name: str = "euler",
    scheduler: str = "normal",
    checkpoint: str = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
):
    W = spec_data["canvas"]["width"]
    H = spec_data["canvas"]["height"]

    global_p = spec_data.get("global_prompt", "")
    global_n = spec_data.get("global_negative_prompt", "worst quality, low quality")
    p_A = spec_data["regions"][0].get("prompt", "")
    p_B = spec_data["regions"][1].get("prompt", "")

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint
            }
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": W,
                "height": H,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "TegakiTwoRegionCoupleEditor",
            "inputs": {
                "canvas_width": W,
                "canvas_height": H,
                "global_prompt": global_p,
                "global_negative_prompt": global_n,
                "prompt_A": p_A,
                "negative_prompt_A": "",
                "prompt_B": p_B,
                "negative_prompt_B": "",
                "two_region_spec_data": json.dumps(spec_data)
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": global_p
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": global_n
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": p_A
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": p_B
            }
        },
        "8": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "vae": ["1", 2],
                "positive": ["4", 0],
                "negative": ["5", 0]
            }
        },
        "9": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "vae": ["1", 2],
                "positive": ["6", 0],
                "negative": ["5", 0]
            }
        },
        "10": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "vae": ["1", 2],
                "positive": ["7", 0],
                "negative": ["5", 0]
            }
        },
        "11": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["8", 0],
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "sigma_factor": 1.0
            }
        },
        "12": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["9", 0],
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "sigma_factor": 1.0
            }
        },
        "13": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["10", 0],
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "sigma_factor": 1.0
            }
        },
        "14": {
            "class_type": "TegakiTwoRegionImpactAdapter",
            "inputs": {
                "two_region_spec": ["3", 0],
                "sampler_A": ["12", 0],
                "sampler_B": ["13", 0],
                "variation_seed": 0,
                "variation_strength": 0.0,
                "variation_method": "linear"
            }
        },
        "15": {
            "class_type": "RegionalSampler",
            "inputs": {
                "seed": seed,
                "seed_2nd": 0,
                "seed_2nd_mode": "ignore",
                "steps": steps,
                "base_only_steps": base_only_steps,
                "denoise": 1.0,
                "samples": ["2", 0],
                "base_sampler": ["11", 0],
                "regional_prompts": ["14", 0],
                "overlap_factor": 10,
                "restore_latent": True,
                "additional_mode": "ratio between",
                "additional_sampler": "AUTO",
                "additional_sigma_ratio": 0.3
            }
        },
        "16": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["15", 0],
                "vae": ["1", 2]
            }
        },
        "17": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["16", 0],
                "filename_prefix": save_prefix
            }
        }
    }
    return workflow


def build_controlnet_aux_prompt(
    spec_data: dict,
    save_prefix: str,
    seed: int = 42,
    steps: int = 15,
    cfg: float = 6.0,
    sampler_name: str = "euler",
    scheduler: str = "normal",
    checkpoint: str = "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors",
    controlnet_name: str = "CN-anytest4_illustrious2_A.safetensors"
):
    W = spec_data["canvas"]["width"]
    H = spec_data["canvas"]["height"]

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": { "ckpt_name": checkpoint }
        },
        "2": {
            "class_type": "ControlNetLoader",
            "inputs": { "control_net_name": controlnet_name }
        },
        "3": {
            "class_type": "EmptyLatentImage",
            "inputs": { "width": W, "height": H, "batch_size": 1 }
        },
        "4": {
            "class_type": "TegakiTwoRegionCoupleEditor",
            "inputs": {
                "canvas_width": W,
                "canvas_height": H,
                "global_prompt": spec_data.get("global_prompt", ""),
                "global_negative_prompt": spec_data.get("global_negative_prompt", ""),
                "prompt_A": spec_data["regions"][0].get("prompt", ""),
                "negative_prompt_A": "",
                "prompt_B": spec_data["regions"][1].get("prompt", ""),
                "negative_prompt_B": "",
                "two_region_spec_data": json.dumps(spec_data)
            }
        },
        "5": {
            "class_type": "TegakiTwoRegionCoreConditioner",
            "inputs": {
                "clip": ["1", 1],
                "two_region_spec": ["4", 0],
                "strength_A": 1.0,
                "strength_B": 1.0,
                "set_cond_area": "default",
                "mask_feather": 0
            }
        },
        "6": {
            "class_type": "TegakiTwoRegionLayoutGuide",
            "inputs": {
                "two_region_spec": ["4", 0],
                "mode": "Panel Outline (White on Black)",
                "line_thickness": 4
            }
        },
        "7": {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["5", 0],
                "negative": ["5", 1],
                "control_net": ["2", 0],
                "image": ["6", 0],
                "strength": 0.6,
                "start_percent": 0.0,
                "end_percent": 0.6
            }
        },
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["7", 0],
                "negative": ["7", 1],
                "latent_image": ["3", 0],
                "seed": seed,
                "control_after_generate": "fixed",
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": 1.0
            }
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["1", 2]
            }
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["9", 0],
                "filename_prefix": save_prefix
            }
        }
    }
    return workflow


def run_experiment(name: str, prompt_dict: dict):
    print(f"\n>>> Running Experiment: {name} ...")
    start = time.time()
    res = queue_prompt(prompt_dict)
    prompt_id = res.get("prompt_id")
    print(f"  Enqueued Prompt ID: {prompt_id}")
    outputs = wait_for_prompt(prompt_id)
    elapsed = time.time() - start
    print(f"  [COMPLETED] in {elapsed:.2f}s! Outputs: {list(outputs.keys())}")
    return outputs


def main():
    print("================================================================================")
    print("Executing Two-Region Oracle Experiments (Phase 3C)")
    print("================================================================================")

    # 1. Dog / Cat Test (Horizontal, Vertical, Overlap)
    dog_cat_base = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": "simple outdoor scene, full body, clear subjects, daylight",
        "global_negative_prompt": "worst quality, low quality, bad anatomy, deformed",
        "regions": [
            {"id": "A", "enabled": True, "prompt": "a golden retriever dog, sitting", "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
            {"id": "B", "enabled": True, "prompt": "a black cat, standing", "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
        ]
    }

    # Core Dog/Cat Horizontal
    run_experiment("Core_DogCat_Horizontal", build_core_oracle_prompt(dog_cat_base, "Tegaki/TwoRegionOracle/Core_DogCat_Horizontal"))

    # Core Dog/Cat Vertical
    dog_cat_vert = json.loads(json.dumps(dog_cat_base))
    dog_cat_vert["regions"] = [
        {"id": "A", "enabled": True, "prompt": "a golden retriever dog, sitting", "negative_prompt": "", "x": 0.10, "y": 0.05, "w": 0.80, "h": 0.42},
        {"id": "B", "enabled": True, "prompt": "a black cat, standing", "negative_prompt": "", "x": 0.10, "y": 0.53, "w": 0.80, "h": 0.42}
    ]
    run_experiment("Core_DogCat_Vertical", build_core_oracle_prompt(dog_cat_vert, "Tegaki/TwoRegionOracle/Core_DogCat_Vertical"))

    # Core Dog/Cat Overlap
    dog_cat_overlap = json.loads(json.dumps(dog_cat_base))
    dog_cat_overlap["regions"] = [
        {"id": "A", "enabled": True, "prompt": "a golden retriever dog, sitting", "negative_prompt": "", "x": 0.10, "y": 0.10, "w": 0.55, "h": 0.80},
        {"id": "B", "enabled": True, "prompt": "a black cat, standing", "negative_prompt": "", "x": 0.35, "y": 0.10, "w": 0.55, "h": 0.80}
    ]
    run_experiment("Core_DogCat_Overlap", build_core_oracle_prompt(dog_cat_overlap, "Tegaki/TwoRegionOracle/Core_DogCat_Overlap"))

    # 2. Man / Woman Test (Horizontal, Overlap, OneScene, OneRegion)
    man_woman_base = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": "simple outdoor scene, full body, clear subjects, afternoon sunlight",
        "global_negative_prompt": "worst quality, low quality, bad anatomy, deformed",
        "regions": [
            {"id": "A", "enabled": True, "prompt": "1man, short black hair, dark jacket, standing", "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
            {"id": "B", "enabled": True, "prompt": "1woman, long blonde hair, light white dress, smiling", "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
        ]
    }
    run_experiment("Core_ManWoman_Horizontal", build_core_oracle_prompt(man_woman_base, "Tegaki/TwoRegionOracle/Core_ManWoman_Horizontal"))

    # Core Man/Woman Overlap
    man_woman_overlap = json.loads(json.dumps(man_woman_base))
    man_woman_overlap["regions"] = [
        {"id": "A", "enabled": True, "prompt": "1man, short black hair, dark jacket, standing", "negative_prompt": "", "x": 0.10, "y": 0.10, "w": 0.55, "h": 0.80},
        {"id": "B", "enabled": True, "prompt": "1woman, long blonde hair, light white dress, smiling", "negative_prompt": "", "x": 0.35, "y": 0.10, "w": 0.55, "h": 0.80}
    ]
    run_experiment("Core_ManWoman_Overlap", build_core_oracle_prompt(man_woman_overlap, "Tegaki/TwoRegionOracle/Core_ManWoman_Overlap"))

    # Core Man/Woman One Scene (同一シーン・演技)
    man_woman_onescene = json.loads(json.dumps(man_woman_base))
    man_woman_onescene["global_prompt"] = "two people standing together, friendly interaction, talking, medium shot"
    man_woman_onescene["regions"] = [
        {"id": "A", "enabled": True, "prompt": "1man, black hair, looking at partner", "negative_prompt": "", "x": 0.12, "y": 0.15, "w": 0.40, "h": 0.70},
        {"id": "B", "enabled": True, "prompt": "1woman, blonde hair, looking at partner, smiling", "negative_prompt": "", "x": 0.48, "y": 0.15, "w": 0.40, "h": 0.70}
    ]
    run_experiment("Core_ManWoman_OneScene", build_core_oracle_prompt(man_woman_onescene, "Tegaki/TwoRegionOracle/Core_ManWoman_OneScene"))

    # Core Man/Woman One Region (対照実験: 領域指定なし)
    man_woman_oneregion = json.loads(json.dumps(man_woman_base))
    man_woman_oneregion["global_prompt"] = "two people standing together, 1man and 1woman, friendly interaction"
    man_woman_oneregion["regions"] = [
        {"id": "A", "enabled": False, "prompt": "", "negative_prompt": "", "x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
        {"id": "B", "enabled": False, "prompt": "", "negative_prompt": "", "x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0}
    ]
    run_experiment("Core_ManWoman_OneRegion", build_core_oracle_prompt(man_woman_oneregion, "Tegaki/TwoRegionOracle/Core_ManWoman_OneRegion"))

    # 3. Locality Metrics Test (Base: Blonde woman, Variant: Blue hair woman)
    locality_base = json.loads(json.dumps(man_woman_base))
    locality_base["regions"][0]["prompt"] = "1woman, blonde hair, blue eyes, smiling, light dress"
    locality_base["regions"][1]["prompt"] = "1boy, black hair, dark jacket, standing"
    run_experiment("Core_Locality_Base", build_core_oracle_prompt(locality_base, "Tegaki/TwoRegionOracle/Core_Locality_Base"))

    locality_variant = json.loads(json.dumps(locality_base))
    locality_variant["regions"][0]["prompt"] = "1woman, blue hair, blue eyes, smiling, light dress"
    run_experiment("Core_Locality_Variant", build_core_oracle_prompt(locality_variant, "Tegaki/TwoRegionOracle/Core_Locality_Variant"))

    # 4. Impact RegionalSampler Tests
    try:
        print("\n--- Running Impact RegionalSampler Oracle Tests ---")
        run_experiment("Impact_DogCat_Horizontal", build_impact_oracle_prompt(dog_cat_base, "Tegaki/TwoRegionOracle/Impact_DogCat_Horizontal"))
        run_experiment("Impact_ManWoman_Horizontal", build_impact_oracle_prompt(man_woman_base, "Tegaki/TwoRegionOracle/Impact_ManWoman_Horizontal"))
        run_experiment("Impact_ManWoman_OneScene", build_impact_oracle_prompt(man_woman_onescene, "Tegaki/TwoRegionOracle/Impact_ManWoman_OneScene"))
    except Exception as e:
        print(f"[IMPACT TEST WARNING/SKIPPED]: {e}")

    # 5. ControlNet Layout Aux Test
    try:
        print("\n--- Running ControlNet Layout Aux Oracle Test ---")
        run_experiment("ControlNet_Layout_Aux_Horizontal", build_controlnet_aux_prompt(man_woman_base, "Tegaki/TwoRegionOracle/ControlNet_Layout_Aux_Horizontal"))
    except Exception as e:
        print(f"[CONTROLNET AUX WARNING/SKIPPED]: {e}")

    print("\n================================================================================")
    print("[SUCCESS] All planned Oracle experiments executed!")
    print("================================================================================")


if __name__ == "__main__":
    main()
