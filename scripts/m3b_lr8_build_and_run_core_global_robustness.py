"""Build and execute the bounded M3B-LR8 Core CAST_GLOBAL robustness qualification."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ComfyUI"))

from scripts import comfy_runtime_helper  # noqa: E402
from custom_nodes.tegaki_manga_nodes.conditioning_builder import (  # noqa: E402
    TegakiMangaConditioningBuilder,
)
from custom_nodes.tegaki_manga_nodes.minimum_hand_scene_editor import (  # noqa: E402
    TegakiMinimumHandSceneEditor,
)

SOURCE_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json"
TARGET_WORKFLOW = ROOT / "workflows/manga/research/M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS.json"
CANONICAL_FILE = ROOT / "workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json"
EVIDENCE_DIR = ROOT / "docs/manga/verification/m3b_lr8"
EVIDENCE_LR7 = ROOT / "docs/manga/verification/m3b_lr7"
OUTPUT_DIRS = [ROOT / "ComfyUI/output", ROOT / "output"]

EXPECTED_CLEAN_GUIDE_SHA = "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a"
EXPECTED_CONTROLNET_SHA = "e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8"

SEEDS = [42, 77, 101, 202, 303, 404]
CONDITIONS = ["CAST_OFF", "CAST_CORE_GLOBAL"]


class StubClip:
    def tokenize(self, text: str) -> dict[str, str]:
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens: dict[str, str]) -> list[list[Any]]:
        import torch

        embedding = torch.zeros((1, 1, 1), dtype=torch.float32)
        return [[embedding, {"stub_text": tokens["text"]}]]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def find_latest_output_matching(prefix: str) -> Path:
    candidates: list[Path] = []
    for d in OUTPUT_DIRS:
        if d.exists():
            candidates.extend(d.glob(f"{prefix}_*.png"))
    if not candidates:
        raise FileNotFoundError(f"No output found matching prefix {prefix!r} in {OUTPUT_DIRS}")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def verify_cast_runtime(document: dict[str, Any]) -> dict[str, Any]:
    scene = document["pages"][0]["scenes"][0]
    if scene.get("input_mode") != "cast":
        raise AssertionError(f"Expected scene input_mode='cast', got {scene.get('input_mode')!r}")

    document_json = json.dumps(document, ensure_ascii=False)
    editor_result = TegakiMinimumHandSceneEditor().edit_and_compile(
        document_json=document_json,
        seed=42,
        style_template="Manga Monochrome",
        resolution="Portrait 832x1216",
    )
    plan = editor_result[0]
    panel = plan["panels"][0]
    characters = panel["characters"]
    expected_provenance = [("inst_1", "cast_1"), ("inst_2", "cast_2")]
    actual_provenance = [(c.get("instance_id"), c.get("character_id")) for c in characters]
    if len(characters) != 2 or actual_provenance != expected_provenance:
        raise AssertionError(f"CAST compile failed: {actual_provenance} vs {expected_provenance}")

    builder_result = TegakiMangaConditioningBuilder().build_conditioning(
        clip=StubClip(),
        page_compile_plan=plan,
        panel_strength=1.0,
        character_strength=1.0,
        set_cond_area="default",
        local_region_strength=1.0,
        mask_feather=0,
    )
    character_masks = builder_result[3]
    conditioning_debug = json.loads(builder_result[4])
    character_entries = conditioning_debug["entries"]["characters"]
    if int(character_masks.shape[0]) != 2 or len(character_entries) != 2:
        raise AssertionError(
            f"Character conditioning failed: masks={character_masks.shape[0]}, entries={len(character_entries)}"
        )

    return {
        "status": "PASS",
        "input_mode": "cast",
        "compiled_characters_count": len(characters),
        "compiled_characters": characters,
        "character_conditioning_entries_count": len(character_entries),
        "character_conditioning_entries": character_entries,
        "character_masks_count": int(character_masks.shape[0]),
    }


def verify_core_node_contract() -> None:
    import nodes

    if "ControlNetApplyAdvanced" not in nodes.NODE_CLASS_MAPPINGS:
        raise AssertionError("ControlNetApplyAdvanced not found in ComfyUI nodes.NODE_CLASS_MAPPINGS")

    cls = nodes.NODE_CLASS_MAPPINGS["ControlNetApplyAdvanced"]
    input_types = cls.INPUT_TYPES()
    required = input_types.get("required", {})
    expected_inputs = ["positive", "negative", "control_net", "image", "strength", "start_percent", "end_percent"]
    for inp in expected_inputs:
        if inp not in required:
            raise AssertionError(f"ControlNetApplyAdvanced missing required input: {inp}")

    print("[LR8 Contract Gate] ControlNetApplyAdvanced contract verified successfully.")


def build_research_workflow() -> dict[str, Any]:
    raw_source = json.loads(SOURCE_WORKFLOW.read_text(encoding="utf-8"))
    source_prompt = raw_source["prompt"]
    doc = json.loads(source_prompt["1"]["inputs"]["document_json"])

    # Base nodes
    node_1 = copy.deepcopy(source_prompt["1"])
    node_2 = copy.deepcopy(source_prompt["2"])
    node_3 = copy.deepcopy(source_prompt["3"])
    node_5 = copy.deepcopy(source_prompt["5"])
    node_7 = copy.deepcopy(source_prompt["7"])
    node_8 = copy.deepcopy(source_prompt["8"])

    # Node 6: ComfyUI Core ControlNetApplyAdvanced (NO Advanced-ControlNet)
    node_6 = {
        "class_type": "ControlNetApplyAdvanced",
        "inputs": {
            "positive": ["3", 0],
            "negative": ["3", 1],
            "control_net": ["5", 0],
            "image": ["8", 0],
            "strength": 0.75,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "vae": ["2", 2],
        },
    }

    nodes_dict: dict[str, Any] = {
        "1": node_1,
        "2": node_2,
        "3": node_3,
        "5": node_5,
        "6": node_6,
        "7": node_7,
        "8": node_8,
    }

    # Generate samplers, vae decodes, and save images for each seed and condition
    seed_node_map = {
        42: (10, 11),
        77: (12, 13),
        101: (14, 15),
        202: (16, 17),
        303: (18, 19),
        404: (110, 111),
    }

    outputs_meta: list[dict[str, Any]] = []

    for seed in SEEDS:
        off_ks_id_int, global_ks_id_int = seed_node_map[seed]

        # 1. CAST_OFF (bypass ControlNet -> connects directly to Node 3)
        off_ks_id = str(off_ks_id_int)
        off_vae_id = str(off_ks_id_int + 10)
        off_save_id = str(off_ks_id_int + 20)
        off_prefix = f"M3B_LR8_SEED_{seed}_CAST_OFF"

        nodes_dict[off_ks_id] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["3", 1],
                "latent_image": ["7", 0],
                "seed": seed,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        }
        nodes_dict[off_vae_id] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": [off_ks_id, 0],
                "vae": ["2", 2],
            },
        }
        nodes_dict[off_save_id] = {
            "class_type": "SaveImage",
            "inputs": {
                "images": [off_vae_id, 0],
                "filename_prefix": off_prefix,
            },
        }
        outputs_meta.append({
            "seed": seed,
            "condition": "CAST_OFF",
            "ks_node": off_ks_id,
            "save_node": off_save_id,
            "prefix": off_prefix,
            "expected_file": f"SEED_{seed}_CAST_OFF.png",
        })

        # 2. CAST_CORE_GLOBAL (uses Node 6 ControlNetApplyAdvanced)
        global_ks_id = str(global_ks_id_int)
        global_vae_id = str(global_ks_id_int + 10)
        global_save_id = str(global_ks_id_int + 20)
        global_prefix = f"M3B_LR8_SEED_{seed}_CAST_CORE_GLOBAL"

        nodes_dict[global_ks_id] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["6", 0],
                "negative": ["6", 1],
                "latent_image": ["7", 0],
                "seed": seed,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        }
        nodes_dict[global_vae_id] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": [global_ks_id, 0],
                "vae": ["2", 2],
            },
        }
        nodes_dict[global_save_id] = {
            "class_type": "SaveImage",
            "inputs": {
                "images": [global_vae_id, 0],
                "filename_prefix": global_prefix,
            },
        }
        outputs_meta.append({
            "seed": seed,
            "condition": "CAST_CORE_GLOBAL",
            "ks_node": global_ks_id,
            "save_node": global_save_id,
            "prefix": global_prefix,
            "expected_file": f"SEED_{seed}_CAST_CORE_GLOBAL.png",
        })

    # Rigorous graph inventory verification
    all_class_types = [n["class_type"] for n in nodes_dict.values()]
    if "ACN_AdvancedControlNetApply_v2" in all_class_types:
        raise AssertionError("ACN_AdvancedControlNetApply_v2 forbidden in LR8 graph!")
    for node_id, n in nodes_dict.items():
        if "AdvancedControlNet" in n["class_type"]:
            raise AssertionError(f"AdvancedControlNet node found: {node_id} ({n['class_type']})")
        for k in n.get("inputs", {}):
            if "mask_optional" in k or "effect_mask" in k:
                raise AssertionError(f"Effect mask input found in node {node_id}: {k}")

    if all_class_types.count("ControlNetApplyAdvanced") != 1:
        raise AssertionError("Expected exactly 1 ControlNetApplyAdvanced node in graph")
    if all_class_types.count("SaveImage") != 12:
        raise AssertionError(f"Expected exactly 12 SaveImage nodes, found {all_class_types.count('SaveImage')}")

    full_workflow = {
        "card": "M3B-LR8",
        "kind": "research_api_prompt",
        "source_workflow": str(SOURCE_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "model": "CN-anytest4_illustrious2_A.safetensors",
        "controlnet_selector": "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
        "fixed": {
            "checkpoint": source_prompt["2"]["inputs"]["ckpt_name"],
            "resolution": [832, 1216],
            "steps": 20,
            "cfg": 7.0,
            "sampler": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "character_strength": 1.0,
            "panel_strength": 1.0,
            "local_region_strength": 1.0,
            "character_mask_feather": 0,
            "control_strength": 0.75,
            "start_percent": 0.0,
            "end_percent": 1.0,
            "seeds": SEEDS,
            "conditions": CONDITIONS,
            "effect_mask": "NONE",
            "advanced_apply_node": "NONE",
            "controlnet_apply_node": "ControlNetApplyAdvanced",
        },
        "prompt": nodes_dict,
        "m3b_lr8": {
            "card": "M3B-LR8",
            "conditions": CONDITIONS,
            "seeds": SEEDS,
            "controlnet_apply": "ControlNetApplyAdvanced",
            "control_strength": 0.75,
            "control_start": 0.0,
            "control_end": 1.0,
            "clean_guide_sha256": EXPECTED_CLEAN_GUIDE_SHA,
            "controlnet_sha256": EXPECTED_CONTROLNET_SHA,
            "outputs": outputs_meta,
        },
    }

    TARGET_WORKFLOW.write_text(
        json.dumps(full_workflow, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[LR8 Workflow] Successfully written: {TARGET_WORKFLOW}")
    return full_workflow


def build_canonical_prompt() -> dict[str, Any]:
    wf = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
    editor_node = next(n for n in wf["nodes"] if n["type"] == "TegakiMinimumHandSceneEditor")
    doc_json = editor_node["widgets_values"][0]

    return {
        "1": {
            "class_type": "TegakiMinimumHandSceneEditor",
            "inputs": {
                "document_json": doc_json,
                "seed": 42,
                "style_template": "Manga Monochrome",
                "resolution": "Portrait 832x1216",
            },
        },
        "2": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors",
            },
        },
        "3": {
            "class_type": "TegakiMangaConditioningBuilder",
            "inputs": {
                "clip": ["2", 1],
                "page_compile_plan": ["1", 0],
                "panel_strength": 1.0,
                "character_strength": 1.0,
                "set_cond_area": "default",
                "local_region_strength": 1.0,
                "mask_feather": 0,
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 832,
                "height": 1216,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["3", 1],
                "latent_image": ["4", 0],
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["2", 2],
            },
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "M3B_LR8_CANONICAL_NO_GUIDE",
            },
        },
    }


def load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def make_contact_sheet(image_records: dict[str, Path]) -> Path:
    """Build the 6 rows x 2 cols + historical comparator contact sheet."""
    thumb_w, thumb_h = 240, 350
    gap = 16
    header_h = 60
    col_header_h = 32
    row_label_w = 90
    footer_h = 20

    # 3 columns:
    # Col 0: CAST_OFF (Core)
    # Col 1: CAST_CORE_GLOBAL (Core ControlNetApplyAdvanced)
    # Col 2: HISTORICAL ACN GLOBAL (LR7)
    cols = ["CAST_OFF", "CAST_CORE_GLOBAL", "HISTORICAL BACKEND COMPARATOR (LR7 ACN)"]
    num_cols = len(cols)

    total_w = row_label_w + num_cols * (thumb_w + gap) + gap
    total_h = header_h + col_header_h + len(SEEDS) * (thumb_h + gap) + footer_h

    sheet = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(sheet)

    title = "M3B-LR8 Core CAST_GLOBAL Robustness Qualification Contact Sheet"
    draw.text((gap, 16), title, fill="black", font=load_font(20))
    subtitle = "6 Seeds x 2 Conditions (CAST_OFF vs CAST_CORE_GLOBAL) | Model: AnyTest v4 | Strength: 0.75 | No Effect Mask"
    draw.text((gap, 42), subtitle, fill="#555555", font=load_font(12))

    # Column headers
    for c_idx, c_title in enumerate(cols):
        cx = row_label_w + c_idx * (thumb_w + gap)
        cy = header_h + 8
        draw.text((cx + 10, cy), c_title, fill="#003366", font=load_font(13))

    # Draw grid rows
    for r_idx, seed in enumerate(SEEDS):
        ry = header_h + col_header_h + r_idx * (thumb_h + gap)
        draw.text((gap + 10, ry + thumb_h // 2 - 10), f"Seed {seed}", fill="black", font=load_font(15))

        # Col 0: CAST_OFF
        off_key = f"SEED_{seed}_CAST_OFF"
        if off_key in image_records:
            im = Image.open(image_records[off_key]).convert("RGB")
            im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (thumb_w, thumb_h), "#f5f5f5")
            cell.paste(im, ((thumb_w - im.width) // 2, (thumb_h - im.height) // 2))
            sheet.paste(cell, (row_label_w + 0 * (thumb_w + gap), ry))

        # Col 1: CAST_CORE_GLOBAL
        global_key = f"SEED_{seed}_CAST_CORE_GLOBAL"
        if global_key in image_records:
            im = Image.open(image_records[global_key]).convert("RGB")
            im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (thumb_w, thumb_h), "#f5f5f5")
            cell.paste(im, ((thumb_w - im.width) // 2, (thumb_h - im.height) // 2))
            sheet.paste(cell, (row_label_w + 1 * (thumb_w + gap), ry))

        # Col 2: Historical comparator (LR7)
        hist_file = None
        if seed == 42:
            hist_file = EVIDENCE_LR7 / "SEED_A_CAST_GLOBAL.png"
        elif seed == 77:
            hist_file = EVIDENCE_LR7 / "SEED_B_CAST_GLOBAL.png"

        cx = row_label_w + 2 * (thumb_w + gap)
        if hist_file and hist_file.exists():
            im = Image.open(hist_file).convert("RGB")
            im.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (thumb_w, thumb_h), "#eeeeee")
            cell.paste(im, ((thumb_w - im.width) // 2, (thumb_h - im.height) // 2))
            sheet.paste(cell, (cx, ry))
            draw.text((cx + 10, ry + thumb_h - 22), f"LR7 ACN GLOBAL (Seed {seed})", fill="#666666", font=load_font(11))
        else:
            cell = Image.new("RGB", (thumb_w, thumb_h), "#fafafa")
            cdraw = ImageDraw.Draw(cell)
            cdraw.text((thumb_w // 2 - 40, thumb_h // 2 - 10), "N/A (Replication)", fill="#aaaaaa", font=load_font(12))
            sheet.paste(cell, (cx, ry))

    out_path = EVIDENCE_DIR / "M3B_LR8_CONTACT_SHEET.png"
    sheet.save(out_path, format="PNG")
    print(f"[LR8 Contact Sheet] Saved to {out_path}")
    return out_path


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== M3B-LR8 Build & Run Execution ===")

    # 1. CLEAN Guide hash verification
    guide_path = ROOT / "ComfyUI/input/tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png"
    if not guide_path.exists():
        guide_path = ROOT / "docs/manga/verification/m3b_lr3/M3B_LR3_CLEAN_GUIDE.png"
    actual_guide_sha = sha256_file(guide_path)
    if actual_guide_sha != EXPECTED_CLEAN_GUIDE_SHA:
        raise AssertionError(f"CLEAN Guide hash mismatch: {actual_guide_sha} vs {EXPECTED_CLEAN_GUIDE_SHA}")
    print(f"[LR8 Asset] CLEAN Guide verified: {actual_guide_sha}")

    # 2. ControlNet model hash verification
    cn_path = Path("E:/EasyReforge/Model/ControlNet/CN-anytest_v4/CN-anytest4_illustrious2_A.safetensors")
    if not cn_path.exists():
        raise AssertionError(f"ControlNet model not found at {cn_path}")
    actual_cn_sha = sha256_file(cn_path)
    if actual_cn_sha != EXPECTED_CONTROLNET_SHA:
        raise AssertionError(f"ControlNet model hash mismatch: {actual_cn_sha} vs {EXPECTED_CONTROLNET_SHA}")
    print(f"[LR8 Asset] ControlNet model verified: {actual_cn_sha}")

    # 3. Verify Core Node Contract
    verify_core_node_contract()

    # 4. Build research workflow and verify CAST runtime
    workflow_obj = build_research_workflow()
    source_prompt = workflow_obj["prompt"]
    doc = json.loads(source_prompt["1"]["inputs"]["document_json"])
    runtime_proof = verify_cast_runtime(doc)
    print(f"[LR8 CAST Runtime] Runtime verified: {runtime_proof['status']}")

    # 5. Ensure ComfyUI server is running
    print("[LR8 Server] Ensuring ComfyUI server is running...")
    comfy_runtime_helper.ensure_server(timeout=90)

    # 6. Check if 12 research outputs already exist or queue them
    outputs_meta = workflow_obj["m3b_lr8"]["outputs"]
    all_found = True
    for item in outputs_meta:
        dst = EVIDENCE_DIR / item["expected_file"]
        if not dst.exists():
            all_found = False
            break

    image_records: dict[str, Path] = {}

    if all_found:
        print("[LR8 Execution] All 12 outputs already exist in evidence directory.")
        for item in outputs_meta:
            dst = EVIDENCE_DIR / item["expected_file"]
            key = f"SEED_{item['seed']}_{item['condition']}"
            image_records[key] = dst
    else:
        print("[LR8 Execution] Queueing 12-output research prompt...")
        res = comfy_runtime_helper.queue_prompt(workflow_obj["prompt"])
        prompt_id = res["prompt_id"]
        print(f"[LR8 Execution] Queued prompt_id: {prompt_id}. Waiting for completion (timeout 600s)...")
        comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=600)
        print("[LR8 Execution] 12 outputs completed successfully!")

        for item in outputs_meta:
            src = find_latest_output_matching(item["prefix"])
            dst = EVIDENCE_DIR / item["expected_file"]
            shutil.copyfile(src, dst)
            key = f"SEED_{item['seed']}_{item['condition']}"
            image_records[key] = dst
            sha = sha256_file(dst)
            print(f"  Saved {dst.name} (SHA256: {sha})")

    # 7. Canonical no-guide regression
    canon_dst = EVIDENCE_DIR / "CANONICAL_NO_GUIDE.png"
    if not canon_dst.exists():
        print("[LR8 Regression] Queueing canonical no-guide generation...")
        canon_prompt = build_canonical_prompt()
        c_res = comfy_runtime_helper.queue_prompt(canon_prompt)
        c_prompt_id = c_res["prompt_id"]
        print(f"[LR8 Regression] Canonical prompt_id: {c_prompt_id}. Waiting...")
        comfy_runtime_helper.wait_for_prompt(c_prompt_id, timeout=300)
        c_src = find_latest_output_matching("M3B_LR8_CANONICAL_NO_GUIDE")
        shutil.copyfile(c_src, canon_dst)
        print(f"[LR8 Regression] Canonical saved: {canon_dst.name} (SHA256: {sha256_file(canon_dst)})")
    else:
        print(f"[LR8 Regression] Canonical already exists: {canon_dst.name} (SHA256: {sha256_file(canon_dst)})")

    # 8. Generate contact sheet
    make_contact_sheet(image_records)

    # 9. Build and write M3B_LR8_RUNTIME_PROVENANCE.json
    provenance = {
        "card": "M3B-LR8",
        "target_workflow": str(TARGET_WORKFLOW.relative_to(ROOT)).replace("\\", "/"),
        "controlnet_apply_class": "ControlNetApplyAdvanced",
        "controlnet_loader_class": "ControlNetLoader",
        "advanced_controlnet_nodes_count": 0,
        "advanced_controlnet_used": False,
        "effect_mask_used": False,
        "clean_guide_sha256": EXPECTED_CLEAN_GUIDE_SHA,
        "controlnet_model": "CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors",
        "controlnet_model_sha256": EXPECTED_CONTROLNET_SHA,
        "input_mode": runtime_proof["input_mode"],
        "compiled_characters_count": runtime_proof["compiled_characters_count"],
        "compiled_characters": runtime_proof["compiled_characters"],
        "character_conditioning_entries_count": runtime_proof["character_conditioning_entries_count"],
        "character_conditioning_entries": runtime_proof["character_conditioning_entries"],
        "character_masks_count": runtime_proof["character_masks_count"],
        "control_strength": 0.75,
        "control_start": 0.0,
        "control_end": 1.0,
        "seeds": SEEDS,
        "conditions": CONDITIONS,
        "outputs": {
            k: {
                "file": v.name,
                "sha256": sha256_file(v),
                "dimensions": f"{Image.open(v).width}x{Image.open(v).height}",
            }
            for k, v in image_records.items()
        },
        "canonical_no_guide": {
            "file": canon_dst.name,
            "sha256": sha256_file(canon_dst),
            "dimensions": f"{Image.open(canon_dst).width}x{Image.open(canon_dst).height}",
        },
    }

    prov_path = EVIDENCE_DIR / "M3B_LR8_RUNTIME_PROVENANCE.json"
    prov_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[LR8 Provenance] Saved runtime provenance to {prov_path}")
    print("=== Execution Complete ===")


if __name__ == "__main__":
    main()
