# M3B-LR4 — Figure-Union Mask Locality A/B Research Slice

Date: 2026-09-10 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Mode: LONG-RUN / BOUNDED RESEARCH
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR4_FIGURE_UNION_MASK_LOCALITY_AB_RESEARCH.md`

---

# 0. Purpose

M3B-LR3 result:

```text
CLEAN representation:
artifact reduction = PASS
image quality = USABLE
placement = WEAK

Seed 42:
CLEAN placement = CLEAR

Seed 77:
CLEAN placement = NONE
only one visible person

Option A:
INCONCLUSIVE
```

次に検証する仮説は一つだけ。

```text
Whole-page ControlNet application is interfering with reliable Figure
placement / Figure count.

Restricting the same CLEAN ControlNet to the existing Figure union area
may improve placement consistency without reintroducing RAW artifacts.
```

---

# 1. Verified baseline

Latest SOL-reviewed Manga public commit:

`d5df3f25866ed05fd147a8b6da2509a6878f7f24`

Current observed repository main:

`d5df3f25866ed05fd147a8b6da2509a6878f7f24`

LR3:

```text
Schema change: NO
CLEAN Guide generation: PASS
Geometry provenance: PASS
Queues: 6/6 PASS
Generation influence: VERIFIED
RAW placement: DEGRADED
RAW quality: DEGRADED
CLEAN placement: WEAK
CLEAN quality: USABLE
Seed variation: PRESENT
Option A: INCONCLUSIVE
Production integration: NOT PERFORMED
```

---

# 2. Start

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

If `origin/main` advances:

```bash
git diff --name-status \
  d5df3f25866ed05fd147a8b6da2509a6878f7f24..origin/main
```

H3-only drift does not stop.

Manga own-file conflict does.

---

# 3. Stage 0 — publication truth

Update CURRENT AUTHORITY to:

```text
Latest SOL-verified Manga public commit:
d5df3f25866ed05fd147a8b6da2509a6878f7f24

M3B-LR3:
PUBLISHED / SOL REVIEWED

M3B-LR3 final SOL result:
OPTION_A_INCONCLUSIVE

Derived CLEAN Guide:
QUALITY IMPROVEMENT VERIFIED
PLACEMENT CONSISTENCY NOT VERIFIED

Production ControlNet integration:
NOT PERFORMED

M3B-LR4:
ACTIVE
```

Do not rewrite LR3 report's execution-time:

```text
Publication: LOCAL
```

No publication-only Card.

---

# 4. Central experiment

Compare exactly:

```text
OFF
CLEAN_GLOBAL
CLEAN_MASKED
```

for exactly:

```text
Seed 42
Seed 77
```

Total:

```text
6 outputs
```

No RAW condition in LR4.

RAW failure is already established.

---

# 5. No new Guide representation

Reuse exactly the LR3 CLEAN Guide:

`M3B_LR3_CLEAN_GUIDE.png`

Expected SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

Do not regenerate with a different silhouette style.

Do not change Figure geometry.

---

# 6. Existing Figure mask

Use existing:

`TegakiMangaRoughGuideBridge.figure_union_mask`

The bridge already derives its mask from:

```text
guide.placement
+
figure_regions[].area
```

No new persisted mask.

No schema change.

No manual mask drawing.

---

# 7. Mask semantics

Before building the experiment, inspect the locally installed:

`ComfyUI-Advanced-ControlNet`

node contract.

Required capability:

an Advanced ControlNet Apply node exposing a documented optional attention/effect mask, typically:

```text
mask_optional
```

Expected installed candidate from prior inventory:

`ACN_AdvancedControlNetApply_v2`

But do not assume the exact node name.

Use local `/object_info` and/or installed source as authority.

---

# 8. Stage 1 gate

Proceed only if local node contract explicitly supports:

```text
CONDITIONING positive
CONDITIONING negative
CONTROL_NET
IMAGE
MASK / attention mask
strength
start_percent
end/stop_percent
```

and the mask is documented as restricting ControlNet effect spatially.

If not:

```text
STOPPED:
LOCAL_CONTROLNET_ATTENTION_MASK_CONTRACT_NOT_ESTABLISHED
```

Do not install another custom node.

Do not update Advanced-ControlNet.

Do not search for another implementation.

---

# 9. Loader rule

Continue using the existing verified model:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

Reuse standard `ControlNetLoader` if compatible with the selected Advanced Apply node.

Do not change loader unless the local node contract requires it.

---

# 10. No model acquisition

No download.

No duplication.

No model storage changes.

No junction/symlink changes.

---

# 11. Mask provenance

Record the exact Figure union mask used.

Expected Figure rectangles:

```text
figure_1:
x = 0.05
y = 0.304984
w = 0.38
h = 0.369504

