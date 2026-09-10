"""Small local HTTP server for the H3 Native T2V / Start-End Frame skin.

The server owns only the local UI/session boundary. ComfyUI remains the source
of truth for queue execution, history, and generated output. No project DB is
created and no candidate custom node is loaded.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default as email_default
from io import BytesIO
import json
import mimetypes
import os
from pathlib import Path
import random
import re
import shutil
import sys
import subprocess
import threading
import time
from typing import Any, Iterable, Mapping
import warnings
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image, UnidentifiedImageError


PORTABLE_ROOT = Path(__file__).resolve().parents[2]
if str(PORTABLE_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTABLE_ROOT))

from h3.adapters.native_t2v import (  # noqa: E402
    H3Reference,
    H3Request,
    REFERENCE_ROLE_END_FRAME,
    REFERENCE_ROLES,
    REFERENCE_ROLE_START_FRAME,
    RequestValidationError,
    ROUTE_I2V,
    ROUTE_T2V,
    WorkflowIncompatibleError,
    resolve_route,
    reference_route_label,
    validate_request,
    video_option_metadata,
    workflow_metadata,
)
from h3.adapters.native_t2v import compile_workflow as compile_t2v  # noqa: E402
from h3.adapters.native_i2v import (  # noqa: E402
    compile_workflow as compile_i2v,
    compile_fl2va_workflow,
    fl2va_workflow_metadata,
    workflow_metadata as i2v_workflow_metadata,
)
from h3.adapters.native_still import (  # noqa: E402
    H3StillRequest,
    ROUTE_STILL,
    compile_workflow as compile_still,
    validate_still_request,
    workflow_metadata as still_workflow_metadata,
)
from h3.adapters.native_source_anchored_still import (  # noqa: E402
    H3SourceAnchorRequest,
    ROUTE_SOURCE_ANCHORED_STILL,
    compile_workflow as compile_source_anchored_still,
    validate_source_anchor_request,
    workflow_metadata as source_anchored_still_workflow_metadata,
)
from h3.adapters.native_ref2va import (  # noqa: E402
    BASELINE_DURATION_SECONDS as REF2VA_DURATION_SECONDS,
    BASELINE_HEIGHT as REF2VA_HEIGHT,
    BASELINE_STEPS as REF2VA_STEPS,
    BASELINE_WIDTH as REF2VA_WIDTH,
    H3Ref2VARequest,
    REF2VA_MODEL,
    RequestValidationError as Ref2VARequestValidationError,
    compile_workflow as compile_ref2va,
    materialize_prompt,
    workflow_metadata as ref2va_workflow_metadata,
)


STATE_LABELS = {
    "READY": "Ready",
    "QUEUED": "Queued",
    "RUNNING": "Running",
    "COMPLETED": "Completed",
    "FAILED": "Failed",
    "CANCELLED": "Cancelled",
    "DISCONNECTED": "Backend disconnected",
}
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv"}
REFERENCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
STILL_SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg"}
STILL_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
REFERENCE_MAX_BYTES = 20 * 1024 * 1024
REFERENCE_MAX_PIXELS = 16_777_216
MULTIPART_OVERHEAD_LIMIT = 512 * 1024
SERVER_ASSET_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
R2V_PICTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
R2V_VIDEO_SUFFIXES = {".mp4"}
R2V_VIDEO_MAX_BYTES = 64 * 1024 * 1024
R2V_ROUTE = "native_ref2va"
R2V_VIDEO_TYPE = "reference"


class BackendError(RuntimeError):
    """A backend request failed or returned an unusable response."""


class BackendRejected(BackendError):
    """ComfyUI rejected a validly shaped request."""


class ReferenceRequestError(RequestValidationError):
    """An uploaded reference failed the H1B input boundary."""

    error_kind = "reference_upload_failed"
    status = HTTPStatus.BAD_REQUEST


class ReferenceTooLargeError(ReferenceRequestError):
    error_kind = "reference_upload_failed"
    status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE


class ReferenceDecodeError(ReferenceRequestError):
    error_kind = "reference_decode_failed"


class ReferenceAssetMissingError(ReferenceRequestError):
    error_kind = "reference_asset_missing"


class StillSourceRequestError(ReferenceRequestError):
    error_kind = "still_source_upload_failed"


class StillSourceTooLargeError(StillSourceRequestError):
    error_kind = "still_source_upload_failed"
    status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE


class StillSourceDecodeError(StillSourceRequestError):
    error_kind = "still_source_decode_failed"


class StillSourceMissingError(StillSourceRequestError):
    error_kind = "still_source_missing"


class ReferenceVideoRequestError(ReferenceRequestError):
    """An experimental Reference Video upload or request failed closed."""

    error_kind = "r2v_request_failed"


class ReferenceVideoTooLargeError(ReferenceVideoRequestError):
    error_kind = "r2v_upload_failed"
    status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE


class ReferenceVideoDecodeError(ReferenceVideoRequestError):
    error_kind = "r2v_decode_failed"


class ReferenceVideoAssetMissingError(ReferenceVideoRequestError):
    error_kind = "r2v_asset_missing"


@dataclass(frozen=True)
class ReferenceAsset:
    reference: H3Reference
    path: Path
    filename: str
    content_type: str
    width: int
    height: int

    def public(self) -> dict[str, Any]:
        return {
            **self.reference.public(),
            "filename": self.filename,
            "content_type": self.content_type,
            "width": self.width,
            "height": self.height,
            "preview_url": f"/api/references/{quote(self.reference.id, safe='')}",
        }


@dataclass(frozen=True)
class StillSourceAsset:
    source_id: str
    path: Path
    filename: str
    content_type: str
    width: int
    height: int

    def public(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "width": self.width,
            "height": self.height,
            "preview_url": f"/api/still/sources/{quote(self.source_id, safe='')}",
        }


@dataclass(frozen=True)
class R2VPictureAsset:
    picture_id: str
    path: Path
    name: str
    filename: str
    content_type: str
    width: int
    height: int

    def public(self) -> dict[str, Any]:
        return {
            "id": self.picture_id,
            "name": self.name,
            "content_type": self.content_type,
            "width": self.width,
            "height": self.height,
            "preview_url": f"/api/r2v/pictures/{quote(self.picture_id, safe='')}",
        }


@dataclass(frozen=True)
class R2VMotionVideoAsset:
    video_id: str
    path: Path
    name: str
    filename: str
    content_type: str
    size_bytes: int
    metadata: dict[str, Any]

    def public(self) -> dict[str, Any]:
        return {
            "id": self.video_id,
            "name": self.name,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            **self.metadata,
            "preview_url": f"/api/r2v/videos/{quote(self.video_id, safe='')}",
        }


@dataclass(frozen=True)
class ReferenceVideoRequest:
    """Browser-facing R2V request retaining original and materialized prompts."""

    prompt: str
    materialized_prompt: str
    picture_id: str
    motion_video_id: str | None
    width: int
    height: int
    duration: float
    seed: int
    steps: int

    def public(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "materialized_prompt": self.materialized_prompt,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "seed": str(self.seed),
            "steps": self.steps,
            "video_type": R2V_VIDEO_TYPE,
            "picture_id": self.picture_id,
            "motion_video_id": self.motion_video_id,
        }


class BackendClient:
    def __init__(self, base_url: str, timeout: float = 8.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = UrlRequest(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout or self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:800]
            except OSError:
                detail = ""
            raise BackendError(
                f"ComfyUI returned HTTP {exc.code}{(': ' + detail) if detail else ''}."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise BackendError("Native backend unavailable.") from exc
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BackendError("Native backend returned invalid JSON.") from exc

    def status(self) -> dict[str, Any]:
        stats = self._request("GET", "/system_stats")
        queue = self._request("GET", "/queue")
        return parse_backend_status(stats, queue)

    def reference_node_available(self) -> bool:
        """Check the exact Native node without loading or hashing model weights."""

        try:
            object_info = self._request("GET", "/object_info", timeout=2.0)
        except BackendError:
            return False
        return isinstance(object_info, Mapping) and "MiniMaxH3ReferenceToVideo" in object_info

    def submit(self, graph: Mapping[str, Any], client_id: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/prompt",
            {"prompt": graph, "client_id": client_id},
            timeout=20.0,
        )
        node_errors = response.get("node_errors") if isinstance(response, dict) else None
        if node_errors:
            raise BackendRejected("Workflow rejected by Native ComfyUI.")
        prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            raise BackendRejected("Workflow rejected: ComfyUI did not return a prompt id.")
        return response

    def queue(self) -> dict[str, Any]:
        return self._request("GET", "/queue")

    def history(self, prompt_id: str) -> dict[str, Any] | None:
        try:
            response = self._request("GET", f"/history/{quote(prompt_id, safe='')}")
        except BackendError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        return response if isinstance(response, dict) else None

    def delete_pending(self, prompt_id: str) -> None:
        self._request("POST", "/queue", {"delete": [prompt_id]})

    def interrupt(self, prompt_id: str) -> None:
        self._request("POST", "/interrupt", {"prompt_id": prompt_id})


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _contains_prompt(entries: Iterable[Any], prompt_id: str) -> bool:
    def walk(value: Any) -> bool:
        if isinstance(value, str):
            return value == prompt_id
        if isinstance(value, Mapping):
            return any(walk(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(walk(item) for item in value)
        return False

    return any(walk(entry) for entry in entries)


def parse_backend_status(stats: Mapping[str, Any], queue: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize Native ComfyUI system/queue payloads for the local skin."""
    devices = stats.get("devices") if isinstance(stats, Mapping) else None
    device = devices[0] if isinstance(devices, list) and devices else {}
    pending = queue.get("queue_pending") if isinstance(queue, Mapping) else None
    running = queue.get("queue_running") if isinstance(queue, Mapping) else None
    pending = pending if isinstance(pending, list) else []
    running = running if isinstance(running, list) else []
    return {
        "state": "READY",
        "label": STATE_LABELS["READY"],
        "queue_count": len(pending) + len(running),
        "running_count": len(running),
        "vram_total": device.get("vram_total") if isinstance(device, Mapping) else None,
        "vram_free": device.get("vram_free") if isinstance(device, Mapping) else None,
        "system_stats": stats,
    }


