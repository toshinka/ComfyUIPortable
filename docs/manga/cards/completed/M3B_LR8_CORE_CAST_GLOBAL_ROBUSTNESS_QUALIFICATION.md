# M3B-LR8 — Core CAST_GLOBAL Robustness Qualification

Date: 2026-09-11 JST
Issuer: Web GPT SOL
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: LONG-RUN / BOUNDED RESEARCH QUALIFICATION
Final product review: Owner / DEFERRED

Save Card:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION.md`

---

# 0. Executor context

This is a continuation of the established TEGAKI Manga Authoring project.

Repository:

`D:\GitHub\tegaki`

Primary root:

`ComfyUIPortable/`

Canonical entry:

`ComfyUIPortable/GITHUB_MANGA.txt`

Product direction:

```text
Minimum-Hand
Scene-first
Illustrious-family Manga generation
seed variation retained as creative brainstorming
progressive disclosure
```

Semantic boundaries remain fixed:

```text
Semantic Scene != Visual Panel Frame

CAST != Character Instance

Character Instance area
= regional text-conditioning area

Guide Figure Region
= rough visual placement provenance

Guide
= Page-owned
```

Do not redesign these concepts.

---

# 1. Governance

Web GPT SOL designs and accepts intermediate Cards.

Gemini executes exactly one bounded Card.

Gemini does not self-accept milestones.

Owner retains final production/product acceptance.

Do not:

```text
commit
push
start LR9
create production integration
perform unrelated cleanup
```

unless separately authorized.

---

# 2. Current verified authority

Expected latest SOL-reviewed Manga public commit:

`6dfbf0e5b9d413aba7f6428db22933d5ef451628`

M3B-LR7 final SOL result:

```text
EFFECT_MASK_INTERACTION_CONFIRMED
```

Interpretation:

```text
The LR5/LR6 rectangular boundary and quality degradation are specifically
associated with ControlNet effect-mask interaction under CAST.

This does NOT yet prove CAST_GLOBAL production robustness.
```

Production ControlNet integration:

```text
NOT PERFORMED
```

---

# 3. Research history relevant to LR8

Treat as established:

```text
LR3:
CLEAN Guide improves image quality over RAW.
Placement consistency not established.

LR4 SIMPLE:
Figure-union mask improved Figure presence.
LOCALITY_SUPPORTED.

LR5 CAST + HARD effect mask:
boundary CLEAR
quality DEGRADED
CAST_MASKED_CONFLICT.

LR6 CAST + SOFT radius-16 effect mask:
boundary still CLEAR
quality still DEGRADED
SOFT_MASK_CONFLICT.

LR7 CAST_GLOBAL:
effect mask removed.

Seed 42:
CLEAR / Figure count PASS / side PASS / quality USABLE

Seed 77:
WEAK / Figure count FAIL / side FAIL / quality USABLE

Both:
boundary NONE
regional/control conflict NONE

Result:
EFFECT_MASK_INTERACTION_CONFIRMED.
```

Effect-mask research is closed for this route.

---

# 4. Central question

Answer exactly:

```text
Can the effect-mask-free CLEAN ControlNet route use ComfyUI core
ControlNetApplyAdvanced and behave as a non-destructive CAST assistance
candidate across multiple seeds?
```

This is a research qualification Card.

It is not production integration.

---

# 5. Start

Run:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

Expected authority:

`6dfbf0e5b9d413aba7f6428db22933d5ef451628`

If origin advanced:

```bash
git diff --name-status \
  6dfbf0e5b9d413aba7f6428db22933d5ef451628..origin/main
```

H3-only drift is permitted.

Manga conflict touching LR8 own files requires STOP.

---

# 6. Stage 0 — publication truth

Update CURRENT AUTHORITY:

```text
Latest SOL-verified Manga public commit:
6dfbf0e5b9d413aba7f6428db22933d5ef451628

M3B-LR7:
PUBLISHED / SOL REVIEWED

M3B-LR7 final result:
EFFECT_MASK_INTERACTION_CONFIRMED

CAST_GLOBAL:
QUALITY USABLE IN TESTED LR7 SEEDS
NO EFFECT-MASK BOUNDARY

CAST_GLOBAL robustness:
NOT YET ESTABLISHED

Production ControlNet integration:
NOT PERFORMED

