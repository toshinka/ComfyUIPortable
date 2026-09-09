# H1B.1 UX P1 — Primary Action Visibility / Control Column Compaction

Date: 2026-09-09

Stage: `H1B.1 / Start + End Frame / Native FL2VA vertical slice`

Astra review status: `KEEP WITH ADJUSTMENTS`

Owner acceptance: `PENDING`

## Summary

This bounded P1 follow-up closes Astra SHOULD ③ for the primary
`1280 x 720` target. The initial H1B.1 creation line now exposes Prompt,
Reference, Resolution/Duration, and the complete Generate button without
scrolling. The fix uses information cleanup, action ordering, and modest
vertical compaction. It does not introduce sticky UI or a broader layout
redesign.

## Before measurement

The live CUA browser measured a CSS viewport of `1280 x 720`, with empty
Reference slots and collapsed Advanced:

| Element | Top | Bottom |
|---|---:|---:|
| Prompt | 173.7 px | 367.4 px |
| Reference | 411.0 px | 743.5 px |
| Resolution / Duration | 761.5 px | 829.6 px |
| Advanced | 848.6 px | 896.6 px |
| Generate | 918.6 px | 966.6 px |

Generate was therefore outside the initial viewport.

## Changes

1. Removed the redundant parent `No keyframes selected` message. The parent
   `Reference` heading, helper text, and explicit Start/End slot messages
   remain, so Reference meaning and the two fixed roles are preserved.
2. Moved Generate and the adjacent Cancel button above the Advanced details
   element. Advanced remains available and still contains the unchanged Seed
   and Steps controls.
3. Reduced Prompt from seven to five rows and lowered only its CSS minimum
   height; this retains a readable multiline prompt field.
4. Applied modest spacing reductions to the control column, Reference card,
   empty slots, status reserve, Resolution/Duration gap, and Generate margin.
   The primary button remains 48px high; Reference Add/Replace/Remove hit
   areas and labels were not reduced.

These changes are limited to `h3/app/static/index.html`,
`h3/app/static/styles.css`, the now-unused P0 parent-state cleanup in
`h3/app/static/app.js`, and the H1B.1 UI source smoke. No Preview size or
control-column width change was used.

## After measurement

With the same `1280 x 720` initial state:

| Element | Top | Bottom | Height |
|---|---:|---:|---:|
| Prompt | 169.7 px | 315.4 px | 145.8 px |
| Reference | 355.0 px | 579.0 px | 224.0 px |
| Resolution / Duration | 589.0 px | 657.1 px | 68.1 px |
| Generate | 669.1 px | 717.1 px | 48.0 px |
| Advanced, collapsed | 736.1 px | 784.1 px | 48.0 px |

Generate is completely visible without scrolling. The live Browser screenshot
is recorded in the CUA transcript; it was not persisted as a PNG artifact.

## Advanced behavior

Opening Advanced keeps Generate before it. The browser's focus handling moved
the viewport to `scrollY=400`, but the document coordinates of Generate stayed
`669.1–717.1px`; Advanced expanded below the primary action. This is the
intended optional-control behavior.

## Reference and P0 regression

The P0 empty/selected visibility rule remains in force. In the final initial
state, both `#reference-selected` and `#end-reference-selected` were hidden
with zero-sized rectangles, while both slot-level empty messages and Add
buttons were visible. The existing selected-state markup and Add/Replace/
Remove behavior were not redesigned.

The P0 job-state separation remains unchanged: `activeJob` continues to own
polling, status, Cancel, and Generate availability; `previewJob` continues to
own Preview selection. The source smoke still asserts that History selection
does not replace the active job.

## Verification

- H1B.1 UX P1 source smoke: `36 PASS`.
- Python unittest discovery: `32 passed`.
- `node --check h3/app/static/app.js`: passed.
- Python `compileall`: passed.
- `git diff --check`: passed.
- No Browser generation rerun; the P1 acceptance is layout-only.

## Deferred findings and boundary

Astra SHOULD ③ is `CLOSED` for the primary `1280 x 720` acceptance target.
SHOULD ④ (Cancelled/Disconnected wording) and SHOULD ⑤ (History `Use
settings`) remain deferred. No sticky action area was required.

No backend/API, Native adapter, workflow, model, dependency, shared ComfyUI,
or Manga change was made. Continuation, Segment, REF2VA, Still, History `Use
settings`, and all broader Studio/Timeline/Storyboard/Project/Shot/Take/Manga
work remain out of scope. H1B.1 remains the current Capability Stage.

Implementation commit:
`247296b626f3e87e46e64c745180712497038f2a` (`fix(h3): keep primary Generate
action above the fold`).

Evidence: [H1B.1 UX P1 layout evidence](../evidence/h1b1-ux-p1/2026-09-09/README.md)

Current gate: bounded Web GPT / Astra review of H1B.1 UX P1.

Owner acceptance remains `PENDING`; technical PASS does not constitute Owner
acceptance.
