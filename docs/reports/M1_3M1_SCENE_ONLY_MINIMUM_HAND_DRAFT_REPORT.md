# M1 / Phase 3M-1: Scene-Only Minimum-Hand Draft Milestone Report

**Date**: 2026-09-06  
**Status**: ACCEPTED / GREEN  
**Author**: Antigravity Assistant  
**Target Milestone**: Phase 3M-1 (M1) — Scene-Only Minimum-Hand Draft  
**Reference Document**: `ComfyUI_Portable_M1_3M1_Scene_Only_Minimum_Hand_Draft_Request.md`  
**Single Source of Truth**: `TEGAKI_AUTHORING_DOCUMENT` v1.0.0  

---

## 1. Executive Summary

Phase 3M-1 (M1) establishes the first functional, end-to-end **Minimum-Hand Scene Draft Pipeline** in Tegaki Manga. The goal was to prove the viability of a radically simplified creator workflow:
$$\text{Resolution Preset} + \text{Style Template} + \text{Scene Rectangles} + \text{Scene Prompts} + \text{Seed} \longrightarrow \text{Generated Draft Page}$$

By strictly bounding M1 to **simple scene regions only** (no CAST requirements, no character placement widgets, no manual mask painting, no visual frame/gutter conflation), M1 delivers a robust, fail-closed authoring-to-execution pipeline backed by `TEGAKI_AUTHORING_DOCUMENT` v1.0.0 as the single source of truth.

All acceptance criteria are met:
- **Core Node**: `TegakiMinimumHandSceneEditor` registered and fully operational.
- **Execution Bridge**: `authoring_execution_bridge.py` compiling authoring documents to `PAGE_COMPILE_PLAN` v1 and rendering real-time region preview tensors.
- **Web UI Extension**: `web/js/minimum_hand_scene_editor.js` featuring interactive rectangle resizing/dragging, prompt inspector with zero text loss on scene switching, and faithful bi-directional widget synchronization.
- **Canonical Workflow**: `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json` deployed with cleanly segmented User Workspace and Internal Pipeline groups.
- **Archive Directory**: Existing research workflows in `workflows/Archive/` preserved as read-only historical provenance without modification.
- **Automated Tests**: 98 tests passing (78 prior M0/M0.1 tests + 20 new M1 unit and integration tests, 100% green).
- **Empirical Image Verification**: 5 conditions executed via live ComfyUI server with SDXL Illustrious v1.7 on RTX 4070 (average generation time 16.5s per draft).
- **Direct Visual Inspection**: Verified line quality, screentone shading, and semantic locality; contact sheet and manifest recorded in `docs/verification/m1/`.

---

## 2. Strategic Reset Context & Philosophy

Prior to Phase 3M, Tegaki development had explored diverse experimental paths (50+ workflows across controlnet fusions, regional adapters, subscene interactions, and impact bindings). While empirically valuable, this resulted in cognitive overload and sprawling node graphs.

M1 executes the strategic direction reset defined in `ComfyUI_Portable_3M_Prep_SSOT_Publication_and_MinimumHand_Direction_Reset_Request.md`:
1. **Authoring Document is SSOT**: The editor does not emit arbitrary ad-hoc masks or loose strings. It operates directly on `TEGAKI_AUTHORING_DOCUMENT` v1.0.0.
2. **Minimum-Hand UX**: The creator needs only to draw rough scene rectangles, pick a style and resolution, and type simple scene prompts.
3. **Strict Boundary Control**: Advanced features (CAST, interactions, character staging, panel cutting) are deliberately deferred to subsequent milestones (M2: CAST, M3: Frame/Gutter, etc.) rather than leaking into M1.

---

## 3. Authoring Document Contract Conformance

M1 strictly conforms to the `TEGAKI_AUTHORING_DOCUMENT` v1.0.0 schema specified in `custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py`:
- `schema_id`: `"TEGAKI_AUTHORING_DOCUMENT"`
- `schema_version`: `"1.0.0"`
- Canonical page structure with `width_px`, `height_px`, `style_prompt`, `style_negative_prompt`, and `generation` (`seed`).
- `scenes` array containing semantic scene objects with page-normalized `area` coordinates (`x`, `y`, `w`, `h`), `input_mode="simple"`, `prompt`, `negative_prompt`, and stable `scene_id`.
- Visual panel frames (`visual_frames`) and character instances (`character_instances`) are preserved if present, but never conflated with semantic scene regions.

