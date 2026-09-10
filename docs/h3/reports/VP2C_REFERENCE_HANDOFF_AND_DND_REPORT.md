# VP2C — Reference Handoff and Drag-and-Drop Report

Date: `2026-09-11`

## Decision

`VP2C REFERENCE HANDOFF & DND: PASS WITH LIMITS`

The bounded server/UI implementation, local contract tests, and the authorized
local Browser acceptance are complete within the stated two-generation budget.
The exact PNG and MP4 were used locally at `http://127.0.0.1:8190/`; exactly one
Still and one Reference Video were generated. Character drag-and-drop accepted
an actual File. Motion drag-and-drop produced an actual File drag source, but
safe Browser automation did not reproduce target-slot acceptance; the exact
MP4 picker route was accepted and used for the Reference generation.

The known VP2B mixed-reference weakness remains a Native fidelity limitation,
not a VP2C failure. VP2C adds ergonomics and handoff only; it does not add a
new generation capability, source-strength control, Image Prep, or
multi-reference semantics.

## Required result fields

| Field | Result |
|---|---|
| VP2C REFERENCE HANDOFF & DND | `PASS WITH LIMITS` |
| Remote base | `56ad30afa128ef4120f962b6c114fc0e7526aae8` |
| Implementation publication | `PUBLISHED ON MAIN` at `56ad30afa128ef4120f962b6c114fc0e7526aae8` |
| Character D&D | `PASS` — actual File accepted by the scoped Character target |
| Motion D&D | `PASS WITH LIMITS` — actual File drag source verified; safe CUA target acceptance not reproduced |
| File picker route | `PASS` — exact MP4 picker upload accepted and used for the Reference run |
| Still generation | `PASS` — one prompt-only Native Still completed |
| Still→Character | `PASS` — History handoff completed without auto-generation |
| Still handoff auto-gen | `NONE` — no handoff path calls a generation endpoint |
| Still source job id | `5feed87a7a3a4072b2d41d658db6dd80` |
| Promoted Character asset opaque id | `1366a9301c5545dfbf1f3d59c520fd45` |
| Reference generation | `PASS` — one Picture + Motion Native Ref2VA run completed and played |
| Reference job/prompt ids | `fdeaf8721f0c4349bd4dded751d89eb3` / `2815ce83-8059-4c57-bea5-ec2828920a62` |
| Video→Motion | `PASS` — History handoff completed without auto-generation |
| Motion auto-gen | `NONE` — no handoff path calls a generation endpoint |
| Promoted Motion asset opaque id | `a05ab0b64b9149c0bd6fec48600500cf` |
| Filesystem paths public | `REJECTED` — local server tests assert no `path` or `staged_path` in public metadata |
| Arbitrary URL/path injection | `REJECTED` — handoff JSON accepts only `job_id` |
| Atomic handoff failure | `PASS` — source validation/copy precedes UI replacement; failure restores the captured state |
| Generation count | `2/2` — exactly one Still and one Reference Video |
| Regression counts | `VP2C server 5; VP2C UI 36; VP2B server 5; VP2B UI 28; all H3 Python 65; H2C UI 52; H1C UI 38; H1B.1 P2 UI 44; H1B.1 P1 UI 36; JS/Python/JSON/diff PASS` |
| Still output | `h2a_native_still_00003_.png`; SHA-256 `6320CDDC990EBDCBAB183DA1A6B60B59AB35FA5672F08E24C9E1B1942C11E1B8`; 608×352 RGB PNG |
| Reference output | `vp2b_r2v_reference_00002_.mp4`; SHA-256 `4CBBCD4D2B8232CAE52A02CBD35C47B04B42C8D1A65F94AA59334751738277A6`; H.264/AAC, 608×352, 124 frames, 24 fps, 5.167 s |
| Original input preservation | `PASS` — PNG `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`; MP4 `412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254` |
| Reference prompt/seed | `The red robot walks forward with a gentle camera push.` / `4321343092772379907` |
| Still prompt/seed | `A small friendly red robot standing still in a clean studio, centered, full body, simple background.` / `7189920060476219937` |
| VRAM/OOM/retry | `Peak/min not instrumented; in-run free sample 1,387,738,700 bytes; OOM 0 / retry 0` |
| Visual review | `Picture influence OBSERVED; Video influence NOT CONVINCING` |
| Evidence/docs commit SHA | `LOCAL CLOSEOUT COMMIT (reported after commit)` |
| Publication | `LOCAL MAIN / PUSH PENDING` for this closeout; implementation is `PUBLISHED ON MAIN` |
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

The authorized Browser run used the exact local PNG and MP4 at
`http://127.0.0.1:8190/`. Character File D&D was accepted by the scoped target;
the UI remained in Reference mode with no navigation and the Character slot
showed the selected file. Motion File D&D produced an actual `File` drag source
(`types=Files`, `files=1`), but safe CUA did not reproduce target-slot
acceptance. The exact MP4 was then accepted through the existing Motion picker,
which supplied the input to the single Reference generation. This is recorded
as an automation-bound acceptance limit, not as a claim that the Motion target
is product-failed.

The completed Still job was `5feed87a7a3a4072b2d41d658db6dd80` with Native
prompt `fc437e73-8e0c-4b6d-a8be-56f3c6b17dd4`. Its History entry was promoted
to Character as opaque asset `1366a9301c5545dfbf1f3d59c520fd45` without
auto-generation. The completed Reference job was
`fdeaf8721f0c4349bd4dded751d89eb3`, Native prompt
`2815ce83-8059-4c57-bea5-ec2828920a62`; playback was loaded and started from
History. Its History entry was promoted to Motion as opaque asset
`a05ab0b64b9149c0bd6fec48600500cf` without auto-generation. Public history
metadata contained no filesystem path, Windows path, file URI, or HTTP source
URL.

The visual gate was applied once, as bounded by the card: the generated Still
retained the red robot identity (`PICTURE INFLUENCE OBSERVED`), while the
Reference output did not convincingly retain the supplied orange greenhouse
motion (`VIDEO INFLUENCE NOT CONVINCING`). This is the known Native
mixed-reference limitation and no quality retry was run. Peak/min VRAM was not
instrumented; one in-run sample recorded 1,387,738,700 bytes free. OOM and
retry counts were both zero.

VP2B Standard generation was not repeated. Manga runtime, Manga documents,
shared ComfyUI core/frontend, model weights, local YAML, temporary harness
files/processes, and generated media were not changed or committed. The two
authorized generated media files were preserved locally for evidence only.

## Publication and next gate

The implementation commit is `56ad30afa128ef4120f962b6c114fc0e7526aae8`,
published on `main` per the current repository baseline. This evidence and
closeout update remains local until Owner performs the push; therefore its
publication state is `LOCAL MAIN / PUSH PENDING`. Implementation publication,
technical verification, Browser acceptance, visual review, and Owner
acceptance remain separate gates.

The next bounded gate is Owner hands-on evaluation of the exact local results.
Only after that may Web-GPT decide Rev.4 ordering. Image Prep remains a
roadmap note only; no Rev.4 document is authored here.

Owner acceptance: `PENDING`

STOP
