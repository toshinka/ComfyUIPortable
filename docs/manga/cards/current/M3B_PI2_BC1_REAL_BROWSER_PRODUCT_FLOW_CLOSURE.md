# M3B-PI2-BC1 — Real Browser Product Flow Closure

Date: 2026-09-11 JST
Issuer: Web GPT SOL
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: BOUNDED BROWSER CLOSURE
Final product review: Owner / DEFERRED

Save as:

`ComfyUIPortable/docs/manga/cards/current/M3B_PI2_BC1_REAL_BROWSER_PRODUCT_FLOW_CLOSURE.md`

# 0. Responsibility

This Card has exactly one responsibility:

```text
Close the missing REAL BROWSER acceptance gate for M3B-PI2.
```

PI2 implementation already has technical/API evidence.

Do NOT redesign routing.

Do NOT add features.

---

# 1. Public baseline

Current public Manga commit containing PI2:

`f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740`

Previous SOL-accepted public Manga commit:

`45487bc741a9f6bb1f8025f50a27868fcc1108ae`

Current SOL assessment:

```text
M3B-PI2 publication:
PUBLISHED

Technical integration:
PASS

Tests:
PASS

Runtime:
PASS

Generated-output visual evidence:
PASS

Real Browser:
PENDING

Milestone acceptance:
PENDING
```

Reason:

`m3b_pi2_run_browser_matrix.py` exercised the live backend/API directly.

It did NOT establish actual user interaction through the rendered
Minimum-Hand UI.

---

# 2. Governance correction

Do not treat the executor-written historical phrase:

```text
Provisional milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL
```

inside the PI2 report as authority.

LUNA/Gemini never self-accepts.

Do NOT rewrite the historical report solely for this.

CURRENT AUTHORITY should state the actual state:

```text
Latest SOL-verified Manga public commit:
45487bc741a9f6bb1f8025f50a27868fcc1108ae

Latest published PI2 commit:
f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740

M3B-PI2:
PUBLISHED / TECHNICAL PASS

M3B-PI2 Browser closure:
PENDING

M3B-PI2 milestone acceptance:
PENDING

M3B-PI2-BC1:
ACTIVE

Final Owner product review:
DEFERRED
```

Also remove stale current-authority statements that still claim PI1 is the
active Card.

Do not alter historical execution records.

---

# 3. Start gate

Run:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

Expected public baseline:

`f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740`

If origin advanced:

```bash
git diff --name-status \
  f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740..origin/main
```

H3-only drift is allowed.

Manga conflicts touching PI2 files require review.

---

# 4. Mandatory execution mechanism

Use:

```text
Antigravity Browser / Computer Use
```

against the actual rendered ComfyUI Minimum-Hand interface.

This Card explicitly forbids using any of the following as a substitute for
the Browser gate:

```text
m3b_pi2_run_browser_matrix.py
urllib
requests
curl
direct /prompt submission
direct /tegaki/manga/generation/prepare invocation
unit tests alone
DOM-free fixture mutation
```

Those remain useful regression evidence, but they do not satisfy BC1.

---

# 5. Browser starting point

Open the actual ComfyUI UI.

Load the normal Minimum-Hand Manga workflow containing:

```text
TegakiMinimumHandSceneEditor
```

Confirm visibly that the product UI contains:

```text
Generate Draft
Generation: Standard / Guide-assisted
Rough Guide editing layer
Disable Guide / Enable Guide
```

Do not replace the visible graph while testing automatic routing.

---

# 6. B0 — real No-Guide flow

Using the rendered UI:

ensure the current Page has no eligible Guide.

Visually confirm:

```text
Generation: Standard
```

Click:

```text
Generate Draft
```

Required:

```text
button visibly enters preparing/queueing state
exactly one prompt is queued
visible feedback says Queued · Standard
generation completes
output appears
```

Record the actual prompt ID if available.

Backend route must be:

`STANDARD_NO_GUIDE`

Submitted prompt must contain:

```text
ControlNet nodes: 0
```

---

# 7. B1 — Guide exists, zero Figures

Use a document/UI state containing an enabled Rough Guide but zero Figure
Regions.

This may be reached through normal Guide editing or a valid saved authoring
state.

Do not simulate it only in Python.

