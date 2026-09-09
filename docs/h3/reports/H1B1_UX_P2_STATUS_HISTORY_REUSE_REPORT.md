# H1B.1 UX P2 — Status Semantics / History “Use settings”

Date: 2026-09-09

Stage: `H1B.1 / Start + End Frame / Native FL2VA vertical slice`

Astra review status: `KEEP WITH ADJUSTMENTS`

Owner acceptance: `PENDING`

Implementation commit: `8084c6a340aca2f6b94bbd2cfced831117810502`

Evidence: [H1B.1 UX P2 evidence](../evidence/h1b1-ux-p2/2026-09-09/README.md)

## Summary

This bounded P2 closes the two remaining Astra findings for the H1B.1 skin:
state copy now describes the actual job state and available next action, and
each History card has a quiet secondary `Use settings` action. The reuse action
copies existing public History metadata into the current Create form only after
all scalar settings have been validated and every referenced server asset has
been verified through its existing preview endpoint.

No new job authority, route, persistence layer, backend endpoint, workflow,
model, dependency, shared ComfyUI, or Manga behavior was added.

## Astra SHOULD closure

| Finding | Result | Evidence |
|---|---|---|
| SHOULD ④ — state wording / available action mismatch | `CLOSED` for the bounded H1B.1 UI contract | State-copy unit/source smoke and live Completed Browser state |
| SHOULD ⑤ — History has no reuse bridge | `CLOSED` for the bounded H1B.1 UI contract | Restore logic smoke, live Text-only History restore, and dedicated feedback |

The live Browser run covered the Text-only History path. Start-only,
End-only, and Start+End restore behavior is covered by the deterministic logic
smoke; a combined reference restore was not replayed live because the UI server
restart reset its intentionally session-only History and no new reference upload
was performed in this pass.

## P2-A — state semantics

`h3/app/static/job-status-copy.js` provides separate active-job and Preview
copy helpers. The server vocabulary remains unchanged:
`READY`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, and
`DISCONNECTED`.

| State | Active status copy | Preview copy / behavior |
|---|---|---|
| `QUEUED` | Waiting in the Native queue. | Native ComfyUI is preparing the preview. |
| `RUNNING` | Native backend is generating. | Native ComfyUI is preparing the preview. |
| `COMPLETED` | Preview ready. | Completed metadata and video remain visible. |
| `FAILED` | Generation failed. Inputs are retained. | Generation failed. Inputs are retained. |
| `CANCELLED` | Job cancelled. Inputs are retained. | Job cancelled. Inputs are retained. |
| `DISCONNECTED` | Backend connection lost. Current job status is unknown. Waiting for the backend to reconnect. | Backend connection lost. Current job status is unknown. |

`DISCONNECTED` remains non-terminal, so the existing `activeJob` is retained,
polling can continue, and Generate stays disabled while that job is active. No
automatic retry job is created. `CANCELLED` is terminal and no longer receives
the generic processing message. The Preview and active-job authorities remain
separate; P2 does not introduce a combined job-view function.

## P2-B — History `Use settings`

History thumbnail and result-title clicks still call `showPreviewJob(entry)` and
remain Preview-only. The new button is created per History card with a quiet
secondary style and calls `useHistorySettings(entry)`.

The action restores, when valid:

- Prompt
- Resolution
- Duration
- the actual numeric Seed used by the job
- Steps, only when it matches the current UI policy
- Start Frame and End Frame through the existing slot renderer

`h3/app/static/history-settings.js` performs normalization and validation
without touching the DOM. It accepts the canonical
`entry.references.start_frame` / `entry.references.end_frame` metadata and the
legacy `entry.reference` Start Frame shape when the canonical slot is absent.
The normalized browser object contains only the server-issued id, role,
dimensions, and canonical `/api/references/<id>` preview route; no filesystem
path is passed to the browser.

The current UI option list is checked for both Resolution and Duration. Seed is
required to be a safe numeric value rather than the string `random`. Steps must
be a supported numeric value in the current form. Prompt length is checked
against the current textarea limit.

## Atomic restore and reference availability

The restore sequence is:

```text
validate Prompt / Resolution / Duration / Seed / Steps / slot metadata
        ↓
GET every required /api/references/<id> preview endpoint
        ↓
apply all form fields and both fixed reference slots
```

