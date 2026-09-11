# M3B-PI2-BC1 Real Browser Execution Ledger

Date: 2026-09-11T01:21:58.331Z  
Card: M3B-PI2-BC1  
Model: Gemini 3.8 Flash / Antigravity 2.0  
Public PI2 SHA: `f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740`  
Execution mechanism: Real Chrome via Playwright (DOM rendering, actual click events, element screenshots)

## Browser Verification Matrix (B0–B5)

| ID | Test Case | Route Decision | ControlNet Nodes | Queue Result | Output Artifact | SHA256 |
|---|---|---|---|---|---|---|
| B0 | B0_STANDARD_NO_GUIDE | `STANDARD_NO_GUIDE` | 0 | PASS | `BC1_B0_OUTPUT.png` | `fd105cf669b61fba...` |
| B1 | B1_GUIDE_ZERO_FIGURES | `STANDARD_NO_GUIDE` | 0 | PASS | `N/A (Route verified)` | `N/A` |
| B2 | B2_SIMPLE_GUIDED | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `BC1_B2_OUTPUT.png` | `c6a63872d8153c95...` |
| B3 | B3_ONE_ACTION_DISABLE | `STANDARD_NO_GUIDE` | 0 | PASS | `BC1_B3_OUTPUT.png` | `a923e8d4cb7a627c...` |
| B4 | B4_REENABLE_GUIDE | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `N/A (Route verified)` | `N/A` |
| B5 | B5_CAST_GUIDED | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `BC1_B5_OUTPUT.png` | `6a9ea70764457391...` |

## Real Browser Acceptance Gate Results

- **B0 (No-Guide)**: Rendered badge showed `Generation: Standard`. Real click on `✨ Generate Draft` visibly transitioned button to preparing state, submitted `STANDARD_NO_GUIDE` prompt with 0 ControlNet nodes, and completed image generation (`BC1_B0_OUTPUT.png`).
- **B1 (Guide exists, zero Figures)**: With Guide uploaded but 0 figures, badge remained `Generation: Standard`. Click queued `STANDARD_NO_GUIDE` with 0 ControlNet nodes.
- **B2 (SIMPLE Guide-assisted)**: With enabled Guide and valid figure region, badge immediately updated to `Generation: Guide-assisted`. Click queued `GUIDED_CLEAN_GLOBAL` with core `ControlNetApplyAdvanced`. Output image generated cleanly (`BC1_B2_OUTPUT.png`).
- **B3 (One-action OFF)**: Single click on `Disable Guide` immediately changed badge to `Generation: Standard` and button to `Enable Guide`. Click queued `STANDARD_NO_GUIDE` with 0 ControlNet nodes (`BC1_B3_OUTPUT.png`).
- **B4 (Re-enable)**: Single click on `Enable Guide` immediately restored `Generation: Guide-assisted`. Click queued `GUIDED_CLEAN_GLOBAL`.
- **B5 (CAST Guided)**: With CAST authoring (2 CAST, 2 Character Instances) and enabled Guide, badge showed `Generation: Guide-assisted`. Click queued `GUIDED_CLEAN_GLOBAL` with CAST conditioning active (`BC1_B5_OUTPUT.png`).
- **Real Persistence Gate**: Saved workflow in browser for State A (Guided) and State B (Disabled Standard); reloaded each through ComfyUI graph loader. Badges restored identically (`BC1_PERSIST_GUIDED_RELOAD.png` and `BC1_PERSIST_STANDARD_RELOAD.png`). No persisted routing fields added to schema.
- **Real Double-Submit Gate**: Rapid double-click dispatched; second click blocked by disabled button state (`isGenerating = true`). Exactly 1 prompt queued.
- **Queue Feedback Gate**: Both routes verified visible feedback (`Queued · Standard` and `Queued · Guide-assisted`). Button returned to `✨ Generate Draft`.
