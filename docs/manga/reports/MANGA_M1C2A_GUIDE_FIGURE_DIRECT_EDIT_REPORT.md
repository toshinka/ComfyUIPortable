# MANGA-M1C2A — Existing Guide / Figure Direct Editing Parity Report

- **Card**: `MANGA-M1C2A`
- **Executor**: Gemini 3.8 Flash / Antigravity 2.0
- **Baseline SHA**: `6e5239354b9e55c4cd558ffe44c7921bb1b7cd21`
- **Scope**: `ComfyUIPortable/manga/**`
- **Result**: PASS

---

## 1. Scope & Responsibility

MANGA-M1C2A elevates Guides and Figure Regions in the standalone Manga Workspace (`ComfyUIPortable/manga/`) from read-only inspection to direct authoring for existing/imported Guides:
- **Guide-local coordinate semantics**: Strictly implemented and enforced. `Guide.placement` is in page-normalized coordinates `[0, 1]`, while `Figure.area` is in Guide-local normalized coordinates `[0, 1]`.
- **Renderer correction**: Updated `canvas_renderer.js` so Figure rectangles are dynamically mapped from Guide-local coordinates `(lx, ly, lw, lh)` to page canvas coordinates `(gx + lx * gw, gy + ly * gh, lw * gw, lh * gh)` at runtime. No page-derived coordinates are persisted into the document.
- **Figure direct manipulation**: Canvas pointer drag (`move_figure`) and 4-corner resize (`resize_figure`: NW, NE, SE, SW) implemented with pointer delta converted into Guide-local delta (`localDx = pageDx / placement.w`, `localDy = pageDy / placement.h`).
- **Guide & Figure Inspector controls**: Guide selection, toggle enabled/disabled, guide removal, add figure (`+ Add Figure`), remove figure, four-corner resize, manual translation buttons, and Character Instance association dropdown.
- **Association semantics & duplicate rejection**: Enforces 1:1 association per Guide (`figure.instance_id`). Associating an already-associated Character Instance is visibly rejected in UI and raises `DUPLICATE_INSTANCE_ASSOCIATION` in store mutations. Unassigning clears `instance_id` without deleting Figure.
- **Character / Scene deletion regression**: Removing a Character Instance or deleting a Scene clears references in `figure.instance_id` while preserving the Figure region itself.
- **M1C1 Pointer Regression**: Added real canvas pointer event tests (`mousedown`, `mousemove`, `mouseup`) verifying Frame dragging and corner handle resizing (SE and NW) through actual canvas interactions rather than control/store mutations.
- **Out of Scope (Deferred to M1C2B)**: Guide asset upload, image replacement, binary proxy transport, and FileReader base64/blob persistence remain strictly NOT IMPLEMENTED.
- **Backend & Generation**: Zero backend queueing, zero calls to `/upload/image` or prepare, 0 real generations. Zero H3 or legacy editor changes.

---

## 2. Implementation Details

### A. Pure Domain Ops (`ComfyUIPortable/manga/app/src/domain/authoring_ops.js`)
- `getNextFigureId(figureRegions)`: Calculates next collision-free `figure_N` ID within a Guide.
- `clampGuideFigureArea(area, minSize)`: Normalizes and clamps Guide-local rectangle within `[0, 1]` enforcing `minSize = 0.04`.
- `calculateNewGuideFigureArea(existingFigures)`: Computes deterministic first/second figure layout in Guide-local space.
- `createGuideFigure(figureRegions)`: Creates new unassigned figure with `instance_id: null` in Guide-local coordinates.
- `clampGuideFigureDrag(startArea, dx, dy)`: Moves figure rectangle strictly within Guide-local `[0, 1]`.
- `resizeGuideFigure(startArea, handle, dx, dy, minSize)`: Resizes figure via NW, NE, SE, SW handles within Guide-local bounds.
- `associateGuideFigure(guide, figureId, instanceId)`: Sets `instance_id` with duplicate association guard within the same Guide.
- `unassignGuideInstance(guide, instanceId)`: Clears association for deleted instances while keeping figure region intact.

### B. Authoring Store (`ComfyUIPortable/manga/app/src/state/authoring_store.js`)
- `toggleGuideEnabled(guideId)`: Toggles `guide.enabled` and validates document schema before commit.
- `deleteGuide(guideId)`: Deletes selected guide without affecting Scenes, Frames, Cast, or Instances.
- `addGuideFigure(guideId)`: Appends newly authored figure in Guide-local space and validates schema.
- `deleteGuideFigure(guideId, figureId)`: Deletes figure without removing associated Character Instance.
- `moveGuideFigure(guideId, figureId, localDx, localDy)`: Updates figure area with Guide-local bounds clamping.
- `resizeGuideFigure(guideId, figureId, handle, localDx, localDy, minSize)`: Resizes figure via corner handle in Guide-local coordinates.
- `associateGuideFigure(guideId, figureId, instanceId)`: Associates instance enforcing duplicate guard and schema validity.

