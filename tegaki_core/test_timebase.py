"""Unit tests for banked canonical timebase and frame math core.

Verifies:
- integer, rational, and NTSC frame rates
- exact rational timestamps and durations
- 0-based frame indexing
- determinism and immutability
- invalid rate rejection (0, negative, bool, NaN, Inf, malformed strings)
- float accumulation prevention and drift-free direct calculation
- production parity with authoritative H3 24 FPS calculations
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegaki_core.timebase import Timebase, create_timebase


class TimebaseCoreTests(unittest.TestCase):
    """Test suite for Timebase and exact rational frame math."""

    def test_integer_rates(self):
        for fps in (24, 25, 30, 60):
            tb = create_timebase(fps)
            self.assertEqual(tb.numerator, fps)
            self.assertEqual(tb.denominator, 1)
            self.assertEqual(tb.rate, Fraction(fps, 1))
            self.assertEqual(tb.frame_duration, Fraction(1, fps))
            self.assertEqual(tb.fps_float, float(fps))
            self.assertEqual(tb.frame_duration_float, 1.0 / fps)

    def test_rational_strings(self):
        tb_24 = create_timebase("24/1")
        self.assertEqual(tb_24, Timebase(24, 1))

        tb_ntsc_24 = create_timebase("24000/1001")
        self.assertEqual(tb_ntsc_24.numerator, 24000)
        self.assertEqual(tb_ntsc_24.denominator, 1001)
        self.assertEqual(tb_ntsc_24.rate, Fraction(24000, 1001))

        tb_ntsc_30 = create_timebase("30000/1001")
        self.assertEqual(tb_ntsc_30.numerator, 30000)
        self.assertEqual(tb_ntsc_30.denominator, 1001)

        tb_ntsc_60 = create_timebase("60000/1001")
        self.assertEqual(tb_ntsc_60.numerator, 60000)
        self.assertEqual(tb_ntsc_60.denominator, 1001)

    def test_factory_variants(self):
        # Two ints
        self.assertEqual(create_timebase(24, 1), Timebase(24, 1))
        self.assertEqual(create_timebase(24000, 1001), Timebase(24000, 1001))
        # Tuple
        self.assertEqual(create_timebase((24000, 1001)), Timebase(24000, 1001))
        # Fraction
        self.assertEqual(create_timebase(Fraction(25, 1)), Timebase(25, 1))
        # Timebase instance pass-through
        original = Timebase(30, 1)
        self.assertIs(create_timebase(original), original)

    def test_gcd_reduction(self):
        tb = Timebase(48, 2)
        self.assertEqual(tb.numerator, 24)
        self.assertEqual(tb.denominator, 1)
        self.assertEqual(tb, Timebase(24, 1))
        self.assertEqual(hash(tb), hash(Timebase(24, 1)))

    def test_frame_index_to_timestamp_zero_based(self):
        tb = create_timebase(24)
        # Frame 0 is timestamp 0
        self.assertEqual(tb.frame_index_to_timestamp(0), Fraction(0, 1))
        # Frame 1 is 1/24 seconds
        self.assertEqual(tb.frame_index_to_timestamp(1), Fraction(1, 24))
        # Frame 24 is 1 second
        self.assertEqual(tb.frame_index_to_timestamp(24), Fraction(1, 1))

    def test_large_frame_index_no_precision_loss(self):
        tb = create_timebase(24000, 1001)
        idx = 1_000_000
        ts = tb.frame_index_to_timestamp(idx)
        expected = Fraction(idx * 1001, 24000)
        self.assertEqual(ts, expected)
        self.assertEqual(ts, Fraction(125125, 3))

    def test_frame_count_to_duration(self):
        tb = create_timebase(24)
        self.assertEqual(tb.frame_count_to_duration(0), Fraction(0, 1))
        self.assertEqual(tb.frame_count_to_duration(24), Fraction(1, 1))
        self.assertEqual(tb.frame_count_to_duration(124), Fraction(31, 6))

    def test_timestamp_to_frame_position_exact(self):
        tb = create_timebase(24)
        # Exact frame boundary
        self.assertEqual(tb.timestamp_to_frame_position(Fraction(1, 24)), Fraction(1, 1))
        self.assertEqual(tb.timestamp_to_frame_position(1), Fraction(24, 1))
        # Sub-frame rational position
        self.assertEqual(tb.timestamp_to_frame_position(Fraction(1, 48)), Fraction(1, 2))
        self.assertEqual(tb.timestamp_to_frame_position("1/12"), Fraction(2, 1))

    def test_duration_to_frame_position_exact(self):
        tb = create_timebase(24)
        self.assertEqual(tb.duration_to_frame_position(Fraction(31, 6)), Fraction(124, 1))
        self.assertEqual(tb.duration_to_frame_position(5), Fraction(120, 1))

    def test_no_cumulative_drift(self):
        tb = create_timebase(24000, 1001)
        # Direct indexing vs rational accumulator are exactly equal
        n_frames = 1000
        direct_ts = tb.frame_index_to_timestamp(n_frames)
        accum_ts = sum(tb.frame_duration for _ in range(n_frames))
        self.assertEqual(direct_ts, accum_ts)

        # Floating-point repeated addition drifts from direct calculation even at small n
        n_drift = 10
        float_accum = sum(tb.frame_duration_float for _ in range(n_drift))
        float_direct = float(tb.frame_index_to_timestamp(n_drift))
        self.assertNotEqual(float_accum, float_direct)

    def test_immutability(self):
        tb = create_timebase(24)
        with self.assertRaises(FrozenInstanceError):
            tb.numerator = 30
        with self.assertRaises(FrozenInstanceError):
            tb.denominator = 2

    def test_determinism(self):
        tb1 = create_timebase("24000/1001")
        tb2 = create_timebase(24000, 1001)
        self.assertEqual(tb1, tb2)
        self.assertEqual(hash(tb1), hash(tb2))
        self.assertEqual(
            tb1.frame_index_to_timestamp(500),
            tb2.frame_index_to_timestamp(500),
        )

    def test_invalid_rate_rejection(self):
        # Zero
        with self.assertRaises(ValueError):
            create_timebase(0)
        with self.assertRaises(ValueError):
            create_timebase(0, 1)
        with self.assertRaises(ValueError):
            create_timebase(24, 0)
        with self.assertRaises(ValueError):
            create_timebase("0/1")
        with self.assertRaises(ValueError):
            create_timebase("24/0")

        # Negative
        with self.assertRaises(ValueError):
            create_timebase(-24)
        with self.assertRaises(ValueError):
            create_timebase(24, -1)
        with self.assertRaises(ValueError):
            create_timebase("-24/1")

        # Boolean rejection
        with self.assertRaises(TypeError):
            create_timebase(True)
        with self.assertRaises(TypeError):
            create_timebase(False)
        with self.assertRaises(TypeError):
            create_timebase(24, True)

        # Float / NaN / Inf rejection
        with self.assertRaises(ValueError):
            create_timebase(float("nan"))
        with self.assertRaises(ValueError):
            create_timebase(float("inf"))
        with self.assertRaises(TypeError):
            create_timebase(24.0)

        # Malformed strings
        with self.assertRaises(ValueError):
            create_timebase("invalid")
        with self.assertRaises(ValueError):
            create_timebase("24/1/2")
        with self.assertRaises(ValueError):
            create_timebase("")

        # Malformed tuples
        with self.assertRaises(ValueError):
            create_timebase((24,))
        with self.assertRaises(ValueError):
            create_timebase((24, 1, 2))

    def test_invalid_frame_operation_inputs(self):
        tb = create_timebase(24)

        # Negative indices
        with self.assertRaises(ValueError):
            tb.frame_index_to_timestamp(-1)
        with self.assertRaises(ValueError):
            tb.frame_count_to_duration(-1)
        with self.assertRaises(ValueError):
            tb.timestamp_to_frame_position(-1)
        with self.assertRaises(ValueError):
            tb.duration_to_frame_position(-1)

        # Booleans
        with self.assertRaises(TypeError):
            tb.frame_index_to_timestamp(True)
        with self.assertRaises(TypeError):
            tb.frame_count_to_duration(False)
        with self.assertRaises(TypeError):
            tb.timestamp_to_frame_position(True)
        with self.assertRaises(TypeError):
            tb.duration_to_frame_position(False)

        # Non-integers for frame indices
        with self.assertRaises(TypeError):
            tb.frame_index_to_timestamp(1.5)
        with self.assertRaises(TypeError):
            tb.frame_count_to_duration(1.5)

    def test_production_parity_h3_24fps(self):
        """Mathematical compatibility with H3 24 FPS conventions."""
        tb = create_timebase(24)

        # Baseline 5s raw duration: 5 * 24 = 120 frames
        self.assertEqual(tb.duration_to_frame_position(5), Fraction(120, 1))

        # Aligned 124 frames (H3 17k+5 envelope at 5s)
        # H3: duration_seconds = 124 / 24
        duration_frac = tb.frame_count_to_duration(124)
        self.assertEqual(duration_frac, Fraction(31, 6))
        self.assertAlmostEqual(float(duration_frac), 124 / 24, places=12)
        self.assertAlmostEqual(float(duration_frac), 5.166666666666667, places=12)

        # 2s raw duration: 2 * 24 = 48 frames, aligned 56 frames
        duration_2s_aligned = tb.frame_count_to_duration(56)
        self.assertEqual(duration_2s_aligned, Fraction(7, 3))
        self.assertAlmostEqual(float(duration_2s_aligned), 56 / 24, places=12)

    def test_representation_strings(self):
        tb_int = create_timebase(24)
        self.assertEqual(str(tb_int), "24 fps")
        self.assertEqual(repr(tb_int), "Timebase(24, 1)")

        tb_ntsc = create_timebase(24000, 1001)
        self.assertEqual(str(tb_ntsc), "24000/1001 fps")
        self.assertEqual(repr(tb_ntsc), "Timebase(24000, 1001)")


if __name__ == "__main__":
    unittest.main()
