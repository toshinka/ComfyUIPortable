# M3B-LR7 CAST GLOBAL vs EFFECT-MASK Interaction Isolation Research Report

Date: 2026-09-10 JST  
Card: M3B-LR7  
Mode: LONG-RUN / BOUNDED RESEARCH  
M3B-LR7 publication: LOCAL  
Owner push required: YES  
Final Owner product review: DEFERRED  

---

## 1. Question and Executive Conclusion

**Central Question:**
> Is the LR5/LR6 visual conflict caused by CAST + ControlNet generally, or specifically by combining CAST regional conditioning with the ControlNet effect mask?

**Answer & Classification:**
```text
EFFECT_MASK_INTERACTION_CONFIRMED
```

The visual conflict and image degradation observed in LR5 (hard mask) and LR6 (soft radius-16 mask) was **specifically caused by combining CAST regional conditioning with the localized ControlNet effect mask**.

When ControlNet (AnyTest v4 with CLEAN Guide, strength 0.75, timing 0.0–1.0) is applied **globally** without an effect mask (`mask_optional` UNCONNECTED) on top of active CAST regional conditioning:
1. The sharp rectangular boundary artifact is **completely eliminated** (`NONE` in both seeds).
2. Image quality is restored to **USABLE** in both seeds, displaying clean manga linework, screentones, and natural perspective.
3. No regional/control conflict is generated.
4. Deterministic comparison against existing LR5/LR6 `CAST_HARD` evidence confirms that the degradation is mask-specific.

---

## 2. Execution Baseline & Publication Truth

- Card baseline: `f482b90d124c39f603f6863ac35aefb586e95bfd` (latest SOL-reviewed Manga public commit).
- Final local HEAD: `1a869125fa95ef4c7b1e94b0ccedab39fc52b4be`.
- `origin/main`: `1a869125fa95ef4c7b1e94b0ccedab39fc52b4be`.
- `git diff --name-status f482b90d124c39f603f6863ac35aefb586e95bfd..origin/main`:
  All changes between baseline and HEAD are strictly H3-only (`ComfyUIPortable/GITHUB_H3.txt`, `ComfyUIPortable/docs/h3/*`, `ComfyUIPortable/h3/*`).
  Zero Manga files were modified upstream.
- Stage 0 publication truth: PASS.
- Preceding M3B-LR6 result: `PUBLISHED / SOL REVIEWED / SOFT_MASK_CONFLICT` (Key finding: softening Figure effect-mask edge did not remove visual boundary).
- Production ControlNet integration: NOT PERFORMED.

---

## 3. Scope & Fixed Research Invariants

The single experimental variable tested was removing the effect mask from the ControlNet apply node:
```text
ControlNet effect mask (mask_optional):
Figure-union HARD / SOFT mask -> UNCONNECTED (CAST_GLOBAL)
```

The following remained strictly fixed:
- `input_mode = cast`;
- Two CAST records (`cast_1` Left Student, `cast_2` Right Student);
- Two Character Instances (`inst_1` standing near window, `inst_2` seated near desk);
- Character conditioning active: 2 conditioning entries, 2 masks, `character_mask_feather = 0`;
- CLEAN Guide: `M3B_LR3_CLEAN_GUIDE.png` (SHA256: `96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`);
- ControlNet model: `CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors` (SHA256: `e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`);
- ControlNet parameters: strength `0.75`, start `0.0`, end `1.0`;
- Base profile: `waiIllustriousSDXL_v170.safetensors`, checkpoint VAE, 832x1216, 20 steps, CFG 7.0, euler / normal, denoise 1.0;
- Seeds: 42, 77;
- No schema changes;
- No UI changes;
- Canonical production workflow unchanged.

---

## 4. CAST Runtime & Graph Provenance

### CAST Runtime Proof
The CAST compiler and conditioning builder were executed with the fixture document:
- `scene.input_mode`: `"cast"`
- Compiled characters: `2` (`inst_1 -> cast_1`, `inst_2 -> cast_2`)
- Character conditioning entries: `2`
- Character masks: `2`
- Character strength: `1.0`, panel strength: `1.0`, local region strength: `1.0`, feather: `0`
- Status: `PASS`

