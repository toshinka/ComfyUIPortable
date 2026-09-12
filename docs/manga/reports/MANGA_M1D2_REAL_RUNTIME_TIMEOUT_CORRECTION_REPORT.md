# MANGA-M1D2 Real Runtime Timeout Correction Report

CARD_ID: MANGA-M1D2
BASE_SHA: ffdcac9ee421d5559a273d39adbcb9a8a53719e4
STATUS: COMPLETED (SOURCE CORRECTION & FAKE LIFECYCLE REGRESSION VERIFICATION)
EXECUTOR: GEMINI

---

## 1. Context & Purpose

This report documents the application of the single empirical finding established by real Portable runtime validation run **TEGAKI-EV1**:

- In TEGAKI-EV1 real Portable lifecycle testing, the initial production default wait timeout of startupWaitTimeoutMs = 5000 (5 seconds) was insufficient for the real Portable Manga backend process to initialize, import Python dependencies, start the HTTP server, and register custom nodes.
- When the 5000ms timeout elapsed, the controller truthfully classified the startup as timed out; subsequently, the same child process became Manga-compatible.
- TEGAKI-EV1 verified that an override of startupWaitTimeoutMs = 120000 (120 seconds) was fully sufficient for the real Portable backend to achieve positive Manga-compatible identity and reach READY. All subsequent real lifecycle operations (positive probe, status verification, safe stop, process termination) passed cleanly.

In MANGA-M1D2, this empirical finding is promoted into the production codebase as the default configuration value.

---

## 2. Product Changes

### 2.1 Default Timeout Correction
In ComfyUIPortable/manga/service/manga_domain_runtime.mjs:
- Changed constructor parameter default:
  startupWaitTimeoutMs = config.startupWaitTimeoutMs || 120000; (previously 5000).
- Explicit configuration override behavior is fully preserved: callers passing { startupWaitTimeoutMs: customMs } retain their custom timeout.

### 2.2 Unchanged Lifecycle Contracts
Zero changes were made to:
- probeTimeoutMs (retained at 800ms)
- shutdownTimeoutMs (retained at 3000ms)
- Default port assignments (8189, 8191)
- Positive service identity probe logic
- Process ownership invariants and exit-event bookkeeping
- Safe-stop rules, busy-queue refusal, and fail-closed error handling
- Process termination logic (zero kill-by-port, zero force kill)

---

## 3. Rationale for 120000ms Bounded Timeout

- **Empirically Proven**: 120000ms was established by TEGAKI-EV1 as an effective upper bound under real Portable execution.
- **Maximum Bound, Not Mandatory Duration**: 120000ms is the maximum polling window. The runtime polls every 100ms and returns immediately as soon as positive identity is confirmed.
- **Pending Revalidation**: Real Portable runtime revalidation is still required after this change to confirm the default-start path without override.

---

## 4. Verification Evidence

### 4.1 Unit & Contract Tests
Added Check A to ComfyUIPortable/manga/tests/test_domain_lifecycle.mjs:
- Verified 
ew MangaDomainRuntime().startupWaitTimeoutMs === 120000.
- Verified 
ew MangaDomainRuntime({ startupWaitTimeoutMs: 45000 }).startupWaitTimeoutMs === 45000.

### 4.2 Lifecycle Suite & Regression Matrix
Executed deterministic test suite:
- All base checks A through Y: PASS
- All M1D1A hotfix checks A through H: PASS
- All M1D1B spawn-ownership checks I through L: PASS
- All M1D1C re-entry recovery checks A through H: PASS
- All M1D1D partial-start and exit-truth checks A through F: PASS
- All M1D1E termination retry & delayed-exit checks A through J: PASS
- M1D2 Check A: PASS
- Execution time: ~450ms total wall time.

### 4.3 Existing Manga Regressions
Executed all standalone domain test suites:
- 	est_backend_adapter.mjs: ALL PASS
- 	est_document_roundtrip.mjs: ALL PASS
- 	est_authoring_ops.mjs: ALL PASS
- 	est_frame_ops.mjs: ALL PASS
- 	est_guide_ops.mjs: ALL PASS
- 	est_guide_asset_ops.mjs: ALL PASS

### 4.4 Operational Limits
- Real ComfyUI processes started: **0**
- Real image generations executed: **0**
- GPU / model loading performed: **0**
- H3 modifications: **NONE**
- Legacy modifications: **NONE**
