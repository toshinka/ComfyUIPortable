# VP2A — Native Ref2VA / R2V Feasibility

Date: 2026-09-10 JST

Current Stage: `VP2A / Native Ref2VA / R2V Feasibility`

VP2A classification: `FEASIBLE WITH LIMITS`

Previous acquisition-gate publication: `PUBLISHED ON MAIN` at
`e4e078490cd2f96a953e6261399f268652d49c04`

Owner acquisition authorization: `RECORDED` in the current Web-GPT handoff for
this exact artifact only. It does not authorize new third-party click-through
terms, gated-access agreements, or unrelated model licenses.

VP1 publication correction: `PASS` — the supplied publication commit is
`41da0bf804d049adc40e2ae2d5abfdd59eabc703`, and it remains an ancestor of the
current local `origin/main` at `e4e078490cd2f96a953e6261399f268652d49c04`.
A live external `git ls-remote` check was attempted but was unavailable in
this run because the GitHub connection failed; this report does not turn that
failed fetch into a separate public-verification claim.

VP1 base remote: `41da0bf804d049adc40e2ae2d5abfdd59eabc703`
R1 base remote: `e4e078490cd2f96a953e6261399f268652d49c04`

Implementation commit: `NONE` (R1 adapter/workflow/runner are local and uncommitted)

Evidence/docs commit: `NONE` (R1 updates are local and push-pending)

Owner acceptance: `PENDING`

## 1. R1 result — acquisition resumed and Native feasibility completed

```text
VP2A-R1: FEASIBLE WITH LIMITS
Ref2VA model: ACQUIRED / SHA-256 VERIFIED / EXTERNAL STORE
Stage A Picture-only: VERIFIED LOCAL GENERATION
Stage B Picture + Video: VERIFIED LOCAL GENERATION
Standard FL2VA/T2V transition: BUILT-IN MODEL TRANSITION PASS
12GB runtime: VERIFIED, near VRAM boundary
Browser R2V UI: NOT IMPLEMENTED
Owner acceptance: PENDING
```

The Owner authorization recorded in the current Web-GPT handoff was applied
only to the exact Ref2VA artifact named below. No new license click-through,
gated agreement, credential, unrelated model, or third-party account action
was used. The file was downloaded once from the pinned official revision,
verified by exact byte count and SHA-256, and moved to the canonical external
H3 model directory. No model file, MP4, or runtime input is committed.

### R1 acquisition and runtime environment

| Item | Result |
|---|---|
| Official source | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3), pinned revision `a98869194787969724c7425d95d0ed73ce9202af` |
| Artifact | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| Expected / observed bytes | `20,970,379,616` / `20,970,379,616` |
| Expected / observed SHA-256 | `9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779` / exact match |
| Canonical external path | `E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| Download result | one official `curl` transfer, no transport retry; partial renamed only after verification |
| Native process | isolated ComfyUI on `127.0.0.1:8189`, PID `45540` |
| Runtime | ComfyUI `0.30.0`, embedded Python `3.13.14`, PyTorch `2.13.0+cu130` |
| GPU | NVIDIA GeForce RTX 4070, `12282 MiB` reported VRAM |
| Reference sizing | `ref_image_size=match` |

The tracked implementation is deliberately narrow: `h3/adapters/native_ref2va.py`,
`workflows/h3/VP2A_NATIVE_REF2VA_BASE.json`, and
`h3/tests/run_vp2a_ref2va.py`. It materializes the installed official
`MiniMaxH3ReferenceToVideo` node, one Picture lane, and optionally one Video
lane through built-in `LoadVideo` / `GetVideoComponents`. It does not widen
the production H3 UI, add a model selector, add Image Prep, LoRA, Manga, or a
model manager. The ComfyUI AutoGrow API required dotted dynamic-path keys
(`ref_images.ref_image_1` and `ref_videos.ref_video_1`); one preflight job
exposed this source/API normalization issue before sampling, with no OOM. The
final Stage A and Stage B jobs each used one accepted submission and
`accepted-job retry=0`.

### R1 source and matched-run contract

The Picture source was the existing local
`output/h3/tests/reference_robot_v1.png`, SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`.
The Video source was the existing verified local H1A baseline
`output/h3/video/h1a_native_t2v_00010_.mp4`, SHA-256
`412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254`,
ffprobe `608x352 / 124 frames / 24 fps / 5.167 s`. It was staged under the
isolated H3 `output/h3/inputs/` boundary; no external video was downloaded and
its audio stream was not connected as a reference.