---

## 4. Structural Decisions & Scope Enforcement

1. **Semantic Scene Rectangles vs. Visual Panel Frames**:
   - In M1, scene rectangles represent semantic areas of interest for regional diffusion conditioning.
   - They do **not** represent visual manga frames (comic gutters, black borders).
   - Conflating scene bounds with visual borders is strictly prohibited; visual framing belongs to downstream post-processing or future layout stages.
2. **Simple-Only Mode Enforcement**:
   - All scenes must have `input_mode == "simple"`.
   - Any document containing `input_mode == "cast"` fails closed in M1 with an explicit error: `"M1 only supports 'simple' scene mode. CAST mode is deferred to M2."`
3. **Strict Panel Limits**:
   - Minimum 1 scene (0 scenes fails closed).
   - Maximum 6 scenes (backend limit of 6 regional conditionings; >6 scenes fails closed).

---

## 5. Execution Bridge Design (`authoring_execution_bridge.py`)

The execution bridge connects the authoring schema to ComfyUI execution:
- `validate_m1_execution_document(doc, page_index)`: Validates schema, enforces 1–6 scene limit, verifies simple mode, and returns the target page with diagnostic warnings.
- `compile_document_to_page_plan(doc, page_index)`: Compiles the document into a strict `PAGE_COMPILE_PLAN` v1 structure. Each scene becomes a fully compliant `COMPILE_PLAN` v1 panel dictionary verified by `validate_compile_plan()`.
- `generate_scene_regions_preview_image(doc, page_index, width, height)`: Generates a high-contrast blueprint-style visualization showing colored scene boundaries, order labels, and prompt snippets.
- `generate_scene_regions_preview_tensor(doc, ...)`: Converts the preview image to a `[1, H, W, 3]` float32 PyTorch tensor for ComfyUI `IMAGE` outputs.
- `get_execution_debug_info(doc, page_index, seed)`: Emits structured diagnostic JSON for auditability and verification provenance.

---

## 6. Editor Node Implementation (`TegakiMinimumHandSceneEditor`)

Located in `custom_nodes_custom/tegaki_manga_nodes/minimum_hand_scene_editor.py`:
- **Inputs**:
  - `document_json` (`STRING`, multiline): The SSOT authoring document JSON.
  - `seed` (`INT`, default: 42): Generation seed.
  - `style_template` (`COMBO`): `"Manga Monochrome"`, `"Manga Color"`, `"Custom"`.
  - `resolution` (`COMBO`): `"Portrait 832x1216"`, `"Landscape 1216x832"`, `"Square 1024x1024"`, `"Custom"`.
- **Outputs**:
  1. `page_compile_plan` (`PAGE_COMPILE_PLAN`): Consumed by `TegakiMangaConditioningBuilder`.
  2. `scene_regions_preview` (`IMAGE`): Connected to `PreviewImage`.
  3. `seed` (`INT`): Synced seed output.
  4. `width` (`INT`): Canvas width in pixels.
  5. `height` (`INT`): Canvas height in pixels.
  6. `debug_json` (`STRING`): Diagnostic metadata.
  7. `authoring_document_json` (`STRING`): Serialized document JSON for downstream saving.
- **Factory Helper**: `create_default_m1_document()` provides the canonical 2-scene vertical layout (Top: Classroom, Bottom: Train Platform).

---

## 7. Web Extension UI (`minimum_hand_scene_editor.js`)

Located in `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js`:
- Registered as `Tegaki.MinimumHandSceneEditor` on node `TegakiMinimumHandSceneEditor`.
- **Visual Canvas**:
  - Renders normalized scene rectangles with distinctive color palette.
  - Interactive hit testing for scene selection, drag-move, and 4-corner resizing.
  - Normalized bounds $[0, 1]$ clamped strictly to canvas boundaries.