Visually confirm:

```text
Generation: Standard
```

Click Generate Draft.

Required:

```text
route:
STANDARD_NO_GUIDE

ControlNet nodes:
0

queue:
PASS
```

Uploading/possessing a raster alone must not activate Guide assistance.

---

# 8. B2 — SIMPLE Guide-assisted

In actual UI:

create or restore an enabled Rough Guide with at least one valid Figure Region.

Scene remains:

```text
input_mode = simple
```

Visually confirm badge changes to:

```text
Generation: Guide-assisted
```

Click Generate Draft.

Required:

```text
submitted route:
GUIDED_CLEAN_GLOBAL

queue:
PASS

output:
present
```

Visual output gate:

```text
quality:
USABLE

hard rectangular artifact:
NONE

obvious RAW raster artifact:
NONE
```

---

# 9. B3 — one-action OFF

Starting directly from the B2 UI state:

click exactly once:

```text
Disable Guide
```

Do not perform any other generation-routing action.

Required immediately:

```text
Generation: Standard
```

Then click:

```text
Generate Draft
```

Required:

```text
STANDARD_NO_GUIDE
ControlNet nodes = 0
queue PASS
visible Queued · Standard feedback
```

This is the critical one-action OFF browser proof.

---

# 10. B4 — re-enable

From B3:

click exactly once:

```text
Enable Guide
```

Required immediately:

```text
Generation: Guide-assisted
```

Click Generate Draft.

Required:

```text
GUIDED_CLEAN_GLOBAL
queue PASS
```

No second routing toggle.

---

# 11. B5 — CAST Guided

Through the rendered Minimum-Hand UI or a valid restored authoring document,
establish:

```text
input_mode = cast

CAST entries:
>= 2

Character Instances:
>= 2

eligible enabled Rough Guide:
YES
```

Visually confirm:

```text
Generation: Guide-assisted
```

Click Generate Draft.

Required:

```text
route:
GUIDED_CLEAN_GLOBAL

CAST conditioning:
ACTIVE

queue:
PASS

output:
present

quality:
USABLE

hard rectangular artifact:
NONE
```

Do not require exact identity or hard placement tracing.

---

# 12. Real persistence gate

This was not established by the published API runner.

In the actual product/browser flow:

state A:

```text
enabled Guide
+ Figure Regions
```

Save/reload through the normal supported workflow/document persistence path.

After restore require:

```text
Generation: Guide-assisted
```

Then:

```text
Disable Guide
```

save/reload again.

After restore require:

```text
Generation: Standard
```

No new persisted routing field may appear.

Route remains derived from Guide state.

---

# 13. Real double-submit gate

With Generate Draft ready:

perform an actual rapid double-click or equivalent two user click events.

Required:

```text
submitted prompts:
1

duplicate queue:
NO
```

The second click must be blocked by the real rendered UI state.

Do not prove this only from source inspection.

---

# 14. Queue feedback gate

Verify visible browser feedback for both routes:

```text
Queued · Standard

Queued · Guide-assisted
```

The button must return to:

```text
Generate Draft
```

after preparation/queue completion.

---

# 15. Browser error presentation

Do NOT rename models, alter shared model storage, or deliberately corrupt the
installation.

Existing automated error-path tests may remain the technical evidence for
backend failures.

For BC1, only confirm the rendered error surface exists and that no stale
success state remains after a safely reproducible frontend/API failure if one
can be triggered without environment mutation.

If no safe real-browser error can be induced:

record:

```text
Browser error injection:
NOT PERFORMED — destructive environment mutation prohibited

Automated error-path regression:
PASS
```

This does not block BC1.

---

# 16. Screenshots

Capture actual Browser/Computer Use screenshots for at least:

```text
BC1_B0_STANDARD_UI.png

BC1_B2_GUIDED_UI.png

BC1_B3_DISABLED_STANDARD_UI.png

BC1_B4_REENABLED_GUIDED_UI.png

BC1_B5_CAST_GUIDED_UI.png

BC1_PERSIST_GUIDED_RELOAD.png

BC1_PERSIST_STANDARD_RELOAD.png
```

Screenshots must show the relevant route badge/control state.

Do not use generated reconstruction/mock screenshots.

---

# 17. Queue evidence

