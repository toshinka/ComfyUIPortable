# H1A Minimum Video Skin — Native T2V Vertical Slice Report

更新: 2026-09-08 JST
Stage: `H1A`
Status: `IMPLEMENTED` / `VERIFIED LOCAL GENERATION` / `VERIFIED BROWSER UI GENERATION`
Owner acceptance: `PENDING`

## 1. Outcome

H1A is implemented as a small TEGAKI-facing local video skin over the Native
ComfyUI H3 backend. A user can enter a prompt, confirm the fixed
`608 x 352` / `5 seconds` contract, press `Generate`, observe `Queued` or
`Running`, watch the completed Preview, and select recent results from the
session History.

The browser path was exercised end to end on an NVIDIA RTX 4070 12GB-class
host. The UI submission reached `Running`, then `Completed`, and produced a
real H.264/AAC MP4 through the Native H3 workflow. This is a technical result,
not a claim of visual production quality or Owner acceptance.

## 2. Implementation boundary

| Area | H1A implementation |
|---|---|
| UI | `h3/app/static/index.html`, `styles.css`, `app.js`; vanilla HTML/CSS/JS |
| Local server | `h3/app/server.py`; stdlib HTTP server, no project DB |
| Semantic adapter | `h3/adapters/native_t2v.py`; request validation, H3 frame grid, workflow compilation |
| Production workflow | `workflows/h3/H1A_NATIVE_T2V_BASE.json`; materialized API prompt graph |
| Launcher | `h3/run_h1a.bat`; Native backend on 8188, skin on 8190 |
| Model boundary | isolated `h3/model_store/`; no shared `ComfyUI/models/` dependency |
| Output boundary | ignored `output/h3/video/`; generated MP4 is not committed |
| Evidence | `docs/h3/evidence/h1a/2026-09-08/` |

The adapter is the only place where UI input becomes workflow input. It patches
prompt, width, height, frame length, seed, steps, and output prefix; it does not
let arbitrary browser fields reach model, VAE, sampler, scheduler, or Turbo
nodes. `validate_workflow()` fails closed if the expected Native H3 semantic
roles disappear or change class.

## 3. User contract and state model

Always-visible controls are Prompt, Resolution, Duration, Generate, Preview,
Native backend status, generation status, queue count, and History. Resolution
and duration are intentionally narrow H1A options. Seed and Steps sit behind
Advanced; Steps is fixed at the verified value `20`. Sampler, scheduler, model,
VAE/offload, Reference/I2V, Project/Shot/Take, Studio/Timeline/Storyboard,
Cast/3D/Manga, and Runtime Profiles are not exposed.

The state vocabulary is explicit text: `READY`, `QUEUED`, `RUNNING`,
`COMPLETED`, `FAILED`, `CANCELLED`, and `DISCONNECTED`. Native queue/history
payloads are normalized by tested mapping functions. Progress is `null` rather
than an invented percentage because this boundary does not have a reliable
step-progress source. Failed/cancelled jobs retain the request inputs.

Session History is only an in-memory mapping to Native ComfyUI prompt/history
and output records. It is not a project database and does not replace the
backend's queue/history authority. On a fresh UI load, the newest session
result is restored into Preview when available; the MP4 remains a backend output.

## 4. Native recipe held constant

- Official Native ComfyUI H3 nodes; all custom nodes disabled.
- Official first-wave H3 model assets in the isolated model store.
- 608 x 352, 124 frames at 24 FPS, 5 seconds in the H1A control.
- 20 steps, `res_multistep`, `simple`, Turbo LoRA disabled.
- DynamicVRAM and asynchronous offload remained Native runtime behavior.

The production graph records the official workflow provenance and materializes
the H0.1 verified Native T2V subgraph. The H0.1 evaluation workflow is not
submitted directly by the H1A server.

## 5. Runtime evidence

The browser-run result is documented in
[H1A evidence](../evidence/h1a/2026-09-08/README.md) and the machine-readable
[manifest](../evidence/h1a/2026-09-08/manifest.json).

| Route | Result | Elapsed | Output SHA-256 |
|---|---|---:|---|
| H1A API smoke | `COMPLETED` | 171.8 s | `0C20302A70C1F48685360A2751AC30BBC1135DD8AF8EEFE68259E5675B6C6ABE` |
| H1A browser UI | `COMPLETED` | 114.0 s | `14CAA00BAAA16F78CEBEF01F49092110C0FC78045F8F85B50E4D2B1CB7937A85` |

For the browser result, `ffprobe` confirmed H.264 video plus AAC audio,
608x352, 24 FPS, 124 frames, and 5.167 seconds of media duration. The
preceding API run sampled minimum Native `vram_free=456707660` bytes,
approximately 11,846 MiB used of 12,282 MiB, with no OOM or quality fallback.
The browser run was not under a separate external VRAM sampler; this
distinction is preserved rather than inferred away.

The committed visual evidence is a completion screenshot plus first/middle/last
frames and a contact sheet. Generated MP4s and model weights remain ignored.

## 6. Verification

| Check | Result |
|---|---|
| H1A adapter/server unit tests | `9 passed` |
| Python syntax compile | passed for adapter, server, and tests |
| Request validation | empty prompt rejected with HTTP 400; valid request accepted |
| Workflow compile | semantic prompt/size/length/seed/steps/output patches verified |
| Stale workflow guard | incompatible semantic role rejected fail closed |
| Native backend status | `READY`, queue count, running count, VRAM parsed |
| Direct H1A API | `QUEUED` → `RUNNING` → `COMPLETED` with real MP4 |
| Browser UI | Generate → Running/Cancel → Completed Preview → History verified by AX and screenshot |
| Media probe | 608x352 / 24 FPS / 124 frames / H.264 + AAC verified |

## 7. Deferred and explicit non-scope

H1B, I2V, REF2VA, Still, multi-shot, Studio, Timeline, Storyboard, Cast, 3D,
Manga, Runtime Profiles, custom-node vendoring, ComfyUI core/frontend changes,
quality auto-fallback, persistent project storage, and public deployment are
not part of H1A. The shared Illustrious Manga implementation and its canonical
documents/workflows were not modified.

The H3 model package remains subject to the existing MiniMax H3 license and
Owner/legal review. Candidate repositories remain references only; no external
candidate source was vendored.

## 8. Review gate

H1A is ready for Web GPT / Astra H1A review as a local technical slice. It is
not marked Owner `ACCEPTED`, and no push was performed. The next decision is
review of this evidence and the narrow H1A contract; H1B must not be inferred
from this implementation.

## 9. Provenance links

- [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)
- [Official MiniMax H3 T2V workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_t2v.json)
- [Comfy-Org MiniMax H3 model package](https://huggingface.co/Comfy-Org/MiniMax-H3)
- [MiniMax H3 license](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE)
