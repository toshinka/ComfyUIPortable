TEGAKI_REPORT_V1
CARD_ID: H3-G1B1
RESULT: PASS
INITIAL_HEAD: 64a14e3fb4957db92dec55cc6769cce252f1e8c1
EXECUTOR: GEMINI
REMOTE_PUBLICATION: NOT PERFORMED — OWNER ACTION REQUIRED

# H3-G1B1 Reference Motion Video First-5s Native Trim Report

## 1. Summary

Card H3-G1B1 implements bounded native trimming of Ref2VA reference motion videos to the first 5.0 seconds (matching the fixed 5.0s / 124 frames / 24 fps / 20 steps Ref2VA baseline) using the ComfyUI core `VideoSlice` ("Trim Video") node.

No real generations were submitted (count: 0).
No Manga files were modified.
No ComfyUI core modifications were made.
No H3 server or UI changes were made.
No start-offset UI was implemented.

---

## 2. Native Node Contract & Wiring

### Native Node Class
- **Class**: `VideoSlice` (`io.ComfyNode` from `comfy_extras/nodes_video.py`)
- **Registered Node Class Type in API graph**: `"Video Slice"`

### Exact Node Inputs
- `video`: `["134", 0]` (fed from `LoadVideo`)
- `start_time`: `0.0`
- `duration`: `5.0` (derived strictly from the Ref2VA baseline `duration_seconds`)
- `strict_duration`: `False`

### strict_duration Decision & Rationale
`strict_duration` is explicitly set to `False` (matching the node's native default).
- When input video is longer than 5.0 seconds: slices exactly the first 5.0 seconds.
- When input video is shorter than 5.0 seconds: returns all available duration truthfully without raising an execution exception and without inventing frames or artificially stretching temporal content.

---

## 3. Graph Behavior

### Picture-Only Mode
When no motion video reference is provided:
- Unused motion pipeline nodes (`motion_loader` [134], `motion_slice` [136], and `motion_components` [135]) are completely pruned from the compiled graph.
- `conditioning` contains no `ref_videos.ref_video_1` entry.
- Audio reference lanes remain completely disconnected.

### Picture + Motion Mode
When a valid staged motion video is provided:
- The compiled pipeline wires:
  `LoadVideo` (134) $\to$ `Video Slice` (136) $\to$ `GetVideoComponents` (135) $\to$ `MiniMaxH3ReferenceToVideo` (131).
- Trimming occurs before video demuxing into individual frame tensors, avoiding memory bloat from decoding unused frames.
- Existing 608x352 resolution, 124 frame count, 20 steps, and model weights remain strictly unchanged.

---

## 4. Verification

- `test_vp2a_ref2va_adapter.py`: **4 PASS** (all assertions A through I verified).
- Full Python test suite (`100 PASS`):
  - `test_h3_profile_guard.py`: 13 PASS
  - `test_vp2b_r2v_playground.py`: 7 PASS
  - `test_vp2c_reference_handoff.py`: 8 PASS
  - `test_ip2_prep_server.py`: 13 PASS
  - `test_pi1_lifecycle_snapshot.py`: 12 PASS
  - all existing adapters and server tests PASS.
- Full UI suite (`12/12 .mjs verifiers PASS`):
  - `verify_h3_g1a_stage_action.mjs`: 22 PASS
  - `verify_vp2b_r2v_ui.mjs`: 28 PASS
  - `verify_vp2c_reference_handoff.mjs`: 36 PASS
- `git diff --check`: **Clean**
