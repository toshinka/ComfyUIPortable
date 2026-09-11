# M3B-PI2 — Minimum-Hand Automatic Guide Routing & Product Generate Integration

Date: 2026-09-11 JST
Issuer: Web GPT SOL
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: LONG-RUN / BOUNDED PRODUCT INTEGRATION
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_PI2_MINIMUM_HAND_AUTOMATIC_GUIDE_ROUTING.md`

---

# 0. Responsibility

This Card has exactly one responsibility:

```text
Make Minimum-Hand generation automatically choose the already-qualified
production backend from the current Authoring Document.

No eligible generation Guide
-> STANDARD no-Guide backend

Eligible enabled Rough Guide with Figure geometry
-> GUIDED CLEAN-GLOBAL backend
```

The user must not manually choose a workflow.

---

# 1. Public authority

Latest SOL-reviewed Manga public commit:

`45487bc741a9f6bb1f8025f50a27868fcc1108ae`

M3B-PI1 final SOL result:

```text
PI1_BACKEND_INTEGRATED
```

Accepted production backends:

```text
STANDARD:
workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json

GUIDED:
workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json
```

Production backend integration:

```text
COMPLETE
```

UI/product routing:

```text
NOT YET IMPLEMENTED
```

---

# 2. Stage 0

Run:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

If origin advanced:

```bash
git diff --name-status \
  45487bc741a9f6bb1f8025f50a27868fcc1108ae..origin/main
```

H3-only drift is allowed.

Manga conflicts touching PI2 files require review before editing.

---

# 3. Authority correction

Current Manga authority documents still contain some historical/current-state
wording such as:

```text
PI1 completed locally
Owner push required
```

even though PI1 is now publicly present.

Stage 0 must update CURRENT AUTHORITY to:

```text
Latest SOL-verified Manga public commit:
45487bc741a9f6bb1f8025f50a27868fcc1108ae

M3B-PI1:
PUBLISHED / SOL REVIEWED

M3B-PI1 final result:
PI1_BACKEND_INTEGRATED

Production backend integration:
COMPLETE

M3B-PI2:
ACTIVE

Automatic product routing:
IN PROGRESS

Final Owner product review:
DEFERRED
```

Do NOT rewrite historical PI1 report execution wording.

---

# 4. Product rule

The routing rule is deterministic.

Use exactly two backend enums:

```text
STANDARD_NO_GUIDE

GUIDED_CLEAN_GLOBAL
```

No third automatic route.

---

# 5. Guide eligibility

`GUIDED_CLEAN_GLOBAL` is selected only when the resolved Page contains:

```text
at least one enabled guide_type == "rough_manga"
AND
at least one valid figure_regions[] entry
```

Everything else selects:

```text
STANDARD_NO_GUIDE
```

---

# 6. Required STANDARD cases

All must route STANDARD:

```text
page.guides missing / []

only disabled rough_manga Guides

enabled rough_manga Guide with zero Figure Regions

Guide removed

Guide disabled after previously being Guided
```

RAW asset existence alone is NOT sufficient.

---

# 7. Required GUIDED cases

Route GUIDED when:

```text
enabled rough_manga Guide
+
one or more valid Figure Regions
```

`figure.instance_id` may be null.

CAST association is not required for routing.

---

# 8. Semantic boundary

Routing uses only Guide enablement and Figure geometry existence.

Do NOT use:

```text
RAW pixel contents
CAST presence
Character Instance count
Scene input_mode
prompt contents
seed
ControlNet availability
```

to decide whether the document semantically requests Guide assistance.

ControlNet availability is a runtime prerequisite after GUIDED has been chosen,
not a routing criterion.

---

# 9. Existing Guide OFF action

The existing button:

```text
Disable Guide
```

already changes:

```text
guide.enabled
```

PI2 must make this sufficient.

Required behavior:

```text
Guide enabled + Figures
-> GUIDED_CLEAN_GLOBAL

click Disable Guide
-> STANDARD_NO_GUIDE

