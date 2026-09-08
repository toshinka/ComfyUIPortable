import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    map_history_state,
    map_queue_state,
    parse_backend_status,
)


class H1AServerMappingTests(unittest.TestCase):
    def test_backend_status_parsing(self):
        parsed = parse_backend_status(
            {"devices": [{"vram_total": 120, "vram_free": 45}]},
            {"queue_pending": [["pending-id"]], "queue_running": [["running-id"]]},
        )
        self.assertEqual(parsed["state"], "READY")
        self.assertEqual(parsed["queue_count"], 2)
        self.assertEqual(parsed["running_count"], 1)
        self.assertEqual(parsed["vram_total"], 120)
        self.assertEqual(parsed["vram_free"], 45)

    def test_queue_state_mapping(self):
        self.assertEqual(
            map_queue_state({"queue_pending": [["p-1"]]}, "p-1"),
            "QUEUED",
        )
        self.assertEqual(
            map_queue_state({"queue_running": [["p-1"]]}, "p-1"),
            "RUNNING",
        )
        self.assertEqual(
            map_queue_state({}, "p-1", cancel_requested=True),
            "CANCELLED",
        )
        self.assertEqual(map_queue_state({}, "p-1", previous_state="RUNNING"), "RUNNING")

    def test_history_state_mapping(self):
        self.assertEqual(map_history_state(None), "FAILED")
        self.assertEqual(
            map_history_state({"status": {"status_str": "error"}}),
            "FAILED",
        )
        self.assertEqual(
            map_history_state({"status": {"status_str": "error"}}, cancel_requested=True),
            "CANCELLED",
        )
        self.assertEqual(
            map_history_state({"status": {"completed": True}}),
            "COMPLETED",
        )
        self.assertEqual(map_history_state({"status": {}}), "RUNNING")


if __name__ == "__main__":
    unittest.main()
