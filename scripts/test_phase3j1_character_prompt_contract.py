"""
Test Phase 3J.1: Character Prompt Contract and Fixture Repair
============================================================
Verifies:
1. CAST_SPEC validation of 'prompt' and 'negative_prompt'
2. CHARACTER_BINDING validation of 'prompt_override' and 'negative_prompt_override'
3. Migration fallback: 'appearance' -> 'prompt', 'acting' -> 'prompt_override'
4. PAGE_COMPILE_PLAN character 'combined_prompt' contains identity tokens
5. Fail-closed assertion: non-empty prompt truth
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.scene_spec import validate_cast_spec, validate_character_binding
from custom_nodes_custom.tegaki_manga_nodes.region_editor import validate_region_spec
from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler


class TestPhase3J1CharacterPromptContract(unittest.TestCase):

    def test_01_canonical_cast_spec(self):
        """Canonical CAST_SPEC with prompt and negative_prompt must pass."""
        cast = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "prompt": "1girl, blonde twin tails, blue eyes, school uniform, pleated skirt",
                    "negative_prompt": "1boy, male, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "enabled": True,
                    "prompt": "1boy, short black hair, dark school uniform, male student",
                    "negative_prompt": "1girl, female, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                }
            ]
        }
        validated = validate_cast_spec(cast)
        self.assertEqual(len(validated["characters"]), 2)
        self.assertIn("1girl", validated["characters"][0]["prompt"])
        self.assertIn("1boy", validated["characters"][1]["prompt"])

    def test_02_cast_spec_migration_fallback(self):
        """Legacy CAST_SPEC with appearance must map to prompt."""
        legacy_cast = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "appearance": "1girl, solo, dark hair, twintails",
                    "negative_prompt": "1boy, male"
                }
            ]
        }
        validated = validate_cast_spec(legacy_cast)
        self.assertEqual(validated["characters"][0]["prompt"], "1girl, solo, dark hair, twintails")

    def test_03_canonical_binding_contract(self):
        """Canonical character binding with prompt_override."""
        binding = {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "standing calmly",
            "negative_prompt_override": "",
            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75},
            "metadata": {"semantic_role": "primary"}
        }
        validated = validate_character_binding(binding, {"char_alice"})
        self.assertEqual(validated["prompt_override"], "standing calmly")

    def test_04_binding_migration_fallback(self):
        """Legacy character binding with acting must map to prompt_override."""
        legacy_binding = {
            "character_id": "char_alice",
            "enabled": True,
            "acting": "standing calmly on left",
            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
        }
        validated = validate_character_binding(legacy_binding, {"char_alice"})
        self.assertEqual(validated["prompt_override"], "standing calmly on left")

    def test_05_page_compile_plan_prompt_truth(self):
        """Compile plan must merge master prompt and override prompt into combined_prompt."""
        cast = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "prompt": "1girl, blonde twin tails, blue eyes, school uniform, pleated skirt",
                    "negative_prompt": "1boy, male, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "enabled": True,
                    "prompt": "1boy, short black hair, dark school uniform, male student",
                    "negative_prompt": "1girl, female, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                }
            ]
        }
        region_spec = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "panel_count": 1,
            "global_prompt": "manga illustration, monochrome linework",
            "global_negative_prompt": "low quality",
            "regions": [
                {
                    "id": 1,
                    "type": "panel",
                    "panel": {
                        "prompt": "empty school courtyard, clear open foreground, simple architectural background",
                        "negative_prompt": "low quality, text"
                    },
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "prompt_override": "standing calmly on left",
                            "negative_prompt_override": "",
                            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
                        },
                        {
                            "character_id": "char_bob",
                            "enabled": True,
                            "prompt_override": "standing listening on right",
                            "negative_prompt_override": "",
                            "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}
                        }
                    ]
                }
            ]
        }
        compiler = TegakiMangaPageCompiler()
        plan, _, _, _ = compiler.compile_page(region_spec=region_spec, cast_spec=json.dumps(cast))
        koma1 = plan["panels"][0]
        chars = koma1["characters"]
        self.assertEqual(len(chars), 2)
        
        alice_p = chars[0]["combined_prompt"]
        bob_p = chars[1]["combined_prompt"]
        
        # Truth Assertions: Character identity MUST reach combined_prompt!
        self.assertIn("1girl", alice_p)
        self.assertIn("blonde twin tails", alice_p)
        self.assertIn("standing calmly on left", alice_p)
        
        self.assertIn("1boy", bob_p)
        self.assertIn("short black hair", bob_p)
        self.assertIn("standing listening on right", bob_p)


if __name__ == "__main__":
    unittest.main()
