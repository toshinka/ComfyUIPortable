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

Execution performance: **250 ms** total wall time (well below the 2-minute target).

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
