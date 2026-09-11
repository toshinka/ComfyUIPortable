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

from h3.app.native_profile import (  # noqa: E402
    CANONICAL_H3,
    PROFILE_MISMATCH,
    PROFILE_UNVERIFIABLE,
    build_h3_profile_expectation,
    validate_h3_native_profile,
)
from h3.app.server import (  # noqa: E402
    BackendClient,
    BackendError,
    BackendProfileError,
    H1AServer,
    H1ASession,
    PORTABLE_ROOT,
    parse_backend_status,
)


def canonical_argv(expected, *, model_path: str | None = None) -> list[str]:
    return [
        expected.native_main,
        "--listen",
        expected.native_host,
        "--port",
        str(expected.native_port),
        "--disable-all-custom-nodes",
        "--extra-model-paths-config",
        model_path or expected.allowed_model_paths[0],
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
        "--log-stdout",
    ]


def system_stats(argv: list[str]) -> dict:
    return {
        "system": {"argv": argv, "comfyui_version": "0.30.0"},
        "devices": [{"vram_total": 120, "vram_free": 45}],
    }


class H3ProfileGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.expected = build_h3_profile_expectation(
            "http://127.0.0.1:8188",
            self.directory.name,
        )
        self.queue = {"queue_pending": [], "queue_running": []}

    def classify(self, argv: list[str]):
        return validate_h3_native_profile(system_stats(argv), self.expected)

    def test_a_canonical_profile(self):
        self.assertEqual(
            self.classify(canonical_argv(self.expected))["classification"],
            CANONICAL_H3,
        )

    def test_b_missing_isolation_flag_is_mismatch(self):
        argv = canonical_argv(self.expected)
        argv.remove("--disable-all-custom-nodes")
        self.assertEqual(self.classify(argv)["classification"], PROFILE_MISMATCH)

    def test_c_wrong_model_path_is_mismatch(self):
        self.assertEqual(
            self.classify(canonical_argv(self.expected, model_path=str(Path(self.directory.name) / "wrong.yaml")))["classification"],
            PROFILE_MISMATCH,
        )

    def test_d_wrong_output_namespace_is_mismatch(self):
        argv = canonical_argv(self.expected)
        argv[argv.index("--output-directory") + 1] = str(Path(self.directory.name) / "wrong-output")
        self.assertEqual(self.classify(argv)["classification"], PROFILE_MISMATCH)

    def test_e_wrong_user_or_temp_namespace_is_mismatch(self):
        for option in ("--user-directory", "--temp-directory"):
            argv = canonical_argv(self.expected)
            argv[argv.index(option) + 1] = str(Path(self.directory.name) / "wrong-namespace")
            self.assertEqual(self.classify(argv)["classification"], PROFILE_MISMATCH)

    def test_f_non_memory_database_is_mismatch(self):
        argv = canonical_argv(self.expected)
        argv[argv.index("--database-url") + 1] = "sqlite:///h3.db"
        self.assertEqual(self.classify(argv)["classification"], PROFILE_MISMATCH)

    def test_g_missing_or_unusable_evidence_is_unverifiable(self):
        self.assertEqual(
            validate_h3_native_profile({"system": {}}, self.expected)["classification"],
            PROFILE_UNVERIFIABLE,
        )
        self.assertEqual(
            validate_h3_native_profile({"system": {"argv": "not-a-list"}}, self.expected)["classification"],
            PROFILE_UNVERIFIABLE,
        )

    def test_i_alternate_local_model_config_is_accepted(self):
        self.assertEqual(
            self.classify(canonical_argv(self.expected, model_path=self.expected.allowed_model_paths[1]))["classification"],
            CANONICAL_H3,
        )

    def test_j_windows_path_variation_is_normalized(self):
        argv = canonical_argv(self.expected)
        for option in (
            "--extra-model-paths-config",
            "--output-directory",
            "--input-directory",
            "--user-directory",
            "--temp-directory",
        ):
            index = argv.index(option) + 1
            argv[index] = argv[index].replace("\\", "/").upper()
        self.assertEqual(self.classify(argv)["classification"], CANONICAL_H3)

    def test_status_requires_canonical_profile_and_valid_queue(self):
        parsed = parse_backend_status(
            system_stats(canonical_argv(self.expected)),
            self.queue,
            self.expected,
        )
        self.assertEqual(parsed["state"], "READY")
        self.assertEqual(parsed["backend_profile"], CANONICAL_H3)
        self.assertNotIn("system_stats", parsed)

        invalid_queue = parse_backend_status(
            system_stats(canonical_argv(self.expected)),
            {"queue_pending": []},
            self.expected,
        )
        self.assertEqual(invalid_queue["state"], PROFILE_UNVERIFIABLE)

    def test_h_unavailable_is_exposed_through_existing_status_path(self):
        session = H1ASession("http://127.0.0.1:9", Path(self.directory.name))
        server = H1AServer(("127.0.0.1", 0), session)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/status") as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["state"], "DISCONNECTED")
        self.assertEqual(payload["backend_profile"], "UNAVAILABLE")

    def test_wrong_backend_never_calls_prompt(self):
        expected = build_h3_profile_expectation("http://127.0.0.1:8188", PORTABLE_ROOT)
        wrong_argv = canonical_argv(expected)
        wrong_argv[wrong_argv.index("--output-directory") + 1] = expected.user_directory
        calls = []
        client = BackendClient("http://127.0.0.1:8188")

        def fake_request(method, path, payload=None, timeout=None):
            del payload, timeout
            calls.append((method, path))
            if path == "/system_stats":
                return system_stats(wrong_argv)
            if path == "/queue":
                return {"queue_pending": [], "queue_running": []}
            if method == "POST" and path == "/prompt":
                raise AssertionError("wrong profile must not reach /prompt")
            raise AssertionError(f"unexpected backend request: {method} {path}")

        client._request = fake_request
        status = client.status()
        self.assertEqual(status["state"], PROFILE_MISMATCH)
        self.assertEqual(status["backend_profile"], PROFILE_MISMATCH)
        with self.assertRaises(BackendProfileError) as raised:
            client.submit({}, "test-client")
        self.assertEqual(raised.exception.profile, PROFILE_MISMATCH)
        self.assertEqual([path for method, path in calls if method == "POST"], [])

    def test_backend_profile_error_is_distinct_from_generic_backend_error(self):
        self.assertTrue(issubclass(BackendProfileError, BackendError))


if __name__ == "__main__":
    unittest.main()
