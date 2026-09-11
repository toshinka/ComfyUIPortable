TEGAKI_REPORT_V1
CARD_ID: H3-G1A
RESULT: PASS WITH LIMIT
INITIAL_HEAD: 2f66d73ecf91ce002faa1c41e61192a43da3ae4e
EXECUTOR: GEMINI
REMOTE_PUBLICATION: NOT PERFORMED — OWNER ACTION REQUIRED

# H3-G1A Stage Action Compression and Media Feasibility Report

## 1. Executive Summary

Card H3-G1A successfully implements the Stage action density compression, establishes the living H3 product ideas backlog, and completes deep architectural audits for truthful progress reporting, aspect-safe image references, and reference video trimming/offsets.

No real generations were submitted (count: 0). No Manga files were touched. No workflow JSON files were altered.

Live browser review is reported as **PASS WITH LIMIT** because the local H3 Skin (`127.0.0.1:8190`) and Native backend (`127.0.0.1:8188`) were offline, and this Card strictly forbids unauthorized process spawning or control. Comprehensive DOM, CSS, and behavioral simulation verifiers confirm 100% test passage (12/12 test suites, 22 new assertions in `verify_h3_g1a_stage_action.mjs`, and 100/100 Python unit tests).

---

## 2. Stage Action Compression Results

### Problem Addressed
Previously, Wide layout wasted significant Stage area above the Preview on:
- A separate two-line STATUS card ("STATUS", "Generating", "Native backend is generating").
- A large Generate button and a large Cancel button displayed simultaneously side-by-side during active jobs.
- Duplicate elapsed time tracking across both the status card and the Preview overlay.

### Implemented Improvements
1. **Compact Stage Action Bar**:
   - `min-height` reduced from 58px to 42px.
   - `margin-bottom` reduced from 12px to 8px.
   - `padding` reduced from 8px 10px to 4px 10px.
2. **Compact Single-Line Status**:
   - In `.stage-status-slot`, the uppercase `.status-label` ("STATUS") is hidden (`display: none`).
   - `#generation-status` (strong) and `#status-detail` (span) align cleanly on a single baseline flex row.
   - Error messages (`FAILED`, `DISCONNECTED`) remain truthful, prominent, and non-truncated.
3. **Single-Slot Action Button Swapping**:
   - Idle / Ready state: Exactly one compact Generate button (`min-height: 34px`, `min-width: 110px`, `padding: 0 14px`, `font-size: 0.82rem`). Cancel is hidden.
   - Active Generation state: Generate is replaced by Cancel in the exact same slot (`generateButton.hidden = !cancelButton.hidden`). Cancel has matching compact styling (`min-height: 34px`, `min-width: 110px`, `margin-top: 0`).
   - Submitting state: Generate shows "Submitting…" and is disabled; Cancel remains hidden.
   - Simultaneous Generate + Cancel: Prevented deterministically by strict boolean inversion (`generateButton.hidden = !cancelButton.hidden`).
4. **Preserved Preview Elapsed Display**:
   - The `#preview-overlay` continues to serve as the primary running-state indicator (`Generating · 126.0s`).
5. **Narrow Mode Regression**:
   - Narrow Create / Result tab navigation and responsive mounting behavior are preserved without regressions.

---

## 3. Progress Feasibility Audit (Section 6)

- **Feasibility Classification**: `SUPPORTED WITH LIMIT`
- **Real Progress Event**: Present in ComfyUI core (`main.py:hijack_progress` and `comfy.utils.ProgressBar`).
- **Transport**: WebSocket connection to `/ws?clientId=<clientId>`.
- **Payload**: `{"value": value, "max": total, "prompt_id": prompt_id, "node": node_id}`.
- **Semantic Classification**: `SAMPLER ONLY`
  - The progress event is emitted from `ProgressBar` instances, primarily inside `latent_preview.py:prepare_callback` (KSampler / MiniMax sampling loop) and tiled VAE decode/encode.
  - It does **not** measure total workflow execution (model loading, text encoding, and audio VAE decoding do not advance this counter).
- **Labeling Recommendation**:
  - Must be explicitly labeled as sampler progress: e.g., `Sampling 7 / 20` or `Sampling 35%`.
  - Must never be labeled as total job completion percentage (e.g. "35% complete").
- **H3 Skin Integration Path**:
  - H3 Skin currently communicates with Native ComfyUI purely via HTTP REST (`/queue`, `/history/<prompt_id>`).
  - H3 Skin server can open an internal background WebSocket listener to `ws://127.0.0.1:8188/ws` matching the job's client ID, update `Job.sampling_step` and `Job.sampling_total`, and expose them via existing `GET /api/jobs/<job_id>` polling.
  - A deterministic mock/stub test can verify this mapping without executing real GPU models.

---

## 4. Image Aspect Audit (Section 7)

