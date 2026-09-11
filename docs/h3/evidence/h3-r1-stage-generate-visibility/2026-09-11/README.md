# H3-R1 Stage / Generate Visibility Evidence

Evidence date: `2026-09-11 JST`

Status: `IMPLEMENTED / VERIFIED BROWSER UI / PASS WITH LIMIT / PUBLISHED ON MAIN / OWNER ACCEPTANCE PENDING`

This package records the H3-only responsive Stage/Generate visibility slice.
The canonical skin was tested at `http://127.0.0.1:8190/` with the Native
backend at `http://127.0.0.1:8188/`. The Native launcher was the existing
canonical H3 profile. No Manga, shared-shell, supervisor, backend lifecycle,
workflow, schema, or runtime files were changed.

## Browser evidence

The rendered page was reviewed, not only queried through the DOM.

| View | Readback and rendered result |
|---|---|
| Wide `1440 x 900` | Preview Stage was dominant and visible beside the Create/Inspector column; the single Generate dock was visible near Create. Preview, status, and History retained separate bounds. |
| Narrow `390 x 844` Create | Create was the initial view; Result was a compact `aria-pressed` view control; Preview was hidden rather than stacked below the full form. |
| Narrow accepted Job | The accepted response selected Result; Stage showed active/completed media and status. |
| Narrow manual intent | Create selected manually after completion remained Create during a further 3-second observation; no focus was moved automatically. Explicit Result restored the completed image. |
| Responsive resize | `390 x 844 -> 1440 x 900 -> 390 x 844` retained prompt, seed, Still mode, completed Preview, and History count without a new request. |

At the wide viewport, the Stage and Generate behavior was also checked after a
long page scroll. The Stage remained bounded by the workspace rather than
becoming a page-wide fixed overlay, and the status/History surfaces did not
overlap it. The containing boundary naturally allows the workspace to leave the
viewport at the end of the page.

## Truthful status evidence

- `Submitting` is a client-only state and is source/logic verified to appear
  before the POST response, with immediate duplicate-submit blocking.
- The single real POST returned an accepted Job quickly; the immediate browser
  readback had already advanced to `Generating`, so no persistent screenshot is
  claimed for the short `Submitting` transient.
- `Generating` was visibly observed while the Native Job was running.
- `Completed` and truthful elapsed time were visible after completion.
- No `Finalizing`, fabricated percentage, or ETA was shown.

## One real generation

Exactly one H3 generation was submitted in this acceptance:

- Job: `997c4fee1efc4fb4a916b0d68d3d6bdf`
- Native prompt: `1e264b2f-ebcc-4160-bcf6-17bd2a109052`
- Route: `native_still`
- Media: prompt-only Still
- Prompt: `A small red paper boat floating on calm water, simple composition.`
- Request: `608 x 352`, `20` steps, seed `20260914`
- Observed elapsed: `86.46s`
- Output: `output/h3/still/h2a_native_still_00005_.png`
- Output SHA-256: `04E60C8D49A445FD559ED23C76BA9F7052ACBF24123DEC5C875AC4D70DE9A49D`
- History count: `2 -> 3`

The completed image was shown in the narrow Result Stage and in the H3 History
list. No upload or file-scheme permission was used.

## Deterministic and regression verification

- H3-R1 source/logic verifier: `48 PASS`
- IP2 Prep/Edit verifier: `45 PASS`
- VP2C Reference handoff verifier: `36 PASS`
- VP2B R2V verifier: `28 PASS`
- H2C Still verifier: `52 PASS`
- H1C continuation verifier: `38 PASS`
- H1B.1 UX P2 verifier: `44 PASS`
- Changed JavaScript syntax: `PASS`
- `git diff --check`: `PASS`

## Scope and publication

- Implementation: `h3/app/static/index.html`, `styles.css`, `app.js`,
  `job-status-copy.js`
- Added verifier: `h3/tests/verify_h3_r1_stage_generate_visibility.mjs`
- Backend/runtime/code outside the H3 static UI: `NONE`
- Manga files: `NONE`
- Shared-shell implementation: `NOT AUTHORIZED`
- Initial `origin/main`: `67b9396481d24be7b4bea51643d589c7a7b7ee28`
- Implementation commit: `988ea5db210bce386904ff24db974f8af996c3ac`
- Publication: `PUBLISHED ON MAIN` (verified `origin/main` and GitHub raw URLs)
- Owner acceptance: `PENDING`

The live Browser screenshots were used for visual review but are not persisted
as binary files in this package. The machine-readable details are in
`manifest.json`.

STOP.
