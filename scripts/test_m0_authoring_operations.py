"""
test_m0_authoring_operations.py — M0 Authoring Operations Fixtures 5-8
=======================================================================
Pure Python tests. No ComfyUI server required.
"""
import sys
import os
import json
import copy
import unittest
import importlib.util

_NODES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "custom_nodes_custom", "tegaki_manga_nodes",
))

def _import_module(name, filepath, parent_package=None):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Import authoring_contract first (dependency of operations)
_ac = _import_module(
    "authoring_contract",
    os.path.join(_NODES_DIR, "authoring_contract.py"),
)

# Patch the relative import that authoring_operations expects
pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg
sys.modules["tegaki_manga_nodes.authoring_contract"] = _ac

# Now import authoring_operations with the patched parent
_ops_spec = importlib.util.spec_from_file_location(
    "tegaki_manga_nodes.authoring_operations",
    os.path.join(_NODES_DIR, "authoring_operations.py"),
    submodule_search_locations=[],
)
_ops = importlib.util.module_from_spec(_ops_spec)
# Patch relative import resolution
_ops.__package__ = "tegaki_manga_nodes"
sys.modules["tegaki_manga_nodes.authoring_operations"] = _ops
_ops_spec.loader.exec_module(_ops)

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_visual_frame = _ac.create_visual_frame
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
validate_document = _ac.validate_document

move_scene = _ops.move_scene
resize_scene = _ops.resize_scene
move_frame = _ops.move_frame
change_resolution = _ops.change_resolution
duplicate_scene = _ops.duplicate_scene


def _build_test_doc():
    """Build a document with 2 scenes, 2 frames, 1 cast, 2 instances."""
    page = create_page(832, 1216, page_id="page_1")

    page["cast"].append(create_cast_entry(
        display_name="Alice", cast_id="alice",
    ))

    # Scene A (left side)
    page["scenes"].append(create_scene(
        name="Scene A", prompt="classroom",
        area=make_area(0.0, 0.0, 0.5, 0.5),
        order=1, scene_id="scene_a", input_mode="cast",
    ))
    # Scene B (right side)
    page["scenes"].append(create_scene(
        name="Scene B", prompt="hallway",
        area=make_area(0.5, 0.0, 0.5, 0.5),
        order=2, scene_id="scene_b", input_mode="cast",
    ))

    # Frame 1 (top half)
    page["visual_frames"].append(create_visual_frame(
        area=make_area(0.0, 0.0, 1.0, 0.5),
        order=1, frame_id="frame_1",
    ))
    # Frame 2 (bottom half)
    page["visual_frames"].append(create_visual_frame(
        area=make_area(0.0, 0.5, 1.0, 0.5),
        order=2, frame_id="frame_2",
    ))

    # Alice in Scene A
    page["character_instances"].append(create_character_instance(
        cast_id="alice", scene_id="scene_a",
        area=make_area(0.05, 0.05, 0.2, 0.4),
        acting_prompt="standing left",
        instance_id="inst_a1",
    ))
    # Alice in Scene B
    page["character_instances"].append(create_character_instance(
        cast_id="alice", scene_id="scene_b",
        area=make_area(0.55, 0.05, 0.2, 0.4),
        acting_prompt="standing right",
        instance_id="inst_b1",
    ))

    return create_document(pages=[page])