def map_queue_state(
    queue: Mapping[str, Any],
    prompt_id: str,
    previous_state: str = "QUEUED",
    cancel_requested: bool = False,
) -> str:
    """Map a Native queue snapshot without inventing progress."""
    pending = queue.get("queue_pending") if isinstance(queue, Mapping) else None
    running = queue.get("queue_running") if isinstance(queue, Mapping) else None
    if _contains_prompt(running if isinstance(running, list) else [], prompt_id):
        return "RUNNING"
    if _contains_prompt(pending if isinstance(pending, list) else [], prompt_id):
        return "QUEUED"
    if cancel_requested:
        return "CANCELLED"
    return previous_state if previous_state in {"QUEUED", "RUNNING"} else "QUEUED"


def map_history_state(history_entry: Any, cancel_requested: bool = False) -> str:
    """Map a Native history status to the H1A state vocabulary."""
    if not isinstance(history_entry, Mapping):
        return "FAILED"
    status = history_entry.get("status")
    status_str = status.get("status_str") if isinstance(status, Mapping) else None
    if cancel_requested and status_str in {"error", "failed"}:
        return "CANCELLED"
    if status_str in {"error", "failed"}:
        return "FAILED"
    if isinstance(status, Mapping) and status.get("completed"):
        return "COMPLETED"
    return "RUNNING"


def _iter_media(
    value: Any,
    suffixes: set[str] = VIDEO_SUFFIXES,
) -> Iterable[dict[str, Any]]:
    if isinstance(value, Mapping):
        filename = value.get("filename")
        if isinstance(filename, str) and Path(filename).suffix.lower() in suffixes:
            yield dict(value)
        for child in value.values():
            yield from _iter_media(child, suffixes)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _iter_media(child, suffixes)


def _error_text(history_entry: Mapping[str, Any]) -> str:
    status = history_entry.get("status")
    if isinstance(status, Mapping):
        messages = status.get("messages")
        if messages:
            text = json.dumps(messages, ensure_ascii=False)
            return text[:1200]
        status_str = status.get("status_str")
        if status_str:
            return str(status_str)
    return "Native ComfyUI job failed."


