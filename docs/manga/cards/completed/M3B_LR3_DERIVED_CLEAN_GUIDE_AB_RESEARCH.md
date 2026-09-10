# M3B-LR3 — Derived Clean Guide A/B Research Slice

Date: 2026-09-10 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Mode: LONG-RUN / BOUNDED RESEARCH
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR3_DERIVED_CLEAN_GUIDE_AB_RESEARCH.md`

---

# 0. Decision basis

Astra structural audit verdict:

```text
PROCEED_WITH_ONE_RESEARCH_SLICE
```

Recommended option:

```text
Option A — Derived clean generation guide
```

Persistent schema change:

```text
NO
```

LR2R1 final SOL classification:

```text
QUALITY WEAK
```

Known facts:

```text
AnyTest v4 model identity: PASS
ControlNetLoader: PASS
A/B 8/8: PASS
Technical causality: PASS
Generation influence: VERIFIED FOR RESEARCH GRAPH
Seed variation: PRESENT

RAW Guide placement: DEGRADED
RAW Guide image quality: DEGRADED

Production integration: NOT PERFORMED
```

---

# 1. Repository state

Current repository `main` observed by SOL:

`bbb9f6720c9a4ed8fb7a029814bd10a5442542fd`

Latest SOL-reviewed Manga commit:

`cd5dcbf4baca2f6e7ca91dc587dcba013216556b`

`bbb9f672...` is H3/model-path work after the Manga commit.

No Manga conflict was observed.

---

# 2. Start

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

If `origin/main` advanced:

```bash
git diff --name-status \
  bbb9f6720c9a4ed8fb7a029814bd10a5442542fd..origin/main
```

H3-only drift does not require STOP.

Any Manga change touching LR3 own files requires review before continuing.

---

# 3. Stage 0 — publication truth

Update CURRENT AUTHORITY to:

```text
Latest SOL-verified Manga public commit:
cd5dcbf4baca2f6e7ca91dc587dcba013216556b

M3B-LR2R1:
PUBLISHED / SOL REVIEWED

M3B-LR2R1 generation influence:
VERIFIED — RESEARCH GRAPH ONLY

M3B-LR2R1 final SOL classification:
QUALITY WEAK

M3B-LR2R1 Guide placement:
DEGRADED

M3B-LR2R1 image quality:
DEGRADED

Production ControlNet integration:
NOT PERFORMED

M3B-LR3:
ACTIVE
```

Update only current-authority/router docs as needed.

Do not rewrite the historical LR2R1 report's:

```text
Publication: LOCAL
```

That remains valid execution-time history.

No publication-only Card.

---

# 4. Central hypothesis

Test exactly this hypothesis:

```text
The main LR2R1 quality failure is caused by sending the user's RAW Rough Guide
pixels directly into ControlNet.

