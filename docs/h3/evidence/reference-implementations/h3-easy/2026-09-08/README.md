# ComfyUI-MiniMaxH3-Easy — 2026-09-08

Status: `BLOCKED` for runtime evaluation. The pinned source was inspected in an
ignored local worktree, but it was not installed into the shared ComfyUI runtime.

## Candidate

- Candidate: H3 Easy
- Source: https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy
- Pinned commit: `d00fd814769e586545c454d75068856c71c79116`
- Upstream status: local shallow clone matches the checked `main` head at the pinned SHA.
- Code license: MIT, local `LICENSE`
- Model provenance/license: MiniMax H3 official distribution and Community License
  Agreement, separate from the node license.

## Local conditions

- Portable Python 3.13.14
- ComfyUI 0.30.0
- GPU: NVIDIA GeForce RTX 4070 / 12282 MiB
- RAM: 63.77 GiB
- Existing runtime packages relevant to `pyproject.toml`: `requests` and `psutil`
  are present.
- Candidate source remains under ignored `h3/reference_impls/h3-easy/`.
- Required custom nodes: `ComfyUI-MiniMaxH3-Easy` under
  `ComfyUI/custom_nodes/`, plus the native MiniMax H3 nodes.
- Python dependencies: `requests`, `psutil` from `pyproject.toml`; ComfyUI runtime
  supplies the remaining node/runtime imports.
- Expected output path for this evaluation: `ComfyUIPortable/output/h3/video/`.
- Compatibility note: current ComfyUI 0.30.0 has the native H3 surface required by
  the README, but Easy itself was not installed and no H3 assets are present.

## Installation / startup

The upstream install target is `ComfyUI/custom_nodes/`. It was intentionally not
copied into the shared runtime, because this pass must not mutate the existing
Portable/Manga-adjacent custom-node set. Live `/object_info` contained no H3 Easy
node names. Source syntax compilation passed; no runtime import or generation was
claimed.

## Models and common test

The upstream workflow expects H3 diffusion, text encoder, video/audio VAE assets,
and optionally a 3D latent upscaler. A targeted local model scan found none.

- Workflow: upstream workflow examples were not run.
- Prompt/reference/resolution/duration/steps: `NOT TESTED`.
- Generation status: `BLOCKED` — not installed and model assets missing.
- Output SHA-256: none.
- 12GB observation: no H3 load, no peak VRAM, no OOM result.

## Behavior record

- Startup: `BLOCKED` before runtime install.
- First flow: `NOT TESTED`.
- Reference / Advanced: source concepts observed; actual ordering and disclosure `NOT TESTED`.
- Queue / Progress / History: `NOT TESTED`.
- Continuation: source concept observed; runtime `NOT TESTED`.
- Error / Disconnect: `NOT TESTED`.
- Good for H1: one-node media entry, ordered references, and progressive disclosure are clear review ingredients.
- Bad for H1: no local runtime result and no model-backed evidence.
- Interesting: `@` references provide an explicit candidate for reference-order review.
- Not relevant to H1 at this gate: long segment refinement, Studio, Storyboard, Cast, 3D, Manga.

## Evaluation notes

The source is relevant to minimum-action review because it combines common H3 modes,
media management, ordered references, `@` prompt references, and advanced/segment
disclosure. These are source observations, not TEGAKI adoption decisions.

No local screenshot is recorded because this candidate did not expose a running UI in
the evaluated environment. Upstream screenshots are deliberately not substituted.

## Local modifications / limitations

No candidate source or shared runtime file was patched. Dependency installation,
custom-node installation, model acquisition, and generation were deferred.