figure_2:
x = 0.57
y = 0.356304
w = 0.28
h = 0.297656
```

Mask should represent the union of those existing Figure page regions.

Do not enlarge, feather, erode, dilate, blur, or otherwise tune the mask in LR4.

---

# 12. Mask orientation

Confirm from local Advanced-ControlNet source/contract whether:

```text
1.0 = active ControlNet region
0.0 = inactive
```

or inverse.

Use the documented/local semantics.

Record it in evidence.

Do not guess.

---

# 13. Condition OFF

```text
ControlNet:
bypassed
```

Same generation baseline.

---

# 14. Condition CLEAN_GLOBAL

Exactly reproduce LR3 CLEAN:

```text
Control image:
M3B_LR3_CLEAN_GUIDE.png

strength:
0.75

start:
0.0

end:
1.0

preprocessor:
none

attention mask:
none
```

This is the whole-page control comparator.

---

# 15. Condition CLEAN_MASKED

Use exactly the same:

```text
Control image
model
strength
start/end
preprocessor
```

as CLEAN_GLOBAL.

Only difference:

```text
attention/effect mask =
figure_union_mask
```

No other graph difference permitted.

---

# 16. Experimental invariant

For the same seed, GLOBAL and MASKED must keep identical:

```text
checkpoint
VAE
positive prompt
negative prompt
latent
resolution
steps
CFG
sampler
scheduler
denoise
ControlNet model
ControlNet input image
ControlNet strength
ControlNet start/end
document
simple-mode conditioning
Figure geometry
```

Only mask application differs.

---

# 17. Fixed generation profile

Use:

```text
Checkpoint:
waiIllustriousSDXL_v170.safetensors

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

Preprocessor:
none

Control strength:
0.75

Control interval:
0.0–1.0
```

Seeds:

```text
42
77
```

---

# 18. Conditioning boundary

Keep:

```text
input_mode = simple
```

Do not turn CAST mode on.

This remains a global Scene-conditioning experiment.

The only new variable is spatial localization of ControlNet.

---

# 19. Important truth

`instance_id` association is provenance only.

Do not claim:

```text
Character-specific ControlNet
```

CLEAN_MASKED means:

```text
Figure-union spatial ControlNet
```

not per-character conditioning.

---

# 20. Research workflow

Preserve historical:

`workflows/manga/research/M3B_LR3_CLEAN_GUIDE_AB.json`

Create:

`workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json`

Production:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

must remain unchanged.

---

# 21. No production source change

Do not change public I/O or production behavior of:

`TegakiMangaRoughGuideBridge`

The existing `figure_union_mask` output is sufficient.

If research wiring needs to consume it differently, do so only in the research graph.

---

# 22. Technical gate

Required:

```text
Seed 42 OFF:
PASS

Seed 42 CLEAN_GLOBAL:
PASS

Seed 42 CLEAN_MASKED:
PASS

Seed 77 OFF:
PASS

Seed 77 CLEAN_GLOBAL:
PASS

Seed 77 CLEAN_MASKED:
PASS
```

Total:

```text
6/6 PASS
```

---

# 23. Output ledger

Record:

```text
seed
condition
filename
SHA256
dimensions
queue status
elapsed time if available
```

Hash differences establish influence only.

---

# 24. Primary visual question

Does Figure-union masking improve:

```text
two-Figure presence
left/right placement
relative Figure scale
```

compared with CLEAN_GLOBAL?

Especially inspect Seed 77.

---

# 25. Secondary visual question

Ensure masking does not cause:

```text
hard rectangular edges
visible mask-boundary artifacts
local tint discontinuity
anatomy degradation
background discontinuity
```

---

# 26. Visual enums

For GLOBAL and MASKED separately:

```text
Placement:
CLEAR
WEAK
NONE
DEGRADED

