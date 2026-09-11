# M3B-PI2 Visual Ledger

Date: 2026-09-11 09:33:28 JST  
Executor: Gemini 3.8 Flash / Antigravity 2.0  

## Visual Evidence Inventory

| Artifact | Route | Seed | Description | Inspection Result |
|---|---|---|---|---|
| `B0_STANDARD_NO_GUIDE.png` | `STANDARD_NO_GUIDE` | 42 | Canonical baseline generation | PASS (Clean line art, no artifacts) |
| `B2_SIMPLE_GUIDED.png` | `GUIDED_CLEAN_GLOBAL` | 42 | Guide-assisted draft in Simple mode | PASS (Guide placement followed, natural) |
| `B3_DISABLED_STANDARD.png` | `STANDARD_NO_GUIDE` | 42 | Generation after 1-click Disable Guide | PASS (Exact match to standard behavior) |
| `B5_CAST_GUIDED.png` | `GUIDED_CLEAN_GLOBAL` | 42 | Guide-assisted draft in CAST mode | PASS (CAST conditioning + Guide intact) |

## Visual Observations
1. In all runs, rendered outputs are completely present without queue or model errors.
2. No hard rectangular ControlNet bounding box artifacts are visible.
3. Frame overlay borders (line thickness 4) are preserved downstream across all generated outputs.
