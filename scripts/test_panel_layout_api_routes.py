import os
import sys
import json
import unittest
import asyncio

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.panel_layout_api import api_panel_layout_split, api_panel_layout_validate


class DummyRequest:
    def __init__(self, data):
        self._data = data

    async def json(self):
        return self._data


class TestPanelLayoutApiRoutes(unittest.TestCase):
    """
    Phase 3C.1.2: Panel Layout REST API Route Tests
    /tegaki/panel-layout/split および /validate の HTTP ハンドラを直接テストする。
    """

    def setUp(self):
        self.spec = get_default_panel_layout_spec(preset="3_basic")

    def test_01_api_split_success(self):
        """有効な Split リクエストで 200 OK と Canonical Spec が返ること"""
        req = DummyRequest({
            "spec": self.spec,
            "panel_id": "p1",
            "split_mode": "horizontal",
            "split_ratio": 0.5
        })
        resp = asyncio.run(api_panel_layout_split(req))
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.text)
        self.assertTrue(body["ok"])
        self.assertEqual(len(body["spec"]["panels"]), 4)
        self.assertEqual(body["topology_summary"]["status"], "VALID")

    def test_02_api_split_missing_params(self):
        """必須フィールド欠落で 400 Bad Request が返ること"""
        req = DummyRequest({"spec": self.spec})  # panel_id missing
        resp = asyncio.run(api_panel_layout_split(req))
        self.assertEqual(resp.status, 400)
        body = json.loads(resp.text)
        self.assertFalse(body["ok"])
        self.assertIn("Missing required fields", body["error"])

    def test_03_api_split_invalid_spec_rejection(self):
        """不正な Spec (自己交差など) で 400 Bad Request が返ること"""
        bad_spec = json.loads(json.dumps(self.spec))
        bad_spec["vertices"][0]["x"] = 0.01  # frame 外
        req = DummyRequest({
            "spec": bad_spec,
            "panel_id": "p1",
            "split_mode": "horizontal"
        })
        resp = asyncio.run(api_panel_layout_split(req))
        self.assertEqual(resp.status, 400)
        body = json.loads(resp.text)
        self.assertFalse(body["ok"])
        self.assertIn("outside the Layout Frame", body["error"])

    def test_04_api_validate_success(self):
        """有効な Spec で 200 OK と topology_summary が返ること"""
        req = DummyRequest({"spec": self.spec})
        resp = asyncio.run(api_panel_layout_validate(req))
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.text)
        self.assertTrue(body["ok"])
        self.assertEqual(body["topology_summary"]["status"], "VALID")

    def test_05_api_validate_failure(self):
        """不正な Spec で 400 Bad Request が返ること"""
        bad_spec = json.loads(json.dumps(self.spec))
        bad_spec["frame"]["w"] = -0.5
        req = DummyRequest({"spec": bad_spec})
        resp = asyncio.run(api_panel_layout_validate(req))
        self.assertEqual(resp.status, 400)
        body = json.loads(resp.text)
        self.assertFalse(body["ok"])
        self.assertIn("Dimensions must be positive", body["error"])


if __name__ == "__main__":
    print("================================================================================")
    print("Running Panel Layout API Routes Unit Tests (Phase 3C.1.2)")
    print("================================================================================")
    unittest.main(verbosity=2)
