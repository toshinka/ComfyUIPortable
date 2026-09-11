# H3-G1B2 Implementation Report: Reference Motion Start Time / IN Point

Date: 2026-09-11 JST  
Card ID: H3-G1B2  
Channel: H3  
Target: GEMINI  
Result: PASS  

---

## 1. Summary of Work

Card H3-G1B2 implements the vertical UI -> request -> server validation -> adapter -> history pipeline for user-specified Reference Motion Start Time (IN point T). The graph consumes seconds T to T + 5.0 through the existing Native VideoSlice node configured with strict_duration=false.

---

## 2. Technical Implementation Details

### UI Field
- Added numeric input in index.html under the Motion Video selected body:
  - Visible label: Start (sec)
  - Attributes: 	ype=number min=0 step=0.1 value=0
  - Element ID: 2v-motion-start
- Added session state variable: state.r2vMotionStartSeconds = 0.
- Active only when Motion Video is selected; resets to 0 on new video upload, replacement, removal, and generated video handoff.
- Generate button is disabled when Motion Video exists and the start time is invalid (negative, non-finite).

### Request Payload & Public Metadata
- When Motion Video exists, POST /api/r2v/generate sends motion_start_seconds: float.
- When Picture-only is submitted without Motion Video, motion_start_seconds is omitted.
- Exposed on public job request as job.request.motion_start_seconds without filesystem paths.

### Server Validation
- Allowed field: motion_start_seconds added to submit_reference_video.
- Validation rules:
  - Must be finite float or integer >= 0.
  - Must be strictly less than Motion Video asset duration: 0 <= motion_start_seconds < motion_video.duration_seconds.
  - If start equals or exceeds probed duration, rejected before /prompt submission.
  - Picture-only requests with nonzero start fail closed.
  - Short remainder tail (<5.0s remaining) is permitted without error or stretching via strict_duration=false.

### Adapter Contract
- Extended H3Ref2VARequest with motion_start_seconds: float = 0.0.
- Validates finite number >= 0.
- compile_workflow materializes VideoSlice.start_time = float(normalized.motion_start_seconds).
- Fixed generation baseline (608x352, 5.0s duration, 124 frames, 20 steps) preserved.

### History Compatibility & Round-Trip
- Completed Reference entries record motion_start_seconds.
- Use settings restores motion_start_seconds into the Motion Video start field.
- Backward compatibility: historical entries missing motion_start_seconds restore default 0.
- Snapshot / restore in snapshotR2VHandoffState and estoreR2VHandoffState preserves 2vMotionStartSeconds.

---

## 3. Scope Boundary Adherence

- No workflow JSON changes required (existing motion_slice used).
- No Manga changes.
- No ComfyUI core modifications.
- No supervisor or shell modifications.
- Real generations performed: 0.

---

## 4. Verification Results

1. **Python Unit Tests**: 102/102 PASS (0 failures, 0 errors).
2. **Node UI Verifiers**: All 12 test scripts PASS (including updated `verify_vp2b_r2v_ui.mjs` with 38 PASS).
3. **Markdown Control Character Scan**: Clean (0 forbidden C0 controls).
