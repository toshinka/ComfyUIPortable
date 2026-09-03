import json
import urllib.request
import time
import shutil
import os

input_dir = os.path.abspath("ComfyUI/input")
os.makedirs(input_dir, exist_ok=True)

src_image = os.path.abspath("ComfyUI/output/Tegaki/Txt2Img_Test_00001_.png")
dest_image = os.path.join(input_dir, "i2i_source_test.png")
shutil.copy(src_image, dest_image)
print(f"Copied test image to {dest_image}")

i2i_prompt = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors"
        }
    },
    "2": {
        "class_type": "LoadImage",
        "inputs": {
            "image": "i2i_source_test.png"
        }
    },
    "3": {
        "class_type": "VAEEncode",
        "inputs": {
            "pixels": ["2", 0],
            "vae": ["1", 2]
        }
    },
    "4": {
        "class_type": "TegakiLoraPromptLoader",
        "inputs": {
            "model": ["1", 0],
            "clip": ["1", 1],
            "text": "masterpiece, best quality, refined linework, detailed manga art, highres"
        }
    },
    "5": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": ["4", 2]
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "worst quality, low quality, deformed, blurry"
        }
    },
    "7": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 6.0,
            "denoise": 0.60,
            "latent_image": ["3", 0],
            "model": ["4", 0],
            "negative": ["6", 0],
            "positive": ["5", 0],
            "sampler_name": "euler_ancestral",
            "scheduler": "normal",
            "seed": 12345,
            "steps": 15
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["7", 0],
            "vae": ["1", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "Tegaki/I2I_Test",
            "images": ["8", 0]
        }
    }
}

print("Queueing I2I test prompt to ComfyUI...")
data = json.dumps({"prompt": i2i_prompt}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        prompt_id = res_json.get("prompt_id")
        print(f"I2I Prompt successfully queued! Prompt ID: {prompt_id}")
except Exception as e:
    print(f"Error queueing I2I prompt: {e}")
    exit(1)

print("Waiting for I2I generation...")
start_time = time.time()
while time.time() - start_time < 120:
    time.sleep(2)
    history_req = urllib.request.Request(f"http://127.0.0.1:8188/history/{prompt_id}")
    try:
        with urllib.request.urlopen(history_req) as resp:
            hist = json.loads(resp.read().decode("utf-8"))
            if prompt_id in hist:
                status = hist[prompt_id].get("status", {})
                completed = status.get("completed", False)
                outputs = hist[prompt_id].get("outputs", {})
                if completed or "9" in outputs:
                    print("I2I Generation completed successfully!")
                    images = outputs.get("9", {}).get("images", [])
                    print(f"I2I Output images: {images}")
                    exit(0)
                if status.get("status_str") == "error":
                    print(f"I2I Error: {status.get('messages')}")
                    exit(1)
    except Exception as e:
        print(f"Polling error: {e}")

print("Timed out waiting for I2I.")
exit(1)
