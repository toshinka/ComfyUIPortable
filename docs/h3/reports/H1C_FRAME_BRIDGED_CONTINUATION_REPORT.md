# H1C — Frame-Bridged Continuation Closeout

Date: 2026-09-09 JST

H1C closeout: `PASS`

Implementation commit: `a92237fe3eeb0f53e16c69d37763d388fedf2145`

Additional fix commit: `ff577a0c`

Evidence/docs commit: `4df2f2a5f29957a9f4ba429ddd8796d13de5de3b`

Owner acceptance: `PENDING`

## Status distinction

| Status | Result | Meaning |
|---|---|---|
| `IMPLEMENTED` | `PASS` | H1C continuation path is present within the existing H1B.1 skin. |
| `VERIFIED SOURCE/LOGIC` | `PASS` | H1C source/logic smoke and all required static checks pass. |
| `VERIFIED BROWSER UI` | `PASS` | P2 Start+End reuse and H1C Continue were exercised in the local Browser. |
| `VERIFIED LOCAL GENERATION` | `PASS` | A real Native continuation completed on the verified RTX 4070 stack. |
| `PUBLISHED ON MAIN` | `PASS` | The H1C implementation, fix, evidence, and canonical docs are present on GitHub `main`. |
| `OWNER ACCEPTED` | `PENDING` | Technical and Browser evidence do not replace Owner acceptance. |

## Summary

H1C closes the bounded flow from a completed Start+End History result to a
manual Start-Frame continuation. The Browser used the existing same-origin
`/api/jobs/<job_id>/video` route, decoded the output, waited for a near-final
decoded frame, rendered it through a canvas as PNG, and uploaded it through the
existing `/api/references` endpoint. The form then held the new bridge as Start
Frame, cleared End Frame, restored the source scalar settings, and waited for a
manual Generate action.

The original implementation's one-shot `seeked` handler could capture the
initial frame in the current Browser runtime. The bounded H1C fix in
`ff577a0c` keeps the temporary video off-screen, starts muted playback, waits
for a decoded near-final frame (with a `requestVideoFrameCallback` path when
available and a stability-timer fallback), and records the actual captured frame
time before PNG encoding. It does not change the backend, workflow, model, or
shared ComfyUI.

## P2 Start+End Browser acceptance

Browser target: `http://127.0.0.1:8190/` in the Codex in-app Browser via
CUA/Playwright. Native target: `http://127.0.0.1:8188/`.

The source History result was generated through the Browser with:

| Field | Observed value |
|---|---|
| Job id | `970a614fed4e43a88d5bbf9f22f0bd7a` |
| Route | `native_i2v` / `Start + End` |
| Prompt | `A small paper kite drifts across a warm evening sky, gentle motion, clean illustrative style.` |
| Resolution / duration | `608 x 352` / `5s` |
| Seed / steps | `24680` / `20` |
| Start Reference | `27749594c9704c38aa3da20e533c90d6` |
| End Reference | `163a4dccec434f6b84b7b86239d49782` |
| Native elapsed | `157.28s` |
| Output | `output/h3/video/h1b1_native_fl2va_00004_.mp4` (ignored) |
| Output SHA-256 | `8D27B20B1570BC3E8DEB40E6ECC5A48444499C0F332BFAD6E2E20A982089F52D` |

The live P2 sequence changed Prompt and Seed to temporary values, pressed the
source card's `Use settings`, and observed the original Prompt, `608x352`,
duration `5`, numeric Seed `24680`, Steps `20`, both original references, and
`Settings loaded.`. The final-code recheck also read Queue `0`; no generation
was created by `Use settings`.

P2 Start+End Browser acceptance: `PASS`.

## H1C Browser preparation

`Continue` was pressed on the completed source History card. The Browser used
the exact server-issued same-origin URL:

```text
/api/jobs/970a614fed4e43a88d5bbf9f22f0bd7a/video
```

The final clean Browser run observed:

| Field | Observed value |
|---|---|
| Status | `Continuation prepared. Edit the prompt if needed, then Generate.` |
| Source video duration | `5.167s` |
| Capture currentTime | `5.125s` |
| Bridge dimensions | `608 x 352` |
| Bridge Reference id | `8a13cf3913b640c5abbcafcdcb4ec627` |
| Bridge endpoint | `/api/references/8a13cf3913b640c5abbcafcdcb4ec627` |
| Bridge PNG bytes | `346179` |
| Bridge PNG SHA-256 | `636FA8552329D0B0F73D3206E0B455EF0FEB6A6F344372ED3CF342250F68EA2D` |
| Start after Continue | newly uploaded bridge Reference |
| End after Continue | `EMPTY` / `No End Frame selected.` |
| Generate after Continue | enabled; no automatic submission |

The final-code clean Browser DOM also verified the atomic result:

```text
Prompt = A small paper kite drifts across a warm evening sky, gentle motion, clean illustrative style.
Resolution = 608x352
Duration = 5
Seed = 24680
Steps = 20
Start Frame = bridge Reference (the clean recheck used e7bb38c4ea2a4a138e3b08f797d33cf3)
End Frame = empty
```

The accepted Native continuation used bridge Reference
`8a13cf3913b640c5abbcafcdcb4ec627`, captured with the same final-code
functional path before the diagnostic-only trace was removed. The clean
recheck reproduced `currentTime=5.125` and did not submit a job.

