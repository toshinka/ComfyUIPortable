"""
Test Phase 3D.1 Panel Locality Diagnostics (Phase 3D.1-A)
=========================================================
Evaluates Panel Prompt locality on KOMA 2 (Corridor vs Convenience Store)
under ControlNet ON (0.60) and ControlNet OFF (0.00).

Diagnostic multi-zone measurements:
- KOMA 1 MeanDiff
- KOMA 2 MeanDiff (Target Panel)
- KOMA 3 MeanDiff
- Other Panels MeanDiff (KOMA 1 & 3)
- Outside Layout Frame MeanDiff
- Target / Other Panels Ratio
- Target / Outside Frame Ratio

Saves results to output/Tegaki/Phase3D1/panel_locality_summary.json.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import subprocess
from PIL import Image, ImageDraw
import numpy as np

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D1")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec


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
            print("  [ComfyUI] Waiting 30s for background warmup tasks to settle...")
            time.sleep(30)
            print("  [ComfyUI] Server is ready for generation.")
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
            print(f"  [Queue] Queued prompt ID: {res.get('prompt_id')}")
            return res
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[COMFY API ERROR] Response: {error_body}")
        raise


def wait_for_prompt(prompt_id, timeout=300):
    start_time = time.time()
    last_print = 0
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=5) as resp:
                history = json.loads(resp.read().decode('utf-8'))
            if prompt_id in history:
                print(f"  [Wait] Prompt {prompt_id} completed in {time.time() - start_time:.1f}s.")
                return history[prompt_id].get("outputs", {})
        except Exception:
            pass

        if time.time() - last_print > 15:
            try:
                with urllib.request.urlopen(f"{COMFY_URL}/queue", timeout=5) as qresp:
                    qdata = json.loads(qresp.read().decode('utf-8'))
                    r_count = len(qdata.get('queue_running', []))
                    p_count = len(qdata.get('queue_pending', []))
                    print(f"  [Wait] ({time.time() - start_time:.0f}s) Running: {r_count}, Pending: {p_count}")
            except Exception:
                pass
            last_print = time.time()

        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout} seconds")


def fetch_image(outputs):
    for nid, out in outputs.items():
        imgs = out.get("images", [])
        if imgs:
            fn = imgs[0]["filename"]
            sub = imgs[0].get("subfolder", "")
            img_path = os.path.join(ROOT_DIR, "ComfyUI", "output", sub, fn)
            return img_path
    raise RuntimeError("No image output returned from workflow.")


def get_existing_image(prefix: str):
    base_name = os.path.basename(prefix)
    check_dirs = [
        os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "Phase3D1"),
        os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "MangaLayoutFusion"),
        OUTPUT_DIR
    ]
    for cdir in check_dirs:
        if os.path.exists(cdir):
            for f in os.listdir(cdir):
                if f.startswith(base_name) and f.endswith(".png"):
                    full_p = os.path.join(cdir, f)
                    if os.path.getsize(full_p) > 1000:
                        return full_p
    return None


def run_or_reuse(prefix: str, wf: dict):
    existing = get_existing_image(prefix)
    if existing:
        print(f"  -> Reusing existing generated image: {existing}")
        return existing
    start_comfy_server(timeout=60)
    res = queue_prompt(wf)
    out = wait_for_prompt(res["prompt_id"], timeout=350)
    path = fetch_image(out)
    print(f"  -> Generated image: {path}")
    return path


def build_3panel_workflow(
    koma2_prompt: str,
    cn_strength: float = 0.60,
    seed: int = 43,
    steps: int = 8,
    save_prefix: str = "Tegaki/Phase3D1/PanelTest"
):
    W, H = 832, 1216
    layout_spec = get_default_panel_layout_spec(W, H, preset="3_basic")

    region_spec = {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d, blurry",
        "regions": [
            {
                "id": 1, "name": "KOMA 1", "enabled": True,
                "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40,
                "prompt": "classroom, two people talking, medium shot",
                "negative_prompt": "empty room, solo",
                "local_regions": [
                    {
                        "id": "lr_window_desks", "name": "Window Desks", "enabled": True,
                        "prompt": "school desks near the window, sunlight streaming",
                        "negative_prompt": "dark",
                        "area": {"x": 0.10, "y": 0.15, "w": 0.38, "h": 0.70}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice", "enabled": True,
                        "prompt_override": "annoyed expression, looking right",
                        "area": {"x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                    },
                    {
                        "character_id": "char_bob", "enabled": True,
                        "prompt_override": "laughing expression, looking left",
                        "area": {"x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                    }
                ]
            },
            {
                "id": 2, "name": "KOMA 2", "enabled": True,
                "x": 0.05, "y": 0.45, "w": 0.45, "h": 0.50,
                "prompt": koma2_prompt,
                "negative_prompt": "",
                "local_regions": [],
                "characters": [
                    {
                        "character_id": "char_alice", "enabled": True,
                        "prompt_override": "walking away, back view",
                        "area": None
                    }
                ]
            },
            {
                "id": 3, "name": "KOMA 3", "enabled": True,
                "x": 0.50, "y": 0.45, "w": 0.45, "h": 0.50,
                "prompt": "sunset schoolyard, fence, dusk sky",
                "negative_prompt": "",
                "local_regions": [],
                "characters": [
                    {
                        "character_id": "char_bob", "enabled": True,
                        "prompt_override": "standing by fence",
                        "area": {"x": 0.20, "y": 0.10, "w": 0.60, "h": 0.80}
                    }
                ]
            }
        ]
    }

    cast_spec = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice", "name": "Alice", "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
                "negative_prompt": "blurry, low quality",
                "loras": []
            },
            {
                "id": "char_bob", "name": "Bob", "enabled": True,
                "prompt": "1boy, short brown hair, school uniform",
                "negative_prompt": "bad anatomy",
                "loras": []
            }
        ]
    }

    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"}},
        "2": {"class_type": "TegakiLoraPromptLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "text": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "3": {"class_type": "TegakiMangaRegionEditor", "inputs": {"panel_count": 3, "canvas_width": W, "canvas_height": H, "global_prompt": region_spec["global_prompt"], "region_spec_data": json.dumps(region_spec)}},
        "4": {"class_type": "TegakiMangaPageCompiler", "inputs": {"region_spec": ["3", 0], "cast_spec": json.dumps(cast_spec), "global_loras": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "5": {"class_type": "TegakiMangaPanelLayoutEditor", "inputs": {"canvas_width": W, "canvas_height": H, "line_thickness": 4, "panel_layout_spec_data": json.dumps(layout_spec)}},
        "6": {"class_type": "TegakiMangaLayoutAwareConditioningBuilder", "inputs": {"clip": ["2", 1], "page_compile_plan": ["4", 0], "panel_layout_spec": ["5", 1], "panel_strength": 1.0, "character_strength": 0.9, "set_cond_area": "default", "local_region_strength": 0.8, "mask_feather": 0}},
        "9": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["1", 2]}},
        "12": {"class_type": "SaveImage", "inputs": {"images": ["11", 0], "filename_prefix": save_prefix}}
    }

    if cn_strength > 0.001:
        workflow["7"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "CN-anytest4_illustrious2_A.safetensors"}}
        workflow["8"] = {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["6", 0], "negative": ["6", 1], "control_net": ["7", 0], "image": ["5", 0], "strength": float(cn_strength), "start_percent": 0.0, "end_percent": 1.0}}
        pos_link = ["8", 0]
        neg_link = ["8", 1]
    else:
        pos_link = ["6", 0]
        neg_link = ["6", 1]

    workflow["10"] = {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": pos_link, "negative": neg_link, "latent_image": ["9", 0], "seed": seed, "control_after_generate": "fixed", "steps": steps, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}}
    return workflow


def compute_multizone_diff(img_a_path: str, img_b_path: str, W: int = 832, H: int = 1216) -> dict:
    """
    Computes mean pixel difference across KOMA 1, KOMA 2, KOMA 3, and Outside Frame.
    """
    img_a = Image.open(img_a_path).convert("RGB")
    img_b = Image.open(img_b_path).convert("RGB")
    arr_a = np.array(img_a).astype(np.float32)
    arr_b = np.array(img_b).astype(np.float32)

    diff = np.mean(np.abs(arr_a - arr_b), axis=2)  # [H, W], scale [0, 255]

    # Polygons in 3_basic
    # p1: (0.05, 0.05) -> (0.05, 0.45) -> (0.50, 0.45) -> (0.95, 0.45) -> (0.95, 0.05)
    koma1_pts = [(int(0.05 * W), int(0.05 * H)), (int(0.05 * W), int(0.45 * H)),
                 (int(0.50 * W), int(0.45 * H)), (int(0.95 * W), int(0.45 * H)), (int(0.95 * W), int(0.05 * H))]

    # p2: (0.05, 0.45) -> (0.05, 0.95) -> (0.50, 0.95) -> (0.50, 0.45) (Target)
    koma2_pts = [(int(0.05 * W), int(0.45 * H)), (int(0.05 * W), int(0.95 * H)),
                 (int(0.50 * W), int(0.95 * H)), (int(0.50 * W), int(0.45 * H))]

    # p3: (0.50, 0.45) -> (0.50, 0.95) -> (0.95, 0.95) -> (0.95, 0.45)
    koma3_pts = [(int(0.50 * W), int(0.45 * H)), (int(0.50 * W), int(0.95 * H)),
                 (int(0.95 * W), int(0.95 * H)), (int(0.95 * W), int(0.45 * H))]

    def _rasterize_mask(pts):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        return np.array(m).astype(np.float32) / 255.0 > 0.5

    m1 = _rasterize_mask(koma1_pts)
    m2 = _rasterize_mask(koma2_pts)
    m3 = _rasterize_mask(koma3_pts)

    # Frame mask
    frame_m = np.zeros((H, W), dtype=bool)
    fx0, fy0 = int(0.05 * W), int(0.05 * H)
    fx1, fy1 = int(0.95 * W), int(0.95 * H)
    frame_m[fy0:fy1, fx0:fx1] = True
    outside_frame_m = ~frame_m

    m_other = m1 | m3

    diff_koma1 = float(np.mean(diff[m1])) if np.sum(m1) > 0 else 0.0
    diff_koma2 = float(np.mean(diff[m2])) if np.sum(m2) > 0 else 0.0
    diff_koma3 = float(np.mean(diff[m3])) if np.sum(m3) > 0 else 0.0
    diff_other = float(np.mean(diff[m_other])) if np.sum(m_other) > 0 else 1.0
    diff_outside = float(np.mean(diff[outside_frame_m])) if np.sum(outside_frame_m) > 0 else 1.0

    target_to_other = diff_koma2 / max(1e-5, diff_other)
    target_to_outside = diff_koma2 / max(1e-5, diff_outside)

    return {
        "koma1_mean_diff": round(diff_koma1, 4),
        "koma2_mean_diff": round(diff_koma2, 4),
        "koma3_mean_diff": round(diff_koma3, 4),
        "other_panels_mean_diff": round(diff_other, 4),
        "outside_frame_mean_diff": round(diff_outside, 4),
        "target_to_other_ratio": round(target_to_other, 4),
        "target_to_outside_ratio": round(target_to_outside, 4)
    }


def run_panel_locality_tests():
    print("=" * 80)
    print(" Phase 3D.1: Panel Locality Multi-Zone Diagnostic Suite")
    print("=" * 80)

    prompt_corridor = "school corridor, lockers, hallway perspective"
    prompt_conveni = "convenience store interior, brightly lit aisles, shelves with snacks and drinks"

    # 1. CN ON (0.60)
    print("\n--- 1. Evaluating Panel Prompt A/B with ControlNet ON (0.60) ---")
    wf_on_a = build_3panel_workflow(prompt_corridor, cn_strength=0.60, seed=43, save_prefix="Tegaki/Phase3D1/Panel_CNON_Corridor")
    wf_on_b = build_3panel_workflow(prompt_conveni, cn_strength=0.60, seed=43, save_prefix="Tegaki/Phase3D1/Panel_CNON_Conveni")

    # Reuse Phase 3D images if available
    path_on_a = get_existing_image("Test3A_Corridor") or run_or_reuse("Panel_CNON_Corridor", wf_on_a)
    path_on_b = get_existing_image("Test3B_Conveni") or run_or_reuse("Panel_CNON_Conveni", wf_on_b)

    metrics_on = compute_multizone_diff(path_on_a, path_on_b)
    print(f"  CN ON Metrics:")
    print(f"    KOMA 2 (Target): {metrics_on['koma2_mean_diff']}")
    print(f"    KOMA 1: {metrics_on['koma1_mean_diff']}, KOMA 3: {metrics_on['koma3_mean_diff']}")
    print(f"    Other Panels Mean: {metrics_on['other_panels_mean_diff']}")
    print(f"    Outside Frame: {metrics_on['outside_frame_mean_diff']}")
    print(f"    Target / Other Ratio: {metrics_on['target_to_other_ratio']}")
    print(f"    Target / Outside Ratio: {metrics_on['target_to_outside_ratio']}")

    # 2. CN OFF (0.00)
    print("\n--- 2. Evaluating Panel Prompt A/B with ControlNet OFF (0.00) ---")
    wf_off_a = build_3panel_workflow(prompt_corridor, cn_strength=0.00, seed=43, save_prefix="Tegaki/Phase3D1/Panel_CNOFF_Corridor")
    wf_off_b = build_3panel_workflow(prompt_conveni, cn_strength=0.00, seed=43, save_prefix="Tegaki/Phase3D1/Panel_CNOFF_Conveni")

    path_off_a = run_or_reuse("Panel_CNOFF_Corridor", wf_off_a)
    path_off_b = run_or_reuse("Panel_CNOFF_Conveni", wf_off_b)

    metrics_off = compute_multizone_diff(path_off_a, path_off_b)
    print(f"  CN OFF Metrics:")
    print(f"    KOMA 2 (Target): {metrics_off['koma2_mean_diff']}")
    print(f"    Other Panels Mean: {metrics_off['other_panels_mean_diff']}")
    print(f"    Outside Frame: {metrics_off['outside_frame_mean_diff']}")
    print(f"    Target / Other Ratio: {metrics_off['target_to_other_ratio']}")
    print(f"    Target / Outside Ratio: {metrics_off['target_to_outside_ratio']}")

    summary = {
        "cn_on_0.60": {
            "path_A": path_on_a,
            "path_B": path_on_b,
            "metrics": metrics_on
        },
        "cn_off_0.00": {
            "path_A": path_off_a,
            "path_B": path_off_b,
            "metrics": metrics_off
        },
        "cn_effect_on_target_locality": {
            "target_diff_gain": round(metrics_on["koma2_mean_diff"] - metrics_off["koma2_mean_diff"], 4),
            "target_to_other_gain": round(metrics_on["target_to_other_ratio"] - metrics_off["target_to_other_ratio"], 4)
        }
    }

    out_file = os.path.join(OUTPUT_DIR, "panel_locality_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved panel locality summary to {out_file}")
    return summary


if __name__ == "__main__":
    run_panel_locality_tests()
