"""
Test Single Region Core Runtime (Phase 3D.2)
============================================
Runs Core Masked Conditioning across the 5 canonical positions:
TL (Top-Left), TR (Top-Right), BL (Bottom-Left), BR (Bottom-Right), C (Center).
Fixed seed=42, steps=15, cfg=6.0, euler/normal.
Prompt:
- Global: "masterpiece, simple clean outdoor background, full composition"
- Neg: "worst quality, bad anatomy, duplicate subject"
- Region A: "a white dog, full body"
- Region B: disabled
Saves outputs to output/Tegaki/Phase3D2/SingleRegion/ and logs metrics.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import subprocess
from PIL import Image
import numpy as np

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2", "SingleRegion")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)


def is_comfy_running() -> bool:
    try:
        req = urllib.request.Request(f"{COMFY_URL}/system_stats")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_comfy_server(timeout: int = 60):
    if is_comfy_running():
        print("  [ComfyUI] Server is already running.")
        return None

    print("  [ComfyUI] Starting embedded server...")
    py_exe = os.path.join(ROOT_DIR, "python_embeded", "python.exe")
    comfy_main = os.path.join(ROOT_DIR, "ComfyUI", "main.py")
    cmd = [py_exe, comfy_main, "--windows-standalone-build", "--listen", "127.0.0.1", "--port", "8188"]

    live_log_path = os.path.join(OUTPUT_DIR, "comfy_live.log")
    live_log = open(live_log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=ROOT_DIR, stdout=live_log, stderr=subprocess.STDOUT)

    start = time.time()
    while time.time() - start < timeout:
        if is_comfy_running():
            print(f"  [ComfyUI] Server port opened in {time.time() - start:.1f}s.")
            print("  [ComfyUI] Waiting 20s for warmup...")
            time.sleep(20)
            print("  [ComfyUI] Server ready.")
            return proc
        time.sleep(2)
    raise TimeoutError("Failed to start ComfyUI server within timeout.")


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


def get_image_file_path(outputs, save_node_id="7"):
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


POSITIONS = {
    "TL": {"x": 0.05, "y": 0.05, "w": 0.35, "h": 0.45},
    "TR": {"x": 0.60, "y": 0.05, "w": 0.35, "h": 0.45},
    "BL": {"x": 0.05, "y": 0.50, "w": 0.35, "h": 0.45},
    "BR": {"x": 0.60, "y": 0.50, "w": 0.35, "h": 0.45},
    "C":  {"x": 0.325, "y": 0.275, "w": 0.35, "h": 0.45},
}


def build_core_prompt(pos_key: str, geom: dict, seed: int = 42):
    spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "global_prompt": "masterpiece, simple clean outdoor background, full composition",
        "global_negative_prompt": "worst quality, bad anatomy, duplicate subject",
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "a white dog, full body",
                "negative_prompt": "",
                "x": geom["x"],
                "y": geom["y"],
                "w": geom["w"],
                "h": geom["h"]
            },
            {
                "id": "B",
                "enabled": False,
                "prompt": "",
                "negative_prompt": "",
                "x": 0.55,
                "y": 0.50,
                "w": 0.35,
                "h": 0.45
            }
        ],
        "metadata": {"oracle_mode": "single_region_core", "position": pos_key}
    }

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
                "prompt_A": "a white dog, full body",
                "negative_prompt_A": "",
                "prompt_B": "",
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
                "filename_prefix": f"Tegaki/Phase3D2/SingleRegion/Core_{pos_key}"
            }
        }
    }
    return workflow


def run_core_single_region_suite():
    print("================================================================================")
    print("Phase 3D.2 Single Region Placement Matrix — Core Masked Conditioning")
    print("================================================================================")
    server_proc = start_comfy_server(timeout=60)

    results = {}
    for pos_key, geom in POSITIONS.items():
        print(f"\n[Core Test] Generating position: {pos_key} (x={geom['x']}, y={geom['y']})...")
        prompt = build_core_prompt(pos_key, geom, seed=42)
        q_res = queue_prompt(prompt)
        prompt_id = q_res["prompt_id"]

        start_t = time.time()
        outputs = wait_for_prompt(prompt_id, timeout=300)
        elapsed = time.time() - start_t
        print(f"  Completed in {elapsed:.1f}s.")

        img_path = get_image_file_path(outputs, save_node_id="7")
        print(f"  Saved Image: {img_path}")
        results[pos_key] = {
            "backend": "Core",
            "position": pos_key,
            "geometry": geom,
            "seed": 42,
            "elapsed_seconds": round(elapsed, 2),
            "image_path": img_path,
            "file_exists": os.path.exists(img_path) if img_path else False
        }

    summary_file = os.path.join(OUTPUT_DIR, "single_region_core_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[Core Matrix Complete] Summary saved to: {summary_file}")
    return results


if __name__ == "__main__":
    run_core_single_region_suite()
