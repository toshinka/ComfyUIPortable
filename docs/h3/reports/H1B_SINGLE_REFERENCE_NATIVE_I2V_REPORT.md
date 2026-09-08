# H1B Single Reference / Native I2V Vertical Slice Report

更新: 2026-09-09 JST

Stage: `H1B`

Status: `IMPLEMENTED` / `VERIFIED LOCAL GENERATION` / `VERIFIED BROWSER UI GENERATION`

Implementation commit: `50573c57ec1fb4ea5858352f07f5332d50326f41`

Owner acceptance: `PENDING`

## 1. Outcome

H1B adds one bounded Native H3 Image-to-Video route beside the existing H1A
text-to-video route. The user can add one image as `Start Frame`, see its
thumbnail, replace it, remove it from the current UI request, and submit the
same prompt/resolution/duration controls through the browser. The server issues
the reference id and owns the safe input path; the browser never supplies a
filesystem path.

The route is selected by reference presence:

- no reference: `native_t2v` and the existing H1A graph;
- one validated `start_frame`: `native_i2v` and the H1B graph;
- any unsupported role, malformed id, missing asset, unsafe path, or stale graph:
  explicit validation failure with no fallback.

This is a technical vertical slice. The Native result and browser result do not
claim visual quality, Owner acceptance, license clearance, or production
deployment.

## 2. Implementation boundary

| Area | H1B implementation |
|---|---|
| UI | `h3/app/static/index.html`, `styles.css`, `app.js`; one Reference card with Add, Replace, Remove, thumbnail, and status |
| Local server | `h3/app/server.py`; multipart upload, Pillow decode/format checks, server-issued ids, preview endpoint, route-aware jobs |
| T2V adapter | `h3/adapters/native_t2v.py`; H1A-compatible no-reference route plus typed reference/route validation |
| I2V adapter | `h3/adapters/native_i2v.py`; fail-closed H1B graph validation and single `first_frame` binding |
| Production workflows | `workflows/h3/H1A_NATIVE_T2V_BASE.json` and `workflows/h3/H1B_NATIVE_I2V_BASE.json` |
| Canonical launcher | `h3/run_h3.bat`; `h3/run_h1a.bat` is a compatibility wrapper |
| Model boundary | isolated `h3/model_store/`; no shared `ComfyUI/models/` dependency |
| Output/input boundary | ignored `output/h3/video/` and `output/h3/inputs/`; no generated MP4 or uploaded runtime input is committed |
| Evidence | `docs/h3/evidence/h1b/2026-09-09/` |

H1A's materialized graph and no-reference browser path remain intact. H1B does
not add a custom node, modify ComfyUI core/frontend, create a project database,
or merge with Manga semantics.

## 3. H1B contract

- Exactly one reference is allowed, with role `start_frame`.
- Reference ids are server-issued 32-character lowercase hexadecimal values.
- Accepted file extensions are PNG, JPEG/JPG, and WebP. Pillow verifies the
  actual image, dimensions, pixel budget, and extension/format agreement.
- Upload size is limited to 20 MiB and decoded pixels to 16,777,216.
- The stored filename is server-generated. The adapter accepts only a relative
  `inputs/<server-filename>` path with an allowed image suffix.
- The H1B graph binds `LoadImage` to `MiniMaxH3ImageToVideo.first_frame` only.
  `last_frame` is absent and is rejected if it appears in a stale graph.
- Remove clears the current browser request only; it does not delete the
  server-side asset or alter Native history. A failed replacement preserves the
  current selected reference.
- No multi-reference, end-frame, REF2VA, Still, Turbo, LightX, PDD, FastH3,
  VSA, Studio, Timeline, Project/Shot/Take, or automatic quality fallback is
  exposed.

## 4. Native workflow provenance

The H1B graph is a materialized API-prompt adaptation of the official
[Comfy-Org MiniMax H3 I2V workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_i2v.json),
at official workflow-template commit
`66abae5205f7c5105281146fa109f7c12801d268`.

| Artifact | Value |
|---|---|
| Local workflow | `workflows/h3/H1B_NATIVE_I2V_BASE.json` |
| Local workflow SHA-256 | `6BFA82EA20B65C84CBDB62A1EF949581D4F03368C2F6B035D6081EF204FE72DE` |
| Official source SHA-256 | `4DC94E9EA308C1D60409E7F55DBA5E2788DAB4659C2DBB90F1E9481498767540` |
| Baseline | 608 x 352, 124 frames, 24 FPS, 5 seconds, 20 steps |
| Sampler / scheduler | `res_multistep` / `simple` |
| Turbo LoRA | disabled |
| H1B output prefix | `video/h1b_native_i2v` |

The local H1A workflow SHA-256 remains
`4783A19B767514D2B901CC508693524D9FA73CAFC7C6FFA20F94167CF0406552`; the H1A
workflow was not rewritten for H1B.