For B0–B5 record where applicable:

```text
UI state before click

route badge

actual backend route

eligible Guide count

Figure count

prompt ID

submitted node-class inventory

queue result

output filename

visible feedback
```

B1 may generate normally even though its main purpose is route verification.

---

# 18. Generated output evidence

Retain actual outputs created through the UI for:

```text
B0
B2
B3
B5
```

B4 output may be retained as well.

Do not substitute the previous API-runner output as evidence for the UI queue
path.

Previous PI2 artifacts may be used only as historical comparators.

---

# 19. No implementation changes by default

Expected source code changes:

```text
NONE
```

This is primarily a Browser closure Card.

Allowed changes:

```text
authority/routing docs
BC1 Card
BC1 report
BC1 evidence
```

---

# 20. One bounded repair

If real Browser use exposes a genuine PI2 defect, one bounded repair attempt
is allowed only in existing PI2-owned files:

```text
product_generation_router.py
product_generation_api.py
minimum_hand_generation_route.js
minimum_hand_scene_editor.js
PI2 tests directly affected
```

After a repair:

rerun the entire B0–B5 real-browser matrix.

If the same acceptance gate fails twice:

STOP.

Do not broaden.

---

# 21. Forbidden changes

Do NOT modify:

```text
Manga schema

PI1 GenerationGuideBridge semantics

ControlNet strength/timing

ControlNet model

effect masks

Advanced-ControlNet

MINIMUM_HAND_MANGA_DRAFT backend semantics

MINIMUM_HAND_MANGA_GUIDED_DRAFT backend semantics

Scene/Frame/CAST/Instance semantics

ComfyUI core

ComfyUI frontend core

H3

M4

Shell
```

---

# 22. Automated regressions

After Browser closure run the existing bounded regression set:

```text
PI2 Python route:
14/14 PASS

PI2 JS route:
10/10 PASS

PI1 Generation Guide:
12/12 PASS

LR1 contract:
12/12 PASS

LR1 bridge:
5/5 PASS

Guide ops:
PASS

Minimum-Hand:
19/19 PASS

CAST authoring:
PASS

CAST execution:
PASS

document roundtrip:
PASS

recurrent CAST:
PASS
```

No new broad test suite.

---

# 23. Browser classification

Use exactly one:

```text
PI2_BROWSER_CLOSED

PI2_BROWSER_FAILED

PI2_BROWSER_INCONCLUSIVE
```

---

# 24. PI2_BROWSER_CLOSED

All required:

```text
B0 PASS
B1 PASS
B2 PASS
B3 PASS
B4 PASS
B5 PASS

real Generate Draft click:
PASS

real one-action Disable Guide:
PASS

real Enable Guide:
PASS

real Standard/Guided badge transitions:
PASS

real UI queue submission:
PASS

real duplicate-submit prevention:
PASS

Guide state persistence/reload:
PASS

generated outputs:
USABLE

schema:
UNCHANGED

regressions:
PASS
```

---

# 25. PI2_BROWSER_FAILED

Use if any critical user-flow requirement fails, including:

```text
badge does not update after Guide toggle

actual submitted backend disagrees with badge

Disable Guide needs another action

Generate Draft fails from rendered UI

two prompts queue from a double-click

save/reload changes routing incorrectly

visible graph must be swapped manually

Guided browser output reintroduces hard artifacts
```

---

# 26. PI2_BROWSER_INCONCLUSIVE

Use only if Browser/Computer Use itself cannot establish the required state or
evidence despite the product being technically runnable.

Do not replace missing browser evidence with another Python script.

---

# 27. Evidence directory

Create:

`docs/manga/verification/m3b_pi2_bc1/`

Minimum:

```text
BC1_B0_STANDARD_UI.png
BC1_B2_GUIDED_UI.png
BC1_B3_DISABLED_STANDARD_UI.png
BC1_B4_REENABLED_GUIDED_UI.png
BC1_B5_CAST_GUIDED_UI.png

BC1_PERSIST_GUIDED_RELOAD.png
BC1_PERSIST_STANDARD_RELOAD.png

BC1_B0_OUTPUT.png
BC1_B2_OUTPUT.png
BC1_B3_OUTPUT.png
BC1_B5_OUTPUT.png

M3B_PI2_BC1_BROWSER_LEDGER.md
M3B_PI2_BC1_VISUAL_LEDGER.md
M3B_PI2_BC1_MANIFEST.json
```

