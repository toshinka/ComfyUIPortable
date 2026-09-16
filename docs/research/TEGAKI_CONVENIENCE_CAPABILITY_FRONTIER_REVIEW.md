# TEGAKI Convenience Capability Frontier Review

Status: RESEARCH / PRODUCT-FIT FRONTIER REVIEW
Review date: 2026-09-16 JST
Priority: lower than core Manga product completion

This document consolidates the supplied Commander/WebGPT convenience-tool
survey into a TEGAKI product-fit review. It is not an extension shopping list.
It is not implementation authority, runtime authority, UI composition
authority, dependency authorization, or a main-roadmap priority change.

Convenience capabilities must not displace resources required for Manga
controllability, MRP / Regional, Guide / ControlNet, Reference Appearance,
CAST, Astra-reviewed production UI, or other higher-priority core work.

## 1. Product philosophy

Convenience should reduce authoring friction, not become another authoring
task.

High-fit convenience capabilities tend to:

- remove memory work;
- remove search work;
- remove small input errors;
- remove repetitive file or resource work;
- make comparison easier;
- make recovery safer;
- appear only when needed.

Low-fit capabilities tend to:

- generate more ideas than requested;
- add a second operation system;
- add large persistent panels;
- create new management work;
- force users to learn provider-specific concepts;
- duplicate an existing owner.

The main-surface test is whether a capability helps the author express and
inspect an existing intention with less friction. A capability that creates a
new task, vocabulary, or management surface needs a stronger justification.

## 2. Product-fit evaluation model

This review uses a qualitative model for TEGAKI only:

BENEFIT

minus:

- learning cost;
- persistent UI cost;
- new concept cost;
- dependency cost;
- ownership duplication;
- maintenance cost.

No numeric scores are assigned, and external projects are not ranked
globally. A capability can be useful in the ecosystem and still be a poor fit
for TEGAKI's primary authoring surface.

## 3. Top-level capability families

The convenience frontier is organized into five families:

### Recovery

Recover previously known state or missing context.

### Lookup

Find known resources or information with less friction.

### Inspection

Understand differences and results more easily.

### Safety

Prevent or recover from accidental loss or destructive action.

### Human Gate

Pause before an expensive or consequential next stage and return control to
the author.

## 4. Classification labels

The classifications used in this document are:

| Label | Meaning |
| --- | --- |
| PRODUCT CANDIDATE | Fits TEGAKI directly if a later need and resource budget justify it |
| SEPARATE SURFACE | Valuable, but should not crowd Create or primary authoring |
| PATTERN ONLY | Learn from an external behavior without adopting it as a subsystem |
| DEFER | Potentially valuable, but current resources have no justification |
| REJECT / LOW FIT | Conflicts with product philosophy or duplicates stronger ownership |

A row may have a primary classification and a priority note. Product candidate
does not mean immediate implementation.

## 5. Result provenance and replay

Classification: PRODUCT CANDIDATE / DEFERRED IMPLEMENTATION.

The authority for this topic is:

docs/architecture/TEGAKI_RESULT_PROVENANCE_REPLAY_ARCHITECTURE.md

That architecture already defines the intended boundary. The concise product
fit conclusion is:

- generation evidence should be recoverable;
- recovery remains proposal-only;
- exact resource identity remains strict;
- Result provenance is not full TEGAKI Authoring state;
- Asset and Lineage are later work.

This review does not duplicate that architecture, authorize a provenance
writer, or create a replay UI.

## 6. Missing-resource assistance

Classification: PRODUCT CANDIDATE / DEFERRED IMPLEMENTATION.

Ownership must remain split:

STRICT RESOURCE RESOLUTION answers:

“What exact resource is required and is it present?”

MISSING RESOURCE ASSISTANCE answers:

“How can the user obtain that exact missing resource?”

The second capability must never weaken the first. A future helper could
provide exact filename or identity awareness, hash verification where
available, present-but-renamed detection, clear missing or unresolved
diagnostics, and an explicit download or import choice.

