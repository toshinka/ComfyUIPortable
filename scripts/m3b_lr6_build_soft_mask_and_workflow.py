"""Build the bounded M3B-LR6 radius-16 Figure-mask research slice.

The helper reuses the existing LR4/LR5 binary Figure-union mask and the
existing Manga ``_apply_feather`` implementation. It writes research
evidence and a non-production API workflow only; it does not modify the
authoring document, production workflow, or any model storage.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ComfyUI"))

from custom_nodes.tegaki_manga_nodes.mask_builder import _apply_feather  # noqa: E402
from custom_nodes.tegaki_manga_nodes.rough_guide_bridge import (  # noqa: E402
    build_rough_guide_plan,
)


LR5_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json"
TARGET_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR6_CAST_SOFT_MASK_COMPATIBILITY.json"
HARD_SOURCE = ROOT / "docs/manga/verification/m3b_lr4/M3B_LR4_FIGURE_UNION_MASK.png"
EVIDENCE = ROOT / "docs/manga/verification/m3b_lr6"
HARD_EVIDENCE = EVIDENCE / "M3B_LR6_HARD_MASK.png"
SOFT_EVIDENCE = EVIDENCE / "M3B_LR6_SOFT_MASK.png"
PROVENANCE = EVIDENCE / "M3B_LR6_MASK_PROVENANCE.json"
INPUT_ROOT = ROOT / "ComfyUI/input"
STAGED_SOFT = INPUT_ROOT / "M3B_LR6_SOFT_MASK.png"

EXPECTED_HARD_SHA = "6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdc b45688d2da6fb".replace(" ", "")
EXPECTED_GUIDE_SHA = "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a"
EXPECTED_SIZE = (832, 1216)
RADIUS = 16
FIGURES = [
    {"figure_id": "figure_1", "instance_id": "inst_1", "x": 0.05, "y": 0.304984, "w": 0.38, "h": 0.369504},
    {"figure_id": "figure_2", "instance_id": "inst_2", "x": 0.57, "y": 0.356304, "w": 0.28, "h": 0.297656},
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_gray(path: Path) -> np.ndarray:
    image = Image.open(path).convert("L")
    if image.size != EXPECTED_SIZE:
        raise RuntimeError(f"Unexpected mask dimensions for {path}: {image.size}")
    return np.asarray(image, dtype=np.uint8)


def save_if_same_or_absent(source: Path, target: Path, expected_sha: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if sha256_file(target) != expected_sha:
            raise RuntimeError(f"Refusing to overwrite mismatched evidence/input file: {target}")
        return
    shutil.copyfile(source, target)


def weighted_center(values: np.ndarray, figure: dict[str, Any]) -> tuple[float, float]:
    height, width = values.shape
    x0 = max(0, int(np.floor(float(figure["x"]) * width)))
    y0 = max(0, int(np.floor(float(figure["y"]) * height)))
    x1 = min(width, int(np.ceil((float(figure["x"]) + float(figure["w"])) * width)))
    y1 = min(height, int(np.ceil((float(figure["y"]) + float(figure["h"])) * height)))
    crop = values[y0:y1, x0:x1]
    yy, xx = np.indices(crop.shape, dtype=np.float64)
    total = float(crop.sum())
    if total <= 0:
        raise RuntimeError(f"No active mask weight for {figure['figure_id']}")
    return (float((xx * crop).sum() / total + x0), float((yy * crop).sum() / total + y0))


def bridge_mask_sha(workflow: dict[str, Any]) -> str:
    document = json.loads(workflow["prompt"]["1"]["inputs"]["document_json"])
    result = build_rough_guide_plan(
        document,
        page_index=0,
        input_root=str(INPUT_ROOT),
    )
    if result.get("status") != "PASS":
        raise RuntimeError(f"Figure-union bridge did not PASS: {result.get('status')}")
    bridge_mask = result["mask"].detach().cpu().numpy()
    if bridge_mask.shape != (1, EXPECTED_SIZE[1], EXPECTED_SIZE[0]):
        raise RuntimeError(f"Unexpected bridge mask shape: {bridge_mask.shape}")
    bridge_image = Image.fromarray(
        np.rint(np.clip(bridge_mask[0], 0.0, 1.0) * 255.0).astype(np.uint8),
        mode="L",
    )
    bridge_path = EVIDENCE / "_bridge_hard_mask_check.png"
    bridge_image.save(bridge_path, format="PNG")
    try:
        return sha256_file(bridge_path)
    finally:
        bridge_path.unlink()


def build_workflow(source: dict[str, Any]) -> dict[str, Any]:
    workflow = copy.deepcopy(source)
    workflow["card"] = "M3B-LR6"
    workflow["fixed"]["conditions"] = ["CAST_OFF", "CAST_HARD", "CAST_SOFT"]
    workflow["fixed"]["mask_source"] = "HARD bridge Figure-union mask -> SOFT LoadImageMask"
    workflow["fixed"]["soft_mask_gaussian_radius_px"] = RADIUS
    workflow["mask_evidence_output"] = "M3B_LR6_HARD_MASK / M3B_LR6_SOFT_MASK"
    workflow["clean_guide_input"] = "tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png"

    prompt = workflow["prompt"]
    prompt["9"] = {
        "class_type": "ACN_AdvancedControlNetApply_v2",
        "inputs": {
            "positive": ["3", 0],
            "negative": ["3", 1],
            "control_net": ["5", 0],
            "image": ["8", 0],
            "strength": 0.75,
            "start_percent": 0,
            "end_percent": 1,
            "mask_optional": ["40", 0],
        },
    }
    prompt["40"] = {
        "class_type": "LoadImageMask",
        "inputs": {"image": "M3B_LR6_SOFT_MASK.png", "channel": "red"},
    }

    def sampler(source_id: str, positive: list[Any], seed: int) -> dict[str, Any]:
        node = copy.deepcopy(prompt[source_id])
        node["inputs"]["positive"] = positive
        node["inputs"]["negative"] = [positive[0], 1]
        node["inputs"]["seed"] = seed
        return node

    prompt["12"] = sampler("10", ["9", 0], 42)
    prompt["15"] = sampler("13", ["9", 0], 77)
    prompt["22"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["12", 0], "vae": ["2", 2]},
    }
    prompt["25"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["15", 0], "vae": ["2", 2]},
    }

    prefixes = {
        "30": "M3B_LR6_SEED_A_CAST_OFF",
        "31": "M3B_LR6_SEED_A_CAST_HARD",
        "32": "M3B_LR6_SEED_A_CAST_SOFT",
        "33": "M3B_LR6_SEED_B_CAST_OFF",
        "34": "M3B_LR6_SEED_B_CAST_HARD",
        "35": "M3B_LR6_SEED_B_CAST_SOFT",
    }
    prompt["32"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["22", 0], "filename_prefix": prefixes["32"]},
    }
    prompt["35"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["25", 0], "filename_prefix": prefixes["35"]},
    }
    for node_id, prefix in prefixes.items():
        prompt[node_id]["inputs"]["filename_prefix"] = prefix

    workflow.pop("m3b_lr5", None)
    workflow["m3b_lr6"] = {
        "card": "M3B-LR6",
        "source_workflow": "workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json",
        "conditions": ["CAST_OFF", "CAST_HARD", "CAST_SOFT"],
        "seeds": [42, 77],
        "hard_effect_mask": {
            "source": "TegakiMangaRoughGuideBridge.figure_union_mask",
            "node": ["6", "mask_optional", ["4", 1]],
            "sha256": EXPECTED_HARD_SHA,
        },
        "soft_effect_mask": {
            "source": "M3B_LR6_SOFT_MASK.png",
            "load_node": "40",
            "node": ["9", "mask_optional", ["40", 0]],
            "gaussian_radius_px": RADIUS,
        },
        "cast_off_positive_negative": ["3", 0],
        "cast_hard_positive_negative": ["6", 0],
        "cast_soft_positive_negative": ["9", 0],
        "control_strength": 0.75,
        "control_start": 0.0,
        "control_end": 1.0,
        "character_specific_controlnet": False,
        "schema_changed": False,
    }
    return workflow


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    hard = load_gray(HARD_SOURCE)
    source_sha = sha256_file(HARD_SOURCE)
    if source_sha != EXPECTED_HARD_SHA:
        raise RuntimeError(f"HARD mask SHA mismatch: {source_sha}")
    unique = set(np.unique(hard).tolist())
    if unique != {0, 255}:
        raise RuntimeError(f"HARD mask is not binary: values={sorted(unique)}")

    source_workflow = json.loads(LR5_WORKFLOW.read_text(encoding="utf-8"))
    if sha256_file(ROOT / "docs/manga/verification/m3b_lr3/M3B_LR3_CLEAN_GUIDE.png") != EXPECTED_GUIDE_SHA:
        raise RuntimeError("CLEAN Guide SHA mismatch")
    bridge_sha = bridge_mask_sha(source_workflow)
    if bridge_sha != EXPECTED_HARD_SHA:
        raise RuntimeError(f"Runtime Figure-union bridge does not reproduce HARD mask: {bridge_sha}")

    hard_tensor = torch.from_numpy(hard.astype(np.float32) / 255.0).unsqueeze(0)
    soft_tensor = _apply_feather(hard_tensor, RADIUS)
    soft_values = soft_tensor[0].detach().cpu().numpy()
    soft_values = np.clip(soft_values, 0.0, 1.0)
    soft = np.rint(soft_values * 255.0).astype(np.uint8)
    Image.fromarray(soft, mode="L").save(SOFT_EVIDENCE, format="PNG")
    save_if_same_or_absent(HARD_SOURCE, HARD_EVIDENCE, EXPECTED_HARD_SHA)
    soft_sha = sha256_file(SOFT_EVIDENCE)
    save_if_same_or_absent(SOFT_EVIDENCE, STAGED_SOFT, soft_sha)

    hard_centers = {f["figure_id"]: weighted_center(hard.astype(np.float64) / 255.0, f) for f in FIGURES}
    soft_centers = {f["figure_id"]: weighted_center(soft_values, f) for f in FIGURES}
    center_deltas = {
        figure_id: {
            "hard": [round(value, 4) for value in hard_centers[figure_id]],
            "soft": [round(value, 4) for value in soft_centers[figure_id]],
            "delta_px": round(float(np.linalg.norm(np.subtract(soft_centers[figure_id], hard_centers[figure_id]))), 6),
        }
        for figure_id in hard_centers
    }
    if any(item["delta_px"] > 1.0 for item in center_deltas.values()):
        raise RuntimeError(f"SOFT mask changed Figure centers: {center_deltas}")

    intermediate = int(np.count_nonzero((soft_values > 0.0) & (soft_values < 1.0)))
    numeric = {
        "dimensions": {"width": int(soft.shape[1]), "height": int(soft.shape[0])},
        "min": float(soft_values.min()),
        "max": float(soft_values.max()),
        "count_value_0": int(np.count_nonzero(soft_values == 0.0)),
        "count_value_1": int(np.count_nonzero(soft_values == 1.0)),
        "count_intermediate_0_lt_value_lt_1": intermediate,
    }
    if numeric["dimensions"] != {"width": 832, "height": 1216} or intermediate <= 0:
        raise RuntimeError(f"SOFT mask numeric contract failed: {numeric}")
    if soft_sha == EXPECTED_HARD_SHA:
        raise RuntimeError("SOFT mask is byte-identical to HARD mask")

    workflow = build_workflow(source_workflow)
    TARGET_WORKFLOW.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance = {
        "card": "M3B-LR6",
        "source_hard_mask": str(HARD_SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "hard_mask_evidence": str(HARD_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "soft_mask_evidence": str(SOFT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "hard_sha256": EXPECTED_HARD_SHA,
        "soft_sha256": soft_sha,
        "bridge_reproduction_sha256": bridge_sha,
        "dimensions": {"width": 832, "height": 1216},
        "hard_values": [0.0, 1.0],
        "soft_mask_gaussian_radius_px": RADIUS,
        "numeric": numeric,
        "figure_centers": center_deltas,
        "manual_drawing": False,
        "schema_changed": False,
        "page_guides_persisted": False,
        "character_masks_feathered": False,
        "runtime_input_stage": str(STAGED_SOFT.relative_to(ROOT)).replace("\\", "/"),
        "workflow": str(TARGET_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "mask_optional_provenance": {
            "cast_hard": {"apply_node": "6", "mask_optional": ["4", 1], "source": "bridge Figure-union mask"},
            "cast_soft": {"apply_node": "9", "mask_optional": ["40", 0], "source": "LoadImageMask M3B_LR6_SOFT_MASK.png"},
        },
    }
    PROVENANCE.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "hard_sha256": EXPECTED_HARD_SHA, "soft_sha256": soft_sha, "numeric": numeric, "figure_centers": center_deltas, "workflow": str(TARGET_WORKFLOW), "provenance": str(PROVENANCE)}, indent=2))


if __name__ == "__main__":
    main()
