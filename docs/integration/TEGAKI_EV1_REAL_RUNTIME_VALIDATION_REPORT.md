# TEGAKI-EV1 Real Runtime Validation Report

- Card: `TEGAKI-EV1`
- Channel: `RUNTIME_VALIDATION`
- Executor: `CODEX`
- Date: `2026-09-12`
- Result: `BLOCKED`
- Initial HEAD: `72c911370920716dd76946c6b695276365903488`
- Baseline: `HEAD == origin/main == 72c911370920716dd76946c6b695276365903488`
- Product source changes: `NONE`
- Push: `NOT PERFORMED`

This report keeps the two Card domains independent. No H3/Manga engine,
schema, workflow, or lifecycle integration was introduced.

## Preflight

- Worktree was clean before validation and remained free of product-source
  changes.
- All target ports were initially free: `8188`, `8190`, `8189`, `8191`.
- `git fetch origin` returned a local `.git/FETCH_HEAD` permission error, but
  the live `HEAD` and `origin/main` refs both resolved to the Card baseline
  above. No concurrent worktree change was observed.
- No unknown process was killed and no kill-by-port operation was used.

## A. Manga Runtime

### Default start and backend identity

The first call used product defaults with no runtime configuration override:

```text
backend:   http://127.0.0.1:8189
workspace: http://127.0.0.1:8191
startupWaitTimeoutMs: 5000
shutdownTimeoutMs: 3000
```

`runtime.start()` returned after approximately 5 seconds with:

```text
Timed out waiting for backend on http://127.0.0.1:8189 to report positive identity
```

Classification: `DEFAULT_STARTUP_TIMEOUT_LIMIT` / `TOO SHORT`.

The same owned backend later became compatible within the Card's bounded
observation window. A single bounded continuation was then used with
`startupWaitTimeoutMs=120000` on the validation harness instance only. The
product default was not changed.

The real backend command retained by the runtime was equivalent to:

```text
python_embeded/python.exe -s ComfyUI/main.py --listen 127.0.0.1 --port 8189
  --disable-auto-launch --output-directory output/Tegaki
```

`--windows-standalone-build` was not required and was not used.

The positive backend identity was verified by the exact Card probes:

- `GET /queue` returned HTTP 200 with `queue_running: []` and
  `queue_pending: []`.
- `GET /object_info/TegakiMinimumHandSceneEditor` returned HTTP 200 and the
  exact node key.
- `POST /tegaki/manga/generation/prepare` with `{}` returned HTTP 400 with
  `ok: false` and `error_code: MISSING_DOCUMENT`.
- The second `GET /queue` remained idle.

Workspace identity returned HTTP 200:

```json
{
  "service": "tegaki_manga_workspace",
  "version": "1.0.0",
  "domain": "manga",
  "authoring_schema": "1.0.0",
  "backend_target": "http://127.0.0.1:8189"
}
```

### Lifecycle evidence

The completed bounded lifecycle continuation used these Card-owned PIDs:

| Checkpoint | Backend | Workspace | Result |
| --- | ---: | ---: | --- |
| Base READY | `70536` | `48668` | PASS |
| `stopBackend()` | exited `70536` | `48668` unchanged and identity-readable | PASS; state `DEGRADED` |
| `start()` recovery | new `30332` | `48668` unchanged | PASS; state `READY` |
| `restartBackend()` | old `30332` exited, new `47616` | `48668` unchanged | PASS; state `READY` |
| `stopWorkspace()` | `47616` unchanged and Manga-compatible | exited `48668` | PASS; state `DEGRADED` |
| `start()` workspace recovery | `47616` unchanged | new `62840` | PASS; state `READY` |
| `stopAll()` | exited | exited | PASS |

Windows termination used the exact retained ChildProcess handles and bounded
`SIGTERM`/exit-event waits. The lifecycle exits were observed as intentional
SIGTERM exits. After `stopAll()`, both `8189` and `8191` refused connections
and the runtime held no Card-owned child record.

Manga real generations: `0`.

### Manga classification

| Item | Classification |
| --- | --- |
| Canonical candidate backend command | REAL VERIFIED |
| Default startup timeout | TOO SHORT / PASS WITH LIMIT |
| Windows termination | PASS |
| Backend restart | PASS |
| Independent workspace lifetime | PASS |
| No-orphan result | PASS; Card-owned children `0` |
| Manga closeout | Not closed by this Card because the default timeout is a documented limit and Owner/SOL closeout remains separate |

## B. H3 Runtime

### Startup and Browser checkpoint

H3 Native and Skin were started sequentially after Manga cleanup, using the
effective arguments from `h3/run_h3.bat` and retaining direct launcher child
handles.

Initial launch records:

- Native ChildProcess: PID `71464`, port `8188`.
- Skin ChildProcess: PID `65472`, port `8190`, backend target
  `http://127.0.0.1:8188`.

Native `/system_stats` responded with the expected local portable ComfyUI
profile, CUDA device, and the recorded H3 argument set including
`--disable-all-custom-nodes`, explicit H3 model-path config, H3 input/output,
user/temp directories, in-memory SQLite, and port `8188`.

Skin `/api/status` returned:

