import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import subprocess

COMFY_URL = "http://127.0.0.1:8188"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec


def is_comfy_running() -> bool:
    try:
        req = urllib.request.Request(f"{COMFY_URL}/system_stats")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_comfy_server(timeout: int = 60):
    if is_comfy_running():
        print("  [ComfyUI] Server is already running.")
        return None

    print("  [ComfyUI] Starting embedded server...")
    py_exe = os.path.join(ROOT_DIR, "python_embeded", "python.exe")
    comfy_main = os.path.join(ROOT_DIR, "ComfyUI", "main.py")
    cmd = [py_exe, comfy_main, "--windows-standalone-build", "--listen", "127.0.0.1", "--port", "8188"]

    proc = subprocess.Popen(cmd, cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    start = time.time()
    while time.time() - start < timeout:
        if is_comfy_running():
            print(f"  [ComfyUI] Server started successfully in {time.time() - start:.1f}s.")
            return proc
        time.sleep(2)
    raise TimeoutError("Failed to start ComfyUI server within timeout.")


def http_post(endpoint: str, payload: dict):
    url = f"{COMFY_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        return e.code, body


def run_http_route_tests():
    print("================================================================================")
    print("Running Runtime HTTP Route Smoke Tests (Phase 3D-0 Preflight Gate)")
    print("================================================================================")

    server_proc = start_comfy_server()
    try:
        # 1. Test POST /tegaki/panel-layout/validate (Valid 200)
        print("\n--- 1. Testing /tegaki/panel-layout/validate (Valid Spec -> 200 OK) ---")
        spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        status, body = http_post("/tegaki/panel-layout/validate", {"spec": spec})
        assert status == 200, f"Expected 200, got {status}"
        assert body.get("ok") is True, f"Expected ok: True, got {body}"
        assert "topology_summary" in body, "Expected topology_summary in response"
        assert body["topology_summary"]["panel_count"] == 3
        print(f"  Status: {status}, Panels: {body['topology_summary']['panel_count']} [PASSED]")

        # 2. Test POST /tegaki/panel-layout/validate (Invalid 400)
        print("\n--- 2. Testing /tegaki/panel-layout/validate (Invalid Spec -> 400 Bad Request) ---")
        invalid_spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
        invalid_spec["vertices"][0]["x"] = 1.35  # Outside [0, 1]
        status, body = http_post("/tegaki/panel-layout/validate", {"spec": invalid_spec})
        assert status == 400, f"Expected 400, got {status}"
        assert body.get("ok") is False, f"Expected ok: False, got {body}"
        assert "error" in body, "Expected error in response"
        print(f"  Status: {status}, Error: {body['error'][:60]}... [PASSED]")

        # 3. Test POST /tegaki/panel-layout/validate (Missing fields -> 400)
        print("\n--- 3. Testing /tegaki/panel-layout/validate (Missing 'spec' -> 400 Bad Request) ---")
        status, body = http_post("/tegaki/panel-layout/validate", {})
        assert status == 400, f"Expected 400, got {status}"
        assert body.get("ok") is False
        print(f"  Status: {status}, Error: {body['error']} [PASSED]")

        # 4. Test POST /tegaki/panel-layout/split (Valid 200)
        print("\n--- 4. Testing /tegaki/panel-layout/split (Valid Split -> 200 OK) ---")
        base_spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
        status, body = http_post("/tegaki/panel-layout/split", {
            "spec": base_spec,
            "panel_id": "p1",
            "split_mode": "horizontal",
            "split_ratio": 0.5
        })
        assert status == 200, f"Expected 200, got {status}"
        assert body.get("ok") is True
        res_spec = body.get("spec")
        assert len(res_spec["panels"]) == 2, f"Expected 2 panels, got {len(res_spec['panels'])}"
        assert body["topology_summary"]["status"] == "VALID"
        print(f"  Status: {status}, Result Panels: {len(res_spec['panels'])}, Topology: {body['topology_summary']['status']} [PASSED]")

        # 5. Test POST /tegaki/panel-layout/split (Diagonal Split -> 200 OK)
        print("\n--- 5. Testing /tegaki/panel-layout/split (Diagonal Split -> 200 OK) ---")
        status, body = http_post("/tegaki/panel-layout/split", {
            "spec": base_spec,
            "panel_id": "p1",
            "split_mode": "diag_slash",
            "split_ratio": 0.5
        })
        assert status == 200, f"Expected 200, got {status}"
        assert body.get("ok") is True
        print(f"  Status: {status}, Result Panels: {len(body['spec']['panels'])} [PASSED]")

        # 6. Test POST /tegaki/panel-layout/split (Missing parameters -> 400)
        print("\n--- 6. Testing /tegaki/panel-layout/split (Missing panel_id -> 400 Bad Request) ---")
        status, body = http_post("/tegaki/panel-layout/split", {
            "spec": base_spec
        })
        assert status == 400, f"Expected 400, got {status}"
        assert body.get("ok") is False
        print(f"  Status: {status}, Error: {body['error']} [PASSED]")

        print("\n================================================================================")
        print("[SUCCESS] ALL 6 RUNTIME HTTP ROUTE SMOKE TESTS PASSED!")
        print("================================================================================")
        return 0

    finally:
        # サーバーをテスト起動した場合は停止せず維持するか、呼び出し元の運用に任せる
        pass


if __name__ == "__main__":
    sys.exit(run_http_route_tests())
