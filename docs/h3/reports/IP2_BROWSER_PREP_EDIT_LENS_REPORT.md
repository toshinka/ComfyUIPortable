# TEGAKI MiniMax H3 IP2-R1B — Experimental Browser Prep/Edit Lens

Evidence date: `2026-09-11 JST`

Current stage: `IP2 / Experimental Browser Prep/Edit Lens`

Classification: **PASS WITH KNOWN NATIVE LIMIT**

Initial public main at acceptance: `f8dd087a1946da80cf070eda4bb137fc1408d085`

IP2 implementation: **PUBLISHED ON MAIN**. The implementation and the latest
server consistency correction were already present in the live main history.
The current main also contains concurrent Manga development history; this
closeout does not rewrite or extract that history.

Owner acceptance: `PENDING`

Publication: **PUBLISHED ON MAIN** after the bounded H3-only closeout push.
The exact final remote tip is reported with the publication check for this
package.

## 1. Decision

The real rendered Browser path at `http://127.0.0.1:8190/` accepted one
authorized Source image and one authorized Donor image without any `file://`
permission expansion. It completed exactly one Source-only Prep generation and
exactly one Source + Donor Prep generation. Preview, public History labeling,
History `Use settings`, `Edit in Prep`, `Use as Character`, and the bounded
mode-isolation checks passed without extra generation.

The result is a bounded experimental lens over the existing IP1 Native
Image Prep route. Source preservation was strong and the requested rainy
environment change was observed. The donor yellow raincoat influence was not
convincing, so donor attribute isolation remains **NOT GUARANTEED**. This is a
known Native limitation and is not a reason to run an aesthetic retry.

## 2. Scope and implementation boundary

IP2 uses the existing H3 Native `MiniMaxH3ReferenceToVideo` route through the
published IP1 adapter. The browser surface is limited to:

```text
Prep/Edit: one required Source image plus one optional Donor image
Source role: subject and composition reference
Donor role: requested attribute reference only
Canvas: 608 x 352
Steps: 20
Native temporal packet: 5 frames at 24 fps
Output: decoded frame 0 as PNG
Route: native_image_prep
```

The user prompt is kept separate from deterministic Picture-role materialization:

```text
Source-only prefix:
Use <Picture 1> as the source subject and composition reference. Preserve its recognizable identity and general framing.

Source + Donor prefix:
Use <Picture 1> as the source subject and composition reference. Preserve its recognizable identity and general framing.
Use <Picture 2> only as the donor for the requested attribute. Do not replace the whole scene.
```

No strength slider, identity lock, masked editing, LoRA, T=1 diffusion route,
semantic multi-reference list, Qwen Image Edit route, Image Studio, audio
conditioning, production MP4, or Manga change was introduced or inferred.

## 3. Runtime acceptance setup

The H3 skin on port `8190` stayed running throughout the correction and Browser
acceptance. The first attempted submission returned HTTP 400 before a job was
submitted because the old port `8188` process was a plain shared ComfyUI launch:

```text
input resolution: default ComfyUI input root, not output/h3
VAE name mismatch: bare minimax_h3_audio_vae_fp32.safetensors was not in that process list
job submitted: NO
output created: NO
counted generation: NO
```

Only that stale `8188` backend was stopped. It was replaced with the already
canonical isolated launcher contract from `h3/run_h3.bat`, using the H3 input
and output root, the local extra-model-paths file, disabled custom nodes, and
isolated user/temp/database locations. The existing in-memory Source selection
was preserved and the corrected backend exposed the expected bare VAE name.
This was acceptance runtime setup, not a tracked product or workflow change.
No Browser restart, file-scheme permission, or external upload was used.

## 4. Authorized files and interaction

### Source

```text
file: D:/GitHub/tegaki/ComfyUIPortable/output/h3/tests/reference_robot_v1.png
sha256: 43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E
bytes: 206821
dimensions: 608 x 352 PNG
selection: DIRECT FILE INPUT
accepted selections: 1
```

The Source thumbnail and name were visible in the Prep Source slot. Donor
remained empty during the Source-only run. The public asset used an opaque
server-issued ID and exposed no local path.

### Donor

The authorized original was present and hash-verified:

```text
original: D:/GitHub/tegaki/ComfyUIPortable/output/h3/still/h2a_native_still_00004_.png
sha256: 4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0
bytes: 193442
dimensions: 608 x 352 PNG
```

The first original-path browser fetch attempts were rejected by the Browser
harness with `Failed to fetch`; no accepted server Donor asset was created and
no generation was run. To continue within the authorized local-only scope, an
exact-content, non-destructive copy was placed at:

```text
final selection: D:/GitHub/tegaki/ComfyUIPortable/output/h3/tests/ip2_donor_4338866a.png
sha256: 4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0
bytes: 193442
selection: DIRECT FILE INPUT
accepted selections: 1
```

The copy is a runtime artifact under ignored `output/h3`; the original remained
unchanged. The rendered UI showed Source and Donor as separate slots, marked
Donor `Experimental`, with Replace and Remove controls and no filesystem path.
No fake strength control was present.

## 5. Source-only Browser generation

| Field | Result |
|---|---|
| Browser route | `Prep · Source` |
| H3 job ID | `0ff31f0035564c289fd396b77d98980e` |
| Native prompt ID | `0c9b7097-e63a-4d40-a58d-5b097ca07fe5` |
| Seed | `20260911` |
| Prompt | `Keep the recognizable red-and-white robot. Change the environment to a rainy outdoor scene with wet surfaces and visible rainfall.` |
| Elapsed | `136.17 s` |
| Output | `output/h3/still/ip1_native_image_prep_00004_.png` |
| Output SHA-256 | `78E35745D3E5379E12DA8B0177AAEA0B556245E43FA5B58EF4E7D55A68789A64` |
| Output | `242027 bytes`, `608 x 352 PNG` |
| Preview | PASS |
| History | PASS — `Prep · Source`, user prompt retained, materialized prompt separate |
| Source preservation | **STRONG** |
| Requested change | **OBSERVED** |
| Drift | **MODERATE** |

The red-and-white robot remained recognizable. Rain, an outdoor environment, wet
surfaces, and visible rainfall were present. The crop and environment changed
enough to record moderate drift. The generated result was reviewed locally with
`view_image`; no retry was run.

The public History record kept the user prompt and stored this materialized
prompt separately:

```text
Use <Picture 1> as the source subject and composition reference. Preserve its recognizable identity and general framing.
Keep the recognizable red-and-white robot. Change the environment to a rainy outdoor scene with wet surfaces and visible rainfall.
```

## 6. Source + Donor Browser generation

| Field | Result |
|---|---|
| Browser route | `Prep · Source + Donor` |
| H3 job ID | `845c3088cf3d4a2b9b4451fd195e59a5` |
| Native prompt ID | `8dd5de78-a615-4db6-9579-964bc5c29ed9` |
| Seed | `20260912` |
| Prompt | `Keep the recognizable source robot. Use the donor only for the bright yellow raincoat / protective-coat appearance.` |
| Elapsed | `41.15 s` |
| Output | `output/h3/still/ip1_native_image_prep_00005_.png` |
| Output SHA-256 | `FA299AC1077F0B0C003D18FD1A5C211DBC98CD0F065AD179496AD9B7C9DADB85` |
| Output | `291346 bytes`, `608 x 352 PNG` |
| Preview | PASS |
| History | PASS — `Prep · Source + Donor`, user prompt retained, materialized prompt separate |
| Source preservation | **STRONG** |
| Donor influence | **NOT CONVINCING** |
| Donor over-transfer | **LOW** |
| Composition drift | **LOW** |
| Donor attribute isolation | **NOT GUARANTEED** |

The output remained close to the Source robot and composition, but the bright
yellow raincoat attribute was not convincingly transferred. The Donor was not
silently ignored at the route level: public History recorded both opaque asset
IDs and the `Prep · Source + Donor` route, and the separate Donor remained
selected in the UI. The visual result nevertheless does not establish
attribute-isolated editing. No retry was run.

The public materialized prompt was:

```text
Use <Picture 1> as the source subject and composition reference. Preserve its recognizable identity and general framing.
Use <Picture 2> only as the donor for the requested attribute. Do not replace the whole scene.
Keep the recognizable source robot. Use the donor only for the bright yellow raincoat / protective-coat appearance.
```

## 7. Browser handoff and state acceptance

| Check | Result |
|---|---|
| Source selection exactly once | PASS |
| Donor selection exactly once | PASS — final accepted input was the hash-matched copy |
| Source and Donor slot separation | PASS |
| Donor Experimental warning | PASS |
| Preview for both results | PASS |
| History route labels | PASS — `Prep · Source` and `Prep · Source + Donor` |
| History `Use settings` Source-only | PASS — restored Source, empty Donor, prompt, seed `20260911` |
| History `Use settings` Source + Donor | PASS — restored both assets, prompt, seed `20260912` |
| `Edit in Prep` | PASS — completed result became Prep Source; no automatic generation |
| Prompt copy guard | PASS — sentinel prompt remained instead of source-generation prompt |
| `Use as Character` | PASS — Video switched to `Reference · Experimental` and promoted `Generated Still` |
| Handoff auto-generation | **NONE** |
| Public filesystem paths | **NONE** |
| File-scheme permission | **NO change** |
| Total real Prep generations | **2** |

