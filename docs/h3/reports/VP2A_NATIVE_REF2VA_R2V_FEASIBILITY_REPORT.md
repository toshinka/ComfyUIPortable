# VP2A — Native Ref2VA / R2V Feasibility

Date: 2026-09-10 JST

Current Stage: `VP2A / Native Ref2VA / R2V Feasibility`

VP2A classification: `ACQUISITION REQUIRED`

VP1 publication correction: `PASS` — the supplied publication commit is
`41da0bf804d049adc40e2ae2d5abfdd59eabc703`, matching the current local
`origin/main` tracking ref. A live external `git ls-remote` check was attempted
but was unavailable in this run because the GitHub connection failed; this
report does not turn that failed fetch into a separate public-verification
claim.

Base remote: `41da0bf804d049adc40e2ae2d5abfdd59eabc703`

Implementation commit: `NONE`

Evidence/docs commit: `NONE` (this package is local and push-pending)

Owner acceptance: `PENDING`

## 1. Outcome

VP2A stopped at the mandatory acquisition and license gate, before any model
download, adapter implementation, workflow execution, or Browser work. The
exact Ref2VA artifact is absent from the approved external H3 model locations
and from the Portable model namespaces. The local H0/H0.1 records explicitly
deferred Ref2VA and do not record exact Owner authorization for acquiring or
using this artifact.

The correct result is `ACQUISITION REQUIRED`, not an implementation failure and
not a 12GB runtime failure. No current FL2VA/T2V model was reinterpreted as
Ref2VA.

## 2. Exact acquisition gate

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

## 3. Native source contract audit

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

## 4. Picture and Video feasibility stages

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

## 5. 12GB runtime and model transition

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

## 6. Browser, regression, and artifact boundary

- Browser R2V UI: `NOT IMPLEMENTED`.
- Existing Video and Still UI: unchanged by VP2A.
- H1B.1 Start/End FL2VA semantics: unchanged.
- No adapter, workflow, model, MP4, reference video, or runtime input was added.
- The old Browser generation suites were not repeated because no Browser code
  or runtime path changed. The prior VP1/H2C evidence remains separate.
- Docs-only validation for this package is limited to JSON parsing and
  `git diff --check`; it is not a replacement for future Native generation,
  Browser evidence, visual review, publication, or Owner acceptance.

## 7. Required Owner action and stop

Owner action is required for the exact artifact below before work can continue:

1. Confirm that acquisition and local use of the MiniMax H3 Community License
   apply to this exact Ref2VA file and intended territory/use.
2. Authorize or provision the official file at the canonical external path,
   with expected size `20,970,379,616` and SHA-256
   `9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779`.
3. After that action, rerun the exact-file check and begin Stage A only.

Until then:

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

