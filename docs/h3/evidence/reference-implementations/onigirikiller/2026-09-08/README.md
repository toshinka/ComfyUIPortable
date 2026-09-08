# onigirikiller/minimax-h3-webui — 2026-09-08

Status: `BLOCKED` before UI startup.

## Candidate

- Candidate: onigirikiller H3 Studio
- Source: https://github.com/onigirikiller/minimax-h3-webui
- Pinned commit: `f9b28d56d69192e4516907a61103a71ff2c29c27`
- Upstream status: local shallow clone matches the checked `main` head at the pinned SHA.
- Code license: Apache-2.0, local `LICENSE` and `NOTICE`
- Model provenance/license: the repository explicitly separates its code license
  from the MiniMax H3 Community License Agreement and third-party ComfyUI, Gradio,
  and FFmpeg terms.

## Local conditions

- Portable Python 3.13.14
- ComfyUI 0.30.0 available at `127.0.0.1:8188`
- GPU: NVIDIA GeForce RTX 4070 / 12282 MiB
- RAM: 63.77 GiB
- Embedded modules: `aiohttp`, Pillow, PyAV, requests present; `gradio` missing.
- Required custom nodes: official MiniMax H3 nodes in `ComfyUI/custom_nodes/`; the
  candidate also expects its documented ComfyUI/video workflow nodes.
- Python dependencies: `gradio>=4.39` plus the separate ComfyUI environment.
- Expected output path for this evaluation: `ComfyUIPortable/output/h3/video/`.
- Compatibility note: current ComfyUI 0.30.0 is available, but this UI cannot import
  until Gradio is installed and generation still needs H3 assets.

## Installation / startup

The source declares `gradio>=4.39`. An actual launch attempt using the Portable
Python (`python app.py --help`) stopped before argument handling with:

```text
ModuleNotFoundError: No module named 'gradio'
```

No dependency was installed. No UI screenshot is recorded because no candidate UI
started. Upstream screenshots are deliberately not substituted.

## Models and common test

The README expects an H3 diffusion model, video/audio VAE, Qwen3-VL text encoder,
and optional Turbo/Ref2VA assets. The local targeted model scan found none.

- Workflow: not started.
- Prompt/reference/resolution/duration/steps: `NOT TESTED`.
- Queue/progress/history/continuation/error UI: `NOT TESTED` at runtime.
- Generation status: `BLOCKED` — missing Gradio and model assets.
- Output SHA-256: none.
- 12GB observation: no H3 load, no peak VRAM, no OOM result.

## Behavior record

- Startup: `BLOCKED` at the missing Gradio import.
- First flow: `NOT TESTED`.
- Reference / Advanced: `NOT TESTED`.
- Queue / Progress / History: source claims are recorded as `NOT TESTED` locally.
- Continuation: `NOT TESTED`.
- Error / Disconnect: only the import blocker was observed; UI behavior `NOT TESTED`.
- Good for H1: small queue-oriented flow and explicit continuation/history are useful source observations.
- Bad for H1: no local UI or model-backed result.
- Interesting: code license and model license/provenance are explicitly separated in `NOTICE`.
- Not relevant to H1 at this gate: full Studio expansion, Storyboard, Timeline, Cast, 3D, Manga.

## Local modifications / limitations

No candidate source or shared runtime file was patched. The blocker is finite and
documented; no infinite dependency repair was attempted.
