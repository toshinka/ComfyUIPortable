# M3B-LR5 — CAST + Figure-Masked CLEAN Compatibility Research

Date: 2026-09-10 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Mode: LONG-RUN / BOUNDED RESEARCH
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR5_CAST_MASKED_CLEAN_COMPATIBILITY_RESEARCH.md`

---

# 0. Purpose

M3B-LR4 is SOL-reviewed:

```text
LOCALITY_SUPPORTED
```

Verified candidate architecture:

```text
Editing Guide:
RAW Rough Guide

Generation Guide:
Figure-derived CLEAN flat silhouette

Control locality:
Figure-union effect mask

Strength:
0.75

Control interval:
0.0–1.0
```

Production integration is still NOT AUTHORIZED.

LR5 answers one remaining question:

```text
Does Figure-masked CLEAN ControlNet remain useful and non-destructive when
existing CAST / Character Instance regional conditioning is actually active?
```

---

# 1. Repository authority

Latest SOL-reviewed Manga public commit:

`54b235f1b18c5c4df5aa01f74cd6a87e201dc5bb`

Current authority documents may still describe LR4 as LOCAL because that was
the execution-time state.

Stage 0 of this Card must correct current publication truth.

---

# 2. Start

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

If main advanced:

```bash
git diff --name-status \
  54b235f1b18c5c4df5aa01f74cd6a87e201dc5bb..origin/main
```

H3-only drift does not stop.

Manga own-file conflict does.

---

# 3. Stage 0 — publication truth

Update CURRENT AUTHORITY:

```text
Latest SOL-verified Manga public commit:
54b235f1b18c5c4df5aa01f74cd6a87e201dc5bb

M3B-LR4:
PUBLISHED / SOL REVIEWED

M3B-LR4 final result:
LOCALITY_SUPPORTED

Derived CLEAN Guide:
RETAINED RESEARCH CANDIDATE

Figure-union masked ControlNet:
SUPPORTED RESEARCH CANDIDATE

Production ControlNet integration:
NOT PERFORMED

M3B-LR5:
ACTIVE
```

Do not rewrite historical LR4 report:

```text
Publication: LOCAL
```

No publication-only Card.

---

# 4. Fixed LR4 assets

Reuse byte-identically:

CLEAN Guide:

`M3B_LR3_CLEAN_GUIDE.png`

SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

Figure-union mask source:

`TegakiMangaRoughGuideBridge.figure_union_mask`

Expected mask SHA256:

`6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb`

No regeneration variation.

---

# 5. Model

Reuse only:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

No download.

No copy.

No storage change.

---

# 6. Existing fixture

Use the LR4 document.

It already contains:

```text
cast_1:
Left Student
young student, short dark hair, school uniform

cast_2:
Right Student
young student, long light hair, school uniform

inst_1:
cast_1
standing near the left window

inst_2:
cast_2
seated near the right desk
```

Guide associations:

```text
figure_1 -> inst_1
figure_2 -> inst_2
```

Do not replace these CAST entries.

Do not rewrite identity prompts to make the test easier.

---

# 7. Only document semantic change

Research copy only:

change Scene:

```text
input_mode:
simple
```

to:

```text
input_mode:
cast
```

No other authoring-document field change.

Persistent production document/schema remains unchanged.

---

# 8. CAST runtime contract gate

Before generation verify:

`compile_document_to_page_plan()` produces exactly two compiled characters.

Expected provenance:

```text
inst_1 -> cast_1
inst_2 -> cast_2
```

Each compiled character must contain:

```text
instance_id
character_id / cast_id
combined_prompt
area
coordinate_space = page
```

If not:

```text
STOPPED:
CAST_COMPILE_PATH_NOT_ESTABLISHED
```

---

# 9. Character conditioning gate

Verify `TegakiMangaConditioningBuilder` consumes both compiled characters and
creates Character masked conditioning.

Required debug evidence:

```text
characters count = 2
character_strength = 1.0
character masks count = 2
```

If Character branches are absent:

```text
STOPPED:
CAST_CHARACTER_CONDITIONING_NOT_ESTABLISHED
```

Do not implement a new regional system.

---

# 10. Spatial inputs

Record both spatial systems.

Character Instance regions:

```text
inst_1:
x 0.08
y 0.18
w 0.32
h 0.62

