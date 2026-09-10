# TEGAKI MiniMax H3 IP1 — Native Image Prep / Reference Edit Feasibility Report

Evidence date: `2026-09-11 JST`

Classification: **FEASIBLE WITH LIMITS**

Recommendation: **IP2 Browser Prep/Edit lens**

Owner acceptance: `PENDING`

Publication: `LOCAL` until the bounded IP1 commit is pushed and checked on
GitHub `main`.

## 1. Decision summary

The current installed Native H3 stack can materialize a bounded reference-
guided Still path with one required source Picture and one optional donor
Picture. The Native API accepted both image-reference forms, preserved the
deterministic Picture roles, produced the required five-frame temporal packet,
decoded it through the video VAE, and emitted the selected decoded frame 0 as a
PNG. All three edit cases completed at the fixed `608 x 352 / 20 steps / seed
20260911` baseline with `OOM 0 / retry 0`.

Source-only environment and mild pose/angle changes were observed while the
source robot remained recognizable. The source-plus-donor case transferred the
yellow raincoat attribute strongly, but also transferred the donor's whole
subject/studio composition and weakened source preservation. Therefore the
stack is technically useful for a narrow feasibility path, but it does not
provide isolated donor-attribute control.

The next recommendation is one bounded future Card: **IP2 Browser Prep/Edit
lens**. It is not implemented here. This Card stops after IP1 evidence and does
not start IP2 or a dedicated Image Studio audit.

## 2. Scope and authority

The initial document correction recorded Rev.4 as `PUBLISHED ON MAIN` at
`3880534af0e26b970a8fd0a1ba564af6bc88c15e`. The current `origin/main` is the
later Manga-only descendant `df0ad3b389db5149e1b6ab1edb24c568c147a10e`.
Unrelated Manga working-tree artifacts were preserved and were not staged or
edited.

This Card used only the installed external H3 model library selected by
`h3/config/extra_model_paths.local.yaml`:

```text
model:       minimax_h3_ref2va_pruned_int8_convrot.safetensors
text encoder: qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
video VAE:   minimax_h3_video_vae_fp16.safetensors
audio VAE:   minimax_h3_audio_vae_fp32.safetensors (required Native input)
```

No new model, VAE, text encoder, LoRA, Turbo/Fast variant, GGUF/Qwen Image
Edit asset, quantization change, offload change, custom node, shared ComfyUI
change, Manga change, Browser UI change, or production MP4 was introduced.
No LoRA was loaded. The Native process was isolated on `127.0.0.1:8189` with
all custom nodes disabled; the Browser skin was not started or called.

## 3. Native `MiniMaxH3ReferenceToVideo` audit

The audited source is
`ComfyUI/comfy_extras/nodes_minimax_h3.py`, class
`MiniMaxH3ReferenceToVideo`, source lines `154-280` at SHA-256
`49B2CBEA340E5588452BA9BFA84EB17FF7D8B76B4EFE992CC2766B6983A5F66E`.

| Contract item | Current Native observation | IP1 decision |
|---|---|---|
| Image reference count | `ref_images` is an ordered autogrow `ref_image_` lane with max 9 | Materialize exactly one source or two source-plus-donor images |
| Ordering and labels | image mapping values are encoded in mapping order; Picture ordinals are 1-based | `Picture 1=source`, `Picture 2=optional donor attribute` |
| Picture prompt roles | Native prompt presentation uses `<Picture i>` | Deterministic role prefix; no LLM rewrite |
| Canvas | `608 x 352` fixed for this Card | Reject other dimensions |
| `ref_image_size` | `match` is supported and retained | Keep `match` |
| Length | Native minimum 5 and `17n+5` temporal grid | Use exactly `length=5` |
| Latent/output shape | `length=5` creates a five-frame packet and video latent temporal dimension 2 | Decode the packet; do not claim single-frame diffusion |
| Decode and selection | `VAEDecode` → `ImageFromBatch(batch_index=0,length=1)` | Save only decoded frame 0 as PNG |
| Video references | Separate `ref_videos` lane exists | Not materialized; rejected by IP1 input validation |
| Audio references | Separate `ref_video_audios` / `ref_audios` lanes exist | Not materialized; audio reference is disconnected |
| Audio VAE | Required by the Native node signature | Loaded only for the required node input; no audio reference or audio output edge |

