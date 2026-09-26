"""MANGA-ILLUSTRIOUS-LORA-PRODUCTION1: resource identity, browsing, and graph application.

Uses the real production contracts: engine_resources (root mapping + lazy listing),
basic_generation (LORA_RE / _compile_prompt / catalog), isolated_scene_plan and
isolated_scene_compile -> compile_scene (LoraLoader chain).  No ComfyUI runtime,
no /prompt, no GPU.
"""

from __future__ import annotations

import builtins
import copy
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
EMBEDDED_SITE = ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from custom_nodes_custom.tegaki_manga_nodes import engine_resources as res  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes.basic_generation import (  # noqa: E402
    GenerationContractError, build_catalog, format_lora_directive, split_lora_directives,
)
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import (  # noqa: E402
    REFERENCE_SUPPORTED_CHECKPOINT, compile_scene,
)
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_plan import create_isolated_scene_plan  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_compile import (  # noqa: E402
    IsolatedSceneCompileError, compile_isolated_scene_plan,
)

ALICE_A = "characters/series_a/alice_v3.safetensors"
ALICE_B = "characters/series_b/alice_v3.safetensors"
INK = "styles/ink.safetensors"
STYLE = "masterpiece, manga style, clean lines"
SCENE = "cat on the roof"

_MODULE_TMP = None
_MODULE_ROOT = None
_ORIG_ENV = None


def setUpModule():
    global _MODULE_TMP, _MODULE_ROOT, _ORIG_ENV
    _MODULE_TMP = tempfile.TemporaryDirectory()
    _MODULE_ROOT = make_tree(pathlib.Path(_MODULE_TMP.name))
    _ORIG_ENV = os.environ.get("TEGAKI_ILLUSTRIOUS_LORA_ROOT")
    os.environ["TEGAKI_ILLUSTRIOUS_LORA_ROOT"] = str(_MODULE_ROOT)


def tearDownModule():
    global _MODULE_TMP, _MODULE_ROOT, _ORIG_ENV
    if _ORIG_ENV is not None:
        os.environ["TEGAKI_ILLUSTRIOUS_LORA_ROOT"] = _ORIG_ENV
    else:
        os.environ.pop("TEGAKI_ILLUSTRIOUS_LORA_ROOT", None)
    if _MODULE_TMP is not None:
        _MODULE_TMP.cleanup()



def node_inputs(lora_names):
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": ([REFERENCE_SUPPORTED_CHECKPOINT], {})}},
        "LoraLoader": {"required": {
            "lora_name": (list(lora_names), {}),
            "model": ("MODEL",), "clip": ("CLIP",), "strength_model": ("FLOAT",), "strength_clip": ("FLOAT",),
        }},
        "CLIPTextEncode": {"required": {"text": ("STRING",), "clip": ("CLIP",)}},
        "EmptyLatentImage": {"required": {
            "width": ("INT", {"min": 256, "max": 2048, "step": 8}),
            "height": ("INT", {"min": 256, "max": 2048, "step": 8}),
            "batch_size": ("INT", {"min": 1, "max": 4096}),
        }},
        "KSampler": {"required": {
            "seed": ("INT", {"min": 0, "max": 4294967295}), "steps": ("INT", {"min": 1, "max": 100}),
            "cfg": ("FLOAT", {"min": 0.0, "max": 30.0}), "sampler_name": (["euler"], {}),
            "scheduler": (["normal"], {}), "model": ("MODEL",), "positive": ("CONDITIONING",),
            "negative": ("CONDITIONING",), "latent_image": ("LATENT",), "denoise": ("FLOAT",),
        }},
        "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
        "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
    }


def make_catalog(lora_names=(ALICE_A, ALICE_B, INK)):
    catalog = build_catalog([REFERENCE_SUPPORTED_CHECKPOINT], list(lora_names), node_inputs(lora_names),
                            lambda _kind, _name: True)
    catalog["scene_generation"] = {
        "available": True,
        "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
        "reference": {"available": False},
    }
    return catalog


