from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import threading
import unittest
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from h3.app.server import (  # noqa: E402
    BackendError,
    H1AServer,
    H1ASession,
    LIFECYCLE_BACKEND_UNAVAILABLE,
    LIFECYCLE_BUSY,
    LIFECYCLE_PROFILE_MISMATCH,
    LIFECYCLE_PROFILE_UNVERIFIABLE,
    LIFECYCLE_SAFE_IDLE,
    TERMINAL_STATES,
    build_lifecycle_snapshot,
    build_h3_profile_expectation,
    parse_backend_status,
    CANONICAL_H3,
    PROFILE_MISMATCH,
    PROFILE_UNVERIFIABLE,
    PORTABLE_ROOT,
    UNAVAILABLE,
)


def backend_status(
    *,
    profile: str = CANONICAL_H3,
    queue_known: bool = True,
    running: int | None = 0,
    pending: int | None = 0,
) -> dict:
    return {
        "state": "READY" if profile == CANONICAL_H3 else profile,
        "backend_profile": profile,
        "queue_known": queue_known,
        "queue_running_count": running,
        "queue_pending_count": pending,
    }


def job(state: str) -> SimpleNamespace:
    return SimpleNamespace(state=state)


class PI1LifecycleSnapshotTests(unittest.TestCase):
    def test_a_canonical_empty_queue_is_safe_idle(self):
        snapshot = build_lifecycle_snapshot(backend_status(), [])
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_SAFE_IDLE)
        self.assertTrue(snapshot["safe_to_stop_native"])

    def test_b_running_queue_is_busy(self):
        snapshot = build_lifecycle_snapshot(backend_status(running=1), [])
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_BUSY)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_c_pending_queue_is_busy(self):
        snapshot = build_lifecycle_snapshot(backend_status(pending=1), [])
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_BUSY)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_d_queued_h3_job_is_busy(self):
        snapshot = build_lifecycle_snapshot(backend_status(), [job("QUEUED")])
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_BUSY)
        self.assertEqual(snapshot["active_nonterminal_job_count"], 1)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_e_running_and_disconnected_h3_jobs_are_busy(self):
        snapshot = build_lifecycle_snapshot(
            backend_status(),
            [job("RUNNING"), job("DISCONNECTED")],
        )
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_BUSY)
        self.assertEqual(snapshot["active_nonterminal_job_count"], 2)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_f_terminal_jobs_only_are_safe_idle(self):
        snapshot = build_lifecycle_snapshot(
            backend_status(),
            [job(state) for state in ("COMPLETED", "FAILED", "CANCELLED")],
        )
        self.assertEqual(TERMINAL_STATES, {"COMPLETED", "FAILED", "CANCELLED"})
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_SAFE_IDLE)
        self.assertEqual(snapshot["active_nonterminal_job_count"], 0)
        self.assertTrue(snapshot["safe_to_stop_native"])

    def test_g_profile_mismatch_fails_closed(self):
        snapshot = build_lifecycle_snapshot(
            backend_status(profile=PROFILE_MISMATCH),
            [],
        )
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_PROFILE_MISMATCH)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_h_profile_unverifiable_fails_closed(self):
        snapshot = build_lifecycle_snapshot(
            backend_status(profile=PROFILE_UNVERIFIABLE, queue_known=False, running=None, pending=None),
            [],
        )
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_PROFILE_UNVERIFIABLE)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_i_backend_unavailable_fails_closed(self):
        snapshot = build_lifecycle_snapshot(
            backend_status(profile=UNAVAILABLE, queue_known=False, running=None, pending=None),
            [],
        )
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_BACKEND_UNAVAILABLE)
        self.assertFalse(snapshot["safe_to_stop_native"])

    def test_j_malformed_queue_never_becomes_safe_idle(self):
        expected = build_h3_profile_expectation("http://127.0.0.1:8188", PORTABLE_ROOT)
        stats = {
            "system": {
                "argv": [
                    expected.native_main,
                    "--listen",
                    expected.native_host,
                    "--port",
                    str(expected.native_port),
                    "--disable-all-custom-nodes",
                    "--extra-model-paths-config",
                    expected.allowed_model_paths[0],
                    "--output-directory",
                    expected.output_directory,
                    "--input-directory",
                    expected.input_directory,
                    "--user-directory",
                    expected.user_directory,
                    "--temp-directory",
                    expected.temp_directory,
                    "--database-url",
                    expected.database_url,
                ]
            }
        }
        parsed = parse_backend_status(stats, {"queue_pending": []}, expected)
        snapshot = build_lifecycle_snapshot(parsed, [])
        self.assertEqual(parsed["backend_profile"], PROFILE_UNVERIFIABLE)
        self.assertFalse(parsed["queue_known"])
        self.assertEqual(snapshot["native_stop_guard"], LIFECYCLE_PROFILE_UNVERIFIABLE)
        self.assertFalse(snapshot["safe_to_stop_native"])
        self.assertNotEqual(snapshot["native_stop_guard"], LIFECYCLE_SAFE_IDLE)

    def test_actual_status_api_exposes_snapshot(self):
        class StubBackend:
            def status(self):
                return backend_status()

        with tempfile.TemporaryDirectory() as directory:
            session = H1ASession("http://127.0.0.1:9", Path(directory))
            session.backend = StubBackend()
            server = H1AServer(("127.0.0.1", 0), session)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/status") as response:
                    payload = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

        self.assertEqual(payload["backend_profile"], CANONICAL_H3)
        self.assertEqual(payload["lifecycle"]["native_stop_guard"], LIFECYCLE_SAFE_IDLE)
        self.assertTrue(payload["lifecycle"]["safe_to_stop_native"])
        self.assertEqual(payload["lifecycle"]["queue_running_count"], 0)
        self.assertEqual(payload["lifecycle"]["queue_pending_count"], 0)
        self.assertEqual(payload["lifecycle"]["active_nonterminal_job_count"], 0)

    def test_status_api_unavailable_path_is_not_safe(self):
        class UnavailableBackend:
            def status(self):
                raise BackendError("Native backend unavailable.")

        with tempfile.TemporaryDirectory() as directory:
            session = H1ASession("http://127.0.0.1:9", Path(directory))
            session.backend = UnavailableBackend()
            server = H1AServer(("127.0.0.1", 0), session)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/status") as response:
                    payload = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

        self.assertEqual(payload["backend_profile"], UNAVAILABLE)
        self.assertEqual(payload["lifecycle"]["native_stop_guard"], LIFECYCLE_BACKEND_UNAVAILABLE)
        self.assertFalse(payload["lifecycle"]["safe_to_stop_native"])


if __name__ == "__main__":
    unittest.main()
