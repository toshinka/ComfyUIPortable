# M3B-PI1 Visual Ledger — Production Matrix

Date: 2026-09-11 JST  
Authority: Web GPT SOL (Reviewing public commit `b5c79b85ed2fdeec1bf30254945db569666ecfa4`)  
Classification: PRODUCTION_BACKEND_QUALIFIED  

---

## 1. Clean Generation Guide Reference

- **File**: `M3B_PI1_GENERATION_GUIDE.png`
- **SHA256**: `96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`
- **Parity with LR3 Reference**: EXACT (Match: 100%)
- **Renderer**: `draw_single_character_mannequin(flat_silhouette, full_body, standing_neutral)`
- **RAW Pixels Accessed**: ZERO (Geometry projection only)

---

## 2. Production Matrix Results

| Run | Name | Workflow | Input Mode | Seed | Guide Condition | Output File | SHA256 | Image Quality | Boundary Artifacts | Regional Conflict |
|---|---|---|---|---|---|---|---|---|---|---|
| P0 | Baseline No-Guide | `MINIMUM_HAND_MANGA_DRAFT.json` | simple | 42 | NONE | `P0_NO_GUIDE.png` | `074e5b9ef95f0870e885197f34f2c79c91f1aa8a4828f3877f9752362e33a721` | USABLE | NONE | NONE |
| P1 | Guided SIMPLE | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | simple | 42 | Clean Global | `P1_SIMPLE_GUIDED.png` | `e3d5776c690e68dd40fd4df75407be9e209ef75f73efe084a68aaa67281b29d5` | USABLE | NONE | NONE |
| P2 | Guided CAST Seed 42 | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | cast | 42 | Clean Global | `P2_CAST_GUIDED_SEED42.png` | `d10ddbc54d62beab0d8eca21c26754c4a75c5c96170eea4d44bca437e46557ee` | USABLE | NONE | NONE |
| P3 | Guided CAST Seed 202 | `MINIMUM_HAND_MANGA_GUIDED_DRAFT.json` | cast | 202 | Clean Global | `P3_CAST_GUIDED_SEED202.png` | `6ac3682428ef708a39f0e9f099b7bafe990e24dc6aa0e63579495f7d6927a47f` | USABLE | NONE | NONE |

---

## 3. Visual Gate Assessment (Section 33)

1. **Image Quality**: USABLE across all 4 runs.
2. **Hard Rectangular Boundary**: NONE. No effect mask or bounding box artifacts.
3. **Regional/Control Conflict**: NONE. Regional CAST conditioning (Alice/Bob left/right) and global guide placement compose seamlessly.
4. **Obvious RAW-guide Artifact**: NONE. Only flat-silhouette mannequins rendered into ControlNet.
5. **Seed Creativity**: Preserved. Seed 42 and Seed 202 exhibit distinct stylistic interpretations while honoring gross layout.
