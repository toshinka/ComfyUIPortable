"""Targeted PLAY1a tests of the production pure catalog and compiler."""

import importlib.util
import os
import pathlib
import tempfile
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / ".." / "custom_nodes_custom" / "tegaki_manga_nodes" / "basic_generation.py"
SPEC = importlib.util.spec_from_file_location("manga_basic_generation", MODULE.resolve())
basic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(basic)


def fake_inputs():
    return {
        basic.NODE_IDENTITY: {"required": {}},
        "CheckpointLoaderSimple": {"required": {"ckpt_name": (["Illustrious.safetensors"], {})}},
        "LoraLoader": {"required": {
            "lora_name": (["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"], {}),
            "model": ("MODEL",), "clip": ("CLIP",), "strength_model": ("FLOAT",), "strength_clip": ("FLOAT",),
        }},
        "CLIPTextEncode": {"required": {"text": ("STRING",), "clip": ("CLIP",)}},
        "EmptyLatentImage": {"required": {
            "width": ("INT", {"min": 16, "max": 8192, "step": 8}),
            "height": ("INT", {"min": 16, "max": 8192, "step": 8}),
            "batch_size": ("INT", {"min": 1, "max": 4096}),
        }},
        "KSampler": {"required": {
            "seed": ("INT", {"min": 0, "max": 18446744073709551615}),
            "steps": ("INT", {"min": 1, "max": 10000}),
            "cfg": ("FLOAT", {"min": 0.0, "max": 100.0}),
            "sampler_name": (["euler", "dpm_2"], {}),
            "scheduler": (["normal", "simple", "sgm_uniform"], {}),
            "model": ("MODEL",), "positive": ("CONDITIONING",), "negative": ("CONDITIONING",),
            "latent_image": ("LATENT",), "denoise": ("FLOAT",),
        }},
        "VAEDecode": {"required": {"samples": ("LATENT",), "vae": ("VAE",)}},
        "SaveImage": {"required": {"images": ("IMAGE",), "filename_prefix": ("STRING",)}},
    }


def request(revision):
    return {
        "request_id": "play1a_1", "mode": "txt2img", "checkpoint_id": "Illustrious.safetensors",
        "positive_raw": "draw <lora:styles/A:0.5> here <lora:B:1>",
        "negative_raw": "bad", "sampler_id": "euler", "scheduler_id": "normal",
        "steps": 20, "cfg": 7.0, "width": 832, "height": 1216,
        "seed_requested": "0", "capability_revision": revision,
    }


class BasicGenerationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = basic.build_catalog(
            ["Illustrious.safetensors"],
            ["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"],
            fake_inputs(), lambda kind, name: True,
        )
        self.valid = request(self.catalog["revision"])

    def expect_error(self, code, **changes):
        candidate = {**self.valid, **changes}
        with self.assertRaises(basic.GenerationContractError) as raised:
            basic.compile_basic(candidate, self.catalog)
        self.assertEqual(raised.exception.code, code)

    def test_catalog_is_source_bounded_and_revisioned(self):
        self.assertEqual(self.catalog["backend_node_identity"], basic.NODE_IDENTITY)
        self.assertEqual(self.catalog["checkpoints"][0]["family_confidence"], "UNKNOWN")
        self.assertEqual(self.catalog["samplers"], ["euler", "dpm_2"])
        self.assertEqual(len(self.catalog["revision"]), 64)
        self.assertEqual(self.catalog["backend_bounds"]["seed"]["max"], "18446744073709551615")
        self.assertEqual(self.catalog, basic.build_catalog(
            ["Illustrious.safetensors"],
            ["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"],
            fake_inputs(), lambda kind, name: True,
        ))

    def test_graph_wires_both_text_encoders_after_ordered_loras(self):
        output = basic.compile_basic(self.valid, self.catalog)
        graph = output["graph"]
        self.assertEqual(output["requested_seed"], "0")
        self.assertEqual(output["effective_seed"], 0)
        self.assertEqual([item["id"] for item in output["resolved_loras"]],
                         ["styles/A.safetensors", "styles/B.safetensors"])
        self.assertEqual(graph["1"]["inputs"]["ckpt_name"], "Illustrious.safetensors")
        self.assertEqual(graph["2"]["inputs"]["model"], ["1", 0])
        self.assertEqual(graph["3"]["inputs"]["model"], ["2", 0])
        self.assertEqual(graph["4"]["inputs"], {"text": "draw  here ", "clip": ["3", 1]})
        self.assertEqual(graph["5"]["inputs"], {"text": "bad", "clip": ["3", 1]})
        self.assertEqual(graph["6"]["inputs"], {"width": 832, "height": 1216, "batch_size": 1})
        self.assertEqual(graph["7"]["inputs"]["model"], ["3", 0])
        self.assertEqual(graph["7"]["inputs"]["seed"], 0)
        self.assertEqual(graph["7"]["inputs"]["denoise"], 1.0)
        self.assertEqual(graph["8"]["inputs"]["vae"], ["1", 2])
        self.assertEqual(graph["9"]["inputs"]["filename_prefix"], "Manga/Playable/compiled")
        self.assertEqual(output["graph_digest"], basic.compile_basic(self.valid, self.catalog)["graph_digest"])

    def test_negative_lora_is_global_and_empty_negative_is_legal(self):
        candidate = {**self.valid, "positive_raw": "hello", "negative_raw": "<lora:A:0.7>"}
        # Ambiguous basename must be refused before constructing a partial graph.
        self.expect_error("LORA_AMBIGUOUS", positive_raw="hello", negative_raw="<lora:A:0.7>")
        candidate["negative_raw"] = "<lora:styles/B:0.7>"
        output = basic.compile_basic(candidate, self.catalog)
        self.assertEqual(output["negative_clean"], "")
        self.assertEqual(output["graph"]["3"]["inputs"]["clip"], ["2", 1])
        candidate["negative_raw"] = ""
        self.assertEqual(basic.compile_basic(candidate, self.catalog)["negative_clean"], "")

    def test_random_seed_called_once_and_only_for_minus_one(self):
        calls = []
        def seed_source():
            calls.append(1)
            return 123
        zero = basic.compile_basic(self.valid, self.catalog, seed_source)
        self.assertEqual(zero["effective_seed"], 0)
        self.assertEqual(calls, [])
        random = basic.compile_basic({**self.valid, "seed_requested": "-1"}, self.catalog, seed_source)
        self.assertEqual(random["effective_seed"], 123)
        self.assertEqual(len(calls), 1)

    def test_fail_closed_lora_syntax_and_resolution(self):
        for raw, code in (
            ("<lora:missing:1>", "LORA_UNAVAILABLE"),
            ("<lora:styles/B.pt:1>", "LORA_UNAVAILABLE"),
            ("<lora:A:1>", "LORA_AMBIGUOUS"),
            ("<lora:styles/A:1:2>", "UNSUPPORTED_PROMPT_TAG"),
            ("<lora:styles/A:nan>", "UNSUPPORTED_PROMPT_TAG"),
            ("<lora:styles/A:5>", "INVALID_LORA"),
            ("<lora:../A:1>", "INVALID_CATALOG_ID"),
            ("<lora:styles/A:1", "UNSUPPORTED_PROMPT_TAG"),
            ("<hypernet:foo:1>", "UNSUPPORTED_PROMPT_TAG"),
            ("<lora:styles/A:1><lora:styles/A.safetensors:1>", "LORA_DUPLICATE"),
        ):
            with self.subTest(raw=raw):
                self.expect_error(code, positive_raw=raw)

    def test_fail_closed_request_and_bounds(self):
        self.expect_error("CHECKPOINT_UNAVAILABLE", checkpoint_id="C:/model.safetensors")
        self.expect_error("CHECKPOINT_UNAVAILABLE", checkpoint_id="missing.safetensors")
        self.expect_error("SAMPLING_UNAVAILABLE", sampler_id="Euler Negative")
        self.expect_error("INVALID_SEED", seed_requested="1.5")
        self.expect_error("INVALID_SEED", seed_requested="-2")
        self.expect_error("INVALID_PARAMETER", width=513)
        backend_step = fake_inputs()
        backend_step["EmptyLatentImage"]["required"]["width"] = ("INT", {"min": 16, "max": 8192, "step": 16})
        step_catalog = basic.build_catalog(["Illustrious.safetensors"], ["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"], backend_step, lambda kind, name: True)
        with self.assertRaises(basic.GenerationContractError):
            basic.compile_basic({**self.valid, "width": 840, "capability_revision": step_catalog["revision"]}, step_catalog)
        self.expect_error("INVALID_PARAMETER", width=2048, height=2048)
        self.expect_error("INVALID_PARAMETER", cfg=float("nan"))
        self.expect_error("INVALID_PARAMETER", steps=True)
        self.expect_error("INVALID_REQUEST", extra="unknown")
        self.expect_error("CAPABILITY_CHANGED", capability_revision="stale")

    def test_catalog_missing_or_stale_is_not_empty_success(self):
        with self.assertRaises(basic.GenerationContractError):
            basic.build_catalog([], [], {}, lambda kind, name: True)
        offline = basic.build_catalog(["Illustrious.safetensors"], [], fake_inputs(), lambda kind, name: False)
        self.assertFalse(offline["checkpoints"][0]["available"])
        with self.assertRaises(basic.GenerationContractError) as raised:
            basic.compile_basic({**self.valid, "capability_revision": offline["revision"]}, offline)
        self.assertEqual(raised.exception.code, "CHECKPOINT_UNAVAILABLE")
        with self.assertRaises(basic.GenerationContractError):
            basic.build_catalog(["../bad.safetensors"], [], fake_inputs(), lambda kind, name: True)
        lora_offline = basic.build_catalog(["Illustrious.safetensors"], ["styles/B.safetensors"], fake_inputs(), lambda kind, name: kind != "loras")
        with self.assertRaises(basic.GenerationContractError) as raised:
            basic.compile_basic({**self.valid, "positive_raw": "<lora:styles/B:1>", "capability_revision": lora_offline["revision"]}, lora_offline)
        self.assertEqual(raised.exception.code, "LORA_UNAVAILABLE")


