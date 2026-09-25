"""Unit tests for isolated-Scene compile API route (Card MANGA-BACKEND-COMPILE-ISOLATED-SCENE-ROUTE1).

Covers cases A through L specified in the Card contract:
Case A: Valid Reference-disabled request (HTTP 200, ok=True, complete graph)
Case B: Correct plan returned (matches direct create_isolated_scene_plan)
Case C: Correct compiler output returned (matches direct compile_isolated_scene_plan)
Case D: Graph digest provenance preserved (root and compile_metadata match)
Case E: Validated guide_state preserved (plan and metadata)
Case F: Placement mapping preserved (page_target_rect and local_source_rect survive)
Case G: Effective settings provenance (reference_weight, reference_start, reference_end)
Case H: Valid active Reference request (compiles successfully without artificial rejection)
Case I: Missing / unknown scene_id (returns 4xx structured error)
Case J: Active structural Guide rejected (422 ISOLATED_SCENE_GUIDE_UNSUPPORTED)
Case K: Source Authoring Document immutability preserved
Case L: Zero execution side effects (pure transformation, no queue/GPU calls)
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
from unittest.mock import MagicMock, patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EMBEDDED_SITE = ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))

# Ensure custom_nodes_custom package can be imported
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

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
    IsolatedScenePlanError,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_compile import (
    compile_isolated_scene_plan,
    IsolatedSceneCompileError,
)
from custom_nodes_custom.tegaki_manga_nodes.basic_generation_api import (
    compile_isolated_scene,
    api_manga_isolated_scene_compile,
    IsolatedSceneEnvelopeError,
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
            ],
        },
        "controlnet": {
            "available": False,
            "required_nodes": [],
            "model": None,
            "default_strength": 0.8,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "guide_assets": [],
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
                ],
                "character_instances": [
                    {
                        "instance_id": "inst_scene_2_heroine",
                        "cast_id": "cast_heroine",
                        "scene_id": "scene_2",
                        "acting_prompt": "looking shocked, hand over mouth",
                        "area": {"shape_type": "rect", "x": 0.10, "y": 0.55, "w": 0.20, "h": 0.30},
                    },
                ],
                "guides": [],
            }
        ],
    }


def make_generation_params() -> dict:
    return {
        "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
        "sampler_id": "euler",
        "scheduler_id": "normal",
        "steps": 28,
        "cfg": 7.0,
        "denoise": 1.0,
        "seed": 123456,
    }


class TestIsolatedSceneCompileApi(AioHTTPTestCase):
    """Test suite verifying isolated-Scene compile API route and pure function."""

    async def get_application(self):
        app = web.Application()
        app.router.add_post(
            "/tegaki/manga/generation/compile-isolated-scene",
            api_manga_isolated_scene_compile,
        )
        return app

    def setUp(self):
        super().setUp()
        self.catalog = make_test_catalog()
        self.doc = make_sample_document()
        self.gen_params = make_generation_params()
        # Patch _live_catalog in basic_generation_api so tests are self-contained
        self.catalog_patcher = patch(
            "custom_nodes_custom.tegaki_manga_nodes.basic_generation_api._live_catalog",
            return_value=self.catalog,
        )
        self.catalog_patcher.start()

    def tearDown(self):
        self.catalog_patcher.stop()
        super().tearDown()

    async def test_case_a_valid_reference_disabled_request(self):
        """Case A: Valid Reference-disabled request returns HTTP 200, ok=True, complete graph."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("graph", data)
        self.assertIn("graph_digest", data)
        self.assertIn("save_node_id", data)
        self.assertIn("compile_metadata", data)
        self.assertIn("page_compile_plan", data)
        self.assertIn("audit_trail", data)

    async def test_case_b_correct_plan_returned(self):
        """Case B: Returned plan is actual output of create_isolated_scene_plan."""
        expected_plan = create_isolated_scene_plan(
            self.doc,
            scene_id="scene_1",
            local_dimensions={"width": 1024, "height": 1024},
        )
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data["plan"], expected_plan)

    async def test_case_c_correct_compiler_output_returned(self):
        """Case C: Returned graph, digests, and metadata match direct compiler call."""
        plan = create_isolated_scene_plan(
            self.doc,
            scene_id="scene_1",
            local_dimensions={"width": 1024, "height": 1024},
        )
        direct_compiled = compile_isolated_scene_plan(
            plan=plan,
            generation_params=self.gen_params,
            catalog=self.catalog,
            random_seed=lambda: 123456,
        )
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        self.assertEqual(data["graph"], direct_compiled["graph"])
        self.assertEqual(data["graph_digest"], direct_compiled["graph_digest"])
        self.assertEqual(data["save_node_id"], direct_compiled["save_node_id"])
        self.assertEqual(data["page_compile_plan"], direct_compiled["page_compile_plan"])
        self.assertEqual(data["page_compile_plan_digest"], direct_compiled["page_compile_plan_digest"])
        self.assertEqual(data["compile_metadata"], direct_compiled["compile_metadata"])

    async def test_case_d_graph_digest_provenance_preserved(self):
        """Case D: graph_digest is present at root and in compile_metadata, and they match."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        root_digest = data.get("graph_digest")
        meta_digest = data.get("compile_metadata", {}).get("graph_digest")

        self.assertIsInstance(root_digest, str)
        self.assertTrue(len(root_digest) >= 32)
        self.assertEqual(root_digest, meta_digest)

    async def test_case_e_validated_guide_state_preserved(self):
        """Case E: plan.guide_state exists and matches compile_metadata."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        self.assertIn("guide_state", data["plan"])
        self.assertEqual(data["plan"]["guide_state"], {"enabled": False, "active": False})
        self.assertEqual(data["compile_metadata"]["guide_state"], data["plan"]["guide_state"])

    async def test_case_f_placement_mapping_preserved(self):
        """Case F: Original Page placement and normalized local source rect survive."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        plan_mapping = data["plan"]["placement_mapping"]
        self.assertIn("page_target_rect", plan_mapping)
        self.assertIn("local_source_rect", plan_mapping)
        self.assertIn("transform", plan_mapping)

        # Scene 1 area from fixture: x: 0.05, y: 0.05, w: 0.90, h: 0.40
        self.assertAlmostEqual(plan_mapping["page_target_rect"]["x"], 0.05)
        self.assertAlmostEqual(plan_mapping["page_target_rect"]["y"], 0.05)
        self.assertAlmostEqual(plan_mapping["page_target_rect"]["w"], 0.90)
        self.assertAlmostEqual(plan_mapping["page_target_rect"]["h"], 0.40)

        # In compile_metadata
        meta = data["compile_metadata"]
        self.assertEqual(meta["page_target_rect"], plan_mapping["page_target_rect"])
        self.assertEqual(meta["local_source_rect"], plan_mapping["local_source_rect"])

    async def test_case_g_effective_settings_provenance(self):
        """Case G: compile_metadata.effective_settings has reference fields."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_2",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        eff = data["compile_metadata"]["effective_settings"]
        self.assertIn("reference_weight", eff)
        self.assertIn("reference_start", eff)
        self.assertIn("reference_end", eff)
        self.assertEqual(eff["reference_weight"], REFERENCE_WEIGHT)
        self.assertEqual(eff["reference_start"], REFERENCE_START_AT)
        self.assertEqual(eff["reference_end"], REFERENCE_END_AT)

    async def test_case_h_valid_active_reference_request(self):
        """Case H: Scene with valid active Reference compiles successfully without artificial rejection."""
        payload = {
            "authoring_document": self.doc,
            "scene_id": "scene_2",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post("/tegaki/manga/generation/compile-isolated-scene", json=payload)
        self.assertEqual(resp.status, 200)
        data = await resp.json()

        self.assertTrue(data["ok"])
        self.assertTrue(data["plan"]["reference"]["enabled"])
        self.assertEqual(
            data["plan"]["reference"]["reference_asset"],
            "tegaki_manga_references/heroine_ref_01.png",
        )

        eff = data["compile_metadata"]["effective_settings"]
        self.assertEqual(eff["reference_weight"], REFERENCE_WEIGHT)
        self.assertEqual(eff["reference_start"], REFERENCE_START_AT)
        self.assertEqual(eff["reference_end"], REFERENCE_END_AT)

        # Graph should contain IPAdapter nodes
        class_types = [node.get("class_type") for node in data["graph"].values()]
        self.assertIn("IPAdapterAdvanced", class_types)
        self.assertIn("CLIPVisionLoader", class_types)

    async def test_case_i_missing_or_unknown_scene_id(self):
        """Case I: Missing/unknown scene_id returns 4xx structured error."""
        # 1. Missing scene_id in envelope -> 400 INVALID_REQUEST
        payload_missing = {
            "authoring_document": self.doc,
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp_missing = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            json=payload_missing,
        )
        self.assertEqual(resp_missing.status, 400)
        data_missing = await resp_missing.json()
        self.assertFalse(data_missing["ok"])
        self.assertEqual(data_missing["error_code"], "INVALID_REQUEST")

        # 2. Unknown scene_id -> 422 SCENE_NOT_FOUND
        payload_unknown = {
            "authoring_document": self.doc,
            "scene_id": "scene_nonexistent",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp_unknown = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            json=payload_unknown,
        )
        self.assertEqual(resp_unknown.status, 422)
        data_unknown = await resp_unknown.json()
        self.assertFalse(data_unknown["ok"])
        self.assertEqual(data_unknown["error_code"], "SCENE_NOT_FOUND")

    async def test_case_j_active_structural_guide_rejected(self):
        """Case J: Active structural Guide rejected with 422 ISOLATED_SCENE_GUIDE_UNSUPPORTED."""
        doc_with_guide = copy.deepcopy(self.doc)
        doc_with_guide["pages"][0]["guides"] = [
            {
                "guide_id": "guide_page1",
                "guide_type": "rough_manga",
                "asset_reference": "tegaki_manga_guides/rough_sketch.png",
                "enabled": True,
            }
        ]
        payload = {
            "authoring_document": doc_with_guide,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        resp = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            json=payload,
        )
        self.assertEqual(resp.status, 422)
        data = await resp.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error_code"], "ISOLATED_SCENE_GUIDE_UNSUPPORTED")

    def test_case_k_immutability_preserved(self):
        """Case K: Source Authoring Document passed in request is identical before and after compilation."""
        doc_original = make_sample_document()
        doc_snapshot = copy.deepcopy(doc_original)
        candidate = {
            "authoring_document": doc_snapshot,
            "scene_id": "scene_1",
            "local_dimensions": {"width": 1024, "height": 1024},
            "generation_params": self.gen_params,
        }
        result = compile_isolated_scene(candidate, self.catalog)
        self.assertTrue(result["ok"])
        self.assertEqual(doc_snapshot, doc_original)

    def test_case_l_zero_execution_side_effects(self):
        """Case L: No ComfyUI queueing, prompt submission, or GPU calls occur during compilation."""
        # Verify compile_isolated_scene is a pure data transformation:
        # It takes JSON-like dicts and returns a JSON-like dict containing the graph.
        mock_prompt_server = MagicMock()
        with patch.dict("sys.modules", {"server": MagicMock(PromptServer=mock_prompt_server)}):
            candidate = {
                "authoring_document": self.doc,
                "scene_id": "scene_1",
                "local_dimensions": {"width": 1024, "height": 1024},
                "generation_params": self.gen_params,
            }
            result = compile_isolated_scene(candidate, self.catalog)
            self.assertTrue(result["ok"])
            # PromptServer was never called to queue or execute
            mock_prompt_server.instance.prompt_queue.put.assert_not_called()

    async def test_envelope_validation_errors(self):
        """Additional envelope validation tests (content type, missing required fields)."""
        # Missing authoring_document -> 400 INVALID_REQUEST
        resp = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            json={"scene_id": "scene_1", "generation_params": self.gen_params},
        )
        self.assertEqual(resp.status, 400)
        self.assertEqual((await resp.json())["error_code"], "INVALID_REQUEST")

        # Missing generation_params -> 400 INVALID_REQUEST
        resp = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            json={"authoring_document": self.doc, "scene_id": "scene_1"},
        )
        self.assertEqual(resp.status, 400)
        self.assertEqual((await resp.json())["error_code"], "INVALID_REQUEST")

        # Invalid Content-Type -> 415 INVALID_CONTENT_TYPE
        resp = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            data="plain text",
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(resp.status, 415)
        self.assertEqual((await resp.json())["error_code"], "INVALID_CONTENT_TYPE")

        # Invalid JSON syntax -> 400 INVALID_JSON
        resp = await self.client.post(
            "/tegaki/manga/generation/compile-isolated-scene",
            data="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status, 400)
        self.assertEqual((await resp.json())["error_code"], "INVALID_JSON")


if __name__ == "__main__":
    unittest.main()
