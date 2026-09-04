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
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "MangaLayoutFusion")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.panel_layout_split import generic_split_panel
from tegaki_manga_nodes.panel_layout_editor import render_panel_layout_image


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
            print("  [ComfyUI] Waiting 30s for background warmup tasks (PromptChain/Manager) to settle...")
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
            print(f"  [Queue] Successfully queued prompt ID: {res.get('prompt_id')}")
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
        except Exception as e:
            if time.time() - last_print > 10:
                print(f"  [Wait] Poll /history error: {e}")

        if time.time() - last_print > 10:
            try:
                with urllib.request.urlopen(f"{COMFY_URL}/queue", timeout=5) as qresp:
                    qdata = json.loads(qresp.read().decode('utf-8'))
                    r_count = len(qdata.get('queue_running', []))
                    p_count = len(qdata.get('queue_pending', []))
                    print(f"  [Wait] ({time.time() - start_time:.0f}s) Running: {r_count}, Pending: {p_count}")
            except Exception as qe:
                print(f"  [Wait] Poll /queue error: {qe}")
            last_print = time.time()

        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout} seconds")


def compute_edge_response_metric(gen_img_path: str, guide_img_path: str) -> float:
    if not os.path.exists(gen_img_path) or not os.path.exists(guide_img_path):
        return 0.0

    gen = Image.open(gen_img_path).convert("L")
    guide = Image.open(guide_img_path).convert("L")

    gen_arr = np.array(gen).astype(np.float32) / 255.0
    guide_arr = np.array(guide).astype(np.float32) / 255.0

    edge_mask = (guide_arr < 0.2).astype(np.float32)
    if np.sum(edge_mask) == 0:
        return 0.0

    gy, gx = np.gradient(gen_arr)
    grad_mag = np.sqrt(gx**2 + gy**2)

    edge_response = float(np.sum(grad_mag * edge_mask) / np.sum(edge_mask))
    return round(edge_response, 4)


def compute_region_locality(img_a_path: str, img_b_path: str, mask_polygon_pts: list, W: int, H: int) -> float:
    img_a = Image.open(img_a_path).convert("RGB")
    img_b = Image.open(img_b_path).convert("RGB")

    arr_a = np.array(img_a).astype(np.float32)
    arr_b = np.array(img_b).astype(np.float32)

    diff = np.mean(np.abs(arr_a - arr_b), axis=2)  # [H, W]

    mask_img = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon(mask_polygon_pts, fill=255)
    mask_arr = np.array(mask_img).astype(np.float32) / 255.0

    in_mask = mask_arr > 0.5
    out_mask = ~in_mask

    diff_in = float(np.mean(diff[in_mask])) if np.sum(in_mask) > 0 else 0.0
    diff_out = float(np.mean(diff[out_mask])) if np.sum(out_mask) > 0 else 1.0

    ratio = diff_in / max(1e-5, diff_out)
    return round(ratio, 4)


