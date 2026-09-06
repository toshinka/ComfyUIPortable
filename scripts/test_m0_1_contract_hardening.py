"""
test_m0_1_contract_hardening.py — M0.1 Contract Hardening & Boundary Truth Tests
================================================================================
Tests added in M0.1 to verify contract hardening requirements:
1. FK validation on empty collections (Finding A)
2. Duplicate page_id rejection (Finding G)
3. Legacy import validation & orphan character binding fail-closed (Finding B)
4. Legacy export pairing & scene/frame divergence fail-closed (Finding C)
5. Strict reverse coordinate transform rejecting out-of-bounds instances (Finding D)
6. Common effective delta for scene boundary moves preserving relative offsets (Finding E)
7. Scene resize rejecting out-of-bounds instances without individual silent clamp (Finding F)
8. Frame move effective delta boundary behavior (Finding I)
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

def _import_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Import modules with package context
_ac = _import_module(
    "authoring_contract",
    os.path.join(_NODES_DIR, "authoring_contract.py"),
)

pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg
sys.modules["tegaki_manga_nodes.authoring_contract"] = _ac

_mig_spec = importlib.util.spec_from_file_location(
    "tegaki_manga_nodes.authoring_migration",
    os.path.join(_NODES_DIR, "authoring_migration.py"),
    submodule_search_locations=[],
)
_mig = importlib.util.module_from_spec(_mig_spec)
_mig.__package__ = "tegaki_manga_nodes"
sys.modules["tegaki_manga_nodes.authoring_migration"] = _mig
_mig_spec.loader.exec_module(_mig)

_ops_spec = importlib.util.spec_from_file_location(
    "tegaki_manga_nodes.authoring_operations",
    os.path.join(_NODES_DIR, "authoring_operations.py"),
    submodule_search_locations=[],
)
_ops = importlib.util.module_from_spec(_ops_spec)
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

import_from_legacy = _mig.import_from_legacy
export_to_legacy = _mig.export_to_legacy
export_regions_to_legacy = _mig.export_regions_to_legacy
page_normalized_to_koma_local = _mig.page_normalized_to_koma_local

move_scene = _ops.move_scene
resize_scene = _ops.resize_scene
move_frame = _ops.move_frame


class TestM01ForeignKeyValidation(unittest.TestCase):
    """Finding A: Foreign Key Validation on empty collections."""

    def test_instance_rejected_when_cast_collection_empty(self):
        """Character Instance exists, CAST collection empty -> must fail closed."""
        page = create_page(832, 1216, page_id="page_1")
        page["scenes"].append(create_scene(scene_id="scene_a"))
        # 0 CAST entries, instance points to ghost
        page["character_instances"].append(create_character_instance(
            cast_id="ghost_cast",
            scene_id="scene_a",
            instance_id="inst_1",
        ))
        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("ghost_cast" in e and "page cast" in e for e in result.errors),
            f"Expected error for missing cast_id in empty collection, got: {result.errors}"
        )

    def test_instance_rejected_when_scene_collection_empty(self):
        """Character Instance exists, Scene collection empty -> must fail closed."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="cast_alice"))
        # 0 scenes, instance points to ghost
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="ghost_scene",
            instance_id="inst_1",
        ))
        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("ghost_scene" in e and "page scenes" in e for e in result.errors),
            f"Expected error for missing scene_id in empty collection, got: {result.errors}"
        )

    def test_orphan_cast_reference_rejected(self):
        """CAST has Alice, instance references Bob -> must fail."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="cast_alice"))
        page["scenes"].append(create_scene(scene_id="scene_a"))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_bob",
            scene_id="scene_a",
            instance_id="inst_1",
        ))
        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("cast_bob" in e for e in result.errors))

    def test_orphan_scene_reference_rejected(self):
        """Scenes has scene_a, instance references scene_b -> must fail."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="cast_alice"))
        page["scenes"].append(create_scene(scene_id="scene_a"))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_b",
            instance_id="inst_1",
        ))
        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("scene_b" in e for e in result.errors))


