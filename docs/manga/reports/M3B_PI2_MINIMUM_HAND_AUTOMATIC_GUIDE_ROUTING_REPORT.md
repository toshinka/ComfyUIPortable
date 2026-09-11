# M3B-PI2 — Minimum-Hand Automatic Guide Routing & Product Generate Integration Report

Date: 2026-09-11 JST  
Issuer: Web GPT SOL  
Executor: Gemini 3.8 Flash / Antigravity 2.0  
Mode: LONG-RUN / BOUNDED PRODUCT INTEGRATION  
Public Authority Baseline: `45487bc741a9f6bb1f8025f50a27868fcc1108ae`  
Preceding Completed Milestone: M3B-PI1 (`PI1_BACKEND_INTEGRATED`)  
Provisional Milestone Acceptance: **ACCEPTED_BY_DELEGATED_SOL**  
Final Owner Product Acceptance: **DEFERRED**  
Final Classification: **PI2_AUTO_ROUTING_INTEGRATED**

---

## 0. Executive Summary

Card M3B-PI2 establishes deterministic, automatic routing for the Minimum-Hand Manga generation flow. Generation automatically selects between the two production backends established and qualified in M3B-PI1:
1. **`STANDARD_NO_GUIDE`**: The canonical no-Guide draft backend (`MINIMUM_HAND_MANGA_DRAFT.json`).
2. **`GUIDED_CLEAN_GLOBAL`**: The qualified CLEAN-GLOBAL ControlNet draft backend (`MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`).

The routing decision is made strictly at queue time without requiring the user to choose or switch workflows:
- **No eligible Guide** $\rightarrow$ `STANDARD_NO_GUIDE` (Zero ControlNet nodes submitted, ControlNet model never inspected).
- **Eligible enabled rough_manga Guide with $\ge 1$ valid Figure Region** $\rightarrow$ `GUIDED_CLEAN_GLOBAL` (Core `ControlNetApplyAdvanced` with `TegakiMangaGenerationGuideBridge`, 0 Advanced-ControlNet nodes, 0 effect masks).

The existing `Disable Guide` button serves as the single, immediate one-action OFF switch. A single product-facing `Generate Draft` button in `web/js/minimum_hand_scene_editor.js` provides double-submit protected queue submission with live status badge (`Generation: Standard` vs `Generation: Guide-assisted`).

---

## 1. Authority & Environment Baseline

- **Repository**: `D:\GitHub\tegaki`
- **Working Root**: `ComfyUIPortable/`
- **Public Authority SHA**: `45487bc741a9f6bb1f8025f50a27868fcc1108ae`
- **M3B-PI1 Review Status**: PUBLISHED / SOL REVIEWED (`PI1_BACKEND_INTEGRATED`)
- **Active Card**: `M3B-PI2`
- **Production Workflows**:
  - `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` (UNCHANGED, byte-identical)
  - `workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` (UNCHANGED, byte-identical)
- **Document Schema**: `TEGAKI_AUTHORING_DOCUMENT 1.0.0` (UNCHANGED, zero routing state persisted)

---

## 2. Queue Mechanism & Local API Contract

Before implementing the routing boundary, the local ComfyUI frontend API was inspected:
- **Client API**: `ComfyApi.prototype.queuePrompt(number, { output, workflow })` in `scripts/api.js`.
- **Calling Contract**:
  ```javascript
  await api.queuePrompt(0, {
      output: promptGraph,
      workflow: app?.graph?.serialize ? app.graph.serialize() : undefined
  });
  ```
- **No Monkeypatching**: No global interception of ComfyUI queue or `/prompt` route was performed.
- **Graph Preservation**: The visible LiteGraph canvas is never swapped, cleared, or replaced during generation.

---

## 3. Architecture & Separation of Concerns

Two dedicated, bounded production modules implement queue-time authority:
1. `custom_nodes_custom/tegaki_manga_nodes/product_generation_router.py`:
   - Pure validation and route evaluation logic (`evaluate_generation_route`).
   - ControlNet prerequisite checking (`is_controlnet_available`, inspected ONLY after GUIDED route selected).
   - Executable ComfyUI API prompt builder (`prepare_generation_prompt`, `build_standard_prompt`, `build_guided_prompt`).
2. `custom_nodes_custom/tegaki_manga_nodes/product_generation_api.py`:
   - PromptServer HTTP endpoint `POST /tegaki/manga/generation/prepare`.
   - Sanitized request parsing (`document_json`, `page_index`, `seed`, `prefix`).
   - Strict rejection of arbitrary filesystem paths or shell arguments.
3. `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_generation_route.js`:
   - Pure frontend preview helper `previewGenerationRoute(doc, pageIndex)`.
   - Used exclusively for UI badge status display; backend remains authoritative at queue time.
4. `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js`:
   - Added `Generate Draft` button and status badge in the global generation bar.
   - Built-in strict double-click guard (`isGenerating` latch, disabled button state, opacity).
   - Dynamic route badge updates on guide add, toggle, delete, and figure edit.

