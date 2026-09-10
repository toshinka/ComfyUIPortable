# M3B-LR6 CAST Soft-Edge Figure Mask Compatibility Research Report

Date: 2026-09-10 JST  
Card: M3B-LR6  
Mode: LONG-RUN / BOUNDED RESEARCH  
M3B-LR6 publication: LOCAL  
Owner push required: YES  
Final Owner product review: DEFERRED

## Execution baseline

- Card baseline: `224c37b9446c412e0dca9ac04a72e74916059b1d`.
- Final HEAD: `d067a4170edeffee200a6f1a8d279a1c1b68be28`.
- `origin/main`: `d067a4170edeffee200a6f1a8d279a1c1b68be28`.
- `git fetch origin`: PASS after the repository metadata permission retry.
- Drift after the Card baseline: H3-only; no Manga own-file conflict.
- Stage 0 publication truth: PASS.
- LR5 SOL result: `CAST_MASKED_CONFLICT`.
- LR5 key failure: `HARD EFFECT-MASK BOUNDARY / QUALITY DEGRADED`.
- LR4 Figure-union locality: `SUPPORTED RESEARCH CANDIDATE`.
- Production ControlNet integration: `NOT PERFORMED`.

LR5's historical execution wording was not rewritten. The current authority
records LR5 as published/SOL-reviewed and LR6 as the active bounded follow-up
while this report is local.

## Scope and invariant boundary

LR6 changed one variable only:

```text
Figure-union ControlNet effect mask:
HARD binary -> SOFT Gaussian edge, radius 16px
```

The following remained fixed:

- `input_mode = cast`;
- two CAST records and two Character Instances;
- CLEAN Guide bytes and geometry;
- HARD Figure-union mask geometry;
- Character-conditioning masks (`mask_feather = 0`);
- checkpoint, VAE, resolution, steps, CFG, sampler, scheduler, denoise;
- ControlNet model, strength `0.75`, start `0.0`, end `1.0`;
- no schema, UI, production workflow, model storage, or extension-source
  changes.

## HARD mask provenance

The source was the exact LR4/LR5 evidence mask:

```text
docs/manga/verification/m3b_lr4/M3B_LR4_FIGURE_UNION_MASK.png
SHA256 6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb
dimensions 832x1216
```

The LR6 HARD evidence copy is byte-identical. The existing
`TegakiMangaRoughGuideBridge.figure_union_mask` runtime reproduction produced
the same SHA, so the bridge HARD mask remains the exact LR4/LR5 mask.

The CLEAN Guide was reused byte-identically:

```text
SHA256 96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a
dimensions 832x1216
```

## SOFT mask derivation

The research helper `scripts/m3b_lr6_build_soft_mask_and_workflow.py` loaded
the verified binary HARD PNG and called the existing
`custom_nodes_custom/tegaki_manga_nodes/mask_builder.py::_apply_feather(...)`
implementation. The function itself was not modified.

```text
Gaussian radius: 16px
SOFT SHA256: 801350fdbf41b6cee88143d3cc0f0dc95f5050090b25357e0f249ad4c10cb300
dimensions: 832x1216
min: 0.0
max: 1.0
count(value == 0): 665066
count(value == 1): 128158
count(0 < value < 1): 218488
```

The SOFT mask is not byte-identical to HARD, has intermediate values, uses no
manual painting, and retains Figure centers. Measured center deltas were
`0.256099px` for `figure_1` and `0.363786px` for `figure_2`.

The radius, SOFT image, and mask mode were not persisted into
`page.guides[]`; they exist only as research evidence/runtime input. The
Character masks remained hard and unchanged.

## CAST conditioning proof

The existing CAST compiler and `TegakiMangaConditioningBuilder` were rerun
with the fixture. Result: `PASS`.

- compiled Characters: `2`;
- `inst_1 -> cast_1`, `inst_2 -> cast_2`;
- Character conditioning entries: `2`;
- Character masks: `2`;
- `character_strength = 1.0`;
- `panel_strength = 1.0`;
- `local_region_strength = 1.0`;
- `mask_feather = 0`.

The Character conditioning regions were not copied into the Figure mask and
the two spatial systems were not aligned or intersected.

## Exact OFF/HARD/SOFT graph difference

The research workflow is
`workflows/manga/research/M3B_LR6_CAST_SOFT_MASK_COMPATIBILITY.json`.

- `CAST_OFF`: KSampler positive/negative connect directly to builder node `3`.
- `CAST_HARD`: KSampler positive/negative connect to
  `ACN_AdvancedControlNetApply_v2` node `6`; `mask_optional = ["4", 1]`, the
  existing bridge Figure-union mask.
- `CAST_SOFT`: KSampler positive/negative connect to
  `ACN_AdvancedControlNetApply_v2` node `9`; `mask_optional = ["40", 0]`, a
  `LoadImageMask` node loading the derived `M3B_LR6_SOFT_MASK.png`.

The live `/object_info` contract exposed `mask_optional` as `MASK` with
display name `effect_mask`. The queued prompt therefore proves the SOFT mask
entering the actual `mask_optional` input by node provenance, not by filename
alone.