```text
state: READY
backend_profile: CANONICAL_H3
queue_running_count: 0
queue_pending_count: 0
safe_to_stop_native: true
```

The in-app Browser showed `TEGAKI / Video`, `Ready`, `Prompt is ready`,
Standard selected, and `Native jobs HISTORY: 0`. The Browser remained on the
empty READY/Create screen after the blocked submit. No browser-side sampling
percent was available because no job reached queue submission.

### Standard Start attempt

The existing local PNG fixture `1a7ba684c37148c58b87cf70c8e433bf.png` was
verified as `344 x 135`, deliberately non-16:9. It was accepted by the Skin
reference upload boundary with HTTP 201 and a server-issued start-frame asset.

The one planned Standard Start submit was rejected by Native before `/prompt`
queue submission. Skin returned HTTP 503 with the underlying Native validation
error:

```text
prompt_outputs_failed_validation
unet_name: minimax_h3_fl2va_pruned_int8_convrot.safetensors not in []
vae_name: minimax_h3_video_vae_fp16.safetensors not in ['taesd3', 'taesd', 'taesdxl', 'taef1', 'pixel_space']
kind: backend_unavailable
```

The configured `h3/config/extra_model_paths.yaml` points at `../model_store/`,
but that store was absent in the workspace. The five required H3 weight files
were not present in the workspace:

- `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
- `minimax_h3_ref2va_pruned_int8_convrot.safetensors`
- `minimax_h3_video_vae_fp16.safetensors`
- `minimax_h3_audio_vae_fp32.safetensors`
- `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`

Therefore there was no real `/prompt`, materialized submitted workflow,
terminal MP4, or real sampler event for this checkpoint.

### Ref2VA and Still Source

Ref2VA and Still Source were not submitted after the deterministic missing
model-path blocker was established. This avoids exploratory or redundant
generations and keeps the real H3 generation count at `0 / 3`.

A local synthetic motion fixture was created with installed `ffmpeg` and
verified as `7.000000` seconds at `608 x 352`; it was not submitted because
the Native model validation blocker occurred before the Ref2VA route could be
meaningfully tested.

### H3 cleanup

The first plain-pipe launcher session did not expose stdin for its explicit
`stop` command. A second TTY-only cleanup observation was used without any
generation: Skin exited through its exact handle with `SIGTERM`, while the
second Native launcher child exited with code `1` because port `8188` was
briefly still occupied by the prior Card-owned Native runtime. A final
read-only process/port check found no H3 launcher process and no listener on
`8188` or `8190`.

Classification: `PASS WITH LIMIT` for postcondition cleanup; direct exit-event
capture for the first Native ChildProcess was not available after the plain
pipe session closed. No unknown process, global Python stop, or kill-by-port was
used.

### H3 classification

| Item | Classification |
| --- | --- |
| H3 Native startup/profile | PASS |
| H3 Skin startup/profile | PASS |
| Standard Start real generation | BLOCKED; Native model validation before `/prompt` |
| Real sampler progress | INCONCLUSIVE; no prompt entered queue |
| Browser Sampling percent | LIMIT; Browser remained READY because no job was accepted |
| Standard Start aspect path | NOT VERIFIED REAL WORKFLOW + GENERATION |
| Ref2VA nonzero Start | BLOCKED before submission |
| Ref2VA 5-second slice | BLOCKED before submission |
| Still Source generation | BLOCKED before submission |
| Still Source aspect path | NOT VERIFIED REAL WORKFLOW + GENERATION |
| H3 real generations | `0 / 3` |
| H3 orphan children | `0` by final process/port postcondition, with Native exit-event capture limit noted above |

## Final handoff

```text
TEGAKI_REPORT_V1
CARD_ID: TEGAKI-EV1
RESULT: BLOCKED
EXECUTOR: CODEX

Initial HEAD:
72c911370920716dd76946c6b695276365903488

=== MANGA ===

Default Manga start: TIMEOUT LIMIT
Real Manga backend profile: PASS
Workspace identity: PASS
Backend stop: PASS
Workspace survives backend stop: PASS
Backend recovery: PASS
Public restartBackend: PASS
Workspace stop: PASS
Backend survives Workspace stop: PASS
Workspace recovery: PASS
stopAll: PASS
Manga orphan children: 0
Manga generations: 0

=== H3 ===

H3 Native: PASS
H3 Skin: PASS
Standard Start real generation: BLOCKED
Real sampler progress: INCONCLUSIVE
Browser Sampling percent: LIMIT
Standard Start aspect path: OTHER
Ref2VA nonzero Start: BLOCKED
Ref2VA 5-sec slice: BLOCKED
Still Source generation: BLOCKED
Still Source aspect path: OTHER
H3 real generations: 0
H3 orphan children: 0 / cleanup evidence limit noted

Product source changes: NONE
Real-runtime defects: H3 required model store/weights unavailable; default Manga startup wait is too short for real Portable startup
Docs-only local commit: PENDING
Remote publication: NOT PERFORMED

PUSH NOT PERFORMED — OWNER ACTION REQUIRED

Recommended next:
SOL AUDIT -> provide/install the declared H3 model store, then rerun a new
bounded validation Card for H3 generation evidence; separately review the
Manga default startup timeout in its own authorized Card.
```
