# M3B-PC1 — Production Closure & Cross-Track Integration Boundary Freeze

Date: 2026-09-11 JST
Issuer: Web GPT SOL
Executor: Gemini 3.8 Flash / Antigravity 2.0
Mode: BOUNDED CLOSURE / DOCUMENTATION + REGRESSION ONLY
Final product review: Owner / DEFERRED

Save as:

`ComfyUIPortable/docs/manga/cards/current/M3B_PC1_PRODUCTION_CLOSURE_AND_INTEGRATION_BOUNDARY_FREEZE.md`

---

# 0. Responsibility

This Card has exactly one responsibility:

```text
Close the current M3B production milestone and freeze the Manga-side
integration boundary for later H3/Manga shared-shell design.
```

This is NOT a feature Card.

No new generation architecture.

No shared shell implementation.

---

# 1. Public authority

Latest SOL-reviewed Manga public commit:

`13f76668a264725ea8c6c3a1f6bb012e2d0c326c`

Accepted state:

```text
M3B-LR8:
CORE_GLOBAL_QUALIFIED

M3B-PI1:
PI1_BACKEND_INTEGRATED

M3B-PI2:
PI2_AUTO_ROUTING_INTEGRATED

M3B-PI2-BC1:
PI2_BROWSER_CLOSED

Production backend:
COMPLETE

Automatic product routing:
COMPLETE

M3B-PI2 milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL

Final Owner product review:
DEFERRED
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

Expected SOL-reviewed baseline:

`13f76668a264725ea8c6c3a1f6bb012e2d0c326c`

If origin advanced, inspect:

```bash
git diff --name-status \
  13f76668a264725ea8c6c3a1f6bb012e2d0c326c..origin/main
```

H3-only drift is legal.

Unexpected Manga production changes require STOP.

---

# 3. No implementation by default

Expected product-source changes:

```text
NONE
```

Do not modify:

```text
product_generation_router.py
product_generation_api.py
generation_guide_bridge.py
rough_guide_bridge.py
minimum_hand_scene_editor.js
minimum_hand_generation_route.js

MINIMUM_HAND_MANGA_DRAFT.json
MINIMUM_HAND_MANGA_GUIDED_DRAFT.json
```

This Card audits and freezes their current contracts.

---

# 4. M3B production contract — Standard route

Freeze:

```text
Route:
STANDARD_NO_GUIDE
```

Selected when:

```text
no eligible enabled rough_manga Guide with valid Figure geometry
```

Required invariant:

```text
ControlNet dependency:
NONE
```

The Standard route must not require:

```text
AnyTest model
ControlNetLoader
ControlNetApplyAdvanced
GenerationGuideBridge
Advanced-ControlNet
effect mask
```

---

# 5. M3B production contract — Guided route

Freeze:

```text
Route:
GUIDED_CLEAN_GLOBAL
```

Selected iff:

```text
>= 1 enabled guide_type == rough_manga
AND
>= 1 valid Figure Region
```

Production route:

```text
Authoring Document
-> Figure geometry
-> deterministic CLEAN Guide
-> core ControlNetApplyAdvanced
-> normal Manga conditioning
-> generation
```

Fixed ControlNet configuration:

```text
CN-anytest4_illustrious2_A.safetensors

strength:
0.75

start:
0.0

end:
1.0

effect mask:
NONE

Advanced-ControlNet:
NONE
```

---

# 6. RAW Guide contract

Freeze:

```text
RAW raster:
EDITING / VISUAL REFERENCE ONLY
```

RAW asset pixels must not become the production ControlNet image.

Production CLEAN Guide derives only from validated Figure geometry.

---

# 7. Guide eligibility contract

Freeze exactly:

```text
No Guide
-> STANDARD

Disabled Guide
-> STANDARD

Enabled Guide + zero Figures
-> STANDARD

Enabled Guide + valid Figures
-> GUIDED

Unassigned Figure
-> legal GUIDED input

