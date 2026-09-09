# M0 / 3M-0 Versioned Authoring Contract Report

2026-09-06 JST

## 1. Scope

This card establishes a versioned, backend-independent Authoring Document that separates Semantic Scene Regions from Visual Panel Frames, uses page-normalized coordinates, stable string IDs, and supports legacy import/export with the existing REGION_SPEC / CAST_SPEC v1 format.

No UI, backend, pose/interaction, or existing workflow changes.

## 2. Read Baseline

| Item | Value |
|---|---|
| GITHUB_ComfyUI HEAD | `09c48e42` |
| Review Target SHA | `5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8` |
| Planning SHA | `261a3d7297455931d391e62f2d8a1335193d8d90` |
| Local main HEAD at start | `09c48e42` |
| Worktree | Clean |

## 3. Contract Name / Version

| Field | Value |
|---|---|
| Schema ID | `TEGAKI_AUTHORING_DOCUMENT` |
| Schema Version | `1.0.0` |
| Known Versions | `{"1.0.0"}` |
| Versioning Format | Semantic (string) |

Name chosen after verifying zero collisions with existing codebase symbols via `rg` search.

## 4. Authoring Document Shape

```
Document
├── schema_id: str ("TEGAKI_AUTHORING_DOCUMENT")
├── schema_version: str ("1.0.0")
├── pages: list[Page]
└── metadata: dict

Page
├── page_id: str
├── width_px: int
├── height_px: int
├── style_prompt: str
├── style_negative_prompt: str
├── scenes: list[Scene]
├── visual_frames: list[VisualFrame]
├── cast: list[CastEntry]
├── character_instances: list[CharacterInstance]
├── guides: list[Guide]
├── generation: dict
└── metadata: dict
```

## 5. Page / Scene / Frame / CAST / Instance / Guide

### Scene
```
scene_id, name, prompt, negative_prompt, input_mode, area, order, metadata
```

### VisualFrame
```
frame_id, shape, order, metadata
```

### CastEntry
```
cast_id, display_name, identity_prompt, negative_prompt, loras, metadata
```

### CharacterInstance
```
instance_id, cast_id (FK), scene_id (FK), area, acting_prompt, negative_prompt_override, order, metadata
```

### Guide
```
guide_id, guide_type, asset_reference, placement, enabled, metadata
```

## 6. Scene vs Frame Separation — VERIFIED

- Scenes and Frames are in separate arrays with separate ID namespaces.
- Scene geometry ≠ Frame geometry (Fixture 1 proves this).
- Moving a Frame does NOT move Scenes or Instances (Fixture 8 proves independence).
- No `Scene ID == Panel ID` conflation.
- Legacy import creates both a Scene AND a Frame per KOMA, with distinct IDs.

Status: **IMPLEMENTED**

## 7. Coordinate Contract — VERIFIED

- Page-normalized coordinates: `x, y, w, h ∈ [0, 1]`
- Character instance areas are page-normalized (not KOMA-local).
- Resolution changes preserve normalized areas (Fixture 5).
- Geometry validation: finite, not NaN, w > 0, h > 0, explicit bounds policy.
- Authoring input: fail clearly (ValueError). Legacy import: migration policy with warning.

Status: **IMPLEMENTED**

## 8. Stable ID Contract — VERIFIED

- `page_id`, `scene_id`, `frame_id`, `cast_id`, `instance_id`, `guide_id` — all string.
- Array index is NOT used as identity.
- Reorder-safe: IDs survive serialize/deserialize and array reordering.
- Duplicate IDs during validation: rejected.
- Duplication creates new IDs. Copy/move generates new IDs.
- Legacy import uses deterministic mapping: `legacy_scene_{id}`, `legacy_frame_{id}`.

Status: **IMPLEMENTED**

## 9. Simple / Cast Mode — VERIFIED

- `input_mode: "simple" | "cast"` per Scene.
- Simple mode: character description in scene prompt is fine, CAST not required.
- Cast mode: Scene = background/context, CAST = identity, Instance = acting/placement.
- Mode switching preserves all data (input_mode is just a flag, no data destruction).
- Mixed modes on same page supported (Fixture 4).

Status: **IMPLEMENTED**

## 10. Overlap / Order Contract — VERIFIED

- Scene regions may overlap. Instance regions may overlap.
- Explicit `order` field on Scene, Frame, and Instance.
- Overlap geometry preserved on JSON round-trip (Fixture 2).
- Mask policy for generation: **PLANNED** — M0 stores order fields but does not implement runtime mask semantics.
- `mask_policy` can be added as metadata extension point.

Status: **IMPLEMENTED** (order persistence). Mask semantics: **PLANNED**.

## 11. Serialization — VERIFIED

- `to_dict()` / `from_dict()` — pure dict round-trip.
- `to_json()` / `from_json()` — JSON string round-trip.
- Key ordering not required for semantic equality.
- Full document round-trip test with all entity types (Fixture in TestSerializationRoundTrip).

Status: **IMPLEMENTED**