Unsafe behavior includes:

- silent fuzzy substitution;
- automatic replacement with a similar model;
- rewriting requested resource identity without approval.

No download implementation or automatic replacement is authorized by this
review.

## 7. External missing-resource references

The following are supplied design references only.

### 21omen / ComfyUI-ModelResolver

Strong reference patterns:

- active graph analysis;
- ignoring irrelevant, muted, or bypassed paths;
- exact identity orientation;
- checksum verification;
- present-but-renamed detection;
- safe resumable acquisition.

Interpretation: STRICT ACQUISITION REFERENCE.

It is not a mandatory dependency and does not own TEGAKI catalog semantics.

### Azornes / Comfyui-Model-Resolver

Strong reference patterns:

- provider abstraction;
- multi-provider diagnostics;
- download queue;
- resource-resolution UX;
- distinct failure states.

Interpretation: PROVIDER / DOWNLOAD UX TEACHER.

Fuzzy matching and automatic workflow updating do not automatically fit
TEGAKI's strict identity rules.

## 8. Model / LoRA library

Classification: SEPARATE SURFACE.

A Model / LoRA library may provide:

- preview;
- trained or trigger words;
- base model;
- recommended strength;
- source and provider information;
- hash;
- notes;
- favorite;
- usage hints.

These are useful LOOKUP functions. Create authoring should show only resource
controls relevant to the current task. Deep browsing and metadata management
belong in a secondary Library / Manager surface rather than becoming a full
model-management UI inside Create.

## 9. LoRA Manager lessons

The supplied LoRA Manager findings are design references. Useful lessons
include rich local metadata, previews, trained words, recommended strength,
notes, favorites, source/provider distinction, hash identity, and an
independent /loras-style management surface.

The LoRA Manager custom loader must not become TEGAKI product authority, and
its full recipe system must not be copied automatically. External code reuse,
external implementation adoption, and design inspiration are separate
decisions; this review makes no legal conclusion.

## 10. Recipe concept

Classification: PATTERN ONLY / POSSIBLE REDUNDANCY.

The underlying need is real: preserve a good combination of LoRAs, weights,
prompt fragments, and generation settings. TEGAKI already has or plans
ownership around Replay, Prompt Preset, LoRA selection, and Result / History.

Do not introduce a new Recipe product concept unless future evidence shows
that those owners cannot express the need cleanly.

## 11. Resource dependency insight

Classification: SEPARATE SURFACE / LONGER-PATH PRODUCT CANDIDATE.

A future dependency view could answer:

- Which saved results or workflows depend on this model?
- Is this LoRA still referenced?
- Which resources appear unused?
- Are these files duplicates?

This is different from resource acquisition. A possible relationship is:

Result Provenance -> resource references

Resource Dependency Index -> reverse lookup from resource to results/assets

Potential value includes safer cleanup, reduced duplicate storage, and better
understanding before deleting resources. Resource deletion management is not
implemented or authorized.

## 12. Resource hygiene references

Supplied tools such as combuddy and advanced-model-manager demonstrate useful
patterns:

- resource/workflow dependency graphs;
- unused-resource detection;
- duplicate detection;
- safe or recoverable deletion concepts;
- workflow-required-resource inventories;
- safe move and copy behavior.

These patterns do not authorize importing large model-manager dashboards,
provider browsers, repository browsers, or persistent download panels into
primary authoring.

## 13. Result A/B comparison

Classification: PRODUCT CANDIDATE.

Useful future behaviors include previous versus current, adopted result versus
candidate, and before versus after refinement. Possible modes are toggle,
slider, and side-by-side, with an optional difference view later.

Comparison belongs to Preview / Result inspection. It should appear only when
requested and should not reserve permanent Create screen space.

## 14. Candidate result selection

Classification: CONDITIONAL PRODUCT CANDIDATE WHEN MULTI-RESULT GENERATION
EXISTS.

The useful pattern is:

GENERATE MULTIPLE CANDIDATES