CAST presence
-> does NOT determine route
```

---

# 8. One-action OFF contract

Freeze:

```text
Disable Guide
-> immediately STANDARD_NO_GUIDE
```

Re-enable:

```text
Enable Guide
-> immediately GUIDED_CLEAN_GLOBAL
```

No second routing toggle.

No ControlNet checkbox in primary UX.

---

# 9. Product generation contract

Freeze the product-facing action:

```text
Generate Draft
```

Status:

```text
Generation: Standard
```

or:

```text
Generation: Guide-assisted
```

Queue-time backend validation remains authoritative.

Frontend status is preview only.

---

# 10. Queue contract

Freeze:

```text
POST /tegaki/manga/generation/prepare
```

as the Manga-owned preparation boundary.

Then product-local ComfyUI queue submission.

Required:

```text
no global Queue monkeypatch
no visible graph swapping
no ComfyUI core modification
```

---

# 11. Persistent schema

Freeze:

```text
TEGAKI_AUTHORING_DOCUMENT 1.0.0
```

Do not persist runtime route fields such as:

```text
generation_route
controlnet_enabled
guided_mode
backend_workflow
```

Route remains derived runtime state.

---

# 12. Semantic boundaries

Record unchanged:

```text
Semantic Scene Region
!=
Visual Panel Frame

CAST
!=
Character Instance

Character Instance area
=
regional text-conditioning area

Guide Figure Region
=
rough visual placement/provenance

Guide
=
Page-owned
```

Do not merge these concepts during future shell work.

---

# 13. Seed contract

Record:

```text
Seed variation is an intentional creative feature.
```

Guide assistance is coarse.

It does NOT promise:

```text
exact pose reproduction
exact Figure tracing
exact camera match
deterministic character count on every seed
```

Production qualification means useful non-destructive assistance, not rigid
layout enforcement.

---

# 14. Known Guided dependency

Record explicitly:

GUIDED route currently depends on the established AnyTest ControlNet model.

If unavailable:

```text
GUIDED_CONTROLNET_NOT_AVAILABLE
```

must remain explicit.

No silent Standard fallback.

No automatic model download.

---

# 15. Output namespace

Current Manga production output remains:

`output/Tegaki`

Do NOT perform an output namespace migration in PC1.

Future migration, if needed, gets a separate Card.

---

# 16. H3 cross-track alignment

Record the current coordination agreement.

Provisional future product-area vocabulary:

```text
TEGAKI
├─ H3
└─ Manga
```

H3 internally owns its own lenses, currently including:

```text
Video
Still
Prep/Edit
```

Do NOT define the future shell as:

```text
Video (H3) / Manga
```

as a fixed architecture.

`H3 / Manga` is only provisional integration vocabulary.

---

# 17. H3/Manga ownership boundary

Manga currently owns:

```text
docs/manga/
workflows/manga/
Manga custom-node product logic
/tegaki/manga/generation/prepare
Manga Authoring Document semantics
Manga production regressions
```

H3 remains separately owned.

Do not merge:

```text
schemas
generation semantics
workflows
server routes
domain regressions
```

---

# 18. Shared runtime statement

Current common boundary:

```text
COMMON COMFYUI RUNTIME
```

This does NOT imply a common domain runtime.

Both product areas may share infrastructure while preserving independently
testable production flows.

---

# 19. Future shell principle

A later shared shell should conceptually:

```text
host / navigate product areas
```

rather than:

```text
merge their internal generation architectures
```

This is a boundary statement only.

Do NOT design the shell implementation in PC1.

---

# 20. Common History/Preview

Ownership is currently:

```text
UNDECIDED FOR FUTURE SHARED SHELL
```

Do not move Manga output/history into H3 History.

Do not create a common History database.

This remains a future integration-design question.

---

# 21. Common launcher

Ownership/design:

```text
UNDECIDED
```

Do not modify launcher files.

Future shared launcher/shell work requires explicit cross-track authorization.

---

# 22. Asset handoff

No new H3↔Manga asset-handoff contract is introduced by PC1.

Record:

```text
CROSS-TRACK ASSET HANDOFF:
NOT DESIGNED
```

H3's internal Still/Video handoffs remain H3-owned.

Manga Guide/CAST assets remain Manga-owned.

---

# 23. H3 Manga

Record:

```text
H3 MANGA:
DEFERRED
```

Current Manga generation is not to be rewritten around H3.

---

# 24. Regression-only verification

Run bounded existing tests.

Required:

```text
PI2 route Python:
PASS

PI2 route JS:
PASS

PI1 Generation Guide Bridge:
PASS

LR1 contract:
PASS

LR1 runtime bridge:
PASS

Guide ops:
PASS

Minimum-Hand:
PASS

CAST authoring:
PASS

CAST execution:
PASS

document roundtrip:
PASS

recurrent CAST:
PASS
```

No GPU generation required.

No Browser replay required.

BC1 is the fresh accepted Browser evidence.

---

# 25. Static production invariants

Verify current repository state:

```text
Standard prompt builder:
0 ControlNet dependencies

Guided prompt builder:
core ControlNetApplyAdvanced

Advanced-ControlNet:
0

