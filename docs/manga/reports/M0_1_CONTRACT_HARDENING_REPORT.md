# M0.1 / Phase 3M-0.1 Contract Hardening & Legacy Boundary Truth Report

2026-09-06 JST

## 1. Baseline Fixed SHA

- Baseline Review Target: `5e57ae2f4f685e78e1b2b911baccb0a6b69292d1` (M0 Implementation Commit)
- Baseline Navigation Commit: `9e60c83a5fbf850f13ee0c2a81c57d5b5c82a2ed` (M0 Navigation Commit)
- Execution Model: Gemini 3.8

## 2. Web GPT Review Findings Summary

M0 established the core architecture (`TEGAKI_AUTHORING_DOCUMENT` v1.0.0, Scene/Frame separation, page-normalized coordinates, stable IDs, pure operations), but web review identified contract boundary gaps where the contract was not fail-closed under specific edge cases or claimed stronger guarantees than implemented:

1. **Finding A (BLOCKER)**: Foreign key validation bug where empty `cast_ids` or `scene_ids` allowed orphan references like `cast_id="ghost"` to pass silently.
2. **Finding B (BLOCKER)**: `import_from_legacy()` did not run `validate_document()` and allowed orphan character bindings without CAST entries to produce unvalidated documents.
3. **Finding C (MAJOR)**: `export_to_legacy()` claimed to validate VisualFrames and fail closed on divergence, but in fact ignored visual frames and silently exported only `scene.area`.
4. **Finding D (MAJOR)**: `page_normalized_to_koma_local` silently clamped coordinates to `[0, 1]`, altering geometry when instances extended outside scene boundaries during legacy export.
5. **Finding E (MAJOR)**: `move_scene()` applied requested `(dx, dy)` and then clamped scene and instances individually, breaking the "same delta" contract near page boundaries.
6. **Finding F (MAJOR)**: `resize_scene()` clamped instance areas individually, distorting proportional relationships when resized instances exceeded page bounds.
7. **Finding G (SHOULD FIX)**: `validate_document()` did not detect duplicate `page_id` values across pages in a document.
8. **Finding H (MINOR)**: `make_area()` docstring claimed to validate areas when it only rounded numbers.
9. **Finding I (MINOR)**: `move_frame()` delta clamping lacked explicit bounding semantics.

## 3. FK Empty-Collection Bug Fix (Finding A)

- **Root Cause**: `elif cast_ids and ref_cast not in cast_ids:` evaluated to `False` when `cast_ids` was an empty set.
- **Fix**: Removed the `cast_ids and` and `scene_ids and` conditions. Now `ref_cast not in cast_ids` and `ref_scene not in scene_ids` are evaluated unconditionally.
- **Verification**: Tested with 0 CAST entries + 1 instance referencing `"ghost_cast"`, and 0 Scene entries + 1 instance referencing `"ghost_scene"`. Both fail closed immediately.

## 4. Legacy Import Validation & Orphan Policy (Finding B)

- **Root Cause**: `import_from_legacy()` did not enforce `validate_document()` at completion, and allowed bindings referencing non-existent CAST members without reporting an error.
- **Fix**:
  1. `MigrationResult` now carries `errors: List[str]` and `valid: bool`.
  2. If a legacy binding references a character not in `cast_spec`, it adds an error and marks `valid = False` (fail closed; no placeholder creation, no silent discard).
  3. `validate_document(doc)` is executed at the end of `import_from_legacy()`, merging validation errors and warnings.
  4. Added pairing metadata: `scene["metadata"]["paired_frame_id"]` and `frame["metadata"]["paired_scene_id"]`.

## 5. Legacy Export Semantic Scope vs Full Round-Trip (Finding C)

- **Separation of Concerns**:
  1. `export_regions_to_legacy(doc, page_index=0)`: Explicitly defined as a semantic-only bridge. Exports Scenes, CAST, and Instances to `REGION_SPEC` + `CAST_SPEC`. Docstring clearly notes that Visual Frames are NOT represented by `REGION_SPEC`.
  2. `export_to_legacy(doc, page_index=0)`: Defined as the full round-trip export. Strictly verifies that:
     - Each Scene has a paired VisualFrame with identical geometry (tolerance `0.001`).
     - Scene count == VisualFrame count.
     - If Scene and Frame geometry have diverged (e.g. independently edited), it reports `unsupported` and fails closed without silent conflation.

## 6. Scene / Frame Divergence Policy (Finding C)

- Any divergence between a Scene's `area` and its paired VisualFrame's `shape` triggers fail-closed `unsupported` diagnostic during full legacy export:
  `"Scene '{scene_id}' geometry diverged from paired VisualFrame '{frame_id}' geometry. Full legacy export requires Scene and Frame geometry to be identical. Fail closed."`

## 7. Strict Reverse Coordinate Export (Finding D)

