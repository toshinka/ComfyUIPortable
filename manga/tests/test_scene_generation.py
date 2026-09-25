"""Targeted PLAY5 Scene Layout compile contract tests; no model or queue use."""

from __future__ import annotations

import copy
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from custom_nodes_custom.tegaki_manga_nodes.basic_generation import build_catalog
from custom_nodes_custom.tegaki_manga_nodes.authoring_contract import (
    create_cast_entry,
    create_character_instance,
    create_guide,
)
from custom_nodes_custom.tegaki_manga_nodes.minimum_hand_scene_editor import create_default_m1_document
from custom_nodes_custom.tegaki_manga_nodes.page_plan_adapter import TegakiMangaPagePlanFromJSON
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (
    CONTROLNET_DEFAULT_MODEL,
    CONTROLNET_DEFAULT_STRENGTH,
    CONTROLNET_END_PERCENT,
    CONTROLNET_START_PERCENT,
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
    _reference_character,
)


def fake_inputs():
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": (["Illustrious.safetensors", REFERENCE_SUPPORTED_CHECKPOINT, "sd15_base.safetensors"], {})}},
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
            ["Illustrious.safetensors", REFERENCE_SUPPORTED_CHECKPOINT], ["styles/ink.safetensors", "styles/line.safetensors"],
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
            "request_id": "play5_scene_1", "mode": "scene", "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
            "authoring_document": copy.deepcopy(document or self.document), "page_index": 0,
            "sampler_id": "euler", "scheduler_id": "normal", "steps": 4, "cfg": 5.0,
            "seed_requested": "0", "capability_revision": self.catalog["revision"],
            "mask_feather": 16, "panel_strength": 1.0,
        }
        value.update(changes)
        return value

    def add_reference_capability(self, asset="tegaki_manga_references/ref_c789751db904319d.png"):
        self.catalog["scene_generation"]["reference"] = {
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
            "reference_assets": [asset],
        }
        self.catalog["revision"] = __import__("hashlib").sha256(
            __import__("json").dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def add_controlnet_capability(self, asset="tegaki_manga_guides/rough_guide_test.png", model=CONTROLNET_DEFAULT_MODEL, strength=CONTROLNET_DEFAULT_STRENGTH):
        self.catalog["scene_generation"]["controlnet"] = {
            "available": True,
            "required_nodes": list(SCENE_CONTROLNET_REQUIRED_NODES),
            "model": model,
            "default_strength": strength,
            "start_percent": CONTROLNET_START_PERCENT,
            "end_percent": CONTROLNET_END_PERCENT,
            "guide_assets": [asset] if asset is not None else [],
        }
        self.catalog["revision"] = __import__("hashlib").sha256(
            __import__("json").dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def guide_fixture_document(self, asset="tegaki_manga_guides/rough_guide_test.png", enabled=True):
        document = copy.deepcopy(self.document)
        page = document["pages"][0]
        page["style_prompt"] = "simple illustration, distinct regions"
        page["scenes"] = [
            {
                "scene_id": "scene_left",
                "name": "Left Car Scene",
                "prompt": "red sports car",
                "negative_prompt": "",
                "input_mode": "simple",
                "area": {"shape_type": "rect", "x": 0.05, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 1,
                "metadata": {},
            },
            {
                "scene_id": "scene_right",
                "name": "Right Ocean Scene",
                "prompt": "blue ocean, open sea, horizon",
                "negative_prompt": "",
                "input_mode": "simple",
                "area": {"shape_type": "rect", "x": 0.55, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 2,
                "metadata": {},
            },
        ]
        page["cast"] = []
        page["character_instances"] = []
        page["guides"] = []
        if asset is not None:
            page["guides"].append(create_guide(
                guide_type="rough_manga",
                asset_reference=asset,
                placement={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
                enabled=enabled,
                guide_id="guide_page1",
            ))
        return document


    def reference_document(self, reference_asset="tegaki_manga_references/ref_c789751db904319d.png"):
        document = copy.deepcopy(self.document)
        page = document["pages"][0]
        page["style_prompt"] = "GLOBAL_BASE"
        page["scenes"] = page["scenes"][:1]
        page["scenes"][0]["input_mode"] = "cast"
        page["scenes"][0]["prompt"] = "SCENE_ACTION"
        page["scenes"][0]["area"] = {"shape_type": "rect", "x": 0.10, "y": 0.10, "w": 0.80, "h": 0.80}
        page["cast"] = [create_cast_entry(
            display_name="A", identity_prompt="CHARACTER_IDENTITY", cast_id="cast_a",
            reference_asset=reference_asset,
        )]
        page["character_instances"] = [create_character_instance(
            "cast_a", "scene_top", area={"shape_type": "rect", "x": 0.25, "y": 0.20, "w": 0.20, "h": 0.30},
            acting_prompt="standing in a classroom", instance_id="inst_a",
        )]
        return document

    def text_generation_document(self):
        document = copy.deepcopy(self.document)
        page = document["pages"][0]
        page["style_prompt"] = "GLOBAL_BASE"
        page["scenes"] = page["scenes"][:1]
        scene = page["scenes"][0]
        scene.update({
            "input_mode": "cast", "prompt": "SCENE_ACTION",
            "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8},
        })
        page["cast"] = [
            create_cast_entry(display_name="Unused", identity_prompt="UNUSED_IDENTITY", cast_id="cast_unused"),
            create_cast_entry(display_name="Hero", identity_prompt="CHARACTER_IDENTITY", cast_id="cast_hero"),
        ]
        page["character_instances"] = [create_character_instance(
            "cast_hero", scene["scene_id"],
            area={"shape_type": "rect", "x": 0.25, "y": 0.2, "w": 0.2, "h": 0.3},
            acting_prompt="", instance_id="instance_hero",
        )]
        return document

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

    def test_simple_only_counts_and_unplaced_cast_is_ignored(self):
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
        result = compile_scene(self.request(cast), self.catalog)
        self.assertTrue(all(not panel["characters"] for panel in result["page_compile_plan"]["panels"]))
        self.assertNotIn("hero", result["page_compile_plan_json"])

    def test_one_scene_cast_identity_uses_instance_area_and_existing_conditioner(self):
        from custom_nodes_custom.tegaki_manga_nodes import conditioning_builder

        document = self.text_generation_document()
        result = compile_scene(self.request(document), self.catalog)
        plan = result["page_compile_plan"]
        panel = plan["panels"][0]
        character = panel["characters"][0]
        instance_area = {"shape_type": "rect", "x": 0.25, "y": 0.2, "w": 0.2, "h": 0.3}

        self.assertEqual(plan["global_prompt"], "GLOBAL_BASE")
        self.assertEqual(panel["panel"]["prompt"], "SCENE_ACTION")
        self.assertEqual(character["combined_prompt"], "CHARACTER_IDENTITY")
        self.assertEqual(character["area"], instance_area)
        self.assertEqual(character["coordinate_space"], "page")
        self.assertNotEqual(character["area"], panel["panel"]["geometry"])
        self.assertIn("GLOBAL_BASE", result["graph"]["2"]["inputs"]["page_compile_plan_json"])
        self.assertIn("SCENE_ACTION", result["graph"]["2"]["inputs"]["page_compile_plan_json"])
        self.assertIn("CHARACTER_IDENTITY", result["graph"]["2"]["inputs"]["page_compile_plan_json"])
        self.assertNotIn("UNUSED_IDENTITY", result["graph"]["2"]["inputs"]["page_compile_plan_json"])
        self.assertFalse(any(node["class_type"] in {"LoadImage", "IPAdapterAdvanced", "ControlNetLoader"}
                             for node in result["graph"].values()))

        applied = {}
        builder = conditioning_builder.TegakiMangaConditioningBuilder()
        builder._encode_text = lambda _clip, text: [{"text": text}]

        def capture_mask(conditioning, mask, _strength, _set_cond_area):
            text = conditioning[0]["text"]
            applied[text] = mask[0].clone()
            return [{"text": text, "mask": mask[0]}]

        builder._apply_mask = capture_mask
        positive, _negative, *_ = builder.build_conditioning(None, plan, mask_feather=0)
        self.assertIn("GLOBAL_BASE", [entry["text"] for entry in positive])
        self.assertIn("SCENE_ACTION", applied)
        self.assertIn("CHARACTER_IDENTITY", applied)
        height, width = plan["canvas"]["height"], plan["canvas"]["width"]
        inside_instance = (int(0.3 * height), int(0.3 * width))
        inside_scene_only = (int(0.7 * height), int(0.7 * width))
        scene_mask = applied["SCENE_ACTION"]
        character_mask = applied["CHARACTER_IDENTITY"]
        self.assertEqual(float(character_mask[inside_instance]), 1.0)
        self.assertEqual(float(character_mask[inside_scene_only]), 0.0)
        self.assertEqual(float(scene_mask[inside_scene_only]), 1.0)

    def test_unsupported_cast_shapes_and_invalid_bindings_fail_closed(self):
        document = self.text_generation_document()

        wrong_parent = copy.deepcopy(document)
        wrong_parent["pages"][0]["character_instances"][0]["scene_id"] = "missing_scene"
        self.expect_code("INVALID_DOCUMENT", self.request(wrong_parent))

        missing_cast = copy.deepcopy(document)
        missing_cast["pages"][0]["character_instances"][0]["cast_id"] = "missing_cast"
        self.expect_code("INVALID_DOCUMENT", self.request(missing_cast))

        outside_parent = copy.deepcopy(document)
        outside_parent["pages"][0]["character_instances"][0]["area"]["x"] = 0.75
        self.expect_code("SCENE_CHARACTER_AREA_INVALID", self.request(outside_parent))

        multiple_instances = copy.deepcopy(document)
        second = copy.deepcopy(multiple_instances["pages"][0]["character_instances"][0])
        second.update({"instance_id": "instance_2", "area": {"shape_type": "rect", "x": 0.5, "y": 0.2, "w": 0.2, "h": 0.3}})
        third = copy.deepcopy(second)
        third.update({"instance_id": "instance_3", "area": {"shape_type": "rect", "x": 0.2, "y": 0.5, "w": 0.2, "h": 0.3}})
        multiple_instances["pages"][0]["character_instances"].extend([second, third])
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(multiple_instances))

        multiple_scenes = copy.deepcopy(document)
        extra_scene = copy.deepcopy(multiple_scenes["pages"][0]["scenes"][0])
        extra_scene.update({"scene_id": "scene_extra", "order": 2, "input_mode": "cast"})
        multiple_scenes["pages"][0]["scenes"].append(extra_scene)
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(multiple_scenes))

        unplaced_cast_scene = copy.deepcopy(document)
        unplaced_cast_scene["pages"][0]["character_instances"] = []
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(unplaced_cast_scene))

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

    def test_one_reference_compiles_the_product_ipadapter_path(self):
        self.add_reference_capability()
        result = compile_scene(self.request(self.reference_document()), self.catalog)
        graph = result["graph"]
        by_class = {node["class_type"]: (node_id, node) for node_id, node in graph.items()}
        classes = [node["class_type"] for node in graph.values()]
        for class_name in ("LoadImage", "CLIPVisionLoader", "IPAdapterModelLoader", "IPAdapterAdvanced"):
            self.assertEqual(classes.count(class_name), 1)
        ref_id, ref_node = by_class["IPAdapterAdvanced"]
        conditioning_id, conditioning_node = by_class["TegakiMangaConditioningBuilder"]
        sampler_node = by_class["KSampler"][1]
        image_id, image_node = by_class["LoadImage"]
        clip_id, _ = by_class["CLIPVisionLoader"]
        adapter_id, _ = by_class["IPAdapterModelLoader"]
        self.assertEqual(ref_node["inputs"]["weight"], REFERENCE_WEIGHT)
        self.assertEqual(ref_node["inputs"]["weight_type"], REFERENCE_WEIGHT_TYPE)
        self.assertEqual(ref_node["inputs"]["combine_embeds"], REFERENCE_COMBINE_EMBEDS)
        self.assertEqual(ref_node["inputs"]["start_at"], REFERENCE_START_AT)
        self.assertEqual(ref_node["inputs"]["end_at"], REFERENCE_END_AT)
        self.assertEqual(ref_node["inputs"]["embeds_scaling"], REFERENCE_EMBEDS_SCALING)
        self.assertEqual(ref_node["inputs"]["image"], [image_id, 0])
        self.assertEqual(ref_node["inputs"]["ipadapter"], [adapter_id, 0])
        self.assertEqual(ref_node["inputs"]["clip_vision"], [clip_id, 0])
        self.assertEqual(ref_node["inputs"]["attn_mask"], [conditioning_id, 6])
        self.assertEqual(sampler_node["inputs"]["model"], [ref_id, 0])
        self.assertEqual(sampler_node["inputs"]["positive"], [conditioning_id, 0])
        self.assertEqual(sampler_node["inputs"]["negative"], [conditioning_id, 1])
        self.assertEqual(conditioning_node["inputs"]["page_compile_plan"], [by_class["TegakiMangaPagePlanFromJSON"][0], 0])
        self.assertEqual(image_node["inputs"]["image"],
                         "tegaki_manga_references/ref_c789751db904319d.png [input]")
        plan = result["page_compile_plan"]
        panel = plan["panels"][0]
        character = panel["characters"][0]
        self.assertEqual(plan["global_prompt"], "GLOBAL_BASE")
        self.assertEqual(panel["panel"]["prompt"], "SCENE_ACTION")
        self.assertEqual(character["raw_identity_prompt"], "CHARACTER_IDENTITY")
        self.assertEqual(panel["panel"]["geometry"], {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8})
        self.assertEqual(character["area"], {"shape_type": "rect", "x": 0.25, "y": 0.2, "w": 0.2, "h": 0.3})
        self.assertNotEqual(panel["panel"]["geometry"], character["area"])
        self.assertEqual(character["reference_asset"], "tegaki_manga_references/ref_c789751db904319d.png")
        self.assertTrue(result["audit_trail"]["reference"]["enabled"])

    def test_reference_rejects_unverified_checkpoint_but_text_only_remains_supported(self):
        self.add_reference_capability()
        self.catalog["checkpoints"].append({
            "id": "sd15_base.safetensors", "available": True, "family": "UNKNOWN", "family_confidence": "UNKNOWN",
        })
        self.catalog["revision"] = __import__("hashlib").sha256(
            __import__("json").dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        referenced = self.reference_document()
        # Incompatible architecture rejected
        self.expect_code(
            "REFERENCE_CHECKPOINT_UNSUPPORTED",
            self.request(referenced, checkpoint_id="sd15_base.safetensors", capability_revision=self.catalog["revision"]),
        )
        # Illustrious checkpoint accepted for reference
        result_illustrious = compile_scene(
            self.request(referenced, checkpoint_id="Illustrious.safetensors", capability_revision=self.catalog["revision"]),
            self.catalog,
        )
        self.assertTrue(any(node["class_type"] == "IPAdapterAdvanced" for node in result_illustrious["graph"].values()))
        # Text-only on sd15 checkpoint remains supported without IPAdapter
        text_only = self.reference_document(reference_asset=None)
        result = compile_scene(
            self.request(text_only, checkpoint_id="sd15_base.safetensors", capability_revision=self.catalog["revision"]),
            self.catalog,
        )
        self.assertFalse(any(node["class_type"] == "IPAdapterAdvanced" for node in result["graph"].values()))

    def test_unavailable_reference_asset_fails_explicitly(self):
        self.add_reference_capability()
        document = self.reference_document("tegaki_manga_references/not_registered.png")
        self.expect_code("REFERENCE_ASSET_UNAVAILABLE", self.request(document))

    def test_reference_execution_uses_top_level_asset_without_metadata(self):
        plan = {"panels": [{"characters": [{"reference_asset": "tegaki_manga_references/ref.png", "metadata": {}}]}]}
        self.assertIsNotNone(_reference_character(plan))
        metadata_only = {"panels": [{"characters": [{"metadata": {"reference_asset": "tegaki_manga_references/ref.png"}}]}]}
        self.assertIsNone(_reference_character(metadata_only))

    def test_cast_without_reference_keeps_text_conditioning_and_no_ipadapter(self):
        document = self.reference_document(reference_asset=None)
        result = compile_scene(self.request(document), self.catalog)
        self.assertFalse(any(node["class_type"] == "IPAdapterAdvanced" for node in result["graph"].values()))
        self.assertFalse(result["audit_trail"]["reference"]["enabled"])

    def test_multiple_referenced_instances_fail_closed(self):
        self.add_reference_capability()
        self.add_reference_capability("tegaki_manga_references/ref_other.png")
        document = self.reference_document()
        page = document["pages"][0]
        # Add second CAST with different reference asset
        page["cast"].append(create_cast_entry(
            display_name="B", identity_prompt="CHARACTER_B", cast_id="cast_b",
            reference_asset="tegaki_manga_references/ref_other.png",
        ))
        page["character_instances"].append(create_character_instance(
            "cast_b", "scene_top", area={"shape_type": "rect", "x": 0.50, "y": 0.15, "w": 0.35, "h": 0.60},
            instance_id="inst_b",
        ))
        # Two different reference assets fail with REFERENCE_MULTI_ASSET_UNSUPPORTED
        self.expect_code("REFERENCE_MULTI_ASSET_UNSUPPORTED", self.request(document))

        # Three instances fail with SCENE_CAST_UNSUPPORTED
        page["character_instances"].append(create_character_instance(
            "cast_a", "scene_top", area={"shape_type": "rect", "x": 0.10, "y": 0.10, "w": 0.20, "h": 0.20},
            instance_id="inst_c",
        ))
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(document))

    def test_reference_prerequisite_missing_fails_before_graph(self):
        document = self.reference_document()
        self.expect_code("REFERENCE_RUNTIME_UNAVAILABLE", self.request(document))

    def test_character_area_is_required_for_the_mask_path(self):
        self.add_reference_capability()
        document = self.reference_document()
        document["pages"][0]["character_instances"][0]["area"] = None
        self.expect_code("SCENE_CHARACTER_AREA_INVALID", self.request(document))

    def test_digest_determinism_across_numeric_representations(self):
        self.add_reference_capability()
        doc = self.reference_document()
        # Test int vs float cfg and panel_strength
        req_int = self.request(doc, cfg=5, panel_strength=1)
        req_float = self.request(doc, cfg=5.0, panel_strength=1.0)
        res_int = compile_scene(req_int, self.catalog)
        res_float = compile_scene(req_float, self.catalog)
        self.assertEqual(res_int["graph_digest"], res_float["graph_digest"])
        self.assertEqual(res_int["audit_trail"]["graph_digest"], res_float["audit_trail"]["graph_digest"])

        # Multiple compilations of the exact same request produce identical digests
        res_float_2 = compile_scene(self.request(doc, cfg=5.0, panel_strength=1.0), self.catalog)
        self.assertEqual(res_float["graph_digest"], res_float_2["graph_digest"])

        # Non-reference scene compile is also deterministic
        doc_no_ref = self.reference_document(reference_asset=None)
        res_noref_1 = compile_scene(self.request(doc_no_ref, cfg=5), self.catalog)
        res_noref_2 = compile_scene(self.request(doc_no_ref, cfg=5.0), self.catalog)
        self.assertEqual(res_noref_1["graph_digest"], res_noref_2["graph_digest"])

        # Deliberately changed semantic setting (cfg) produces a different digest
        res_diff_cfg = compile_scene(self.request(doc, cfg=6.0), self.catalog)
        self.assertNotEqual(res_float["graph_digest"], res_diff_cfg["graph_digest"])

        # Deliberately changed reference asset produces a different digest
        self.add_reference_capability("tegaki_manga_references/other.png")
        doc_other = self.reference_document("tegaki_manga_references/other.png")
        res_diff_ref = compile_scene(self.request(doc_other, cfg=5.0), self.catalog)
        self.assertNotEqual(res_float["graph_digest"], res_diff_ref["graph_digest"])

    def test_text_only_scene_generation_compiles_without_guide(self):
        """Card §11.A: Existing text-only Scene generation compiles without a Guide."""
        doc = self.guide_fixture_document(asset=None)
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        classes = [node["class_type"] for node in graph.values()]
        self.assertNotIn("ControlNetLoader", classes)
        self.assertNotIn("ControlNetApplyAdvanced", classes)
        self.assertNotIn("LoadImage", classes)
        # KSampler positive and negative connect directly to TegakiMangaConditioningBuilder
        sampler = [n for n in graph.values() if n["class_type"] == "KSampler"][0]
        cond_builder_id = [k for k, n in graph.items() if n["class_type"] == "TegakiMangaConditioningBuilder"][0]
        self.assertEqual(sampler["inputs"]["positive"], [cond_builder_id, 0])
        self.assertEqual(sampler["inputs"]["negative"], [cond_builder_id, 1])
        self.assertFalse(res["audit_trail"]["controlnet"]["enabled"])

    def test_disabled_guide_falls_back_to_text_only(self):
        """Card §9: Disabled guide compiles as text-only without ControlNet."""
        doc = self.guide_fixture_document(enabled=False)
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        classes = [node["class_type"] for node in graph.values()]
        self.assertNotIn("ControlNetLoader", classes)
        self.assertNotIn("ControlNetApplyAdvanced", classes)
        self.assertFalse(res["audit_trail"]["controlnet"]["enabled"])

    def test_structural_guide_connects_to_controlnet_and_sampler(self):
        """Card §11.B,C,D,E: Guide image reaches ControlNet; model/control connected; scene conditioning preserved; sampler receives ControlNet."""
        self.add_controlnet_capability(asset="tegaki_manga_guides/rough_layout1.png")
        doc = self.guide_fixture_document(asset="tegaki_manga_guides/rough_layout1.png")
        req = self.request(doc, controlnet_strength=0.30)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]

        # Node existence
        load_images = [k for k, n in graph.items() if n["class_type"] == "LoadImage"]
        cnet_loaders = [k for k, n in graph.items() if n["class_type"] == "ControlNetLoader"]
        cnet_applies = [k for k, n in graph.items() if n["class_type"] == "ControlNetApplyAdvanced"]
        cond_builders = [k for k, n in graph.items() if n["class_type"] == "TegakiMangaConditioningBuilder"]
        plan_adapters = [k for k, n in graph.items() if n["class_type"] == "TegakiMangaPagePlanFromJSON"]
        samplers = [k for k, n in graph.items() if n["class_type"] == "KSampler"]

        self.assertEqual(len(load_images), 1)
        self.assertEqual(len(cnet_loaders), 1)
        self.assertEqual(len(cnet_applies), 1)
        self.assertEqual(len(cond_builders), 1)
        self.assertEqual(len(plan_adapters), 1)
        self.assertEqual(len(samplers), 1)

        cnet_img_id = load_images[0]
        cnet_loader_id = cnet_loaders[0]
        cnet_apply_id = cnet_applies[0]
        cond_builder_id = cond_builders[0]
        sampler = samplers[0]

        # Card §11.B: Guide image reaches LoadImage input and ControlNetApplyAdvanced image input
        self.assertEqual(graph[cnet_img_id]["inputs"]["image"], "tegaki_manga_guides/rough_layout1.png [input]")
        self.assertEqual(graph[cnet_apply_id]["inputs"]["image"], [cnet_img_id, 0])

        # Card §11.C: Model and control image connected to final generation graph through correct nodes
        self.assertEqual(graph[cnet_loader_id]["inputs"]["control_net_name"], CONTROLNET_DEFAULT_MODEL)
        self.assertEqual(graph[cnet_apply_id]["inputs"]["control_net"], [cnet_loader_id, 0])
        self.assertEqual(graph[cnet_apply_id]["inputs"]["vae"], ["1", 2])
        self.assertEqual(graph[cnet_apply_id]["inputs"]["strength"], 0.30)
        self.assertEqual(graph[cnet_apply_id]["inputs"]["start_percent"], 0.0)
        self.assertEqual(graph[cnet_apply_id]["inputs"]["end_percent"], 1.0)

        # Card §11.D: Global and both Scene conditioning paths remain present in plan and builder
        self.assertEqual(graph[cnet_apply_id]["inputs"]["positive"], [cond_builder_id, 0])
        self.assertEqual(graph[cnet_apply_id]["inputs"]["negative"], [cond_builder_id, 1])
        plan = json.loads(graph[plan_adapters[0]]["inputs"]["page_compile_plan_json"])
        self.assertEqual(len(plan["panels"]), 2)
        prompts = [p["panel"]["prompt"] for p in plan["panels"]]
        self.assertIn("red sports car", prompts)
        self.assertIn("blue ocean, open sea, horizon", prompts)

        # Card §11.E: ControlNet conditioning reaches the actual sampler inputs
        self.assertEqual(graph[sampler]["inputs"]["positive"], [cnet_apply_id, 0])
        self.assertEqual(graph[sampler]["inputs"]["negative"], [cnet_apply_id, 1])

        # Audit trail records ControlNet activation
        self.assertTrue(res["audit_trail"]["controlnet"]["enabled"])
        self.assertEqual(res["audit_trail"]["controlnet"]["asset_reference"], "tegaki_manga_guides/rough_layout1.png")
        self.assertEqual(res["audit_trail"]["controlnet"]["strength"], 0.30)

    def test_missing_model_and_image_produce_truthful_explicit_errors(self):
        """Card §11.F: Missing model, unavailable asset, missing runtime, or invalid params produce explicit errors."""
        # Missing runtime
        doc = self.guide_fixture_document(asset="tegaki_manga_guides/rough_layout1.png")
        self.expect_code("CONTROLNET_RUNTIME_UNAVAILABLE", self.request(doc))

        # Runtime present but guide asset missing from catalog
        self.add_controlnet_capability(asset="tegaki_manga_guides/known_asset.png")
        doc_missing_asset = self.guide_fixture_document(asset="tegaki_manga_guides/unknown_asset.png")
        self.expect_code("GUIDE_ASSET_UNAVAILABLE", self.request(doc_missing_asset))

        # Guide asset invalid format (traversal/absolute) caught by schema validation
        doc_invalid_asset = self.guide_fixture_document(asset="/absolute/path.png")
        self.expect_code("INVALID_DOCUMENT", self.request(doc_invalid_asset))

        # Multiple active guides
        doc_multi = self.guide_fixture_document(asset="tegaki_manga_guides/known_asset.png")
        doc_multi["pages"][0]["guides"].append(create_guide(
            guide_type="rough_manga",
            asset_reference="tegaki_manga_guides/known_asset.png",
            placement={"x": 0, "y": 0, "w": 1, "h": 1},
            enabled=True,
            guide_id="guide_2",
        ))
        self.expect_code("GUIDE_MULTI_INSTANCE_UNSUPPORTED", self.request(doc_multi))

        # Unsupported checkpoint
        self.add_controlnet_capability(asset="tegaki_manga_guides/known_asset.png")
        doc_good = self.guide_fixture_document(asset="tegaki_manga_guides/known_asset.png")
        # Change checkpoint to non-illustrious
        self.catalog["checkpoints"].append({"id": "sd15_base.safetensors", "available": True, "family": "UNKNOWN", "family_confidence": "UNKNOWN"})
        self.catalog["revision"] = __import__("hashlib").sha256(
            __import__("json").dumps(self.catalog, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.expect_code("CONTROLNET_CHECKPOINT_UNSUPPORTED", self.request(doc_good, checkpoint_id="sd15_base.safetensors", capability_revision=self.catalog["revision"]))

    def test_unsupported_document_shapes_retain_existing_validation(self):
        """Card §11.G: Unsupported document shapes retain existing validation."""
        self.add_controlnet_capability(asset="tegaki_manga_guides/rough_layout1.png")
        doc = self.guide_fixture_document(asset="tegaki_manga_guides/rough_layout1.png")
        # 0 scenes rejected
        doc["pages"][0]["scenes"] = []
        self.expect_code("INVALID_DOCUMENT", self.request(doc))

        # Invalid page index rejected
        doc_good = self.guide_fixture_document(asset="tegaki_manga_guides/rough_layout1.png")
        self.expect_code("INVALID_PAGE_INDEX", self.request(doc_good, page_index=99))

    def test_combined_guide_and_cast_reference_compiles_both_paths(self):
        """Card COMBINED1: Combined Guide and CAST Reference compiles both ControlNet and IP-Adapter paths."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_reference_capability(asset=ref_asset)
        self.add_controlnet_capability(asset=guide_asset)

        doc = self.reference_document(reference_asset=ref_asset)
        doc["pages"][0]["guides"] = [create_guide(
            guide_type="rough_manga",
            asset_reference=guide_asset,
            placement={"x": 0, "y": 0, "w": 1, "h": 1},
            enabled=True,
            guide_id="guide_combined_1",
        )]
        req = self.request(doc, controlnet_strength=0.35)
        res = compile_scene(req, self.catalog)

        self.assertTrue(res["ok"])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertTrue(res["audit_trail"]["controlnet"]["enabled"])
        self.assertEqual(res["audit_trail"]["controlnet"]["strength"], 0.35)

        graph = res["graph"]
        classes = {k: v["class_type"] for k, v in graph.items()}
        self.assertIn("ControlNetApplyAdvanced", classes.values())
        self.assertIn("IPAdapterAdvanced", classes.values())

        # KSampler receives IP-Adapter model and ControlNet conditioning
        ksampler = [v for v in graph.values() if v["class_type"] == "KSampler"][0]
        cnet_apply = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        ip_apply = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]

        self.assertEqual(ksampler["inputs"]["model"], [ip_apply, 0])
        self.assertEqual(ksampler["inputs"]["positive"], [cnet_apply, 0])
        self.assertEqual(ksampler["inputs"]["negative"], [cnet_apply, 1])

    def multi_scene_single_cast_document(self, reference_asset=None, guide_asset=None, guide_enabled=True):
        doc = copy.deepcopy(self.document)
        page = doc["pages"][0]
        page["style_prompt"] = "monochrome manga, high contrast, clean line art"
        page["scenes"] = [
            {
                "scene_id": "scene_left",
                "name": "Left CAST Scene",
                "prompt": "standing outdoors in a courtyard, trees",
                "negative_prompt": "",
                "input_mode": "cast",
                "area": {"shape_type": "rect", "x": 0.05, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 1,
                "metadata": {},
            },
            {
                "scene_id": "scene_right",
                "name": "Right Simple Scene",
                "prompt": "ceramic flower vase with roses, indoors",
                "negative_prompt": "",
                "input_mode": "simple",
                "area": {"shape_type": "rect", "x": 0.55, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 2,
                "metadata": {},
            },
        ]
        page["cast"] = [create_cast_entry(
            display_name="Heroine",
            identity_prompt="1girl, silver hair, school uniform",
            cast_id="cast_heroine",
            reference_asset=reference_asset,
        )]
        page["character_instances"] = [create_character_instance(
            "cast_heroine",
            "scene_left",
            area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60},
            acting_prompt="standing, looking forward",
            instance_id="inst_heroine",
        )]
        page["guides"] = []
        if guide_asset is not None:
            page["guides"].append(create_guide(
                guide_type="rough_manga",
                asset_reference=guide_asset,
                placement={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
                enabled=guide_enabled,
                guide_id="guide_multi_1",
            ))
        return doc

    def test_two_scenes_one_cast_instance_compilation(self):
        """Card §7: Two Scenes (Left CAST + 1 instance, Right simple) compile without reference or guide."""
        doc = self.multi_scene_single_cast_document(reference_asset=None, guide_asset=None)
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        plan = res["page_compile_plan"]
        self.assertEqual(len(plan["panels"]), 2)

        left_panel = plan["panels"][0]
        right_panel = plan["panels"][1]
        self.assertIn("courtyard", left_panel["panel"]["prompt"])
        self.assertIn("vase", right_panel["panel"]["prompt"])
        self.assertEqual(len(left_panel["characters"]), 1)
        self.assertEqual(len(right_panel["characters"]), 0)

        char = left_panel["characters"][0]
        self.assertEqual(char["cast_id"], "cast_heroine")
        self.assertIn("1girl, silver hair", char["combined_prompt"])
        self.assertEqual(char["area"], {"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60})

        scenes_audit = res["audit_trail"]["scenes"]
        self.assertEqual(len(scenes_audit), 2)
        self.assertIn("courtyard", scenes_audit[0]["positive"]["raw"])
        self.assertIn("vase", scenes_audit[1]["positive"]["raw"])

        graph = res["graph"]
        classes = [node["class_type"] for node in graph.values()]
        self.assertNotIn("IPAdapterAdvanced", classes)
        self.assertNotIn("ControlNetApplyAdvanced", classes)
        self.assertFalse(res["audit_trail"]["reference"]["enabled"])
        self.assertFalse(res["audit_trail"]["controlnet"]["enabled"])

    def test_two_scenes_one_cast_instance_with_reference(self):
        """Card §7: Two Scenes + 1 CAST instance + Reference: IP-Adapter receives attn_mask and patches model."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        self.add_reference_capability(asset=ref_asset)
        doc = self.multi_scene_single_cast_document(reference_asset=ref_asset, guide_asset=None)
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])

        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        ksampler_id = [k for k, v in graph.items() if v["class_type"] == "KSampler"][0]

        # IPAdapterAdvanced receives reference mask at port 6
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        # KSampler receives patched model from IPAdapterAdvanced
        self.assertEqual(graph[ksampler_id]["inputs"]["model"], [ipa_id, 0])
        # KSampler receives positive/negative directly from TegakiMangaConditioningBuilder
        self.assertEqual(graph[ksampler_id]["inputs"]["positive"], [cond_builder_id, 0])
        self.assertEqual(graph[ksampler_id]["inputs"]["negative"], [cond_builder_id, 1])

        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertFalse(res["audit_trail"]["controlnet"]["enabled"])

    def test_two_scenes_one_cast_instance_with_reference_and_guide(self):
        """Card §7: Two Scenes + 1 CAST instance + Reference + Guide: IP-Adapter and ControlNet combined."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_reference_capability(asset=ref_asset)
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.multi_scene_single_cast_document(reference_asset=ref_asset, guide_asset=guide_asset, guide_enabled=True)
        res = compile_scene(self.request(doc, controlnet_strength=0.35), self.catalog)
        self.assertTrue(res["ok"])

        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        capply_id = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        ksampler_id = [k for k, v in graph.items() if v["class_type"] == "KSampler"][0]

        # IPAdapter receives reference mask at port 6
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        # ControlNetApplyAdvanced receives positive/negative conditioning from ConditioningBuilder
        self.assertEqual(graph[capply_id]["inputs"]["positive"], [cond_builder_id, 0])
        self.assertEqual(graph[capply_id]["inputs"]["negative"], [cond_builder_id, 1])
        # KSampler receives patched model from IPAdapter and guided conditioning from ControlNet
        self.assertEqual(graph[ksampler_id]["inputs"]["model"], [ipa_id, 0])
        self.assertEqual(graph[ksampler_id]["inputs"]["positive"], [capply_id, 0])
        self.assertEqual(graph[ksampler_id]["inputs"]["negative"], [capply_id, 1])

        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertTrue(res["audit_trail"]["controlnet"]["enabled"])
        self.assertEqual(res["audit_trail"]["controlnet"]["strength"], 0.35)

    def create_two_scene_document(self):
        doc = copy.deepcopy(self.document)
        page = doc["pages"][0]
        page["style_prompt"] = "monochrome manga, clean line art"
        page["scenes"] = [
            {
                "scene_id": "scene_left",
                "name": "Left Scene",
                "prompt": "courtyard, stone pavement",
                "negative_prompt": "",
                "input_mode": "cast",
                "area": {"shape_type": "rect", "x": 0.05, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 1,
                "metadata": {},
            },
            {
                "scene_id": "scene_right",
                "name": "Right Scene",
                "prompt": "indoor room, desk and window",
                "negative_prompt": "",
                "input_mode": "cast",
                "area": {"shape_type": "rect", "x": 0.55, "y": 0.10, "w": 0.40, "h": 0.80},
                "order": 2,
                "metadata": {},
            },
        ]
        page["cast"] = []
        page["character_instances"] = []
        page["guides"] = []
        return doc

    def test_case_a_two_cast_two_instances_zero_references(self):
        """Case A: Two different CAST definitions, 1 instance each, zero references."""
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Hero", identity_prompt="1boy, black hair", cast_id="cast_hero", reference_asset=None),
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=None),
        ]
        page["character_instances"] = [
            create_character_instance("cast_hero", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        classes = [node["class_type"] for node in graph.values()]
        self.assertNotIn("IPAdapterAdvanced", classes)
        self.assertFalse(res["audit_trail"]["reference"]["enabled"])

    def test_case_b_one_cast_two_instances_with_reference(self):
        """Case B: One CAST definition with Reference, 2 instances in different Scenes."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        self.add_reference_capability(asset=ref_asset)
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=ref_asset),
        ]
        page["character_instances"] = [
            create_character_instance("cast_heroine", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertEqual(res["audit_trail"]["reference"]["reference_asset"], ref_asset)

    def test_case_c_two_cast_two_instances_one_reference(self):
        """Case C: Two CAST definitions, 2 placed instances, only one CAST has a Reference."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        self.add_reference_capability(asset=ref_asset)
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Hero", identity_prompt="1boy, black hair", cast_id="cast_hero", reference_asset=None),
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=ref_asset),
        ]
        page["character_instances"] = [
            create_character_instance("cast_hero", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertEqual(res["audit_trail"]["reference"]["cast_id"], "cast_heroine")

    def test_case_d_two_cast_two_instances_same_reference_asset(self):
        """Case D: Two CAST definitions, 2 placed instances, both share the SAME reference asset."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        self.add_reference_capability(asset=ref_asset)
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Heroine Alternate", identity_prompt="1girl, silver hair, ponytail", cast_id="cast_heroine_alt", reference_asset=ref_asset),
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=ref_asset),
        ]
        page["character_instances"] = [
            create_character_instance("cast_heroine_alt", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        res = compile_scene(self.request(doc), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertEqual(res["audit_trail"]["reference"]["reference_asset"], ref_asset)

    def test_case_e_two_different_reference_assets_fail_closed(self):
        """Case E: Two different active Reference assets across instances fails closed."""
        ref_a = "tegaki_manga_references/ref_c789751db904319d.png"
        ref_b = "tegaki_manga_references/ref_other.png"
        self.add_reference_capability(asset=ref_a)
        self.add_reference_capability(asset=ref_b)
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Hero", identity_prompt="1boy, black hair", cast_id="cast_hero", reference_asset=ref_b),
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=ref_a),
        ]
        page["character_instances"] = [
            create_character_instance("cast_hero", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        self.expect_code("REFERENCE_MULTI_ASSET_UNSUPPORTED", self.request(doc))

    def test_case_f_three_placed_instances_fail_closed(self):
        """Case F: 3 or more placed instances fails closed."""
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["scenes"].append({
            "scene_id": "scene_bottom",
            "name": "Bottom Scene",
            "prompt": "garden",
            "negative_prompt": "",
            "input_mode": "cast",
            "area": {"shape_type": "rect", "x": 0.05, "y": 0.70, "w": 0.90, "h": 0.25},
            "order": 3,
            "metadata": {},
        })
        page["cast"] = [
            create_cast_entry(display_name="Hero", identity_prompt="1boy, black hair", cast_id="cast_hero", reference_asset=None),
        ]
        page["character_instances"] = [
            create_character_instance("cast_hero", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_hero", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
            create_character_instance("cast_hero", "scene_bottom", area={"shape_type": "rect", "x": 0.10, "y": 0.72, "w": 0.30, "h": 0.20}, instance_id="inst_3"),
        ]
        self.expect_code("SCENE_CAST_UNSUPPORTED", self.request(doc))

    def test_two_instances_with_guide_and_reference_combined(self):
        """Case B combined with ControlNet Guide: IP-Adapter and ControlNet active together."""
        ref_asset = "tegaki_manga_references/ref_c789751db904319d.png"
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_reference_capability(asset=ref_asset)
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.create_two_scene_document()
        page = doc["pages"][0]
        page["cast"] = [
            create_cast_entry(display_name="Heroine", identity_prompt="1girl, silver hair", cast_id="cast_heroine", reference_asset=ref_asset),
        ]
        page["character_instances"] = [
            create_character_instance("cast_heroine", "scene_left", area={"shape_type": "rect", "x": 0.10, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_1"),
            create_character_instance("cast_heroine", "scene_right", area={"shape_type": "rect", "x": 0.60, "y": 0.20, "w": 0.30, "h": 0.60}, instance_id="inst_2"),
        ]
        page["guides"].append(create_guide(
            guide_type="rough_manga",
            asset_reference=guide_asset,
            placement={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            enabled=True,
            guide_id="guide_combined",
        ))
        res = compile_scene(self.request(doc, controlnet_strength=0.4), self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        cond_builder_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        ipa_id = [k for k, v in graph.items() if v["class_type"] == "IPAdapterAdvanced"][0]
        capply_id = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        self.assertEqual(graph[ipa_id]["inputs"]["attn_mask"], [cond_builder_id, 6])
        self.assertTrue(res["audit_trail"]["reference"]["enabled"])
        self.assertTrue(res["audit_trail"]["controlnet"]["enabled"])
        self.assertEqual(res["audit_trail"]["controlnet"]["strength"], 0.4)

    def test_controlnet_custom_timing_and_strength_1_0(self):
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.guide_fixture_document(asset=guide_asset)
        req = self.request(doc, controlnet_strength=1.0, controlnet_start_percent=0.0, controlnet_end_percent=0.8)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        capply_id = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        self.assertEqual(graph[capply_id]["inputs"]["strength"], 1.0)
        self.assertEqual(graph[capply_id]["inputs"]["start_percent"], 0.0)
        self.assertEqual(graph[capply_id]["inputs"]["end_percent"], 0.8)
        self.assertEqual(res["audit_trail"]["controlnet"]["strength"], 1.0)
        self.assertEqual(res["audit_trail"]["controlnet"]["start_percent"], 0.0)
        self.assertEqual(res["audit_trail"]["controlnet"]["end_percent"], 0.8)

    def test_controlnet_strength_1_2_and_timing(self):
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.guide_fixture_document(asset=guide_asset)
        req = self.request(doc, controlnet_strength=1.2, controlnet_start_percent=0.1, controlnet_end_percent=0.9)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        capply_id = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        self.assertEqual(graph[capply_id]["inputs"]["strength"], 1.2)
        self.assertEqual(graph[capply_id]["inputs"]["start_percent"], 0.1)
        self.assertEqual(graph[capply_id]["inputs"]["end_percent"], 0.9)

    def test_controlnet_legacy_defaults_preserved(self):
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.guide_fixture_document(asset=guide_asset)
        req = self.request(doc)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        capply_id = [k for k, v in graph.items() if v["class_type"] == "ControlNetApplyAdvanced"][0]
        self.assertEqual(graph[capply_id]["inputs"]["strength"], 0.35)
        self.assertEqual(graph[capply_id]["inputs"]["start_percent"], 0.0)
        self.assertEqual(graph[capply_id]["inputs"]["end_percent"], 1.0)

    def test_controlnet_timing_validation(self):
        guide_asset = "tegaki_manga_guides/rough_guide_test.png"
        self.add_controlnet_capability(asset=guide_asset)
        doc = self.guide_fixture_document(asset=guide_asset)
        # start >= end
        self.expect_code("INVALID_PARAMETER", self.request(doc, controlnet_start_percent=0.8, controlnet_end_percent=0.8))
        self.expect_code("INVALID_PARAMETER", self.request(doc, controlnet_start_percent=0.9, controlnet_end_percent=0.8))
        # start < 0
        self.expect_code("INVALID_PARAMETER", self.request(doc, controlnet_start_percent=-0.1, controlnet_end_percent=0.8))
        # end > 1
        self.expect_code("INVALID_PARAMETER", self.request(doc, controlnet_start_percent=0.0, controlnet_end_percent=1.1))
        # strength > 2
        self.expect_code("INVALID_PARAMETER", self.request(doc, controlnet_strength=2.5))

    def test_reference_controls_defaults_and_routing(self):
        self.add_reference_capability()
        doc = self.reference_document()
        req = self.request(doc)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        ref_node = [v for v in graph.values() if v["class_type"] == "IPAdapterAdvanced"][0]
        cond_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        self.assertEqual(ref_node["inputs"]["weight"], 0.70)
        self.assertEqual(ref_node["inputs"]["start_at"], 0.0)
        self.assertEqual(ref_node["inputs"]["end_at"], 1.0)
        self.assertEqual(ref_node["inputs"]["attn_mask"], [cond_id, 6])
        self.assertEqual(res["audit_trail"]["reference"]["weight"], 0.70)
        self.assertEqual(res["audit_trail"]["reference"]["start_at"], 0.0)
        self.assertEqual(res["audit_trail"]["reference"]["end_at"], 1.0)

    def test_reference_controls_explicit_values(self):
        self.add_reference_capability()
        doc = self.reference_document()
        req = self.request(doc, reference_weight=1.25, reference_start=0.15, reference_end=0.85)
        res = compile_scene(req, self.catalog)
        self.assertTrue(res["ok"])
        graph = res["graph"]
        ref_node = [v for v in graph.values() if v["class_type"] == "IPAdapterAdvanced"][0]
        cond_id = [k for k, v in graph.items() if v["class_type"] == "TegakiMangaConditioningBuilder"][0]
        self.assertEqual(ref_node["inputs"]["weight"], 1.25)
        self.assertEqual(ref_node["inputs"]["start_at"], 0.15)
        self.assertEqual(ref_node["inputs"]["end_at"], 0.85)
        self.assertEqual(ref_node["inputs"]["attn_mask"], [cond_id, 6])
        self.assertEqual(res["audit_trail"]["reference"]["weight"], 1.25)
        self.assertEqual(res["audit_trail"]["reference"]["start_at"], 0.15)
        self.assertEqual(res["audit_trail"]["reference"]["end_at"], 0.85)

    def test_reference_controls_validation(self):
        self.add_reference_capability()
        doc = self.reference_document()
        # start >= end
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_start=0.8, reference_end=0.8))
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_start=0.9, reference_end=0.8))
        # start < 0
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_start=-0.1, reference_end=0.8))
        # end > 1
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_start=0.0, reference_end=1.1))
        # weight < 0
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_weight=-0.5))
        # weight > 2.0
        self.expect_code("INVALID_PARAMETER", self.request(doc, reference_weight=2.5))


if __name__ == "__main__":
    unittest.main()