## 12. Unknown Field Policy — VERIFIED

- Unknown fields within a known schema version are preserved on read → edit → save.
- `from_dict()` performs `deepcopy` without stripping unknown keys.
- Validation passes through unrecognized keys without error.
- Fixture 11 proves: add `future_vendor_extension`, edit unrelated field, save → preserved.

Status: **IMPLEMENTED**

## 13. Unknown Version Policy — VERIFIED

- `from_dict()`: unknown `schema_version` → `ValueError` with "fail closed" message.
- `from_json()`: same behavior.
- `validate_document()`: unknown version → error in result, stops further validation.
- Never silently overwrites a document with an unknown newer version.
- Fixture 12 proves: `schema_version = "99.0.0"` → rejected.

Status: **IMPLEMENTED**

## 14. Legacy Import Mapping — VERIFIED

| Legacy Field | New Field | Transform | Lossless? |
|---|---|---|---|
| `region.id` (int 1-6) | `scene.scene_id` (str) | `"legacy_scene_{id}"` | Yes |
| `region.{x,y,w,h}` | `scene.area` (page-norm) | Direct copy | Yes |
| `region.prompt` | `scene.prompt` | Direct copy | Yes |
| `region.characters[].character_id` | `instance.cast_id` | Direct copy | Yes |
| `region.characters[].area` (KOMA-local) | `instance.area` (page-norm) | `panel_x + area_x*panel_w` | Yes (real geom) |
| `region.characters[].prompt_override` | `instance.acting_prompt` | Direct copy | Yes |
| `region.characters[].shot_type` | `instance.metadata.shot_type` | Preserve | Yes |
| `region.characters[].pose_preset` | `instance.metadata.pose_preset` | Preserve | Yes |
| `region.characters[].interaction` | `instance.metadata.interaction` | Preserve | Yes |
| `cast.characters[].id` | `cast.cast_id` | Direct copy | Yes |
| `cast.characters[].prompt` | `cast.identity_prompt` | Direct copy | Yes |
| Panel ID (int) | `frame.frame_id` (str) | `"legacy_frame_{id}"` | Yes |

Each active KOMA produces both a Scene and a VisualFrame with distinct IDs.

Status: **IMPLEMENTED**

## 15. Lossy Conversion Policy — VERIFIED

- PanelContentEditor dummy geometry (`{x:0.05, y:0.05, w:0.9, h:0.9}`) triggers explicit warning during import.
- Export to legacy fails closed for unsupported features: >6 scenes, non-rect shapes.
- No silent data discard.

Status: **IMPLEMENTED**

## 16. Pure Operations — VERIFIED

| Operation | Behavior | Tested |
|---|---|---|
| `move_scene` | Scene + belonging instances move by (dx,dy). Frames untouched. | Fixture 6 |
| `resize_scene` | Scene resized, instances proportionally transform. | Fixture 7 |
| `move_frame` | Frame only moves. Scenes/instances untouched. | Fixture 8 |
| `change_resolution` | Pixel dimensions change. Normalized areas unchanged. | Fixture 5 |
| `duplicate_scene` | Deep copy with new IDs for scene and instances. | Dedicated test |

All operations return new documents (deep copy). Original is never mutated.

Status: **IMPLEMENTED**

## 17. Fixtures

| # | Name | Status |
|---|---|---|
| 0 | Empty editable state | PASS |
| 1 | Two independent Scenes + Frames | PASS |
| 2 | Overlapping Scenes | PASS |
| 3 | Same CAST repeated (3 instances) | PASS |
| 4 | Mixed simple/cast modes | PASS |
| 5 | Resolution change | PASS |
| 6 | Scene move | PASS |
| 7 | Scene resize | PASS |
| 8 | Frame move (independence) | PASS |
| 9 | Legacy import | PASS |
| 10 | Invalid references | PASS |
| 11 | Unknown field round-trip | PASS |
| 12 | Unknown newer schema fail-closed | PASS |

## 18. Tests

| Test File | Tests | Status |
|---|---|---|
| `scripts/test_m0_authoring_contract.py` | 31 | ALL PASS |
| `scripts/test_m0_authoring_operations.py` | 10 | ALL PASS |
| `scripts/test_m0_legacy_import.py` | 19 | ALL PASS |
| **Total** | **60** | **ALL PASS** |

All tests are pure Python, no ComfyUI server required.

## 19. Existing Workflow Regression

- Zero workflow JSON files modified.
- `test_m0_legacy_import.py::TestWorkflowStructuralRegression` verifies all existing workflow JSONs parse as valid dicts.
- No load paths changed.

Status: **PASS**

## 20. Runtime / UI Non-Changes

| Area | Changed? |
|---|---|
| Canvas | NO |
| Scene Editor | NO |
| CAST Chips UI | NO |
| Inspector | NO |
| A1111 skin | NO |
| SPA | NO |
| `scene_compiler.py` | NO |
| `impact_region_plan.py` | NO |
| `manga_impact_regional_adapter.py` | NO |
| Samplers / KSampler | NO |
| ControlNet | NO |
| Workflow JSONs | NO |
| Comic Creator | NO |