## 5. Browser verification

The live browser path at `http://127.0.0.1:8190/` was exercised through the
canonical launcher and the in-app browser. AX state and screenshots showed the
visible control/state transitions; the live UI screenshot capture is retained
in the CUA run transcript, while the committed evidence package contains the
media frames and contact sheet.

| Browser action | Observed result |
|---|---|
| H1A/T2V regression | Prompt retained; `Running` then `Completed`; Preview visible; History showed `Completed · T2V` |
| Add reference | Multipart upload succeeded; thumbnail, `Start Frame`, dimensions, Replace, and Remove appeared |
| Replace reference | Existing selection was replaced with the new uploaded image; `Start Frame` card remained visible |
| Remove reference | Card cleared to `No Start Frame selected.`; prompt, resolution, duration, and Generate remained usable; no server asset deletion was requested |
| H1B/I2V generation | Reference remained selected through `Running` and `Completed`; Preview showed `Start Frame`; History showed `Completed · Start Frame`; queue returned to 0 |
| Failed generation behavior | UI request fields and reference selection were not automatically cleared and no T2V fallback was introduced |

## 6. Runtime and media evidence

The full machine-readable record is in
[the H1B evidence manifest](../evidence/h1b/2026-09-09/manifest.json).

| Route | Job / prompt | Elapsed | Output | SHA-256 |
|---|---|---:|---|---|
| H1B T2V regression | `a188fe59-2031-4fac-a6f8-dc82ef7ea4c3` | 158.43 s | `output/h3/video/h1a_native_t2v_00003_.mp4` | `6F849052D9D3252FB8A5EBF4D1DDA7269C6328539A5BBC932DA58A803A9E0236` |
| H1B Native I2V | `5ea30fc7-e8a1-413b-9d4e-3bca0812c29c` | 142.28 s | `output/h3/video/h1b_native_i2v_00001_.mp4` | `7D322ABE7B159514C46A2690ED5145FF00C846579F8E3EDFD21DF65FB6C49386` |

The I2V session job id was `816c8270228f40c6b39735414e499ed9`, using reference
id `00c89a2a6cdc49b8adc833b447a75700` with role `start_frame`. Native history
inspection confirmed node `131` had `first_frame: ["132", 0]`, prompt, size,
and length, while node `132` loaded
`inputs/00c89a2a6cdc49b8adc833b447a75700.png`; no `last_frame` key was present.

`ffprobe` confirmed for both outputs: H.264 video, AAC stereo audio at 32 kHz,
608 x 352, 24 FPS, 124 video frames, and 5.167 seconds media duration. The
I2V MP4 is 413,441 bytes; the T2V regression MP4 is 228,976 bytes. Neither MP4
is committed.

During active I2V generation, sampled Native status reported total VRAM
`12,878,086,144` bytes and minimum sampled free VRAM
`2,355,837,824` bytes (approximately 10.52 GB decimal allocated at that
sample). Minimum sampled free system RAM was `3,103,027,200` bytes from a total
`68,476,002,304` bytes. No OOM, retry, fallback, or backend error occurred.
Post-job free VRAM fell to roughly 0.7 GB because the Native model cache stayed
resident; that post-job cache state is not used as the generation peak.

## 7. Verification

| Check | Result |
|---|---|
| Python adapter/server tests, including existing H1A coverage | `19 passed` |
| H1B UI/source smoke | `13 PASS` |
| JavaScript syntax | `node --check h3/app/static/app.js` passed |
| Python syntax | `compileall` passed |
| Workflow JSON parse | H1A and H1B passed |
| `git diff --check` | passed |
| Upload validation | valid PNG/JPEG accepted; invalid decode, oversize, unsafe filename, traversal, and missing asset distinguished |
| Browser T2V regression | `COMPLETED` with real Native MP4 |
| Browser Native I2V | `COMPLETED` with real Native MP4 |

The existing H0.1 evidence frame was used as the browser reference source:
`docs/h3/evidence/reference-implementations/native/2026-09-08_generation/frames/first_frame.png`.
The H1B upload was a runtime copy in ignored `output/h3/inputs/`; no new model
or private reference asset was added to the repository.

## 8. Explicit non-scope and review gate

H1B.1, REF2VA, multi-reference, end-frame, Still, Turbo, LightX, PDD, FastH3,
VSA, Studio, Timeline, Storyboard, Cast, 3D, Manga, custom-node vendoring,
ComfyUI core/frontend changes, persistent project storage, public deployment,
and quality auto-fallback remain out of scope. The existing Illustrious Manga
implementation, Manga documents, Manga workflows, and shared ComfyUI runtime
were not modified.

H1B is ready for Web GPT / Astra H1B review as a bounded local technical slice.
If that review is accepted, the next separately authorized slice may be H1B.1;
do not infer REF2VA, Still, or broader Studio scope from this result. Owner
acceptance remains `PENDING`.
