import tempfile
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
# Import engine_resources without executing the ComfyUI-dependent package __init__.
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    _pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    _pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = _pkg

from custom_nodes_custom.tegaki_manga_nodes.engine_resources import (
    CHECKPOINT_PREVIEW_SLOT_SUFFIXES,
    PREVIEW_SLOT_SUFFIXES,
    ResourceContractError,
    resolve_checkpoint_preview,
    resolve_lora_preview,
)

PNG = b"\x89PNG\r\n\x1a\nfixture"
JPEG = b"\xff\xd8\xffjpeg-fixture"
WEBP = b"RIFF\x04\x00\x00\x00WEBPfixture"


class CheckpointPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.checkpoint = self.root / "nested" / "Example.safetensors"
        self.checkpoint.parent.mkdir(parents=True)
        self.checkpoint.write_bytes(b"checkpoint fixture")

    def tearDown(self):
        self.temp.cleanup()

    def resolve_model(self, checkpoint, slot):
        checkpoint_id = checkpoint.relative_to(self.root).as_posix()
        return resolve_checkpoint_preview(
            checkpoint_id,
            str(checkpoint),
            [str(self.root)],
            extensions=(".safetensors", ".ckpt"),
            slot=slot,
        )

    def resolve(self, slot):
        return self.resolve_model(self.checkpoint, slot)

    def sidecar(self, name, data=PNG):
        path = self.checkpoint.with_name(name)
        path.write_bytes(data)
        return str(path)

    def test_exact_preview_wins_and_remaining_owned_images_fill_four_slots(self):
        primary = self.sidecar("Example.preview.webp", WEBP)
        one = self.sidecar("Example_1.jpg", JPEG)
        two = self.sidecar("Example_2.jpg", JPEG)
        three = self.sidecar("Example_3.jpg", JPEG)
        self.sidecar("Example_10.jpg", JPEG)

        resolved = [self.resolve(slot) for slot in range(1, 5)]
        self.assertEqual(resolved, [primary, one, two, three])
        self.assertEqual(len(set(resolved)), 4, "one image cannot fill multiple slots")
        self.assertEqual(len(CHECKPOINT_PREVIEW_SLOT_SUFFIXES), 4)
        with self.assertRaises(ResourceContractError) as caught:
            self.resolve(5)
        self.assertEqual(caught.exception.code, "INVALID_REQUEST")

    def test_no_primary_uses_natural_order_and_missing_slots_stay_blank(self):
        one = self.sidecar("Example_1.jpg", JPEG)
        two = self.sidecar("Example_2.jpg", JPEG)
        ten = self.sidecar("Example_10.jpg", JPEG)

        self.assertEqual([self.resolve(slot) for slot in (1, 2, 3)], [one, two, ten])
        with self.assertRaises(ResourceContractError) as caught:
            self.resolve(4)
        self.assertEqual(caught.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")

    def test_arbitrary_same_stem_legacy_jpg_is_discovered(self):
        dated = self.sidecar("Example_20260218104720.jpg", JPEG)
        self.assertEqual(self.resolve(1), dated)

    def test_historical_suffixes_are_candidates_without_semantic_mapping(self):
        primary = self.sidecar("Example.preview.png", PNG)
        ani = self.sidecar("Example_ani.webp", WEBP)
        illust = self.sidecar("Example_illust.jpeg", JPEG)
        manga = self.sidecar("Example_man.jpg", JPEG)

        self.assertEqual(self.resolve(1), primary)
        self.assertEqual([self.resolve(slot) for slot in (2, 3, 4)], [ani, illust, manga])

    def test_primary_extension_priority_is_png_webp_jpg_then_jpeg(self):
        jpeg = self.sidecar("Example.preview.jpeg", JPEG)
        jpg = self.sidecar("Example.preview.jpg", JPEG)
        self.assertEqual(self.resolve(1), jpg)
        self.assertNotEqual(self.resolve(1), jpeg)

    def test_foo_does_not_steal_foobar_and_longest_stem_owns_overlap(self):
        folder = self.checkpoint.parent
        foo = folder / "foo.safetensors"
        foobar = folder / "foobar.safetensors"
        foo_one = folder / "foo_01.safetensors"
        for path in (foo, foobar, foo_one):
            path.write_bytes(b"checkpoint fixture")

        foobar_image = folder / "foobar_01.jpg"
        foobar_image.write_bytes(JPEG)
        foo_one_image = folder / "foo_01_2.jpg"
        foo_one_image.write_bytes(JPEG)

        with self.assertRaises(ResourceContractError) as short_prefix:
            self.resolve_model(foo, 1)
        self.assertEqual(short_prefix.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")
        self.assertEqual(self.resolve_model(foobar, 1), str(foobar_image))
        with self.assertRaises(ResourceContractError) as shorter_overlap:
            self.resolve_model(foo, 2)
        self.assertEqual(shorter_overlap.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")
        self.assertEqual(self.resolve_model(foo_one, 1), str(foo_one_image))

    def test_equal_length_duplicate_checkpoint_stems_are_ambiguous(self):
        duplicate = self.checkpoint.with_suffix(".ckpt")
        duplicate.write_bytes(b"checkpoint fixture")
        self.sidecar("Example.preview.png", PNG)

        for checkpoint in (self.checkpoint, duplicate):
            with self.subTest(checkpoint=checkpoint.name), self.assertRaises(ResourceContractError) as caught:
                self.resolve_model(checkpoint, 1)
            self.assertEqual(caught.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")

    def test_nested_checkpoint_identity_is_preserved_and_subfolders_are_not_scanned(self):
        nested_preview_dir = self.checkpoint.parent / "deeper"
        nested_preview_dir.mkdir()
        (nested_preview_dir / "Example_0.jpg").write_bytes(JPEG)

        with self.assertRaises(ResourceContractError) as caught:
            self.resolve(1)
        self.assertEqual(caught.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")
        self.sidecar("Example.preview.png", PNG)
        self.assertEqual(self.resolve(1), str(self.checkpoint.with_name("Example.preview.png")))

    def test_foreign_and_traversal_paths_remain_rejected(self):
        outside = Path(self.temp.name).parent / f"{Path(self.temp.name).name}_outside"
        outside.mkdir()
        try:
            foreign = outside / "Example.safetensors"
            foreign.write_bytes(b"foreign")
            (outside / "Example.preview.png").write_bytes(PNG)
            for bad_id in ("../x/Example.safetensors", "/abs/Example.safetensors", "C:/x/Example.safetensors",
                           "nested/../../Example.safetensors"):
                with self.subTest(bad_id=bad_id), self.assertRaises(ResourceContractError):
                    resolve_checkpoint_preview(bad_id, str(foreign), [str(self.root)],
                                               extensions=(".safetensors", ".ckpt"), slot=1)
            with self.assertRaises(ResourceContractError) as caught:
                resolve_checkpoint_preview("Example.safetensors", str(foreign), [str(self.root)],
                                           extensions=(".safetensors", ".ckpt"), slot=1)
            self.assertEqual(caught.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")
            with self.assertRaises(ResourceContractError) as missing:
                resolve_checkpoint_preview("nested/Example.safetensors", None, [str(self.root)],
                                           extensions=(".safetensors", ".ckpt"), slot=1)
            self.assertEqual(missing.exception.code, "CHECKPOINT_UNAVAILABLE")
            for bad_slot in (0, 5, "../1", "x"):
                with self.subTest(slot=bad_slot), self.assertRaises(ResourceContractError):
                    self.resolve(bad_slot)
        finally:
            for item in outside.iterdir():
                item.unlink()
            outside.rmdir()


class LoraPreviewContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "loras"
        self.root.mkdir()
        self.model = self.root / "Style.safetensors"
        self.model.write_bytes(b"lora fixture")

    def tearDown(self):
        self.temp.cleanup()

    def test_lora_jpg_jpeg_and_three_fixed_slots_remain_supported(self):
        jpg = self.root / "Style.preview.jpg"
        jpeg = self.root / "Style_ani.jpeg"
        webp = self.root / "Style_man.webp"
        jpg.write_bytes(JPEG)
        jpeg.write_bytes(JPEG)
        webp.write_bytes(WEBP)
        (self.root / "Style_illust.png").write_bytes(PNG)

        resolved = [
            resolve_lora_preview(str(self.root), "Style.safetensors", slot=slot)
            for slot in (1, 2, 3)
        ]
        self.assertEqual(resolved, [str(jpg), str(jpeg), str(webp)])
        self.assertEqual(PREVIEW_SLOT_SUFFIXES, {1: ".preview", 2: "_ani", 3: "_man"})
        with self.assertRaises(ResourceContractError) as caught:
            resolve_lora_preview(str(self.root), "Style.safetensors", slot=4)
        self.assertEqual(caught.exception.code, "INVALID_REQUEST")

    def test_lora_illust_is_not_a_slot(self):
        (self.root / "OnlyIllust.safetensors").write_bytes(b"lora fixture")
        (self.root / "OnlyIllust_illust.png").write_bytes(PNG)
        for slot in (1, 2, 3):
            with self.subTest(slot=slot), self.assertRaises(ResourceContractError) as caught:
                resolve_lora_preview(str(self.root), "OnlyIllust.safetensors", slot=slot)
            self.assertEqual(caught.exception.code, "RESOURCE_PREVIEW_NOT_FOUND")


if __name__ == "__main__":
    unittest.main(verbosity=2)
