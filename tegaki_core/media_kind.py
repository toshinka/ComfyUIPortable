"""Pure deterministic media-kind extension classification core for TEGAKI.

Provides syntactic, zero-I/O classification of filenames, paths, and extensions
into proven repository media families (IMAGE, VIDEO, UNKNOWN).
No file opening, sniffing, codec inspection, or filesystem access is performed.
"""

from __future__ import annotations

from enum import Enum
import os
from pathlib import PurePath
from typing import Any, Union


class MediaKind(str, Enum):
    """Broad media families proven by current repository contracts."""

    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


# Evidence-backed extension sets (lowercase, with leading dot).
# IMAGE: Proven across H3 (PICTURE_SUFFIXES / REFERENCE_SUFFIXES) and Manga (SUPPORTED_REFERENCE_EXTENSIONS)
IMAGE_EXTENSIONS: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".webp"})

# VIDEO: Proven across H3 (VIDEO_SUFFIXES in server, adapters, and runners)
VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".webm", ".mov", ".mkv"})


def extract_media_extension(path_or_extension: Union[str, os.PathLike[str]]) -> str:
    """Extract and normalize a lowercase extension with leading dot.

    Operates purely syntactically without filesystem access.
    Returns empty string if no extension is present.
    """
    if isinstance(path_or_extension, bool) or not isinstance(
        path_or_extension, (str, os.PathLike)
    ):
        raise TypeError(
            f"Expected str or PathLike, got {type(path_or_extension).__name__}"
        )

    text = os.fspath(path_or_extension).strip()
    if not text:
        return ""

    # If already a pure extension string like ".png" or "png"
    if "/" not in text and "\\" not in text:
        if text.startswith("."):
            return text.lower()
        # Bare extension token without slash or dot (e.g. 'png', 'mp4')
        # Check if it matches a known extension before treating as extension
        candidate = f".{text.lower()}"
        if candidate in IMAGE_EXTENSIONS or candidate in VIDEO_EXTENSIONS:
            return candidate

    pure = PurePath(text)
    suffix = pure.suffix
    return suffix.lower() if suffix else ""


def classify_media_kind(path_or_extension: Union[str, os.PathLike[str]]) -> MediaKind:
    """Classify a path, filename, or extension into a proven MediaKind.

    Returns:
      MediaKind.IMAGE for .png, .jpg, .jpeg, .webp
      MediaKind.VIDEO for .mp4, .webm, .mov, .mkv
      MediaKind.UNKNOWN for any other extension, missing extension, or unrecognized type
    """
    ext = extract_media_extension(path_or_extension)
    if not ext:
        return MediaKind.UNKNOWN

    if ext in IMAGE_EXTENSIONS:
        return MediaKind.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return MediaKind.VIDEO
    return MediaKind.UNKNOWN


def is_image_extension(path_or_extension: Union[str, os.PathLike[str]]) -> bool:
    """Return True if the path/extension belongs to the proven IMAGE family."""
    return classify_media_kind(path_or_extension) == MediaKind.IMAGE


def is_video_extension(path_or_extension: Union[str, os.PathLike[str]]) -> bool:
    """Return True if the path/extension belongs to the proven VIDEO family."""
    return classify_media_kind(path_or_extension) == MediaKind.VIDEO
