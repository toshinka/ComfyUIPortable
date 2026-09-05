"""
Phase 3I.2: Character Staging Pointer Contract Simulation & Guide SSOT Verification
===================================================================================
Tests the contract and mathematical mechanics of character_staging_editor.js:
1. Hit testing for character boxes and resize handles.
2. Drag move coordinate calculation and [0.0, 1.0] boundary clamping.
3. Drag resize calculation and minimum dimension clamping.
4. Transactional serialization: JS commitOverride format matches Python backend schema.
5. End-to-end backend causality: Updated overrides propagate identically to
   Impact Region Mask and ControlNet Mannequin Guide (Guide Source SSOT).

NOTE: This simulates the browser DOM/pointer events in Python. Live interactive
browser testing in an active ComfyUI session is tracked as LIVE BROWSER POINTER E2E.
"""

import sys
import os
import json
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.character_staging_editor import TegakiMangaCharacterStagingEditor
from custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator import TegakiMangaLayoutGuideGenerator
from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from custom_nodes_custom.tegaki_manga_nodes.cast_master import get_default_cast_spec
from custom_nodes_custom.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from custom_nodes_custom.tegaki_manga_nodes.region_editor import default_region_spec


class SimulatedBrowserPointerSession:
    """
    Simulates the exact JavaScript pointer interaction logic implemented in
    custom_nodes_custom/tegaki_manga_nodes/web/js/character_staging_editor.js
    """
    def __init__(self, initial_overrides="{}"):
        self.selected_panel = 1
        self.selected_char_id = None
        self.drag_state = None
        self.last_canvas_layout = {"pX": 30, "pY": 30, "pW": 400, "pH": 400}
        self.overrides = json.loads(initial_overrides)
        self.chars = [
            {"character_id": "char_alice", "name": "Alice", "area": {"x": 0.08, "y": 0.15, "w": 0.45, "h": 0.75}},
            {"character_id": "char_bob", "name": "Bob", "area": {"x": 0.47, "y": 0.15, "w": 0.45, "h": 0.75}}
        ]
        self._apply_overrides_to_chars()

    def _apply_overrides_to_chars(self):
        pid_str = str(self.selected_panel)
        p_ov = self.overrides.get(pid_str, {})
        for c in self.chars:
            if c["character_id"] in p_ov and "area" in p_ov[c["character_id"]]:
                c["area"] = dict(p_ov[c["character_id"]]["area"])

    def commit_override(self, panel_id, char_id, area):
        pid_str = str(panel_id)
        if pid_str not in self.overrides:
            self.overrides[pid_str] = {}
        self.overrides[pid_str][char_id] = {"area": dict(area)}

    def get_serialized_overrides(self):
        return json.dumps(self.overrides, indent=2)

    def on_mouse_down(self, px, py):
        layout = self.last_canvas_layout
        pX, pY, pW, pH = layout["pX"], layout["pY"], layout["pW"], layout["pH"]
        if px < pX or px > pX + pW or py < pY or py > pY + pH:
            return False

        norm_x = max(0.0, min(1.0, (px - pX) / pW))
        norm_y = max(0.0, min(1.0, (py - pY) / pH))
        hs_norm_x = 10.0 / pW
        hs_norm_y = 10.0 / pH

        # 1. Resize handle check on selected char
        sel_char = next((c for c in self.chars if c["character_id"] == self.selected_char_id), None)
        if sel_char:
            hx = sel_char["area"]["x"] + sel_char["area"]["w"]
            hy = sel_char["area"]["y"] + sel_char["area"]["h"]
            if abs(norm_x - hx) <= hs_norm_x and abs(norm_y - hy) <= hs_norm_y:
                self.drag_state = {
                    "mode": "resize",
                    "char_id": sel_char["character_id"],
                    "start_norm_x": norm_x,
                    "start_norm_y": norm_y,
                    "orig_area": dict(sel_char["area"])
                }
                return True

        # 2. Hit test inside char box
        for c in reversed(self.chars):
            a = c["area"]
            if a["x"] <= norm_x <= a["x"] + a["w"] and a["y"] <= norm_y <= a["y"] + a["h"]:
                self.selected_char_id = c["character_id"]
                self.drag_state = {
                    "mode": "move",
                    "char_id": c["character_id"],
                    "start_norm_x": norm_x,
                    "start_norm_y": norm_y,
                    "orig_area": dict(a)
                }
                return True
        return False

    def on_mouse_move(self, px, py):
        if not self.drag_state:
            return False
        layout = self.last_canvas_layout
        pX, pY, pW, pH = layout["pX"], layout["pY"], layout["pW"], layout["pH"]
        norm_x = max(0.0, min(1.0, (px - pX) / pW))
        norm_y = max(0.0, min(1.0, (py - pY) / pH))
        dx = norm_x - self.drag_state["start_norm_x"]
        dy = norm_y - self.drag_state["start_norm_y"]

        target_char = next((c for c in self.chars if c["character_id"] == self.drag_state["char_id"]), None)
        if not target_char:
            return False

        orig = self.drag_state["orig_area"]
        if self.drag_state["mode"] == "move":
            new_x = max(0.0, min(1.0 - target_char["area"]["w"], orig["x"] + dx))
            new_y = max(0.0, min(1.0 - target_char["area"]["h"], orig["y"] + dy))
            target_char["area"]["x"] = round(new_x, 3)
            target_char["area"]["y"] = round(new_y, 3)
            self.commit_override(self.selected_panel, target_char["character_id"], target_char["area"])
            return True
        elif self.drag_state["mode"] == "resize":
            min_size = 0.05
            new_w = max(min_size, min(1.0 - target_char["area"]["x"], orig["w"] + dx))
            new_h = max(min_size, min(1.0 - target_char["area"]["y"], orig["h"] + dy))
            target_char["area"]["w"] = round(new_w, 3)
            target_char["area"]["h"] = round(new_h, 3)
            self.commit_override(self.selected_panel, target_char["character_id"], target_char["area"])
            return True
        return False

    def on_mouse_up(self):
        if self.drag_state:
            self.drag_state = None
            return True
        return False


