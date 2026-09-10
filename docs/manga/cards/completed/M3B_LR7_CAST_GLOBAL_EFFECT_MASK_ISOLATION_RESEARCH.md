# M3B-LR7 — CAST GLOBAL vs EFFECT-MASK Interaction Isolation

Date: 2026-09-10 JST

Issuer:
Web GPT SOL

Executor:
Gemini 3.8 Flash / Antigravity 2.0

Mode:
BOUNDED LONG-RUN RESEARCH

Save Card as:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION_RESEARCH.md`

---

# 1. Question

Answer exactly one question:

```text
Is the LR5/LR6 visual conflict caused by CAST + ControlNet generally,
or specifically by combining CAST regional conditioning with the
ControlNet effect mask?
```

No other hypothesis is tested.

---

# 2. Known facts

Treat these as fixed:

```text
CAST compile:
PASS

Character conditioning:
PASS

2 Character masks:
PASS

CLEAN Guide:
valid

AnyTest v4:
valid

Simple-mode CLEAN_GLOBAL:
quality USABLE in previous research

CAST_HARD:
quality DEGRADED
hard mask boundary CLEAR

CAST_SOFT radius 16:
quality DEGRADED
mask boundary CLEAR

SOFT numerical feathering:
PASS

Seed variation:
PRESENT
```

Therefore:

Do NOT perform another feather sweep.

---

# 3. Stage 0

Run:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

Expected SOL-reviewed Manga authority:

`f482b90d124c39f603f6863ac35aefb586e95bfd`

If origin advanced, inspect:

```bash
git diff --name-status \
  f482b90d124c39f603f6863ac35aefb586e95bfd..origin/main
```

H3-only drift is permitted.

Manga conflict with LR7-owned files requires STOP and report.

---

# 4. Current authority update

Update current authority/routing documents as required:

```text
Latest SOL-verified Manga public commit:
f482b90d124c39f603f6863ac35aefb586e95bfd

M3B-LR6:
PUBLISHED / SOL REVIEWED

M3B-LR6 final result:
SOFT_MASK_CONFLICT

M3B-LR6 key finding:
SOFTENING FIGURE EFFECT-MASK EDGE DID NOT REMOVE VISUAL BOUNDARY

Production ControlNet integration:
NOT PERFORMED

M3B-LR7:
ACTIVE
```

Do not rewrite historical LR6:

```text
M3B-LR6 publication: LOCAL
```

That was correct at execution time.

---

# 5. Missing experimental condition

Previous CAST research tested:

```text
CAST_OFF
CAST_MASKED
CAST_SOFT_MASKED
```

It did NOT directly test:

```text
CAST_GLOBAL
```

This missing condition is the entire reason for LR7.

---

# 6. Fixed CAST fixture

Reuse LR5/LR6 fixture unchanged.

Two CAST entries.

Two Character Instances.

Scene:

```text
input_mode = cast
```

Character regional conditioning remains active.

Do not change:

```text
CAST prompts
acting prompts
Character areas
Figure areas
Guide associations
Scene prompt
negative prompt
```

---

# 7. Fixed CLEAN Guide

Reuse byte-identically:

`M3B_LR3_CLEAN_GUIDE.png`

Expected SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

No new Guide representation.

---

# 8. ControlNet

Reuse:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256 from established evidence:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

Do not re-download.

Do not move.

Do not duplicate.

---

# 9. New condition

Create exactly:

```text
CAST_GLOBAL
```

using:

```text
ACN_AdvancedControlNetApply_v2

positive / negative:
existing CAST ConditioningBuilder outputs

control image:
existing CLEAN Guide

strength:
0.75

start_percent:
0.0

end_percent:
1.0

mask_optional:
UNCONNECTED
```

This is the critical invariant.

---

# 10. Comparator

Primary direct comparator:

```text
CAST_GLOBAL
vs
existing LR5 CAST_HARD
```

The intended graph difference is only:

```text
mask_optional:
none
vs
Figure-union HARD mask
```

Use existing LR5/LR6 evidence as historical comparators.

Do not regenerate them unless a technical provenance mismatch makes comparison
invalid.

---

# 11. New generations

Generate only:

```text
Seed 42 CAST_GLOBAL
Seed 77 CAST_GLOBAL
```

Exactly TWO new generation outputs.

Do not waste another four generations reproducing existing OFF/HARD evidence
unless deterministic comparison becomes technically invalid.

If regeneration becomes necessary, document why before doing it.

Maximum total generation outputs under LR7:

```text
6
```

Normal expected new outputs:

```text
2
```

---

# 12. Fixed generation profile

Keep:

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

Control strength:
0.75

Control interval:
0.0–1.0
```

