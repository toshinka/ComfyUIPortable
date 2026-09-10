"""Execute the M3B-LR7 CAST_GLOBAL research generation and canonical regression."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ComfyUI"))

from scripts import comfy_runtime_helper  # noqa: E402

WORKFLOW_FILE = ROOT / "workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json"
CANONICAL_FILE = ROOT / "workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json"
OUTPUT_DIRS = [ROOT / "ComfyUI/output", ROOT / "output"]
EVIDENCE_DIR = ROOT / "docs/manga/verification/m3b_lr7"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def find_latest_output_matching(prefix: str) -> Path:
    candidates: list[Path] = []
    for d in OUTPUT_DIRS:
        if d.exists():
            candidates.extend(d.glob(f"{prefix}_*.png"))
    if not candidates:
        raise FileNotFoundError(f"No output found matching prefix {prefix!r} in {OUTPUT_DIRS}")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def build_canonical_prompt() -> dict[str, Any]:
    wf = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
    editor_node = next(n for n in wf["nodes"] if n["type"] == "TegakiMinimumHandSceneEditor")
    doc_json = editor_node["widgets_values"][0]

    return {
        "1": {
            "class_type": "TegakiMinimumHandSceneEditor",
            "inputs": {
                "document_json": doc_json,
                "seed": 42,
                "style_template": "Manga Monochrome",
                "resolution": "Portrait 832x1216",
            },
        },
        "2": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors",
            },
        },
        "3": {
            "class_type": "TegakiMangaConditioningBuilder",
            "inputs": {
                "clip": ["2", 1],
                "page_compile_plan": ["1", 0],
                "panel_strength": 1.0,
                "character_strength": 1.0,
                "set_cond_area": "default",
                "local_region_strength": 1.0,
                "mask_feather": 0,
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["3", 1],
                "latent_image": ["4", 0],
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["2", 2],
            },
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "M3B_LR7_CANONICAL_NO_GUIDE",
            },
        },
    }


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    print("[LR7 Execute] Ensuring ComfyUI server is running...")
    comfy_runtime_helper.ensure_server(timeout=90)

    # Check if CAST_GLOBAL outputs already exist
    seed_a_dst = EVIDENCE_DIR / "SEED_A_CAST_GLOBAL.png"
    seed_b_dst = EVIDENCE_DIR / "SEED_B_CAST_GLOBAL.png"

    prompt_id = "7d705115-f499-4ca0-9c4d-a76037d57dda"
    try:
        seed_a_src = find_latest_output_matching("M3B_LR7_SEED_A_CAST_GLOBAL")
        seed_b_src = find_latest_output_matching("M3B_LR7_SEED_B_CAST_GLOBAL")
        print(f"[LR7 Execute] Found existing outputs from prompt {prompt_id}:")
        print(f"  {seed_a_src}")
        print(f"  {seed_b_src}")
    except FileNotFoundError:
        print(f"[LR7 Execute] Loading research workflow: {WORKFLOW_FILE}")
        wf_data = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
        prompt = wf_data["prompt"]

        print("[LR7 Execute] Queueing CAST_GLOBAL prompt...")
        res = comfy_runtime_helper.queue_prompt(prompt)
        prompt_id = res["prompt_id"]
        print(f"[LR7 Execute] CAST_GLOBAL queued with prompt_id: {prompt_id}")

        print(f"[LR7 Execute] Waiting for completion (timeout 300s)...")
        history = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=300)
        print(f"[LR7 Execute] CAST_GLOBAL finished successfully!")

        seed_a_src = find_latest_output_matching("M3B_LR7_SEED_A_CAST_GLOBAL")
        seed_b_src = find_latest_output_matching("M3B_LR7_SEED_B_CAST_GLOBAL")

    shutil.copyfile(seed_a_src, seed_a_dst)
    shutil.copyfile(seed_b_src, seed_b_dst)

    sha_a = sha256_file(seed_a_dst)
    sha_b = sha256_file(seed_b_dst)
    print(f"[LR7 Evidence] SEED_A_CAST_GLOBAL: {seed_a_dst} (SHA256: {sha_a})")
    print(f"[LR7 Evidence] SEED_B_CAST_GLOBAL: {seed_b_dst} (SHA256: {sha_b})")

    # 2. Queue canonical no-Guide regression
    print("[LR7 Execute] Queueing canonical no-Guide prompt...")
    canon_prompt = build_canonical_prompt()
    c_res = comfy_runtime_helper.queue_prompt(canon_prompt)
    c_prompt_id = c_res["prompt_id"]
    print(f"[LR7 Execute] Canonical queued with prompt_id: {c_prompt_id}")

    print(f"[LR7 Execute] Waiting for canonical completion (timeout 300s)...")
    c_history = comfy_runtime_helper.wait_for_prompt(c_prompt_id, timeout=300)
    print(f"[LR7 Execute] Canonical finished successfully!")

    canon_src = find_latest_output_matching("M3B_LR7_CANONICAL_NO_GUIDE")
    canon_dst = EVIDENCE_DIR / "CANONICAL_NO_GUIDE.png"
    shutil.copyfile(canon_src, canon_dst)
    sha_canon = sha256_file(canon_dst)
    print(f"[LR7 Evidence] CANONICAL_NO_GUIDE: {canon_dst} (SHA256: {sha_canon})")

    results = {
        "status": "PASS",
        "cast_global": {
            "prompt_id": prompt_id,
            "seed_42": {
                "file": "SEED_A_CAST_GLOBAL.png",
                "sha256": sha_a,
                "dimensions": "832x1216",
            },
            "seed_77": {
                "file": "SEED_B_CAST_GLOBAL.png",
                "sha256": sha_b,
                "dimensions": "832x1216",
            },
        },
        "canonical_no_guide": {
            "prompt_id": c_prompt_id,
            "file": "CANONICAL_NO_GUIDE.png",
            "sha256": sha_canon,
            "dimensions": "832x1216",
        },
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
