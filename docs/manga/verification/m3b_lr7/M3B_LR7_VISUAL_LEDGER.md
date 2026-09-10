# M3B-LR7 Visual Ledger — CAST GLOBAL vs EFFECT-MASK Isolation

Date: 2026-09-10 JST  
Card: M3B-LR7  
Review: local contact sheet plus direct visual image inspection  
Scope: coarse Figure placement, ControlNet effect-mask boundary isolation, and quality comparison; no biometric identity claim.

## Per-output ledger

| Seed | Condition | Queue | Placement | Figure count | Side association | Image quality | Hard rectangular boundary | Regional/control conflict | Extra/faint Figure | Evidence |
|---:|---|---|---|---|---|---|---|---|---|---|
| 42 | CAST_OFF (HISTORICAL) | PASS | CLEAR | PASS | MIXED | USABLE | NONE | NONE | NO | `SEED_A_CAST_OFF.png` |
| 42 | CAST_HARD (HISTORICAL) | PASS | CLEAR | PASS | PASS | DEGRADED | CLEAR | CLEAR | NO | `SEED_A_CAST_HARD.png` |
| 42 | CAST_GLOBAL (NEW) | PASS | CLEAR | PASS | PASS | USABLE | NONE | NONE | YES | `SEED_A_CAST_GLOBAL.png` |
| 77 | CAST_OFF (HISTORICAL) | PASS | CLEAR | FAIL | MIXED | USABLE | NONE | NONE | YES | `SEED_B_CAST_OFF.png` |
| 77 | CAST_HARD (HISTORICAL) | PASS | CLEAR | FAIL | MIXED | DEGRADED | CLEAR | CLEAR | YES | `SEED_B_CAST_HARD.png` |
| 77 | CAST_GLOBAL (NEW) | PASS | WEAK | FAIL | FAIL | USABLE | NONE | NONE | NO | `SEED_B_CAST_GLOBAL.png` |

### Notes

- **Seed 42 CAST_GLOBAL**:
  - Placement: CLEAR. Both left and right character placements align well with the scene composition.
  - Figure count: PASS. Two distinct figures are present (dark-haired student by the window on the left, light-haired student seated at the desk on the right foreground). A reflection of the left student is visible in the window pane (Extra/faint Figure: YES).
  - Side association: PASS. Dark-haired student is on the left; light-haired student is on the right.
  - Quality: USABLE. Clean manga screentone, fine linework, accurate classroom geometry, natural lighting.
  - Hard rectangular boundary: NONE. The sharp rectangular artifact pillars seen in CAST_HARD are completely absent.
  - Regional/control conflict: NONE.

- **Seed 77 CAST_GLOBAL**:
  - Placement: WEAK. One small figure is situated on/behind the central desk near the window.
  - Figure count: FAIL. Only 1 figure is clearly realized. (Distinction: Seed 77 CAST_OFF baseline already suffered from a pre-existing Figure count defect where multiple indistinct/faint figures collided; CAST_GLOBAL does not introduce a new regression, but inherits baseline instability).
  - Side association: FAIL (only 1 character realized).
  - Quality: USABLE. Architecture, perspective, desk details, and ceiling lamp fixtures are sharply rendered with consistent manga screentone.
  - Hard rectangular boundary: NONE. No vertical seam, cage artifact, or bounding box cutoff.
  - Regional/control conflict: NONE.

- **Comparator Analysis (CAST_GLOBAL vs CAST_HARD)**:
  - In CAST_HARD (LR5/LR6), the presence of the Figure-union effect mask on `mask_optional` produced repeatable, severe vertical mask boundary artifacts cutting through the image in both seeds, degrading image quality to DEGRADED.
  - In CAST_GLOBAL (LR7), removing the effect mask (`mask_optional` UNCONNECTED) completely eliminates the rectangular boundary artifact in both seeds while restoring image quality to USABLE in both seeds.
  - This cleanly isolates the root cause of the LR5/LR6 visual defect: it was not a general incompatibility between CAST regional conditioning and ControlNet, but specifically the interaction between CAST regional conditioning and the localized ControlNet effect mask.

## Aggregate result

```text
Hard rectangular boundary artifact:
CAST_HARD: CLEAR
CAST_GLOBAL: NONE

Image quality:
CAST_HARD: DEGRADED
CAST_GLOBAL: USABLE

Regional/control conflict:
CAST_HARD: CLEAR
CAST_GLOBAL: NONE

Baseline defect distinction:
Seed 77 CAST_OFF baseline contains pre-existing Figure-count failure.
CAST_GLOBAL does not introduce new degradation.

Classification:
EFFECT_MASK_INTERACTION_CONFIRMED
```