def build_phase3d_prompt_workflow(
    region_spec: dict,
    cast_spec: dict,
    layout_spec: dict,
    cn_strength: float = 0.60,
    seed: int = 42,
    steps: int = 15,
    save_prefix: str = "Tegaki/MangaLayoutFusion/POC"
):
    W = layout_spec["canvas"]["width"]
    H = layout_spec["canvas"]["height"]

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
                "text": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"
            }
        },
        "3": {
            "class_type": "TegakiMangaRegionEditor",
            "inputs": {
                "panel_count": len(region_spec.get("regions", [])),
                "canvas_width": W,
                "canvas_height": H,
                "global_prompt": region_spec.get("global_prompt", ""),
                "region_spec_data": json.dumps(region_spec)
            }
        },
        "4": {
            "class_type": "TegakiMangaPageCompiler",
            "inputs": {
                "region_spec": ["3", 0],
                "cast_spec": json.dumps(cast_spec),
                "global_loras": "<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.4>"
            }
        },
        "5": {
            "class_type": "TegakiMangaPanelLayoutEditor",
            "inputs": {
                "canvas_width": W,
                "canvas_height": H,
                "line_thickness": 4,
                "panel_layout_spec_data": json.dumps(layout_spec)
            }
        },
        "6": {
            "class_type": "TegakiMangaLayoutAwareConditioningBuilder",
            "inputs": {
                "clip": ["2", 1],
                "page_compile_plan": ["4", 0],
                "panel_layout_spec": ["5", 1],
                "panel_strength": 1.0,
                "character_strength": 0.9,
                "set_cond_area": "default",
                "local_region_strength": 0.8,
                "mask_feather": 0
            }
        },
        "7": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": W,
                "height": H,
                "batch_size": 1
            }
        }
    }

    if cn_strength > 0.001:
        workflow["8"] = {
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": "CN-anytest4_illustrious2_A.safetensors"
            }
        }
        workflow["9"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["6", 1],
                "control_net": ["8", 0],
                "image": ["5", 0],
                "strength": float(cn_strength),
                "start_percent": 0.0,
                "end_percent": 1.0
            }
        }
        pos_link = ["9", 0]
        neg_link = ["9", 1]
    else:
        pos_link = ["6", 0]
        neg_link = ["6", 1]

    workflow["10"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["2", 0],
            "positive": pos_link,
            "negative": neg_link,
            "latent_image": ["7", 0],
            "seed": int(seed),
            "control_after_generate": "fixed",
            "steps": int(steps),
            "cfg": 6.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0
        }
    }
    workflow["11"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["10", 0],
            "vae": ["1", 2]
        }
    }
    workflow["12"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["11", 0],
            "filename_prefix": save_prefix
        }
    }

    return workflow