@dataclass
class Job:
    job_id: str
    request: H3Request | H3StillRequest | H3SourceAnchorRequest | ReferenceVideoRequest
    created_at: str
    created_epoch: float
    route: str = ROUTE_T2V
    media_kind: str = "video"
    video_type: str = "standard"
    reference: dict[str, Any] | None = None
    references: dict[str, dict[str, Any] | None] | None = None
    still_source: dict[str, Any] | None = None
    reference_video: dict[str, Any] | None = None
    prompt_id: str | None = None
    state: str = "QUEUED"
    error: str | None = None
    backend_error: str | None = None
    cancel_requested: bool = False
    completed_at: str | None = None
    completed_epoch: float | None = None
    output: dict[str, Any] | None = None
    media_path: Path | None = None

    def elapsed_seconds(self) -> float:
        end = self.completed_epoch or time.time()
        return round(max(0.0, end - self.created_epoch), 2)

    def public(self) -> dict[str, Any]:
        media_url = None
        if self.media_path:
            media_endpoint = "image" if self.media_kind == "still" else "video"
            media_url = f"/api/jobs/{quote(self.job_id, safe='')}/{media_endpoint}"
        video_url = media_url if self.media_kind == "video" else None
        image_url = media_url if self.media_kind == "still" else None
        references = self.references or {
            REFERENCE_ROLE_START_FRAME: None,
            REFERENCE_ROLE_END_FRAME: None,
        }
        has_start_frame = references.get(REFERENCE_ROLE_START_FRAME) is not None
        has_end_frame = references.get(REFERENCE_ROLE_END_FRAME) is not None
        if self.media_kind == "still":
            route_label = "Source Image" if self.still_source else "Text only"
        elif self.video_type == R2V_VIDEO_TYPE:
            route_label = (
                "Reference · Picture + Motion"
                if self.reference_video and self.reference_video.get("motion_video")
                else "Reference · Picture"
            )
        else:
            route_label = reference_route_label(self.request.references)
        request = self.request.public()
        if self.media_kind == "still":
            request = {
                **request,
                "source_id": self.still_source.get("id") if self.still_source else None,
            }
        return {
            "job_id": self.job_id,
            "prompt_id": self.prompt_id,
            "state": self.state,
            "label": STATE_LABELS.get(self.state, self.state),
            "route": self.route,
            "media_kind": self.media_kind,
            "video_type": self.video_type if self.media_kind == "video" else None,
            "route_label": route_label,
            "reference_used": self.media_kind == "video" and (
                self.video_type == R2V_VIDEO_TYPE or has_start_frame or has_end_frame
            ),
            "reference": self.reference,
            "references": references,
            "reference_video": self.reference_video,
            "has_start_frame": has_start_frame,
            "has_end_frame": has_end_frame,
            "source": self.still_source,
            "request": request,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "elapsed_seconds": self.elapsed_seconds(),
            "error": self.error or self.backend_error,
            "progress": None,
            "output": self.output,
            "video_url": video_url,
            "image_url": image_url,
            "thumbnail_url": video_url or image_url,
            "cancel_available": self.state in {"QUEUED", "RUNNING"},
        }


