# H2B — Source-Anchored Still / Single Reference I2I Feasibility Closeout

Date: 2026-09-10 JST

## Decision

```text
H2B SOURCE-ANCHORED STILL: PASS
Classification: SOURCE ANCHOR FEASIBLE WITH LIMITS
Selected route: one source image → Native first_frame → five-frame packet → selected frame
Recommended next direction: 1. Still UI vertical slice
```

The existing verified Native H3 model/runtime stack accepted exactly one local
PNG source image as a visual anchor and produced a valid Still PNG on the RTX
4070 12GB environment. A matched prompt-only control was generated with the
same prompt, seed, resolution, steps, packet length, and frame-selection
semantics. The anchored output visibly retained the source subject layout,
silhouette, orientation, coarse colors, and composition beyond prompt-only
coincidence.

`FEASIBLE WITH LIMITS` is intentional. H2B uses the existing H3
`MiniMaxH3ImageToVideo.first_frame` conditioning surface rather than a native
single-image latent or production I2I semantic. It still creates the minimum
five-frame temporal packet, decodes through the video VAE, and selects frame
`0`. There is no bounded source-strength/fidelity parameter, the evidence is
one matched pair, and no production Still UI was added.

## Status distinction

| Status | Result | Meaning |
|---|---|---|
| `IMPLEMENTED` | `PASS` | H2B source-anchor adapter, workflow, runner, and contract tests are present. |
| `VERIFIED SOURCE/LOGIC` | `PASS` | The one-source path, graph edge, packet/decode/select route, and fail-closed contracts pass. |
| `VERIFIED LOCAL STILL GENERATION` | `PASS` | Both matched prompt-only and source-anchored Native PNGs completed locally. |
| `SOURCE INFLUENCE OBSERVED` | `PASS` | The anchored output visibly retains source structure while prompt-only does not. |
| `VERIFIED BROWSER UI` | `N/A` | This feasibility Card intentionally adds no production Still control. |
| `PUBLISHED ON MAIN` | `PUBLISHED ON MAIN` | H2B implementation and evidence/docs are present on GitHub `main`; Owner acceptance remains separate. |
| `OWNER ACCEPTED` | `PENDING` | Technical evidence does not replace Owner acceptance. |

The H2A publication wording correction is `PASS` in commit `67a8bd47`:
H2A is recorded as `PUBLISHED ON MAIN`, while Owner acceptance remains
`PENDING`. Historical H2A technical results were not changed.

## 1. Selected route and source contract

```text
one local PNG/JPEG
→ LoadImage
→ MiniMaxH3ImageToVideo.first_frame
→ minimum packet length 5
→ SamplerCustomAdvanced
→ video VAEDecode
→ ImageFromBatch(frame 0, length 1)
→ SaveImage
```

The source was the existing local H3 test input
`output/h3/tests/reference_robot_v1.png`, a clearly identifiable single robot
subject in a simple greenhouse composition. It was not used as a
prompt-derived target. The source SHA-256 is:

```text
43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E
```

The adapter accepts only one staged `inputs/<filename>` path with PNG/JPEG
suffix. It rejects remote URLs, `file://` URLs, absolute or arbitrary local
paths, traversal, multiple image values, reference arrays, and WebP. The local
runner may receive one explicit local test path, verifies its actual PNG/JPEG
content and limits, then stages it below the Native input directory before
compilation. No Browser upload or production request contract is defined.

## 2. Conditioning semantics

The H2B workflow is a separate H3-only adaptation of the verified H2A graph.
It adds one `LoadImage` node and one edge:

```text
node 133: LoadImage
  image = inputs/h2b_source_43d29d07b5d0b4a2.png

node 131: MiniMaxH3ImageToVideo
  first_frame = ["133", 0]
  length = 5
```

The existing Native implementation in
`ComfyUI/comfy_extras/nodes_minimax_h3.py` takes `first_frame[:1]`, applies
`_resize(..., width=608, height=352, crop="disabled")`, and encodes that
tensor with the existing video VAE. This is a plain stretch to the fixed
canvas, not a new adapter-level crop or resize policy. The resulting keyframe
metadata records `resolved_frame_index: 0`; the source occupies the first
temporal frame conditioning role.

The node has no strength or fidelity-like input. Optional source-strength
observation: `NOT APPLICABLE`. No new semantic layer was invented.

For the matched prompt-only control, the H2B compiler removes node `133` and
the `first_frame` edge from the same workflow basis. The graph still uses the
same H2A packet/decode/select path, so the comparison does not introduce a
second Still engine.

## 3. Matched comparison

| Field | Prompt-only control | Source-anchored |
|---|---|---|
| Route | `native_prompt_only_still_control` | `native_source_anchored_still` |
| Prompt id | `7a821bbb-dcbb-4486-9899-2cbb7a4cc09e` | `5b4dc931-f6d6-4fbe-9a97-56ec8294328e` |
| Prompt | same | same |
| Resolution | `608 x 352` | `608 x 352` |
| Seed / steps | `20260910` / `20` | `20260910` / `20` |
| Packet / selected frame | `5` / `0` | `5` / `0` |
| Runner elapsed | `52.27s` | `29.34s` |
| Output | `prompt_only.png` | `anchored.png` |
| Output SHA-256 | `A1485D07555F756CE7810341E29C082BD383C013153F1F489C4482D3341539FB` | `1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5` |

## 4. Source influence review

