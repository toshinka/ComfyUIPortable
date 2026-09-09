# H2A — H3 Still Native Feasibility Evidence

Date: 2026-09-09 evidence directory; generation observed 2026-09-10 JST.

Status: `PASS`

This package records one bounded text-only H3 still feasibility run. The
selected route uses the existing Native H3 AV model path for the minimum
five-frame temporal packet, decodes the video branch, selects frame `0`, and
saves that one image through the built-in `SaveImage` node. It is not a
production Still UI and does not establish Manga readiness.

## Accepted run

| Field | Observed value |
|---|---|
| Route | `native_still` |
| Workflow | `workflows/h3/H2A_NATIVE_STILL_BASE.json` |
| Prompt id | `9f07fad0-6b9b-4523-8044-de2df4674251` |
| Prompt | Small orange robot, pale blue studio background, clean illustrative anime style |
| Resolution | `608 x 352` |
| Temporal packet | `5` frames at `24` fps |
| Selected frame | `0` |
| Seed / steps | `20260910` / `20` |
| Sampler / scheduler | `res_multistep` / `simple` |
| Runner elapsed | `54.21s` |
| Native prompt execution | `53.04s` |
| Output | [`accepted_still.png`](accepted_still.png) |
| Format / dimensions | `PNG` / `608 x 352` / RGB |
| Output bytes | `172927` |
| SHA-256 | `86165612E0DFDE15219AB90343DE7991BEEB2641C41BAD2495F7CE9057867A99` |

## Runtime and telemetry

| Field | Observed value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 |
| VRAM total | `12282 MiB` |
| Peak observed VRAM used | `9736 MiB` |
| Minimum observed VRAM free | `2277 MiB` |
| System RAM total | `68476002304 bytes` |
| Peak Native working set | `38185992192 bytes` (`36417 MiB`) |
| Native process | PID `51096`, port `8189` |
| Samples | `29` |
| OOM | `0` |
| Retry | `0` |
| ComfyUI / Python / PyTorch | `0.30.0` / `3.13.14 embedded` / `2.13.0+cu130` |
| Custom nodes | disabled |

VRAM was sampled with `nvidia-smi`; working set and total RAM were sampled with
`psutil`. The working-set value is not a continuous system-RAM peak. The
accepted job was submitted once. One earlier request was rejected before
queueing because an unrelated process on port `8188` did not expose the
isolated H3 model paths; it is recorded as a pre-submit validation issue, not
an H2A generation retry or OOM.

## Provenance

- The workflow is H3-only and is based on the tracked H1A Native T2V graph:
  `workflows/h3/H1A_NATIVE_T2V_BASE.json`.
- The model files were read from the existing isolated `h3/model_store/` via
  `h3/config/extra_model_paths.yaml`.
- The selected model, Qwen text encoder, and video VAE are unchanged from the
  verified first-wave stack.
- No model was copied into `ComfyUI/models/`; no custom node was installed or
  loaded; shared ComfyUI and Manga were unchanged.
- The source output remains under ignored `output/h3/`; only this one small
  still PNG is retained in the tracked evidence package.

## Bounded visual review

The retained PNG is a valid RGB still image. The single robot is recognizable,
the centered composition is coherent, and the simple background is consistent
with the test prompt. No obvious temporal artifact, frame-blending artifact, or
decode artifact is visible in the selected frame. This is a static feasibility
observation, not a Manga production-quality judgment.

## Acceptance boundary

Browser UI: `N/A`. H2A intentionally validates the Still execution path
without adding a visible production Still control or a second UI architecture.

Source-anchor test: `DEFER`; this text-only adapter does not support an image
anchor without expanding the Card into I2I/REF2VA work.

## Regression checks

- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `python -m unittest discover -s h3/tests -p 'test_*.py'` — `36 tests, OK`.
- H3 JavaScript syntax checks — all `PASS`.
- Python `compileall` and `git diff --check` — `PASS`.

Publication: `LOCAL MAIN / OWNER PUSH PENDING` for H2A. Owner acceptance remains
`PENDING`.
