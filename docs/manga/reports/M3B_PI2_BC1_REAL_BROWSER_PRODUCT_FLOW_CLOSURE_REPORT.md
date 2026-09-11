# M3B-PI2-BC1 — Real Browser Product Flow Closure Report

Date: 2026-09-11 JST  
Issuer: Web GPT SOL  
Card: M3B-PI2-BC1  
Model: Gemini 3.8 Flash / Antigravity 2.0  
Classification: PI2_BROWSER_CLOSED  
Intermediate milestone acceptance: PENDING_SOL_REVIEW  
Final Owner product review: DEFERRED  

---

## 1. Public Authority & Baseline

- **Verified Public Baseline**: `45487bc741a9f6bb1f8025f50a27868fcc1108ae`
- **Published PI2 Commit**: `f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740`
- **M3B-PI2 State**: PUBLISHED / TECHNICAL PASS
- **Card**: M3B-PI2-BC1 (Real Browser Product Flow Closure)
- **Active Card at Start**: `M3B-PI2-BC1`
- **Active Card on Completion**: `NONE`
- **Publication Status**: LOCAL / Owner push required
- **Source Code Repair**: NONE (Zero product source modifications required)

---

## 2. Why BC1 Was Required

Card M3B-PI2 provided comprehensive unit tests, contract tests, and a live runner (`m3b_pi2_run_browser_matrix.py`) exercising the backend preparation and queue endpoints directly. However, as noted by Web GPT SOL, direct API requests do not prove actual user interaction through the rendered Minimum-Hand UI.

BC1 was issued to close this acceptance gate using real browser execution against the live ComfyUI UI rendered in Chromium. It proves that a human author can operate the rendered UI controls:
- Observe live route badge transitions (`Generation: Standard` vs `Generation: Guide-assisted`).
- Click `✨ Generate Draft` directly from the rendered interface.
- Perform a single-action `Disable Guide` to revert immediately to Standard draft generation.
- Perform a single-action `Enable Guide` to immediately re-engage Guided generation.
- Rely on duplicate submit prevention during prompt preparation and queueing.
- Save and reload workflows with Guide state and derived routing preserved, without adding persisted routing fields to the document schema.

---

## 3. Real Browser Execution Environment

- **Browser**: Real Google Chrome (Channel `chrome`, Headless Chromium runner via Playwright)
- **ComfyUI Server**: Live portable instance at `http://127.0.0.1:8188`
- **Workflow**: `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` with live LiteGraph canvas and `TegakiMinimumHandSceneEditor` DOM widget container.
- **Interaction Mechanism**: Real DOM pointer/click events dispatching to `#btn-generate-draft`, `#route-badge`, layer selector buttons, and `#btn-toggle-guide`.
- **Evidence Capture**: Real rendered DOM element screenshots (`.png`) and full SaveImage output images directly from the UI queue path.

---

## 4. Real Browser Verification Matrix (B0–B5)

| ID | Case | Live Badge Text | Actual Backend Route | ControlNet Nodes | Queue Feedback | Output Artifact | SHA256 (prefix) | Result |
|---|---|---|---|---|---|---|---|---|
| **B0** | Real No-Guide flow | `Generation: Standard` | `STANDARD_NO_GUIDE` | 0 | `✅ Queued · Standard` | `BC1_B0_OUTPUT.png` | `fd105cf669b61fba` | **PASS** |
| **B1** | Guide uploaded, 0 figures | `Generation: Standard` | `STANDARD_NO_GUIDE` | 0 | `✅ Queued · Standard` | N/A (Route verified) | N/A | **PASS** |
| **B2** | SIMPLE Guide-assisted | `Generation: Guide-assisted` | `GUIDED_CLEAN_GLOBAL` | 3 | `✅ Queued · Guide-assisted` | `BC1_B2_OUTPUT.png` | `c6a63872d8153c95` | **PASS** |
| **B3** | One-action OFF (`Disable Guide`) | `Generation: Standard` | `STANDARD_NO_GUIDE` | 0 | `✅ Queued · Standard` | `BC1_B3_OUTPUT.png` | `a923e8d4cb7a627c` | **PASS** |
| **B4** | Re-enable (`Enable Guide`) | `Generation: Guide-assisted` | `GUIDED_CLEAN_GLOBAL` | 3 | `✅ Queued · Guide-assisted` | N/A (Route verified) | N/A | **PASS** |
| **B5** | CAST Guided | `Generation: Guide-assisted` | `GUIDED_CLEAN_GLOBAL` | 3 | `✅ Queued · Guide-assisted` | `BC1_B5_OUTPUT.png` | `6a9ea70764457391` | **PASS** |

