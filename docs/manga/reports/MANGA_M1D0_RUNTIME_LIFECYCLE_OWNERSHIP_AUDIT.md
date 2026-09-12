# MANGA-M1D0 Runtime Lifecycle Ownership Source Audit & Design Freeze

CARD_ID: MANGA-M1D0
BASE_SHA: c9072e3707d1de1f6c7ffea90947c05f467d90d4
STATUS: COMPLETED (SOURCE & DESIGN AUDIT ONLY)
EXECUTOR: GEMINI

---

## 1. Executive Summary

MANGA-M1D0 establishes the definitive runtime lifecycle ownership architecture for the Manga standalone editor. Following the completion of the Manga standalone authoring-parity track (MANGA-M1A through M1C2B1), this audit resolves how the Manga standalone Workspace server and its backing ComfyUI backend process are initiated, owned, monitored, verified, and safely terminated.

Strict constraints enforced during this audit:
- 0 real processes started (no Manga backend, no Manga Workspace, no H3, no ComfyUI, no browser).
- 0 real image generations executed.
- Authoring document schemas, node implementations, and UI editor components remained untouched and frozen.
- Design freeze is strictly documented for implementation in MANGA-M1D1 and future validation by CODEX.

---

## 2. Startup Source Facts & Canonical Command

### 2.1 Audited Windows Startup Scripts
1. `ComfyUIPortable/run_nvidia_gpu.bat`:
   ```bat
   .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build
   ```
2. `ComfyUIPortable/run_cpu.bat`:
   ```bat
   .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --cpu
   ```
3. Python Environment:
   - Root: `ComfyUIPortable/python_embeded/python.exe`
   - Python Version: 3.13.14 (packaged in portable environment)
   - Flags: `-s` (disables user site-packages for isolation)

### 2.2 Custom Node Discovery Mechanics
- `ComfyUI/custom_nodes/tegaki_manga_nodes` is an NTFS junction pointing directly to `custom_nodes_custom/tegaki_manga_nodes`.
- Custom node discovery occurs in `ComfyUI/nodes.py` via `init_custom_nodes()`. Any directory or junction located inside `ComfyUI/custom_nodes/` is imported automatically unless `--disable-all-custom-nodes` is supplied.
- Unlike H3 (which runs isolated on 8188 with `--disable-all-custom-nodes`), Manga requires custom nodes to load its 24 domain nodes and REST endpoints.

### 2.3 Command-Line Argument Space
Audited from `ComfyUI/comfy/cli_args.py`:
- `--listen [IP]`: Defaults to `127.0.0.1`.
- `--port [PORT]`: Defaults to `8188`.
- `--disable-auto-launch`: Disables opening default system browser upon server start.
- `--output-directory [DIR]`: Sets root output location. For Manga, `output/Tegaki` ensures output separation.
- `--disable-all-custom-nodes`: MUST NOT be passed for Manga backend.

### 2.4 Canonical Backend Launch Command (Source-Derived Candidate)
The proposed canonical launch command for the dedicated Manga ComfyUI backend is a **source-derived candidate** until CODEX real runtime verification:
```powershell
.\python_embeded\python.exe -s ComfyUI\main.py --listen 127.0.0.1 --port 8189 --disable-auto-launch --output-directory output/Tegaki
```
(Note: Whether `--windows-standalone-build` is required for the final canonical profile remains a CODEX validation item).

---

## 3. Hosting Direction & Port Assignment

### 3.1 Decision: MANGA_DOMAIN_RUNTIME_RECOMMENDED
Option A (`MANGA_DOMAIN_RUNTIME_RECOMMENDED`) is selected:
- The Manga domain owns its own dedicated runtime controller and lifecycle supervisor (`manga_domain_runtime.mjs`).
- Port 8191 is the current configurable default for the standalone Manga Workspace server (`manga_workspace_server.mjs`).
- Port 8189 is the current configurable default for the dedicated Manga ComfyUI backend.
- Port 8188 is explicitly reserved as the default for H3 / Native Isolated workflows and is strictly avoided for Manga.
- Ports 8188, 8189, and 8191 are current configurable defaults, not eternal reservations.
- A single unmanaged ComfyUI instance on port 8188 shared across H3 and Manga is REJECTED due to incompatible custom node requirements (H3 requires `--disable-all-custom-nodes`; Manga requires custom nodes enabled).

---

## 4. Positive Profile Identity & Fingerprinting

To avoid blind port assumptions and ensure robust multi-process safety, both the Manga ComfyUI backend and Manga Workspace server require positive deterministic service/profile identity probes (no cryptographic authentication exists).

