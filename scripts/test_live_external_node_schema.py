"""
Live External Node Schema Verification (Phase 3F)
================================================
Fetches and validates the schema of critical external nodes (ToBasicPipe,
KSamplerAdvancedProvider, RegionalSampler) from live ComfyUI /object_info
to detect schema drift, unlinked required inputs, and widget ordering mismatches.
"""

import os
import sys
import json
import urllib.request
from typing import Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts import comfy_runtime_helper

OBJECT_INFO_URL = f"{comfy_runtime_helper.COMFY_URL}/object_info"


def fetch_live_object_info() -> Dict[str, Any]:
    """Ensures ComfyUI server is running and fetches /object_info for critical nodes."""
    comfy_runtime_helper.ensure_server(timeout=90)
    
    target_nodes = ["ToBasicPipe", "KSamplerAdvancedProvider", "RegionalSampler"]
    node_schemas = {}
    
    for node_name in target_nodes:
        url = f"{OBJECT_INFO_URL}/{node_name}"
        req = urllib.request.Request(url, headers={"User-Agent": "TegakiLiveSchemaTest/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            if node_name in data:
                node_schemas[node_name] = data[node_name]
            else:
                raise KeyError(f"Node '{node_name}' not found in live /object_info response")
                
    return node_schemas


def compute_frontend_widget_sequence(node_schema: Dict[str, Any]) -> list:
    """
    Simulates ComfyUI frontend logic for determining widget sequence
    from node schema returned by /object_info.
    
    Frontend rules:
    - Primitive types (INT, FLOAT, STRING, BOOLEAN, combo list) become widgets.
    - Non-primitive types (LATENT, MODEL, CLIP, VAE, CONDITIONING, BASIC_PIPE, etc.) become socket inputs.
    - Inputs named 'seed' or 'noise_seed' automatically gain an inserted 'control_after_generate' combo widget immediately following.
    """
    input_data = node_schema.get("input", {})
    req = input_data.get("required", {})
    opt = input_data.get("optional", {})
    
    # Primitive types check
    non_widget_types = {
        "LATENT", "MODEL", "CLIP", "VAE", "CONDITIONING",
        "BASIC_PIPE", "KSAMPLER_ADVANCED", "REGIONAL_PROMPTS",
        "SAMPLER", "SCHEDULER_FUNC", "IMAGE", "MASK"
    }
    
    widgets = []
    all_inputs = list(req.items()) + list(opt.items())
    for name, spec in all_inputs:
        t = spec[0] if isinstance(spec, (tuple, list)) else spec
        if isinstance(t, list):
            # Combo list -> widget
            widgets.append({"name": name, "type": "combo", "options": t})
        elif isinstance(t, str):
            if t.upper() not in non_widget_types:
                widgets.append({"name": name, "type": t, "spec": spec[1] if len(spec) > 1 else {}})
                if name in ("seed", "noise_seed"):
                    widgets.append({
                        "name": f"{name}_control_after_generate",
                        "type": "control_after_generate",
                        "options": ["fixed", "increment", "decrement", "randomize"]
                    })
    return widgets


def run_schema_verification():
    print("================================================================================")
    print("Phase 3F Live External Node Schema Verification (/object_info)")
    print("================================================================================")
    
    try:
        nodes = fetch_live_object_info()
        
        # 1. Test ToBasicPipe
        print("\n--- 1. Testing ToBasicPipe Live Schema ---")
        tbp_info = nodes["ToBasicPipe"]
        tbp_req = tbp_info.get("input", {}).get("required", {})
        expected_tbp_req = ["model", "clip", "vae", "positive", "negative"]
        assert list(tbp_req.keys()) == expected_tbp_req, f"ToBasicPipe required inputs mismatch: {list(tbp_req.keys())}"
        print(f"  ToBasicPipe Required Inputs: {list(tbp_req.keys())} [OK]")
        assert tbp_req["clip"][0] == "CLIP", f"ToBasicPipe.clip must be type CLIP, got {tbp_req['clip']}"
        print(f"  ToBasicPipe.clip Socket Type: {tbp_req['clip'][0]} [OK]")
        tbp_widgets = compute_frontend_widget_sequence(tbp_info)
        assert len(tbp_widgets) == 0, f"ToBasicPipe should have 0 widgets, got {len(tbp_widgets)}"
        print(f"  ToBasicPipe Frontend Widgets: {len(tbp_widgets)} [OK]")

        # 2. Test KSamplerAdvancedProvider
        print("\n--- 2. Testing KSamplerAdvancedProvider Live Schema ---")
        ks_info = nodes["KSamplerAdvancedProvider"]
        ks_req = ks_info.get("input", {}).get("required", {})
        expected_ks_req = ["cfg", "sampler_name", "scheduler", "sigma_factor", "basic_pipe"]
        assert list(ks_req.keys()) == expected_ks_req, f"KSamplerAdvancedProvider inputs mismatch: {list(ks_req.keys())}"
        print(f"  KSamplerAdvancedProvider Required Inputs: {list(ks_req.keys())} [OK]")
        ks_widgets = compute_frontend_widget_sequence(ks_info)
        expected_ks_widget_names = ["cfg", "sampler_name", "scheduler", "sigma_factor"]
        assert [w["name"] for w in ks_widgets] == expected_ks_widget_names
        print(f"  KSamplerAdvancedProvider Widgets: {[w['name'] for w in ks_widgets]} (Count: {len(ks_widgets)}) [OK]")

        # 3. Test RegionalSampler
        print("\n--- 3. Testing RegionalSampler Live Schema ---")
        rs_info = nodes["RegionalSampler"]
        rs_req = rs_info.get("input", {}).get("required", {})
        expected_rs_req = [
            "seed", "seed_2nd", "seed_2nd_mode", "steps", "base_only_steps", "denoise",
            "samples", "base_sampler", "regional_prompts", "overlap_factor",
            "restore_latent", "additional_mode", "additional_sampler", "additional_sigma_ratio"
        ]
        assert list(rs_req.keys()) == expected_rs_req, f"RegionalSampler required mismatch: {list(rs_req.keys())}"
        print(f"  RegionalSampler Required Inputs: {len(rs_req)} inputs verified [OK]")
        
        rs_widgets = compute_frontend_widget_sequence(rs_info)
        print(f"  RegionalSampler Frontend Computed Widgets: {len(rs_widgets)}")
        for idx, w in enumerate(rs_widgets):
            print(f"    [{idx:02d}] {w['name']} ({w['type']})")
        
        assert len(rs_widgets) == 12, f"RegionalSampler MUST have 12 frontend widgets, got {len(rs_widgets)}"
        assert rs_widgets[0]["name"] == "seed"
        assert rs_widgets[1]["name"] == "seed_control_after_generate"
        assert rs_widgets[2]["name"] == "seed_2nd"
        assert rs_widgets[3]["name"] == "seed_2nd_mode"
        assert rs_widgets[4]["name"] == "steps"
        assert rs_widgets[5]["name"] == "base_only_steps"
        assert rs_widgets[6]["name"] == "denoise"
        assert rs_widgets[7]["name"] == "overlap_factor"
        assert rs_widgets[8]["name"] == "restore_latent"
        assert rs_widgets[9]["name"] == "additional_mode"
        assert rs_widgets[10]["name"] == "additional_sampler"
        assert rs_widgets[11]["name"] == "additional_sigma_ratio"
        print("  [OK] RegionalSampler 12-Widget Sequence and Seed Control Verified!")

        print("\n================================================================================")
        print("[SUCCESS] ALL EXTERNAL NODE LIVE SCHEMAS VERIFIED SUCCESSFULLY!")
        print("================================================================================")
    finally:
        # STRICT LIFECYCLE: Stop server immediately after test to avoid leaving background process
        comfy_runtime_helper.stop_server()


if __name__ == "__main__":
    run_schema_verification()
