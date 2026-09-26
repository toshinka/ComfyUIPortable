"""MANGA-PROMPT-VALIDATION-COHERENCE1: Wildcard-contained LoRAs, explicit Expand, runtime source identity.

Real contracts: engine_resources.diagnose_lora_sources (raw-prompt UI preflight),
basic_generation.expand_wildcard_text / compile path (dynamicprompts), and
basic_generation_api.expand_one_wildcard / package_source_digest.  No ComfyUI, no /prompt, no GPU.
"""

from __future__ import annotations

import hashlib
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
from custom_nodes_custom.tegaki_manga_nodes import basic_generation as bg  # noqa: E402
from custom_nodes_custom.tegaki_manga_nodes import basic_generation_api as api  # noqa: E402

LORAS = ("styles/ink.safetensors", "characters/A/hero.safetensors")


class WildcardLoraContractTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.root = base / "Lora"
        for rel in LORAS:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(b"MODEL")
        self.index = res.build_trusted_lora_index(list(LORAS), str(self.root))
        self.wildcards = base / "wildcards"
        (self.wildcards / "nested").mkdir(parents=True)
        (self.wildcards / "style_lora.txt").write_text("<lora:ink:0.4>, monochrome\n<lora:hero:0.6>, smile\n", encoding="utf-8")
        (self.wildcards / "broken_lora.txt").write_text("<lora:does_not_exist:0.5>, x\n", encoding="utf-8")
        (self.wildcards / "nested" / "pose.txt").write_text("standing\nsitting\n", encoding="utf-8")
        self.digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.wildcards.rglob("*.txt")}
        self._env = os.environ.get(bg.WILDCARD_ENV)
        os.environ[bg.WILDCARD_ENV] = str(self.wildcards)

    def tearDown(self):
        if self._env is None:
            os.environ.pop(bg.WILDCARD_ENV, None)
        else:
            os.environ[bg.WILDCARD_ENV] = self._env
        self._tmp.cleanup()

    def diagnose(self, text):
        return res.diagnose_lora_sources([{"source": "page_positive", "text": text}], self.index)

    # --- A: raw-prompt preflight never falsely rejects Wildcard-borne LoRAs -------------
    def test_a_wildcard_reference_is_not_judged_as_lora_syntax(self):
        result = self.diagnose("1girl, __style_lora__")
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["problems"], 0)
        self.assertTrue(result["has_wildcards"])

    def test_a_choice_group_alternatives_are_conditional_not_duplicates(self):
        result = self.diagnose("{<lora:ink:0.4>, red|<lora:ink:0.4>, blue}, <lora:hero:1>")
        self.assertEqual(result["problems"], 0, result)
        self.assertEqual([e["status"] for e in result["entries"]], ["RESOLVED", "RESOLVED", "RESOLVED"])
        self.assertEqual([e.get("conditional", False) for e in result["entries"]], [True, True, False])
        self.assertEqual([c["resolved_id"] for c in result["chain"]], ["characters/A/hero.safetensors"],
                         "only unconditional LoRAs are claimed in the generation-order chain")
        dynamic = self.diagnose("<lora:{ink|hero}:0.5>")
        self.assertEqual((dynamic["entries"][0]["status"], dynamic["entries"][0]["blocking"], dynamic["problems"]),
                         ("DYNAMIC_LORA", False, 0))
        maybe = self.diagnose("{<lora:gone:1>|plain}")
        self.assertEqual((maybe["entries"][0]["status"], maybe["entries"][0]["blocking"], maybe["problems"]),
                         ("LORA_UNAVAILABLE", False, 0), "reported, but only fails generation if chosen")
        # outside a choice group nothing changed: duplicates and unknowns still block
        self.assertEqual(self.diagnose("<lora:ink:1>, <lora:ink:1>")["problems"], 1)
        self.assertEqual(self.diagnose("<lora:gone:1>")["problems"], 1)
        self.assertEqual(self.diagnose(r"\{<lora:gone:1>\}")["problems"], 1, "escaped braces are literal text")

    # --- B/C/D/E: explicit Expand ---------------------------------------------------------
    def test_b_expand_produces_one_existing_dynamicprompts_expansion(self):
        seen = set()
        for _ in range(12):
            out = api.expand_one_wildcard("style_lora")
            self.assertEqual((out["ok"], out["name"], out["token"]), (True, "style_lora", "__style_lora__"))
            self.assertIn(out["expanded_text"], {"<lora:ink:0.4>, monochrome", "<lora:hero:0.6>, smile"},
                          "exactly one line, never all alternatives")
            seen.add(out["expanded_text"])
            self.assertNotIn(str(self.wildcards), repr(out), "no physical root leaves the backend")
        nested = api.expand_one_wildcard("nested\\pose")
        self.assertIn(nested["expanded_text"], {"standing", "sitting"})
        self.assertEqual(nested["token"], "__nested/pose__")

    def test_c_expanded_loras_are_diagnosed_like_any_explicit_lora(self):
        expanded = api.expand_one_wildcard("style_lora")["expanded_text"]
        result = self.diagnose(f"1girl, {expanded}")
        self.assertEqual(result["problems"], 0)
        self.assertEqual(len(result["chain"]), 1)

    def test_d_invalid_lora_in_a_concrete_expansion_reports_the_normal_error(self):
        expanded = api.expand_one_wildcard("broken_lora")["expanded_text"]
        result = self.diagnose(expanded)
        self.assertEqual((result["problems"], result["entries"][0]["status"]), (1, "LORA_UNAVAILABLE"))
        # and generation (expand first, then LORA_RE) sees the same directive
        text = bg.expand_wildcard_text("__broken_lora__", seed=3)["expanded_text"]
        self.assertEqual([m.group(1) for m in bg.LORA_RE.finditer(text)], ["does_not_exist"])

    def test_e_expand_is_read_only_and_fails_closed(self):
        api.expand_one_wildcard("style_lora")
        for bad in ("../x", "/abs", "C:/x", "a{b|c}", "a__b", "", None, 5):
            with self.subTest(bad=bad), self.assertRaises(bg.GenerationContractError):
                api.expand_one_wildcard(bad)
        with self.assertRaises(bg.GenerationContractError) as missing:
            api.expand_one_wildcard("missing_one")
        self.assertEqual(missing.exception.code, "WILDCARD_NOT_FOUND")
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.wildcards.rglob("*.txt")}
        self.assertEqual(after, self.digests, "Wildcard source files unchanged")


