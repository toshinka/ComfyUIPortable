# H3-G1C2 Implementation Report: Aspect-Safe Still Source Cover-Crop

Date: 2026-09-12 JST  
Card ID: H3-G1C2  
Channel: H3  
Target: GEMINI  
Result: PASS  

---

## 1. Summary of Work

Card H3-G1C2 eliminates the anamorphic distortion (squashing/stretching of non-16:9 inputs) of Still Source Image inputs by inserting ComfyUI's core `ImageScale` node configured for aspect-preserving center cover-cropping between `LoadImage` and `MiniMaxH3ImageToVideo.first_frame`.

### Old Distortion Path
In the original H2B graph, `LoadImage` (`133`) connected directly to `MiniMaxH3ImageToVideo.first_frame` (`131`). Because the Native `MiniMaxH3ImageToVideo` node resizes `first_frame` directly to 608x352 with `crop=disabled` (plain stretch), portrait and square source images were distorted/flattened into 16:9.

### New Aspect-Safe Graph
The source-anchored still pipeline now executes:
```
LoadImage (133) -> ImageScale (134) -> MiniMaxH3ImageToVideo.first_frame (131)
```

### Exact ComfyUI Core Node Contract
- **Class Type**: `ImageScale`
- **Location**: Installed in ComfyUI core (`nodes.py`)
- **Inputs**:
  - `image`: `["133", 0]` (from `source_image_loader`)
  - `upscale_method`: `"lanczos"`
  - `width`: 608
  - `height`: 352
  - `crop`: `"center"`

---

## 2. Base Workflow & Adapter Changes

### Base Workflow (`H2B_SOURCE_ANCHORED_STILL_BASE.json`)
- Added semantic role `"source_image_framing": {"id": "134", "class_type": "ImageScale"}` to `semantic_nodes`.
- Added node `"134"` to `prompt`:
  ```json
  "134": {
    "class_type": "ImageScale",
    "inputs": {
      "image": ["133", 0],
      "upscale_method": "lanczos",
      "width": 608,
      "height": 352,
      "crop": "center"
    }
  }
  ```
- Re-routed `MiniMaxH3ImageToVideo.first_frame` input from `["133", 0]` to `["134", 0]`.
- Updated workflow metadata description and baseline `source_resize` to document center cover-cropping via `ImageScale` instead of plain stretch.

### Adapter Logic (`native_source_anchored_still.py`)
- **Semantic Roles**: Added `SOURCE_FRAMING_ROLE = "source_image_framing"` to required roles.
- **Validation (`validate_workflow`)**:
  - Enforces presence and contract of `source_image_framing`.
  - Verifies `source_image_framing.inputs.image == [source_image_loader.id, 0]`.
  - Verifies `source_image_framing.inputs.upscale_method == "lanczos"`.
  - Verifies `source_image_framing.inputs.width == 608` and `height == 352`.
  - Verifies `source_image_framing.inputs.crop == "center"`.
  - Verifies `conditioning_latent.inputs.first_frame == [source_image_framing.id, 0]`.
- **Compilation (`compile_workflow`)**:
  - Populates `source_image_framing` inputs with `["133", 0]`, `upscale_method="lanczos"`, request `width` and `height`, and `crop="center"`.
  - Sets `conditioning_latent.inputs.first_frame = [framing_id, 0]`.
- **Prompt-Only Control Compilation (`compile_prompt_only_workflow`)**:
  - Removes `first_frame` conditioning edge.
  - Prunes BOTH `source_image_loader` (`133`) AND `source_image_framing` (`134`) from the graph.
  - Leaves zero orphan framing nodes in the prompt-only graph.

---

## 3. Tradeoff Statement

- **Aspect Ratio**: Fully preserved. Images of arbitrary aspect ratio (e.g. 1:1 square, 9:16 portrait, 4:3) are scaled proportionally without anamorphic squashing or stretching.
- **Image Content**: Outer edges exceeding the target 608x352 aspect ratio are cropped away symmetrically from the center to fill the frame. The full source image is **NOT** guaranteed to be preserved in the frame.

---

## 4. Scope Boundary Adherence

- **Untouched Components**:
  - Request schema (`H3SourceAnchorRequest`): Untouched.
  - Server endpoints & request schemas (`server.py`): Untouched.
  - Browser UI and styles (`app.js`, `styles.css`): Untouched.
  - Standard Video routes (`native_i2v.py`, `native_t2v.py`): Untouched.
  - Prep/Edit & Ref2VA routes: Untouched.
  - ComfyUI core source code: Untouched.
  - Manga track: Untouched.
- **Real generations**: 0.

---

## 5. Verification Results

1. **Python Unit Tests**:
   - `test_h2b_source_anchored_still.py`: 6/6 PASS. Verifies:
     - ImageScale node present in compiled graph.
     - LoadImage feeds ImageScale.
     - ImageScale feeds first_frame.
     - ImageScale uses lanczos.
     - width == 608, height == 352.
     - crop == center.
     - Prompt-only control prunes both LoadImage and ImageScale.
     - Prompt-only conditioning contains no first_frame.
     - Workflow validation rejects missing or misconfigured framing.
     - 5-frame packet, 0-frame selected index, and 20 steps preserved.
   - `test_h2c_still_server.py`: 7/7 PASS. Verifies:
     - H2C server session submit_still correctly produces graph with ImageScale.
     - Missing source failure, upload validations, and history handling unaffected.
   - Full Python test suite: 123/123 PASS (0 failures, 0 errors in 68.5s).
2. **Node UI Verifiers**: All 13 suites PASS.
3. **Generation Count**: 0 real generations performed.

