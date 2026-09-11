# H3-R1 Stage / Generate Visibility Report

Card: `H3-R1 — Stage / Generate Visibility Responsive Stage + Truthful Submission / Generation Status`

Result: `PASS WITH LIMIT`

This closeout covers the H3-only responsive Stage/Generate visibility slice. It
does not implement a shared shell, change the Native lifecycle, alter Manga,
or introduce new generation semantics. Owner acceptance remains `PENDING`.

## Baseline and scope

- Base `origin/main`: `67b9396481d24be7b4bea51643d589c7a7b7ee28`
- H3 skin: `http://127.0.0.1:8190/`
- Canonical Native backend observed: `http://127.0.0.1:8188/`
- Allowed implementation files: `h3/app/static/index.html`,
  `h3/app/static/styles.css`, `h3/app/static/app.js`, and
  `h3/app/static/job-status-copy.js`
- Added verifier: `h3/tests/verify_h3_r1_stage_generate_visibility.mjs`
- Backend/server/workflow/launcher/model changes: `NONE`
- Manga changes: `NONE`
- Shared-shell, shared supervisor, shared History, and cross-track handoff:
  `NOT IMPLEMENTED`

## Implemented contract

Wide layouts keep the existing H3 Preview column bounded and sticky within the
workspace while the Create/Inspector column grows naturally. The single
Generate action is in a small sticky action dock inside the H3 control form;
there is no duplicate Generate action and the Stage was not made a page-wide
fixed overlay.

Narrow layouts use the H3-only `Create` / `Result` segmented view. Create is
the initial view. Result is selected explicitly by the user or is selected
after a server-accepted Job response; validation and pre-submit failures stay
in Create and retain form values. Polling and completion do not call the view
switcher or focus an element, so a manual return to Create is preserved.

Submission and status behavior is truthful:

- `state.submitting` is client-only, set before the generation POST, and blocks
  repeated submits immediately.
- `Submitting` is shown only before an accepted Job exists.
- `state.submitting` clears on an accepted Job and on a pre-accept failure.
- Server `RUNNING` is displayed as `Generating`.
- Accepted vocabulary is `Submitting`, `Queued`, `Generating`, `Completed`,
  `Failed`, `Cancelled`, and `Disconnected`.
- `Finalizing`, fabricated percentages, and ETA language are not added.
- `activeJob` remains separate from `previewJob`, so History/Preview selection
  does not replace the active status authority.

## Browser acceptance

Acceptance used the canonical local H3 skin through the Codex Browser
CUA/Playwright path. No upload was used and exactly one real H3 generation was
submitted.

### Wide: `1440 x 900`

- Initial Preview Stage was rendered as the dominant left surface.
- The single Generate action was visible near the top of Create and remained
  findable while controls were scrolled.
- Preview, control, status, and History regions had separate natural bounds;
  the Stage did not overlay the topbar or History.
- Video, Still, and Prep/Edit mode changes remained H3-local UI changes and did
  not submit a generation or change the History count.

### Narrow: `390 x 844`

- Initial state was `Create`; `Result` was a clear, keyboard-accessible,
  `aria-pressed` view control.
- Create hid the Preview column instead of stacking a large Preview plus
  Inspector page. Prompt, mode, resolution, and Advanced controls remained
  usable.
- Explicit Result showed the Stage as the protagonist, with no duplicate
  Inspector below it.
- A `390 x 844` to `1440 x 900` to `390 x 844` resize preserved prompt, seed,
  Still mode, Preview result, and History count without submitting a request.

### One real Still generation

| Field | Observed value |
|---|---|
| Media | Still, prompt-only |
| Prompt | `A small red paper boat floating on calm water, simple composition.` |
| Resolution | `608 x 352` |
| Steps | `20` |
| Seed | `20260914` |
| Job ID | `997c4fee1efc4fb4a916b0d68d3d6bdf` |
| Native prompt ID | `1e264b2f-ebcc-4160-bcf6-17bd2a109052` |
| Observed running status | `Generating` |
| Observed completed status | `Completed` |
| Elapsed | `86.46s` |
| Output | `output/h3/still/h2a_native_still_00005_.png` |
| Output SHA-256 | `04E60C8D49A445FD559ED23C76BA9F7052ACBF24123DEC5C875AC4D70DE9A49D` |
| History | `2 -> 3`, exactly one new Still result |

The accepted Job immediately moved the narrow UI from Create to Result. While
the Job was running, the browser showed `Generating`, an active Cancel action,
and a disabled Generate action. After completion, the user-selected Create view
remained Create during a further 3-second observation; explicit Result then
showed the completed image, `Completed`, elapsed time, and the History result.

The `Submitting` state is implemented and covered by the deterministic source/
logic verifier. The Native POST response was faster than the browser readback,
so the post-click snapshot had already advanced to `Generating`; no claim is
made that a persistent screenshot captured the short transient. This is the
only bounded limitation in this report.

## Verification

- `node h3/tests/verify_h3_r1_stage_generate_visibility.mjs` — `48 PASS`
- `node h3/tests/verify_ip2_prep_edit.mjs` — `45 PASS`
- `node h3/tests/verify_vp2c_reference_handoff.mjs` — `36 PASS`
- `node h3/tests/verify_vp2b_r2v_ui.mjs` — `28 PASS`
- `node h3/tests/verify_h2c_still_ui.mjs` — `52 PASS`
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`
- `node --check` for changed H3 JavaScript — `PASS`
- `git diff --check` — `PASS`

The rendered Browser review verified wide Stage/Generate visibility, narrow
Create-first behavior, accepted-submit Result transition, manual Create intent
after completion, explicit Result restoration, running feedback, no fake
percentage, and no topbar/History layout overlap. The implementation does not
claim a new backend lifecycle or a Finalizing state.

## Integration and next gate

The cross-track plan remains the authority for architecture boundaries:

- H3 Stage UX: `ACCEPTED / R1 COMPLETED / VERIFIED BROWSER UI`
- Finalizing: `NOT ADOPTED`
- Runtime Lifecycle Feasibility: `NEXT GATE / OPEN`
- Manga Hosting Feasibility: `NOT STARTED / OPEN`
- Shared-shell implementation: `NOT AUTHORIZED`
- Cross-track asset handoff: `DEFERRED`

Publication is recorded separately from local verification. At report creation
time publication was `PENDING`; the final publication commit is recorded in the
evidence manifest and the final integration updates.

Owner acceptance: `PENDING`

STOP.