class H1ASession:
    def __init__(self, backend_url: str, output_root: Path):
        self.backend = BackendClient(backend_url)
        self.output_root = output_root.resolve()
        self.input_root = (self.output_root / "inputs").resolve()
        self.input_root.mkdir(parents=True, exist_ok=True)
        self.client_id = f"tegaki-h1a-{os.getpid()}-{uuid_token()}"
        self.jobs: OrderedDict[str, Job] = OrderedDict()
        self.references: dict[str, ReferenceAsset] = {}
        self.still_sources: dict[str, StillSourceAsset] = {}
        self.r2v_pictures: dict[str, R2VPictureAsset] = {}
        self.r2v_motion_videos: dict[str, R2VMotionVideoAsset] = {}
        self.lock = threading.RLock()

    def upload_reference(
        self,
        filename: str,
        body: bytes,
        role: str = REFERENCE_ROLE_START_FRAME,
    ) -> ReferenceAsset:
        if role not in REFERENCE_ROLES:
            raise ReferenceRequestError("Reference slot is unsupported.")
        suffix, actual_format, width, height, content_type = _validate_image_upload(
            filename,
            body,
            suffixes=REFERENCE_SUFFIXES,
            label="Reference",
            request_error=ReferenceRequestError,
            too_large_error=ReferenceTooLargeError,
            decode_error=ReferenceDecodeError,
        )

        reference_id = uuid_token()
        safe_filename = f"{reference_id}{suffix}"
        path = (self.input_root / safe_filename).resolve()
        try:
            path.relative_to(self.input_root)
            with path.open("xb") as handle:
                handle.write(body)
        except OSError as exc:
            raise ReferenceRequestError("Reference upload could not be stored.") from exc

        asset = ReferenceAsset(
            reference=H3Reference(reference_id, role),
            path=path,
            filename=safe_filename,
            content_type=content_type,
            width=width,
            height=height,
        )
        with self.lock:
            self.references[reference_id] = asset
        return asset

    def upload_still_source(self, filename: str, body: bytes) -> StillSourceAsset:
        suffix, _actual_format, width, height, content_type = _validate_image_upload(
            filename,
            body,
            suffixes=STILL_SOURCE_SUFFIXES,
            label="Still source",
            request_error=StillSourceRequestError,
            too_large_error=StillSourceTooLargeError,
            decode_error=StillSourceDecodeError,
        )
        source_id = uuid_token()
        safe_filename = f"{source_id}{suffix}"
        path = (self.input_root / safe_filename).resolve()
        try:
            path.relative_to(self.input_root)
            with path.open("xb") as handle:
                handle.write(body)
        except OSError as exc:
            raise StillSourceRequestError("Still source could not be stored.") from exc

        asset = StillSourceAsset(
            source_id=source_id,
            path=path,
            filename=safe_filename,
            content_type=content_type,
            width=width,
            height=height,
        )
        with self.lock:
            self.still_sources[source_id] = asset
        return asset

    def get_reference(self, reference_id: str) -> ReferenceAsset | None:
        with self.lock:
            return self.references.get(reference_id)

    def get_still_source(self, source_id: str) -> StillSourceAsset | None:
        with self.lock:
            return self.still_sources.get(source_id)

    def reference_video_capability(self) -> dict[str, Any]:
        """Return the small UI capability record for Experimental Reference."""

        model_available = _configured_ref2va_model() is not None
        node_checker = getattr(self.backend, "reference_node_available", None)
        node_available = bool(node_checker()) if callable(node_checker) else True
        return {
            "enabled": model_available and node_available,
            "native_node": "MiniMaxH3ReferenceToVideo",
            "model": REF2VA_MODEL,
        }

    def upload_r2v_picture(self, filename: str, body: bytes) -> R2VPictureAsset:
        suffix, _actual_format, width, height, content_type = _validate_image_upload(
            filename,
            body,
            suffixes=R2V_PICTURE_SUFFIXES,
            label="Character Image",
            request_error=ReferenceVideoRequestError,
            too_large_error=ReferenceVideoTooLargeError,
            decode_error=ReferenceVideoDecodeError,
        )
        picture_id = uuid_token()
        safe_filename = f"{picture_id}{suffix}"
        path = (self.input_root / safe_filename).resolve()
        try:
            path.relative_to(self.input_root)
            with path.open("xb") as handle:
                handle.write(body)
        except OSError as exc:
            raise ReferenceVideoRequestError("Character Image could not be stored.") from exc
        asset = R2VPictureAsset(
            picture_id=picture_id,
            path=path,
            name=Path(filename).name,
            filename=safe_filename,
            content_type=content_type,
            width=width,
            height=height,
        )
        with self.lock:
            self.r2v_pictures[picture_id] = asset
        return asset

    def upload_r2v_motion_video(self, filename: str, body: bytes) -> R2VMotionVideoAsset:
        if not isinstance(body, bytes) or not body:
            raise ReferenceVideoRequestError("Motion Video upload is empty.")
        if len(body) > R2V_VIDEO_MAX_BYTES:
            raise ReferenceVideoTooLargeError(
                f"Motion Video must be {R2V_VIDEO_MAX_BYTES // (1024 * 1024)} MB or smaller."
            )
        if not isinstance(filename, str) or not filename.strip():
            raise ReferenceVideoRequestError("Motion Video filename is required.")
        filename = filename.strip()
        if (
            filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            or ":" in filename
            or Path(filename).is_absolute()
        ):
            raise ReferenceVideoRequestError("Motion Video filename is unsafe.")
        suffix = Path(filename).suffix.lower()
        if suffix not in R2V_VIDEO_SUFFIXES:
            raise ReferenceVideoRequestError("Motion Video must be an MP4 file.")

        video_id = uuid_token()
        safe_filename = f"{video_id}.mp4"
        path = (self.input_root / safe_filename).resolve()
        try:
            path.relative_to(self.input_root)
            with path.open("xb") as handle:
                handle.write(body)
            metadata = _probe_video_file(path)
        except ReferenceVideoRequestError:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        except OSError as exc:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            raise ReferenceVideoRequestError("Motion Video could not be stored.") from exc
        asset = R2VMotionVideoAsset(
            video_id=video_id,
            path=path,
            name=Path(filename).name,
            filename=safe_filename,
            content_type="video/mp4",
            size_bytes=len(body),
            metadata=metadata,
        )
        with self.lock:
            self.r2v_motion_videos[video_id] = asset
        return asset

    def get_r2v_picture(self, picture_id: str) -> R2VPictureAsset | None:
        with self.lock:
            return self.r2v_pictures.get(picture_id)

    def get_r2v_motion_video(self, video_id: str) -> R2VMotionVideoAsset | None:
        with self.lock:
            return self.r2v_motion_videos.get(video_id)

    def submit_reference_video(self, payload: Mapping[str, Any]) -> Job:
        """Submit the bounded one-picture/optional-motion Ref2VA route."""

        if not isinstance(payload, Mapping):
            raise RequestValidationError("Reference Video request must be a JSON object.")
        forbidden = {
            "picture_path",
            "video_path",
            "source_path",
            "reference",
            "references",
            "source_id",
        }
        if forbidden.intersection(payload):
            raise RequestValidationError(
                "Reference Video accepts server-issued picture_id and motion_video_id only."
            )
        allowed = {
            "video_type",
            "prompt",
            "picture_id",
            "motion_video_id",
            "width",
            "height",
            "duration",
            "steps",
            "seed",
        }
        if set(payload).difference(allowed):
            raise RequestValidationError("Reference Video request contains unsupported fields.")
        if payload.get("video_type", R2V_VIDEO_TYPE) != R2V_VIDEO_TYPE:
            raise RequestValidationError("Reference Video requests must use video_type=reference.")

        picture_id = payload.get("picture_id")
        if not isinstance(picture_id, str) or not SERVER_ASSET_ID_PATTERN.fullmatch(picture_id):
            raise RequestValidationError("Character Image id is invalid.")
        picture = self.get_r2v_picture(picture_id)
        if picture is None or not picture.path.is_file():
            raise ReferenceVideoAssetMissingError("Character Image asset is missing.")

        motion_video_id = payload.get("motion_video_id")
        if motion_video_id in (None, ""):
            motion_video_id = None
            motion_video = None
        else:
            if not isinstance(motion_video_id, str) or not SERVER_ASSET_ID_PATTERN.fullmatch(motion_video_id):
                raise RequestValidationError("Motion Video id is invalid.")
            motion_video = self.get_r2v_motion_video(motion_video_id)
            if motion_video is None or not motion_video.path.is_file():
                raise ReferenceVideoAssetMissingError("Motion Video asset is missing.")

        try:
            user_prompt, materialized = materialize_prompt(
                payload.get("prompt"),
                has_video=motion_video is not None,
            )
        except Ref2VARequestValidationError as exc:
            raise RequestValidationError(str(exc)) from exc
        seed_value = payload.get("seed")
        if seed_value in (None, "", "random"):
            seed_value = random.SystemRandom().randint(0, (1 << 63) - 1)
        elif isinstance(seed_value, bool):
            raise RequestValidationError("Seed must be an integer between 0 and 2^63-1.")
        elif isinstance(seed_value, int):
            pass
        elif isinstance(seed_value, str) and re.fullmatch(r"\d+", seed_value.strip()):
            seed_value = int(seed_value.strip())
        else:
            raise RequestValidationError("Seed must be an integer between 0 and 2^63-1.")
        if not 0 <= seed_value <= (1 << 63) - 1:
            raise RequestValidationError("Seed must be an integer between 0 and 2^63-1.")
        native_payload = {
            "prompt": materialized,
            "picture_path": f"inputs/{picture.filename}",
            "video_path": f"inputs/{motion_video.filename}" if motion_video else None,
            "width": payload.get("width", REF2VA_WIDTH),
            "height": payload.get("height", REF2VA_HEIGHT),
            "duration_seconds": payload.get("duration", REF2VA_DURATION_SECONDS),
            "seed": seed_value,
            "steps": payload.get("steps", REF2VA_STEPS),
            "output_prefix": "video/vp2b_r2v_reference",
        }
        try:
            native_request = H3Ref2VARequest(**native_payload)
            graph = compile_ref2va(native_request)
        except Ref2VARequestValidationError as exc:
            raise RequestValidationError(str(exc)) from exc

        with self.lock:
            if any(job.state in {"QUEUED", "RUNNING", "DISCONNECTED"} for job in self.jobs.values()):
                raise RequestValidationError("Another H3 generation is active.")

        request = ReferenceVideoRequest(
            prompt=user_prompt,
            materialized_prompt=materialized,
            picture_id=picture.picture_id,
            motion_video_id=motion_video.video_id if motion_video else None,
            width=native_request.width,
            height=native_request.height,
            duration=native_request.duration_seconds,
            seed=native_request.seed,
            steps=native_request.steps,
        )
        job_id = uuid_token()
        job = Job(
            job_id,
            request,
            now_iso(),
            time.time(),
            route=R2V_ROUTE,
            video_type=R2V_VIDEO_TYPE,
            reference_video={
                "picture": picture.public(),
                "motion_video": motion_video.public() if motion_video else None,
            },
            references={
                REFERENCE_ROLE_START_FRAME: None,
                REFERENCE_ROLE_END_FRAME: None,
            },
        )
        with self.lock:
            self.jobs[job_id] = job
        try:
            response = self.backend.submit(graph, self.client_id)
        except Exception:
            with self.lock:
                self.jobs.pop(job_id, None)
            raise
        with self.lock:
            job.prompt_id = response["prompt_id"]
            job.state = "QUEUED"
        return job

    def submit(self, payload: Mapping[str, Any]) -> Job:
        if payload.get("video_type") not in (None, "standard"):
            raise RequestValidationError(
                "Reference Video requests must use the dedicated Reference route."
            )
        if any(field in payload for field in ("picture_id", "motion_video_id", "picture_path", "video_path")):
            raise RequestValidationError("Standard Video does not accept Reference Video assets.")
        request = validate_request(payload)
        route = resolve_route(request.references)
        assets: dict[str, ReferenceAsset] = {}
        if route == ROUTE_T2V:
            graph = compile_t2v(request)
        elif request.legacy_reference and request.references.start_frame is not None:
            reference = request.references.start_frame
            asset = self.get_reference(reference.id)
            if asset is None or not asset.path.is_file():
                raise ReferenceAssetMissingError("Start Frame asset is missing.")
            assets[REFERENCE_ROLE_START_FRAME] = asset
            graph = compile_i2v(request, f"inputs/{asset.filename}")
        else:
            reference_paths: dict[str, str] = {}
            for role, reference in (
                (REFERENCE_ROLE_START_FRAME, request.references.start_frame),
                (REFERENCE_ROLE_END_FRAME, request.references.end_frame),
            ):
                if reference is None:
                    continue
                asset = self.get_reference(reference.id)
                if asset is None or not asset.path.is_file():
                    raise ReferenceAssetMissingError(f"{role} asset is missing.")
                assets[role] = asset
                reference_paths[role] = f"inputs/{asset.filename}"
            graph = compile_fl2va_workflow(request, reference_paths)
        job_id = uuid_token()
        references_public = {
            role: assets[role].public() if role in assets else None
            for role in REFERENCE_ROLES
        }
        job = Job(
            job_id,
            request,
            now_iso(),
            time.time(),
            route=route,
            reference=assets[REFERENCE_ROLE_START_FRAME].public()
            if REFERENCE_ROLE_START_FRAME in assets
            else None,
            references=references_public,
        )
        with self.lock:
            self.jobs[job_id] = job
        try:
            response = self.backend.submit(graph, self.client_id)
        except Exception:
            with self.lock:
                self.jobs.pop(job_id, None)
            raise
        with self.lock:
            job.prompt_id = response["prompt_id"]
            job.state = "QUEUED"
        return job

    def submit_still(self, payload: Mapping[str, Any]) -> Job:
        """Submit one H2A/H2B Still request without exposing local paths."""

        if not isinstance(payload, Mapping):
            raise RequestValidationError("Still request must be a JSON object.")
        for field in ("source_path", "source_images", "source_paths", "reference", "references"):
            if payload.get(field) not in (None, "", {}):
                raise RequestValidationError(
                    "Still source must be supplied as a server-issued source_id."
                )

        source_id = payload.get("source_id")
        source: StillSourceAsset | None = None
        if source_id in (None, ""):
            request = validate_still_request(payload)
            graph = compile_still(request)
            route = ROUTE_STILL
        else:
            if not isinstance(source_id, str) or not SERVER_ASSET_ID_PATTERN.fullmatch(source_id):
                raise RequestValidationError("Still source id is invalid.")
            source = self.get_still_source(source_id)
            if source is None or not source.path.is_file():
                raise StillSourceMissingError("Still source asset is missing.")
            source_path = f"inputs/{source.filename}"
            request = validate_source_anchor_request(
                {**payload, "source_path": source_path}
            )
            graph = compile_source_anchored_still(request)
            route = ROUTE_SOURCE_ANCHORED_STILL

        job_id = uuid_token()
        job = Job(
            job_id,
            request,
            now_iso(),
            time.time(),
            route=route,
            media_kind="still",
            references={
                REFERENCE_ROLE_START_FRAME: None,
                REFERENCE_ROLE_END_FRAME: None,
            },
            still_source=source.public() if source else None,
        )
        with self.lock:
            self.jobs[job_id] = job
        try:
            response = self.backend.submit(graph, self.client_id)
        except Exception:
            with self.lock:
                self.jobs.pop(job_id, None)
            raise
        with self.lock:
            job.prompt_id = response["prompt_id"]
            job.state = "QUEUED"
        return job

    def get_job(self, job_id: str) -> Job | None:
        with self.lock:
            return self.jobs.get(job_id)

    def refresh_job(self, job: Job) -> Job:
        if job.prompt_id is None or job.state in TERMINAL_STATES:
            return job
        try:
            history = self.backend.history(job.prompt_id)
            if history and job.prompt_id in history:
                self._apply_history(job, history[job.prompt_id])
                return job
            queue = self.backend.queue()
            job.state = map_queue_state(
                queue,
                job.prompt_id,
                previous_state=job.state,
                cancel_requested=job.cancel_requested,
            )
            if job.state == "CANCELLED":
                job.completed_at = job.completed_at or now_iso()
                job.completed_epoch = job.completed_epoch or time.time()
            job.backend_error = None
        except BackendError as exc:
            job.backend_error = str(exc)
            job.state = "DISCONNECTED"
        return job

    def _apply_history(self, job: Job, entry: Any) -> None:
        if not isinstance(entry, Mapping):
            job.state = "FAILED"
            job.error = "Native ComfyUI returned malformed history."
        else:
            job.state = map_history_state(entry, cancel_requested=job.cancel_requested)
            if job.state == "CANCELLED":
                job.error = "Cancelled by user."
            elif job.state == "FAILED":
                job.error = _error_text(entry)
            elif job.state == "COMPLETED":
                suffixes = STILL_IMAGE_SUFFIXES if job.media_kind == "still" else VIDEO_SUFFIXES
                media = next(_iter_media(entry.get("outputs"), suffixes), None)
                if media is None:
                    job.state = "FAILED"
                    output_label = "image" if job.media_kind == "still" else "video"
                    job.error = f"Job completed without a {output_label} output."
                else:
                    path = self._safe_media_path(media, suffixes)
                    if path is None or not path.is_file():
                        job.state = "FAILED"
                        output_label = "image" if job.media_kind == "still" else "video"
                        job.error = f"Job completed but the {output_label} output is unavailable."
                    else:
                        job.state = "COMPLETED"
                        job.output = media
                        job.media_path = path
        if job.state in TERMINAL_STATES:
            job.completed_at = job.completed_at or now_iso()
            job.completed_epoch = job.completed_epoch or time.time()

    def _safe_media_path(
        self,
        media: Mapping[str, Any],
        suffixes: set[str] = VIDEO_SUFFIXES,
    ) -> Path | None:
        filename = media.get("filename")
        subfolder = media.get("subfolder") or ""
        if not isinstance(filename, str) or not isinstance(subfolder, str):
            return None
        if Path(filename).suffix.lower() not in suffixes:
            return None
        candidate = (self.output_root / subfolder / filename).resolve()
        try:
            candidate.relative_to(self.output_root)
        except ValueError:
            return None
        return candidate

    def cancel(self, job: Job) -> Job:
        if job.state not in {"QUEUED", "RUNNING", "DISCONNECTED"}:
            return job
        job.cancel_requested = True
        try:
            if not job.prompt_id:
                raise BackendError("Cancel was not dispatched safely: prompt id is missing.")
            queue = self.backend.queue()
            pending = queue.get("queue_pending") or []
            running = queue.get("queue_running") or []
            if _contains_prompt(pending, job.prompt_id):
                self.backend.delete_pending(job.prompt_id)
            elif _contains_prompt(running, job.prompt_id):
                self.backend.interrupt(job.prompt_id)
            else:
                # Never fall back to global /interrupt: another job may have
                # taken the worker between snapshots.
                self.refresh_job(job)
                if job.state in TERMINAL_STATES:
                    return job
                raise BackendError("Cancel was not dispatched safely: job is no longer visible in the Native queue.")
            job.state = "CANCELLED"
            job.completed_at = now_iso()
            job.completed_epoch = time.time()
            job.error = "Cancelled by user."
        except BackendError as exc:
            job.backend_error = str(exc)
            job.state = "DISCONNECTED"
        return job

    def history(self) -> list[dict[str, Any]]:
        with self.lock:
            jobs = list(self.jobs.values())
        for job in jobs:
            self.refresh_job(job)
        return [job.public() for job in reversed(jobs) if job.state in TERMINAL_STATES]


