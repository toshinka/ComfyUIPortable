"""Build the bounded M3B-LR7 CAST_GLOBAL research workflow and provenance."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ComfyUI"))

from custom_nodes.tegaki_manga_nodes.conditioning_builder import (  # noqa: E402
    TegakiMangaConditioningBuilder,
)
from custom_nodes.tegaki_manga_nodes.minimum_hand_scene_editor import (  # noqa: E402
    TegakiMinimumHandSceneEditor,
)

SOURCE_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json"
TARGET_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json"
EVIDENCE_DIR = ROOT / "docs/manga/verification/m3b_lr7"
PROVENANCE_FILE = EVIDENCE_DIR / "M3B_LR7_RUNTIME_PROVENANCE.json"

EXPECTED_CLEAN_GUIDE_SHA = "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a"
EXPECTED_CONTROLNET_SHA = "e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8"


class StubClip:
    def tokenize(self, text: str) -> dict[str, str]:
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens: dict[str, str]) -> list[list[Any]]:
        import torch

        embedding = torch.zeros((1, 1, 1), dtype=torch.float32)
        return [[embedding, {"stub_text": tokens["text"]}]]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def verify_cast_runtime(document: dict[str, Any]) -> dict[str, Any]:
    scene = document["pages"][0]["scenes"][0]
    if scene.get("input_mode") != "cast":
        raise AssertionError(f"Expected scene input_mode='cast', got {scene.get('input_mode')!r}")

    document_json = json.dumps(document, ensure_ascii=False)
    editor_result = TegakiMinimumHandSceneEditor().edit_and_compile(
        document_json=document_json,
        seed=42,
        style_template="Manga Monochrome",
        resolution="Portrait 832x1216",
    )
    plan = editor_result[0]
    panel = plan["panels"][0]
    characters = panel["characters"]
    expected_provenance = [("inst_1", "cast_1"), ("inst_2", "cast_2")]
    actual_provenance = [(c.get("instance_id"), c.get("character_id")) for c in characters]
    if len(characters) != 2 or actual_provenance != expected_provenance:
        raise AssertionError(f"CAST compile failed: {actual_provenance} vs {expected_provenance}")

    builder_result = TegakiMangaConditioningBuilder().build_conditioning(
        clip=StubClip(),
        page_compile_plan=plan,
        panel_strength=1.0,
        character_strength=1.0,
        set_cond_area="default",
        local_region_strength=1.0,
        mask_feather=0,
    )
    character_masks = builder_result[3]
    conditioning_debug = json.loads(builder_result[4])
    character_entries = conditioning_debug["entries"]["characters"]
    if int(character_masks.shape[0]) != 2 or len(character_entries) != 2:
        raise AssertionError(
            f"Character conditioning failed: masks={character_masks.shape[0]}, entries={len(character_entries)}"
        )

    return {
        "status": "PASS",
        "input_mode": "cast",
        "compiled_characters_count": len(characters),
        "compiled_characters": characters,
        "character_conditioning_entries_count": len(character_entries),
        "character_conditioning_entries": character_entries,
        "character_masks_count": int(character_masks.shape[0]),
    }


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify clean guide exists & matches expected hash
    guide_path = ROOT / "ComfyUI/input/tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png"
    if not guide_path.exists():
        guide_path = ROOT / "docs/manga/verification/m3b_lr3/M3B_LR3_CLEAN_GUIDE.png"
    actual_guide_sha = sha256_file(guide_path)
    if actual_guide_sha != EXPECTED_CLEAN_GUIDE_SHA:
        raise AssertionError(f"CLEAN Guide hash mismatch: {actual_guide_sha}")

    # 2. Verify ControlNet model exists & matches expected hash
    cn_path = Path("E:/EasyReforge/Model/ControlNet/CN-anytest_v4/CN-anytest4_illustrious2_A.safetensors")
    if not cn_path.exists():
        raise AssertionError(f"ControlNet model not found at {cn_path}")
    actual_cn_sha = sha256_file(cn_path)
    if actual_cn_sha != EXPECTED_CONTROLNET_SHA:
        raise AssertionError(f"ControlNet model hash mismatch: {actual_cn_sha}")

    # 3. Load LR5 source workflow
    raw_source = json.loads(SOURCE_WORKFLOW.read_text(encoding="utf-8"))
    source_prompt = raw_source["prompt"]
    doc = json.loads(source_prompt["1"]["inputs"]["document_json"])

    # 4. Verify CAST runtime provenance
    runtime_proof = verify_cast_runtime(doc)

    # 5. Build CAST_GLOBAL workflow
    # Node 6 in LR5 was ACN_AdvancedControlNetApply_v2 with mask_optional: ["4", 1]
    # In LR7, node 6 removes mask_optional completely (UNCONNECTED)
    node_6 = copy.deepcopy(source_prompt["6"])
    if "mask_optional" in node_6["inputs"]:
        del node_6["inputs"]["mask_optional"]

    # Verify invariants on node 6
    if node_6["class_type"] != "ACN_AdvancedControlNetApply_v2":
        raise AssertionError(f"Unexpected class_type for node 6: {node_6['class_type']}")
    if node_6["inputs"]["positive"] != ["3", 0] or node_6["inputs"]["negative"] != ["3", 1]:
        raise AssertionError(f"Node 6 inputs not connected to CAST ConditioningBuilder: {node_6['inputs']}")
    if node_6["inputs"]["control_net"] != ["5", 0]:
        raise AssertionError(f"Node 6 not connected to ControlNetLoader: {node_6['inputs']}")
    if node_6["inputs"]["image"] != ["8", 0]:
        raise AssertionError(f"Node 6 not connected to LoadImage: {node_6['inputs']}")
    if float(node_6["inputs"]["strength"]) != 0.75:
        raise AssertionError(f"Node 6 strength is not 0.75: {node_6['inputs']['strength']}")
    if float(node_6["inputs"]["start_percent"]) != 0.0 or float(node_6["inputs"]["end_percent"]) != 1.0:
        raise AssertionError(f"Node 6 start/end mismatch: {node_6['inputs']}")
    if "mask_optional" in node_6["inputs"]:
        raise AssertionError("Node 6 still has mask_optional connected!")

    # Samplers for CAST_GLOBAL: Seed 42 and Seed 77
    node_11 = copy.deepcopy(source_prompt["11"])  # seed 42, connected to ["6", 0]
    node_11["inputs"]["positive"] = ["6", 0]
    node_11["inputs"]["negative"] = ["6", 1]
    node_11["inputs"]["seed"] = 42

    node_14 = copy.deepcopy(source_prompt["14"])  # seed 77, connected to ["6", 0]
    node_14["inputs"]["positive"] = ["6", 0]
    node_14["inputs"]["negative"] = ["6", 1]
    node_14["inputs"]["seed"] = 77

    node_21 = copy.deepcopy(source_prompt["21"])  # VAE decode for 11
    node_21["inputs"]["samples"] = ["11", 0]

    node_24 = copy.deepcopy(source_prompt["24"])  # VAE decode for 14
    node_24["inputs"]["samples"] = ["14", 0]

    node_31 = copy.deepcopy(source_prompt["31"])  # SaveImage for 21
    node_31["inputs"]["images"] = ["21", 0]
    node_31["inputs"]["filename_prefix"] = "M3B_LR7_SEED_A_CAST_GLOBAL"

    node_34 = copy.deepcopy(source_prompt["34"])  # SaveImage for 24
    node_34["inputs"]["images"] = ["24", 0]
    node_34["inputs"]["filename_prefix"] = "M3B_LR7_SEED_B_CAST_GLOBAL"

    keep_nodes = {
        "1": source_prompt["1"],
        "2": source_prompt["2"],
        "3": source_prompt["3"],
        "5": source_prompt["5"],
        "6": node_6,
        "7": source_prompt["7"],
        "8": source_prompt["8"],
        "11": node_11,
        "14": node_14,
        "21": node_21,
        "24": node_24,
        "31": node_31,
        "34": node_34,
    }

    lr7_workflow = {
        "card": "M3B-LR7",
        "kind": "research_api_prompt",
        "source_workflow": str(SOURCE_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "model": "CN-anytest4_illustrious2_A.safetensors",
        "controlnet_selector": "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
        "fixed": {
            "checkpoint": source_prompt["2"]["inputs"]["ckpt_name"],
            "resolution": [832, 1216],
            "steps": 20,
            "cfg": 7.0,
            "sampler": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "character_strength": 1.0,
            "panel_strength": 1.0,
            "local_region_strength": 1.0,
            "character_mask_feather": 0,
            "control_strength": 0.75,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "seeds": [42, 77],
            "condition": "CAST_GLOBAL",
            "mask_optional": "UNCONNECTED",
            "advanced_apply_node": "ACN_AdvancedControlNetApply_v2",
        },
        "prompt": keep_nodes,
        "m3b_lr7": {
            "card": "M3B-LR7",
            "condition": "CAST_GLOBAL",
            "seeds": [42, 77],
            "cast_global_positive_negative": ["6", 0],
            "control_strength": 0.75,
            "control_start": 0.0,
            "control_end": 1.0,
            "mask_optional": "UNCONNECTED",
            "clean_guide_sha256": EXPECTED_CLEAN_GUIDE_SHA,
            "controlnet_sha256": EXPECTED_CONTROLNET_SHA,
            "outputs": [
                {"seed": 42, "node": "31", "prefix": "M3B_LR7_SEED_A_CAST_GLOBAL"},
                {"seed": 77, "node": "34", "prefix": "M3B_LR7_SEED_B_CAST_GLOBAL"},
            ],
        },
    }

    TARGET_WORKFLOW.write_text(
        json.dumps(lr7_workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Written: {TARGET_WORKFLOW}")

    # 6. Save runtime provenance
    provenance = {
        "card": "M3B-LR7",
        "source_workflow": str(SOURCE_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "target_workflow": str(TARGET_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "input_mode": runtime_proof["input_mode"],
        "compiled_characters_count": runtime_proof["compiled_characters_count"],
        "compiled_characters": runtime_proof["compiled_characters"],
        "character_conditioning_entries_count": runtime_proof["character_conditioning_entries_count"],
        "character_conditioning_entries": runtime_proof["character_conditioning_entries"],
        "character_masks_count": runtime_proof["character_masks_count"],
        "clean_guide": {
            "path": "tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png",
            "sha256": actual_guide_sha,
            "verified": True,
        },
        "controlnet_model": {
            "selector": "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
            "path": "E:/EasyReforge/Model/ControlNet/CN-anytest_v4/CN-anytest4_illustrious2_A.safetensors",
            "sha256": actual_cn_sha,
            "verified": True,
        },
        "cast_global_graph": {
            "apply_node": "6",
            "class_type": "ACN_AdvancedControlNetApply_v2",
            "positive": ["3", 0],
            "negative": ["3", 1],
            "control_net": ["5", 0],
            "image": ["8", 0],
            "strength": 0.75,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "mask_optional": "UNCONNECTED",
            "mask_optional_present_in_inputs": False,
        },
        "seeds": [42, 77],
        "outputs": [
            {
                "seed": 42,
                "sampler_node": "11",
                "save_node": "31",
                "prefix": "M3B_LR7_SEED_A_CAST_GLOBAL",
                "expected_file": "SEED_A_CAST_GLOBAL.png",
            },
            {
                "seed": 77,
                "sampler_node": "14",
                "save_node": "34",
                "prefix": "M3B_LR7_SEED_B_CAST_GLOBAL",
                "expected_file": "SEED_B_CAST_GLOBAL.png",
            },
        ],
        "schema_changed": False,
        "production_workflow_modified": False,
        "comparator": {
            "primary": "existing LR5 CAST_HARD",
            "historical_off_a": "docs/manga/verification/m3b_lr6/SEED_A_CAST_OFF.png",
            "historical_hard_a": "docs/manga/verification/m3b_lr6/SEED_A_CAST_HARD.png",
            "historical_off_b": "docs/manga/verification/m3b_lr6/SEED_B_CAST_OFF.png",
            "historical_hard_b": "docs/manga/verification/m3b_lr6/SEED_B_CAST_HARD.png",
        },
    }

    PROVENANCE_FILE.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Written: {PROVENANCE_FILE}")


if __name__ == "__main__":
    main()
