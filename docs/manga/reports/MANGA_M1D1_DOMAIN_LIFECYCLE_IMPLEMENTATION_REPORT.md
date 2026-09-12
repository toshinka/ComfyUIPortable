# MANGA-M1D1 Domain Lifecycle Implementation Report

CARD_ID: MANGA-M1D1 (Hardened by MANGA-M1D1A)
BASE_SHA: 39fdea87e4c5d2ce77829802956ab4ba995e4a53
STATUS: COMPLETED (SOURCE / LOGIC / FAKE-PROCESS VERIFICATION)
EXECUTOR: GEMINI

---

## 1. Executive Summary

MANGA-M1D1 (and subsequent SOL audit hotfix MANGA-M1D1A) implements the Manga-specific domain lifecycle controller defined in MANGA-M1D0. In accordance with card requirements, this implementation was verified using source, logic, and deterministic fake-process fixtures only:
- **0 real ComfyUI processes started** (no real Python ComfyUI backend child).
- **0 real generations executed**.
- **No GPU or model loading performed**.
- Real Portable validation remains deferred to CODEX.
- Manga authoring features remain strictly frozen.

---

## 2. Corrections to M1D0 Audit Report & Audit Fixes (M1D1A)

### 2.1 Initial M1D0 Audit Corrections
1. **Language Truthfulness**: Replaced all claims of "cryptographically sound identity" and "cryptographic ownership verification" with "positive deterministic service/profile identity" and "process ownership evidence".
2. **Prepare Route Fingerprint Expectation**: Corrected capability probe expectation to `HTTP 400` with `ok == false` and `error_code == "MISSING_DOCUMENT"`.
3. **No Force Stop / Force Kill Exception**: Completely eliminated normal force stop/kill exceptions. The Manga Domain Runtime strictly fails closed.
4. **Public Lifecycle States**: Standardized public states to `STOPPED`, `STARTING`, `READY`, `BUSY`, `DEGRADED`, `STOPPING`, `FAILED`. Internal states exist internally only.
5. **Identity Route Status**: Marked `GET /api/runtime/identity` as proposed in M1D0 and implemented by M1D1.
6. **Browser Authoring Separation Truth**: Clarified that browser-held authoring state is independent from backend lifetime, surviving backend restart while the browser page remains alive, but uncommitted memory is not guaranteed across tab destruction.
7. **Port Assignments**: Defined ports 8188, 8189, and 8191 as current configurable defaults, not eternal reservations.
8. **Canonical Command**: Designated the canonical backend command as a source-derived candidate pending CODEX real runtime validation.

### 2.2 SOL Audit Hardening (MANGA-M1D1A)
1. **Fail-Closed Second Queue Recheck**: Removed fallback to first queue read. If the second `/queue` recheck is unavailable (`status === 0`), non-200, invalid JSON, or missing array fields, probe returns `PORT_OCCUPIED_WRONG_PROFILE` with `queue: null`.
2. **Exact Node Fingerprint**: Removed overly permissive check (`|| Boolean(nodeRes.json.input)`). Exactly requires `TegakiMinimumHandSceneEditor` in node definition object.
3. **Child Exit Diagnostics**: Added `lastBackendExit` and `lastWorkspaceExit` recording `{ code, signal, timestamp, intentional }`.
4. **Tested Public restartBackend()**: Full deterministic test of public `await runtime.restartBackend()` asserting termination of old child, spawning of new child, workspace process preservation, and reaching `READY`.
5. **Tested Unexpected Workspace Exit**: Full deterministic test asserting backend survives untouched, workspace process record is cleared, status reports `DEGRADED`, and exit diagnostics are recorded.
6. **Partial Startup Failure Handling**: When owned backend is spawned and workspace probe encounters pre-existing wrong profile, external wrong workspace is NEVER killed, and owned backend is safely stopped (or kept explicitly owned if busy, never orphaned).

