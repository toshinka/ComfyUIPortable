# MANGA-M1C2B — Standalone Guide Asset Ingestion + Preview Report

- **Card**: `MANGA-M1C2B`
- **Executor**: Gemini 3.8 Flash / Antigravity 2.0
- **Baseline SHA**: `0cc1d8951d6275715282e3aad00f8c2c844678cb`
- **Scope**: `ComfyUIPortable/manga/**`
- **Result**: PASS

---

## 1. Scope & Responsibility

MANGA-M1C2B completes the bounded standalone Rough Guide authoring slice:
- **Add Guide from Local File**: Supports PNG, JPEG, and WEBP image ingestion via `+ Add Guide` button and hidden file input.
- **Replace Selected Guide Asset**: Supports replacing the image of any selected Guide via `Replace Asset` button, preserving the `guide_id`, `enabled` status, and all Guide-local `figure_regions`.
- **Pure Contain-Fit Placement**: Pure domain function `calculateContainPlacement(imageWidth, imageHeight, pageWidth, pageHeight)` centers the image on page without cropping, preserving the native aspect ratio for square, portrait, and landscape assets.
- **Dedicated Workspace Transport Endpoints**:
  - `POST /api/guide-assets/upload?filename=...`: Dedicated Workspace upload endpoint with strictly enforced loopback/same-origin policy, basename-only filename validation (rejects path traversal, backslashes, null/control characters), 20 MiB size limit, strict magic byte inspection (PNG `89 50 4E 47 0D 0A 1A 0A`, JPEG `FF D8 FF`, WEBP `RIFF....WEBP`), and file extension matching.
  - Forwards multipart FormData (`image`, `subfolder: "tegaki_manga_guides"`) to configured ComfyUI backend endpoint `/upload/image`.
  - `GET /api/guide-assets/view?ref=...`: Dedicated view proxy streaming binary image data from ComfyUI `/view?filename=...&subfolder=tegaki_manga_guides&type=input`. Enforces subfolder namespace prefix `tegaki_manga_guides/` and basename validation.
- **No Direct Browser Backend Access**: The browser client communicates exclusively with the Workspace server on origin (e.g. `http://127.0.0.1:8191`); no direct requests to ComfyUI port 8189 or `/upload/image` are made from the frontend.
- **Canvas Image Preview & Caching**: Standalone canvas renderer accepts cached guide images and paints the rough guide at `(gx, gy, gw, gh)` before borders and figure regions. Respects enabled state (full opacity vs translucent when disabled).
- **Inspector Thumbnail Preview**: `#guide-editor-container` displays image thumbnail `#guide-preview-thumbnail` with `src` pointing to `/api/guide-assets/view?ref=...`.
- **Zero Real Generations & Zero Queueing**: Fake backend and live probes verify queue remains known IDLE and 0 real generations are performed. Zero H3 or legacy editor changes.

---

## 2. Implementation Summary

### A. Pure Domain Ops (`ComfyUIPortable/manga/app/src/domain/authoring_ops.js`)
- `getNextGuideId(guides)`: Derives collision-free `guide_N` identifier.
- `calculateContainPlacement(iw, ih, pw, ph)`: Computes page-normalized contain-fit placement `(x, y, w, h)` rounded to 4 decimals, centered and uncropped.

### B. Authoring Store (`ComfyUIPortable/manga/app/src/state/authoring_store.js`)
- `addGuideFromAsset({ asset_reference, image_width, image_height })`: Validates dimensions, generates `guide_id`, computes contain placement, sets `guide_type: "rough_manga"`, stores `fit_mode: "contain"` and source dimensions in metadata, commits valid document.
- `replaceGuideAsset(guideId, { asset_reference, image_width, image_height })`: Updates `asset_reference`, recalculates placement, preserves `guide_id`, `enabled`, and all `figure_regions` in Guide-local coordinates.

### C. Workspace Server (`ComfyUIPortable/manga/service/manga_workspace_server.mjs`)
- Dynamic port detection in `allowedLocalOrigins` for both configured and bound ports.
- `POST /api/guide-assets/upload`: Origin enforcement, basename-only traversal checks, 20 MiB stream buffering, magic byte validation, multipart forwarding via Node 22 native `fetch`/`FormData`/`Blob` to `${BACKEND_URL}/upload/image`, verification of backend response subfolder.
- `GET /api/guide-assets/view`: Enforces `tegaki_manga_guides/` namespace, basename validation, proxies to `${BACKEND_URL}/view`, validates image content type, pipes binary data.

### D. Canvas Renderer & App UI (`ComfyUIPortable/manga/app/src/view/canvas_renderer.js` & `ComfyUIPortable/manga/app/index.html`)
- `renderMangaCanvas(canvas, document, sessionState, pageIndex, imageCache)`: Draws cached images into guide placements with opacity adjustment for disabled guides.
- `guideImageCache`: Map of `asset_reference -> HTMLImageElement` with automatic canvas re-render upon image load.
- UI elements: `+ Add Guide` button, `Replace Asset` button, hidden file input, and `#guide-preview-thumbnail` in inspector.

---

## 3. Verification & Regressions

1. **Pure & Server Tests (`ComfyUIPortable/manga/tests/test_guide_asset_ops.mjs`)**:
   - `getNextGuideId`: Collision-free ID generation verified.
   - `calculateContainPlacement`: Square, ultra-wide landscape, tall portrait, and exact aspect ratio contain-fit verified.
   - Store operations: `addGuideFromAsset` and `replaceGuideAsset` tested with figure preservation.
   - Server upload security: Rejects invalid magic bytes (400), rejects path traversal (400), rejects cross-origin upload (403), validates 20 MiB limit.
   - Exact byte integrity: Verified exact byte-for-byte binary equality between uploaded buffer and backend received buffer via `Buffer.compare === 0`.
   - View streaming: Exact byte-for-byte streaming verified via `/api/guide-assets/view`.
   - Format support: PNG, JPEG, and WEBP successfully verified.

2. **Real Browser Gate Suite (`ComfyUIPortable/manga/tests/verify_m1c2b_browser.mjs`)**:
   - Step 1: Open standalone workspace (0 initial guides).
   - Step 2: Ingest PNG guide via file chooser -> Guide count 1, active layer automatically switches to guides.
   - Step 3: Inspector thumbnail loaded from same-origin `/api/guide-assets/view`.
   - Step 4: Contain-fit placement verified in store.
   - Step 5: Replace asset with square WEBP -> asset_reference updated, figure regions preserved.
   - Step 6: Export JSON -> Reset -> Re-import JSON -> durable asset reference and placement survive.
   - Step 7: Queue remains IDLE, 0 generations executed.

3. **Full Regressions**:
   - `test_domain_document.mjs`: PASS
   - `test_backend_adapter.mjs`: PASS
   - `test_canvas_renderer.mjs`: PASS
   - `test_authoring_ops.mjs`: PASS
   - `test_document_roundtrip.mjs`: PASS
   - `test_frame_ops.mjs`: PASS
   - `test_guide_ops.mjs`: PASS
   - `test_guide_asset_ops.mjs`: PASS
   - `verify_m1c2b_browser.mjs`: PASS
