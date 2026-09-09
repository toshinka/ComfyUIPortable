# H1B.1 UX Integrity P0 Fix Report

Date: 2026-09-09 JST
Stage: `H1B.1 / Start + End Frame / Native FL2VA vertical slice`
Astra H1B.1 review verdict: `KEEP WITH ADJUSTMENTS`
Owner acceptance: `PENDING`

## Summary

This bounded fix addresses only the two Astra P0 findings: empty Reference
slot visibility and the accidental coupling of Active Job execution state to
History Preview selection. The H1B.1 capability boundary remains unchanged.

## P0-A — Reference visibility

`h3/app/static/styles.css` now explicitly honors the existing HTML `hidden`
attribute for `.reference-slot-empty` and `.reference-selected`. The existing
`setReferenceSlotView()` state transitions remain the authority:

- empty slot: empty message visible, selected controls hidden;
- selected slot: thumbnail/metadata/Replace/Remove visible, empty message
  hidden;
- Remove returns the slot to the empty state.

No Reference-card redesign, spacing reset, typography change, or upload/API
change was made.

## P0-B — Active Job / Preview separation

`h3/app/static/app.js` now keeps two explicit state objects:

| Concern | Authority |
|---|---|
| Poll target | `state.activeJob` |
| Cancel target | `state.activeJob` |
| Current generation status | `state.activeJob` |
| Running/terminal Generate availability | `state.activeJob` |
| Preview selection and metadata | `state.previewJob` |
| History click | `showPreviewJob(entry)` only |

History selection no longer replaces the active job or changes its poll/cancel
target. Active-job completion still selects the newly completed result as the
Preview, preserving the existing H1B.1 completion behavior. Failed and
cancelled active jobs remain active authority until a later Generate replaces
them.

## Verification

Automated checks passed after the implementation commit:

- Python tests: `32 passed`;
- H1B.1 UX source smoke: `34 PASS`;
- `node --check h3/app/static/app.js`: passed;
- Python `compileall`: passed;
- `git diff --check`: passed.

The source smoke explicitly asserts `activeJob`/`previewJob`, active polling,
History-only Preview selection, and the targeted CSS visibility rules. It also
asserts that `state.currentJob` is no longer used.

## Browser acceptance

The live in-app browser verified the initial empty Reference state and one
real, text-only Native generation. At the initial page, both selected
containers were `hidden=true`, computed `display:none`, and zero-sized while
both Add buttons and empty messages were visible. The real job reached visible
`Running` and then `Completed` states; while Running, Generate was disabled and
Cancel was shown. On completion, History contained one result and Generate
became enabled. Selecting that result did not alter the displayed status or
Generate/Cancel state.

The exact `Running + older Completed History` interaction was not replayed in
this run because the local server's in-memory History was empty after restart,
and the instruction capped new real generations at one. The code path is
covered by the source contract and remains a targeted Web GPT review point.
Existing H1B.1 browser evidence covers the unchanged Add/Replace/Remove
interaction path.

## 1366 x 768 remeasurement

The CUA in-app browser exposed `1280 x 720`; no viewport override was
available. At that live viewport, after P0-A, the Generate button measured
`top=918.6px` and `bottom=966.6px`, so it was below the initial fold. The
control column is capped at 390px at both target widths, and the P0-A CSS rule
does not alter vertical flow. The 1366 x 768 target is therefore expected to
remain below fold, but this report does not mislabel that inference as a
direct 1366 x 768 browser measurement.

Astra SHOULD ③ remains `OPEN / DEFERRED`. No sticky Generate was introduced.
Astra SHOULD ④ (Cancelled/Disconnected wording) and SHOULD ⑤ (History `Use
settings`) are deferred.

## Boundary and current gate

No workflow, model, dependency, server/API, shared ComfyUI, or Manga change
was made. Continuation, Segment, REF2VA, ordered generic multi-reference,
semantic references, Still, Timeline, Storyboard, Project/Shot/Take, Studio,
and Manga remain out of scope. H1B.1 remains the Capability Stage.

Implementation commit:
`12942d04e5baa8c882a265a1d21fc34bf910da58` (`fix(h3): separate active job
from history preview`).

Evidence: [H1B.1 UX integrity evidence](../evidence/h1b1-ux/2026-09-09/README.md)
Current gate: bounded Web GPT / Astra review of H1B.1 UX P0 Fix.
Owner acceptance remains `PENDING`; publication or technical PASS is not
Owner acceptance.