class TestFixture5_ResolutionChange(unittest.TestCase):
    """Fixture 5: Resolution change preserves normalized areas."""

    def test_resolution_832x1216_to_1216x832(self):
        doc = _build_test_doc()
        original_area = doc["pages"][0]["scenes"][0]["area"].copy()

        new_doc = change_resolution(doc, "page_1", 1216, 832)

        # Resolution updated
        page = new_doc["pages"][0]
        self.assertEqual(page["width_px"], 1216)
        self.assertEqual(page["height_px"], 832)

        # Normalized areas unchanged
        self.assertAlmostEqual(page["scenes"][0]["area"]["x"], original_area["x"])
        self.assertAlmostEqual(page["scenes"][0]["area"]["y"], original_area["y"])
        self.assertAlmostEqual(page["scenes"][0]["area"]["w"], original_area["w"])
        self.assertAlmostEqual(page["scenes"][0]["area"]["h"], original_area["h"])

        # Instances also unchanged
        inst_area = page["character_instances"][0]["area"]
        self.assertAlmostEqual(inst_area["x"], 0.05)
        self.assertAlmostEqual(inst_area["y"], 0.05)

        # Frame areas unchanged
        frame_area = page["visual_frames"][0]["shape"]
        self.assertAlmostEqual(frame_area["w"], 1.0)

    def test_original_not_mutated(self):
        doc = _build_test_doc()
        original_width = doc["pages"][0]["width_px"]
        change_resolution(doc, "page_1", 1216, 832)
        self.assertEqual(doc["pages"][0]["width_px"], original_width)


class TestFixture6_SceneMove(unittest.TestCase):
    """Fixture 6: Scene move — instances follow, others unchanged."""

    def test_scene_move_basic(self):
        doc = _build_test_doc()
        dx, dy = 0.1, 0.2

        new_doc = move_scene(doc, "page_1", "scene_a", dx, dy)
        page = new_doc["pages"][0]

        # Scene A moved
        scene_a = next(s for s in page["scenes"] if s["scene_id"] == "scene_a")
        self.assertAlmostEqual(scene_a["area"]["x"], 0.0 + dx, places=3)
        self.assertAlmostEqual(scene_a["area"]["y"], 0.0 + dy, places=3)

        # Instance in Scene A follows same delta
        inst_a1 = next(i for i in page["character_instances"]
                       if i["instance_id"] == "inst_a1")
        self.assertAlmostEqual(inst_a1["area"]["x"], 0.05 + dx, places=3)
        self.assertAlmostEqual(inst_a1["area"]["y"], 0.05 + dy, places=3)

    def test_other_scene_unchanged(self):
        doc = _build_test_doc()
        new_doc = move_scene(doc, "page_1", "scene_a", 0.1, 0.2)
        page = new_doc["pages"][0]

        # Scene B unchanged
        scene_b = next(s for s in page["scenes"] if s["scene_id"] == "scene_b")
        self.assertAlmostEqual(scene_b["area"]["x"], 0.5, places=3)
        self.assertAlmostEqual(scene_b["area"]["y"], 0.0, places=3)

        # Instance in Scene B unchanged
        inst_b1 = next(i for i in page["character_instances"]
                       if i["instance_id"] == "inst_b1")
        self.assertAlmostEqual(inst_b1["area"]["x"], 0.55, places=3)

    def test_frames_unchanged(self):
        doc = _build_test_doc()
        new_doc = move_scene(doc, "page_1", "scene_a", 0.1, 0.2)
        page = new_doc["pages"][0]

        # Frames unchanged
        frame_1 = next(f for f in page["visual_frames"]
                       if f["frame_id"] == "frame_1")
        self.assertAlmostEqual(frame_1["shape"]["x"], 0.0, places=3)
        self.assertAlmostEqual(frame_1["shape"]["y"], 0.0, places=3)

    def test_original_not_mutated(self):
        doc = _build_test_doc()
        orig_x = doc["pages"][0]["scenes"][0]["area"]["x"]
        move_scene(doc, "page_1", "scene_a", 0.1, 0.2)
        self.assertAlmostEqual(doc["pages"][0]["scenes"][0]["area"]["x"], orig_x)