def make_document(scene_prompt=SCENE, style_prompt=STYLE):
    area = {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40}
    return {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT", "schema_version": "1.0.0", "document_id": "doc_lora",
        "pages": [{
            "page_id": "page_1", "width_px": 1024, "height_px": 1536,
            "style_prompt": style_prompt, "style_negative_prompt": "blurry",
            "scenes": [
                {"scene_id": "scene_1", "order": 1, "name": "Panel 1", "input_mode": "simple",
                 "prompt": scene_prompt, "negative_prompt": "human", "area": area},
                {"scene_id": "scene_2", "order": 2, "name": "Panel 2", "input_mode": "simple",
                 "prompt": "unrelated street", "negative_prompt": "",
                 "area": {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.90, "h": 0.45}},
            ],
            "cast": [], "character_instances": [], "guides": [],
        }],
    }


PARAMS = {"checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT, "sampler_id": "euler", "scheduler_id": "normal",
          "steps": 20, "cfg": 7.0, "seed_requested": "42", "mask_feather": 16, "panel_strength": 1.0}


def compile_isolated(scene_prompt=SCENE, style_prompt=STYLE, catalog=None):
    plan = create_isolated_scene_plan(make_document(scene_prompt, style_prompt), scene_id="scene_1",
                                      local_dimensions=(512, 768))
    return compile_isolated_scene_plan(plan, dict(PARAMS), catalog or make_catalog())


def lora_chain(graph):
    """Follow MODEL from KSampler back to the checkpoint; return LoraLoader nodes in apply order."""
    sampler = next(n for n in graph.values() if n["class_type"] == "KSampler")
    chain, ref = [], sampler["inputs"]["model"]
    while graph[ref[0]]["class_type"] == "LoraLoader":
        node = graph[ref[0]]
        chain.append(node)
        ref = node["inputs"]["model"]
    assert graph[ref[0]]["class_type"] == "CheckpointLoaderSimple"
    return list(reversed(chain))


def make_tree(base: pathlib.Path) -> pathlib.Path:
    root = base / "Lora"
    for rel in (ALICE_A, ALICE_B, INK, "root_level.safetensors", "characters/readme.txt",
                "characters/series_a/deep/deeper/hidden.safetensors"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"NOT-A-REAL-MODEL")
    return root


class ResourceIdentityTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_tree(pathlib.Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_canonical_identity_is_root_relative_path(self):
        self.assertEqual(res.canonical_id_for_path(str(self.root), str(self.root / ALICE_A)), ALICE_A)
        self.assertEqual(res.normalize_relative_id("characters\\series_a\\alice_v3.safetensors"), ALICE_A)
        self.assertEqual(format_lora_directive(ALICE_A), f"<lora:{ALICE_A}:1.0>")

    def test_a_root_mapping_is_engine_scoped_and_must_be_comfy_registered(self):
        env = {"TEGAKI_ILLUSTRIOUS_LORA_ROOT": str(self.root)}
        got = res.resolve_resource_root("illustrious", "lora", [str(self.root)], environ=env)
        self.assertEqual(os.path.realpath(got), os.path.realpath(str(self.root)))
        self.assertEqual(res.ENGINE_RESOURCE_ROOTS["illustrious"]["lora"]["comfy_folder"], "loras")
        with self.assertRaises(res.ResourceContractError) as unregistered:
            res.resolve_resource_root("illustrious", "lora", ["/somewhere/else"], environ=env)
        self.assertEqual(unregistered.exception.code, "RESOURCE_ROOT_UNREGISTERED")
        with self.assertRaises(res.ResourceContractError) as unsupported:
            res.resolve_resource_root("minimaxH3", "lora", [str(self.root)], environ=env)
        self.assertEqual(unsupported.exception.code, "RESOURCE_UNSUPPORTED")
        payload = res.browse_lora_payload("illustrious", "", [str(self.root)], environ=env)
        self.assertNotIn(str(self.root), json.dumps(payload))  # physical root never leaves the backend

    def test_b_nested_folders_are_browsed_one_level_at_a_time(self):
        def no_walk(*_a, **_k):
            raise AssertionError("browse must not recurse")

        def no_open(*_a, **_k):
            raise AssertionError("browse must not open files")

        with mock.patch.object(os, "walk", no_walk), mock.patch.object(builtins, "open", no_open):
            top = res.list_lora_directory(str(self.root), "")
            chars = res.list_lora_directory(str(self.root), "characters")
            series_a = res.list_lora_directory(str(self.root), "characters/series_a")
        self.assertEqual([f["id"] for f in top["folders"]], ["characters", "styles"])
        self.assertEqual([l["id"] for l in top["loras"]], ["root_level.safetensors"])
        self.assertEqual([f["id"] for f in chars["folders"]], ["characters/series_a", "characters/series_b"])
        self.assertEqual(chars["loras"], [])  # readme.txt ignored; nothing flattened upward
        self.assertEqual([l["id"] for l in series_a["loras"]], [ALICE_A])
        self.assertEqual([f["id"] for f in series_a["folders"]], ["characters/series_a/deep"])
        self.assertEqual(series_a["parent"], "characters")

    def test_c_duplicate_basenames_do_not_collide(self):
        a = res.list_lora_directory(str(self.root), "characters/series_a")["loras"][0]
        b = res.list_lora_directory(str(self.root), "characters/series_b")["loras"][0]
        self.assertEqual(a["name"], b["name"])
        self.assertNotEqual(a["id"], b["id"])
        graph_a = lora_chain(compile_isolated(f"{SCENE}, <lora:{ALICE_A}:1.0>")["graph"])
        graph_b = lora_chain(compile_isolated(f"{SCENE}, <lora:{ALICE_B}:1.0>")["graph"])
        self.assertEqual([n["inputs"]["lora_name"] for n in graph_a], [ALICE_A])
        self.assertEqual([n["inputs"]["lora_name"] for n in graph_b], [ALICE_B])
        with self.assertRaises(IsolatedSceneCompileError) as ambiguous:
            compile_isolated(f"{SCENE}, <lora:alice_v3.safetensors:1.0>")
        self.assertEqual(ambiguous.exception.code, "LORA_AMBIGUOUS")

    def test_c_shadowed_entry_is_marked_unavailable(self):
        other = pathlib.Path(self._tmp.name) / "OtherRoot" / ALICE_A
        listing = res.list_lora_directory(str(self.root), "characters/series_a",
                                          comfy_full_path=lambda _id: str(other))
        self.assertFalse(listing["loras"][0]["available"])
        listing = res.list_lora_directory(str(self.root), "characters/series_a",
                                          comfy_full_path=lambda item: str(self.root / item))
        self.assertTrue(listing["loras"][0]["available"])

    def test_d_missing_lora_and_missing_folder_fail_closed(self):
        with self.assertRaises(IsolatedSceneCompileError) as missing:
            compile_isolated(f"{SCENE}, <lora:characters/series_c/missing.safetensors:1.0>")
        self.assertEqual(missing.exception.code, "LORA_UNAVAILABLE")
        with self.assertRaises(res.ResourceContractError) as folder:
            res.list_lora_directory(str(self.root), "characters/series_c")
        self.assertEqual(folder.exception.code, "RESOURCE_PATH_NOT_FOUND")
        with self.assertRaises(res.ResourceContractError) as root:
            res.resolve_resource_root("illustrious", "lora", [], environ={
                "TEGAKI_ILLUSTRIOUS_LORA_ROOT": str(self.root / "nope")})
        self.assertEqual(root.exception.code, "RESOURCE_ROOT_UNAVAILABLE")

    def test_e_traversal_and_out_of_root_identity_fail_closed(self):
        for bad in ("..", "../x.safetensors", "characters/../../x", "/etc/passwd", "C:/Windows/x.safetensors",
                    "characters//series_a", "\\\\server\\share\\x"):
            with self.subTest(bad=bad), self.assertRaises(res.ResourceContractError) as ctx:
                res.list_lora_directory(str(self.root), bad)
            self.assertEqual(ctx.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")
        outside = pathlib.Path(self._tmp.name) / "outside"
        outside.mkdir()
        (outside / "evil.safetensors").write_bytes(b"x")
        try:
            os.symlink(outside, self.root / "escape", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        self.assertNotIn("escape", [f["id"] for f in res.list_lora_directory(str(self.root), "")["folders"]])
        with self.assertRaises(res.ResourceContractError) as link:
            res.list_lora_directory(str(self.root), "escape")
        self.assertEqual(link.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")
        with self.assertRaises(IsolatedSceneCompileError) as token:
            compile_isolated(f"{SCENE}, <lora:../outside/evil.safetensors:1.0>")
        self.assertEqual(token.exception.code, "INVALID_CATALOG_ID")


class GraphContractTests(unittest.TestCase):
    def test_f_one_token_parses_resolves_and_feeds_model_and_clip(self):
        result = compile_isolated(f"{SCENE}, <lora:{INK}:0.8>")
        graph = result["graph"]
        chain = lora_chain(graph)
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0]["inputs"]["lora_name"], INK)
        lora_id = next(k for k, v in graph.items() if v is chain[0])
        builder = next(n for n in graph.values() if n["class_type"] == "TegakiMangaConditioningBuilder")
        self.assertEqual(builder["inputs"]["clip"], [lora_id, 1])  # prompt encoding uses the LoRA CLIP

    def test_f_windows_style_catalog_ids_resolve_from_canonical_slash_token(self):
        win = "characters\\series_a\\alice_v3.safetensors"
        chain = lora_chain(compile_isolated(f"{SCENE}, <lora:{ALICE_A}:1.0>", catalog=make_catalog((win, INK)))["graph"])
        self.assertEqual(chain[0]["inputs"]["lora_name"], win)  # the exact ComfyUI LoraLoader choice

    def test_g_multiple_loras_preserve_deterministic_order(self):
        scene = f"{SCENE}, <lora:{ALICE_B}:0.6>, sunset, <lora:{ALICE_A}:0.9>"
        style = f"{STYLE}, <lora:{INK}:0.5>"
        first = compile_isolated(scene, style)
        second = compile_isolated(scene, style)
        names = [n["inputs"]["lora_name"] for n in lora_chain(first["graph"])]
        self.assertEqual(names, [INK, ALICE_B, ALICE_A])  # page style first, then Scene prompt order
        self.assertEqual(first["graph_digest"], second["graph_digest"])
        with self.assertRaises(IsolatedSceneCompileError) as dup:
            compile_isolated(f"{SCENE}, <lora:{INK}:1.0>", style)
        self.assertEqual(dup.exception.code, "LORA_DUPLICATE")

    def test_h_strength_propagates_to_both_loader_strengths(self):
        chain = lora_chain(compile_isolated(f"{SCENE}, <lora:{ALICE_A}:0.85>, <lora:{INK}:-1.25>")["graph"])
        self.assertEqual([(n["inputs"]["strength_model"], n["inputs"]["strength_clip"]) for n in chain],
                         [(0.85, 0.85), (-1.25, -1.25)])
        self.assertEqual(format_lora_directive(INK, 0.85), f"<lora:{INK}:0.85>")
        self.assertEqual(format_lora_directive(INK, 1), f"<lora:{INK}:1.0>")
        with self.assertRaises(GenerationContractError):
            format_lora_directive(INK, 5)

    def test_i_directive_never_reaches_ordinary_prompt_encoding(self):
        result = compile_isolated(f"{SCENE}, <lora:{ALICE_A}:0.7>, night")
        graph_text = json.dumps(result["graph"], ensure_ascii=False)
        self.assertNotIn("<lora", graph_text)
        self.assertNotIn("<lora", json.dumps(result["page_compile_plan"], ensure_ascii=False))
        page = result["audit_trail"]["scenes"][0]
        self.assertEqual(page["clean_positive"], f"{SCENE}, night")
        self.assertEqual(result["audit_trail"]["global"]["clean_positive"], STYLE)

    def test_j_split_preserves_unrelated_prompt_content(self):
        untouched = "1girl,  smile ,\n{a|b}, __hair__"
        self.assertEqual(split_lora_directives(untouched), (untouched, []))
        self.assertEqual(split_lora_directives(f"1girl, <lora:{INK}:1.0>, smile"),
                         ("1girl, smile", [f"<lora:{INK}:1.0>"]))
        self.assertEqual(split_lora_directives(f"<lora:{INK}:1.0>, 1girl, smile, <lora:{ALICE_A}:0.5>"),
                         ("1girl, smile", [f"<lora:{INK}:1.0>", f"<lora:{ALICE_A}:0.5>"]))

    def test_k_no_lora_compile_is_unchanged(self):
        result = compile_isolated()
        self.assertEqual(lora_chain(result["graph"]), [])
        self.assertEqual(sorted(n["class_type"] for n in result["graph"].values()), sorted([
            "CheckpointLoaderSimple", "TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder",
            "EmptyLatentImage", "KSampler", "VAEDecode", "SaveImage"]))
        scene = result["audit_trail"]["scenes"][0]
        self.assertEqual((scene["raw_positive"], scene["clean_positive"]), (SCENE, SCENE))
        self.assertEqual(result["audit_trail"]["global"]["raw_positive"], STYLE)

    def test_k_full_page_scene_lora_guard_is_unchanged(self):
        doc = make_document(f"{SCENE}, <lora:{INK}:1.0>")
        catalog = make_catalog()
        request = {"request_id": "full_page", "mode": "scene", "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
                   "authoring_document": copy.deepcopy(doc), "page_index": 0, "sampler_id": "euler",
                   "scheduler_id": "normal", "steps": 20, "cfg": 7.0, "seed_requested": "42",
                   "capability_revision": catalog["revision"]}
        with self.assertRaises(GenerationContractError) as ctx:
            compile_scene(request, catalog)
        self.assertEqual(ctx.exception.code, "SCENE_LORA_UNSUPPORTED")


class IllustriousLoraRootBoundaryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._tmp.name)
        self.root = make_tree(self.base)
        self.outside_root = self.base / "OutsideLora"
        self.outside_root.mkdir(parents=True, exist_ok=True)
        (self.outside_root / "outside_registered.safetensors").write_bytes(b"OUTSIDE")
        (self.outside_root / "unique_bare_outside.safetensors").write_bytes(b"OUTSIDE")
        self._orig_env = os.environ.get("TEGAKI_ILLUSTRIOUS_LORA_ROOT")
        os.environ["TEGAKI_ILLUSTRIOUS_LORA_ROOT"] = str(self.root)

        # Catalog simulating ComfyUI merged get_filename_list("loras") across multiple folders
        self.all_lora_names = (
            ALICE_A,
            ALICE_B,
            INK,
            "outside_registered.safetensors",
            "unique_bare_outside.safetensors",
        )
        self.catalog = make_catalog(self.all_lora_names)

    def tearDown(self):
        if self._orig_env is not None:
            os.environ["TEGAKI_ILLUSTRIOUS_LORA_ROOT"] = self._orig_env
        else:
            os.environ.pop("TEGAKI_ILLUSTRIOUS_LORA_ROOT", None)
        self._tmp.cleanup()

    def test_section8_a_nested_canonical_id_inside_illustrious_root_resolves(self):
        # A. nested canonical ID inside Illustrious root resolves
        result = compile_isolated(f"{SCENE}, <lora:{ALICE_A}:1.0>", catalog=self.catalog)
        chain = lora_chain(result["graph"])
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0]["inputs"]["lora_name"], ALICE_A)

    def test_section8_b_duplicate_basename_inside_root_remains_distinct_by_canonical_id(self):
        # B. duplicate basename inside Illustrious root remains unambiguous by canonical ID
        res_a = compile_isolated(f"{SCENE}, <lora:{ALICE_A}:1.0>", catalog=self.catalog)
        res_b = compile_isolated(f"{SCENE}, <lora:{ALICE_B}:1.0>", catalog=self.catalog)
        self.assertEqual(lora_chain(res_a["graph"])[0]["inputs"]["lora_name"], ALICE_A)
        self.assertEqual(lora_chain(res_b["graph"])[0]["inputs"]["lora_name"], ALICE_B)
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated(f"{SCENE}, <lora:alice_v3.safetensors:1.0>", catalog=self.catalog)
        self.assertEqual(ctx.exception.code, "LORA_AMBIGUOUS")

    def test_section8_c_traversal_fails_closed(self):
        # C. traversal fails closed
        for bad in ("../outside.safetensors", "characters/../../escape.safetensors"):
            with self.subTest(bad=bad), self.assertRaises(IsolatedSceneCompileError) as ctx:
                compile_isolated(f"{SCENE}, <lora:{bad}:1.0>", catalog=self.catalog)
            self.assertIn(ctx.exception.code, ("INVALID_CATALOG_ID", "RESOURCE_PATH_OUTSIDE_ROOT"))

    def test_section8_d_absolute_path_fails_closed(self):
        # D. absolute path fails closed
        for bad in ("C:/evil.safetensors", "C:\\evil.safetensors", "/etc/passwd", "\\\\server\\share\\x.safetensors"):
            with self.subTest(bad=bad), self.assertRaises(IsolatedSceneCompileError) as ctx:
                compile_isolated(f"{SCENE}, <lora:{bad}:1.0>", catalog=self.catalog)
            self.assertIn(ctx.exception.code, ("INVALID_CATALOG_ID", "RESOURCE_PATH_OUTSIDE_ROOT", "SCENE_LORA_UNSUPPORTED", "UNSUPPORTED_PROMPT_TAG"))

    def test_section8_e_registered_lora_outside_illustrious_root_rejected(self):
        # E. a ComfyUI-registered LoRA OUTSIDE D:\Models\Lora is rejected for engine=illustrious
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated(f"{SCENE}, <lora:outside_registered.safetensors:1.0>", catalog=self.catalog)
        self.assertEqual(ctx.exception.code, "LORA_UNAVAILABLE")

        # Also verify when comfy_full_path is explicitly used (simulating live ComfyUI resolver)
        def comfy_full_path(item):
            if item == "outside_registered.safetensors":
                return str(self.outside_root / item)
            return str(self.root / item)

        catalog_with_resolver = make_catalog(self.all_lora_names)
        catalog_with_resolver["comfy_full_path"] = comfy_full_path
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated(f"{SCENE}, <lora:outside_registered.safetensors:1.0>", catalog=catalog_with_resolver)
        self.assertEqual(ctx.exception.code, "LORA_UNAVAILABLE")

    def test_section8_f_unique_bare_basename_outside_root_does_not_bypass_boundary(self):
        # F. unique bare basename outside the Illustrious root does NOT bypass the boundary
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated(f"{SCENE}, <lora:unique_bare_outside:1.0>", catalog=self.catalog)
        self.assertEqual(ctx.exception.code, "LORA_UNAVAILABLE")

        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            compile_isolated(f"{SCENE}, <lora:unique_bare_outside.safetensors:1.0>", catalog=self.catalog)
        self.assertEqual(ctx.exception.code, "LORA_UNAVAILABLE")

    def test_section8_g_valid_in_root_lora_produces_normal_comfy_lora_loader_contract(self):
        # G. valid in-root LoRA still produces the normal ComfyUI LoraLoader contract
        result = compile_isolated(f"{SCENE}, <lora:{INK}:0.75>", catalog=self.catalog)
        chain = lora_chain(result["graph"])
        self.assertEqual(len(chain), 1)
        node = chain[0]
        self.assertEqual(node["class_type"], "LoraLoader")
        self.assertEqual(node["inputs"]["lora_name"], INK)
        self.assertEqual(node["inputs"]["strength_model"], 0.75)
        self.assertEqual(node["inputs"]["strength_clip"], 0.75)

    def test_section8_h_no_lora_compilation_remains_unchanged(self):
        # H. no-LoRA compilation remains unchanged
        result = compile_isolated(SCENE, catalog=self.catalog)
        self.assertEqual(lora_chain(result["graph"]), [])
        self.assertEqual(result["audit_trail"]["scenes"][0]["clean_positive"], SCENE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