The audit passes. A shared core change or custom node was not required. The
result remains a current-stack Native Ref2VA reference-guided Still behavior
test, not a promise of a stronger image-edit primitive.

## 4. Bounded implementation

IP1 adds one separate Native-only adapter and one separate graph:

```text
h3/adapters/native_image_prep.py
workflows/h3/IP1_NATIVE_IMAGE_PREP_BASE.json
h3/tests/run_ip1_image_prep.py
h3/tests/test_ip1_native_image_prep.py
```

The existing `h3/adapters/native_ref2va.py` and the VP2B Browser route are
unchanged. The adapter accepts only a server-staged `inputs/<filename>` path
with PNG/JPEG/WebP suffix, rejects absolute paths, traversal, local drive or
remote URLs, and rejects video, audio, third, and fourth reference lanes. It
does not expose a generic multi-reference list.

The materialized graph is:

```text
Picture 1 source (+ optional Picture 2 donor)
  -> MiniMaxH3ReferenceToVideo (608x352, length=5, ref_image_size=match)
  -> Native sampler (20 steps)
  -> VAEDecode video samples
  -> ImageFromBatch batch_index=0 length=1
  -> SaveImage PNG
```

The graph contains no `SaveVideo`, `CreateVideo`, `VAEDecodeAudio`,
`LoadVideo`, or `GetVideoComponents` node. It is a five-frame packet followed
by decoded frame-0 selection, not a `T=1` diffusion graph.

## 5. Inputs and runtime method

The source was the existing local H3 image:

```text
output/h3/tests/reference_robot_v1.png
PNG / 608x352 / 206821 bytes
sha256: 43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E
```

Inspected local candidates were either source duplicates or multi-frame contact
sheets, so no suitable single donor existed. Exactly one donor was generated
using the existing H2A prompt-only Still route:

```text
prompt: A single small service robot wearing a bright yellow raincoat or protective coat stands centered on a simple pale blue studio background, clean illustrative H3 still, soft daylight, full subject visible.
route: native_still
prompt_id: c91ddfe8-cb01-44a2-bb1f-99b102019a5b
seed: 20260911 / steps: 20 / elapsed: 110.68 s
output: output/h3/still/h2a_native_still_00004_.png
PNG / 608x352 / 193442 bytes
sha256: 4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0
```

The donor was not externally uploaded and remains an uncommitted runtime
asset. The three edit cases used the same source, same donor where applicable,
same seed, same dimensions, same step count, same five-frame packet, and same
frame-0 selection.

## 6. Runtime results

### 6.1 Per-case result

| Case | Request | References | Output / SHA-256 | Elapsed | Runtime result |
|---|---|---|---|---:|---|
| A | Source-only environment/weather edit: rainy outdoor setting, wet surfaces, rainfall | Picture 1 source | `output/h3/still/ip1_native_image_prep_00001_.png` / `84CE9C5B0EC07EFA24CAE3A604144E7EF38ACAB64E677AC6DAE1B32042B9E5AF` | 99.25 s | PNG `608x352`; OOM 0; retry 0 |
| B | Source plus one donor attribute: bright yellow raincoat/protective-coat material and color | Picture 1 source + Picture 2 donor | `output/h3/still/ip1_native_image_prep_00002_.png` / `CD09680F816482B009D3F6C2CFBB8DC348845B9D5BE8B384E07934F57070800B` | 24.98 s | PNG `608x352`; OOM 0; retry 0 |
| C | Source-only mild three-quarter angle and one raised arm | Picture 1 source | `output/h3/still/ip1_native_image_prep_00003_.png` / `B6E04D7A43C98C2850692A01D0F8E80DDD6470C1CD5DEC836AFE6E22D6FFB32D` | 18.69 s | PNG `608x352`; OOM 0; retry 0 |

For every row the evidence identifies `Native 5-frame temporal packet` →
`VAEDecode node 122` → `ImageFromBatch node 132, batch_index 0, length 1` →
`SaveImage PNG`. No production MP4 was created.

### 6.2 Telemetry

Telemetry used the existing `nvidia-smi` GPU query and `psutil` Native process
sampling method. The interval was approximately 2 seconds; values are sampled
observations, not exact profiler traces. System RAM total was
`68,476,002,304` bytes for each run.

