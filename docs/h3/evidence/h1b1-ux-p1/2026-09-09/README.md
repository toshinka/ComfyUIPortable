# H1B.1 UX P1 Primary Action Visibility Evidence — 2026-09-09

Status: `IMPLEMENTED` and `VERIFIED BROWSER LAYOUT`.

Owner acceptance: `PENDING`.

This is a small layout evidence package for the H1B.1 UX P1 follow-up. It
covers only primary Generate visibility and modest control-column compaction.
It does not add a generation capability or change Native execution.

## Implementation boundary

- Current stage remains `H1B.1 / Start + End Frame / Native FL2VA vertical
  slice`.
- Implementation commit:
  `247296b626f3e87e46e64c745180712497038f2a`.
- Generate and Cancel now appear immediately before the collapsed Advanced
  panel.
- The redundant parent `No keyframes selected` line was removed; the
  Start/End slot messages remain.
- Prompt and empty Reference spacing were compacted modestly. Button sizes,
  labels, Start/End meaning, Preview priority, and P0 state authorities were
  retained.
- No sticky/fixed action area was needed.

## Browser measurement

The live in-app browser used `http://127.0.0.1:8190/` with a CSS viewport of
`1280 x 720`, `Reference` empty, and `Advanced` collapsed. No generation was
rerun for this P1 check.

| Element | Before | After |
|---|---:|---:|
| Prompt | 173.7–367.4 px | 169.7–315.4 px |
| Reference | 411.0–743.5 px | 355.0–579.0 px |
| Resolution / Duration | 761.5–829.6 px | 589.0–657.1 px |
| Generate | 918.6–966.6 px | 669.1–717.1 px |
| Advanced, collapsed | 848.6–896.6 px | 736.1–784.1 px |

At `1280 x 720`, the entire Generate button is visible without scrolling
(`bottom=717.1px`). Prompt, Reference, Resolution/Duration, and Generate are
all visible in the initial viewport.

The browser screenshot was emitted in the live CUA transcript but was not
persisted as a PNG binary in this repository. No placeholder image is claimed
as durable evidence.

## Advanced and regression checks

After opening Advanced, the browser auto-scrolled to keep the focused summary
visible, but the Generate document coordinates remained `669.1–717.1px`; the
Advanced content expanded below it. This confirms the primary action does not
move below optional controls.

The initial page also showed both slot-level empty messages while the selected
containers remained hidden. The P0 `activeJob` / `previewJob` source contract
was retained; no server, adapter, workflow, model, dependency, shared
ComfyUI, or Manga file changed.

The existing H1B.1 browser evidence covers selected Start/End interaction and
the fixed Start+End layout. This P1 check did not upload new files or rerun
Native generation.

## Automated checks

| Check | Result |
|---|---|
| H1B.1 UX P1 source smoke | `36 PASS` |
| JavaScript syntax | `node --check h3/app/static/app.js` passed |
| Python unittest discovery | `32 passed` |
| Python syntax | `compileall` passed |
| `git diff --check` | passed |

## Review gate

Astra SHOULD ③ (`Generate` below the initial viewport) is `CLOSED` for the
primary `1280 x 720` acceptance target. No sticky action was introduced.
SHOULD ④ (Cancelled/Disconnected wording) and SHOULD ⑤ (History `Use
settings`) remain deferred. H1B.1 remains ready for bounded Web GPT / Astra
review; Owner acceptance remains `PENDING`.