M3B-LR8:
ACTIVE
```

Do not rewrite historical LR7 report:

```text
M3B-LR7 publication: LOCAL
```

No publication-only Card.

---

# 7. Production-candidate architecture under test

Candidate:

```text
RAW Rough Guide
-> editing/reference only

Figure geometry
-> derive CLEAN structural Guide

CLEAN Guide
-> GLOBAL ControlNet influence

Effect mask
-> NONE

CAST Character regional conditioning
-> remains active
```

The derived CLEAN Guide is still not persisted as a new schema object.

---

# 8. Critical dependency decision

LR7 used:

`ACN_AdvancedControlNetApply_v2`

LR8 must instead use ComfyUI core:

`ControlNetApplyAdvanced`

Reason:

```text
Effect-mask functionality is no longer part of the candidate architecture.

Therefore Advanced-ControlNet should not become a production dependency
without a separate reason.
```

---

# 9. Core node contract gate

Before generation inspect local `/object_info` and local ComfyUI implementation.

Verify:

`ControlNetApplyAdvanced`

supports the required route:

```text
positive
negative
control_net
image
strength
start_percent
end_percent
```

and any locally required VAE input.

Historical LR2R1 workflow may be used as provenance.

If the core node cannot consume the existing CAST ConditioningBuilder outputs:

```text
STOPPED:
CORE_CONTROLNET_CAST_CONTRACT_NOT_ESTABLISHED
```

Do not fall back to Advanced-ControlNet.

---

# 10. No Advanced-ControlNet in LR8 graph

The new research generation graph must contain:

```text
ControlNetLoader
ControlNetApplyAdvanced
```

It must NOT contain:

```text
ACN_AdvancedControlNetApply_v2
mask_optional
effect_mask
```

Record node-type inventory in evidence.

---

# 11. Fixed CLEAN Guide

Reuse byte-identically:

`M3B_LR3_CLEAN_GUIDE.png`

Expected SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

No renderer changes.

No Guide-style changes.

No RAW input.

---

# 12. Model

Reuse only:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256 from established evidence:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

No download.

No copy.

No junction or model-path changes.

Do not modify:

```text
E:\EasyReforge\
E:\Data\Models\
D:\Models\
```

---

# 13. CAST fixture

Reuse the existing LR7 CAST fixture.

Required:

```text
input_mode = cast

compiled Characters = 2

inst_1 -> cast_1
inst_2 -> cast_2

Character conditioning entries = 2
Character masks = 2
```

Do not edit prompts or spatial areas.

---

# 14. Fixed generation settings

Use:

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

Character mask feather:
0

ControlNet strength:
0.75

ControlNet start:
0.0

ControlNet end:
1.0

preprocessor:
none
```

No parameter tuning.

---

# 15. Seed matrix

Use exactly six seeds:

```text
42
77
101
202
303
404
```

42 and 77 preserve continuity.

101/202/303/404 are fixed additional replication seeds.

Do not replace failed seeds.

Do not cherry-pick successful seeds.

---

# 16. Conditions

Exactly two conditions per seed:

```text
CAST_OFF
CAST_CORE_GLOBAL
```

Total:

```text
6 seeds × 2 conditions = 12 outputs
```

No masked condition.

No ACN generation condition.

---

# 17. CAST_OFF

CAST regional conditioning:

```text
ACTIVE
```

ControlNet:

```text
BYPASSED
```

---

# 18. CAST_CORE_GLOBAL

Same CAST condition.

Use:

```text
ControlNetApplyAdvanced

CLEAN Guide

strength = 0.75
start = 0.0
end = 1.0

effect mask:
NONE
```

For each seed, the only generation difference from CAST_OFF is global
ControlNet application.

---

# 19. Paired invariant

Within each seed OFF vs CORE_GLOBAL keep identical:

```text
document
CAST
Character Instances
Character areas
Scene prompt
CAST prompts
acting prompts
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
Character conditioning
```

Only global ControlNet differs.

---

# 20. LR7 historical parity check

For Seeds 42 and 77 compare new:

```text
CAST_CORE_GLOBAL
```

against historical LR7:

```text
CAST_GLOBAL using ACN_AdvancedControlNetApply_v2
```

Historical LR7 hashes:

Seed 42:

`51154a6680303d62736456553752a01731fa37f5c90658ee66fd459f4d24a6e5`

Seed 77:

`7d1149c25124d6690a24153929d344164320840e843fa443f05ef8913a829e0d`

Record:

```text
pixel/hash exact parity:
YES / NO

visual behavioral parity:
PASS / FAIL
```