-> HUMAN SELECTS ONE

-> ONLY SELECTED RESULT CONTINUES

This becomes valuable if TEGAKI later generates multiple candidates. Candidate
management UI should not be created before that need exists.

## 15. Human gate

Classification: PATTERN ONLY NOW / HIGH-VALUE FUTURE PIPELINE PRINCIPLE.

The principle is:

EXPENSIVE NEXT STEP

-> HUMAN APPROVAL

-> CONTINUE

For example:

generation -> Preview -> user approval -> upscale/refine/detail pass

This can avoid wasted GPU time, prevent unwanted downstream work, and keep
authority with the author. It does not authorize pause nodes, a Retry Manager,
or a merged Manga/H3 runtime architecture. Manga and H3 remain separate even
when they share the same human-gate principle.

## 16. Recent / pinned reference

Classification: PRODUCT CANDIDATE.

This is useful for Reference Appearance, Guide images, and future Asset
selection. A compact selection pattern is:

CURRENT ATTACHMENT

when selecting:

RECENT / PINNED / BROWSE

The feature should reduce repeated file picking without adding a new
management task. An always-visible full asset browser is a poor default.

## 17. FileHub lesson

The supplied FileHub pattern is an INPUT UX REFERENCE:

- recent files;
- a small number of pinned files;
- search or browse only when opened;
- drag and drop.

Do not adopt a full FileHub subsystem by default.

## 18. Clipboard image paste

Classification: PRODUCT CANDIDATE / LOW PRIORITY.

Future Attachment inputs may reasonably accept:

DROP / CHOOSE / PASTE

This has high explanatory value and little persistent UI cost. It is not
implemented now.

## 19. Result keep / favorite

Classification: DEFER.

The minimal value is preventing a useful temporary result from being cleaned
up. Do not create albums, ratings, a complex favorites database, collections,
or tag taxonomies unless later Asset/History requirements justify them.

A future distinction such as temporary KEEP versus formal ASSET ADOPTION may
be useful, but terminology is not frozen here.

## 20. Predictable result organization

Classification: PATTERN ONLY / BACKGROUND PRODUCT CANDIDATE.

Results should have predictable identity and location. Product context such as
project, page, Scene, and result may become useful owners when those owners
exist. Avoid making authors learn complex filename-template languages.

This review does not define filesystem architecture.

## 21. Autocomplete

Classification: CURRENT DIRECTION / HIGH FIT.

The current Manga autocomplete direction is a strong product fit because it
removes small input errors without changing author intent. Preserve:

- incremental completion;
- canonical Danbooru tag conversion;
- aliases;
- language-to-canonical lookup;
- duplicate-tag suppression;
- light formatting.

Related-tag ideation needs caution, and AI prompt expansion has a different,
lower-fit role. Autocomplete should help the user express what they already
intend, not continuously propose a different creative direction.

## 22. Related tags

Classification: DEFER / DEFAULT-OFF CANDIDATE.

Autocomplete finishes or corrects intended input. Related suggestions
introduce adjacent ideas. The latter may increase cognitive noise.

If ever adopted, related tags should be hidden by default or require explicit
opt-in. No implementation is authorized.

## 23. Minimal prompt preset

Classification: PRODUCT CANDIDATE / LOW COMPLEXITY.

A small preset function lets a user save a useful text fragment and search or
select it later for insertion. Examples include a common negative fragment, a
lighting phrase, background simplification, or a frequent composition phrase.

It should not require AI expansion, a large style-card gallery, a preset
programming language, or another full prompt workspace.

## 24. Wildcard management

Classification: CURRENT CORE + MINIMAL FUTURE UI.

Wildcard runtime/core already exists. A future management surface may provide
only search, preview, and add/edit. Avoid another large wildcard subsystem
unless future evidence justifies it.

## 25. Control and combo filtering

Classification: PATTERN ONLY / IMPORTANT UI PRINCIPLE.

