# H1B.1 UX P2 — Status / History reuse evidence

Date: 2026-09-09

Status: `VERIFIED SOURCE/LOGIC + PARTIAL BROWSER ACCEPTANCE`

Stage: `H1B.1 / Start + End Frame / Native FL2VA vertical slice`

Implementation commit: `8084c6a340aca2f6b94bbd2cfced831117810502`

Report: [H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md](../../../reports/H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md)

Owner acceptance: `PENDING`

## Scope

This package records the bounded P2 changes:

- state-specific Active and Preview copy for `QUEUED`, `RUNNING`,
  `COMPLETED`, `FAILED`, `CANCELLED`, and `DISCONNECTED`;
- History `Use settings` as a quiet secondary action;
- atomic restore of current form settings using existing public History
  metadata and existing reference preview routes;
- P0 active-job / Preview separation and P1 Generate ordering regression checks.

No backend/API, workflow, model, dependency, persistence, shared ComfyUI, or
Manga change belongs to this package.

## Browser record

Browser target: `http://127.0.0.1:8190/` in the Codex in-app browser.

The new UI server had a fresh in-memory session, so one Text-only generation was
used to create a real History entry. No reference upload was performed in this
pass. The completed job was:

| Field | Value |
|---|---|
| Job id | `8189245dd90644aeaa42090d7c99bece` |
| Prompt | `A small paper kite drifts across a warm evening sky, gentle motion, clean illustrative style.` |
| Route | `Text only` / `native_t2v` |
| Resolution / Duration | `608 x 352` / `5s` |
| Seed / Steps | `24680` / `20` |
| Elapsed | `146.94s` |
| MP4 | `output/h3/video/h1a_native_t2v_00006_.mp4` (ignored, not committed) |
| SHA-256 | `663C6927B02242DC1275D81F7CBF36A23197678EE6F0D4DD68C876622883E951` |

The live sequence was:

1. Complete the Text-only generation and observe the History card.
2. Change Prompt and Seed in the Create form.
3. Press `Use settings`.
4. Observe the original Prompt and numeric Seed `24680` restored, Resolution
   `608x352` and Duration `5` retained, and `Settings loaded.` announced in
   `#history-action-status`.
5. Observe both Start/End selected containers remain hidden for the Text-only
   entry.
6. Press the History result title and observe Preview selection without form
   mutation.

The final Browser DOM result was `PASS` for this Text-only path. The final
viewport was `864 x 520`; the prior P1 `1280 x 720` layout measurement remains
the primary-action evidence. A final History-card screenshot was emitted in the
CUA transcript but was not persisted as a PNG file.

## Automated contract record

- `python -m unittest discover -s h3/tests -p 'test_*.py'`: `32 passed`.
- `node h3/tests/verify_h1b_ui.mjs`: `36 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs`: `44 PASS`.
- JavaScript syntax checks for `app.js`, `history-settings.js`, and
  `job-status-copy.js`: `PASS`.
- The P2 logic smoke covers Text-only, Start-only, End-only, Start+End, legacy
  Start metadata, numeric Seed, current-option mismatch, missing Reference,
  no partial resolver result, no new job state, and no `/api/generate` from
  `Use settings`.

The reference-bearing paths were not made to pass through a destructive missing
file scenario. The automated verifier injects a missing End Reference failure
and confirms that no restored settings are returned; the UI handler applies
only after resolver success.

## Boundary

History remains session-only. Restart discovery and persistence are intentionally
not part of H1B.1 UX P2. Start/End live restore remains a follow-up Browser
acceptance item for a session with existing reference assets; it is not a new
capability gate.
