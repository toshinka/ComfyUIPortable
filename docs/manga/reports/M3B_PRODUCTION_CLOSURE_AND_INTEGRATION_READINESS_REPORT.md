# M3B Production Closure & Integration Readiness Report

Date: 2026-09-11 JST
Card: M3B-PC1
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: BOUNDED CLOSURE / DOCUMENTATION + REGRESSION ONLY
Final product review: Owner / DEFERRED

---

## 1. Executive Summary

Milestone M3B (Minimum-Hand Rough Guide Generation & Integration) has achieved full production closure.
Across 10 research cards (LR1–LR8), 2 production integration cards (PI1, PI2), 1 browser closure card (PI2-BC1), and the final boundary freeze (PC1), the Manga subsystem has established a fully deterministic, dual-route generation capability (Standard vs Guided) with zero user-side workflow friction, zero document schema pollution, and 100% test and browser qualification.

With all technical, runtime, browser, and regression gates satisfied, M3B is classified as **`M3B_PRODUCTION_CLOSED`** and Manga authoring is declared **`MANGA_READY_FOR_INTEGRATION_DESIGN`**. Shared-shell implementation remains explicitly **`NOT AUTHORIZED`** pending cross-track alignment with H3.

---

## 2. M3B Research Progression (LR1 – LR8)

1. **M3B-LR1 (Rough Guide Foundation)**:
   - Established `rough_manga` guide contract in `TEGAKI_AUTHORING_DOCUMENT 1.0.0`.
   - Built authoring and runtime bridges separating raw reference artwork from structural Figure regions.
2. **M3B-LR2 (Initial AnyTest Exploration)**:
   - Evaluated candidate control models; identified need for exact SDXL/Illustrious compatibility; paused at inventory gate.
3. **M3B-LR2R1 (Shared Store Acquisition & A/B Resume)**:
   - Pinned `CN-anytest4_illustrious2_A.safetensors` from shared reForge store without duplicating files.
   - Demonstrated generation influence in ComfyUI runtime; noted raw mannequin baseline quality limitations.
4. **M3B-LR3 (Derived CLEAN Guide Research)**:
   - Discovered that rendering a deterministic, clean flat silhouette from Figure geometry eliminated scribble noise and artifacting present in hand-drawn guides.
   - Retained Derived CLEAN Guide as primary research candidate.
5. **M3B-LR4 (Figure-Union Mask Locality Research)**:
   - Evaluated spatial confinement of ControlNet influence via figure-union masks. Verified locality principles.
6. **M3B-LR5 & LR6 (CAST-Masked & Soft-Edge Compatibility Research)**:
   - Discovered that applying hard or softened effect masks directly to the ControlNet node created prominent visual boundaries and seam artifacts with Regional Prompts.
7. **M3B-LR7 (Effect-Mask Isolation Confirmation)**:
   - Rigorously confirmed that removing the effect mask entirely and applying ControlNet globally with clean silhouette input produced seamless, artifact-free blending.
8. **M3B-LR8 (Core CAST_GLOBAL Robustness Qualification)**:
   - Proved that ComfyUI core `ControlNetApplyAdvanced` with global CLEAN silhouette and standard regional prompt conditioning achieved superior stability (0 regressions across 12-image matrix).
   - Eliminated all dependencies on Advanced-ControlNet (ACN) custom nodes.
   - Result: `CORE_GLOBAL_QUALIFIED`.

---

## 3. Production Integration (PI1 & PI2)

1. **M3B-PI1 (Production Backend Integration)**:
   - Promoted qualified CLEAN Global architecture into production workflow `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`.
   - Created `TegakiMangaGenerationGuideBridge` to generate deterministic (1, H, W, 3) silhouette tensors at runtime from document Figure geometry.
   - Preserved unmodified canonical `MINIMUM_HAND_MANGA_DRAFT.json` for no-guide generation.
   - Validated 4/4 live runs with bit-exact parity against LR8 candidate; 0 ACN nodes, 0 effect masks.
   - Result: `PI1_BACKEND_INTEGRATED`.
2. **M3B-PI2 (Automatic Routing & Product Generate Integration)**:
   - Eliminated manual workflow swapping.
   - Integrated deterministic queue-time routing via `POST /tegaki/manga/generation/prepare` endpoint.
   - Embedded single product-facing `✨ Generate Draft` button with real-time status badge (`Generation: Standard` vs `Generation: Guide-assisted`) into Minimum-Hand Scene Editor.
   - Implemented one-action OFF (`Disable Guide`) and one-action re-enable (`Enable Guide`).
   - Implemented double-submit prevention and missing model fail-closed handling.
   - Result: `PI2_AUTO_ROUTING_INTEGRATED`.

---

## 4. Real Browser Product Flow Closure (PI2-BC1)

