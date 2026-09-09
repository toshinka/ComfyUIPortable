from __future__ import annotations

import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from h3.adapters.native_i2v import (  # noqa: E402
    compile_fl2va_workflow,
    fl2va_workflow_metadata,
    validate_fl2va_workflow,
)
from h3.adapters.native_t2v import (  # noqa: E402
    H3ReferenceSlots,
    RequestValidationError,
    ROUTE_I2V,
    ROUTE_T2V,
    WorkflowIncompatibleError,
    resolve_route,
    validate_request,
)


def reference(reference_id: str, role: str) -> dict[str, str]:
    return {"id": reference_id, "role": role}


class H1B1AdapterTests(unittest.TestCase):
    def test_route_resolver_uses_fixed_slot_presence(self):
        self.assertEqual(resolve_route(None), ROUTE_T2V)
        self.assertEqual(
            resolve_route({"start_frame": reference("a" * 32, "start_frame")}),
            ROUTE_I2V,
        )
        self.assertEqual(
            resolve_route({"end_frame": reference("b" * 32, "end_frame")}),
            ROUTE_I2V,
        )
        self.assertEqual(
            resolve_route(
                {
                    "start_frame": reference("a" * 32, "start_frame"),
                    "end_frame": reference("b" * 32, "end_frame"),
                }
            ),
            ROUTE_I2V,
        )

    def test_canonical_request_normalization_and_legacy_start_reference(self):
        empty = validate_request({"prompt": "text only", "references": None})
        self.assertEqual(empty.references, H3ReferenceSlots())
        self.assertFalse(empty.legacy_reference)

        canonical = validate_request(
            {
                "prompt": "two keyframes",
                "references": {
                    "start_frame": reference("a" * 32, "start_frame"),
                    "end_frame": reference("b" * 32, "end_frame"),
                },
            }
        )
        self.assertEqual(canonical.references.start_frame.id, "a" * 32)
        self.assertEqual(canonical.references.end_frame.id, "b" * 32)
        self.assertFalse(canonical.legacy_reference)

        legacy = validate_request(
            {
                "prompt": "old H1B",
                "reference": reference("c" * 32, "start_frame"),
            }
        )
        self.assertTrue(legacy.legacy_reference)
        self.assertEqual(legacy.references.start_frame.id, "c" * 32)
        self.assertIsNone(legacy.references.end_frame)

    def test_invalid_slot_role_and_malformed_id_fail_closed(self):
        with self.assertRaisesRegex(RequestValidationError, "must be end_frame"):
            validate_request(
                {
                    "prompt": "bad role",
                    "references": {
                        "end_frame": reference("a" * 32, "start_frame")
                    },
                }
            )
        with self.assertRaisesRegex(RequestValidationError, "id is invalid"):
            validate_request(
                {
                    "prompt": "bad id",
                    "references": {
                        "start_frame": reference("../escape", "start_frame")
                    },
                }
            )
        with self.assertRaisesRegex(RequestValidationError, "unsupported"):
            validate_request(
                {
                    "prompt": "bad slot",
                    "references": {"identity": reference("a" * 32, "identity")},
                }
            )

    def test_fl2va_workflow_start_only_has_no_end_loader_or_edge(self):
        request = validate_request(
            {
                "prompt": "start only",
                "references": {
                    "start_frame": reference("a" * 32, "start_frame"),
                    "end_frame": None,
                },
            }
        )
        graph = compile_fl2va_workflow(
            request,
            {"start_frame": f"inputs/{'a' * 32}.png"},
        )
        self.assertEqual(graph["131"]["inputs"]["first_frame"], ["132", 0])
        self.assertNotIn("last_frame", graph["131"]["inputs"])
        self.assertNotIn("133", graph)
        self.assertEqual(graph["132"]["inputs"]["image"], f"inputs/{'a' * 32}.png")

    def test_fl2va_workflow_end_only_has_no_start_loader_or_edge(self):
        request = validate_request(
            {
                "prompt": "end only",
                "references": {
                    "start_frame": None,
                    "end_frame": reference("b" * 32, "end_frame"),
                },
            }
        )
        graph = compile_fl2va_workflow(
            request,
            {"end_frame": f"inputs/{'b' * 32}.png"},
        )
        self.assertNotIn("first_frame", graph["131"]["inputs"])
        self.assertEqual(graph["131"]["inputs"]["last_frame"], ["133", 0])
        self.assertNotIn("132", graph)
        self.assertEqual(graph["133"]["inputs"]["image"], f"inputs/{'b' * 32}.png")

    def test_fl2va_workflow_binds_both_edges_and_baseline(self):
        request = validate_request(
            {
                "prompt": "between keyframes",
                "width": 608,
                "height": 352,
                "duration": 5,
                "seed": 17,
                "steps": 20,
                "references": {
                    "start_frame": reference("a" * 32, "start_frame"),
                    "end_frame": reference("b" * 32, "end_frame"),
                },
            }
        )
        graph = compile_fl2va_workflow(
            request,
            {
                "start_frame": f"inputs/{'a' * 32}.png",
                "end_frame": f"inputs/{'b' * 32}.jpg",
            },
        )
        self.assertEqual(graph["131"]["inputs"]["first_frame"], ["132", 0])
        self.assertEqual(graph["131"]["inputs"]["last_frame"], ["133", 0])
        self.assertIn("132", graph)
        self.assertIn("133", graph)
        self.assertEqual(graph["129"]["inputs"]["noise_seed"], 17)
        self.assertEqual(graph["124"]["inputs"]["steps"], 20)
        self.assertEqual(graph["92"]["inputs"]["filename_prefix"], "video/h1b1_native_fl2va")

    def test_fl2va_workflow_rejects_mismatched_paths_and_stale_edges(self):
        request = validate_request(
            {
                "prompt": "safe paths",
                "references": {"start_frame": reference("a" * 32, "start_frame")},
            }
        )
        for paths in ({"end_frame": "inputs/end.png"}, {"start_frame": "../escape.png"}):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(RequestValidationError, "Reference"):
                    compile_fl2va_workflow(request, paths)

        metadata = fl2va_workflow_metadata()
        stale = {
            "schema": metadata["schema"],
            "semantic_nodes": {
                "image_to_video": {"id": "131", "class_type": "MiniMaxH3ImageToVideo"},
                "start_image_loader": {"id": "132", "class_type": "LoadImage"},
                "end_image_loader": {"id": "133", "class_type": "LoadImage"},
            },
            "prompt": {
                "131": {
                    "class_type": "MiniMaxH3ImageToVideo",
                    "inputs": {"first_frame": ["133", 0]},
                },
                "132": {"class_type": "LoadImage", "inputs": {}},
                "133": {"class_type": "LoadImage", "inputs": {}},
            },
        }
        with self.assertRaises(WorkflowIncompatibleError):
            validate_fl2va_workflow(stale)

    def test_fl2va_metadata_records_current_official_source(self):
        metadata = fl2va_workflow_metadata()
        self.assertEqual(metadata["schema"], "tegaki.h3.h1b1.native-fl2va/v1")
        self.assertEqual(
            metadata["source"]["official_workflow_commit"],
            "66abae5205f7c5105281146fa109f7c12801d268",
        )
        self.assertEqual(metadata["baseline"]["reference_roles"], ["start_frame", "end_frame"])


if __name__ == "__main__":
    unittest.main()
