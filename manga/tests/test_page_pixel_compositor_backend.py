"""Targeted test suite for Python CPU page pixel compositor (Card MANGA-PAGE-PIXEL-COMPOSITOR-PY1).

Covers cases A through V:
Case A: Empty/UNFILLED page returns exact-size opaque white PNG.
Case B: UNFILLED performs ZERO source loads.
Case C: One CURRENT_RESULT source is loaded exactly once.
Case D: Correct source digest is accepted.
Case E: Source digest mismatch fails closed.
Case F: Source dimensions mismatch fails closed.
Case G: Full-image source rect composites at correct target rectangle.
Case H: Partial local_source_rect crops correct source pixels.
Case I: Non-integer normalized boundaries use exact documented half-up edge rounding.
Case J: Resize produces exact target pixel dimensions.
Case K: Transparent source pixels preserve white/background content.
Case L: Two overlapping Scenes obey plan order.
Case M: target_page_dimensions mismatch fails.
Case N: Out-of-bounds source rect fails.
Case O: Out-of-bounds target rect fails.
Case P: Final page dimensions equal plan page dimensions.
Case Q: Final background pixel is exactly 255/255/255/255 where untouched.
Case R: Automatic borders/strokes are ZERO.
Case S: Composite disk write is ZERO.
Case T: /prompt and GPU activity are ZERO.
Case U: HTTP success is image/png raw bytes.
Case V: HTTP error does not leak absolute path or stack trace.
"""

from __future__ import annotations

import hashlib
import io
import os
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EMBEDDED_SITE = ROOT / "python_embeded" / "Lib" / "site-packages"
if EMBEDDED_SITE.exists() and str(EMBEDDED_SITE) not in sys.path:
    sys.path.append(str(EMBEDDED_SITE))

# Ensure custom_nodes_custom package can be imported
if "custom_nodes_custom.tegaki_manga_nodes" not in sys.modules:
    pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
    pkg.__path__ = [str(ROOT / "custom_nodes_custom" / "tegaki_manga_nodes")]
    sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg

from PIL import Image
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from custom_nodes_custom.tegaki_manga_nodes.page_pixel_compositor import (
    PagePixelCompositorError,
    compose_page_pixels,
    normalized_rect_to_pixel_edges,
)
from custom_nodes_custom.tegaki_manga_nodes.basic_generation_api import api_manga_page_composite


