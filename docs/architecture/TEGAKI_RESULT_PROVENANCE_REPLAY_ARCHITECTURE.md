# TEGAKI Result Provenance / Replay Architecture

Status: DEFERRED CONVENIENCE CAPABILITY
Review date: 2026-09-16 JST
Authority: future architecture / convenience capability design

This document records a possible way for TEGAKI to preserve and later recover
generation provenance. It is a design note only. It is not production runtime
authority, UI composition authority, a main roadmap priority, an Astra
replacement, or implementation authorization.

## 1. Product intent

A Manga page that was generated earlier may be worth revisiting. The useful
question is not only what the image is, but which settings and resources
produced it and which production context was known at the time. A future
provenance/replay capability should let an author recover enough context to
try that state again without remembering or manually reconstructing every
setting.

The primary philosophy is:

REMOVE MEMORY / RECONSTRUCTION WORK

It is not:

ADD A NEW COMPLEX WORKFLOW

This convenience must not consume implementation capacity needed for Manga
controllability, regional/MRP work, Guide/ControlNet, Reference Appearance, or
the Astra-reviewed Create UI.

## 2. Replay levels

Replay has three distinct levels. A lower level can be useful even when the
next level is unavailable.

### Level A — Settings replay

This is the near-term useful target. A recovered proposal may contain:

- positive prompt;
- negative prompt;
- checkpoint;
- LoRA list and strengths;
- seed;
- steps;
- CFG;
- sampler;
- scheduler;
- width;
- height.

Settings replay can reproduce a request shape while still requiring current
catalog revalidation and an explicit user decision.

### Level B — Workflow replay

This level may preserve a ComfyUI workflow, prompt graph, generation path, and
runtime-oriented provenance. It can improve fidelity to the original graph,
but it is not the same as TEGAKI authoring state and does not automatically
restore authoring semantics.

### Level C — TEGAKI authoring replay

This longer-path level could eventually include CAST references, Reference
Appearance, Guide state/references, MRP / Scene / Region intent, page and Scene
context, authoring document linkage, and asset lineage. Level C does not
currently exist and must not be claimed as present.

## 3. Existing TEGAKI building blocks

The current pieces have intentionally different responsibilities:

| Building block | Current role | Boundary |
| --- | --- | --- |
| Result Metadata Recovery | Reads bounded generation evidence from an existing PNG | Read-only evidence recovery; no apply or generation |
| Settings Import Proposal | Converts recovered hints into reviewable field candidates | Proposal-only; no authoring mutation |
| Strict Catalog / Resource Resolution | Decides whether an exact checkpoint, LoRA, sampler, or scheduler is available | Resource identity authority; no metadata enrichment |
| Model / LoRA Metadata Enrichment | Reads bounded safetensors header metadata for an already resolved resource | Descriptive metadata only; not catalog authority |
| Result / History | Owns Manga job facts, state, prompt identity, and verified output locator | Execution/history ownership; not a future Asset schema |
| Future Result-to-Asset | Possible adoption boundary for a result intentionally reused in production | Reserve concept; no Asset or lineage schema today |

These responsibilities must not be merged into one provenance service.

### 3.1 Result Metadata Recovery

manga/service/result_metadata_recovery.mjs is a bounded, read-only PNG reader.
It recognizes PNG textual chunks, preserves raw metadata entries, parses
prompt/workflow JSON where valid, and derives conservative hints from supported
ComfyUI graph nodes. It can retain file dimensions, prompts, checkpoint and
LoRA references, sampler, scheduler, steps, CFG, seed, and latent dimensions
when the evidence is explicit and consistent. It reports malformed,
conflicting, absent, or unsupported evidence rather than guessing.

It does not decode pixels, execute a workflow, write files, contact a backend,
or select a resource.

### 3.2 Settings Import Proposal

manga/service/result_settings_import.mjs converts a validated recovery result
into a deterministic proposal object. The current field set includes prompts,
checkpoint, LoRAs, seed, steps, CFG, sampler, scheduler, width, height, and
dimensions. Each field retains provenance, evidence class, warnings, and
readiness. Resource fields require caller-provided strict availability facts;
missing, stale, conflicting, and unsupported values remain unresolved.

The reserve contract explicitly has no document mutation, catalog mutation,
file write, queue, network, /prompt call, GPU work, or generation.

