"""Pure deterministic timebase and frame math core for TEGAKI.

This module provides exact rational timebase representations and conversion
helpers for temporal operations. It has zero external dependencies, maintains
internal rational authority via fractions.Fraction, and avoids floating-point
drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import re
from typing import Any


_RATIONAL_STR_PATTERN = re.compile(r"^\s*(\d+)(?:\s*/\s*(\d+))?\s*$")


def _validate_not_bool(value: Any, name: str) -> None:
    if isinstance(value, bool):
        raise TypeError(f"{name} must not be a boolean.")


def _validate_positive_int(value: Any, name: str) -> int:
    _validate_not_bool(value, name)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"{name} cannot be NaN or Infinity.")
        raise TypeError(
            f"Floating-point values are disallowed for {name} to prevent precision loss. "
            "Use int, Fraction, or rational string 'num/den'."
        )
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    if value <= 0:
        raise ValueError(f"{name} must be strictly positive (> 0), got {value}.")
    return value


def _validate_non_negative_int(value: Any, name: str) -> int:
    _validate_not_bool(value, name)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"{name} cannot be NaN or Infinity.")
        raise TypeError(
            f"Floating-point values are disallowed for {name} to prevent precision loss. "
            "Use int."
        )
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}.")
    if value < 0:
        raise ValueError(f"{name} must be non-negative (>= 0), got {value}.")
    return value


def _coerce_to_fraction(value: Any, name: str) -> Fraction:
    _validate_not_bool(value, name)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"{name} cannot be NaN or Infinity.")
        raise TypeError(
            f"Floating-point values are disallowed for {name} to prevent precision loss. "
            "Use Fraction, int, or rational string 'num/den'."
        )
    if isinstance(value, Fraction):
        if value < 0:
            raise ValueError(f"{name} must be non-negative (>= 0), got {value}.")
        return value
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{name} must be non-negative (>= 0), got {value}.")
        return Fraction(value, 1)
    if isinstance(value, str):
        match = _RATIONAL_STR_PATTERN.match(value)
        if not match:
            raise ValueError(f"Malformed rational string for {name}: {value!r}")
        num_str, den_str = match.groups()
        num = int(num_str)
        den = int(den_str) if den_str is not None else 1
        if den == 0:
            raise ValueError(f"{name} denominator cannot be zero.")
        return Fraction(num, den)
    raise TypeError(
        f"{name} must be Fraction, int, or rational string, got {type(value).__name__}."
    )


@dataclass(frozen=True)
class Timebase:
    """Immutable exact rational timebase.

    Represents frame rate as numerator / denominator (e.g., 24/1, 24000/1001).
    All conversions maintain exact rational values internally.
    """

    numerator: int
    denominator: int = 1

    def __init__(self, numerator: int, denominator: int = 1) -> None:
        num = _validate_positive_int(numerator, "numerator")
        den = _validate_positive_int(denominator, "denominator")
        gcd = math.gcd(num, den)
        object.__setattr__(self, "numerator", num // gcd)
        object.__setattr__(self, "denominator", den // gcd)

    @property
    def rate(self) -> Fraction:
        """Frame rate as exact Fraction (frames per second)."""
        return Fraction(self.numerator, self.denominator)

    @property
    def frame_duration(self) -> Fraction:
        """Duration of a single frame as exact Fraction (seconds per frame)."""
        return Fraction(self.denominator, self.numerator)

    @property
    def fps_float(self) -> float:
        """Convenience floating-point approximation of frame rate."""
        return self.numerator / self.denominator

    @property
    def frame_duration_float(self) -> float:
        """Convenience floating-point approximation of single frame duration."""
        return self.denominator / self.numerator

    def frame_index_to_timestamp(self, frame_index: int) -> Fraction:
        """Calculate the exact rational timestamp (seconds) at the start of frame_index.

        Uses 0-based indexing: frame 0 starts at timestamp 0.
        Calculation is direct: frame_index * (denominator / numerator).
        """
        idx = _validate_non_negative_int(frame_index, "frame_index")
        return Fraction(idx * self.denominator, self.numerator)

    def frame_count_to_duration(self, frame_count: int) -> Fraction:
        """Calculate the exact rational duration (seconds) of frame_count frames.

        Calculation is direct: frame_count * (denominator / numerator).
        """
        count = _validate_non_negative_int(frame_count, "frame_count")
        return Fraction(count * self.denominator, self.numerator)

    def timestamp_to_frame_position(self, timestamp: Any) -> Fraction:
        """Convert a timestamp (seconds) to exact rational frame position.

        Returns exact Fraction position (e.g. at 24fps, 0.5s -> Fraction(12, 1)).
        NOTE: This does NOT round to integer frame index.
        """
        ts = _coerce_to_fraction(timestamp, "timestamp")
        return ts * self.rate

    def duration_to_frame_position(self, duration: Any) -> Fraction:
        """Convert a duration (seconds) to exact rational frame count.

        Returns exact Fraction count.
        NOTE: This does NOT round to integer frame count.
        """
        dur = _coerce_to_fraction(duration, "duration")
        return dur * self.rate

    def __str__(self) -> str:
        if self.denominator == 1:
            return f"{self.numerator} fps"
        return f"{self.numerator}/{self.denominator} fps"

    def __repr__(self) -> str:
        return f"Timebase({self.numerator}, {self.denominator})"


def create_timebase(
    value: Any,
    denominator: int | None = None,
) -> Timebase:
    """Create a Timebase instance from various supported rate formats.

    Supported inputs:
    - Timebase instance (returned as-is or equivalent)
    - int: e.g. 24 -> Timebase(24, 1)
    - two ints: e.g. create_timebase(24000, 1001)
    - Fraction: e.g. Fraction(24000, 1001)
    - str: e.g. "24", "24/1", "24000/1001"
    - tuple: e.g. (24000, 1001)

    Disallowed inputs:
    - Booleans (raise TypeError)
    - Floating-point values (raise TypeError / ValueError)
    - Zero or negative values (raise ValueError)
    - Malformed or invalid strings (raise ValueError)
    """
    _validate_not_bool(value, "timebase rate")
    if denominator is not None:
        _validate_not_bool(denominator, "timebase denominator")

    if isinstance(value, Timebase):
        if denominator is not None:
            raise ValueError("Denominator cannot be specified when value is already a Timebase.")
        return value

    if denominator is not None:
        return Timebase(value, denominator)

    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(f"Expected 2-element tuple (numerator, denominator), got {len(value)} elements.")
        return Timebase(value[0], value[1])

    if isinstance(value, Fraction):
        return Timebase(value.numerator, value.denominator)

    if isinstance(value, int):
        return Timebase(value, 1)

    if isinstance(value, str):
        match = _RATIONAL_STR_PATTERN.match(value)
        if not match:
            raise ValueError(f"Malformed rational string for timebase: {value!r}")
        num_str, den_str = match.groups()
        num = int(num_str)
        den = int(den_str) if den_str is not None else 1
        return Timebase(num, den)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("Timebase rate cannot be NaN or Infinity.")
        raise TypeError(
            "Floating-point values are disallowed for timebase creation to prevent precision loss. "
            "Use int, Fraction, or rational string 'num/den'."
        )

    raise TypeError(
        f"Unsupported timebase rate type: {type(value).__name__}. "
        "Expected Timebase, int, Fraction, str, or (num, den) tuple."
    )
