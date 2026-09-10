# M3B-LR4 Visual Ledger

Card: `M3B-LR4`  
Live ComfyUI prompt: `16523812-a927-404e-85a8-b43cc4f6a52b`  
Queue status: `success` / technical gate `6/6 PASS`  
Canvas: `832x1216`, RGB PNG  
Control image: LR3 CLEAN Guide, SHA256 `96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`  
Mask: existing Figure union, direct bridge evidence SHA256 `6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb`

## Technical output ledger

| Seed | Condition | Source output | Evidence | SHA256 | Dimensions | Queue |
|---:|---|---|---|---|---|---|
| 42 | OFF | `M3B_LR4_SEED_A_OFF_00001_.png` | `SEED_A_OFF.png` | `7a35216efa241080ddbdca8e43e464944b90c2cd8812e7123e8d87078ea03646` | 832x1216 RGB | PASS |
| 42 | CLEAN_GLOBAL | `M3B_LR4_SEED_A_GLOBAL_00001_.png` | `SEED_A_GLOBAL.png` | `8d5b30bf97068cc2042237cc96aa5ed6203a955e1f0788d4b673febdc165eff3` | 832x1216 RGB | PASS |
| 42 | CLEAN_MASKED | `M3B_LR4_SEED_A_MASKED_00001_.png` | `SEED_A_MASKED.png` | `b0c8f0e4d18a9b0b439553d51f548d9134ad711bb9d27411f212ffbe5da03897` | 832x1216 RGB | PASS |
| 77 | OFF | `M3B_LR4_SEED_B_OFF_00001_.png` | `SEED_B_OFF.png` | `91ddbfd697ab1be5267bdcf36bf809cd32e7f09cdeb820d9d07fa700b0102a85` | 832x1216 RGB | PASS |
| 77 | CLEAN_GLOBAL | `M3B_LR4_SEED_B_GLOBAL_00001_.png` | `SEED_B_GLOBAL.png` | `f6a5b167d7ab7181d0f63388db52240bd22048d1bd3be849b2b06efda0b7e6ae` | 832x1216 RGB | PASS |
| 77 | CLEAN_MASKED | `M3B_LR4_SEED_B_MASKED_00001_.png` | `SEED_B_MASKED.png` | `908f23d19556c5d4e0df390af4be7cb0b5199e0be0e613a93d68f0da1f548282` | 832x1216 RGB | PASS |

## Manual visual review

`OFF` is included as the fixed baseline and is not part of the locality enum.
The expected count is two intended Figures; identity correctness is not judged.

| Seed | Condition | Figure count | Placement | Quality | Notes |
|---:|---|---|---|---|---|
| 42 | OFF | FAIL | NONE | USABLE | Multi-panel page; no stable intended two-Figure composition. |
| 42 | CLEAN_GLOBAL | PASS | CLEAR | USABLE | Two figures are clearly separated left/right in one classroom image. |
| 42 | CLEAN_MASKED | PASS | CLEAR | USABLE | Two figures remain left/right with comparable full-body scale; no material quality regression. |
| 77 | OFF | FAIL | NONE | USABLE | Multi-panel/group composition without stable intended two-Figure placement. |
| 77 | CLEAN_GLOBAL | FAIL | NONE | USABLE | One visible person; the second intended Figure is lost. |
| 77 | CLEAN_MASKED | PASS | WEAK | USABLE | Two figures return; they are more central/closer together than the Seed 42 pair, but the intended pair is present. |

### Boundary and variation review

- Mask-boundary artifacts: **NONE**. No hard rectangular edge, local tint discontinuity, anatomy break, or background discontinuity was visible in either MASKED output.
- Seed 42 MASKED: two-Figure presence and usable quality retained versus GLOBAL.
- Seed 77 MASKED: two-Figure presence improves from GLOBAL's one visible person.
- Seed variation: **PRESENT**. Seed 42 and Seed 77 produce visibly different compositions while the masked condition remains useful.
- Review surfaces: local full-resolution images, contact sheet, and live ComfyUI `/view` pages.

## Locality result

`LOCALITY_SUPPORTED`

The result meets all six Card criteria: Seed 77 improves presence over GLOBAL;
Seed 42 has no material regression; both MASKED outputs contain two Figures;
quality remains USABLE; no boundary artifact is apparent; and seed variation is
PRESENT.