### 3.3 Strict catalog and resource resolution

The Manga catalog remains the only authority for exact resource identity.
Future replay must preserve canonical identifiers and revalidate them at the
time a user chooses to apply a proposal. A recovered basename, display title,
or stale path is evidence, not permission to select a different resource.

### 3.4 Model / LoRA metadata enrichment

custom_nodes_custom/tegaki_manga_nodes/model_lora_metadata.py reads only the
bounded safetensors header for an already catalog-resolved CHECKPOINT or LORA.
It preserves raw embedded metadata and normalizes explicitly established
fields such as base model, trigger words, source, and embedded hash. It does
not scan model trees, accept a browser path, compute a full payload hash, load
tensors, or change catalog identity. Its metadata is descriptive and must not
become replay or resource authority.

### 3.5 Result and History ownership

Manga execution facts are currently owned by GenerationJournal and the
generation service. A journal record binds a Manga job_id to request identity,
graph digest, effective settings, prompt_id, state, and a validated
Manga/Playable PNG output locator. Backend history is consulted to verify the
owned result. This execution record is a useful provenance input, but it is
not an Asset model and does not merge Manga and H3 timelines.

## 4. Proposal-only principle

Recovery must retain the existing proposal-only direction:

READ -> NORMALIZE -> RESOLVE -> PROPOSE -> USER DECIDES

Allowed future behavior includes showing recovered values, showing differences
from current settings, showing availability, showing missing or ambiguous
resources, and allowing an explicit user-selected import of individual fields.

The architecture does not authorize:

- silent overwrite of current authoring state;
- silent checkpoint substitution;
- basename guessing;
- automatic fallback resource selection;
- automatic prompt flattening;
- automatic AuthoringDocument mutation;
- automatic generation after recovery.

Recovered evidence may be useful even when no field is safe to apply.

## 5. Provenance write direction

TEGAKI currently has recovery-oriented capability. A complementary future
RESULT PROVENANCE WRITER could intentionally record normalized evidence at
generation time so later recovery is more reliable.

Potential information classes are:

- generation settings;
- exact resource identity;
- resource hashes where appropriate;
- workflow information;
- a TEGAKI product/domain marker;
- result identity;
- future parent/source relationships.

The writer is not implemented or authorized here. Its output must remain
evidence that a later reader can classify; it must not bypass strict catalog
resolution or proposal-only import.

## 6. Storage channels

Three channels are complementary. No requirement is made to implement all
three.

### A. Embedded media metadata

Advantages:

- travels with the media;
- enables simple single-file recovery;
- can be read when no TEGAKI journal is present.

Failure modes:

- editing, conversion, or export tools may strip metadata;
- metadata size and format support may be limited;
- a copied image can lose its original production context.

### B. Sidecar metadata

Advantages:

- can preserve larger or more structured provenance;
- can survive media metadata stripping;
- can carry workflow and lineage details without changing image encoding.

Failure modes:

- the sidecar can become detached or renamed;
- portability depends on a stable pairing rule;
- external tools may not move it with the media.

### C. TEGAKI internal record or journal

Advantages:

- supports TEGAKI-native result identity, lineage, and asset relationships;
- can retain operational facts beyond a media file.

Failure modes:

- the record may not travel with an exported image;
- cleanup, migration, or workspace changes can break the association;
- internal ownership must remain separate for Manga and H3.

The future architecture can choose a primary channel and optional companions
after a bounded writer/recovery decision.

## 7. PNG and WebP policy

PNG remains an acceptable provenance carrier and compatibility baseline. The
architecture must not require a format migration before replay is useful. PNG
may remain the only implemented embedded-metadata format for a long time.

WebP is only a FUTURE FORMAT CANDIDATE. Storage efficiency may eventually make
it attractive for generated Manga results if provenance retention is reliable,
but:

- WebP is not a requirement;
- WebP is not a current implementation priority;
- WebP must not block provenance/replay design;
- WebP must not consume resources before core Manga work.

Based on the inspected local evidence, current WebP provenance capability is
UNKNOWN. No WebP support or feasibility testing is implemented here, and no
WebP internals were researched.

