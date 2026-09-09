"""Run one bounded H2A Native H3 still feasibility generation.

This is an evaluation entry, not a production Still UI.  It submits the
H2A semantic adapter's materialized graph to an already-running local Native
ComfyUI instance and records enough output/telemetry to close the feasibility
card without adding a second runtime.
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
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    import psutil
except ImportError:  # pragma: no cover - the runner records unavailable telemetry
    psutil = None

from PIL import Image

from h3.adapters.native_still import (
    H3StillRequest,
    PACKET_FRAMES,
    ROUTE_STILL,
    SELECTED_FRAME_INDEX,
    compile_workflow,
    workflow_metadata,
)


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT = (
    "A small orange robot stands alone on a pale blue studio background, "
    "clean illustrative anime style, centered composition, soft daylight."
)
DEFAULT_SEED = 20260910
DEFAULT_OUTPUT_ROOT = PORTABLE_ROOT / "output" / "h3"


class GenerationError(RuntimeError):
    """The Native generation did not complete with a usable output."""


def _json_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Mapping[str, Any] | None = None,
    timeout: float = 20.0,
) -> Any:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url.rstrip('/')}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
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
    def __init__(self, native_port: int) -> None:
        self.native_port = native_port
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
                used
                if self.peak_vram_used_mib is None
                else max(self.peak_vram_used_mib, used)
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


def _history_error(entry: Mapping[str, Any]) -> str:
    status = entry.get("status")
    if isinstance(status, Mapping):
        messages = status.get("messages")
        if messages:
            return json.dumps(messages, ensure_ascii=False)[:2000]
        if status.get("status_str"):
            return str(status["status_str"])
    return "Native H3 still generation failed."


def _iter_image_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, Mapping):
        filename = value.get("filename")
        if isinstance(filename, str) and Path(filename).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            yield dict(value)
        for child in value.values():
            yield from _iter_image_records(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _iter_image_records(child)


def _completed(entry: Mapping[str, Any]) -> bool:
    status = entry.get("status")
    if isinstance(status, Mapping):
        status_str = status.get("status_str")
        if status_str in {"error", "failed"}:
            raise GenerationError(_history_error(entry))
        if status.get("completed") or status_str in {"success", "completed"}:
            return True
    return bool(list(_iter_image_records(entry.get("outputs"))))


def _safe_output_path(output_root: Path, record: Mapping[str, Any]) -> Path:
    filename = record.get("filename")
    subfolder = record.get("subfolder") or ""
    if not isinstance(filename, str) or not isinstance(subfolder, str):
        raise GenerationError("Native returned an invalid image record.")
    candidate = (output_root / subfolder / filename).resolve()
    try:
        candidate.relative_to(output_root.resolve())
    except ValueError as exc:
        raise GenerationError("Native image output escaped the H3 output directory.") from exc
    if not candidate.is_file():
        raise GenerationError(f"Native image output is unavailable: {candidate}")
    return candidate


def run(args: argparse.Namespace) -> dict[str, Any]:
    request = H3StillRequest(prompt=args.prompt, seed=args.seed, steps=args.steps)
    graph = compile_workflow(request)
    telemetry = Telemetry(args.native_port)
    telemetry.sample()
    started = time.monotonic()
    response = _json_request(
        args.comfy_url,
        "/prompt",
        method="POST",
        payload={"prompt": graph, "client_id": "tegaki-h2a-still-feasibility"},
        timeout=30,
    )
    prompt_id = response.get("prompt_id") if isinstance(response, Mapping) else None
    if not isinstance(prompt_id, str) or not prompt_id:
        if isinstance(response, Mapping) and response.get("node_errors"):
            raise GenerationError(f"Native rejected H2A workflow: {response['node_errors']}")
        raise GenerationError("Native did not return a prompt id.")

    deadline = time.monotonic() + args.timeout
    entry: Mapping[str, Any] | None = None
    while time.monotonic() < deadline:
        telemetry.sample()
        history = _json_request(
            args.comfy_url,
            f"/history/{quote(prompt_id, safe='')}",
            timeout=15,
        )
        candidate = history.get(prompt_id) if isinstance(history, Mapping) else None
        if isinstance(candidate, Mapping) and _completed(candidate):
            entry = candidate
            break
        time.sleep(args.poll_seconds)
    telemetry.sample()
    if entry is None:
        raise GenerationError(f"Native still generation timed out after {args.timeout:g}s.")

    records = list(_iter_image_records(entry.get("outputs")))
    if not records:
        raise GenerationError("Native completed without an image output.")
    record = records[0]
    output_root = Path(args.output_root).resolve()
    output_path = _safe_output_path(output_root, record)
    with Image.open(output_path) as image:
        dimensions = [int(image.width), int(image.height)]
        output_format = image.format
        image.load()
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest().upper()
    elapsed = round(time.monotonic() - started, 2)
    result = {
        "route": ROUTE_STILL,
        "workflow": "workflows/h3/H2A_NATIVE_STILL_BASE.json",
        "workflow_schema": "tegaki.h3.h2a.native-still/v1",
        "prompt_id": prompt_id,
        "prompt": request.prompt,
        "resolution": f"{request.width}x{request.height}",
        "packet_frames": PACKET_FRAMES,
        "selected_frame_index": SELECTED_FRAME_INDEX,
        "seed": request.seed,
        "steps": request.steps,
        "elapsed_seconds": elapsed,
        "output": {
            "path": str(output_path),
            "filename": record.get("filename"),
            "subfolder": record.get("subfolder") or "",
            "format": output_format,
            "dimensions": dimensions,
            "bytes": output_path.stat().st_size,
            "sha256": digest,
        },
        "telemetry": telemetry.public(),
        "oom_count": 0,
        "retry_count": 0,
        "model_changes": "NONE",
        "dependency_changes": "NONE",
        "shared_comfyui_changes": "NONE",
        "manga_changes": "NONE",
        "metadata": workflow_metadata(),
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the H2A Native H3 still feasibility slice.")
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
    print(json.dumps({"status": "PASS", **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
