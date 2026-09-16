"""Bounded, read-only metadata enrichment for resolved Manga resources.

The Manga catalog remains the only resource authority.  This module accepts a
canonical id and a path that the authority has already resolved, then inspects
only the safetensors header.  It deliberately has no catalog, server, UI,
network, cache, model-loading, or tensor-reading dependency.
"""

from __future__ import annotations

import json
import os
import struct
from typing import Any, TypedDict


SUPPORTED_KINDS = frozenset({"CHECKPOINT", "LORA"})
SUPPORTED_SUFFIXES = frozenset({".safetensors", ".sft"})
FORMAT_NAME = "SAFETENSORS"

MAX_HEADER_BYTES = 8 * 1024 * 1024
MAX_METADATA_ENTRIES = 256
MAX_VALUE_CHARS = 4096
MAX_LIST_ENTRIES = 128
MAX_NESTED_DEPTH = 3


class MetadataResult(TypedDict):
    """Stable JSON-shaped result returned by :func:`inspect_model_lora_metadata`."""

    ok: bool
    kind: str
    canonical_id: str
    metadata_state: str
    format: str | None
    raw_embedded_metadata: dict[str, Any] | None
    normalized_metadata: dict[str, Any]
    warnings: list[str]
    error: dict[str, str] | None
    bytes_inspected: int
    hash_state: str


def _base_result(kind: str, canonical_id: str, format_name: str | None = None) -> MetadataResult:
    return {
        "ok": False,
        "kind": kind,
        "canonical_id": canonical_id,
        "metadata_state": "ERROR",
        "format": format_name,
        "raw_embedded_metadata": None,
        "normalized_metadata": {},
        "warnings": [],
        "error": None,
        "bytes_inspected": 0,
        "hash_state": "ABSENT",
    }


def _error_result(
    kind: str,
    canonical_id: str,
    code: str,
    message: str,
    format_name: str | None = None,
    bytes_inspected: int = 0,
) -> MetadataResult:
    result = _base_result(kind, canonical_id, format_name)
    result["error"] = {"code": code, "message": message}
    result["bytes_inspected"] = bytes_inspected
    return result


def _bounded_value(value: Any, depth: int = 0) -> tuple[Any, bool]:
    """Return a JSON-safe value bounded by depth, entries, and string size."""

    if isinstance(value, str):
        if len(value) > MAX_VALUE_CHARS:
            return value[:MAX_VALUE_CHARS], True
        return value, False
    if value is None or isinstance(value, (bool, int, float)):
        return value, False
    if depth >= MAX_NESTED_DEPTH:
        return "[TRUNCATED]", True
    if isinstance(value, list):
        bounded: list[Any] = []
        truncated = len(value) > MAX_LIST_ENTRIES
        for item in value[:MAX_LIST_ENTRIES]:
            item_value, item_truncated = _bounded_value(item, depth + 1)
            bounded.append(item_value)
            truncated = truncated or item_truncated
        return bounded, truncated
    if isinstance(value, dict):
        bounded_dict: dict[str, Any] = {}
        keys = sorted((key for key in value if isinstance(key, str)))
        truncated = len(keys) > MAX_METADATA_ENTRIES
        for key in keys[:MAX_METADATA_ENTRIES]:
            item_value, item_truncated = _bounded_value(value[key], depth + 1)
            bounded_dict[key] = item_value
            truncated = truncated or item_truncated
        return bounded_dict, truncated
    return "[UNSUPPORTED]", True


