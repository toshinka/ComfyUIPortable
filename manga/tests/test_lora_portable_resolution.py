"""MANGA-LORA-PORTABLE-COMPAT-DIAGNOSTICS1: portable aliases, root-safe staged resolution,
batch diagnostics, and diagnostic chain == compiler LoraLoader order.

Real contracts: engine_resources (trusted index / resolver / diagnostics), basic_generation
(_compile_prompt, dynamic-prompt wildcard expansion), isolated_scene_compile -> compile_scene.
No ComfyUI runtime, no /prompt, no GPU.
"""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from custom_nodes_custom.tegaki_manga_nodes import engine_resources as res  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes.basic_generation import (  # noqa: E402
    GenerationContractError, build_catalog, compile_basic,
)
from custom_nodes_custom.tegaki_manga_nodes.scene_generation import REFERENCE_SUPPORTED_CHECKPOINT  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_plan import create_isolated_scene_plan  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes.isolated_scene_compile import (  # noqa: E402
    IsolatedSceneCompileError, compile_isolated_scene_plan,
)

# Legacy-style assets: unique aliases living in unrelated nested folders.
FOO = "!!!BASIC/0/foo.safetensors"
BAR = "styles/painterly/bar.safetensors"
BAZ = "!!Stabilizer/deep/er/baz.safetensors"
DUP_A = "characters/A/dup.safetensors"
DUP_B = "styles/dup.safetensors"
PONY = "pony_trained/inueShinsukeStylePonyV1S.safetensors"  # cross-family on purpose
PT = "legacy/oldstyle.pt"
OUTSIDE_ONLY = "easyreforge_only.safetensors"
IN_ROOT = (FOO, BAR, BAZ, DUP_A, DUP_B, PONY, PT)


