"""Contract tests for VP2C History handoff into the bounded R2V slots."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    H1AServer,
    H1ASession,
    R2VHandoffConflictError,
    R2VHandoffJobNotFoundError,
    R2VHandoffRequestError,
)


class FakeBackend:
    def __init__(self) -> None:
        self.graphs = []
        self.counter = 0

    def submit(self, graph, client_id):
        self.graphs.append(graph)
        self.counter += 1
        return {"prompt_id": f"vp2c-fake-prompt-{self.counter}"}

    def history(self, prompt_id):
        return {}

    def queue(self):
        return {"queue_pending": [], "queue_running": []}


def image_bytes(image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", (64, 48), (190, 46, 46))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


VIDEO_METADATA = {
    "width": 608,
    "height": 352,
    "duration_seconds": 5.167,
    "frame_rate": 24.0,
    "frame_count": 124,
}


class VP2CReferenceHandoffTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def completed_still(self, session: H1ASession, filename: str = "generated.png"):
        job = session.submit_still({"prompt": "a red robot portrait", "seed": 11})
        path = session.output_root / "still" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image_bytes())
        session._apply_history(
            job,
            {
                "status": {"completed": True},
                "outputs": {"1": {"images": [{"filename": filename, "subfolder": "still"}]}},
            },
        )
        return job, path

    def completed_video(self, session: H1ASession, filename: str = "generated.mp4"):
        job = session.submit({"prompt": "a red robot walks", "seed": 12})
        path = session.output_root / "video" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"server-owned test mp4")
        session._apply_history(
            job,
            {
                "status": {"completed": True},
                "outputs": {"1": {"gifs": [{"filename": filename, "subfolder": "video"}]}},
            },
        )
        return job, path

    def test_still_handoff_copies_source_and_keeps_opaque_provenance(self):
        session = self.new_session()
        job, source_path = self.completed_still(session)
        before = source_path.read_bytes()

        asset = session.promote_still_to_character(job.job_id)
        public = asset.public()

        self.assertEqual(asset.name, "Generated Still")
        self.assertEqual(asset.source_kind, "generated_still")
        self.assertEqual(asset.source_job_id, job.job_id)
        self.assertRegex(asset.picture_id, r"^[0-9a-f]{32}$")
        self.assertEqual(asset.path.parent, session.input_root)
        self.assertTrue(asset.path.is_file())
        self.assertEqual(asset.path.read_bytes(), before)
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_bytes(), before)
        self.assertNotIn("path", public)
        self.assertNotIn("staged_path", public)
        self.assertEqual(public["display_name"], "Generated Still")

        replacement = session.promote_still_to_character(job.job_id)
        self.assertNotEqual(asset.picture_id, replacement.picture_id)
        self.assertTrue(asset.path.is_file())
        self.assertTrue(replacement.path.is_file())
        self.assertEqual(len(session.r2v_pictures), 2)

    def test_video_handoff_copies_source_and_preserves_video_metadata(self):
        session = self.new_session()
        job, source_path = self.completed_video(session)
        before = source_path.read_bytes()

        with patch("h3.app.server._probe_video_file", return_value=VIDEO_METADATA):
            asset = session.promote_video_to_motion(job.job_id)

        public = asset.public()
        self.assertEqual(asset.name, "Generated Video")
        self.assertEqual(asset.source_kind, "generated_video")
        self.assertEqual(asset.source_job_id, job.job_id)
        self.assertRegex(asset.video_id, r"^[0-9a-f]{32}$")
        self.assertEqual(asset.metadata, VIDEO_METADATA)
        self.assertTrue(asset.path.is_file())
        self.assertEqual(asset.path.read_bytes(), before)
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_bytes(), before)
        self.assertNotIn("path", public)
        self.assertNotIn("staged_path", public)
        self.assertEqual(public["display_name"], "Generated Video")

    def test_handoff_rejects_wrong_session_state_kind_output_and_injection(self):
        session = self.new_session()
        still, _still_path = self.completed_still(session)
        video, _video_path = self.completed_video(session)

        with self.assertRaises(R2VHandoffJobNotFoundError):
            session.promote_still_to_character("f" * 32)
        with self.assertRaises(R2VHandoffRequestError):
            session.promote_still_to_character(r"C:\outside\job")
        with self.assertRaises(R2VHandoffRequestError):
            session.promote_still_to_character(video.job_id)
        with self.assertRaises(R2VHandoffRequestError):
            session.promote_video_to_motion(still.job_id)

        queued, _queued_path = self.completed_still(session, "queued.png")
        queued.state = "RUNNING"
        with self.assertRaises(R2VHandoffConflictError):
            session.promote_still_to_character(queued.job_id)
        queued.state = "COMPLETED"

        missing, _missing_path = self.completed_still(session, "missing.png")
        missing.output = {"filename": "missing.png", "subfolder": "still"}
        (session.output_root / "still" / "missing.png").unlink()
        with self.assertRaises(R2VHandoffConflictError):
            session.promote_still_to_character(missing.job_id)

        outside, _outside_path = self.completed_still(session, "outside.png")
        outside.output = {"filename": "outside.png", "subfolder": ".."}
        with self.assertRaises(R2VHandoffConflictError):
            session.promote_still_to_character(outside.job_id)

        wrong_suffix, wrong_suffix_path = self.completed_still(session, "wrong.png")
        wrong_suffix.output = {"filename": "wrong.mp4", "subfolder": "still"}
        (session.output_root / "still" / "wrong.mp4").write_bytes(b"not an image")
        with self.assertRaises(R2VHandoffConflictError):
            session.promote_still_to_character(wrong_suffix.job_id)
        self.assertTrue(wrong_suffix_path.is_file())

    def test_active_generation_blocks_handoff_without_replacing_existing_asset(self):
        session = self.new_session()
        completed, _source_path = self.completed_still(session)
        existing = session.upload_r2v_picture("existing.png", image_bytes())
        before_ids = set(session.r2v_pictures)
        active = session.submit_still({"prompt": "active still", "seed": 13})
        active.state = "RUNNING"

        with self.assertRaises(R2VHandoffConflictError):
            session.promote_still_to_character(completed.job_id)

        self.assertEqual(set(session.r2v_pictures), before_ids)
        self.assertTrue(existing.path.is_file())
        active.state = "COMPLETED"

    def test_http_handoff_is_job_id_only_and_returns_no_filesystem_path(self):
        session = self.new_session()
        job, _source_path = self.completed_still(session)
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            body = json.dumps({"job_id": job.job_id, "path": r"C:\outside.png"}).encode("utf-8")
            request = Request(
                f"{base_url}/api/r2v/from-still",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(request)
            self.assertEqual(context.exception.code, 400)
            payload = json.loads(context.exception.read().decode("utf-8"))
            self.assertEqual(payload["kind"], "r2v_handoff_failed")
            self.assertEqual(len(session.r2v_pictures), 0)

            with urlopen(
                Request(
                    f"{base_url}/api/r2v/from-still",
                    data=json.dumps({"job_id": job.job_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            ) as response:
                self.assertEqual(response.status, 201)
                payload = json.loads(response.read().decode("utf-8"))
            picture = payload["picture"]
            self.assertRegex(picture["id"], r"^[0-9a-f]{32}$")
            self.assertEqual(picture["source_kind"], "generated_still")
            self.assertEqual(picture["source_job_id"], job.job_id)
            self.assertNotIn("path", json.dumps(payload))
            with urlopen(f"{base_url}{picture['preview_url']}") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "image/png")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