### C. Canvas Renderer & Hit-Testing (`ComfyUIPortable/manga/app/src/view/canvas_renderer.js`)
- Corrected runtime rendering: `placement.x + figure.area.x * placement.w`, etc.
- Selected Figure renders 4 corner handles (`nw`, `ne`, `se`, `sw`) in teal `#0891b2`.
- Active-layer hit-test isolation: when `activeTab === "guides"`, figure handles, figure rectangles, and guide placement rectangles take exclusive hit priority over underlying scenes and frames.

### D. UI & Session Controls (`ComfyUIPortable/manga/app/index.html`)
- Removed `[Read-Only]` tag from Guides panel.
- Added Guide editor, Enable/Disable toggle, Remove Guide button.
- Added Figures list, `+ Add Figure` button, Figure editor with Character Instance association `<select>`, Guide-local coordinates readout, manual move/resize buttons, and Remove Figure button.
- Canvas pointer event handlers for `move_figure` and `resize_figure` with page-to-guide delta conversion.
- Connected `#guide-error-banner` for visible rejection on duplicate instance association.

---

## 3. Verification Results

### A. Pure Guide Tests (`ComfyUIPortable/manga/tests/test_guide_ops.mjs`)
- `A`: `getNextFigureId` collision-free -> PASS
- `B`: New Figure geometry stays in Guide-local `[0, 1]` -> PASS
- `C`: `clampGuideFigureDrag` stays within Guide-local bounds -> PASS
- `D & E`: `resizeGuideFigure` supports NW/NE/SE/SW and respects minimum size -> PASS
- `F & G`: Valid association succeeds, duplicate association rejected -> PASS
- `H`: Unassign preserves Figure region -> PASS
- `I`: Figure deletion does not delete Character Instance -> PASS

### B. Render / Coordinate Mapping Tests (Section 30)
- Verified with non-full-page Guide placement (`x=0.20, y=0.10, w=0.50, h=0.70`) and Figure-local area (`x=0.10, y=0.20, w=0.40, h=0.50`).
- Runtime derived page coordinates (`x=0.25, y=0.24, w=0.20, h=0.35`) hit-test successfully inside transformed area and at SE handle (`x=0.45, y=0.59`).
- Untransformed local coordinates lie outside guide placement and correctly return `null` -> PASS

### C. Store Tests (Section 31)
- `A`: Toggle Guide enabled persists -> PASS
- `B`: Delete Guide leaves other document layers intact -> PASS
- `C`: Add Figure commits valid document -> PASS
- `D`: Remove Figure leaves Instance intact -> PASS
- `E & F`: Move and resize Figure persist local geometry -> PASS
- `G`: Associate / unassign persists -> PASS
- `H`: Character removal unassigns Figure -> PASS
- `I`: Scene deletion unassigns Figures for deleted child Instances -> PASS
- `J`: Export / import exact durable parity without session leakage -> PASS

### D. Real Browser Gate Suite (`ComfyUIPortable/manga/tests/verify_m1c2a_browser.mjs`)
Executed in headless Chromium against `http://127.0.0.1:8191` (zero backend, zero generations):
1. Loaded rich fixture -> PASS
2. Switched to Guides layer -> PASS
3. Selected Guide -> PASS
4. Selected existing Figure `fig_ren` -> PASS
5. Actual canvas pointer-drag Figure (`mousedown`, `mousemove`, `mouseup`) -> PASS
6. Actual pointer resize via SE and NW corner handles -> PASS
7. Added new Figure (`figure_1`) -> PASS
8. Associated new Figure with `inst_sora_1` -> PASS
9. Duplicate association visibly rejected with banner error -> PASS
10. Unassign succeeded -> PASS
11. Guide toggle disabled/enabled verified -> PASS
12. Removed one Figure -> PASS
13-15. Export, reset, and re-import durable parity verified -> PASS
- **Part 2 M1C1 Frame Pointer Regression**:
  - Frame canvas pointer drag verified -> PASS
  - Frame SE corner handle pointer resize verified -> PASS
  - Frame NW corner handle pointer resize verified -> PASS

### E. Full Suite Regression
- `test_domain_document.mjs`: PASS (6/6)
- `test_backend_adapter.mjs`: PASS (9/9)
- `test_canvas_renderer.mjs`: PASS (3/3)
- `test_authoring_ops.mjs`: PASS (14/14)
- `test_document_roundtrip.mjs`: PASS (2/2)
- `test_frame_ops.mjs`: PASS (19/19)
- `test_guide_ops.mjs`: PASS (18/18)