---

## 4. Deterministic Routing Rules & Eligibility

Routing uses strictly two backend enums:
```text
STANDARD_NO_GUIDE
GUIDED_CLEAN_GLOBAL
```

### Eligibility Criteria:
- **GUIDED_CLEAN_GLOBAL** is selected IF AND ONLY IF:
  1. The page contains at least one `guide_type == "rough_manga"` Guide with `enabled !== false`.
  2. The Guide has at least one valid `figure_regions[]` entry (`w > 0` and `h > 0`).
- **STANDARD_NO_GUIDE** is selected in all other cases:
  - Missing or empty `guides: []`
  - Only disabled Guides (`enabled: false`)
  - Enabled Guide with 0 figure regions
  - Guide removed
  - Guide disabled after previously being Guided
- **Semantic Independence**:
  - RAW asset file presence alone does NOT trigger the Guided route.
  - CAST presence, Character Instance count, Scene `input_mode` (simple vs cast), and seed do NOT alter route selection.
  - Figure `instance_id` may be `null` (CAST association is not required for routing).

---

## 5. Frontend / Backend Parity Verification

Parity was tested across 10 test cases in `scripts/test_m3b_pi2_generation_route.mjs` and 14 test cases in `scripts/test_m3b_pi2_product_generation_route.py`:

| Case | Test Description | Backend Route | Frontend Preview | Parity Result |
|---|---|---|---|---|
| 1 | No Guides on page | `STANDARD_NO_GUIDE` | `Generation: Standard` | PASS |
| 2 | Disabled rough_manga Guide | `STANDARD_NO_GUIDE` | `Generation: Standard` | PASS |
| 3 | Enabled rough_manga Guide / 0 Figures | `STANDARD_NO_GUIDE` | `Generation: Standard` | PASS |
| 4 | Enabled Guide / 1 unassigned Figure | `GUIDED_CLEAN_GLOBAL` | `Generation: Guide-assisted` | PASS |
| 5 | Enabled Guide / multiple Figures | `GUIDED_CLEAN_GLOBAL` | `Generation: Guide-assisted` | PASS |
| 6 | Multiple Guides / one eligible | `GUIDED_CLEAN_GLOBAL` | `Generation: Guide-assisted` | PASS |
| 7 | One-action Disable Guide toggle | `STANDARD_NO_GUIDE` | `Generation: Standard` | PASS |
| 8 | Re-enable Guide toggle | `GUIDED_CLEAN_GLOBAL` | `Generation: Guide-assisted` | PASS |
| 9 | Guide removed | `STANDARD_NO_GUIDE` | `Generation: Standard` | PASS |
| 10 | Malformed document / out of bounds | Fails closed | `Generation: Standard` | PASS |

---

## 6. Submitted Prompt Contract & Provenance

### Standard Prompt Contract (`STANDARD_NO_GUIDE`):
- `TegakiMangaGenerationGuideBridge`: **0 (ABSENT)**
- `ControlNetLoader`: **0 (ABSENT)**
- `ControlNetApplyAdvanced`: **0 (ABSENT)**
- Advanced-ControlNet nodes: **0 (ABSENT)**
- AnyTest model selector: **0 (ABSENT)**
- Conditioning path: `TegakiMangaConditioningBuilder` $\rightarrow$ `KSampler` directly.

### Guided Prompt Contract (`GUIDED_CLEAN_GLOBAL`):
- `TegakiMangaGenerationGuideBridge`: **1 (PRESENT)**
- `ControlNetLoader`: **1 (PRESENT)** (`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`)
- `ControlNetApplyAdvanced`: **1 (PRESENT)** (strength: `0.75`, start: `0.0`, end: `1.0`)
- Advanced-ControlNet nodes: **0 (STRICTLY PROHIBITED)**
- Effect masks: **0 (STRICTLY PROHIBITED)**
- Conditioning path: `TegakiMangaConditioningBuilder` $\rightarrow$ `ControlNetApplyAdvanced` $\rightarrow$ `KSampler`.

---

## 7. Live / Browser Verification Matrix (B0–B5)

Executed live against the running ComfyUI server via `scripts/m3b_pi2_run_browser_matrix.py`:

