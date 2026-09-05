"""
Test: Phase 3L Visual Provenance Contract
==========================================
Verifies that:
- runtime status PASS never automatically assigns visual status PASS.
- visual provenance schema requires:
    - runtime_status ("PASS" | "FAIL")
    - visual_status ("PASS" | "PARTIAL" | "FAIL" | "PENDING")
    - evaluation_source ("AI_VISUAL_ANNOTATION" | "USER_VISUAL_REVIEW" | "NONE")
    - machine_detector (bool)
    - confidence (float or None)
- If evaluation_source is "NONE", visual_status MUST be "PENDING".
"""

import os
import sys
import unittest
from typing import Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def validate_visual_provenance(record: Dict[str, Any]) -> None:
    required_keys = {"runtime_status", "visual_status", "evaluation_source", "machine_detector", "confidence"}
    missing = required_keys - set(record.keys())
    if missing:
        raise ValueError(f"Missing required provenance keys: {sorted(list(missing))}")

    valid_runtime = {"PASS", "FAIL"}
    valid_visual = {"PASS", "PARTIAL", "FAIL", "PENDING"}
    valid_sources = {"AI_VISUAL_ANNOTATION", "USER_VISUAL_REVIEW", "NONE"}

    if record["runtime_status"] not in valid_runtime:
        raise ValueError(f"Invalid runtime_status '{record['runtime_status']}'. Must be {valid_runtime}")

    if record["visual_status"] not in valid_visual:
        raise ValueError(f"Invalid visual_status '{record['visual_status']}'. Must be {valid_visual}")

    if record["evaluation_source"] not in valid_sources:
        raise ValueError(f"Invalid evaluation_source '{record['evaluation_source']}'. Must be {valid_sources}")

    if not isinstance(record["machine_detector"], bool):
        raise ValueError(f"machine_detector must be a bool, got {type(record['machine_detector']).__name__}")

    # Strict decoupling: runtime PASS does NOT imply visual PASS
    if record["evaluation_source"] == "NONE" and record["visual_status"] != "PENDING":
        raise ValueError("When evaluation_source is 'NONE', visual_status must be 'PENDING'!")

    if record["confidence"] is not None:
        if not isinstance(record["confidence"], (int, float)) or not (0.0 <= record["confidence"] <= 1.0):
            raise ValueError(f"confidence must be float [0.0..1.0] or None, got {record['confidence']!r}")


class TestPhase3LVisualProvenanceContract(unittest.TestCase):

    def test_valid_provenance_pending(self):
        rec = {
            "runtime_status": "PASS",
            "visual_status": "PENDING",
            "evaluation_source": "NONE",
            "machine_detector": False,
            "confidence": None
        }
        # Should pass without error
        validate_visual_provenance(rec)

    def test_valid_provenance_ai_annotation(self):
        rec = {
            "runtime_status": "PASS",
            "visual_status": "PASS",
            "evaluation_source": "AI_VISUAL_ANNOTATION",
            "machine_detector": True,
            "confidence": 0.95
        }
        validate_visual_provenance(rec)

    def test_reject_auto_visual_pass_without_source(self):
        rec = {
            "runtime_status": "PASS",
            "visual_status": "PASS",  # ILLEGAL when source is NONE!
            "evaluation_source": "NONE",
            "machine_detector": False,
            "confidence": None
        }
        with self.assertRaises(ValueError):
            validate_visual_provenance(rec)

    def test_reject_invalid_status_enums(self):
        rec = {
            "runtime_status": "SUCCESS",  # Invalid
            "visual_status": "PENDING",
            "evaluation_source": "NONE",
            "machine_detector": False,
            "confidence": None
        }
        with self.assertRaises(ValueError):
            validate_visual_provenance(rec)


if __name__ == "__main__":
    unittest.main()