- **Root Cause**: `page_normalized_to_koma_local` clamped values with `max(0.0, min(1.0, ...))`, silently modifying geometry for instances extending outside the containing scene.
- **Fix**: Added `strict: bool = False` to `page_normalized_to_koma_local`. When `strict=True`, any instance whose bounding box falls outside the containing scene's page geometry raises `ValueError`.
- **Export Behavior**: `export_regions_to_legacy` and `export_to_legacy` catch this and add an explicit `unsupported` error naming the `instance_id` and stating that lossless reverse conversion is not possible without clamping. No silent modification.

## 8. Boundary Scene Move Semantics (Finding E)

- **Root Cause**: `scene["area"]` and each `inst["area"]` were individually clamped to `[0, 1]`, causing different actual deltas near edges.
- **Fix**: `move_scene()` calculates the group-wide maximum allowable delta (`effective_dx`, `effective_dy`) bounded by `[0, 1]` across all rects (scene + all belonging instances), and applies the exact same delta to all members.
- **Result**:
  1. `scene actual delta == every instance actual delta`
  2. Relative offsets between scene and instances are strictly preserved.
  3. No member leaves `[0, 1]`.

## 9. Scene Resize Failure Semantics (Finding F)

- **Root Cause**: `resize_scene()` applied `_clamp_area()` to each proportionally scaled instance, silently distorting proportional placement if an instance exceeded page bounds.
- **Fix**: `resize_scene()` validates `new_area`, pre-computes candidate areas for all instances, and validates all candidates with `validate_area()`. If any candidate would fall outside `[0, 1]`, the operation raises `ValueError` and leaves the document unchanged. No individual silent clamping.

## 10. Page ID Uniqueness & ID Scope (Finding G)

- `page_id` is validated as document-global unique in `validate_document()`.
- Scope definitions documented:
  - `page_id`: Document-global unique.
  - `scene_id`, `frame_id`, `cast_id`, `instance_id`, `guide_id`: Page-local FK scope (unique within containing page).

## 11. New M0.1 Tests

Added `scripts/test_m0_1_contract_hardening.py` containing 18 tests:

| Test Class | Tests | Focus |
|---|---|---|
| `TestM01ForeignKeyValidation` | 4 | Empty CAST orphan, empty Scene orphan, orphan CAST ref, orphan Scene ref |
| `TestM01DuplicatePageId` | 1 | Duplicate `page_id` rejection |
| `TestM01LegacyMigrationValidation` | 3 | Legacy binding missing CAST fails closed, clean import valid=True, pairing metadata |
| `TestM01LegacyExportScopeAndDivergence` | 6 | Clean export, scene/frame diverged fails closed, frame/scene diverged fails closed, count mismatch fails closed, instance outside scene fails closed, semantic-only export scope |
| `TestM01OperationsBoundaryAndResize` | 4 | Boundary scene move common effective delta, negative boundary move, resize out of bounds rejected atomically, frame move effective delta |

**Result**: 18/18 PASSED in 0.001s.

## 12. Full Test Suite & Regression

```powershell
python -m unittest scripts/test_m0_authoring_contract.py scripts/test_m0_authoring_operations.py scripts/test_m0_legacy_import.py scripts/test_m0_1_contract_hardening.py
```

- Original M0 Test Suite: 60/60 PASSED (0 skipped)
- New M0.1 Hardening Suite: 18/18 PASSED
- Total Tests: **78/78 PASSED** in 0.028s.

## 13. Workflow Regression

- Legacy workflows moved by user to `workflows/Archive/`.
- `TestWorkflowStructuralRegression` updated to search recursively across `workflows/` including `Archive/`.
- All 55+ workflow JSON files verified as valid JSON dictionaries.
- Zero runtime code modified (`scene_compiler.py`, samplers, UI untouched).

## 14. Remaining Known Limitations

1. **Mask Policy**: Generation mask policy remains `PLANNED` (M0.1 hardens contract data; no runtime mask changes).
2. **Polygon/Freeform**: `shape_type` extensible point exists; only `"rect"` is currently supported.
3. **Multi-page export**: Legacy format only supports a single page; multi-page authoring documents export page 0 by default.

## 15. M1 Readiness

All M0.1 Acceptance Criteria are satisfied:
- FK EMPTY COLLECTION: PASS
- LEGACY IMPORT ALWAYS VALID OR EXPLICIT INVALID: PASS
- LEGACY EXPORT SCOPE TRUTHFUL: PASS
- SCENE / FRAME DIVERGENCE: NO SILENT CONFLATION (FAIL CLOSED)
- INSTANCE OUTSIDE SCENE: NO SILENT CLAMP (FAIL CLOSED)
- BOUNDARY SCENE MOVE: COMMON EFFECTIVE DELTA (PRESERVES OFFSETS)
- SCENE RESIZE: NO INDIVIDUAL SILENT CLAMP (ATOMIC REJECT)
- DUPLICATE PAGE ID: REJECTED
- OLD 60 TESTS: ALL PASS
- NEW M0.1 TESTS: ALL PASS
- WORKFLOW JSON MODIFIED: NO
- UI MODIFIED: NO
- BACKEND MODIFIED: NO

**M1 READY: YES**
