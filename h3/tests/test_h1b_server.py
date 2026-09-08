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
    REFERENCE_MAX_BYTES,
    ReferenceAssetMissingError,
    ReferenceDecodeError,
    ReferenceRequestError,
    ReferenceTooLargeError,
)


class FakeBackend:
    def submit(self, graph, client_id):
        self.graph = graph
        return {"prompt_id": "fake-prompt-id"}


def image_bytes(image_format: str) -> bytes:
    image = Image.new("RGB", (64, 48), (128, 32, 64))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def multipart_body(filename: str, body: bytes) -> tuple[bytes, str]:
    boundary = "----tegaki-h1b-test-boundary"
    encoded = boundary.encode("ascii")
    result = (
        b"--" + encoded + b"\r\n"
        + f'Content-Disposition: form-data; name="reference"; filename="{filename}"\r\n'.encode("utf-8")
        + b"Content-Type: application/octet-stream\r\n\r\n"
        + body
        + b"\r\n--"
        + encoded
        + b"--\r\n"
    )
    return result, f"multipart/form-data; boundary={boundary}"


class H1BReferenceServerTests(unittest.TestCase):
    def test_reference_upload_validation_and_missing_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            session = H1ASession("http://127.0.0.1:9", Path(directory))
            png = image_bytes("PNG")
            jpeg = image_bytes("JPEG")
            png_asset = session.upload_reference("start.png", png)
            jpeg_asset = session.upload_reference("replace.jpeg", jpeg)
            self.assertTrue(png_asset.path.is_file())
            self.assertEqual(png_asset.reference.role, "start_frame")
            self.assertNotEqual(png_asset.reference.id, jpeg_asset.reference.id)
            self.assertEqual(png_asset.public()["width"], 64)

            with self.assertRaises(ReferenceDecodeError):
                session.upload_reference("bad.png", b"not an image")
            with self.assertRaises(ReferenceTooLargeError):
                session.upload_reference("large.png", b"0" * (REFERENCE_MAX_BYTES + 1))
            with self.assertRaises(ReferenceRequestError):
                session.upload_reference(r"..\escape.png", png)
            with self.assertRaises(ReferenceAssetMissingError):
                session.submit(
                    {
                        "prompt": "uses a missing reference",
                        "reference": {"id": "f" * 32, "role": "start_frame"},
                    }
                )

    def test_http_upload_preview_and_generate_with_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            session = H1ASession("http://127.0.0.1:9", Path(directory))
            session.backend = FakeBackend()
            server = H1AServer(("127.0.0.1", 0), session)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                body, content_type = multipart_body("start.png", image_bytes("PNG"))
                upload_request = Request(
                    f"{base_url}/api/references",
                    data=body,
                    headers={"Content-Type": content_type},
                    method="POST",
                )
                with urlopen(upload_request) as response:
                    self.assertEqual(response.status, 201)
                    uploaded = json.loads(response.read().decode("utf-8"))["reference"]
                self.assertEqual(uploaded["role"], "start_frame")
                self.assertTrue(uploaded["preview_url"].startswith("/api/references/"))

                with urlopen(f"{base_url}{uploaded['preview_url']}") as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers["Content-Type"], "image/png")
                    self.assertGreater(len(response.read()), 20)

                generate_body = json.dumps(
                    {
                        "prompt": "the greenhouse leaves move gently",
                        "width": 608,
                        "height": 352,
                        "duration": 5,
                        "seed": 7,
                        "steps": 20,
                        "reference": {"id": uploaded["id"], "role": uploaded["role"]},
                    }
                ).encode("utf-8")
                generate_request = Request(
                    f"{base_url}/api/generate",
                    data=generate_body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(generate_request) as response:
                    self.assertEqual(response.status, 202)
                    job = json.loads(response.read().decode("utf-8"))["job"]
                self.assertEqual(job["route"], "native_i2v")
                self.assertTrue(job["reference_used"])
                self.assertEqual(job["reference"]["role"], "start_frame")
                self.assertEqual(
                    session.backend.graph["132"]["inputs"]["image"],
                    f"inputs/{uploaded['filename']}",
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_http_invalid_upload_is_distinguished(self):
        with tempfile.TemporaryDirectory() as directory:
            session = H1ASession("http://127.0.0.1:9", Path(directory))
            server = H1AServer(("127.0.0.1", 0), session)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                body, content_type = multipart_body("bad.png", b"not an image")
                request = Request(
                    f"{base_url}/api/references",
                    data=body,
                    headers={"Content-Type": content_type},
                    method="POST",
                )
                with self.assertRaises(HTTPError) as context:
                    urlopen(request)
                response = context.exception
                self.assertEqual(response.code, 400)
                payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["kind"], "reference_decode_failed")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
