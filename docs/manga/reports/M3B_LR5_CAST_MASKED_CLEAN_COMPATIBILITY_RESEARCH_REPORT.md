# M3B-LR5 CAST + Figure-Masked CLEAN Compatibility Research Report

Date: 2026-09-10 JST  
Card: M3B-LR5  
Mode: LONG-RUN / BOUNDED RESEARCH  
Publication: LOCAL  
Owner push required: YES  
Final Owner product review: DEFERRED

## Execution baseline

- Final HEAD: 5d4dde818e9e5155a7fd267c70f5d5980252b98f
- origin/main: 5d4dde818e9e5155a7fd267c70f5d5980252b98f
- Latest SOL-reviewed Manga public commit required by the Card:
  54b235f1b18c5c4df5aa01f74cd6a87e201dc5bb
- Diff after that Manga baseline was H3-only; no Manga own-file conflict was
  present.
- Stage 0 publication truth: PASS
- LR4 SOL result: LOCALITY_SUPPORTED
- Derived CLEAN Guide: retained research candidate.
- Figure-union masked ControlNet: supported research candidate.
- Production ControlNet integration: NOT PERFORMED.

The historical LR4 report's execution-time Publication: LOCAL wording was not
rewritten.

## Scope and schema boundary

The research copy changed exactly one authoring-document semantic field:

pages[0].scenes[0].input_mode: simple -> cast

M3B_LR4_FIGURE_MASK_AB.json was preserved. The production workflow
workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json was unchanged. No persistent
schema, CAST schema, Character Instance schema, Guide schema, production
source, UI, model storage, or Advanced-ControlNet source was changed.

## CAST compile provenance

The existing TegakiMinimumHandSceneEditor and
compile_document_to_page_plan() were executed with the LR4 fixture and
input_mode: cast.

Result: PASS

- Compiled Character count: 2
- inst_1 -> cast_1
- inst_2 -> cast_2
- Each compiled Character contained instance_id, character_id,
  combined_prompt, area, and coordinate_space: page.
- cast_1 remained Left Student with young student, short dark hair, school
  uniform.
- cast_2 remained Right Student with young student, long light hair, school
  uniform.
- No CAST prompt or fixture identity field was replaced.

The derived runtime prompts were:

- inst_1: young student, short dark hair, school uniform, standing near the
  left window, on the left side
- inst_2: young student, long light hair, school uniform, seated near the
  right desk, on the right side

Evidence: verification/m3b_lr5/M3B_LR5_CONDITIONING_PROVENANCE.json.

## Character-conditioning runtime proof

The existing TegakiMangaConditioningBuilder consumed the compiled plan.

Result: PASS

- Builder status: success
- Character entries: 2
- Character masks: 2
- character_strength: 1.0
- Character debug entries retained cast_1 and cast_2 prompts and their
  instance areas.

This was proven from compiler/builder runtime/debug output and not inferred
from the authoring document alone. The live generation graph uses the same
builder node for all four CAST conditions.

## Two spatial systems

The two systems were recorded without alignment or tuning.

Character Instance regions, used for regional text-conditioning:

| Instance | x | y | w | h |
|---|---:|---:|---:|---:|
| inst_1 | 0.08 | 0.18 | 0.32 | 0.62 |
| inst_2 | 0.60 | 0.26 | 0.26 | 0.50 |

Guide-derived Figure page regions, used for rough placement provenance and
ControlNet locality:

| Figure | x | y | w | h |
|---|---:|---:|---:|---:|
| figure_1 | 0.05 | 0.304984 | 0.38 | 0.369504 |
| figure_2 | 0.57 | 0.356304 | 0.28 | 0.297656 |

These areas are intentionally not identical.

## Local Advanced-ControlNet contract

Result: PASS

Live /object_info/ACN_AdvancedControlNetApply_v2 exposed:

- required positive, negative, control_net, image, strength, start_percent,
  end_percent;
- optional mask_optional of type MASK, display name effect_mask.

The installed local README and source describe mask_optional as an
attention/effect mask that decides where the ControlNet applies and scales
relative strength for non-binary values. The existing Figure union mask is
binary, with active white Figure rectangles and inactive black background.

Fixed assets were reused byte-identically:

- CLEAN Guide SHA256:
  96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a
- Figure-union mask SHA256:
  6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb
- ControlNet model SHA256:
  e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8

The model was reused from the verified reForge shared store. No download,
copy, junction, symlink, or storage change occurred.

## Exact OFF versus MASKED graph difference

The research workflow is
workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json.

- CAST_OFF: KSampler positive/negative connect directly to the existing
  Character-conditioning builder output.
- CAST_MASKED: the same builder output passes through one existing
  ACN_AdvancedControlNetApply_v2 node using the same CLEAN Guide, the same
  model, strength 0.75, start 0.0, end 1.0, and the existing Figure-union
  mask on mask_optional.
- Both conditions use the same CAST document, compiled Characters, Character
  areas, prompts, negative prompts, checkpoint, VAE, latent, resolution,
  steps, CFG, sampler, scheduler, denoise, character_strength,
  panel_strength, local_region_strength, and mask_feather.