- **Scene Prompt Inspector**:
  - Immediate two-way binding: edits in the prompt textarea or label input update the underlying document state instantaneously.
  - Scene switching preserves prompt text without loss.
- **Scene Management Controls**:
  - `+ Add Scene` (adds stacked rectangle; disabled at 6 scenes).
  - `- Remove Scene` (removes active scene; disabled at 1 scene).
  - `Reset 2-Scene` (restores canonical vertical split).
- **Lifecycle & Persistence**:
  - `onConfigure` hook restores UI state faithfully from `document_json` widget.
  - `onRemoved` hook deregisters window event listeners (`mousemove`, `mouseup`).

---

## 8. Canonical Workflow Topology

Workflow path: `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json`.

```
┌────────────────────────────────────────────────────────────────────────┐
│ USER WORKSPACE — MINIMUM-HAND SCENE DRAFT                              │
│                                                                        │
│  ┌──────────────────────────────┐        ┌──────────────────────────┐  │
│  │ TegakiMinimumHandSceneEditor │        │ PreviewImage             │  │
│  │ (Interactive Canvas + UI)    │───────>│ (Scene Regions Preview)  │  │
│  └──────────────┬───────────────┘        └──────────────────────────┘  │
└─────────────────┼──────────────────────────────────────────────────────┘
                  │ [PAGE_COMPILE_PLAN]
┌─────────────────▼──────────────────────────────────────────────────────┐
│ INTERNAL PIPELINE — DO NOT TOUCH                                       │
│                                                                        │
│  ┌──────────────────────────────┐                                      │
│  │ CheckpointLoaderSimple       │───[CLIP]──┐                          │
│  │ (Illustrious SDXL v1.7)      │───[MODEL]─┼───────────┐              │
│  └──────────────┬───────────────┘           │           │              │
│                 │ [VAE]                     ▼           │              │
│                 │              ┌────────────────────────┴─┐            │
│                 │              │ TegakiConditioningBuilder│            │
│                 │              └────────────┬─────────────┘            │
│                 │                           │ [POS / NEG COND]         │
│                 │                           ▼                          │
│  ┌──────────────▼───────────────┐      ┌─────────┐                     │
│  │ EmptyLatentImage (832x1216)  │─────>│ KSampler│                     │
│  └──────────────────────────────┘      └────┬────┘                     │
│                                             │ [LATENT]                 │
│                                             ▼                          │
│                                        ┌─────────┐                     │
│                                        │VAEDecode│                     │
│                                        └────┬────┘                     │
└─────────────────────────────────────────────┼──────────────────────────┘
                                              │ [IMAGE]
┌─────────────────────────────────────────────▼──────────────────────────┐
│ OUTPUT DRAFT IMAGE                                                     │
│                                                                        │
│  ┌──────────────────────────────┐                                      │
│  │ SaveImage (Draft Output)     │                                      │
│  └──────────────────────────────┘                                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Archive Directory Isolation & Preservation

- `workflows/Archive/` contains all 72 historical exploration workflows (01 through 50+).
- The user relocated these files during M0.1 reorganization.
- In accordance with safety policies, `workflows/Archive/` was treated as strictly read-only historical provenance.
- `workflows/README.md` was authored to formally establish that `M1_MINIMUM_HAND_SCENE_DRAFT.json` in the root is the sole active canonical workflow.

---

## 10. Automated Test Suite Results

A total of **98 unit and integration tests** were executed with 100% passing results:

| Test Suite | File | Tests | Result | Focus |
|---|---|:---:|:---:|---|
| M0 Authoring Contract | `scripts/test_m0_authoring_contract.py` | 31 | PASS | Fixtures 0–4, 10–12, schema validity, roundtrip |
| M0 Authoring Operations | `scripts/test_m0_authoring_operations.py` | 10 | PASS | Scene move, resize, duplication, resolution |
| M0 Legacy Import | `scripts/test_m0_legacy_import.py` | 19 | PASS | Backward compatibility, transform matrices |
| M0.1 Contract Hardening | `scripts/test_m0_1_contract_hardening.py` | 18 | PASS | Boundary clamps, FK validation, fail-closed |
| **M1 Execution Bridge** | `scripts/test_m1_authoring_execution_bridge.py` | 10 | **PASS** | 0-scene / >6 scene rejection, CAST mode rejection, COMPILE_PLAN v1 schema |
| **M1 Scene Editor Node** | `scripts/test_m1_scene_editor_document.py` | 7 | **PASS** | Node I/O, default doc generation, preset mappings |
| **M1 Mask Plan Integration** | `scripts/test_m1_scene_mask_plan.py` | 3 | **PASS** | Mask tensor shapes, geometry swap, 6-scene layout |
| **Total** | | **98** | **PASS** | **Zero failures, zero regressions** |

---

## 11. Empirical Verification Suite

All 5 empirical verification conditions were generated via live ComfyUI server using SDXL checkpoint `waiIllustriousSDXL_v170.safetensors` on NVIDIA GeForce RTX 4070 (12GB VRAM).

| Condition | File | Seed | Resolution | Time | Verification Focus | Result |
|---|---|:---:|:---:|:---:|---|:---:|
| **Condition A** | `A_one_scene.png` | 42 | 832×1216 | 18.0s | Single scene baseline draft (Classroom 1boy) | **PASS** |
| **Condition B** | `B_two_scene_seed42.png` | 42 | 832×1216 | 16.0s | Canonical 2-scene vertical split (Top Classroom / Bottom Train) | **PASS** |
| **Condition C** | `C_swap_same_seed42.png` | 42 | 832×1216 | 16.0s | Geometry Swap Oracle (Top Train / Bottom Classroom, same seed 42) | **PASS** |
| **Condition D1** | `D_seed101.png` | 101 | 832×1216 | 16.2s | Seed variation brainstorm 1 on canonical layout | **PASS** |
| **Condition D2** | `E_seed202.png` | 202 | 832×1216 | 16.0s | Seed variation brainstorm 2 on canonical layout | **PASS** |

---

## 12. Semantic Locality & Oracle Analysis

The Geometry Swap Oracle (Condition B vs. Condition C) tests whether regional conditioning causally governs semantic placement when keeping seed 42 constant:
- **Condition B (Top Classroom, Bottom Train)**:
  - Top region contains expansive classroom windows, school interior walls, and a student quietly reading.
  - Bottom region contains railway platform, tracks, and a commuter bicycle.
- **Condition C (Top Train, Bottom Classroom, Seed 42)**:
  - Swapping the scene rectangles caused the diffusion latent space to restructure: the reading character (from classroom prompt) shifted into a prominent close-up in the lower frame holding a book, while the upper area took on high-contrast station/outdoor elements.
- **Condition D1 (Seed 101)**:
  - Clear spatial stratification: classroom windows in upper half, train tracks and cyclist girl in lower half.
- **Condition D2 (Seed 202)**:
  - High-angle dramatic perspective with school window lighting upstairs and station ramp/bike downstairs.

---

## 13. Generation Performance & Profiling

- **Hardware**: NVIDIA GeForce RTX 4070 (12GB VRAM), AMD64 Windows.
- **Peak VRAM Usage**: ~6.8 GB during SDXL sampling (well within 12.2 GB capacity).
- **Sampling Parameters**: 20 steps, Euler normal, CFG 7.0, denoise 1.0.
- **Per-Image Latency**:
  - Condition A: 18.04s (initial model load into VRAM)
  - Conditions B, C, D1, D2: 16.02s – 16.25s (cached model)
- **Total Suite Execution Time**: 82.35 seconds for 5 full SDXL portrait draft pages.

---

## 14. Contact Sheet & Artifact Provenance

Artifacts committed under `docs/verification/m1/`:
- `M1_SCENE_DRAFT_CONTACT_SHEET.png`: Side-by-side comparison of Layout Blueprint Plans vs. Final Generated Drafts across all 5 conditions.
- `M1_SCENE_DRAFT_MANIFEST.json`: Machine-readable JSON manifest recording seeds, timestamps, generation times, and file paths.
- Raw outputs saved in `output/Tegaki/M1/` and mirrored to `docs/verification/m1/`.

---

## 15. Honest Visual Evaluation

Following the required direct image inspection:
- **Strengths**:
  - Excellent lineart and screentone rendering faithful to Japanese manga aesthetics.
  - Dynamic compositions achieved with zero manual mask drawing or controlnet preprocessors.
  - Multi-scene draft enables rapid visual brainstorming for scene pairings before committing to detailed character staging.
- **Known Visual Behaviors**:
  - **Seamless Bleed**: Because M1 explicitly lacks visual panel frames / gutters, adjacent scene contents naturally bleed into each other at regional boundaries, creating continuous composite illustrations rather than bordered comic panels. This is expected and desirable for draft brainstorming, but illustrates why explicit panel guttering is necessary in M3.
  - **Single Subject Bias**: When prompts in multiple regions describe human figures without character consistency conditioning, SDXL sometimes combines or merges subjects into a shared focal point depending on seed (e.g. Condition C).

---

## 16. Deficiencies, Edge Cases & Deferred Scope

| Feature / Requirement | Status in M1 | Handling / Deferred To |
|---|---|---|
| CAST Master & Consistency | **Deferred** | Scheduled for Phase 3M-2 (M2) |
| Character Staging & Pose | **Deferred** | Scheduled for Phase 3M-2 (M2) |
| Visual Panel Frames / Gutters | **Deferred** | Scheduled for Phase 3M-3 (M3) |
| Speech Bubbles & Text | **Deferred** | Scheduled for Phase 3M-4 (M4) |
| Non-rectangular Scenes | **Deferred** | Polygon/freeform areas reserved for v1.1.0 schema |
| >6 Scene Layouts | **Fail-Closed** | Rejects >6 scenes; creator must merge or reduce |
| 0 Scene Layouts | **Fail-Closed** | Rejects 0 scenes; creator must define at least 1 scene |

---

## 17. Boundary Integrity Audit Checklist

- [x] Single Source of Truth maintained: `TEGAKI_AUTHORING_DOCUMENT` v1.0.0.
- [x] Visual panel frames decoupled from semantic scene rectangles.
- [x] Simple scene mode enforced; CAST mode rejected.
- [x] Backend 6-panel limit enforced fail-closed.
- [x] Zero scene documents rejected fail-closed.
- [x] Single canonical workflow deployed at `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json`.
- [x] `workflows/Archive/` preserved untouched and read-only.
- [x] Web extension UI implements zero text loss on scene switching.
- [x] Web extension cleans up window listeners on node removal.
- [x] All 98 automated unit and integration tests passing.
- [x] Direct image inspection performed on all empirical verification outputs.
- [x] Contact sheet and manifest recorded in `docs/verification/m1/`.

---

## 18. Documentation Register & Status Updates

- `docs/STATUS.md`: Updated to mark M1 (Phase 3M-1) COMPLETE and define M2 as next active task.
- `docs/DOCUMENT_REGISTER.md`: Updated to register `M1_3M1_SCENE_ONLY_MINIMUM_HAND_DRAFT_REPORT.md` and verification artifacts.

---

## 19. Guidance for Architecture Lead & Next Milestones

With M1 complete and empirically validated:
1. **M2 (Phase 3M-2) — CAST & Minimum Character Integration**:
   - Introduce CAST Master into the authoring UI without overwhelming the Minimum-Hand simplicity.
   - Allow assigning 1–2 characters to scenes while preserving simple mode as fallback.
   - Implement LoRA stacking and trigger prompt injection through `TegakiMangaConditioningBuilder`.
2. **M3 (Phase 3M-3) — Visual Framing & Gutters**:
   - Introduce visual panel cuts and gutters on top of generated scene drafts.
   - Decouple frame geometry from semantic scene geometry.

---

## 20. Conclusion

Phase 3M-1 (M1) successfully proves that the Minimum-Hand Scene Draft pipeline works reliably, intuitively, and fast. The authoring contract is hardened, the execution bridge is seamless, the UI extension is responsive and non-destructive, and the empirical visual generations demonstrate authentic manga quality.
