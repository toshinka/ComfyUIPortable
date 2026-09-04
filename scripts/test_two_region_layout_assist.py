"""
Test Two-Region Layout Assist (Phase 3D.2)
==========================================
Evaluates whether adding a simple geometric ControlNet guide
(via TegakiTwoRegionLayoutGuide + ControlNetApplyAdvanced)
improves or harms the generation compared to Regional Backend alone (Impact).
Tests under identical seed=42:
1. Dog/Cat LR (CN OFF vs CN ON)
2. Dog/Cat Swap (CN OFF vs CN ON)
Generates output/Tegaki/Phase3D2/layout_assist_comparison_contact_sheet.png
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
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2", "LayoutAssist")
REPORTS_IMG_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2")
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


def build_layout_assist_prompt(spec: dict, prefix: str, cn_strength: float = 0.40, seed: int = 42):
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
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": "CN-anytest4_illustrious2_A.safetensors"
            }
        },
        "3": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1
            }
        },
        "4": {
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
        "5": {
            "class_type": "TegakiTwoRegionLayoutGuide",
            "inputs": {
                "two_region_spec": ["4", 0],
                "mode": "Panel Outline (White on Black)",
                "line_thickness": 4
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": global_p
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": global_n
            }
        },
        "8": {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "control_net": ["2", 0],
                "image": ["5", 0],
                "strength": cn_strength,
                "start_percent": 0.0,
                "end_percent": 0.60
            }
        },
        "9": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": prompt_A
            }
        },
        "10": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["1", 1],
                "text": prompt_B
            }
        },
        "11": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": ["1", 2],
                "positive": ["8", 0] if cn_strength > 0.0 else ["6", 0],
                "negative": ["8", 1] if cn_strength > 0.0 else ["7", 0]
            }
        },
        "12": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": ["1", 2],
                "positive": ["9", 0],
                "negative": ["7", 0]
            }
        },
        "13": {
            "class_type": "ToBasicPipe",
            "inputs": {
                "model": ["1", 0],
                "clip": None,
                "vae": ["1", 2],
                "positive": ["10", 0],
                "negative": ["7", 0]
            }
        },
        "14": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["11", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "15": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["12", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "16": {
            "class_type": "KSamplerAdvancedProvider",
            "inputs": {
                "basic_pipe": ["13", 0],
                "cfg": 6.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "sigma_factor": 1.0
            }
        },
        "17": {
            "class_type": "TegakiTwoRegionImpactAdapter",
            "inputs": {
                "two_region_spec": ["4", 0],
                "sampler_A": ["15", 0],
                "sampler_B": ["16", 0]
            }
        },
        "18": {
            "class_type": "RegionalSampler",
            "inputs": {
                "seed": seed,
                "seed_2nd": 0,
                "seed_2nd_mode": "ignore",
                "steps": 15,
                "base_only_steps": 2,
                "denoise": 1.0,
                "samples": ["3", 0],
                "base_sampler": ["14", 0],
                "regional_prompts": ["17", 0],
                "overlap_factor": 10,
                "restore_latent": True,
                "additional_mode": "ratio between",
                "additional_sampler": "AUTO",
                "additional_sigma_ratio": 0.3
            }
        },
        "19": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["18", 0],
                "vae": ["1", 2]
            }
        },
        "20": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["19", 0],
                "filename_prefix": prefix
            }
        }
    }
    return workflow


def run_layout_assist_experiments():
    print("\n================================================================================")
    print("Stage 3: ControlNet Layout Assist vs Regional Backend Alone (Impact)")
    print("================================================================================")

    p_dog = "a white dog, full body"
    p_cat = "a black cat, full body"
    p_glob = "simple park background, two subjects"
    p_neg = "worst quality, bad anatomy, duplicate subject"

    spec_lr = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": p_glob, "global_negative_prompt": p_neg,
        "regions": [
            {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80},
            {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
        ]
    }

    spec_swap = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": p_glob, "global_negative_prompt": p_neg,
        "regions": [
            {"id": "A", "enabled": True, "prompt": p_dog, "negative_prompt": "", "x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80},
            {"id": "B", "enabled": True, "prompt": p_cat, "negative_prompt": "", "x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
        ]
    }

    tests = [
        ("DogCat_CN_OFF_LR", spec_lr, 0.0),
        ("DogCat_CN_ON_LR", spec_lr, 0.40),
        ("DogCat_CN_OFF_Swap", spec_swap, 0.0),
        ("DogCat_CN_ON_Swap", spec_swap, 0.40),
    ]

    results = {}
    for test_id, spec, cn_str in tests:
        print(f"\n[Layout Assist Test] Generating {test_id} (CN strength={cn_str})...")
        save_prefix = f"Tegaki/Phase3D2/LayoutAssist/{test_id}"
        prompt = build_layout_assist_prompt(spec, save_prefix, cn_strength=cn_str, seed=42)

        q_res = queue_prompt(prompt)
        start_t = time.time()
        outputs = wait_for_prompt(q_res["prompt_id"], timeout=300)
        elapsed = time.time() - start_t
        print(f"  Completed in {elapsed:.1f}s.")

        img_path = get_image_file_path(outputs, save_node_id="20")
        print(f"  Saved Image: {img_path}")
        results[test_id] = {
            "test_id": test_id,
            "cn_strength": cn_str,
            "seed": 42,
            "elapsed": round(elapsed, 2),
            "image_path": img_path
        }

    # Generate Contact Sheet
    thumb_w = 320
    thumb_h = int(thumb_w * 1216 / 832)

    cols = ["Left / Right", "Geometry Swap"]
    rows = ["CN OFF (Strength 0.00)", "CN ON (Strength 0.40)"]

    pad = 16
    header_h = 50
    row_label_w = 180

    sheet_w = row_label_w + len(cols) * (thumb_w + pad) + pad
    sheet_h = header_h + len(rows) * (thumb_h + pad) + pad

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)

    draw.text((pad, 14), "Stage 3: ControlNet Layout Assist (Impact RegionalSampler | Seed: 42)", fill=(50, 40, 30))

    for c_idx, col_name in enumerate(cols):
        cx = row_label_w + c_idx * (thumb_w + pad)
        draw.text((cx + thumb_w // 2 - 35, header_h - 22), col_name, fill=(70, 60, 50))

    img_map = {
        ("CN OFF (Strength 0.00)", "Left / Right"): results["DogCat_CN_OFF_LR"]["image_path"],
        ("CN ON (Strength 0.40)", "Left / Right"): results["DogCat_CN_ON_LR"]["image_path"],
        ("CN OFF (Strength 0.00)", "Geometry Swap"): results["DogCat_CN_OFF_Swap"]["image_path"],
        ("CN ON (Strength 0.40)", "Geometry Swap"): results["DogCat_CN_ON_Swap"]["image_path"],
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
            sheet.paste(thumb, (cx, ry))
            draw.rectangle([cx, ry, cx + thumb_w, ry + thumb_h], outline=(200, 190, 180), width=1)

    out_sheet = os.path.join(REPORTS_IMG_DIR, "layout_assist_comparison_contact_sheet.png")
    sheet.save(out_sheet, quality=95)
    print(f"[Layout Assist Contact Sheet] Saved: {out_sheet}")

    summary_path = os.path.join(REPORTS_IMG_DIR, "layout_assist_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[Summary] Saved: {summary_path}")


if __name__ == "__main__":
    run_layout_assist_experiments()
