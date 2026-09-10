# IP1 — Native Image Prep / Reference Edit Feasibility evidence

Evidence date: `2026-09-11 JST`

Classification: `FEASIBLE WITH LIMITS`

Recommendation: `IP2 Browser Prep/Edit lens` — not implemented in this Card.

Owner acceptance: `PENDING`

Publication: `LOCAL` until the bounded IP1 commit is pushed and checked on
GitHub `main`.

Report: [IP1_NATIVE_IMAGE_PREP_REFERENCE_EDIT_FEASIBILITY_REPORT.md](../../../reports/IP1_NATIVE_IMAGE_PREP_REFERENCE_EDIT_FEASIBILITY_REPORT.md)

Manifest: [manifest.json](manifest.json)

## Scope

This package records the current installed Native H3 Ref2VA stack only. No
Browser UI, Browser generation, new model, LoRA, Turbo/Fast variant, quantized
replacement, custom node, shared ComfyUI change, Manga change, or production
MP4 was used. The new route emits a PNG selected from decoded frame `0` of one
Native five-frame temporal packet.

The Native source audit covered `ComfyUI/comfy_extras/nodes_minimax_h3.py`,
`MiniMaxH3ReferenceToVideo`, and its current `ref_images` contract. The node
accepts ordered image references through the autogrow `ref_image_` inputs; one
source and one optional donor are materialized as `<Picture 1>` and
`<Picture 2>`. Video and audio reference lanes remain absent.

## Authorized local inputs

Source was the existing local H3 image:

```text
role: source
path: output/h3/tests/reference_robot_v1.png
sha256: 43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E
bytes: 206821
format: PNG / 608x352
external upload: NONE
```

No suitable single-image donor existed in the inspected local candidates. One
prompt-only H2A Still donor was therefore generated exactly once, with the
existing FL2VA route and no Browser UI:

```text
prompt: A single small service robot wearing a bright yellow raincoat or protective coat stands centered on a simple pale blue studio background, clean illustrative H3 still, soft daylight, full subject visible.
route: native_still
prompt_id: c91ddfe8-cb01-44a2-bb1f-99b102019a5b
seed: 20260911
steps: 20
elapsed_seconds: 110.68
output: output/h3/still/h2a_native_still_00004_.png
sha256: 4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0
bytes: 193442
format: PNG / 608x352
```

The donor is used only as the optional Picture 2 attribute source in Case B.
The source and donor remain runtime-only files and are not committed.

## Native IP1 cases

All three edit cases used the same Native Ref2VA model, source, `608x352`,
`20` steps, seed `20260911`, 24 fps basis, five-frame packet, and decoded frame
0. Each accepted output is a PNG from `SaveImage`; no video container was
created.

| Case | References | Result | Output | Elapsed | Peak observed VRAM / minimum free | OOM / retry |
|---|---|---|---|---:|---:|---:|
| A | Picture 1 source | rain environment observed; source identity strong; composition drift moderate | `ip1_native_image_prep_00001_.png` / `84CE9C5B0EC07EFA24CAE3A604144E7EF38ACAB64E677AC6DAE1B32042B9E5AF` | 99.25 s | 11748 / 265 MiB | 0 / 0 |
| B | Picture 1 source + Picture 2 donor | donor influence strong; source preservation weak; over-transfer and composition drift high | `ip1_native_image_prep_00002_.png` / `CD09680F816482B009D3F6C2CFBB8DC348845B9D5BE8B384E07934F57070800B` | 24.98 s | 11759 / 254 MiB | 0 / 0 |
| C | Picture 1 source | mild three-quarter angle and raised arm observed; source identity strong; structural drift moderate | `ip1_native_image_prep_00003_.png` / `B6E04D7A43C98C2850692A01D0F8E80DDD6470C1CD5DEC836AFE6E22D6FFB32D` | 18.69 s | 11676 / 337 MiB | 0 / 0 |

The VRAM values are sampled observations, not exact profiler traces. The full
per-case sample count, system RAM total, Native process working set, prompt
IDs, output bytes, and frame-selection record are in `manifest.json`.

## Visual review boundary

Visual review was performed side-by-side against the local source and the one
local donor. The review records source preservation, requested attribute or
environment observation, donor influence, and drift only; it is not an
aesthetic score. No three-view consistency, turnaround, pixel preservation,
masked edit, region lock, or identity lock claim is made.

## Verification

```text
Native source audit: PASS
IP1 targeted contract tests: 7 PASS
Native IP1 runtime cases: 3 PASS
donor generation: 1 PASS / 1 allowed
Browser UI: NOT RUN / NOT IMPLEMENTED
Owner acceptance: PENDING
```

The next route is recorded only as a recommendation. This Card stops after
the IP1 evidence package and does not start IP2 or an Image Studio audit.
