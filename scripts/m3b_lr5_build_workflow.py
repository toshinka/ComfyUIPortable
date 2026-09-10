"""Build the bounded M3B-LR5 CAST_OFF vs CAST_MASKED research workflow."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json"
TARGET = ROOT / "workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json"


def main() -> None:
    workflow = json.loads(SOURCE.read_text(encoding="utf-8"))
    prompt: dict[str, Any] = workflow["prompt"]
    source_doc = json.loads(prompt["1"]["inputs"]["document_json"])
    cast_doc = copy.deepcopy(source_doc)
    scenes = cast_doc["pages"][0]["scenes"]
    changed_paths: list[str] = []
    for index, scene in enumerate(scenes):
        if scene.get("input_mode") != "simple":
            raise AssertionError(
                f"Expected source scene {index} to be simple, got {scene.get('input_mode')!r}"
            )
        scene["input_mode"] = "cast"
        changed_paths.append(f"pages[0].scenes[{index}].input_mode")
    reverted = copy.deepcopy(cast_doc)
    for scene in reverted["pages"][0]["scenes"]:
        scene["input_mode"] = "simple"
    if reverted != source_doc:
        raise AssertionError("Document diff is broader than the input_mode change")

    prompt["1"]["inputs"]["document_json"] = json.dumps(
        cast_doc, ensure_ascii=False, separators=(",", ":")
    )

    # The existing LR4 masked apply is repurposed as the single LR5 masked
    # branch. CAST_OFF bypasses ControlNet by using node 3 directly.
    prompt["6"]["inputs"]["mask_optional"] = ["4", 1]

    keep_nodes = {"1", "2", "3", "4", "5", "6", "7", "8", "10", "11", "13", "14", "20", "21", "23", "24", "30", "31", "33", "34"}
    workflow["prompt"] = {node_id: node for node_id, node in prompt.items() if node_id in keep_nodes}

    workflow["prompt"]["30"]["inputs"]["filename_prefix"] = "M3B_LR5_SEED_A_CAST_OFF"
    workflow["prompt"]["31"]["inputs"]["filename_prefix"] = "M3B_LR5_SEED_A_CAST_MASKED"
    workflow["prompt"]["33"]["inputs"]["filename_prefix"] = "M3B_LR5_SEED_B_CAST_OFF"
    workflow["prompt"]["34"]["inputs"]["filename_prefix"] = "M3B_LR5_SEED_B_CAST_MASKED"

    # Keep the workflow wrapper stable while documenting its exact research
    # transformation for later manifest inspection.
    workflow["m3b_lr5"] = {
        "card": "M3B-LR5",
        "source_workflow": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "changed_document_paths": changed_paths,
        "conditions": ["CAST_OFF", "CAST_MASKED"],
        "seeds": [42, 77],
        "cast_off_positive_negative": ["3", 0],
        "cast_masked_positive_negative": ["6", 0],
        "control_strength": 0.75,
        "control_start": 0.0,
        "control_end": 1.0,
        "mask_input": ["4", 1],
        "character_specific_controlnet": False,
    }
    TARGET.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
