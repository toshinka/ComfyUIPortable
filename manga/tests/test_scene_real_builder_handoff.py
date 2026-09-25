"""test_scene_real_builder_handoff.py — Cross-language real producer-to-builder handoff test.

Card: MANGA-SCENE-REAL-BUILDER-HANDOFF1
Tests the actual data handoff:
  create_isolated_scene_plan(...)
    -> compile_isolated_scene_plan(...)
    -> buildSceneResultManifest(...)
using real Python producer outputs serialized to the real JavaScript Builder over stdin.
"""

from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EMBEDDED_SITE = REPO_ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))

# Ensure custom_nodes_custom package can be imported without triggering ComfyUI runtime
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(REPO_ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
    REFERENCE_SUPPORTED_CHECKPOINT,
    REFERENCE_CLIP_VISION,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_plan import (
    create_isolated_scene_plan,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_compile import (
    compile_isolated_scene_plan,
)

MANIFEST_ID_1 = "11111111-2222-4333-8444-555555555555"
MANIFEST_ID_2 = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
JOB_ID = "22222222-3333-4444-8555-666666666666"
PROMPT_ID = "33333333-4444-4555-8666-777777777777"
SNAPSHOT_DIGEST = "a" * 64
REF_CONTENT_DIGEST = "b" * 64
PNG_DIGEST = "c" * 64


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
            "ipadapter": "ip-adapter-plus_sdxl_vit-h.safetensors",
            "weight": 0.70,
            "weight_type": "linear",
            "combine_embeds": "concat",
            "start_at": 0.0,
            "end_at": 1.0,
            "embeds_scaling": "V only",
            "reference_assets": [
                "tegaki_manga_references/heroine_ref_01.png",
            ],
        },
    }
    return catalog


def make_sample_document():
    return {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
        "schema_version": "1.0.0",
        "document_id": "doc_tegaki_handoff_test",
        "pages": [
            {
                "page_id": "page_main",
                "width_px": 1024,
                "height_px": 1536,
                "style_prompt": "masterpiece, manga monochrome, high contrast",
                "style_negative_prompt": "color, lowres",
                "scenes": [
                    {
                        "scene_id": "scene_disabled_ref",
                        "order": 1,
                        "name": "Simple Panel",
                        "input_mode": "simple",
                        "prompt": "city skyline at night, distant lights",
                        "negative_prompt": "people",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40},
                    },
                    {
                        "scene_id": "scene_active_ref",
                        "order": 2,
                        "name": "Character Panel",
                        "input_mode": "cast",
                        "prompt": "1girl standing in classroom, sunlight from window",
                        "negative_prompt": "darkness",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.45, "h": 0.45},
                    },
                ],
                "cast": [
                    {
                        "cast_id": "cast_heroine",
                        "display_name": "Heroine",
                        "identity_prompt": "1girl, blue hair, school uniform",
                        "negative_prompt": "short hair",
                        "reference_asset": "tegaki_manga_references/heroine_ref_01.png",
                    },
                ],
                "character_instances": [
                    {
                        "instance_id": "inst_heroine_1",
                        "cast_id": "cast_heroine",
                        "scene_id": "scene_active_ref",
                        "acting_prompt": "smiling gently",
                        "area": {"shape_type": "rect", "x": 0.10, "y": 0.55, "w": 0.25, "h": 0.35},
                    },
                ],
                "guides": [],
            }
        ],
    }


def invoke_js_builder(evidence: dict) -> dict:
    """Executes the actual JavaScript buildSceneResultManifest via Node.js subprocess over stdin."""
    node_code = (
        'import { buildSceneResultManifest } from "./manga/service/scene_result_builder.mjs";\n'
        'import fs from "node:fs";\n'
        'const raw = fs.readFileSync(0, "utf8");\n'
        'try {\n'
        '    const input = JSON.parse(raw);\n'
        '    const manifest = buildSceneResultManifest(input);\n'
        '    process.stdout.write(JSON.stringify({ ok: true, manifest }));\n'
        '} catch (err) {\n'
        '    process.stdout.write(JSON.stringify({\n'
        '        ok: false,\n'
        '        error: {\n'
        '            name: err.name,\n'
        '            code: err.code,\n'
        '            message: err.message\n'
        '        }\n'
        '    }));\n'
        '    process.exit(1);\n'
        '}\n'
    )
    res = subprocess.run(
        ["node", "--input-type=module", "-e", node_code],
        input=json.dumps(evidence),
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        timeout=15,
    )
    if res.stdout:
        return json.loads(res.stdout)
    return {
        "ok": False,
        "error": {
            "name": "SubprocessError",
            "code": "SUBPROCESS_FAILED",
            "message": f"Exit code {res.returncode}, stderr: {res.stderr}",
        },
    }