To close the acceptance gate without substituting API scripts for real UI interactions, automated real Chromium execution (Playwright) was conducted against `http://127.0.0.1:8188`:
- **Live Route Badge Transitions**: Confirmed immediate DOM badge changes upon toggling guide visibility.
- **Generate Draft Execution**: Executed real DOM click events; verified preparation, queueing, and completed output generation across all matrix scenarios (B0, B1, B2, B3, B4, B5).
- **One-Action Disable / Enable**: Single click on `Disable Guide` immediately set badge to `Generation: Standard` and queued 0 ControlNet nodes; single click on `Enable Guide` immediately restored `Generation: Guide-assisted`.
- **Double-Submit Prevention**: Rapid double-clicks safely locked the button during execution.
- **Persistence & Reload**: Document JSON serialized to storage and reloaded into browser canvas; correctly restored Guided and Standard states with zero schema alterations.
- Result: `PI2_BROWSER_CLOSED`.

---

## 5. Current Production Contracts Summary

1. **Standard Route (`STANDARD_NO_GUIDE`)**:
   - Active when no eligible guide or 0 figures exist.
   - Zero ControlNet dependencies (no loader, no apply node, no bridge).
2. **Guided Route (`GUIDED_CLEAN_GLOBAL`)**:
   - Active when >=1 enabled rough guide with >=1 valid Figure region exists.
   - Fixed configuration: `CN-anytest4_illustrious2_A.safetensors`, strength 0.75, start 0.0, end 1.0, core `ControlNetApplyAdvanced`.
   - 0 Advanced-ControlNet nodes, 0 effect masks.
3. **RAW Asset Separation**:
   - RAW raster pixels are strictly reference/editing aids; never fed into ControlNet.
4. **Persistent Schema**:
   - Strictly `TEGAKI_AUTHORING_DOCUMENT 1.0.0`. Zero transient routing parameters persisted.
5. **Semantic Invariants**:
   - Semantic Scene Region != Visual Panel Frame.
   - CAST != Character Instance.
   - Character Instance area = regional text conditioning.
   - Guide Figure Region = rough visual placement provenance.

---

## 6. Known Limitations & Constraints

1. **ControlNet Model Dependency**:
   - Guided generation strictly requires `CN-anytest4_illustrious2_A.safetensors` in `models/controlnet/`.
   - If missing, explicit error `GUIDED_CONTROLNET_NOT_AVAILABLE` is displayed; silent fallback to Standard is prohibited.
2. **Coarse Guidance vs Seed Randomness**:
   - Seed variation is an intentional creative brainstorming feature.
   - Guidance provides coarse layout and character positioning; it does not enforce rigid contour tracing or exact camera angle parity.
3. **Output Namespace**:
   - Remains `output/Tegaki`. No migration attempted in M3B.

---

## 7. Cross-Track Alignment & Ownership Boundary

1. **Provisional Integration Vocabulary**:
   - `TEGAKI` umbrella hosting `H3` and `Manga`.
2. **Separation of Ownership**:
   - Manga owns `docs/manga/`, `workflows/manga/`, custom nodes in `tegaki_manga_nodes`, `POST /tegaki/manga/generation/prepare`, and Manga test suites.
   - H3 owns its video/still pipelines, nodes, workflows, and server routes.
   - Schemas, workflows, and generation pipelines MUST NOT be merged.
3. **Future Shared Shell Principle**:
   - A future shared shell should act as a navigation host (switching tabs/views), NOT a unified generation pipeline.
   - History database and launcher unification remain undecided.

---

## 8. Automated Regressions Audit

All 11 regression suites executed and passed with 0 errors:
- PI2 Route Contract: 14/14 PASS (`scripts/test_m3b_pi2_product_generation_route.py`)
- PI2 Frontend Route Preview: 10/10 PASS (`scripts/test_m3b_pi2_generation_route.mjs`)
- PI1 Generation Guide Bridge: 12/12 PASS (`scripts/test_m3b_pi1_generation_guide_bridge.py`)
- LR1 Rough Guide Contract: 12/12 PASS (`scripts/test_m3b_lr1_contract.py`)
- LR1 Runtime Bridge: 5/5 PASS (`scripts/test_m3b_lr1_runtime_bridge.py`)
- Guide Operations: PASS (`scripts/test_m3b_lr1_guide_ops.mjs`)
- Minimum-Hand Editor Logic: 19/19 PASS (`scripts/test_m2b_minimum_hand_editor.mjs`)
- CAST Instance Authoring: 7/7 PASS (`scripts/test_m2b_cast_instance_authoring.py`)
- CAST Execution Bridge: 14/14 PASS (`scripts/test_m2a_cast_execution_bridge.py`)
- Product Document Roundtrip: 5/5 PASS (`scripts/test_m2b_product_document_roundtrip.py`)
- Recurrent CAST Runtime: 3/3 PASS (`scripts/test_recurrent_cast_instances.py`)

---

## 9. Final Classifications

- **M3B Milestone**: `M3B_PRODUCTION_CLOSED`
- **Manga Track Readiness**: `MANGA_READY_FOR_INTEGRATION_DESIGN`
- **Cross-Track Implementation**: `NOT AUTHORIZED`
- **Final Owner Product Review**: `DEFERRED`
