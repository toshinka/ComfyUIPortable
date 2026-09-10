# M3B-PI1 — Optional CLEAN Guide Production Backend Integration

Date: 2026-09-11 JST
Issuer: Web GPT SOL
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: LONG-RUN / BOUNDED PRODUCTION INTEGRATION
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_PI1_OPTIONAL_CLEAN_GUIDE_PRODUCTION_BACKEND_INTEGRATION.md`

---

# 0. Responsibility

This Card has exactly one responsibility:

```text
Promote the qualified M3B research architecture into a production-class
GUIDED backend workflow while leaving the existing no-Guide production
workflow unchanged.
```

This Card does NOT implement user-facing automatic workflow routing.

This Card does NOT add new UI controls.

---

# 1. Project context

Repository:

`D:\GitHub\tegaki`

Primary root:

`ComfyUIPortable/`

Canonical Manga entry:

`ComfyUIPortable/GITHUB_MANGA.txt`

Product principles remain:

```text
Minimum-Hand
Scene-first
seed variation retained
progressive disclosure
Guide optional
CAST optional
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

Do not redesign these semantics.

---

# 2. Governance

Web GPT SOL owns intermediate Card design/review.

Gemini executes this Card.

Gemini does NOT self-accept the milestone.

Owner retains final product acceptance.

Do NOT:

```text
commit
push
start PI2
redesign schema
perform unrelated cleanup
```

unless separately authorized.

---

# 3. Mandatory publication gate

The previous M3B-LR8 local report claimed:

```text
CORE_GLOBAL_QUALIFIED
```

But Web GPT SOL previously observed that LR8 completed evidence had not yet been
published.

Therefore Stage 0 MUST establish publication before any production edits.

Run:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

Then verify on the current repository state that all of these exist:

```text
docs/manga/cards/completed/
M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION.md

docs/manga/reports/
M3B_LR8_CORE_CAST_GLOBAL_ROBUSTNESS_QUALIFICATION_REPORT.md

docs/manga/verification/m3b_lr8/
M3B_LR8_MANIFEST.json
M3B_LR8_VISUAL_LEDGER.md
M3B_LR8_CONTACT_SHEET.png
M3B_LR8_RUNTIME_PROVENANCE.json
```

Manifest/report must establish:

```text
Core ControlNetApplyAdvanced contract: PASS
Advanced-ControlNet used: NO
Effect mask used: NO
Queues: 12/12 PASS
paired regressed: 0/6
Figure count not worse: 6/6
All CORE_GLOBAL quality USABLE: YES
Clear boundary artifacts: 0/6
Clear regional/control conflicts: 0/6
Seed variation: PRESENT
qualification: CORE_GLOBAL_QUALIFIED
```

If any required publication artifact is absent or contradictory:

```text
STOPPED:
LR8_PUBLICATION_NOT_ESTABLISHED
```

Do not use unpublished/local-only evidence as production authorization.

---

# 4. LR8 acceptance transition

If Stage 0 passes, record CURRENT AUTHORITY as:

```text
Latest SOL-reviewed Manga public commit:
<public SHA containing completed LR8>

M3B-LR8:
PUBLISHED / SOL REVIEWED

M3B-LR8 final result:
CORE_GLOBAL_QUALIFIED

M3B research qualification:
CLOSED FOR CURRENT CLEAN-GLOBAL CANDIDATE

Production ControlNet integration:
M3B-PI1 ACTIVE
```

Do not rewrite historical LR8 execution wording such as:

```text
Publication: LOCAL
Owner push required: YES
```

Historical execution truth remains historical.

---

# 5. Qualified architecture

The production candidate is fixed:

```text
User RAW Rough Guide
        |
        +--> editing/reference preview only

Guide Figure Regions
        |
        +--> deterministic CLEAN generation Guide
                |
                +--> GLOBAL ControlNet
                        |
                        +--> existing Scene / CAST conditioning
```

Explicitly:

```text
RAW pixels are NOT sent to ControlNet.

Effect mask is NOT used.

Advanced-ControlNet is NOT used.
```

---

# 6. Production candidate parameters

Fixed from research qualification:

```text
ControlNet:
CN-anytest4_illustrious2_A.safetensors

Apply:
ComfyUI core ControlNetApplyAdvanced

strength:
0.75

start_percent:
0.0

end_percent:
1.0

preprocessor:
none

effect mask:
NONE
```

No parameter tuning in PI1.

---

# 7. Model identity

Selector:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

