"""
test_reference_identity_analyzer.py
==================================
Unit tests for Manga Reference-to-Identity WD14 Local Analyzer.
Verifies:
1. Security and path traversal rejection.
2. Tag taxonomy index alignment.
3. Deterministic filtering of ratings, background, angle, and temporary expression tags.
4. Exactly ONE real WD14 CPU inference run on staged reference asset.
"""

import os
import sys
import json
import unittest

# Ensure service modules can be imported
SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "service"))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

import reference_identity_analyzer as analyzer

class TestReferenceIdentityAnalyzer(unittest.TestCase):

    def test_01_security_and_traversal_rejection(self):
        """Verify that malformed paths, path traversals and invalid extensions are strictly rejected."""
        invalid_inputs = [
            "",
            "   ",
            "../secret.png",
            "tegaki_manga_references/../../escaped.png",
            "foo/bar/test.png",
            "ref_test.gif",
            "ref_test.exe",
            "ref_test.txt"
        ]
        for bad_ref in invalid_inputs:
            with self.subTest(bad_ref=bad_ref):
                with self.assertRaises((ValueError, FileNotFoundError)):
                    analyzer.validate_and_resolve_asset(bad_ref)

    def test_02_taxonomy_csv_alignment(self):
        """Verify that selected_tags.csv is readable and has exactly 9083 tags."""
        csv_path = os.path.join(analyzer.DEFAULT_MODEL_DIR, "selected_tags.csv")
        self.assertTrue(os.path.exists(csv_path), f"Missing CSV: {csv_path}")

        import csv
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["tag_id", "name", "category", "count"])
            rows = list(reader)

        self.assertEqual(len(rows), 9083, "Expected exactly 9083 tags in selected_tags.csv")

    def test_03_deterministic_identity_filtering(self):
        """Verify that rating tags and non-identity general tags (background, expression, angle) are filtered out."""
        # Mock tag rows
        mock_tag_rows = [
            ["0", "general", "9", "1000"],          # Rating tag
            ["1", "sensitive", "9", "200"],         # Rating tag
            ["2", "white_background", "0", "500"],  # Background tag (exclude)
            ["3", "smile", "0", "400"],             # Expression tag (exclude)
            ["4", "cowboy_shot", "0", "300"],       # Camera angle (exclude)
            ["5", "1girl", "0", "2000"],            # Stable identity tag (keep)
            ["6", "blue_hair", "0", "600"],         # Stable identity tag (keep)
            ["7", "school_uniform", "0", "550"],    # Stable identity tag (keep)
            ["8", "glasses", "0", "500"]            # Stable identity tag (keep)
        ]
        # Probabilities
        probs = [0.95, 0.05, 0.88, 0.75, 0.70, 0.92, 0.85, 0.80, 0.72]

        result = analyzer.filter_tags_for_identity(probs, mock_tag_rows, confidence_threshold=0.35)
        
        # Check ratings extracted separately
        self.assertEqual(result["ratings"]["general"], 0.95)
        self.assertEqual(result["ratings"]["sensitive"], 0.05)

        # Check candidate excludes rating, background, smile, cowboy_shot
        tags = result["tags"]
        self.assertNotIn("general", tags)
        self.assertNotIn("sensitive", tags)
        self.assertNotIn("white_background", tags)
        self.assertNotIn("smile", tags)
        self.assertNotIn("cowboy_shot", tags)

        # Check candidate keeps identity features sorted by confidence
        self.assertEqual(tags, ["1girl", "blue_hair", "school_uniform", "glasses"])
        self.assertEqual(result["candidate"], "1girl, blue_hair, school_uniform, glasses")

    def test_04_single_real_cpu_inference_run(self):
        """
        MAX REAL WD14 CPU INFERENCE RUNS: ONE.
        Executes exactly one real CPU inference on staged ref_c789751db904319d.png.
        """
        test_ref = "tegaki_manga_references/ref_c789751db904319d.png"
        ref_path = analyzer.validate_and_resolve_asset(test_ref)
        self.assertTrue(os.path.exists(ref_path))

        result = analyzer.analyze_character_reference(test_ref, confidence_threshold=0.35)

        self.assertTrue(result["ok"])
        self.assertEqual(result["execution_provider"], "CPUExecutionProvider")
        self.assertEqual(result["model"], "SmilingWolf/wd-v1-4-convnext-tagger-v2")
        self.assertIsInstance(result["candidate"], str)
        self.assertGreater(len(result["candidate"]), 0)

        # Verify prominent traits detected in previous probe
        self.assertIn("1girl", result["tags"])
        self.assertIn("long_hair", result["tags"])
        self.assertIn("school_uniform", result["tags"])

        # Verify ratings were extracted (sensitive was 0.6591 in probe)
        self.assertIn("general", result["ratings"])
        self.assertIn("sensitive", result["ratings"])
        self.assertGreater(result["ratings"]["sensitive"], 0.5)

        # Verify candidate formatting (comma separated)
        self.assertEqual(result["candidate"], ", ".join(result["tags"]))
        print(f"\n[REAL WD14 CPU TEST PASS] Candidate:\n{result['candidate']}")

if __name__ == "__main__":
    unittest.main()