class TestM01DuplicatePageId(unittest.TestCase):
    """Finding G: Duplicate page_id detection."""

    def test_duplicate_page_id_rejected(self):
        page1 = create_page(832, 1216, page_id="page_alpha")
        page2 = create_page(832, 1216, page_id="page_alpha")  # duplicate
        doc = create_document(pages=[page1, page2])
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("duplicate page_id" in e and "page_alpha" in e for e in result.errors),
            f"Expected duplicate page_id error, got: {result.errors}"
        )


class TestM01LegacyMigrationValidation(unittest.TestCase):
    """Finding B: Legacy import validation & orphan binding policy."""

    def test_legacy_binding_missing_cast_fails_closed(self):
        """Legacy binding references character not in CAST_SPEC -> valid=False."""
        region_spec = {
            "version": 1,
            "panel_count": 1,
            "regions": [
                {
                    "id": 1,
                    "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
                    "prompt": "scene 1",
                    "characters": [
                        {
                            "character_id": "char_ghost",  # not in cast_spec
                            "enabled": True,
                            "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.6},
                        }
                    ],
                }
            ],
        }
        cast_spec = {
            "version": 1,
            "characters": [
                {"id": "char_alice", "name": "Alice", "enabled": True, "prompt": "1girl"}
            ],
        }
        res = import_from_legacy(region_spec, cast_spec)
        self.assertFalse(res.valid)
        self.assertGreater(len(res.errors), 0)
        self.assertTrue(any("char_ghost" in e for e in res.errors))

    def test_imported_document_validation_result_clean(self):
        """Valid legacy data -> valid=True, errors=[]."""
        region_spec = {
            "version": 1,
            "panel_count": 1,
            "regions": [
                {
                    "id": 1,
                    "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
                    "prompt": "scene 1",
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.6},
                        }
                    ],
                }
            ],
        }
        cast_spec = {
            "version": 1,
            "characters": [
                {"id": "char_alice", "name": "Alice", "enabled": True, "prompt": "1girl"}
            ],
        }
        res = import_from_legacy(region_spec, cast_spec)
        self.assertTrue(res.valid, f"Errors: {res.errors}")
        self.assertEqual(len(res.errors), 0)

    def test_pairing_metadata_created(self):
        """Imported scenes and frames contain pairing metadata."""
        region_spec = {
            "version": 1,
            "panel_count": 1,
            "regions": [
                {"id": 1, "enabled": True, "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
            ],
        }
        cast_spec = {"version": 1, "characters": []}
        res = import_from_legacy(region_spec, cast_spec)
        page = res.document["pages"][0]
        scene = page["scenes"][0]
        frame = page["visual_frames"][0]

        self.assertEqual(scene["metadata"].get("legacy_slot_id"), 1)
        self.assertEqual(scene["metadata"].get("paired_frame_id"), frame["frame_id"])
        self.assertEqual(frame["metadata"].get("legacy_slot_id"), 1)
        self.assertEqual(frame["metadata"].get("paired_scene_id"), scene["scene_id"])


class TestM01LegacyExportScopeAndDivergence(unittest.TestCase):
    """Finding C & D: Scene/Frame divergence and strict coordinate export."""

    def _make_paired_doc(self):
        page = create_page(832, 1216, page_id="page_1")
        page["scenes"].append(create_scene(
            name="S1", area=make_area(0.1, 0.1, 0.8, 0.4),
            scene_id="s1", order=1,
            metadata={"paired_frame_id": "f1"},
        ))
        page["visual_frames"].append(create_visual_frame(
            area=make_area(0.1, 0.1, 0.8, 0.4),
            frame_id="f1", order=1,
            metadata={"paired_scene_id": "s1"},
        ))
        return create_document(pages=[page])

    def test_clean_export_succeeds(self):
        doc = self._make_paired_doc()
        res = export_to_legacy(doc)
        self.assertEqual(len(res.unsupported), 0)
        self.assertIn("regions", res.region_spec)

    def test_scene_frame_diverged_export_fails_closed(self):
        """Scene moved, frame stayed -> export_to_legacy must fail closed."""
        doc = self._make_paired_doc()
        doc["pages"][0]["scenes"][0]["area"] = make_area(0.2, 0.2, 0.7, 0.4)

        res = export_to_legacy(doc)
        self.assertGreater(len(res.unsupported), 0)
        self.assertTrue(
            any("diverged" in u.lower() for u in res.unsupported),
            f"Expected divergence error, got: {res.unsupported}"
        )

    def test_frame_scene_diverged_export_fails_closed(self):
        """Frame moved, scene stayed -> export_to_legacy must fail closed."""
        doc = self._make_paired_doc()
        doc["pages"][0]["visual_frames"][0]["shape"] = make_area(0.1, 0.15, 0.8, 0.4)

        res = export_to_legacy(doc)
        self.assertGreater(len(res.unsupported), 0)
        self.assertTrue(any("diverged" in u.lower() for u in res.unsupported))

    def test_unpaired_frame_count_mismatch_fails_closed(self):
        """2 scenes but 1 frame -> export_to_legacy fails closed."""
        doc = self._make_paired_doc()
        doc["pages"][0]["scenes"].append(create_scene(
            name="S2", area=make_area(0.1, 0.55, 0.8, 0.4),
            scene_id="s2", order=2,
        ))
        res = export_to_legacy(doc)
        self.assertGreater(len(res.unsupported), 0)
        self.assertTrue(any("pairing" in u.lower() or "differs" in u.lower() for u in res.unsupported))

    def test_instance_outside_scene_fails_closed(self):
        """Instance extends outside scene geometry -> export fails closed (no silent clamp)."""
        doc = self._make_paired_doc()
        page = doc["pages"][0]
        page["cast"].append(create_cast_entry(cast_id="alice"))
        # Scene is at [0.1, 0.1, 0.8, 0.4] -> bounds [0.1..0.9, 0.1..0.5]
        # Instance extends to y=0.55 (> 0.5)
        page["character_instances"].append(create_character_instance(
            cast_id="alice",
            scene_id="s1",
            area=make_area(0.2, 0.3, 0.3, 0.25),  # y + h = 0.55 > 0.5!
            instance_id="inst_alice_overflow",
        ))

        res = export_to_legacy(doc)
        self.assertGreater(len(res.unsupported), 0)
        self.assertTrue(
            any("inst_alice_overflow" in u and "extends outside" in u for u in res.unsupported),
            f"Expected out-of-bounds error with instance ID, got: {res.unsupported}"
        )

    def test_semantic_only_export_scope(self):
        """export_regions_to_legacy succeeds even if visual frames are absent."""
        doc = self._make_paired_doc()
        doc["pages"][0]["visual_frames"] = []  # no visual frames

        res = export_regions_to_legacy(doc)
        self.assertEqual(len(res.unsupported), 0)
        self.assertEqual(len(res.region_spec["regions"]), 6)


class TestM01OperationsBoundaryAndResize(unittest.TestCase):
    """Finding E & F: Scene boundary move and resize strictness."""

    def test_scene_move_boundary_uses_common_effective_delta(self):
        """Scene and instance near boundary: common effective delta applied to both."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="alice"))
        # Scene at x=0.6, w=0.3 (right edge at 0.90)
        page["scenes"].append(create_scene(
            name="S1", area=make_area(0.6, 0.1, 0.3, 0.4),
            scene_id="s1",
        ))
        # Instance at x=0.7, w=0.25 (right edge at 0.95 -> max possible dx is +0.05)
        page["character_instances"].append(create_character_instance(
            cast_id="alice", scene_id="s1",
            area=make_area(0.7, 0.15, 0.25, 0.3),
            instance_id="i1",
        ))
        doc = create_document(pages=[page])

        # Request a large dx = +0.2
        moved = move_scene(doc, "page_1", "s1", dx=0.2, dy=0.0)
        m_page = moved["pages"][0]
        m_scene = m_page["scenes"][0]
        m_inst = m_page["character_instances"][0]

        # Limiting rect is instance (0.7 + 0.25 = 0.95 -> max dx is 0.05)
        # Both scene and instance must move by EXACTLY 0.05
        scene_actual_dx = round(m_scene["area"]["x"] - 0.6, 4)
        inst_actual_dx = round(m_inst["area"]["x"] - 0.7, 4)

        self.assertAlmostEqual(scene_actual_dx, 0.05, places=3)
        self.assertAlmostEqual(inst_actual_dx, 0.05, places=3)
        self.assertEqual(scene_actual_dx, inst_actual_dx)

        # Relative offset strictly preserved
        original_offset = round(0.7 - 0.6, 4)
        new_offset = round(m_inst["area"]["x"] - m_scene["area"]["x"], 4)
        self.assertEqual(original_offset, new_offset)

    def test_scene_move_negative_boundary_common_delta(self):
        """Scene at x=0.15, instance at x=0.05 -> request dx = -0.2 -> effective is -0.05."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="alice"))
        page["scenes"].append(create_scene(
            name="S1", area=make_area(0.15, 0.1, 0.4, 0.4),
            scene_id="s1",
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="alice", scene_id="s1",
            area=make_area(0.05, 0.15, 0.2, 0.3),
            instance_id="i1",
        ))
        doc = create_document(pages=[page])

        moved = move_scene(doc, "page_1", "s1", dx=-0.2, dy=0.0)
        m_page = moved["pages"][0]
        m_scene = m_page["scenes"][0]
        m_inst = m_page["character_instances"][0]

        self.assertAlmostEqual(m_scene["area"]["x"], 0.10, places=3)
        self.assertAlmostEqual(m_inst["area"]["x"], 0.00, places=3)

    def test_scene_resize_producing_out_of_bounds_instance_rejected(self):
        """Resize would push instance outside [0, 1] -> ValueError, doc unchanged."""
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="alice"))
        # Scene at x=0.1, w=0.5. Instance at x=0.45, w=0.2 (rel_x = 0.7, rel_w = 0.4, overhangs right)
        page["scenes"].append(create_scene(
            name="S1", area=make_area(0.1, 0.1, 0.5, 0.5),
            scene_id="s1",
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="alice", scene_id="s1",
            area=make_area(0.45, 0.1, 0.2, 0.2),
            instance_id="i1",
        ))
        doc = create_document(pages=[page])

        # New scene area is valid (x=0.5, w=0.5 -> right edge = 1.0), but
        # instance becomes x = 0.5 + 0.7*0.5 = 0.85, w = 0.2 -> x+w = 1.05 > 1.0!
        valid_scene_area = make_area(0.5, 0.1, 0.5, 0.5)

        with self.assertRaises(ValueError) as cm:
            resize_scene(doc, "page_1", "s1", valid_scene_area)
        self.assertIn("out of page bounds", str(cm.exception))

        # Document unchanged
        self.assertEqual(doc["pages"][0]["scenes"][0]["area"]["x"], 0.1)

    def test_frame_move_bounded_by_effective_delta(self):
        """Frame moved near edge clamps to page bounds via effective delta."""
        page = create_page(832, 1216, page_id="page_1")
        page["visual_frames"].append(create_visual_frame(
            area=make_area(0.8, 0.1, 0.15, 0.5),
            frame_id="f1",
        ))
        doc = create_document(pages=[page])

        # Request dx = +0.2 -> max possible is 1.0 - (0.8 + 0.15) = 0.05
        moved = move_frame(doc, "page_1", "f1", dx=0.2, dy=0.0)
        m_shape = moved["pages"][0]["visual_frames"][0]["shape"]
        self.assertAlmostEqual(m_shape["x"], 0.85, places=3)
        self.assertAlmostEqual(m_shape["x"] + m_shape["w"], 1.00, places=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
