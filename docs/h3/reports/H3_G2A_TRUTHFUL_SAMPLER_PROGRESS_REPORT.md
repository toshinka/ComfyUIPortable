# H3-G2A Implementation Report: Truthful Sampler Progress Channel

Date: 2026-09-12 JST  
Card ID: H3-G2A  
Channel: H3  
Target: GEMINI  
Result: PASS  

---

## 1. Summary of Work

Card H3-G2A implements a truthful, supplemental live sampler progress channel for TEGAKI H3. A server-side background WebSocket listener (`NativeProgressListener`) connects to Native ComfyUI using the session's existing client ID (`/ws?clientId=<client_id>`). It strictly validates incoming `progress` events against the submitted prompt ID and dynamically discovered sampler node IDs (`SamplerCustomAdvanced`), exposing sampler progress via `Job.public()["progress"]` to the browser without displacing HTTP queue/history authority or altering job states.

---

## 2. Installed Native Event Contract & Source Evidence

Before implementation, the installed ComfyUI core source was inspected:
- **WebSocket Endpoint**: `server.py` line 269: `@routes.get('/ws')` extracts `clientId = request.rel_url.query.get('clientId', '')`.
- **Event Dispatch**: `main.py` lines 447–450 (`hijack_progress`):
  ```python
  progress = {"value": value, "max": total, "prompt_id": prompt_id, "node": node_id}
  server_instance.send_sync("progress", progress, server_instance.client_id)
  ```
- **Envelope**: `server.py` lines 1382–1390 (`send_json`):
  ```json
  {"type": "progress", "data": {"value": 7, "max": 20, "prompt_id": "...", "node": "125"}}
  ```
- **Conclusion**: Both `prompt_id` and `node` are reliably emitted on all `progress` events.

---

## 3. Technical Implementation Details

### Dependency & Module Architecture
- **Dependency**: Used `aiohttp` (version 3.13.1 already installed in the environment). Zero new packages installed; zero requirement changes.
- **Pure Module**: Implemented `ComfyUIPortable/h3/app/native_progress.py`:
  - `discover_sampler_node_ids(graph, target_classes)`: Dynamically scans compiled workflow graphs for sampler node IDs matching `SamplerCustomAdvanced` instead of relying on hard-coded IDs.
  - `map_progress_event(event_data, expected_prompt_id, allowed_sampler_node_ids)`: Pure function validating prompt ID match, sampler node ID match, non-negativity, finite numeric boundaries, 0 <= value <= max, and computing percent = floor((value / max) * 100).
  - `NativeProgressListener`: Background thread managing an `asyncio` event loop with `aiohttp.ClientSession.ws_connect` subscribing to `/ws?clientId=<client_id>`.

### Session & Server Integration
- In `server.py`:
  - `Job` dataclass tracks `sampler_node_ids: set[str]` and `progress: dict[str, Any] | None`.
  - `Job.public()["progress"]` exposes progress only when `job.state == "RUNNING"`. On terminal states (`COMPLETED`, `FAILED`, `CANCELLED`) or `DISCONNECTED`, progress is strictly `None`.
  - `H1ASession` manages one `NativeProgressListener` using the session's existing `self.client_id`.
  - Submissions (`submit`, `submit_still`, `submit_prep`, `submit_reference_video`) extract and attach dynamic `sampler_node_ids` from the compiled graph before queuing.
  - Lifecycle: `start_progress_listener()` and `stop_progress_listener()` explicitly bound to server startup/shutdown in `main()`.

### Disconnect & Stale Progress Handling
- When the WebSocket channel drops, `_handle_progress_disconnect()` clears `job.progress = None` across all active non-terminal jobs.
- Disconnection of the progress channel does not alter `Job.state` or HTTP polling.
- Reconnection attempts back off gracefully without busy-looping.

### UI Presentation
- In `app.js`, `showPreviewJob(job)` formats `previewState.textContent` as:
  `Generating · Sampling ${progressPercent}%`
  when running with valid sampling progress.
  Falls back immediately to truthful `statusLabelForJob(job)` (`Generating`) and elapsed time if progress is absent, disconnected, or non-sampling.
- Preview job ownership isolation is preserved: selecting an older historical job in Preview does not display active job progress.

---

## 4. Verification Results

1. **Python Unit & Fake WebSocket Integration Tests**: 123/123 PASS (0 failures, 0 errors).
   - Dynamic sampler node ID discovery: PASS.
   - Comprehensive validation matrix (A through O): PASS.
   - Multi-job & stale prompt isolation: PASS.
   - Loopback fake WebSocket server integration: PASS (verifies connect, progress, non-sampler node filter, drop/clear, and shutdown).
   - Reconnect: VERIFIED BY SECOND LOOPBACK CONNECTION + SECOND VALID PROGRESS EVENT (`test_loopback_ws_reconnect_flow` proves drop, clear, 2nd connection, stale rejection, 60% update, and clean thread termination).
2. **Node UI Verifiers**: All 13 suites PASS (including `verify_h3_g2a_progress.mjs` with 25 PASS).
3. **Live Native WS Handshake**: NOT TESTED / UNAVAILABLE (Native ComfyUI backend port 8188 is offline, as expected without starting backend).
4. **Scope & Code Hygiene**:
   - Zero workflow JSON changes.
   - Zero Manga changes.
   - Zero new pip dependencies.
   - Git diff check clean.
   - Zero forbidden Markdown C0 control characters or malformed backslash escapes.
