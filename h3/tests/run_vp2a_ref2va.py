"""Run the VP2A-R1 Native Ref2VA feasibility slice.

The runner stages only the approved local picture and an already-verified local
H1A motion result under the isolated H3 input directory. It submits one
Picture-only Ref2VA graph, then one matched Picture+Video graph, and finally
one standard FL2VA/T2V transition graph. It performs no browser or model
manager action and never connects reference audio.
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


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.adapters.native_ref2va import (
    BASELINE_DURATION_SECONDS,
    BASELINE_HEIGHT,
    BASELINE_STEPS,
    BASELINE_WIDTH,
    H3Ref2VARequest,
    compile_workflow as compile_ref2va,
)
from h3.adapters.native_t2v import H3Request, compile_workflow as compile_t2v

from h3.tests.run_vp1_video_envelope import (
    FPS,
    GenerationError,
    Telemetry,
    _ffprobe,
    _history_error,
    _is_completed,
    _is_failed,
    _iter_media,
    _json_request,
    _safe_output_path,
)


OUTPUT_ROOT = REPO_ROOT / "output" / "h3"
INPUT_ROOT = OUTPUT_ROOT / "inputs"
DEFAULT_PICTURE = OUTPUT_ROOT / "tests" / "reference_robot_v1.png"
DEFAULT_MOTION = OUTPUT_ROOT / "video" / "h1a_native_t2v_00010_.mp4"
DEFAULT_COMFY_URL = "http://127.0.0.1:8189"
DEFAULT_NATIVE_PORT = 8189
DEFAULT_SEED = 20260910
DEFAULT_TIMEOUT_SECONDS = 2400
DEFAULT_POLL_SECONDS = 2.0
EXPECTED_FRAMES = 124
EXPECTED_DURATION_SECONDS = EXPECTED_FRAMES / FPS
MOTION_INPUT_WIDTH = 608
MOTION_INPUT_HEIGHT = 352
MOTION_INPUT_FRAMES = 124

PICTURE_PROMPT = (
    "Use <Picture 1> as the subject appearance reference. Preserve its recognizable "
    "small red service robot design, round white head, and dominant colors. Place the "
    "robot in a simple quiet workshop with warm daylight, walking slowly from left to "
    "right while the camera tracks gently."
)
PICTURE_VIDEO_PROMPT = (
    "Use <Picture 1> for the subject identity and appearance: preserve its recognizable "
    "small red service robot design, round white head, and dominant colors. Use <Video 1> "
    "for motion, timing, and camera behavior: follow its walking movement and gentle "
    "tracking rhythm. Place the robot in a simple quiet workshop with warm daylight."
)
TRANSITION_PROMPT = (
    "A small red service robot with a round white head walks slowly through a quiet "
    "workshop in warm daylight. The camera tracks gently from left to right while a "
    "few loose papers move slightly in the air."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve_inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise GenerationError(f"{label} must remain inside {root}.") from exc
    if not resolved.is_file():
        raise GenerationError(f"{label} is missing: {resolved}")
    return resolved


def _stage_file(source: Path, destination_stem: str, suffix: str) -> dict[str, Any]:
    source = source.resolve()
    source_sha = _sha256(source)
    staged_name = f"{destination_stem}_{source_sha[:16].lower()}{suffix}"
    staged = (INPUT_ROOT / staged_name).resolve()
    _resolve_inside(staged, INPUT_ROOT, "staged input") if staged.exists() else None
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if staged.exists():
        if _sha256(staged) != source_sha:
            raise GenerationError(f"Existing staged input hash mismatch: {staged}")
    else:
        shutil.copyfile(source, staged)
    return {
        "source_path": str(source),
        "staged_path": f"inputs/{staged.name}",
        "bytes": staged.stat().st_size,
        "sha256": source_sha,
    }


def _stage_sources(picture_path: Path, motion_path: Path) -> dict[str, Any]:
    picture = _resolve_inside(picture_path, OUTPUT_ROOT, "picture source")
    if picture.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise GenerationError("Picture source must be a local PNG/JPEG/WebP file.")
    motion = _resolve_inside(motion_path, OUTPUT_ROOT, "motion source")
    if motion.suffix.lower() not in {".mp4", ".webm", ".mov", ".mkv"}:
        raise GenerationError("Motion source must be a local video file.")
    motion_media = _ffprobe(motion)
    if (motion_media["width"], motion_media["height"]) != (MOTION_INPUT_WIDTH, MOTION_INPUT_HEIGHT):
        raise GenerationError("Motion reference is not the verified 608x352 baseline.")
    if motion_media["encoded_frame_count"] != MOTION_INPUT_FRAMES:
        raise GenerationError("Motion reference is not the verified 124-frame baseline.")
    if abs(motion_media["fps"] - FPS) > 0.01:
        raise GenerationError("Motion reference is not 24 fps.")
    picture_record = _stage_file(picture, "vp2a_r1_picture", picture.suffix.lower())
    motion_record = _stage_file(motion, "vp2a_r1_motion", ".mp4")
    return {
        "picture": picture_record,
        "motion": {**motion_record, "ffprobe": motion_media},
    }


def _validate_media(path: Path) -> dict[str, Any]:
    media = _ffprobe(path)
    if (media["width"], media["height"]) != (BASELINE_WIDTH, BASELINE_HEIGHT):
        raise GenerationError(
            f"Native output dimensions {media['width']}x{media['height']} do not match 608x352."
        )
    if media["encoded_frame_count"] != EXPECTED_FRAMES:
        raise GenerationError(
            f"Native encoded {media['encoded_frame_count']} frames; expected {EXPECTED_FRAMES}."
        )
    if abs(media["fps"] - FPS) > 0.01:
        raise GenerationError(f"Native output fps {media['fps']} is not {FPS}.")
    if abs(media["duration_seconds"] - EXPECTED_DURATION_SECONDS) > 0.15:
        raise GenerationError(
            f"Native duration {media['duration_seconds']:.3f}s is not near "
            f"{EXPECTED_DURATION_SECONDS:.3f}s."
        )
    return media


def _run_graph(
    args: argparse.Namespace,
    *,
    label: str,
    graph: Mapping[str, Any],
    route: str,
) -> dict[str, Any]:
    telemetry = Telemetry(args.native_port)
    telemetry.sample()
    started = time.monotonic()
    prompt_id: str | None = None
    entry: Mapping[str, Any] | None = None
    try:
        response = _json_request(
            args.comfy_url,
            "/prompt",
            method="POST",
            payload={"prompt": graph, "client_id": f"tegaki-vp2a-r1-{label}"},
            timeout=30,
        )
        prompt_id = response.get("prompt_id") if isinstance(response, Mapping) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            node_errors = response.get("node_errors") if isinstance(response, Mapping) else None
            raise GenerationError(f"Native did not return a prompt id: {node_errors or response}")

        deadline = time.monotonic() + float(args.timeout)
        while time.monotonic() < deadline:
            telemetry.sample()
            history = _json_request(args.comfy_url, f"/history/{prompt_id}", timeout=20)
            candidate = history.get(prompt_id) if isinstance(history, Mapping) else None
            if isinstance(candidate, Mapping) and (_is_completed(candidate) or _is_failed(candidate)):
                entry = candidate
                break
            time.sleep(float(args.poll_seconds))
        telemetry.sample()
        if entry is None:
            raise GenerationError(f"Native generation timed out after {args.timeout:g}s.")
        if not _is_completed(entry):
            raise GenerationError(_history_error(entry))
        records = list(_iter_media(entry.get("outputs")))
        if not records:
            raise GenerationError("Native completed without a video output.")
        output_path = _safe_output_path(OUTPUT_ROOT, records[0])
        media = _validate_media(output_path)
        return {
            "status": "PASS",
            "label": label,
            "route": route,
            "prompt_id": prompt_id,
            "output": {
                "path": str(output_path),
                "filename": records[0].get("filename"),
                "subfolder": records[0].get("subfolder") or "",
                "bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
                "ffprobe": media,
            },
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "telemetry": telemetry.public(),
            "oom_count": 0,
            "retry_count": 0,
        }
    except GenerationError as exc:
        message = str(exc)
        lowered = message.lower()
        oom_count = 1 if "out of memory" in lowered or "cuda oom" in lowered else 0
        return {
            "status": "FAIL",
            "classification": "12GB BLOCKED" if oom_count else "FAILED",
            "label": label,
            "route": route,
            "prompt_id": prompt_id,
            "error": message,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "telemetry": telemetry.public(),
            "oom_count": oom_count,
            "retry_count": 0,
        }


def _make_transition_graph() -> dict[str, dict[str, Any]]:
    request = H3Request(
        prompt=TRANSITION_PROMPT,
        width=BASELINE_WIDTH,
        height=BASELINE_HEIGHT,
        duration=BASELINE_DURATION_SECONDS,
        seed=DEFAULT_SEED,
        steps=BASELINE_STEPS,
    )
    graph = compile_t2v(request)
    graph["92"]["inputs"]["filename_prefix"] = "video/vp2a_r1_transition_fl2va"
    return graph


def run(args: argparse.Namespace) -> dict[str, Any]:
    picture_path = Path(args.picture).resolve() if args.picture else DEFAULT_PICTURE
    motion_path = Path(args.motion).resolve() if args.motion else DEFAULT_MOTION
    sources = _stage_sources(picture_path, motion_path)
    picture_request = H3Ref2VARequest(
        prompt=PICTURE_PROMPT,
        picture_path=sources["picture"]["staged_path"],
        seed=DEFAULT_SEED,
        output_prefix="video/vp2a_r1_ref2va_picture",
    )
    picture_video_request = H3Ref2VARequest(
        prompt=PICTURE_VIDEO_PROMPT,
        picture_path=sources["picture"]["staged_path"],
        video_path=sources["motion"]["staged_path"],
        seed=DEFAULT_SEED,
        output_prefix="video/vp2a_r1_ref2va_picture_video",
    )

    picture = _run_graph(
        args,
        label="picture-only",
        graph=compile_ref2va(picture_request),
        route="native_ref2va_picture_only",
    )
    result: dict[str, Any] = {
        "schema": "tegaki.h3.vp2a-r1.native-ref2va-feasibility/v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "backend": {"comfy_url": args.comfy_url, "native_port": args.native_port},
        "contract": {
            "width": BASELINE_WIDTH,
            "height": BASELINE_HEIGHT,
            "duration_seconds": BASELINE_DURATION_SECONDS,
            "frames": EXPECTED_FRAMES,
            "fps": FPS,
            "steps": BASELINE_STEPS,
            "seed": DEFAULT_SEED,
            "ref_image_size": "match",
            "audio_reference": "NOT USED",
        },
        "sources": sources,
        "stages": {"picture_only": picture},
    }
    if picture["status"] != "PASS":
        result["classification"] = "12GB BLOCKED" if picture.get("oom_count") else "NATIVE API BLOCKED"
        result["stages"]["picture_plus_video"] = {
            "status": "SKIPPED",
            "reason": "Picture-only stage did not pass; Stage B is gated.",
        }
        result["transition"] = {"status": "SKIPPED", "reason": "No Ref2VA success; transition is gated."}
        return result

    picture_video = _run_graph(
        args,
        label="picture-plus-video",
        graph=compile_ref2va(picture_video_request),
        route="native_ref2va_picture_plus_video",
    )
    result["stages"]["picture_plus_video"] = picture_video
    if picture_video["status"] != "PASS":
        result["classification"] = "12GB BLOCKED" if picture_video.get("oom_count") else "NATIVE API BLOCKED"
        result["transition"] = {"status": "SKIPPED", "reason": "Picture+Video stage did not pass."}
        return result

    transition = _run_graph(
        args,
        label="transition-fl2va-t2v",
        graph=_make_transition_graph(),
        route="native_t2v_fl2va_transition",
    )
    if transition["status"] == "PASS":
        transition["classification"] = "BUILT-IN MODEL TRANSITION PASS"
        result["classification"] = "FEASIBLE WITH LIMITS"
        result["classification_reason"] = (
            "All three bounded Native rows passed, but the observed 12GB VRAM "
            "headroom was near the limit and Picture+Video visual influence "
            "must be treated as reference-role dependent."
        )
    elif transition.get("oom_count"):
        transition["classification"] = "FEASIBLE WITH LIMITS"
        transition["transition_classification"] = "RESTART REQUIRED"
    else:
        result["classification"] = "FEASIBLE WITH LIMITS"
        transition["classification"] = "BLOCKED"
        result["transition_classification"] = "BLOCKED"
    result["transition"] = transition
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-url", default=DEFAULT_COMFY_URL)
    parser.add_argument("--native-port", type=int, default=DEFAULT_NATIVE_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--picture", help="Approved local picture below output/h3.")
    parser.add_argument("--motion", help="Verified local H1A motion video below output/h3.")
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        result = run(args)
    except GenerationError as exc:
        result = {
            "schema": "tegaki.h3.vp2a-r1.native-ref2va-feasibility/v1",
            "classification": "NATIVE API BLOCKED",
            "status": "FAIL",
            "error": str(exc),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("classification") in {"NATIVE API BLOCKED", "12GB BLOCKED"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
