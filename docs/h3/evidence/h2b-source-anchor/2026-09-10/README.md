# H2B — Source-Anchored Still / Single Reference I2I Feasibility Evidence

Date: 2026-09-10 JST

Status: `PASS`

This package records one matched Native H3 comparison: prompt-only Still
control versus one source-anchored Still. Both use the existing five-frame
temporal packet, video VAE decode, `ImageFromBatch` frame `0`, and built-in
`SaveImage`. The source-anchored graph adds exactly one `LoadImage` edge to
`MiniMaxH3ImageToVideo.first_frame`; it is not generic multi-reference,
REF2VA, or a production Still UI.

## Source and matched settings

| Field | Observed value |
|---|---|
| Source | [`source.png`](source.png) |
| Source provenance | Existing local H3 test source `output/h3/tests/reference_robot_v1.png`; not a prompt-derived target |
| Source format / dimensions | `PNG` / `608 x 352` |
| Source bytes | `206821` |
| Source SHA-256 | `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E` |
| Prompt | Retain the same small service robot, pose, and overall greenhouse composition from the source image; change the lighting to warm late-afternoon sunlight with a gentle golden atmosphere while preserving the framing. |
| Resolution | `608 x 352` |
| Seed / steps | `20260910` / `20` |
| Sampler / scheduler | `res_multistep` / `simple` |
| Temporal packet / selected frame | `5` / `0` |

## Matched Native runs

| Run | Prompt id | Runner elapsed | Output | SHA-256 | Peak VRAM / minimum free | Peak Native working set | OOM / retry |
|---|---|---:|---|---|---:|---:|---:|
| Prompt-only control | `7a821bbb-dcbb-4486-9899-2cbb7a4cc09e` | `52.27s` | [`prompt_only.png`](prompt_only.png) | `A1485D07555F756CE7810341E29C082BD383C013153F1F489C4482D3341539FB` | `11488 / 525 MiB` | `39984459776 bytes` | `0 / 0` |
| Source-anchored | `5b4dc931-f6d6-4fbe-9a97-56ec8294328e` | `29.34s` | [`anchored.png`](anchored.png) | `1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5` | `11449 / 564 MiB` | `40173133824 bytes` | `0 / 0` |

Both outputs are valid RGB PNGs at `608 x 352`. The Native process was the
isolated H3 runtime on port `8189`, GPU `NVIDIA GeForce RTX 4070`, VRAM total
`12282 MiB`, system RAM total `68476002304 bytes`, with custom nodes disabled.
The pair ran close to the 12GB boundary; the source-anchored run did not
exceed the matched prompt-only peak in this observation, but this is not a
stability or memory-matrix claim. H2A's earlier text-only peak was `9736 MiB`;
H2B's absolute peaks were higher for both matched runs, so this pair does not
isolate a source-conditioning-specific increase.

## Source influence review

[`comparison_contact_sheet.png`](comparison_contact_sheet.png) is ordered
`source` → `prompt-only` → `anchored`.

- The prompt-only control produces a different robot silhouette, scale, pose,
  and greenhouse composition.
- The anchored result retains the source robot's large close-up layout,
  orientation, major silhouette, red/white body colors, blue eye light, and
  leafy greenhouse background.
- The result is not byte-identical to the source and is visibly a generated
  Still, but the retained structure is much stronger than the matched
  prompt-only control.

Bounded qualitative conclusion: `SOURCE INFLUENCE OBSERVED: PASS`. No identity
score, CLIP score, fidelity percentage, or production consistency claim is
made.

## Conditioning semantics

```text
node 133 LoadImage
  image = inputs/h2b_source_43d29d07b5d0b4a2.png

node 131 MiniMaxH3ImageToVideo
  first_frame = ["133", 0]
  length = 5

node 131 → SamplerCustomAdvanced → VAEDecode
  → node 132 ImageFromBatch(batch_index=0, length=1)
  → node 92 SaveImage
```

The existing Native implementation takes `first_frame[:1]`, applies
`_resize(..., width=608, height=352, crop="disabled")` (plain stretch), and
encodes that image with the existing video VAE. Its keyframe metadata places
the encoded source at temporal frame `0`. There is no source-strength or
fidelity-like input on this node, so the optional strength observation is
`NOT APPLICABLE`.

The prompt-only control uses the same H2B workflow basis after removing node
`133` and the `first_frame` edge. No second Still engine was created.

## Provenance and scope audit

- Workflow: `workflows/h3/H2B_SOURCE_ANCHORED_STILL_BASE.json`.
- Adapter: `h3/adapters/native_source_anchored_still.py`.
- Local runner: `h3/tests/run_h2b_source_anchor.py`.
- Source contract accepts exactly one staged PNG/JPEG under `inputs/`; remote
  URLs, `file://`, arbitrary paths, multiple images, reference arrays, and
  WebP fail closed.
- Existing isolated models under `h3/model_store/` were used unchanged.
- New model: `NONE`.
- New dependency/custom node: `NONE`.
- Shared ComfyUI core/frontend change: `NONE`.
- Manga change: `NONE`.
- Production Still UI: `NONE`; Browser UI is `N/A` by design.
- Implementation commit: `8a6b74f4fef2c9437ce07dd8fb85eb85bcda5971`.
- Evidence/docs commit: `828524e8700d4c36906e692e3153ed9e17772ee5`.

## Regression checks

- `python -m unittest h3.tests.test_h2a_still_adapter` — `4 tests, OK`.
- `python -m unittest h3.tests.test_h2b_source_anchored_still` — `5 tests, OK`.
- `python -m unittest discover -s h3/tests -p 'test_*.py'` — `41 tests, OK`.
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- H3 JavaScript syntax checks — `PASS`.
- Python `compileall` — `PASS`.
- `git diff --check` — `PASS`.

Publication: `PUBLISHED ON MAIN` for H2B. H2A publication is also
`PUBLISHED ON MAIN`. Owner acceptance remains
`PENDING`.
