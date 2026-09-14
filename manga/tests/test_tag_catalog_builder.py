#!/usr/bin/env python3
"""
Unit tests for Manga Tag Catalog Builder (manga/tools/build_tag_catalog.py).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from manga.tools.build_tag_catalog import (
    build_catalog_from_csv,
    write_catalog_json,
    normalize_category,
    parse_ranking
)

FIXTURES_DIR = REPO_ROOT / "manga" / "tests" / "fixtures"


class TestTagCatalogBuilder(unittest.TestCase):
    def setUp(self):
        self.sample_csv = FIXTURES_DIR / "sample_tags.csv"

    def test_ranking_parsing(self):
        self.assertEqual(parse_ranking("100"), 100)
        self.assertEqual(parse_ranking("  42  "), 42)
        self.assertEqual(parse_ranking("123.45"), 123)
        self.assertEqual(parse_ranking("", 0), 0)
        self.assertEqual(parse_ranking(None, 0), 0)
        self.assertEqual(parse_ranking("invalid", 0), 0)

    def test_category_normalization(self):
        self.assertEqual(normalize_category("0"), "general")
        self.assertEqual(normalize_category("1"), "artist")
        self.assertEqual(normalize_category("3"), "copyright")
        self.assertEqual(normalize_category("4"), "character")
        self.assertEqual(normalize_category("5"), "meta")
        self.assertEqual(normalize_category("General"), "general")
        self.assertEqual(normalize_category("ARTIST"), "artist")
        self.assertEqual(normalize_category(""), "")
        self.assertEqual(normalize_category(None), "")

    def test_build_from_sample_csv(self):
        entries, stats = build_catalog_from_csv(self.sample_csv)

        # 10 rows in CSV, 1 empty tag skipped, 2 duplicates resolved = 7 unique tags
        self.assertEqual(stats["total_rows_read"], 10)
        self.assertEqual(stats["skipped_empty"], 1)
        self.assertEqual(stats["unique_tags"], 7)
        self.assertEqual(len(entries), 7)

        # Expected tags in deterministic order: (-ranking, tag)
        expected = [
            {"tag": "1girl", "category": "general", "ranking": 900},
            {"tag": "duplicate_tag", "category": "general", "ranking": 500},
            {"tag": "blue_eyes", "category": "character", "ranking": 400},
            {"tag": "artist_name", "category": "artist", "ranking": 300},
            {"tag": "solo", "category": "general", "ranking": 200},
            {"tag": "alpha_tag", "category": "general", "ranking": 100},
            {"tag": "beta_tag", "category": "general", "ranking": 100},
        ]
        self.assertEqual(entries, expected)

    def test_write_and_load_json(self):
        entries, _ = build_catalog_from_csv(self.sample_csv)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_catalog.json"
            size = write_catalog_json(entries, out_file)
            self.assertTrue(out_file.is_file())
            self.assertGreater(size, 0)

            with open(out_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded, entries)
            # Verify compact JSON: no extra spaces around colons/commas
            raw_text = out_file.read_text(encoding="utf-8")
            self.assertNotIn(": ", raw_text)
            self.assertNotIn(", ", raw_text)


if __name__ == "__main__":
    unittest.main()
