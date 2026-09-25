"""
reference_identity_analyzer.py
==============================
TEGAKI Manga - Reference-to-Identity WD14 Local Analyzer
Bounded local inference script using SmilingWolf/wd-v1-4-convnext-tagger-v2.

Strict constraints:
- Local CPUExecutionProvider only (0 GPU allocation).
- Input resolution restricted strictly to authorized Character Reference assets.
- Path traversal rejection.
- Sanitized error output (no internal Windows filesystem paths or stack traces leaked).
- Deterministic tag filtering for persistent Character Identity traits.
"""

import sys
import os
import re
import csv
import json
import argparse
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    from PIL import Image
    import onnxruntime as ort
except ImportError as e:
    # Sanitized import failure
    print(json.dumps({
        "ok": False,
        "error": "Required runtime packages (onnxruntime, numpy, Pillow) are unavailable."
    }))
    sys.exit(1)

# Canonical directories resolved relative to repository root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_MODEL_DIR = os.path.join(BASE_DIR, "ComfyUI", "models", "taggers", "wd-v1-4-convnext-tagger-v2")
DEFAULT_REFERENCES_DIR = os.path.join(BASE_DIR, "ComfyUI", "input", "tegaki_manga_references")
MAX_ASSET_BYTES = 20 * 1024 * 1024  # 20 MiB

# Non-identity patterns to exclude from candidate tags (Card Section 4)
EXCLUDE_TAG_NAMES = {
    # Background and environment
    "white_background", "simple_background", "black_background", "grey_background", "transparent_background",
    "outdoors", "indoors", "room", "scenery", "blurry_background", "sky", "day", "night", "cloud", "sunlight",
    "city", "street", "building", "floor", "wall", "window", "tree", "nature", "water", "shadow", "depth_of_field",
    "forest", "bamboo", "bamboo_forest", "grass", "plants", "woods", "mountain", "ocean", "beach",
    # Medium, style and quality
    "monochrome", "greyscale", "sketch", "lineart", "traditional_media", "comic", "manga", "cover",
    "retro_artstyle", "official_art", "absurdres", "highres", "masterpiece", "anime_coloring", "digital_media",
    "screentone", "gradient_background", "spot_color",
    # Camera angle, framing and composition
    "cowboy_shot", "portrait", "upper_body", "full_body", "close-up", "looking_at_viewer", "from_side",
    "profile", "dutch_angle", "straight-on", "wide_shot", "medium_shot", "facing_viewer", "head_shot",
    "front_view", "back_view", "from_behind", "from_above", "from_below", "cut_in", "shot", "solo",
    # Temporary pose, action and expression
    "smile", "open_mouth", "closed_eyes", "blush", "standing", "sitting", "waving", "head_tilt",
    "expressionless", "looking_down", "looking_up", "looking_away", "parted_lips", "frown", "wink",
    "arms_at_sides", "hand_on_hip", "holding", "hands_in_pockets", "arms_behind_back", "crossed_arms",
    "peace_sign", "pointing", "walking", "running", "jumping", "hands_on_hips", "arms_up", "arm_up", "closed_mouth",
    # Meta and artifacts
    "text", "watermark", "signature", "artist_name", "sample", "copyright_name", "speech_bubble",
    "sound_effects", "border", "letterboxed"
}

def sanitize_message(msg: str) -> str:
    """Strip Windows filesystem paths or potential sensitive server details."""
    cleaned = re.sub(r"[A-Za-z]:\\[^ \t\n\r\"\'\)]+", "[redacted-path]", msg)
    return cleaned

