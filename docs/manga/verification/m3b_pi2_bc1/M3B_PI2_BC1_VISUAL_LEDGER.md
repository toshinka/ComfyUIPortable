# M3B-PI2-BC1 Visual Ledger

Date: 2026-09-11T01:21:58.332Z  
Card: M3B-PI2-BC1  
Baseline PI2 SHA: `f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740`  

## Rendered UI Screenshots (Playwright Real Chrome)

- `BC1_B0_STANDARD_UI.png`: Shows initial Standard route badge with No-Guide canvas.
- `BC1_B2_GUIDED_UI.png`: Shows Guide-assisted badge with simple guided canvas.
- `BC1_B3_DISABLED_STANDARD_UI.png`: Shows one-action Disable Guide immediately switching to Standard.
- `BC1_B4_REENABLED_GUIDED_UI.png`: Shows one-action Enable Guide restoring Guide-assisted badge.
- `BC1_B5_CAST_GUIDED_UI.png`: Shows Guide-assisted badge with CAST authoring.
- `BC1_PERSIST_GUIDED_RELOAD.png`: Shows reloaded workflow preserving Guide-assisted state.
- `BC1_PERSIST_STANDARD_RELOAD.png`: Shows reloaded workflow preserving Disabled Standard state.

## Generated Output Images (Real UI Queue Path)

- `BC1_B0_OUTPUT.png`: Standard draft output. Clean monochrome manga draft, 0 ControlNet artifacts.
- `BC1_B2_OUTPUT.png`: Simple guided draft output. Clean global ControlNet guidance, usable quality, no hard rectangular boundary.
- `BC1_B3_OUTPUT.png`: Disabled Guide draft output. Canonical standard draft, zero ControlNet influence.
- `BC1_B5_OUTPUT.png`: CAST guided draft output. Regional character conditioning active alongside clean global ControlNet guidance.
