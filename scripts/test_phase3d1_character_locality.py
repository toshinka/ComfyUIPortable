"""
Test Phase 3D.1 Character Locality Diagnostics & 5-Panel Generation (Phase 3D.1-A)
=================================================================================
Evaluates Character Prompt locality under ControlNet ON (0.60):
1. Alice hair color A/B (blonde vs bright cyan blue), Bob fixed.
2. Bob hair color A/B (brown vs silver white), Alice fixed.
3. KOMA 1 retains semantic overlap between Alice and Bob, logging overlap stats.
4. Multi-zone diagnostic difference measurements:
   - Alice Mask MeanDiff
   - Bob Mask MeanDiff
   - KOMA 1 Remainder MeanDiff
   - KOMA 2 MeanDiff
   - KOMA 3 MeanDiff
   - Other Panels MeanDiff
   - Outside Frame MeanDiff
   - Diagnostic Ratios (Target/Other Char, Target/Remainder, Target/Other Panels)
5. 5-Panel Actual SDXL Image Generation (N=5 viability proof).

Saves results to output/Tegaki/Phase3D1/character_locality_summary.json.
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
from tegaki_manga_nodes.panel_layout_split import generic_split_panel


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


def compute_overlap_stats(alice_rel: dict, bob_rel: dict) -> dict:
    """
    Computes overlap statistics between Alice and Bob relative bboxes in KOMA 1.
    """
    ax0, ay0 = alice_rel["x"], alice_rel["y"]
    ax1, ay1 = ax0 + alice_rel["w"], ay0 + alice_rel["h"]
    bx0, by0 = bob_rel["x"], bob_rel["y"]
    bx1, by1 = bx0 + bob_rel["w"], by0 + bob_rel["h"]

    alice_area = alice_rel["w"] * alice_rel["h"]
    bob_area = bob_rel["w"] * bob_rel["h"]

    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)

    if ix1 > ix0 and iy1 > iy0:
        intersection_area = (ix1 - ix0) * (iy1 - iy0)
    else:
        intersection_area = 0.0

    union_area = alice_area + bob_area - intersection_area
    overlap_ratio_union = intersection_area / max(1e-6, union_area)
    overlap_ratio_alice = intersection_area / max(1e-6, alice_area)

    return {
        "alice_area": round(alice_area, 4),
        "bob_area": round(bob_area, 4),
        "intersection_area": round(intersection_area, 4),
        "overlap_ratio_union": round(overlap_ratio_union, 4),
        "overlap_ratio_alice": round(overlap_ratio_alice, 4)
    }


def build_character_test_workflow(
    alice_prompt: str,
    bob_prompt: str,
    cn_strength: float = 0.60,
    seed: int = 43,
    steps: int = 8,
    save_prefix: str = "Tegaki/Phase3D1/CharTest"
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
                "prompt": "classroom, two students standing side by side talking, medium shot",
                "negative_prompt": "empty room, solo",
                "local_regions": [],
                "characters": [
                    {
                        "character_id": "char_alice", "enabled": True,
                        "prompt_override": "medium shot, looking right, talking",
                        "area": {"x": 0.05, "y": 0.08, "w": 0.62, "h": 0.84}
                    },
                    {
                        "character_id": "char_bob", "enabled": True,
                        "prompt_override": "medium shot, looking left, listening",
                        "area": {"x": 0.33, "y": 0.08, "w": 0.62, "h": 0.84}
                    }
                ]
            },
            {
                "id": 2, "name": "KOMA 2", "enabled": True,
                "x": 0.05, "y": 0.45, "w": 0.45, "h": 0.50,
                "prompt": "school corridor, lockers, hallway",
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
                "prompt": alice_prompt,
                "negative_prompt": "blurry, low quality",
                "loras": []
            },
            {
                "id": "char_bob", "name": "Bob", "enabled": True,
                "prompt": bob_prompt,
                "negative_prompt": "bad anatomy",
                "loras": []
            }
        ]
    }

    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"}},
        "2": {"class_type": "TegakiLoraPromptLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "text": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "3": {"class_type": "TegakiMangaCastMaster", "inputs": {"cast_spec_data": json.dumps(cast_spec)}},
        "4": {"class_type": "TegakiMangaRegionEditor", "inputs": {"panel_count": 3, "canvas_width": W, "canvas_height": H, "global_prompt": region_spec["global_prompt"], "region_spec_data": json.dumps(region_spec)}},
        "5": {"class_type": "TegakiMangaPageCompiler", "inputs": {"region_spec": ["4", 0], "cast_spec": ["3", 1], "global_loras": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "6": {"class_type": "TegakiMangaPanelLayoutEditor", "inputs": {"canvas_width": W, "canvas_height": H, "line_thickness": 4, "panel_layout_spec_data": json.dumps(layout_spec)}},
        "7": {"class_type": "TegakiMangaLayoutAwareConditioningBuilder", "inputs": {"clip": ["2", 1], "page_compile_plan": ["5", 0], "panel_layout_spec": ["6", 1], "panel_strength": 1.0, "character_strength": 0.9, "set_cond_area": "default", "local_region_strength": 0.8, "mask_feather": 0}},
        "8": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "CN-anytest4_illustrious2_A.safetensors"}},
        "9": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["7", 0], "negative": ["7", 1], "control_net": ["8", 0], "image": ["6", 0], "strength": float(cn_strength), "start_percent": 0.0, "end_percent": 1.0}},
        "10": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["9", 0], "negative": ["9", 1], "latent_image": ["10", 0], "seed": seed, "control_after_generate": "fixed", "steps": steps, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["1", 2]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": save_prefix}}
    }
    return workflow


def build_5panel_workflow(
    seed: int = 42,
    steps: int = 8,
    cn_strength: float = 0.60,
    save_prefix: str = "Tegaki/Phase3D1/Test5_5Panel_Actual"
):
    W, H = 832, 1216
    spec4 = get_default_panel_layout_spec(W, H, preset="4_grid")
    spec5 = generic_split_panel(spec4, "p1", "horizontal", 0.5)

    region_spec_5 = {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "panel_count": 5,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast, screentone shading",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d, blurry",
        "regions": [
            {"id": 1, "name": "KOMA 1", "enabled": True, "x": 0.05, "y": 0.05, "w": 0.45, "h": 0.22, "prompt": "close-up eyes, intense expression", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 2, "name": "KOMA 2", "enabled": True, "x": 0.50, "y": 0.05, "w": 0.45, "h": 0.45, "prompt": "shouting face, dramatic angle", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 3, "name": "KOMA 3", "enabled": True, "x": 0.05, "y": 0.50, "w": 0.45, "h": 0.45, "prompt": "running pose, motion lines", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 4, "name": "KOMA 4", "enabled": True, "x": 0.50, "y": 0.50, "w": 0.45, "h": 0.45, "prompt": "reaching hand, dramatic perspective", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 5, "name": "KOMA 5", "enabled": True, "x": 0.05, "y": 0.28, "w": 0.45, "h": 0.22, "prompt": "clenched fist, speed lines", "negative_prompt": "", "local_regions": [], "characters": []}
        ]
    }

    cast_spec = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice", "name": "Alice", "enabled": True,
                "prompt": "1girl, golden blonde hair, twin tails, school uniform",
                "negative_prompt": "blurry",
                "loras": []
            }
        ]
    }

    workflow = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"}},
        "2": {"class_type": "TegakiLoraPromptLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "text": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "3": {"class_type": "TegakiMangaCastMaster", "inputs": {"cast_spec_data": json.dumps(cast_spec)}},
        "4": {"class_type": "TegakiMangaRegionEditor", "inputs": {"panel_count": 5, "canvas_width": W, "canvas_height": H, "global_prompt": region_spec_5["global_prompt"], "region_spec_data": json.dumps(region_spec_5)}},
        "5": {"class_type": "TegakiMangaPageCompiler", "inputs": {"region_spec": ["4", 0], "cast_spec": ["3", 1], "global_loras": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"}},
        "6": {"class_type": "TegakiMangaPanelLayoutEditor", "inputs": {"canvas_width": W, "canvas_height": H, "line_thickness": 4, "panel_layout_spec_data": json.dumps(spec5)}},
        "7": {"class_type": "TegakiMangaLayoutAwareConditioningBuilder", "inputs": {"clip": ["2", 1], "page_compile_plan": ["5", 0], "panel_layout_spec": ["6", 1], "panel_strength": 1.0, "character_strength": 0.9, "set_cond_area": "default", "local_region_strength": 0.8, "mask_feather": 0}},
        "8": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "CN-anytest4_illustrious2_A.safetensors"}},
        "9": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["7", 0], "negative": ["7", 1], "control_net": ["8", 0], "image": ["6", 0], "strength": float(cn_strength), "start_percent": 0.0, "end_percent": 1.0}},
        "10": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "11": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["9", 0], "negative": ["9", 1], "latent_image": ["10", 0], "seed": seed, "control_after_generate": "fixed", "steps": steps, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["1", 2]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": save_prefix}}
    }
    return workflow


def compute_character_multizone_diff(
    img_a_path: str,
    img_b_path: str,
    target_char: str = "alice",
    W: int = 832,
    H: int = 1216
) -> dict:
    """
    Computes mean pixel difference for character variation across:
    - Alice mask (projected in KOMA 1)
    - Bob mask (projected in KOMA 1)
    - KOMA 1 remainder mask
    - KOMA 2 mask
    - KOMA 3 mask
    - Other panels mask (KOMA 2 & 3)
    - Outside frame mask
    """
    img_a = Image.open(img_a_path).convert("RGB")
    img_b = Image.open(img_b_path).convert("RGB")
    arr_a = np.array(img_a).astype(np.float32)
    arr_b = np.array(img_b).astype(np.float32)

    diff = np.mean(np.abs(arr_a - arr_b), axis=2)  # [H, W], scale [0, 255]

    def _rasterize_polygon(pts):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        return np.array(m).astype(np.float32) / 255.0 > 0.5

    def _rasterize_box(x0, y0, x1, y1):
        m = np.zeros((H, W), dtype=bool)
        m[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = True
        return m

    # Panel Polygons in 3_basic
    koma1_pts = [(int(0.05 * W), int(0.05 * H)), (int(0.05 * W), int(0.45 * H)),
                 (int(0.50 * W), int(0.45 * H)), (int(0.95 * W), int(0.45 * H)), (int(0.95 * W), int(0.05 * H))]
    koma2_pts = [(int(0.05 * W), int(0.45 * H)), (int(0.05 * W), int(0.95 * H)),
                 (int(0.50 * W), int(0.95 * H)), (int(0.50 * W), int(0.45 * H))]
    koma3_pts = [(int(0.50 * W), int(0.45 * H)), (int(0.50 * W), int(0.95 * H)),
                 (int(0.95 * W), int(0.95 * H)), (int(0.95 * W), int(0.45 * H))]

    m_koma1 = _rasterize_polygon(koma1_pts)
    m_koma2 = _rasterize_polygon(koma2_pts)
    m_koma3 = _rasterize_polygon(koma3_pts)

    # Frame mask
    frame_m = np.zeros((H, W), dtype=bool)
    frame_m[int(0.05 * H):int(0.95 * H), int(0.05 * W):int(0.95 * W)] = True
    outside_frame_m = ~frame_m

    # KOMA 1 character boxes (relative to KOMA 1 bbox: x: 0.05..0.95, y: 0.05..0.45)
    # Alice rel: x: 0.05, y: 0.08, w: 0.62, h: 0.84
    # Page coords:
    ax0 = int((0.05 + 0.05 * 0.90) * W)
    ay0 = int((0.05 + 0.08 * 0.40) * H)
    ax1 = int((0.05 + (0.05 + 0.62) * 0.90) * W)
    ay1 = int((0.05 + (0.08 + 0.84) * 0.40) * H)
    m_alice = _rasterize_box(ax0, ay0, ax1, ay1) & m_koma1

    # Bob rel: x: 0.33, y: 0.08, w: 0.62, h: 0.84
    bx0 = int((0.05 + 0.33 * 0.90) * W)
    by0 = int((0.05 + 0.08 * 0.40) * H)
    bx1 = int((0.05 + (0.33 + 0.62) * 0.90) * W)
    by1 = int((0.05 + (0.08 + 0.84) * 0.40) * H)
    m_bob = _rasterize_box(bx0, by0, bx1, by1) & m_koma1

    # KOMA 1 remainder: pixels in KOMA 1 not in Alice or Bob bbox
    m_koma1_remainder = m_koma1 & ~(m_alice | m_bob)
    m_other_panels = m_koma2 | m_koma3

    diff_alice = float(np.mean(diff[m_alice])) if np.sum(m_alice) > 0 else 0.0
    diff_bob = float(np.mean(diff[m_bob])) if np.sum(m_bob) > 0 else 0.0
    diff_remainder = float(np.mean(diff[m_koma1_remainder])) if np.sum(m_koma1_remainder) > 0 else 0.0
    diff_koma2 = float(np.mean(diff[m_koma2])) if np.sum(m_koma2) > 0 else 0.0
    diff_koma3 = float(np.mean(diff[m_koma3])) if np.sum(m_koma3) > 0 else 0.0
    diff_other_panels = float(np.mean(diff[m_other_panels])) if np.sum(m_other_panels) > 0 else 0.0
    diff_outside = float(np.mean(diff[outside_frame_m])) if np.sum(outside_frame_m) > 0 else 0.0

    if target_char == "alice":
        target_diff = diff_alice
        other_char_diff = diff_bob
    else:
        target_diff = diff_bob
        other_char_diff = diff_alice

    target_to_other_char = target_diff / max(1e-5, other_char_diff)
    target_to_remainder = target_diff / max(1e-5, diff_remainder)
    target_to_other_panels = target_diff / max(1e-5, diff_other_panels)
    target_to_outside = target_diff / max(1e-5, diff_outside)

    return {
        "target_character": target_char,
        "alice_mask_mean_diff": round(diff_alice, 4),
        "bob_mask_mean_diff": round(diff_bob, 4),
        "koma1_remainder_mean_diff": round(diff_remainder, 4),
        "koma2_mean_diff": round(diff_koma2, 4),
        "koma3_mean_diff": round(diff_koma3, 4),
        "other_panels_mean_diff": round(diff_other_panels, 4),
        "outside_frame_mean_diff": round(diff_outside, 4),
        "target_to_other_char_ratio": round(target_to_other_char, 4),
        "target_to_same_panel_remainder_ratio": round(target_to_remainder, 4),
        "target_to_other_panels_ratio": round(target_to_other_panels, 4),
        "target_to_outside_ratio": round(target_to_outside, 4)
    }


def run_character_locality_tests():
    print("=" * 80)
    print(" Phase 3D.1: Character Locality & 5-Panel Generation Diagnostic Suite")
    print("=" * 80)

    # 1. Overlap calculation
    alice_rel = {"x": 0.05, "y": 0.08, "w": 0.62, "h": 0.84}
    bob_rel = {"x": 0.33, "y": 0.08, "w": 0.62, "h": 0.84}
    overlap_stats = compute_overlap_stats(alice_rel, bob_rel)
    print("\n--- 1. KOMA 1 Character Overlap Geometry ---")
    print(f"  Alice Area: {overlap_stats['alice_area']}")
    print(f"  Bob Area: {overlap_stats['bob_area']}")
    print(f"  Intersection Area: {overlap_stats['intersection_area']}")
    print(f"  Overlap Ratio (Intersection / Union): {overlap_stats['overlap_ratio_union'] * 100:.2f}%")
    print(f"  Overlap Ratio (Intersection / Alice): {overlap_stats['overlap_ratio_alice'] * 100:.2f}%")

    prompt_alice_a = "1girl, golden blonde hair, twin tails, blue eyes, school uniform"
    prompt_alice_b = "1girl, bright cyan blue hair, twin tails, blue eyes, school uniform"
    prompt_bob_a = "1boy, short brown hair, school uniform"
    prompt_bob_b = "1boy, silver white hair, school uniform"

    # Base condition: Alice A (blonde) + Bob A (brown)
    print("\n--- 2. Base Condition (Alice A blonde + Bob A brown) ---")
    wf_base = build_character_test_workflow(
        alice_prompt=prompt_alice_a,
        bob_prompt=prompt_bob_a,
        cn_strength=0.60,
        seed=43,
        steps=8,
        save_prefix="Tegaki/Phase3D1/Char_Base_AliceA_BobA"
    )
    path_base = run_or_reuse("Char_Base_AliceA_BobA", wf_base)

    # Alice B condition: Alice B (cyan blue) + Bob A (brown)
    print("\n--- 3. Alice B Condition (Alice B cyan blue + Bob A brown) ---")
    wf_alice_b = build_character_test_workflow(
        alice_prompt=prompt_alice_b,
        bob_prompt=prompt_bob_a,
        cn_strength=0.60,
        seed=43,
        steps=8,
        save_prefix="Tegaki/Phase3D1/Char_AliceB_BobA"
    )
    path_alice_b = run_or_reuse("Char_AliceB_BobA", wf_alice_b)

    # Bob B condition: Alice A (blonde) + Bob B (silver)
    print("\n--- 4. Bob B Condition (Alice A blonde + Bob B silver) ---")
    wf_bob_b = build_character_test_workflow(
        alice_prompt=prompt_alice_a,
        bob_prompt=prompt_bob_b,
        cn_strength=0.60,
        seed=43,
        steps=8,
        save_prefix="Tegaki/Phase3D1/Char_AliceA_BobB"
    )
    path_bob_b = run_or_reuse("Char_AliceA_BobB", wf_bob_b)

    # Multi-zone diff metrics for Alice A vs Alice B
    print("\n--- 5. Computing Alice Locality Metrics ---")
    alice_metrics = compute_character_multizone_diff(path_base, path_alice_b, target_char="alice")
    print(f"  Alice Mask MeanDiff: {alice_metrics['alice_mask_mean_diff']}")
    print(f"  Bob Mask MeanDiff: {alice_metrics['bob_mask_mean_diff']}")
    print(f"  KOMA 1 Remainder MeanDiff: {alice_metrics['koma1_remainder_mean_diff']}")
    print(f"  Other Panels MeanDiff: {alice_metrics['other_panels_mean_diff']}")
    print(f"  Outside Frame MeanDiff: {alice_metrics['outside_frame_mean_diff']}")
    print(f"  Target / Other Character Ratio: {alice_metrics['target_to_other_char_ratio']}")
    print(f"  Target / Same-Panel Remainder Ratio: {alice_metrics['target_to_same_panel_remainder_ratio']}")
    print(f"  Target / Other Panels Ratio: {alice_metrics['target_to_other_panels_ratio']}")

    # Multi-zone diff metrics for Bob A vs Bob B
    print("\n--- 6. Computing Bob Locality Metrics ---")
    bob_metrics = compute_character_multizone_diff(path_base, path_bob_b, target_char="bob")
    print(f"  Bob Mask MeanDiff: {bob_metrics['bob_mask_mean_diff']}")
    print(f"  Alice Mask MeanDiff: {bob_metrics['alice_mask_mean_diff']}")
    print(f"  KOMA 1 Remainder MeanDiff: {bob_metrics['koma1_remainder_mean_diff']}")
    print(f"  Other Panels MeanDiff: {bob_metrics['other_panels_mean_diff']}")
    print(f"  Outside Frame MeanDiff: {bob_metrics['outside_frame_mean_diff']}")
    print(f"  Target / Other Character Ratio: {bob_metrics['target_to_other_char_ratio']}")
    print(f"  Target / Same-Panel Remainder Ratio: {bob_metrics['target_to_same_panel_remainder_ratio']}")
    print(f"  Target / Other Panels Ratio: {bob_metrics['target_to_other_panels_ratio']}")

    # 5-Panel Actual Image Generation
    print("\n--- 7. 5-Panel Actual SDXL Image Generation ---")
    wf_5panel = build_5panel_workflow(seed=42, steps=8, cn_strength=0.60, save_prefix="Tegaki/Phase3D1/Test5_5Panel_Actual")
    path_5panel = run_or_reuse("Test5_5Panel_Actual", wf_5panel)
    print(f"  -> 5-Panel Actual Image: {path_5panel}")

    summary = {
        "overlap_geometry": overlap_stats,
        "alice_ab_test": {
            "path_A_base": path_base,
            "path_B_alice": path_alice_b,
            "metrics": alice_metrics
        },
        "bob_ab_test": {
            "path_A_base": path_base,
            "path_B_bob": path_bob_b,
            "metrics": bob_metrics
        },
        "five_panel_generation": {
            "path": path_5panel,
            "status": "PASS" if os.path.exists(path_5panel) and os.path.getsize(path_5panel) > 1000 else "FAIL"
        }
    }

    out_file = os.path.join(OUTPUT_DIR, "character_locality_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved character locality & 5-panel summary to {out_file}")
    return summary


if __name__ == "__main__":
    run_character_locality_tests()