### 2.3 Spawn Ownership Truth on Startup Failure (MANGA-M1D1B)
1. **Immediate Ownership Assignment**: In `_spawnBackendChild()` and `_spawnWorkspaceChild()`, ownership is assigned to `OWNED_BY_THIS_RUNTIME` immediately upon acquiring the `ChildProcess` handle and recording the process metadata, prior to any readiness polling.
2. **No False Reversion to UNAVAILABLE**: Startup polling timeout, wrong profile verification, or internal error cannot cause an active, running child handle to revert to `UNAVAILABLE`.
3. **Truthful Public Status on Startup Failure**: Failure in `start()` transitions `internalSubstate` to `FAILED` and records `lastError`. Any subsequent `getStatus()` check truthfully reflects `FAILED` or `DEGRADED` (if pre-existing backend is compatible), never a misleading `STOPPED` or `READY`.
4. **Lifecycle Exit Synchronization**: Child exit listeners on the spawned processes exclusively reset `processRecord` to `null` and return ownership to `UNAVAILABLE` once the OS process has actually terminated.

### 2.4 Preserve Owned Process Identity Across start() Re-entry (MANGA-M1D1C)
1. **Root Cause**: While M1D1B established immediate ownership assignment upon spawn, subsequent calls to `start()` (e.g. repeated `start()`, `stopBackend() -> start()`, or `stopWorkspace() -> start()`) probed target ports and unconditionally overwrote ownership to `PREEXISTING_COMPATIBLE` while discarding `backendProcessRecord` / `workspaceProcessRecord`.
2. **Re-entry Invariant**: If this runtime already has `OWNED_BY_THIS_RUNTIME` and a live matching `processRecord` / child handle, positive service probe retains `OWNED_BY_THIS_RUNTIME` and preserves the existing process record. Only when no live owned child exists is positive identity classified as `PREEXISTING_COMPATIBLE`.
3. **Idempotency**: Invoking `await runtime.start()` when both services are already running and owned returns `READY`, spawns zero additional children, and keeps both child handles, PIDs, and ownerships intact.
4. **Zero Duplicate Spawn on Unavailable / Wrong Profile Probe**: If an owned child handle is alive but the HTTP probe is temporarily `UNAVAILABLE` or reports `WRONG_PROFILE`, `start()` fails closed without spawning a duplicate second child or detaching from the owned handle.
5. **Partial Service Recovery & Clean Teardown**: After `stopBackend() -> start()` or `stopWorkspace() -> start()`, exactly one replacement child is spawned for the stopped service while the survivor's handle and PID remain untouched. Subsequent `stopAll()` terminates both owned processes cleanly without process leaks.

### 2.5 Existing-Owned Cleanup Guard + Exit-Truth Ownership (MANGA-M1D1D)
1. **Exit Event Authority**: A child process remains owned and recorded until the child's `exit` event actually fires. `child.killed` indicates only that a signal was sent; it is not treated as evidence of process termination.
2. **Termination Timeout Truth**: If `child.kill("SIGTERM")` is sent and the child fails to exit within `shutdownTimeoutMs`, termination throws a timeout error while preserving `processRecord` and `OWNED_BY_THIS_RUNTIME`. No duplicate process is spawned on subsequent `start()`, and ownership is never downgraded to `PREEXISTING` or cleared to `UNAVAILABLE`.
3. **Pre-Owned Backend Preservation**: In `start()`, cleanup upon discovering an incompatible Workspace profile is strictly scoped to backends spawned during that exact `start()` call (`spawnedBackendThisStart`). An already-running, pre-owned backend is never stopped or killed when Workspace startup fails.

---

## 3. Runtime Architecture & Ownership Contract

### 3.1 Controller Component
Implemented in `ComfyUIPortable/manga/service/manga_domain_runtime.mjs`:
- Class `MangaDomainRuntime` utilizing pure Node.js built-ins (`node:http`, `node:child_process`, `node:fs`, `node:path`). Zero npm dependencies.
- Derives all paths (Portable root, python.exe, main.py, workspace script) relative to the module location, independent of `process.cwd()`.

### 3.2 Process Ownership Model
- Processes are classified strictly into:
  - `OWNED_BY_THIS_RUNTIME`: Child process handle held directly by this runtime instance (PID, spawn timestamp, argv, ChildProcess handle recorded).
  - `PREEXISTING_COMPATIBLE`: Positive identity verified on target port, but process was not spawned by this controller.
  - `PORT_OCCUPIED_WRONG_PROFILE`: Port occupied by an incompatible service.
  - `UNAVAILABLE`: Port is closed / connection refused.
- Ownership is **never** inferred from port discovery.

### 3.3 Strict Anti-Kill-by-Port Safeguard
- Zero `taskkill`, `Stop-Process`, or `netstat` process termination.
- Discovering an external PID listening on a port never triggers process termination.
- Only direct `ChildProcess` handles spawned by this controller are terminated on shutdown.

