"""Deterministic serialization and digest core for TEGAKI.

This module provides deterministic JSON serialization matching current TEGAKI
repository digest contracts and SHA-256 digest computation for structured data
(graphs, plans, manifests, revisions, and snapshots).

Zero external dependencies (pure Python stdlib), strictly I/O-free, and
follows the evidence-backed TEGAKI stable serialization contract.

Contract:
- Canonical JSON string: UTF-8 compatible (ensure_ascii=False), compact separators (',', ':'),
  lexicographically sorted object keys (sort_keys=True), and strict finite number validation (allow_nan=False).
  Follows Python JSON number serialization used by current Python digest owners.
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


def canonical_json_digest(value: Any) -> str:
    """Compute a deterministic SHA-256 lowercase hexadecimal digest of the canonical JSON representation.

    Args:
        value: The Python data structure to digest.

    Returns:
        Hexadecimal hash string (lowercase, 64 characters SHA-256).
    """
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
