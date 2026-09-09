# H1B.1 Start / End Frame Native FL2VA Vertical Slice Report

更新: 2026-09-09 JST

Stage: `H1B.1`

Status: `IMPLEMENTED` / `VERIFIED LOCAL GENERATION` /
`VERIFIED BROWSER UI GENERATION`

Implementation commit: `48adcb27cfc24d9c0f0e2b0b27f2284621a4a18d`

Owner acceptance: `PENDING`

## 1. Outcome

H1B.1 extends H1B from one Start Frame to exactly two fixed named slots:
`start_frame` and `end_frame`. The browser sends the canonical `references`
object, the server owns all uploaded paths, and Native MiniMax H3 receives the
optional `first_frame` and `last_frame` edges of a new FL2VA workflow.

The route remains presence-driven:

- no references: H1A `native_t2v`;
- Start Frame only: H1B.1 `native_i2v` with `first_frame`;
- End Frame only: H1B.1 `native_i2v` with `last_frame`;
- Start + End: H1B.1 `native_i2v` with both edges.

End-only was exercised against the current Native implementation and completed;
it is therefore `VERIFIED`, not `BLOCKED` or `NOT SUPPORTED`.

This is a technical vertical slice. Local generation and browser completion do
not claim visual quality, Owner acceptance, license clearance, or production
deployment.

## 2. Fixed-slot contract

The canonical request shape is:

```json
{
  "references": {
    "start_frame": {"id": "<id>", "role": "start_frame"},
    "end_frame": {"id": "<id>", "role": "end_frame"}
  }
}
```

Each slot may be `null`. The legacy H1B shape
`reference: {"id": "<id>", "role": "start_frame"}` is accepted only as a
Start Frame request and is normalized to the canonical Start Frame slot. A
request containing both a non-null legacy field and canonical slots is rejected
to avoid ambiguous truth.

There is no ordered generic multi-reference list, no user-facing route
selector, and no dummy image substitution. The adapter binds only selected
edges and removes unused loader nodes from the compiled graph.

## 3. Implementation boundary

| Area | H1B.1 implementation |
|---|---|
| UI | `h3/app/static/index.html`, `styles.css`, `app.js`; compact Start Frame and End Frame cards with independent Add, Replace, Remove, thumbnail, and status |
| Local server | `h3/app/server.py`; multipart slot field, shared image validation, server-issued ids, canonical request metadata, route-aware jobs |
| Request vocabulary | `h3/adapters/native_t2v.py`; fixed-slot types, legacy normalization, route labels, fail-closed role/id checks |
| FL2VA adapter | `h3/adapters/native_i2v.py`; separate H1B.1 graph validation and optional `first_frame`/`last_frame` binding |
| Historical H1B | `workflows/h3/H1B_NATIVE_I2V_BASE.json` remains intact for legacy `reference` requests |
| H1B.1 workflow | `workflows/h3/H1B1_NATIVE_FL2VA_BASE.json` |
| Launcher | `h3/run_h3.bat`; `h3/run_h1a.bat` remains a compatibility wrapper |
| Model boundary | isolated `h3/model_store/`; no shared `ComfyUI/models/` dependency |
| Output/input boundary | ignored `output/h3/video/` and `output/h3/inputs/`; no generated MP4 or runtime upload is committed |
| Evidence | `docs/h3/evidence/h1b1/2026-09-09/` |

## 4. Workflow provenance

The new graph is adapted from the official
[Comfy-Org MiniMax H3 I2V workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_i2v.json),
at official workflow-template commit
`66abae5205f7c5105281146fa109f7c12801d268`.

| Artifact | Value |
|---|---|
| Local workflow | `workflows/h3/H1B1_NATIVE_FL2VA_BASE.json` |
| Local workflow SHA-256 | `0072756BBB3A259E83D441054C838AC18CE8A40EACFEC63D0C11948001F685E9` |
| Official source SHA-256 | `4DC94E9EA308C1D60409E7F55DBA5E2788DAB4659C2DBB90F1E9481498767540` |
| Schema | `tegaki.h3.h1b1.native-fl2va/v1` |
| Baseline | 608 x 352, 124 frames, 24 FPS, 5 seconds, 20 steps |
| Sampler / scheduler | `res_multistep` / `simple` |
| Turbo LoRA | disabled |
| Output prefix | `video/h1b1_native_fl2va` |
| Native conditioning node | `MiniMaxH3ImageToVideo` node `131` |
| Start / End loaders | `LoadImage` nodes `132` / `133` |

The official source currently exposes optional `first_frame` and `last_frame`
inputs; H1B.1 adopts only those two fixed edges for this bounded slice.

## 5. Browser verification

The live browser path at `http://127.0.0.1:8190/` was exercised through the
canonical launcher and in-app browser. The completion views were visible in
AX state and the video preview; no browser screenshot binary was persisted.

