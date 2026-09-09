"""Contract tests for the H2A feasibility-only still route."""

from __future__ import annotations

import unittest

from h3.adapters.native_still import (
    HEIGHT,
    PACKET_FRAMES,
    SELECTED_FRAME_INDEX,
    WIDTH,
    H3StillRequest,
    compile_workflow,
    validate_still_request,
    validate_workflow,
)
from h3.adapters.native_t2v import RequestValidationError


class H2AStillAdapterTests(unittest.TestCase):
    def test_default_text_only_request(self) -> None:
        request = validate_still_request({"prompt": "a red paper lantern"})
        self.assertEqual(request.width, WIDTH)
        self.assertEqual(request.height, HEIGHT)
        self.assertEqual(request.steps, 20)

    def test_rejects_references(self) -> None:
        with self.assertRaises(RequestValidationError):
            validate_still_request(
                {"prompt": "a red paper lantern", "references": {"start_frame": {}}}
            )

    def test_rejects_non_baseline_shape_or_steps(self) -> None:
        with self.assertRaises(RequestValidationError):
            validate_still_request({"prompt": "x", "width": 640})
        with self.assertRaises(RequestValidationError):
            validate_still_request({"prompt": "x", "steps": 8})

    def test_compiled_graph_selects_one_frame_without_video_output(self) -> None:
        request = H3StillRequest(prompt="a red paper lantern", seed=123)
        graph = compile_workflow(request)
        self.assertEqual(graph["131"]["inputs"]["length"], PACKET_FRAMES)
        self.assertEqual(graph["129"]["inputs"]["noise_seed"], 123)
        self.assertEqual(graph["132"]["inputs"]["batch_index"], SELECTED_FRAME_INDEX)
        self.assertEqual(graph["132"]["inputs"]["length"], 1)
        self.assertEqual(graph["92"]["class_type"], "SaveImage")
        self.assertNotIn("SaveVideo", {node["class_type"] for node in graph.values()})
        self.assertNotIn("CreateVideo", {node["class_type"] for node in graph.values()})
        roles = {
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
        }
        validate_workflow(
            {
                "schema": "tegaki.h3.h2a.native-still/v1",
                "semantic_nodes": {
                    role: {"id": node_id, "class_type": graph[node_id]["class_type"]}
                    for role, node_id in roles.items()
                },
                "prompt": graph,
            }
        )


if __name__ == "__main__":
    unittest.main()
