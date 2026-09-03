import json
import urllib.request
import time
import os

prompt = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
        }
    },
    "2": {
        "class_type": "TegakiLoraPromptLoader",
        "inputs": {
            "model": ["1", 0],
            "clip": ["1", 1],
            "text": "masterpiece, best quality, 1girl, manga art style, cute smile, detailed ink lines,\n<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.7>"
        }
    },
    "3": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["2", 1],
            "text": ["2", 2]
        }
    },
    "4": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["2", 1],
            "text": "worst quality, low quality, deformed, blurry"
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "batch_size": 1,
            "height": 768,
            "width": 512
        }
    },
    "6": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 6.0,
            "denoise": 1.0,
            "latent_image": ["5", 0],
            "model": ["2", 0],
            "negative": ["4", 0],
            "positive": ["3", 0],
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "seed": 42,
            "steps": 15
        }
    },
    "7": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["6", 0],
            "vae": ["1", 2]
        }
    },
    "8": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "Tegaki/Txt2Img_Test",
            "images": ["7", 0]
        }
    }
}

print("Queueing test prompt to ComfyUI (http://127.0.0.1:8188/prompt)...")
data = json.dumps({"prompt": prompt}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        prompt_id = res_json.get("prompt_id")
        print(f"Prompt successfully queued! Prompt ID: {prompt_id}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)
except Exception as e:
    print(f"Error queueing prompt: {e}")
    exit(1)

# ポーリングして進捗と完了を確認
print("Waiting for generation to finish...")
start_time = time.time()
while time.time() - start_time < 180:
    time.sleep(3)
    history_req = urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}")
    try:
        with urllib.request.urlopen(history_req) as resp:
            hist = json.loads(resp.read().decode("utf-8"))
            if prompt_id in hist:
                status = hist[prompt_id].get("status", {})
                completed = status.get("completed", False)
                outputs = hist[prompt_id].get("outputs", {})
                print(f"Job status: {status}")
                if completed or "8" in outputs:
                    print("Generation completed successfully!")
                    images = outputs.get("8", {}).get("images", [])
                    print(f"Output images: {images}")
                    exit(0)
                if status.get("status_str") == "error":
                    print(f"Generation error: {status.get('messages')}")
                    exit(1)
    except Exception as e:
        print(f"Polling error: {e}")

print("Timed out waiting for generation.")
exit(1)