A clean generation-specific silhouette derived only from Figure geometry may
preserve placement influence without reproducing raw Guide marks.
```

Do not test additional architecture hypotheses in this Card.

---

# 5. Architecture boundary

Preserve:

```text
Uploaded Rough Guide
=
editing/reference asset
```

Separate from:

```text
Derived CLEAN Guide
=
research generation-control image
```

Do not replace the original asset.

Do not persist the derived image in `page.guides[]`.

Do not add new document fields.

---

# 6. No schema change

Current persistent data is sufficient:

```text
page.guides[]
guide.placement
figure_regions[]
figure_id
area
instance_id
```

Page-space Figure geometry is derived at runtime/research time.

No schema version bump.

---

# 7. Research-only implementation

Do NOT modify production generation behavior.

Preferred implementation:

create a deterministic research helper/script, for example:

`ComfyUIPortable/scripts/m3b_lr3_build_clean_guide.py`

It may import and reuse:

`draw_single_character_mannequin()`

from:

`custom_nodes_custom/tegaki_manga_nodes/layout_guide_generator.py`

Do not duplicate a new silhouette drawing architecture unless importing the
existing renderer proves technically impossible.

---

# 8. CLEAN representation

Canvas:

```text
832 × 1216
white background
```

Draw exactly two black:

```text
flat_silhouette
```

figures.

Use:

```text
shot_type = full_body
include_bbox_outline = false
```

Do not draw:

```text
bounding boxes
panel outlines
text
labels
raw Rough Guide pixels
background strokes
tint
scene geometry
visual frame borders
```

---

# 9. Fixed Figure bounds

Use the Figure page bounds identified by Astra:

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

These must correspond to the current LR2R1 document-derived geometry.

Before generation, independently derive them from:

```text
guide.placement
+
figure local area
```

and compare.

Tolerance:

```text
absolute coordinate difference <= 0.0001
```

If mismatch:

```text
STOPPED:
CLEAN_GUIDE_GEOMETRY_PROVENANCE_MISMATCH
```

Do not silently use Astra's numeric values if repository data disagrees.

---

# 10. Provenance

CLEAN fixture evidence must record:

```text
guide_id
figure_id
instance_id
local area
guide placement
derived page area
renderer
renderer style
canvas dimensions
output SHA256
```

`instance_id` is provenance only.

Do not claim that ControlNet itself understands Character Instance identity.

---

# 11. Important conditioning truth

LR2R1 used:

```text
input_mode: simple
```

Therefore active character-specific CAST conditioning was not demonstrated.

Record explicitly:

```text
This experiment tests geometry-derived global ControlNet assistance.

It does NOT test Character Instance-specific ControlNet conditioning.
```

Do not change to CAST mode in LR3.

---

# 12. ControlNet model

Reuse only:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Verified shared storage:

`E:\EasyReforge\Model\ControlNet\CN-anytest_v4\`

Expected SHA256:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

Do not download another model.

Do not copy the model into Portable.

---

# 13. Exact experimental matrix

Two seeds:

```text
42
77
```

Exactly three conditions per seed:

```text
OFF
RAW
CLEAN
```

Total:

```text
6 outputs
```

No additional sweep.

---

# 14. OFF condition

```text
ControlNet bypassed
```

Same as LR2R1 baseline semantics.

---

# 15. RAW condition

Input:

existing LR2R1 raw bridge image.

ControlNet:

```text
strength = 0.75
start = 0.0
end = 1.0
preprocessor = none
```

This reproduces the strongest LR2R1 RAW condition.

---

# 16. CLEAN condition

Input:

new derived flat-silhouette CLEAN image.

ControlNet:

```text
strength = 0.75
start = 0.0
end = 1.0
preprocessor = none
```

RAW and CLEAN differ only in ControlNet input image representation.

---

# 17. Fixed generation settings

All six outputs must use:

```text
Checkpoint:
waiIllustriousSDXL_v170.safetensors

Checkpoint VAE

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
```

Keep identical:

```text
positive prompt
negative prompt
latent
document
Scene conditioning
simple-mode conditioning
Guide placement
Figure records
seed per comparison
```

---

# 18. Research workflow

Do not overwrite LR2R1 historical workflow.

Preserve:

`workflows/manga/research/M3B_LR2R1_ANYTEST_AB.json`

Create:

`workflows/manga/research/M3B_LR3_CLEAN_GUIDE_AB.json`

Production workflow:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

must not receive ControlNet generation wiring.

---

# 19. No source promotion

Do not yet add a production node for CLEAN generation.

Do not alter the public I/O contract of:

`TegakiMangaRoughGuideBridge`

for this experiment.

Do not add CLEAN Guide controls to the user UI.

Research first.

---

# 20. Technical gate

For each seed:

```text
OFF queue PASS
RAW queue PASS
CLEAN queue PASS
```

Record:

```text
output filename
output SHA256
dimensions
queue status
elapsed time if available
```

Same-seed hashes should be recorded.

Hash difference proves influence only.

It does not prove better placement.

---

# 21. Visual questions

For each seed compare OFF / RAW / CLEAN.

Evaluate only:

```text
1. left/right intended placement
2. relative Figure scale
3. duplicate / extra people
4. intrusive line / box / tint artifacts
5. basic anatomy usability
6. standing/seated prompt adherence
```

Do not introduce automatic detection or segmentation.

---

# 22. Visual enum

For RAW and CLEAN independently:

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
```