## 21. Known Limitations

1. **Mask policy**: M0 stores `order` fields but does not implement runtime mask generation semantics. Marked as PLANNED.
2. **Polygon shapes**: `shape_type` extensibility point exists but only `"rect"` is implemented in M0.
3. **Guide asset**: Schema supports guide entries but no guide generation pipeline is connected.
4. **KOMA-local coordinate transform**: When panel geometry is PanelContentEditor's dummy default, the page-normalized coordinates are mathematically correct but may not reflect real layout positions.
5. **SubScene migration**: Existing SubScene v1.1 data is not specifically migrated (subscenes are a panel-internal concept; M0 focuses on page-level Scene/Frame separation).
6. **Multi-page**: Document supports multiple pages but M0 tests focus on single-page workflows.

## 22. Next Card Recommendation

```
M1 / 3M-1 — Scene-only Minimum-Hand Draft
```

M1 scope:
- Resolution + Style Template + Scene rectangle + Scene Prompt + optional frame guide + Seed → Generate
- Simple mode only (no CAST required for first useful draft)
- Connects authoring document to existing backend for actual image generation
- First user-facing UI surface

## 23. Claude独自判断

1. **Contract naming**: Chose `TEGAKI_AUTHORING_DOCUMENT` over `MANGA_AUTHORING_DATA` (Astra's planning term) because the latter appeared only in docs and was explicitly noted as "not an API name" in the card (§7). The chosen name is descriptive, collision-free, and consistent with the `TEGAKI` prefix used throughout the codebase.

2. **Version format**: Used semver string (`"1.0.0"`) instead of integer (`1`) for the schema version. This provides more granularity for future minor/patch updates without breaking the version comparison semantics. The existing v1 contracts use integer versions, so the format change makes the boundary explicit.

3. **Test import mechanism**: Used `importlib.util` direct file imports to bypass the package `__init__.py` which pulls in ComfyUI runtime dependencies. This keeps M0 contract tests truly pure Python as the card requires (§46).

4. **Instance area in page coordinates**: The card specified page-normalized coordinates for all entities. The legacy KOMA-local character area is transformed to page-normalized during import. This is a deliberate break from the two-tier coordinate system (page-norm panels + panel-local characters) in favor of a single flat coordinate space, which simplifies scene move/resize operations and eliminates the panel↔character coordinate coupling.

5. **Metadata as escape hatch**: `shot_type`, `pose_preset`, `interaction` are preserved in instance `metadata` rather than as first-class fields. This follows the card's instruction (§23) that pose is not M0's primary concern, while ensuring no data loss during migration.

---

## M0 Acceptance Gates

```
VERSIONED AUTHORING DOCUMENT:              PASS
SCENE / FRAME SEPARATION:                 PASS
STABLE IDS:                               PASS
PAGE-NORMALIZED COORDINATES:              PASS
SIMPLE / CAST PER-SCENE MODE:             PASS
SAME CAST MULTI-INSTANCE:                 PASS
OVERLAP ORDER PERSISTENCE:                PASS
SERIALIZATION ROUNDTRIP:                  PASS
UNKNOWN FIELDS PRESERVED:                 PASS
UNKNOWN NEWER VERSION FAIL-CLOSED:        PASS
LEGACY IMPORT:                            PASS
LOSSY CONVERSION DIAGNOSTICS:             PASS
SCENE MOVE OPERATION:                     PASS
SCENE RESIZE OPERATION:                   PASS
FRAME INDEPENDENCE:                       PASS
EXISTING WORKFLOW STRUCTURAL REGRESSION:  PASS

UI CHANGED:                               NO
BACKEND CHANGED:                          NO
POSE / INTERACTION EXPANDED:              NO
```

---

## M0.1 Review Correction & Hardening (2026-09-06)

Following Web GPT review of M0, M0.1 hardened specific boundary conditions:
1. **FK Validation**: Fixed empty collection hole where missing CAST/Scene was not detected. Unconditional check enforced.
2. **Legacy Import**: `MigrationResult` now has `errors: List[str]` and `valid: bool`. Runs `validate_document()` and fails closed on orphan bindings.
3. **Legacy Export**: Separated `export_regions_to_legacy()` (semantic only) from `export_to_legacy()` (full round-trip with strict Scene/Frame divergence fail-closed checks).
4. **Coordinate Export**: `page_normalized_to_koma_local(strict=True)` strictly rejects instances extending outside scene geometry instead of silently clamping.
5. **Group Operations**: `move_scene()` uses common effective delta preserving relative offsets; `resize_scene()` atomically rejects out-of-bounds candidates without individual clamping.
6. **Page ID Uniqueness**: Document-global uniqueness enforced for `page_id`.
7. **Test Suite**: Original 60 tests retained and passing; 18 new M0.1 tests added (78/78 total).
See full details in [M0_1_CONTRACT_HARDENING_REPORT.md](M0_1_CONTRACT_HARDENING_REPORT.md).