Exact hash equality is desirable but NOT required.

Core implementation may produce a different image while preserving equivalent
useful behavior.

---

# 21. Core parity failure

If the core node causes a new repeated technical/visual failure that LR7 ACN
GLOBAL did not exhibit:

```text
CORE_BACKEND_PARITY_FAIL
```

Do not continue to parameter tuning.

---

# 22. Queue gate

Required:

```text
12/12 PASS
```

Record per output:

```text
seed
condition
filename
SHA256
dimensions
queue status
```

---

# 23. Paired visual evaluation

For every seed evaluate OFF and CORE_GLOBAL:

```text
Placement:
CLEAR / WEAK / NONE / DEGRADED

Figure count:
PASS / FAIL

Side association:
PASS / MIXED / FAIL

Image quality:
USABLE / DEGRADED / FAILED

Boundary artifact:
NONE / WEAK / CLEAR

Regional/control conflict:
NONE / WEAK / CLEAR

Extra/faint Figure:
YES / NO
```

No biometric identity claim.

---

# 24. Paired delta

For each seed classify CORE_GLOBAL relative to OFF:

```text
IMPROVED

NEUTRAL

REGRESSED
```

`IMPROVED` means coarse placement / Figure presence / side association improves
without quality regression.

`NEUTRAL` means behavior is comparably usable with no meaningful new defect.

`REGRESSED` means CORE_GLOBAL introduces a new meaningful defect not present
in paired OFF.

---

# 25. Baseline defects

A defect already present in CAST_OFF must remain identified as:

```text
BASELINE
```

Do not automatically charge it to ControlNet.

But if CORE_GLOBAL makes a baseline defect materially worse, that is:

```text
REGRESSED
```

---

# 26. Creative-seed principle

Do NOT require every seed to reproduce exact Figure coordinates.

The product deliberately preserves seed creativity.

The Guide is intended to provide:

```text
coarse assistance
```

not hard tracing.

Therefore minor composition differences are legal.

---

# 27. Non-destructive requirement

The production candidate must primarily be non-destructive.

Required across all six CORE_GLOBAL outputs:

```text
Image quality:
USABLE

Boundary artifact:
NONE or non-disruptive WEAK

Regional/control conflict:
not CLEAR
```

A repeatable CLEAR artifact is automatic qualification failure.

---

# 28. Robustness classification

Use exactly one:

```text
CORE_GLOBAL_QUALIFIED

CORE_GLOBAL_NOT_QUALIFIED

CORE_GLOBAL_INCONCLUSIVE
```

---

# 29. CORE_GLOBAL_QUALIFIED gates

All required:

1. Core `ControlNetApplyAdvanced` contract/runtime PASS.
2. No Advanced-ControlNet node in LR8 generation graph.
3. 12/12 generation queues PASS.
4. All six CORE_GLOBAL images remain `USABLE`.
5. No CORE_GLOBAL image has `CLEAR` boundary artifact.
6. No CORE_GLOBAL image has `CLEAR` regional/control conflict.
7. Paired delta:

   * at least 4/6 are `IMPROVED` or `NEUTRAL`;
   * no more than 2/6 are `REGRESSED`.
8. Figure-count behavior is not worse than paired OFF in at least 5/6 seeds.
9. Seed variation remains clearly present.
10. Seeds 42/77 retain acceptable behavioral parity with LR7 ACN GLOBAL.

---

# 30. CORE_GLOBAL_NOT_QUALIFIED

Use if any of these occur:

```text
repeated quality degradation
repeatable new visual artifact
clear regional/control conflict
more than 2/6 paired regressions
Figure count worsens in 2 or more seeds
core backend cannot preserve CAST conditioning
seed variation collapses
```

---

# 31. CORE_GLOBAL_INCONCLUSIVE

Use only when:

```text
technical route works
quality remains generally usable
but paired evidence is too mixed to support or reject robustness
```

Do not rescue with parameter tuning.

---

# 32. No timing or strength sweep

Do NOT test:

```text
strength 0.25
strength 0.50
different start_percent
different end_percent
```

Fixed:

```text
0.75
0.0
1.0
```

---

# 33. Mask research closed

Do NOT test:

```text
HARD mask
SOFT mask
feather
Character-union mask
Figure/Character intersection
per-Figure mask
per-character ControlNet
```

LR5–LR7 already isolated the relevant effect-mask failure.

---

# 34. No Guide redesign