External filtering tools demonstrate that a broad backend need not expose every
choice in ordinary UI. Potential applications include samplers, schedulers,
Guide preprocessors, and advanced resource options.

HIDE COMPLEXITY WITHOUT DESTROYING CAPABILITY.

Existing saved or advanced values should remain representable even when hidden
from Basic UI. This is a UI principle, not authorization for a new filtering
subsystem.

## 26. Pin-frequently-used-controls lesson

Classification: PATTERN ONLY.

External pin-input tools show that a complex backend does not require all
controls to be visible. TEGAKI Create UI already owns this abstraction.

Do not add another pin-controls subsystem unless evidence requires
user-customizable pinning.

## 27. Autosave and version snapshot

Classification: PATTERN ONLY / FUTURE INTERNAL SAFETY.

ComfyUI and external tools demonstrate autosave and version-history patterns.
TEGAKI should not create a second workflow manager for this.

If future AuthoringDocument editing needs recovery, a small internal
return-point or safety snapshot should be owned by the AuthoringDocument
subsystem. No separate management product is required by this review.

## 28. Error retry

Classification: DEFER.

Do not create a Retry Manager subsystem. If evidence later shows a need,
small actions such as Retry same resolved request should belong to existing
Generation Status / Journal ownership.

## 29. Full Gallery or DAM

Classification: REJECT AS PRIMARY PRODUCT SURFACE / REFERENCE ONLY.

Useful ideas can be extracted:

- compare;
- metadata search;
- lineage;
- keep/favorite;
- asset inspection.

Reject importing the whole interaction model into Create. TEGAKI should not
become a second Digital Asset Management application unless actual production
requirements later demand it.

## 30. Full model manager

Classification: REJECT AS PRIMARY PRODUCT SURFACE / SEPARATE-SURFACE IDEAS
ONLY.

Useful parts include resource lookup, preview, metadata, dependency
diagnostics, and missing-resource resolution.

Do not import into primary authoring:

- repository browsing;
- provider catalog browsing;
- large dashboards;
- manual filesystem management;
- persistent downloader controls.

A secondary surface may later carry selected lookup or diagnostics functions.

## 31. AI prompt expansion

Classification: REJECT / LOW FIT.

Unrequested expansion changes the task from expressing user intent into
reviewing generated ideas. It increases cognitive branching, visual
suggestion noise, and authoring interruption.

Optional external experimentation is not prohibited, but AI prompt expansion
should not become a TEGAKI core convenience direction.

## 32. Large prompt workbench

Classification: REJECT / LOW FIT.

Avoid requiring authors to manage style grids, large recipe panels, prompt
modularization systems, prompt-flow programming, or complex preset trees.
Small reusable fragments and autocomplete address the high-value low-cost
portion.

## 33. Custom-node dependency management

Classification: REJECT AS TEGAKI PRODUCT CAPABILITY.

ComfyUI ecosystem tooling already owns much of custom-node installation,
dependency resolution, and environment diagnostics. TEGAKI should minimize
unnecessary dependencies.

CORE FIRST.

EXTERNAL DEPENDENCY ONLY WHEN VALUE IS CLEAR.

## 34. Surface model

The convenience frontier has three presentation levels:

### Primary authoring

Low-noise controls necessary for the current creative act.

### Secondary surface

Library, Asset, and resource-management functions opened intentionally.

### Contextual or ephemeral

Compare, Replay, missing-resource dialog, Recent/Pinned chooser, and human
approval. These appear only when triggered by context.

This separation prevents a useful convenience from becoming a permanent
authoring burden.

## 35. Short-verb test

High-fit convenience functions often reduce to obvious verbs:

RECENT / PIN / PASTE / COMPARE / KEEP / RESTORE / RETRY / CONTINUE

This is not a formal requirement. If a capability needs a long explanation
before the user can benefit, its primary-surface fit should be questioned.

## 36. Astra handoff boundary

This document may later be provided to Astra as product-fit evidence. Astra
should not be asked to rediscover the external tool universe.

