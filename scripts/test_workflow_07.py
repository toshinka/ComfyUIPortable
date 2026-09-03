import json
import urllib.request
import time
import os

wf_path = os.path.abspath("workflows/07_MANGA_REGION_EDITOR_UI_TEST.json")
with open(wf_path, "r", encoding="utf-8") as f:
    wf = json.load(f)

# API形式のプロンプトに変換
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

print("Queueing Workflow 07 test to ComfyUI...")
data = json.dumps({"prompt": api_prompt}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        prompt_id = res_json.get("prompt_id")
        print(f"Workflow 07 queued! Prompt ID: {prompt_id}")
except Exception as e:
    print(f"Error queueing prompt: {e}")
    exit(1)

print("Waiting for execution...")
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
                    print("Workflow 07 execution successful!")
                    images = outputs.get("2", {}).get("images", [])
                    print(f"Output preview images: {images}")
                    exit(0)
                if status.get("status_str") == "error":
                    print(f"Execution error: {status.get('messages')}")
                    exit(1)
    except Exception as e:
        print(f"Polling error: {e}")

print("Timed out.")
exit(1)
