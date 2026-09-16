"""Unit tests for banked canonical media descriptor and metadata normalizer.

Verifies:
- pure immutable MediaDescriptor value object
- image descriptor creation and dimension validation
- video descriptor creation with Timebase and exact duration
- rejection of invalid/negative dimensions, booleans, and floats
- kind-specific constraints (image cannot have timebase or non-zero duration)
- pure normalization of raw ffprobe JSON payloads
- immutability and determinism
- production parity with H3 ffprobe metadata structures
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegaki_core.media_descriptor import (
    MediaDescriptor,
    create_image_descriptor,
    create_video_descriptor,
    normalize_ffprobe_payload,
)
from tegaki_core.media_kind import MediaKind
from tegaki_core.timebase import Timebase, create_timebase


class MediaDescriptorTests(unittest.TestCase):
    """Test suite for MediaDescriptor and ffprobe normalizer."""

    def test_create_image_descriptor(self):
        desc = create_image_descriptor(
            width=832,
            height=1216,
            format_label="PNG",
            file_size_bytes=1024000,
        )
        self.assertEqual(desc.kind, MediaKind.IMAGE)
        self.assertEqual(desc.width, 832)
        self.assertEqual(desc.height, 1216)
        self.assertEqual(desc.frame_count, 1)
        self.assertIsNone(desc.duration_seconds)
        self.assertIsNone(desc.timebase)
        self.assertEqual(desc.format_label, "PNG")
        self.assertEqual(desc.file_size_bytes, 1024000)

        # Aspect ratio
        self.assertEqual(desc.aspect_ratio, Fraction(832, 1216))
        self.assertEqual(desc.aspect_ratio, Fraction(13, 19))
        self.assertAlmostEqual(desc.aspect_ratio_float, 832 / 1216)

    def test_create_video_descriptor(self):
        tb = create_timebase(24)
        desc = create_video_descriptor(
            width=1920,
            height=1080,
            duration_seconds=Fraction(31, 6),
            timebase=tb,
            frame_count=124,
            format_label="H264",
            file_size_bytes=5242880,
        )
        self.assertEqual(desc.kind, MediaKind.VIDEO)
        self.assertEqual(desc.width, 1920)
        self.assertEqual(desc.height, 1080)
        self.assertEqual(desc.duration_seconds, Fraction(31, 6))
        self.assertEqual(desc.timebase, tb)
        self.assertEqual(desc.frame_count, 124)
        self.assertEqual(desc.format_label, "H264")
        self.assertEqual(desc.file_size_bytes, 5242880)

        self.assertEqual(desc.aspect_ratio, Fraction(16, 9))
        self.assertAlmostEqual(desc.duration_float, 5.166667, places=5)
        self.assertEqual(desc.fps_float, 24.0)

    def test_image_constraint_violations(self):
        # Non-zero duration rejected for image
        with self.assertRaises(ValueError):
            MediaDescriptor(
                kind=MediaKind.IMAGE,
                width=800,
                height=600,
                duration_seconds=Fraction(1, 1),
            )

        # Timebase rejected for image
        with self.assertRaises(ValueError):
            MediaDescriptor(
                kind=MediaKind.IMAGE,
                width=800,
                height=600,
                timebase=create_timebase(24),
            )

        # Frame count > 1 rejected for image
        with self.assertRaises(ValueError):
            MediaDescriptor(
                kind=MediaKind.IMAGE,
                width=800,
                height=600,
                frame_count=24,
            )

    def test_dimension_validations(self):
        # Zero or negative dimensions
        with self.assertRaises(ValueError):
            create_image_descriptor(width=0, height=100)
        with self.assertRaises(ValueError):
            create_image_descriptor(width=100, height=-5)

        # Non-integer / boolean dimensions
        with self.assertRaises(TypeError):
            create_image_descriptor(width=True, height=100)  # type: ignore
        with self.assertRaises(TypeError):
            create_image_descriptor(width=100, height=False)  # type: ignore
        with self.assertRaises(TypeError):
            create_image_descriptor(width=100.5, height=200)  # type: ignore

    def test_immutability(self):
        desc = create_image_descriptor(800, 600)
        with self.assertRaises(FrozenInstanceError):
            desc.width = 1000  # type: ignore
        with self.assertRaises(FrozenInstanceError):
            desc.height = 800  # type: ignore

    def test_determinism(self):
        desc1 = create_image_descriptor(800, 600, format_label="PNG")
        desc2 = create_image_descriptor(800, 600, format_label="png")
        self.assertEqual(desc1, desc2)
        self.assertEqual(hash(desc1), hash(desc2))

    def test_normalize_ffprobe_payload_h3_runner_fixture(self):
        # Replicates output from h3/tests/run_vp1_video_envelope.py
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 608,
                    "height": 352,
                    "avg_frame_rate": "24/1",
                    "nb_frames": "124",
                    "nb_read_frames": "124",
                }
            ],
            "format": {
                "duration": "5.166667",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            },
        }
        desc = normalize_ffprobe_payload(payload, file_size_bytes=3456789)
        self.assertEqual(desc.kind, MediaKind.VIDEO)
        self.assertEqual(desc.width, 608)
        self.assertEqual(desc.height, 352)
        self.assertEqual(desc.frame_count, 124)
        self.assertEqual(desc.timebase, Timebase(24, 1))
        self.assertAlmostEqual(desc.duration_float, 5.166667, places=5)
        self.assertEqual(desc.format_label, "H264")
        self.assertEqual(desc.file_size_bytes, 3456789)

    def test_normalize_ffprobe_payload_ntsc(self):
        # Replicates NTSC 24000/1001 video stream
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                    "avg_frame_rate": "24000/1001",
                    "nb_frames": "240",
                }
            ],
            "format": {
                "duration": "10.010000",
                "format_name": "mp4",
            },
        }
        desc = normalize_ffprobe_payload(payload)
        self.assertEqual(desc.kind, MediaKind.VIDEO)
        self.assertEqual(desc.width, 1280)
        self.assertEqual(desc.height, 720)
        self.assertEqual(desc.timebase, Timebase(24000, 1001))
        self.assertEqual(desc.frame_count, 240)
        self.assertAlmostEqual(desc.duration_float, 10.01, places=3)
        self.assertEqual(desc.format_label, "MP4")

    def test_normalize_ffprobe_payload_missing_optional_fields(self):
        payload = {
            "streams": [
                {
                    "width": "1920",
                    "height": "1080",
                    "avg_frame_rate": "0/0",
                }
            ]
        }
        desc = normalize_ffprobe_payload(payload)
        self.assertEqual(desc.width, 1920)
        self.assertEqual(desc.height, 1080)
        self.assertIsNone(desc.timebase)
        self.assertIsNone(desc.duration_seconds)
        self.assertIsNone(desc.frame_count)

    def test_normalize_ffprobe_payload_invalid_structure(self):
        with self.assertRaises(TypeError):
            normalize_ffprobe_payload("not_a_dict")  # type: ignore
        with self.assertRaises(ValueError):
            normalize_ffprobe_payload({})
        with self.assertRaises(ValueError):
            normalize_ffprobe_payload({"streams": []})
        with self.assertRaises(ValueError):
            normalize_ffprobe_payload({"streams": [{"codec_type": "audio"}]})


if __name__ == "__main__":
    unittest.main()