Evidence: [`comparison_contact_sheet.png`](../evidence/h2b-source-anchor/2026-09-10/comparison_contact_sheet.png)

The prompt-only control renders a different robot silhouette, scale, pose, and
greenhouse composition. The anchored result retains the source's large
close-up robot layout, orientation, major silhouette, red/white body colors,
blue eye light, and leafy greenhouse background. It is not byte-identical to
the source and remains a generated image, but the structure is visibly much
closer to the source than to the matched prompt-only control.

```text
SOURCE INFLUENCE: PASS
Evidence method: bounded qualitative visual comparison only
Identity score: NOT MEASURED
CLIP score: NOT MEASURED
Source fidelity percentage: NOT MEASURED
Production consistency: NOT CLAIMED
```

The source-anchored output is a valid `608 x 352` RGB PNG with no obvious
decode corruption, temporal artifact, or frame-blending artifact in the
selected frame.

## 5. RTX 4070 / memory evidence

| Field | Prompt-only control | Source-anchored |
|---|---:|---:|
| GPU | NVIDIA GeForce RTX 4070 | NVIDIA GeForce RTX 4070 |
| VRAM total | `12282 MiB` | `12282 MiB` |
| Peak observed VRAM used | `11488 MiB` | `11449 MiB` |
| Minimum observed VRAM free | `525 MiB` | `564 MiB` |
| System RAM total | `68476002304 bytes` | `68476002304 bytes` |
| Peak Native working set | `39984459776 bytes` | `40173133824 bytes` |
| Samples | `28` | `17` |
| OOM | `0` | `0` |
| Accepted-job retry | `0` | `0` |

The pair was observed close to the 12GB boundary. In this matched pair the
source-anchored run did not exceed the prompt-only peak, but the result is not
a memory-stability matrix or a guarantee for other source sizes, prompts, or
runtime states. H2A's earlier text-only run observed `9736 MiB` peak used;
H2B observed higher absolute peaks for both the prompt-only control and the
anchored run. Because the matched prompt-only control reached `11488 MiB`,
this one pair does not isolate a source-conditioning-specific increase. The
accepted source-anchored job was submitted once, and the near-limit behavior
is retained as a limitation rather than hidden.

## 6. Verification and scope audit

- H2A adapter test: `python -m unittest h3.tests.test_h2a_still_adapter` —
  `4 tests, OK`.
- H2B adapter test: `python -m unittest h3.tests.test_h2b_source_anchored_still`
  — `5 tests, OK`.
- Full Python tests: `python -m unittest discover -s h3/tests -p 'test_*.py'`
  — `41 tests, OK`.
- H1C regression: `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- P2 regression: `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- H1B UI regression: `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- JavaScript syntax, Python `compileall`, and `git diff --check`: `PASS`.

No shared H3 adapter behavior was modified, so no real Video regression was
required by this Card. No new model, dependency, custom node, shared ComfyUI
change, or Manga change was made. No Still UI, ordered multi-reference,
REF2VA, source-fidelity control, or external Studio integration was started.

## 7. Report and evidence

Report: `docs/h3/reports/H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md`

Evidence README: `docs/h3/evidence/h2b-source-anchor/2026-09-10/README.md`

Manifest: `docs/h3/evidence/h2b-source-anchor/2026-09-10/manifest.json`

Source: `docs/h3/evidence/h2b-source-anchor/2026-09-10/source.png`

Prompt-only output: `docs/h3/evidence/h2b-source-anchor/2026-09-10/prompt_only.png`

Anchored output: `docs/h3/evidence/h2b-source-anchor/2026-09-10/anchored.png`

## Final report format

```text
H2B SOURCE-ANCHORED STILL: PASS

Publication correction: PASS
H2A publication: PUBLISHED ON MAIN
H2B publication: PUBLISHED ON MAIN

Implementation commit:
8a6b74f4fef2c9437ce07dd8fb85eb85bcda5971

Evidence/docs commit:
828524e8700d4c36906e692e3153ed9e17772ee5

Selected anchor route:
one LoadImage source → first_frame → five-frame packet → selected frame 0

Classification:
SOURCE ANCHOR FEASIBLE WITH LIMITS

Source SHA-256:
43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E

Prompt-only output SHA-256:
A1485D07555F756CE7810341E29C082BD383C013153F1F489C4482D3341539FB

Anchored output SHA-256:
1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5

Source influence:
PASS

Resolution:
608x352

Seed:
20260910

Steps:
20

Elapsed:
prompt-only 52.27s; anchored 29.34s

Peak VRAM:
prompt-only 11488 MiB; anchored 11449 MiB

Peak RAM:
prompt-only 39984459776 bytes; anchored 40173133824 bytes Native working set

OOM:
0

Retries:
0

H2A regression:
PASS

H1C regression:
PASS

P2 regression:
PASS

Workflow changes:
one H3-only H2B source-anchor workflow

Model changes:
NONE

Dependency changes:
NONE

Shared ComfyUI changes:
NONE

Manga changes:
NONE

Report:
docs/h3/reports/H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md

Evidence:
docs/h3/evidence/h2b-source-anchor/2026-09-10/

Recommended next direction:
1. Still UI vertical slice

Owner acceptance:
PENDING

STOP
```

After success, STOP. Ordered multi-reference, REF2VA, Still UI, Manga,
H3→Illustrious, Timeline, and Studio remain outside this Card.