---

## 4. Positive Deterministic Identity Fingerprinting

### 4.1 Backend Fingerprint
Requires ALL of:
1. `GET /queue`: Returns HTTP 200 with arrays `queue_running` and `queue_pending`.
2. `GET /object_info/TegakiMinimumHandSceneEditor`: Returns HTTP 200 with exact node key `TegakiMinimumHandSceneEditor`.
3. Non-mutating Capability Probe `POST /tegaki/manga/generation/prepare` with body `{}`: Returns HTTP 400 with `ok == false` and `error_code == "MISSING_DOCUMENT"`.
4. Second `GET /queue` recheck: Confirms queue remained completely untouched and idle. If this second check fails, returns `PORT_OCCUPIED_WRONG_PROFILE` with `queue: null` (fail-closed; no fallback).

### 4.2 Workspace Server Fingerprint
Added endpoint `GET /api/runtime/identity` to `ComfyUIPortable/manga/service/manga_workspace_server.mjs`:
```json
{
  "service": "tegaki_manga_workspace",
  "version": "1.0.0",
  "domain": "manga",
  "authoring_schema": "1.0.0",
  "backend_target": "http://127.0.0.1:8189"
}
```
Does not expose PIDs, filesystem paths, or tokens.

---

## 5. Fail-Closed Safe-Stop and Restart Rules

- `stopBackend()` and `restartBackend()`:
  - Allowed **only** when `backendOwnership === OWNED_BY_THIS_RUNTIME`.
  - Refuses stop/restart if pre-existing compatible or wrong profile.
  - Requires queue check confirming `queue_running.length === 0` and `queue_pending.length === 0`.
  - If queue is busy, unavailable, or malformed: **REFUSES STOP** (Fail-Closed).
  - Absolutely **NO force flag** or override.
- `stopWorkspace()`:
  - Terminates only owned workspace child. Never affects backend.
- `stopAll()`:
  - If owned backend cannot pass safe-stop (e.g. busy), **REFUSES full shutdown** to avoid abandoning or orphaning an unmanaged busy process.

---

## 6. Two-Engine Manga Boundary Architecture Note

The existing standalone Manga track is the **Illustrious / ReForge Manga Engine**. It is independent of future H3 Manga / Previs work:
- **Illustrious/ReForge Manga**: Style diversity, LoRA assets, final redraw/bake, Scene/Frame/Guide structural assistance.
- **H3 Manga / Previs**: Prompt-faithful structure, composition, reference placement, previsualization.
- **Future Convergence**: Asset, reference, and ControlNet material handoff (e.g. H3 output -> Guide/reference -> Illustrious redraw).
- This lifecycle controller owns **only** the Illustrious / ReForge Manga track. Zero H3 files were modified.

---

## 7. Deterministic Fake-Process Test Evidence

Implemented comprehensive test suite `ComfyUIPortable/manga/tests/test_domain_lifecycle.mjs` verifying:
- **Base Matrix A through Y**:
  - **Test A, B, C**: Unavailable backend & workspace -> spawned owned fake children, recorded PIDs and child handles (`PASS`).
  - **Test D, E**: Pre-existing compatible backend & workspace reused and never killed (`PASS`).
  - **Test F, G**: Incompatible wrong profile on backend or workspace blocks startup with diagnostic error, without killing (`PASS`).
  - **Test H, I**: Capability probe checks `MISSING_DOCUMENT` without altering idle queue (`PASS`).
  - **Test J, K, L, M**: Public state mapping correctly transitions between `READY`, `BUSY` (running/pending), and `DEGRADED` on invalid queue (`PASS`).
  - **Test N, O, P, Q, R, S**: Busy and invalid queues refuse stop; pre-existing backend refuses stop/restart; owned idle backend stops cleanly; workspace survives backend stop; restart reconnects cleanly (`PASS`).
  - **Test T, U, V, W**: Unexpected backend exit leaves workspace alive and reports `DEGRADED`; stopWorkspace does not stop backend; stopAll refuses to orphan owned busy backend (`PASS`).
  - **Test X, Y**: All fake test children cleaned at teardown; zero kill-by-port or taskkill utilities exist (`PASS`).
