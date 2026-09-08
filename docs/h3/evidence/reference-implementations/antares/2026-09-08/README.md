# AntaresAlice/h3-webui — 2026-09-08

Status: `VERIFIED LOCAL` for WebUI startup and status API; `BLOCKED` for generation
because the H3 model assets are missing.

## Candidate

- Candidate: AntaresAlice H3 WebUI
- Source: https://github.com/AntaresAlice/h3-webui
- Pinned commit: `4f10667c604f9cb333ac119b457a3659260a8966`
- Upstream status: local shallow clone matches the checked `main` head at the pinned SHA.
- Code license: MIT, local `LICENSE`
- Model provenance/license: the repository README separates its code license from
  MiniMax H3, ComfyUI, and other third-party terms.

## Local conditions

- Portable Python 3.13.14
- ComfyUI 0.30.0 at `http://127.0.0.1:8188`
- WebUI at `http://127.0.0.1:8081`
- GPU: NVIDIA GeForce RTX 4070 / 12282 MiB
- RAM: 63.77 GiB
- Source imports `aiohttp`, Pillow, and PyAV; local versions were present.
- Required custom nodes: MiniMax H3 nodes and the ComfyUI node chain referenced by
  the WebUI workflow (including its video save/decode helpers).
- Python dependencies: `aiohttp`, Pillow, and PyAV from the Portable ComfyUI runtime;
  no separate candidate requirements file is present.
- Expected output path: `ComfyUIPortable/output/h3/video/` (configured for this pass).
- Compatibility note: the WebUI connected to ComfyUI 0.30.0 and returned status;
  `ref2va_present:false` and missing weights block generation.
- `COMFYUI_INPUT` was set to `output/h3/tests`.
- `COMFYUI_OUTPUT` was set to `output/h3/video`.

## Startup and actual local surface

The server started without patching source. HTTP `/` and
`/api/comfyui/status` both returned 200. The live browser surface showed:

- H3 Studio / Chat / Overview / Studio navigation
- i2v single-image and r2v multi-asset task modes
- reference input, prompt, model, resolution, native scale, steps, duration, seed
- low-VRAM / SageAttention / Turbo labels
- History and a disabled Generate action until a reference is provided

The status response reported `ref2va_present:false`. The workspace history was empty.
The actual local start surface is captured in [01_start.png](screenshots/01_start.png);
the contact sheet contains only available local capture(s), not upstream images.

## Common test / generation

- Prompt: `NOT TESTED`.
- Reference: input surface observed; actual reference upload/reuse `NOT TESTED`.
- Resolution/duration/steps: UI presets observed; generation `NOT TESTED`.
- Queue/progress/history/continuation: source/UI boundary observed; successful
  generation path `NOT TESTED`.
- Generation status: `BLOCKED` — required H3 assets absent.
- Output SHA-256: none.
- 12GB observation: startup only; no peak VRAM, OOM, or recovery result.

## Behavior record

- Startup: `VERIFIED LOCAL` at `127.0.0.1:8081`.
- First flow: `BLOCKED` before generation because H3 assets are absent and no reference was uploaded.
- Reference: input surface observed; upload, order, and reuse `NOT TESTED`.
- Advanced: model, resolution, native scale, steps, duration, seed, and acceleration labels were visible; deeper behavior `NOT TESTED`.
- Queue / Progress: source/UI boundary observed; running-job behavior `NOT TESTED`.
- History: empty history state observed; reuse behavior `NOT TESTED`.
- Continuation: `NOT TESTED`.
- Error / Disconnect: `NOT TESTED`; no generation job was submitted.
- Good for H1: Video-first minimum surface, familiar terms, visible status boundary, and disabled Generate state.
- Bad for H1: model availability is not yet coupled to a successful local generation.
- Interesting: the visible UI separates Chat / Overview / Studio while the initial surface stays focused on one task.
- Not relevant to H1 at this gate: full Studio, Storyboard, Timeline, Cast, multi-track, 3D, Manga.

## Local modifications / limitations

No source files were changed. Only environment paths and port were supplied. No
generated video was written to `output/h3/video/`.
