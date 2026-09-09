"""Contract tests for the H2B single-source anchored still route."""

from __future__ import annotations

import unittest

from h3.adapters.native_source_anchored_still import (
    SCHEMA,
    H3SourceAnchorRequest,
    compile_prompt_only_workflow,
    compile_workflow,
    validate_source_anchor_request,
    validate_workflow,
)
from h3.adapters.native_still import H3StillRequest, PACKET_FRAMES, SELECTED_FRAME_INDEX
from h3.adapters.native_t2v import RequestValidationError


SOURCE_PATH = "inputs/h2b_source_0123456789abcdef.png"


class H2BSourceAnchoredStillTests(unittest.TestCase):
    def test_accepts_exactly_one_safe_source_path(self) -> None:
        request = validate_source_anchor_request(
            {
                "prompt": "retain the subject and change the lighting",
                "source_path": SOURCE_PATH,
                "seed": 123,
            }
        )
        self.assertEqual(request.source_path, SOURCE_PATH)
        self.assertEqual(request.seed, 123)

    def test_rejects_remote_external_or_multiple_source_values(self) -> None:
        for value in (
            "https://example.test/source.png",
            "file://C:/source.png",
            "C:/source.png",
            "inputs/sub/source.png",
            "inputs/source.webp",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RequestValidationError):
                    validate_source_anchor_request(
                        {"prompt": "x", "source_path": value}
                    )
        with self.assertRaises(RequestValidationError):
            validate_source_anchor_request(
                {
                    "prompt": "x",
                    "source_path": SOURCE_PATH,
                    "source_images": [SOURCE_PATH, SOURCE_PATH],
                }
            )
        with self.assertRaises(RequestValidationError):
            validate_source_anchor_request(
                {"prompt": "x", "source_path": [SOURCE_PATH]}
            )

    def test_rejects_non_baseline_shape_or_steps(self) -> None:
        for field, value in (("width", 640), ("height", 640), ("steps", 8)):
            with self.subTest(field=field):
                with self.assertRaises(RequestValidationError):
                    validate_source_anchor_request(
                        {"prompt": "x", "source_path": SOURCE_PATH, field: value}
                    )

    def test_compiled_graph_binds_one_first_frame_and_selects_one_frame(self) -> None:
        request = H3SourceAnchorRequest(
            prompt="retain the subject and change the lighting",
            source_path=SOURCE_PATH,
            seed=123,
        )
        graph = compile_workflow(request)
        self.assertEqual(graph["131"]["inputs"]["length"], PACKET_FRAMES)
        self.assertEqual(graph["131"]["inputs"]["first_frame"], ["133", 0])
        self.assertEqual(graph["133"]["inputs"]["image"], SOURCE_PATH)
        self.assertEqual(graph["132"]["inputs"]["batch_index"], SELECTED_FRAME_INDEX)
        self.assertEqual(graph["132"]["inputs"]["length"], 1)
        self.assertEqual(graph["92"]["class_type"], "SaveImage")
        self.assertEqual(
            sum(node["class_type"] == "LoadImage" for node in graph.values()), 1
        )
        self.assertNotIn("SaveVideo", {node["class_type"] for node in graph.values()})
        self.assertNotIn("CreateVideo", {node["class_type"] for node in graph.values()})
        validate_workflow(
            {
                "schema": SCHEMA,
                "semantic_nodes": {
                    role: {"id": node_id, "class_type": graph[node_id]["class_type"]}
                    for role, node_id in {
                        "save_image": "92",
                        "video_vae": "119",
                        "video_decode": "122",
                        "sampler_select": "123",
                        "scheduler": "124",
                        "sampler": "125",
                        "guider": "126",
                        "model": "127",
                        "text_encoder": "128",
                        "noise": "129",
                        "conditioning_latent": "131",
                        "select_frame": "132",
                        "source_image_loader": "133",
                    }.items()
                },
                "prompt": graph,
            }
        )

    def test_prompt_only_control_removes_source_edge_and_loader(self) -> None:
        graph = compile_prompt_only_workflow(
            H3StillRequest(
                prompt="retain the subject and change the lighting", seed=123
            )
        )
        self.assertNotIn("first_frame", graph["131"]["inputs"])
        self.assertNotIn("133", graph)
        self.assertEqual(graph["131"]["inputs"]["length"], PACKET_FRAMES)
        self.assertEqual(graph["92"]["inputs"]["filename_prefix"], "still/h2b_prompt_only")


if __name__ == "__main__":
    unittest.main()