- **M1D1A Hotfix Matrix (Checks A through H)**:
  - **Check A**: Second queue unavailable after valid first read -> not compatible (`PASS`).
  - **Check B**: Second queue malformed after valid first read -> not compatible (`PASS`).
  - **Check C**: `stopBackend` with stale first-idle / failed second queue -> refused, child kill count = 0 (`PASS`).
  - **Check D**: Generic `{ input: {} }` object-info -> wrong profile (`PASS`).
  - **Check E**: Public `await runtime.restartBackend()` -> old child stopped, new child started, workspace survives, reaches `READY` (`PASS`).
  - **Check F**: Unexpected workspace exit -> backend untouched, status `DEGRADED`, `lastWorkspaceExit` recorded (`PASS`).
  - **Check G**: Unexpected backend exit -> `lastBackendExit` recorded (`PASS`).
  - **Check H**: Partial startup failure -> wrong external workspace not killed, owned backend safely stopped (`PASS`).
- **M1D1B Ownership Truth Matrix (Checks I through L)**:
  - **Check I**: Backend startup polling timeout -> retains `OWNED_BY_THIS_RUNTIME` while child process is alive, not killed automatically, resets to `UNAVAILABLE` on exit (`PASS`).
  - **Check J**: Spawned backend wrong profile -> retains `OWNED_BY_THIS_RUNTIME` while child process is alive, not killed automatically, resets to `UNAVAILABLE` on exit (`PASS`).
  - **Check K**: Workspace startup polling timeout -> retains `OWNED_BY_THIS_RUNTIME` while child process is alive, not killed automatically, reports truthful `DEGRADED` (pre-existing compatible backend) and `internalSubstate: FAILED` (`PASS`).
  - **Check L**: Spawned workspace wrong profile -> retains `OWNED_BY_THIS_RUNTIME` while child process is alive, reports truthful `FAILED` (`PASS`).
- **M1D1C Re-entry & Recovery Matrix (Checks A through H)**:
  - **Check A**: `start()` on already-owned READY runtime is idempotent -> zero additional children spawned, handles/PIDs/ownerships preserved (`PASS`).
  - **Check B**: `stopBackend() -> start()` -> workspace child/PID/ownership preserved, exactly one replacement backend spawned, both cleaned on `stopAll()` (`PASS`).
  - **Check C**: `stopWorkspace() -> start()` -> backend child/PID/ownership preserved, exactly one replacement workspace spawned, both cleaned on `stopAll()` (`PASS`).
  - **Check D**: Owned backend child alive + unavailable probe -> zero duplicate spawn, ownership retained, state not READY (`PASS`).
  - **Check E**: Owned workspace child alive + unavailable probe -> zero duplicate spawn, ownership retained, state not READY (`PASS`).
  - **Check F**: Owned live service returning wrong profile -> fails closed, zero duplicate spawn, ownership retained (`PASS`).
  - **Check G, H**: Genuine pre-existing compatible backend/workspace remain `PREEXISTING_COMPATIBLE` and are never killed (`PASS`).
- **M1D1D Ownership Truth & Partial-Start Matrix (Checks A through F)**:
  - **Check A**: `child.killed == true` without exit event retains owned process record & ownership; exit event cleans record (`PASS`).
  - **Check B, C**: Backend termination timeout retains ownership & record; subsequent `start()` spawns 0 duplicate backend (`PASS`).
  - **Check D, E**: Workspace termination timeout retains ownership & record; subsequent `start()` spawns 0 duplicate workspace (`PASS`).
  - **Check F**: Pre-owned backend + wrong external Workspace -> existing backend NOT killed, process handle/PID preserved (`PASS`).

Execution performance: **~400 ms** total wall time (well below the 2-minute target).

---

## 8. Existing Regression Verifications

All existing standalone Manga test suites executed and passed:
- `test_backend_adapter.mjs`: ALL PASS
- `test_document_roundtrip.mjs`: ALL PASS
- `test_authoring_ops.mjs`: ALL PASS
- `test_frame_ops.mjs`: ALL PASS
- `test_guide_ops.mjs`: ALL PASS
- `test_guide_asset_ops.mjs`: ALL PASS

---

## 9. Real-Runtime Limits & CODEX Delegation

The following remain deferred to CODEX for real GPU / Portable validation:
1. Real execution of `ComfyUIPortable/python_embeded/python.exe ComfyUI/main.py`.
2. Windows signal handling and clean termination under real GPU memory allocation.
3. Verification of whether `--windows-standalone-build` is necessary in the canonical production command.
4. Real browser connection and E2E visual redraw.