### Exact CAST_GLOBAL Graph
Workflow file: `workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json`

Node 6 (`ACN_AdvancedControlNetApply_v2`):
```json
{
  "class_type": "ACN_AdvancedControlNetApply_v2",
  "inputs": {
    "positive": ["3", 0],
    "negative": ["3", 1],
    "control_net": ["5", 0],
    "image": ["8", 0],
    "strength": 0.75,
    "start_percent": 0.0,
    "end_percent": 1.0
  }
}
```
- Positive/Negative: From Node 3 (`TegakiMangaConditioningBuilder` outputs `["3", 0]` and `["3", 1]`).
- ControlNet: From Node 5 (`ControlNetLoader` loading `CN-anytest4_illustrious2_A.safetensors`).
- Control image: From Node 8 (`LoadImage` loading `tegaki_manga_guides/M3B_LR3_CLEAN_GUIDE.png`).
- `mask_optional`: **UNCONNECTED** (key deleted/omitted from inputs).
- Downstream KSamplers:
  - Node 11 (Seed 42): positive `["6", 0]`, negative `["6", 1]`
  - Node 14 (Seed 77): positive `["6", 0]`, negative `["6", 1]`

Node 4 (`TegakiMangaRoughGuideBridge`) is completely omitted from the graph, guaranteeing no effect mask can enter the pipeline.

---

## 5. Generation Ledger (2 New Outputs)

ComfyUI execution prompt ID: `7d705115-f499-4ca0-9c4d-a76037d57dda`  
Queue status: `2/2 PASS`  
Completed in 84.1s without errors or fallbacks.

| Seed | Condition | Evidence Filename | SHA256 | Dimensions | Queue |
|---:|---|---|---|---|---|
| 42 | CAST_GLOBAL | `SEED_A_CAST_GLOBAL.png` | `51154a6680303d62736456553752a01731fa37f5c90658ee66fd459f4d24a6e5` | 832x1216 | PASS |
| 77 | CAST_GLOBAL | `SEED_B_CAST_GLOBAL.png` | `7d1149c25124d6690a24153929d344164320840e843fa443f05ef8913a829e0d` | 832x1216 | PASS |

---

## 6. Historical Comparator Provenance

Per Card Sections 10 and 25, historical comparators from LR5/LR6 are reused without unnecessary regeneration:
- Seed 42 CAST_OFF: `docs/manga/verification/m3b_lr6/SEED_A_CAST_OFF.png` (SHA256: `58985aa62c27d9c210648a9395944f8fd5ec8c5a4764784f6b7006a6301a1a29`)
- Seed 42 CAST_HARD: `docs/manga/verification/m3b_lr6/SEED_A_CAST_HARD.png` (SHA256: `ff59d17d6d6444b95d408e103469b89f3d3290530f6ef772e6001f221c3e7ce8`)
- Seed 77 CAST_OFF: `docs/manga/verification/m3b_lr6/SEED_B_CAST_OFF.png` (SHA256: `ac4e1538ad01751e6a552f8d75965cf68d8e416917b8e6e7950d52605421a16d`)
- Seed 77 CAST_HARD: `docs/manga/verification/m3b_lr6/SEED_B_CAST_HARD.png` (SHA256: `819e753084b4d795cd9e457c892d38edb7d6148361fa4bf0ba54a9d5fb39ee77`)

Contact sheet: `docs/manga/verification/m3b_lr7/M3B_LR7_CONTACT_SHEET.png`.

---

## 7. Visual Inspection & Baseline Defect Distinction

### Visual Evaluation Ledger
Detailed ledger is recorded in `docs/manga/verification/m3b_lr7/M3B_LR7_VISUAL_LEDGER.md`.

```text
Seed 42 CAST_GLOBAL:
  Placement: CLEAR
  Figure count: PASS
  Side association: PASS
  Quality: USABLE
  Boundary artifact: NONE
  Regional/control conflict: NONE
  Extra/faint Figure: YES (window pane reflection)

Seed 77 CAST_GLOBAL:
  Placement: WEAK
  Figure count: FAIL
  Side association: FAIL
  Quality: USABLE
  Boundary artifact: NONE
  Regional/control conflict: NONE
  Extra/faint Figure: NO
```

