# M3B-LR6 — CAST Soft-Edge Figure Mask Compatibility Research

Date: 2026-09-10 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Mode: LONG-RUN / BOUNDED RESEARCH
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR6_CAST_SOFT_EDGE_FIGURE_MASK_COMPATIBILITY_RESEARCH.md`

## 0. Purpose

M3B-LR5 final SOL result:

```text
CAST_MASKED_CONFLICT
```

Observed ControlNet-specific failure:

```text
repeatable hard rectangular effect-mask boundary
+
MASKED image quality DEGRADED
```

Do NOT interpret LR5 as:

```text
CAST cannot work with ControlNet
```

CAST_OFF itself already has a Seed-77 Figure-count failure.

LR6 answers one question only:

```text
Does softening only the Figure-union ControlNet effect-mask boundary remove
the CAST_MASKED quality conflict while preserving useful Figure locality?
```

---

## 1. Repository authority

Latest SOL-reviewed Manga public commit:

`224c37b9446c412e0dca9ac04a72e74916059b1d`

M3B-LR5:

```text
PUBLISHED / SOL REVIEWED / CAST_MASKED_CONFLICT
```

Production integration remains:

```text
NOT PERFORMED
```

---

## 2. Start

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

If main advanced:

```bash
git diff --name-status \
  224c37b9446c412e0dca9ac04a72e74916059b1d..origin/main
```

H3-only drift is allowed.

Manga own-file conflict requires review.

---

## 3. Stage 0 — publication truth

Update CURRENT AUTHORITY:

```text
Latest SOL-verified Manga public commit:
224c37b9446c412e0dca9ac04a72e74916059b1d

M3B-LR5:
PUBLISHED / SOL REVIEWED

M3B-LR5 final result:
CAST_MASKED_CONFLICT

M3B-LR5 key failure:
HARD EFFECT-MASK BOUNDARY / QUALITY DEGRADED

M3B-LR4 locality:
SUPPORTED RESEARCH CANDIDATE

Production ControlNet integration:
NOT PERFORMED

M3B-LR6:
ACTIVE
```

Do not rewrite LR5 historical:

```text
Publication: LOCAL
```

No publication-only Card.

---

## 4. Fixed architecture

Retain all of LR5:

```text
input_mode = cast

2 CAST
2 Character Instances
2 active Character regional conditioning branches

CLEAN Figure-derived Guide

Figure-union ControlNet locality

AnyTest v4

strength = 0.75
start = 0.0
end = 1.0
```

Only the effect-mask edge changes.

---

## 5. Fixed CLEAN Guide

Reuse byte-identically:

`M3B_LR3_CLEAN_GUIDE.png`

SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

No renderer change.

No silhouette change.

---

## 6. HARD Figure mask

Reuse the exact LR4/LR5 Figure-union mask.

SHA256:

`6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb`

Semantics:

```text
1.0 = ControlNet active
0.0 = inactive
```

No geometry change.

---

## 7. SOFT Figure mask

Derive from the HARD Figure-union mask only.

Use:

```text
Gaussian feather radius = 16 px
```

Preferred implementation:

reuse existing Manga mask feather logic:

`custom_nodes_custom/tegaki_manga_nodes/mask_builder.py`

`_apply_feather(...)`

Research-only use is allowed.

Do not modify the function.

---

## 8. Why radius 16

This Card does NOT run a feather sweep.

`16 px` is a single conservative research value intended to remove an abrupt
binary boundary without materially redefining the Figure locality.

Do not test:

```text
8
24
32
64
```

or any alternative radius.

---

## 9. SOFT mask contract

The resulting mask must:

```text
retain dimensions 832x1216

retain the same Figure centers

contain values between 0 and 1

contain pixels strictly between 0 and 1

not be byte-identical to HARD

not introduce manual painting

not alter Figure regions
```

Record:

```text
SHA256
dimensions
min
max
count(value == 0)
count(value == 1)
count(0 < value < 1)
```

---

## 10. Important mask boundary

Softening the mask is runtime/research derivation.

Do NOT persist:

```text
feather radius
soft mask
generation mask mode
```

into `page.guides[]`.

Schema remains unchanged.

---

## 11. CAST fixture

Reuse exactly LR5 CAST fixture.

```text
cast_1:
short dark hair
left
standing near left window

