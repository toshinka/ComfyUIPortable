"""VP1 Video enum, API-config, and Still-isolation contract tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.adapters.native_t2v import (  # noqa: E402
    RequestValidationError,
    validate_request,
    video_option_metadata,
)
from h3.app.server import H1AServer, H1ASession  # noqa: E402


class FakeBackend:
    def __init__(self) -> None:
        self.graph = None

    def submit(self, graph, client_id):
        self.graph = graph
        return {"prompt_id": f"vp1-{client_id}"}


class VP1VideoEnvelopeTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def test_verified_video_enums_are_accepted_and_compiled(self):
        session = self.new_session()
        duration_job = session.submit(
            {
                "prompt": "a small robot crosses the greenhouse",
                "width": 608,
                "height": 352,
                "duration": 15,
                "seed": 20260910,
                "steps": 20,
            }
        )
        self.assertEqual(duration_job.request.duration, 15.0)
        self.assertEqual(duration_job.public()["request"]["seed"], "20260910")
        self.assertEqual(session.backend.graph["131"]["inputs"]["length"], 362)

        resolution_job = session.submit(
            {
                "prompt": "a small robot crosses the greenhouse",
                "width": 736,
                "height": 416,
                "duration": 5,
                "seed": 20260910,
                "steps": 20,
            }
        )
        self.assertEqual(resolution_job.request.width, 736)
        self.assertEqual(resolution_job.request.height, 416)
        self.assertEqual(session.backend.graph["131"]["inputs"]["width"], 736)
        self.assertEqual(session.backend.graph["131"]["inputs"]["height"], 416)

    def test_unverified_resolution_and_duration_fail_closed(self):
        for payload, message in (
            (
                {"prompt": "unsupported size", "width": 864, "height": 480, "duration": 5},
                "verified resolutions",
            ),
            (
                {"prompt": "unsupported duration", "width": 608, "height": 352, "duration": 10},
                "verified duration options",
            ),
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(RequestValidationError, message):
                    validate_request(payload)

    def test_api_config_is_video_source_of_truth_and_still_isolated(self):
        expected = video_option_metadata()
        session = self.new_session()
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base_url}/api/config") as response:
                self.assertEqual(response.status, 200)
                config = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(config["resolution_options"], expected["resolution_options"])
        self.assertEqual(config["duration_options"], expected["duration_options"])
        self.assertEqual(
            config["still"]["resolution_options"],
            [{"label": "608 x 352", "width": 608, "height": 352}],
        )
        self.assertNotIn("duration_options", config["still"])


if __name__ == "__main__":
    unittest.main()