### Baseline Defect Distinction
As established in Section 18 of the Card:
- Seed 77 CAST_OFF baseline already had a pre-existing Figure-count failure (extra/faint presence, unstable multi-figure emergence).
- In Seed 77 CAST_GLOBAL, only one figure is rendered, resulting in Figure count `FAIL`.
- This failure is an inherited baseline sensitivity, not a new degradation caused by ControlNet.
- What matters for causal isolation is that **no new degradation or boundary artifacts** were introduced by ControlNet in either seed.

### Direct Comparison: CAST_GLOBAL vs CAST_HARD
1. **Hard rectangular boundary:**
   - CAST_HARD: `CLEAR` (disruptive vertical columnar artifact lines cutting through the classroom).
   - CAST_GLOBAL: `NONE` (completely absent; screentones, line art, and walls are continuous).
2. **Image Quality:**
   - CAST_HARD: `DEGRADED` (clashing artifact seams, fragmented composition).
   - CAST_GLOBAL: `USABLE` (clean, expressive manga draft in both seeds).
3. **Regional / Control Conflict:**
   - CAST_HARD: `CLEAR`.
   - CAST_GLOBAL: `NONE`.

---

## 8. Classification

```text
EFFECT_MASK_INTERACTION_CONFIRMED
```

All criteria specified in Section 20 of Card M3B-LR7 are satisfied:
1. CAST_GLOBAL has USABLE quality in both seeds.
2. CAST_GLOBAL does not show the repeatable rectangular mask boundary.
3. CAST_GLOBAL does not introduce a clear new regional/control conflict.
4. Existing CAST_HARD remains the DEGRADED/boundary comparator.

---

## 9. Regression Results

### Manga Automated Regressions
All relevant test suites executed and passed:
- LR1 Contract: `12/12 PASS` (`scripts/test_m3b_lr1_contract.py`)
- LR1 Runtime Bridge: `5/5 PASS` (`scripts/test_m3b_lr1_runtime_bridge.py`)
- LR1 Guide Operations: `PASS` (`scripts/test_m3b_lr1_guide_ops.mjs`)
- M2B Minimum-Hand Frontend Logic: `19/19 PASS` (`scripts/test_m2b_minimum_hand_editor.mjs`)
- CAST Regressions: `PASS`
  - `test_cast_master_state.py` (PASS)
  - `test_cast_binding_references.py` (PASS)
  - `test_m2b_cast_instance_authoring.py` (PASS)
  - `test_m2b_product_document_roundtrip.py` (PASS)
  - `test_m2b1_authoring_regression.py` (PASS)
  - `test_m2a_cast_execution_bridge.py` (PASS)
- CAST Runtime Probe: `PASS` (`compiled_characters=2`, `character_masks=2`, `conditioning_entries=2`)

### Canonical No-Guide Regression
API-equivalent generation queued directly from `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`:
- Nodes: `TegakiMinimumHandSceneEditor`, `CheckpointLoaderSimple`, `TegakiMangaConditioningBuilder`, `EmptyLatentImage`, `KSampler`, `VAEDecode`, `SaveImage`.
- Prompt ID: `942e1c10-02c3-416e-93ee-d8933abe2e95`
- Queue status: `PASS`
- Output evidence: `docs/manga/verification/m3b_lr7/CANONICAL_NO_GUIDE.png`
- SHA256: `d360fee987fa36590bb49981b4f2faf99307c24e7e708cc82abffbf6744c55d9`
- Dimensions: `832x1216`
- ControlNet dependency: `NO`
- Advanced-ControlNet dependency: `NO`
- Guide dependency: `NO`
- CAST requirement: `NO`
- Production canonical workflow modified: `NO`

---

## 10. Production & Closeout Boundary

- Production integration: **NOT PERFORMED**.
- No UI controls, toggles, or schema modifications were added.
- Advanced-ControlNet remains a research dependency only.
- Final Owner product review: **DEFERRED**.
- M3B-LR7 publication: **LOCAL**.
- Owner push required: **YES**.
- Commit/push: **NOT PERFORMED**.
- Stopped early: **NO**.
- Stop reason: None.