cast_2:
long light hair
right
seated near right desk

inst_1 -> cast_1
inst_2 -> cast_2

figure_1 -> inst_1
figure_2 -> inst_2
```

No prompt changes.

No area changes.

---

## 12. Character conditioning

Keep:

```text
character_strength = 1.0
panel_strength = 1.0
local_region_strength = 1.0
mask_feather = 0
```

IMPORTANT:

```text
Character-conditioning masks remain HARD / unchanged.
```

Do NOT feather Character masks in LR6.

Only the ControlNet effect mask changes.

---

## 13. Spatial semantics

Continue to preserve:

```text
Character Instance area
=
text-conditioning region
```

and:

```text
Figure region
=
Guide / ControlNet locality provenance
```

Do not align them.

Do not copy one area into the other.

---

## 14. Experimental matrix

Seeds:

```text
42
77
```

Conditions:

```text
CAST_OFF
CAST_HARD
CAST_SOFT
```

Exactly:

```text
2 seeds × 3 conditions = 6 outputs
```

---

## 15. CAST_OFF

CAST Character conditioning:

```text
ACTIVE
```

ControlNet:

```text
BYPASSED
```

---

## 16. CAST_HARD

Exact LR5 masked semantics:

```text
CLEAN Guide

AnyTest v4

strength = 0.75

start = 0.0

end = 1.0

effect mask =
original HARD Figure-union mask
```

---

## 17. CAST_SOFT

Identical to CAST_HARD except:

```text
effect mask =
radius-16 SOFT Figure-union mask
```

No other graph difference.

---

## 18. Fixed generation profile

```text
Checkpoint:
waiIllustriousSDXL_v170.safetensors

VAE:
checkpoint VAE

Resolution:
832x1216

Steps:
20

CFG:
7.0

Sampler:
euler

Scheduler:
normal

Denoise:
1.0

Control strength:
0.75

Control start:
0.0

Control end:
1.0
```

---

## 19. Model

Reuse only:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

No download.

No copy.

No storage changes.

---

## 20. Advanced-ControlNet

Reuse:

`ACN_AdvancedControlNetApply_v2`

and:

`mask_optional / effect_mask`

Do not update the extension.

Do not modify its source.

No production dependency is authorized.

---

## 21. Research workflow

Preserve LR5:

`workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json`

Create:

`workflows/manga/research/M3B_LR6_CAST_SOFT_MASK_COMPATIBILITY.json`

Production:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

must remain unchanged.

---

## 22. Research helper

Allowed:

`scripts/m3b_lr6_build_soft_mask_and_workflow.py`

Responsibilities only:

```text
load/derive existing HARD Figure mask

apply fixed radius-16 feather

verify mask numeric properties

save evidence representation

construct bounded LR6 research workflow
```

Do not add production nodes.

---

## 23. Runtime mask proof

Before generation prove that the mask actually entering:

```text
mask_optional
```

for CAST_SOFT is the SOFT mask.

Do not rely on filename alone.

Record workflow/node provenance.

---

## 24. Queue gate

Required:

```text
Seed 42 CAST_OFF: PASS
Seed 42 CAST_HARD: PASS
Seed 42 CAST_SOFT: PASS

Seed 77 CAST_OFF: PASS
Seed 77 CAST_HARD: PASS
Seed 77 CAST_SOFT: PASS
```

Expected:

```text
6/6 PASS
```

---

## 25. Primary visual question

The primary question is:

```text
Does CAST_SOFT remove the repeatable hard vertical/rectangular ControlNet
boundary visible in CAST_HARD?
```

Record per seed:

```text
HARD_BOUNDARY:
NONE / WEAK / CLEAR
```

---

## 26. Secondary visual questions

Also inspect:

```text
two-Figure presence
extra/faint Figure
left/right placement
side association
standing/seated broad acting
anatomy usability
background continuity
```

Do not demand perfect identity.

---

## 27. Do not charge baseline defects to SOFT

Seed 77 CAST_OFF already contains extra Figure presence.

Therefore distinguish:

```text
pre-existing CAST baseline failure
```

from:

```text
new ControlNet-induced regression
```

This distinction must appear in the report.

---

## 28. Visual enums

For HARD and SOFT:

```text
Placement:
CLEAR / WEAK / NONE / DEGRADED

