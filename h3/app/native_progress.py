from __future__ import annotations

import asyncio
import json
import logging
import math
import threading
from typing import Any, Callable, Mapping

import aiohttp

SAMPLER_CLASS_TYPES = frozenset({"SamplerCustomAdvanced"})

logger = logging.getLogger("h3.native_progress")


def discover_sampler_node_ids(
    graph: Mapping[str, Any] | None,
    target_classes: frozenset[str] = SAMPLER_CLASS_TYPES,
) -> set[str]:
    """Extract node IDs whose class_type matches the target sampler classes."""
    if not isinstance(graph, Mapping):
        return set()
    prompt_dict = graph.get("prompt") if "prompt" in graph and isinstance(graph.get("prompt"), Mapping) else graph
    sampler_ids: set[str] = set()
    for node_id, node_def in prompt_dict.items():
        if isinstance(node_def, Mapping):
            class_type = node_def.get("class_type")
            if class_type in target_classes:
                sampler_ids.add(str(node_id))
    return sampler_ids


def map_progress_event(
    event_data: Mapping[str, Any] | None,
    expected_prompt_id: str | None,
    allowed_sampler_node_ids: set[str] | frozenset[str] | None,
) -> dict[str, Any] | None:
    """Pure validator for Native ComfyUI progress events."""
    if not isinstance(event_data, Mapping):
        return None
    if not expected_prompt_id or not allowed_sampler_node_ids:
        return None

    prompt_id = event_data.get("prompt_id")
    if not isinstance(prompt_id, str) or prompt_id != expected_prompt_id:
        return None

    node_id = event_data.get("node")
    if node_id is None or str(node_id) not in allowed_sampler_node_ids:
        return None

    raw_value = event_data.get("value")
    raw_max = event_data.get("max")

    if isinstance(raw_value, bool) or isinstance(raw_max, bool):
        return None
    if not isinstance(raw_value, (int, float)) or not isinstance(raw_max, (int, float)):
        return None
    if math.isnan(raw_value) or math.isinf(raw_value):
        return None
    if math.isnan(raw_max) or math.isinf(raw_max):
        return None
    if raw_max <= 0:
        return None
    if raw_value < 0 or raw_value > raw_max:
        return None

    percent = int(math.floor((float(raw_value) / float(raw_max)) * 100.0))
    percent = max(0, min(100, percent))

    return {
        "kind": "sampling",
        "value": int(raw_value) if isinstance(raw_value, int) or (isinstance(raw_value, float) and raw_value.is_integer()) else raw_value,
        "max": int(raw_max) if isinstance(raw_max, int) or (isinstance(raw_max, float) and raw_max.is_integer()) else raw_max,
        "percent": percent,
    }


class NativeProgressListener:
    """Background client connecting to Native ComfyUI /ws?clientId=..."""

    def __init__(
        self,
        base_url: str,
        client_id: str,
        on_progress: Callable[[str, str, dict[str, Any]], None],
        on_disconnect: Callable[[], None],
        reconnect_interval: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.on_progress = on_progress
        self.on_disconnect = on_disconnect
        self.reconnect_interval = reconnect_interval

        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def ws_url(self) -> str:
        url = self.base_url
        if url.startswith("http://"):
            url = "ws://" + url[7:]
        elif url.startswith("https://"):
            url = "wss://" + url[8:]
        elif not url.startswith("ws://") and not url.startswith("wss://"):
            url = "ws://" + url
        return f"{url}/ws?clientId={self.client_id}"

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_requested.clear()
        self._thread = threading.Thread(
            target=self._run_thread,
            name="h3-native-progress-listener",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop_requested.set()
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._cancel_all_tasks)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self.on_disconnect()

    def _cancel_all_tasks(self) -> None:
        if self._loop is not None:
            for task in asyncio.all_tasks(self._loop):
                task.cancel()

    def _run_thread(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._listen_loop())
        except asyncio.CancelledError:
            pass
        finally:
            try:
                self._cancel_all_tasks()
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            loop.close()
            self._loop = None

    async def _listen_loop(self) -> None:
        while not self._stop_requested.is_set():
            try:
                timeout = aiohttp.ClientTimeout(total=5.0)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.ws_connect(self.ws_url) as ws:
                        async for msg in ws:
                            if self._stop_requested.is_set():
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    payload = json.loads(msg.data)
                                    if isinstance(payload, Mapping) and payload.get("type") == "progress":
                                        data = payload.get("data")
                                        if isinstance(data, Mapping):
                                            p_id = data.get("prompt_id")
                                            n_id = data.get("node")
                                            if isinstance(p_id, str) and n_id is not None:
                                                self.on_progress(p_id, str(n_id), data)
                                except Exception:
                                    pass
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
            except Exception:
                pass

            self.on_disconnect()

            if self._stop_requested.is_set():
                break

            try:
                for _ in range(int(self.reconnect_interval * 10)):
                    if self._stop_requested.is_set():
                        break
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break