---

# 28. Report

Create:

`docs/manga/reports/M3B_PI2_BC1_REAL_BROWSER_PRODUCT_FLOW_CLOSURE_REPORT.md`

Include:

```text
public PI2 SHA:
f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740

reason BC1 was required

difference between prior API/live runner and real Browser verification

actual B0-B5 interactions

route badge transitions

actual Generate Draft interactions

actual queue evidence

one-action OFF

re-enable

CAST Guided

double-submit

persistence/reload

visual output results

automated regression

source changes:
NONE / <bounded repair>

Browser classification

Final Owner product review:
DEFERRED
```

---

# 29. Manifest minimum

```json
{
  "card": "M3B-PI2-BC1",
  "executor": "Gemini 3.8 Flash",
  "pi2_public_sha": "f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740",
  "real_browser_used": true,
  "api_runner_used_as_browser_substitute": false,
  "b0": "PASS|FAIL",
  "b1": "PASS|FAIL",
  "b2": "PASS|FAIL",
  "b3": "PASS|FAIL",
  "b4": "PASS|FAIL",
  "b5": "PASS|FAIL",
  "one_action_disable": "PASS|FAIL",
  "reenable": "PASS|FAIL",
  "double_submit": "PASS|FAIL",
  "persistence": "PASS|FAIL",
  "schema_changed": false,
  "source_repair_performed": false,
  "browser_classification": "CLOSED|FAILED|INCONCLUSIVE",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 30. Routing

At start:

```text
Active Card:
M3B-PI2-BC1
```

On full completion:

move Card byte-identically to:

`docs/manga/cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not start another Card.

---

# 31. Publication

Execution report may state:

```text
Publication:
LOCAL

Owner push required:
YES
```

Do not self-accept PI2.

Do not write:

```text
ACCEPTED_BY_DELEGATED_SOL
```

as the execution result.

Only Web GPT SOL assigns that after public review.

---

# 32. Required final response

```text
Card:
M3B-PI2-BC1

Model:
Gemini 3.8 Flash

Execution baseline:
Final HEAD:
origin/main:

Public PI2 SHA:
f43acfc5ae26c0ce8cb66b2bb1cfbbecad43d740

Schema changed:
NO

Real Browser / Computer Use:
PASS / FAIL

Python API runner used as Browser substitute:
NO

B0:
PASS / FAIL

B1:
PASS / FAIL

B2:
PASS / FAIL

B3:
PASS / FAIL

B4:
PASS / FAIL

B5:
PASS / FAIL

Real Generate Draft:
PASS / FAIL

One-action Disable Guide:
PASS / FAIL

Re-enable Guide:
PASS / FAIL

Route badge transitions:
PASS / FAIL

Actual UI queue:
PASS / FAIL

Double-submit prevention:
PASS / FAIL

Persistence/reload:
PASS / FAIL

Standard output:
USABLE / DEGRADED / FAILED

Guided output:
USABLE / DEGRADED / FAILED

CAST Guided output:
USABLE / DEGRADED / FAILED

Hard Guide artifact:
NONE / PRESENT

Source repair performed:
YES / NO

Automated regressions:
PASS / FAIL

Browser classification:
PI2_BROWSER_CLOSED /
PI2_BROWSER_FAILED /
PI2_BROWSER_INCONCLUSIVE

PI2 milestone acceptance:
PENDING_SOL_REVIEW

Final Owner product review:
DEFERRED

Evidence:
Manifest:
Report:
Browser ledger:

Stopped early:
YES / NO

Stop reason:

Publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

---

# 33. Final instruction

Do not implement another feature.

Do not run another API-only "browser" matrix.

Use the actual rendered Minimum-Hand product.

The task is to establish that a human can perform:

```text
No Guide
-> Generate Draft
-> Standard

Guide + Figures
-> Generate Draft
-> Guide-assisted

Disable Guide
-> Generate Draft
-> Standard

Enable Guide
-> Generate Draft
-> Guide-assisted
```

through visible controls, with persistence and duplicate-submit behavior intact.

Prove that, record it, and stop.
