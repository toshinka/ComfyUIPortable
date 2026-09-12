# H3-PLAY1 Playable Controls Implementation Report

Date: 2026-09-12
Result: PASS WITH LIMIT
Executor: ASTRA
Publication: LOCAL ONLY; push and merge forbidden and not performed.

## Isolation and scope

- Exact base: `e835892635d5323d1160765c6e56a9e42db2772b`.
- Isolated worktree: `D:\GitHub\tegaki-h3-play1`.
- Local branch: `h3-play1-longrun`. Both path and branch were absent before creation.
- Original working tree was clean at entry and at final scope check, at `dfc349e53ef460edff24afa61a2dda8f7798fcac`. No original worktree files were edited or cleaned.
- Changed product files: **9**, plus five direct test files and this report.
- Manga, EasyReforge, shared shell, launchers/lifecycle, Director, timeline and continuation implementation: no changes.
- Real H3 generations: **0**. No Native generation request or model acquisition was performed.

## Delivered controls

One initially collapsed **Advanced** contains Resolution, Duration, Model and optional LoRA, followed by the existing Seed and read-only 20 Steps controls. The simple Prompt / optional Reference / Generate flow is retained.

| Control | Implemented values |
|---|---|
| Video resolution | 512 x 288 (Experimental Small), 608 x 352 (Default), 736 x 416 (Large) |
| Video duration | 3, 5 (default), 10, 15 seconds; semantic product maximum 15 |
| Model | Filtered Native UNETLoader capability names, independently selected for Standard and Reference |
| LoRA | 0–3 ordered Native model-only entries; file + finite strength in [-2, 2], initial strength 1 |
| Still | Existing 608 x 352 / 20 steps / current model and source contract |

All video routes share the same resolution and duration enumeration. Ref2VA motion slicing uses the selected duration and preserves optional motion start. The existing duration-to-frame function remains the authority: 3/5/10/15 seconds map to 73/124/243/362 frames on the 17k+5 grid. Labels are nominal durations, with existing grid rounding retained.

Small 512 x 288: **IMPLEMENTED**. Both dimensions fit the existing semantic workflow and Native 32px input grid. Read-only inspection of the installed Native `nodes_minimax_h3.py` confirmed min/step 32 and the existing latent dimension handling. This is structural evidence; no Small output quality or GPU memory claim is made.

## Model and capability boundary

`GET /api/config` includes a filtered, server-owned `playable` capability record. Production data comes from Native `/object_info` after the existing canonical profile status check. No browser graph, node identifiers or arbitrary filesystem paths are accepted for these controls.

Candidates are Native UNETLoader names whose basename identifies MiniMax H3 FL2VA or Ref2VA and ends in `.safetensors`. Other model families, VAE/text encoders, absolute paths, parent traversal and GGUF names are excluded. Native relative subfolder names remain exact metadata values; they are not arbitrary user paths. Filtering is conservative filename-family filtering, not weight-content inspection.

Preserved defaults:

- Standard / Start-End: `minimax_h3_fl2va_pruned_int8_convrot.safetensors`.
- Reference: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`.

Every explicit selected request re-reads Native capability and validates model family and membership before graph compilation. The existing BackendClient submit profile check still runs before `/prompt`. Missing/stale/wrong-family selection raises an error without submitting, creating a retained job, or substituting a default. Browser controls and History preserve stale selected names so the user can correct them explicitly. Existing requests without a selection retain the baseline adapter behavior and Native validation.

Reference availability uses the verified Native Ref2VA candidate set, so an available compatible alternative does not require the default filename to exist. Existing Native node/profile guards remain in effect.

## LoRA result

**Live Native capability: UNVERIFIED.** The read-only request to `http://127.0.0.1:8188/object_info` was connection-refused. Native was not launched for this Card.

**Implementation: IMPLEMENTED, capability-gated.** Deterministic tests and the Browser fixture exercise the available capability path. The accepted native schema is exactly `LoraLoaderModelOnly` with MODEL input/output, enumerable lora_name and FLOAT strength_model supporting the requested range; incompatible or absent schemas disable the stack and display `Unavailable for this Native profile`. Unreachable/unverified Native is identified separately and also disables adding LoRAs. No custom loader or dependency was added.

The adapters insert a deterministic ordered chain and rewire the existing model consumers (scheduler and guider). Text encoding is unchanged. Zero LoRA leaves the baseline graph and model edge unchanged. Unknown files, invalid strength, more than three entries and unavailable loader capability fail closed. Model/LoRA selections are separate for Standard and Reference and do not leak into Still/Prep payloads or form validation. A refresh button updates available names without replacing retained selections.

LoRA tensor compatibility, actual application/effectiveness, generation performance and quality require the following real runtime Card. The Native file list is not proof that every listed LoRA belongs to H3.

