# H3-G1C1 Implementation Report: Aspect-Safe Standard Start Frame Cover-Crop

Date: 2026-09-11 JST  
Card ID: H3-G1C1  
Channel: H3  
Target: GEMINI  
Result: PASS  

---

## 1. Summary of Work

Card H3-G1C1 resolves the anamorphic distortion (squashing/stretching of non-16:9 inputs) of Standard Video Start Frame inputs by inserting ComfyUI's core `ImageScale` node configured for aspect-preserving center cover-cropping between `LoadImage` and `MiniMaxH3ImageToVideo.first_frame`.

### Exact ComfyUI Core Node Used
- **Class Type**: `ImageScale`
- **Location**: Installed in ComfyUI core (`nodes.py`)
- **Parameters**:
  - `upscale_method`: `"lanczos"`
  - `crop`: `"center"`
  - `width`: 608 (or `request.width` dynamically resolved from request)
  - `height`: 352 (or `request.height` dynamically resolved from request)

---

## 2. Graph Wiring Changes

### Base Workflow (`H1B1_NATIVE_FL2VA_BASE.json`)
- Added semantic role `"start_image_framing": {"id": "134", "class_type": "ImageScale"}` to `semantic_nodes`.
- Added node `"134"` to `prompt`:
  ```json
  "134": {
    "class_type": "ImageScale",
    "inputs": {
      "image": ["132", 0],
      "upscale_method": "lanczos",
      "width": 608,
      "height": 352,
      "crop": "center"
    }
  }
  ```

### Adapter Logic (`native_i2v.py`)
- **Validation (`validate_fl2va_workflow`)**:
  - Enforces presence and contract of `start_image_framing`.
  - Verifies `start_image_framing.inputs.image == [start_image_loader.id, 0]`.
  - Verifies `start_image_framing.inputs.crop == "center"`.
  - Verifies `image_to_video.inputs.first_frame` (when present) targets `[start_image_framing.id, 0]`.
- **Compilation (`compile_fl2va_workflow`)**:
  - When Start Frame slot is present:
    - Binds `first_frame` to `[start_image_framing.id, 0]`.
    - Updates framing inputs with request target `width`, `height`, `upscale_method="lanczos"`, and `crop="center"`.
  - When Start Frame slot is empty:
    - Removes `first_frame` conditioning edge.
    - Prunes both `start_image_loader` (`132`) and `start_image_framing` (`134`) from the compiled graph.

---

## 3. Scope Boundary Adherence

- **Untouched Components**:
  - `last_frame` (End Frame): Untouched. Binds directly to `end_image_loader` (`133`). (Native `MiniMaxH3ImageToVideo` internal code already performs center-crop framing for `last_frame`).
  - Still Source Image (`native_still.py` / `H2C_NATIVE_STILL_BASE.json`): Untouched.
  - Ref2VA Picture (`native_r2v.py`): Untouched.
  - Browser Prep / Edit: Untouched.
  - ComfyUI core source code: Untouched.
  - UI surfaces (`app.js`, `styles.css`): Untouched.
  - Manga / Illustrious tracks: Untouched.

---

## 4. Tradeoff Statement

- **Aspect Ratio**: 100% preserved. Images of any aspect ratio (portrait 9:16, square 1:1, ultrawide 21:9) are scaled proportionately without anamorphic stretching or squashing.
- **Image Content**: Outer edges exceeding the target aspect ratio are cropped away symmetrically from the center. The full source image is **NOT** guaranteed to be preserved in the frame.

---

## 5. Verification Results

1. **Python Unit Tests**:
   - `python -m unittest discover -s ComfyUIPortable/h3/tests`:
     - **100 tests executed, 100 PASS, 0 failures, 0 errors**.
     - Covered Start-only, End-only, Start+End, empty slots, invalid bindings, and route resolution.
2. **Node UI Verifiers**:
   - All 12 test scripts executed successfully:
     - `verify_h1b1_p2_ui.mjs`: 44 PASS
     - `verify_h1b_ui.mjs`: 36 PASS
     - `verify_h1c_continuation.mjs`: 38 PASS
     - `verify_h2c_still_ui.mjs`: 52 PASS
     - `verify_h3_g1a_stage_action.mjs`: 22 PASS
     - `verify_h3_r1_stage_generate_visibility.mjs`: 61 PASS
     - `verify_h3_r2a1_backend_reconnect.mjs`: 10 PASS
     - `verify_h3_r2b_profile_guard.mjs`: 16 PASS
     - `verify_ip2_prep_edit.mjs`: 45 PASS
     - `verify_vp1_video_ui.mjs`: PASS
     - `verify_vp2b_r2v_ui.mjs`: 28 PASS
     - `verify_vp2c_reference_handoff.mjs`: 36 PASS
3. **Generation Count**: 0 real generations performed.