## Six-output generation ledger

Prompt ID: `891bed33-0ae4-4046-af9f-2763cc610390`  
Queue result: `6/6 PASS`  
ComfyUI history: `status_str=success`, `completed=true`  
Live browser review: `PASS`

| Seed | Condition | Evidence | SHA256 | Dimensions | Queue |
|---:|---|---|---|---|---|
| 42 | CAST_OFF | `SEED_A_CAST_OFF.png` | `58985aa62c27d9c210648a9395944f8fd5ec8c5a4764784f6b7006a6301a1a29` | 832x1216 | PASS |
| 42 | CAST_HARD | `SEED_A_CAST_HARD.png` | `ff59d17d6d6444b95d408e103469b89f3d3290530f6ef772e6001f221c3e7ce8` | 832x1216 | PASS |
| 42 | CAST_SOFT | `SEED_A_CAST_SOFT.png` | `6de038b2095120ec5649232e1144951e4574d22df40faf2429d7d541b9d61627` | 832x1216 | PASS |
| 77 | CAST_OFF | `SEED_B_CAST_OFF.png` | `ac4e1538ad01751e6a552f8d75965cf68d8e416917b8e6e7950d52605421a16d` | 832x1216 | PASS |
| 77 | CAST_HARD | `SEED_B_CAST_HARD.png` | `819e753084b4d795cd9e457c892d38edb7d6148361fa4bf0ba54a9d5fb39ee77` | 832x1216 | PASS |
| 77 | CAST_SOFT | `SEED_B_CAST_SOFT.png` | `605a1e1668de3e8b10f6b689d205bd1b858784c7137af5d7bd32c356f4c3dded` | 832x1216 | PASS |

## Baseline defect distinction

Seed 77 CAST_OFF already contains an extra Figure-like presence, so its
Figure-count `FAIL` is a pre-existing CAST baseline defect. CAST_SOFT does not
repair that defect, but the overall compatibility result is not based on
charging that baseline failure to SOFT. The SOFT-specific failure is the
repeatable clear mask-aligned vertical/rectangular boundary and the resulting
degraded image quality in both seeds.

## Visual comparison

The full ledger is in
`docs/manga/verification/m3b_lr6/M3B_LR6_VISUAL_LEDGER.md`.

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

The SOFT transition is numerically feathered and modestly changes local edge
tonality, but it does not remove the visually disruptive boundary. Seed 42
retains two coarse left/right Figures under SOFT; seed 77 remains
seed-sensitive with an extra/faint Figure-like presence. No perfect identity
or acting result was required, and no tuning was attempted.

## Compatibility result

```text
SOFT_MASK_CONFLICT
```

`SOFT_MASK_COMPATIBLE` criteria are not met because the boundary artifact is
`CLEAR` in both seeds and SOFT quality remains `DEGRADED`. The pre-existing
seed-77 CAST Figure-count instability remains separately recorded.

## Regression

All required regression gates passed:

- LR1 contract: `12/12 PASS`;
- LR1 runtime bridge: `5/5 PASS`;
- Guide operations: `PASS`;
- M2B Minimum-Hand frontend: `19/19 PASS`;
- relevant CAST regressions: `PASS` (CAST master, binding references,
  authoring, recurrent instances, document roundtrip, M2B.1, M2A execution
  bridge).

## Canonical no-Guide regression

The canonical no-Guide path was queued API-equivalently from
`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` using only:

```text
TegakiMinimumHandSceneEditor
CheckpointLoaderSimple
TegakiMangaConditioningBuilder
EmptyLatentImage
KSampler
VAEDecode
SaveImage
```

Prompt ID: `fac9d447-be61-4c5b-8ae8-7175ff67eaa1`  
Queue: `PASS`  
Evidence: `verification/m3b_lr6/CANONICAL_NO_GUIDE.png`  
Dimensions: `832x1216`  
SHA256: `5f2113c971089583f26c59c7da6f2e4296a004d2ebeb26cd0c90411cb7a69212`

```text
ControlNet dependency: NO
Advanced-ControlNet dependency: NO
Guide dependency: NO
CAST requirement: NO
Production canonical workflow modified: NO
```

## Model and storage boundary

The existing AnyTest v4 model was reused without download, copy, junction, or
symlink changes:

```text
E:\EasyReforge\stable-diffusion-webui-reForge\models\ControlNet
  Junction -> E:\EasyReforge\Model\ControlNet

E:\EasyReforge\Model\ControlNet\CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors
bytes: 2502139104
SHA256: e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8
```

The production workflow, Advanced-ControlNet source, and `_apply_feather`
source were unchanged. Staging the research SOFT PNG in ComfyUI `input/` was
runtime evidence only and is outside Git.

## Closeout boundary

- Production integration: `NOT PERFORMED`.
- UI/product controls: not added.
- Final Owner product review: `DEFERRED`.
- M3B-LR6 publication: `LOCAL`.
- Owner push required: `YES`.
- Stopped early: `NO`.
- Stop reason: none.

