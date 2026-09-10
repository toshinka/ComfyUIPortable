"""Run the bounded IP1 Native H3 image-prep/reference-edit cases.

This runner stages local PNG/JPEG/WebP inputs below ``output/h3/inputs`` and
submits only the IP1 Native ``SaveImage`` graph to an already-running ComfyUI
instance.  It never calls the H3 Browser skin, uploads to an external service,
or performs quality-driven retries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Mapping

from PIL import Image, UnidentifiedImageError

PORTABLE_ROOT = Path(__file__).resolve().parents[2]
if str(PORTABLE_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTABLE_ROOT))

from h3.adapters.native_image_prep import (  # noqa: E402
    FPS,
    H3ImagePrepRequest,
    PACKET_FRAMES,
    ROUTE_IMAGE_PREP,
    SELECTED_FRAME_INDEX,
    WIDTH,
    HEIGHT,
    compile_workflow,
    materialize_prompt,
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


DEFAULT_SEED = 20260911
DEFAULT_TIMEOUT = 1800.0
DEFAULT_POLL_SECONDS = 2.0
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_INPUT_BYTES = 20 * 1024 * 1024
MAX_INPUT_PIXELS = 16_777_216

CASE_PROMPTS = {
    "A": (
        "Keep the recognizable red-and-white robot design and approximate framing. "
        "Change only the environment to a rainy outdoor setting with visible wet "
        "surfaces and rainfall."
    ),
    "B": (
        "Keep the recognizable source robot design and general composition. "
        "Transfer only the bright yellow raincoat or protective-coat material and "
        "color treatment from the donor. Do not replace the whole scene."
    ),
    "C": (
        "Keep the same recognizable robot design. Change only the view to a mild "
        "three-quarter angle and raise one arm. Keep a simple background."
    ),
}


def _stage_image(source: Path, output_root: Path, *, role: str) -> dict[str, Any]:
    source_path = source.expanduser().resolve()
    if not source_path.is_file():
        raise GenerationError(f"IP1 {role} image is unavailable: {source_path}")
    if source_path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise GenerationError(f"IP1 {role} image must have a PNG, JPEG, or WebP suffix.")
    source_bytes = source_path.read_bytes()
    if len(source_bytes) > MAX_INPUT_BYTES:
        raise GenerationError(f"IP1 {role} image exceeds the 20 MiB limit.")
    try:
        with Image.open(source_path) as image:
            image.load()
            image_format = image.format
            dimensions = [int(image.width), int(image.height)]
    except (OSError, UnidentifiedImageError) as exc:
        raise GenerationError(f"IP1 {role} image is not readable.") from exc
    if image_format not in ALLOWED_FORMATS:
        raise GenerationError(f"IP1 {role} image content must be PNG, JPEG, or WebP.")
    if dimensions[0] * dimensions[1] > MAX_INPUT_PIXELS:
        raise GenerationError(f"IP1 {role} image exceeds the pixel limit.")

    digest = hashlib.sha256(source_bytes).hexdigest().upper()
    suffix = source_path.suffix.lower()
    if suffix == ".jpeg":
        suffix = ".jpg"
    staged_name = f"ip1_{role}_{digest[:16].lower()}{suffix}"
    staged_path = (output_root / "inputs" / staged_name).resolve()
    try:
        staged_path.relative_to(output_root.resolve())
    except ValueError as exc:  # pragma: no cover - fixed staging path guard
        raise GenerationError("IP1 image staging escaped the H3 output directory.") from exc
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    if staged_path != source_path:
        shutil.copyfile(source_path, staged_path)
    return {
        "role": role,
        "source_name": source_path.name,
        "source_sha256": digest,
        "source_bytes": len(source_bytes),
        "format": image_format,
        "dimensions": dimensions,
        "staged_path": f"inputs/{staged_name}",
        "staged_absolute_path": str(staged_path),
    }


def _run_case(
    args: argparse.Namespace,
    *,
    case: str,
    source: Mapping[str, Any],
    donor: Mapping[str, Any] | None,
) -> dict[str, Any]:
    request = H3ImagePrepRequest(
        prompt=CASE_PROMPTS[case],
        source_path=str(source["staged_path"]),
        donor_path=str(donor["staged_path"]) if donor is not None and case == "B" else None,
        seed=args.seed,
        steps=20,
    )
    graph = compile_workflow(request)
    conditioning = graph["131"]["inputs"]
    telemetry = Telemetry(args.native_port)
    telemetry.sample()
    started = time.monotonic()
    response = _json_request(
        args.comfy_url,
        "/prompt",
        method="POST",
        payload={
            "prompt": graph,
            "client_id": f"tegaki-ip1-image-prep-case-{case.lower()}",
        },
        timeout=30,
    )
    prompt_id = response.get("prompt_id") if isinstance(response, Mapping) else None
    if not isinstance(prompt_id, str) or not prompt_id:
        node_errors = response.get("node_errors") if isinstance(response, Mapping) else None
        raise GenerationError(f"Native rejected IP1 case {case}: {node_errors or response}")

    deadline = time.monotonic() + float(args.timeout)
    entry: Mapping[str, Any] | None = None
    while time.monotonic() < deadline:
        telemetry.sample()
        history = _json_request(
            args.comfy_url,
            f"/history/{prompt_id}",
            timeout=20,
        )
        candidate = history.get(prompt_id) if isinstance(history, Mapping) else None
        if isinstance(candidate, Mapping) and _completed(candidate):
            entry = candidate
            break
        time.sleep(float(args.poll_seconds))
    telemetry.sample()
    if entry is None:
        raise GenerationError(f"Native IP1 case {case} timed out after {args.timeout:g}s.")

    records = list(_iter_image_records(entry.get("outputs")))
    if not records:
        status = entry.get("status")
        if isinstance(status, Mapping) and status.get("status_str") in {"error", "failed"}:
            raise GenerationError(_history_error(entry))
        raise GenerationError(f"Native IP1 case {case} completed without a PNG output.")
    record = records[0]
    output_root = Path(args.output_root).resolve()
    output_path = _safe_output_path(output_root, record)
    with Image.open(output_path) as image:
        image.load()
        dimensions = [int(image.width), int(image.height)]
        output_format = image.format
    if dimensions != [WIDTH, HEIGHT] or output_format != "PNG":
        raise GenerationError(
            f"Native IP1 case {case} output must be a {WIDTH}x{HEIGHT} PNG; "
            f"received {dimensions} {output_format}."
        )
    elapsed = round(time.monotonic() - started, 2)
    public_telemetry = telemetry.public()
    return {
        "case": case,
        "route": ROUTE_IMAGE_PREP,
        "workflow": "workflows/h3/IP1_NATIVE_IMAGE_PREP_BASE.json",
        "workflow_schema": "tegaki.h3.ip1.native-image-prep/v1",
        "prompt_id": prompt_id,
        "prompt": request.prompt,
        "materialized_prompt": conditioning["prompt"],
        "references": {
            "Picture 1": {"role": "source", "staged_path": source["staged_path"]},
            "Picture 2": (
                {"role": "optional donor attribute", "staged_path": donor["staged_path"]}
                if donor is not None and case == "B"
                else None
            ),
        },
        "settings": {
            "width": request.width,
            "height": request.height,
            "steps": request.steps,
            "seed": request.seed,
            "fps_basis": request.fps,
            "packet_frames": request.length,
        },
        "frame_selection": {
            "packet": "Native 5-frame temporal packet",
            "decode_node": "122",
            "select_node": "132 ImageFromBatch",
            "selected_frame_index": SELECTED_FRAME_INDEX,
            "selected_output": "SaveImage PNG",
        },
        "output": {
            "path": str(output_path),
            "filename": record.get("filename"),
            "subfolder": record.get("subfolder") or "",
            "format": output_format,
            "dimensions": dimensions,
            "bytes": output_path.stat().st_size,
            "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest().upper(),
        },
        "elapsed_seconds": elapsed,
        "telemetry": public_telemetry,
        "derived_observed_peak_vram_mib": public_telemetry.get("peak_observed_vram_used_mib"),
        "oom_count": 0,
        "retry_count": 0,
        "model_changes": "NONE",
        "dependency_changes": "NONE",
        "shared_comfyui_changes": "NONE",
        "manga_changes": "NONE",
        "audio_reference": "NOT CONNECTED",
        "video_reference": "NOT CONNECTED",
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root).resolve()
    source = _stage_image(Path(args.source), output_root, role="source")
    donor = _stage_image(Path(args.donor), output_root, role="donor") if args.donor else None
    if donor is None:
        raise GenerationError("IP1 requires the approved single donor for cases B; pass --donor.")
    cases = [_run_case(args, case=case, source=source, donor=donor) for case in ("A", "B", "C")]
    return {
        "status": "PASS",
        "card": "IP1",
        "classification": "PENDING VISUAL REVIEW",
        "baseline": {
            "width": WIDTH,
            "height": HEIGHT,
            "steps": 20,
            "fps_basis": FPS,
            "packet_frames": PACKET_FRAMES,
            "selected_frame_index": SELECTED_FRAME_INDEX,
            "model": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
            "text_encoder": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
            "video_vae": "minimax_h3_video_vae_fp16.safetensors",
            "audio_vae": "minimax_h3_audio_vae_fp32.safetensors (required Native input; no audio lane)",
            "turbo_lora": False,
            "custom_nodes": "none",
        },
        "source": {key: value for key, value in source.items() if key != "staged_absolute_path"},
        "donor": {key: value for key, value in donor.items() if key != "staged_absolute_path"},
        "donor_generation": "ONE H2A prompt-only Still generation; no additional donor generation",
        "cases": cases,
        "browser_ui": "NOT IMPLEMENTED",
        "owner_acceptance": "PENDING",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded IP1 Native H3 image-prep cases.")
    parser.add_argument("--source", required=True, help="One local PNG, JPEG, or WebP source image.")
    parser.add_argument("--donor", required=True, help="The one local PNG, JPEG, or WebP donor image.")
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8189")
    parser.add_argument("--native-port", type=int, default=8189)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
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