inst_2:
x 0.60
y 0.26
w 0.26
h 0.50
```

Guide-derived Figure regions:

```text
figure_1:
x 0.05
y 0.304984
w 0.38
h 0.369504

figure_2:
x 0.57
y 0.356304
w 0.28
h 0.297656
```

These are not identical.

Do not silently align them.

Their coexistence is part of this compatibility test.

---

# 11. Important semantics

Character Instance area means:

```text
regional text-conditioning area
```

Figure region means:

```text
rough visual placement provenance / ControlNet locality
```

LR5 does NOT redefine one as the other.

Do not modify either set of coordinates.

---

# 12. Experimental matrix

Exactly two seeds:

```text
42
77
```

Exactly two conditions:

```text
CAST_OFF
CAST_MASKED
```

Total:

```text
4 outputs
```

No GLOBAL condition.

LR4 already established GLOBAL vs MASKED.

---

# 13. CAST_OFF

Scene:

```text
input_mode = cast
```

Character regional conditioning:

```text
ACTIVE
```

ControlNet:

```text
BYPASSED
```

---

# 14. CAST_MASKED

Same CAST document and conditioning.

ControlNet:

```text
CLEAN Guide
strength = 0.75
start = 0.0
end = 1.0
preprocessor = none
effect mask = existing Figure union mask
```

Only ControlNet application differs from CAST_OFF.

---

# 15. Fixed generation profile

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

character_strength:
1.0

panel_strength:
1.0

local_region_strength:
1.0

mask_feather:
0
```

Do not tune these.

---

# 16. Research workflow

Preserve:

`workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json`

Create:

`workflows/manga/research/M3B_LR5_CAST_MASKED_COMPATIBILITY.json`

Production:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

must remain unchanged.

---

# 17. Technical invariant

For each seed CAST_OFF vs CAST_MASKED keep identical:

```text
document
CAST
Character Instances
Character areas
prompts
negative prompts
checkpoint
VAE
latent
resolution
steps
CFG
sampler
scheduler
denoise
character strength
panel strength
```

Only masked CLEAN ControlNet is added.

---

# 18. Technical queue gate

Required:

```text
Seed 42 CAST_OFF:
PASS

Seed 42 CAST_MASKED:
PASS

Seed 77 CAST_OFF:
PASS

Seed 77 CAST_MASKED:
PASS
```

Expected:

```text
4/4 PASS
```

---

# 19. Conditioning evidence

For every CAST queue record:

```text
compiled character count
character mask count
inst_1 compiled prompt
inst_2 compiled prompt
character_strength
conditioning builder status
```

Do not infer active CAST from document contents alone.

Prove it from runtime/debug output.

---

# 20. Primary visual questions

Evaluate:

```text
two-Figure presence

left/right coarse placement

cast_1 on intended left side

cast_2 on intended right side

standing-left / seated-right broad acting adherence

duplicate / extra people

missing Figure

anatomy usability
```

Do not require face-perfect identity.

---

# 21. Identity-side criterion

This Card does not test biometric identity.

Use only coarse distinguishing traits already in CAST prompts:

```text
cast_1:
short dark hair

cast_2:
long light hair
```

Record:

```text
SIDE_ASSOCIATION:
PASS / MIXED / FAIL
```

Do not claim identity guarantee.

---

# 22. Spatial-conflict review

Explicitly inspect whether Character regional masks and Figure ControlNet mask
appear to fight each other.

Record:

```text
REGIONAL_CONTROL_CONFLICT:
NONE
WEAK
CLEAR
```

Examples of conflict:

```text
identity regions visually pulled away from intended Figure
duplicate person between the two spatial areas
character split across competing regions
one spatial system suppresses the other character
```

---

# 23. Placement enum