def uuid_token() -> str:
    import uuid

    return uuid.uuid4().hex


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _configured_ref2va_model() -> Path | None:
    """Find the exact Ref2VA file from the H3-only model-path config."""

    config_paths = (
        PORTABLE_ROOT / "h3" / "config" / "extra_model_paths.local.yaml",
        PORTABLE_ROOT / "h3" / "config" / "extra_model_paths.yaml",
    )
    for config_path in config_paths:
        try:
            text = config_path.read_text(encoding="utf-8")
        except OSError:
            continue
        base_match = re.search(r"^\s*base_path:\s*([^#\r\n]+)", text, re.MULTILINE)
        diffusion_match = re.search(
            r"^\s*diffusion_models:\s*([^#\r\n]+)",
            text,
            re.MULTILINE,
        )
        if not base_match or not diffusion_match:
            continue
        base_value = base_match.group(1).strip().strip("'\"")
        diffusion_value = diffusion_match.group(1).strip().strip("'\"")
        base_path = Path(base_value)
        if not base_path.is_absolute():
            base_path = (config_path.parent / base_path).resolve()
        diffusion_path = Path(diffusion_value)
        if not diffusion_path.is_absolute():
            diffusion_path = base_path / diffusion_path
        candidate = (diffusion_path / REF2VA_MODEL).resolve()
        if candidate.is_file():
            return candidate
    return None