def run_tests():
    print("=" * 80)
    print(" Phase 3D: Variable N-Region Live Generation & Semantic Locality Oracle")
    print("=" * 80)

    # 1. 共通スペック準備
    W, H = 832, 1216
    layout_3_basic = get_default_panel_layout_spec(W, H, preset="3_basic")

    # ガイド画像出力
    guide_pil = render_panel_layout_image(layout_3_basic, line_thickness=4)
    guide_path = os.path.join(OUTPUT_DIR, "guide_3_basic.png")
    guide_pil.save(guide_path)

    # 基本 3-panel Region Spec
    def create_region_spec_3(koma2_prompt="school corridor, walking scene"):
        return {
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
                            "id": "lr_window_desks",
                            "name": "Window Desks",
                            "enabled": True,
                            "prompt": "school desks near the window, sunlight streaming",
                            "negative_prompt": "dark",
                            "area": {"x": 0.10, "y": 0.15, "w": 0.38, "h": 0.70}
                        }
                    ],
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "prompt_override": "annoyed expression, looking right",
                            "area": {"x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                        },
                        {
                            "character_id": "char_bob",
                            "enabled": True,
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
                            "character_id": "char_alice",
                            "enabled": True,
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
                            "character_id": "char_bob",
                            "enabled": True,
                            "prompt_override": "standing by fence",
                            "area": {"x": 0.20, "y": 0.10, "w": 0.60, "h": 0.80}
                        }
                    ]
                }
            ]
        }

    # Cast Spec
    def create_cast_spec(alice_hair="blonde twin tails"):
        return {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice", "name": "Alice", "enabled": True,
                    "prompt": f"1girl, {alice_hair}, blue eyes, school uniform",
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
    results = {}

    def get_existing_image(prefix):
        base_name = os.path.basename(prefix)
        # Check both potential output directories
        check_dirs = [
            os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "MangaLayoutFusion"),
            os.path.join(OUTPUT_DIR)
        ]
        for cdir in check_dirs:
            if os.path.exists(cdir):
                for f in os.listdir(cdir):
                    if f.startswith(base_name) and f.endswith(".png"):
                        full_p = os.path.join(cdir, f)
                        if os.path.getsize(full_p) > 1000:
                            return full_p
        return None

    def fetch_image(outputs):
        save_node_out = outputs.get("12", {})
        imgs = save_node_out.get("images", [])
        if not imgs:
            raise RuntimeError("No image output returned from SaveImage node.")
        fn = imgs[0]["filename"]
        sub = imgs[0].get("subfolder", "")
        img_path = os.path.join(ROOT_DIR, "ComfyUI", "output", sub, fn)
        return img_path

    def run_or_reuse(prefix, wf):
        existing = get_existing_image(prefix)
        if existing:
            print(f"  -> Reusing existing generated image: {existing}")
            return existing
        start_comfy_server(timeout=60)
        res = queue_prompt(wf)
        out = wait_for_prompt(res["prompt_id"], timeout=400)
        path = fetch_image(out)
        print(f"  -> Generated image: {path}")
        return path

    # =========================================================================
    # Test 1: 3-panel ControlNet ON (strength 0.60)
    # =========================================================================
    print("\n[Test 1] Generating 3-Panel with ControlNet ON (strength 0.60)...")
    wf1 = build_phase3d_prompt_workflow(
        region_spec=create_region_spec_3(),
        cast_spec=create_cast_spec(),
        layout_spec=layout_3_basic,
        cn_strength=0.60,
        seed=42,
        save_prefix="Tegaki/MangaLayoutFusion/Test1_CN_ON"
    )
    path1 = run_or_reuse("Test1_CN_ON", wf1)
    edge_on = compute_edge_response_metric(path1, guide_path)
    print(f"  -> ControlNet ON Edge Response: {edge_on}")
    results["Test1_CN_ON"] = {"path": path1, "edge_response": edge_on}

    # =========================================================================
    # Test 2: 3-panel ControlNet OFF (strength 0.00)
    # =========================================================================
    print("\n[Test 2] Generating 3-Panel with ControlNet OFF (strength 0.00)...")
    wf2 = build_phase3d_prompt_workflow(
        region_spec=create_region_spec_3(),
        cast_spec=create_cast_spec(),
        layout_spec=layout_3_basic,
        cn_strength=0.00,
        seed=42,
        save_prefix="Tegaki/MangaLayoutFusion/Test2_CN_OFF"
    )
    path2 = run_or_reuse("Test2_CN_OFF", wf2)
    edge_off = compute_edge_response_metric(path2, guide_path)
    print(f"  -> ControlNet OFF Edge Response: {edge_off}")
    results["Test2_CN_OFF"] = {"path": path2, "edge_response": edge_off}

    edge_gain = edge_on - edge_off
    print(f"  -> Edge Response Gain: {edge_gain:+.4f} (ON: {edge_on} vs OFF: {edge_off})")
    assert edge_on > edge_off, f"Expected CN ON edge response ({edge_on}) > CN OFF ({edge_off})"

    # =========================================================================
    # Test 3: KOMA 2 Prompt A/B Locality Test
    # =========================================================================
    print("\n[Test 3] KOMA 2 Prompt A/B Locality Test...")
    wf3a = build_phase3d_prompt_workflow(
        region_spec=create_region_spec_3(koma2_prompt="school corridor, lockers, hallway"),
        cast_spec=create_cast_spec(),
        layout_spec=layout_3_basic,
        cn_strength=0.60,
        seed=43,
        steps=8,
        save_prefix="Tegaki/MangaLayoutFusion/Test3A_Corridor"
    )
    path3a = run_or_reuse("Test3A_Corridor", wf3a)
    print(f"  -> Condition A (Corridor) ready: {path3a}")

    wf3b = build_phase3d_prompt_workflow(
        region_spec=create_region_spec_3(koma2_prompt="convenience store interior, brightly lit aisles, shelves with snacks and drinks"),
        cast_spec=create_cast_spec(),
        layout_spec=layout_3_basic,
        cn_strength=0.60,
        seed=43,
        steps=8,
        save_prefix="Tegaki/MangaLayoutFusion/Test3B_Conveni"
    )
    path3b = run_or_reuse("Test3B_Conveni", wf3b)
    print(f"  -> Condition B (Convenience Store) ready: {path3b}")

    # KOMA 2 の多角形 (p2: v4, v6, v7, v5 -> x: [0.05, 0.50], y: [0.45, 0.95])
    koma2_pts = [(int(0.05 * W), int(0.45 * H)), (int(0.05 * W), int(0.95 * H)),
                 (int(0.50 * W), int(0.95 * H)), (int(0.50 * W), int(0.45 * H))]
    koma2_ratio = compute_region_locality(path3a, path3b, koma2_pts, W, H)
    print(f"  -> KOMA 2 Locality Ratio (Target vs Outside): {koma2_ratio:.4f}")
    assert koma2_ratio > 0.0, f"Expected valid KOMA 2 locality ratio, got {koma2_ratio}"
    results["Test3_KOMA2_AB"] = {"path_A": path3a, "path_B": path3b, "locality_ratio": koma2_ratio}

    # =========================================================================
    # Test 4: Alice Hair Color A/B Semantic Conditioning Integration Test (KOMA 1)
    # =========================================================================
    print("\n[Test 4] Alice Hair Color A/B Semantic Conditioning Integration Test...")
    from test_layout_aware_conditioning import MockCLIP
    from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
    from tegaki_manga_nodes.layout_aware_conditioning import TegakiMangaLayoutAwareConditioningBuilder

    compiler = TegakiMangaPageCompiler()
    cond_builder = TegakiMangaLayoutAwareConditioningBuilder()
    mock_clip = MockCLIP()

    reg_spec_3 = create_region_spec_3()
    cast_a = create_cast_spec(alice_hair="golden blonde hair, twin tails")
    cast_b = create_cast_spec(alice_hair="vibrant bright cyan blue hair, twin tails")

    plan_a, _, _, _ = compiler.compile_page(region_spec=reg_spec_3, cast_spec=cast_a)
    plan_b, _, _, _ = compiler.compile_page(region_spec=reg_spec_3, cast_spec=cast_b)

    pos_a, _, pmasks_a, cmasks_a, prev_a, dbg_a, _ = cond_builder.build_conditioning(
        clip=mock_clip, page_compile_plan=plan_a, panel_layout_spec=layout_3_basic
    )
    pos_b, _, pmasks_b, cmasks_b, prev_b, dbg_b, _ = cond_builder.build_conditioning(
        clip=mock_clip, page_compile_plan=plan_b, panel_layout_spec=layout_3_basic
    )

    dbg_data_a = json.loads(dbg_a)
    dbg_data_b = json.loads(dbg_b)

    alice_a_prompt = dbg_data_a["characters"][0]["positive"]
    alice_b_prompt = dbg_data_b["characters"][0]["positive"]
    bob_a_prompt = dbg_data_a["characters"][1]["positive"]
    bob_b_prompt = dbg_data_b["characters"][1]["positive"]

    print(f"  -> Alice Condition A: {alice_a_prompt}")
    print(f"  -> Alice Condition B: {alice_b_prompt}")
    assert "golden blonde hair" in alice_a_prompt
    assert "bright cyan blue hair" in alice_b_prompt
    # Bob and other branches remain completely untouched
    assert bob_a_prompt == bob_b_prompt, "Bob conditioning should remain invariant between Alice variations"
    assert len(cmasks_a) == len(cmasks_b) == 4, f"Expected 4 character masks, got {len(cmasks_a)}"

    results["Test4_Alice_AB"] = {
        "alice_prompt_A": alice_a_prompt,
        "alice_prompt_B": alice_b_prompt,
        "bob_prompt_invariant": (bob_a_prompt == bob_b_prompt),
        "status": "PASS"
    }

    # =========================================================================
    # Test 5: 5-panel Layout Runtime Integration Test
    # =========================================================================
    print("\n[Test 5] 5-Panel Manga Layout Runtime Integration Test...")
    spec4 = get_default_panel_layout_spec(W, H, preset="4_grid")
    spec5 = generic_split_panel(spec4, "p1", "horizontal", 0.5)
    assert len(spec5["panels"]) == 5, f"Expected 5 panels in spec5, got {len(spec5['panels'])}"

    region_spec_5 = {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "panel_count": 5,
        "global_prompt": "manga page, monochrome, action scene, expressive lines, screentone",
        "global_negative_prompt": "bad anatomy, color, photo, realistic, 3d",
        "regions": [
            {"id": 1, "name": "KOMA 1", "enabled": True, "x": 0.05, "y": 0.05, "w": 0.45, "h": 0.22, "prompt": "close-up eyes, intense look", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 2, "name": "KOMA 2", "enabled": True, "x": 0.50, "y": 0.05, "w": 0.45, "h": 0.45, "prompt": "shouting face, dramatic angle", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 3, "name": "KOMA 3", "enabled": True, "x": 0.05, "y": 0.50, "w": 0.45, "h": 0.45, "prompt": "running pose, motion lines", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 4, "name": "KOMA 4", "enabled": True, "x": 0.50, "y": 0.50, "w": 0.45, "h": 0.45, "prompt": "reaching hand, dramatic perspective", "negative_prompt": "", "local_regions": [], "characters": []},
            {"id": 5, "name": "KOMA 5", "enabled": True, "x": 0.05, "y": 0.28, "w": 0.45, "h": 0.22, "prompt": "clenched fist, speed lines", "negative_prompt": "", "local_regions": [], "characters": []}
        ]
    }

    plan_5, _, _, act_count_5 = compiler.compile_page(region_spec=region_spec_5, cast_spec=cast_a)
    assert act_count_5 == 5, f"Expected 5 active KOMA in compile plan, got {act_count_5}"

    pos_5, neg_5, pmasks_5, _, prev_5, dbg_5, _ = cond_builder.build_conditioning(
        clip=mock_clip, page_compile_plan=plan_5, panel_layout_spec=spec5
    )

    dbg_data_5 = json.loads(dbg_5)
    print(f"  -> 5-Panel Mapped Panels: {dbg_data_5['panel_content_map']}")
    self_expected_map = {"1": "p1", "2": "p2", "3": "p3", "4": "p4", "5": "p5"}
    assert dbg_data_5["panel_content_map"] == self_expected_map, f"Expected {self_expected_map}, got {dbg_data_5['panel_content_map']}"
    assert len(pmasks_5) == 5, f"Expected 5 panel masks, got {len(pmasks_5)}"
    assert len(pos_5) == 6, f"Expected 6 positive branches (1 global + 5 panels), got {len(pos_5)}"

    # Save 5-Panel guide image and mask preview
    guide5_pil = render_panel_layout_image(spec5, line_thickness=4)
    guide5_path = os.path.join(OUTPUT_DIR, "guide_5_panel.png")
    guide5_pil.save(guide5_path)
    print(f"  -> Saved 5-panel guide image to {guide5_path}")

    results["Test5_5Panel"] = {
        "panel_count": 5,
        "panel_content_map": dbg_data_5["panel_content_map"],
        "panel_masks_count": len(pmasks_5),
        "conditioning_branches": len(pos_5),
        "guide_image": guide5_path,
        "status": "PASS"
    }

    print("\n" + "=" * 80)
    print(" ALL 5 PHASE 3D GENERATION & INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    summary_file = os.path.join(OUTPUT_DIR, "phase3d_generation_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {summary_file}")


if __name__ == "__main__":
    run_tests()
