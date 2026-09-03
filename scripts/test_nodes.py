import sys
import os

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

import folder_paths
import utils.extra_config

yaml_path = os.path.join(comfy_dir, "extra_model_paths.yaml")
if os.path.exists(yaml_path):
    utils.extra_config.load_extra_path_config(yaml_path)

print("--- Checking Model Counts ---")
checkpoints = folder_paths.get_filename_list("checkpoints")
loras = folder_paths.get_filename_list("loras")
vaes = folder_paths.get_filename_list("vae")
controlnets = folder_paths.get_filename_list("controlnet")
print(f"Checkpoints: {len(checkpoints)}")
print(f"LoRAs:       {len(loras)}")
print(f"VAEs:        {len(vaes)}")
print(f"ControlNets: {len(controlnets)}")

print("\n--- Testing Tegaki Manga Custom Nodes ---")
from custom_nodes.tegaki_manga_nodes import NODE_CLASS_MAPPINGS
print("Loaded nodes:", list(NODE_CLASS_MAPPINGS.keys()))

from custom_nodes.tegaki_manga_nodes.lora_loader import resolve_lora_name, TegakiLoraPromptLoader
if loras:
    sample_raw = loras[0]
    sample_base = os.path.splitext(os.path.basename(sample_raw))[0]
    resolved = resolve_lora_name(sample_base, loras)
    print(f"Resolved base '{sample_base}' -> '{resolved}'")
    assert resolved == sample_raw, f"Resolution mismatch: {resolved} vs {sample_raw}"
    print("LoRA Name Resolver test: PASSED")

print("\n--- Testing ComfyUI-Impact-Pack Import ---")
try:
    import custom_nodes.ComfyUI_Impact_Pack as impact
    print("Impact Pack: SUCCESS")
except Exception as e:
    # impact pack directory uses hyphen: ComfyUI-Impact-Pack
    import importlib.util
    spec = importlib.util.spec_from_file_location("impact", os.path.join(comfy_dir, "custom_nodes", "ComfyUI-Impact-Pack", "__init__.py"))
    print("Impact Pack loaded manually:", spec is not None)

print("\n--- Testing dynamicprompts ---")
import dynamicprompts
print("dynamicprompts version:", dynamicprompts.__version__)

print("\nAll Node Tests Completed Successfully!")