For CAST_OFF and CAST_MASKED:

```text
Placement:
CLEAR / WEAK / NONE / DEGRADED

Figure count:
PASS / FAIL

Image quality:
USABLE / DEGRADED / FAILED

Side association:
PASS / MIXED / FAIL
```

Overall:

```text
Seed variation:
PRESENT / REDUCED / LOST
```

---

# 24. Compatibility classification

Use exactly one:

```text
CAST_MASKED_COMPATIBLE

CAST_MASKED_CONFLICT

CAST_MASKED_INCONCLUSIVE
```

---

# 25. CAST_MASKED_COMPATIBLE

All required:

1. Both MASKED seeds contain two intended Figures.
2. MASKED placement is better than or not materially worse than CAST_OFF.
3. Side association is PASS or at worst one seed PASS / one MIXED.
4. Image quality remains USABLE.
5. Regional/control conflict is NONE or WEAK without visible failure.
6. Seed variation remains PRESENT or usefully REDUCED.
7. No hard ControlNet-mask artifact.

---

# 26. CAST_MASKED_CONFLICT

Use if:

```text
MASKED loses a character that OFF retained
MASKED causes obvious identity-side inversion
MASKED introduces duplication/splitting from competing regions
quality becomes DEGRADED due to the combination
clear regional/control conflict appears
```

---

# 27. CAST_MASKED_INCONCLUSIVE

Use for mixed results between the two seeds without a clear failure mechanism.

Do not tune parameters inside LR5.

---

# 28. Historical comparison

LR4 SIMPLE/MASKED evidence may be referenced for context.

Do not regenerate SIMPLE mode.

Do not combine its hashes statistically with LR5.

LR5 direct A/B is:

```text
CAST_OFF
vs
CAST_MASKED
```

only.

---

# 29. No timing sweep

Do not change:

```text
0.75
0.0
1.0
```

No end-percent experiment.

No strength sweep.

No mask feathering.

---

# 30. No spatial alignment tuning

Do not alter Character Instance areas to match Figure regions.

Do not alter Figure regions to match Character Instance areas.

The mismatch must remain visible as a real compatibility test.

---

# 31. No per-character ControlNet

Do not create:

```text
ControlNet figure_1
ControlNet figure_2
```

No separate strengths.

No separate ControlNet prompts.

Figure union remains one mask.

---

# 32. Evidence

Create:

`docs/manga/verification/m3b_lr5/`

Minimum:

```text
SEED_A_CAST_OFF.png
SEED_A_CAST_MASKED.png

SEED_B_CAST_OFF.png
SEED_B_CAST_MASKED.png

M3B_LR5_CONTACT_SHEET.png
M3B_LR5_CONDITIONING_PROVENANCE.json
M3B_LR5_VISUAL_LEDGER.md
M3B_LR5_MANIFEST.json
```

---

# 33. Contact sheet

```text
              CAST_OFF      CAST_MASKED
Seed 42           x              x
Seed 77           x              x
```

Optionally include small Character mask and Figure-union mask references.

Do not alter generated pixels.

---

# 34. Regression

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
```

All PASS required.

---

# 35. CAST regression

Also run existing CAST/M2 authoring tests relevant to:

```text
CAST master persistence
Character Instance foreign keys
same CAST multiple appearances
instance area persistence
simple <-> cast state preservation
```

Use existing tests only.

Do not invent a broad new test suite.

---

# 36. Canonical no-Guide regression

Queue canonical Manga no-Guide path.

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

# 37. Production integration

Still forbidden.

Even if:

```text
CAST_MASKED_COMPATIBLE
```

do not modify production generation in this Card.

Do not add Product UI controls.

Do not require Advanced-ControlNet in the canonical path.

SOL reviews the published result first.

---

# 38. Next decision

If:

```text
CAST_MASKED_COMPATIBLE
```

the architecture becomes eligible for a bounded production-integration Card.

If:

```text
CAST_MASKED_CONFLICT
```

SOL decides whether to reconcile competing spatial semantics before integration.

If:

```text
CAST_MASKED_INCONCLUSIVE
```

SOL decides the smallest next research slice.

LUNA does not self-promote.

---

# 39. Report

Create:

`docs/manga/reports/M3B_LR5_CAST_MASKED_CLEAN_COMPATIBILITY_RESEARCH_REPORT.md`

Must include:

```text
Execution baseline