click Enable Guide again
-> GUIDED_CLEAN_GLOBAL
```

No second routing toggle.

This is the required one-action OFF behavior.

---

# 10. Product-facing language

Do not expose technical implementation language as primary UX.

Preferred user labels:

```text
Generation: Standard

Generation: Guide-assisted
```

Do not show by default:

```text
ControlNet
AnyTest
ControlNetApplyAdvanced
workflow filename
effect mask
```

These remain implementation details.

---

# 11. Generate action

Add one product-facing button to:

`web/js/minimum_hand_scene_editor.js`

Preferred label:

```text
Generate Draft
```

It must be available regardless of whether a Guide exists.

Place it in the global/product generation area, not inside the Guide-only
inspector.

---

# 12. Route status

Near `Generate Draft`, display a compact current route status:

```text
Generation: Standard
```

or:

```text
Generation: Guide-assisted
```

This is status only.

It is not a selector.

---

# 13. Queue-time authority

The frontend route label may use a lightweight local preview function.

But queue-time route authority MUST be backend validated.

Never queue solely from cached frontend route state.

On every Generate Draft click:

```text
sync current Authoring Document
-> backend validation
-> backend route decision
-> executable prompt preparation
-> queue
```

---

# 14. Preferred production modules

Create bounded production modules such as:

```text
custom_nodes_custom/tegaki_manga_nodes/product_generation_router.py

custom_nodes_custom/tegaki_manga_nodes/product_generation_api.py
```

Responsibilities must remain separate:

```text
product_generation_router.py:
pure validation / route / prompt preparation logic

product_generation_api.py:
PromptServer HTTP boundary only
```

Do not put routing semantics directly into a large frontend callback.

---

# 15. Existing API pattern

Use the repository's existing Manga `PromptServer.instance.routes` pattern.

Do NOT modify ComfyUI server core.

Register through the Tegaki custom-node package.

A preferred endpoint is:

```text
POST /tegaki/manga/generation/prepare
```

Exact path may differ only for a clear collision/consistency reason.

---

# 16. Endpoint input

Accept only product state needed for generation:

```json
{
  "document_json": "...",
  "page_index": 0
}
```

Do not accept arbitrary:

```text
workflow filesystem paths
model filesystem paths
node class names
shell commands
output directories
remote URLs
```

from the browser.

---

# 17. Endpoint output

Successful response should include:

```json
{
  "ok": true,
  "route": "STANDARD_NO_GUIDE",
  "reason": "...",
  "prompt": {},
  "route_meta": {}
}
```

or:

```json
{
  "ok": true,
  "route": "GUIDED_CLEAN_GLOBAL",
  "reason": "...",
  "prompt": {},
  "route_meta": {}
}
```

The endpoint prepares the prompt.

It does NOT directly manipulate the browser graph.

---

# 18. Queue mechanism gate

Before implementation, inspect the installed local ComfyUI frontend contract
for:

```text
api.queuePrompt
```

and any required prompt wrapper/signature.

Record the exact local signature/usage.

Use the existing supported local API.

Do NOT monkeypatch global Queue behavior.

Do NOT replace ComfyUI's `/prompt` implementation.

If a supported product-local queue call cannot be established:

```text
STOPPED:
PRODUCT_QUEUE_ROUTING_CONTRACT_NOT_ESTABLISHED
```

---

# 19. No workflow graph swapping

Generate Draft must NOT:

```text
load another workflow into the visible graph
replace the user's current LiteGraph
delete/recreate visible nodes
switch tabs
reload the page
```

Routing happens at prompt preparation/submission level.

The authoring UI stays in place.

---

# 20. Prompt builder source

Use the already-proven PI1 production wiring as the authority.

Historical implementation reference:

`scripts/m3b_pi1_run_production_matrix.py`

specifically its proven canonical/guided API prompt construction.

Do NOT import production runtime from `scripts/`.

Implement production-owned prompt preparation.

---

# 21. Prompt parity

For the same document/seed:

STANDARD product prompt must preserve the relevant API semantics of:

```text
MINIMUM_HAND_MANGA_DRAFT.json
```

GUIDED product prompt must preserve the relevant API semantics of:

```text
MINIMUM_HAND_MANGA_GUIDED_DRAFT.json
```

Add structural parity tests.

---

# 22. STANDARD submitted prompt contract

The actual submitted STANDARD prompt must contain zero:

```text
TegakiMangaGenerationGuideBridge
ControlNetLoader
ControlNetApplyAdvanced
Advanced-ControlNet nodes
effect-mask logic
AnyTest model selector
```

This is mandatory.

---

# 23. GUIDED submitted prompt contract

The submitted GUIDED prompt must include:

```text
TegakiMinimumHandSceneEditor