| Run | GPU / total VRAM | Peak observed used | Minimum observed free | Peak Native working set | Samples |
|---|---|---:|---:|---:|---:|
| Donor H2A | RTX 4070 / 12282 MiB | 11743 MiB | 270 MiB | 31249317888 bytes | 56 |
| A | RTX 4070 / 12282 MiB | 11748 MiB | 265 MiB | 38368489472 bytes | 51 |
| B | RTX 4070 / 12282 MiB | 11759 MiB | 254 MiB | 43360518144 bytes | 15 |
| C | RTX 4070 / 12282 MiB | 11676 MiB | 337 MiB | 43559407616 bytes | 12 |

No OOM or accepted-job retry occurred. No DynamicVRAM/SageAttention/GGUF,
Turbo/Fast H3, quantization, or new offload setting was introduced by this
Card. The process was cleanly stopped after the local runs.

## 7. Visual review

The source, donor, and three outputs were reviewed side-by-side locally. This
is a behavior review, not an aesthetic rating.

### Case A — source-only environment edit

```text
source preservation: STRONG
requested environment: OBSERVED
drift: MODERATE
```

The red-and-white robot design remained recognizable and the rain, outdoor
setting, wet surface, and rainfall were visible. The generated crop and
environment differed from the source framing, so drift is recorded as moderate.

### Case B — source plus one donor attribute

```text
source preservation: WEAK
donor influence: STRONG
over-transfer: HIGH
composition drift: HIGH
```

The bright yellow raincoat donor attribute was clearly transferred. However,
the output also followed the donor's whole yellow subject/studio composition;
the source red-and-white robot and original composition were not preserved
strongly. This is the decisive limit on donor-based attribute editing in the
current stack.

### Case C — bounded angle and pose change

```text
source preservation: STRONG
requested angle: OBSERVED
requested pose: OBSERVED
structural drift: MODERATE
```

The red-and-white robot remained recognizable. A mild three-quarter view and a
raised arm were visible. The new arm, crop, and angle caused moderate structural
change. This is not evidence of three-view consistency or a turnaround.

## 8. Verification

```text
Native source audit: PASS
IP1 targeted contract tests: 7 PASS
IP1 Native runtime cases: 3 PASS
Allowed donor generation: 1/1 PASS
Browser UI: NOT RUN / NOT IMPLEMENTED
VP2B adapter and route: unchanged; targeted preservation test PASS
H3 Python regression: 14 test files / 72 PASS
H2A targeted regression: 4 PASS
H2B targeted regression: 5 PASS
VP2B targeted regression: 5 PASS
VP2C targeted regression: 5 PASS
Python compileall: PASS
Workflow JSON parse: 7 PASS
git diff --check: PASS
```

The targeted tests cover one source, optional donor, deterministic Picture
roles, third/fourth rejection, video/audio rejection, traversal/absolute/
remote rejection, fixed dimensions/steps/length/fps, frame-0 output, and
preservation of the VP2B Ref2VA contract. The full H3 run covered all 14
existing and IP1 Python test files without adding any runtime generation.

## 9. Explicit non-claims and boundaries

This report describes current-stack Native Ref2VA reference-guided Still
behavior only. It does **not** claim:

- pixel-preserving editing;
- masked editing, region lock, spatial hard binding, or identity lock;
- three-view, turnaround, or multi-view consistency;
- `T=1` single-frame diffusion;
- a dedicated Image Studio;
- multi-character R2V;
- audio or video reference conditioning in IP1;
- Browser Prep/Edit UI or production deployment;
- LoRA compatibility, an acceleration track, or a model selector.

LoRA status is unchanged. Multi-character R2V remains not implemented. Browser
Prep/Edit remains not implemented. Existing VP2B and VP2C behavior was not
expanded.

## 10. Final status

```text
IP1 Native Image Prep / Reference Edit Feasibility:
FEASIBLE WITH LIMITS

Recommendation:
IP2 Browser Prep/Edit lens

Browser Prep/Edit UI:
NOT IMPLEMENTED

LoRA:
UNCHANGED

Multi-character R2V:
NOT IMPLEMENTED

Owner acceptance:
PENDING

Publication:
LOCAL — Owner push and remote verification remain separate from local PASS

STOP
```