No tuning.

---

# 13. Research workflow

Preserve all prior research workflows.

Create:

`ComfyUIPortable/workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json`

Preferred source:

LR5 or LR6 CAST workflow.

Remove effect-mask connection only for the GLOBAL branch.

Do not modify canonical production workflow.

---

# 14. Production workflow

Must remain unchanged:

`ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

Production dependencies must remain:

```text
ControlNet:
NO

Advanced-ControlNet:
NO

Guide:
optional / no required generation dependency
```

---

# 15. Runtime proof

Before visual classification prove:

```text
input_mode = cast

compiled Characters = 2

Character conditioning entries = 2

Character masks = 2

CAST_GLOBAL uses CLEAN Guide

CAST_GLOBAL ControlNet strength = 0.75

CAST_GLOBAL start/end = 0.0 / 1.0

CAST_GLOBAL mask_optional = UNCONNECTED
```

Record node provenance.

---

# 16. Browser verification

Use Antigravity Browser/Computer Use.

Inspect the two new CAST_GLOBAL images individually.

Also inspect the existing LR5/LR6 comparator images or contact sheet.

Do not classify from hashes alone.

Capture only enough browser/artifact evidence to support the visual ledger.

No broad UI replay.

---

# 17. Visual criteria

For each seed record:

```text
Placement:
CLEAR / WEAK / NONE / DEGRADED

Figure count:
PASS / FAIL

Side association:
PASS / MIXED / FAIL

Image quality:
USABLE / DEGRADED / FAILED

Hard rectangular boundary:
NONE / WEAK / CLEAR

Regional/control conflict:
NONE / WEAK / CLEAR
```

Also record:

```text
extra/faint Figure:
YES / NO
```

---

# 18. Important baseline distinction

Seed 77 CAST_OFF already has a Figure-count defect.

Do not charge that pre-existing defect to CAST_GLOBAL.

The central comparison is new degradation introduced by ControlNet.

---

# 19. Classification

Use exactly one:

```text
EFFECT_MASK_INTERACTION_CONFIRMED

CAST_CONTROLNET_GENERAL_CONFLICT

CAST_GLOBAL_ISOLATION_INCONCLUSIVE
```

---

# 20. EFFECT_MASK_INTERACTION_CONFIRMED

Use this if:

```text
CAST_GLOBAL has USABLE quality in both seeds

CAST_GLOBAL does not show the repeatable rectangular mask boundary

CAST_GLOBAL does not introduce a clear new regional/control conflict

and existing CAST_HARD remains the DEGRADED/boundary comparator
```

CAST_GLOBAL does not need to repair every baseline Figure-count defect.

---

# 21. CAST_CONTROLNET_GENERAL_CONFLICT

Use if CAST_GLOBAL itself produces repeatable new degradation attributable to
ControlNet despite having no effect mask.

Examples:

```text
quality DEGRADED in both seeds
clear CAST regional-conditioning conflict
new duplication/splitting
major side-association regression
```

---

# 22. CAST_GLOBAL_ISOLATION_INCONCLUSIVE

Use if results are mixed between seeds and neither causal interpretation is
supported cleanly.

Do not tune anything to rescue the result.

---

# 23. Explicit prohibitions

Do NOT test:

```text
another feather radius
ControlNet strength sweep
start/end timing sweep
Character mask feather
Character/Figure area alignment
Character-union ControlNet mask
intersection masks
per-Figure ControlNet
per-character ControlNet
another ControlNet model
new preprocessor
new schema
production integration
```

---

# 24. Allowed implementation files

Prefer only:

```text
ComfyUIPortable/scripts/m3b_lr7_build_cast_global_workflow.py

ComfyUIPortable/workflows/manga/research/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION.json

