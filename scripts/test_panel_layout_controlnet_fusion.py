import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import math
from PIL import Image, ImageDraw, ImageOps
import numpy as np

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "PanelLayoutFusion")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from custom_nodes.tegaki_manga_nodes.panel_layout_split import generic_split_panel
from custom_nodes.tegaki_manga_nodes.panel_layout_editor import render_panel_layout_image


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

    proc = subprocess.Popen(cmd, cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    start = time.time()
    while time.time() - start < timeout:
        if is_comfy_running():
            print(f"  [ComfyUI] Server started successfully in {time.time() - start:.1f}s.")
            return proc
        time.sleep(2)
    raise TimeoutError("Failed to start ComfyUI server within timeout.")


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
            with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
                history = json.loads(resp.read().decode('utf-8'))
            if prompt_id in history:
                return history[prompt_id].get("outputs", {})
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout} seconds")


def compute_edge_response_metric(gen_img_path: str, guide_img_path: str) -> float:
    """
    ControlNet ガイド画像の黒枠線（Guide Edges）付近における
    生成画像の輝度勾配（Edge Response）を計算する。
    """
    if not os.path.exists(gen_img_path) or not os.path.exists(guide_img_path):
        return 0.0

    gen = Image.open(gen_img_path).convert("L")
    guide = Image.open(guide_img_path).convert("L")

    gen_arr = np.array(gen).astype(np.float32) / 255.0
    guide_arr = np.array(guide).astype(np.float32) / 255.0

    # ガイドの黒線マスク (輝度 < 0.2)
    edge_mask = (guide_arr < 0.2).astype(np.float32)
    if np.sum(edge_mask) == 0:
        return 0.0

    # 生成画像の簡易勾配 (Sobel/差分)
    gy, gx = np.gradient(gen_arr)
    grad_mag = np.sqrt(gx**2 + gy**2)

    # 枠線上での平均勾配強度
    edge_response = float(np.sum(grad_mag * edge_mask) / np.sum(edge_mask))
    return round(edge_response, 4)


def build_fusion_workflow(
    layout_spec: dict,
    cn_strength: float = 0.60,
    seed: int = 42,
    save_prefix: str = "Tegaki/PanelLayoutFusion/Test"
):
    W = layout_spec["canvas"]["width"]
    H = layout_spec["canvas"]["height"]

    # ガイド画像の生成と保存 (一時ファイル)
    guide_pil = render_panel_layout_image(layout_spec, line_thickness=4)
    guide_filename = f"guide_{int(time.time() * 1000)}.png"
    guide_path = os.path.join(ROOT_DIR, "ComfyUI", "input", guide_filename)
    os.makedirs(os.path.dirname(guide_path), exist_ok=True)
    guide_pil.save(guide_path)

    # 上段パネル付近に重なる Semantic Region (A: 少女, B: 少年)
    two_region_spec = {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "global_prompt": "1girl, 1boy, manga page, three panels, talking in upper panel, monochrome manga, screentone, expressive anime",
        "global_negative": "worst quality, low quality, bad anatomy, bad hands, blurry, color, photo, realistic",
        "regions": [
            {
                "id": "A",
                "x": 0.05,
                "y": 0.08,
                "w": 0.55,
                "h": 0.35,
                "prompt": "1girl, solo, smiling, blonde hair, long hair, upper body",
                "negative_prompt": "",
                "weight": 1.0,
                "enabled": True
            },
            {
                "id": "B",
                "x": 0.38,
                "y": 0.08,
                "w": 0.55,
                "h": 0.35,
                "prompt": "1boy, solo, looking at her, black hair, short hair, upper body",
                "negative_prompt": "",
                "weight": 1.0,
                "enabled": True
            }
        ],
        "metadata": {"layout_preset": "semantic_overlap"}
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
                "width": W,
                "height": H,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "TegakiTwoRegionCoreConditioner",
            "inputs": {
                "clip": ["1", 1],
                "two_region_spec": two_region_spec,
                "strength_A": 1.0,
                "strength_B": 1.0,
                "set_cond_area": "default",
                "mask_feather": 0
            }
        },
        "4": {
            "class_type": "LoadImage",
            "inputs": {
                "image": guide_filename
            }
        }
    }

    if cn_strength > 0.001:
        workflow["5"] = {
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": "CN-anytest4_illustrious2_A.safetensors"
            }
        }
        workflow["6"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["3", 0],
                "negative": ["3", 1],
                "control_net": ["5", 0],
                "image": ["4", 0],
                "strength": float(cn_strength),
                "start_percent": 0.0,
                "end_percent": 1.0
            }
        }
        pos_link = ["6", 0]
        neg_link = ["6", 1]
    else:
        pos_link = ["3", 0]
        neg_link = ["3", 1]

    workflow["7"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": pos_link,
            "negative": neg_link,
            "latent_image": ["2", 0],
            "seed": int(seed),
            "control_after_generate": "fixed",
            "steps": 15,
            "cfg": 6.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0
        }
    }
    workflow["8"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["7", 0],
            "vae": ["1", 2]
        }
    }
    workflow["9"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["8", 0],
            "filename_prefix": save_prefix
        }
    }

    return workflow, guide_path


