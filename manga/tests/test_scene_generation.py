"""Targeted PLAY5 Scene Layout compile contract tests; no model or queue use."""

from __future__ import annotations

import copy
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog
from custom_nodes_custom.tegaki_manga_nodes.minimum_hand_scene_editor import create_default_m1_document
from custom_nodes_custom.tegaki_manga_nodes.page_plan_adapter import TegakiMangaPagePlanFromJSON
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import compile_scene


def fake_inputs():
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": (["Illustrious.safetensors"], {})}},
        "LoraLoader": {"required": {
            "lora_name": (["styles/ink.safetensors", "styles/line.safetensors"], {}),
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


class SceneGenerationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = build_catalog(
            ["Illustrious.safetensors"], ["styles/ink.safetensors", "styles/line.safetensors"],
            fake_inputs(), lambda _kind, _name: True,
        )
        self.catalog["scene_generation"] = {
            "available": True,
            "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
        }
        # Scene capability is part of the reviewed revision.
        self.catalog["revision"] = __import__("hashlib").sha256(
            __import__("json").dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.document = create_default_m1_document()

    def request(self, document=None, **changes):
        value = {
            "request_id": "play5_scene_1", "mode": "scene", "checkpoint_id": "Illustrious.safetensors",
            "authoring_document": copy.deepcopy(document or self.document), "page_index": 0,
            "sampler_id": "euler", "scheduler_id": "normal", "steps": 4, "cfg": 5.0,
            "seed_requested": "0", "capability_revision": self.catalog["revision"],
            "mask_feather": 16, "panel_strength": 1.0,
        }
        value.update(changes)
        return value

    def expect_code(self, code, request=None, **changes):
        with self.assertRaises(Exception) as raised:
            compile_scene(request or self.request(), self.catalog, random_seed=lambda: 17)
        self.assertEqual(getattr(raised.exception, "code", None), code)

    def test_graph_uses_existing_page_plan_conditioning_path_and_resolution(self):
        result = compile_scene(self.request(), self.catalog)
        graph = result["graph"]
        self.assertEqual(result["resolution"], {"width": 832, "height": 1216})
        self.assertEqual(graph["4"]["class_type"], "EmptyLatentImage")
        self.assertEqual(graph["4"]["inputs"], {"width": 832, "height": 1216, "batch_size": 1})
        self.assertEqual(sum(n["class_type"] == "TegakiMangaPagePlanFromJSON" for n in graph.values()), 1)
        self.assertEqual(sum(n["class_type"] == "TegakiMangaConditioningBuilder" for n in graph.values()), 1)
        self.assertEqual(sum(n["class_type"] == "SaveImage" for n in graph.values()), 1)
        self.assertEqual(graph["3"]["inputs"]["mask_feather"], 16)
        self.assertEqual(result["audit_trail"]["scene_ids"], ["scene_top", "scene_bottom"])

    def test_dynamic_prompt_domains_are_deterministic_and_scene_id_stable(self):
        document = copy.deepcopy(self.document)
        document["pages"][0]["style_prompt"] = "page {quiet|bright}"
        document["pages"][0]["scenes"][0]["prompt"] = "top {blue|green}"
        document["pages"][0]["scenes"][1]["prompt"] = "bottom {room|yard}"
        first = compile_scene(self.request(document), self.catalog)
        second = compile_scene(self.request(document), self.catalog)
        self.assertEqual(first["graph_digest"], second["graph_digest"])
        self.assertEqual(first["audit_trail"]["scenes"], second["audit_trail"]["scenes"])
        reordered = copy.deepcopy(document)
        reordered["pages"][0]["scenes"] = list(reversed(reordered["pages"][0]["scenes"]))
        reordered["pages"][0]["scenes"][0]["order"] = 1
        reordered["pages"][0]["scenes"][1]["order"] = 2
        third = compile_scene(self.request(reordered), self.catalog)
        by_id = {entry["scene_id"]: entry for entry in third["audit_trail"]["scenes"]}
        original_by_id = {entry["scene_id"]: entry for entry in first["audit_trail"]["scenes"]}
        for scene_id in original_by_id:
            self.assertEqual(by_id[scene_id]["positive"]["expanded"], original_by_id[scene_id]["positive"]["expanded"])

    def test_global_lora_resolves_but_scene_lora_is_rejected(self):
        document = copy.deepcopy(self.document)
        document["pages"][0]["style_prompt"] = "page <lora:styles/ink:0.7>"
        result = compile_scene(self.request(document), self.catalog)
        self.assertEqual(result["resolved_loras"][0]["id"], "styles/ink.safetensors")
        self.assertEqual(sum(n["class_type"] == "LoraLoader" for n in result["graph"].values()), 1)
        bad = copy.deepcopy(self.document)
        bad["pages"][0]["scenes"][0]["prompt"] = "top <lora:styles/ink:0.7>"
        self.expect_code("SCENE_LORA_UNSUPPORTED", self.request(bad))

    def test_wildcard_emitted_scene_lora_is_rejected_and_ssot_is_unchanged(self):
        document = copy.deepcopy(self.document)
        document["pages"][0]["scenes"][0]["prompt"] = "top __scene_lora__"
        before = copy.deepcopy(document)
        with tempfile.TemporaryDirectory(prefix="tegaki-play5-wildcards-") as directory:
            pathlib.Path(directory, "scene_lora.txt").write_text("<lora:styles/line:0.4>\n", encoding="utf-8")
            previous = os.environ.get("TEGAKI_MANGA_WILDCARDS_DIR")
            os.environ["TEGAKI_MANGA_WILDCARDS_DIR"] = directory
            try:
                self.expect_code("SCENE_LORA_UNSUPPORTED", self.request(document))
            finally:
                if previous is None:
                    os.environ.pop("TEGAKI_MANGA_WILDCARDS_DIR", None)
                else:
                    os.environ["TEGAKI_MANGA_WILDCARDS_DIR"] = previous
        self.assertEqual(document, before)

    def test_simple_only_counts_and_cast_gate_fail_closed(self):
        empty = copy.deepcopy(self.document)
        empty["pages"][0]["scenes"] = []
        self.expect_code("INVALID_DOCUMENT", self.request(empty))
        too_many = copy.deepcopy(self.document)
        while len(too_many["pages"][0]["scenes"]) < 7:
            scene = copy.deepcopy(too_many["pages"][0]["scenes"][0])
            scene["scene_id"] = f"extra_{len(too_many['pages'][0]['scenes'])}"
            scene["order"] = len(too_many["pages"][0]["scenes"]) + 1
            too_many["pages"][0]["scenes"].append(scene)
        self.expect_code("INVALID_DOCUMENT", self.request(too_many))
        cast = copy.deepcopy(self.document)
        cast["pages"][0]["cast"] = [{"cast_id": "cast_a", "display_name": "A", "identity_prompt": "hero", "negative_prompt": "", "color": "#fff", "loras": [], "metadata": {}}]
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(cast))

    def test_one_and_max_six_scene_documents_compile_with_geometry(self):
        one = copy.deepcopy(self.document)
        one["pages"][0]["scenes"] = one["pages"][0]["scenes"][:1]
        one_result = compile_scene(self.request(one), self.catalog)
        self.assertEqual(one_result["scene_ids"], ["scene_top"])
        area = one["pages"][0]["scenes"][0]["area"]
        self.assertEqual(one_result["page_compile_plan"]["panels"][0]["panel"]["geometry"],
                         {key: area[key] for key in ("x", "y", "w", "h")})
        six = copy.deepcopy(self.document)
        for index in range(2, 6):
            scene = copy.deepcopy(six["pages"][0]["scenes"][0])
            scene["scene_id"] = f"scene_{index + 1}"
            scene["name"] = f"Scene {index + 1}"
            scene["order"] = index + 1
            scene["area"]["y"] = round(0.02 + index * 0.17, 4)
            scene["area"]["h"] = 0.12
            six["pages"][0]["scenes"].append(scene)
        six_result = compile_scene(self.request(six), self.catalog)
        self.assertEqual(len(six_result["page_compile_plan"]["panels"]), 6)
        self.assertEqual(six_result["scene_ids"][-1], "scene_6")

    def test_conditioning_builder_receives_global_and_scene_mask_branches(self):
        from custom_nodes_custom.tegaki_manga_nodes import conditioning_builder
        result = compile_scene(self.request(), self.catalog)
        applied = []

        class FakeMasks:
            def build_masks(self, plan, mask_feather=0):
                return (["mask-a", "mask-b"], [], None, "{}", [])

        builder = conditioning_builder.TegakiMangaConditioningBuilder()
        builder._encode_text = lambda _clip, text: [{"text": text}]
        builder._apply_mask = lambda cond, mask, strength, area: applied.append((cond[0]["text"], mask[0], strength, area)) or [{"text": cond[0]["text"], "mask": mask[0]}]
        with patch.object(conditioning_builder, "TegakiMangaMaskBuilder", FakeMasks):
            positive, negative, *_ = builder.build_conditioning(None, result["page_compile_plan"], mask_feather=16)
        self.assertEqual(len(positive), 3)  # global + two scene branches
        self.assertEqual(len(negative), 1)  # empty scene negatives are skipped
        self.assertEqual([entry[1] for entry in applied], ["mask-a", "mask-b"])
        self.assertTrue(all(entry[3] == "default" for entry in applied))

        overlapping = copy.deepcopy(self.document)
        overlapping["pages"][0]["scenes"][1]["area"] = copy.deepcopy(overlapping["pages"][0]["scenes"][0]["area"])
        self.assertEqual(len(compile_scene(self.request(overlapping), self.catalog)["scene_ids"]), 2)

    def test_resolution_authority_and_strict_scene_fields(self):
        request = self.request()
        result = compile_scene(request, self.catalog)
        self.assertNotIn("width", result["normalized_request"])
        self.assertNotIn("height", result["normalized_request"])
        self.expect_code("INVALID_REQUEST", {**request, "width": 832})
        bad = copy.deepcopy(self.document)
        bad["pages"][0]["width_px"] = 840
        resized = compile_scene(self.request(bad), self.catalog)
        self.assertEqual(resized["resolution"], {"width": 840, "height": 1216})
        self.assertEqual(resized["graph"]["4"]["inputs"]["width"], 840)

    def test_regional_tuning_is_optional_and_defaults_are_reviewed(self):
        request = self.request()
        request.pop("mask_feather")
        request.pop("panel_strength")
        result = compile_scene(request, self.catalog)
        self.assertEqual(result["normalized_request"]["mask_feather"], 16)
        self.assertEqual(result["normalized_request"]["panel_strength"], 1.0)
        self.assertEqual(result["graph"]["3"]["inputs"]["mask_feather"], 16)
        self.assertEqual(result["graph"]["3"]["inputs"]["panel_strength"], 1.0)

    def test_minus_one_seed_resolves_once_and_zero_is_retained(self):
        calls = []
        result = compile_scene(self.request(seed_requested="-1"), self.catalog, random_seed=lambda: calls.append(1) or 123)
        self.assertEqual(result["effective_seed"], 123)
        self.assertEqual(calls, [1])
        zero = compile_scene(self.request(seed_requested="0"), self.catalog, random_seed=lambda: calls.append(1) or 456)
        self.assertEqual(zero["effective_seed"], 0)
        self.assertEqual(calls, [1])

    def test_page_plan_adapter_revalidates_transport(self):
        plan = compile_scene(self.request(), self.catalog)["page_compile_plan"]
        adapted = TegakiMangaPagePlanFromJSON().parse_page_compile_plan(__import__("json").dumps(plan))[0]
        self.assertEqual(adapted, plan)
        with self.assertRaises(ValueError):
            TegakiMangaPagePlanFromJSON().parse_page_compile_plan("{bad")


if __name__ == "__main__":
    unittest.main()
