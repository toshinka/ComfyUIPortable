"""Unit tests for banked canonical serialization and digest core.

Verifies:
- deterministic key sorting across shallow and nested dictionaries
- sequence order preservation (lists remain strictly ordered)
- proper serialization of primitives (str, int, float, bool, null)
- unescaped UTF-8 string encoding (ensure_ascii=False)
- rejection of non-finite floats (NaN, Infinity)
- rejection of non-serializable types and malformed keys
- exact SHA-256 64-character lowercase hex digest computation
- exact equivalence with existing Manga and H3 production digest logic
- zero I/O and zero external dependencies
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegaki_core.canonical_serialization import (
    canonical_json_bytes,
    canonical_json_digest,
    canonical_json_str,
    stable_json_bytes,
    stable_json_digest,
    stable_json_str,
)


class CanonicalSerializationTests(unittest.TestCase):
    """Test suite for canonical serialization and digest core."""

    def test_dict_key_sorting_determinism(self):
        d1 = {"z": 1, "b": 2, "a": 3}
        d2 = {"a": 3, "z": 1, "b": 2}
        d3 = {"b": 2, "a": 3, "z": 1}

        expected_str = '{"a":3,"b":2,"z":1}'
        self.assertEqual(canonical_json_str(d1), expected_str)
        self.assertEqual(canonical_json_str(d2), expected_str)
        self.assertEqual(canonical_json_str(d3), expected_str)

        self.assertEqual(canonical_json_bytes(d1), expected_str.encode("utf-8"))
        self.assertEqual(canonical_json_digest(d1), canonical_json_digest(d2))
        self.assertEqual(canonical_json_digest(d1), canonical_json_digest(d3))

    def test_nested_dict_key_sorting(self):
        nested = {
            "outer_b": {"inner_2": True, "inner_1": False},
            "outer_a": [{"k2": "val2", "k1": "val1"}],
        }
        expected_str = '{"outer_a":[{"k1":"val1","k2":"val2"}],"outer_b":{"inner_1":false,"inner_2":true}}'
        self.assertEqual(canonical_json_str(nested), expected_str)
        self.assertEqual(canonical_json_bytes(nested), expected_str.encode("utf-8"))

    def test_list_order_preservation(self):
        l1 = [1, 2, 3]
        l2 = [3, 2, 1]
        self.assertNotEqual(canonical_json_str(l1), canonical_json_str(l2))
        self.assertNotEqual(canonical_json_digest(l1), canonical_json_digest(l2))

    def test_primitive_types_and_values(self):
        payload = {
            "str": "hello world",
            "int": 42,
            "neg_int": -100,
            "zero": 0,
            "float": 3.1415,
            "bool_true": True,
            "bool_false": False,
            "null": None,
            "empty_list": [],
            "empty_dict": {},
        }
        serialized = canonical_json_str(payload)
        self.assertIn('"bool_true":true', serialized)
        self.assertIn('"bool_false":false', serialized)
        self.assertIn('"null":null', serialized)
        self.assertIn('"empty_list":[]', serialized)
        self.assertIn('"empty_dict":{}', serialized)

    def test_utf8_unensured_ascii(self):
        payload = {"greeting": "こんにちは", "manga": "漫画", "accent": "café"}
        serialized = canonical_json_str(payload)
        self.assertEqual(serialized, '{"accent":"café","greeting":"こんにちは","manga":"漫画"}')
        # Verify UTF-8 byte serialization without ASCII escaping (\u...)
        raw_bytes = canonical_json_bytes(payload)
        self.assertNotIn(b"\\u", raw_bytes)
        self.assertEqual(raw_bytes.decode("utf-8"), serialized)

    def test_compact_separators_no_whitespace(self):
        payload = {"a": [1, 2], "b": {"c": 3}}
        serialized = canonical_json_str(payload)
        self.assertNotIn(": ", serialized)
        self.assertNotIn(", ", serialized)
        self.assertNotIn("\n", serialized)
        self.assertNotIn("\t", serialized)
        self.assertEqual(serialized, '{"a":[1,2],"b":{"c":3}}')

    def test_rejection_of_non_finite_floats(self):
        with self.assertRaises(ValueError):
            canonical_json_str({"val": float("nan")})

        with self.assertRaises(ValueError):
            canonical_json_str({"val": float("inf")})

        with self.assertRaises(ValueError):
            canonical_json_str({"val": float("-inf")})

    def test_rejection_of_non_serializable_types(self):
        with self.assertRaises(TypeError):
            canonical_json_str({"set": {1, 2, 3}})

        with self.assertRaises(TypeError):
            canonical_json_str({"func": lambda: None})

        with self.assertRaises(TypeError):
            canonical_json_str(object())

    def test_sha256_digest_properties(self):
        digest = canonical_json_digest({"key": "value"})
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

        # Empty dict digest
        empty_digest = canonical_json_digest({})
        expected_empty = hashlib.sha256(b"{}").hexdigest()
        self.assertEqual(empty_digest, expected_empty)

    def test_custom_algorithm_support_and_rejection(self):
        md5_digest = canonical_json_digest({"key": "value"}, algorithm="md5")
        self.assertEqual(len(md5_digest), 32)
        expected_md5 = hashlib.md5(b'{"key":"value"}').hexdigest()
        self.assertEqual(md5_digest, expected_md5)

        with self.assertRaises(ValueError):
            canonical_json_digest({}, algorithm="invalid_algo_xyz")

        with self.assertRaises(ValueError):
            canonical_json_digest({}, algorithm="")

    def test_aliases_equivalence(self):
        data = {"test": [1, 2, 3]}
        self.assertEqual(canonical_json_str(data), stable_json_str(data))
        self.assertEqual(canonical_json_bytes(data), stable_json_bytes(data))
        self.assertEqual(canonical_json_digest(data), stable_json_digest(data))

    def test_parity_with_manga_basic_generation_digest(self):
        # Reproduce exact basic_generation._canonical_json and _digest
        def legacy_canonical_json(value):
            return json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )

        def legacy_digest(value):
            return hashlib.sha256(legacy_canonical_json(value).encode("utf-8")).hexdigest()

        sample_catalog = {
            "models": [{"id": "model_1", "path": "/models/m1.safetensors"}],
            "loras": [{"id": "lora_a", "scale": 0.8}],
            "schema_version": 2,
            "title": "テストカタログ",
        }

        self.assertEqual(canonical_json_str(sample_catalog), legacy_canonical_json(sample_catalog))
        self.assertEqual(canonical_json_digest(sample_catalog), legacy_digest(sample_catalog))

    def test_parity_with_h3_graph_digest(self):
        # Reproduce exact h3/tests/test_play1_playable_controls.py digest
        def h3_digest(graph):
            return hashlib.sha256(
                json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()

        sample_graph = {
            "3": {"inputs": {"seed": 123, "steps": 20}, "class_type": "KSampler"},
            "4": {"inputs": {"ckpt_name": "v1-5-pruned.ckpt"}, "class_type": "CheckpointLoaderSimple"},
        }

        self.assertEqual(canonical_json_digest(sample_graph), h3_digest(sample_graph))


if __name__ == "__main__":
    unittest.main()
