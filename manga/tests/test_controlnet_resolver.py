"""Tests for ControlNet logical basename resolution.

Card: MANGA-SCENE-CONTROLNET-RESOURCE-RESOLUTION1
"""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
    CONTROLNET_DEFAULT_BASENAME,
    resolve_controlnet_model,
)


class TestResolveControlnetModel(unittest.TestCase):
    """Unit tests for resolve_controlnet_model basename resolver."""

    def test_root_level_catalog_entry(self):
        """Case 1: Logical basename resolves a root-level catalog entry."""
        catalog = ["CN-anytest4_illustrious2_A.safetensors"]
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, catalog)
        self.assertEqual(result, "CN-anytest4_illustrious2_A.safetensors")

    def test_nested_backslash_catalog_entry(self):
        """Case 2: Logical basename resolves nested Illustrious\\CN-... entry."""
        catalog = [r"Illustrious\CN-anytest4_illustrious2_A.safetensors"]
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, catalog)
        self.assertEqual(result, r"Illustrious\CN-anytest4_illustrious2_A.safetensors")

    def test_nested_forward_slash_catalog_entry(self):
        """Case 3: Forward-slash nested form also matches."""
        catalog = ["Illustrious/CN-anytest4_illustrious2_A.safetensors"]
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, catalog)
        self.assertEqual(result, "Illustrious/CN-anytest4_illustrious2_A.safetensors")

    def test_zero_matches_returns_none(self):
        """Case 4: Zero catalog matches → unavailable (None)."""
        catalog = ["other_model.safetensors", "Illustrious/different.safetensors"]
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, catalog)
        self.assertIsNone(result)

    def test_empty_catalog_returns_none(self):
        """Case 4b: Empty catalog → unavailable."""
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, [])
        self.assertIsNone(result)

    def test_duplicate_basename_ambiguity_returns_none(self):
        """Case 5: Duplicate basename in two folders → ambiguous, fail-closed."""
        catalog = [
            r"Illustrious\CN-anytest4_illustrious2_A.safetensors",
            r"CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors",
        ]
        result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, catalog)
        self.assertIsNone(result)

    def test_resolver_returns_actual_catalog_spelling(self):
        """Resolver returns the exact catalog string, preserving original separator."""
        for entry in [
            r"deep\nested\path\CN-anytest4_illustrious2_A.safetensors",
            "deep/nested/path/CN-anytest4_illustrious2_A.safetensors",
        ]:
            with self.subTest(entry=entry):
                result = resolve_controlnet_model(CONTROLNET_DEFAULT_BASENAME, [entry])
                self.assertEqual(result, entry)

    def test_default_basename_is_correct(self):
        """Sanity: CONTROLNET_DEFAULT_BASENAME is the expected filename."""
        self.assertEqual(CONTROLNET_DEFAULT_BASENAME, "CN-anytest4_illustrious2_A.safetensors")