## Validation

- Before implementation: all **123 Python tests PASS**; all **13 existing Node verifiers PASS**.
- Final Python suite: `python -B -m unittest discover -s h3/tests -p 'test_*.py'` — **137 tests PASS** in 68.811 seconds.
- New deterministic adapter/server coverage: **14 tests PASS**. A–O covered by exact-base graph hashes, all size/duration combinations on Standard/Start/End/Start+End/Ref2VA picture and motion routes, model loader override, fresh submit-time disappearance/profile rejection, 0/1/2/3 LoRA chains and invalid requests. Existing Still and Source Still tests remain in the full suite.
- Exact-base graph hashes were independently generated from unmodified adapters/workflows extracted from the specified base into a temporary directory. Standard, Start, End, Start+End, Ref2VA picture, Ref2VA motion and Still remain identical at 608 x 352 / 5 seconds where applicable, including explicit default model + empty LoRA.
- All **14 Node verifiers PASS**, including the new production-function DOM fixture for LoRA ordering, three-entry limit, model change, stale choice retention, route separation, hidden Still controls, History and semantic payloads.
- Python syntax compilation, `node --check` for both changed JS files, and `git diff --check`: PASS.
- No separate H3 bundler exists for these directly served static assets; actual Skin serving and Browser operation were checked.

Windows test environment notes: the initial sandboxed Python run could not create the isolated worktree's scratch_output; rerunning with authorized worktree write access passed. The existing R1 Node verifier assumes LF inside literal CSS snippets, whereas checkout uses CRLF. Node verification used a temporary import hook that only normalizes string reads from CRLF to LF (`fs/promises.readFile`, followed by `syncBuiltinESMExports`). No old verifier or repository line-ending configuration was changed for this accommodation. Existing enum tests were updated only where this Card intentionally supersedes their old 5/15 or fixed Ref2VA expectations.

Browser evidence: Codex in-app Browser served the isolated Skin at 8190 with fixture capability data, actual Native disconnected, and all generation endpoints explicitly disabled by a temporary external test harness. Confirmed Advanced initially collapsed, default 608 x 352 / 5 seconds, all options, Small / 3 seconds / alternate FL2VA selection, LoRA strength 0.8, three-entry Add disabled, Ref2VA model-family switch, Still hiding video controls, and restoration of Standard settings after switching back. Screenshot inspection showed usable controls; captured Browser error/warning logs were empty. No Generate was clicked. The fixture and tab were closed using their own handles; server process exited 0. A pending status request aborted when the test tab closed; this was teardown only. This is Browser fixture evidence, not real Native acceptance or Owner acceptance.

## Exact changed files

Paths below are relative to the isolated repository root `D:\GitHub\tegaki-h3-play1`.

Product (9):

1. `ComfyUIPortable/h3/adapters/native_t2v.py`
2. `ComfyUIPortable/h3/adapters/native_i2v.py`
3. `ComfyUIPortable/h3/adapters/native_ref2va.py`
4. `ComfyUIPortable/h3/adapters/playable_controls.py` (new)
5. `ComfyUIPortable/h3/app/server.py`
6. `ComfyUIPortable/h3/app/static/index.html`
7. `ComfyUIPortable/h3/app/static/app.js`
8. `ComfyUIPortable/h3/app/static/styles.css`
9. `ComfyUIPortable/h3/app/static/history-settings.js`

Tests (5):

1. `ComfyUIPortable/h3/tests/test_play1_playable_controls.py` (new)
2. `ComfyUIPortable/h3/tests/verify_play1_playable_controls.mjs` (new)
3. `ComfyUIPortable/h3/tests/test_vp1_video_envelope.py`
4. `ComfyUIPortable/h3/tests/test_vp2a_ref2va_adapter.py`
5. `ComfyUIPortable/h3/tests/test_vp2b_r2v_playground.py`

Report (1):

- `ComfyUIPortable/docs/h3/reports/H3_PLAY1_PLAYABLE_CONTROLS_IMPLEMENTATION_REPORT.md`

## Limits and handoff

Real Native model/LoRA capability, new preset output quality and runtime generation remain unverified. The isolated Git worktree does not copy ignored Native installation, local model paths or weights; provision the appropriate local validation environment without editing the original worktree. Native 8188 / Skin 8190 defaults, profile validation code, local model-path preference, queue truth, job state, seed semantics and history ownership remain in place.

One local commit on `h3-play1-longrun` contains this report and the files above. Its SHA is returned in the chat report (the commit cannot embed its own hash). No push, merge or Owner acceptance is claimed.

Recommended next: **SOL AUDIT -> CODEX H3-PLAY1 REAL RUNTIME VALIDATION**.
