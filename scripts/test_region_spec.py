import sys
import os
import json
import torch

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.region_editor import (
    TegakiMangaRegionEditor,
    default_region_spec,
    render_preview_image,
    render_mask_batch
)

print("--- Testing default_region_spec ---")
spec = default_region_spec(width=832, height=1216, panel_count=3, global_prompt="test prompt")
assert spec["version"] == 1, "Version must be 1"
assert spec["panel_count"] == 3, "Panel count must be 3"
assert len(spec["regions"]) == 6, "Must contain 6 regions"
print("default_region_spec: PASSED")

print("\n--- Testing render_preview_image ---")
img_tensor = render_preview_image(spec, 832, 1216)
print("Preview Image tensor shape:", img_tensor.shape)
assert isinstance(img_tensor, torch.Tensor), "Must be torch.Tensor"
assert img_tensor.shape == (1, 1216, 832, 3), f"Shape mismatch: {img_tensor.shape}"
assert img_tensor.min() >= 0.0 and img_tensor.max() <= 1.0, "Values must be normalized 0..1"
print("render_preview_image: PASSED")

print("\n--- Testing render_mask_batch ---")
mask_tensor = render_mask_batch(spec, 832, 1216)
print("Mask Batch tensor shape:", mask_tensor.shape)
assert isinstance(mask_tensor, torch.Tensor), "Must be torch.Tensor"
assert mask_tensor.shape == (3, 1216, 832), f"Expected 3 masks, got {mask_tensor.shape}"
print("render_mask_batch: PASSED")

print("\n--- Testing TegakiMangaRegionEditor Node execute ---")
editor = TegakiMangaRegionEditor()
spec_out, spec_json, global_p, preview, masks = editor.execute_editor(
    panel_count=4,
    canvas_width=832,
    canvas_height=1216,
    global_prompt="masterpiece, manga tone",
    region_spec_data="{}"
)

assert isinstance(spec_out, dict), "spec_out must be dict"
assert spec_out["panel_count"] == 4, "panel_count must be 4"
assert isinstance(spec_json, str), "spec_json must be str"
assert preview.shape == (1, 1216, 832, 3), "preview shape must match"
assert masks.shape == (4, 1216, 832), f"masks shape must be [4, 1216, 832], got {masks.shape}"
print("TegakiMangaRegionEditor execute: PASSED")

print("\n--- Testing State Preservation (JSON reload) ---")
saved_json = spec_json
editor2 = TegakiMangaRegionEditor()
spec_out2, spec_json2, _, _, _ = editor2.execute_editor(
    panel_count=4,
    canvas_width=832,
    canvas_height=1216,
    global_prompt="masterpiece, manga tone",
    region_spec_data=saved_json
)
assert spec_out2["regions"][0]["x"] == spec_out["regions"][0]["x"], "Coordinates must be preserved"
print("State Preservation test: PASSED")

print("\nALL REGION EDITOR TESTS PASSED SUCCESSFULLY!")