The form is not modified before the resolver returns successfully. A missing
Start or End asset, invalid role/id metadata, unsupported current option,
invalid seed, or invalid steps value reports through the dedicated
`#history-action-status` `aria-live` region as:

```text
Settings were not changed. <reason>
```

There is no silent Text-only fallback and no partial Start+End restore. The
explicit slot results are:

| History entry | Start Frame after restore | End Frame after restore |
|---|---|---|
| Text only | cleared | cleared |
| Start only | restored | cleared |
| End only | cleared | restored |
| Start + End | restored | restored |

`Use settings` does not call `/api/generate`, does not alter `activeJob`, does
not alter `previewJob`, does not alter polling or Cancel ownership, and does
not create a runtime upload or persistence record. `updatePromptCount()` and
Generate availability are re-evaluated after a successful apply; an existing
running `activeJob` therefore continues to keep Generate disabled.

## Browser acceptance

The live local skin was opened at `http://127.0.0.1:8190/` with the Native
backend at `http://127.0.0.1:8188/`. Because the new UI server was started in a
fresh process, its in-memory session History was initially empty. One bounded
Text-only generation was therefore used, within the instruction limit, to
create the History entry; no reference upload was performed.

The Browser generation completed as:

| Field | Observed value |
|---|---|
| Job id | `8189245dd90644aeaa42090d7c99bece` |
| Route | Text only / `native_t2v` |
| Prompt | `A small paper kite drifts across a warm evening sky, gentle motion, clean illustrative style.` |
| Resolution / Duration | 608 x 352 / 5 seconds |
| Seed / Steps | 24680 / 20 |
| Elapsed | 146.94 seconds |
| Output | `output/h3/video/h1a_native_t2v_00006_.mp4` (ignored) |
| SHA-256 | `663C6927B02242DC1275D81F7CBF36A23197678EE6F0D4DD68C876622883E951` |

After completion, the form was changed to a different Prompt and Seed, then the
History card's `Use settings` button was pressed. The final live DOM showed the
original Prompt, Seed `24680`, Resolution `608x352`, Duration `5`, Preview
state `Completed`, and `Settings loaded.` in the dedicated History feedback
region. Both Start/End selected containers remained hidden for the Text-only
entry. Clicking the History result title afterwards kept those form values
unchanged while selecting the Preview.

The final Browser acceptance result is `PARTIAL`: the Text-only restore and
Preview-only separation passed live; the three reference-bearing restore paths
were not replayed live in this session. A History-card screenshot was captured
in the CUA transcript but was not persisted as a PNG artifact.

## Verification

- Python unittest discovery: `32 passed`.
- Existing H1B.1 P1 UI source smoke: `36 PASS`.
- H1B.1 UX P2 status/history source + logic smoke: `44 PASS`.
- `node --check h3/app/static/app.js`: passed.
- `node --check h3/app/static/history-settings.js`: passed.
- `node --check h3/app/static/job-status-copy.js`: passed.
- Python compile check: passed.
- `git diff --check`: passed.

P0 regression remains covered: empty/selected reference containers retain the
existing hidden semantics, and `activeJob` / `previewJob` remain separate. P1
primary-action ordering remains unchanged: Generate is still before Advanced;
the prior live `1280 x 720` measurement remains the layout evidence, while the
P2 History controls are below the Create workspace.

## Backend, persistence, and explicit non-scope

- Backend/API changes: none. Existing `GET /api/references/<id>` is used only
  for availability verification.
- Workflow changes: none. Existing H1A, H1B, and H1B.1 workflows remain intact.
- Models/dependencies: none. No package, framework, model download, or shared
  ComfyUI change.
- History persistence: none. History remains session-only and disappears after
  server restart by design.
- Reference files: no copy, filesystem scan, or new upload is created by reuse.
- Manga/shared runtime: none.
- Explicitly not started: Continuation, Segment, REF2VA, ordered generic
  multi-reference, Still, Timeline, Storyboard, Project, Shot, Take, Studio,
  and Manga work.

## Current gate

H1B.1 UX P2 is implemented and technically verified within the bounded scope.
The current gate is Web GPT / Astra review of this P2 report and evidence.
Owner acceptance remains `PENDING`; technical or Browser evidence does not
replace Owner acceptance.
