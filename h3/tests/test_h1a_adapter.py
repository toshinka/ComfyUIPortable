from __future__ import annotations

import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from h3.adapters.native_t2v import (
    H3Request,
    RequestValidationError,
    WorkflowIncompatibleError,
    compile_workflow,
    duration_to_frames,
    validate_request,
    validate_workflow,
    workflow_metadata,
)


class H1AAdapterTests(unittest.TestCase):
    def test_duration_uses_verified_h3_frame_grid(self) -> None:
        self.assertEqual(duration_to_frames(5), 124)
        self.assertEqual(duration_to_frames(2), 56)
        self.assertEqual(duration_to_frames(0.2), 5)

    def test_validate_request_keeps_user_contract_small(self) -> None:
        request = validate_request(
            {
                "prompt": "a quiet greenhouse",
                "width": 608,
                "height": 352,
                "duration": 5,
                "seed": 123,
                "steps": 20,
            }
        )
        self.assertEqual(request.public()["seed"], 123)
        self.assertEqual(request.public()["duration"], 5.0)

    def test_invalid_request_values_fail_closed(self) -> None:
        invalid = [
            ({"prompt": ""}, "Prompt"),
            ({"prompt": "ok", "width": 864, "height": 480}, "608"),
            ({"prompt": "ok", "steps": 8}, "20-step"),
            ({"prompt": "ok", "duration": 20}, "between"),
            ({"prompt": "ok", "duration": None}, "number"),
        ]
        for payload, expected in invalid:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(RequestValidationError, expected):
                    validate_request(payload)

    def test_compile_replaces_only_semantic_user_inputs(self) -> None:
        graph = compile_workflow(
            H3Request(
                prompt="a red robot walks",
                width=608,
                height=352,
                duration=5,
                seed=987,
                steps=20,
            )
        )
        self.assertEqual(graph["131"]["inputs"]["prompt"], "a red robot walks")
        self.assertEqual(graph["131"]["inputs"]["length"], 124)
        self.assertEqual(graph["129"]["inputs"]["noise_seed"], 987)
        self.assertEqual(graph["124"]["inputs"]["steps"], 20)
        self.assertNotIn("134", graph)
        self.assertNotIn("LoraLoaderModelOnly", {node["class_type"] for node in graph.values()})

    def test_workflow_metadata_is_auditable(self) -> None:
        metadata = workflow_metadata()
        self.assertEqual(metadata["schema"], "tegaki.h3.h1a.native-t2v/v1")
        self.assertIn("official_workflow_commit", metadata["source"])
        self.assertEqual(metadata["baseline"]["turbo_lora"], False)

    def test_workflow_validation_rejects_stale_role(self) -> None:
        metadata = workflow_metadata()
        # The production loader is responsible for the full check; this test
        # fixes the fail-closed behavior independently of any backend process.
        with self.assertRaises(WorkflowIncompatibleError):
            validate_workflow(
                {
                    "schema": "tegaki.h3.h1a.native-t2v/v1",
                    "semantic_nodes": {"model": {"id": "127", "class_type": "WrongNode"}},
                    "prompt": {"127": {"class_type": "UNETLoader", "inputs": {}}},
                }
            )
        self.assertEqual(metadata["baseline"]["width"], 608)


if __name__ == "__main__":
    unittest.main()