TegakiMangaConditioningBuilder

TegakiMangaGenerationGuideBridge

ControlNetLoader

ControlNetApplyAdvanced

KSampler

VAEDecode

TegakiMangaFrameOverlay

SaveImage
```

ControlNet parameters remain fixed:

```text
strength = 0.75
start = 0.0
end = 1.0
effect mask = NONE
```

---

# 24. No Advanced-ControlNet

PI2 production prompt must never include:

```text
ACN_AdvancedControlNetApply_v2
Advanced-ControlNet-specific node
mask_optional
effect_mask
```

---

# 25. Model availability behavior

Only after `GUIDED_CLEAN_GLOBAL` is selected may the backend verify the required
ControlNet selector:

`CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

If unavailable:

```text
GUIDED_CONTROLNET_NOT_AVAILABLE
```

Return an explicit error.

Frontend must display the error.

Do NOT fall back silently to STANDARD.

Do NOT download another model.

---

# 26. STANDARD model independence

For `STANDARD_NO_GUIDE`:

Do not require or inspect the AnyTest model.

STANDARD preparation and queueing must remain independent of ControlNet
availability.

---

# 27. Frontend failure behavior

If preparation fails:

```text
do not queue
restore Generate Draft button
show concise visible error
```

No silent fallback.

If queue submission fails:

```text
do not report success
show queue failure
```

---

# 28. Double-submit protection

While preparing/queueing:

```text
Generate Draft:
disabled
```

After success/failure:

```text
Generate Draft:
enabled
```

One click must create at most one prompt submission.

---

# 29. Queue feedback

After successful queue:

show compact feedback such as:

```text
Queued · Standard
```

or:

```text
Queued · Guide-assisted
```

Do not implement a new history system.

Normal ComfyUI history/output handling remains authoritative.

---

# 30. Route-preview helper

Preferred frontend helper file:

`web/js/minimum_hand_generation_route.js`

It may provide:

```text
previewGenerationRoute(document, pageIndex)
```

for display/status only.

Backend remains authoritative at queue time.

---

# 31. Frontend/backend route parity tests

Test both implementations against the same route cases:

```text
no Guides
disabled Guide
enabled Guide / zero Figures
enabled Guide / one unassigned Figure
enabled Guide / multiple Figures
multiple Guides / one eligible
remove Guide
disable -> enable
```

Frontend preview and backend route must agree in all cases.

---

# 32. Schema

Persistent schema remains:

```text
TEGAKI_AUTHORING_DOCUMENT 1.0.0
```

Do not add:

```text
generation_route
guided_mode
controlnet_enabled
controlnet_strength
backend_workflow
```

to the saved document.

Route is derived runtime state.

---

# 33. Workflow files

Do NOT modify production semantics of either PI1 workflow:

```text
workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json

workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json
```

Prefer byte-identical preservation.

PI2 is routing, not backend redesign.

---

# 34. Guide editing preservation

Preserve existing:

```text
Add Guide
Replace Asset
Enable / Disable Guide
Remove Guide
Add Figure
Remove Figure
Figure association
drag / resize
save / reload
```

No Guide editor redesign.

---

# 35. CAST preservation

Automatic backend routing must work independently with:

```text
input_mode = simple

input_mode = cast
```

No CAST-specific routing rule.

CAST regional conditioning remains controlled by the existing document/compiler.

---

# 36. Visual Frame preservation

