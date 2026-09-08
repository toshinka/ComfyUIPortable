from __future__ import annotations

import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from h3.adapters.native_i2v import (  # noqa: E402
    compile_workflow as compile_i2v,
    validate_workflow as validate_i2v_workflow,
    workflow_metadata as i2v_workflow_metadata,
)
from h3.adapters.native_t2v import (  # noqa: E402
    H3Request,
    H3Reference,
    RequestValidationError,
    ROUTE_I2V,
    ROUTE_T2V,
    WorkflowIncompatibleError,
    compile_workflow as compile_t2v,
    resolve_route,
    validate_request,
)


class H1BAdapterTests(unittest.TestCase):
    def test_route_resolver_uses_reference_presence(self):
        self.assertEqual(resolve_route(None), ROUTE_T2V)
        self.assertEqual(resolve_route(H3Reference("a" * 32)), ROUTE_I2V)
        self.assertEqual(
            resolve_route({"id": "b" * 32, "role": "start_frame"}),
            ROUTE_I2V,
        )

    def test_unknown_reference_role_fails_closed(self):
        with self.assertRaisesRegex(RequestValidationError, "unsupported"):
            validate_request(
                {
                    "prompt": "a quiet greenhouse",
                    "reference": {"id": "a" * 32, "role": "identity"},
                }
            )

    def test_reference_id_validation_fails_closed(self):
        with self.assertRaisesRegex(RequestValidationError, "id is invalid"):
            validate_request(
                {
                    "prompt": "a quiet greenhouse",
                    "reference": {"id": "../escape", "role": "start_frame"},
                }
            )

    def test_i2v_compile_binds_only_first_frame(self):
        request = validate_request(
            {
                "prompt": "a quiet greenhouse moves in a gentle breeze",
                "width": 608,
                "height": 352,
                "duration": 5,
                "seed": 123,
                "steps": 20,
                "reference": {"id": "a" * 32, "role": "start_frame"},
            }
        )
        graph = compile_i2v(request, f"inputs/{'a' * 32}.png")
        self.assertEqual(graph["132"]["inputs"]["image"], f"inputs/{'a' * 32}.png")
        self.assertEqual(graph["131"]["inputs"]["first_frame"], ["132", 0])
        self.assertNotIn("last_frame", graph["131"]["inputs"])
        self.assertEqual(graph["131"]["inputs"]["length"], 124)
        self.assertEqual(graph["92"]["inputs"]["filename_prefix"], "video/h1b_native_i2v")

    def test_i2v_compile_rejects_unsafe_reference_path(self):
        request = H3Request(
            prompt="a quiet greenhouse",
            reference=H3Reference("a" * 32),
        )
        for path in ("../escape.png", r"inputs\escape.png", "C:/escape.png"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(RequestValidationError, "path is invalid"):
                    compile_i2v(request, path)

    def test_workflow_metadata_and_validation_are_separate_from_h1a(self):
        metadata = i2v_workflow_metadata()
        self.assertEqual(metadata["schema"], "tegaki.h3.h1b.native-i2v/v1")
        self.assertIn("official_workflow_commit", metadata["source"])
        self.assertEqual(metadata["baseline"]["reference_role"], "start_frame")

        # T2V remains a no-reference graph and does not acquire the H1B loader.
        t2v_graph = compile_t2v(H3Request(prompt="text only"))
        self.assertNotIn("132", t2v_graph)

    def test_i2v_workflow_rejects_last_frame_binding(self):
        metadata = i2v_workflow_metadata()
        workflow = {
            "schema": metadata["schema"],
            "semantic_nodes": {
                "conditioning_latent": {"id": "131", "class_type": "MiniMaxH3ImageToVideo"},
                "load_image": {"id": "132", "class_type": "LoadImage"},
            },
            "prompt": {
                "131": {
                    "class_type": "MiniMaxH3ImageToVideo",
                    "inputs": {"first_frame": ["132", 0], "last_frame": ["132", 0]},
                },
                "132": {"class_type": "LoadImage", "inputs": {}},
            },
        }
        with self.assertRaises(WorkflowIncompatibleError):
            validate_i2v_workflow(workflow)


if __name__ == "__main__":
    unittest.main()