All reference rows used `608x352`, Native length `124` frames, `24 fps`,
`5.0 s` user duration, `20 steps`, seed `20260910`, `res_multistep`,
`simple`, and the Ref2VA model above. The runner sampled telemetry every
approximately two seconds and recorded minimum free VRAM, peak used VRAM,
Native working set, elapsed time, OOM count, and retry count.

### Stage A — Picture-only

Prompt basis:

> Use `<Picture 1>` as the subject appearance reference. Preserve its
> recognizable small red service robot design, round white head, and dominant
> colors. Place the robot in a simple quiet workshop with warm daylight,
> walking slowly from left to right while the camera tracks gently.

| Field | Result |
|---|---|
| Prompt ID | `f201dc61-48ac-4ae4-be1c-59d4668e211d` |
| Output | `output/h3/video/vp2a_r1_ref2va_picture_00001_.mp4` |
| Output bytes / SHA-256 | `352,750` / `A3C4899BFDFA63084031D885B6EAA17B97149D108796638AC26E55CF6962202F` |
| ffprobe | `608x352 / 124 frames / 24 fps / 5.167 s` |
| Elapsed / telemetry samples | `238.09 s` / `118` |
| Peak VRAM / minimum free | `11669 MiB` / `344 MiB` |
| Peak Native working set | `44,376,182,784 bytes` |
| OOM / accepted-job retry | `0` / `0` |
| Visual result | `PICTURE REF INFLUENCE OBSERVED` |

The output visibly retained the source Picture's red compact body, round white
head, black face panel, and overall subject silhouette across the sampled
frames.

### Stage B — Picture + one Video

Matched prompt:

> Use `<Picture 1>` for the subject identity and appearance: preserve its
> recognizable small red service robot design, round white head, and dominant
> colors. Use `<Video 1>` for motion, timing, and camera behavior: follow its
> walking movement and gentle tracking rhythm. Place the robot in a simple
> quiet workshop with warm daylight.

| Field | Result |
|---|---|
| Prompt ID | `8a9d8a84-7c38-4bea-9e20-3038dbf738b0` |
| Output | `output/h3/video/vp2a_r1_ref2va_picture_video_00001_.mp4` |
| Output bytes / SHA-256 | `467,724` / `790392A527A4C13DF65092FB57887C31D386AF5F7A404F40A7AB3C1FC424851E` |
| ffprobe | `608x352 / 124 frames / 24 fps / 5.167 s` |
| Elapsed / telemetry samples | `375.46 s` / `185` |
| Peak VRAM / minimum free | `11678 MiB` / `335 MiB` |
| Peak Native working set | `45,711,646,720 bytes` |
| OOM / accepted-job retry | `0` / `0` |
| Picture visual result | `PICTURE REF INFLUENCE NOT CONVINCING` |
| Video visual result | `VIDEO REF INFLUENCE OBSERVED` |

The sampled output followed the supplied motion reference's orange robot and
greenhouse framing more than the supplied red Picture. This is recorded as a
reference-role limitation, not as a claim of identity preservation. The graph
connected only the Video frames to `ref_videos.ref_video_1`; no
`ref_video_audio_1` or standalone `ref_audio_1` was connected. Reference-video
audio was `NOT USED`; standalone audio was `NOT TESTED`.

### Standard FL2VA/T2V transition

After both Ref2VA stages passed technically, exactly one current standard H1A
FL2VA/T2V graph was submitted on the same isolated process at the same
`608x352 / 124 frames / 20 steps` baseline. It used the existing
`minimax_h3_fl2va_pruned_int8_convrot.safetensors` route and no model manager.

| Field | Result |
|---|---|
| Prompt ID | `1b457097-b2cc-4284-a89c-24aa971e0c67` |
| Output | `output/h3/video/vp2a_r1_transition_fl2va_00001_.mp4` |
| Output bytes / SHA-256 | `359,588` / `CF2E69472CA11EB03151DF1B725B0EF215CA5668271116E956AAA8ED8A8D1222` |
| ffprobe | `608x352 / 124 frames / 24 fps / 5.167 s` |
| Elapsed / telemetry samples | `175.99 s` / `88` |
| Peak VRAM / minimum free | `11657 MiB` / `356 MiB` |
| Peak Native working set | `46,405,963,776 bytes` |
| OOM / accepted-job retry | `0` / `0` |
| Transition classification | `BUILT-IN MODEL TRANSITION PASS` |