Figure count:
PASS / FAIL

Side association:
PASS / MIXED / FAIL

Image quality:
USABLE / DEGRADED / FAILED

Control-mask boundary artifact:
NONE / WEAK / CLEAR
```

Overall:

```text
Seed variation:
PRESENT / REDUCED / LOST
```

---

## 29. Compatibility result

Use exactly one:

```text
SOFT_MASK_COMPATIBLE

SOFT_MASK_CONFLICT

SOFT_MASK_INCONCLUSIVE
```

---

## 30. SOFT_MASK_COMPATIBLE criteria

All required:

1. SOFT boundary artifact is `NONE` or at most non-disruptive `WEAK` in both seeds.
2. SOFT image quality is `USABLE` in both seeds.
3. SOFT placement is not materially worse than CAST_OFF.
4. SOFT Figure count is not worse than CAST_OFF for either seed.
5. SOFT side association is not worse than CAST_OFF.
6. No new duplication/splitting attributable to SOFT.
7. Seed variation remains PRESENT or usefully REDUCED.

SOFT does NOT need to repair a defect already present in CAST_OFF.

---

## 31. SOFT_MASK_CONFLICT

Use if:

```text
hard/soft boundary failure remains visually disruptive
quality remains DEGRADED
SOFT loses a Figure retained by OFF
SOFT introduces new duplicate/split Figures
SOFT worsens side association
new clear regional/control conflict appears
```

---

## 32. SOFT_MASK_INCONCLUSIVE

Use when one seed improves and the other introduces a different tradeoff without
a clear failure mechanism.

---

## 33. No other tuning

Do NOT change:

```text
strength
start/end
Character strength
Character mask feather
Figure geometry
Character geometry
CLEAN Guide
checkpoint
ControlNet model
```

No timing experiment.

No strength sweep.

---

## 34. No Character-mask alignment

Do not switch ControlNet locality to:

```text
Character union mask
```

Do not intersect:

```text
Character mask ∩ Figure mask
```

Do not union the two systems.

That is a later hypothesis only if soft Figure locality fails.

---

## 35. Evidence directory

Create:

`docs/manga/verification/m3b_lr6/`

Minimum:

```text
M3B_LR6_HARD_MASK.png
M3B_LR6_SOFT_MASK.png
M3B_LR6_MASK_PROVENANCE.json

SEED_A_CAST_OFF.png
SEED_A_CAST_HARD.png
SEED_A_CAST_SOFT.png

SEED_B_CAST_OFF.png
SEED_B_CAST_HARD.png
SEED_B_CAST_SOFT.png

M3B_LR6_CONTACT_SHEET.png
M3B_LR6_VISUAL_LEDGER.md
M3B_LR6_MANIFEST.json
```

---

## 36. Contact sheet

```text
             CAST_OFF     CAST_HARD     CAST_SOFT
Seed 42          x             x             x
Seed 77          x             x             x
```

Also include small HARD/SOFT mask references if practical.

---

## 37. Regression

Run:

```text
LR1 contract:
12/12

LR1 runtime bridge:
5/5

Guide ops:
PASS

M2B Minimum-Hand frontend:
19/19

relevant CAST regression:
PASS
```

---

## 38. Canonical regression

Queue canonical no-Guide Manga path.

Confirm:

```text
ControlNet dependency:
NO

Advanced-ControlNet dependency:
NO

Guide dependency:
NO

CAST requirement:
NO

