# Native / Official H3 baseline — 2026-09-08

Status: `VERIFIED LOCAL` for startup and native H3 node registration; `BLOCKED` for
generation because the local H3 model assets are missing.

## Candidate

- Candidate: Native / official ComfyUI H3
- Source: https://github.com/Comfy-Org/ComfyUI
- Checked local commit: `b1693ecba9f5b65f8c80ab36b195ab963ec92413`
- Upstream master checked separately: `efa6c8f804bff78b46a0fd458ebd2e47bba07a30`
- Code license: GPL-3.0, local `ComfyUI/LICENSE`
- Model provenance/license: MiniMax H3 official distribution and Community License
  Agreement; see https://github.com/MiniMax-AI/MiniMax-H3 and the current model terms.

## Local conditions

- Portable Python 3.13.14
- ComfyUI 0.30.0
- NVIDIA GeForce RTX 4070 / 12282 MiB
- 63.77 GiB system RAM reported by `/system_stats`
- Launch: `main.py --listen 127.0.0.1 --port 8188 --cpu --disable-auto-launch`
- HTTP `/system_stats`: 200
- HTTP `/object_info`: 200
- Required custom nodes: native MiniMax H3 nodes are present in ComfyUI; no
  third-party H3 candidate node was installed.
- Python dependencies: existing Portable ComfyUI environment; Python 3.13.14,
  PyTorch 2.13.0+cu130, aiohttp, Pillow, PyAV.
- Expected output path for this evaluation: `ComfyUIPortable/output/h3/video/`.
- Compatibility note: ComfyUI 0.30.0 registered native H3 nodes, but generation
  remains blocked until the expected model assets are supplied.

## Native capability result

The live native registry exposed:

- `EmptyMiniMaxH3LatentAV`
- `MiniMaxH3ImageToVideo`
- `MiniMaxH3ReferenceToVideo`
- `MiniMaxH3SigmaShift`

This verifies the backend/node surface only. It does not verify generation quality.

## Models

A targeted filename scan under `ComfyUIPortable/ComfyUI/models/` found no H3 assets.
Expected assets include the FL2VA/Ref2VA diffusion checkpoint, Qwen3-VL H3 text
encoder, video VAE, and audio VAE. The model files were not downloaded.

## Workflow and common test

- Workflow: native H3 node/API capability inspection only.
- Prompt/reference/resolution/duration/steps: `NOT TESTED`.
- Generation status: `BLOCKED` — no H3 weights.
- Output SHA-256: none.
- 12GB observation: startup was forced to CPU; no peak GPU VRAM, OOM, or recovery
  result exists.

## Behavior record

- Startup: `VERIFIED LOCAL`.
- First flow: `BLOCKED` by missing H3 assets.
- Reference / Advanced: native node/API surface only; `NOT TESTED` as a user flow.
- Queue / Progress / History: `NOT TESTED`.
- Continuation: `NOT TESTED`.
- Error / Disconnect: no H3 job was submitted; `NOT TESTED`.
- Good for H1: official capability and node boundary are locally visible.
- Bad for H1: the native surface is graph-first and does not validate the minimum-action skin.
- Interesting: live `/object_info` makes the native H3 route auditable without source copying.
- Not relevant to H1 at this gate: Studio, Storyboard, Timeline, Cast, multi-track, 3D, Manga.

## Screens and evidence

- [01_start.png](screenshots/01_start.png) is a screenshot from the actual local
  ComfyUI start surface. It is not an upstream image.
- [contact_sheet.png](contact_sheet.png) contains the available local start capture;
  no unobserved screens are represented.

## Local modifications / limitations

No source or custom node was patched. Only launch flags were supplied. Existing
custom nodes produced unrelated startup warnings (Triton unavailable and Manager
outbound fetches blocked); they are recorded as environment observations, not H3
generation results.
