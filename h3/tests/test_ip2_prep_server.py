"""Contract tests for the IP2 experimental Browser Prep/Edit boundary."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    H1AServer,
    H1ASession,
    PrepAssetMissingError,
    RequestValidationError,
)


class FakeBackend:
    def __init__(self) -> None:
        self.graphs: list[dict] = []
        self.counter = 0

    def submit(self, graph, client_id):
        self.graphs.append(graph)
        self.counter += 1
        return {"prompt_id": f"ip2-fake-prompt-{self.counter}"}

    def history(self, prompt_id):
        return {}

    def queue(self):
        return {"queue_pending": [], "queue_running": []}

    def reference_node_available(self):
        return True


def image_bytes(image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", (64, 48), (190, 46, 46))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def json_request(url: str, payload: dict, method: str = "POST") -> tuple[int, dict]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def multipart_body(field: str, filename: str, body: bytes) -> tuple[str, bytes]:
    boundary = "----tegaki-ip2-test"
    raw = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n"
        "\r\n"
    ).encode("utf-8") + body + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return f"multipart/form-data; boundary={boundary}", raw


class IP2PrepServerTests(unittest.TestCase):
    def new_session(self) -> H1ASession:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = H1ASession("http://127.0.0.1:9", Path(directory.name))
        session.backend = FakeBackend()
        return session

    def test_semantic_submit_reuses_ip1_graph_and_sanitizes_public_request(self):
        session = self.new_session()
        source = session.upload_prep_asset("source.png", image_bytes())
        donor = session.upload_prep_asset("donor.webp", image_bytes("WEBP"))

        job = session.submit_prep(
            {
                "prompt": "change the jacket color",
                "source_id": source.asset_id,
                "donor_id": donor.asset_id,
                "seed": "17",
            }
        )
        public = job.public()
        graph_text = json.dumps(session.backend.graphs[-1])

        self.assertEqual(job.route, "native_image_prep")
        self.assertEqual(public["route_label"], "Prep · Source + Donor")
        self.assertEqual(public["media_kind"], "still")
        self.assertEqual(public["request"]["source_id"], source.asset_id)
        self.assertEqual(public["request"]["donor_id"], donor.asset_id)
        self.assertEqual(public["request"]["seed"], "17")
        self.assertNotIn("source_path", json.dumps(public))
        self.assertNotIn("donor_path", json.dumps(public))
        self.assertNotIn("filename", public["prep_source"])
        self.assertNotIn("length", public["request"])
        self.assertIn("Picture 1", graph_text)
        self.assertIn("Picture 2", graph_text)
        self.assertIn(f"inputs/{source.filename}", graph_text)
        self.assertIn(f"inputs/{donor.filename}", graph_text)
        self.assertRegex(source.asset_id, re.compile(r"^[0-9a-f]{32}$"))

    def test_source_only_and_invalid_donor_are_fail_closed(self):
        session = self.new_session()
        source = session.upload_prep_asset("source.jpg", image_bytes("JPEG"))

        source_only = session.submit_prep(
            {"prompt": "make a clean variation", "source_id": source.asset_id, "donor_id": None, "seed": 3}
        )
        self.assertEqual(source_only.public()["route_label"], "Prep · Source")
        self.assertIsNone(source_only.public()["request"]["donor_id"])

        for payload in (
            {"prompt": "x", "donor_id": None, "seed": 3},
            {"prompt": "x", "source_id": source.asset_id, "donor_id": "f" * 32, "seed": 3},
            {"prompt": "x", "source_id": source.asset_id, "donor_id": None, "seed": 3, "source_path": "inputs/a.png"},
        ):
            with self.assertRaises((RequestValidationError, PrepAssetMissingError)):
                session.submit_prep(payload)

        source_only.state = "COMPLETED"
        active = session.submit_prep(
            {"prompt": "active", "source_id": source.asset_id, "donor_id": None, "seed": 4}
        )
        active.state = "RUNNING"
        with self.assertRaises(RequestValidationError):
            session.submit_prep(
                {"prompt": "blocked", "source_id": source.asset_id, "donor_id": None, "seed": 5}
            )

    def test_http_config_upload_generate_and_still_handoff(self):
        session = self.new_session()
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(f"{base_url}/api/config") as response:
                config = json.loads(response.read().decode("utf-8"))
            self.assertEqual(config["prep"]["schema"], "tegaki.h3.ip2.experimental-browser-prep-edit/v1")
            self.assertEqual(config["prep"]["resolution_options"], [{"label": "608 x 352", "width": 608, "height": 352}])
            self.assertEqual(config["prep"]["source"]["required"], True)
            self.assertFalse(config["prep"]["donor"]["required"])

            content_type, body = multipart_body("source", "source.png", image_bytes())
            with urlopen(
                Request(
                    f"{base_url}/api/prep/source",
                    data=body,
                    headers={"Content-Type": content_type},
                    method="POST",
                )
            ) as response:
                source_payload = json.loads(response.read().decode("utf-8"))
            source = source_payload["source"]
            self.assertRegex(source["id"], r"^[0-9a-f]{32}$")
            self.assertNotIn("path", json.dumps(source_payload))

            content_type, body = multipart_body("donor", "donor.png", image_bytes())
            with urlopen(
                Request(
                    f"{base_url}/api/prep/donor",
                    data=body,
                    headers={"Content-Type": content_type},
                    method="POST",
                )
            ) as response:
                donor_payload = json.loads(response.read().decode("utf-8"))
            donor = donor_payload["donor"]

            status, generated = json_request(
                f"{base_url}/api/prep/generate",
                {"prompt": "transfer the warm coat color", "source_id": source["id"], "donor_id": donor["id"], "seed": 8},
            )
            self.assertEqual(status, 202)
            self.assertEqual(generated["job"]["route_label"], "Prep · Source + Donor")
            self.assertNotIn("source_path", json.dumps(generated))

            prep_job = session.get_job(generated["job"]["job_id"])
            assert prep_job is not None
            prep_job.state = "COMPLETED"

            still = session.submit_still({"prompt": "a completed still", "seed": 12})
            still_path = session.output_root / "still" / "handoff.png"
            still_path.parent.mkdir(parents=True, exist_ok=True)
            still_path.write_bytes(image_bytes())
            session._apply_history(
                still,
                {
                    "status": {"completed": True},
                    "outputs": {"1": {"images": [{"filename": "handoff.png", "subfolder": "still"}]}},
                },
            )
            status, handoff = json_request(
                f"{base_url}/api/prep/from-still",
                {"job_id": still.job_id},
            )
            self.assertEqual(status, 201)
            self.assertEqual(handoff["source"]["source_kind"], "generated_still")
            self.assertEqual(handoff["source"]["source_job_id"], still.job_id)
            self.assertNotIn("path", json.dumps(handoff))
            with urlopen(f"{base_url}{handoff['source']['preview_url']}") as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Content-Type"], "image/png")

            bad_request = Request(
                f"{base_url}/api/prep/from-still",
                data=json.dumps({"job_id": still.job_id, "path": "C:\\outside.png"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as context:
                urlopen(bad_request)
            self.assertEqual(context.exception.code, 400)
            error = json.loads(context.exception.read().decode("utf-8"))
            self.assertEqual(error["kind"], "prep_handoff_failed")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