Overall:

```text
Seed variation:
PRESENT
REDUCED
LOST
```

---

# 23. Support criterion

Option A is:

```text
SUPPORTED
```

only if CLEAN, in BOTH seeds:

1. improves intended placement relative to OFF,
2. improves intended placement relative to RAW,
3. does not worsen visual quality relative to RAW,
4. removes or materially reduces intrusive raw-guide geometry,
5. retains meaningful seed variation.

All five are required.

---

# 24. Important failure interpretation

If CLEAN is visually cleaner but does not improve Figure placement:

```text
OPTION_A_NOT_SUPPORTED
```

Do not promote it just because artifacts disappear.

If only one seed improves:

```text
OPTION_A_INCONCLUSIVE
```

If both improve but seed variation collapses:

```text
OPTION_A_NOT_SUPPORTED
```

---

# 25. Scope of rejection

Failure rejects only:

```text
flat_silhouette
strength 0.75
full interval
whole-page application
fixed LR2R1 conditions
```

Do not write:

```text
Derived Guides do not work
ControlNet cannot work
M3B failed
```

---

# 26. Figure association truth

Record explicitly:

```text
Figure masks / Figure associations are used to derive geometry provenance.

They do not currently spatially restrict ControlNet application.
```

Whole-page ControlNet application remains unchanged.

Do not implement regional ControlNet in LR3.

---

# 27. RAW/CLEAN separation

Evidence must show:

```text
RAW editing/reference image
```

and:

```text
CLEAN generation-control image
```

side by side.

This is the primary architecture question.

---

# 28. Evidence directory

Create:

`docs/manga/verification/m3b_lr3/`

Minimum:

```text
M3B_LR3_CLEAN_GUIDE.png

SEED_A_OFF.png
SEED_A_RAW.png
SEED_A_CLEAN.png

SEED_B_OFF.png
SEED_B_RAW.png
SEED_B_CLEAN.png

M3B_LR3_CONTACT_SHEET.png
M3B_LR3_MANIFEST.json
M3B_LR3_VISUAL_LEDGER.md
```

---

# 29. Contact sheet

Preferred layout:

```text
           OFF     RAW     CLEAN
Seed 42     x       x        x
Seed 77     x       x        x
```

Also include small RAW Guide and CLEAN Guide references if easily possible.

Do not alter generated images for presentation.

---

# 30. Regression

Run LR1 regressions:

```text
Contract:
12/12 PASS expected

Runtime bridge:
5/5 PASS expected

Guide ops:
PASS expected

Minimum-Hand frontend:
19/19 PASS expected
```

---

# 31. Canonical regression

Queue:

`MINIMUM_HAND_MANGA_DRAFT.json`

without Guide/ControlNet requirement.

Expected:

```text
PASS
```

Confirm:

```text
ControlNet dependency:
NO
```

---

# 32. No full Browser UI replay required

LR3 changes no production UI.

Browser/live runtime is needed for actual generation queues.

Do not rerun unrelated B0–B9 or R0–R8 full suites.

---

# 33. Production promotion forbidden

Even if Option A is SUPPORTED:

do not connect CLEAN Guide to production Manga generation.

Do not add:

```text
Guide Strength
ControlNet ON/OFF
generation guide mode
```

to Product UI.

Do not alter default user behavior.

That requires the next SOL Card.

---

# 34. Astra

Do not call Astra again during LR3.

This experiment directly implements Astra's one requested research slice.

After publication, SOL reviews the evidence.

---

# 35. Report

Create:

