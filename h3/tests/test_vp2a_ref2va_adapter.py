from __future__ import annotations

import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from h3.adapters.native_ref2va import (
    H3Ref2VARequest,
    RequestValidationError,
    REF2VA_MODEL,
    compile_workflow,
    workflow_metadata,
)


PICTURE = "inputs/vp2a_r1_picture_0123456789abcdef.png"
MOTION = "inputs/vp2a_r1_motion_0123456789abcdef.mp4"


class H3Ref2VAAdapterTests(unittest.TestCase):
    def test_workflow_contract_is_native_ref2va_and_bounded(self) -> None:
        metadata = workflow_metadata()
        self.assertEqual(metadata["schema"], "tegaki.h3.vp2a.native-ref2va/v1")
        self.assertEqual(metadata["baseline"]["width"], 608)
        self.assertEqual(metadata["baseline"]["height"], 352)
        self.assertEqual(metadata["baseline"]["frames"], 124)
        self.assertEqual(metadata["baseline"]["steps"], 20)

    def test_picture_only_graph_uses_one_picture_and_no_video_or_audio_reference(self) -> None:
        graph = compile_workflow(
            H3Ref2VARequest(
                prompt="Use <Picture 1> as the subject appearance reference.",
                picture_path=PICTURE,
            )
        )
        self.assertEqual(graph["127"]["inputs"]["unet_name"], REF2VA_MODEL)
        self.assertEqual(graph["131"]["inputs"]["ref_images.ref_image_1"], ["132", 0])
        self.assertNotIn("ref_videos.ref_video_1", graph["131"]["inputs"])
        self.assertNotIn("134", graph)
        self.assertNotIn("135", graph)
        self.assertFalse(
            any(
                key.startswith("ref_video_") or key.startswith("ref_audio_")
                for key in graph["131"]["inputs"]
            )
        )

    def test_picture_plus_video_graph_connects_video_frames_but_not_video_audio(self) -> None:
        graph = compile_workflow(
            H3Ref2VARequest(
                prompt="Use <Picture 1> for identity and <Video 1> for motion.",
                picture_path=PICTURE,
                video_path=MOTION,
                output_prefix="video/vp2a_r1_ref2va_picture_video",
            )
        )
        self.assertEqual(graph["131"]["inputs"]["ref_images.ref_image_1"], ["132", 0])
        self.assertEqual(graph["131"]["inputs"]["ref_videos.ref_video_1"], ["135", 0])
        self.assertEqual(graph["134"]["class_type"], "LoadVideo")
        self.assertEqual(graph["135"]["class_type"], "GetVideoComponents")
        self.assertNotIn("ref_video_audio_1", graph["131"]["inputs"])
        self.assertNotIn("ref_audio_1", graph["131"]["inputs"])

    def test_request_rejects_out_of_scope_values(self) -> None:
        invalid = [
            {"picture_path": "https://example.invalid/reference.png"},
            {"picture_path": "inputs/../outside.png"},
            {"picture_path": "C:/outside.png"},
            {"picture_path": "pictures/reference.png"},
            {"video_path": "inputs/reference.png"},
            {"width": 736},
            {"duration_seconds": 15.0},
            {"steps": 21},
        ]
        for override in invalid:
            with self.subTest(override=override):
                values: dict[str, object] = {
                    "prompt": "A bounded feasibility test.",
                    "picture_path": PICTURE,
                }
                values.update(override)
                with self.assertRaises(RequestValidationError):
                    H3Ref2VARequest(**values)


if __name__ == "__main__":
    unittest.main()
