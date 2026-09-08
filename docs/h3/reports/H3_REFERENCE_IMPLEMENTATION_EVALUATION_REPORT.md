# H3 Reference Implementation Evaluation Report

更新: 2026-09-08 JST
Status: H0 evidence pass; no H1 implementation decision

## Summary

The canonical H3 path survived the Manga namespace split. The native ComfyUI runtime
contains MiniMax H3 support and starts locally. AntaresAlice's WebUI starts against
that local ComfyUI and exposes the expected minimum Video surface. H3 Easy and
onigirikiller were source-audited but blocked before generation: the former was not
installed into the shared custom-node runtime, and the latter lacks `gradio` in the
embedded Python environment. All four candidates are therefore useful evidence, but
none is an adopted implementation and no quality or performance claim is made.

## Environment

| Field | Observed value |
|---|---|
| Portable Python | 3.13.14 |
| ComfyUI | 0.30.0 |
| Native ComfyUI local commit | `b1693ecba9f5b65f8c80ab36b195ab963ec92413` (detached); upstream master checked `efa6c8f804bff78b46a0fd458ebd2e47bba07a30` |
| PyTorch | 2.13.0+cu130 |
| GPU | NVIDIA GeForce RTX 4070 |
| VRAM | 12282 MiB reported by `nvidia-smi` |
| RAM | 63.77 GiB reported by ComfyUI `/system_stats` |
| Native launch | `main.py --listen 127.0.0.1 --port 8188 --cpu --disable-auto-launch` |
| Antares launch | `webui/server.py` at `127.0.0.1:8081`, env-only ComfyUI/input/output paths |
| H3 weights | Missing from `ComfyUIPortable/ComfyUI/models/` |
| Generated media | None |

The `--cpu` native launch was used to verify startup and node registration without
loading absent H3 weights. It is not a GPU generation result.

## Candidates and installation

### Native / official ComfyUI baseline

- Repository: https://github.com/Comfy-Org/ComfyUI
- Code license: GPL-3.0, from the local `ComfyUI/LICENSE`.
- Checked local commit: `b1693ecba9f5b65f8c80ab36b195ab963ec92413`.
- Runtime: `VERIFIED LOCAL` — HTTP 200 from `/system_stats`; `/object_info` listed
  `EmptyMiniMaxH3LatentAV`, `MiniMaxH3ImageToVideo`, `MiniMaxH3ReferenceToVideo`,
  and `MiniMaxH3SigmaShift`.
- Generation: `BLOCKED` — no H3 model weights were present.
- Local modification: none; only launch flags were supplied.

### H3 Easy

- Repository: https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy
- Checked commit: `d00fd814769e586545c454d75068856c71c79116`.
- Code license: MIT (`LICENSE`). Model license/provenance is separate and points to
  the official MiniMax H3 distribution terms.
- Dependencies: `requests` and `psutil` in `pyproject.toml`; both are present in the
  Portable Python. The node itself still requires installation under
  `ComfyUI/custom_nodes/`.
- Runtime: `BLOCKED` — it was not copied into the shared ComfyUI runtime; no H3 Easy
  node names appeared in `/object_info`.
- Generation: `BLOCKED` — required model files are absent.
- Local modification: none. The source clone is ignored under `h3/reference_impls/`.

### onigirikiller H3 Studio

- Repository: https://github.com/onigirikiller/minimax-h3-webui
- Checked commit: `f9b28d56d69192e4516907a61103a71ff2c29c27`.
- Code license: Apache-2.0 (`LICENSE`/`NOTICE`). The repository explicitly separates
  its code license from the MiniMax H3 Community License Agreement and third-party
  ComfyUI/Gradio/FFmpeg terms.
- Dependencies: `gradio>=4.39` in `requirements.txt`; the embedded environment has
  no `gradio` module.
- Startup: attempted `python app.py --help`; it stopped before argument handling with
  `ModuleNotFoundError: No module named 'gradio'`.
- Generation: `BLOCKED` — dependency and model weights are missing.
- Local modification: none; no dependency was installed.

### AntaresAlice H3 WebUI

- Repository: https://github.com/AntaresAlice/h3-webui
- Checked commit: `4f10667c604f9cb333ac119b457a3659260a8966`.
- Code license: MIT (`LICENSE`). The source README separates the code license from
  MiniMax H3, ComfyUI, and other component terms.
- Dependencies: source imports `aiohttp`, Pillow, and PyAV; the Portable environment
  contains `aiohttp 3.14.3`, `Pillow 12.3.0`, and `av 18.0.0`.
- Runtime: `VERIFIED LOCAL` — server started at `127.0.0.1:8081`; `/` and
  `/api/comfyui/status` returned HTTP 200. The browser showed the actual H3 Studio
  start surface with i2v/r2v mode, reference input, prompt, model/resolution/steps/
  duration/seed controls, and a disabled Generate action until a reference is added.
- Generation: `BLOCKED` — status returned `ref2va_present:false`, and the local H3
  weight scan was empty. No output was written.
- Local modification: environment-only path configuration pointed input to
  `output/h3/tests` and output to `output/h3/video`; source files were not patched.

## Generation and same-task comparison

No candidate reached a comparable generation. Therefore these fields are deliberately
`NOT TESTED` rather than inferred from README claims:

| Axis | Native | H3 Easy | onigirikiller | AntaresAlice |
|---|---|---|---|---|
| First generation | BLOCKED: weights | BLOCKED: not installed + weights | BLOCKED: gradio + weights | BLOCKED: weights |
| Prompt behavior | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Reference order/reuse | NOT TESTED | NOT TESTED | NOT TESTED | UI surface observed; runtime not tested |
| Resolution/duration/steps | Node surface only | NOT TESTED | NOT TESTED | UI defaults/presets observed; runtime not tested |
| Queue/progress/history | native queue not evaluated | NOT TESTED | NOT TESTED | start surface/history empty; generation not tested |
| Continuation | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Visual output | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| H1 relevance | baseline boundary | design material | design material | design material |

This pass is not a performance benchmark. There is no output SHA-256, first/middle/last
frame record, peak VRAM, runtime duration, or OOM recovery result.

## Native observations

The local native implementation is a credible capability baseline: it exposes H3 latent,
I2V, reference-to-video, and sigma-shift node entries in the live API. Its UI remains a
workflow canvas, so it is a backend/node baseline rather than the minimum-action H1 skin.

## H3 Easy observations

The candidate provides a single H3-oriented node surface, media management, ordered
references, `@` prompt references, and progressive advanced/segment controls in its
source documentation. These are design observations only. They were not promoted to
runtime evidence because installing the node into the shared ComfyUI would cross the
evaluation boundary and the model shelf is empty.

## onigirikiller observations

The candidate's intended small flow, queue, continuation, and history are relevant to
the H1 review. They remain `NOT TESTED`: the embedded environment lacks Gradio and no
new dependency was installed. No upstream screenshot is used as local evidence.

## AntaresAlice observations

The actual local start surface makes the following visible without entering an advanced
screen: Video task type, reference assets, prompt, model, resolution, native scale,
sampling steps, duration, seed, low-VRAM/SageAttention/Turbo labels, History, and
Generate. This is useful evidence for minimum-action and cognitive-lens review. The
empty history and disabled Generate state also make the missing-reference boundary
legible. The richer Studio/history/continuation paths were not claimed as verified
without a successful generation.

## Common good / bad / interesting / not relevant

### Good

- Video-first entry remains visible in the local Antares surface.
- Familiar production terms are used instead of brand-specific replacements.
- Preview/result and history are visually part of the production flow.
- The native baseline keeps H3 capability close to the ComfyUI API boundary.

### Bad

- Missing weights prevent an honest visual or performance comparison.
- Native ComfyUI is still a graph-first surface for a normal user.
- An apparently complete UI can expose model choices even when the actual asset is
  absent; the error/availability copy must remain explicit.

### Interesting

- Antares exposes model and resolution state in the minimum surface while keeping the
  Generate action disabled until an input exists.
- H3 Easy's ordered media and `@` references are promising but need a real reference
  order test.
- onigirikiller separates its UI license from the model license in a way that should
  remain in any future evidence record.

### Not relevant to H1 at this gate

- Full Studio, Storyboard, Timeline, Cast, multi-track, 3D, Manga, and large-system
  architecture.
- Fast-runtime or 12GB performance claims copied from upstream README text.

## 12GB observations, errors, and OOM

The target GPU is a 12GB-class RTX 4070. Native and Antares startup succeeded without
loading H3 weights. No H3 generation was attempted, so peak VRAM, quality at 864x480,
OOM behavior, recovery, and output quality are all `NOT TESTED`. Native startup logged
environmental warnings for unavailable Triton and blocked outbound ComfyUI-Manager
fetches; those are startup-environment observations, not H3 generation failures.

## Evidence links and output locations

- [Evaluation index](../evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md)
- [Native evidence](../evidence/reference-implementations/native/2026-09-08/README.md)
- [H3 Easy evidence](../evidence/reference-implementations/h3-easy/2026-09-08/README.md)
- [onigirikiller evidence](../evidence/reference-implementations/onigirikiller/2026-09-08/README.md)
- [Antares evidence](../evidence/reference-implementations/antares/2026-09-08/README.md)
- Production namespace: `ComfyUIPortable/output/h3/video/`
- Debug namespace: `ComfyUIPortable/output/h3/debug/`
- Smoke-test namespace: `ComfyUIPortable/output/h3/tests/`

No generated video or large media is committed.

## Commits, licenses, local modifications, blockers

- Candidate source clones are ignored under `h3/reference_impls/`; no external source
  repository is committed.
- Code licenses are recorded separately from MiniMax H3 model provenance in every
  candidate record.
- No model download, dependency installation, custom-node installation, frontend
  implementation, H1 implementation, Astra rerun, Still/Studio/Timeline/Storyboard
  implementation, or Manga change was performed.
- The remaining blockers are the missing H3 weights, missing Gradio for onigirikiller,
  and the owner decision on whether an isolated custom-node runtime may be created.

## Recommendations for Web GPT

1. Review the four pinned source/license records and accept the explicit blocked state.
2. Treat Antares' visible minimum surface and H3 Easy's ordered-reference concept as
   review ingredients, not adopted code.
3. Keep native ComfyUI as the backend capability boundary and do not promote its graph
   canvas to the H1 user entry by default.
4. Require an owner-authorized model/dependency pass before any generation comparison.
5. Keep all Studio/Storyboard/Cast/Manga ideas outside H1 until the first flow is
   reproducible.

## Next gate

Web GPT evidence review. If and only if that review releases a bounded card, a later
owner-authorized pass may acquire the required model assets and run the common smoke
task. This report stops before H1.