- No GLOBAL condition, no RAW Guide, no per-Figure ControlNet, and no timing
  or strength sweep was run.

## Four-output technical ledger

Prompt id: 367d4e5e-ab85-4b3b-987e-f55f9d326bae  
Queue result: 4/4 PASS

| Seed | Condition | Evidence | SHA256 | Dimensions | Queue |
|---:|---|---|---|---|---|
| 42 | CAST_OFF | SEED_A_CAST_OFF.png | 19cb9d83f9ee5a8e4797d54dfaa1bc311d5083177735372697f3b157c5ca5548 | 832x1216 | PASS |
| 42 | CAST_MASKED | SEED_A_CAST_MASKED.png | 5bd6eb4f17a7c019d8e40f1a4a1bf0cdacc95e55bfa7023d4270df505c4447ae | 832x1216 | PASS |
| 77 | CAST_OFF | SEED_B_CAST_OFF.png | 08b4c6c16516880f61b98c212a26662c156fec2e4b6f4cd7991963624077cfde | 832x1216 | PASS |
| 77 | CAST_MASKED | SEED_B_CAST_MASKED.png | c98737b71b1db7bd6250a86a01b1341d8d13fcc13e5bf756bb15c0ab186e102e | 832x1216 | PASS |

Fixed generation profile:

waiIllustriousSDXL_v170.safetensors, checkpoint VAE, 832x1216, 20 steps,
CFG 7.0, euler/normal, denoise 1.0, Character strength 1.0, panel strength
1.0, local-region strength 1.0, mask feather 0.

## Visual review

Review sources:

- verification/m3b_lr5/M3B_LR5_CONTACT_SHEET.png
- four individual evidence PNGs
- live ComfyUI browser view at http://127.0.0.1:8188/view

This is coarse Figure/side review only. It makes no biometric identity claim.

| Seed | Condition | Placement | Figure count | Side association | Acting | Quality | Conflict |
|---:|---|---|---|---|---|---|---|
| 42 | CAST_OFF | CLEAR | PASS | MIXED | WEAK | USABLE | NONE |
| 42 | CAST_MASKED | CLEAR | PASS | PASS | WEAK | DEGRADED | CLEAR |
| 77 | CAST_OFF | CLEAR | FAIL | MIXED | WEAK | USABLE | NONE |
| 77 | CAST_MASKED | CLEAR | FAIL | MIXED | WEAK | DEGRADED | CLEAR |

Aggregate enums:

- CAST_OFF placement: CLEAR
- CAST_OFF Figure count: FAIL
- CAST_MASKED placement: CLEAR
- CAST_MASKED Figure count: FAIL
- CAST_MASKED quality: DEGRADED
- Side association: MIXED
- Regional/control conflict: CLEAR
- Seed variation: PRESENT
- Hard mask artifact: PRESENT

The masked output retains coarse left/right Figure presence in both seeds and
improves the seed-77 Figure presence relative to CAST_OFF. However, the
standing-left / seated-right acting relationship is not preserved, seed 77
contains an extra/faint Figure-like presence, and both masked images show a
repeatable hard vertical boundary signature aligned with the rectangular
effect-mask locality. This is a visible combination failure, not a parameter
optimization target for LR5.

## Compatibility classification

CAST_MASKED_CONFLICT

The result fails the Card's compatible criteria because the masked condition
has degraded quality with a hard mask artifact, does not preserve the intended
acting relationship, and fails the aggregate two-Figure count due to the
seed-77 extra/faint presence. No tuning was performed to rescue the result.

## Regression

All required and relevant existing tests passed:

- LR1 contract: 12/12 PASS
- LR1 runtime bridge: 5/5 PASS
- Guide operations: PASS
- M2B Minimum-Hand frontend: 19/19 PASS
- CAST master persistence: PASS
- Character Instance foreign keys: PASS
- Same CAST multiple appearances: PASS
- Instance area persistence: PASS
- Simple/CAST state preservation: PASS
- M2B CAST authoring: PASS
- M2B.1 authoring regression: PASS
- M2A CAST execution bridge: PASS

## Canonical no-Guide regression

The canonical source was workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json. An
API-equivalent prompt was queued from its authoring and generation nodes while
omitting the Guide bridge, Frame overlay, ControlNetLoader, and
Advanced-ControlNet apply node. The authoring document remained the canonical
simple/no-CAST document.

- Prompt id: c0ca42ac-85da-44ae-bc44-312305f3196f
- Queue: PASS
- Evidence: verification/m3b_lr5/CANONICAL_NO_GUIDE.png
- Dimensions: 832x1216
- ControlNet dependency: NO
- Advanced-ControlNet dependency: NO
- Guide dependency: NO
- CAST requirement: NO
- Production canonical workflow modified: NO

## Production and Owner boundary

- Production integration: NOT PERFORMED
- Product UI controls: not added.
- Canonical production path: unchanged.
- Final Owner product review: DEFERRED
- M3B-LR5 publication: LOCAL
- Owner push required: YES

This Card answers only whether the existing Figure-masked CLEAN ControlNet
can coexist with active CAST/Character regional conditioning. The observed
answer is CAST_MASKED_CONFLICT; no next Card is self-issued.
