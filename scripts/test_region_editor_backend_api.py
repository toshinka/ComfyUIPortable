import json
import urllib.request
import time
import os
import sys

"""
test_region_editor_backend_api.py
=================================
Tegaki Manga Region Editor の Backend Node 実行および画像生成APIテスト。
(旧称: test_workflow_07.py から役割を実態に合わせて再定義)
ComfyUIサーバーへ直接 REST API 形式のプロンプトを送信し、
TegakiMangaRegionEditor ノードが正しくプレビュー画像を生成できるかを検証します。
"""

api_prompt = {
    "1": {
        "class_type": "TegakiMangaRegionEditor",
        "inputs": {
            "panel_count": 3,
            "canvas_width": 832,
            "canvas_height": 1216,
            "global_prompt": "manga page, monochrome, expressive linework, high contrast",
            "region_spec_data": "{}"
        }
    },
    "2": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "Tegaki/RegionEditor_Test",
            "images": ["1", 3]  # slot 3 is preview_image
        }
    }
}

def test_api_execution():
    print("================================================================================")
    print("Tegaki Manga Region Editor Backend API Execution Test")
    print("================================================================================")

    data = json.dumps({"prompt": api_prompt}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            prompt_id = res_json.get("prompt_id")
            print(f"Queue successful! Prompt ID: {prompt_id}")
    except Exception as e:
        print(f"[ERROR] Failed to queue prompt to ComfyUI (Server running?): {e}")
        return 1

    print("Polling execution status...")
    start_time = time.time()
    while time.time() - start_time < 60:
        time.sleep(2)
        history_req = urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}")
        try:
            with urllib.request.urlopen(history_req) as resp:
                hist = json.loads(resp.read().decode("utf-8"))
                if prompt_id in hist:
                    status = hist[prompt_id].get("status", {})
                    completed = status.get("completed", False)
                    outputs = hist[prompt_id].get("outputs", {})
                    if completed or "2" in outputs:
                        images = outputs.get("2", {}).get("images", [])
                        print(f"[SUCCESS] Execution completed! Output preview: {images}")
                        return 0
                    if status.get("status_str") == "error":
                        print(f"[ERROR] Node execution error: {status.get('messages')}")
                        return 1
        except Exception as e:
            print(f"Polling warning: {e}")

    print("[ERROR] Timed out waiting for node execution.")
    return 1

if __name__ == "__main__":
    sys.exit(test_api_execution())