def _stable_value(value: Any) -> str:
    """Create a deterministic comparison form without changing the value."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _select_explicit(
    metadata: dict[str, Any],
    aliases: tuple[str, ...],
    normalized_name: str,
    warnings: list[str],
) -> Any | None:
    """Select one explicit key, reporting disagreement instead of guessing."""

    present = [(key, metadata[key]) for key in aliases if key in metadata]
    if not present:
        return None
    values = {_stable_value(value) for _, value in present}
    if len(values) > 1:
        warnings.append(f"METADATA_CONFLICT:{normalized_name}")
        return None
    return present[0][1]


def _normalize_metadata(metadata: dict[str, Any], warnings: list[str]) -> tuple[dict[str, Any], str]:
    """Normalize only explicit, locally established metadata keys."""

    normalized: dict[str, Any] = {}

    base_model = _select_explicit(
        metadata,
        ("ss_base_model_version", "ss_sd_model_name"),
        "base_model",
        warnings,
    )
    base_conflict = "METADATA_CONFLICT:base_model" in warnings
    if base_conflict:
        normalized["base_model_state"] = "CONFLICTING"
    elif base_model is None:
        normalized["base_model_state"] = "ABSENT"
    else:
        normalized["base_model_state"] = "EXPLICIT"
        normalized["base_model"] = base_model

    architecture = _select_explicit(
        metadata, ("modelspec.architecture",), "architecture", warnings
    )
    if architecture is not None:
        normalized["architecture"] = architecture

    title = _select_explicit(metadata, ("modelspec.title",), "title", warnings)
    if title is not None:
        normalized["title"] = title

    description = _select_explicit(
        metadata, ("modelspec.description",), "description", warnings
    )
    if description is not None:
        normalized["description"] = description

    trigger_words = _select_explicit(
        metadata,
        ("modelspec.trigger_phrase", "ss_trigger_words", "trigger_words"),
        "trigger_words",
        warnings,
    )
    if trigger_words is not None:
        # Keep the producer's explicit value.  In particular, do not split,
        # frequency-rank, or derive tags from a filename or description.
        normalized["trigger_words"] = trigger_words

    training_resolution = _select_explicit(
        metadata,
        ("ss_resolution", "modelspec.resolution"),
        "training_resolution",
        warnings,
    )
    if training_resolution is not None:
        normalized["training_resolution"] = training_resolution

    training: dict[str, Any] = {}
    if "ss_tag_frequency" in metadata:
        training["tag_frequency"] = metadata["ss_tag_frequency"]
    if "ss_bucket_info" in metadata:
        training["bucket_info"] = metadata["ss_bucket_info"]
    if training:
        # These values are deliberately left in producer form; parsing them
        # would turn raw training evidence into an inferred trigger list.
        normalized["training_metadata"] = training

    provenance: dict[str, Any] = {}
    for key in ("modelspec.source", "source", "source_url"):
        if key in metadata:
            provenance[key] = metadata[key]
    if provenance:
        normalized["provenance"] = provenance

    hash_value = _select_explicit(
        metadata,
        (
            "modelspec.hash.sha256",
            "modelspec.hash.blake3",
            "_sha256",
            "sha256",
            "sshs_model_hash",
            "sshs_legacy_hash",
        ),
        "embedded_hash",
        warnings,
    )
    if hash_value is not None:
        normalized["embedded_hash"] = hash_value

    metadata_state = "CONFLICT" if any(
        warning.startswith("METADATA_CONFLICT:") for warning in warnings
    ) else "PRESENT"
    return normalized, metadata_state


def inspect_model_lora_metadata(
    kind: str,
    canonical_id: str,
    resolved_path: str | os.PathLike[str],
    *,
    max_header_bytes: int = MAX_HEADER_BYTES,
) -> MetadataResult:
    """Inspect bounded embedded metadata for an authority-resolved resource.

    ``resolved_path`` is an internal/server-owned path supplied after strict
    catalog resolution.  This function does not resolve catalog IDs, scan a
    directory, inspect sidecars, hash payload bytes, load tensors, or write
    files.  The optional path argument exists to make pure fixture testing
    possible; no product API exposes arbitrary browser paths here.
    """

    normalized_kind = kind.upper() if isinstance(kind, str) else ""
    if normalized_kind not in SUPPORTED_KINDS:
        return _error_result(normalized_kind, "", "INVALID_REQUEST", "kind must be CHECKPOINT or LORA")
    if not isinstance(canonical_id, str) or not canonical_id:
        return _error_result(normalized_kind, "", "INVALID_REQUEST", "canonical_id must be non-empty")
    if type(max_header_bytes) is not int or not 0 < max_header_bytes <= MAX_HEADER_BYTES:
        return _error_result(normalized_kind, canonical_id, "INVALID_REQUEST", "invalid header bound")
    try:
        path = os.fspath(resolved_path)
    except TypeError:
        return _error_result(normalized_kind, canonical_id, "INVALID_REQUEST", "resolved_path must be path-like")

    suffix = os.path.splitext(path)[1].lower()
    if suffix not in SUPPORTED_SUFFIXES:
        return _error_result(
            normalized_kind,
            canonical_id,
            "UNSUPPORTED_FORMAT",
            "only safetensors headers are supported",
        )

    try:
        file_size = os.path.getsize(path)
        with open(path, "rb") as handle:
            prefix = handle.read(8)
            if len(prefix) != 8:
                return _error_result(
                    normalized_kind,
                    canonical_id,
                    "INVALID_SAFETENSORS",
                    "safetensors header length prefix is incomplete",
                    FORMAT_NAME,
                    len(prefix),
                )
            header_size = struct.unpack("<Q", prefix)[0]
            if header_size == 0:
                return _error_result(
                    normalized_kind,
                    canonical_id,
                    "INVALID_SAFETENSORS",
                    "safetensors header is empty",
                    FORMAT_NAME,
                    8,
                )
            if header_size > max_header_bytes:
                return _error_result(
                    normalized_kind,
                    canonical_id,
                    "HEADER_TOO_LARGE",
                    "safetensors header exceeds the bounded inspection limit",
                    FORMAT_NAME,
                    8,
                )
            if file_size < 8 + header_size:
                return _error_result(
                    normalized_kind,
                    canonical_id,
                    "INVALID_SAFETENSORS",
                    "file ends before the declared safetensors header",
                    FORMAT_NAME,
                    8,
                )
            header_bytes = handle.read(header_size)
            bytes_inspected = 8 + len(header_bytes)
            if len(header_bytes) != header_size:
                return _error_result(
                    normalized_kind,
                    canonical_id,
                    "INVALID_SAFETENSORS",
                    "safetensors header is incomplete",
                    FORMAT_NAME,
                    bytes_inspected,
                )
    except FileNotFoundError:
        return _error_result(normalized_kind, canonical_id, "FILE_NOT_FOUND", "resolved resource does not exist")
    except OSError as exc:
        return _error_result(normalized_kind, canonical_id, "READ_FAILED", str(exc))

    try:
        header = json.loads(header_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _error_result(
            normalized_kind,
            canonical_id,
            "INVALID_SAFETENSORS",
            "safetensors header is not valid UTF-8 JSON",
            FORMAT_NAME,
            bytes_inspected,
        )
    if not isinstance(header, dict):
        return _error_result(
            normalized_kind,
            canonical_id,
            "INVALID_SAFETENSORS",
            "safetensors header JSON must be an object",
            FORMAT_NAME,
            bytes_inspected,
        )

    metadata = header.get("__metadata__")
    if metadata is None or metadata == {}:
        result = _base_result(normalized_kind, canonical_id, FORMAT_NAME)
        result.update({
            "ok": True,
            "metadata_state": "ABSENT",
            "normalized_metadata": {"base_model_state": "ABSENT"},
            "bytes_inspected": bytes_inspected,
        })
        return result
    if not isinstance(metadata, dict):
        return _error_result(
            normalized_kind,
            canonical_id,
            "METADATA_MALFORMED",
            "safetensors __metadata__ must be an object",
            FORMAT_NAME,
            bytes_inspected,
        )

    bounded_metadata, truncated = _bounded_value(metadata)
    if not isinstance(bounded_metadata, dict):
        return _error_result(
            normalized_kind,
            canonical_id,
            "METADATA_MALFORMED",
            "safetensors metadata could not be bounded",
            FORMAT_NAME,
            bytes_inspected,
        )
    warnings: list[str] = []
    if truncated:
        warnings.append("METADATA_TRUNCATED")
    normalized, metadata_state = _normalize_metadata(bounded_metadata, warnings)
    result = _base_result(normalized_kind, canonical_id, FORMAT_NAME)
    result.update({
        "ok": True,
        "metadata_state": metadata_state,
        "raw_embedded_metadata": bounded_metadata,
        "normalized_metadata": normalized,
        "warnings": warnings,
        "error": None,
        "bytes_inspected": bytes_inspected,
        "hash_state": "KNOWN" if "embedded_hash" in normalized else "ABSENT",
    })
    if any(warning == "METADATA_CONFLICT:embedded_hash" for warning in warnings):
        result["hash_state"] = "ABSENT"
    return result


__all__ = [
    "FORMAT_NAME",
    "MAX_HEADER_BYTES",
    "MetadataResult",
    "SUPPORTED_KINDS",
    "inspect_model_lora_metadata",
]