The core replay contract should remain media-format-independent. Embedded PNG,
possible future embedded WebP, sidecar JSON, and future formats should
normalize into the same recovery/proposal pipeline without encoding WebP-only
fields in that contract.

## 8. Conceptual provenance envelope

The following categories describe a possible normalized envelope. They are
conceptual categories, not a schema and not one giant mandatory object. The
envelope must allow partial evidence.

### Result identity

- result identity;
- created time;
- domain;
- media format;
- dimensions.

### Generation settings

- positive prompt;
- negative prompt;
- seed;
- steps;
- CFG;
- sampler;
- scheduler.

### Resource references

- exact checkpoint identity;
- LoRA identities and weights;
- optional resource hashes;
- availability state as observed by a later resolver.

### Workflow evidence

- raw workflow;
- prompt graph;
- source metadata.

### TEGAKI future context

- page;
- Scene / Region intent;
- CAST;
- Reference Appearance;
- Guide;
- authoring snapshot reference.

### Lineage

- source result;
- parent result;
- derived result;
- asset linkage.

Each category may be absent, partial, conflicting, or unsupported. Raw evidence
must not be overwritten by a normalized guess.

## 9. Raw evidence versus normalized data

The architecture keeps five representations separate:

1. RAW SOURCE EVIDENCE — bytes, metadata entries, workflow JSON, prompt graph,
   and source identifiers as recovered;
2. NORMALIZED RECOVERY — conservative fields extracted from that evidence;
3. RESOURCE AVAILABILITY — an independent answer from strict resolution;
4. IMPORT PROPOSAL — reviewable candidates with provenance and warnings;
5. PROVENANCE / LINEAGE — relationships among results, sources, and future
   adopted assets.

A parser may understand more of raw evidence in the future. Discarding raw
evidence after current normalization would make that evolution harder.

## 10. Recovery pipeline

The conceptual recovery flow is:

MEDIA / RESULT

-> inspect available embedded metadata

-> inspect optional sidecar or internal evidence

-> RAW EVIDENCE

-> Result Metadata Recovery

-> normalized recovered fields

-> Strict Resource Resolution

-> Settings Import Proposal

-> user review

-> optional explicit apply later

Missing, conflicting, stale, and ambiguous fields remain visibly unresolved.
The pipeline never turns an unavailable resource into a fallback selection.

## 11. Resource replay and missing-resource assistance

Replay quality depends on exact resource resolution. The current principles
are:

- preserve exact canonical identity;
- do not silently substitute;
- do not guess from a basename;
- keep stale references visible.

Conceptual resource states include AVAILABLE, MISSING, AMBIGUOUS, STALE, and
UNSUPPORTED where a future consumer has an established vocabulary. This
document does not add new runtime states.

A later optional convenience could help a user locate or obtain an exact
missing checkpoint or LoRA. That is separate from strict resource resolution:

- strict resolution answers, “What exact resource is requested and is it
  available?”;
- acquisition assistance answers, “How can the user obtain that exact
  missing resource?”.

No automatic replacement and no download implementation are authorized.

## 12. Model / LoRA library relationship

A future model or LoRA library may provide previews, trigger words, base model
information, source information, notes, and descriptive resource metadata.
It does not own generation replay semantics, resource identity authority, or
automatic substitution.

Such a library should be a separate or secondary management surface rather
than crowding the Create authoring UI. Manual LoRA prompt notation and strict
resource resolution remain valid independent of any catalog presentation.

## 13. Result, Asset, and Lineage

These terms are intentionally distinct:

- RESULT = generated output;
- PROVENANCE = evidence describing how it was generated;
- ASSET = a result intentionally adopted for later production use;
- LINEAGE = relationships among source and derived results or assets.

An example future chain is:

ROUGH RESULT -> selected result -> img2img / refinement -> final Manga result
-> adopted page asset

No Asset schema, lineage schema, media copy operation, or History migration is
implemented here.

## 14. Why lineage may matter for Manga

A useful page may descend through rough composition, Guide creation,
generation, refinement, inpaint, upscale, manual edit, and regeneration. A
future system may need to answer:

- What result did this come from?
- What settings produced this branch?
- Which branch produced the adopted page?

This is future value, not immediate product scope. It must not merge Manga and
H3 histories or introduce an Assemble workspace without a separate Card.

## 15. Authoring snapshot boundary