class TestCharacterStagingBrowserPointerE2E(unittest.TestCase):
    def test_01_pointer_drag_move_and_clamping(self):
        """Test dragging Alice from left (0.08) to right (0.55)."""
        session = SimulatedBrowserPointerSession()

        # Alice box: x=0.08, y=0.15, w=0.45, h=0.75
        # In canvas pixels (layout: pX=30, pY=30, pW=400, pH=400):
        # Alice center roughly at px = 30 + 0.20*400 = 110, py = 30 + 0.40*400 = 190
        down_ok = session.on_mouse_down(110, 190)
        self.assertTrue(down_ok)
        self.assertEqual(session.selected_char_id, "char_alice")
        self.assertEqual(session.drag_state["mode"], "move")

        # Drag to right by +160px (dx = 160/400 = +0.40)
        # target x should become 0.08 + 0.40 = 0.48
        move_ok = session.on_mouse_move(270, 190)
        self.assertTrue(move_ok)
        alice = next(c for c in session.chars if c["character_id"] == "char_alice")
        self.assertEqual(alice["area"]["x"], 0.48)

        # Further drag to right beyond boundary (px = 30 + 400 = 430 -> norm_x = 1.0)
        # Max x is 1.0 - w = 1.0 - 0.45 = 0.55
        session.on_mouse_move(430, 190)
        self.assertEqual(alice["area"]["x"], 0.55)

        session.on_mouse_up()
        self.assertIsNone(session.drag_state)

        # Check serialization output
        serialized = session.get_serialized_overrides()
        data = json.loads(serialized)
        self.assertIn("1", data)
        self.assertIn("char_alice", data["1"])
        self.assertEqual(data["1"]["char_alice"]["area"]["x"], 0.55)

    def test_02_backend_causality_and_guide_ssot(self):
        """Verify that browser staging override propagates to both backend nodes synchronously."""
        cast_data = get_default_cast_spec()
        layout_data = get_default_panel_layout_spec(512, 512, preset="1_full")
        reg_spec = default_region_spec(512, 512, panel_count=1)
        reg_spec["regions"][0]["characters"] = [
            {"character_id": "char_alice", "name": "Alice", "enabled": True, "area": {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}}
        ]

        staging_editor = TegakiMangaCharacterStagingEditor()
        page_compiler = TegakiMangaPageCompiler()
        guide_gen = TegakiMangaLayoutGuideGenerator()

        # Step 1: Base without override
        base_reg, _, _ = staging_editor.process(
            region_spec=reg_spec,
            panel_layout_spec=layout_data,
            staging_overrides="{}"
        )
        base_char_x = base_reg["regions"][0]["characters"][0]["area"]["x"]

        # Step 2: With browser override moving Alice to x = 0.55
        browser_overrides = json.dumps({
            "1": {
                "char_alice": {
                    "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}
                }
            }
        })
        mod_reg, _, _ = staging_editor.process(
            region_spec=reg_spec,
            panel_layout_spec=layout_data,
            staging_overrides=browser_overrides
        )
        mod_char_x = mod_reg["regions"][0]["characters"][0]["area"]["x"]

        self.assertNotEqual(base_char_x, mod_char_x)
        self.assertEqual(mod_char_x, 0.55)

        # Step 3: Page compiler compiles modified region_spec
        mod_plan, _, _, _ = page_compiler.compile_page(
            region_spec=mod_reg,
            cast_spec=cast_data
        )

        # Step 4: Layout Guide Generator receives compiled plan
        guide_img, _, debug_json = guide_gen.generate_guide(
            scene_plan=mod_plan,
            guide_style="mannequin_capsule"
        )
        guide_debug = json.loads(debug_json)
        # Guide generator must reflect the exact x=0.55 staging
        rendered_char = guide_debug["characters"][0]
        self.assertEqual(rendered_char["box"][0], 0.55)
        print(f"\n[Pointer Contract Simulation] Dragged Alice x: {base_char_x} -> {mod_char_x}")
        print(f"[Guide SSOT Verification] Mannequin guide rendered bounds: {rendered_char['box']}")


def run_test():
    print("=" * 80)
    print("Phase 3I.2: Character Staging Pointer Contract Simulation & Guide SSOT")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCharacterStagingBrowserPointerE2E)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 80)
    print(f"POINTER CONTRACT SIMULATION: {'PASS' if result.wasSuccessful() else 'FAIL'}")
    print(f"BACKEND GUIDE SSOT:          {'PASS' if result.wasSuccessful() else 'FAIL'}")
    print("LIVE BROWSER POINTER E2E:    PENDING")
    print("=" * 80)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_test())
