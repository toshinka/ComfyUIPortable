"""Targeted tests for the bounded Manga model/LoRA metadata reader."""

from __future__ import annotations

import builtins
import importlib.util
import json
import os
import pathlib
import struct
import tempfile
import unittest


MODULE = pathlib.Path(__file__).resolve().parents[2] / "custom_nodes_custom" / "tegaki_manga_nodes" / "model_lora_metadata.py"
SPEC = importlib.util.spec_from_file_location("manga_model_lora_metadata", MODULE.resolve())
metadata = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(metadata)


def write_fixture(path: pathlib.Path, embedded_metadata: dict | None, payload: bytes = b"TENSOR-PAYLOAD") -> None:
    header: dict = {"tensor": {"dtype": "F32", "shape": [1], "data_offsets": [0, len(payload)]}}
    if embedded_metadata is not None:
        header["__metadata__"] = embedded_metadata
    encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + payload)


class ModelLoraMetadataTests(unittest.TestCase):
    def test_checkpoint_metadata_preserves_raw_and_normalizes_explicit_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "Illustrious.safetensors"
            embedded = {
                "ss_base_model_version": "SDXL 1.0",
                "modelspec.architecture": "stable-diffusion-xl-v1-base",
                "modelspec.title": "Example checkpoint",
                "modelspec.description": "An explicit description",
                "modelspec.trigger_phrase": "ink wash",
                "ss_resolution": "(1024, 1024)",
                "ss_tag_frequency": '{"set":{"ink wash":3}}',
                "modelspec.source": "local manifest",
                "modelspec.hash.sha256": "abc123",
                "unknown_key": {"nested": ["kept"]},
            }
            write_fixture(path, embedded)
            result = metadata.inspect_model_lora_metadata("CHECKPOINT", "models/Illustrious.safetensors", path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "CHECKPOINT")
        self.assertEqual(result["canonical_id"], "models/Illustrious.safetensors")
        self.assertEqual(result["metadata_state"], "PRESENT")
        self.assertEqual(result["format"], "SAFETENSORS")
        self.assertEqual(result["raw_embedded_metadata"]["unknown_key"], {"nested": ["kept"]})
        normalized = result["normalized_metadata"]
        self.assertEqual(normalized["base_model_state"], "EXPLICIT")
        self.assertEqual(normalized["base_model"], "SDXL 1.0")
        self.assertEqual(normalized["architecture"], "stable-diffusion-xl-v1-base")
        self.assertEqual(normalized["trigger_words"], "ink wash")
        self.assertEqual(normalized["training_resolution"], "(1024, 1024)")
        self.assertEqual(normalized["training_metadata"]["tag_frequency"], '{"set":{"ink wash":3}}')
        self.assertEqual(normalized["embedded_hash"], "abc123")
        self.assertEqual(result["hash_state"], "KNOWN")

    def test_lora_kind_and_canonical_id_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "style.safetensors"
            write_fixture(path, {"ss_sd_model_name": "Illustrious", "modelspec.trigger_phrase": "style_token"})
            result = metadata.inspect_model_lora_metadata("lora", "styles/style.safetensors", path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "LORA")
        self.assertEqual(result["canonical_id"], "styles/style.safetensors")
        self.assertEqual(result["normalized_metadata"]["base_model_state"], "EXPLICIT")
        self.assertEqual(result["normalized_metadata"]["base_model"], "Illustrious")

    def test_metadata_absence_is_nonfatal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "empty.safetensors"
            write_fixture(path, None)
            result = metadata.inspect_model_lora_metadata("CHECKPOINT", "empty.safetensors", path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["metadata_state"], "ABSENT")
        self.assertIsNone(result["raw_embedded_metadata"])
        self.assertEqual(result["normalized_metadata"], {"base_model_state": "ABSENT"})
        self.assertEqual(result["hash_state"], "ABSENT")

    def test_no_trigger_guess_from_name_or_description(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "name_that_looks_like_a_trigger.safetensors"
            write_fixture(path, {"modelspec.description": "description with a possible token"})
            result = metadata.inspect_model_lora_metadata("LORA", "name_that_looks_like_a_trigger.safetensors", path)

        self.assertNotIn("trigger_words", result["normalized_metadata"])

    def test_conflicting_explicit_base_values_fail_closed_without_selecting_one(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "conflict.safetensors"
            write_fixture(path, {"ss_base_model_version": "SDXL", "ss_sd_model_name": "Illustrious"})
            result = metadata.inspect_model_lora_metadata("CHECKPOINT", "conflict.safetensors", path)

        self.assertTrue(result["ok"])
        self.assertEqual(result["metadata_state"], "CONFLICT")
        self.assertEqual(result["normalized_metadata"]["base_model_state"], "CONFLICTING")
        self.assertNotIn("base_model", result["normalized_metadata"])
        self.assertIn("METADATA_CONFLICT:base_model", result["warnings"])

    def test_hash_conflict_is_diagnostic_and_never_computed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "hash-conflict.safetensors"
            write_fixture(path, {"modelspec.hash.sha256": "one", "sha256": "two"})
            result = metadata.inspect_model_lora_metadata("CHECKPOINT", "hash-conflict.safetensors", path)

        self.assertEqual(result["hash_state"], "ABSENT")
        self.assertNotIn("embedded_hash", result["normalized_metadata"])
        self.assertIn("METADATA_CONFLICT:embedded_hash", result["warnings"])

    def test_malformed_json_and_oversized_declaration_are_bounded_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            malformed = pathlib.Path(directory) / "malformed.safetensors"
            malformed.write_bytes(struct.pack("<Q", 4) + b"{bad" + b"payload")
            malformed_result = metadata.inspect_model_lora_metadata("CHECKPOINT", "malformed.safetensors", malformed)

            oversized = pathlib.Path(directory) / "oversized.safetensors"
            oversized.write_bytes(struct.pack("<Q", 1024) + b"{}")
            oversized_result = metadata.inspect_model_lora_metadata(
                "CHECKPOINT", "oversized.safetensors", oversized, max_header_bytes=64
            )

        self.assertEqual(malformed_result["error"]["code"], "INVALID_SAFETENSORS")
        self.assertEqual(oversized_result["error"]["code"], "HEADER_TOO_LARGE")

    def test_non_safetensors_and_missing_resource_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = pathlib.Path(directory) / "model.ckpt"
            checkpoint.write_bytes(b"legacy")
            unsupported = metadata.inspect_model_lora_metadata("CHECKPOINT", "model.ckpt", checkpoint)
            missing = metadata.inspect_model_lora_metadata(
                "LORA", "missing.safetensors", pathlib.Path(directory) / "missing.safetensors"
            )

        self.assertEqual(unsupported["error"]["code"], "UNSUPPORTED_FORMAT")
        self.assertEqual(missing["error"]["code"], "FILE_NOT_FOUND")

    def test_reader_never_reads_tensor_payload_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "bounded.safetensors"
            write_fixture(path, {"modelspec.title": "bounded"}, payload=b"SENTINEL-TENSOR-PAYLOAD")
            before = (path.stat().st_size, path.stat().st_mtime_ns)
            original_open = builtins.open
            header_limit = 8 + len(json.dumps(
                {"tensor": {"dtype": "F32", "shape": [1], "data_offsets": [0, 22]},
                 "__metadata__": {"modelspec.title": "bounded"}},
                ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8"))

            class ReadGuard:
                def __init__(self, wrapped):
                    self.wrapped = wrapped

                def __enter__(self):
                    self.wrapped.__enter__()
                    return self

                def __exit__(self, *args):
                    return self.wrapped.__exit__(*args)

                def read(self, size=-1):
                    data = self.wrapped.read(size)
                    if self.wrapped.tell() > header_limit:
                        raise AssertionError("tensor payload was read")
                    return data

                def __getattr__(self, name):
                    return getattr(self.wrapped, name)

            def guarded_open(file, mode="r", *args, **kwargs):
                handle = original_open(file, mode, *args, **kwargs)
                if os.fspath(file) == os.fspath(path) and "rb" in mode:
                    return ReadGuard(handle)
                return handle

            builtins.open = guarded_open
            try:
                result = metadata.inspect_model_lora_metadata("CHECKPOINT", "bounded.safetensors", path)
            finally:
                builtins.open = original_open
            after = (path.stat().st_size, path.stat().st_mtime_ns)

        self.assertTrue(result["ok"])
        self.assertEqual(before, after)
        self.assertEqual(result["bytes_inspected"], header_limit)

    def test_result_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "deterministic.safetensors"
            write_fixture(path, {"unknown": {"b": 2, "a": 1}, "modelspec.title": "title"})
            first = metadata.inspect_model_lora_metadata("CHECKPOINT", "deterministic.safetensors", path)
            second = metadata.inspect_model_lora_metadata("CHECKPOINT", "deterministic.safetensors", path)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