effect masks:
0

RAW pixels used by generation bridge:
NO

schema:
1.0.0

production workflows:
present

Manga generation endpoint:
present
```

---

# 26. No unnecessary evidence reproduction

Do NOT rerun:

```text
LR8 12-image matrix
PI1 4-run matrix
PI2 B0-B5 GPU outputs
BC1 Browser B0-B5
```

Those milestones already have accepted evidence.

PC1 is closure, not requalification.

---

# 27. Closure report

Create:

`docs/manga/reports/M3B_PRODUCTION_CLOSURE_AND_INTEGRATION_READINESS_REPORT.md`

The report must summarize, without rewriting historical results:

```text
M3B research progression
LR8 final qualification
PI1 backend integration
PI2 automatic routing
PI2-BC1 real Browser closure
current production contracts
known limitations
shared-area boundary
H3 coordination status
Owner acceptance status
```

---

# 28. Stable integration-boundary document

Create:

`docs/manga/MANGA_PRODUCT_INTEGRATION_BOUNDARY.md`

This becomes the concise Manga-side reference for later cross-track design.

It should contain only:

```text
Manga product entry
Manga-owned endpoint
Manga-owned workflows
persistent schema identity
Standard/Guided routing contract
Guide semantics
queue ownership
shared-runtime assumptions
areas future shell MAY wrap
areas future shell MUST NOT merge implicitly
current readiness
```

Keep it short.

Do not duplicate the full historical roadmap.

---

# 29. Authoritative boundary for future H3 chat

The future H3 command chat should normally need at most:

```text
ComfyUIPortable/GITHUB_MANGA.txt

ComfyUIPortable/docs/manga/MANGA_PRODUCT_INTEGRATION_BOUNDARY.md

ComfyUIPortable/docs/manga/reports/
M3B_PRODUCTION_CLOSURE_AND_INTEGRATION_READINESS_REPORT.md

ComfyUIPortable/docs/manga/STATUS.md
```

No full Manga-history inspection unless a concrete conflict appears.

---

# 30. Integration readiness classification

Use exactly one:

```text
MANGA_NOT_READY_FOR_INTEGRATION_DESIGN

MANGA_READY_FOR_INTEGRATION_DESIGN

MANGA_CLOSURE_BLOCKED
```

---

# 31. MANGA_READY_FOR_INTEGRATION_DESIGN

Requires:

```text
PI1 SOL accepted

PI2 SOL accepted

BC1 SOL accepted

Standard backend contract stable

Guided backend contract stable

automatic routing stable

schema unchanged

real Browser closure PASS

regressions PASS

cross-track ownership boundary documented

no current H3/Manga conflict
```

This means:

```text
ready to DESIGN integration
```

It does NOT mean:

```text
authorized to IMPLEMENT integration
```

---

# 32. M3B closure classification

Use exactly one:

```text
M3B_PRODUCTION_CLOSED

M3B_PRODUCTION_NOT_CLOSED

M3B_PRODUCTION_CLOSURE_INCONCLUSIVE
```

Expected if all gates pass:

```text
M3B_PRODUCTION_CLOSED
```

---

# 33. What M3B_PRODUCTION_CLOSED means

It means the current Minimum-Hand Rough Guide milestone has:

```text
qualified generation influence

production backend integration

automatic product routing

real Browser product closure

bounded regressions
```

It does NOT mean the entire Manga product is finished.

---

# 34. Not part of M3B closure

Explicitly exclude:

```text
shared TEGAKI shell
H3 integration
common History
common launcher
output namespace migration
advanced Pose workflow
SubScene refinement
inpaint/refinement expansion
H3 Manga
final Owner production acceptance
```

---

# 35. Current Owner state

Always preserve:

```text
Final Owner product review:
DEFERRED
```

Do not convert SOL technical acceptance into Owner acceptance.

---

# 36. Cross-track timing

H3 currently reports:

```text
PARTIAL INTEGRATION READY
```

with IP2 Browser Prep/Edit closure still underway.

Therefore even if Manga becomes:

```text
MANGA_READY_FOR_INTEGRATION_DESIGN
```

PC1 must state:

```text
SHARED-SHELL IMPLEMENTATION:
NOT AUTHORIZED
```

Recommended coordination:

```text
wait for H3 IP2 browser closure
then perform one new cross-track status exchange
then decide whether a bounded shared-shell IA Card is warranted
```

---

# 37. Astra

Do NOT invoke Astra for PC1.

Reason:

```text
No unresolved architecture conflict exists.
This is a bounded closure and contract-freeze task.
```

If the later H3/Manga shared-shell design presents genuine multi-domain
architecture conflicts, Astra may be considered under the separate current
Astra usage policy.

---

# 38. Allowed changes

Expected:

```text
docs/manga/MANGA_PRODUCT_INTEGRATION_BOUNDARY.md

