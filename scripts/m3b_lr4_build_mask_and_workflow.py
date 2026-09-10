"""Build the bounded M3B-LR4 research mask evidence and API workflow.

The mask is obtained from the existing TegakiMangaRoughGuideBridge implementation.
This helper does not change the bridge, authoring schema, or production workflow.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ComfyUI"))

from custom_nodes.tegaki_manga_nodes.rough_guide_bridge import (  # noqa: E402
    build_rough_guide_plan,
)


LR3_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR3_CLEAN_GUIDE_AB.json"
LR4_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json"
EVIDENCE = ROOT / "docs/manga/verification/m3b_lr4"
INPUT_ROOT = ROOT / "ComfyUI/input"
EXPECTED_GUIDE_SHA = "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a"
EXPECTED_FIGURES = [
    {"figure_id": "figure_1", "instance_id": "inst_1", "x": 0.05, "y": 0.304984, "w": 0.38, "h": 0.369504},
    {"figure_id": "figure_2", "instance_id": "inst_2", "x": 0.57, "y": 0.356304, "w": 0.28, "h": 0.297656},
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_to_mask_image(mask) -> Image.Image:
    array = mask.detach().cpu().numpy()
    if array.ndim != 3 or array.shape[0] != 1:
        raise RuntimeError(f"Unexpected bridge mask shape: {array.shape}")
    values = array[0]
    image = Image.fromarray((values.clip(0.0, 1.0) * 255.0).round().astype("uint8"), mode="L")
    return image


def build_mask(workflow: dict) -> tuple[Image.Image, dict]:
    document = json.loads(workflow["prompt"]["1"]["inputs"]["document_json"])
    result = build_rough_guide_plan(document, page_index=0, input_root=str(INPUT_ROOT))
    if result["status"] != "PASS":
        raise RuntimeError(f"Bridge did not produce PASS: {result['status']}")
    mask_image = tensor_to_mask_image(result["mask"])
    if mask_image.size != (832, 1216):
        raise RuntimeError(f"Unexpected mask dimensions: {mask_image.size}")
    debug = result["debug"]
    if debug.get("figure_count") != 2:
        raise RuntimeError(f"Expected two bridge figures, got {debug.get('figure_count')}")
    return mask_image, debug


def build_lr4_workflow(workflow: dict) -> dict:
    output = copy.deepcopy(workflow)
    output["card"] = "M3B-LR4"
    output["kind"] = "research_api_prompt"
    output["controlnet_selector"] = "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors"
    fixed = output["fixed"]
    fixed.pop("raw_strength", None)
    fixed["control_strength"] = 0.75
    fixed["conditions"] = ["OFF", "CLEAN_GLOBAL", "CLEAN_MASKED"]
    fixed["mask_source"] = "TegakiMangaRoughGuideBridge.figure_union_mask"
    fixed["advanced_apply_node"] = "ACN_AdvancedControlNetApply_v2"
    prompt = output["prompt"]

    global_inputs = {
        "positive": ["3", 0],
        "negative": ["3", 1],
        "control_net": ["5", 0],
        "image": ["8", 0],
        "strength": 0.75,
        "start_percent": 0,
        "end_percent": 1,
    }
    prompt["6"] = {
        "class_type": "ACN_AdvancedControlNetApply_v2",
        "inputs": {**global_inputs},
    }
    prompt["9"] = {
        "class_type": "ACN_AdvancedControlNetApply_v2",
        "inputs": {**global_inputs, "mask_optional": ["4", 1]},
    }

    for node_id in ("11", "14"):
        prompt[node_id]["inputs"]["positive"] = ["6", 0]
        prompt[node_id]["inputs"]["negative"] = ["6", 1]
    for node_id in ("12", "15"):
        prompt[node_id]["inputs"]["positive"] = ["9", 0]
        prompt[node_id]["inputs"]["negative"] = ["9", 1]

    prefixes = {
        "30": "M3B_LR4_SEED_A_OFF",
        "31": "M3B_LR4_SEED_A_GLOBAL",
        "32": "M3B_LR4_SEED_A_MASKED",
        "33": "M3B_LR4_SEED_B_OFF",
        "34": "M3B_LR4_SEED_B_GLOBAL",
        "35": "M3B_LR4_SEED_B_MASKED",
    }
    for node_id, prefix in prefixes.items():
        prompt[node_id]["inputs"]["filename_prefix"] = prefix

    prompt["16"] = {
        "class_type": "MaskToImage",
        "inputs": {"mask": ["4", 1]},
    }
    prompt["17"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["16", 0],
            "filename_prefix": "M3B_LR4_FIGURE_UNION_MASK",
        },
    }
    output["mask_evidence_output"] = "M3B_LR4_FIGURE_UNION_MASK"
    output["clean_guide_input"] = "tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png"
    return output


def main() -> None:
    workflow = json.loads(LR3_WORKFLOW.read_text(encoding="utf-8"))
    guide_path = INPUT_ROOT / "tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png"
    if sha256_file(guide_path) != EXPECTED_GUIDE_SHA:
        raise RuntimeError("LR3 CLEAN Guide SHA256 mismatch")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    mask_image, debug = build_mask(workflow)
    mask_path = EVIDENCE / "M3B_LR4_FIGURE_UNION_MASK.png"
    mask_image.save(mask_path, format="PNG")

    provenance = {
        "card": "M3B-LR4",
        "source": "TegakiMangaRoughGuideBridge.figure_union_mask",
        "source_workflow": "workflows/manga/research/M3B_LR3_CLEAN_GUIDE_AB.json",
        "document_id": json.loads(workflow["prompt"]["1"]["inputs"]["document_json"])["document_id"],
        "canvas_dimensions": {"width": 832, "height": 1216},
        "mask_dimensions": {"width": mask_image.width, "height": mask_image.height},
        "mask_semantics": "bridge MASK tensor values are normalized 1.0 inside the existing Figure union rectangles and 0.0 outside; consumed as Advanced-ControlNet effect_mask where 1.0 is active and 0.0 is inactive",
        "orientation": {"active_value": 1.0, "inactive_value": 0.0},
        "transformations": [],
        "figures": EXPECTED_FIGURES,
        "bridge_debug": debug,
        "mask_sha256": sha256_file(mask_path),
        "mask_file": "docs/manga/verification/m3b_lr4/M3B_LR4_FIGURE_UNION_MASK.png",
        "clean_guide_sha256": EXPECTED_GUIDE_SHA,
        "schema_changed": False,
        "manual_drawing": False,
    }
    (EVIDENCE / "M3B_LR4_MASK_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    LR4_WORKFLOW.write_text(
        json.dumps(build_lr4_workflow(workflow), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"mask": str(mask_path), "mask_sha256": provenance["mask_sha256"], "workflow": str(LR4_WORKFLOW)}, indent=2))


if __name__ == "__main__":
    main()