def _probe_video_file(path: Path) -> dict[str, Any]:
    """Validate one MP4 with the already-installed ffprobe executable."""

    executable = shutil.which("ffprobe")
    if not executable:
        raise ReferenceVideoDecodeError("Motion Video validation requires ffprobe.")
    command = [
        executable,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_frames:format=duration",
        "-of",
        "json",
        os.fspath(path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReferenceVideoDecodeError("Motion Video could not be inspected.") from exc
    if result.returncode != 0:
        raise ReferenceVideoDecodeError("Motion Video must be a decodable MP4.")
    try:
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
        duration = float(payload.get("format", {}).get("duration"))
        if width <= 0 or height <= 0 or duration <= 0:
            raise ValueError
        rate_text = str(stream.get("avg_frame_rate") or "")
        if "/" in rate_text:
            numerator, denominator = rate_text.split("/", 1)
            frame_rate = round(float(numerator) / float(denominator), 6)
        else:
            frame_rate = float(rate_text) if rate_text else None
        frame_count_value = stream.get("nb_frames")
        frame_count = int(frame_count_value) if str(frame_count_value).isdigit() else None
    except (KeyError, TypeError, ValueError, ZeroDivisionError, json.JSONDecodeError) as exc:
        raise ReferenceVideoDecodeError("Motion Video metadata is incomplete.") from exc
    return {
        "width": width,
        "height": height,
        "duration_seconds": round(duration, 6),
        "frame_rate": frame_rate,
        "frame_count": frame_count,
    }


def _validate_image_upload(
    filename: str,
    body: bytes,
    *,
    suffixes: set[str],
    label: str,
    request_error: type[ReferenceRequestError],
    too_large_error: type[ReferenceRequestError],
    decode_error: type[ReferenceRequestError],
) -> tuple[str, str, int, int, str]:
    """Validate one bounded PNG/JPEG/WebP upload before it reaches disk."""

    if not isinstance(body, bytes) or not body:
        raise request_error(f"{label} upload is empty.")
    if len(body) > REFERENCE_MAX_BYTES:
        raise too_large_error(
            f"{label} image must be {REFERENCE_MAX_BYTES // (1024 * 1024)} MB or smaller."
        )
    if not isinstance(filename, str) or not filename.strip():
        raise request_error(f"{label} filename is required.")
    filename = filename.strip()
    if (
        filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or ":" in filename
        or Path(filename).is_absolute()
    ):
        raise request_error(f"{label} filename is unsafe.")
    suffix = Path(filename).suffix.lower()
    allowed_formats = {"PNG", "JPEG", "WEBP"} if ".webp" in suffixes else {"PNG", "JPEG"}
    if suffix not in suffixes:
        allowed_text = "PNG, JPEG, or WebP" if "WEBP" in allowed_formats else "PNG or JPEG"
        raise request_error(f"{label} must be {allowed_text}.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(body)) as image:
                actual_format = (image.format or "").upper()
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > REFERENCE_MAX_PIXELS:
                    raise decode_error(f"{label} image dimensions are too large.")
                image.verify()
        with Image.open(BytesIO(body)) as image:
            image.load()
    except ReferenceRequestError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
    ) as exc:
        raise decode_error(f"{label} image could not be decoded.") from exc

    format_suffixes = {
        "PNG": {".png"},
        "JPEG": {".jpg", ".jpeg"},
        "WEBP": {".webp"},
    }
    if actual_format not in allowed_formats or suffix not in format_suffixes.get(actual_format, set()):
        raise decode_error(f"{label} extension does not match its image format.")
    content_types = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
    }
    return suffix, actual_format, width, height, content_types[actual_format]


class H1AHandler(BaseHTTPRequestHandler):
    server: "H1AServer"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[h3] {self.address_string()} - {format % args}", flush=True)

    def _send_json(self, status: int, value: Any) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise RequestValidationError("Invalid request body length.") from exc
        if length > 128 * 1024:
            raise RequestValidationError("Request body is too large.")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestValidationError("Request body must be valid JSON.") from exc
        if not isinstance(value, dict):
            raise RequestValidationError("Request body must be a JSON object.")
        return value

    def _read_multipart_upload(
        self,
        *,
        file_names: set[str],
        allow_slot: bool,
        request_error: type[ReferenceRequestError],
        too_large_error: type[ReferenceRequestError],
        max_bytes: int = REFERENCE_MAX_BYTES,
        size_label: str = "Image",
    ) -> tuple[str | None, str, bytes]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise request_error("Invalid upload length.") from exc
        if length <= 0:
            raise request_error("Upload is empty.")
        if length > max_bytes + MULTIPART_OVERHEAD_LIMIT:
            raise too_large_error(
                f"{size_label} must be {max_bytes // (1024 * 1024)} MB or smaller."
            )
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            raise request_error("Upload must use multipart/form-data.")
        raw = self.rfile.read(length)
        header = (
            f"Content-Type: {content_type}\r\n"
            "MIME-Version: 1.0\r\n"
            "\r\n"
        ).encode("utf-8", errors="replace")
        try:
            message = BytesParser(policy=email_default).parsebytes(header + raw)
        except (TypeError, ValueError) as exc:
            raise request_error("Upload could not be parsed.") from exc
        if not message.is_multipart():
            raise request_error("Upload must contain a file part.")
        role: str | None = REFERENCE_ROLE_START_FRAME if allow_slot else None
        file_part: tuple[str, bytes] | None = None
        for part in message.walk():
            if part.is_multipart():
                continue
            disposition = part.get("Content-Disposition", "")
            name = part.get_param("name", header="content-disposition")
            if name == "slot" and "filename" not in disposition:
                if not allow_slot:
                    raise request_error("Still source upload does not accept a slot.")
                slot_body = part.get_payload(decode=True)
                if isinstance(slot_body, bytes):
                    try:
                        role = slot_body.decode("utf-8").strip()
                    except UnicodeDecodeError as exc:
                        raise request_error("Upload slot is malformed.") from exc
                continue
            if name in file_names and "filename" in disposition:
                filename = part.get_filename()
                body = part.get_payload(decode=True)
                if not isinstance(filename, str) or not isinstance(body, bytes):
                    raise request_error("Upload file is malformed.")
                file_part = (filename, body)
        if file_part is not None:
            return role, file_part[0], file_part[1]
        raise request_error("Upload file is missing.")

    def _read_multipart_reference(self) -> tuple[str, str, bytes]:
        role, filename, body = self._read_multipart_upload(
            file_names={"reference", "file"},
            allow_slot=True,
            request_error=ReferenceRequestError,
            too_large_error=ReferenceTooLargeError,
        )
        return role or REFERENCE_ROLE_START_FRAME, filename, body

    def _read_multipart_still_source(self) -> tuple[str, bytes]:
        _role, filename, body = self._read_multipart_upload(
            file_names={"source"},
            allow_slot=False,
            request_error=StillSourceRequestError,
            too_large_error=StillSourceTooLargeError,
        )
        return filename, body

    def _read_multipart_r2v_picture(self) -> tuple[str, bytes]:
        _role, filename, body = self._read_multipart_upload(
            file_names={"picture", "file"},
            allow_slot=False,
            request_error=ReferenceVideoRequestError,
            too_large_error=ReferenceVideoTooLargeError,
            size_label="Character Image",
        )
        return filename, body

    def _read_multipart_r2v_video(self) -> tuple[str, bytes]:
        _role, filename, body = self._read_multipart_upload(
            file_names={"motion_video", "video", "file"},
            allow_slot=False,
            request_error=ReferenceVideoRequestError,
            too_large_error=ReferenceVideoTooLargeError,
            max_bytes=R2V_VIDEO_MAX_BYTES,
            size_label="Motion Video",
        )
        return filename, body

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/config":
            video_options = video_option_metadata()
            reference_video = self.server.session.reference_video_capability()
            self._send_json(
                HTTPStatus.OK,
                {
                    **video_options,
                    "video_type_options": [
                        {"id": "standard", "label": "Standard", "enabled": True},
                        {
                            "id": R2V_VIDEO_TYPE,
                            "label": "Reference · Experimental",
                            "enabled": reference_video["enabled"],
                        },
                    ],
                    "reference_video": {
                        **reference_video,
                        "schema": "tegaki.h3.vp2b.experimental-r2v/v1",
                        "resolution_options": [
                            {"label": "608 x 352", "width": REF2VA_WIDTH, "height": REF2VA_HEIGHT}
                        ],
                        "duration_options": [{"label": "5 seconds", "value": 5}],
                        "default_steps": REF2VA_STEPS,
                        "picture": {
                            "extensions": [".png", ".jpg", ".jpeg", ".webp"],
                            "max_bytes": REFERENCE_MAX_BYTES,
                            "required": True,
                        },
                        "motion_video": {
                            "extensions": [".mp4"],
                            "max_bytes": R2V_VIDEO_MAX_BYTES,
                            "required": False,
                        },
                        "audio_reference": False,
                    },
                    "default_steps": 20,
                    "workflow": workflow_metadata(),
                    "i2v_workflow": i2v_workflow_metadata(),
                    "fl2va_workflow": fl2va_workflow_metadata(),
                    "ref2va_workflow": ref2va_workflow_metadata(),
                    "still": {
                        "workflows": [
                            still_workflow_metadata(),
                            source_anchored_still_workflow_metadata(),
                        ],
                        "resolution_options": [
                            {"label": "608 x 352", "width": 608, "height": 352}
                        ],
                        "default_steps": 20,
                        "source": {
                            "extensions": [".png", ".jpg", ".jpeg"],
                            "max_bytes": REFERENCE_MAX_BYTES,
                        },
                    },
                    "reference": {
                        "roles": list(REFERENCE_ROLES),
                        "schema": "h3.references/v1",
                        "extensions": [".png", ".jpg", ".jpeg", ".webp"],
                        "max_bytes": REFERENCE_MAX_BYTES,
                    },
                },
            )
            return
        if path == "/api/status":
            try:
                self._send_json(HTTPStatus.OK, self.server.session.backend.status())
            except BackendError as exc:
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "state": "DISCONNECTED",
                        "label": STATE_LABELS["DISCONNECTED"],
                        "queue_count": 0,
                        "running_count": 0,
                        "error": str(exc),
                    },
                )
            return
        if path == "/api/history":
            self._send_json(HTTPStatus.OK, {"entries": self.server.session.history()})
            return
        if path.startswith("/api/references/"):
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 3:
                self._serve_reference(segments[2])
                return
        if path.startswith("/api/still/sources/"):
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 4:
                self._serve_still_source(segments[3])
                return
        if path.startswith("/api/r2v/pictures/"):
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 4:
                self._serve_r2v_picture(segments[3])
                return
        if path.startswith("/api/r2v/videos/"):
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 4:
                self._serve_r2v_motion_video(segments[3])
                return
        if path.startswith("/api/jobs/"):
            segments = [segment for segment in path.split("/") if segment]
            if len(segments) == 4 and segments[-1] == "video":
                self._serve_job_video(segments[2])
                return
            if len(segments) == 4 and segments[-1] == "image":
                self._serve_job_image(segments[2])
                return
            if len(segments) == 3:
                self._serve_job(segments[2])
                return
        if path == "/" or path == "/index.html":
            self._serve_static("index.html")
            return
        if path.startswith("/static/"):
            self._serve_static(path.removeprefix("/static/"))
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def _serve_reference(self, reference_id: str) -> None:
        asset = self.server.session.get_reference(reference_id)
        if asset is None or not asset.path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Reference asset not found"})
            return
        try:
            body = asset.path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Reference asset not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", asset.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_still_source(self, source_id: str) -> None:
        if not SERVER_ASSET_ID_PATTERN.fullmatch(source_id):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Still source not found"})
            return
        asset = self.server.session.get_still_source(source_id)
        if asset is None or not asset.path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Still source not found"})
            return
        try:
            body = asset.path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Still source not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", asset.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_r2v_picture(self, picture_id: str) -> None:
        if not SERVER_ASSET_ID_PATTERN.fullmatch(picture_id):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Character Image not found"})
            return
        asset = self.server.session.get_r2v_picture(picture_id)
        if asset is None or not asset.path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Character Image not found"})
            return
        try:
            body = asset.path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Character Image not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", asset.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_r2v_motion_video(self, video_id: str) -> None:
        if not SERVER_ASSET_ID_PATTERN.fullmatch(video_id):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Motion Video not found"})
            return
        asset = self.server.session.get_r2v_motion_video(video_id)
        if asset is None or not asset.path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Motion Video not found"})
            return
        try:
            body = asset.path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Motion Video not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", asset.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_job(self, job_id: str) -> None:
        job = self.server.session.get_job(job_id)
        if job is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            return
        self.server.session.refresh_job(job)
        self._send_json(HTTPStatus.OK, job.public())

    def _serve_job_video(self, job_id: str) -> None:
        job = self.server.session.get_job(job_id)
        if job is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            return
        self.server.session.refresh_job(job)
        if job.media_kind != "video" or job.media_path is None or not job.media_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Video is not available"})
            return
        try:
            body = job.media_path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Video is not available"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(job.media_path.name)[0] or "video/mp4")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_job_image(self, job_id: str) -> None:
        job = self.server.session.get_job(job_id)
        if job is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Job not found"})
            return
        self.server.session.refresh_job(job)
        if job.media_kind != "still" or job.media_path is None or not job.media_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Still image is not available"})
            return
        try:
            body = job.media_path.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Still image is not available"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(job.media_path.name)[0] or "image/png")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, relative_path: str) -> None:
        static_root = (Path(__file__).resolve().parent / "static").resolve()
        candidate = (static_root / relative_path).resolve()
        try:
            candidate.relative_to(static_root)
        except ValueError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        if not candidate.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            body = candidate.read_bytes()
        except OSError:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        self.send_response(HTTPStatus.OK)
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/r2v/picture":
                filename, body = self._read_multipart_r2v_picture()
                asset = self.server.session.upload_r2v_picture(filename, body)
                self._send_json(HTTPStatus.CREATED, {"picture": asset.public()})
                return
            if path == "/api/r2v/video":
                filename, body = self._read_multipart_r2v_video()
                asset = self.server.session.upload_r2v_motion_video(filename, body)
                self._send_json(HTTPStatus.CREATED, {"motion_video": asset.public()})
                return
            if path == "/api/r2v/generate":
                payload = self._read_json()
                job = self.server.session.submit_reference_video(payload)
                self._send_json(HTTPStatus.ACCEPTED, {"job": job.public()})
                return
            if path == "/api/still/source":
                filename, body = self._read_multipart_still_source()
                asset = self.server.session.upload_still_source(filename, body)
                self._send_json(HTTPStatus.CREATED, {"source": asset.public()})
                return
            if path == "/api/still/generate":
                payload = self._read_json()
                job = self.server.session.submit_still(payload)
                self._send_json(HTTPStatus.ACCEPTED, {"job": job.public()})
                return
            if path == "/api/references":
                role, filename, body = self._read_multipart_reference()
                asset = self.server.session.upload_reference(filename, body, role=role)
                self._send_json(HTTPStatus.CREATED, {"reference": asset.public()})
                return
            if path == "/api/generate":
                payload = self._read_json()
                job = self.server.session.submit(payload)
                self._send_json(HTTPStatus.ACCEPTED, {"job": job.public()})
                return
            if path.startswith("/api/jobs/") and path.endswith("/cancel"):
                segments = [segment for segment in path.split("/") if segment]
                if len(segments) == 4:
                    job = self.server.session.get_job(segments[2])
                    if job is None:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Job not found"})
                        return
                    self.server.session.cancel(job)
                    self._send_json(HTTPStatus.OK, {"job": job.public()})
                    return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except ReferenceRequestError as exc:
            self._send_json(exc.status, {"error": str(exc), "kind": exc.error_kind})
        except RequestValidationError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc), "kind": "validation"})
        except WorkflowIncompatibleError as exc:
            self._send_json(
                HTTPStatus.CONFLICT,
                {"error": str(exc), "kind": "workflow_incompatible"},
            )
        except BackendRejected as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc), "kind": "workflow_rejected"})
        except BackendError as exc:
            self._send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"error": str(exc), "kind": "backend_unavailable"},
            )
        except Exception as exc:  # Keep local UI errors readable without exposing a traceback.
            print(f"[h3] internal error: {exc!r}", flush=True)
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "H3 server error."})


class H1AServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], session: H1ASession):
        super().__init__(address, H1AHandler)
        self.session = session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TEGAKI H3 local Native video skin")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8190)
    parser.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    parser.add_argument("--output-dir", default="output/h3")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = (PORTABLE_ROOT / args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    session = H1ASession(args.comfy_url, output_root)
    server = H1AServer((args.host, args.port), session)
    print(
        f"TEGAKI H3 UI listening on http://{args.host}:{args.port}/ "
        f"(Native backend: {args.comfy_url})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
