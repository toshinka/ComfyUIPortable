# M3B-LR6 Visual Ledger — CAST Soft-Edge Figure Mask Compatibility

Date: 2026-09-10 JST  
Card: M3B-LR6  
Review: local contact sheet plus live ComfyUI browser `/view` review  
Scope: coarse Figure locality and ControlNet boundary review; no biometric identity claim.

## Per-output ledger

| Seed | Condition | Queue | Placement | Figure count | Side association | Broad acting | Image quality | HARD/SOFT boundary artifact | Evidence |
|---:|---|---|---|---|---|---|---|---|---|
| 42 | CAST_OFF | PASS | CLEAR | PASS | MIXED | WEAK | USABLE | NONE | `SEED_A_CAST_OFF.png` |
| 42 | CAST_HARD | PASS | CLEAR | PASS | PASS | WEAK | DEGRADED | CLEAR | `SEED_A_CAST_HARD.png` |
| 42 | CAST_SOFT | PASS | CLEAR | PASS | PASS | WEAK | DEGRADED | CLEAR | `SEED_A_CAST_SOFT.png` |
| 77 | CAST_OFF | PASS | CLEAR | FAIL | MIXED | WEAK | USABLE | NONE | `SEED_B_CAST_OFF.png` |
| 77 | CAST_HARD | PASS | CLEAR | FAIL | MIXED | WEAK | DEGRADED | CLEAR | `SEED_B_CAST_HARD.png` |
| 77 | CAST_SOFT | PASS | CLEAR | FAIL | MIXED | WEAK | DEGRADED | CLEAR | `SEED_B_CAST_SOFT.png` |

### Notes

- Seed 42 CAST_OFF has two visible Figures but mixed identity/side association.
- Seed 42 CAST_HARD and CAST_SOFT retain two coarse left/right Figures. The
  short-dark Figure remains on the left and the long-light Figure on the
  right, but the expected seated-right acting is not retained.
- Seed 77 CAST_OFF already has an extra Figure-like presence. This is a
  pre-existing CAST baseline defect and is not charged to SOFT as a new
  Figure-count failure.
- Seed 77 CAST_HARD and CAST_SOFT both retain the seed-sensitive extra/faint
  Figure behavior. SOFT does not repair the baseline count instability.
- The hard vertical/rectangular boundary signature is clear in both HARD
  outputs and remains clear in both SOFT outputs. The soft edge changes the
  transition but does not remove the visually disruptive mask-aligned
  division.
- No Character-mask feathering, strength change, timing change, geometry
  change, or Character/Figure-region alignment was performed.

## Aggregate result

```text
HARD boundary artifact: CLEAR
SOFT boundary artifact: CLEAR
HARD quality: DEGRADED
SOFT quality: DEGRADED
SOFT placement: CLEAR
SOFT Figure count: FAIL
Side association: MIXED
Seed variation: PRESENT
```

The SOFT mask does not meet the compatible criteria because the ControlNet
boundary remains clear and image quality remains degraded in both seeds. The
seed-77 Figure-count failure is retained as a baseline defect distinction;
the compatibility decision is driven by the persistent ControlNet-specific
boundary/quality failure.

## Result

```text
SOFT_MASK_CONFLICT
```

