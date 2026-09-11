# H3-R1A — Wide Stage Action Bar

TEGAKI_REPORT_V1
CARD_ID: H3-R1A
RESULT: PASS WITH LIMIT

## Scope

H3 UI only. The existing Generate dock was responsively reparented into a
compact Stage-top Action Bar on Wide layouts and back into the Create action
area on Narrow layouts. The native form association and single submit path
were preserved.

## Browser acceptance

- Wide: PASS on the local H3 page at `http://127.0.0.1:8190/`.
  The available in-app Browser surface rendered the Wide layout at
  approximately 1265x711. Stage actions appeared above Preview, with the
  truthful Ready status and exactly one Generate action. The Inspector began
  with Create and Prompt; no topbar, History, or nested-scroll overlap was
  visible.
- Video: PASS in the Wide Browser review.
- Still: PASS for the mode switch and Stage-top structure in the Browser AX
  review; no generation was submitted.
- Prep/Edit: PASS through the bounded static UI verifier; no live generation
  or backend interaction was performed.
- Narrow 390x844: PASS WITH LIMIT. The responsive source contract verifies
  that the Stage-top bar is hidden, the existing Generate dock returns to the
  Create area, and status returns to the existing status strip. A direct
  narrow visual viewport could not be opened because the Browser tool rejected
  the non-page wrapper URL under its security policy.
- Exact 1440x900 / 390x844 viewport overrides and a live scroll-through check
  were not available in the Browser tool. This is the only acceptance limit.

## Contract checks

- Exactly one `generate-button` remains in the DOM.
- Wide Generate is associated with `generate-form` and remains keyboard
  accessible.
- Wide action placement uses the existing dock; no duplicate submit handler or
  payload change was introduced.
- Narrow Create / Result ownership remains unchanged by the mount logic.
- `activeJob` and `previewJob` semantics and status copy were not changed.
- No Finalizing label, fabricated percentage, ETA, or real generation was
  introduced. Authorized real generations: `0`.

## Validation

- `node --check ComfyUIPortable/h3/app/static/app.js`: PASS
- H3-R1A Stage / Generate visibility verifier: `61 PASS`
- Existing H3 static UI verifiers: PASS
- `git diff --check`: PASS
- Runtime/backend/workflow/model changes: NONE
- Manga changes: NONE

## Publication

Local commit only. Push was intentionally not performed per H3-R1A.
