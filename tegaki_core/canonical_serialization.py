"""Pure deterministic canonical serialization and digest core for TEGAKI.

This module provides deterministic, platform-independent JSON serialization
and SHA-256 digest computation for structured data (graphs, plans, manifests,
revisions, and snapshots).

Zero external dependencies (pure Python stdlib), strictly I/O-free, and
reproducible across environments.

Contract:
- Canonical JSON string: UTF-8 compatible (ensure_ascii=False), compact separators (',', ':'),
  lexicographically sorted object keys (sort_keys=True), and strict finite number validation (allow_nan=False).
- Canonical JSON bytes: UTF-8 encoded canonical JSON string.
- Canonical JSON digest: SHA-256 lowercase 64-character hexadecimal digest over canonical JSON bytes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_str(value: Any) -> str:
    """Serialize a value to a compact, deterministic, key-sorted JSON string.

    Args:
        value: The Python data structure to serialize. Must consist of standard
            JSON-serializable types (dict, list, str, int, float, bool, None).
            Object keys must be strings.

    Returns:
        Deterministic compact JSON string with sorted keys and no unnecessary whitespace.

    Raises:
        TypeError: If value or any nested element is not JSON-serializable, or if
            dictionary keys cannot be sorted.
        ValueError: If value contains out-of-range floats (NaN, Infinity, -Infinity).
    """
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a value to deterministic canonical JSON encoded as UTF-8 bytes.

    Args:
        value: The Python data structure to serialize.

    Returns:
        Bytes representation of the canonical JSON string encoded in UTF-8 without BOM.
    """
    return canonical_json_str(value).encode("utf-8")


def canonical_json_digest(value: Any, *, algorithm: str = "sha256") -> str:
    """Compute a deterministic lowercase hexadecimal digest of the canonical JSON representation.

    Args:
        value: The Python data structure to digest.
        algorithm: Hash algorithm name from hashlib (defaults to 'sha256').

    Returns:
        Hexadecimal hash string (lowercase, 64 characters for sha256).

    Raises:
        ValueError: If algorithm is not supported by hashlib.
    """
    if not isinstance(algorithm, str) or not algorithm.strip():
        raise ValueError("Hash algorithm must be a non-empty string.")
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"Unsupported digest algorithm: {algorithm!r}") from exc

    hasher.update(canonical_json_bytes(value))
    return hasher.hexdigest().lower()


# Aliases for convenience matching alternative naming styles in codebase
stable_json_str = canonical_json_str
stable_json_bytes = canonical_json_bytes
stable_json_digest = canonical_json_digest