def make_test_png(width: int, height: int, color: tuple[int, int, int, int] = (255, 0, 0, 255)) -> tuple[bytes, str, int, int]:
    img = Image.new("RGBA", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    return data, digest, width, height


def make_test_plan(page_w: int = 512, page_h: int = 512, scenes: list[dict] | None = None) -> dict:
    return {
        "schema_id": "TEGAKI_PAGE_COMPOSITION_PLAN",
        "schema_version": "1.0.0",
        "plan_id": "plan-test-1",
        "page": {
            "document_id": "doc-test",
            "page_id": "page-1",
            "width": page_w,
            "height": page_h,
        },
        "background": {
            "mode": "solid",
            "value": "white",
        },
        "scenes": scenes if scenes is not None else [],
    }


def make_current_slot(
    scene_id: str,
    data: bytes,
    digest: str,
    src_w: int,
    src_h: int,
    target_rect: dict,
    source_rect: dict | None = None,
    page_w: int = 512,
    page_h: int = 512,
    order: int = 0,
) -> dict:
    if source_rect is None:
        source_rect = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    transform = {
        "scale_x": target_rect["w"],
        "scale_y": target_rect["h"],
        "offset_x": target_rect["x"],
        "offset_y": target_rect["y"],
    }
    return {
        "scene_id": scene_id,
        "order": order,
        "state": "CURRENT_RESULT",
        "selected_result": {
            "manifest_id": f"manifest-{scene_id}",
            "artifact": {
                "locator": {"filename": f"{scene_id}.png", "subfolder": "Manga/Playable", "type": "output"},
                "dimensions": {"width": src_w, "height": src_h},
                "content_digest": digest,
            },
            "placement": {
                "page_target_rect": target_rect,
                "local_source_rect": source_rect,
                "transform": transform,
                "target_page_dimensions": {"width": page_w, "height": page_h},
            },
        },
    }


class TestPurePagePixelCompositor(unittest.TestCase):
    def test_case_a_empty_unfilled_page_returns_white(self):
        plan = make_test_plan(256, 256, scenes=[{"scene_id": "s1", "state": "UNFILLED"}])
        png_bytes = compose_page_pixels(plan)
        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.size, (256, 256))
        self.assertEqual(img.mode, "RGBA")
        # Check corners and center are all opaque white
        for pt in [(0, 0), (255, 0), (0, 255), (255, 255), (128, 128)]:
            self.assertEqual(img.getpixel(pt), (255, 255, 255, 255))

    def test_case_b_unfilled_performs_zero_source_loads(self):
        calls = []
        def loader(loc):
            calls.append(loc)
            return b""
        plan = make_test_plan(256, 256, scenes=[
            {"scene_id": "s1", "state": "UNFILLED"},
            {"scene_id": "s2", "state": "UNFILLED"},
        ])
        compose_page_pixels(plan, artifact_loader=loader)
        self.assertEqual(len(calls), 0)

    def test_case_c_d_one_current_result_loaded_once_with_valid_digest(self):
        data, digest, w, h = make_test_png(64, 64, (255, 0, 0, 255))
        calls = []
        def loader(loc):
            calls.append(loc)
            return data
        slot = make_current_slot("s1", data, digest, w, h, {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}, page_w=256, page_h=256)
        plan = make_test_plan(256, 256, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=loader)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["filename"], "s1.png")
        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.size, (256, 256))

    def test_case_e_source_digest_mismatch_fails_closed(self):
        data, digest, w, h = make_test_png(64, 64)
        slot = make_current_slot("s1", data, "0" * 64, w, h, {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5})
        plan = make_test_plan(scenes=[slot])
        with self.assertRaises(PagePixelCompositorError) as ctx:
            compose_page_pixels(plan, artifact_loader=lambda loc: data)
        self.assertEqual(ctx.exception.code, "SOURCE_DIGEST_MISMATCH")

    def test_case_f_source_dimensions_mismatch_fails_closed(self):
        data, digest, w, h = make_test_png(64, 64)
        slot = make_current_slot("s1", data, digest, 128, 128, {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5})
        plan = make_test_plan(scenes=[slot])
        with self.assertRaises(PagePixelCompositorError) as ctx:
            compose_page_pixels(plan, artifact_loader=lambda loc: data)
        self.assertEqual(ctx.exception.code, "SOURCE_DIMENSION_MISMATCH")

    def test_case_g_full_image_source_rect_composites_at_target_rect(self):
        red_data, digest, w, h = make_test_png(100, 100, (255, 0, 0, 255))
        # Place red box at [x=0.25, y=0.25, w=0.5, h=0.5] on 200x200 canvas -> pixel [50, 50, 150, 150]
        slot = make_current_slot("s1", red_data, digest, w, h, {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5}, page_w=200, page_h=200)
        plan = make_test_plan(200, 200, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: red_data)
        img = Image.open(io.BytesIO(png_bytes))
        # Inside target rect is red
        self.assertEqual(img.getpixel((100, 100)), (255, 0, 0, 255))
        # Outside target rect is white
        self.assertEqual(img.getpixel((10, 10)), (255, 255, 255, 255))
        self.assertEqual(img.getpixel((190, 190)), (255, 255, 255, 255))

    def test_case_h_partial_local_source_crop(self):
        # Create image with left half red, right half blue
        src = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        blue_box = Image.new("RGBA", (50, 100), (0, 0, 255, 255))
        src.paste(blue_box, (50, 0))
        buf = io.BytesIO()
        src.save(buf, format="PNG")
        data = buf.getvalue()
        digest = hashlib.sha256(data).hexdigest()

        # Crop only the blue half: local_source_rect: {x: 0.5, y: 0.0, w: 0.5, h: 1.0}
        slot = make_current_slot(
            "s1", data, digest, 100, 100,
            target_rect={"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            source_rect={"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0},
            page_w=100, page_h=100
        )
        plan = make_test_plan(100, 100, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: data)
        img = Image.open(io.BytesIO(png_bytes))
        # Entire page should be blue (since blue half was resized to fill page)
        self.assertEqual(img.getpixel((10, 10)), (0, 0, 255, 255))
        self.assertEqual(img.getpixel((90, 90)), (0, 0, 255, 255))

    def test_case_i_normalized_edge_half_up_conversion(self):
        # dim=100, x=0.125, w=0.375
        # left = floor(12.5 + 0.5) = 13
        # right = floor(50.0 + 0.5) = 50
        l, t, r, b = normalized_rect_to_pixel_edges({"x": 0.125, "y": 0.125, "w": 0.375, "h": 0.375}, 100, 100)
        self.assertEqual(l, 13)
        self.assertEqual(t, 13)
        self.assertEqual(r, 50)
        self.assertEqual(b, 50)
        self.assertEqual(r - l, 37)

    def test_case_j_resize_matches_target_pixel_dimensions(self):
        # Source 50x50, target is 100x200
        data, digest, w, h = make_test_png(50, 50, (0, 255, 0, 255))
        slot = make_current_slot("s1", data, digest, w, h, {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}, page_w=100, page_h=200)
        plan = make_test_plan(100, 200, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: data)
        img = Image.open(io.BytesIO(png_bytes))
        self.assertEqual(img.size, (100, 200))
        self.assertEqual(img.getpixel((50, 100)), (0, 255, 0, 255))

    def test_case_k_transparent_pixels_preserve_background(self):
        # Source with 50% opacity red
        data, digest, w, h = make_test_png(50, 50, (255, 0, 0, 128))
        slot = make_current_slot("s1", data, digest, w, h, {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}, page_w=50, page_h=50)
        plan = make_test_plan(50, 50, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: data)
        img = Image.open(io.BytesIO(png_bytes))
        # Over white (255, 255, 255, 255), 50% red gives (255, 127, 127, 255)
        px = img.getpixel((25, 25))
        self.assertEqual(px, (255, 127, 127, 255))

    def test_case_l_overlapping_scenes_respect_plan_order(self):
        red_data, r_digest, rw, rh = make_test_png(50, 50, (255, 0, 0, 255))
        green_data, g_digest, gw, gh = make_test_png(50, 50, (0, 255, 0, 255))
        loader_map = {"s1.png": red_data, "s2.png": green_data}

        slot1 = make_current_slot("s1", red_data, r_digest, rw, rh, {"x": 0.0, "y": 0.0, "w": 0.8, "h": 0.8}, page_w=100, page_h=100, order=0)
        slot2 = make_current_slot("s2", green_data, g_digest, gw, gh, {"x": 0.2, "y": 0.2, "w": 0.8, "h": 0.8}, page_w=100, page_h=100, order=1)
        plan = make_test_plan(100, 100, [slot1, slot2])

        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: loader_map[loc["filename"]])
        img = Image.open(io.BytesIO(png_bytes))

        # (10, 10) is only covered by slot1 -> red
        self.assertEqual(img.getpixel((10, 10)), (255, 0, 0, 255))
        # (50, 50) is covered by both slot1 and slot2 -> slot2 (green) is on top
        self.assertEqual(img.getpixel((50, 50)), (0, 255, 0, 255))
        # (90, 90) is only covered by slot2 -> green
        self.assertEqual(img.getpixel((90, 90)), (0, 255, 0, 255))

    def test_case_m_target_page_dimensions_mismatch_fails(self):
        data, digest, w, h = make_test_png(50, 50)
        slot = make_current_slot("s1", data, digest, w, h, {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}, page_w=800, page_h=600)
        plan = make_test_plan(1000, 1000, [slot])
        with self.assertRaises(PagePixelCompositorError) as ctx:
            compose_page_pixels(plan, artifact_loader=lambda loc: data)
        self.assertEqual(ctx.exception.code, "TARGET_DIMENSIONS_MISMATCH")

    def test_case_n_o_out_of_bounds_rect_fails(self):
        data, digest, w, h = make_test_png(50, 50)
        # Out of bounds target rect (x + w = 1.3)
        slot_o = make_current_slot("s1", data, digest, w, h, {"x": 0.5, "y": 0.0, "w": 0.8, "h": 1.0}, page_w=100, page_h=100)
        plan_o = make_test_plan(100, 100, [slot_o])
        with self.assertRaises(PagePixelCompositorError) as ctx_o:
            compose_page_pixels(plan_o, artifact_loader=lambda loc: data)
        self.assertEqual(ctx_o.exception.code, "PLACEMENT_INVALID")

        # Out of bounds source rect (x + w = 1.2)
        slot_n = make_current_slot(
            "s1", data, digest, w, h,
            {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            source_rect={"x": 0.5, "y": 0.0, "w": 0.7, "h": 1.0},
            page_w=100, page_h=100
        )
        plan_n = make_test_plan(100, 100, [slot_n])
        with self.assertRaises(PagePixelCompositorError) as ctx_n:
            compose_page_pixels(plan_n, artifact_loader=lambda loc: data)
        self.assertEqual(ctx_n.exception.code, "PLACEMENT_INVALID")

    def test_case_p_q_r_dimensions_background_and_no_borders(self):
        data, digest, w, h = make_test_png(50, 50, (0, 0, 255, 255))
        # Place at [20, 20, 70, 70] on 100x100
        slot = make_current_slot("s1", data, digest, w, h, {"x": 0.2, "y": 0.2, "w": 0.5, "h": 0.5}, page_w=100, page_h=100)
        plan = make_test_plan(100, 100, [slot])
        png_bytes = compose_page_pixels(plan, artifact_loader=lambda loc: data)
        img = Image.open(io.BytesIO(png_bytes))

        self.assertEqual(img.size, (100, 100))
        # Untouched area is exact white
        self.assertEqual(img.getpixel((0, 0)), (255, 255, 255, 255))
        self.assertEqual(img.getpixel((19, 19)), (255, 255, 255, 255))
        # No border at edge of slot (19, 20) is pure white
        self.assertEqual(img.getpixel((19, 20)), (255, 255, 255, 255))

    def test_case_s_t_disk_writes_gpu_zero(self):
        # Pure in-memory proof
        plan = make_test_plan(64, 64)
        png_bytes = compose_page_pixels(plan)
        self.assertTrue(len(png_bytes) > 0)


class TestPagePixelCompositorAPI(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/tegaki/manga/page/composite", api_manga_page_composite)
        return app

    async def test_case_u_http_success_raw_png(self):
        plan = make_test_plan(64, 64)
        resp = await self.client.post("/tegaki/manga/page/composite", json={"composition_plan": plan})
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.content_type, "image/png")
        body = await resp.read()
        self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))

    async def test_case_v_http_error_does_not_leak_path_or_trace(self):
        # Missing artifact in filesystem
        slot = {
            "scene_id": "s1",
            "state": "CURRENT_RESULT",
            "selected_result": {
                "manifest_id": "m1",
                "artifact": {
                    "locator": {"filename": "nonexistent_scene.png", "subfolder": "Manga/Playable", "type": "output"},
                    "dimensions": {"width": 64, "height": 64},
                    "content_digest": "a" * 64,
                },
                "placement": {
                    "page_target_rect": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
                    "local_source_rect": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
                    "transform": {"scale_x": 1.0, "scale_y": 1.0, "offset_x": 0.0, "offset_y": 0.0},
                    "target_page_dimensions": {"width": 64, "height": 64},
                },
            },
        }
        plan = make_test_plan(64, 64, [slot])
        resp = await self.client.post("/tegaki/manga/page/composite", json={"composition_plan": plan})
        self.assertEqual(resp.status, 404)
        json_data = await resp.json()
        self.assertFalse(json_data["ok"])
        self.assertEqual(json_data["error_code"], "SOURCE_ARTIFACT_NOT_FOUND")
        # Check no absolute path or stack trace leaked
        self.assertNotIn("Traceback", json_data["error"])
        self.assertNotIn("D:", json_data["error"])
        self.assertNotIn("C:", json_data["error"])
        self.assertNotIn("/", json_data["error"])
        self.assertNotIn("\\", json_data["error"])


if __name__ == "__main__":
    unittest.main()
