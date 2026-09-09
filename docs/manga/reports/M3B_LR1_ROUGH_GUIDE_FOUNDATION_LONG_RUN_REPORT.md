# M3B-LR1 — Rough Guide Foundation Long-Run Report

Date: 2026-09-09 JST  
Card: `M3B-LR1`  
Milestone: `M3B-LR1 COMPLETED`  
Decision: `ACCEPTED_BY_DELEGATED_SOL` for the preceding M3A.1 gate; final Owner product review remains `DEFERRED`.

## Outcome

M3B-LR1 is technically complete for its bounded foundation slice. Contract validation, regression checks, live ComfyUI Browser R0–R8, runtime Guide bridge checks, and the requested visual evidence all pass. The Guide remains a page-owned authoring aid and has no generation influence.

## Implemented contract

- `page.guides[]` is optional and keeps the existing document schema version.
- Guide placement is page-normalized contain-fit geometry; Figure areas are Guide-local normalized geometry.
- Runtime derives page-space Figure areas and does not persist derived page geometry.
- Associations use `instance_id`; one Figure and one Character Instance can be paired at most once within a Guide.
- Unassigned Figures are legal. Deleting a Character Instance unassigns its Figure and preserves that Figure.
- Removing a Guide removes only the Guide entry; it does not mutate Character Instances or delete the uploaded asset.
- Asset references are canonical relative ComfyUI input-boundary paths with PNG/JPG/JPEG/WEBP validation and traversal/absolute-path rejection.
- No automatic interpretation or matching is performed.

## Implementation slice

- Python authoring contract validation in `custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py`.
- Pure Guide ID, contain placement, Figure drag/resize, creation, association, and unassignment operations in `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js`.
- Guide layer, standard upload, inspector, overlay preview, manual association, save/reload state, and deletion guards in `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js`.
- Render-only page image/mask/debug bridge in `custom_nodes_custom/tegaki_manga_nodes/rough_guide_bridge.py`, registered as `TegakiMangaRoughGuideBridge`.
- Canonical workflow wiring in `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` adds the bridge and preview output without connecting it to KSampler or ControlNet.

## Verification summary

| Gate | Result | Evidence |
|---|---|---|
| Contract | PASS | `scripts/test_m3b_lr1_contract.py`, 12/12 |
| Guide operations | PASS | `scripts/test_m3b_lr1_guide_ops.mjs` |
| Runtime bridge | PASS | `scripts/test_m3b_lr1_runtime_bridge.py`, 5/5 |
| Existing frontend regression | PASS | `scripts/test_m2b_minimum_hand_editor.mjs`, 19/19 |
| JS/Python syntax | PASS | `node --check`, `py_compile` |
| Canonical workflow JSON | PASS | JSON parse and link consistency check |
| Browser R0 | PASS | Canonical queue completed and produced `R0_CANONICAL_OUTPUT.png` |
| Browser R1–R8 | PASS | `docs/manga/verification/m3b_lr1/R1...R8_*.md` |
| Visual UI evidence | PASS | Live Guide inspector/overlay checks and R0 output view |

The live queue completed through `TegakiMangaConditioningBuilder` and `KSampler`, returned to Idle, and produced a `832x1216` output view. The output is baseline generation evidence only; it does not demonstrate Guide causality.

## Browser R0–R8 closeout

R1 confirmed the Guide layer and explicit optional empty state. R2 confirmed standard upload and contain placement. R3 confirmed two manually created Figures and manual `figure_1 -> inst_1`, `figure_2 -> inst_2` associations. R4 confirmed Guide-local drag and resize isolation from Character geometry. R5 confirmed save/reload persistence. R6 confirmed deletion unassigns while preserving the Figure. R7 confirmed disable preserves authored Guide data. R8 confirmed Guide removal preserves Scene, Frame, Character Instance, and the uploaded file.

During R4, a real zoomed-canvas issue was found: resize hit testing used backing canvas dimensions while pointer coordinates were CSS pixels. The bounded fix switched hit testing to the rendered CSS dimensions and was reverified in a fresh live browser tab.

## Explicit non-scope

- `generation_influence`: `NOT_IMPLEMENTED`
- `controlnet`: `NOT_ADDED`
- Automatic Guide interpretation/matching: `NOT_PERFORMED`
- ControlNet, pose estimation, OpenPose, AI detection/segmentation, M4, Shell integration, and H3: not started.

## Authority and acceptance

The delegated SOL milestone decision remains `ACCEPTED_BY_DELEGATED_SOL`. This report records technical and Browser evidence only. It does not mark Owner product acceptance. Final Owner product review remains `DEFERRED`; no push was performed.

The current authority is this report and the completed M3B-LR1 card. The LR1 card was moved from current to completed byte-identically; Active Card is `NONE`, and no next card is issued automatically.