Image quality:
USABLE
DEGRADED
FAILED

Figure count adherence:
PASS
FAIL
```

Overall:

```text
Seed variation:
PRESENT
REDUCED
LOST
```

---

# 27. Figure count rule

Expected:

```text
2 intended Figures
```

This is coarse presence only.

Do not evaluate identity correctness.

Do not use automatic detector.

Manual visual evidence is sufficient.

---

# 28. Locality hypothesis result

Record exactly one:

```text
LOCALITY_SUPPORTED

LOCALITY_NOT_SUPPORTED

LOCALITY_INCONCLUSIVE
```

---

# 29. LOCALITY_SUPPORTED criteria

All required:

1. Seed 77 MASKED improves Figure presence or placement over GLOBAL.
2. Seed 42 MASKED does not regress materially from GLOBAL.
3. Both seeds retain two-Figure presence.
4. MASKED image quality remains USABLE.
5. No obvious mask-boundary artifact.
6. Seed variation remains PRESENT or REDUCED-but-useful.

---

# 30. LOCALITY_NOT_SUPPORTED

Use if:

* MASKED provides no placement/presence benefit in either seed, or
* MASKED visibly worsens quality, or
* hard mask-boundary artifacts appear, or
* seed variation collapses.

---

# 31. LOCALITY_INCONCLUSIVE

Use if:

* only one seed improves,
* results trade one failure for another,
* technical mask behavior is real but placement interpretation remains ambiguous.

---

# 32. No timing experiments

Do not change:

```text
strength
start_percent
end_percent
```

No 0.5 end.

No early-only ControlNet.

No strength sweep.

Timing is the next hypothesis only if locality does not resolve the issue.

---

# 33. No mask tuning

Do not test:

```text
feather
blur
padding
expanded boxes
silhouette mask vs rectangle mask
per-Figure masks
```

Use the existing Figure union mask unchanged.

---

# 34. No regional ControlNet stack

Do not create two separate ControlNet instances for figure_1 / figure_2.

Do not apply different prompts or strengths per Figure.

This Card tests spatial union masking only.

---

# 35. Advanced-ControlNet boundary

Use Advanced-ControlNet only because its existing mask contract is required for this research comparison.

Do not adopt it as production dependency.

Do not claim backend parity.

Do not modify its source.

---

# 36. Evidence directory

Create:

`docs/manga/verification/m3b_lr4/`

Minimum:

```text
M3B_LR4_FIGURE_UNION_MASK.png
M3B_LR4_MASK_PROVENANCE.json

SEED_A_OFF.png
SEED_A_GLOBAL.png
SEED_A_MASKED.png

SEED_B_OFF.png
SEED_B_GLOBAL.png
SEED_B_MASKED.png

M3B_LR4_CONTACT_SHEET.png
M3B_LR4_VISUAL_LEDGER.md
M3B_LR4_MANIFEST.json
```

---

# 37. Contact sheet

Layout:

```text
            OFF       GLOBAL      MASKED
Seed 42      x           x           x
Seed 77      x           x           x
```

Include CLEAN Guide and Figure union mask as small references if convenient.

---

# 38. Regression

Run:

```text
LR1 contract:
12/12

LR1 runtime bridge:
5/5

Guide ops:
PASS

M2B frontend:
19/19
```

All PASS required.

---

# 39. Canonical regression

Queue canonical no-Guide Manga workflow.

Confirm:

```text
ControlNet dependency:
NO

Advanced-ControlNet dependency:
NO

Guide dependency:
NO

Queue:
PASS
```

Production remains independent of the research plugin path.

---

# 40. No full browser suite

No production UI change.

Only actual live generation and visual evidence are required.

Do not rerun full B0–B9 / R0–R8.

---

# 41. Report

Create:

`docs/manga/reports/M3B_LR4_FIGURE_UNION_MASK_LOCALITY_AB_RESEARCH_REPORT.md`

Minimum:

```text
Execution baseline

LR3 SOL result:
OPTION_A_INCONCLUSIVE