Expected SHA256:

`e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8`

Model remains in shared external storage.

Do NOT modify:

```text
E:\EasyReforge\
E:\Data\Models\
D:\Models\
```

No model download.

No copy.

No junction/symlink changes.

---

# 8. Preserve RoughGuideBridge contract

Existing:

`custom_nodes_custom/tegaki_manga_nodes/rough_guide_bridge.py`

has an intentionally observational contract.

Do NOT repurpose:

`TegakiMangaRoughGuideBridge`

into a generation-conditioning node.

Its current outputs remain:

```text
rough_guide_image
figure_union_mask
debug_json
```

and its historical semantics remain valid.

---

# 9. New production generation-guide bridge

Preferred new source:

`ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/generation_guide_bridge.py`

Preferred node name:

```text
TegakiMangaGenerationGuideBridge
```

Responsibility:

```text
Authoring Document
+
enabled rough_manga Guide Figure geometry
->
deterministic CLEAN page-sized generation Guide
```

Nothing else.

---

# 10. Generation bridge inputs

Minimum:

```text
document_json
page_index
```

Do not add user-adjustable generation parameters.

No strength input.

No ControlNet selector input.

No pose inference setting.

---

# 11. Generation bridge outputs

Preferred:

```text
clean_generation_guide : IMAGE
debug_json              : STRING
```

If an explicit status output is technically useful, one boolean/status output
may be added.

Do not expose Figure masks for production ControlNet application.

---

# 12. Eligible generation Guide

A Page is generation-Guide eligible only when:

```text
at least one enabled guide_type = rough_manga
AND
at least one valid figure_regions[] entry exists
```

CAST association is NOT required.

Therefore:

```text
figure.instance_id = null
```

remains legal.

Figure geometry itself is sufficient.

---

# 13. No-generation-guide cases

These must NOT activate Guide generation influence:

```text
no page.guides[]

only disabled rough_manga Guides

enabled rough_manga Guide with zero Figure Regions
```

Classification:

```text
NO_GENERATION_GUIDE
```

Do not derive control from RAW pixels alone.

---

# 14. Multiple Figures

All valid Figure Regions from eligible enabled Rough Guides may contribute to
the same page-sized CLEAN generation Guide.

Same CAST multiple appearances remain separate Figure/Instance records.

No identity inference.

No human detection.

No segmentation.

---

# 15. Geometry source

Page-space geometry must use the existing LR1 semantics:

```text
page_x = placement.x + local.x * placement.w
page_y = placement.y + local.y * placement.h
page_w = local.w * placement.w
page_h = local.h * placement.h
```

Do not reinterpret Figure coordinates.

Prefer reuse of existing validated helpers rather than duplicating geometry
rules.

---

# 16. CLEAN rendering contract

For every Figure:

```text
background:
white

foreground:
black

renderer:
existing draw_single_character_mannequin()

guide_style:
flat_silhouette

shot_type:
full_body

include_bbox_outline:
false
```

Do not draw:

```text
Figure bounding rectangles
panel frames
labels
text
RAW image strokes
Guide asset pixels
Character mask rectangles
effect-mask boundaries
```

---

# 17. Pose policy

PI1 does NOT infer pose from:

```text
acting_prompt
RAW Guide pixels
CAST identity
```

Use the same deterministic CLEAN representation qualified by LR3–LR8.

Do not introduce pose extraction.

---

# 18. Research parity gate

Using the existing LR3/LR8 fixture, the new production generation bridge must
produce a CLEAN image byte-equivalent to the qualified research CLEAN fixture
unless a documented encoding-only difference exists.

Expected research CLEAN SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

Preferred gate:

```text
SHA256 exact parity:
PASS
```

If bytes differ:

compare decoded pixels.

Allowed only if:

```text
decoded pixel parity:
EXACT
```

Otherwise:

```text
STOPPED:
PRODUCTION_CLEAN_GUIDE_PARITY_FAIL
```

Do not silently accept a new rendering representation.

---

# 19. RAW separation proof

Add a deterministic test proving:

```text
RAW asset A
and
RAW asset B
```

with identical Guide placement/Figure geometry produce the identical CLEAN
generation Guide.

This proves:

```text
RAW pixels do not affect generation-control representation.
```

This is a required production gate.

---

# 20. New production workflow

Create:

`ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`

Do NOT replace:

`ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

The existing workflow remains the canonical no-Guide backend.

---

# 21. Guided workflow required nodes

The guided production workflow should use the established production path plus:

```text
TegakiMangaGenerationGuideBridge