Visual Panel Frame behavior is unchanged.

Frame overlay remains downstream of generation in both prompt paths.

Do not merge Scene and Frame semantics.

---

# 37. Browser acceptance matrix

Use real browser/computer-use against the live Minimum-Hand product UI.

Required:

### B0 — no Guide

```text
route badge:
Standard

click Generate Draft

submitted route:
STANDARD_NO_GUIDE

ControlNet nodes in submitted prompt:
0

queue:
PASS
```

### B1 — Guide uploaded, zero Figures

```text
route:
STANDARD_NO_GUIDE

queue:
PASS
```

Uploading an image alone must not activate generation influence.

### B2 — enabled Guide + Figures / SIMPLE

```text
route badge:
Guide-assisted

route:
GUIDED_CLEAN_GLOBAL

queue:
PASS
```

### B3 — one-action OFF

From B2:

```text
click Disable Guide once
```

Expected immediately:

```text
route badge:
Standard
```

Then:

```text
Generate Draft
-> STANDARD_NO_GUIDE
-> queue PASS
```

No workflow selection or second OFF action.

### B4 — re-enable

```text
click Enable Guide
```

Expected:

```text
route badge:
Guide-assisted
Generate Draft
-> GUIDED_CLEAN_GLOBAL
-> PASS
```

### B5 — CAST Guided

With active CAST/Character Instances and eligible Guide:

```text
route:
GUIDED_CLEAN_GLOBAL

CAST conditioning:
active

queue:
PASS
```

---

# 38. Persistence browser gate

Save/reload an authoring document with:

```text
Guide enabled + Figures
```

Expected after restore:

```text
route preview:
Guide-assisted
```

Then disable Guide, save/reload:

```text
route preview:
Standard
```

No new persisted routing field may appear.

---

# 39. Browser visual output

For B0/B2/B3/B5 generated outputs require:

```text
rendered output present
no queue error
image quality usable
no hard rectangular ControlNet artifact
```

B2/B5:

```text
Guide influence broadly present
```

Exact placement is not required.

---

# 40. Technical route evidence

For every browser generation record:

```text
document state
eligible Guide count
Figure count
route decision
reason
submitted prompt node-class inventory
prompt_id
queue result
output filename
```

This is required evidence.

---

# 41. API contract tests

Add bounded Python tests for:

```text
valid STANDARD route

valid GUIDED route

disabled Guide -> STANDARD

zero Figures -> STANDARD

unassigned Figure -> GUIDED

multiple Guides -> deterministic route

malformed document -> fail closed

page_index out of range -> fail closed

STANDARD prompt has zero ControlNet nodes

GUIDED prompt has core ControlNet nodes

GUIDED has zero ACN/effect masks

seed propagated from document

frame overlay retained

RAW asset path not consumed by routing
```

---

# 42. Frontend tests

Extend or add bounded JS tests for:

```text
route preview

one-action disable

re-enable

zero-Figure behavior

route badge state

Generate double-click guard state

backend error -> no queue
```

Do not build a broad browser mock framework.

---

# 43. Existing regression

Run:

```text
PI1 Generation Guide Bridge:
12/12 PASS

LR1 contract:
12/12 PASS

LR1 runtime bridge:
5/5 PASS

Guide ops:
PASS

Minimum-Hand frontend:
existing suite PASS

CAST authoring:
PASS

CAST execution:
PASS

document roundtrip:
PASS

recurrent CAST:
PASS
```

---

# 44. PI1 backend preservation

Re-run bounded backend probes establishing:

```text
STANDARD production prompt:
PASS

GUIDED production prompt:
PASS

CLEAN parity:
PASS

Advanced-ControlNet:
0

effect masks:
0
```

Do not repeat LR8 six-seed research.

---

# 45. Evidence directory

Create:

`docs/manga/verification/m3b_pi2/`

Minimum:

```text
M3B_PI2_ROUTE_CONTRACT.json

M3B_PI2_STANDARD_PROMPT_PROVENANCE.json

M3B_PI2_GUIDED_PROMPT_PROVENANCE.json

B0_STANDARD_NO_GUIDE.png

B2_SIMPLE_GUIDED.png

B3_DISABLED_STANDARD.png

B5_CAST_GUIDED.png

M3B_PI2_BROWSER_LEDGER.md

M3B_PI2_VISUAL_LEDGER.md

M3B_PI2_MANIFEST.json
```

Screenshots of route UI states may be included separately.

---

# 46. Product classification

Use exactly one:

```text
PI2_AUTO_ROUTING_INTEGRATED

PI2_AUTO_ROUTING_REJECTED

PI2_AUTO_ROUTING_INCONCLUSIVE
```

---

# 47. PI2_AUTO_ROUTING_INTEGRATED

All required:

```text
backend route contract PASS

frontend/backend route parity PASS

STANDARD prompt contains zero ControlNet dependency

GUIDED prompt matches PI1 backend semantics

one-action Disable Guide -> STANDARD PASS

Enable Guide -> GUIDED PASS

zero Figure -> STANDARD PASS

simple mode PASS

CAST mode PASS

Generate Draft queue integration PASS

no duplicate queue submission

visible failure handling PASS

B0/B1/B2/B3/B4/B5 browser PASS

existing regressions PASS

schema unchanged

PI1 workflow semantics unchanged
```

---

# 48. PI2_AUTO_ROUTING_REJECTED

Use if:

```text
no-Guide route still validates/loads ControlNet

Guide upload alone activates Guided route

Disable Guide requires another user action

frontend route and submitted backend differ

queue integration duplicates jobs

silent fallback occurs

visible workflow graph must be destructively replaced

schema change becomes necessary

PI1 backend semantics must be redesigned
```

---

# 49. PI2_AUTO_ROUTING_INCONCLUSIVE

Use only if route logic works but the local ComfyUI queue contract cannot be
verified strongly enough for product use.

Do not monkeypatch around uncertainty.

---

# 50. Explicit prohibitions

Do NOT:

```text
intercept/replace global ComfyUI Queue application-wide

monkeypatch app.queuePrompt globally

load/swap visible workflow on every generation

modify ComfyUI frontend core

modify ComfyUI server core

change ControlNet strength/timing

reintroduce effect masks

use Advanced-ControlNet

add model selector UI

add ControlNet strength UI

add a second Guide ON/OFF control

change Manga schema

start M4

touch H3

start Shell integration
```

---

# 51. Allowed implementation scope

Expected files approximately:

```text
custom_nodes_custom/tegaki_manga_nodes/product_generation_router.py

custom_nodes_custom/tegaki_manga_nodes/product_generation_api.py

custom_nodes_custom/tegaki_manga_nodes/__init__.py

custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_generation_route.js

custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js

scripts/test_m3b_pi2_product_generation_route.py

scripts/test_m3b_pi2_generation_route.mjs

bounded PI2 browser/evidence helper if needed

PI2 evidence/report

authority/router docs

this Card
```

If implementation expands substantially beyond this:

STOP and report.

---

# 52. STOP conditions

STOP immediately if:

```text
PRODUCT_QUEUE_ROUTING_CONTRACT_NOT_ESTABLISHED

product-local queue requires global ComfyUI monkeypatching

visible graph replacement is required

STANDARD route cannot exclude ControlNet from submitted prompt

GUIDED route cannot preserve PI1 backend semantics

schema change is required

ComfyUI core change is required

same routing root cause fails twice
```

No adjacent exploration.

---

# 53. Report

Create:

`docs/manga/reports/M3B_PI2_MINIMUM_HAND_AUTOMATIC_GUIDE_ROUTING_REPORT.md`

Include:

```text
public PI1 authority SHA

PI1 SOL result:
PI1_BACKEND_INTEGRATED

local queue API contract

route semantics

Guide eligibility

frontend/backend parity

STANDARD prompt provenance

GUIDED prompt provenance

one-action OFF behavior

Generate Draft UI behavior

B0-B5 browser results

simple/CAST results

failure handling

regressions

schema unchanged

production workflow preservation

classification

Final Owner product review:
DEFERRED
```