Do NOT test:

```text
new silhouette style
pose skeleton
line-art cleaner
new preprocessor
RAW Guide
```

CLEAN representation remains fixed.

---

# 35. Research workflow

Preserve all historical workflows.

Create:

`ComfyUIPortable/workflows/manga/research/M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS.json`

Production workflow:

`ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

must remain unchanged.

---

# 36. Allowed helper

Allowed:

`ComfyUIPortable/scripts/m3b_lr8_build_and_run_core_global_robustness.py`

It may:

```text
construct research workflow
verify node inventory
queue 12 outputs
copy evidence
record hashes/runtime provenance
```

Do not use it to modify production source.

---

# 37. Browser review

Use Antigravity browser/computer-use.

Inspect all 12 outputs through actual image views/contact sheet.

Do not classify only from hashes.

No full unrelated UI suite.

---

# 38. Evidence directory

Create:

`ComfyUIPortable/docs/manga/verification/m3b_lr8/`

Minimum:

```text
SEED_42_CAST_OFF.png
SEED_42_CAST_CORE_GLOBAL.png

SEED_77_CAST_OFF.png
SEED_77_CAST_CORE_GLOBAL.png

SEED_101_CAST_OFF.png
SEED_101_CAST_CORE_GLOBAL.png

SEED_202_CAST_OFF.png
SEED_202_CAST_CORE_GLOBAL.png

SEED_303_CAST_OFF.png
SEED_303_CAST_CORE_GLOBAL.png

SEED_404_CAST_OFF.png
SEED_404_CAST_CORE_GLOBAL.png

M3B_LR8_CONTACT_SHEET.png
M3B_LR8_RUNTIME_PROVENANCE.json
M3B_LR8_VISUAL_LEDGER.md
M3B_LR8_MANIFEST.json
```

---

# 39. Contact sheet

Layout:

```text
             CAST_OFF      CAST_CORE_GLOBAL
Seed 42          x                x
Seed 77          x                x
Seed 101         x                x
Seed 202         x                x
Seed 303         x                x
Seed 404         x                x
```

Optionally add LR7 ACN GLOBAL 42/77 separately and label:

```text
HISTORICAL BACKEND COMPARATOR
```

Do not mix them into the 12-output count.

---

# 40. Runtime provenance

Record:

```text
ControlNet apply class
ControlNet loader class
CLEAN Guide SHA256
model selector
model SHA256
compiled Character count
Character conditioning count
Character mask count
ControlNet strength/start/end
effect-mask presence = false
Advanced-ControlNet node count = 0
```

---

# 41. Regression

Run existing:

```text
LR1 contract
LR1 runtime bridge
Guide operations
M2B Minimum-Hand frontend
CAST authoring regression
CAST execution regression
same-CAST recurrent-instance regression
document roundtrip
```

All expected PASS.

Do not invent a broad new suite.

---

# 42. Canonical no-Guide regression

Queue canonical API-equivalent no-Guide generation.

Confirm:

```text
Queue:
PASS

ControlNet dependency:
NO

Advanced-ControlNet dependency:
NO

Guide dependency:
NO

CAST requirement:
NO
```

Canonical workflow remains untouched.

---

# 43. Production dependency target

LR8 is specifically testing whether the future candidate can avoid:

```text
ComfyUI-Advanced-ControlNet
```

for Guide generation influence.

Do not remove the installed extension.

Do not modify it.

Simply prove the Manga production candidate does not need it.

---

# 44. Production integration remains forbidden

Even if:

```text
CORE_GLOBAL_QUALIFIED
```

do NOT modify:

```text
MINIMUM_HAND_MANGA_DRAFT.json
product UI
Guide UI
runtime production wiring
schema
```

Qualification first.

Web GPT SOL reviews the publication before issuing production integration.

---

# 45. Subagents

Gemini may use at most TWO read-only subagents.

Recommended:

```text
Subagent A:
graph/runtime provenance audit

Subagent B:
regression/evidence consistency audit
```

Neither may write.

Primary Gemini agent owns all modifications.

---

# 46. Scope boundaries

Do not touch:

```text
H3
M4
Shell
Manga persistent schema
Scene semantics
Visual Frame semantics
CAST schema
Character Instance schema
Guide schema
ComfyUI core
ComfyUI frontend
Advanced-ControlNet source
model storage
production output namespace
```

---

# 47. STOP conditions

STOP if:

```text
core ControlNetApplyAdvanced contract is unavailable
core node cannot accept CAST conditioning
schema change becomes necessary
production source modification becomes necessary
different model becomes necessary
CLEAN Guide identity cannot be established
same runtime failure occurs twice
```

No fallback to ACN.

No parameter exploration.

---

# 48. Report

Create:

`ComfyUIPortable/docs/manga/reports/M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION_REPORT.md`

Include:

```text
Execution baseline