ControlNetLoader

ControlNetApplyAdvanced
```

The conditioning order must remain:

```text
TegakiMinimumHandSceneEditor
        |
        v
TegakiMangaConditioningBuilder
        |
        v
ControlNetApplyAdvanced
        |
        v
KSampler
```

ControlNet image:

```text
TegakiMangaGenerationGuideBridge
```

---

# 22. Forbidden guided-workflow nodes

The production guided workflow must contain zero:

```text
ACN_AdvancedControlNetApply_v2
Advanced-ControlNet-specific nodes
effect_mask
mask_optional
Figure-union ControlNet masks
RAW Rough Guide image -> ControlNet connections
```

---

# 23. Simple and CAST behavior

The same guided production workflow must support:

```text
input_mode = simple
```

and:

```text
input_mode = cast
```

For CAST:

existing Character regional conditioning remains active.

No special CAST-specific ControlNet branch.

No Character-specific ControlNet.

---

# 24. No-Guide production isolation

`MINIMUM_HAND_MANGA_DRAFT.json`

must remain free of:

```text
ControlNetLoader
ControlNetApplyAdvanced
Advanced-ControlNet
Guide generation dependency
ControlNet model dependency
```

No-Guide generation must therefore remain usable even if the AnyTest model is
absent.

This is mandatory.

---

# 25. Guided model failure policy

When the GUIDED production workflow is explicitly selected and the required
AnyTest model cannot be loaded:

```text
FAIL EXPLICITLY
```

Do NOT:

```text
silently fall back to RAW Guide
silently fall back to another ControlNet
silently ignore Guide influence
download a model
```

The error must identify the missing/unloadable ControlNet.

---

# 26. No UI routing yet

PI1 does NOT automatically select:

```text
MINIMUM_HAND_MANGA_GUIDED_DRAFT.json
```

from the product UI.

No frontend generation-button routing change in this Card.

No new Guide toggle.

No strength control.

No model selector.

No Advanced panel control.

That is PI2 responsibility after PI1 publication review.

---

# 27. Existing Guide UI

Existing authoring behavior remains untouched:

```text
upload RAW raster
preview RAW raster
edit Figure Regions
associate optional Character Instances
enable/disable Guide
save/reload
```

Do not redesign it.

---

# 28. Node registration

Register the new node through the existing Tegaki Manga custom-node registration
mechanism only.

Do not modify ComfyUI core.

Do not modify ComfyUI frontend.

---

# 29. Required unit/contract tests

Add a bounded test suite for the generation bridge.

Minimum cases:

```text
1. no Guide -> NO_GENERATION_GUIDE

2. disabled Guide -> NO_GENERATION_GUIDE

3. enabled Guide / zero Figures -> NO_GENERATION_GUIDE

4. one Figure -> deterministic CLEAN image

5. two Figures -> deterministic CLEAN image

6. unassigned Figure -> legal

7. same CAST multiple appearances -> legal

8. Guide-local -> Page geometry projection correct

9. invalid document -> fail closed

10. invalid Figure geometry -> fail closed

11. RAW asset pixel changes do not change CLEAN output

12. LR3 qualified fixture pixel/hash parity
```

---

# 30. Existing regression

Run:

```text
LR1 contract:
12/12 PASS

LR1 runtime bridge:
5/5 PASS

Guide ops:
PASS

M2B Minimum-Hand:
19/19 PASS

CAST authoring:
PASS

CAST execution:
PASS

document roundtrip:
PASS

same-CAST recurrent instance:
PASS
```

---

# 31. Production workflow structural tests

Verify:

`MINIMUM_HAND_MANGA_DRAFT.json`

contains:

```text
ControlNet nodes:
0
```

Verify:

`MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`

contains exactly the expected core ControlNet path and:

```text
Advanced-ControlNet nodes:
0

effect-mask inputs:
0
```

---

# 32. Live production-path generation matrix

Run exactly four required production-path generations.

### P0 — existing no-Guide

```text
workflow:
MINIMUM_HAND_MANGA_DRAFT.json

input mode:
simple

Guide:
none
```

Expected:

```text
PASS
```

### P1 — Guided SIMPLE

```text
workflow:
MINIMUM_HAND_MANGA_GUIDED_DRAFT.json

input mode:
simple

Guide:
qualified fixture
```

Expected:

```text
PASS
```

### P2 — Guided CAST / seed 42

```text
input mode:
cast

