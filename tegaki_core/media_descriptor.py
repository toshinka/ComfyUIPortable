"""Pure deterministic media descriptor and metadata normalizer core for TEGAKI.

Provides an immutable, normalized factual representation of already-observed
media properties (dimensions, duration, frame rate, frame count, file size).
Operates with zero I/O, no filesystem access, and no subprocess ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Any, Mapping

from tegaki_core.media_kind import MediaKind
from tegaki_core.timebase import Timebase, create_timebase


def _validate_not_bool(value: Any, name: str) -> None:
    if isinstance(value, bool):
        raise TypeError(f"{name} must not be a boolean.")


def _validate_positive_int(value: Any, name: str) -> int:
    _validate_not_bool(value, name)
    if isinstance(value, float):
        raise TypeError(f"{name} must be an integer, got float.")
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    if value <= 0:
        raise ValueError(f"{name} must be strictly positive (> 0), got {value}.")
    return value


def _validate_non_negative_int(value: Any, name: str) -> int:
    _validate_not_bool(value, name)
    if isinstance(value, float):
        raise TypeError(f"{name} must be an integer, got float.")
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    if value < 0:
        raise ValueError(f"{name} must be non-negative (>= 0), got {value}.")
    return value


@dataclass(frozen=True)
class MediaDescriptor:
    """Immutable normalized factual descriptor of observed media properties.

    Represents verified physical/structural attributes of an image or video asset.
    Does not store filesystem paths, asset IDs, or claim product compatibility.
    """

    kind: MediaKind
    width: int
    height: int
    duration_seconds: Fraction | None = None
    timebase: Timebase | None = None
    frame_count: int | None = None
    file_size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MediaKind):
            raise TypeError(f"kind must be a MediaKind enum instance, got {type(self.kind).__name__}.")

        num_w = _validate_positive_int(self.width, "width")
        num_h = _validate_positive_int(self.height, "height")
        object.__setattr__(self, "width", num_w)
        object.__setattr__(self, "height", num_h)

        if self.duration_seconds is not None:
            _validate_not_bool(self.duration_seconds, "duration_seconds")
            if isinstance(self.duration_seconds, float):
                if math.isnan(self.duration_seconds) or math.isinf(self.duration_seconds):
                    raise ValueError("duration_seconds cannot be NaN or Infinity.")
                if self.duration_seconds < 0:
                    raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}.")
                object.__setattr__(self, "duration_seconds", Fraction(str(self.duration_seconds)))
            elif isinstance(self.duration_seconds, str):
                try:
                    frac = Fraction(self.duration_seconds)
                except ValueError as exc:
                    raise ValueError(f"Malformed duration string: {self.duration_seconds!r}") from exc
                if frac < 0:
                    raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}.")
                object.__setattr__(self, "duration_seconds", frac)
            elif isinstance(self.duration_seconds, (int, Fraction)):
                if self.duration_seconds < 0:
                    raise ValueError(f"duration_seconds must be non-negative, got {self.duration_seconds}.")
                object.__setattr__(self, "duration_seconds", Fraction(self.duration_seconds))
            else:
                raise TypeError(
                    f"duration_seconds must be Fraction, int, float, or str, got {type(self.duration_seconds).__name__}."
                )

        if self.timebase is not None:
            if not isinstance(self.timebase, Timebase):
                raise TypeError(f"timebase must be a Timebase instance, got {type(self.timebase).__name__}.")

        if self.frame_count is not None:
            count = _validate_non_negative_int(self.frame_count, "frame_count")
            object.__setattr__(self, "frame_count", count)

        if self.file_size_bytes is not None:
            size = _validate_non_negative_int(self.file_size_bytes, "file_size_bytes")
            object.__setattr__(self, "file_size_bytes", size)

        # MediaKind-specific constraints
        if self.kind == MediaKind.IMAGE:
            if self.duration_seconds is not None:
                raise ValueError("IMAGE descriptors cannot have duration_seconds.")
            if self.timebase is not None:
                raise ValueError("IMAGE descriptors cannot have a timebase.")
            if self.frame_count is not None:
                raise ValueError("IMAGE descriptors cannot have a frame_count.")

    @property
    def aspect_ratio(self) -> Fraction:
        """Exact rational aspect ratio (width / height)."""
        return Fraction(self.width, self.height)

    @property
    def aspect_ratio_float(self) -> float:
        """Convenience floating-point aspect ratio approximation."""
        return self.width / self.height

    @property
    def duration_float(self) -> float | None:
        """Convenience floating-point duration in seconds."""
        return float(self.duration_seconds) if self.duration_seconds is not None else None

    @property
    def fps_float(self) -> float | None:
        """Convenience floating-point frame rate approximation."""
        return self.timebase.fps_float if self.timebase is not None else None


def create_image_descriptor(
    width: int,
    height: int,
    *,
    file_size_bytes: int | None = None,
) -> MediaDescriptor:
    """Create an immutable MediaDescriptor for an image asset."""
    return MediaDescriptor(
        kind=MediaKind.IMAGE,
        width=width,
        height=height,
        file_size_bytes=file_size_bytes,
    )


def create_video_descriptor(
    width: int,
    height: int,
    *,
    duration_seconds: Fraction | int | float | str | None = None,
    timebase: Timebase | None = None,
    frame_count: int | None = None,
    file_size_bytes: int | None = None,
) -> MediaDescriptor:
    """Create an immutable MediaDescriptor for a video asset."""
    return MediaDescriptor(
        kind=MediaKind.VIDEO,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        timebase=timebase,
        frame_count=frame_count,
        file_size_bytes=file_size_bytes,
    )


def normalize_ffprobe_payload(
    payload: Mapping[str, Any],
    *,
    file_size_bytes: int | None = None,
) -> MediaDescriptor:
    """Normalize already-collected ffprobe JSON output into a MediaDescriptor.

    Accepts the raw dictionary produced by ffprobe -show_entries ... -of json.
    Operates purely in memory without spawning subprocesses or touching disk.
    """
    if not isinstance(payload, Mapping):
        raise TypeError(f"Expected mapping for ffprobe payload, got {type(payload).__name__}.")

    streams = payload.get("streams")
    if not isinstance(streams, list) or not streams:
        raise ValueError("ffprobe payload contains no streams.")

    video_stream = None
    for stream in streams:
        if isinstance(stream, Mapping):
            codec_type = stream.get("codec_type")
            if codec_type == "video" or ("width" in stream and "height" in stream):
                video_stream = stream
                break

    if video_stream is None:
        raise ValueError("ffprobe payload contains no decodable video stream.")

    try:
        width = int(video_stream["width"])
        height = int(video_stream["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Video stream width/height missing or invalid.") from exc

    format_data = payload.get("format")
    format_map = format_data if isinstance(format_data, Mapping) else {}

    # Duration: prefer format.duration, fallback to stream.duration
    duration_val = format_map.get("duration") or video_stream.get("duration")
    duration_frac: Fraction | None = None
    if duration_val not in (None, "", "N/A"):
        try:
            duration_frac = Fraction(str(duration_val))
        except (TypeError, ValueError):
            duration_frac = None

    # Timebase: parse avg_frame_rate or r_frame_rate
    tb: Timebase | None = None
    rate_str = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")
    if rate_str and rate_str not in ("0/0", "N/A", "0"):
        try:
            tb = create_timebase(rate_str)
        except (TypeError, ValueError):
            tb = None

    # Frame count: check nb_read_frames fallback to nb_frames
    frame_count: int | None = None
    frames_val = video_stream.get("nb_read_frames") or video_stream.get("nb_frames")
    if frames_val not in (None, "", "N/A"):
        try:
            parsed_count = int(frames_val)
            if parsed_count >= 0:
                frame_count = parsed_count
        except (TypeError, ValueError):
            frame_count = None

    return create_video_descriptor(
        width=width,
        height=height,
        duration_seconds=duration_frac,
        timebase=tb,
        frame_count=frame_count,
        file_size_bytes=file_size_bytes,
    )