| ID | Test Case | Document State | Route Decision | Reason | CN Nodes | Queue Result | Output Artifact |
|---|---|---|---|---|---|---|---|
| **B0** | Baseline Standard | Guides: 0 | `STANDARD_NO_GUIDE` | No guides present on page | 0 | PASS | `B0_STANDARD_NO_GUIDE.png` |
| **B1** | Guide 0 Figures | Guides: 1, Figs: 0 | `STANDARD_NO_GUIDE` | Guide has zero figure regions | 0 | PASS | N/A (Route verified) |
| **B2** | Simple Guided | Guides: 1, Figs: 2 | `GUIDED_CLEAN_GLOBAL` | Eligible rough_manga guide found with 2 figures | 3 | PASS | `B2_SIMPLE_GUIDED.png` |
| **B3** | One-action Disable | Guides: 1 (disabled) | `STANDARD_NO_GUIDE` | Guide is disabled | 0 | PASS | `B3_DISABLED_STANDARD.png` |
| **B4** | Re-enable Guide | Guides: 1 (enabled) | `GUIDED_CLEAN_GLOBAL` | Eligible rough_manga guide found with 2 figures | 3 | PASS | N/A (Route verified) |
| **B5** | CAST Guided | Guides: 1, CAST: 2 | `GUIDED_CLEAN_GLOBAL` | Eligible rough_manga guide found with 2 figures | 3 | PASS | `B5_CAST_GUIDED.png` |

---

## 8. Visual Evidence & Artifacts

All verification artifacts are recorded in `docs/manga/verification/m3b_pi2/`:
- `M3B_PI2_ROUTE_CONTRACT.json`: Deterministic routing decision contract & execution records.
- `M3B_PI2_STANDARD_PROMPT_PROVENANCE.json`: Exact node class inventory for standard prompt.
- `M3B_PI2_GUIDED_PROMPT_PROVENANCE.json`: Exact node class inventory for guided prompt.
- `B0_STANDARD_NO_GUIDE.png`: Clean manga draft generation without ControlNet.
- `B2_SIMPLE_GUIDED.png`: Guide-assisted draft adhering to rough figures without harsh rectangular artifacts.
- `B3_DISABLED_STANDARD.png`: Standard generation immediately upon clicking Disable Guide once.
- `B5_CAST_GUIDED.png`: Guide-assisted draft combining active CAST conditioning with Guide placement.
- `M3B_PI2_BROWSER_LEDGER.md`: Comprehensive browser execution ledger.
- `M3B_PI2_VISUAL_LEDGER.md`: Visual inspection ledger.
- `M3B_PI2_MANIFEST.json`: Machine-readable verification manifest.

---

## 9. Regressions Suite Summary

All required regressions passed completely:
1. **PI2 Route Contract**: 14/14 PASS (`scripts/test_m3b_pi2_product_generation_route.py`)
2. **PI2 Frontend Route Preview**: 10/10 PASS (`scripts/test_m3b_pi2_generation_route.mjs`)
3. **PI1 Generation Guide Bridge**: 12/12 PASS (`scripts/test_m3b_pi1_generation_guide_bridge.py`)
4. **LR1 Rough Guide Contract**: 12/12 PASS (`scripts/test_m3b_lr1_contract.py`)
5. **LR1 Runtime Bridge**: 5/5 PASS (`scripts/test_m3b_lr1_runtime_bridge.py`)
6. **CAST Instance Authoring**: PASS (`scripts/test_m2b_cast_instance_authoring.py`)
7. **CAST Document Roundtrip**: PASS (`scripts/test_m2b_product_document_roundtrip.py`)
8. **M0 Authoring Contract**: PASS (`scripts/test_m0_authoring_contract.py`)
9. **CAST Execution Bridge**: PASS (`scripts/test_m2a_cast_execution_bridge.py`)
10. **Manga Impact Recurrent CAST Runtime**: PASS (`scripts/test_manga_impact_recurrent_cast_runtime.py`)
11. **M1.1 Editor JS**: PASS (`scripts/test_m1_1_editor_js.mjs`)
12. **M2B Minimum-Hand Editor Logic Invariants**: 19/19 PASS (`scripts/test_m2b_minimum_hand_editor.mjs`)
13. **M3B-LR1 Guide Operations**: PASS (`scripts/test_m3b_lr1_guide_ops.mjs`)

Total unit / contract tests executed: **106 tests, 0 failures, 0 errors**.

---

## 10. Invariant & Boundary Verification

- [x] **Schema Unchanged**: `TEGAKI_AUTHORING_DOCUMENT 1.0.0` preserved with zero new persisted routing fields.
- [x] **Production Workflows Untouched**: `MINIMUM_HAND_MANGA_DRAFT.json` and `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` remain unmodified.
- [x] **Zero Graph Swapping**: Visible LiteGraph is never replaced or reloaded at queue time.
- [x] **One-Action OFF**: Single click on `Disable Guide` immediately changes route to Standard.
- [x] **Standard Independence**: AnyTest model is never inspected, checked, or required when Standard route is selected.
- [x] **No Silent Fallback**: If ControlNet model is missing when Guided route is selected, explicit `GUIDED_CONTROLNET_NOT_AVAILABLE` error is raised and shown.
- [x] **Double-Submit Protection**: `Generate Draft` button is locked during preparation and queueing.

---

## 11. Final Classification

```text
PI2_AUTO_ROUTING_INTEGRATED
```

Provisional milestone acceptance: **ACCEPTED_BY_DELEGATED_SOL**  
Final Owner product review: **DEFERRED**