class TestSceneRealBuilderHandoff(unittest.TestCase):
    """Integration test suite executing the actual Python producer-to-JavaScript builder handoff."""

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

    def test_case_disabled_reference_real_handoff(self):
        """Cases A-G, J: Disabled reference real plan & compiler outputs reach the JS Builder."""
        doc_snapshot = copy.deepcopy(self.document)

        # 1. Real isolated plan extraction
        plan = create_isolated_scene_plan(
            self.document,
            scene_id="scene_disabled_ref",
            local_dimensions=(512, 768),
        )

        # Verify real plan properties
        self.assertFalse(plan["reference"]["enabled"])
        self.assertIsNone(plan["reference"]["reference_asset"])
        self.assertEqual(plan["guide_state"], {"enabled": False, "active": False})

        # 2. Real isolated compile execution
        compile_result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)
        self.assertTrue(compile_result["ok"])

        # Untouched compile_metadata from real compiler
        compile_metadata = compile_result["compile_metadata"]
        self.assertEqual(compile_metadata["graph_digest"], compile_result["graph_digest"])
        self.assertNotIn("reference_weight", compile_metadata["effective_settings"])

        # 3. Assemble synthetic execution evidence deriving digests & settings from actual compiler
        evidence = {
            "manifest_id": MANIFEST_ID_1,
            "created_at": "2026-09-25T06:30:00.000Z",
            "owner": {
                "document_id": self.document["document_id"],
                "page_id": "page_main",
                "scene_id": "scene_disabled_ref",
            },
            "snapshot_ref": f"snapshots/{self.document['document_id']}/snap_01.json",
            "snapshot_digest": SNAPSHOT_DIGEST,
            "plan": plan,  # ACTUAL UNTOUCHED PLAN
            "compile_metadata": compile_metadata,  # ACTUAL UNTOUCHED METADATA
            "reference_evidence": {
                "enabled": False,
                "reference_asset": None,
                "content_digest": None,
            },
            "job": {
                "job_id": JOB_ID,
                "prompt_id": PROMPT_ID,
                "state": "SUCCEEDED",
                "graph_digest": compile_result["graph_digest"],
                "page_compile_plan_digest": compile_result["page_compile_plan_digest"],
                "effective_settings": copy.deepcopy(compile_metadata["effective_settings"]),
            },
            "locator": {
                "filename": "scene_disabled_0001.png",
                "subfolder": "manga/scenes",
                "type": "output",
            },
            "png_analysis": {
                "content_digest": PNG_DIGEST,
                "declared_width": compile_metadata["local_dimensions"]["width"],
                "declared_height": compile_metadata["local_dimensions"]["height"],
            },
        }

        # 4. Invoke actual JS Builder via Node.js subprocess
        builder_result = invoke_js_builder(evidence)
        self.assertTrue(
            builder_result["ok"],
            f"Builder rejected real producer data: {builder_result.get('error')}",
        )

        manifest = builder_result["manifest"]

        # Case C: Validated manifest returned
        self.assertEqual(manifest["schema_id"], "TEGAKI_SCENE_RESULT_MANIFEST")
        self.assertEqual(manifest["manifest_id"], MANIFEST_ID_1)

        # Case D: Returned owner identity matches original
        self.assertEqual(manifest["owner"]["document_id"], "doc_tegaki_handoff_test")
        self.assertEqual(manifest["owner"]["page_id"], "page_main")
        self.assertEqual(manifest["owner"]["scene_id"], "scene_disabled_ref")

        # Case E: Graph and compile plan digests match actual compiler output
        self.assertEqual(manifest["execution"]["graph_digest"], compile_result["graph_digest"])
        self.assertEqual(manifest["execution"]["page_compile_plan_digest"], compile_result["page_compile_plan_digest"])

        # Case F: Original page placement survives with normalized local_source_rect
        self.assertEqual(manifest["placement"]["page_target_rect"]["x"], 0.05)
        self.assertEqual(manifest["placement"]["page_target_rect"]["y"], 0.05)
        self.assertEqual(manifest["placement"]["page_target_rect"]["w"], 0.90)
        self.assertEqual(manifest["placement"]["page_target_rect"]["h"], 0.40)
        self.assertEqual(manifest["placement"]["local_source_rect"]["x"], 0.0)
        self.assertEqual(manifest["placement"]["local_source_rect"]["y"], 0.0)
        self.assertEqual(manifest["placement"]["local_source_rect"]["w"], 1.0)
        self.assertEqual(manifest["placement"]["local_source_rect"]["h"], 1.0)
        self.assertEqual(manifest["placement"]["target_page_dimensions"]["width"], 1024)
        self.assertEqual(manifest["placement"]["target_page_dimensions"]["height"], 1536)

        # Case G: Explicit guide-disabled state and disabled reference
        self.assertIsNone(manifest["input_provenance"]["reference_content_digest"])

        # Case J: Input document and producer outputs remain unmodified
        self.assertEqual(self.document, doc_snapshot)

    def test_case_active_reference_real_handoff(self):
        """Case I: Active reference real plan & compiler outputs reach the JS Builder."""
        # Custom reference timing in generation parameters
        gen_params = copy.deepcopy(self.gen_params)
        gen_params["reference_weight"] = 0.85
        gen_params["reference_start"] = 0.10
        gen_params["reference_end"] = 0.80

        # 1. Real isolated plan extraction
        plan = create_isolated_scene_plan(
            self.document,
            scene_id="scene_active_ref",
            local_dimensions=(512, 768),
        )
        self.assertTrue(plan["reference"]["enabled"])
        self.assertEqual(plan["reference"]["reference_asset"], "tegaki_manga_references/heroine_ref_01.png")

        # 2. Real isolated compile execution
        compile_result = compile_isolated_scene_plan(plan, gen_params, self.catalog)
        self.assertTrue(compile_result["ok"])

        compile_metadata = compile_result["compile_metadata"]
        eff_settings = compile_metadata["effective_settings"]

        # Verify actual effective reference settings recorded by compiler
        self.assertEqual(eff_settings["reference_weight"], 0.85)
        self.assertEqual(eff_settings["reference_start"], 0.10)
        self.assertEqual(eff_settings["reference_end"], 0.80)

        # 3. Assemble execution evidence
        evidence = {
            "manifest_id": MANIFEST_ID_2,
            "created_at": "2026-09-25T06:30:00.000Z",
            "owner": {
                "document_id": self.document["document_id"],
                "page_id": "page_main",
                "scene_id": "scene_active_ref",
            },
            "snapshot_ref": f"snapshots/{self.document['document_id']}/snap_02.json",
            "snapshot_digest": SNAPSHOT_DIGEST,
            "plan": plan,  # ACTUAL UNTOUCHED PLAN
            "compile_metadata": compile_metadata,  # ACTUAL UNTOUCHED METADATA
            "reference_evidence": {
                "enabled": True,
                "reference_asset": plan["reference"]["reference_asset"],
                "content_digest": REF_CONTENT_DIGEST,
            },
            "job": {
                "job_id": JOB_ID,
                "prompt_id": PROMPT_ID,
                "state": "SUCCEEDED",
                "graph_digest": compile_result["graph_digest"],
                "page_compile_plan_digest": compile_result["page_compile_plan_digest"],
                "effective_settings": copy.deepcopy(compile_metadata["effective_settings"]),
            },
            "locator": {
                "filename": "scene_active_0001.png",
                "subfolder": "manga/scenes",
                "type": "output",
            },
            "png_analysis": {
                "content_digest": PNG_DIGEST,
                "declared_width": compile_metadata["local_dimensions"]["width"],
                "declared_height": compile_metadata["local_dimensions"]["height"],
            },
        }

        # 4. Invoke actual JS Builder via Node.js subprocess
        builder_result = invoke_js_builder(evidence)
        self.assertTrue(
            builder_result["ok"],
            f"Builder rejected real active reference producer data: {builder_result.get('error')}",
        )

        manifest = builder_result["manifest"]

        # Verify active reference content digest is stored
        self.assertEqual(manifest["input_provenance"]["reference_content_digest"], REF_CONTENT_DIGEST)
        # Verify effective settings in execution record
        self.assertEqual(manifest["execution"]["effective_settings"]["effective_seed"], 42)
        # Verify effective input digest was generated
        self.assertEqual(len(manifest["input_provenance"]["effective_input_digest"]), 64)

    def test_case_h_dimension_mismatch_fails_in_builder(self):
        """Case H: Generated PNG dimensions mismatching real compiled canvas fails."""
        plan = create_isolated_scene_plan(
            self.document,
            scene_id="scene_disabled_ref",
            local_dimensions=(512, 768),
        )
        compile_result = compile_isolated_scene_plan(plan, self.gen_params, self.catalog)

        evidence = {
            "manifest_id": MANIFEST_ID_1,
            "created_at": "2026-09-25T06:30:00.000Z",
            "owner": {
                "document_id": self.document["document_id"],
                "page_id": "page_main",
                "scene_id": "scene_disabled_ref",
            },
            "snapshot_ref": f"snapshots/{self.document['document_id']}/snap_01.json",
            "snapshot_digest": SNAPSHOT_DIGEST,
            "plan": plan,
            "compile_metadata": compile_result["compile_metadata"],
            "reference_evidence": {
                "enabled": False,
                "reference_asset": None,
                "content_digest": None,
            },
            "job": {
                "job_id": JOB_ID,
                "prompt_id": PROMPT_ID,
                "state": "SUCCEEDED",
                "graph_digest": compile_result["graph_digest"],
                "page_compile_plan_digest": compile_result["page_compile_plan_digest"],
                "effective_settings": copy.deepcopy(compile_result["compile_metadata"]["effective_settings"]),
            },
            "locator": {
                "filename": "scene_disabled_0001.png",
                "subfolder": "manga/scenes",
                "type": "output",
            },
            "png_analysis": {
                "content_digest": PNG_DIGEST,
                "declared_width": 768,  # MISMATCH with compiled canvas 512
                "declared_height": 768,
            },
        }

        builder_result = invoke_js_builder(evidence)
        self.assertFalse(builder_result["ok"])
        self.assertEqual(builder_result["error"]["code"], "ARTIFACT_PROVENANCE_ERROR")


if __name__ == "__main__":
    unittest.main()