---

# 54. Manifest minimum

```json
{
  "card": "M3B-PI2",
  "executor": "Gemini 3.8 Flash",
  "pi1_public_sha": "45487bc741a9f6bb1f8025f50a27868fcc1108ae",
  "schema_changed": false,
  "routes": [
    "STANDARD_NO_GUIDE",
    "GUIDED_CLEAN_GLOBAL"
  ],
  "guide_upload_alone_enables_guided": false,
  "one_action_disable": true,
  "frontend_backend_route_parity": "PASS|FAIL",
  "standard_controlnet_dependency": false,
  "guided_controlnet_apply": "ControlNetApplyAdvanced",
  "guided_advanced_controlnet": false,
  "guided_effect_mask": false,
  "queue_integration": "PASS|FAIL",
  "browser": "PASS|FAIL",
  "classification": "INTEGRATED|REJECTED|INCONCLUSIVE",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 55. Routing closeout

At start:

```text
Active Card:
M3B-PI2
```

At successful completion:

move Card byte-identically to:

`docs/manga/cards/completed/`

Set:

```text
Active Card:
NONE
```

Do not start another Card.

---

# 56. Publication semantics

Execution report may record:

```text
M3B-PI2 publication:
LOCAL

Owner push required:
YES
```

Historical wording remains after later publication.

No publication-only follow-up Card.

---

# 57. Required final response

```text
Card:
M3B-PI2

Model:
Gemini 3.8 Flash

Execution baseline:
Final HEAD:
origin/main:

Stage 0:
PASS / FAIL

Latest SOL-reviewed Manga public commit:

PI1 publication:
PASS / FAIL

Schema changed:
NO

Queue API contract:
PASS / FAIL

Generate Draft:
PASS / FAIL

Routes:
STANDARD_NO_GUIDE / GUIDED_CLEAN_GLOBAL

Frontend/backend parity:
PASS / FAIL

No Guide route:
STANDARD_NO_GUIDE / OTHER

Guide + zero Figures route:
STANDARD_NO_GUIDE / OTHER

Guide + Figures route:
GUIDED_CLEAN_GLOBAL / OTHER

Disable Guide one-action route:
STANDARD_NO_GUIDE / OTHER

Re-enable route:
GUIDED_CLEAN_GLOBAL / OTHER

STANDARD ControlNet dependency:
NO / YES

GUIDED ControlNetApplyAdvanced:
PASS / FAIL

Advanced-ControlNet:
NO

Effect mask:
NO

B0 no Guide:
PASS / FAIL

B1 Guide zero Figures:
PASS / FAIL

B2 Simple Guided:
PASS / FAIL

B3 Disable Guide:
PASS / FAIL

B4 Re-enable Guide:
PASS / FAIL

B5 CAST Guided:
PASS / FAIL

Duplicate queue protection:
PASS / FAIL

Visible error handling:
PASS / FAIL

PI1 backend regression:
PASS / FAIL

LR1 regression:
PASS / FAIL

CAST regression:
PASS / FAIL

Minimum-Hand regression:
PASS / FAIL

Production routing provisional classification:
PI2_AUTO_ROUTING_INTEGRATED /
PI2_AUTO_ROUTING_REJECTED /
PI2_AUTO_ROUTING_INCONCLUSIVE

Final Owner product review:
DEFERRED

Evidence:
Manifest:
Report:
Browser ledger:

Stopped early:
YES / NO

Stop reason:

M3B-PI2 publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

---

# 58. Final boundary

PI1 established two working production backends.

PI2 does not redesign them.

PI2 adds only the Minimum-Hand product decision:

```text
Does the current Page have an enabled Rough Guide with Figure geometry?

NO
-> Standard generation

YES
-> Guide-assisted generation
```

The existing `Disable Guide` action is the user's single OFF control.

`Generate Draft` is the single product generation action.

No manual workflow choice.

No ControlNet terminology required in the primary UX.

Complete this routing slice and stop.
