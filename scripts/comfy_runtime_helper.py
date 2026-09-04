"""
ComfyUI Runtime Helper with Breaker & Lifecycle Management (Phase 3E)
====================================================================
Provides safe prompt queueing, execution waiting with timeout breaker,
and deterministic server lifecycle management so processes are NEVER
orphaned or left running indefinitely.
"""

import os
import sys
import time
import json
import socket
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

COMFY_HOST = "127.0.0.1"
COMFY_PORT = 8188
COMFY_URL = f"http://{COMFY_HOST}:{COMFY_PORT}"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = os.path.join(ROOT_DIR, "python_embeded", "python.exe")
COMFY_MAIN = os.path.join(ROOT_DIR, "ComfyUI", "main.py")

_LAUNCHED_SERVER_PROCESS = None
_SERVER_LOG_FILE = None


def is_port_open(host: str = COMFY_HOST, port: int = COMFY_PORT) -> bool:
    """Checks if ComfyUI port is actively accepting connections."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def ensure_server(timeout: int = 90):
    """
    Ensures ComfyUI server is running and accepting API requests.
    If not running, starts server as a subprocess and tracks it for cleanup.
    Output is streamed to output/comfy_server_runtime.log to avoid pipe deadlocks.
    """
    global _LAUNCHED_SERVER_PROCESS, _SERVER_LOG_FILE
    if is_port_open():
        print(f"[ComfyRuntimeHelper] Server is already running on port {COMFY_PORT}.")
        return

    print(f"[ComfyRuntimeHelper] Starting ComfyUI server on port {COMFY_PORT}...")
    log_dir = os.path.join(ROOT_DIR, "output")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "comfy_server_runtime.log")
    _SERVER_LOG_FILE = open(log_path, "w", encoding="utf-8", buffering=1)

    cmd = [
        PYTHON_EXE,
        "-u",
        "-s",
        COMFY_MAIN,
        "--windows-standalone-build",
        "--listen",
        COMFY_HOST,
        "--port",
        str(COMFY_PORT)
    ]
    _LAUNCHED_SERVER_PROCESS = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=_SERVER_LOG_FILE,
        stderr=subprocess.STDOUT,
        text=True
    )

    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open():
            # Verify HTTP response
            try:
                with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=2) as resp:
                    if resp.status == 200:
                        print(f"[ComfyRuntimeHelper] Server started and ready in {time.time() - start_time:.1f}s.")
                        return
            except Exception:
                pass
        time.sleep(1.5)

    raise TimeoutError(f"[ComfyRuntimeHelper] Server failed to start within {timeout}s.")


def stop_server():
    """Stops the ComfyUI server if it was launched by this helper."""
    global _LAUNCHED_SERVER_PROCESS, _SERVER_LOG_FILE
    if _LAUNCHED_SERVER_PROCESS is not None:
        print("[ComfyRuntimeHelper] Stopping launched ComfyUI server...")
        pid = _LAUNCHED_SERVER_PROCESS.pid
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            else:
                _LAUNCHED_SERVER_PROCESS.terminate()
                _LAUNCHED_SERVER_PROCESS.wait(timeout=5)
        except Exception:
            try:
                _LAUNCHED_SERVER_PROCESS.kill()
            except Exception:
                pass
        _LAUNCHED_SERVER_PROCESS = None
        if _SERVER_LOG_FILE is not None:
            try:
                _SERVER_LOG_FILE.close()
            except Exception:
                pass
            _SERVER_LOG_FILE = None
        print(f"[ComfyRuntimeHelper] Server process (PID {pid}) stopped successfully.")


def queue_prompt(prompt_workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Queues a prompt workflow to ComfyUI /prompt endpoint."""
    payload = {"prompt": prompt_workflow}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"[ComfyRuntimeHelper] API Error: {err_body}")
        raise


def wait_for_prompt(prompt_id: str, timeout: int = 180) -> Dict[str, Any]:
    """
    Waits for prompt completion with timeout breaker.
    Raises TimeoutError if execution exceeds timeout.
    """
    start_time = time.time()
    last_print = start_time
    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=5) as resp:
                history = json.loads(resp.read().decode("utf-8"))
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                print(f"[ComfyRuntimeHelper] Prompt {prompt_id} completed in {elapsed:.1f}s.")
                return outputs
        except Exception:
            pass

        if time.time() - last_print > 15:
            print(f"[ComfyRuntimeHelper] Waiting for prompt {prompt_id}... ({elapsed:.0f}s elapsed / {timeout}s timeout breaker)")
            last_print = time.time()

        time.sleep(2)

    raise TimeoutError(f"[ComfyRuntimeHelper] Breaker fired: Prompt {prompt_id} did not finish within {timeout}s.")


def get_image_file_path(outputs: Dict[str, Any], save_node_id: str) -> Optional[str]:
    """Resolves local disk file path from SaveImage output."""
    node_out = outputs.get(save_node_id, {})
    images = node_out.get("images", [])
    if not images:
        return None
    img_info = images[0]
    filename = img_info["filename"]
    subfolder = img_info.get("subfolder", "")
    folder_type = img_info.get("type", "output")
    base_folder = os.path.join(ROOT_DIR, "ComfyUI", folder_type)
    return os.path.join(base_folder, subfolder, filename)
