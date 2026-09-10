#!/usr/bin/env python3
"""Build the M3B-LR3 Figure-geometry-derived clean ControlNet guide.

This is a research-only helper.  It reads the existing LR2R1 research
workflow, derives page-space Figure bounds from the persisted Guide placement
and Figure local areas, verifies the audited bounds, and reuses Tegaki's
existing flat-silhouette renderer.  It does not modify the authoring schema,
production workflows, or the Rough Guide bridge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = REPO_ROOT / "workflows" / "manga" / "research" / "M3B_LR2R1_ANYTEST_AB.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "manga" / "verification" / "m3b_lr3" / "M3B_LR3_CLEAN_GUIDE.png"
DEFAULT_PROVENANCE = REPO_ROOT / "docs" / "manga" / "verification" / "m3b_lr3" / "M3B_LR3_CLEAN_GUIDE_PROVENANCE.json"

WIDTH = 832
HEIGHT = 1216
TOLERANCE = 0.0001
EXPECTED_PAGE_BOUNDS: Mapping[str, Tuple[float, float, float, float]] = {
    "figure_1": (0.05, 0.304984, 0.38, 0.369504),
    "figure_2": (0.57, 0.356304, 0.28, 0.297656),
}


def _load_document(workflow_path: Path) -> Dict[str, Any]:
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    document_json = workflow["prompt"]["1"]["inputs"]["document_json"]
    document = json.loads(document_json)
    if document.get("schema_id") != "TEGAKI_AUTHORING_DOCUMENT":
        raise RuntimeError("LR2R1 document schema id is not TEGAKI_AUTHORING_DOCUMENT")
    if document.get("schema_version") != "1.0.0":
        raise RuntimeError(f"unexpected LR2R1 schema version: {document.get('schema_version')!r}")
    scene = document["pages"][0]["scenes"][0]
    if scene.get("input_mode") != "simple":
        raise RuntimeError(f"M3B-LR3 requires LR2R1 simple input_mode, got {scene.get('input_mode')!r}")
    return document


def _get_guide(document: Mapping[str, Any]) -> Mapping[str, Any]:
    guides = document["pages"][0].get("guides", [])
    for guide in guides:
        if guide.get("guide_id") == "guide_1":
            return guide
    raise RuntimeError("LR2R1 guide_1 was not found")


def _derive_page_area(placement: Mapping[str, Any], local_area: Mapping[str, Any]) -> Tuple[float, float, float, float]:
    gx = float(placement["x"])
    gy = float(placement["y"])
    gw = float(placement["w"])
    gh = float(placement["h"])
    lx = float(local_area["x"])
    ly = float(local_area["y"])
    lw = float(local_area["w"])
    lh = float(local_area["h"])
    return (
        gx + lx * gw,
        gy + ly * gh,
        lw * gw,
        lh * gh,
    )


def _assert_audited_bounds(figure_id: str, derived: Sequence[float]) -> None:
    expected = EXPECTED_PAGE_BOUNDS[figure_id]
    mismatches = [abs(float(actual) - float(want)) for actual, want in zip(derived, expected)]
    if any(delta > TOLERANCE for delta in mismatches):
        raise RuntimeError("CLEAN_GUIDE_GEOMETRY_PROVENANCE_MISMATCH")


def _pixel_bounds(page_area: Sequence[float]) -> Tuple[int, int, int, int]:
    x, y, w, h = (float(value) for value in page_area)
    x0 = max(0, min(WIDTH - 1, int(round(x * WIDTH))))
    y0 = max(0, min(HEIGHT - 1, int(round(y * HEIGHT))))
    x1 = max(x0 + 1, min(WIDTH, int(round((x + w) * WIDTH))))
    y1 = max(y0 + 1, min(HEIGHT, int(round((y + h) * HEIGHT))))
    return (x0, y0, x1, y1)


def _validate_clean_image(image: Image.Image, pixel_bounds: Iterable[Sequence[int]]) -> None:
    if image.size != (WIDTH, HEIGHT):
        raise RuntimeError(f"CLEAN guide dimensions are {image.size}, expected {(WIDTH, HEIGHT)}")
    if image.mode != "RGB":
        raise RuntimeError(f"CLEAN guide mode is {image.mode}, expected RGB")

    colors = set(image.getdata())
    allowed = {(0, 0, 0), (255, 255, 255)}
    if not colors or not colors.issubset(allowed) or (0, 0, 0) not in colors:
        raise RuntimeError(f"CLEAN guide must contain only black and white pixels, got {sorted(colors)[:8]}")

    pixels = image.load()
    boxes = [tuple(int(value) for value in bounds) for bounds in pixel_bounds]
    black_counts: List[int] = []
    for x0, y0, x1, y1 in boxes:
        black_counts.append(
            sum(
                1
                for y in range(y0, y1)
                for x in range(x0, x1)
                if pixels[x, y] == (0, 0, 0)
            )
        )
    if any(count == 0 for count in black_counts):
        raise RuntimeError(f"CLEAN guide did not render both Figure silhouettes: {black_counts}")

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if pixels[x, y] != (0, 0, 0):
                continue
            if not any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in boxes):
                raise RuntimeError("CLEAN guide contains black pixels outside derived Figure bounds")


def build_clean_guide(workflow_path: Path, output_path: Path, provenance_path: Path) -> Dict[str, Any]:
    # Import only after the repository root is known so the existing package
    # renderer can resolve its relative interaction_resolver import.
    sys.path.insert(0, str(REPO_ROOT))
    from custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator import (  # pylint: disable=import-outside-toplevel
        draw_single_character_mannequin,
    )

    document = _load_document(workflow_path)
    guide = _get_guide(document)
    placement = guide["placement"]
    figures = guide.get("figure_regions", [])
    if len(figures) != 2:
        raise RuntimeError(f"expected exactly two LR2R1 figure regions, got {len(figures)}")

    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    records: List[Dict[str, Any]] = []
    pixel_boxes: List[Tuple[int, int, int, int]] = []
    for figure in figures:
        figure_id = str(figure["figure_id"])
        if figure_id not in EXPECTED_PAGE_BOUNDS:
            raise RuntimeError(f"unexpected LR2R1 figure id: {figure_id}")
        local_area = figure["area"]
        derived_page_area = _derive_page_area(placement, local_area)
        _assert_audited_bounds(figure_id, derived_page_area)
        pixel_box = _pixel_bounds(derived_page_area)
        draw_single_character_mannequin(
            draw,
            *pixel_box,
            guide_style="flat_silhouette",
            fg_color=(0, 0, 0),
            box_outline_color=(0, 0, 0),
            fill_color=(0, 0, 0),
            line_thickness=1,
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="standing_neutral",
        )
        pixel_boxes.append(pixel_box)
        records.append(
            {
                "guide_id": guide["guide_id"],
                "figure_id": figure_id,
                "instance_id": figure["instance_id"],
                "local_area": local_area,
                "guide_placement": placement,
                "derived_page_area": dict(zip(("x", "y", "w", "h"), derived_page_area)),
                "pixel_bounds": dict(zip(("x0", "y0", "x1", "y1"), pixel_box)),
                "renderer": "custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator.draw_single_character_mannequin",
                "renderer_style": "flat_silhouette",
                "shot_type": "full_body",
                "pose_preset": "standing_neutral",
                "include_bbox_outline": False,
            }
        )

    _validate_clean_image(image, pixel_boxes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=False)
    output_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
    for record in records:
        record["canvas_dimensions"] = {"width": WIDTH, "height": HEIGHT}
        record["output_sha256"] = output_sha256

    provenance = {
        "card": "M3B-LR3",
        "source_workflow": str(workflow_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "document_id": document["document_id"],
        "input_mode": document["pages"][0]["scenes"][0]["input_mode"],
        "whole_page_control": True,
        "character_specific_control": False,
        "geometry_tolerance": TOLERANCE,
        "canvas_dimensions": {"width": WIDTH, "height": HEIGHT},
        "figures": records,
        "output": str(output_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "output_sha256": output_sha256,
    }
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    args = parser.parse_args()

    provenance = build_clean_guide(
        args.workflow.resolve(),
        args.output.resolve(),
        args.provenance.resolve(),
    )
    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
