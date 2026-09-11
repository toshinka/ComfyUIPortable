"""Contract tests for the H2C Still server boundary."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    H1AServer,
    H1ASession,
    StillSourceMissingError,
    StillSourceRequestError,
)


class FakeBackend:
    def __init__(self) -> None:
        self.graph = None
        self.prompt_id = "h2c-fake-prompt"

    def submit(self, graph, client_id):
        self.graph = graph
        return {"prompt_id": self.prompt_id}


def image_bytes(image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", (64, 48), (128, 32, 64))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def multipart_body(field: str, filename: str, body: bytes) -> tuple[bytes, str]:
    boundary = "----tegaki-h2c-test-boundary"
    encoded = boundary.encode("ascii")
    result = (
        b"--" + encoded + b"\r\n"
        + f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode("utf-8")
        + b"Content-Type: application/octet-stream\r\n\r\n"
        + body
        + b"\r\n--"
        + encoded
        + b"--\r\n"
    )
    return result, f"multipart/form-data; boundary={boundary}"


class H2CStillServerTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def test_still_source_upload_is_server_issued_and_png_jpeg_only(self):
        session = self.new_session()
        source = session.upload_still_source("source.png", image_bytes())
        self.assertRegex(source.source_id, r"^[0-9a-f]{32}$")
        self.assertEqual(source.path.parent, session.input_root)
        self.assertEqual(source.public()["preview_url"], f"/api/still/sources/{source.source_id}")
        self.assertEqual(source.content_type, "image/png")
        with self.assertRaises(StillSourceRequestError):
            session.upload_still_source("source.webp", image_bytes("PNG"))
        with self.assertRaises(StillSourceRequestError):
            session.upload_still_source(r"..\escape.png", image_bytes())

    def test_http_source_upload_and_preview_use_dedicated_boundary(self):
        session = self.new_session()
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            body, content_type = multipart_body("source", "source.jpg", image_bytes("JPEG"))
            request = Request(
                f"{base_url}/api/still/source",
                data=body,
                headers={"Content-Type": content_type},
                method="POST",
            )
            with urlopen(request) as response:
                self.assertEqual(response.status, 201)
                source = json.loads(response.read().decode("utf-8"))["source"]
            self.assertRegex(source["id"], r"^[0-9a-f]{32}$")
            self.assertTrue(source["preview_url"].startswith("/api/still/sources/"))
            with urlopen(f"{base_url}{source['preview_url']}") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "image/jpeg")
                self.assertGreater(len(response.read()), 20)

            wrong_field, wrong_type = multipart_body("reference", "source.png", image_bytes())
            wrong_request = Request(
                f"{base_url}/api/still/source",
                data=wrong_field,
                headers={"Content-Type": wrong_type},
                method="POST",
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(wrong_request)
            self.assertEqual(context.exception.code, 400)
            payload = json.loads(context.exception.read().decode("utf-8"))
            self.assertEqual(payload["kind"], "still_source_upload_failed")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_prompt_only_still_uses_h2a_and_has_no_video_media(self):
        session = self.new_session()
        job = session.submit_still(
            {"prompt": "a paper lantern on a quiet desk", "seed": 123}
        )
        self.assertEqual(job.media_kind, "still")
        self.assertEqual(job.route, "native_still")
        public = job.public()
        self.assertEqual(public["media_kind"], "still")
        self.assertEqual(public["route_label"], "Text only")
        self.assertIsNone(public["source"])
        self.assertIsNone(public["request"]["source_id"])
        self.assertEqual(public["request"]["seed"], "123")
        self.assertIsNone(public["video_url"])
        self.assertIsNone(public["image_url"])
        self.assertEqual(session.backend.graph["131"]["inputs"]["length"], 5)
        self.assertNotIn("first_frame", session.backend.graph["131"]["inputs"])

    def test_source_still_uses_h2b_and_browser_cannot_submit_a_path(self):
        session = self.new_session()
        source = session.upload_still_source("source.png", image_bytes())
        job = session.submit_still(
            {"prompt": "keep the subject, change the light", "source_id": source.source_id, "seed": 456}
        )
        self.assertEqual(job.route, "native_source_anchored_still")
        self.assertEqual(job.public()["route_label"], "Source Image")
        self.assertEqual(job.public()["source"]["id"], source.source_id)
        self.assertEqual(job.public()["request"]["seed"], "456")
        self.assertEqual(
            session.backend.graph["133"]["inputs"]["image"],
            f"inputs/{source.filename}",
        )
        self.assertEqual(
            session.backend.graph["134"]["class_type"],
            "ImageScale",
        )
        self.assertEqual(
            session.backend.graph["134"]["inputs"]["image"],
            ["133", 0],
        )
        self.assertEqual(
            session.backend.graph["134"]["inputs"]["crop"],
            "center",
        )
        self.assertEqual(
            session.backend.graph["131"]["inputs"]["first_frame"],
            ["134", 0],
        )
        with self.assertRaisesRegex(ValueError, "server-issued source_id"):
            session.submit_still(
                {"prompt": "raw path", "source_path": r"D:\private\source.png"}
            )
        with self.assertRaisesRegex(ValueError, "source id is invalid"):
            session.submit_still({"prompt": "bad id", "source_id": "../../source.png"})

    def test_missing_source_fails_closed_before_backend_submit(self):
        session = self.new_session()
        source = session.upload_still_source("source.png", image_bytes())
        source.path.unlink()
        with self.assertRaises(StillSourceMissingError):
            session.submit_still({"prompt": "missing", "source_id": source.source_id})
        self.assertIsNone(session.backend.graph)

    def test_still_history_selects_image_only_and_serves_safe_endpoint(self):
        session = self.new_session()
        source = session.upload_still_source("source.png", image_bytes())
        job = session.submit_still(
            {"prompt": "source anchored still", "source_id": source.source_id, "seed": 789}
        )
        output = session.output_root / "still" / "h2c.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image_bytes())
        session._apply_history(
            job,
            {
                "status": {"completed": True},
                "outputs": {"92": {"images": [{"filename": "h2c.png", "subfolder": "still"}]}},
            },
        )
        public = job.public()
        self.assertEqual(job.state, "COMPLETED")
        self.assertEqual(public["media_kind"], "still")
        self.assertEqual(public["image_url"], f"/api/jobs/{job.job_id}/image")
        self.assertEqual(public["thumbnail_url"], public["image_url"])
        self.assertIsNone(public["video_url"])
        self.assertEqual(public["request"]["source_id"], source.source_id)

        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base_url}{public['image_url']}") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "image/png")
                self.assertGreater(len(response.read()), 20)
            with self.assertRaises(HTTPError) as context:
                urlopen(f"{base_url}/api/jobs/{job.job_id}/video")
            self.assertEqual(context.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_still_history_rejects_video_output_suffix(self):
        session = self.new_session()
        job = session.submit_still({"prompt": "still"})
        session._apply_history(
            job,
            {
                "status": {"completed": True},
                "outputs": {"92": {"gifs": [{"filename": "wrong.mp4", "subfolder": "still"}]}},
            },
        )
        self.assertEqual(job.state, "FAILED")
        self.assertIn("image output", job.error or "")


if __name__ == "__main__":
    unittest.main()