MIKI = "<lora:Miki_Hoshii__The_iDOLM_STER_2011__epoch_8:1.0>"
KAT = "<lora:Katsuragi__Idol__v2:0.4>"


class LoraDoubleUnderscoreCollisionTests(unittest.TestCase):
    """MANGA-WILDCARD-LORA-DOUBLE-UNDERSCORE-COLLISION1: '__' inside <lora:...> is literal."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.root = base / "Lora"
        for rel in ("chars/Miki_Hoshii__The_iDOLM_STER_2011__epoch_8.safetensors",
                    "chars/Katsuragi__Idol__v2.safetensors"):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(b"MODEL")
        self.index = res.build_trusted_lora_index(
            ["chars/Miki_Hoshii__The_iDOLM_STER_2011__epoch_8.safetensors", "chars/Katsuragi__Idol__v2.safetensors"],
            str(self.root))
        self.wildcards = base / "wildcards"
        self.wildcards.mkdir()
        (self.wildcards / "quality.txt").write_text("masterpiece\n", encoding="utf-8")
        (self.wildcards / "pose.txt").write_text("standing\n", encoding="utf-8")
        (self.wildcards / "idol_lora.txt").write_text(f"{MIKI}, stage\n", encoding="utf-8")
        self.before = {p.name: p.read_bytes() for p in self.wildcards.iterdir()}
        self._env = os.environ.get(bg.WILDCARD_ENV)
        os.environ[bg.WILDCARD_ENV] = str(self.wildcards)

    def tearDown(self):
        if self._env is None:
            os.environ.pop(bg.WILDCARD_ENV, None)
        else:
            os.environ[bg.WILDCARD_ENV] = self._env
        self._tmp.cleanup()

    def expand(self, raw):
        return bg._expand_dynamic_prompt(raw, 7, "global:positive")[0]

    def test_a_b_lora_name_is_not_a_wildcard_and_stays_byte_identical(self):
        self.assertEqual(self.expand(MIKI), MIKI)  # no WILDCARD_NOT_FOUND for The_iDOLM_STER_2011
        checked = bg.validate_wildcard_text(MIKI)
        self.assertTrue(checked["ok"], checked["errors"])
        self.assertEqual(checked["wildcards"], [])

    def test_c_d_real_wildcards_before_and_after_still_expand(self):
        self.assertEqual(self.expand(f"portrait, __quality__, {MIKI}"), f"portrait, masterpiece, {MIKI}")
        self.assertEqual(self.expand(f"{MIKI}, __pose__"), f"{MIKI}, standing")

    def test_e_multiple_double_underscore_loras_intact(self):
        raw = f"__quality__, {MIKI}, {KAT}, __pose__"
        self.assertEqual(self.expand(raw), f"masterpiece, {MIKI}, {KAT}, standing")
        self.assertEqual([m.group(1) for m in bg.LORA_RE.finditer(self.expand(raw))],
                         ["Miki_Hoshii__The_iDOLM_STER_2011__epoch_8", "Katsuragi__Idol__v2"])

    def test_f_plain_wildcard_syntax_unchanged(self):
        self.assertEqual(self.expand("__quality__"), "masterpiece")
        with self.assertRaises(bg.GenerationContractError) as missing:
            self.expand("__The_iDOLM_STER_2011__")  # outside a LoRA it IS a wildcard reference
        self.assertEqual(missing.exception.code, "WILDCARD_NOT_FOUND")
        self.assertEqual(self.expand("{<lora:{a|b}:1>|x}").count("__"), 0)

    def test_g_expand_ui_keeps_loras_emitted_by_a_wildcard(self):
        self.assertEqual(api.expand_one_wildcard("idol_lora")["expanded_text"], f"{MIKI}, stage")
        self.assertEqual(self.expand("__idol_lora__"), f"{MIKI}, stage", "generation path too")
        self.assertEqual({p.name: p.read_bytes() for p in self.wildcards.iterdir()}, self.before)

    def test_h_diagnostics_resolve_the_actual_lora(self):
        result = res.diagnose_lora_sources([{"source": "page_positive", "text": f"__quality__, {MIKI}"}], self.index)
        self.assertEqual([(e["status"], e.get("resolved_id")) for e in result["entries"]],
                         [("RESOLVED", "chars/Miki_Hoshii__The_iDOLM_STER_2011__epoch_8.safetensors")])
        self.assertEqual((result["problems"], len(result["chain"]), result["has_wildcards"]), (0, 1, True))
        only_lora = res.diagnose_lora_sources([{"source": "page_positive", "text": MIKI}], self.index)
        self.assertFalse(only_lora["has_wildcards"], "a LoRA name is not a Wildcard reference")

    def test_reserved_placeholder_characters_fail_closed(self):
        with self.assertRaises(bg.GenerationContractError):
            self.expand("x \ue0020\ue003")


class RuntimeSourceIdentityTests(unittest.TestCase):
    def test_backend_digest_matches_the_launcher_formula(self):
        folder = ROOT / "custom_nodes_custom" / "tegaki_manga_nodes"
        expected = hashlib.sha256()
        for name in sorted(n for n in os.listdir(folder) if n.endswith(".py")):
            expected.update(name.encode() + b"\0" + (folder / name).read_bytes() + b"\0")
        self.assertEqual(api.package_source_digest(str(folder)), expected.hexdigest())
        self.assertEqual(api.LOADED_SOURCE_DIGEST, expected.hexdigest(), "digest of the source this process loaded")

    def test_digest_changes_when_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / "a.py").write_text("x = 1\n")
            before = api.package_source_digest(tmp)
            (pathlib.Path(tmp) / "a.py").write_text("x = 2\n")
            self.assertNotEqual(before, api.package_source_digest(tmp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
