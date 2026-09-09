# H2A — H3 Still Native Feasibility Closeout

Date: 2026-09-10 JST

## Decision

```text
H2A STILL FEASIBILITY: PASS
Classification: FEASIBLE WITH LIMITS
Selected route: B. short temporal packet → selected frame
Recommended next direction: 1. Still UI vertical slice
```

The current verified H3 model/runtime stack can produce one practical still
image on the RTX 4070 12GB environment through a bounded text-only route. The
current Native H3 nodes do not expose a true single-image latent or a supported
`T=1` execution. The least invasive tested route is therefore a five-frame
temporal packet, decoded with the existing video VAE, followed by selection of
one decoded frame. It completed with no OOM, no accepted-job retry, no model
relocation, and no shared runtime change.

`FEASIBLE WITH LIMITS` is intentional: this proves execution feasibility of a
selected-frame still route, not a final Still product, broad quality baseline,
native T2I semantics, source fidelity, or production stability across a matrix
of prompts and resolutions.

## Status distinction

| Status | Result | Meaning |
|---|---|---|
| `IMPLEMENTED` | `PASS` | H2A adapter, workflow, runner, and contract test are present. |
| `VERIFIED SOURCE/LOGIC` | `PASS` | The H2A graph and fail-closed text-only adapter contracts pass. |
| `VERIFIED LOCAL STILL GENERATION` | `PASS` | One real Native PNG completed on the RTX 4070 stack. |
| `VERIFIED BROWSER UI` | `N/A` | This feasibility Card intentionally adds no production Still UI. |
| `PUBLISHED ON MAIN` | `LOCAL MAIN / OWNER PUSH PENDING` | H2A commits are local; they are not claimed as published. |
| `OWNER ACCEPTED` | `PENDING` | Technical evidence does not replace Owner acceptance. |

## 1. Route comparison and selection

| Route | Required model / node path | Custom node | Output semantics | Known status | 12GB expectation | H2A decision |
|---|---|---|---|---|---|---|
| A. Native single-image decode | Existing H3 diffusion model, Qwen3-VL text encoder, video VAE; would still need a valid H3 temporal latent before decode | None if it collapsed into B | One image only if a valid temporal packet already exists; no current direct single-image latent path | Not exposed by the current Native node surface | Unknown as a distinct route | Rejected as not separately exposed |
| B. Short temporal packet → selected frame | Existing `MiniMaxH3ImageToVideo` → `SamplerCustomAdvanced` → `VAEDecode` → `ImageFromBatch` → `SaveImage`; packet length `5` | None | One selected decoded frame; not a native T2I semantic | Feasibility-only experimental adaptation; locally generated successfully | Tested successfully with peak `9736 MiB` used and minimum `2277 MiB` free | Accepted and tested |
| C. Experimental `T=1` | Would require a new temporal contract around the H3 AV latent/model path | None in current graph; a workaround would broaden runtime or require external code | Experimental one-frame latent | Unsupported research path under the current node contract | Not testable under the current node contract | Rejected / deferred |

The decisive source constraint is in the current native H3 node implementation:
`EmptyMiniMaxH3LatentAV` and `MiniMaxH3ImageToVideo` accept a minimum length of
`5`, and the temporal shape is aligned to the model's `17k+5` frame grid. The
current video VAE is a 3D causal VAE with a video latent temporal axis. H2A
does not change those contracts; it uses the minimum supported packet and
selects one decoded image afterward.

## 2. Implementation boundary

Added in the H2A implementation commits:

- `h3/adapters/native_still.py` — text-only semantic validation and
  materialization of the H2A graph.
- `workflows/h3/H2A_NATIVE_STILL_BASE.json` — one H3-only experimental graph
  with existing model loaders, sampler, video VAE, `ImageFromBatch`, and
  `SaveImage`.
- `h3/tests/run_h2a_still.py` — one-shot local Native runner with output hash
  and bounded `nvidia-smi`/`psutil` telemetry.
- `h3/tests/test_h2a_still_adapter.py` — H2A graph and fail-closed contract
  tests.

No visible Still control was added. No H3 Video adapter, H3 Video UI, shared
ComfyUI core/frontend, Manga implementation, or project schema was changed.

## 3. Real local still generation

