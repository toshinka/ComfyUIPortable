"""
test_m1_1_scene_id_uniqueness.py — M1.1 Scene ID Uniqueness Tests (Finding G)
=============================================================================
Verifies that adding and deleting scenes (specifically deleting middle scenes)
guarantees stable, collision-free, unique scene_ids.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.authoring_contract import (
    create_document,
    create_page,
    create_scene,
    make_area,
    validate_document,
)
from tegaki_manga_nodes.minimum_hand_scene_editor import create_default_m1_document


def simulate_js_add_scene(scenes: list) -> dict:
    """Mirrors the updated JS btnAddScene logic in web/js/minimum_hand_scene_editor.js."""
    if len(scenes) >= 6:
        raise ValueError("Max 6 scenes allowed")

    # Stable unique ID generation (Finding G)
    import re
    existing_nums = []
    for s in scenes:
        sid = s.get("scene_id", "")
        m = re.search(r"scene_(\d+)", sid)
        if m:
            existing_nums.append(int(m.group(1)))

    next_num = (max(existing_nums) + 1) if existing_nums else 1
    new_id = f"scene_{next_num}"
    while any(s.get("scene_id") == new_id for s in scenes):
        next_num += 1
        new_id = f"scene_{next_num}"

    y_offset = 0.06 + ((len(scenes) % 3) * 0.30)
    order_num = len(scenes) + 1
    new_scene = create_scene(
        name=f"Scene {order_num}",
        prompt=f"scene {order_num} content prompt",
        negative_prompt="",
        input_mode="simple",
        area=make_area(0.08, min(0.70, y_offset), 0.84, 0.25),
        order=order_num,
        scene_id=new_id,
    )
    scenes.append(new_scene)
    return new_scene


def simulate_js_delete_scene(scenes: list, index: int):
    """Mirrors the JS btnDeleteScene logic."""
    if len(scenes) <= 1:
        raise ValueError("Min 1 scene required")
    scenes.pop(index)
    for i, s in enumerate(scenes):
        s["order"] = i + 1


class TestM1_1SceneIdUniqueness(unittest.TestCase):
    def test_01_default_document_scene_ids_unique(self):
        """Default 2-scene document has unique scene_ids."""
        doc = create_default_m1_document()
        scenes = doc["pages"][0]["scenes"]
        self.assertEqual(len(scenes), 2)
        ids = [s["scene_id"] for s in scenes]
        self.assertEqual(len(ids), len(set(ids)))
        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [])

    def test_02_add_scenes_sequential_unique_ids(self):
        """Adding scenes sequentially generates unique scene_ids."""
        doc = create_default_m1_document()
        scenes = doc["pages"][0]["scenes"]
        # Add up to 6 scenes
        while len(scenes) < 6:
            simulate_js_add_scene(scenes)

        self.assertEqual(len(scenes), 6)
        ids = [s["scene_id"] for s in scenes]
        self.assertEqual(len(ids), len(set(ids)), f"Collision detected in scene IDs: {ids}")
        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [])

    def test_03_delete_middle_scene_then_add_no_collision(self):
        """Finding G: Deleting middle scene and adding a new scene must not collide with existing IDs."""
        page = create_page(width_px=832, height_px=1216, page_id="page_1")
        # Start with 4 scenes: scene_1, scene_2, scene_3, scene_4
        for i in range(1, 5):
            page["scenes"].append(create_scene(
                name=f"Scene {i}",
                prompt=f"prompt {i}",
                area=make_area(0.1, 0.1 * i, 0.8, 0.2),
                order=i,
                scene_id=f"scene_{i}",
            ))
        doc = create_document(pages=[page])
        scenes = page["scenes"]

        self.assertEqual([s["scene_id"] for s in scenes], ["scene_1", "scene_2", "scene_3", "scene_4"])

        # Delete middle scene (index 1: scene_2)
        simulate_js_delete_scene(scenes, index=1)
        self.assertEqual([s["scene_id"] for s in scenes], ["scene_1", "scene_3", "scene_4"])
        # Orders renumbered to 1, 2, 3
        self.assertEqual([s["order"] for s in scenes], [1, 2, 3])

        # Add new scene: previously with count = 4, would have generated scene_4 which ALREADY EXISTS!
        # With Finding G fix, it must generate a new unique ID (e.g. scene_5).
        new_scene = simulate_js_add_scene(scenes)
        self.assertEqual(new_scene["scene_id"], "scene_5")
        self.assertNotIn(new_scene["scene_id"], ["scene_1", "scene_3", "scene_4"])

        # Check all IDs are strictly unique
        all_ids = [s["scene_id"] for s in scenes]
        self.assertEqual(len(all_ids), len(set(all_ids)))

        # Validation must pass cleanly
        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [])

    def test_04_multiple_delete_and_add_cycles_remain_collision_free(self):
        """Multiple random delete/add cycles maintain strict uniqueness."""
        doc = create_default_m1_document()
        scenes = doc["pages"][0]["scenes"]

        # Add to 4
        simulate_js_add_scene(scenes)
        simulate_js_add_scene(scenes)
        self.assertEqual(len(scenes), 4)

        # Delete scene at index 2, then add, then delete at index 1, then add
        simulate_js_delete_scene(scenes, index=2)
        simulate_js_add_scene(scenes)
        simulate_js_delete_scene(scenes, index=1)
        simulate_js_add_scene(scenes)

        all_ids = [s["scene_id"] for s in scenes]
        self.assertEqual(len(all_ids), len(set(all_ids)), f"Duplicates found: {all_ids}")
        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [])


if __name__ == "__main__":
    unittest.main()