class TestFixture7_SceneResize(unittest.TestCase):
    """Fixture 7: Scene resize — instances proportionally transform."""

    def test_scene_resize_proportional(self):
        doc = _build_test_doc()

        # Scene A: {0.0, 0.0, 0.5, 0.5}
        # Instance inst_a1: {0.05, 0.05, 0.2, 0.4}
        # Relative to scene: (0.05/0.5, 0.05/0.5, 0.2/0.5, 0.4/0.5) = (0.1, 0.1, 0.4, 0.8)

        new_area = make_area(0.1, 0.1, 0.8, 0.8)
        new_doc = resize_scene(doc, "page_1", "scene_a", new_area)
        page = new_doc["pages"][0]

        scene_a = next(s for s in page["scenes"] if s["scene_id"] == "scene_a")
        self.assertAlmostEqual(scene_a["area"]["x"], 0.1, places=3)
        self.assertAlmostEqual(scene_a["area"]["w"], 0.8, places=3)

        # Instance should be proportionally transformed
        # new_x = 0.1 + 0.1 * 0.8 = 0.18
        # new_y = 0.1 + 0.1 * 0.8 = 0.18
        # new_w = 0.4 * 0.8 = 0.32
        # new_h = 0.8 * 0.8 = 0.64
        inst_a1 = next(i for i in page["character_instances"]
                       if i["instance_id"] == "inst_a1")
        self.assertAlmostEqual(inst_a1["area"]["x"], 0.18, places=2)
        self.assertAlmostEqual(inst_a1["area"]["y"], 0.18, places=2)
        self.assertAlmostEqual(inst_a1["area"]["w"], 0.32, places=2)
        self.assertAlmostEqual(inst_a1["area"]["h"], 0.64, places=2)


class TestFixture8_FrameMove(unittest.TestCase):
    """Fixture 8: Frame move — scenes and instances unchanged (independence)."""

    def test_frame_move_independence(self):
        doc = _build_test_doc()
        dx, dy = 0.0, 0.1

        new_doc = move_frame(doc, "page_1", "frame_1", dx, dy)
        page = new_doc["pages"][0]

        # Frame moved
        frame_1 = next(f for f in page["visual_frames"]
                       if f["frame_id"] == "frame_1")
        self.assertAlmostEqual(frame_1["shape"]["y"], 0.0 + dy, places=3)

        # Scene A unchanged
        scene_a = next(s for s in page["scenes"] if s["scene_id"] == "scene_a")
        self.assertAlmostEqual(scene_a["area"]["x"], 0.0, places=3)
        self.assertAlmostEqual(scene_a["area"]["y"], 0.0, places=3)

        # Instance unchanged
        inst_a1 = next(i for i in page["character_instances"]
                       if i["instance_id"] == "inst_a1")
        self.assertAlmostEqual(inst_a1["area"]["x"], 0.05, places=3)
        self.assertAlmostEqual(inst_a1["area"]["y"], 0.05, places=3)

    def test_original_not_mutated(self):
        doc = _build_test_doc()
        orig_y = doc["pages"][0]["visual_frames"][0]["shape"]["y"]
        move_frame(doc, "page_1", "frame_1", 0.0, 0.1)
        self.assertAlmostEqual(
            doc["pages"][0]["visual_frames"][0]["shape"]["y"], orig_y
        )


class TestDuplicateScene(unittest.TestCase):
    """Verify scene duplication creates new IDs."""

    def test_duplicate_creates_new_ids(self):
        doc = _build_test_doc()
        new_doc = duplicate_scene(doc, "page_1", "scene_a")
        page = new_doc["pages"][0]

        # Should have 3 scenes now
        self.assertEqual(len(page["scenes"]), 3)

        # Original scene_a still exists
        scene_ids = [s["scene_id"] for s in page["scenes"]]
        self.assertIn("scene_a", scene_ids)

        # New scene has different ID
        new_scene = page["scenes"][2]
        self.assertNotEqual(new_scene["scene_id"], "scene_a")
        self.assertIn("(copy)", new_scene["name"])

        # New instance with new ID
        self.assertEqual(len(page["character_instances"]), 3)
        new_inst = page["character_instances"][2]
        self.assertNotEqual(new_inst["instance_id"], "inst_a1")
        self.assertEqual(new_inst["scene_id"], new_scene["scene_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