### 4.1 Manga Backend Positive Identity Probe
A candidate HTTP endpoint on port 8189 is positively identified as a compatible Manga backend if and only if ALL of the following conditions hold:
1. `GET /queue`: Returns HTTP 200 with JSON payload containing array fields `queue_running` and `queue_pending`.
2. `GET /object_info/TegakiMinimumHandSceneEditor`: Returns HTTP 200 with JSON object defining the node input/output specification (verifying custom nodes are loaded).
3. Non-mutating Capability Probe: `POST /tegaki/manga/generation/prepare` with body `{}`.
   - Audited implementation in `custom_nodes_custom/tegaki_manga_nodes/product_generation_api.py`:
     ```python
     data = await request.json()
     raw_doc = body.get("document_json")
     if raw_doc is None:
         return web.json_response(
             {"ok": False, "error": "Missing required field: 'document_json'", "error_code": "MISSING_DOCUMENT"},
             status=400,
         )
     ```
   - When given `{}`, it returns HTTP 400 with JSON containing `ok == false` and `error_code == "MISSING_DOCUMENT"`.
   - This proves the endpoint is live, routed, and functional without side effects (no queueing, no file system writes).

### 4.2 Manga Workspace Server Identity Probe
A candidate HTTP endpoint on port 8191 is positively identified as the Manga Workspace server if:
- `GET /api/runtime/identity`: (Proposed in M1D0; implemented by M1D1) Returns HTTP 200 with JSON:
  ```json
  {
    "service": "tegaki_manga_workspace",
    "version": "1.0.0",
    "domain": "manga",
    "authoring_schema": "1.0.0",
    "backend_target": "http://127.0.0.1:8189"
  }
  ```

---

## 5. Ownership Contract & Lifecycle State Machine

### 5.1 Ownership Classification
Every probed service instance is classified into exactly one of four ownership tiers based on process ownership evidence (child process handle spawned by this runtime):
1. `OWNED_BY_THIS_RUNTIME`: The process was spawned directly by the running controller instance (child process handle held, PID match, spawn timestamp recorded).
2. `PREEXISTING_COMPATIBLE`: A process is already listening on the designated port and successfully passes positive deterministic profile identity checks, but was NOT spawned by this controller instance.
3. `PORT_OCCUPIED_WRONG_PROFILE`: A process is listening on the port, but fails positive deterministic profile identity checks (e.g. general ComfyUI without manga nodes, H3 instance, rogue server).
4. `UNAVAILABLE`: Port is closed, no listener.

### 5.2 Externally Visible Lifecycle States
The externally visible public lifecycle states are:
- `STOPPED`
- `STARTING`
- `READY`
- `BUSY`
- `DEGRADED`
- `STOPPING`
- `FAILED`

Internal substates such as `STARTING_BACKEND`, `STARTING_WORKSPACE`, or `BACKEND_READY` may exist internally only, but `getStatus()` maps truthfully to the public enum.

---

## 6. Anti-Kill-by-Port & Safe Stop Rules

### 6.1 Anti-Kill-by-Port Rule
Killing an operating system process based solely on port discovery (`netstat`, `Get-NetTCPConnection`) without process ownership evidence is STRICTLY REJECTED.
- The controller will NEVER execute `taskkill /PID` or `process.kill()` against a process it did not spawn.
- If port 8189 or 8191 is occupied by an external PID, the controller MUST NOT kill it. If it is `PORT_OCCUPIED_WRONG_PROFILE`, the controller aborts with a diagnostic error instructing the user to reconfigure or stop the conflicting application.

### 6.2 Safe Stop Rules (Fail-Closed)
A running backend may only be terminated when:
1. Ownership is verified as `OWNED_BY_THIS_RUNTIME`.
2. Positive backend identity passes.
3. Queue check `GET /queue` confirms `queue_running` is empty (`[]`) and `queue_pending` is empty (`[]`).

**Strict Fail-Closed Policy**:
- There is NO force stop, force flag, or operator force kill exception.
- If the queue is busy, unavailable, or invalid, backend stop/restart is strictly REFUSED.
- Preexisting backends and wrong-profile processes are strictly REFUSED for stop/restart.

---

## 7. Decoupled Lifetimes & In-Memory State Contract

### 7.1 Separation of Browser Authoring and Backend Execution
- The authoring document (`TEGAKI_AUTHORING_DOCUMENT 1.0.0`) lives in the browser DOM / store memory.
- Browser-held authoring state is independent from backend lifetime.
- Unsaved state survives backend restart while the current browser page/store remains alive.
- Unsaved state across refresh/tab destruction is NOT guaranteed; permanent durability requires explicit local file export or document save.

---

## 8. Technology Recommendation & M1D1 Implementation Plan

### 8.1 Technology: Pure Node.js Lifecycle Controller
The runtime controller will be implemented in `manga_domain_runtime.mjs` using pure Node.js built-ins (`node:child_process`, `node:http`, `node:fs`, `node:path`), maintaining zero new npm dependencies.

### 8.2 Testing Strategy for MANGA-M1D1
To guarantee high test coverage without spawning real GPU processes:
- Create a deterministic fake ComfyUI backend mock in Node.js that simulates `/queue`, `/object_info`, and `/tegaki/manga/generation/prepare`.
- Test all transition paths: clean startup, port conflict handling, preexisting compatible adoption, safe stop rejection when busy, and graceful shutdown.
- Real end-to-end integration and GPU validation will be handed over to CODEX.

---

## 9. Final Decision & Sign-off

- Architecture & Design: FROZEN.
- Real processes spawned: 0.
- Source files modified: 0 (docs and reports only).
- Next Card: MANGA-M1D1 (Lifecycle Implementation & Fake Process Harness).