LR4 SOL result:
LOCALITY_SUPPORTED

CAST compile provenance

Character-conditioning runtime proof

Character Instance areas

Figure Guide areas

Exact OFF/MASKED graph difference

Four-output ledger

Figure-count result

Placement result

Side-association result

Regional/control conflict review

Image quality

Seed variation

Regression

Canonical no-Guide result

Compatibility classification

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

# 40. Manifest

Minimum:

```json
{
  "card": "M3B-LR5",
  "input_mode": "cast",
  "seeds": [42, 77],
  "conditions": ["CAST_OFF", "CAST_MASKED"],
  "compiled_characters": 2,
  "character_conditioning_active": true,
  "character_strength": 1.0,
  "control_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "figure_union_mask": true,
  "character_specific_controlnet": false,
  "schema_changed": false,
  "compatibility_result": "COMPATIBLE|CONFLICT|INCONCLUSIVE",
  "canonical_regression": "PASS|FAIL",
  "lr1_regression": "PASS|FAIL",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 41. Routing

At start:

```text
Active Card:
M3B-LR5
```

At full completion:

move Card byte-identically to:

`cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not start another Card.

---

# 42. Publication

Local report may record:

```text
M3B-LR5 publication:
LOCAL

Owner push required:
YES
```

Do not rewrite this after push.

CURRENT AUTHORITY must not use historical LOCAL wording as current truth after publication.

---

# 43. Do not touch

Do not touch:

```text
H3
Manga schema
Scene ownership
Frame semantics
CAST schema
Character Instance schema
Guide schema
model storage
ControlNet model
Advanced-ControlNet source
ComfyUI core/frontend
M4
Shell
production output namespace
```

---

# 44. STOP conditions

STOP immediately if:

```text
CAST compile produces no Characters
ConditioningBuilder produces no Character branches
existing fixture foreign keys become invalid
schema change is required
production code modification is required for the research comparison
different model is required
same runtime root cause fails twice
```

Do not broaden scope.

---

# 45. Required final response

```text
Card:
M3B-LR5

Execution baseline:
Final HEAD:
origin/main:

Stage 0 publication truth:
PASS / FAIL

Schema changed:
NO

CAST compile:
PASS / FAIL

Compiled Characters:
2 / other

Character conditioning:
PASS / FAIL

Character masks:
2 / other

Seed 42:
CAST_OFF:
CAST_MASKED:

Seed 77:
CAST_OFF:
CAST_MASKED:

Queues:
4/4 PASS / FAIL

CAST_OFF placement:
CLEAR / WEAK / NONE / DEGRADED

CAST_OFF Figure count:
PASS / FAIL

CAST_MASKED placement:
CLEAR / WEAK / NONE / DEGRADED

CAST_MASKED Figure count:
PASS / FAIL

CAST_MASKED quality:
USABLE / DEGRADED / FAILED

Side association:
PASS / MIXED / FAIL

Regional/control conflict:
NONE / WEAK / CLEAR

Seed variation:
PRESENT / REDUCED / LOST

Compatibility provisional result:
CAST_MASKED_COMPATIBLE /
CAST_MASKED_CONFLICT /
CAST_MASKED_INCONCLUSIVE

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

M3B-LR5 publication:
LOCAL

Owner push required:
YES
```

---

# 46. Final instruction

This Card answers exactly one question:

```text
Can the supported Figure-masked CLEAN ControlNet coexist with the existing
CAST / Character Instance regional-conditioning path without damaging the
Minimum-Hand generation behavior?
```

Do not optimize placement further.

Do not tune ControlNet timing.

Do not align the two spatial systems.

Do not integrate into production.

Prove compatibility or prove conflict, then stop.

