"""Pure CPU Page Pixel Compositor for TEGAKI_PAGE_COMPOSITION_PLAN 1.0.0.

Consumes a trusted page composition plan, loads and verifies selected scene
artifacts, performs normalized edge conversion, crops, aspect-preserving center-crop (cover fit, no stretch), resizes via Lanczos,
and executes source-over alpha compositing on an opaque white canvas.
"""

from __future__ import annotations

import hashlib
import io
import math
import os
from typing import Any, Callable

from PIL import Image

SCHEMA_ID = "TEGAKI_PAGE_COMPOSITION_PLAN"
SCHEMA_VERSION = "1.0.0"


class PagePixelCompositorError(Exception):
    """Domain error with stable error code and safe message."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalized_rect_to_pixel_edges(
    rect: dict[str, Any], dim_w: int, dim_h: int
) -> tuple[int, int, int, int]:
    """Converts a normalized rectangle [0, 1] to pixel edges using explicit half-up rounding.

    Edge rounding rule: floor(value * dimension + 0.5)
    pixel_width = right - left
    pixel_height = bottom - top
    """
    for k in ("x", "y", "w", "h"):
        val = rect.get(k) if isinstance(rect, dict) else None
        if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise PagePixelCompositorError("PLACEMENT_INVALID", f"Rectangle missing finite numeric {k}")

    x = float(rect["x"])
    y = float(rect["y"])
    w = float(rect["w"])
    h = float(rect["h"])

    if w <= 0.0 or h <= 0.0:
        raise PagePixelCompositorError("PLACEMENT_INVALID", f"Rectangle w and h must be positive, got w={w}, h={h}")

    EPS = 0.001
    if x < -EPS or y < -EPS or (x + w) > (1.0 + EPS) or (y + h) > (1.0 + EPS):
        raise PagePixelCompositorError(
            "PLACEMENT_INVALID", f"Rectangle [{x}, {y}, {w}, {h}] exceeds unit bounds [0, 1]"
        )

    left = math.floor(x * dim_w + 0.5)
    top = math.floor(y * dim_h + 0.5)
    right = math.floor((x + w) * dim_w + 0.5)
    bottom = math.floor((y + h) * dim_h + 0.5)

    if left < 0 or top < 0 or right > dim_w or bottom > dim_h:
        raise PagePixelCompositorError(
            "PLACEMENT_INVALID",
            f"Pixel edges [{left}, {top}, {right}, {bottom}] exceed canvas dimensions {dim_w}x{dim_h}",
        )

    pixel_w = right - left
    pixel_h = bottom - top
    if pixel_w <= 0 or pixel_h <= 0:
        raise PagePixelCompositorError(
            "PLACEMENT_INVALID",
            f"Pixel edges result in non-positive dimensions: {pixel_w}x{pixel_h}",
        )

    return left, top, right, bottom


def default_artifact_loader(locator: dict[str, Any], output_root: str | None = None) -> bytes:
    """Resolves and reads an artifact file through restricted ComfyUI output semantics."""
    if not isinstance(locator, dict):
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Artifact locator must be an object")

    filename = locator.get("filename")
    subfolder = locator.get("subfolder", "")
    loc_type = locator.get("type", "output")

    if not filename or not isinstance(filename, str):
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Artifact locator must specify filename")
    if not isinstance(subfolder, str):
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Artifact locator subfolder must be a string")
    if loc_type != "output":
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", f"Unsupported artifact locator type: {loc_type}")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Filename must not contain path traversal characters")
    if ".." in subfolder:
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Subfolder must not contain path traversal characters")

    if output_root is None:
        try:
            import folder_paths

            output_root = folder_paths.get_output_directory()
        except Exception:
            output_root = os.path.join(os.getcwd(), "output")

    base_dir = os.path.abspath(output_root)
    clean_subfolder = os.path.normpath(subfolder).lstrip("\\/.")
    target_dir = os.path.abspath(os.path.join(base_dir, clean_subfolder))

    if not (target_dir == base_dir or target_dir.startswith(base_dir + os.sep)):
        raise PagePixelCompositorError("SOURCE_LOCATOR_INVALID", "Subfolder traverses outside output root")

    file_path = os.path.join(target_dir, filename)
    if not os.path.isfile(file_path):
        raise PagePixelCompositorError("SOURCE_ARTIFACT_NOT_FOUND", f"Artifact file '{filename}' not found")

    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception:
        raise PagePixelCompositorError("SOURCE_ARTIFACT_NOT_FOUND", f"Failed to read artifact '{filename}'")


def validate_plan_envelope(plan: Any) -> tuple[int, int, list[dict[str, Any]]]:
    """Validates TEGAKI_PAGE_COMPOSITION_PLAN envelope and returns (page_width, page_height, scenes)."""
    if not isinstance(plan, dict):
        raise PagePixelCompositorError("INVALID_COMPOSITION_PLAN", "Composition plan must be a non-null object")

    if plan.get("schema_id") != SCHEMA_ID:
        raise PagePixelCompositorError(
            "INVALID_COMPOSITION_PLAN", f"Expected schema_id '{SCHEMA_ID}', got '{plan.get('schema_id')}'"
        )
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise PagePixelCompositorError(
            "INVALID_COMPOSITION_PLAN",
            f"Expected schema_version '{SCHEMA_VERSION}', got '{plan.get('schema_version')}'",
        )

    page = plan.get("page")
    if not isinstance(page, dict):
        raise PagePixelCompositorError("INVALID_COMPOSITION_PLAN", "Plan must contain page object")

    width = page.get("width")
    height = page.get("height")
    if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
        raise PagePixelCompositorError(
            "INVALID_COMPOSITION_PLAN", f"Page width and height must be positive integers, got {width}x{height}"
        )

    bg = plan.get("background")
    if not isinstance(bg, dict) or bg.get("mode") != "solid" or bg.get("value") != "white":
        raise PagePixelCompositorError(
            "INVALID_COMPOSITION_PLAN", "Plan background must be mode='solid', value='white'"
        )

    scenes = plan.get("scenes")
    if not isinstance(scenes, list):
        raise PagePixelCompositorError("INVALID_COMPOSITION_PLAN", "Plan scenes must be an array")

    return width, height, scenes


def compose_page_pixels(
    plan: dict[str, Any],
    artifact_loader: Callable[[dict[str, Any]], bytes] | None = None,
) -> bytes:
    """Executes CPU pixel composition for one TEGAKI_PAGE_COMPOSITION_PLAN.

    Returns the exact encoded composite PNG bytes.
    """
    page_w, page_h, scenes = validate_plan_envelope(plan)
    loader = artifact_loader or default_artifact_loader

    # 1. Allocate opaque solid white canvas (R=255, G=255, B=255, A=255)
    canvas = Image.new("RGBA", (page_w, page_h), (255, 255, 255, 255))

    # 2. Process scenes strictly in plan order
    for idx, slot in enumerate(scenes):
        if not isinstance(slot, dict):
            raise PagePixelCompositorError("INVALID_COMPOSITION_PLAN", f"Scene slot {idx} is not an object")

        state = slot.get("state")
        if state == "UNFILLED":
            # Untouched white canvas
            continue
        elif state == "CURRENT_RESULT":
            sel = slot.get("selected_result")
            if not isinstance(sel, dict):
                raise PagePixelCompositorError(
                    "INVALID_COMPOSITION_PLAN", f"Slot {idx} in CURRENT_RESULT missing selected_result"
                )

            artifact = sel.get("artifact")
            placement = sel.get("placement")
            if not isinstance(artifact, dict) or not isinstance(placement, dict):
                raise PagePixelCompositorError(
                    "INVALID_COMPOSITION_PLAN", f"Slot {idx} selected_result missing artifact or placement"
                )

            locator = artifact.get("locator")
            expected_digest = artifact.get("content_digest")
            expected_dims = artifact.get("dimensions")
            if not isinstance(locator, dict) or not isinstance(expected_digest, str) or not isinstance(expected_dims, dict):
                raise PagePixelCompositorError(
                    "INVALID_COMPOSITION_PLAN", f"Slot {idx} artifact metadata incomplete"
                )

            exp_w = expected_dims.get("width")
            exp_h = expected_dims.get("height")
            if not isinstance(exp_w, int) or exp_w <= 0 or not isinstance(exp_h, int) or exp_h <= 0:
                raise PagePixelCompositorError(
                    "INVALID_COMPOSITION_PLAN", f"Slot {idx} artifact dimensions must be positive integers"
                )

            # Check target_page_dimensions match plan page dimensions
            target_page_dims = placement.get("target_page_dimensions")
            if not isinstance(target_page_dims, dict):
                raise PagePixelCompositorError(
                    "TARGET_DIMENSIONS_MISMATCH", f"Slot {idx} placement missing target_page_dimensions"
                )
            if target_page_dims.get("width") != page_w or target_page_dims.get("height") != page_h:
                raise PagePixelCompositorError(
                    "TARGET_DIMENSIONS_MISMATCH",
                    f"Slot {idx} target_page_dimensions {target_page_dims} mismatch plan page {page_w}x{page_h}",
                )

            # Check transform consistency
            transform = placement.get("transform")
            target_rect = placement.get("page_target_rect")
            source_rect = placement.get("local_source_rect")
            if not isinstance(transform, dict) or not isinstance(target_rect, dict) or not isinstance(source_rect, dict):
                raise PagePixelCompositorError(
                    "PLACEMENT_INVALID", f"Slot {idx} placement missing transform or rectangles"
                )

            pw = target_rect.get("w", 0)
            ph = target_rect.get("h", 0)
            px = target_rect.get("x", 0)
            py = target_rect.get("y", 0)
            sx = transform.get("scale_x", 0)
            sy = transform.get("scale_y", 0)
            ox = transform.get("offset_x", 0)
            oy = transform.get("offset_y", 0)

            EPS = 0.001
            if (
                abs(sx - pw) > EPS
                or abs(sy - ph) > EPS
                or abs(ox - px) > EPS
                or abs(oy - py) > EPS
            ):
                raise PagePixelCompositorError(
                    "PLACEMENT_INVALID",
                    f"Slot {idx} transform ({sx}, {sy}, {ox}, {oy}) inconsistent with target_rect ({pw}, {ph}, {px}, {py})",
                )

            # Fetch artifact bytes
            raw_bytes = loader(locator)
            if not isinstance(raw_bytes, (bytes, bytearray)) or len(raw_bytes) == 0:
                raise PagePixelCompositorError("SOURCE_ARTIFACT_NOT_FOUND", "Empty or invalid artifact bytes")

            # Verify content digest
            actual_digest = hashlib.sha256(raw_bytes).hexdigest()
            if actual_digest != expected_digest:
                raise PagePixelCompositorError(
                    "SOURCE_DIGEST_MISMATCH",
                    f"Slot {idx} digest mismatch: expected {expected_digest}, got {actual_digest}",
                )

            # Decode source PNG
            try:
                src_img = Image.open(io.BytesIO(raw_bytes))
            except Exception as exc:
                raise PagePixelCompositorError("IMAGE_DECODE_FAILED", f"Failed to decode source PNG: {exc}")

            # Verify source dimensions
            if src_img.width != exp_w or src_img.height != exp_h:
                raise PagePixelCompositorError(
                    "SOURCE_DIMENSION_MISMATCH",
                    f"Slot {idx} source dimensions {src_img.width}x{src_img.height} do not match expected {exp_w}x{exp_h}",
                )

            # Local source crop
            src_l, src_t, src_r, src_b = normalized_rect_to_pixel_edges(source_rect, src_img.width, src_img.height)
            if src_l == 0 and src_t == 0 and src_r == src_img.width and src_b == src_img.height:
                cropped = src_img
            else:
                try:
                    cropped = src_img.crop((src_l, src_t, src_r, src_b))
                except Exception as exc:
                    raise PagePixelCompositorError("IMAGE_COMPOSITE_FAILED", f"Source crop failed: {exc}")

            # Target pixel edges & resize
            tgt_l, tgt_t, tgt_r, tgt_b = normalized_rect_to_pixel_edges(target_rect, page_w, page_h)
            tgt_w = tgt_r - tgt_l
            tgt_h = tgt_b - tgt_t

            # Aspect-preserving cover fit: never stretch non-uniformly.  If the
            # source aspect differs from the target aspect, center-crop the
            # excess from the source before a uniform resize (no letterbox bars).
            if tgt_w > 0 and tgt_h > 0 and cropped.width > 0 and cropped.height > 0:
                if cropped.width * tgt_h > tgt_w * cropped.height:
                    keep_w = max(1, min(cropped.width, int(cropped.height * tgt_w / tgt_h + 0.5)))
                    keep_h = cropped.height
                else:
                    keep_w = cropped.width
                    keep_h = max(1, min(cropped.height, int(cropped.width * tgt_h / tgt_w + 0.5)))
                if keep_w != cropped.width or keep_h != cropped.height:
                    cut_l = (cropped.width - keep_w) // 2
                    cut_t = (cropped.height - keep_h) // 2
                    try:
                        cropped = cropped.crop((cut_l, cut_t, cut_l + keep_w, cut_t + keep_h))
                    except Exception as exc:
                        raise PagePixelCompositorError("IMAGE_COMPOSITE_FAILED", f"Aspect crop failed: {exc}")

            if cropped.width != tgt_w or cropped.height != tgt_h:
                try:
                    resized = cropped.resize((tgt_w, tgt_h), Image.Resampling.LANCZOS)
                except Exception as exc:
                    raise PagePixelCompositorError("IMAGE_RESIZE_FAILED", f"Image resize failed: {exc}")
            else:
                resized = cropped

            # Ensure RGBA for alpha composition
            if resized.mode != "RGBA":
                resized = resized.convert("RGBA")

            # Source-over alpha composite onto the canvas subregion
            try:
                sub = canvas.crop((tgt_l, tgt_t, tgt_r, tgt_b))
                composed_sub = Image.alpha_composite(sub, resized)
                canvas.paste(composed_sub, (tgt_l, tgt_t))
            except Exception as exc:
                raise PagePixelCompositorError("IMAGE_COMPOSITE_FAILED", f"Alpha compositing failed: {exc}")
        else:
            raise PagePixelCompositorError("INVALID_COMPOSITION_PLAN", f"Unknown slot state: '{state}'")

    # 3. Encode final page as PNG in memory
    try:
        out_buf = io.BytesIO()
        canvas.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception as exc:
        raise PagePixelCompositorError("IMAGE_ENCODE_FAILED", f"Failed to encode final composite PNG: {exc}")
