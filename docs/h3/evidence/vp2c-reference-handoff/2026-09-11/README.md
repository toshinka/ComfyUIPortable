# VP2C — Reference Handoff and scoped D&D evidence

Evidence date: `2026-09-11`

Remote base: `543d8c2c2817743b10f255c168047e4edd1781a9`

Current classification: `BLOCKED`

This package records the bounded VP2C implementation and local contract
verification. The real Browser acceptance cases are intentionally not claimed:
the exact local PNG/MP4 upload and the two real local generations require
direct action-time authorization before they are performed.

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

## Browser UI smoke completed without upload or generation

The isolated H3 Native process and skin were started locally. The browser
confirmed:

| Check | Result |
|---|---|
| Video mode loaded | PASS |
| Reference Experimental enabled after Native startup | PASS |
| Character Image dropzone count | 1 |
| Motion Video dropzone count | 1 |
| Standard Start/End card hidden in Reference mode | PASS |
| Generate disabled before Character Image | PASS |
| Uploads / generations | 0 / 0 |

No file chooser, drag-and-drop upload, History promotion, Still generation, or
Reference Video generation was performed in this pass.

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
retained. No runtime media, model, local YAML, or Manga file is part of this
change.

Manifest: [manifest.json](manifest.json)

Report: [VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md](../../../reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md)

Owner acceptance: `PENDING`

STOP pending direct authorization for the exact local files and two-generation
Browser acceptance budget.
