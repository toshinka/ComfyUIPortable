"""Targeted acceptance tests for Manga Reference and Guide checkpoint name gate removal."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog, GenerationContractError
from custom_nodes_custom.tegaki_manga_nodes.authoring_contract import (
    create_cast_entry,
    create_character_instance,
)
from custom_nodes_custom.tegaki_manga_nodes.minimum_hand_scene_editor import create_default_m1_document
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
    CONTROLNET_DEFAULT_MODEL,
    CONTROLNET_DEFAULT_STRENGTH,
    REFERENCE_CLIP_VISION,
    REFERENCE_COMBINE_EMBEDS,
    REFERENCE_EMBEDS_SCALING,
    REFERENCE_END_AT,
    REFERENCE_IPADAPTER,
    REFERENCE_START_AT,
    REFERENCE_SUPPORTED_CHECKPOINT,
    REFERENCE_WEIGHT,
    REFERENCE_WEIGHT_TYPE,
    SCENE_CONTROLNET_REQUIRED_NODES,
    SCENE_REFERENCE_REQUIRED_NODES,
    compile_scene,
    is_illustrious_sdxl_checkpoint,
)

# Test Checkpoint definitions per Card Section 7:
# Case A: Filename contains "Illustrious"
CHECKPOINT_CASE_A = r"!新規SDモデル\darkbubbleIllustrious_illustriousV3d.safetensors"
# Case B: Filename contains neither "Illustrious", "ILL", nor "SDXL"
CHECKPOINT_CASE_B = r"models\my_anime_fantasy_mix.safetensors"
# Case C: Checkpoint with catalog family = UNKNOWN
CHECKPOINT_CASE_C = r"general\noname_model_checkpoint.safetensors"
# Missing checkpoint
CHECKPOINT_MISSING = r"nonexistent\missing_model.safetensors"


def fake_inputs():
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {
            "ckpt_name": ([CHECKPOINT_CASE_A, CHECKPOINT_CASE_B, CHECKPOINT_CASE_C], {})
        }},
        "LoraLoader": {"required": {
            "lora_name": (["styles/ink.safetensors"], {}),
            "model": ("MODEL",), "clip": ("CLIP",), "strength_model": ("FLOAT",), "strength_clip": ("FLOAT",),
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
            "model": ("MODEL",), "positive": ("CONDITIONING",), "negative": ("CONDITIONING",),
            "latent_image": ("LATENT",), "denoise": ("FLOAT",),
        }},
        "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
        "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
    }


class CheckpointNameGatesRemovalTests(unittest.TestCase):
    def setUp(self):
        checkpoints = [CHECKPOINT_CASE_A, CHECKPOINT_CASE_B, CHECKPOINT_CASE_C]
        self.catalog = build_catalog(
            checkpoints,
            ["styles/ink.safetensors"],
            fake_inputs(),
            lambda _kind, _name: True,
        )
        # Ensure Case C explicitly has family = UNKNOWN
        for entry in self.catalog["checkpoints"]:
            if entry["id"] == CHECKPOINT_CASE_C:
                entry["family"] = "UNKNOWN"
                entry["family_confidence"] = "UNKNOWN"

        self.catalog["scene_generation"] = {
            "available": True,
            "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
            "reference": {
                "available": True,
                "required_nodes": list(SCENE_REFERENCE_REQUIRED_NODES),
                "clip_vision": REFERENCE_CLIP_VISION,
                "ipadapter": REFERENCE_IPADAPTER,
                "weight": REFERENCE_WEIGHT,
                "weight_type": REFERENCE_WEIGHT_TYPE,
                "combine_embeds": REFERENCE_COMBINE_EMBEDS,
                "start_at": REFERENCE_START_AT,
                "end_at": REFERENCE_END_AT,
                "embeds_scaling": REFERENCE_EMBEDS_SCALING,
                "reference_assets": ["tegaki_manga_references/ref_c789751db904319d.png"],
            },
            "controlnet": {
                "available": True,
                "required_nodes": list(SCENE_CONTROLNET_REQUIRED_NODES),
                "model": CONTROLNET_DEFAULT_MODEL,
                "default_strength": CONTROLNET_DEFAULT_STRENGTH,
                "guide_assets": ["tegaki_manga_guides/guide_sample.png"],
            },
        }
        self.catalog["revision"] = hashlib.sha256(
            json.dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def make_reference_doc(self, asset="tegaki_manga_references/ref_c789751db904319d.png"):
        doc = create_default_m1_document()
        page = doc["pages"][0]
        page["style_prompt"] = "GLOBAL_BASE"
        page["scenes"] = page["scenes"][:1]
        page["scenes"][0]["input_mode"] = "cast"
        page["scenes"][0]["prompt"] = "SCENE_ACTION"
        page["scenes"][0]["area"] = {"shape_type": "rect", "x": 0.10, "y": 0.10, "w": 0.80, "h": 0.80}
        cast = create_cast_entry(
            display_name="Hero",
            identity_prompt="hero, black hair, blue eyes",
            cast_id="cast_compat_test",
            reference_asset=asset,
        )
        page["cast"] = [cast]
        inst = create_character_instance(
            "cast_compat_test",
            page["scenes"][0]["scene_id"],
            area={"shape_type": "rect", "x": 0.25, "y": 0.20, "w": 0.20, "h": 0.30},
            instance_id="inst_compat_test",
        )
        page["character_instances"] = [inst]
        return doc

    def make_guide_doc(self, asset="tegaki_manga_guides/guide_sample.png"):
        doc = create_default_m1_document()
        page = doc["pages"][0]
        page["style_prompt"] = "GLOBAL_BASE"
        page["scenes"] = page["scenes"][:1]
        page["scenes"][0]["input_mode"] = "simple"
        page["scenes"][0]["prompt"] = "SCENE_ACTION"
        page["scenes"][0]["area"] = {"shape_type": "rect", "x": 0.10, "y": 0.10, "w": 0.80, "h": 0.80}
        page["guides"] = [{
            "guide_id": "guide_01",
            "guide_type": "rough_manga",
            "asset_reference": asset,
            "enabled": True,
            "figure_regions": [],
            "placement": {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90},
        }]
        return doc

    def make_request(self, checkpoint_id, doc, **overrides):
        req = {
            "request_id": "req_compat_test",
            "mode": "scene",
            "checkpoint_id": checkpoint_id,
            "authoring_document": copy.deepcopy(doc),
            "page_index": 0,
            "sampler_id": "euler",
            "scheduler_id": "normal",
            "steps": 4,
            "cfg": 5.0,
            "seed_requested": "42",
            "capability_revision": self.catalog["revision"],
            "mask_feather": 16,
            "panel_strength": 1.0,
        }
        req.update(overrides)
        return req

    def test_case_a_illustrious_checkpoint_with_reference(self):
        doc = self.make_reference_doc()
        req = self.make_request(
            CHECKPOINT_CASE_A,
            doc,
            reference_weight=0.65,
            reference_start=0.1,
            reference_end=0.9,
        )
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]

        # Loader must load the requested checkpoint ID
        loader = next(n for n in graph.values() if n["class_type"] == "CheckpointLoaderSimple")
        self.assertEqual(loader["inputs"]["ckpt_name"], CHECKPOINT_CASE_A)

        # IPAdapterAdvanced must be present and correctly wired
        ip_nodes = [node for node in graph.values() if node["class_type"] == "IPAdapterAdvanced"]
        self.assertEqual(len(ip_nodes), 1)
        ip_node = ip_nodes[0]
        self.assertAlmostEqual(ip_node["inputs"]["weight"], 0.65)
        self.assertAlmostEqual(ip_node["inputs"]["start_at"], 0.1)
        self.assertAlmostEqual(ip_node["inputs"]["end_at"], 0.9)
        self.assertEqual(ip_node["inputs"]["weight_type"], REFERENCE_WEIGHT_TYPE)
        self.assertEqual(ip_node["inputs"]["combine_embeds"], REFERENCE_COMBINE_EMBEDS)
        self.assertEqual(ip_node["inputs"]["embeds_scaling"], REFERENCE_EMBEDS_SCALING)

        cond_builder_id = next(k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder")
        self.assertEqual(ip_node["inputs"]["attn_mask"], [cond_builder_id, 6])

    def test_case_b_no_illustrious_in_filename_with_reference(self):
        """Case B: Checkpoint without 'Illustrious', 'ILL' or 'SDXL' in name compiles cleanly."""
        doc = self.make_reference_doc()
        req = self.make_request(
            CHECKPOINT_CASE_B,
            doc,
            reference_weight=0.50,
            reference_start=0.0,
            reference_end=0.85,
        )
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]

        loader = next(n for n in graph.values() if n["class_type"] == "CheckpointLoaderSimple")
        self.assertEqual(loader["inputs"]["ckpt_name"], CHECKPOINT_CASE_B)

        ip_nodes = [node for node in graph.values() if node["class_type"] == "IPAdapterAdvanced"]
        self.assertEqual(len(ip_nodes), 1)
        ip_node = ip_nodes[0]
        self.assertAlmostEqual(ip_node["inputs"]["weight"], 0.50)
        self.assertAlmostEqual(ip_node["inputs"]["start_at"], 0.0)
        self.assertAlmostEqual(ip_node["inputs"]["end_at"], 0.85)

        cond_builder_id = next(k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder")
        self.assertEqual(ip_node["inputs"]["attn_mask"], [cond_builder_id, 6])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])

    def test_case_c_family_unknown_checkpoint_with_reference(self):
        """Case C: Checkpoint with catalog family = UNKNOWN compiles cleanly."""
        doc = self.make_reference_doc()
        req = self.make_request(CHECKPOINT_CASE_C, doc)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]

        loader = next(n for n in graph.values() if n["class_type"] == "CheckpointLoaderSimple")
        self.assertEqual(loader["inputs"]["ckpt_name"], CHECKPOINT_CASE_C)

        ip_nodes = [node for node in graph.values() if node["class_type"] == "IPAdapterAdvanced"]
        self.assertEqual(len(ip_nodes), 1)
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])

    def test_case_e_checkpoint_b_with_page_guide(self):
        """Case E: Checkpoint B without 'Illustrious' compiles with enabled Page Guide and ControlNet."""
        doc = self.make_guide_doc()
        req = self.make_request(
            CHECKPOINT_CASE_B,
            doc,
            controlnet_strength=0.45,
            controlnet_start_percent=0.1,
            controlnet_end_percent=0.9,
        )
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]

        loader = next(n for n in graph.values() if n["class_type"] == "CheckpointLoaderSimple")
        self.assertEqual(loader["inputs"]["ckpt_name"], CHECKPOINT_CASE_B)

        cnet_nodes = [node for node in graph.values() if node["class_type"] == "ControlNetApplyAdvanced"]
        self.assertEqual(len(cnet_nodes), 1)
        cnet_node = cnet_nodes[0]
        self.assertAlmostEqual(cnet_node["inputs"]["strength"], 0.45)
        self.assertAlmostEqual(cnet_node["inputs"]["start_percent"], 0.1)
        self.assertAlmostEqual(cnet_node["inputs"]["end_percent"], 0.9)

        cnet_loader = next(n for n in graph.values() if n["class_type"] == "ControlNetLoader")
        self.assertEqual(cnet_loader["inputs"]["control_net_name"], CONTROLNET_DEFAULT_MODEL)

    def test_missing_checkpoint_fails_validation(self):
        """Preserved check: missing or unavailable checkpoint fails with CHECKPOINT_UNAVAILABLE."""
        doc = self.make_reference_doc()
        req = self.make_request(CHECKPOINT_MISSING, doc)
        with self.assertRaises(GenerationContractError) as ctx:
            compile_scene(req, self.catalog)
        self.assertEqual(ctx.exception.code, "CHECKPOINT_UNAVAILABLE")

    def test_missing_reference_asset_fails_validation(self):
        """Preserved check: missing reference asset fails with REFERENCE_ASSET_UNAVAILABLE."""
        doc = self.make_reference_doc(asset="tegaki_manga_references/missing_asset.png")
        req = self.make_request(CHECKPOINT_CASE_B, doc)
        with self.assertRaises(GenerationContractError) as ctx:
            compile_scene(req, self.catalog)
        self.assertEqual(ctx.exception.code, "REFERENCE_ASSET_UNAVAILABLE")

    def test_missing_guide_asset_fails_validation(self):
        """Preserved check: missing guide asset fails with GUIDE_ASSET_UNAVAILABLE."""
        doc = self.make_guide_doc(asset="tegaki_manga_guides/missing_guide.png")
        req = self.make_request(CHECKPOINT_CASE_B, doc)
        with self.assertRaises(GenerationContractError) as ctx:
            compile_scene(req, self.catalog)
        self.assertEqual(ctx.exception.code, "GUIDE_ASSET_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