The transition completed without a restart, so the final classification is
`FEASIBLE WITH LIMITS`: the exact Native Ref2VA path and return to standard
FL2VA/T2V are technically feasible on this RTX 4070 12GB environment, but
headroom is only about `335–356 MiB` at the observed peaks, runtime is several
minutes per row, and the matched Picture+Video row did not preserve Picture
appearance convincingly.

### R1 verification and boundary

| Check | Result |
|---|---|
| VP1 verifier | `PASS` — Video config/history/Continue/Still isolation smoke |
| H2C verifier | `52 PASS` |
| H1C verifier | `38 PASS` |
| H1B.1 UX P2 verifier | `44 PASS` |
| H1B UI verifier | `36 PASS` |
| Embedded Python unittest discovery | `55 tests, OK` |
| JavaScript syntax | `PASS` for the five existing H3 static JS files |
| Embedded Python `compileall -q h3` | `PASS` |
| VP2A/workflow JSON parse | `PASS` |
| `git diff --check` | `PASS` (only normal LF→CRLF warnings) |

No Browser source changed, so the expensive Browser generation suites were not
rerun. No new dependency, custom node, shared ComfyUI change, Image Prep, LoRA,
Manga, or UI/Studio surface was added. The Native process was stopped after
the evidence run; port `8189` is no longer listening.

Recommended next direction: `Owner review of VP2A-R1 evidence and acceptance
decision`.

## 2. Historical acquisition-gate outcome

VP2A stopped at the mandatory acquisition and license gate, before any model
download, adapter implementation, workflow execution, or Browser work. The
exact Ref2VA artifact is absent from the approved external H3 model locations
and from the Portable model namespaces. The local H0/H0.1 records explicitly
deferred Ref2VA and do not record exact Owner authorization for acquiring or
using this artifact.

The correct result is `ACQUISITION REQUIRED`, not an implementation failure and
not a 12GB runtime failure. No current FL2VA/T2V model was reinterpreted as
Ref2VA.

## 3. Exact acquisition gate (historical snapshot)