- **Root-Cause Confidence**: `IDENTIFIED`
- **Distortion Analysis**:
  - **Standard Start Frame & Still Source Image**:
    - Both map to `MiniMaxH3ImageToVideo.first_frame` (`comfy_extras/nodes_minimax_h3.py:131-134`).
    - The node explicitly comments `# geometry anchor: plain stretch to canvas` and executes `_resize(first_frame[:1], width, height, "disabled")`.
    - `crop="disabled"` forces an anamorphic stretch from the source dimensions into the target 608x352 (1.72:1) canvas. Portrait or square inputs are heavily squashed vertically / stretched horizontally in actual generation pixels.
  - **Standard End Frame**:
    - Maps to `MiniMaxH3ImageToVideo.last_frame` (`nodes_minimax_h3.py:136-139`).
    - Executes `_resize(last_frame[:1], width, height, "center")`, which performs an aspect-preserving center cover-crop.
  - **Ref2VA Picture Reference**:
    - Maps to `MiniMaxH3ReferenceToVideo.ref_images` (`nodes_minimax_h3.py:221-233`).
    - Scales with aspect ratio preservation (`scale = min(1.0, math.sqrt((width * height) / (w * h)))`), but places the reference into a landscape canvas.
  - **UI / CSS**:
    - `.reference-thumbnail` uses `object-fit: cover;`, which crops thumbnails nicely in the UI but masks the severe anamorphic distortion occurring in the underlying `first_frame` conditioning.
- **Policy Candidates**:
  1. *Aspect-preserving cover-crop (crop-to-fill)*: Matches `last_frame` (`crop="center"`). Avoids distortion; crops outer edges.
  2. *Aspect-preserving contain / pad (letterbox/pillarbox)*: Letterboxes or pillarboxes with neutral fill. Preserves all pixels; introduces black/neutral bars into the video generation canvas.
  3. *Interactive crop / Prep/Edit handoff*: Allows user to position and preview the 608x352 crop frame prior to submission.
- **Recommended Next Step**: Introduce a bounded Card providing an aspect-safe cover-crop mode (`crop="center"`) for `first_frame` / `still_source`.

---

## 5. Reference Video Audit (Section 8)

- **Native Interface Inspection**:
  - In `comfy_extras/nodes_video.py`, `LoadVideo` (line 220) accepts only a `file` parameter and outputs an `io.Video.Output()`. It has no built-in trimming or skip parameters.
  - However, the exact same native module provides `VideoSlice` (`Trim Video`, line 260):
    - Inputs: `video` (io.Video), `start_time` (Float, seconds), `duration` (Float, seconds), `strict_duration` (Boolean).
    - Output: `io.Video.Output()`.
  - In `VP2A_NATIVE_REF2VA_BASE.json`, `motion_loader` (`LoadVideo`) currently connects directly to `motion_components` (`GetVideoComponents`).
  - Inserting `VideoSlice` between `LoadVideo` and `GetVideoComponents` provides clean, native trimming and time offsets before frame extraction occurs.
- **Case A (First N seconds only)**: `SIMPLE`
  - Connect `VideoSlice(start_time=0.0, duration=5.0)` between `LoadVideo` and `GetVideoComponents`.
  - ComfyUI's core `as_trimmed()` handles trimming prior to decoding frames.
- **Case B (Start at user time T and consume N seconds)**: `SIMPLE`
  - Expose a single `start_time` parameter in the UI / adapter.
  - Materialize `VideoSlice(start_time=T, duration=5.0)`.
- **FFmpeg / External Preprocessing**: `NOT REQUIRED`
  - ComfyUI core native nodes fully support both slicing and start-offsets without external scripts or tools.

---

## 6. Verification Summary

- **UI Tests**:
  - `verify_h3_g1a_stage_action.mjs`: **22 PASS**
  - `verify_h3_r1_stage_generate_visibility.mjs`: **61 PASS**
  - `verify_h3_r2a1_backend_reconnect.mjs`: **10 PASS**
  - `verify_h3_r2b_profile_guard.mjs`: **16 PASS**
  - `verify_ip2_prep_edit.mjs`: **45 PASS**
  - `verify_vp1_video_ui.mjs`: **PASS**
  - `verify_vp2b_r2v_ui.mjs`: **28 PASS**
  - `verify_vp2c_reference_handoff.mjs`: **36 PASS**
  - `verify_h1b1_p2_ui.mjs`: **44 PASS**
  - `verify_h1b1_p1_layout.mjs`: **36 PASS**
  - `verify_h1c_continuation.mjs`: **38 PASS**
  - `verify_h2c_still_ui.mjs`: **52 PASS**
- **Python Unit Tests**:
  - Full suite (`python -m unittest discover -s ComfyUIPortable/h3/tests`): **100 PASS** in 7.9s.
- **Real Generations**: **0**
- **Git Diff Check**: **Clean**

---

## 7. Recommended Next Cards

1. **`H3-G1B`**: Reference Video Native Trimming & Start Offset (Materialize `VideoSlice` in `native_ref2va` for 5s duration & start-time IN point).
2. **`H3-G1C`**: Aspect-Safe Image Framing for Start Frame & Source Image (Cover-crop option to eliminate anamorphic stretching).
3. **`H3-G2A`**: Truthful Sampler Progress WebSocket Consumer (`Sampling X%`).
