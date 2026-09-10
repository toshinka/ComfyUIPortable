"""Run the bounded VP1 Native H3 video envelope matrix.

This runner is an evidence tool, not a second runtime. It submits the existing
H1A and H1B.1 API graphs to one already-running isolated Native ComfyUI
instance, records the same nvidia-smi/psutil telemetry method used by the H2
feasibility runners, and validates the returned MP4 with ffprobe.

The two candidate values are deliberately fixed to credible Native/official
patterns:

* D: 15 seconds, the upper end of the Native node's documented trained frame
  range (362 frames after the 17k+5 grid conversion), at the 608x352 baseline.
* R: 736x416, the next 16:9 / 0.3 MP entry in the official H3 workflow size
  reference, at the verified 5-second baseline.

Candidates are never submitted through the browser or advertised by /api/config
by this runner. Stage 2 runs only when the corresponding Stage 1 T2V result
passes all media checks. No retry is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import psutil
except ImportError:  # pragma: no cover - evidence records unavailable telemetry
    psutil = None

from h3.adapters.native_i2v import compile_fl2va_workflow  # noqa: E402
from h3.adapters.native_t2v import (  # noqa: E402
    H3Reference,
    H3ReferenceSlots,
    H3Request,
    REFERENCE_ROLE_END_FRAME,
    REFERENCE_ROLE_START_FRAME,
    compile_workflow as compile_t2v,
    duration_to_frames,
)


DEFAULT_COMFY_URL = "http://127.0.0.1:8189"
DEFAULT_NATIVE_PORT = 8189
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output" / "h3"
DEFAULT_PROMPT = (
    "A small orange service robot stands alone in a leafy greenhouse after rain, "
    "warm late-afternoon light, gentle natural camera movement, coherent motion, "
    "cinematic live-action texture."
)
DEFAULT_SEED = 20260910
DEFAULT_STEPS = 20
REFERENCE_PATH = "inputs/h2b_source_43d29d07b5d0b4a2.png"
REFERENCE_SHA256 = "43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E"

BASELINE_WIDTH = 608
BASELINE_HEIGHT = 352
BASELINE_DURATION = 5.0
BASELINE_FRAMES = 124
CANDIDATE_DURATION = 15.0
CANDIDATE_WIDTH = 736
CANDIDATE_HEIGHT = 416
FPS = 24

VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv"}


class GenerationError(RuntimeError):
    """The Native generation did not complete with a usable output."""


def _json_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Mapping[str, Any] | None = None,
    timeout: float = 30.0,
) -> Any:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise GenerationError(f"Native HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise GenerationError("Native backend is unavailable.") from exc
    try:
        return json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationError("Native backend returned invalid JSON.") from exc


def _find_process_id(port: int) -> int | None:
    if psutil is None:
        return None
    try:
        connections = psutil.net_connections(kind="tcp")
    except (psutil.Error, OSError):
        return None
    for connection in connections:
        local = connection.laddr
        local_port = getattr(local, "port", None)
        if local_port is None and isinstance(local, tuple) and len(local) >= 2:
            local_port = local[1]
        if connection.status == psutil.CONN_LISTEN and local_port == port:
            return connection.pid if isinstance(connection.pid, int) else None
    return None


def _nvidia_sample() -> dict[str, Any] | None:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), None)
    if not line:
        return None
    fields = [field.strip() for field in line.split(",")]
    if len(fields) != 4:
        return None
    try:
        return {
            "name": fields[0],
            "total_mib": float(fields[1]),
            "used_mib": float(fields[2]),
            "free_mib": float(fields[3]),
        }
    except ValueError:
        return None


class Telemetry:
    """Sample one consistent GPU/process method for every matrix row."""

    def __init__(self, native_port: int) -> None:
        self.native_pid = _find_process_id(native_port)
        self.samples = 0
        self.peak_vram_used_mib: float | None = None
        self.minimum_vram_free_mib: float | None = None
        self.peak_working_set_bytes: int | None = None
        self.gpu_name: str | None = None
        self.vram_total_mib: float | None = None
        self.system_ram_total_bytes: int | None = None
        if psutil is not None:
            try:
                self.system_ram_total_bytes = int(psutil.virtual_memory().total)
            except (psutil.Error, OSError):
                pass

    def sample(self) -> None:
        self.samples += 1
        gpu = _nvidia_sample()
        if gpu is not None:
            self.gpu_name = gpu["name"]
            self.vram_total_mib = gpu["total_mib"]
            used = gpu["used_mib"]
            free = gpu["free_mib"]
            self.peak_vram_used_mib = (
                used if self.peak_vram_used_mib is None else max(self.peak_vram_used_mib, used)
            )
            self.minimum_vram_free_mib = (
                free
                if self.minimum_vram_free_mib is None
                else min(self.minimum_vram_free_mib, free)
            )
        if psutil is not None and self.native_pid is not None:
            try:
                rss = int(psutil.Process(self.native_pid).memory_info().rss)
            except (psutil.Error, OSError):
                rss = None
            if rss is not None:
                self.peak_working_set_bytes = (
                    rss
                    if self.peak_working_set_bytes is None
                    else max(self.peak_working_set_bytes, rss)
                )

    def public(self) -> dict[str, Any]:
        return {
            "gpu": self.gpu_name,
            "vram_total_mib": self.vram_total_mib,
            "peak_observed_vram_used_mib": self.peak_vram_used_mib,
            "minimum_observed_vram_free_mib": self.minimum_vram_free_mib,
            "system_ram_total_bytes": self.system_ram_total_bytes,
            "native_process_id": self.native_pid,
            "peak_native_working_set_bytes": self.peak_working_set_bytes,
            "sample_count": self.samples,
        }


def _history_status(entry: Mapping[str, Any] | None) -> str:
    if not isinstance(entry, Mapping):
        return ""
    status = entry.get("status")
    if isinstance(status, Mapping):
        status_str = status.get("status_str")
        if isinstance(status_str, str):
            return status_str.lower()
        if status.get("completed") is True:
            return "completed"
    return ""


def _is_completed(entry: Mapping[str, Any] | None) -> bool:
    return _history_status(entry) in {"completed", "success", "successful"}


def _is_failed(entry: Mapping[str, Any] | None) -> bool:
    return _history_status(entry) in {"error", "failed", "failure"}


def _history_error(entry: Mapping[str, Any] | None) -> str:
    if isinstance(entry, Mapping):
        status = entry.get("status")
        if isinstance(status, Mapping):
            messages = status.get("messages")
            if messages:
                return json.dumps(messages, ensure_ascii=False)[:2400]
            if status.get("status_str"):
                return str(status["status_str"])
    return "Native H3 generation failed."


def _iter_media(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, Mapping):
        filename = value.get("filename")
        if isinstance(filename, str) and Path(filename).suffix.lower() in VIDEO_SUFFIXES:
            yield dict(value)
        for child in value.values():
            yield from _iter_media(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _iter_media(child)


def _safe_output_path(output_root: Path, record: Mapping[str, Any]) -> Path:
    filename = record.get("filename")
    subfolder = record.get("subfolder") or ""
    if not isinstance(filename, str) or not isinstance(subfolder, str):
        raise GenerationError("Native returned an invalid video output record.")
    path = (output_root / subfolder / filename).resolve()
    try:
        path.relative_to(output_root.resolve())
    except ValueError as exc:
        raise GenerationError("Native output escaped the H3 output directory.") from exc
    if path.suffix.lower() not in VIDEO_SUFFIXES or not path.is_file():
        raise GenerationError("Native video output is unavailable.")
    return path


def _parse_rate(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            denominator_value = float(denominator)
            return float(numerator) / denominator_value if denominator_value else None
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def _ffprobe(path: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,avg_frame_rate,nb_frames,nb_read_frames:format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GenerationError("ffprobe could not inspect the Native output.") from exc
    if result.returncode != 0:
        raise GenerationError(f"ffprobe rejected the Native output: {result.stderr[:1000]}")
    try:
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        format_data = payload.get("format") or {}
        frames_value = stream.get("nb_read_frames") or stream.get("nb_frames")
        frames = int(frames_value) if frames_value not in (None, "N/A") else None
        duration = float(format_data["duration"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GenerationError("ffprobe returned incomplete video metadata.") from exc
    fps = _parse_rate(stream.get("avg_frame_rate"))
    if fps is None:
        raise GenerationError("ffprobe returned an invalid video frame rate.")
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "encoded_frame_count": frames,
        "fps": fps,
        "duration_seconds": duration,
    }


def _request_for(case: Mapping[str, Any]) -> H3Request:
    references = None
    if case["route"] == "native_i2v":
        references = H3ReferenceSlots(
            start_frame=H3Reference("a" * 32, REFERENCE_ROLE_START_FRAME),
            end_frame=H3Reference("b" * 32, REFERENCE_ROLE_END_FRAME),
        )
    return H3Request(
        prompt=DEFAULT_PROMPT,
        width=int(case["width"]),
        height=int(case["height"]),
        duration=float(case["duration"]),
        seed=DEFAULT_SEED,
        steps=DEFAULT_STEPS,
        references=references,
    )


def _graph_for(case: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    request = _request_for(case)
    if case["route"] == "native_t2v":
        return compile_t2v(request)
    return compile_fl2va_workflow(
        request,
        {
            REFERENCE_ROLE_START_FRAME: REFERENCE_PATH,
            REFERENCE_ROLE_END_FRAME: REFERENCE_PATH,
        },
    )


def _case(
    case_id: str,
    axis: str,
    route: str,
    width: int,
    height: int,
    duration: float,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "axis": axis,
        "route": route,
        "width": width,
        "height": height,
        "duration": duration,
    }


def _run_case(args: argparse.Namespace, case: Mapping[str, Any]) -> dict[str, Any]:
    width = int(case["width"])
    height = int(case["height"])
    duration = float(case["duration"])
    native_length = duration_to_frames(duration)
    telemetry = Telemetry(args.native_port)
    telemetry.sample()
    started = time.monotonic()
    prompt_id = None
    entry: Mapping[str, Any] | None = None
    error = None
    try:
        response = _json_request(
            args.comfy_url,
            "/prompt",
            method="POST",
            payload={
                "prompt": _graph_for(case),
                "client_id": f"tegaki-vp1-{case['case_id']}",
            },
            timeout=30,
        )
        prompt_id = response.get("prompt_id") if isinstance(response, Mapping) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            node_errors = response.get("node_errors") if isinstance(response, Mapping) else None
            raise GenerationError(f"Native did not return a prompt id: {node_errors or response}")

        deadline = time.monotonic() + float(args.timeout)
        while time.monotonic() < deadline:
            telemetry.sample()
            history = _json_request(
                args.comfy_url,
                f"/history/{prompt_id}",
                timeout=20,
            )
            candidate = history.get(prompt_id) if isinstance(history, Mapping) else None
            if isinstance(candidate, Mapping):
                if _is_completed(candidate) or _is_failed(candidate):
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
        output_path = _safe_output_path(Path(args.output_root), records[0])
        media = _ffprobe(output_path)
        expected_native_duration = native_length / FPS
        if (media["width"], media["height"]) != (width, height):
            raise GenerationError(
                f"Native output dimensions {media['width']}x{media['height']} "
                f"do not match requested {width}x{height}."
            )
        if media["encoded_frame_count"] != native_length:
            raise GenerationError(
                f"Native encoded {media['encoded_frame_count']} frames; "
                f"expected {native_length}."
            )
        if abs(media["fps"] - FPS) > 0.01:
            raise GenerationError(f"Native output fps {media['fps']} is not {FPS}.")
        if abs(media["duration_seconds"] - expected_native_duration) > 0.15:
            raise GenerationError(
                f"Native ffprobe duration {media['duration_seconds']:.3f}s is not "
                f"near {expected_native_duration:.3f}s."
            )
        return {
            "status": "PASS",
            "case_id": case["case_id"],
            "axis": case["axis"],
            "route": case["route"],
            "requested": {
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "steps": DEFAULT_STEPS,
                "seed": DEFAULT_SEED,
            },
            "native": {
                "length_frames": native_length,
                "duration_seconds": expected_native_duration,
                "fps": FPS,
            },
            "prompt_id": prompt_id,
            "output": {
                "path": str(output_path),
                "filename": records[0].get("filename"),
                "subfolder": records[0].get("subfolder") or "",
                "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest().upper(),
                "bytes": output_path.stat().st_size,
                "ffprobe": media,
            },
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "telemetry": telemetry.public(),
            "oom_count": 0,
            "retry_count": 0,
        }
    except GenerationError as exc:
        error = str(exc)
        lower = error.lower()
        oom_count = 1 if "out of memory" in lower or "cuda oom" in lower else 0
        return {
            "status": "FAIL",
            "classification": "BLOCKED" if oom_count else "FAILED",
            "case_id": case["case_id"],
            "axis": case["axis"],
            "route": case["route"],
            "requested": {
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "steps": DEFAULT_STEPS,
                "seed": DEFAULT_SEED,
            },
            "native": {
                "length_frames": native_length,
                "duration_seconds": native_length / FPS,
                "fps": FPS,
            },
            "prompt_id": prompt_id,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "error": error,
            "telemetry": telemetry.public(),
            "oom_count": oom_count,
            "retry_count": 0,
        }


def _skipped(case: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "status": "SKIPPED",
        "classification": "BLOCKED",
        "case_id": case["case_id"],
        "axis": case["axis"],
        "route": case["route"],
        "requested": {
            "width": int(case["width"]),
            "height": int(case["height"]),
            "duration_seconds": float(case["duration"]),
            "steps": DEFAULT_STEPS,
            "seed": DEFAULT_SEED,
        },
        "native": {
            "length_frames": duration_to_frames(float(case["duration"])),
            "duration_seconds": duration_to_frames(float(case["duration"])) / FPS,
            "fps": FPS,
        },
        "reason": reason,
        "oom_count": 0,
        "retry_count": 0,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_root = Path(args.output_root).resolve()
    reference = (output_root / Path(REFERENCE_PATH)).resolve()
    if not reference.is_file():
        raise GenerationError(f"The approved Start/End reference is missing: {reference}")
    if hashlib.sha256(reference.read_bytes()).hexdigest().upper() != REFERENCE_SHA256:
        raise GenerationError("The approved Start/End reference SHA-256 does not match.")

    baseline_t2v = _case("baseline-t2v", "baseline", "native_t2v", BASELINE_WIDTH, BASELINE_HEIGHT, BASELINE_DURATION)
    baseline_fl2va = _case("baseline-fl2va", "baseline", "native_i2v", BASELINE_WIDTH, BASELINE_HEIGHT, BASELINE_DURATION)
    duration_t2v = _case("duration-15s-t2v", "duration", "native_t2v", BASELINE_WIDTH, BASELINE_HEIGHT, CANDIDATE_DURATION)
    duration_fl2va = _case("duration-15s-fl2va", "duration", "native_i2v", BASELINE_WIDTH, BASELINE_HEIGHT, CANDIDATE_DURATION)
    resolution_t2v = _case("resolution-736x416-t2v", "resolution", "native_t2v", CANDIDATE_WIDTH, CANDIDATE_HEIGHT, BASELINE_DURATION)
    resolution_fl2va = _case("resolution-736x416-fl2va", "resolution", "native_i2v", CANDIDATE_WIDTH, CANDIDATE_HEIGHT, BASELINE_DURATION)

    results: list[dict[str, Any]] = []
    first = _run_case(args, baseline_t2v)
    results.append(first)
    if first["status"] != "PASS":
        results.extend(
            [
                _skipped(baseline_fl2va, "Baseline T2V did not pass; matrix stopped."),
                _skipped(duration_t2v, "Baseline T2V did not pass; candidate matrix stopped."),
                _skipped(duration_fl2va, "Duration Stage 1 was not run."),
                _skipped(resolution_t2v, "Baseline T2V did not pass; candidate matrix stopped."),
                _skipped(resolution_fl2va, "Resolution Stage 1 was not run."),
            ]
        )
    else:
        baseline_second = _run_case(args, baseline_fl2va)
        results.append(baseline_second)
        duration_first = _run_case(args, duration_t2v)
        results.append(duration_first)
        results.append(
            _run_case(args, duration_fl2va)
            if duration_first["status"] == "PASS"
            else _skipped(duration_fl2va, "Duration Stage 1 did not pass; Start+End Stage 2 was not run.")
        )
        resolution_first = _run_case(args, resolution_t2v)
        results.append(resolution_first)
        results.append(
            _run_case(args, resolution_fl2va)
            if resolution_first["status"] == "PASS"
            else _skipped(resolution_fl2va, "Resolution Stage 1 did not pass; Start+End Stage 2 was not run.")
        )

    candidate_status = {}
    for axis in ("duration", "resolution"):
        axis_rows = [row for row in results if row["axis"] == axis]
        candidate_status[axis] = (
            "UI VERIFIED"
            if len(axis_rows) == 2 and all(row["status"] == "PASS" for row in axis_rows)
            else "HEAVY/NOT UI ENABLED"
            if any(row["status"] == "PASS" for row in axis_rows)
            else "BLOCKED"
        )
    return {
        "status": "PASS" if results and all(row["status"] in {"PASS", "SKIPPED"} for row in results) else "PARTIAL",
        "card": "VP1",
        "target": "NVIDIA GeForce RTX 4070 12GB / 64GB RAM",
        "comfy_url": args.comfy_url,
        "baseline": {
            "resolution": f"{BASELINE_WIDTH}x{BASELINE_HEIGHT}",
            "duration_seconds_requested": BASELINE_DURATION,
            "native_length_frames": BASELINE_FRAMES,
            "fps": FPS,
            "steps": DEFAULT_STEPS,
        },
        "candidates": {
            "duration": {
                "value_seconds": CANDIDATE_DURATION,
                "resolution": f"{BASELINE_WIDTH}x{BASELINE_HEIGHT}",
                "native_length_frames": duration_to_frames(CANDIDATE_DURATION),
                "status": candidate_status["duration"],
            },
            "resolution": {
                "value": f"{CANDIDATE_WIDTH}x{CANDIDATE_HEIGHT}",
                "duration_seconds": BASELINE_DURATION,
                "native_length_frames": BASELINE_FRAMES,
                "status": candidate_status["resolution"],
            },
        },
        "reference": {
            "path": REFERENCE_PATH,
            "sha256": REFERENCE_SHA256,
            "used_for": "Start+End FL2VA baseline and candidate Stage 2",
        },
        "runs": results,
        "model_changes": "NONE",
        "dependency_changes": "NONE",
        "shared_comfyui_changes": "NONE",
        "manga_changes": "NONE",
        "browser_ui": "NOT RUN BY THIS NATIVE MATRIX",
        "owner_acceptance": "PENDING",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the VP1 Native H3 video envelope matrix.")
    parser.add_argument("--comfy-url", default=DEFAULT_COMFY_URL)
    parser.add_argument("--native-port", type=int, default=DEFAULT_NATIVE_PORT)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
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