`docs/manga/reports/M3B_LR3_DERIVED_CLEAN_GUIDE_AB_RESEARCH_REPORT.md`

Minimum contents:

```text
Execution baseline

Astra recommendation

Persistent schema:
UNCHANGED

RAW editing Guide semantics

CLEAN generation Guide derivation

Geometry provenance

Exact generation settings

Six-output ledger

Visual comparison

Seed variation

Regression

Canonical no-Guide result

Option A result:
SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

# 36. Manifest

Minimum:

```json
{
  "card": "M3B-LR3",
  "seeds": [42, 77],
  "conditions": ["OFF", "RAW", "CLEAN"],
  "raw_strength": 0.75,
  "clean_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "preprocessor": "none",
  "schema_changed": false,
  "whole_page_control": true,
  "character_specific_control": false,
  "generation_influence": "VERIFIED",
  "option_a": "SUPPORTED|NOT_SUPPORTED|INCONCLUSIVE",
  "canonical_regression": "PASS|FAIL",
  "lr1_regression": "PASS|FAIL",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 37. Classification

LUNA may record a provisional result using only:

```text
OPTION_A_SUPPORTED
OPTION_A_NOT_SUPPORTED
OPTION_A_INCONCLUSIVE
```

Final classification belongs to Web GPT SOL after public review.

---

# 38. Routing

Start:

```text
Active Card:
M3B-LR3
```

After all required stages finish:

move Card byte-identically to:

`cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not issue or start another Card.

---

# 39. Publication semantics

Local report may end with:

```text
M3B-LR3 publication:
LOCAL

Owner push required:
YES
```

CURRENT AUTHORITY must not present historical LOCAL wording as current public truth after push.

No publication-only follow-up Card.

---

# 40. Do not touch

Do not modify:

* H3
* H3 model paths
* Manga persistent schema
* Scene semantics
* Visual Frame semantics
* CAST semantics
* Character Instance ownership
* production ControlNet path
* production UI
* M4
* Shell
* ComfyUI core/frontend
* other ControlNet models
* shared model storage
* model junctions
* output namespace

---

# 41. STOP conditions

STOP if:

```text
Figure page-space derivation disagrees with audited bounds
existing renderer cannot produce requested CLEAN semantics without changing production behavior
schema change becomes necessary
production workflow modification becomes necessary
ControlNet model identity changes
same generation root cause fails twice
```

Do not broaden the experiment.

---

# 42. Required final response

```text
Card:
M3B-LR3

Execution baseline:
Final HEAD:
origin/main:

Stage 0 publication truth:
PASS / FAIL

Schema changed:
NO

CLEAN guide generation:
PASS / FAIL

CLEAN guide SHA256:

Geometry provenance:
PASS / FAIL

Figure 1 derived bounds:
Figure 2 derived bounds:

Seed 42:
OFF:
RAW:
CLEAN:

Seed 77:
OFF:
RAW:
CLEAN:

Queues:
6/6 PASS / FAIL

RAW placement:
CLEAR / WEAK / NONE / DEGRADED

RAW quality:
USABLE / DEGRADED / FAILED

CLEAN placement:
CLEAR / WEAK / NONE / DEGRADED

CLEAN quality:
USABLE / DEGRADED / FAILED

Seed variation:
PRESENT / REDUCED / LOST

Option A provisional result:
OPTION_A_SUPPORTED /
OPTION_A_NOT_SUPPORTED /
OPTION_A_INCONCLUSIVE

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

M3B-LR3 publication:
LOCAL

Owner push required:
YES
```

---

# 43. Final instruction

This Card answers one question only:

```text
Does a clean Figure-derived flat silhouette provide better useful placement
control than both OFF and the existing RAW Rough Guide under otherwise identical
LR2R1 conditions?
```

Do not solve the next problem in the same Card.

If CLEAN succeeds, stop with evidence.

If CLEAN fails, stop with evidence.

Do not automatically move to regional ControlNet, timing sweeps, sanitization,
pose extraction, or production integration.