LR7 SOL result:
EFFECT_MASK_INTERACTION_CONFIRMED

Core ControlNetApplyAdvanced contract

No-ACN graph proof

CAST runtime proof

fixed 6-seed matrix

12-output ledger

42/77 historical ACN parity comparison

paired OFF/CORE_GLOBAL visual ledger

baseline-defect distinction

paired IMPROVED/NEUTRAL/REGRESSED classification

Figure-count robustness

quality/artifact review

seed variation

qualification result

regression

canonical no-Guide result

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

# 49. Manifest minimum

```json
{
  "card": "M3B-LR8",
  "executor": "Gemini 3.8 Flash",
  "input_mode": "cast",
  "seeds": [42, 77, 101, 202, 303, 404],
  "conditions": ["CAST_OFF", "CAST_CORE_GLOBAL"],
  "controlnet_apply": "ControlNetApplyAdvanced",
  "advanced_controlnet_used": false,
  "effect_mask_used": false,
  "compiled_characters": 2,
  "character_conditioning_active": true,
  "control_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "schema_changed": false,
  "queues": "12/12 PASS|FAIL",
  "paired_improved": 0,
  "paired_neutral": 0,
  "paired_regressed": 0,
  "figure_count_not_worse": "0/6",
  "qualification": "QUALIFIED|NOT_QUALIFIED|INCONCLUSIVE",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 50. Routing

At start:

```text
Active Card:
M3B-LR8
```

At full closeout:

move byte-identically to:

`docs/manga/cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not create or begin another Card.

---

# 51. Publication semantics

Local report may record:

```text
M3B-LR8 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

Historical LOCAL wording remains historical after later publication.

---

# 52. Required final response

Return exactly the operational result:

```text
Card:
M3B-LR8

Model:
Gemini 3.8 Flash

Execution baseline:
Final HEAD:
origin/main:

Stage 0:
PASS / FAIL

Latest SOL-reviewed Manga public commit:

Schema changed:
NO

Core ControlNetApplyAdvanced contract:
PASS / FAIL

Advanced-ControlNet used:
NO

Effect mask used:
NO

CAST compile:
PASS / FAIL

Compiled Characters:

Character conditioning:
PASS / FAIL

Character masks:

CLEAN Guide:
PASS / FAIL

ControlNet model:
PASS / FAIL

Queues:
12/12 PASS / FAIL

Seed 42:
OFF:
CORE_GLOBAL:
Delta:

Seed 77:
OFF:
CORE_GLOBAL:
Delta:

Seed 101:
OFF:
CORE_GLOBAL:
Delta:

Seed 202:
OFF:
CORE_GLOBAL:
Delta:

Seed 303:
OFF:
CORE_GLOBAL:
Delta:

Seed 404:
OFF:
CORE_GLOBAL:
Delta:

Paired improved:
x/6

Paired neutral:
x/6

Paired regressed:
x/6

Figure count not worse:
x/6

All CORE_GLOBAL quality USABLE:
YES / NO

Clear boundary artifacts:
0/6 or other

Clear regional/control conflicts:
0/6 or other

Seed variation:
PRESENT / REDUCED / LOST

LR7 ACN behavioral parity 42/77:
PASS / FAIL

Qualification provisional result:
CORE_GLOBAL_QUALIFIED /
CORE_GLOBAL_NOT_QUALIFIED /
CORE_GLOBAL_INCONCLUSIVE

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
Contact sheet:

Stopped early:
YES / NO

Stop reason:

M3B-LR8 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

---

# 53. Final instruction

Do not optimize for perfect placement.

Do not restore effect masks.

Do not tune parameters.

This Card qualifies one candidate architecture:

```text
CAST regional text conditioning
+
Figure-derived CLEAN Guide
+
GLOBAL ControlNet
+
ComfyUI core ControlNetApplyAdvanced
```

The question is whether this route is sufficiently non-destructive and robust
across seeds to justify a later production-integration Card.

Qualify it, reject it, or return inconclusive evidence.

Then stop.