Local Advanced-ControlNet mask contract

Mask semantics

Figure-union provenance

Exact graph difference:
GLOBAL vs MASKED

Exact generation settings

Six-output ledger

Figure count comparison

Placement comparison

Quality comparison

Mask-boundary artifact review

Seed variation

Locality result

Regression

Canonical no-Guide result

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

# 42. Manifest

Minimum:

```json
{
  "card": "M3B-LR4",
  "seeds": [42, 77],
  "conditions": ["OFF", "CLEAN_GLOBAL", "CLEAN_MASKED"],
  "control_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "clean_guide_sha256": "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a",
  "schema_changed": false,
  "mask_source": "TegakiMangaRoughGuideBridge.figure_union_mask",
  "whole_page_global_control": true,
  "masked_control": true,
  "character_specific_control": false,
  "locality_result": "SUPPORTED|NOT_SUPPORTED|INCONCLUSIVE",
  "canonical_regression": "PASS|FAIL",
  "lr1_regression": "PASS|FAIL",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 43. Routing

At start:

```text
Active Card:
M3B-LR4
```

After full completion:

move byte-identically to:

`cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not create the next Card.

---

# 44. Publication

Local report:

```text
M3B-LR4 publication:
LOCAL

Owner push required:
YES
```

Historical local wording is retained after push.

CURRENT AUTHORITY is updated by the next substantive Card / SOL publication review flow.

No publication-only Card.

---

# 45. Production integration forbidden

Even if:

```text
LOCALITY_SUPPORTED
```

do NOT:

* modify canonical Manga generation
* add Advanced-ControlNet as required production dependency
* add Guide Strength UI
* add Mask UI
* add ControlNet toggle
* expose region-local settings
* alter Minimum-Hand default behavior

This remains research.

---

# 46. Do not touch

Do not touch:

* H3
* H3 model config
* Manga persistent schema
* Scene semantics
* Visual Frame semantics
* CAST semantics
* Character Instance semantics
* model storage
* ControlNet model files
* ComfyUI core/frontend
* Advanced-ControlNet source
* M4
* Shell
* production output namespace

---

# 47. STOP conditions

STOP if:

```text
Local Advanced-ControlNet mask contract is unavailable
mask semantics cannot be established
existing Figure union mask cannot be consumed without production source changes
schema change becomes necessary
different ControlNet model becomes necessary
same root cause fails twice
```

Do not broaden to another technique.

---

# 48. Required final response

```text
Card:
M3B-LR4

Execution baseline:
Final HEAD:
origin/main:

Stage 0 publication truth:
PASS / FAIL

Schema changed:
NO

Advanced-ControlNet local mask contract:
PASS / FAIL

Apply node:
Mask input:
Mask semantics:

Figure union mask:
PASS / FAIL

Mask SHA256:

Figure 1 bounds:
Figure 2 bounds:

Seed 42:
OFF:
GLOBAL:
MASKED:

Seed 77:
OFF:
GLOBAL:
MASKED:

Queues:
6/6 PASS / FAIL

GLOBAL placement:
CLEAR / WEAK / NONE / DEGRADED

GLOBAL quality:
USABLE / DEGRADED / FAILED

GLOBAL Figure count:
PASS / FAIL

MASKED placement:
CLEAR / WEAK / NONE / DEGRADED

MASKED quality:
USABLE / DEGRADED / FAILED

MASKED Figure count:
PASS / FAIL

Mask-boundary artifacts:
NONE / PRESENT

Seed variation:
PRESENT / REDUCED / LOST

Locality provisional result:
LOCALITY_SUPPORTED /
LOCALITY_NOT_SUPPORTED /
LOCALITY_INCONCLUSIVE

LR1 regression:
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

M3B-LR4 publication:
LOCAL

Owner push required:
YES
```

---

# 49. Final instruction

This Card answers exactly one question:

```text
Does applying the same CLEAN ControlNet only inside the existing Figure union
mask improve reliable two-Figure placement compared with whole-page CLEAN
ControlNet application?
```

Do not test timing, feathering, per-character control, new Guide styles,
different models, or production integration.

If supported, stop with evidence.

If unsupported, stop with evidence.

If inconclusive, stop with evidence.