docs/manga/reports/
M3B_PRODUCTION_CLOSURE_AND_INTEGRATION_READINESS_REPORT.md

M3B-PC1 Card

authority/status/router docs
```

Tests should preferably remain unchanged unless a factual closure invariant
cannot currently be checked.

No production feature source changes.

---

# 39. STOP conditions

STOP if:

```text
accepted PI2 production code has changed unexpectedly

schema drift is found

Standard path now depends on ControlNet

Guided path no longer matches PI1 contract

BC1 evidence is unavailable/inconsistent

a source fix becomes necessary

a shared-shell design decision becomes necessary

H3 files must be modified
```

Do not repair these inside PC1.

Report the blocking fact.

---

# 40. Authority closeout

If successful, update CURRENT AUTHORITY to:

```text
Latest SOL-verified Manga public commit:
13f76668a264725ea8c6c3a1f6bb012e2d0c326c

M3B-PI1:
PUBLISHED / SOL REVIEWED / PI1_BACKEND_INTEGRATED

M3B-PI2:
PUBLISHED / SOL REVIEWED / PI2_AUTO_ROUTING_INTEGRATED

M3B-PI2-BC1:
PUBLISHED / SOL REVIEWED / PI2_BROWSER_CLOSED

M3B:
PRODUCTION CLOSED

Manga integration readiness:
READY FOR INTEGRATION DESIGN

Shared-shell implementation:
NOT AUTHORIZED

Final Owner product review:
DEFERRED

Active Card:
NONE
```

Historical LOCAL statements remain unchanged.

---

# 41. Routing

At start:

```text
Active Card:
M3B-PC1
```

On successful completion:

move Card byte-identically to:

`docs/manga/cards/completed/`

Then:

```text
Active Card:
NONE
```

Do not start M4.

Do not start shared-shell work.

---

# 42. Publication semantics

Execution report may state:

```text
Publication:
LOCAL

Owner push required:
YES

Commit/push:
NOT PERFORMED
```

Gemini does not self-accept this closure.

---

# 43. Required final response

```text
Card:
M3B-PC1

Model:
Gemini 3.8 Flash

Execution baseline:
Final HEAD:
origin/main:

Stage 0:
PASS / FAIL

Latest SOL-reviewed Manga public commit:
13f76668a264725ea8c6c3a1f6bb012e2d0c326c

PI1 authority:
PASS / FAIL

PI2 authority:
PASS / FAIL

PI2-BC1 authority:
PASS / FAIL

Schema:
UNCHANGED / OTHER

Standard route contract:
PASS / FAIL

Standard ControlNet dependency:
NO / YES

Guided route contract:
PASS / FAIL

Guided core ControlNet:
PASS / FAIL

Advanced-ControlNet:
NO

Effect mask:
NO

RAW generation input:
NO

One-action Guide OFF:
PRESERVED / FAIL

Generate Draft:
PRESERVED / FAIL

Manga endpoint:
PASS / FAIL

Production workflows:
PASS / FAIL

Automated regressions:
PASS / FAIL

GPU generation rerun:
NOT PERFORMED

Browser rerun:
NOT PERFORMED

Current H3/Manga conflict:
NONE / <details>

M3B closure provisional classification:
M3B_PRODUCTION_CLOSED /
M3B_PRODUCTION_NOT_CLOSED /
M3B_PRODUCTION_CLOSURE_INCONCLUSIVE

Manga integration readiness:
MANGA_READY_FOR_INTEGRATION_DESIGN /
MANGA_NOT_READY_FOR_INTEGRATION_DESIGN /
MANGA_CLOSURE_BLOCKED

Shared-shell implementation:
NOT AUTHORIZED

Final Owner product review:
DEFERRED

Integration boundary:
<path>

Closure report:
<path>

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

# 44. Final instruction

Do not add another feature.

Freeze the current Manga production boundary.

The desired successful result is:

```text
M3B_PRODUCTION_CLOSED

MANGA_READY_FOR_INTEGRATION_DESIGN

SHARED-SHELL IMPLEMENTATION:
NOT AUTHORIZED
```

This means Manga can later participate in an H3/Manga integration-design
discussion without reopening its internal production architecture.

Complete the closure evidence and stop.
