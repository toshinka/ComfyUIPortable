# M3B-PI1 — Optional CLEAN Guide Production Backend Integration Report

Date: 2026-09-11 JST  
Issuer: Web GPT SOL  
Executor: Gemini 3.8 Flash / Antigravity 2.0  
Classification: `PI1_BACKEND_INTEGRATED`  
Production Integration Scope: **BACKEND ONLY**  
Final Owner Product Acceptance: **DEFERRED**  

---

## 1. Public LR8 Authority Verification

Production integration was initiated under explicit delegated authority from Web GPT SOL following formal public review of research qualification milestone M3B-LR8.

- **Reviewed Public Commit**: `b5c79b85ed2fdeec1bf30254945db569666ecfa4`
- **LR8 Publication Verification**:
  - `M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION.md` present
  - `M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION_REPORT.md` present
  - `M3B_LR8_MANIFEST.json` present
  - `M3B_LR8_VISUAL_LEDGER.md` present
  - `M3B_LR8_CONTACT_SHEET.png` present
  - `M3B_LR8_RUNTIME_PROVENANCE.json` present
- **LR8 Research Qualification**: `CORE_GLOBAL_QUALIFIED`
- **M3B Research Cycle**: Closed for current CLEAN-GLOBAL candidate.

---

## 2. Implementation Scope & Semantic Boundaries

M3B-PI1 executed strictly bounded backend integration without architectural creep:

1. **Persistent Schema**: **UNCHANGED** (`TEGAKI_AUTHORING_DOCUMENT` version `1.0.0`). No schema additions, modifications, or migrations.
2. **UI Routing**: **NOT IMPLEMENTED** (Reserved for PI2). No UI generation-button routing changes, no frontend Guide toggles, no strength sliders, no model selectors.
3. **No-Guide Workflow**: Completely untouched and isolated (`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` diff = 0 bytes).
4. **RAW Guide Independence**: RAW sketch pixels remain editing/reference only; they are **never** passed to ControlNet.
5. **No Advanced-ControlNet**: 0 ACN nodes, 0 effect masks, 0 Figure union masks in generation pipeline.
6. **Core ControlNet Route**: Uses ComfyUI native `ControlNetApplyAdvanced` with fixed parameters (strength: 0.75, start: 0.0, end: 1.0) and external model `CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`.

---

## 3. Production Node: `TegakiMangaGenerationGuideBridge`

A dedicated, deterministic generation-guide bridge node was created:

- **Source**: `custom_nodes_custom/tegaki_manga_nodes/generation_guide_bridge.py`
- **Class**: `TegakiMangaGenerationGuideBridge`
- **Display Name**: `Tegaki Manga Generation Guide Bridge (Clean)`
- **Category**: `tegaki/manga/guide`
- **Inputs**:
  - `document_json`: `STRING` (multiline, default `""`)
  - `page_index`: `INT` (default 0, min 0, max 64)
- **Outputs**:
  - `clean_generation_guide`: `IMAGE` (ComfyUI tensor `(1, H, W, 3)`)
  - `debug_json`: `STRING` (machine-readable execution provenance)
- **Contract & Behavior**:
  - Filters for enabled `rough_manga` guides.
  - If no eligible guide or zero figure regions: returns `status: "NO_GENERATION_GUIDE"` and a pure white canvas tensor (`(1, H, W, 3)` all 1.0).
  - Evaluates figure regions, projects Guide-local bounding boxes to Page-normalized coordinates (`page_x = placement.x + local.x * placement.w`).
  - Renders deterministic flat silhouettes using existing validated core helper `draw_single_character_mannequin(flat_silhouette, full_body, standing_neutral)`.
  - Never accesses or decodes `asset_reference` image files, guaranteeing 100% RAW asset pixel independence.

---

## 4. Verification Gates & Parity

### 4.1 Research CLEAN Parity Gate
- **LR3 Research Qualified Fixture SHA256**: `96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`
- **M3B-PI1 Generation Guide Output SHA256**: `96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`
- **Parity Result**: `HASH_EXACT` (100% bitwise parity).

### 4.2 RAW Separation Proof
- Test 11 of `test_m3b_pi1_generation_guide_bridge.py` executed two documents with identical geometry but radically different RAW asset references (`raw_cat_sketch.png` vs `raw_robot_render.webp`).
- Output comparison: Decoded pixel difference = 0, exact array equality verified.

### 4.3 Generation Guide Bridge Unit Suite (12/12 PASS)
1. `no Guide -> NO_GENERATION_GUIDE`: PASS
2. `disabled Guide -> NO_GENERATION_GUIDE`: PASS
3. `enabled Guide / zero Figures -> NO_GENERATION_GUIDE`: PASS
4. `one Figure -> deterministic CLEAN image`: PASS
5. `two Figures -> deterministic CLEAN image`: PASS
6. `unassigned Figure -> legal`: PASS
7. `same CAST multiple appearances -> legal`: PASS
8. `Guide-local -> Page geometry projection correct`: PASS
9. `invalid document -> fail closed`: PASS
10. `invalid Figure geometry -> fail closed`: PASS
11. `RAW asset pixel changes do not change CLEAN output`: PASS
12. `LR3 qualified fixture pixel/hash parity`: PASS

---

## 5. Production Workflows

### 5.1 Canonical Baseline Workflow (`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`)
- **ControlNet Nodes**: 0
- **Advanced-ControlNet Nodes**: 0
- **Effect Mask Inputs**: 0
- **Model Dependencies**: Standalone checkpoint only (`waiIllustriousSDXL_v170.safetensors`). Operates without AnyTest model present.
- **Modifications**: 0 bytes (Untouched).

