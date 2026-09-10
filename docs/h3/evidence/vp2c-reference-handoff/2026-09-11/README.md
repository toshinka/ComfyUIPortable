# VP2C — Reference Handoff and scoped D&D evidence

Evidence date: `2026-09-11`

Remote base: `56ad30afa128ef4120f962b6c114fc0e7526aae8`

Current classification: `PASS WITH LIMITS`

This package records the bounded VP2C implementation, local contract
verification, and the authorized Browser acceptance at
`http://127.0.0.1:8190/`. Exactly one Still and one Reference Video were
generated. Character drag-and-drop accepted an actual File. Motion drag-and-
drop produced an actual File drag source, but safe Browser automation did not
reproduce target-slot acceptance; the exact MP4 picker route was accepted and
used for the Reference generation.

## Implemented boundary

The H3 server now exposes two job-id-only promotion routes:

```text
POST /api/r2v/from-still  -> Character Image
POST /api/r2v/from-video  -> Motion Video
```

Both routes accept only a server-issued `job_id` from the current in-memory
session. The source must be a completed, correctly typed H3 result whose
server-owned output resolves inside the H3 output boundary. The result is
copied, never moved, into the existing `output/h3/inputs` asset boundary.
Public metadata contains an opaque asset ID, `Generated Still` or
`Generated Video`, preview URL, dimensions or video metadata, `source_kind`,
and `source_job_id`; filesystem and staged paths are not public.

The server rejects unknown, non-completed, wrong-kind, missing, outside-boundary,
wrong-extension, malformed job, and browser-supplied path/URL requests. It also
fails closed when another H3 job is `QUEUED`, `RUNNING`, or `DISCONNECTED`.

The UI adds drop handling only to the existing Reference Character Image and
Motion Video slots. It requires one actual browser `File`, rejects multiple
files and URL drops, reuses the existing upload functions, scopes navigation
prevention to those two dropzones, clears the maroon active state on exit/drop/
error, and leaves Add/Replace/Remove and picker listeners intact.

Completed Still History entries expose `Use as Character`; completed Standard
or Reference Video entries expose `Use as Motion`. Handoff sends only the
source job ID, does not copy the source prompt, does not generate automatically,
and snapshots/restores the current prompt, seed, other slot, and mode state on
failure. Reference Video still has no Continue action.

## Authorized Browser acceptance

The isolated H3 Native process and skin were started locally. The browser
confirmed the following bounded sequence:

| Check | Result |
|---|---|
| Video mode loaded | PASS |
| Reference Experimental enabled after Native startup | PASS |
| Character Image dropzone count | 1 |
| Motion Video dropzone count | 1 |
| Standard Start/End card hidden in Reference mode | PASS |
| Generate disabled before Character Image | PASS |
| Character File D&D | PASS — actual File accepted by the scoped target |
| Motion File D&D | PASS WITH LIMITS — actual File drag source verified; target acceptance not reproduced by safe CUA |
| Exact MP4 picker route | PASS — accepted and used for Reference |
| Still generation | PASS — one prompt-only run |
| Still → Character | PASS — History handoff, no auto-generation |
| Reference generation | PASS — one Picture + Motion run, playback started |
| Reference → Motion | PASS — History handoff, no auto-generation |
| Uploads / generations | 2 authorized files / 2 generations |

The two original files were preserved. No extra Browser generation or retry was
run.

### Browser run identifiers and media

| Item | Result |
|---|---|
| Still job / Native prompt | `5feed87a7a3a4072b2d41d658db6dd80` / `fc437e73-8e0c-4b6d-a8be-56f3c6b17dd4` |
| Still output | `h2a_native_still_00003_.png`; SHA-256 `6320CDDC990EBDCBAB183DA1A6B60B59AB35FA5672F08E24C9E1B1942C11E1B8`; 608×352 |
| Still → Character asset | `1366a9301c5545dfbf1f3d59c520fd45`; `source_kind=generated_still` |
| Reference job / Native prompt | `fdeaf8721f0c4349bd4dded751d89eb3` / `2815ce83-8059-4c57-bea5-ec2828920a62` |
| Reference materialized prompt | `Use <Picture 1> for the subject identity and appearance.` + `Use <Video 1> for motion, timing, and camera behavior.` + `The red robot walks forward with a gentle camera push.` |
| Reference output | `vp2b_r2v_reference_00002_.mp4`; SHA-256 `4CBBCD4D2B8232CAE52A02CBD35C47B04B42C8D1A65F94AA59334751738277A6`; H.264/AAC, 608×352, 124 frames, 24 fps, 5.167 s |
| Reference → Motion asset | `a05ab0b64b9149c0bd6fec48600500cf`; `source_kind=generated_video` |
| Original PNG / MP4 | SHA-256 `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E` / `412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254` |
| Visual gate | Picture influence `OBSERVED`; Video influence `NOT CONVINCING` |
| Runtime sample | Peak/min not instrumented; free VRAM sample `1,387,738,700` bytes; OOM 0 / retry 0 |

Public history payload contained no filesystem path, Windows path, file URI, or
HTTP source URL.

## Local contract verification

```text
VP2C server contract: 5 PASS
VP2C UI contract: 36 PASS
VP2B server regression: 5 PASS
VP2B UI regression: 28 PASS
All H3 Python tests: 65 PASS
VP1 UI: PASS
H2C UI: 52 PASS
H1C UI: 38 PASS
H1B.1 P2 UI: 44 PASS
H1B.1 P1 UI: 36 PASS
JavaScript syntax / Python compile / JSON / diff check: PASS
```

The VP2B Standard generation was not repeated; its prior Browser evidence is
retained. No runtime media, model, local YAML, temporary harness, or Manga file
is part of this change.

Manifest: [manifest.json](manifest.json)

Report: [VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md](../../../reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md)

Implementation: `PUBLISHED ON MAIN` at `56ad30afa128ef4120f962b6c114fc0e7526aae8`

Closeout publication: `LOCAL MAIN / PUSH PENDING`

Owner acceptance: `PENDING`

STOP after the authorized two-generation Browser acceptance budget.