def run_experiment_matrix():
    print("================================================================================")
    print("Phase 3C.1.1 — Panel Topology & ControlNet Fusion Live Experiment Harness")
    print("================================================================================")

    server_proc = start_comfy_server()
    time.sleep(3)

    results = []

    # 1. ControlNet Strength Sweep (3 Panels Basic)
    sweep_strengths = [0.0, 0.35, 0.60, 0.85]
    spec_3b = get_default_panel_layout_spec(832, 1216, preset="3_basic")

    print("\n--- 1. ControlNet Strength Sweep (OFF, 0.35, 0.60, 0.85) ---")
    for st in sweep_strengths:
        label = "CN_OFF" if st == 0.0 else f"CN_{int(st*100):02d}"
        prefix = f"Tegaki/PanelLayoutFusion/Sweep_{label}"
        print(f"\n[Running] Strength: {st} ({label})...")
        wf, guide_p = build_fusion_workflow(spec_3b, cn_strength=st, seed=42, save_prefix=prefix)
        t0 = time.time()
        q_res = queue_prompt(wf)
        pid = q_res["prompt_id"]
        out = wait_for_prompt(pid, timeout=120)
        elapsed = time.time() - t0

        saved_files = out.get("9", {}).get("images", [])
        saved_filename = saved_files[0]["filename"] if saved_files else None
        saved_subfolder = saved_files[0]["subfolder"] if saved_files else ""
        img_path = os.path.join(ROOT_DIR, "ComfyUI", "output", saved_subfolder, saved_filename) if saved_filename else ""

        edge_resp = compute_edge_response_metric(img_path, guide_p)
        print(f"  -> Generated: {saved_filename} in {elapsed:.1f}s (Edge Response: {edge_resp})")
        results.append({
            "test": "Strength Sweep",
            "label": label,
            "strength": st,
            "layout": "3_basic",
            "elapsed": round(elapsed, 1),
            "image_path": img_path,
            "guide_path": guide_p,
            "edge_response": edge_resp
        })

    # 2. Layout Variant Test (Strength: 0.60)
    print("\n--- 2. Layout Variant Tests (3_dynamic, 4_grid, diagonal) ---")
    variants = [
        ("3_dynamic", get_default_panel_layout_spec(832, 1216, preset="3_dynamic")),
        ("4_grid", get_default_panel_layout_spec(832, 1216, preset="4_grid")),
        ("diagonal", generic_split_panel(get_default_panel_layout_spec(832, 1216, preset="1_full"), "p1", split_mode="diag_slash"))
    ]

    for v_name, v_spec in variants:
        prefix = f"Tegaki/PanelLayoutFusion/Variant_{v_name}"
        print(f"\n[Running] Variant: {v_name}...")
        wf, guide_p = build_fusion_workflow(v_spec, cn_strength=0.60, seed=42, save_prefix=prefix)
        t0 = time.time()
        q_res = queue_prompt(wf)
        pid = q_res["prompt_id"]
        out = wait_for_prompt(pid, timeout=120)
        elapsed = time.time() - t0

        saved_files = out.get("9", {}).get("images", [])
        saved_filename = saved_files[0]["filename"] if saved_files else None
        saved_subfolder = saved_files[0]["subfolder"] if saved_files else ""
        img_path = os.path.join(ROOT_DIR, "ComfyUI", "output", saved_subfolder, saved_filename) if saved_filename else ""

        edge_resp = compute_edge_response_metric(img_path, guide_p)
        print(f"  -> Generated: {saved_filename} in {elapsed:.1f}s (Edge Response: {edge_resp})")
        results.append({
            "test": "Layout Variant",
            "label": v_name,
            "strength": 0.60,
            "layout": v_name,
            "elapsed": round(elapsed, 1),
            "image_path": img_path,
            "guide_path": guide_p,
            "edge_response": edge_resp
        })

    # 3. Create Contact Sheet
    print("\n--- 3. Creating Contact Sheet ---")
    valid_imgs = [r["image_path"] for r in results if os.path.exists(r["image_path"])]
    if valid_imgs:
        thumb_w, thumb_h = 208, 304
        cols = 4
        rows = math.ceil(len(valid_imgs) / cols)
        sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (240, 240, 240))
        draw = ImageDraw.Draw(sheet)

        for idx, r in enumerate(results):
            if not os.path.exists(r["image_path"]):
                continue
            c = idx % cols
            row = idx // cols
            im = Image.open(r["image_path"]).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (c * thumb_w, row * thumb_h))
            draw.text((c * thumb_w + 5, row * thumb_h + 5), f"{r['label']} (ER:{r['edge_response']})", fill=(255, 0, 0))

        contact_path = os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "PanelLayoutFusion", "CN_Fusion_Contact_Sheet.png")
        os.makedirs(os.path.dirname(contact_path), exist_ok=True)
        sheet.save(contact_path)
        print(f"  Contact Sheet saved: {contact_path}")

    # 結果サマリー出力
    summary_path = os.path.join(ROOT_DIR, "docs", "reports", "phase3c_1_1_fusion_metrics.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Done] Experiment results saved to {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(run_experiment_matrix())
