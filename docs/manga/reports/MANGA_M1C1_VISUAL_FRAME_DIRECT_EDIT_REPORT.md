# MANGA-M1C1 — Standalone Visual Frame Direct Editing Parity Report

- **Card**: `MANGA-M1C1`
- **Executor**: Gemini 3.8 Flash / Antigravity 2.0
- **Baseline SHA**: `11bc52b5795cf58f837f8ec680ac82fbccd13999`
- **Scope**: `ComfyUIPortable/manga/**`
- **Result**: PASS

---

## 1. Scope & Execution Summary

MANGA-M1C1 advances the standalone Manga Workspace (`ComfyUIPortable/manga/`) by elevating Visual Frames from read-only to directly authorable:
- Visual Frames are now interactive in the editor: Add, Delete, Move, and 4-corner Resize (NW, NE, SE, SW).
- Added one-shot convenience action `Copy Scenes to Frames` with user confirmation.
- Added overlap detection diagnostic banner (`#frame-overlap-warning`) reporting intersecting frame pairs without blocking editing or export.
- Frame-layer hit-test isolation: when on the Visual Frames tab, Visual Frames and corner handles take pointer precedence, preventing underlying Scenes and Characters from stealing interaction.
- Scene/Frame decoupling invariant preserved: moving/resizing a Frame never alters Scenes, and moving/resizing Scenes never alters Frames.
- All operations are validated through `validateAuthoringDocument` on a cloned draft before state commit.
- Guide and Figure direct editing remain strictly READ-ONLY / DEFERRED for `MANGA-M1C2`.
- Zero backend queueing, zero image generation, zero H3 changes, zero legacy M3B modifications.

---

## 2. Implementation Details

### A. Pure Domain Ops (`ComfyUIPortable/manga/app/src/domain/authoring_ops.js`)
- `getNextFrameId(frames)`: Computes collision-free `frame_N` IDs.
- `calculateNewFrameGeometry(frames, defaultArea)`: Staggers new frames diagonally inside page bounds `[0, 1]`.
- `copyFramesFromScenes(scenes, existingFrames, defaultBorderThickness)`: Deep clones Scene bounds into new Frames, preserving order and setting `border_thickness`.
- `clampFrameDrag(startArea, dx, dy)`: Clamps moved rectangle strictly within page bounds `[0, 1]`.
- `resizeFrame(startArea, handle, dx, dy, minSize)`: Supports 4 corners (`nw`, `ne`, `se`, `sw`) enforcing `minSize = 0.05` and bounding within page `[0, 1]`.
- `checkFrameOverlap(frames)`: Detects overlapping bounding box pairs using strict intersection (`left < right && top < bottom`), ignoring exact edge-touching boundaries.

### B. Authoring Store (`ComfyUIPortable/manga/app/src/state/authoring_store.js`)
- `addFrame(frameData)`: Appends frame and validates schema.
- `deleteFrame(frameId)`: Removes frame, re-indexes `z_order` sequentially `[0..N-1]`, and validates schema.
- `copyScenesToFrames()`: Replaces frames with scene projections and validates schema.
- `moveFrame(frameId, dx, dy)`: Updates frame area with bounds clamping and validates schema.
- `resizeFrame(frameId, handle, dx, dy)`: Resizes frame via corner handle with bounds clamping and validates schema.
- `updateFrame(frameId, patch)`: Supports updating `border_thickness` and coordinates.
- `getFrameOverlap()`: Evaluates current frames for overlapping pairs.

### C. Canvas Renderer & Hit-Testing (`ComfyUIPortable/manga/app/src/view/canvas_renderer.js`)
- Renders 4 corner handles (`nw`, `ne`, `se`, `sw`) on the selected frame.
- Active-layer hit-test isolation: when `activeTab === "frames"`, corner handles and frame rectangles are evaluated first so underlying scene rectangles do not consume pointer events.

### D. UI & Session Controls (`ComfyUIPortable/manga/app/index.html` & `session_state.js`)
- Removed `[Read-Only]` indicator from Visual Frames tab.
- Added `+ Add Frame`, `Copy Scenes to Frames`, Overlap diagnostic warning banner, border thickness input, frame coordinates display, and `Delete Frame` button.
- Canvas pointer drag and resize handling for frames.

---

## 3. Verification Results

### Unit Tests (`ComfyUIPortable/manga/tests/test_frame_ops.mjs`)
- **Section 18 Pure Tests (A through K)**:
  - `A`: `getNextFrameId` avoids collisions -> PASS
  - `B`: `calculateNewFrameGeometry` matches reference behavior -> PASS
  - `C`: `copyScenesToFrames` creates independent clones -> PASS
  - `D`: moving Scene after copy does not move Frame -> PASS
  - `E`: moving Frame after copy does not move Scene -> PASS
  - `F`: `clampFrameDrag` cannot leave page bounds -> PASS
  - `G`: `resizeFrame` supports NW/NE/SE/SW -> PASS
  - `H`: resize remains within page bounds -> PASS
  - `I`: minimum frame size enforced -> PASS
  - `J`: overlap detection identifies intersecting pair -> PASS
  - `K`: touching borders are not incorrectly treated as overlap -> PASS
- **Section 19 Store Tests (A through H)**:
  - `A`: `addFrame` commits valid schema -> PASS
  - `B`: `deleteFrame` reorders survivors -> PASS
  - `C`: `copyScenesToFrames` replaces previous frames intentionally -> PASS
  - `D`: `moveFrame` persists geometry -> PASS
  - `E`: `resizeFrame` persists geometry -> PASS
  - `F`: border thickness persists -> PASS
  - `G`: `exportJson` preserves all frame document data without session leakage -> PASS
  - `H`: `importJson` round-trip restores exact frame attributes and schema -> PASS

### Full Test Suite
- `test_domain_document.mjs`: PASS (6/6)
- `test_backend_adapter.mjs`: PASS (9/9)
- `test_canvas_renderer.mjs`: PASS (3/3)
- `test_authoring_ops.mjs`: PASS (14/14)
- `test_document_roundtrip.mjs`: PASS (2/2)
- `test_frame_ops.mjs`: PASS (19/19)

### Browser Verification (`ComfyUIPortable/manga/tests/verify_m1c1_browser.mjs`)
All 16 steps executed and passed in Chromium against standalone workspace:
1. Workspace loaded -> PASS
2. Switched to Visual Frames layer -> PASS
3. `Copy Scenes to Frames` creates 2 frames -> PASS
4. Frame selection verified -> PASS
5. Frame moved via inspector buttons -> PASS (see Note below)
6. Frame resized via direct store call -> PASS (see Note below)
7. Add Frame creates 3rd frame -> PASS
8. Overlap diagnostic detected overlap -> PASS
9. Moved 3rd frame to resolve overlap -> PASS
10. Adjusted border thickness -> PASS
11. Deleted 3rd frame -> PASS
12. Scene/Frame independence verified -> PASS
13. Frame layer hit-test isolation verified -> PASS
14. Document export / round-trip verified -> PASS
15. Backend queue remains 0 (no generations) -> PASS
16. Guides remain untouched -> PASS

> **Audit Correction Note (Card Section 28)**:
> The original M1C1 Browser suite proved browser integration and UI responsiveness, but its movement and resize steps exercised inspector button and direct store mutation paths rather than physical canvas pointer drags. The underlying implementation source does contain full canvas pointer event handling, and MANGA-M1C2A closes this evidence gap by adding actual canvas pointer regression tests (mousedown, mousemove, mouseup) for Frame move and multi-handle resize.
