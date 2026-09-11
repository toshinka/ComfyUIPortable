from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    H1ASession,
    ReferenceRequestError,
)


class FakeBackend:
    def submit(self, graph, client_id):
        self.graph = graph
        return {"prompt_id": "h1b1-fake-prompt"}


def image_bytes(image_format: str, color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (64, 48), color)
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


class H1B1ServerTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def test_start_and_end_assets_share_security_and_are_independent(self):
        session = self.new_session()
        start = session.upload_reference("start.png", image_bytes("PNG", (200, 30, 30)), role="start_frame")
        end = session.upload_reference("end.jpg", image_bytes("JPEG", (30, 30, 200)), role="end_frame")
        self.assertEqual(start.reference.role, "start_frame")
        self.assertEqual(end.reference.role, "end_frame")
        self.assertNotEqual(start.reference.id, end.reference.id)
        with self.assertRaises(ReferenceRequestError):
            session.upload_reference("bad.png", image_bytes("PNG", (1, 2, 3)), role="identity")

    def test_canonical_start_only_compiles_fl2va_and_history_metadata(self):
        session = self.new_session()
        start = session.upload_reference("start.png", image_bytes("PNG", (200, 30, 30)), role="start_frame")
        job = session.submit(
            {
                "prompt": "start only",
                "references": {
                    "start_frame": {"id": start.reference.id, "role": "start_frame"},
                    "end_frame": None,
                },
            }
        )
        self.assertEqual(job.route, "native_i2v")
        self.assertEqual(job.public()["route_label"], "Start Frame")
        self.assertTrue(job.public()["has_start_frame"])
        self.assertFalse(job.public()["has_end_frame"])
        self.assertEqual(session.backend.graph["131"]["inputs"]["first_frame"], ["134", 0])
        self.assertEqual(session.backend.graph["134"]["inputs"]["image"], ["132", 0])
        self.assertEqual(session.backend.graph["134"]["inputs"]["crop"], "center")
        self.assertNotIn("last_frame", session.backend.graph["131"]["inputs"])
        self.assertNotIn("133", session.backend.graph)

    def test_canonical_end_only_compiles_last_frame(self):
        session = self.new_session()
        end = session.upload_reference("end.jpg", image_bytes("JPEG", (30, 30, 200)), role="end_frame")
        job = session.submit(
            {
                "prompt": "end only",
                "references": {
                    "start_frame": None,
                    "end_frame": {"id": end.reference.id, "role": "end_frame"},
                },
            }
        )
        self.assertEqual(job.public()["route_label"], "End Frame")
        self.assertFalse(job.public()["has_start_frame"])
        self.assertTrue(job.public()["has_end_frame"])
        self.assertNotIn("first_frame", session.backend.graph["131"]["inputs"])
        self.assertEqual(session.backend.graph["131"]["inputs"]["last_frame"], ["133", 0])
        self.assertNotIn("132", session.backend.graph)
        self.assertNotIn("134", session.backend.graph)

    def test_canonical_start_end_compiles_both_and_same_asset_is_allowed(self):
        session = self.new_session()
        start = session.upload_reference("start.png", image_bytes("PNG", (200, 30, 30)), role="start_frame")
        end = session.upload_reference("end.jpg", image_bytes("JPEG", (30, 30, 200)), role="end_frame")
        job = session.submit(
            {
                "prompt": "motion between keyframes",
                "references": {
                    "start_frame": {"id": start.reference.id, "role": "start_frame"},
                    "end_frame": {"id": end.reference.id, "role": "end_frame"},
                },
            }
        )
        self.assertEqual(job.public()["route_label"], "Start + End")
        graph = session.backend.graph
        self.assertEqual(graph["131"]["inputs"]["first_frame"], ["134", 0])
        self.assertEqual(graph["134"]["inputs"]["image"], ["132", 0])
        self.assertEqual(graph["134"]["inputs"]["crop"], "center")
        self.assertEqual(graph["131"]["inputs"]["last_frame"], ["133", 0])
        self.assertEqual(graph["132"]["inputs"]["image"], f"inputs/{start.filename}")
        self.assertEqual(graph["133"]["inputs"]["image"], f"inputs/{end.filename}")

        same = session.submit(
            {
                "prompt": "same asset in both slots",
                "references": {
                    "start_frame": {"id": start.reference.id, "role": "start_frame"},
                    "end_frame": {"id": start.reference.id, "role": "end_frame"},
                },
            }
        )
        self.assertEqual(same.public()["route_label"], "Start + End")

    def test_legacy_h1b_start_reference_stays_on_h1b_graph(self):
        session = self.new_session()
        start = session.upload_reference("start.png", image_bytes("PNG", (200, 30, 30)))
        session.submit(
            {
                "prompt": "legacy H1B",
                "reference": {"id": start.reference.id, "role": "start_frame"},
            }
        )
        self.assertEqual(session.backend.graph["132"]["inputs"]["image"], f"inputs/{start.filename}")
        self.assertNotIn("133", session.backend.graph)


if __name__ == "__main__":
    unittest.main()