| Field | Observed value |
|---|---|
| Route | `native_still` |
| Workflow | `workflows/h3/H2A_NATIVE_STILL_BASE.json` |
| Workflow schema | `tegaki.h3.h2a.native-still/v1` |
| Prompt | `A small orange robot stands alone on a pale blue studio background, clean illustrative anime style, centered composition, soft daylight.` |
| Model | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| Text encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` |
| Video VAE | `minimax_h3_video_vae_fp16.safetensors` |
| Resolution | `608 x 352` |
| Packet / selected frame | `5` / `0` |
| Seed | `20260910` |
| Steps | `20` |
| Sampler / scheduler | `res_multistep` / `simple` |
| Runner elapsed | `54.21s` |
| Native prompt execution | `53.04s` |
| Output dimensions / format | `608 x 352` / `PNG` |
| Output | `output/h3/still/h2a_native_still_00001_.png` (ignored) |
| Evidence copy | `docs/h3/evidence/h2a-still/2026-09-09/accepted_still.png` |
| Output SHA-256 | `86165612E0DFDE15219AB90343DE7991BEEB2641C41BAD2495F7CE9057867A99` |

The runner submitted the accepted job once. An earlier request to the already
running, misconfigured `8188` process was rejected during ComfyUI validation
because the isolated H3 model list was empty; it did not queue or execute a
job. The accepted run used the correctly isolated H3 Native process on `8189`.

## 4. RTX 4070 / memory evidence

| Field | Observed value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 |
| VRAM total | `12282 MiB` |
| Peak observed VRAM | `9736 MiB` |
| Minimum observed free VRAM | `2277 MiB` |
| System RAM total | `68476002304 bytes` (`63.77 GiB`) |
| Peak Native working set | `38185992192 bytes` (`36417 MiB`, about `35.56 GiB`) |
| Telemetry samples | `29` |
| OOM count | `0` |
| Accepted-job retry count | `0` |
| Custom nodes | disabled |
| Model store | isolated `h3/model_store/` |

VRAM was sampled with `nvidia-smi` and the Native process working set with
`psutil`. The working-set value is not claimed as a continuous system-RAM
peak. The accepted run did not require deleting models, restarting for an OOM,
moving weights into `ComfyUI/models/`, or installing dependencies.

## 5. Bounded static output review

| Question | Observation |
|---|---|
| Valid still image? | Yes; RGB PNG, `608 x 352`. |
| Composition coherent? | Yes; centered single robot on a simple pale blue background. |
| Subject recognizable? | Yes; the orange robot is clearly recognizable. |
| Obvious temporal/video artifact? | None observed in the selected frame. |
| Obvious frame-blending artifact? | None observed. |
| Obvious decode artifact? | None observed. |

This is a bounded visual observation only. It does not judge Manga production
readiness and does not claim Still superiority over Illustrious.

## 6. Optional source-anchor test

`DEFER`. The selected H2A adapter is intentionally text-only. It does not add
image anchoring, REF2VA, ordered references, or I2I semantics merely to obtain
an optional second test.

## 7. Video regression and verification

H2A is isolated from the H1 Video adapter and UI. Required regression evidence:

- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `python -m unittest discover -s h3/tests -p 'test_*.py'` — `36 tests, OK`.
- `node --check` for `app.js`, `history-settings.js`, `job-status-copy.js`,
  and `continuation-source.js` — all `PASS`.
- `python -m compileall -q h3/app h3/adapters h3/tests` — `PASS`.
- `git diff --check` — `PASS`.

No real Video generation was repeated because H2A did not touch the shared H3
execution path. The exact command results are recorded in the completion
message and the evidence package's provenance boundary.

## 8. Scope audit

| Area | Result |
|---|---|
| Workflow changes | One H3-only H2A still workflow. |
| Model changes | `NONE`; existing first-wave stack only. |
| Dependency changes | `NONE`. |
| Shared ComfyUI changes | `NONE`. |
| Manga changes | `NONE`. |
| Production Still UI | `NONE`; Browser UI is `N/A` by design. |
| Ordered references / REF2VA / I2I | `NOT STARTED`; source anchor deferred. |
| Studio / Timeline / Storyboard / Cast / 3D | `NOT STARTED`. |

## Report and evidence

Report: `docs/h3/reports/H2A_H3_STILL_NATIVE_FEASIBILITY_REPORT.md`

Evidence README: `docs/h3/evidence/h2a-still/2026-09-09/README.md`

Manifest: `docs/h3/evidence/h2a-still/2026-09-09/manifest.json`

Accepted image: `docs/h3/evidence/h2a-still/2026-09-09/accepted_still.png`

## Final report format

```text
H2A STILL FEASIBILITY: PASS

Publication correction: PASS

Implementation commits:
`6e81ce95fd67e1a8ce89855ee26647fedb1b6905`,
`0b8615f9ac7d54b009059e4e50faaab127b2eacd`

Evidence/docs commit:
`c3b15a9468b6423148b2760c0ea08953eb71c96c`

Selected Still route: B. short temporal packet → selected frame

Classification: FEASIBLE WITH LIMITS

Real Still generation: PASS

Resolution: 608x352

Seed: 20260910

Steps: 20

Elapsed: 54.21s

Peak VRAM: 9736 MiB used

Peak RAM: 38185992192 bytes Native working set

OOM: 0

Retries: 0

Output SHA-256: 86165612E0DFDE15219AB90343DE7991BEEB2641C41BAD2495F7CE9057867A99

Source-anchor optional test: DEFER

H1C regression: PASS

P2 regression: PASS

Workflow changes: one H3-only experimental still workflow

Model changes: NONE

Dependency changes: NONE

Shared ComfyUI changes: NONE

Manga changes: NONE

Report: docs/h3/reports/H2A_H3_STILL_NATIVE_FEASIBILITY_REPORT.md

Evidence: docs/h3/evidence/h2a-still/2026-09-09/

Recommended next direction: 1. Still UI vertical slice

Owner acceptance: PENDING

STOP
```

H2A stops here. Ordered multi-reference, REF2VA, Manga, H3→Illustrious,
Timeline, and Studio are not started.