def node_inputs(names):
    return {
        "TegakiMinimumHandSceneEditor": {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": ([REFERENCE_SUPPORTED_CHECKPOINT], {})}},
        "LoraLoader": {"required": {"lora_name": (list(names), {}), "model": ("MODEL",), "clip": ("CLIP",),
                                    "strength_model": ("FLOAT",), "strength_clip": ("FLOAT",)}},
        "CLIPTextEncode": {"required": {"text": ("STRING",), "clip": ("CLIP",)}},
        "EmptyLatentImage": {"required": {"width": ("INT", {"min": 256, "max": 2048, "step": 8}),
                                          "height": ("INT", {"min": 256, "max": 2048, "step": 8}),
                                          "batch_size": ("INT", {"min": 1, "max": 4096})}},
        "KSampler": {"required": {"seed": ("INT", {"min": 0, "max": 4294967295}), "steps": ("INT", {"min": 1, "max": 100}),
                                  "cfg": ("FLOAT", {"min": 0.0, "max": 30.0}), "sampler_name": (["euler"], {}),
                                  "scheduler": (["normal"], {}), "model": ("MODEL",), "positive": ("CONDITIONING",),
                                  "negative": ("CONDITIONING",), "latent_image": ("LATENT",), "denoise": ("FLOAT",)}},
        "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
        "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
    }


class PortableLoraTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.root = base / "Lora"
        self.other = base / "EasyReforgeLora"
        for rel in IN_ROOT:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(b"MODEL")
        self.other.mkdir()
        (self.other / OUTSIDE_ONLY).write_bytes(b"MODEL")
        self.wildcards = base / "wildcards"
        self.wildcards.mkdir()
        (self.wildcards / "my_style_mix.txt").write_text("<lora:foo:0.2>, <lora:bar:0.1>, <lora:baz:0.15>\n", encoding="utf-8")
        self._env = {k: os.environ.get(k) for k in ("TEGAKI_ILLUSTRIOUS_LORA_ROOT", "TEGAKI_MANGA_WILDCARDS_DIR")}
        os.environ["TEGAKI_ILLUSTRIOUS_LORA_ROOT"] = str(self.root)
        os.environ["TEGAKI_MANGA_WILDCARDS_DIR"] = str(self.wildcards)
        # ComfyUI's merged catalog: trusted root + another registered root.
        self.names = list(IN_ROOT) + [OUTSIDE_ONLY]
        self.catalog = build_catalog([REFERENCE_SUPPORTED_CHECKPOINT], self.names, node_inputs(self.names),
                                     lambda _kind, _name: True)
        self.catalog["scene_generation"] = {"available": True, "reference": {"available": False},
                                            "required_nodes": ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"]}
        self.index = res.build_trusted_lora_index(self.catalog["loras"], str(self.root))

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def resolve(self, name):
        return self.index.resolve(name).id

    def fails(self, name, code):
        with self.assertRaises(res.ResourceContractError) as ctx:
            self.index.resolve(name)
        self.assertEqual(ctx.exception.code, code)
        return ctx.exception

    # --- A..J resolution contract --------------------------------------------------
    def test_a_unique_basename_with_extension(self):
        self.assertEqual(self.resolve("foo.safetensors"), FOO)

    def test_b_unique_basename_without_extension(self):
        self.assertEqual(self.resolve("foo"), FOO)
        self.assertEqual(self.resolve("inueShinsukeStylePonyV1S"), PONY)  # no family filtering

    def test_c_nested_canonical_path(self):
        self.assertEqual(self.resolve(BAZ), BAZ)
        self.assertEqual(self.resolve(BAZ.replace("/", "\\")), BAZ)

    def test_d_canonical_path_without_extension(self):
        self.assertEqual(self.resolve("!!Stabilizer/deep/er/baz"), BAZ)
        self.assertEqual(self.resolve("legacy/oldstyle"), PT)

    def test_e_duplicate_basename_is_ambiguous_with_candidates(self):
        for name in ("dup", "dup.safetensors"):
            exc = self.fails(name, "LORA_AMBIGUOUS")
            self.assertEqual(exc.candidates, [DUP_A, DUP_B])

    def test_f_explicit_canonical_id_disambiguates(self):
        self.assertEqual(self.resolve("characters/A/dup"), DUP_A)
        self.assertEqual(self.resolve("styles/dup"), DUP_B)
        self.assertEqual(self.index.token_for(DUP_A), "characters/A/dup")
        self.assertEqual(self.index.token_for(FOO), "foo")
        self.assertEqual(self.index.token_for(PT), "oldstyle.pt")  # stem alias is .safetensors-only

    def test_g_out_of_root_unique_basename_is_rejected(self):
        self.fails("easyreforge_only", "LORA_UNAVAILABLE")
        self.assertEqual(self.index.outside_matches("easyreforge_only"), [OUTSIDE_ONLY])
        with self.assertRaises(IsolatedSceneCompileError) as ctx:
            self.compile_isolated("cat, <lora:easyreforge_only:1.0>")
        self.assertEqual(ctx.exception.code, "LORA_UNAVAILABLE")

    def test_h_missing_is_unavailable(self):
        self.fails("missing_style", "LORA_UNAVAILABLE")
        self.fails("oldstyle", "LORA_UNAVAILABLE")  # '.pt' needs its extension or folder

    def test_i_traversal_rejected(self):
        for bad in ("../foo", "C:/foo", "/foo", "!!!BASIC/../../x"):
            with self.subTest(bad=bad):
                self.fails(bad, "RESOURCE_PATH_OUTSIDE_ROOT")

    def test_j_stage_order_is_deterministic(self):
        (self.root / "foo.safetensors").write_bytes(b"MODEL")  # a root-level foo beside !!!BASIC/0/foo
        names = self.names + ["foo.safetensors"]
        index = res.build_trusted_lora_index(names, str(self.root))
        self.assertEqual(index.resolve("foo").id, "foo.safetensors")           # stage 2 beats stage 4
        self.assertEqual(index.resolve("foo.safetensors").id, "foo.safetensors")  # stage 1 beats stage 3
        self.assertEqual([index.resolve("foo").id for _ in range(5)], ["foo.safetensors"] * 5)

    # --- legacy prompt, chain order, wildcard ------------------------------------
    def compile_isolated(self, scene_prompt, style_prompt="masterpiece"):
        area = {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.4}
        doc = {"schema_id": "TEGAKI_AUTHORING_DOCUMENT", "schema_version": "1.0.0", "document_id": "d",
               "pages": [{"page_id": "p", "width_px": 1024, "height_px": 1536, "style_prompt": style_prompt,
                          "style_negative_prompt": "blurry", "cast": [], "character_instances": [], "guides": [],
                          "scenes": [{"scene_id": "s1", "order": 1, "name": "S", "input_mode": "simple",
                                      "prompt": scene_prompt, "negative_prompt": "", "area": area}]}]}
        plan = create_isolated_scene_plan(doc, scene_id="s1", local_dimensions=(512, 768))
        return compile_isolated_scene_plan(plan, {"checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT, "sampler_id": "euler",
                                                  "scheduler_id": "normal", "steps": 20, "cfg": 7.0,
                                                  "seed_requested": "42"}, self.catalog)

    @staticmethod
    def loader_order(graph):
        sampler = next(n for n in graph.values() if n["class_type"] == "KSampler")
        chain, ref = [], sampler["inputs"]["model"]
        while graph[ref[0]]["class_type"] == "LoraLoader":
            chain.append(graph[ref[0]]["inputs"])
            ref = graph[ref[0]]["inputs"]["model"]
        return list(reversed(chain))

    def test_legacy_prompt_works_without_folder_names(self):
        result = self.compile_isolated("1girl, <lora:foo:0.2>, <lora:bar:0.1>, <lora:baz:0.15>")
        order = self.loader_order(result["graph"])
        self.assertEqual([(n["lora_name"], n["strength_model"]) for n in order], [(FOO, 0.2), (BAR, 0.1), (BAZ, 0.15)])
        self.assertTrue(all(n["strength_model"] == n["strength_clip"] for n in order))

    def test_diagnostic_chain_matches_compiler_order(self):
        style = "masterpiece, <lora:baz:0.15>"
        scene = "1girl, <lora:foo:0.2>, <lora:bar:0.1>"
        order = [n["lora_name"] for n in self.loader_order(self.compile_isolated(scene, style)["graph"])]
        diag = res.diagnose_lora_sources([
            {"source": "page_positive", "text": style}, {"source": "scene_positive", "text": scene},
            {"source": "page_negative", "text": "blurry"}, {"source": "scene_negative", "text": "", "lora_allowed": False},
        ], self.index)
        self.assertEqual([link["resolved_id"] for link in diag["chain"]], order)
        self.assertEqual(order, [BAZ, FOO, BAR])  # page first, then Scene; not alphabetical
        self.assertEqual(diag["problems"], 0)

    def test_mixed_prompt_reports_every_problem_individually(self):
        text = ("<lora:foo:0.2>, <lora:missing_style:0.3>, <lora:dup:0.5>, <lora:bar>, "
                "<lora:baz:9>, <lora:easyreforge_only:1>, <lora:../x:1>, <lora:foo:0.4>, <lora:unclosed:0.1")
        diag = res.validate_lora_request("illustrious", {"sources": [{"source": "page_positive", "text": text}]}, self.index)
        got = [(e.get("name") or e["raw"], e["status"]) for e in diag["entries"]]
        self.assertEqual(got, [
            ("foo", "RESOLVED"), ("missing_style", "LORA_UNAVAILABLE"), ("dup", "LORA_AMBIGUOUS"),
            ("<lora:bar>", "INVALID_LORA_SYNTAX"), ("baz", "INVALID_STRENGTH"),
            ("easyreforge_only", "OUTSIDE_RESOURCE_ROOT"), ("../x", "OUTSIDE_RESOURCE_ROOT"),
            ("foo", "LORA_DUPLICATE"), ("<lora:unclosed:0.1", "INVALID_LORA_SYNTAX"),
        ])
        self.assertEqual(diag["entries"][2]["candidates"], [DUP_A, DUP_B])
        self.assertEqual(diag["entries"][0]["resolved_id"], FOO)
        self.assertEqual(diag["problems"], 8)
        self.assertNotIn(str(self.root), repr(diag))
        self.assertNotIn(str(self.other), repr(diag))
        # compiler_code agrees with what generation would raise for the same directive
        with self.assertRaises(GenerationContractError) as ctx:
            self.compile_basic("<lora:dup:0.5>")
        self.assertEqual(ctx.exception.code, diag["entries"][2]["compiler_code"])

    def compile_basic(self, positive):
        return compile_basic({"request_id": "r1", "mode": "txt2img", "checkpoint_id": REFERENCE_SUPPORTED_CHECKPOINT,
                              "positive_raw": positive, "negative_raw": "", "sampler_id": "euler",
                              "scheduler_id": "normal", "steps": 20, "cfg": 7.0, "width": 1024, "height": 1024,
                              "seed_requested": "42", "capability_revision": self.catalog["revision"]}, self.catalog)

    def test_wildcard_emitting_portable_aliases_reaches_trusted_resolver(self):
        compiled = self.compile_basic("1girl, __my_style_mix__")
        self.assertEqual(compiled["positive_expanded"], "1girl, <lora:foo:0.2>, <lora:bar:0.1>, <lora:baz:0.15>")
        self.assertEqual([(i["id"], i["weight_model"]) for i in compiled["resolved_loras"]],
                         [(FOO, 0.2), (BAR, 0.1), (BAZ, 0.15)])
        # same through the isolated Scene path when the wildcard is in the page (Global) prompt
        order = self.loader_order(self.compile_isolated("1girl", "masterpiece, __my_style_mix__")["graph"])
        self.assertEqual([n["lora_name"] for n in order], [FOO, BAR, BAZ])

    def test_index_and_browse_payloads_expose_relative_ids_only(self):
        payload = res.lora_index_payload("illustrious", self.index)
        by_id = {e["id"]: e for e in payload["entries"]}
        self.assertNotIn(OUTSIDE_ONLY, by_id)
        self.assertEqual(by_id[FOO]["token"], "foo")
        self.assertEqual(by_id[DUP_B]["token"], "styles/dup")
        listing = res.browse_lora_payload("illustrious", "characters/A", [str(self.root)],
                                          environ={"TEGAKI_ILLUSTRIOUS_LORA_ROOT": str(self.root)},
                                          token_for=self.index.token_for)
        self.assertEqual(listing["loras"][0]["token"], "characters/A/dup")
        self.assertNotIn(str(self.root), repr(payload) + repr(listing))



# MANGA-WILDCARD-AUTOCOMPLETE-RUNTIME-CLOSE1: live catalog names (Windows separators) whose file
# stem ends with a space before '.safetensors'.  The canonical ID is valid; only the shortened
# stem alias is not a valid directive name.  token_for must skip that form instead of failing the
# whole index / browse payload with RESOURCE_PATH_OUTSIDE_ROOT.
SPACED_RAW = ("!!!Cha\\Cha0\u2606\\SSSS\u30fb\u30ad\u30e5\u30a2\\morialuluka_v1.1_IL .safetensors",
              "!!!kawaii\\0\\Onono_Imoko .safetensors")


class SpacedStemIndexTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.root = base / "Lora"
        self.other = base / "Other"
        self.canon = [raw.replace("\\", "/") for raw in SPACED_RAW]
        for rel in self.canon + [FOO, DUP_A, DUP_B]:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(b"MODEL")
        self.other.mkdir()
        (self.other / "Onono_Imoko .safetensors").write_bytes(b"MODEL")
        catalog = list(SPACED_RAW) + [FOO, DUP_A, DUP_B, "outside/Onono_Imoko .safetensors", "../escape .safetensors"]
        self.index = res.build_trusted_lora_index(catalog, str(self.root))
        self.env = {"TEGAKI_ILLUSTRIOUS_LORA_ROOT": str(self.root)}

    def tearDown(self):
        self._tmp.cleanup()

    def test_index_payload_succeeds_and_keeps_spaced_loras(self):
        payload = res.lora_index_payload("illustrious", self.index)
        by_id = {e["id"]: e for e in payload["entries"]}
        self.assertEqual(sorted(by_id), sorted(self.canon + [FOO, DUP_A, DUP_B]))
        self.assertEqual(by_id[self.canon[0]]["token"], "morialuluka_v1.1_IL .safetensors")
        self.assertEqual(by_id[self.canon[1]]["token"], "Onono_Imoko .safetensors")
        for cid in self.canon:
            self.assertEqual(self.index.resolve(by_id[cid]["token"]).id, cid, "token resolves back to the same LoRA")
        # unchanged: portable alias and duplicate-basename behaviour
        self.assertEqual(by_id[FOO]["token"], "foo")
        self.assertEqual(by_id[DUP_B]["token"], "styles/dup")
        self.assertNotIn(str(self.root), repr(payload))

    def test_browse_folder_with_spaced_lora_succeeds(self):
        listing = res.browse_lora_payload("illustrious", "!!!kawaii/0", [str(self.root)], environ=self.env,
                                          token_for=self.index.token_for)
        self.assertEqual([(l["id"], l["token"]) for l in listing["loras"]],
                         [(self.canon[1], "Onono_Imoko .safetensors")])

    def test_trust_boundary_unchanged(self):
        self.assertEqual(sorted(self.index.outside_ids), ["outside/Onono_Imoko .safetensors"])
        with self.assertRaises(res.ResourceContractError) as stem:
            self.index.resolve("Onono_Imoko ")
        self.assertEqual(stem.exception.code, "INVALID_CATALOG_ID")
        for bad in ("../escape .safetensors", "/abs/x.safetensors", "!!!kawaii/../../x.safetensors"):
            with self.subTest(bad=bad), self.assertRaises(res.ResourceContractError) as ctx:
                self.index.resolve(bad)
            self.assertEqual(ctx.exception.code, "RESOURCE_PATH_OUTSIDE_ROOT")

if __name__ == "__main__":
    unittest.main(verbosity=2)