Later Astra may judge which candidate conveniences deserve visible UI, which
belong on secondary surfaces, which should remain hidden or contextual, and
whether any candidate conflicts with Create composition.

The current Astra priority remains core production UI review. Convenience
features must not dominate that review.

Bounded future Astra questions:

1. Which convenience capabilities can remain entirely invisible until
   triggered?
2. Which belong outside Create?
3. Which existing product surfaces can absorb them without a new navigation
   concept?
4. Are any candidates redundant with Result, Asset, Attachment, or Generation
   Status ownership?
5. Which should explicitly not be represented in the initial production UI?

These are questions, not final UI composition decisions.

## 37. Product candidate summary

| Capability | Product-fit classification |
| --- | --- |
| Result Provenance / Replay | PRODUCT CANDIDATE / DEFERRED |
| Missing Resource Assistance | PRODUCT CANDIDATE / DEFERRED |
| Model / LoRA Library | SEPARATE SURFACE |
| Resource Dependency Insight | SEPARATE SURFACE / LONGER PATH |
| A/B Compare | PRODUCT CANDIDATE |
| Candidate Result Selection | CONDITIONAL PRODUCT CANDIDATE |
| Human Gate | PATTERN ONLY NOW |
| Recent / Pinned Reference | PRODUCT CANDIDATE |
| Clipboard Paste | PRODUCT CANDIDATE / LOW PRIORITY |
| Result Keep | DEFER |
| Predictable Result Organization | PATTERN / BACKGROUND |
| Autocomplete | CURRENT HIGH FIT |
| Related Tags | DEFER / DEFAULT-OFF CANDIDATE |
| Minimal Prompt Preset | PRODUCT CANDIDATE |
| Wildcard Management | MINIMAL FUTURE UI |
| Combo Filtering | PATTERN ONLY |
| Autosave / Snapshot | FUTURE INTERNAL SAFETY |
| Full Gallery / DAM | REJECT AS PRIMARY SURFACE |
| Full Model Manager | REJECT AS PRIMARY SURFACE |
| AI Prompt Expansion | REJECT / LOW FIT |
| Large Prompt Workbench | REJECT / LOW FIT |
| Custom Node Dependency Manager | REJECT AS TEGAKI PRODUCT CAPABILITY |

## 38. No roadmap conversion

This is a capability frontier review, not a roadmap. Do not schedule
implementation, assign phases, or convert every PRODUCT CANDIDATE into a
backlog commitment.

Candidate means architecturally and product-wise plausible if a future need
and resource budget justify it. It does not override current product
priorities.

## 39. Current project priority

Core Manga completion remains more important than this entire
convenience-capability set.

No convenience feature in this document overrides:

- MRP;
- Guide;
- Reference Appearance;
- CAST;
- core generation reliability;
- Astra-reviewed production UI.

## 40. Frontier conclusion

The strongest TEGAKI convenience capabilities remove reconstruction, lookup,
comparison, and small-input work. The best convenience features are often
contextual rather than persistent.

Model and resource management has value, but full manager UIs do not belong in
primary authoring. Result/Replay and missing-resource assistance have strong
architectural fit but remain deferred. Result inspection should appear only
when requested. Reference selection benefits from Recent, Pinned, and Paste
patterns. Prompt assistance should correct or complete intent rather than
expand it unsolicited.

Full Gallery, full Model Manager, AI prompt expansion, and large prompt
workbenches are poor primary-surface fits. Convenience research is sufficiently mature to close this frontier for now.

No implementation is authorized.

## 41. Document boundary and validation

This Card creates one research document only. It does not modify product
source, tests, fixtures, UI, status, capability-bank documents, reserve
documents, or existing architecture/research/UI authority. It performs no
runtime, GPU, generation, /prompt, network, internet research, model
download, or dependency installation.

Validation is limited to exact start-state and final-state checks, one-file
scope checks, and git diff --check. Product tests are not required for this
documentation-only pass.

Suggested local commit:

docs: record TEGAKI convenience capability frontier review

Push is forbidden.
