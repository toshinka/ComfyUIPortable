# M3B-PI2 Browser Execution Ledger

Date: 2026-09-11 09:33:28 JST  
Executor: Gemini 3.8 Flash / Antigravity 2.0  
Authority SHA: `45487bc741a9f6bb1f8025f50a27868fcc1108ae`  

## Matrix Results (B0–B5)

| ID | Test Case | Route Decision | ControlNet Nodes | Queue Result | Output Artifact | SHA256 |
|---|---|---|---|---|---|---|
| B0 | B0_STANDARD_NO_GUIDE | `STANDARD_NO_GUIDE` | 0 | PASS | `B0_STANDARD_NO_GUIDE.png` | `0761e6fc3116...` |
| B1 | B1_GUIDE_ZERO_FIGURES | `STANDARD_NO_GUIDE` | 0 | PASS | `N/A (Route verified)` | `N/A` |
| B2 | B2_SIMPLE_GUIDED | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `B2_SIMPLE_GUIDED.png` | `d02c78aa8ad9...` |
| B3 | B3_DISABLED_STANDARD | `STANDARD_NO_GUIDE` | 0 | PASS | `B3_DISABLED_STANDARD.png` | `bcdddb82958e...` |
| B4 | B4_REENABLE_GUIDED | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `N/A (Route verified)` | `N/A` |
| B5 | B5_CAST_GUIDED | `GUIDED_CLEAN_GLOBAL` | 3 | PASS | `B5_CAST_GUIDED.png` | `792db5aeed7e...` |

## Route Transition Proofs
- **B0 (No Guide)**: Evaluates to `STANDARD_NO_GUIDE`. Zero ControlNet/bridge nodes submitted. Renders cleanly.
- **B1 (Guide Uploaded, 0 Figures)**: Uploading an image alone evaluates to `STANDARD_NO_GUIDE`. Generation influence remains inactive.
- **B2 (Simple Guided)**: Enabled Guide with figures evaluates to `GUIDED_CLEAN_GLOBAL`. Renders with CLEAN GLOBAL ControlNet.
- **B3 (One-action Disable)**: Clicking 'Disable Guide' once immediately changes route to `STANDARD_NO_GUIDE`. Zero ControlNet nodes.
- **B4 (Re-enable)**: Clicking 'Enable Guide' immediately restores `GUIDED_CLEAN_GLOBAL`.
- **B5 (CAST Guided)**: CAST regional conditioning remains fully active alongside `GUIDED_CLEAN_GLOBAL` ControlNet guidance.
