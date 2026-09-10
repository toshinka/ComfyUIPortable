"""Contract tests for the bounded VP2B Experimental Reference Video route."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
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

from h3.adapters.native_ref2va import (  # noqa: E402
    PICTURE_PROMPT_PREFIX,
    PICTURE_VIDEO_PROMPT_PREFIX,
    RequestValidationError as Ref2VARequestValidationError,
    materialize_prompt,
)
from h3.app.server import (  # noqa: E402
    H1AServer,
    H1ASession,
    R2V_VIDEO_MAX_BYTES,
    ReferenceVideoAssetMissingError,
    ReferenceVideoDecodeError,
    ReferenceVideoRequestError,
    ReferenceVideoTooLargeError,
)


class FakeBackend:
    def __init__(self) -> None:
        self.graph = None
        self.prompt_id = "vp2b-fake-prompt"

    def submit(self, graph, client_id):
        self.graph = graph
        return {"prompt_id": self.prompt_id}


def image_bytes(image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", (64, 48), (190, 46, 46))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def multipart_body(field: str, filename: str, body: bytes) -> tuple[bytes, str]:
    boundary = "----tegaki-vp2b-test-boundary"
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


class VP2BR2VPlaygroundTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def upload_assets(self, session: H1ASession):
        picture = session.upload_r2v_picture("robot.webp", image_bytes("WEBP"))
        with patch(
            "h3.app.server._probe_video_file",
            return_value={
                "width": 608,
                "height": 352,
                "duration_seconds": 5.167,
                "frame_rate": 24.0,
                "frame_count": 124,
            },
        ):
            motion = session.upload_r2v_motion_video("motion.mp4", b"valid test mp4")
        return picture, motion

    def test_prompt_adapter_is_deterministic_and_keeps_original_separate(self):
        original, materialized = materialize_prompt("  A red robot walks.  ", has_video=False)
        self.assertEqual(original, "A red robot walks.")
        self.assertEqual(materialized, f"{PICTURE_PROMPT_PREFIX}A red robot walks.")
        _, with_motion = materialize_prompt("A red robot walks.", has_video=True)
        self.assertEqual(with_motion, f"{PICTURE_VIDEO_PROMPT_PREFIX}A red robot walks.")
        self.assertNotIn("<Picture 1>", original)

    def test_uploads_are_opaque_and_reject_unsafe_or_unsupported_inputs(self):
        session = self.new_session()
        picture, motion = self.upload_assets(session)
        self.assertRegex(picture.picture_id, r"^[0-9a-f]{32}$")
        self.assertRegex(motion.video_id, r"^[0-9a-f]{32}$")
        self.assertTrue(picture.path.is_file())
        self.assertTrue(motion.path.is_file())
        self.assertNotIn("path", picture.public())
        self.assertNotIn("path", motion.public())
        with self.assertRaises(ReferenceVideoRequestError):
            session.upload_r2v_picture(r"C:\outside.png", image_bytes())
        with self.assertRaises(ReferenceVideoRequestError):
            session.upload_r2v_picture("picture.gif", image_bytes())
        with self.assertRaises(ReferenceVideoRequestError):
            session.upload_r2v_motion_video("motion.mov", b"not mp4")
        with self.assertRaises(ReferenceVideoRequestError):
            session.upload_r2v_motion_video(r"..\motion.mp4", b"not mp4")
        with self.assertRaises(ReferenceVideoTooLargeError):
            session.upload_r2v_motion_video("large.mp4", b"0" * (R2V_VIDEO_MAX_BYTES + 1))
        with self.assertRaises(ReferenceVideoDecodeError):
            with patch("h3.app.server._probe_video_file", side_effect=ReferenceVideoDecodeError("bad")):
                session.upload_r2v_motion_video("bad.mp4", b"not decodable")

    def test_picture_only_and_picture_plus_motion_use_ref2va_without_audio(self):
        session = self.new_session()
        picture, motion = self.upload_assets(session)
        picture_job = session.submit_reference_video(
            {
                "video_type": "reference",
                "prompt": "A red robot walks through a workshop.",
                "picture_id": picture.picture_id,
                "motion_video_id": None,
                "width": 608,
                "height": 352,
                "duration": 5,
                "seed": "9223372036854775807",
                "steps": 20,
            }
        )
        picture_public = picture_job.public()
        self.assertEqual(picture_public["route_label"], "Reference · Picture")
        self.assertEqual(picture_public["request"]["prompt"], "A red robot walks through a workshop.")
        self.assertTrue(picture_public["request"]["materialized_prompt"].startswith(PICTURE_PROMPT_PREFIX))
        self.assertEqual(picture_public["request"]["seed"], "9223372036854775807")
        self.assertEqual(session.backend.graph["131"]["inputs"]["ref_images.ref_image_1"], ["132", 0])
        self.assertNotIn("ref_videos.ref_video_1", session.backend.graph["131"]["inputs"])
        self.assertNotIn("ref_video_audio_1", session.backend.graph["131"]["inputs"])

        picture_job.state = "COMPLETED"
        motion_job = session.submit_reference_video(
            {
                "video_type": "reference",
                "prompt": "A red robot follows the motion reference.",
                "picture_id": picture.picture_id,
                "motion_video_id": motion.video_id,
                "width": 608,
                "height": 352,
                "duration": 5,
                "seed": 7,
                "steps": 20,
            }
        )
        public = motion_job.public()
        self.assertEqual(public["route"], "native_ref2va")
        self.assertEqual(public["route_label"], "Reference · Picture + Motion")
        self.assertEqual(public["video_type"], "reference")
        self.assertEqual(public["reference_video"]["picture"]["id"], picture.picture_id)
        self.assertEqual(public["reference_video"]["motion_video"]["id"], motion.video_id)
        self.assertEqual(
            session.backend.graph["131"]["inputs"]["ref_videos.ref_video_1"],
            ["135", 0],
        )
        self.assertEqual(
            public["request"]["materialized_prompt"],
            f"{PICTURE_VIDEO_PROMPT_PREFIX}A red robot follows the motion reference.",
        )
        self.assertFalse(any(key.startswith("ref_audio") for key in session.backend.graph["131"]["inputs"]))

    def test_fixed_settings_missing_assets_conflicts_and_path_arrays_fail_closed(self):
        session = self.new_session()
        picture, _motion = self.upload_assets(session)
        base = {
            "video_type": "reference",
            "prompt": "bounded reference test",
            "picture_id": picture.picture_id,
            "motion_video_id": None,
            "width": 608,
            "height": 352,
            "duration": 5,
            "seed": 1,
            "steps": 20,
        }
        for override in (
            {"width": 736},
            {"duration": 15},
            {"steps": 21},
            {"references": []},
            {"picture_path": "C:/outside.png"},
            {"unknown": True},
        ):
            with self.subTest(override=override):
                with self.assertRaises((ValueError, Ref2VARequestValidationError)):
                    session.submit_reference_video({**base, **override})
        with self.assertRaises(ReferenceVideoAssetMissingError):
            session.submit_reference_video({**base, "picture_id": "f" * 32})
        active = session.submit_reference_video(base)
        with self.assertRaisesRegex(ValueError, "(?i)another H3 generation is active"):
            session.submit_reference_video(base)
        active.state = "COMPLETED"

    def test_http_boundaries_config_and_public_history_metadata(self):
        session = self.new_session()
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base_url}/api/config") as response:
                config = json.loads(response.read().decode("utf-8"))
            self.assertEqual(config["reference_video"]["resolution_options"], [{"label": "608 x 352", "width": 608, "height": 352}])
            self.assertEqual(config["reference_video"]["duration_options"], [{"label": "5 seconds", "value": 5}])
            self.assertEqual(config["reference_video"]["default_steps"], 20)
            self.assertFalse(config["reference_video"]["audio_reference"])

            picture_body, picture_type = multipart_body("picture", "robot.png", image_bytes())
            picture_request = Request(
                f"{base_url}/api/r2v/picture",
                data=picture_body,
                headers={"Content-Type": picture_type},
                method="POST",
            )
            with urlopen(picture_request) as response:
                picture = json.loads(response.read().decode("utf-8"))["picture"]
            self.assertRegex(picture["id"], r"^[0-9a-f]{32}$")
            with urlopen(f"{base_url}{picture['preview_url']}") as response:
                self.assertEqual(response.headers["Content-Type"], "image/png")

            invalid = json.dumps(
                {
                    "video_type": "reference",
                    "prompt": "missing motion",
                    "picture_id": picture["id"],
                    "motion_video_id": None,
                    "width": 736,
                    "height": 352,
                    "duration": 5,
                    "seed": 1,
                    "steps": 20,
                }
            ).encode("utf-8")
            request = Request(
                f"{base_url}/api/r2v/generate",
                data=invalid,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(request)
            self.assertEqual(context.exception.code, 400)
            payload = json.loads(context.exception.read().decode("utf-8"))
            self.assertEqual(payload["kind"], "validation")

            job = session.submit_reference_video(
                {
                    "video_type": "reference",
                    "prompt": "public history entry",
                    "picture_id": picture["id"],
                    "motion_video_id": None,
                    "width": 608,
                    "height": 352,
                    "duration": 5,
                    "seed": 3,
                    "steps": 20,
                }
            )
            self.assertEqual(job.public()["reference_video"]["motion_video"], None)
            self.assertNotIn("path", json.dumps(job.public()))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