| Browser action | Observed result |
|---|---|
| Add Start Frame | Existing committed H0.1 first frame accepted and displayed at 608 x 352 |
| Add End Frame | Existing committed H0.1 last frame accepted independently and displayed at 608 x 352 |
| Invalid replacement | A workflow JSON upload was rejected as non-image; current selections remained |
| Independent removal | Removing Start left End; removing End left both slots empty |
| Start-only Native run | `Completed · Start Frame`, Preview visible, 161.67 s |
| Start+End Native run | `Completed · Start + End`, Preview visible, 145.94 s |
| End-only Native run | `Completed · End Frame`, Preview visible, 130.97 s |
| T2V regression | `Completed · Text only`, Preview visible, 112.54 s |

The final UI state was both slots empty after the T2V regression, preserving the
H1A entry path.

## 6. Native and media evidence

The complete machine-readable record is in the
[H1B.1 evidence manifest](../evidence/h1b1/2026-09-09/manifest.json).

| Route | Job id | Elapsed | Output | SHA-256 |
|---|---|---:|---|---|
| Start Frame | `76a93d28ea2c485d8e0ebd678e20b7b1` | 161.67 s | `output/h3/video/h1b1_native_fl2va_00001_.mp4` | `E75435D266514801CBD76996A51870B1637E73AFB47535BAB47FE329ECE79DAD` |
| Start + End | `7d3aac4b7d62434e9b71859846bcd4d9` | 145.94 s | `output/h3/video/h1b1_native_fl2va_00002_.mp4` | `3F233C69F101A7063E3A97AD64F1DE0F2DB51E7FE6376DA1A5CCF34486326883` |
| End Frame | `30b82801fa3f4e1b984679f132225bdf` | 130.97 s | `output/h3/video/h1b1_native_fl2va_00003_.mp4` | `CE192DA29B145674296707421E6CB3BA76545A737D64757BCA66CB4C2B053A65` |
| Text only regression | `03d17c6a98a7412a9c2b5c5a5d1fb6db` | 112.54 s | `output/h3/video/h1a_native_t2v_00004_.mp4` | `22218C7FFECF602F13D3D76007B2C67708B672FD105347A6C28FE2AE2AB5AA61` |

All four outputs were H.264/AAC MP4s at 608 x 352, 24 FPS, 124 frames, and
5.167 seconds. The Start+End MP4 metadata confirmed `node 131` carried both
edges and the server-issued input paths:

```text
first_frame = ["132", 0]
last_frame  = ["133", 0]
inputs/e2c6b035a25d4902817eac81f9a82506.png
inputs/7a3af13037664071bdfc53bceee939a8.png
```

The evidence directory contains the [output frame triplet](../evidence/h1b1/2026-09-09/start_end_output_frame_000.png),
[middle frame](../evidence/h1b1/2026-09-09/start_end_output_frame_061.png),
[last frame](../evidence/h1b1/2026-09-09/start_end_output_frame_123.png),
and [contact sheet](../evidence/h1b1/2026-09-09/start_end_output_contact_sheet.png).

## 7. Resource and safety observation

During active Start+End generation, the status endpoint reported total VRAM
`12,878,086,144` bytes and an active sampled free-VRAM minimum of
`2,147,616,431` bytes. The corresponding sampled used value was
`10,730,469,713` bytes. Total RAM was `68,476,002,304` bytes with sampled free
RAM `7,497,875,456` bytes. This is a sampled observation, not a hardware trace.

No OOM, retry, fallback, unsafe path, or dummy-image substitution was observed.
The adapter rejects malformed ids, unsupported roles, mismatched paths, stale
edges, and missing assets before Native submission.

## 8. Verification

| Check | Result |
|---|---|
| Python adapter/server tests plus prior H1A/H1B coverage | `32 passed` |
| H1B.1 UI/source smoke | `23 PASS` |
| JavaScript syntax | `node --check h3/app/static/app.js` passed |
| Python syntax | `compileall` passed |
| Workflow JSON parse | passed |
| `git diff --check` | passed |
| Browser Start-only | real Native MP4 completed |
| Browser Start+End | real Native MP4 completed |
| Browser End-only | real Native MP4 completed |
| Browser T2V regression | real Native MP4 completed |

## 9. Non-scope and review gate

REF2VA, ordered generic multi-reference, Still, Continuation, Segment, Timeline,
Studio, Project/Shot/Take, Manga integration, custom-node vendoring, shared
ComfyUI core/frontend changes, persistent project storage, public deployment,
and new model downloads remain out of scope. H1A and historical H1B remain
available and were not rewritten.

H1B.1 is ready for bounded Web GPT / Astra H1B.1 review. Owner acceptance and
license action remain separate and `PENDING`. If the review is accepted, stop;
do not infer REF2VA, ordered multi-reference, Still, Continuation, or Studio
from this slice.
