# H3 Reference Implementation Evaluation Index

更新: 2026-09-08 JST

## Purpose

このindexは、H3 Reference Implementation Evaluationの実行条件、固定source、
local runtime結果、candidate別証跡をWeb GPTがGitHub上で追跡するための入口である。
Production output (`output/h3/`)とreview evidence (`docs/h3/evidence/`)を分離する。
外部candidateのsource、依存、model、生成mediaはTEGAKIへcommitしない。

## Evaluation date

2026-09-08 JST

## Environment boundary

- Repository: `https://github.com/toshinka/tegaki`
- Portable Python: 3.13.14
- ComfyUI local vendor: 0.30.0, detached local commit recorded below
- GPU: NVIDIA GeForce RTX 4070, 12282 MiB reported by `nvidia-smi`
- System RAM: 63.77 GiB reported by ComfyUI `/system_stats`
- H3 model weights: not found under `ComfyUIPortable/ComfyUI/models/`
- No model was downloaded and no candidate was installed into the shared
  ComfyUI custom-node directory.

## Candidates

| Candidate | Source commit | Installation status | Runtime status | Evidence | Contact sheet | Comparison status | Blocker / boundary |
|---|---|---|---|---|---|---|---|
| Native / official ComfyUI H3 | local `b1693ecba9f5b65f8c80ab36b195ab963ec92413`; upstream master checked `efa6c8f804bff78b46a0fd458ebd2e47bba07a30` | VERIFIED LOCAL: existing Portable runtime | VERIFIED LOCAL: server startup, `/system_stats`, native H3 entries in `/object_info`; generation BLOCKED | [native evidence](reference-implementations/native/2026-09-08/README.md) / [manifest](reference-implementations/native/2026-09-08/manifest.json) | [native contact sheet](reference-implementations/native/2026-09-08/contact_sheet.png) | UI/runtime baseline only; no generation comparison | H3 weights absent; startup used `--cpu` |
| H3 Easy | `d00fd814769e586545c454d75068856c71c79116` | BLOCKED: source clone is isolated; not copied into shared `custom_nodes` | BLOCKED: `/object_info` contains no H3 Easy entries; no generation | [H3 Easy evidence](reference-implementations/h3-easy/2026-09-08/README.md) / [manifest](reference-implementations/h3-easy/2026-09-08/manifest.json) | Not generated | Not directly comparable | shared runtime mutation and model absence intentionally avoided |
| onigirikiller H3 Studio | `f9b28d56d69192e4516907a61103a71ff2c29c27` | BLOCKED: no install; required `gradio>=4.39` is missing | BLOCKED: `app.py --help` stopped at `ModuleNotFoundError: gradio` | [onigirikiller evidence](reference-implementations/onigirikiller/2026-09-08/README.md) / [manifest](reference-implementations/onigirikiller/2026-09-08/manifest.json) | Not generated | Not directly comparable | no dependency installation authorized; model absence also blocks generation |
| AntaresAlice H3 WebUI | `4f10667c604f9cb333ac119b457a3659260a8966` | VERIFIED LOCAL: source clone only; runtime launched with env-only path config | VERIFIED LOCAL: WebUI `8081`, ComfyUI status API; generation BLOCKED | [Antares evidence](reference-implementations/antares/2026-09-08/README.md) / [manifest](reference-implementations/antares/2026-09-08/manifest.json) | [Antares contact sheet](reference-implementations/antares/2026-09-08/contact_sheet.png) | UI/startup comparison only; no generation comparison | model weights absent; no output produced |

## Comparison status

This is a same-task smoke evaluation, not a performance benchmark. A common prompt,
reference, resolution, duration, and steps were not run because the local H3 weights
were absent. UI-level observations are marked separately from generation-level results;
the candidates are not declared equivalent or adopted.

## Blockers

1. No H3 diffusion, text-encoder, video-VAE, or audio-VAE weights were found in the
   local Portable model shelf.
2. onigirikiller needs `gradio>=4.39`, which is not in the embedded environment; no
   dependency installation was performed.
3. H3 Easy is a ComfyUI custom node and was not installed into the shared runtime,
   so the Manga-adjacent Portable environment was not mutated for this evaluation.
4. No generated video exists, so no output SHA-256, frame triplet, peak VRAM, or OOM
   recovery result can be claimed.

## Next review

Web GPT may review the pinned source/license/provenance records and the actual local
startup evidence. A separate owner-authorized card is required before installing
weights/dependencies, running generation, or selecting an H1 ingredient.
