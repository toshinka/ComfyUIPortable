# VP2C — Reference Handoff and Drag-and-Drop Report

Date: `2026-09-11`

## Decision

`VP2C REFERENCE HANDOFF & DND: BLOCKED`

The bounded server/UI implementation and local contract tests are complete.
Browser UI smoke completed with zero uploads and zero generations. The required
real Browser acceptance remains pending because the exact local file upload and
the two real local generations require direct action-time authorization.

The known VP2B mixed-reference weakness remains a Native fidelity limitation,
not a VP2C failure. VP2C adds ergonomics and handoff only; it does not add a
new generation capability, source-strength control, Image Prep, or
multi-reference semantics.

## Required result fields

| Field | Result |
|---|---|
| VP2C REFERENCE HANDOFF & DND | `BLOCKED` |
| Remote base | `543d8c2c2817743b10f255c168047e4edd1781a9` |
| VP2B closeout publication correction | `PASS` — current docs now record `PUBLISHED ON MAIN` at `543d8c2c` |
| Character D&D | `PENDING AUTHORIZATION` |
| Motion D&D | `PENDING AUTHORIZATION` |
| File picker regression | `PASS` — existing picker listeners and upload routes retained; real picker action not repeated |
| Still generation | `PENDING AUTHORIZATION` |
| Still→Character | `PENDING AUTHORIZATION` |
| Still handoff auto-gen | `NONE` — no handoff path calls a generation endpoint |
| Still source job id | `NONE` |
| Promoted Character asset opaque id | `NONE` |
| Reference generation | `PENDING AUTHORIZATION` |
| Reference job/prompt ids | `NONE` |
| Video→Motion | `PENDING AUTHORIZATION` |
| Motion auto-gen | `NONE` — no handoff path calls a generation endpoint |
| Promoted Motion asset opaque id | `NONE` |
| Filesystem paths public | `REJECTED` — local server tests assert no `path` or `staged_path` in public metadata |
| Arbitrary URL/path injection | `REJECTED` — handoff JSON accepts only `job_id` |
| Atomic handoff failure | `PASS` — source validation/copy precedes UI replacement; failure restores the captured state |
| Generation count | `0/2` — no real Browser generation was started |
| Regression counts | `VP2C server 5; VP2C UI 36; VP2B server 5; VP2B UI 28; all H3 Python 65; H2C UI 52; H1C UI 38; H1B.1 P2 UI 44; H1B.1 P1 UI 36; JS/Python/JSON/diff PASS` |
| Implementation commit SHA | `LOCAL PENDING` |
| Evidence/docs commit SHA | `LOCAL PENDING` |
| Publication | `LOCAL MAIN / PUSH PENDING` for VP2C; VP2B correction is already `PUBLISHED ON MAIN` |
| Image Prep | `NOT IMPLEMENTED` |
| LoRA | `UNCHANGED` |
| Multi-reference | `NOT IMPLEMENTED` |
| Manga changes | `NONE` |
| Report path | `docs/h3/reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md` |
| Evidence path | `docs/h3/evidence/vp2c-reference-handoff/2026-09-11/` |
| Recommended next | `Owner hands-on evaluation, then Web-GPT Rev.4 ordering decision` |
| Owner acceptance | `PENDING` |
| STOP | `STOP` |

## Implementation contract

### Still → Character

`POST /api/r2v/from-still` accepts only `{ "job_id": "..." }`. The server
resolves the exact completed same-session Still job, validates the output image
inside the H3 output root, copies it into the existing R2V input boundary, and
registers a `Generated Still` asset with `source_kind=generated_still` and the
source job ID. The original generated file remains present and unchanged.

### Video → Motion

`POST /api/r2v/from-video` applies the same boundary to a completed same-session
Standard or Reference Video result. The copied MP4 is revalidated through the
existing 64 MiB/ffprobe route and registered as `Generated Video` with
`source_kind=generated_video`. No recursive continuation or automatic
generation is involved.

### UI handoff and D&D

The History card adds `Use as Character` only for completed Still entries and
`Use as Motion` only for completed Video entries, including Reference Video.
The action sends no prompt or browser path and applies only the target slot plus
the required `Video → Reference` mode. Current prompt, seed, and opposite slot
are preserved. Active generation blocks handoff, and any server or application
failure restores the prior snapshot.

The only drop targets are the existing Character Image and Motion Video slots.
Character accepts PNG/JPEG/WebP through the current upload route; Motion accepts
one MP4 through the current 64 MiB route. Multiple files and URL/text drops
fail closed with a concise slot message. The active style is restrained
maroon-derived styling on the slot itself; no overlay or modal was added.

## Verification and exclusions

The five VP2C Python tests cover successful Still and Video copies, opaque
provenance, original preservation, replacement safety, unknown/non-completed/
wrong-kind/missing/outside/wrong-extension boundaries, active-job blocking, and
HTTP path injection. The 36-marker UI smoke covers scoped dropzone handlers,
actual `File` enforcement, one-file rejection, existing upload function reuse,
History action gating, source-job-only requests, no auto-generation, and state
snapshot/restore.

The Browser rendered Reference mode after isolated Native startup and showed
one dropzone per existing R2V slot. No upload or generation was performed, so
there are no Still, Reference job, promoted asset, or Browser D&D IDs to record.

VP2B Standard generation was not repeated. Manga runtime, Manga documents,
shared ComfyUI core/frontend, model weights, local YAML, runtime uploads, staged
inputs, and generated media were not changed or committed.

## Publication and next gate

The current live baseline is `HEAD=origin/main=543d8c2`. VP2B closeout wording
was corrected from the stale local/push-pending state to `PUBLISHED ON MAIN` at
that commit. VP2C changes are currently local and must remain distinct from
Owner acceptance.

The next bounded gate is Owner authorization and hands-on evaluation of the
exact local PNG/MP4 files at the local H3 URL, using exactly one prompt-only
Still and exactly one Reference Video generation, then stopping. Only after
that may Web-GPT decide Rev.4 ordering. Image Prep remains a roadmap note only;
no Rev.4 document is authored here.

Owner acceptance: `PENDING`

STOP
