"""M3B-LR5 CAST compiler and character-conditioning contract probe.

This is a research-only verifier. It executes the existing Manga authoring
editor/compiler and conditioning builder without changing production code.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import torch

from custom_nodes.tegaki_manga_nodes.conditioning_builder import (
    TegakiMangaConditioningBuilder,
)
from custom_nodes.tegaki_manga_nodes.minimum_hand_scene_editor import (
    TegakiMinimumHandSceneEditor,
)


ROOT = Path(__file__).resolve().parents[1]
LR4_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json"


class StubClip:
    """Minimal CLIP surface for exercising the existing builder branch."""

    def tokenize(self, text: str) -> dict[str, str]:
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens: dict[str, str]) -> list[list[Any]]:
        embedding = torch.zeros((1, 1, 1), dtype=torch.float32)
        return [[embedding, {"stub_text": tokens["text"]}]]


def load_lr4_document() -> dict[str, Any]:
    workflow = json.loads(LR4_WORKFLOW.read_text(encoding="utf-8"))
    return json.loads(workflow["prompt"]["1"]["inputs"]["document_json"])


def make_cast_research_document() -> tuple[dict[str, Any], list[str]]:
    source = load_lr4_document()
    research = copy.deepcopy(source)
    scenes = research["pages"][0]["scenes"]
    changed_paths: list[str] = []
    for index, scene in enumerate(scenes):
        if scene.get("input_mode") != "simple":
            raise AssertionError(
                f"Expected LR4 source scene {index} to be simple, got {scene.get('input_mode')!r}"
            )
        scene["input_mode"] = "cast"
        changed_paths.append(f"pages[0].scenes[{index}].input_mode")
    return research, changed_paths


def main() -> None:
    source = load_lr4_document()
    research, changed_paths = make_cast_research_document()
    source_for_diff = copy.deepcopy(source)
    research_for_diff = copy.deepcopy(research)
    # The fixture has one scene. Compare recursively after reverting only the
    # deliberately changed semantic field.
    reverted = copy.deepcopy(research_for_diff)
    for scene in reverted["pages"][0]["scenes"]:
        scene["input_mode"] = "simple"
    if reverted != source_for_diff:
        raise AssertionError("CAST research document changed fields beyond input_mode")

    document_json = json.dumps(research, ensure_ascii=False)
    editor_result = TegakiMinimumHandSceneEditor().edit_and_compile(
        document_json=document_json,
        seed=42,
        style_template="Manga Monochrome",
        resolution="Portrait 832x1216",
    )
    plan = editor_result[0]
    debug = json.loads(editor_result[5])
    panel = plan["panels"][0]
    characters = panel["characters"]
    expected_provenance = [
        ("inst_1", "cast_1"),
        ("inst_2", "cast_2"),
    ]
    actual_provenance = [(c.get("instance_id"), c.get("character_id")) for c in characters]
    if len(characters) != 2 or actual_provenance != expected_provenance:
        raise AssertionError(
            f"CAST compile gate failed: count={len(characters)} provenance={actual_provenance}"
        )
    required_fields = {
        "instance_id",
        "character_id",
        "combined_prompt",
        "area",
        "coordinate_space",
    }
    for character in characters:
        missing = sorted(required_fields - set(character))
        if missing or character.get("coordinate_space") != "page":
            raise AssertionError(f"Compiled character contract failed: {character!r}; missing={missing}")

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
            "Character conditioning gate failed: "
            f"mask_count={character_masks.shape[0]} debug_count={len(character_entries)}"
        )

    print(
        json.dumps(
            {
                "status": "PASS",
                "source_workflow": str(LR4_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
                "changed_document_paths": changed_paths,
                "schema_changed": False,
                "input_mode": research["pages"][0]["scenes"][0]["input_mode"],
                "compiled_character_count": len(characters),
                "compiled_characters": [
                    {
                        "instance_id": c["instance_id"],
                        "character_id": c["character_id"],
                        "combined_prompt": c["combined_prompt"],
                        "area": c["area"],
                        "coordinate_space": c["coordinate_space"],
                    }
                    for c in characters
                ],
                "editor_debug": {
                    "compiled_characters": debug.get("compiled_characters", []),
                    "cast_count": debug.get("cast_count"),
                    "character_instances_count": debug.get("character_instances_count"),
                },
                "conditioning": {
                    "status": conditioning_debug["status"],
                    "character_strength": conditioning_debug["tuning"]["character_strength"],
                    "character_masks_count": int(character_masks.shape[0]),
                    "character_entries": character_entries,
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
