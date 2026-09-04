"""
Tegaki Manga Generation Profile Contract (Phase 3H)
===================================================
Defines standardized generation profiles for manga regional sampling:
1. "reference" (Canonical SSOT):
   - 20 steps, CFG 7.0, Euler / Normal, base_only_steps=2
   - No acceleration LoRA
2. "fast_draft_12" (Accepted Fast Draft):
   - 12 steps, CFG 6.0, Euler / Normal, base_only_steps=2
   - ByteDance Hyper-SDXL 12-step CFG LoRA (調整\\Hyper-SDXL-12steps-CFG-lora.safetensors)

Note: Fast-8 was REJECTED in Phase 3G due to mask boundary tile seams
and anatomical edge clipping, and is deliberately excluded from standard profiles.
"""

import copy
from typing import Dict, Any, Optional, List


# Relative asset path resolved via ComfyUI extra_model_paths
LORA_HYPER_SDXL_12STEP = "調整\\Hyper-SDXL-12steps-CFG-lora.safetensors"

PROFILES: Dict[str, Dict[str, Any]] = {
    "reference": {
        "name": "reference",
        "label": "Reference Mode (20 steps, CFG 7.0, SSOT)",
        "steps": 20,
        "cfg": 7.0,
        "sampler": "euler",
        "scheduler": "normal",
        "base_only_steps": 2,
        "denoise": 1.0,
        "lora_name": None,
        "lora_strength_model": 1.0,
        "lora_strength_clip": 1.0,
    },
    "fast_draft_12": {
        "name": "fast_draft_12",
        "label": "Fast Draft Profile (12 steps, CFG 6.0, Hyper-SDXL)",
        "steps": 12,
        "cfg": 6.0,
        "sampler": "euler",
        "scheduler": "normal",
        "base_only_steps": 2,
        "denoise": 1.0,
        "lora_name": LORA_HYPER_SDXL_12STEP,
        "lora_strength_model": 1.0,
        "lora_strength_clip": 1.0,
    }
}


def get_profile(name: str) -> Dict[str, Any]:
    """Retrieves generation profile configuration by name."""
    profile_key = name.lower().strip()
    if profile_key not in PROFILES:
        valid_keys = list(PROFILES.keys())
        raise KeyError(f"Unknown generation profile: '{name}'. Valid profiles: {valid_keys}")
    return copy.deepcopy(PROFILES[profile_key])


def list_profiles() -> List[Dict[str, Any]]:
    """Returns list of all available generation profile definitions."""
    return [copy.deepcopy(v) for v in PROFILES.values()]


def validate_generation_profile_name(name: str) -> bool:
    """Checks if given profile name is registered."""
    return name.lower().strip() in PROFILES


def apply_profile_to_prompt(prompt_workflow: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    """
    Applies a generation profile to a ComfyUI prompt workflow dictionary.
    Adjusts steps and CFG across RegionalSampler, KSampler, and KSamplerAdvancedProvider.
    Injects LoraLoader for fast_draft_12 if a LoRA is specified in the profile.
    """
    profile = get_profile(profile_name)
    p = copy.deepcopy(prompt_workflow)

    target_steps = profile["steps"]
    target_cfg = profile["cfg"]
    target_base_steps = profile["base_only_steps"]
    lora_name = profile["lora_name"]

    # 1. Inject or wire LoRA if specified
    if lora_name:
        ckpt_nid = None
        for nid, nd in p.items():
            if nd.get("class_type") in ("CheckpointLoaderSimple", "CheckpointLoader"):
                ckpt_nid = nid
                break

        if ckpt_nid:
            lora_nid = "profile_hypersd_lora"
            p[lora_nid] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": [ckpt_nid, 0],
                    "clip": [ckpt_nid, 1],
                    "lora_name": lora_name,
                    "strength_model": profile["lora_strength_model"],
                    "strength_clip": profile["lora_strength_clip"]
                }
            }

            # Rewire nodes that consume MODEL and CLIP from CheckpointLoader
            for nid, nd in p.items():
                if nid == lora_nid:
                    continue
                for inp_name, inp_val in nd.get("inputs", {}).items():
                    if isinstance(inp_val, list) and len(inp_val) == 2:
                        src_node, src_slot = inp_val
                        if src_node == ckpt_nid:
                            if src_slot == 0:  # MODEL
                                nd["inputs"][inp_name] = [lora_nid, 0]
                            elif src_slot == 1:  # CLIP
                                nd["inputs"][inp_name] = [lora_nid, 1]

    # 2. Update sampling parameters
    for nid, nd in p.items():
        ctype = nd.get("class_type")
        inputs = nd.get("inputs", {})
        if ctype == "RegionalSampler":
            inputs["steps"] = target_steps
            if "base_only_steps" in inputs:
                inputs["base_only_steps"] = target_base_steps
        elif ctype == "KSamplerAdvancedProvider":
            inputs["cfg"] = target_cfg
        elif ctype in ("KSampler", "KSamplerAdvanced"):
            if "steps" in inputs:
                inputs["steps"] = target_steps
            if "cfg" in inputs:
                inputs["cfg"] = target_cfg

    return p