### 5.2 Guided Production Workflow (`workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`)
- **ControlNet Nodes**: 2 (`ControlNetLoader`, `ControlNetApplyAdvanced`)
- **Bridge Node**: 1 (`TegakiMangaGenerationGuideBridge`)
- **Advanced-ControlNet Nodes**: 0
- **Effect Mask Inputs**: 0
- **Conditioning Chain**:
  `TegakiMinimumHandSceneEditor` -> `TegakiMangaConditioningBuilder` -> `ControlNetApplyAdvanced` -> `KSampler`
- **ControlNet Parameters**: Model AnyTest v4, Strength 0.75, Start 0.0, End 1.0.

---

## 6. Live Production Matrix (4/4 PASS)

Executed on local ComfyUI instance (`127.0.0.1:8188`) using Illustrious checkpoint:

| Run | Label | Workflow | Input Mode | Seed | Guide Condition | Output File | SHA256 | Image Quality | Seams / Artifacts | Regional Conflict |
|---|---|---|---|---|---|---|---|---|---|---|
| **P0** | Baseline No-Guide | `MINIMUM_HAND_MANGA_DRAFT.json` | simple | 42 | NONE | `P0_NO_GUIDE.png` | `074e5b9ef95f0870e885197f34f2c79c91f1aa8a4828f3877f9752362e33a721` | USABLE | NONE | NONE |
| **P1** | Guided SIMPLE | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | simple | 42 | Clean Global | `P1_SIMPLE_GUIDED.png` | `e3d5776c690e68dd40fd4df75407be9e209ef75f73efe084a68aaa67281b29d5` | USABLE | NONE | NONE |
| **P2** | Guided CAST 42 | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | cast | 42 | Clean Global | `P2_CAST_GUIDED_SEED42.png` | `d10ddbc54d62beab0d8eca21c26754c4a75c5c96170eea4d44bca437e46557ee` | USABLE | NONE | NONE |
| **P3** | Guided CAST 202 | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | cast | 202 | Clean Global | `P3_CAST_GUIDED_SEED202.png` | `6ac3682428ef708a39f0e9f099b7bafe990e24dc6aa0e63579495f7d6927a47f` | USABLE | NONE | NONE |

### Visual Evaluation:
1. **P0 (Baseline)**: Produces standard outdoor railway/school platform without ControlNet dependency.
2. **P1 (Guided Simple)**: Positions two students in front of the classroom windows matching the figure regions. No rectangular boundary seams.
3. **P2 (Guided CAST / Seed 42)**: Accurately renders dark-haired Left Student (`cast_1`) standing by the window and blonde Right Student (`cast_2`) seated at the desk. Seamless fusion of regional text conditioning with global mannequin guidance.
4. **P3 (Guided CAST / Seed 202)**: Generates distinct high-contrast creative linework and atmospheric lighting while preserving character placement.

Visual evidence contact sheet: `docs/manga/verification/m3b_pi1/M3B_PI1_CONTACT_SHEET.png`.

---

## 7. Regression Suite (ALL PASS)

All 8 mandated regression suites and new contract tests executed successfully:

1. **LR1 Contract**: `12/12 PASS` (`scripts/test_m3b_lr1_contract.py`)
2. **LR1 Runtime Bridge**: `5/5 PASS` (`scripts/test_m3b_lr1_runtime_bridge.py`)
3. **Guide Operations**: `PASS` (`scripts/test_m3b_lr1_guide_ops.mjs`)
4. **M2B Minimum-Hand Editor**: `19/19 PASS` (`scripts/test_m2b_minimum_hand_editor.mjs`)
5. **CAST Authoring**: `7/7 PASS` (`scripts/test_m2b_cast_instance_authoring.py`)
6. **CAST Execution**: `14/14 PASS` (`scripts/test_m2a_cast_execution_bridge.py`)
7. **Document Roundtrip**: `5/5 PASS` (`scripts/test_m2b_product_document_roundtrip.py`)
8. **Recurrent CAST 4-Panel**: `PASS` (`scripts/test_manga_impact_recurrent_cast_runtime.py`)
9. **Generation Guide Bridge Suite**: `12/12 PASS` (`scripts/test_m3b_pi1_generation_guide_bridge.py`)

---

## 8. Artifacts Generated

All required artifacts have been placed in `ComfyUIPortable/docs/manga/verification/m3b_pi1/`:
- `M3B_PI1_GENERATION_GUIDE.png` (`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`)
- `M3B_PI1_GENERATION_GUIDE_PROVENANCE.json`
- `P0_NO_GUIDE.png`
- `P1_SIMPLE_GUIDED.png`
- `P2_CAST_GUIDED_SEED42.png`
- `P3_CAST_GUIDED_SEED202.png`
- `M3B_PI1_CONTACT_SHEET.png`
- `M3B_PI1_RUNTIME_PROVENANCE.json`
- `M3B_PI1_VISUAL_LEDGER.md`
- `M3B_PI1_MANIFEST.json`

---

## 9. Provisional Classification & Next Steps

- **Classification**: `PI1_BACKEND_INTEGRATED`
- **UI Routing**: **NOT IMPLEMENTED**
- **Publication**: LOCAL (Owner push required; commit/push not performed by executor)
- **Final Owner Product Acceptance**: **DEFERRED**