### Matrix Observations
1. **B0 (No-Guide)**: Rendered badge showed `Generation: Standard`. Clicking `✨ Generate Draft` submitted a prompt containing 0 ControlNet/Bridge nodes. Output image `MangaDraft_M1_00022_.png` rendered cleanly.
2. **B1 (Guide exists, zero Figures)**: An uploaded Guide without Figure Regions evaluated to `Generation: Standard`. The prompt submitted zero ControlNet nodes.
3. **B2 (SIMPLE Guide-assisted)**: With a valid Figure Region, badge immediately transitioned to `Generation: Guide-assisted`. Prompt submitted core `ControlNetApplyAdvanced` with `TegakiMangaGenerationGuideBridge` (0 ACN, 0 effect masks). Output `MangaDraft_M1_00024_.png` showed usable manga draft with clean guidance.
4. **B3 (One-action OFF)**: In the Rough Guide layer, clicking `Disable Guide` once immediately updated the badge to `Generation: Standard` and the toggle button to `Enable Guide`. Clicking `✨ Generate Draft` queued `STANDARD_NO_GUIDE` with 0 ControlNet nodes. Output `MangaDraft_M1_00025_.png` produced canonical standard art.
5. **B4 (Re-enable)**: Clicking `Enable Guide` once immediately restored `Generation: Guide-assisted` and the button to `Disable Guide`. Prompt queued `GUIDED_CLEAN_GLOBAL`.
6. **B5 (CAST Guided)**: CAST authoring document with 2 CAST entries (`Left Student`, `Right Student`) and 2 Character Instances evaluated to `Generation: Guide-assisted`. Regional text conditioning remained active alongside clean global ControlNet guidance. Output `MangaDraft_M1_00027_.png` showed character staging within the classroom.

---

## 5. Persistence & Invariant Gates

### Real Persistence Gate (Section 12)
- **State A (Enabled Guide + Figures)**: Graph serialized via `app.graph.serialize()` and reloaded via `app.loadGraphData()`. Rendered badge restored to `Generation: Guide-assisted`. Screenshot: `BC1_PERSIST_GUIDED_RELOAD.png`.
- **State B (One-action Disable Guide)**: Clicked `Disable Guide`, graph serialized and reloaded. Rendered badge restored to `Generation: Standard`. Screenshot: `BC1_PERSIST_STANDARD_RELOAD.png`.
- **Schema Purity**: Document keys inspected after reload: `schema_id`, `schema_version`, `document_id`, `pages`, `metadata`. No persisted `route` or `generation_route` field was added. The schema remains strictly `TEGAKI_AUTHORING_DOCUMENT 1.0.0`.

### Real Double-Submit Gate (Section 13)
- When `✨ Generate Draft` was clicked twice rapidly:
  - First click immediately set `btn.disabled = true`, `btn.style.opacity = '0.5'`, and text to `⏳ Preparing...`.
  - Second click event was blocked by the disabled UI state (`isGenerating = true`).
  - Exactly 1 prompt was submitted to the ComfyUI queue.

### Queue Feedback Gate (Section 14)
- Visible feedback confirmed for both routes:
  - `Queued · Standard`
  - `Queued · Guide-assisted`
- Button returned to `✨ Generate Draft` and re-enabled upon queue completion.

### Browser Error Presentation (Section 15)
- Rendered error surface (`#generate-feedback`) exists and displays inline red error text upon API failure.
- Destructive environment mutation was prohibited:
  ```text
  Browser error injection:
  NOT PERFORMED — destructive environment mutation prohibited

  Automated error-path regression:
  PASS
  ```

---

## 6. Visual Output Gate

All retained outputs were inspected directly:
- `BC1_B0_OUTPUT.png`: Standard generation. Clean inked manga linework, no ControlNet influence.
- `BC1_B2_OUTPUT.png`: Simple guided generation. Usable draft quality, clean guidance from rough layout, **zero hard rectangular boundary artifacts**, **zero RAW raster artifacts**.
- `BC1_B3_OUTPUT.png`: One-action disabled generation. Clean standard draft, zero ControlNet influence.
- `BC1_B5_OUTPUT.png`: CAST guided generation. Two distinct character instances staged within classroom environment, clean screentone, **zero hard rectangular artifacts**.

---

## 7. Automated Regressions

Full bounded regression suite executed after browser closure:
- PI2 Python route contract: **14/14 PASS**
- PI2 JS frontend route parity: **10/10 PASS**
- PI1 Generation Guide Bridge: **12/12 PASS**
- LR1 rough guide contract: **12/12 PASS**
- LR1 runtime bridge: **5/5 PASS**
- LR1 guide ops: **PASS**
- Minimum-Hand editor invariants: **19/19 PASS**
- CAST instance authoring: **7/7 PASS**
- CAST execution bridge: **14/14 PASS**
- Product document roundtrip: **5/5 PASS**
- Recurrent CAST runtime: **3/3 PASS**

---

## 8. Classification & Closure

- **Real Browser Used**: YES (Playwright Chrome against live ComfyUI frontend)
- **API Runner Used as Browser Substitute**: NO
- **Source Repair Performed**: NO (0 product source modifications)
- **Browser Acceptance Gate**: **PI2_BROWSER_CLOSED**
- **PI2 Milestone Acceptance**: **PENDING_SOL_REVIEW**
- **Final Owner Product Review**: **DEFERRED**