class TestCatalogCapabilityAndGeneration(unittest.TestCase):
    """Cases 6-7: Capabilities and generation use the same resolved value."""

    def _build_catalog_with_controlnet(self, controlnet_model):
        """Build a minimal catalog with controlnet capability set."""
        from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog, _digest
        from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
            CONTROLNET_DEFAULT_STRENGTH,
            CONTROLNET_START_PERCENT,
            CONTROLNET_END_PERCENT,
            SCENE_CONTROLNET_REQUIRED_NODES,
        )

        # Build base catalog
        catalog = build_catalog(
            ["Illustrious.safetensors"],
            ["styles/ink.safetensors"],
            {
                "TegakiMinimumHandSceneEditor": {"required": {}},
                "CheckpointLoaderSimple": {"required": {"ckpt_name": (["Illustrious.safetensors"], {})}},
                "LoraLoader": {"required": {
                    "lora_name": (["styles/ink.safetensors"], {}),
                    "model": ("MODEL",), "clip": ("CLIP",),
                    "strength_model": ("FLOAT",), "strength_clip": ("FLOAT",),
                }},
                "CLIPTextEncode": {"required": {"text": ("STRING",), "clip": ("CLIP",)}},
                "EmptyLatentImage": {"required": {
                    "width": ("INT", {"min": 256, "max": 2048, "step": 8}),
                    "height": ("INT", {"min": 256, "max": 2048, "step": 8}),
                    "batch_size": ("INT", {"min": 1, "max": 4096}),
                }},
                "KSampler": {"required": {
                    "seed": ("INT", {"min": 0, "max": 4294967295}),
                    "steps": ("INT", {"min": 1, "max": 100}),
                    "cfg": ("FLOAT", {"min": 0.0, "max": 30.0}),
                    "sampler_name": (["euler"], {}),
                    "scheduler": (["normal"], {}),
                    "model": ("MODEL",), "positive": ("CONDITIONING",),
                    "negative": ("CONDITIONING",), "latent_image": ("LATENT",),
                    "denoise": ("FLOAT",),
                }},
                "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
                "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
            },
            lambda _kind, _name: True,
        )
        catalog["scene_generation"] = {
            "available": True,
            "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
            "controlnet": {
                "available": controlnet_model is not None,
                "required_nodes": list(SCENE_CONTROLNET_REQUIRED_NODES),
                "model": controlnet_model,
                "default_strength": CONTROLNET_DEFAULT_STRENGTH,
                "start_percent": CONTROLNET_START_PERCENT,
                "end_percent": CONTROLNET_END_PERCENT,
                "guide_assets": ["tegaki_manga_guides/rough.png"],
            },
        }
        catalog["revision"] = _digest(catalog)
        return catalog

    def test_capability_uses_resolved_catalog_name(self):
        """Case 6: Capabilities report the resolved canonical catalog value."""
        resolved = resolve_controlnet_model(
            CONTROLNET_DEFAULT_BASENAME,
            [r"Illustrious\CN-anytest4_illustrious2_A.safetensors"],
        )
        self.assertEqual(resolved, r"Illustrious\CN-anytest4_illustrious2_A.safetensors")
        catalog = self._build_catalog_with_controlnet(resolved)
        cnet = catalog["scene_generation"]["controlnet"]
        self.assertTrue(cnet["available"])
        self.assertEqual(cnet["model"], r"Illustrious\CN-anytest4_illustrious2_A.safetensors")

    def test_generation_uses_same_resolved_entry(self):
        """Case 7: Generation graph uses same resolver result as capabilities."""
        from copy import deepcopy
        from custom_nodes_custom.tegaki_manga_nodes.scene_generation import compile_scene
        from custom_nodes_custom.tegaki_manga_nodes.minimum_hand_scene_editor import create_default_m1_document
        from custom_nodes_custom.tegaki_manga_nodes.authoring_contract import create_guide

        resolved = resolve_controlnet_model(
            CONTROLNET_DEFAULT_BASENAME,
            [r"Illustrious\CN-anytest4_illustrious2_A.safetensors"],
        )
        catalog = self._build_catalog_with_controlnet(resolved)

        doc = create_default_m1_document()
        doc["pages"][0]["guides"] = [
            create_guide(
                "rough_manga",
                "tegaki_manga_guides/rough.png",
                placement={"x": 0, "y": 0, "w": 1, "h": 1},
            ),
        ]

        request = {
            "request_id": "resolver_test_1",
            "mode": "scene",
            "checkpoint_id": "Illustrious.safetensors",
            "authoring_document": deepcopy(doc),
            "page_index": 0,
            "sampler_id": "euler",
            "scheduler_id": "normal",
            "steps": 4,
            "cfg": 5.0,
            "seed_requested": "0",
            "capability_revision": catalog["revision"],
            "mask_feather": 16,
            "panel_strength": 1.0,
        }
        result = compile_scene(request, catalog)
        self.assertTrue(result["ok"])

        # Find the ControlNetLoader node and verify it uses the resolved name
        graph = result["graph"]
        cnet_loaders = [
            (k, v) for k, v in graph.items()
            if v["class_type"] == "ControlNetLoader"
        ]
        self.assertEqual(len(cnet_loaders), 1)
        loader_id, loader_node = cnet_loaders[0]
        self.assertEqual(
            loader_node["inputs"]["control_net_name"],
            r"Illustrious\CN-anytest4_illustrious2_A.safetensors",
        )

        # Audit trail records the same resolved model
        self.assertTrue(result["audit_trail"]["controlnet"]["enabled"])
        self.assertEqual(
            result["audit_trail"]["controlnet"]["model"],
            r"Illustrious\CN-anytest4_illustrious2_A.safetensors",
        )


if __name__ == "__main__":
    unittest.main()