seed:
42
```

Expected:

```text
PASS
```

### P3 — Guided CAST / seed 202

```text
input mode:
cast

seed:
202
```

Expected:

```text
PASS
```

No larger research sweep.

LR8 already performed robustness qualification.

---

# 33. Visual gate

For P1/P2/P3 require:

```text
image quality:
USABLE

hard rectangular boundary:
NONE

regional/control conflict:
NONE or non-disruptive WEAK

obvious RAW-guide artifact:
NONE
```

Do not require exact hard tracing.

Seed creativity remains intentional.

---

# 34. Production parity

P2/P3 need only reproduce the qualified behavioral class:

```text
coarse Guide influence
usable image quality
no effect-mask boundary
no clear ControlNet/CAST conflict
```

Exact LR8 output hashes are NOT required.

---

# 35. Browser verification

Use Antigravity Browser/Computer Use.

Verify:

```text
P0
P1
P2
P3
```

through actual ComfyUI execution/image views.

No broad unrelated UI replay.

No user-facing UI changes are expected.

---

# 36. Evidence directory

Create:

`ComfyUIPortable/docs/manga/verification/m3b_pi1/`

Minimum:

```text
M3B_PI1_GENERATION_GUIDE.png
M3B_PI1_GENERATION_GUIDE_PROVENANCE.json

P0_NO_GUIDE.png
P1_SIMPLE_GUIDED.png
P2_CAST_GUIDED_SEED42.png
P3_CAST_GUIDED_SEED202.png

M3B_PI1_CONTACT_SHEET.png
M3B_PI1_RUNTIME_PROVENANCE.json
M3B_PI1_VISUAL_LEDGER.md
M3B_PI1_MANIFEST.json
```

---

# 37. Runtime provenance

Record:

```text
production generation bridge node
CLEAN renderer
Guide count
Figure count
Figure IDs
optional instance IDs
derived page areas
CLEAN SHA256
ControlNet selector
ControlNet model SHA256
ControlNet apply class
strength
start
end
effect mask = NONE
Advanced-ControlNet used = false
```

---

# 38. Contact sheet

Preferred:

```text
P0 NO-GUIDE

P1 SIMPLE GUIDED

P2 CAST GUIDED / 42

P3 CAST GUIDED / 202
```

Also show the derived CLEAN Guide in a smaller reference panel.

Do not modify generated pixels.

---

# 39. Production integration classification

Use exactly one:

```text
PI1_BACKEND_INTEGRATED

PI1_BACKEND_REJECTED

PI1_BACKEND_INCONCLUSIVE
```

---

# 40. PI1_BACKEND_INTEGRATED gates

All required:

```text
LR8 publication gate PASS

schema unchanged

new generation bridge contract PASS

RAW separation PASS

LR3/LR8 CLEAN parity PASS

existing no-Guide workflow unchanged

new guided workflow PASS

core ControlNetApplyAdvanced only

Advanced-ControlNet absent

effect mask absent

P0/P1/P2/P3 queues PASS

P1/P2/P3 image quality USABLE

no clear mask boundary artifacts

no clear regional/control conflict

existing regression PASS
```

---

# 41. PI1_BACKEND_REJECTED

Use if:

```text
production CLEAN differs materially from qualified CLEAN representation

RAW pixels leak into generation Guide

existing no-Guide path gains ControlNet dependency

guided workflow requires Advanced-ControlNet

effect mask returns

CAST conditioning breaks

new repeated image-quality degradation appears

schema change becomes necessary
```

---

# 42. PI1_BACKEND_INCONCLUSIVE

Use only when technical integration works but live evidence is insufficient to
classify production behavior.

Do not tune parameters.

---

# 43. Allowed implementation scope

Expected production source changes should remain approximately:

```text
custom_nodes_custom/tegaki_manga_nodes/generation_guide_bridge.py

custom_nodes_custom/tegaki_manga_nodes/__init__.py
or existing node registry file

workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json

bounded PI1 tests/scripts

PI1 evidence/report

current authority/router docs

this Card
```

If substantially broader source modification becomes necessary:

STOP and report.

---

# 44. Do not touch

Do not modify:

```text
H3
M4
Shell
Manga schema
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

Do not modify:

`MINIMUM_HAND_MANGA_DRAFT.json`

except if a purely metadata/non-semantic correction is absolutely required;
prefer zero diff.

---

# 45. STOP conditions

STOP immediately if:

```text
LR8_PUBLICATION_NOT_ESTABLISHED

production CLEAN parity cannot be established

schema change becomes necessary

existing no-Guide workflow must gain ControlNet dependency

Advanced-ControlNet becomes necessary

effect mask becomes necessary

new orchestration layer becomes necessary inside PI1

model identity changes

same runtime root cause fails twice
```

Do not broaden scope.

---

# 46. Report

Create:

`ComfyUIPortable/docs/manga/reports/M3B_PI1_OPTIONAL_CLEAN_GUIDE_PRODUCTION_BACKEND_INTEGRATION_REPORT.md`

Include:

```text
public LR8 authority SHA

LR8 qualification verification

implementation scope

persistent schema:
UNCHANGED

RAW editing/reference semantics

production CLEAN derivation

qualified CLEAN parity

RAW separation proof

production node contract

guided workflow node inventory

no-Guide workflow isolation

simple guided runtime

CAST guided runtime

visual results

regression

production backend classification

UI routing:
NOT IMPLEMENTED

Final Owner product review:
DEFERRED
```

---

# 47. Manifest minimum

```json
{
  "card": "M3B-PI1",
  "executor": "Gemini 3.8 Flash",
  "lr8_publication_verified": true,
  "schema_changed": false,
  "raw_guide_generation_input": false,
  "clean_guide_runtime_derived": true,
  "controlnet_apply": "ControlNetApplyAdvanced",
  "advanced_controlnet_used": false,
  "effect_mask_used": false,
  "control_strength": 0.75,
  "control_start": 0.0,
  "control_end": 1.0,
  "no_guide_workflow_controlnet_dependency": false,
  "guided_workflow_added": true,
  "ui_routing_implemented": false,
  "production_runs": "4/4 PASS|FAIL",
  "classification": "INTEGRATED|REJECTED|INCONCLUSIVE",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 48. Routing

At start:

```text
Active Card:
M3B-PI1
```

After successful closeout:

move Card byte-identically to:

`docs/manga/cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not issue or begin PI2.

---

# 49. Publication semantics

Local report may record:

```text
M3B-PI1 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

Do not self-publish.

---

# 50. Required final response

Return:

```text
Card:
M3B-PI1

Model:
Gemini 3.8 Flash

Execution baseline:
Final HEAD:
origin/main:

LR8 public publication gate:
PASS / FAIL

LR8 public SHA:

LR8 qualification:
CORE_GLOBAL_QUALIFIED / OTHER

Schema changed:
NO

Generation Guide Bridge:
PASS / FAIL

RAW pixels used for generation:
NO

CLEAN parity:
HASH_EXACT / PIXEL_EXACT / FAIL

Generation Guide SHA256:

No-Guide production workflow modified:
NO / YES

No-Guide ControlNet dependency:
NO / YES

Guided production workflow:
PASS / FAIL

ControlNetApplyAdvanced:
PASS / FAIL

Advanced-ControlNet used:
NO

Effect mask used:
NO

P0 no-Guide:
PASS / FAIL

P1 simple guided:
PASS / FAIL

P2 CAST guided seed42:
PASS / FAIL

P3 CAST guided seed202:
PASS / FAIL

Production runs:
4/4 PASS / FAIL

Guided image quality:
USABLE / DEGRADED / FAILED

Boundary artifacts:
NONE / PRESENT

Regional/control conflict:
NONE / WEAK / CLEAR

LR1 regression:
PASS / FAIL

CAST regression:
PASS / FAIL

Minimum-Hand regression:
PASS / FAIL

Production backend provisional classification:
PI1_BACKEND_INTEGRATED /
PI1_BACKEND_REJECTED /
PI1_BACKEND_INCONCLUSIVE

UI routing:
NOT IMPLEMENTED

Production integration:
BACKEND ONLY

Final Owner product review:
DEFERRED

Evidence:
Manifest:
Report:
Contact sheet:

Stopped early:
YES / NO

Stop reason:

M3B-PI1 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

---

# 51. Final boundary

This Card promotes only the qualified backend architecture:

```text
Figure Regions
->
deterministic CLEAN Guide
->
GLOBAL ComfyUI-core ControlNet
```

It does NOT yet make the product automatically choose that workflow.

The existing no-Guide production workflow must remain clean and independent.

If PI1 passes, stop.

Do not implement PI2.

PI2 will later own:

```text
Guide-enabled -> guided backend routing
Guide disabled/no Figures -> existing no-Guide backend
one-action OFF behavior
user-facing production flow verification
```