H1C Browser preparation: `PASS`.

## Bridge identity and provenance

The source input Start PNG was
`output/h3/tests/reference_robot_v1.png` with SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`. The
source generation's original Start and End Reference ids were `277495...` and
`163a4d...`; the bridge id is `8a13cf...`, so Continue did not reuse either
source Reference id.

The bridge was encoded by the Browser canvas. It is therefore not claimed to
be byte-identical to an independently extracted FFmpeg PNG. The source output
near-final frame is `source_last.png`; the bridge is
`bridge_start_final.png`. Their mean absolute RGB difference is approximately
`1.447`, and the contact sheet shows the same near-final robot image. The
provenance claim is the complete chain of source job id, server video URL,
`currentTime=5.125` of `5.167`, `608x352` dimensions, new `/api/references`
id, stored bridge hash, and visual comparison. This does not claim a model
quality score or a byte-level identity that was not measured.

The Browser bridge was accepted by the existing `/api/references` route. The
resulting continuation's first frame carries the bridge visual content; the
contact sheet also records source middle/near-final and continuation middle/
near-final frames. Visual evidence is observational and remains separate from
Owner acceptance.

## Real Native continuation

After Continue, the Prompt was manually edited to:

```text
The kite continues drifting into a brighter patch of evening sky, gentle motion, clean illustrative style.
```

The Browser then pressed Generate exactly once for the accepted run:

| Field | Observed value |
|---|---|
| Continuation job id | `ebe2a7b6621849bdb37833826c9235a0` |
| Route | `native_i2v` / `Start Frame` |
| Start Reference | `8a13cf3913b640c5abbcafcdcb4ec627` |
| End Reference | `null` |
| Browser result | `Start Frame · Completed in 138.2s · 608 x 352 · 5s` |
| Native elapsed | `138.22s` |
| Output | `output/h3/video/h1b1_native_fl2va_00006_.mp4` (ignored) |
| Output SHA-256 | `31D121A5110CF473B2A8129A38612DBDD67D2FC0DAC9EBAADD58BDAAD78D1828` |

`ffprobe` measured the source and continuation MP4s as H.264/AAC,
`608x352`, `24fps`, `124` video frames, and `5.167s` duration.

Real Native continuation: `PASS`.

## Runtime telemetry

Verified stack:

```text
GPU: NVIDIA GeForce RTX 4070
VRAM total: 12,878,086,144 bytes
System RAM total: 68,476,002,304 bytes
ComfyUI: 0.30.0
Python: 3.13.14 embedded
PyTorch: 2.13.0+cu130
Custom nodes: disabled
H3 model store: isolated
```

The accepted continuation was monitored at 10-second intervals. Peak observed
VRAM used was `11,784.3 MB`; minimum free VRAM was `497.2 MB`. OOM count was
`0`; accepted-job retry count was `0`. Native PID was `30580`. Continuous peak
RAM was not captured; the post-run Native working-set sample was `27,767.8 MB`.

An earlier launcher-mode source attempt (`f66a61f1839c4aa292da9d81e3c132da`)
failed with ComfyUI logger `OSError [Errno 22] Invalid argument` while tqdm
flushed stderr. This was not an OOM, model, or input rejection. The accepted
source and continuation used the same existing model/workflow stack under the
direct Native PTY launch. The earlier pre-fix H1C continuation result was not
used for closeout because its Browser capture reported `currentTime=0`; the
accepted result uses the corrected `5.125` near-final capture.

## Verification

- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- `python -m unittest discover -s h3/tests -p 'test_*.py'` — `32 passed`.
- `node --check h3/app/static/app.js` — `PASS`.
- `node --check h3/app/static/history-settings.js` — `PASS`.
- `node --check h3/app/static/job-status-copy.js` — `PASS`.
- `node --check h3/app/static/continuation-source.js` — `PASS`.
- `python -m compileall -q h3/app h3/adapters` — `PASS`.
- `git diff --check` — `PASS`.

Regression: `PASS`.

## Scope audit

| Area | Result |
|---|---|
| Workflow changes | `NONE` — existing `workflows/h3/H1B1_NATIVE_FL2VA_BASE.json` used unchanged. |
| Model changes | `NONE` — existing `minimax_h3_fl2va_pruned_int8_convrot.safetensors` stack used. |
| Dependency changes | `NONE`. |
| Shared ComfyUI changes | `NONE`. |
| Manga changes | `NONE`. |
| Persistence / Segment architecture | `NONE`. |
| Generated MP4/model weights/runtime caches committed | `NONE`. |

H1B.1/P0/P1/P2 remain regression capabilities. H1C does not start Still,
REF2VA, ordered generic multi-reference, Segment, Studio, Timeline, Storyboard,
Cast, 3D, Manga, or a persistent project schema.

## Report and evidence

Report: `docs/h3/reports/H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md`

Evidence: `docs/h3/evidence/h1c/2026-09-09/README.md`

Manifest: `docs/h3/evidence/h1c/2026-09-09/manifest.json`

Visual comparison: `docs/h3/evidence/h1c/2026-09-09/contact_sheet.png`

Canonical H3 entry and document hub were advanced to the H1C gate only after
the Browser and real Native continuation checks above passed. The H1C
implementation, fix, evidence, and canonical docs are published on GitHub
`main`; Owner acceptance remains `PENDING`.
