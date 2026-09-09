"""Run the bounded H2B prompt-only/source-anchored still comparison.

This is a local feasibility runner, not a production Still UI.  It stages one
validated PNG/JPEG below the configured Native input directory, materializes
the H2B graph through its semantic adapter, and submits prompt-only and
source-anchored controls with matched settings when ``--mode both`` is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
import sys
import time
from typing import Any, Mapping

from PIL import Image, UnidentifiedImageError

PORTABLE_ROOT = Path(__file__).resolve().parents[2]
if str(PORTABLE_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTABLE_ROOT))

from h3.adapters.native_source_anchored_still import (  # noqa: E402
    H3SourceAnchorRequest,
    PROMPT_ONLY_ROUTE,
    ROUTE_SOURCE_ANCHORED_STILL,
    compile_prompt_only_workflow,
    compile_workflow,
    validate_source_anchor_request,
    workflow_metadata,
)
from h3.adapters.native_still import (  # noqa: E402
    H3StillRequest,
    PACKET_FRAMES,
    SELECTED_FRAME_INDEX,
)
from h3.tests.run_h2a_still import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    GenerationError,
    Telemetry,
    _completed,
    _history_error,
    _iter_image_records,
    _json_request,
    _safe_output_path,
)


DEFAULT_PROMPT = (
    "Retain the same small service robot, pose, and overall greenhouse "
    "composition from the source image; change the lighting to warm "
    "late-afternoon sunlight with a gentle golden atmosphere while "
    "preserving the framing."
)
DEFAULT_SEED = 20260910
ALLOWED_SOURCE_FORMATS = {"PNG", "JPEG"}
ALLOWED_SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_SOURCE_PIXELS = 16_777_216


def _validate_and_stage_source(source: Path, output_root: Path) -> dict[str, Any]:
    source_path = source.resolve()
    if not source_path.is_file():
        raise GenerationError(f"H2B source image is unavailable: {source_path}")
    if source_path.suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
        raise GenerationError("H2B source image must have a PNG or JPEG suffix.")

    source_bytes = source_path.read_bytes()
    if len(source_bytes) > MAX_SOURCE_BYTES:
        raise GenerationError("H2B source image exceeds the 20 MiB limit.")
    source_sha256 = hashlib.sha256(source_bytes).hexdigest().upper()
    try:
        with Image.open(source_path) as image:
            image.load()
            image_format = image.format
            dimensions = [int(image.width), int(image.height)]
    except (OSError, UnidentifiedImageError) as exc:
        raise GenerationError("H2B source image is not a readable PNG or JPEG.") from exc
    if image_format not in ALLOWED_SOURCE_FORMATS:
        raise GenerationError("H2B source image content must be PNG or JPEG.")
    if dimensions[0] * dimensions[1] > MAX_SOURCE_PIXELS:
        raise GenerationError("H2B source image exceeds the pixel limit.")

    staged_suffix = ".png" if image_format == "PNG" else ".jpg"
    staged_name = f"h2b_source_{source_sha256[:16].lower()}{staged_suffix}"
    staged_path = (output_root / "inputs" / staged_name).resolve()
    try:
        staged_path.relative_to(output_root.resolve())
    except ValueError as exc:  # pragma: no cover - fixed staging path guard
        raise GenerationError("H2B source staging escaped the H3 output directory.") from exc
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    if staged_path != source_path:
        shutil.copyfile(source_path, staged_path)

    staged_relative_path = f"inputs/{staged_name}"
    return {
        "source_name": source_path.name,
        "source_sha256": source_sha256,
        "source_bytes": len(source_bytes),
        "format": image_format,
        "dimensions": dimensions,
        "staged_path": staged_relative_path,
        "staged_absolute_path": str(staged_path),
    }


def _run_one(
    args: argparse.Namespace,
    *,
    mode: str,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    request = H3StillRequest(prompt=args.prompt, seed=args.seed, steps=args.steps)
    if mode == "anchored":
        anchor_request = validate_source_anchor_request(
            {
                "prompt": request.prompt,
                "width": request.width,
                "height": request.height,
                "seed": request.seed,
                "steps": request.steps,
                "source_path": source["staged_path"],
            }
        )
        graph = compile_workflow(anchor_request)
        route = ROUTE_SOURCE_ANCHORED_STILL
        client_id = "tegaki-h2b-source-anchor"
        conditioning = {
            "node": "131",
            "class_type": "MiniMaxH3ImageToVideo",
            "source_loader_node": "133",
            "first_frame": ["133", 0],
            "source_path": source["staged_path"],
            "temporal_frame": 0,
            "resize": "plain stretch to 608x352; crop=disabled",
            "strength": "NOT APPLICABLE",
        }
    else:
        graph = compile_prompt_only_workflow(request)
        route = PROMPT_ONLY_ROUTE
        client_id = "tegaki-h2b-prompt-only-control"
        conditioning = {
            "node": "131",
            "class_type": "MiniMaxH3ImageToVideo",
            "source_loader_node": None,
            "first_frame": None,
            "temporal_frame": None,
            "resize": "NOT APPLICABLE",
            "strength": "NOT APPLICABLE",
        }

    telemetry = Telemetry(args.native_port)
    telemetry.sample()
    started = time.monotonic()
    response = _json_request(
        args.comfy_url,
        "/prompt",
        method="POST",
        payload={"prompt": graph, "client_id": client_id},
        timeout=30,
    )
    prompt_id = response.get("prompt_id") if isinstance(response, Mapping) else None
    if not isinstance(prompt_id, str) or not prompt_id:
        if isinstance(response, Mapping) and response.get("node_errors"):
            raise GenerationError(
                f"Native rejected H2B {mode} workflow: {response['node_errors']}"
            )
        raise GenerationError(f"Native did not return a prompt id for H2B {mode}.")

    deadline = time.monotonic() + args.timeout
    entry: Mapping[str, Any] | None = None
    while time.monotonic() < deadline:
        telemetry.sample()
        history = _json_request(
            args.comfy_url,
            f"/history/{prompt_id}",
            timeout=15,
        )
        candidate = history.get(prompt_id) if isinstance(history, Mapping) else None
        if isinstance(candidate, Mapping) and _completed(candidate):
            entry = candidate
            break
        time.sleep(args.poll_seconds)
    telemetry.sample()
    if entry is None:
        raise GenerationError(f"Native H2B {mode} generation timed out after {args.timeout:g}s.")

    records = list(_iter_image_records(entry.get("outputs")))
    if not records:
        status = entry.get("status")
        if isinstance(status, Mapping) and status.get("status_str") in {"error", "failed"}:
            raise GenerationError(_history_error(entry))
        raise GenerationError(f"Native H2B {mode} completed without an image output.")
    record = records[0]
    output_root = Path(args.output_root).resolve()
    output_path = _safe_output_path(output_root, record)
    with Image.open(output_path) as image:
        image.load()
        output_format = image.format
        dimensions = [int(image.width), int(image.height)]
    output_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest().upper()
    return {
        "mode": mode,
        "route": route,
        "workflow": "workflows/h3/H2B_SOURCE_ANCHORED_STILL_BASE.json",
        "workflow_schema": "tegaki.h3.h2b.source-anchored-still/v1",
        "prompt_id": prompt_id,
        "prompt": request.prompt,
        "resolution": f"{request.width}x{request.height}",
        "packet_frames": PACKET_FRAMES,
        "selected_frame_index": SELECTED_FRAME_INDEX,
        "seed": request.seed,
        "steps": request.steps,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "output": {
            "path": str(output_path),
            "filename": record.get("filename"),
            "subfolder": record.get("subfolder") or "",
            "format": output_format,
            "dimensions": dimensions,
            "bytes": output_path.stat().st_size,
            "sha256": output_sha256,
        },
        "conditioning": conditioning,
        "telemetry": telemetry.public(),
        "oom_count": 0,
        "retry_count": 0,
        "model_changes": "NONE",
        "dependency_changes": "NONE",
        "shared_comfyui_changes": "NONE",
        "manga_changes": "NONE",
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root).resolve()
    source = _validate_and_stage_source(Path(args.source).expanduser(), output_root)
    modes = {
        "both": ("prompt-only", "anchored"),
        "prompt-only": ("prompt-only",),
        "anchored": ("anchored",),
    }[args.mode]
    runs = [
        _run_one(args, mode=mode, source=source)
        for mode in modes
    ]
    return {
        "status": "PASS",
        "card": "H2B",
        "source": {
            key: value
            for key, value in source.items()
            if key != "staged_absolute_path"
        },
        "matched_settings": {
            "prompt": args.prompt,
            "resolution": "608x352",
            "seed": args.seed,
            "steps": args.steps,
            "packet_frames": PACKET_FRAMES,
            "selected_frame_index": SELECTED_FRAME_INDEX,
        },
        "workflow_metadata": workflow_metadata(),
        "runs": runs,
        "browser_ui": "N/A",
        "owner_acceptance": "PENDING",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the H2B Native H3 source-anchored still comparison."
    )
    parser.add_argument("--source", required=True, help="One local PNG or JPEG source image.")
    parser.add_argument("--mode", choices=("both", "prompt-only", "anchored"), default="both")
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    parser.add_argument("--native-port", type=int, default=8188)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--poll-seconds", type=float, default=2)
    return parser.parse_args()


def main() -> None:
    try:
        result = run(parse_args())
    except (GenerationError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