Generation metadata is not complete TEGAKI authoring state. A generation file
may reproduce prompts and sampler settings while lacking:

- CAST definitions;
- Reference Appearance semantics;
- Guide ownership;
- Scene / Region authoring intent;
- page structure;
- future Assemble relationships.

A later TEGAKI AUTHORING SNAPSHOT may be needed for full product-state
restoration. It is conceptually separate from media metadata and Level A/B
replay.

## 16. Low-noise UX hypothesis

Replay/provenance should mostly disappear during ordinary authoring. Useful
future actions might be:

- Load Result;
- Read Settings;
- Replay Proposal;
- Restore selected settings;
- show a missing-resource diagnostic.

The interaction should remain low-noise. A future result could expose a compact
action such as USE SETTINGS. Activating it might show recovered settings,
current-versus-recovered differences, resource availability, and selected
values to apply.

This is only a UX hypothesis. Wording, layout, persistent metadata editors,
and visibility rules are not finalized. Do not make a large provenance panel
always visible, force workflow-graph knowledge, or require metadata management
during normal generation. Astra remains the UI composition authority.

## 17. External reference lessons

No internet research is performed by this Card. General lessons already
supplied by the Commander are recorded only as patterns:

- saving workflow or generation parameters in media metadata;
- recording model or LoRA hashes;
- using sidecar metadata;
- recovering a workflow from media;
- local metadata indexing;
- result lineage;
- missing-model assistance.

These lessons do not authorize copying external implementations, adopting an
external extension as a required dependency, or changing TEGAKI ownership.

## 18. Priority classification

| Capability | Classification |
| --- | --- |
| Result provenance / replay | VALUABLE CONVENIENCE CAPABILITY |
| Result provenance / replay relative to core Manga | LOWER PRIORITY |
| WebP format work | DEFERRED / VERY LOW PRIORITY |
| Full Asset / Lineage system | LONGER-PATH |
| TEGAKI authoring snapshot | LONGER-PATH |

Do not recommend implementation before currently higher-priority Manga work
unless a later explicit Card authorizes it.

## 19. Possible future implementation slices

These are possible slices only; none is authorized by this document:

1. Provenance Writer reconciliation;
2. current PNG provenance write/read round-trip;
3. Replay Proposal integration;
4. missing-resource assistance;
5. sidecar persistence;
6. Asset / lineage evolution;
7. WebP provenance feasibility.

Slice 7 must follow core functional replay work. WebP is an optimization and
convenience question after function, not a prerequisite.

## 20. Recommended future order

This is a conceptual order, not a schedule:

1. continue Manga core product priorities;
2. when explicitly authorized, establish a provenance writer and recovery
   round-trip;
3. integrate a replay proposal through explicit review;
4. consider optional missing-resource assistance;
5. evolve Asset / lineage ownership;
6. add a sidecar strategy where justified;
7. investigate WebP provenance only when storage optimization warrants product
   resources.

## 21. Relationship to Astra

Astra does not need to review this convenience architecture now. When Result,
History, or Asset UI is eventually designed, Astra may decide how replay
actions appear, what remains hidden, and how differences are presented.

This note must not consume the current Astra UI review scope, replace the
existing UI authority documents, or authorize a provenance panel.

## 22. Current conclusion

TEGAKI already owns useful recovery and proposal building blocks. The natural
next conceptual step is reliable provenance writing, followed by a
read/normalize/resolve/propose flow that requires explicit user choice.
Resource identity remains strict; metadata, sidecars, and internal records are
complementary. Result provenance is not full Authoring state, and Asset or
Lineage is a later extension.

PNG remains the compatibility baseline. WebP may be interesting for storage
efficiency, but it is deliberately deferred and must not compete with core
Manga priorities. No implementation is authorized by this document.

## 23. Document boundary and validation

This Card creates one architecture document only. It does not modify product
source, tests, fixtures, UI, status, schema, runtime, models, dependencies,
or reserve authority. It performs no runtime, GPU, generation, /prompt,
network, internet research, model download, or dependency installation.

Validation is limited to exact start-state and final-state checks, one-file
scope checks, and git diff --check. Product tests are not required for this
documentation-only pass.

Suggested commit:

docs: define TEGAKI result provenance replay architecture

Push is forbidden.