Queue:
PASS
```

---

## 39. Production integration

Still forbidden.

Even if:

```text
SOFT_MASK_COMPATIBLE
```

do not modify canonical production generation or UI.

SOL reviews published evidence first.

---

## 40. Report

Create:

`docs/manga/reports/M3B_LR6_CAST_SOFT_EDGE_FIGURE_MASK_COMPATIBILITY_RESEARCH_REPORT.md`

Must include:

```text
Execution baseline

LR5 SOL result:
CAST_MASKED_CONFLICT

HARD mask provenance

SOFT mask derivation

radius:
16

mask numeric evidence

CAST conditioning proof

exact OFF/HARD/SOFT graph difference

six-output ledger

baseline defect distinction

boundary-artifact comparison

placement comparison

Figure-count comparison

side association

image quality

seed variation

compatibility result

regression

canonical no-Guide result

production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

## 41. Manifest minimum

```json
{
  "card": "M3B-LR6",
  "input_mode": "cast",
  "seeds": [42, 77],
  "conditions": ["CAST_OFF", "CAST_HARD", "CAST_SOFT"],
  "compiled_characters": 2,
  "character_conditioning_active": true,
  "character_mask_feather": 0,
  "control_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "hard_figure_mask": true,
  "soft_figure_mask": true,
  "soft_mask_gaussian_radius_px": 16,
  "schema_changed": false,
  "compatibility_result": "COMPATIBLE|CONFLICT|INCONCLUSIVE",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

## 42. Routing

At start:

```text
Active Card:
M3B-LR6
```

At successful closeout:

move Card byte-identically to:

`cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not issue another Card.

---

## 43. Publication

Local report may state:

```text
M3B-LR6 publication:
LOCAL

Owner push required:
YES
```

Historical wording remains unchanged after later push.

---

## 44. STOP conditions

STOP if:

```text
HARD mask cannot be reproduced byte-identically
SOFT mask cannot be traced deterministically from HARD
soft mask cannot be fed to mask_optional with established semantics
schema change becomes necessary
production source change becomes necessary
different model becomes necessary
same root cause fails twice
```

Do not broaden the experiment.

---

## 45. Required final response

```text
Card:
M3B-LR6

Execution baseline:
Final HEAD:
origin/main:

Stage 0 publication truth:
PASS / FAIL

Schema changed:
NO

CAST compile:
PASS / FAIL

Character conditioning:
PASS / FAIL

HARD mask:
PASS / FAIL

HARD SHA256:

SOFT mask:
PASS / FAIL

SOFT SHA256:

Soft radius:
16

Intermediate-value pixels:
<count>

Queues:
6/6 PASS / FAIL

Seed 42:
CAST_OFF:
CAST_HARD:
CAST_SOFT:

Seed 77:
CAST_OFF:
CAST_HARD:
CAST_SOFT:

HARD boundary artifact:
NONE / WEAK / CLEAR

SOFT boundary artifact:
NONE / WEAK / CLEAR

HARD quality:
USABLE / DEGRADED / FAILED

SOFT quality:
USABLE / DEGRADED / FAILED

SOFT placement:
CLEAR / WEAK / NONE / DEGRADED

SOFT Figure count:
PASS / FAIL

Side association:
PASS / MIXED / FAIL

Seed variation:
PRESENT / REDUCED / LOST

Compatibility provisional result:
SOFT_MASK_COMPATIBLE /
SOFT_MASK_CONFLICT /
SOFT_MASK_INCONCLUSIVE

LR1 regression:
PASS / FAIL

CAST regression:
PASS / FAIL

Canonical no-Guide regression:
PASS / FAIL

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED

Evidence:
Manifest:
Report:

Stopped early:
YES / NO

Stop reason:

M3B-LR6 publication:
LOCAL

Owner push required:
YES
```

---

## 46. Final instruction

This Card changes one variable only:

```text
Figure-union ControlNet effect mask edge:
HARD binary
->
Gaussian-soft radius 16
```

Do not solve baseline CAST Figure-count instability.

Do not align Character/Figure regions.

Do not tune ControlNet strength or timing.

Determine whether the ControlNet-specific hard-boundary conflict can be removed,
then stop.

False
