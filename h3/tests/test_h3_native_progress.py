import asyncio
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import aiohttp
from aiohttp import web

from h3.app.native_progress import (
    NativeProgressListener,
    discover_sampler_node_ids,
    map_progress_event,
)
from h3.app.server import H1ASession, Job


class SamplerNodeDiscoveryTests(unittest.TestCase):
    def test_discover_sampler_node_ids_standard_and_custom(self):
        graph_a = {
            "125": {"class_type": "SamplerCustomAdvanced"},
            "92": {"class_type": "SaveVideo"},
            "121": {"class_type": "VAEDecodeAudio"},
        }
        self.assertEqual(discover_sampler_node_ids(graph_a), {"125"})

        graph_b = {
            "prompt": {
                "42": {"class_type": "SamplerCustomAdvanced"},
                "100": {"class_type": "VAELoader"},
            }
        }
        self.assertEqual(discover_sampler_node_ids(graph_b), {"42"})

    def test_discover_sampler_node_ids_empty_or_non_sampler(self):
        self.assertEqual(discover_sampler_node_ids(None), set())
        self.assertEqual(discover_sampler_node_ids({}), set())
        self.assertEqual(discover_sampler_node_ids({"10": {"class_type": "KSampler"}}), set())


class MapProgressEventPureTests(unittest.TestCase):
    def test_matrix_a_correct_prompt_and_sampler_node(self):
        data = {"prompt_id": "p1", "node": "125", "value": 7, "max": 20}
        mapped = map_progress_event(data, "p1", {"125"})
        self.assertEqual(mapped, {"kind": "sampling", "value": 7, "max": 20, "percent": 35})

    def test_matrix_b_value_equals_max_100_percent(self):
        data = {"prompt_id": "p1", "node": "125", "value": 20, "max": 20}
        mapped = map_progress_event(data, "p1", {"125"})
        self.assertEqual(mapped, {"kind": "sampling", "value": 20, "max": 20, "percent": 100})

    def test_matrix_c_wrong_prompt_id(self):
        data = {"prompt_id": "wrong-prompt", "node": "125", "value": 7, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_d_missing_prompt_id(self):
        data = {"node": "125", "value": 7, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_e_correct_prompt_wrong_node(self):
        data = {"prompt_id": "p1", "node": "999", "value": 7, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_f_event_from_vae_or_non_sampler(self):
        data = {"prompt_id": "p1", "node": "122", "value": 10, "max": 10}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_g_missing_node(self):
        data = {"prompt_id": "p1", "value": 7, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_h_max_zero(self):
        data = {"prompt_id": "p1", "node": "125", "value": 0, "max": 0}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_i_negative_value(self):
        data = {"prompt_id": "p1", "node": "125", "value": -1, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_j_value_greater_than_max(self):
        data = {"prompt_id": "p1", "node": "125", "value": 21, "max": 20}
        self.assertIsNone(map_progress_event(data, "p1", {"125"}))

    def test_matrix_k_nan_or_non_finite_or_bool(self):
        self.assertIsNone(map_progress_event({"prompt_id": "p1", "node": "125", "value": float("nan"), "max": 20}, "p1", {"125"}))
        self.assertIsNone(map_progress_event({"prompt_id": "p1", "node": "125", "value": float("inf"), "max": 20}, "p1", {"125"}))
        self.assertIsNone(map_progress_event({"prompt_id": "p1", "node": "125", "value": True, "max": 20}, "p1", {"125"}))
        self.assertIsNone(map_progress_event({"prompt_id": "p1", "node": "125", "value": 5, "max": False}, "p1", {"125"}))
        self.assertIsNone(map_progress_event({"prompt_id": "p1", "node": "125", "value": "7", "max": 20}, "p1", {"125"}))

    def test_matrix_l_non_dict_event(self):
        self.assertIsNone(map_progress_event(None, "p1", {"125"}))
        self.assertIsNone(map_progress_event("string", "p1", {"125"}))


class JobPublicProgressTests(unittest.TestCase):
    def _make_job(self, state="RUNNING"):
        req = MagicMock()
        req.public.return_value = {"prompt": "test"}
        req.references = MagicMock()
        return Job(
            job_id="j1",
            request=req,
            created_at="2026-09-12T00:00:00Z",
            created_epoch=time.time(),
            prompt_id="p1",
            state=state,
            sampler_node_ids={"125"},
            progress={"kind": "sampling", "value": 7, "max": 20, "percent": 35},
        )

    def test_running_job_exposes_progress(self):
        job = self._make_job("RUNNING")
        self.assertEqual(
            job.public()["progress"],
            {"kind": "sampling", "value": 7, "max": 20, "percent": 35},
        )

    def test_terminal_jobs_hide_progress(self):
        for terminal in ("COMPLETED", "FAILED", "CANCELLED"):
            job = self._make_job(terminal)
            self.assertIsNone(job.public()["progress"])

    def test_disconnected_job_hides_progress(self):
        job = self._make_job("DISCONNECTED")
        self.assertIsNone(job.public()["progress"])

    def test_queued_job_hides_progress(self):
        job = self._make_job("QUEUED")
        self.assertIsNone(job.public()["progress"])


class MultiJobStaleEventTests(unittest.TestCase):
    def test_stale_event_isolation(self):
        session = H1ASession("http://127.0.0.1:8188", REPO_ROOT / "scratch_output")

        req_a = MagicMock()
        req_a.public.return_value = {}
        req_a.references = MagicMock()
        job_a = Job(
            job_id="ja",
            request=req_a,
            created_at="2026-09-12T00:00:00Z",
            created_epoch=time.time(),
            prompt_id="prompt-a",
            state="COMPLETED",
            sampler_node_ids={"125"},
        )

        req_b = MagicMock()
        req_b.public.return_value = {}
        req_b.references = MagicMock()
        job_b = Job(
            job_id="jb",
            request=req_b,
            created_at="2026-09-12T00:00:00Z",
            created_epoch=time.time(),
            prompt_id="prompt-b",
            state="RUNNING",
            sampler_node_ids={"42"},
        )

        session.jobs["ja"] = job_a
        session.jobs["jb"] = job_b

        # Event for prompt-a arrives late: must NOT affect job_b!
        session._handle_native_progress(
            "prompt-a",
            "125",
            {"prompt_id": "prompt-a", "node": "125", "value": 10, "max": 20},
        )
        self.assertIsNone(job_b.progress)
        self.assertIsNone(job_b.public()["progress"])

        # Event for prompt-b arrives with wrong node: must be ignored!
        session._handle_native_progress(
            "prompt-b",
            "125",
            {"prompt_id": "prompt-b", "node": "125", "value": 10, "max": 20},
        )
        self.assertIsNone(job_b.progress)

        # Event for prompt-b with correct node 42: updates job_b!
        session._handle_native_progress(
            "prompt-b",
            "42",
            {"prompt_id": "prompt-b", "node": "42", "value": 14, "max": 20},
        )
        self.assertEqual(job_b.progress["percent"], 70)
        self.assertEqual(job_b.public()["progress"]["percent"], 70)


class FakeWebSocketIntegrationTests(unittest.TestCase):
    def test_loopback_ws_flow(self):
        async def run_integration():
            messages_to_send = [
                {"type": "status", "data": {}},
                {"type": "progress", "data": {"prompt_id": "p-int", "node": "125", "value": 7, "max": 20}},
                {"type": "progress", "data": {"prompt_id": "p-int", "node": "122", "value": 1, "max": 1}},
                {"type": "progress", "data": {"prompt_id": "p-int", "node": "125", "value": 20, "max": 20}},
            ]

            async def ws_handler(request):
                ws = web.WebSocketResponse()
                await ws.prepare(request)
                for m in messages_to_send:
                    await ws.send_json(m)
                    await asyncio.sleep(0.02)
                await asyncio.sleep(0.1)
                await ws.close()
                return ws

            app = web.Application()
            app.router.add_get("/ws", ws_handler)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "127.0.0.1", 9876)
            await site.start()

            session = H1ASession("http://127.0.0.1:9876", REPO_ROOT / "scratch_output")
            req = MagicMock()
            req.public.return_value = {}
            req.references = MagicMock()
            job = Job(
                job_id="j-int",
                request=req,
                created_at="2026-09-12T00:00:00Z",
                created_epoch=time.time(),
                prompt_id="p-int",
                state="RUNNING",
                sampler_node_ids={"125"},
            )
            session.jobs["j-int"] = job

            listener = NativeProgressListener(
                base_url="http://127.0.0.1:9876",
                client_id="test-client-int",
                on_progress=session._handle_native_progress,
                on_disconnect=session._handle_progress_disconnect,
                reconnect_interval=0.2,
            )
            listener.start()

            for _ in range(50):
                if job.progress and job.progress["percent"] == 100:
                    break
                await asyncio.sleep(0.05)

            self.assertIsNotNone(job.progress)
            self.assertEqual(job.progress["percent"], 100)
            self.assertEqual(job.state, "RUNNING")

            for _ in range(50):
                if job.progress is None:
                    break
                await asyncio.sleep(0.05)

            self.assertIsNone(job.progress)
            self.assertEqual(job.state, "RUNNING")

            listener.stop()
            await runner.cleanup()

        asyncio.run(run_integration())


if __name__ == "__main__":
    unittest.main()