ComfyUIPortable/docs/manga/verification/m3b_lr7/*

ComfyUIPortable/docs/manga/reports/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION_RESEARCH_REPORT.md

Manga current-authority/router documents required for Stage 0

this Card
```

No production source edits are expected.

---

# 25. Evidence directory

Create:

`ComfyUIPortable/docs/manga/verification/m3b_lr7/`

Minimum:

```text
SEED_A_CAST_GLOBAL.png
SEED_B_CAST_GLOBAL.png

M3B_LR7_CONTACT_SHEET.png
M3B_LR7_RUNTIME_PROVENANCE.json
M3B_LR7_VISUAL_LEDGER.md
M3B_LR7_MANIFEST.json
```

The contact sheet may reuse copies of existing OFF/HARD evidence for visual
comparison, but clearly label them:

```text
HISTORICAL COMPARATOR
```

Do not present reused images as newly generated LR7 outputs.

---

# 26. Contact sheet

Preferred:

```text
             CAST_OFF       CAST_HARD       CAST_GLOBAL
Seed 42     historical      historical          NEW
Seed 77     historical      historical          NEW
```

Preserve original generated pixels.

---

# 27. Regression

Run existing relevant regressions:

```text
LR1 contract
LR1 runtime bridge
Guide operations
M2B Minimum-Hand frontend
CAST authoring/execution regression
```

All expected PASS.

Do not create a broad new test suite.

---

# 28. Canonical no-Guide regression

Run canonical no-Guide API-equivalent generation.

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

---

# 29. Subagent policy

Optional:

Use one read-only subagent to audit graph invariants.

Use one read-only/test subagent to run regressions.

No subagent may edit files.

The primary Gemini agent owns all writes.

If subagents produce conflicting conclusions, primary agent must inspect the
evidence directly.

---

# 30. Failure policy

One repair attempt is allowed for an ordinary workflow wiring/runtime mistake.

If the same root failure occurs twice:

STOP.

Do not broaden scope.

STOP immediately if:

```text
schema change becomes necessary
production source change becomes necessary
model change becomes necessary
CAST runtime provenance cannot be established
GLOBAL condition cannot be isolated from mask changes
```

---

# 31. Production boundary

Even if:

```text
EFFECT_MASK_INTERACTION_CONFIRMED
```

do NOT integrate CAST_GLOBAL into production.

Do not modify Product UI.

Do not add ControlNet toggles.

Do not make Advanced-ControlNet a canonical dependency.

Web GPT SOL reviews the public result first.

---

# 32. Report

Create:

`ComfyUIPortable/docs/manga/reports/M3B_LR7_CAST_GLOBAL_EFFECT_MASK_ISOLATION_RESEARCH_REPORT.md`

Include:

```text
execution baseline
publication truth
LR6 SOL result
CAST runtime provenance
exact GLOBAL graph
proof mask_optional is unconnected
two new generation outputs
historical comparator provenance
visual comparison
baseline-defect distinction
classification
regressions
canonical no-Guide result
production integration NOT PERFORMED
Final Owner product review DEFERRED
```

---

# 33. Routing

At start:

```text
Active Card:
M3B-LR7
```

At complete closeout:

move this Card byte-identically to:

`docs/manga/cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not create LR8.

---

# 34. Publication semantics

Execution report may record:

```text
M3B-LR7 publication:
LOCAL

Owner push required:
YES
```

Do not commit or push.

Owner handles publication.

---

# 35. Required final response

Return:

```text
Card:
M3B-LR7

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

CAST compile:
PASS / FAIL

Compiled Characters:

Character conditioning:
PASS / FAIL

Character masks:

CAST_GLOBAL graph provenance:
PASS / FAIL

mask_optional:
UNCONNECTED / OTHER

New generations:
2/2 PASS / FAIL

Seed 42 CAST_GLOBAL:
Placement:
Figure count:
Side association:
Quality:
Boundary artifact:
Regional/control conflict:
Extra/faint Figure:

Seed 77 CAST_GLOBAL:
Placement:
Figure count:
Side association:
Quality:
Boundary artifact:
Regional/control conflict:
Extra/faint Figure:

Existing CAST_HARD comparator:
VALID / INVALID

Classification:
EFFECT_MASK_INTERACTION_CONFIRMED /
CAST_CONTROLNET_GENERAL_CONFLICT /
CAST_GLOBAL_ISOLATION_INCONCLUSIVE

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

M3B-LR7 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

---

# 36. Final boundary

Complete this one Card thoroughly.

Do not continue into LR8.

Do not solve adjacent problems.

Do not redesign Manga architecture.

The desired outcome is causal isolation, not parameter optimization.