| Field | Required value / result |
|---|---|
| Artifact | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| Role | Native MiniMax H3 Ref2VA / R2V diffusion model |
| Official source | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3), `diffusion_models/` |
| Model terms | MiniMax H3 Community License Agreement |
| Expected bytes | `20,970,379,616` |
| Expected SHA-256 | `9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779` |
| Canonical destination | `E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| External exact-file check | `NOT FOUND` |
| Portable exact-file check | `NOT FOUND` in `h3/model_store/` and `ComfyUI/models/` |
| License / authorization | `OWNER ACTION REQUIRED`; exact Ref2VA authorization is not recorded |

The H0.1 acquisition manifest records only the first-wave FL2VA/T2V-I2V
assets and says that Ref2VA was deliberately deferred. It also records that
the MiniMax H3 Community License has territory, use, and redistribution
restrictions requiring Owner/legal review. Existing first-wave technical
acquisition evidence is not treated as authorization for this different
artifact.

No terms were clicked or accepted, no credentials were used, and no download
or replacement was attempted. The next authorized pass must verify the exact
official source revision, license applicability, available disk, byte count,
and SHA-256 before generation.

## 4. Native source contract audit

The installed Native source was inspected at
`ComfyUI/comfy_extras/nodes_minimax_h3.py`, lines 154–269. The source contains
`MiniMaxH3ReferenceToVideo`; this is a source-contract result only. Runtime
node listing, model loading, and generation were not attempted.

Supported schema inputs observed in the source:

| Input | Native contract |
|---|---|
| `clip`, `vae`, `audio_vae` | Required model/encoding inputs |
| `prompt` | Multiline, dynamic prompts; reference labels are `<Picture i>`, `<Video k>`, and `<Audio j>` |
| `width`, `height` | Integer canvas inputs; source defaults `1344 x 768` |
| `length` | Frame count at 24 fps; default `124`, minimum `5`, maximum `3600`, step `17` |
| `ref_image_size` | `match` or `max`; default `match` |
| `ref_images` | Optional AutoGrow `ref_image_`; declared range `0–9` |
| `ref_videos` | Optional AutoGrow `ref_video_`; declared range `0–3`; frame input at 24 fps, tooltip range 2–15 seconds |
| `ref_video_audios` | Optional AutoGrow `ref_video_audio_`; declared range `0–3`; paired by the same numeric suffix |
| `ref_audios` | Optional AutoGrow `ref_audio_`; declared range `0–3`; standalone audio |

The node returns positive conditioning and an AV latent. The source scales
Picture references down only: `match` uses the generation pixel area while
`max` uses the 2048-pixel reference short-edge limit. Video references are
canvas-adapted, capped to the output frame count, require at least five frames,
and are truncated to the Native `17n + 5` frame grid. Qwen receives sampled
video frames at 2 fps with timestamps. A same-index video soundtrack is encoded
only when its paired `ref_video_audio_N` input is connected; standalone audio
uses the separate `ref_audios` lane.

This contract confirms that Native Ref2VA is distinct from the existing H1B.1
Start/End FL2VA path. No `REFERENCE_ROLES` widening, Start Frame
reinterpretation, generic reference framework, or shared ComfyUI change was
made.

## 5. Picture and Video feasibility stages (historical snapshot)

### Stage A — Picture-only

`NOT TESTED`. The required Ref2VA model was not acquired, so no Picture-only
workflow was built or run. The intended safe baseline remains `608 x 352`,
approximately 5 seconds, 20 steps, 24 fps, one approved local robot Picture,
and `ref_image_size=match`; the requested prompt must explicitly assign
identity/appearance to `<Picture 1>`. No output MP4, qualitative influence
classification, seed record, elapsed time, VRAM sample, working-set sample,
or OOM/retry result exists.

### Stage B — Picture + one Video

`NOT TESTED`. Stage B is conditional on a technically complete Stage A and was
therefore not started. No reference video was downloaded or generated for this
gate, no reference-video audio was connected, and no Picture-vs-Picture+Video
matched comparison exists. No `VIDEO REF INFLUENCE OBSERVED` or
`VIDEO REF INFLUENCE NOT CONVINCING` classification is claimed.

## 6. 12GB runtime and model transition (historical snapshot)

| Qualification | Result |
|---|---|
| RTX 4070 12GB Picture-only baseline | `NOT TESTED — acquisition gate stopped first` |
| OOM count / retry count | `NOT RECORDED` / `NOT RECORDED` |
| Memory optimization or alternate runtime | `NOT USED` |
| Post-Ref2VA current T2V transition | `NOT TESTED` |
| Automatic model swap manager | `NOT ADDED` |

This pass does not classify the stack as `NATIVE REF2VA 12GB BLOCKED ON CURRENT
STACK`, because the model never reached the runtime. If the exact artifact is
authorized and acquired, the first run must use the safe baseline and stop on
repeated baseline OOM without introducing SageAttention, DynamicVRAM, GGUF,
FastH3, Turbo LoRA, or a new offload system.

## 7. Browser, regression, and artifact boundary (historical snapshot)

- Browser R2V UI: `NOT IMPLEMENTED`.
- Existing Video and Still UI: unchanged by VP2A.
- H1B.1 Start/End FL2VA semantics: unchanged.
- No adapter, workflow, model, MP4, reference video, or runtime input was added.
- The old Browser generation suites were not repeated because no Browser code
  or runtime path changed. The prior VP1/H2C evidence remains separate.
- Docs-only validation for this package is limited to JSON parsing and
  `git diff --check`; it is not a replacement for future Native generation,
  Browser evidence, visual review, publication, or Owner acceptance.

## 8. Required Owner action and stop (historical snapshot)

At the original acquisition gate, Owner action was required for the exact
artifact below before work could continue:

1. Confirm that acquisition and local use of the MiniMax H3 Community License
   apply to this exact Ref2VA file and intended territory/use.
2. Authorize or provision the official file at the canonical external path,
   with expected size `20,970,379,616` and SHA-256
   `9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779`.
3. After that action, rerun the exact-file check and begin Stage A only.

Historical gate state at that time:

```text
VP2A REF2VA / R2V FEASIBILITY: ACQUISITION REQUIRED
Native Ref2VA source: AUDITED
Ref2VA model: NOT ACQUIRED / NOT VERIFIED
Picture Ref: NOT TESTED
Video Ref: NOT TESTED
12GB runtime: NOT TESTED
Browser R2V: NOT IMPLEMENTED
Owner acceptance: PENDING
STOP BEFORE DOWNLOAD
```
