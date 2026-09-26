"""MANGA-PROMPT-ASSIST-PRODUCTION1: lazy, root-bounded LoRA preview sidecars.

Real engine_resources contracts over a temp tree; no ComfyUI, no /prompt, no GPU.
"""

from __future__ import annotations

import builtins
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from custom_nodes_custom.tegaki_manga_nodes import engine_resources as res  # noqa: E402

PNG = res.PNG_SIGNATURE + b"\x00\x00\x00\rIHDR-fixture"
WITH = "AnimeOriginalArtStyleShadow2_SDXL-000100"


class LoraPreviewTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        self.root = self.base / "Lora"
        style = self.root / "style"
        style.mkdir(parents=True)
        (style / f"{WITH}.safetensors").write_bytes(b"MODEL")
        (style / f"{WITH}.preview.png").write_bytes(PNG)
        (style / "plain.safetensors").write_bytes(b"MODEL")
        (style / "notes.txt").write_bytes(b"text")
        (style / "fake.safetensors").write_bytes(b"MODEL")
        (style / "fake.preview.png").write_bytes(b"not a png")
        deep = self.root / "unopened" / "deeper"
        deep.mkdir(parents=True)
        (deep / "hidden.safetensors").write_bytes(b"MODEL")
        (deep / "hidden.preview.png").write_bytes(PNG)
        self.env = {"TEGAKI_ILLUSTRIOUS_LORA_ROOT": str(self.root)}

    def tearDown(self):
        self._tmp.cleanup()

    def listing(self, folder):
        return {l["id"]: l for l in res.list_lora_directory(str(self.root), folder)["loras"]}

    def test_a_matching_preview_png_is_detected(self):
        loras = self.listing("style")
        self.assertTrue(loras[f"style/{WITH}.safetensors"]["preview"])
        path = res.lora_preview_path("illustrious", f"style/{WITH}.safetensors", [str(self.root)], environ=self.env)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), PNG)

    def test_b_absent_preview_falls_back(self):
        self.assertFalse(self.listing("style")["style/plain.safetensors"]["preview"])
        with self.assertRaises(res.ResourceContractError) as ctx:
            res.resolve_lora_preview(str(self.root), "style/plain.safetensors")
        self.assertEqual(ctx.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")

    def test_c_listing_scans_only_the_requested_folder_and_opens_nothing(self):
        real_scandir = os.scandir
        scanned = []

        def spy(path="."):
            scanned.append(os.path.realpath(path))
            return real_scandir(path)

        def no_open(*_a, **_k):
            raise AssertionError("listing must not open files")

        def no_walk(*_a, **_k):
            raise AssertionError("listing must not recurse")

        with mock.patch.object(res.os, "scandir", spy), mock.patch.object(builtins, "open", no_open), \
                mock.patch.object(res.os, "walk", no_walk):
            top = res.list_lora_directory(str(self.root), "")
            res.list_lora_directory(str(self.root), "style")
        self.assertEqual(scanned, [os.path.realpath(self.root), os.path.realpath(self.root / "style")])
        self.assertEqual([f["id"] for f in top["folders"]], ["style", "unopened"])
        self.assertEqual(top["loras"], [])

    def test_d_traversal_and_out_of_root_fail_closed(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "evil.safetensors").write_bytes(b"x")
        (outside / "evil.preview.png").write_bytes(PNG)
        for bad in ("../outside/evil.safetensors", "/etc/passwd.safetensors", "C:/x.safetensors",
                    "style/../../outside/evil.safetensors", "style//x.safetensors"):
            with self.subTest(bad=bad), self.assertRaises(res.ResourceContractError) as ctx:
                res.resolve_lora_preview(str(self.root), bad)
            self.assertEqual(ctx.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")
        try:
            os.symlink(outside / "evil.preview.png", self.root / "style" / "linked.preview.png")
            (self.root / "style" / "linked.safetensors").write_bytes(b"MODEL")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(res.ResourceContractError) as link:
            res.resolve_lora_preview(str(self.root), "style/linked.safetensors")
        self.assertEqual(link.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")

    def test_e_physical_root_not_in_browse_payload(self):
        payload = res.browse_lora_payload("illustrious", "style", [str(self.root)], environ=self.env)
        text = json.dumps(payload)
        self.assertNotIn(str(self.root), text)
        self.assertNotIn(os.path.realpath(self.root), text)

    def test_f_only_png_sidecars_derived_from_lora_ids_are_served(self):
        for bad in (f"style/{WITH}.preview.png", "style/notes.txt", "style", f"style/{WITH}"):
            with self.subTest(bad=bad), self.assertRaises(res.ResourceContractError) as ctx:
                res.resolve_lora_preview(str(self.root), bad)
            self.assertEqual(ctx.exception.code, "RESOURCE_PREVIEW_UNSUPPORTED")
        with self.assertRaises(res.ResourceContractError) as not_png:
            res.resolve_lora_preview(str(self.root), "style/fake.safetensors")
        self.assertEqual(not_png.exception.code, "RESOURCE_PREVIEW_UNSUPPORTED")
        with self.assertRaises(res.ResourceContractError) as unregistered:
            res.lora_preview_path("illustrious", f"style/{WITH}.safetensors", ["/elsewhere"], environ=self.env)
        self.assertEqual(unregistered.exception.code, "RESOURCE_ROOT_UNREGISTERED")

    def test_g_lora_without_preview_remains_fully_listed(self):
        plain = self.listing("style")["style/plain.safetensors"]
        self.assertEqual({k: plain[k] for k in ("id", "name", "available", "preview")},
                         {"id": "style/plain.safetensors", "name": "plain", "available": True, "preview": False})


class PreviewContentTypeTests(unittest.TestCase):
    """Owner correction: validity and MIME come from the bytes, not the '.png' name."""

    JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00jpeg-fixture"
    WEBP = b"RIFF\x10\x00\x00\x00WEBPVP8 webp-fixture"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name) / "Lora"
        (self.root / "style").mkdir(parents=True)
        for stem, data in (("Jujutsu_Kaisen_Cover_Style_JJK_Manga", PNG), ("HELLSING_illustrious_v1-000020", self.JPEG),
                           ("webp_style", self.WEBP), ("text_style", b"GIF89a-not-allowed"), ("empty_style", b"")):
            (self.root / "style" / f"{stem}.safetensors").write_bytes(b"MODEL")
            (self.root / "style" / f"{stem}.preview.png").write_bytes(data)

    def tearDown(self):
        self._tmp.cleanup()

    def served(self, stem):
        path = res.resolve_lora_preview(str(self.root), f"style/{stem}.safetensors")
        return res.preview_mime(path)

    def test_a_real_png_preview_is_served_as_png(self):
        self.assertEqual(self.served("Jujutsu_Kaisen_Cover_Style_JJK_Manga"), "image/png")

    def test_b_c_jpeg_bytes_under_preview_png_are_served_as_jpeg(self):
        self.assertEqual(self.served("HELLSING_illustrious_v1-000020"), "image/jpeg")
        self.assertEqual(self.served("webp_style"), "image/webp")

    def test_d_non_image_sidecar_rejected(self):
        for stem in ("text_style", "empty_style"):
            with self.subTest(stem=stem), self.assertRaises(res.ResourceContractError) as ctx:
                res.resolve_lora_preview(str(self.root), f"style/{stem}.safetensors")
            self.assertEqual(ctx.exception.code, "RESOURCE_PREVIEW_UNSUPPORTED")

    def test_e_boundary_unchanged_for_jpeg_content(self):
        outside = pathlib.Path(self._tmp.name) / "outside"
        outside.mkdir()
        (outside / "x.preview.png").write_bytes(self.JPEG)
        for bad in ("../outside/x.safetensors", "style/HELLSING_illustrious_v1-000020.preview.png"):
            with self.subTest(bad=bad), self.assertRaises(res.ResourceContractError):
                res.resolve_lora_preview(str(self.root), bad)

    def test_sniff_reads_magic_bytes_only(self):
        self.assertEqual(res.sniff_preview_mime(PNG[:12]), "image/png")
        self.assertEqual(res.sniff_preview_mime(self.JPEG[:12]), "image/jpeg")
        self.assertIsNone(res.sniff_preview_mime(b"<svg xmlns="))


if __name__ == "__main__":
    unittest.main(verbosity=2)
