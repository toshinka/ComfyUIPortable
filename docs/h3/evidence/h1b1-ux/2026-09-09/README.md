# H1B.1 UX Integrity P0 Fix Evidence — 2026-09-09

Status: `IMPLEMENTED`, `VERIFIED LOCAL STARTUP`, `VERIFIED SOURCE/STATIC
CONTRACT`, and `PARTIALLY VERIFIED BROWSER UI`.

Owner acceptance: `PENDING`.

This small evidence package records the H1B.1 UX integrity fix requested after
the Astra bounded review. It covers only Reference-slot visibility and the
separation of active execution state from History preview selection. It is
technical evidence, not visual-quality approval or Owner production
acceptance.

## Scope and implementation

- Astra review verdict: `KEEP WITH ADJUSTMENTS`.
- P0-A: `hidden` Reference containers now have an explicit targeted
  `display: none` rule, so each slot shows either its empty message or its
  selected controls.
- P0-B: `state.activeJob` owns polling, generation status, Cancel, and
  Generate availability. `state.previewJob` owns only the selected Preview.
- Implementation commit:
  `12942d04e5baa8c882a265a1d21fc34bf910da58`.
- No server/API, workflow, model, dependency, shared ComfyUI, or Manga files
  changed.

## Browser record

The live in-app browser used `http://127.0.0.1:8190/` on 2026-09-09 JST.

### P0-A initial empty state

The initial page showed:

- `No Start Frame selected.` and `Add image` for Start Frame;
- `No End Frame selected.` and `Add image` for End Frame;
- `#reference-selected` and `#end-reference-selected` with
  `hidden=true`, computed `display:none`, and zero-sized rectangles;
- the shared `No keyframes selected` message.

The browser screenshot was emitted in the live CUA transcript. It was not
persisted as a PNG binary in this repository; no placeholder image is claimed
as evidence.

The earlier H1B.1 browser evidence already covers real Add/Replace/Remove
interaction and selected-state rendering. This fix did not alter the upload
API or the selected-state markup; the new targeted rule only restores the
intended hidden semantics for the empty state.

### P0-B active completion

One new real browser generation was used, within the requested maximum:

| Field | Value |
|---|---|
| Route | `Text only` / `native_t2v` |
| Job id | `1ccfa3b536d2412a9248f9848dfc41ae` |
| Prompt id | `a92a9345-3ad1-45d1-9605-b8062dbad4fe` |
| Request | 608 x 352 / 5 seconds / 20 steps |
| Result | `COMPLETED` |
| Elapsed | 242.78 s |
| Ignored output | `output/h3/video/h1a_native_t2v_00005_.mp4` |
| Output bytes | 183,034 |
| Output SHA-256 | `47F29CC314BCCC81E760A8F01B733E4811458D8F9B3CBFB00AFBD1A09F40B5E7` |

At start, the browser showed `Running`, `Cancel current job`, disabled
`Generate`, and a `Running` Preview overlay. At completion it showed
`Completed`, `Preview ready.`, enabled `Generate`, hidden Cancel, one History
entry, and a playable Preview. Selecting that History entry kept the current
status and Generate/Cancel state unchanged.

The complete `Running + an older Completed History entry` scenario was not
replayed in this run: restarting the local server cleared its in-memory
session History, and the one-generation cap was used for the completion check.
The source contract and static smoke cover that History click path; this
limitation is intentionally recorded rather than inferred away.

## Automated checks

| Check | Result |
|---|---|
| Python unittest discovery | `32 passed` |
| H1B.1 UX source smoke | `34 PASS` |
| JavaScript syntax | `node --check h3/app/static/app.js` passed |
| Python syntax | `compileall` passed |
| `git diff --check` | passed |

## Layout remeasurement

The live CUA browser exposed a CSS viewport of `1280 x 720` (the in-app
browser did not provide a 1366 x 768 viewport override). After P0-A, the
`Generate` button measured `top=918.6px`, `bottom=966.6px`; it is below the
initial viewport. The right control column is capped at 390px for both widths,
and the P0-A rule changes no vertical spacing, so the target-width result is
expected to remain below the `768px` fold. This is recorded as a bounded
remeasurement, not as a direct 1366 x 768 browser claim.

Astra SHOULD ③ therefore remains `OPEN / DEFERRED`; no sticky Generate or
layout redesign was added. SHOULD ④ (Cancelled/Disconnected wording) and
SHOULD ⑤ (History `Use settings`) remain deferred.

## Explicit non-scope and review gate

This fix does not start Continuation, Segment, REF2VA, ordered generic
multi-reference, semantic references, Still, Timeline, Storyboard,
Project/Shot/Take, Studio, Manga integration, new dependencies, model
downloads, workflow edits, shared ComfyUI edits, or persistent project
storage. H1B.1 remains the current stage. The package is ready for bounded Web
GPT / Astra review; Owner acceptance remains `PENDING`.