`Use as Character` performed no R2V generation. The Video mode showed the
promoted generated still in the Character Image slot, with Reference selected
and Standard unselected. The Source + Donor result remained available through
the same-session History path.

## 8. Mode isolation

No generation was run during these checks:

| Transition | Result |
|---|---|
| `Video → Prep/Edit → Video` | PASS — Reference Experimental and Generated Still Character Image preserved |
| `Still → Prep/Edit → Still` | PASS — Still prompt sentinel and seed `20260913` preserved |
| `Prep/Edit → other lens → Prep/Edit` | PASS — current Prep prompt, Source, and Donor remained valid |

The final Browser state remained in Prep/Edit with the valid Source and Donor
assets selected. No extra Still, Standard Video, Reference Video, or Prep
generation was used for state inspection.

## 9. Telemetry

The Browser acceptance route did not have a native VRAM sampler attached to the
run. The recorded status observations are therefore bounded samples, not peak
or minimum profiler values:

| Run / field | Recorded value |
|---|---|
| Source-only H3 job | `0ff31f0035564c289fd396b77d98980e` |
| Source + Donor H3 job | `845c3088cf3d4a2b9b4451fd195e59a5` |
| Sample interval | Browser UI polling and post-run `/api/status`; exact native sampler not instrumented |
| Peak observed VRAM | `NOT INSTRUMENTED` |
| Minimum observed free VRAM | `NOT INSTRUMENTED` |
| Post-run free VRAM sample | approximately `639959080` bytes |
| Total VRAM sample | approximately `12878086144` bytes |
| Additional post-Source free sample | approximately `626098216` bytes |
| OOM | `0` |
| Accepted-job retry | `0` |

No memory optimization, offload change, or quality retry was introduced. The
absence of peak/minimum values is explicit and does not get promoted to a
performance claim.

## 10. Verification and regression

```text
IP2 targeted Python: 27 PASS
IP2 UI verifier: 45 PASS
IP1 targeted Python: included in targeted set; PASS
VP2C UI: 36 PASS
VP2B UI: 28 PASS
H2C UI: 52 PASS
H1C UI: 38 PASS
H1B.1 P2 UI: 44 PASS
H1B.1 P1 UI: 36 PASS
VP1 UI: PASS
Full H3 Python discovery: 75 PASS
JavaScript syntax: PASS
Python compileall: PASS
Workflow JSON parse: 7 PASS
git diff --check: PASS
```

The targeted Python command ran the IP2, IP1, VP2C, VP2B, and H2C modules and
reported `Ran 27 tests ... OK`. Full H3 discovery reported
`Ran 75 tests ... OK`. No additional Browser generation was used for the
regression set.

## 11. Publication and closeout boundary

This package contains only the bounded H3 canonical correction, report, dated
evidence README, and machine-readable manifest. No generated PNG, runtime copy,
model, cache, local YAML, temporary harness, or Manga file is committed.

The live baseline used for reconciliation was:

```text
HEAD before closeout:       f8dd087a1946da80cf070eda4bb137fc1408d085
origin/main before closeout: f8dd087a1946da80cf070eda4bb137fc1408d085
```

The IP2 implementation is described neutrally as present in published main
history. This closeout is a new bounded H3-only descendant; it does not claim
that the original implementation entered GitHub as a clean H3-only commit.

Final report fields:

```text
IP2 EXPERIMENTAL BROWSER PREP/EDIT: PASS WITH KNOWN NATIVE LIMIT
Initial public main: f8dd087a1946da80cf070eda4bb137fc1408d085
IP2 implementation: PUBLISHED ON MAIN
Chrome file:// access enabled: NO
Source upload: PASS
Source interaction: DIRECT INPUT
Source-only generation: PASS
Donor upload: PASS
Donor interaction: DIRECT INPUT
Source + Donor generation: PASS
Generation count: 2
Edit in Prep: PASS
Use as Character: PASS
Handoff auto-generation: NONE
Mode isolation: PASS
Public filesystem paths: NONE
Manga changes in final closeout: NONE
Owner acceptance: PENDING
```

STOP after the authorized two-generation Browser acceptance budget.
