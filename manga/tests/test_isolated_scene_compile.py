"""Unit tests for isolated_scene_compile.py (Card MANGA-ISOLATED-SCENE-COMPILER1).

Covers cases A through H specified in the Card contract:
A. A valid isolated plan compiles to the expected existing graph contract.
B. Graph dimensions match the explicit local canvas.
C. Only the selected Scene prompt and applicable Page style contribute to the graph.
D. Unrelated Scene and CAST data do not enter the compiled graph.
E. Selected CAST and Reference associations reach the existing graph-building path.
F. An active unsupported Guide fails explicitly with ISOLATED_SCENE_GUIDE_UNSUPPORTED.
G. Invalid settings or unresolved required inputs fail explicitly.
H. The source plan is not mutated (immutability).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EMBEDDED_SITE = ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))

# Ensure custom_nodes_custom package can be imported without triggering ComfyUI runtime
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
    REFERENCE_SUPPORTED_CHECKPOINT,
    REFERENCE_CLIP_VISION,
    REFERENCE_IPADAPTER,
    REFERENCE_WEIGHT,
    REFERENCE_WEIGHT_TYPE,
    REFERENCE_COMBINE_EMBEDS,
    REFERENCE_START_AT,
    REFERENCE_END_AT,
    REFERENCE_EMBEDS_SCALING,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_plan import (
    create_isolated_scene_plan,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_compile import (
    compile_isolated_scene_plan,
    IsolatedSceneCompileError,
)


def fake_inputs():
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": ([REFERENCE_SUPPORTED_CHECKPOINT, "Illustrious.safetensors"], {})}},
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
            "sampler_name": (["euler", "dpm_2"], {}),
            "scheduler": (["normal", "simple"], {}),
            "model": ("MODEL",), "positive": ("CONDITIONING",), "negative": ("CONDITIONING",),
            "latent_image": ("LATENT",), "denoise": ("FLOAT",),
        }},
        "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
        "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
    }


def make_test_catalog():
    catalog = build_catalog(
        [REFERENCE_SUPPORTED_CHECKPOINT],
        ["styles/ink.safetensors"],
        fake_inputs(),
        lambda _kind, _name: True,
    )
    catalog["scene_generation"] = {
        "available": True,
        "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
        "reference": {
            "available": True,
            "required_nodes": ["LoadImage", "CLIPVisionLoader", "IPAdapterModelLoader", "IPAdapterAdvanced"],
            "clip_vision": REFERENCE_CLIP_VISION,
            "ipadapter": REFERENCE_IPADAPTER,
            "weight": REFERENCE_WEIGHT,
            "weight_type": REFERENCE_WEIGHT_TYPE,
            "combine_embeds": REFERENCE_COMBINE_EMBEDS,
            "start_at": REFERENCE_START_AT,
            "end_at": REFERENCE_END_AT,
            "embeds_scaling": REFERENCE_EMBEDS_SCALING,
            "reference_assets": [
                "tegaki_manga_references/heroine_ref_01.png",
                "tegaki_manga_references/rival_ref_02.png",
            ],
        },
    }
    catalog["revision"] = hashlib.sha256(
        json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return catalog


def make_sample_document() -> dict:
    return {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
        "schema_version": "1.0.0",
        "document_id": "doc_test_123",
        "pages": [
            {
                "page_id": "page_1",
                "width_px": 1024,
                "height_px": 1536,
                "style_prompt": "masterpiece, manga style, clean lines",
                "style_negative_prompt": "blurry, low quality",
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "order": 1,
                        "name": "Panel 1",
                        "input_mode": "simple",
                        "prompt": "cat on the roof",
                        "negative_prompt": "human",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40},
                    },
                    {
                        "scene_id": "scene_2",
                        "order": 2,
                        "name": "Panel 2",
                        "input_mode": "cast",
                        "prompt": "girl standing in the room",
                        "negative_prompt": "outdoor",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.40, "h": 0.45},
                    },
                    {
                        "scene_id": "scene_3",
                        "order": 3,
                        "name": "Panel 3",
                        "input_mode": "cast",
                        "prompt": "vintage car parked",
                        "negative_prompt": "",
                        "area": {"shape_type": "rect", "x": 0.55, "y": 0.50, "w": 0.40, "h": 0.45},
                    },
                ],
                "cast": [
                    {
                        "cast_id": "cast_heroine",
                        "display_name": "Heroine",
                        "identity_prompt": "1girl, brown hair, school uniform",
                        "negative_prompt": "boy, man",
                        "color": "#ff6699",
                        "reference_asset": "tegaki_manga_references/heroine_ref_01.png",
                    },
                    {
                        "cast_id": "cast_rival",
                        "display_name": "Rival",
                        "identity_prompt": "1girl, blonde twin-tails",
                        "negative_prompt": "",
                        "color": "#3399ff",
                        "reference_asset": "tegaki_manga_references/rival_ref_02.png",
                    },
                ],
                "character_instances": [
                    {
                        "instance_id": "inst_scene_2_heroine",
                        "cast_id": "cast_heroine",
                        "scene_id": "scene_2",
                        "acting_prompt": "looking shocked, hand over mouth",
                        "area": {"shape_type": "rect", "x": 0.10, "y": 0.55, "w": 0.20, "h": 0.30},
                    },
                    {
                        "instance_id": "inst_scene_3_rival",
                        "cast_id": "cast_rival",
                        "scene_id": "scene_3",
                        "acting_prompt": "leaning on the car hood",
                        "area": {"shape_type": "rect", "x": 0.60, "y": 0.60, "w": 0.25, "h": 0.25},
                    },
                ],
                "guides": [],
            }
        ],
    }


class TestIsolatedSceneCompile(unittest.TestCase):
    """Test suite covering cases A through H of MANGA-ISOLATED-SCENE-COMPILER1."""

    def setUp(self):
        self.catalog = make_test_catalog()
        self.document = make_sample_document()
        self.gen_params = {
            "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
            "sampler_id": "euler",
            "scheduler_id": "normal",
            "steps": 20,
            "cfg": 7.0,
            "seed_requested": "42",
            "mask_feather": 16,
            "panel_strength": 1.0,
        }

    def test_case_a_valid_isolated_plan_compiles_to_expected_graph(self):
        """A. A valid isolated plan compiles to the expected existing graph contract."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        self.assertTrue(result["ok"])
        graph = result["graph"]
        self.assertIsInstance(graph, dict)

        # Check required node classes in compiled graph
        class_types = {node["class_type"] for node in graph.values()}
        expected_classes = {
            "CheckpointLoaderSimple",
            "EmptyLatentImage",
            "TegakiMangaPagePlanFromJSON",
            "TegakiMangaConditioningBuilder",
            "KSampler",
            "VAEDecode",
            "SaveImage",
        }
        self.assertTrue(expected_classes.issubset(class_types), f"Missing classes: {expected_classes - class_types}")

        # Metadata checks
        meta = result["compile_metadata"]
        self.assertEqual(meta["scene_id"], "scene_2")
        self.assertEqual(meta["local_dimensions"], {"width": 512, "height": 768})
        self.assertEqual(meta["selected_instances"], ["inst_scene_2_heroine"])
        self.assertEqual(meta["referenced_cast_ids"], ["cast_heroine"])

    def test_case_b_graph_dimensions_match_local_canvas(self):
        """B. Graph dimensions match the explicit local canvas."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(640, 896))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        graph = result["graph"]
        latent_nodes = [node for node in graph.values() if node["class_type"] == "EmptyLatentImage"]
        self.assertEqual(len(latent_nodes), 1)
        latent_inputs = latent_nodes[0]["inputs"]
        self.assertEqual(latent_inputs["width"], 640)
        self.assertEqual(latent_inputs["height"], 896)
        self.assertEqual(latent_inputs["batch_size"], 1)

    def test_case_c_only_selected_scene_prompt_and_style_contribute(self):
        """C. Only the selected Scene prompt and applicable Page style contribute to the graph."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        # Retrieve TegakiMangaPagePlanFromJSON inputs
        plan_node = next(n for n in result["graph"].values() if n["class_type"] == "TegakiMangaPagePlanFromJSON")
        page_compile_plan = json.loads(plan_node["inputs"]["page_compile_plan_json"])

        self.assertEqual(len(page_compile_plan["panels"]), 1)
        panel = page_compile_plan["panels"][0]

        # Selected scene prompt: "girl standing in the room"
        # Style prompt: "masterpiece, manga style, clean lines"
        self.assertEqual(panel["panel"]["prompt"], "girl standing in the room")
        self.assertEqual(panel["global_prompt"], "masterpiece, manga style, clean lines")
        combined_prompt = panel["compiled_prompt"]
        self.assertIn("girl standing in the room", combined_prompt)
        self.assertIn("masterpiece, manga style, clean lines", combined_prompt)

        # Style negative: "blurry, low quality", Scene negative: "outdoor"
        self.assertEqual(panel["panel"]["negative_prompt"], "outdoor")
        self.assertEqual(panel["global_negative_prompt"], "blurry, low quality")
        combined_neg = panel["compiled_negative_prompt"]
        self.assertIn("blurry, low quality", combined_neg)
        self.assertIn("outdoor", combined_neg)

    def test_case_d_unrelated_scene_and_cast_data_excluded(self):
        """D. Unrelated Scene and CAST data do not enter the compiled graph."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        plan_node = next(n for n in result["graph"].values() if n["class_type"] == "TegakiMangaPagePlanFromJSON")
        plan_json_str = plan_node["inputs"]["page_compile_plan_json"]

        # Scene 1 ("cat on the roof") and Scene 3 ("vintage car parked") must not appear
        self.assertNotIn("cat on the roof", plan_json_str)
        self.assertNotIn("vintage car parked", plan_json_str)
        self.assertNotIn("scene_1", plan_json_str)
        self.assertNotIn("scene_3", plan_json_str)

        # Rival cast ("cast_rival", "blonde twin-tails", "rival_ref_02.png") must not appear
        self.assertNotIn("cast_rival", plan_json_str)
        self.assertNotIn("blonde twin-tails", plan_json_str)
        self.assertNotIn("tegaki_manga_references/rival_ref_02.png", plan_json_str)

    def test_case_e_cast_and_reference_reach_graph_path(self):
        """E. Selected CAST and Reference associations reach the existing graph-building path."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        graph = result["graph"]
        class_types = {node["class_type"] for node in graph.values()}
        reference_classes = {"CLIPVisionLoader", "IPAdapterModelLoader", "LoadImage", "IPAdapterAdvanced"}
        self.assertTrue(reference_classes.issubset(class_types))

        # Check LoadImage node specifies the heroine reference asset
        load_image_node = next(n for n in graph.values() if n["class_type"] == "LoadImage")
        self.assertEqual(load_image_node["inputs"]["image"], "tegaki_manga_references/heroine_ref_01.png [input]")

        # Check IPAdapterAdvanced attention mask is wired to ConditioningBuilder output 6
        ipadapter_node = next(n for n in graph.values() if n["class_type"] == "IPAdapterAdvanced")
        self.assertEqual(ipadapter_node["inputs"]["attn_mask"][1], 6)

    def test_case_f_active_unsupported_guide_fails_explicitly(self):
        """F. An active unsupported Guide fails explicitly."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))

        # Inject an active structural guide into the plan
        bad_plan = copy.deepcopy(plan)
        bad_plan["guides"] = [
            {
                "guide_id": "guide_rough_1",
                "guide_type": "rough_manga",
                "enabled": True,
                "asset_reference": "rough_layout.png",
            }
        ]

        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "ISOLATED_SCENE_GUIDE_UNSUPPORTED")

    def test_case_g_invalid_settings_fail_explicitly(self):
        """G. Invalid settings or unresolved required inputs fail explicitly."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))

        # Missing required parameter: checkpoint_id
        missing_params = copy.deepcopy(self.gen_params)
        del missing_params["checkpoint_id"]
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(plan, missing_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_REQUEST")

        # Invalid steps (< 1)
        bad_steps = copy.deepcopy(self.gen_params)
        bad_steps["steps"] = 0
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(plan, bad_steps, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PARAMETER")

        # Invalid CFG (> 30.0)
        bad_cfg = copy.deepcopy(self.gen_params)
        bad_cfg["cfg"] = 50.0
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(plan, bad_cfg, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PARAMETER")

    def test_case_h_source_plan_is_not_mutated(self):
        """H. The source plan is not mutated."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        plan_copy = copy.deepcopy(plan)

        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        self.assertIsNotNone(result)
        self.assertEqual(plan, plan_copy, "Source plan must not be mutated during compilation")


class TestIsolatedScenePlacementPassthrough(unittest.TestCase):
    """Test suite for MANGA-ISOLATED-SCENE-PLACEMENT-PASSTHROUGH1 (Cases A through H)."""

    def setUp(self):
        self.catalog = make_test_catalog()
        self.document = make_sample_document()
        self.gen_params = {
            "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
            "sampler_id": "euler",
            "scheduler_id": "normal",
            "steps": 20,
            "cfg": 7.0,
            "seed_requested": "42",
            "mask_feather": 16,
            "panel_strength": 1.0,
        }

    def test_case_a_non_origin_scene_page_rectangle_survives_unchanged(self):
        """A. A non-origin Scene's original Page rectangle survives compilation unchanged."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        expected_rect = {"shape_type": "rect", "x": 0.55, "y": 0.50, "w": 0.40, "h": 0.45}
        self.assertEqual(meta["page_target_rect"], expected_rect)
        self.assertEqual(meta["placement_mapping"]["page_target_rect"], expected_rect)

    def test_case_b_local_graph_dimensions_match_canvas(self):
        """B. Local generation graph dimensions still match the isolated canvas."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        graph = result["graph"]
        latent_node = next(n for n in graph.values() if n["class_type"] == "EmptyLatentImage")
        self.assertEqual(latent_node["inputs"]["width"], 512)
        self.assertEqual(latent_node["inputs"]["height"], 768)

        meta = result["compile_metadata"]
        self.assertEqual(meta["local_dimensions"], {"width": 512, "height": 768})

    def test_case_c_page_and_local_dimensions_preserved_distinctly(self):
        """C. Original Page dimensions and local dimensions are both preserved distinctly."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        self.assertEqual(meta["page_dimensions"], {"width": 1024, "height": 1536})
        self.assertEqual(meta["page_context"]["width_px"], 1024)
        self.assertEqual(meta["page_context"]["height_px"], 1536)
        self.assertEqual(meta["local_dimensions"], {"width": 512, "height": 768})
        self.assertNotEqual(meta["page_dimensions"], meta["local_dimensions"])

    def test_case_d_returned_placement_metadata_matches_source_plan(self):
        """D. Returned placement metadata matches the source plan."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        self.assertEqual(meta["placement_mapping"], plan["placement_mapping"])
        self.assertEqual(meta["scene_id"], plan["scene"]["scene_id"])
        self.assertEqual(meta["page_id"], plan["page_context"]["page_id"])
        self.assertEqual(meta["page_index"], plan["page_context"]["page_index"])
        self.assertEqual(meta["transform"], plan["placement_mapping"]["transform"])
        self.assertEqual(meta["local_source_rect"], plan["placement_mapping"]["local_source_rect"])

    def test_case_e_synthetic_scene_area_does_not_overwrite_page_placement(self):
        """E. The synthetic compiler document's local Scene rectangle does not overwrite the original Page placement."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        # The synthetic document places the scene at [0, 0, 1, 1], but page_target_rect must be [0.55, 0.50, 0.40, 0.45]
        self.assertNotEqual(meta["page_target_rect"]["x"], 0.0)
        self.assertEqual(meta["page_target_rect"]["x"], 0.55)
        self.assertEqual(meta["page_target_rect"]["y"], 0.50)
        self.assertEqual(meta["local_source_rect"]["x"], 0.0)
        self.assertEqual(meta["local_source_rect"]["y"], 0.0)

    def test_case_f_source_plan_is_not_mutated(self):
        """F. The source plan is not mutated."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        snapshot = copy.deepcopy(plan)

        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        self.assertIsNotNone(result)
        self.assertEqual(plan, snapshot)

    def test_case_g_mutating_source_plan_after_compile_does_not_affect_metadata(self):
        """G. Mutating the source plan after compilation does not change previously returned metadata."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        # Mutate plan
        plan["placement_mapping"]["page_target_rect"]["x"] = 0.999
        plan["page_context"]["width_px"] = 9999
        plan["local_canvas"]["width"] = 9999

        self.assertEqual(meta["page_target_rect"]["x"], 0.55)
        self.assertEqual(meta["placement_mapping"]["page_target_rect"]["x"], 0.55)
        self.assertEqual(meta["page_dimensions"]["width"], 1024)
        self.assertEqual(meta["local_dimensions"]["width"], 512)

    def test_case_h_missing_or_malformed_placement_fails_explicitly(self):
        """H. Missing or malformed required placement information fails explicitly."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_3", local_dimensions=(512, 768))

        # Missing placement_mapping
        bad_plan1 = copy.deepcopy(plan)
        del bad_plan1["placement_mapping"]
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan1, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PLAN")

        # Missing transform inside placement_mapping
        bad_plan2 = copy.deepcopy(plan)
        del bad_plan2["placement_mapping"]["transform"]
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan2, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PLAN")

        # Inconsistent transform
        bad_plan3 = copy.deepcopy(plan)
        bad_plan3["placement_mapping"]["transform"]["scale_x"] = 0.1
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan3, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INCONSISTENT_PLACEMENT")

        # Missing page_context
        bad_plan4 = copy.deepcopy(plan)
        del bad_plan4["page_context"]
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan4, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PLAN")

        # Invalid page_context dimensions
        bad_plan5 = copy.deepcopy(plan)
        bad_plan5["page_context"]["width_px"] = 0
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated_scene_plan(bad_plan5, self.gen_params, self.catalog)
        self.assertEqual(ctx.exception.code, "INVALID_PAGE_DIMENSIONS")

    def test_case_d_graph_digest_present_in_top_level_and_metadata_identically(self):
        """D. The real Compiler return value contains result['graph_digest'] and result['compile_metadata']['graph_digest'] with identical values."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        top_level_digest = result.get("graph_digest")
        metadata_digest = result.get("compile_metadata", {}).get("graph_digest")

        self.assertIsNotNone(top_level_digest)
        self.assertIsNotNone(metadata_digest)
        self.assertEqual(len(top_level_digest), 64)
        self.assertEqual(top_level_digest, metadata_digest)

    def test_case_e_validated_guide_state_survives_handoff(self):
        """E. The validated guide_state survives the plan-to-Compiler handoff."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(plan.get("guide_state"), {"enabled": False, "active": False})

        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        compile_guide_state = result.get("compile_metadata", {}).get("guide_state")
        self.assertEqual(compile_guide_state, {"enabled": False, "active": False})

    def test_case_f_graph_structure_dimensions_and_placement_unaffected(self):
        """F. Graph structure, local canvas dimensions and original Page placement remain unchanged."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta = result["compile_metadata"]
        self.assertEqual(meta["local_dimensions"], {"width": 512, "height": 768})
        self.assertEqual(meta["page_dimensions"], {"width": 1024, "height": 1536})
        self.assertEqual(meta["page_target_rect"], {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.40, "h": 0.45})
        self.assertEqual(meta["placement_mapping"]["page_target_rect"], {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.40, "h": 0.45})

    def test_case_g_no_injected_fixtures_needed(self):
        """G. No test fixture injects graph_digest into compile_metadata or guide_state into plan after producer returns."""
        # Directly chain real plan to real compile
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        # Ensure guide_state is present natively
        self.assertIn("guide_state", plan)
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        # Ensure graph_digest is present natively in compile_metadata
        self.assertIn("graph_digest", result["compile_metadata"])

    def test_case_ref_a_explicit_reference_settings_match_ipadapter_node(self):
        """A. Active Reference with explicit weight/start/end records values actually present in generated IP-Adapter node."""
        params = copy.deepcopy(self.gen_params)
        params["reference_weight"] = 0.85
        params["reference_start"] = 0.15
        params["reference_end"] = 0.75

        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, params, self.catalog)

        meta_settings = result["compile_metadata"]["effective_settings"]
        self.assertEqual(meta_settings.get("reference_weight"), 0.85)
        self.assertEqual(meta_settings.get("reference_start"), 0.15)
        self.assertEqual(meta_settings.get("reference_end"), 0.75)

        ipadapter_node = next(n for n in result["graph"].values() if n["class_type"] == "IPAdapterAdvanced")
        self.assertEqual(ipadapter_node["inputs"]["weight"], 0.85)
        self.assertEqual(ipadapter_node["inputs"]["start_at"], 0.15)
        self.assertEqual(ipadapter_node["inputs"]["end_at"], 0.75)

    def test_case_ref_b_omitted_reference_settings_record_effective_defaults(self):
        """B. Active Reference with omitted optional settings records effective defaults actually used by graph."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        meta_settings = result["compile_metadata"]["effective_settings"]
        self.assertEqual(meta_settings.get("reference_weight"), 0.70)
        self.assertEqual(meta_settings.get("reference_start"), 0.0)
        self.assertEqual(meta_settings.get("reference_end"), 1.0)

        ipadapter_node = next(n for n in result["graph"].values() if n["class_type"] == "IPAdapterAdvanced")
        self.assertEqual(ipadapter_node["inputs"]["weight"], 0.70)
        self.assertEqual(ipadapter_node["inputs"]["start_at"], 0.0)
        self.assertEqual(ipadapter_node["inputs"]["end_at"], 1.0)

    def test_case_ref_c_changing_reference_settings_changes_recorded_values_and_digest(self):
        """C. Changing Reference weight or timing changes corresponding recorded effective value and graph digest."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))

        params1 = copy.deepcopy(self.gen_params)
        params1["reference_weight"] = 0.50
        result1 = compile_isolated_scene_plan(plan, params1, self.catalog)

        params2 = copy.deepcopy(self.gen_params)
        params2["reference_weight"] = 0.90
        result2 = compile_isolated_scene_plan(plan, params2, self.catalog)

        self.assertEqual(result1["compile_metadata"]["effective_settings"]["reference_weight"], 0.50)
        self.assertEqual(result2["compile_metadata"]["effective_settings"]["reference_weight"], 0.90)
        self.assertNotEqual(result1["graph_digest"], result2["graph_digest"])

    def test_case_ref_d_reference_disabled_does_not_invent_reference_settings(self):
        """D. Reference-disabled compilation does not report invented active Reference conditioning."""
        # scene_1 has input_mode="simple", no instances, no reference
        plan = create_isolated_scene_plan(self.document, scene_id="scene_1", local_dimensions=(512, 768))
        self.assertFalse(plan["reference"]["enabled"])

        result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        meta_settings = result["compile_metadata"]["effective_settings"]

        self.assertNotIn("reference_weight", meta_settings)
        self.assertNotIn("reference_start", meta_settings)
        self.assertNotIn("reference_end", meta_settings)

        self.assertEqual(result["compile_metadata"]["reference"], {"enabled": False, "reference_asset": None})
        ipadapter_nodes = [n for n in result["graph"].values() if n["class_type"] == "IPAdapterAdvanced"]
        self.assertEqual(len(ipadapter_nodes), 0)

    def test_case_ref_e_existing_settings_and_immutability_preserved(self):
        """E, F, G. Existing settings, determinism and plan immutability preserved."""
        plan = create_isolated_scene_plan(self.document, scene_id="scene_2", local_dimensions=(512, 768))
        plan_snapshot = copy.deepcopy(plan)

        result1 = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        result2 = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        # Plan immutability
        self.assertEqual(plan, plan_snapshot)

        # Settings preservation
        meta1 = result1["compile_metadata"]["effective_settings"]
        self.assertEqual(meta1["checkpoint_id"], self.gen_params["checkpoint_id"])
        self.assertEqual(meta1["sampler_id"], "euler")
        self.assertEqual(meta1["scheduler_id"], "normal")
        self.assertEqual(meta1["steps"], 20)
        self.assertEqual(meta1["cfg"], 7.0)
        self.assertEqual(meta1["effective_seed"], 42)

        # Graph digest determinism
        self.assertEqual(result1["graph_digest"], result2["graph_digest"])


if __name__ == "__main__":
    unittest.main()