def validate_and_resolve_asset(asset_identifier: str, references_dir: str = DEFAULT_REFERENCES_DIR) -> str:
    """Validate asset reference identifier and resolve strictly within references directory."""
    if not asset_identifier or not isinstance(asset_identifier, str):
        raise ValueError("Missing or invalid Character Reference asset identifier.")
    
    clean_identifier = asset_identifier.strip()
    prefix = "tegaki_manga_references/"
    alt_prefix = "tegaki_manga_references\\"
    if clean_identifier.startswith(prefix):
        clean_identifier = clean_identifier[len(prefix):]
    elif clean_identifier.startswith(alt_prefix):
        clean_identifier = clean_identifier[len(alt_prefix):]

    basename = os.path.basename(clean_identifier)
    if not basename or basename != clean_identifier or ".." in clean_identifier or "/" in clean_identifier or "\\" in clean_identifier:
        raise ValueError("Invalid asset identifier: path traversal detected.")

    ext = os.path.splitext(basename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise ValueError(f"Unsupported image format '{ext}'. Must be PNG, JPEG, or WEBP.")

    resolved_path = os.path.abspath(os.path.join(references_dir, basename))
    expected_dir = os.path.abspath(references_dir)
    if os.path.commonpath([resolved_path, expected_dir]) != expected_dir:
        raise ValueError("Asset resolves outside authorized Character Reference directory.")

    if not os.path.exists(resolved_path) or not os.path.isfile(resolved_path):
        raise FileNotFoundError(f"Character Reference asset '{basename}' not found.")

    file_size = os.path.getsize(resolved_path)
    if file_size == 0:
        raise ValueError(f"Character Reference asset '{basename}' is empty.")
    if file_size > MAX_ASSET_BYTES:
        raise ValueError(f"Character Reference asset '{basename}' exceeds 20 MiB size limit.")

    return resolved_path

def preprocess_image(image_path: str) -> np.ndarray:
    """Exact preprocessing matching wd-v1-4-convnext-tagger-v2 CPU probe."""
    try:
        img = Image.open(image_path)
    except Exception as e:
        raise ValueError(f"Failed to read image asset: {sanitize_message(str(e))}")

    # Convert RGBA to RGB on white background
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    # RGB to BGR
    img_np = np.array(img, dtype=np.float32)
    img_np = img_np[:, :, ::-1]

    # Pad to square with white (255.0)
    target_dim = 448
    h, w = img_np.shape[:2]
    max_dim = max(h, w)
    pad_h = max_dim - h
    pad_w = max_dim - w
    top = pad_h // 2
    left = pad_w // 2
    padded = np.pad(
        img_np,
        ((top, pad_h - top), (left, pad_w - left), (0, 0)),
        mode="constant",
        constant_values=255.0
    )

    # Resize to 448x448 bicubic
    pil_padded = Image.fromarray(padded.astype(np.uint8)[:, :, ::-1])
    pil_resized = pil_padded.resize((target_dim, target_dim), Image.BICUBIC)
    input_tensor = np.array(pil_resized, dtype=np.float32)[:, :, ::-1]
    input_tensor = np.expand_dims(input_tensor, axis=0)  # [1, 448, 448, 3]
    return input_tensor

def filter_tags_for_identity(probs: np.ndarray, tag_rows: List[List[str]], confidence_threshold: float = 0.35) -> Dict[str, Any]:
    """
    Extract and filter tags deterministically for Character Identity traits.
    Prioritizes hair, eyes, clothing, distinctive stable attributes.
    Excludes ratings, copyright/named characters, background, camera angle, temporary expressions/poses.
    """
    if len(probs) != len(tag_rows):
        raise ValueError(f"Tag count mismatch: model outputs {len(probs)} vs CSV {len(tag_rows)}")

    ratings = {}
    general_tags = []
    
    for idx, row in enumerate(tag_rows):
        tag_id, name, cat, count = row[0], row[1], row[2], row[3]
        prob = float(probs[idx])
        item = {
            "index": idx,
            "tag_id": tag_id,
            "name": name,
            "category": int(cat),
            "score": round(prob, 4)
        }
        if cat == "9":  # Rating
            ratings[name] = round(prob, 4)
        elif cat == "0":  # General
            if prob >= 0.10:
                general_tags.append(item)

    general_tags.sort(key=lambda x: x["score"], reverse=True)

    identity_tags = []
    for item in general_tags:
        name = item["name"]
        score = item["score"]
        if name in EXCLUDE_TAG_NAMES:
            continue
        if score >= confidence_threshold:
            identity_tags.append(name)

    candidate_text = ", ".join(identity_tags)
    return {
        "candidate": candidate_text,
        "tags": identity_tags,
        "ratings": ratings
    }

def analyze_character_reference(
    asset_identifier: str,
    model_dir: str = DEFAULT_MODEL_DIR,
    references_dir: str = DEFAULT_REFERENCES_DIR,
    confidence_threshold: float = 0.35
) -> Dict[str, Any]:
    """Run single reference image analysis strictly on CPU."""
    # 1. Resolve and validate asset
    image_path = validate_and_resolve_asset(asset_identifier, references_dir)

    # 2. Check model and csv
    model_path = os.path.join(model_dir, "model.onnx")
    csv_path = os.path.join(model_dir, "selected_tags.csv")
    if not os.path.exists(model_path) or not os.path.isfile(model_path):
        raise FileNotFoundError("WD14 model file (model.onnx) not found.")
    if not os.path.exists(csv_path) or not os.path.isfile(csv_path):
        raise FileNotFoundError("WD14 tags CSV (selected_tags.csv) not found.")

    # 3. Read tag list
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            tag_rows = list(reader)
    except Exception as e:
        raise ValueError(f"Failed to read tag taxonomy CSV: {sanitize_message(str(e))}")

    # 4. Preprocess image
    input_tensor = preprocess_image(image_path)

    # 5. Initialize ONNX session strictly on CPU
    sess_opts = ort.SessionOptions()
    sess_opts.inter_op_num_threads = 4
    sess_opts.intra_op_num_threads = 4
    sess = ort.InferenceSession(model_path, sess_options=sess_opts, providers=["CPUExecutionProvider"])
    
    # Verify CPUExecutionProvider
    providers = sess.get_providers()
    if "CPUExecutionProvider" not in providers:
        raise RuntimeError("CPUExecutionProvider is not available.")

    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name

    # 6. Run inference
    outputs = sess.run([output_name], {input_name: input_tensor})
    probs = outputs[0][0]

    # 7. Filter tags
    filtering_result = filter_tags_for_identity(probs, tag_rows, confidence_threshold)

    return {
        "ok": True,
        "candidate": filtering_result["candidate"],
        "tags": filtering_result["tags"],
        "ratings": filtering_result["ratings"],
        "model": "SmilingWolf/wd-v1-4-convnext-tagger-v2",
        "execution_provider": "CPUExecutionProvider"
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze character reference image with WD14 tagger")
    parser.add_argument("--asset", type=str, help="Character Reference asset identifier (e.g. ref_xxx.png)")
    parser.add_argument("--json", type=str, help="JSON input string containing asset_reference")
    parser.add_argument("--threshold", type=float, default=0.35, help="Confidence threshold")
    args = parser.parse_args()

    asset_identifier = None
    if args.json:
        try:
            payload = json.loads(args.json)
            asset_identifier = payload.get("asset_reference") or payload.get("ref") or payload.get("asset")
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"Invalid JSON input: {sanitize_message(str(e))}"}))
            sys.exit(1)
    elif args.asset:
        asset_identifier = args.asset
    else:
        # Check stdin
        if not sys.stdin.isatty():
            try:
                raw_input = sys.stdin.read().strip()
                if raw_input:
                    payload = json.loads(raw_input)
                    asset_identifier = payload.get("asset_reference") or payload.get("ref") or payload.get("asset")
            except Exception:
                pass

    if not asset_identifier:
        print(json.dumps({"ok": False, "error": "Missing required Character Reference asset identifier."}))
        sys.exit(1)

    try:
        result = analyze_character_reference(asset_identifier, confidence_threshold=args.threshold)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": sanitize_message(str(e))
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