class DynamicPromptTests(unittest.TestCase):
    """PLAY4 bounded dynamic-prompt contract tests over project fixtures."""

    @classmethod
    def setUpClass(cls):
        try:
            import dynamicprompts  # noqa: F401
        except Exception:
            raise unittest.SkipTest("embedded dynamicprompts is unavailable")

    def setUp(self):
        self.catalog = basic.build_catalog(
            ["Illustrious.safetensors"],
            ["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"],
            fake_inputs(), lambda kind, name: True,
        )

    def _request(self, positive, negative="", seed="123"):
        return {
            "request_id": "play4_dynamic",
            "mode": "txt2img",
            "checkpoint_id": "Illustrious.safetensors",
            "positive_raw": positive,
            "negative_raw": negative,
            "sampler_id": "euler",
            "scheduler_id": "normal",
            "steps": 20,
            "cfg": 7.0,
            "width": 832,
            "height": 1216,
            "seed_requested": seed,
            "capability_revision": self.catalog["revision"],
        }

    def _compile(self, files, positive, negative="", seed="123"):
        with tempfile.TemporaryDirectory(prefix="tegaki-play4-wildcards-") as directory:
            root = pathlib.Path(directory)
            for name, contents in files.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
            previous = os.environ.get(basic.WILDCARD_ENV)
            os.environ[basic.WILDCARD_ENV] = str(root)
            try:
                return basic.compile_basic(self._request(positive, negative, seed), self.catalog)
            finally:
                if previous is None:
                    os.environ.pop(basic.WILDCARD_ENV, None)
                else:
                    os.environ[basic.WILDCARD_ENV] = previous

    def _expect_error(self, files, positive, code, negative=""):
        with self.assertRaises(basic.GenerationContractError) as raised:
            self._compile(files, positive, negative)
        self.assertEqual(raised.exception.code, code)

    def test_wildcard_and_choice_expansion(self):
        wildcard = self._compile({"color.txt": "red\nblue\n"}, "hero __color__")
        self.assertIn(wildcard["positive_expanded"], ("hero red", "hero blue"))
        choice = self._compile({}, "hero {smile|serious expression}")
        self.assertIn(choice["positive_expanded"], ("hero smile", "hero serious expression"))

    def test_same_seed_is_deterministic(self):
        files = {"color.txt": "red\nblue\n", "nested/pose.txt": "__color__ {front|profile}\n"}
        first = self._compile(files, "hero __nested/pose__", "bad {soft|hard}", seed="77")
        second = self._compile(files, "hero __nested/pose__", "bad {soft|hard}", seed="77")
        self.assertEqual(first["positive_expanded"], second["positive_expanded"])
        self.assertEqual(first["negative_expanded"], second["negative_expanded"])
        self.assertEqual(first["graph_digest"], second["graph_digest"])

    def test_positive_and_negative_rng_domains_are_independent(self):
        first = self._compile({}, "hero {a|b}", "bad {red|blue}", seed="8")
        second = self._compile({}, "hero {a|b|c}", "bad {red|blue}", seed="8")
        self.assertEqual(first["negative_expanded"], second["negative_expanded"])

    def test_nested_wildcard_choice_and_weighted_choice(self):
        nested = self._compile({"outer.txt": "__inner__\n", "inner.txt": "inside\n"}, "__outer__")
        self.assertEqual(nested["positive_expanded"], "inside")
        choice = self._compile({}, "{left|{middle|right}}")
        self.assertIn(choice["positive_expanded"], ("left", "middle", "right"))
        weighted = self._compile({}, "{1::rare|9::common}")
        self.assertIn(weighted["positive_expanded"], ("rare", "common"))

    def test_escaped_braces_are_literal(self):
        result = self._compile({}, r"literal \{a|b\}")
        self.assertEqual(result["positive_expanded"], "literal {a|b}")

    def test_missing_and_malformed_fail_closed(self):
        self._expect_error({}, "hero __does_not_exist__", "WILDCARD_NOT_FOUND")
        self._expect_error({}, "hero {red|blue", "INVALID_PROMPT_SYNTAX")

    def test_wildcard_path_safety(self):
        for prompt in ("__../secret__", "__foo/../../secret__", "__C:/secret__", "__/secret__", "__\\\\secret__", "__bad\x00name__"):
            with self.subTest(prompt=prompt):
                self._expect_error({}, prompt, "INVALID_WILDCARD_PATH")

    def test_wildcard_emitted_lora_uses_strict_resolver(self):
        valid = self._compile({"with_lora.txt": "hero <lora:styles/B:0.7>\n"}, "__with_lora__")
        self.assertEqual(valid["resolved_loras"][0]["id"], "styles/B.safetensors")
        self.assertEqual(valid["positive_clean"], "hero ")
        self._expect_error({"bad_lora.txt": "hero <lora:missing:0.7>\n"}, "__bad_lora__", "LORA_UNAVAILABLE")
        self._expect_error({"dup.txt": "<lora:styles/A:0.5> <lora:styles/A.safetensors:0.6>\n"}, "__dup__", "LORA_DUPLICATE")

    def test_prompt_audit_trail_and_root_override(self):
        raw = "hero __with_lora__"
        result = self._compile({"with_lora.txt": "style <lora:styles/B:0.7>\n"}, raw)
        self.assertEqual(result["positive_raw"], raw)
        self.assertEqual(result["positive_expanded"], "hero style <lora:styles/B:0.7>")
        self.assertEqual(result["positive_clean"], "hero style ")
        self.assertEqual(result["wildcard_root"].split("\\")[-1], pathlib.Path(result["wildcard_root"]).name)
        self.assertEqual(result["dynamicprompts_version"], "0.31.0")

    def test_wildcard_changes_are_seen_on_later_compile(self):
        with tempfile.TemporaryDirectory(prefix="tegaki-play4-refresh-") as directory:
            root = pathlib.Path(directory)
            file = root / "changing.txt"
            file.write_text("first\n", encoding="utf-8")
            previous = os.environ.get(basic.WILDCARD_ENV)
            os.environ[basic.WILDCARD_ENV] = str(root)
            try:
                first = basic.compile_basic(self._request("__changing__"), self.catalog)
                file.write_text("second\n", encoding="utf-8")
                second = basic.compile_basic(self._request("__changing__"), self.catalog)
            finally:
                if previous is None:
                    os.environ.pop(basic.WILDCARD_ENV, None)
                else:
                    os.environ[basic.WILDCARD_ENV] = previous
        self.assertEqual(first["positive_expanded"], "first")
        self.assertEqual(second["positive_expanded"], "second")



class BasicApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        import types
        package = types.ModuleType("tegaki_play1a_test_package")
        package.__path__ = [str(MODULE.resolve().parent)]
        sys.modules[package.__name__] = package
        sys.modules[package.__name__ + ".basic_generation"] = basic
        class Routes:
            def __init__(self):
                self.registered = []
            def get(self, path):
                return lambda handler: self.registered.append(("GET", path, handler))
            def post(self, path):
                return lambda handler: self.registered.append(("POST", path, handler))
        cls.routes = Routes()
        fake_server = types.ModuleType("server")
        fake_server.PromptServer = types.SimpleNamespace(instance=types.SimpleNamespace(routes=cls.routes))
        previous = sys.modules.get("server")
        sys.modules["server"] = fake_server
        try:
            api_path = MODULE.resolve().with_name("basic_generation_api.py")
            spec = importlib.util.spec_from_file_location(package.__name__ + ".basic_generation_api", api_path)
            cls.api = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.api)
        finally:
            if previous is None:
                del sys.modules["server"]
            else:
                sys.modules["server"] = previous
        cls.catalog = basic.build_catalog(
            ["Illustrious.safetensors"], ["styles/A.safetensors", "styles/B.safetensors", "other/A.safetensors"],
            fake_inputs(), lambda kind, name: True,
        )

    def test_only_two_backend_routes_registered(self):
        self.assertEqual([(method, path) for method, path, _ in self.routes.registered], [
            ("GET", "/tegaki/manga/generation/capabilities"),
            ("POST", "/tegaki/manga/generation/compile-basic"),
        ])

    def test_api_compile_and_malformed_json_fail_closed(self):
        import asyncio
        from unittest.mock import patch
        class Content:
            def __init__(self, body):
                self.body = body
            async def iter_chunked(self, size):
                for index in range(0, len(self.body), size):
                    yield self.body[index:index + size]
        class Request:
            def __init__(self, body):
                self.content = Content(body)
                self.content_length = len(body)
                self.content_type = "application/json"
        import json
        with patch.object(self.api, "_live_catalog", return_value=self.catalog):
            body = json.dumps(request(self.catalog["revision"])).encode()
            response = asyncio.run(self.api.api_manga_basic_compile(Request(body)))
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.text)["effective_seed"], 0)
            for invalid in (b'{"cfg":NaN}', b'{"cfg":1,"cfg":2}'):
                rejected = asyncio.run(self.api.api_manga_basic_compile(Request(invalid)))
                self.assertEqual(rejected.status, 400)
                self.assertEqual(json.loads(rejected.text)["error_code"], "INVALID_JSON")
            rejected = asyncio.run(self.api.api_manga_basic_compile(Request(json.dumps({**request(self.catalog["revision"]), "positive_raw": "<lora:missing:1>"}).encode())))
            self.assertEqual(rejected.status, 422)
            self.assertEqual(json.loads(rejected.text)["error_code"], "LORA_UNAVAILABLE")
if __name__ == "__main__":
    unittest.main()
