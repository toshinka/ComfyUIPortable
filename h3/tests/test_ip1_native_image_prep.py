"""Contract tests for the bounded IP1 Native image-prep feasibility route."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.adapters.native_image_prep import (
    DONOR_IMAGE_ROLE,
    H3ImagePrepRequest,
    PACKET_FRAMES,
    ROUTE_IMAGE_PREP,
    SOURCE_IMAGE_ROLE,
    materialize_prompt,
    compile_workflow,
    validate_request,
    validate_workflow,
    workflow_metadata,
)
from h3.adapters.native_ref2va import (
    H3Ref2VARequest,
    compile_workflow as compile_ref2va_workflow,
)
from h3.adapters.native_t2v import RequestValidationError


SOURCE = "inputs/ip1_source_0123456789abcdef.png"
DONOR = "inputs/ip1_donor_0123456789abcdef.png"


class IP1NativeImagePrepTests(unittest.TestCase):
    def test_metadata_identifies_native_ref2va_and_frame_zero_output(self) -> None:
        metadata = workflow_metadata()
        self.assertEqual(metadata["route"], ROUTE_IMAGE_PREP)
        self.assertEqual(metadata["schema"], "tegaki.h3.ip1.native-image-prep/v1")
        self.assertEqual(metadata["baseline"]["width"], 608)
        self.assertEqual(metadata["baseline"]["height"], 352)
        self.assertEqual(metadata["baseline"]["packet_frames"], PACKET_FRAMES)
        self.assertEqual(metadata["baseline"]["selected_frame_index"], 0)
        self.assertEqual(metadata["baseline"]["steps"], 20)
        self.assertEqual(metadata["baseline"]["ref_image_size"], "match")
        self.assertEqual(metadata["audio_reference"], "not connected")
        self.assertEqual(metadata["browser_ui"], "NOT IMPLEMENTED")

    def test_source_only_binds_picture_one_and_removes_optional_donor(self) -> None:
        request = H3ImagePrepRequest(
            prompt="Change only the weather to gentle rain.",
            source_path=SOURCE,
            seed=77,
        )
        graph = compile_workflow(request)
        conditioning = graph["131"]["inputs"]
        self.assertEqual(conditioning["ref_images.ref_image_1"], ["133", 0])
        self.assertNotIn("ref_images.ref_image_2", conditioning)
        self.assertNotIn("134", graph)
        self.assertEqual(graph["133"]["inputs"]["image"], SOURCE)
        self.assertEqual(conditioning["length"], PACKET_FRAMES)
        self.assertEqual(conditioning["width"], 608)
        self.assertEqual(conditioning["height"], 352)
        self.assertEqual(graph["129"]["inputs"]["noise_seed"], 77)

        classes = {node["class_type"] for node in graph.values()}
        self.assertIn("MiniMaxH3ReferenceToVideo", classes)
        self.assertIn("SaveImage", classes)
        self.assertNotIn("SaveVideo", classes)
        self.assertNotIn("CreateVideo", classes)
        self.assertNotIn("VAEDecodeAudio", classes)
        self.assertNotIn("LoadVideo", classes)
        self.assertFalse(any(key.startswith(("ref_video", "ref_audio")) for key in conditioning))

    def test_source_plus_donor_has_deterministic_picture_roles(self) -> None:
        original, materialized = materialize_prompt("  Transfer one coat attribute.  ", has_donor=True)
        self.assertEqual(original, "Transfer one coat attribute.")
        self.assertLess(materialized.index("<Picture 1>"), materialized.index("<Picture 2>"))
        self.assertIn("source subject and composition reference", materialized)
        self.assertIn("donor for the requested attribute", materialized)
        self.assertNotIn("<Picture 3>", materialized)

        graph = compile_workflow(
            H3ImagePrepRequest(
                prompt=original,
                source_path=SOURCE,
                donor_path=DONOR,
                seed=77,
            )
        )
        conditioning = graph["131"]["inputs"]
        self.assertEqual(conditioning["ref_images.ref_image_1"], ["133", 0])
        self.assertEqual(conditioning["ref_images.ref_image_2"], ["134", 0])
        self.assertEqual(graph["133"]["inputs"]["image"], SOURCE)
        self.assertEqual(graph["134"]["inputs"]["image"], DONOR)
        self.assertEqual(graph["132"]["inputs"]["image"], ["122", 0])
        self.assertEqual(graph["132"]["inputs"]["batch_index"], 0)
        self.assertEqual(graph["132"]["inputs"]["length"], 1)
        self.assertEqual(graph["92"]["class_type"], "SaveImage")

    def test_validate_workflow_keeps_base_roles_and_frame_zero_contract(self) -> None:
        from h3.adapters.native_image_prep import _load_workflow

        workflow = _load_workflow()
        validate_workflow(workflow)
        roles = workflow["semantic_nodes"]
        self.assertEqual(roles[SOURCE_IMAGE_ROLE]["id"], "133")
        self.assertEqual(roles[DONOR_IMAGE_ROLE]["id"], "134")
        self.assertEqual(workflow["prompt"]["131"]["class_type"], "MiniMaxH3ReferenceToVideo")

    def test_rejects_third_fourth_video_audio_remote_and_traversal_inputs(self) -> None:
        invalid_payloads = [
            {"third_picture_path": DONOR},
            {"fourth_picture_path": DONOR},
            {"references": [SOURCE, DONOR, "inputs/third.png"]},
            {"video_path": "inputs/motion.mp4"},
            {"audio_path": "inputs/audio.wav"},
            {"source_path": "C:/outside.png"},
            {"source_path": "file:///outside.png"},
            {"source_path": "https://example.invalid/source.png"},
            {"source_path": "inputs/../outside.png"},
            {"source_path": "inputs/subdir/source.png"},
            {"source_path": "inputs/source.gif"},
        ]
        for override in invalid_payloads:
            with self.subTest(override=override):
                payload: dict[str, object] = {
                    "prompt": "bounded IP1 request",
                    "source_path": SOURCE,
                }
                payload.update(override)
                with self.assertRaises(RequestValidationError):
                    validate_request(payload)

    def test_rejects_non_baseline_dimensions_steps_length_or_fps(self) -> None:
        for override in (
            {"width": 736},
            {"height": 416},
            {"steps": 21},
            {"length": 1},
            {"length": 22},
            {"fps": 30},
        ):
            with self.subTest(override=override):
                payload: dict[str, object] = {
                    "prompt": "bounded IP1 request",
                    "source_path": SOURCE,
                }
                payload.update(override)
                with self.assertRaises(RequestValidationError):
                    validate_request(payload)

    def test_vp2b_ref2va_contract_remains_video_reference_route(self) -> None:
        graph = compile_ref2va_workflow(
            H3Ref2VARequest(
                prompt="Use Picture 1 as the subject.",
                picture_path="inputs/vp2b_picture_0123456789abcdef.png",
            )
        )
        self.assertEqual(graph["131"]["class_type"], "MiniMaxH3ReferenceToVideo")
        self.assertEqual(graph["131"]["inputs"]["length"], 124)
        self.assertEqual(graph["92"]["class_type"], "SaveVideo")
        self.assertIn("129", graph)
        self.assertEqual(graph["127"]["inputs"]["unet_name"], "minimax_h3_ref2va_pruned_int8_convrot.safetensors")


if __name__ == "__main__":
    unittest.main()
