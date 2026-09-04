"""
Test Two-Region Backend Runtime (Phase 3D.2)
============================================
Runs real SDXL generations to evaluate Two-Region Semantic Binding & Geometry Swap:
1. Dog / Cat Matrix (White Dog vs Black Cat):
   - Test 1: Left / Right (A=Left, B=Right)
   - Test 2: Geometry Swap (A=Right, B=Left, exact same prompts)
   - Test 3: Vertical (A=Top, B=Bottom)
   - Test 4: Overlap (A/B ~35% overlap)
   Plus Core baseline comparison on Test 1 (LR) and Test 2 (Swap).
2. Man / Woman Matrix:
   - Test 1: Left / Right (A=Man Left, B=Woman Right)
   - Test 2: Geometry Swap (A=Man Right, B=Woman Left)
   - Test 3: Couple Overlap (A/B overlap with friendly conversation prompt)
3. Generates comparison contact sheets:
   - output/Tegaki/Phase3D2/two_region_dog_cat_contact_sheet.png
   - output/Tegaki/Phase3D2/two_region_man_woman_contact_sheet.png
4. Records structured evaluation summary to JSON.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from PIL import Image, ImageDraw

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2", "TwoRegion")
REPORTS_IMG_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def queue_prompt(prompt_workflow):
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[COMFY API ERROR] Response: {error_body}")
        raise


def wait_for_prompt(prompt_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=5) as resp:
                history = json.loads(resp.read().decode('utf-8'))
            if prompt_id in history:
                return history[prompt_id].get("outputs", {})
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish within {timeout}s.")


def get_image_file_path(outputs, save_node_id):
    node_out = outputs.get(save_node_id, {})
    images = node_out.get("images", [])
    if not images:
        return None
    img_info = images[0]
    filename = img_info["filename"]
    subfolder = img_info.get("subfolder", "")
    folder_type = img_info.get("type", "output")
    base_folder = os.path.join(ROOT_DIR, "ComfyUI", folder_type)
    return os.path.join(base_folder, subfolder, filename)


def build_two_region_impact_prompt(spec: dict, prefix: str, seed: int = 42):
    global_p = spec["global_prompt"]
    global_n = spec["global_negative_prompt"]
    prompt_A = spec["regions"][0]["prompt"]
    prompt_B = spec["regions"][1]["prompt"]

    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
            }
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "TegakiTwoRegionCoupleEditor",
            "inputs": {
                "canvas_width": 832,
                "canvas_height": 1216,
                "global_prompt": global_p,
                "global_negative_prompt": global_n,
                "prompt_A": prompt_A,
                "negative_prompt_A": "",
                "prompt_B": prompt_B,
                "negative_prompt_B": "",
                "two_region_spec_data": json.dumps(spec)
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
                "text": prompt_A
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": prompt_B
            }
        },
        "8": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": None,
                "positive": ["4", 0],
                "negative": ["5", 0]
            }
        },
        "9": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": None,
                "positive": ["6", 0],
                "negative": ["5", 0]
            }
        },
        "10": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": None,
                "positive": ["7", 0],
                "negative": ["5", 0]
            }
        },
        "11": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["8", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "12": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["9", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "13": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["10", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "14": {
            "class_type": "TegakiTwoRegionImpactAdapter",
            "inputs": {
                "two_region_spec": ["3", 0],
                "sampler_A": ["12", 0],
                "sampler_B": ["13", 0]
            }
        },
        "15": {
            "class_type": "RegionalSampler",
            "inputs": {
                "seed": seed,
                "seed_2nd": 0,
                "seed_2nd_mode": "ignore",
                "steps": 15,
                "base_only_steps": 2,
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
                "filename_prefix": prefix
            }
        }
    }
    return workflow


def build_two_region_core_prompt(spec: dict, prefix: str, seed: int = 42):
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
            }
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "TegakiTwoRegionCoupleEditor",
            "inputs": {
                "canvas_width": 832,
                "canvas_height": 1216,
                "global_prompt": spec["global_prompt"],
                "global_negative_prompt": spec["global_negative_prompt"],
                "prompt_A": spec["regions"][0]["prompt"],
                "negative_prompt_A": "",
                "prompt_B": spec["regions"][1]["prompt"],
                "negative_prompt_B": "",
                "two_region_spec_data": json.dumps(spec)
            }
        },
        "4": {
            "class_type": "TegakiTwoRegionCoreConditioner",
            "inputs": {
                "clip": ["1", 1],
                "two_region_spec": ["3", 0],
                "strength_A": 1.0,
                "strength_B": 1.0,
                "set_cond_area": "default",
                "mask_feather": 0
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
                "steps": 15,
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
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
                "filename_prefix": prefix
            }
        }
    }
    return workflow


def run_dog_cat_suite():
    print("\n================================================================================")
    print("Stage 2: Two-Region Semantic Binding — White Dog vs Black Cat")
    print("================================================================================")

    p_dog = "a white dog, full body"
    p_cat = "a black cat, full body"
    p_glob = "simple park background, two subjects"
    p_neg = "worst quality, bad anatomy, duplicate subject"

    cases = {
        "DogCat_Impact_LR": {
            "backend": "Impact",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        },
        "DogCat_Impact_Swap": {
            "backend": "Impact",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        },
        "DogCat_Impact_Vert": {
            "backend": "Impact",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.10, "y": 0.05, "w": 0.80, "h": 0.42},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.10, "y": 0.53, "w": 0.80, "h": 0.42}
                ]
            }
        },
        "DogCat_Impact_Overlap": {
            "backend": "Impact",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.62, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.33, "y": 0.10, "w": 0.62, "h": 0.80}
                ]
            }
        },
        "DogCat_Core_LR": {
            "backend": "Core",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        },
        "DogCat_Core_Swap": {
            "backend": "Core",
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": p_glob, "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        }
    }

    results = {}
    for case_id, info in cases.items():
        print(f"\n[Dog/Cat Test] Generating: {case_id}...")
        save_prefix = f"Tegaki/Phase3D2/TwoRegion/{case_id}"
        if info["backend"] == "Impact":
            prompt = build_two_region_impact_prompt(info["spec"], save_prefix, seed=42)
            save_node = "17"
        else:
            prompt = build_two_region_core_prompt(info["spec"], save_prefix, seed=42)
            save_node = "7"

        q_res = queue_prompt(prompt)
        start_t = time.time()
        outputs = wait_for_prompt(q_res["prompt_id"], timeout=300)
        elapsed = time.time() - start_t
        print(f"  Completed in {elapsed:.1f}s.")

        img_path = get_image_file_path(outputs, save_node)
        print(f"  Saved Image: {img_path}")
        results[case_id] = {
            "case_id": case_id,
            "backend": info["backend"],
            "seed": 42,
            "elapsed": round(elapsed, 2),
            "image_path": img_path,
            "spec": info["spec"]
        }

    return results


def run_man_woman_suite():
    print("\n================================================================================")
    print("Stage 2: Two-Region Semantic Binding — Man vs Woman (Candidate Backend: Impact)")
    print("================================================================================")

    p_man = "1man, black hair, dark jacket"
    p_woman = "1woman, blonde hair, light dress"
    p_neg = "worst quality, bad anatomy, duplicate subject"

    cases = {
        "ManWoman_Impact_LR": {
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": "simple park background, two people",
                "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_man, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_woman, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        },
        "ManWoman_Impact_Swap": {
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": "simple park background, two people",
                "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_man, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_woman, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                ]
            }
        },
        "ManWoman_Impact_Overlap": {
            "spec": {
                "version": 1,
                "canvas": {"width": 832, "height": 1216},
                "global_prompt": "two people standing close together, friendly conversation",
                "global_negative_prompt": p_neg,
                "regions": [
                    {"id": "A", "enabled": True, "prompt": p_man, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.62, "h": 0.80},
                    {"id": "B", "enabled": True, "prompt": p_woman, "negative_prompt": "", "x": 0.33, "y": 0.10, "w": 0.62, "h": 0.80}
                ]
            }
        }
    }

    results = {}
    for case_id, info in cases.items():
        print(f"\n[Man/Woman Test] Generating: {case_id}...")
        save_prefix = f"Tegaki/Phase3D2/TwoRegion/{case_id}"
        prompt = build_two_region_impact_prompt(info["spec"], save_prefix, seed=42)

        q_res = queue_prompt(prompt)
        start_t = time.time()
        outputs = wait_for_prompt(q_res["prompt_id"], timeout=300)
        elapsed = time.time() - start_t
        print(f"  Completed in {elapsed:.1f}s.")

        img_path = get_image_file_path(outputs, save_node_id="17")
        print(f"  Saved Image: {img_path}")
        results[case_id] = {
            "case_id": case_id,
            "backend": "Impact",
            "seed": 42,
            "elapsed": round(elapsed, 2),
            "image_path": img_path,
            "spec": info["spec"]
        }

    return results


def generate_dog_cat_contact_sheet(dc_results):
    thumb_w = 320
    thumb_h = int(thumb_w * 1216 / 832)  # ~467 px

    cols = ["Left/Right", "Geometry Swap", "Vertical", "Overlap"]
    rows = ["Impact RegionalSampler", "Core Masked Cond"]

    pad = 16
    header_h = 50
    row_label_w = 140

    sheet_w = row_label_w + len(cols) * (thumb_w + pad) + pad
    sheet_h = header_h + len(rows) * (thumb_h + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)

    draw.text((pad, 14), "Stage 2: Dog / Cat Semantic Binding & Geometry Swap (A=White Dog, B=Black Cat | Seed: 42)", fill=(50, 40, 30))

    for c_idx, col_name in enumerate(cols):
        cx = row_label_w + c_idx * (thumb_w + pad)
        draw.text((cx + thumb_w // 2 - 35, header_h - 22), col_name, fill=(70, 60, 50))

    img_map = {
        ("Impact RegionalSampler", "Left/Right"): dc_results.get("DogCat_Impact_LR", {}).get("image_path"),
        ("Impact RegionalSampler", "Geometry Swap"): dc_results.get("DogCat_Impact_Swap", {}).get("image_path"),
        ("Impact RegionalSampler", "Vertical"): dc_results.get("DogCat_Impact_Vert", {}).get("image_path"),
        ("Impact RegionalSampler", "Overlap"): dc_results.get("DogCat_Impact_Overlap", {}).get("image_path"),
        ("Core Masked Cond", "Left/Right"): dc_results.get("DogCat_Core_LR", {}).get("image_path"),
        ("Core Masked Cond", "Geometry Swap"): dc_results.get("DogCat_Core_Swap", {}).get("image_path"),
    }

    for r_idx, row_name in enumerate(rows):
        ry = header_h + r_idx * (thumb_h + pad)
        draw.text((pad, ry + thumb_h // 2 - 10), row_name, fill=(50, 40, 30))

        for c_idx, col_name in enumerate(cols):
            cx = row_label_w + c_idx * (thumb_w + pad)
            p = img_map.get((row_name, col_name))
            if p and os.path.exists(p):
                with Image.open(p) as im:
                    thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            else:
                thumb = Image.new("RGB", (thumb_w, thumb_h), (230, 230, 230))
                d_th = ImageDraw.Draw(thumb)
                d_th.text((20, thumb_h // 2), "N/A (Impact only)", fill=(120, 120, 120))

            sheet.paste(thumb, (cx, ry))
            draw.rectangle([cx, ry, cx + thumb_w, ry + thumb_h], outline=(200, 190, 180), width=1)

    out_path = os.path.join(REPORTS_IMG_DIR, "two_region_dog_cat_contact_sheet.png")
    sheet.save(out_path, quality=95)
    print(f"[Contact Sheet] Saved: {out_path}")
    return out_path


def generate_man_woman_contact_sheet(mw_results):
    thumb_w = 340
    thumb_h = int(thumb_w * 1216 / 832)

    cols = ["Left / Right", "Geometry Swap", "Couple Overlap"]
    pad = 16
    header_h = 50
    row_label_w = 140

    sheet_w = row_label_w + len(cols) * (thumb_w + pad) + pad
    sheet_h = header_h + (thumb_h + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)

    draw.text((pad, 14), "Stage 2: Man / Woman Semantic Binding (A=Man, B=Woman | Impact RegionalSampler | Seed: 42)", fill=(50, 40, 30))

    for c_idx, col_name in enumerate(cols):
        cx = row_label_w + c_idx * (thumb_w + pad)
        draw.text((cx + thumb_w // 2 - 40, header_h - 22), col_name, fill=(70, 60, 50))

    row_name = "Impact Regional"
    ry = header_h
    draw.text((pad, ry + thumb_h // 2 - 10), row_name, fill=(50, 40, 30))

    cases_keys = ["ManWoman_Impact_LR", "ManWoman_Impact_Swap", "ManWoman_Impact_Overlap"]
    for c_idx, k in enumerate(cases_keys):
        cx = row_label_w + c_idx * (thumb_w + pad)
        p = mw_results.get(k, {}).get("image_path")
        if p and os.path.exists(p):
            with Image.open(p) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        else:
            thumb = Image.new("RGB", (thumb_w, thumb_h), (220, 220, 220))
        sheet.paste(thumb, (cx, ry))
        draw.rectangle([cx, ry, cx + thumb_w, ry + thumb_h], outline=(200, 190, 180), width=1)

    out_path = os.path.join(REPORTS_IMG_DIR, "two_region_man_woman_contact_sheet.png")
    sheet.save(out_path, quality=95)
    print(f"[Contact Sheet] Saved: {out_path}")
    return out_path


def main():
    dc_res = run_dog_cat_suite()
    mw_res = run_man_woman_suite()

    dc_sheet = generate_dog_cat_contact_sheet(dc_res)
    mw_sheet = generate_man_woman_contact_sheet(mw_res)

    all_summary = {
        "dog_cat": dc_res,
        "man_woman": mw_res,
        "dog_cat_contact_sheet": dc_sheet,
        "man_woman_contact_sheet": mw_sheet
    }

    summary_file = os.path.join(REPORTS_IMG_DIR, "two_region_backend_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_summary, f, indent=2, ensure_ascii=False)
    print(f"\n[Two Region Complete] Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()
