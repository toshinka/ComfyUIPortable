# TEGAKI Capability Compatibility Map

Status: bounded internal design map, 2026-09-16
Scope: capabilities already owned, banked, implemented as reserve-derived
headless cores, or explicitly reserved in current TEGAKI documents.

## 1. Purpose and limits

This map records compatibility and affinity between current TEGAKI contracts.
It is a design baseline for a later Web/Frontier Technology Review. It does
not add a capability, choose an external technology, connect a graph, or
authorize UI, runtime, GPU, /prompt, network, or schema work.

The evidence labels used below are:

- PROVEN: the current source or an accepted bounded document shows the
  behavior;
- PLAUSIBLE: the contract boundary is a safe architectural consequence, but
  runtime or visual behavior is not established; and
- UNKNOWN: a later experiment or product decision is required.

The compatibility labels describe a possible relationship, not permission to
connect it. The current owners remain authoritative. Existing EasyReforge
material is a behavior reference only; its implementation and UI are not
TEGAKI source to reuse. H3 and Manga runtime, workflow, state, and output
ownership are never merged by this map.

### Reuse exclusions

- Do not use H3 runtime graphs, job state, timelines, or supervisor behavior
  as Manga implementation dependencies.
- Do not turn the UI component contracts into a shared product schema or
  event bus.
- Do not copy EasyReforge implementation or UI code; its inspected license
  status is unknown.
- Do not replace Manga authoring, catalog, or regional owners with a new
  abstraction merely because a relationship is attractive.
- Do not treat a future reserve entry as an implementation instruction.

## 2. Capability matrix

Layers are the current responsibility vocabulary: PURE CORE, LOCAL SERVICE,
DOMAIN CORE, DOMAIN ADAPTER, RUNTIME GRAPH, UI ADAPTER, COMPOSITION, and
FUTURE HANDOFF. A row may name more than one layer when the source has a
bounded split.

| Capability | Current owner / evidence | Domain; ownership quality | Current layer | Maturity | Current connection | Engine replacement | Baseline value | Astra coupling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Result metadata recovery | manga/service/result_metadata_recovery.mjs; test_result_metadata_recovery.mjs | MANGA; ACCEPTABLE_FOR_NOW | PURE CORE; LOCAL SERVICE | STABLE | UNCONNECTED_BY_DESIGN | ENGINE_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE | LOW |
| Wildcard core | custom_nodes_custom/tegaki_manga_nodes/basic_generation.py; DynamicPromptTests and HeadlessWildcardTests | MANGA; GOOD | PURE CORE; DOMAIN CORE | STABLE | EXISTING_PRODUCT_OWNER_EXTENDED | PARTIALLY_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE | LOW |
| Catalog / strict resource resolution | basic_generation.py: build_catalog, snapshots, exact resolution | MANGA; GOOD | DOMAIN CORE; LOCAL SERVICE | STABLE | EXISTING_PRODUCT_OWNER_EXTENDED | ENGINE_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE | LOW |
| Manga regional compile core | scene_spec.py: compile_regional_spec; regional compile tests | MANGA; GOOD | DOMAIN CORE | EXPERIMENTAL | UNCONNECTED_BY_DESIGN | PARTIALLY_SWAPPABLE | REFERENCE_IMPLEMENTATION; EXECUTABLE_SPECIFICATION; TEST_ORACLE | LOW |
| Prompt / Settings Import Proposal | manga/service/result_settings_import.mjs; test_result_settings_import.mjs | MANGA; ACCEPTABLE_FOR_NOW | LOCAL SERVICE; DOMAIN ADAPTER | EXPERIMENTAL | UNCONNECTED_BY_DESIGN | ENGINE_SWAPPABLE | REFERENCE_IMPLEMENTATION; TEST_ORACLE | LOW |
| Model / LoRA Metadata Enrichment | custom_nodes_custom/tegaki_manga_nodes/model_lora_metadata.py; test_model_lora_metadata.py | MANGA; ACCEPTABLE_FOR_NOW | PURE CORE; LOCAL SERVICE | EXPERIMENTAL | UNCONNECTED_BY_DESIGN | PARTIALLY_SWAPPABLE | REFERENCE_IMPLEMENTATION; TEST_ORACLE | LOW |
| Scene / Region authoring | authoring_document.js, authoring_contract.py, authoring execution bridge | MANGA; GOOD | DOMAIN CORE; DOMAIN ADAPTER | STABLE | CURRENT PRODUCT AUTHORITY | PARTIALLY_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | MEDIUM |
| CAST identity | authoring document/ops and cast_master.py | MANGA; GOOD | DOMAIN CORE; DOMAIN ADAPTER | STABLE | DIRECTLY_COMPATIBLE with character_instance | PARTIALLY_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | MEDIUM |
| Reference Appearance | CAST reference_asset plus IPAdapter adapter path | MANGA; ACCEPTABLE_FOR_NOW | DOMAIN ADAPTER; RUNTIME GRAPH | EXPERIMENTAL | ADAPTER_REQUIRED from CAST/instance | PARTIALLY_SWAPPABLE | REFERENCE_IMPLEMENTATION; TEST_ORACLE | MEDIUM |
| character_instance placement | authoring document, authoring_ops.js, execution bridge | MANGA; GOOD | DOMAIN CORE; DOMAIN ADAPTER | STABLE | DIRECTLY_COMPATIBLE with CAST; geometry only to masks | PARTIALLY_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | MEDIUM |
| Guide authoring | authoring document/ops, workspace asset guards | MANGA; GOOD | DOMAIN CORE; UI ADAPTER | STABLE | SEMANTICALLY_SEPARATE from MRP and CAST | PARTIALLY_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | HIGH |
| Guide / ControlNet preparation boundary | rough_guide_bridge.py, generation_guide_bridge.py, product_generation_router.py; reconciliation document | MANGA; NEEDS_FUTURE_REVIEW for generalized control | DOMAIN ADAPTER; RUNTIME GRAPH | RECONCILED_ONLY | ADAPTER_REQUIRED; fixed qualified route only | PARTIALLY_SWAPPABLE | REFERENCE_IMPLEMENTATION; EXECUTABLE_SPECIFICATION | HIGH |
| Manga Generation status | generation_state.js, generation_view.js, GenerationJournal | MANGA; GOOD | DOMAIN CORE; UI ADAPTER | STABLE | SHARED_PRIMITIVE_ONLY with H3 presentation grammar | ENGINE_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | MEDIUM |
| H3 Generation status / result projection | h3/app/server.py Job.public and native_progress.py | H3; GOOD | DOMAIN CORE; UI ADAPTER | STABLE | SHARED_PRIMITIVE_ONLY with Manga presentation grammar | ENGINE_SWAPPABLE | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION | MEDIUM |
| Manga Result / History | GenerationService, GenerationJournal, validated output locator | MANGA; GOOD | LOCAL SERVICE; DOMAIN CORE | STABLE | CURRENT PRODUCT AUTHORITY | ENGINE_SWAPPABLE | PRODUCTION_CORE; TEST_ORACLE | MEDIUM |
| H3 Result / History | Job.public, history-settings.js, continuation-source.js | H3; GOOD | LOCAL SERVICE; DOMAIN CORE | STABLE | CURRENT PRODUCT AUTHORITY | ENGINE_SWAPPABLE | PRODUCTION_CORE; TEST_ORACLE | MEDIUM |
| Attachment media identity | Manga CAST/Guide namespaces and H3ReferenceSlots | MANGA / H3; GOOD per domain | DOMAIN CORE; UI ADAPTER | STABLE | COMMON UI GRAMMAR CANDIDATE only | PARTIALLY_SWAPPABLE | EXECUTABLE_SPECIFICATION; TEST_ORACLE | HIGH |

Reserve-derived rows are implemented as headless local cores but remain
reserve status and are not catalog, authoring, UI, or runtime authority.
Guide/ControlNet authoring is stable; its generalized normalized control
specification and preprocessor/resource policy are only reconciled.

### Reserved future concepts

These entries are intentionally retained without an implementation owner.
Their maturity is RESERVED and their layer is a future adapter, composition,
or handoff layer.

| Reserved concept | Intended owner / domain | Layer | Connection classification | Primary boundary |
| --- | --- | --- | --- | --- |
| Wildcard persistence/editor | Future Manga prompt utility | UI ADAPTER; LOCAL SERVICE | FUTURE_COMPATIBLE with Wildcard core | Validate-before-save and bounded wildcard root; no second syntax authority |
| Result-to-Asset | Future Asset/Assemble adapter | FUTURE HANDOFF | FUTURE_COMPATIBLE | Source job, locator, and provenance first; no Asset schema yet |
| Media / Shot metadata | Future Asset/Assemble service | FUTURE HANDOFF | FUTURE_COMPATIBLE | Keep media type, take, duration, and source identity explicit |
| H3 Frame / Time helpers | H3 media core | PURE CORE; FUTURE HANDOFF | FUTURE_COMPATIBLE | H3-owned timebase/FPS and frame rules |
| H3 Video Reference preparation | H3 local service/adapter | LOCAL SERVICE; DOMAIN ADAPTER | FUTURE_COMPATIBLE with H3ReferenceSlots | Read-only media identity and safe locator contract |
| Timeline handoff | Assemble boundary | FUTURE HANDOFF | FUTURE_COMPATIBLE | No shared Manga/H3 timeline |
| Civitai-style optional metadata provider | Optional metadata service | DOMAIN ADAPTER; FUTURE HANDOFF | FUTURE_COMPATIBLE | Network, privacy, credentials, and provenance require a later decision |
| H3 multi-reference / Start-End / keyframe family | H3 generation domain | DOMAIN CORE; DOMAIN ADAPTER | FUTURE_COMPATIBLE | Preserve fixed slot semantics and H3 time meaning |
| 3D previs / pose bridge | Future Guide/ControlNet adapter | DOMAIN ADAPTER; FUTURE HANDOFF | FUTURE_COMPATIBLE | Pose/camera intent must remain separate from CAST and MRP |

## 3. Fixed semantic axes

The following axes are shared vocabulary, not a shared schema:

| Axis | Manga authority | H3 authority | Boundary |
| --- | --- | --- | --- |
| INTENT | Prompt, negative prompt, page/Scene text | Video or still prompt | Text entry grammar may resemble; payloads remain separate |
| SUBJECT | CAST, character_instance, Reference Appearance | Subject/reference material and R2V input | CAST is not H3 R2V |
| SPACE / STRUCTURE | Scene, Region, MRP, page and panel geometry | Frame, Start/End, and temporal/spatial framing | Region is not Frame |
| CONTROL | Guide, ControlNet, composition constraints | Pose, camera, motion controls | Guide is not H3 motion control |
| OUTPUT | Generation, validated PNG, Result/History | Generation, media result, Result/History | Locators/provenance may be compared later |

The narrower semantic rules remain fixed: CAST means who, Reference
Appearance means appearance, Scene/Region means where text applies,
Guide/ControlNet means structure/pose/composition/geometry, LoRA is a learned
modifier, and Timeline/Keyframe means when.

## 4. Primary capability chains

Arrows below describe current or future affinity and do not by themselves
specify execution order.

### A. Result recovery chain

Generated PNG
→ Result metadata recovery (CURRENT)
→ Prompt / Settings Import Proposal (CURRENT, read-only)
→ Catalog strict resolution (ADAPTER_REQUIRED, exact IDs)
→ Model / LoRA Metadata Enrichment (ADAPTER_REQUIRED, already resolved path)
→ explicit user review/apply (FUTURE; not implemented)

Recovery preserves raw evidence and conservative hints. The proposal preserves
ambiguity and availability. Neither mutates authoring, catalog, or generation.

### B. Prompt authoring chain

Prompt text
→ autocomplete/context helper (CURRENT UI utility)
→ Wildcard validation/expansion and trace (CURRENT)
→ domain generation compile (CURRENT Manga boundary)
→ Wildcard persistence/editor (FUTURE)

Autocomplete edits text; wildcard expansion transforms text under the existing
syntax, seed, catalog-root, and trace contract. A future editor must delegate
to the same core.

### C. Manga spatial text chain

AuthoringDocument
→ Scene / Region
→ regional compile core (CURRENT, experimental)
→ mask/conditioning adapter (FUTURE ADAPTER)
→ runtime generation (FUTURE CONNECTION)

The current bridge compiles Scene prompt and area but does not invent arbitrary
user-facing local regions. No runtime graph connection or overlap precedence is
added by this map.

### D. Structural control chain

Guide media
→ canonical media validation (CURRENT)
→ normalized Control Specification (FUTURE PREPARATION)
→ strict preprocessor/resource resolution (FUTURE ADAPTER)
→ ControlNet runtime adapter (FUTURE / fixed route boundary)

The existing rough_manga route is a narrow qualified graph boundary. It does
not make Guide fields equal to ComfyUI node parameters or create a generalized
multi-ControlNet system.

### E. Subject / appearance chain

CAST
→ character_instance
→ Reference Appearance
→ current/future appearance conditioning

The existing regional proof uses the character area as an IPAdapter attention
mask. This reuses normalized geometry through an adapter; it does not turn
Reference Appearance into MRP or Guide.

### F. Result / asset chain

Generation
→ Result / History
→ provenance
→ Result-to-Asset (FUTURE)
→ Media / Shot metadata (FUTURE)
→ Assemble / Timeline handoff (FUTURE)

The minimum common idea is a source job, media locator, generation provenance,
and result/take identity. A universal Asset schema is deliberately absent.

### G. H3 temporal chain

H3 reference/media
→ Video Reference preparation (FUTURE)
→ Frame / Time helpers (FUTURE)
→ Start / End / keyframe semantics (H3-owned)
→ generation result
→ future Asset / Timeline handoff

No Manga state, graph, or timeline participates in this chain.

## 5. Connection graph

~~~mermaid
flowchart LR
  MR[PNG result] -->|CURRENT| REC[Metadata recovery]
  REC -->|CURRENT| IMP[Import proposal]
  IMP -->|ADAPTER_REQUIRED| CAT[Strict catalog resolver]
  CAT -->|ADAPTER_REQUIRED| ENR[Model/LoRA enrichment]
  ENR -->|FUTURE ADAPTER| REVIEW[Explicit user review/apply]

  TXT[Prompt text] -->|CURRENT| WC[Wildcard core]
  WC -->|CURRENT| MCOMP[Manga generation compile]
  WC -.->|FUTURE| WED[Wildcard persistence/editor]

  DOC[AuthoringDocument] -->|CURRENT| SC[Scene/Region]
  SC -->|CURRENT| REG[Regional compile]
  REG -.->|FUTURE ADAPTER| RMASK[MRP mask/conditioning]
  RMASK -.->|FUTURE| MGEN[Manga runtime graph]

  CAST[CAST] -->|CURRENT| INST[character_instance]
  INST -->|ADAPTER_REQUIRED| IP[Reference Appearance/IPAdapter]
  GUIDE[Guide] -->|ADAPTER_REQUIRED| CTRL[Control specification]
  CTRL -.->|FUTURE ADAPTER| CN[ControlNet graph]
  REG -.->|DO NOT MERGE| CTRL
  IP -.->|DO NOT MERGE| CTRL
  REG -.->|DO NOT MERGE| CAST

  MJ[Manga Result/History] -.->|SHARED PRIMITIVE ONLY| ASSET[Future Asset/Assemble]
  HJ[H3 Result/History] -.->|SHARED PRIMITIVE ONLY| ASSET
  HREF[H3 reference slots] -.->|FUTURE| HT[H3 Frame/Time]
  HT -.->|FUTURE| ASSET
~~~

The dashed edges are affinities or future adapter points. Manga and H3
runtime/state edges are intentionally absent.

## 6. Shared primitives

Sharing here means a stable rule or an explicitly scoped pure function. It
does not justify extracting a module before a second real consumer exists.

| Primitive | Classification | Reason |
| --- | --- | --- |
| canonical area {x,y,w,h} | SHARE NOW as a representation rule | Scene, character_instance, and future Guide/MRP targets already use normalized rectangles; every use must carry scope |
| safe asset identity/path validation | SHARE LATER IF SECOND CONSUMER | Manga CAST and Guide namespaces have different roots; share a pure safety rule only if H3 or another consumer adopts it without hiding namespace |
| strict resource-resolution principles | SHARE NOW as a policy; keep Manga resolver local | Exact server-owned IDs, availability, stale/ambiguous diagnostics, and no fallback are portable principles; authorities stay separate |
| metadata provenance representation | SHARE LATER IF SECOND CONSUMER | Source job, locator, field provenance, and warnings are useful, but Manga journal and H3 Job remain separate |
| diagnostic/error conventions | SHARE NOW as a vocabulary | Stable code/severity/reason concepts reduce ambiguity without sharing transport or state machines |
| deterministic IDs and ordering | SHARE NOW as a contract | Explicit IDs and source order are already required by journal, authoring, and regional compile |
| generation status projection | SHARE NOW at interaction boundary | Generic truthful states and progress projection can be shared; Manga and H3 event/state owners remain local |
| geometry-to-mask utility | SHARE LATER IF SECOND CONSUMER | Normalized geometry can feed page masks, Reference, MRP, or Guide, but scope and semantics must be explicit |
| attachment interaction grammar | SHARE NOW as UI grammar only | Thumbnail, name, availability, Add/Replace/Remove are common behavior; payload/schema remains domain-owned |

### Geometry affinity

The canonical rectangle is the same shape but not the same entity:

| Consumer | Geometry space | Affinity |
| --- | --- | --- |
| Scene / Region | Page or panel-local normalized area | CURRENT |
| character_instance | Page-space normalized area, linked to CAST and Scene | CURRENT |
| Reference mask scope | Character area projected to a page mask and IPAdapter attention mask | ADAPTER_REQUIRED |
| Guide target geometry | Guide placement plus Guide-local Figure areas projected to page space | ADAPTER_REQUIRED |
| Future MRP mask adapter | Regional compile area projected to a page mask | FUTURE ADAPTER |
| Future Control Specification | Explicit page/Guide target scope and area | FUTURE ADAPTER |

There is no evidence for a competing product-wide rectangle authority. A
legacy editor shape compatibility value and Guide-local coordinates are
scoped details, not replacements for canonical area. Local-region areas must
not be mistaken for page-global areas.

## 7. Metadata affinity and resource authority

Metadata must remain layered rather than becoming one universal object.

| Layer | Current/future owner | Meaning |
| --- | --- | --- |
| RAW SOURCE EVIDENCE | result_metadata_recovery; model_lora_metadata | Lossless PNG chunks or bounded safetensors header facts |
| NORMALIZED LOCAL METADATA | recovery hints; model/LoRA normalized fields | Conservative typed values with explicit conflict/absence states |
| RESOURCE AVAILABILITY | Manga strict catalog resolver | Whether an exact server-owned ID is available now |
| IMPORT PROPOSAL | result_settings_import | Reviewable candidate settings with field provenance and eligibility |
| PROVENANCE | Manga GenerationJournal; H3 Job/History | Source job, request snapshot, result identity, locator, and warnings |
| REMOTE ENRICHMENT | future optional provider | Outside descriptions and provenance, never selection authority |

The resource boundary is explicit:

1. Catalog Resolver answers which exact resource exists and whether it is
   available.
2. Metadata Enrichment explains an already resolved resource.
3. A future remote provider may add optional outside descriptions and source
   provenance.
4. Import Proposal offers recovered settings for review.

None of these responsibilities may guess a basename, silently substitute,
download, mutate the catalog, or auto-generate.

## 8. Prompt affinity

| Prompt concern | Owner | EDIT TEXT | TRANSFORM TEXT | STRUCTURE TEXT | RESOLVE RESOURCE | COMPILE CONDITIONING |
| --- | --- | --- | --- | --- | --- | --- |
| Manual positive/negative prompt | Domain Create state | YES | only explicit user edits | domain snapshot | NO | domain compiler |
| Autocomplete/context helper | Manga prompt utility/UI | YES | NO | NO | NO | NO |
| Wildcard expansion | Wildcard core | NO | YES, deterministic | choice trace | wildcard catalog only | Manga compile consumes result |
| Page/global prompt | Manga AuthoringDocument/page plan | YES | compile preserves scope | YES | NO | global branch |
| Scene prompt | Manga Scene | YES | compile preserves scope | YES | NO | panel/Scene branch |
| Region prompt | lower-level MRP regional records | YES when supplied | compile preserves scope | YES | NO | future regional adapter |
| Negative prompts | Domain-specific prompt branches | YES | preserve positive/negative separation | YES | NO | each domain compiler |
| LoRA prompt syntax | Manga basic compiler plus strict catalog at compile boundary | YES; preserve manual notation | only supported exact resolution | traceable modifier | exact LORA ID when resolved | runtime compile later |

Regional text must remain structured as global → Scene → region scopes. It must
not be flattened into one universal string merely because the runtime has
CLIP text nodes. CAST identity text and Guide intent remain separate from MRP.
H3 prompt handling remains H3-owned.

## 9. Attachment affinity

The following is a COMMON UI GRAMMAR CANDIDATE, not a common product schema:

| Attachment | Domain meaning | Identity / availability | Common actions | Domain-only fields |
| --- | --- | --- | --- | --- |
| Manga CAST Reference Appearance | Who / visual appearance | canonical reference_asset and server-owned availability | Add, Replace, Remove, Inspect | CAST identity, character scope, IPAdapter strength/mask when supported |
| Manga Guide | Structure / pose / composition | canonical Guide asset and validation state | Add, Replace, Remove, Inspect | Guide type, placement, Figure regions, future control kind |
| H3 reference | H3 subject/reference material | H3ReferenceSlots with fixed role and preview identity | Add, Replace, Remove, Inspect | Start/End role, H3 route and time semantics |
| Future H3 video reference | Prepared H3 media input | future H3-owned safe locator and media facts | Add, Replace, Remove, Inspect | Frame/time selection and H3-specific preparation |

Strength, scope, target, and Start/End controls appear only when the domain
contract defines them. Invalid or unavailable values remain visible and fail
closed. No browser filesystem path, upload transport, or shared attachment
storage format is implied.

## 10. Output affinity

| Current output | Evidence retained | Future affinity | Boundary |
| --- | --- | --- | --- |
| Manga Result / History | Manga job/request snapshot, validated PNG locator, prompt/model/LoRA settings, journal state | Result-to-Asset; Media/Shot metadata | Manga remains result authority |
| H3 Result / History | H3 Job.public projection, media locator, request, references, phase/error/progress | Result-to-Asset; Media/Shot; Timeline | H3 remains media/result authority |

The minimum comparable ideas are source job, media locator, generation
provenance, and take/result identity. Asset conversion, media/shot fields,
and Assemble/TL handoff require a future owner and must not be introduced as a
universal Asset schema.

## 11. Manga / H3 boundary

| Boundary | Required state |
| --- | --- |
| Runtime graphs | Separate Manga and H3 graphs; no shared graph compiler |
| Generation state | Separate journal/GenerationState and H3 Job/history state |
| Schemas | TEGAKI authoring and Manga request contracts remain separate from H3 request/reference contracts |
| Workflows | Domain-owned workflow/node choices; no common timeline |
| Output ownership | Manga output locators/history remain Manga-owned; H3 media remains H3-owned |
| Safe sharing | Pure primitives, interaction grammar, bounded handoff concepts, and justified metadata conventions only |

Conceptual reuse is useful where a user asks for the same cognitive slot, but
it must pass through a domain adapter. There is no common supervisor or
Manga/H3 runtime dependency.

### Semantic separation checks

| Pair | Compatibility classification | Reason |
| --- | --- | --- |
| Scene / Region ↔ MRP | DIRECTLY_COMPATIBLE at structured compile boundary | Scene prompt + area is current MRP input; arbitrary local regions remain bounded |
| MRP ↔ CAST / Reference Appearance | SEMANTICALLY_SEPARATE | MRP says where/what text applies; CAST/IPAdapter says who/appearance |
| MRP ↔ Guide / ControlNet | SEMANTICALLY_SEPARATE | Guide says structure/pose/geometry; a future adapter may share area only |
| CAST ↔ character_instance | DIRECTLY_COMPATIBLE | Instance explicitly links cast_id and scene_id |
| character_instance area ↔ IPAdapter mask | ADAPTER_REQUIRED | Page geometry is converted to an IPAdapter attention mask |
| Guide ↔ ControlNet | ADAPTER_REQUIRED | Guide intent/media must become a future normalized control specification |
| Manga GenerationStatus ↔ H3 GenerationStatus | SHARED_PRIMITIVE_ONLY | Projection grammar may align; state/event owners do not |
| Manga Result ↔ H3 Result | SHARED_PRIMITIVE_ONLY | Provenance ideas align; history schemas and locators remain domain-owned |

## 12. Compatibility / adapter map

| Relationship | Classification | Evidence / condition |
| --- | --- | --- |
| Result recovery → Import Proposal | DIRECTLY_COMPATIBLE | result_settings_import consumes the bounded recovery shape read-only |
| Import Proposal → Catalog Resolver | ADAPTER_REQUIRED | Recovered IDs require exact current availability and stale/ambiguous diagnostics |
| Catalog Resolver → Metadata Enrichment | ADAPTER_REQUIRED | Enrichment accepts an already resolved canonical ID/path and cannot resolve itself |
| Autocomplete → Wildcard Core | ADAPTER_REQUIRED | UI text can contain wildcard syntax; basic_generation remains the syntax authority |
| Wildcard Core → Manga compile | DIRECTLY_COMPATIBLE | Expanded text and trace are compile inputs under existing seed/path rules |
| Scene/Region → Regional Compile | DIRECTLY_COMPATIBLE | compile_regional_spec preserves IDs, order, scope, area, prompt, and diagnostics |
| Regional Compile → runtime graph | FUTURE_COMPATIBLE | Masks, overlap precedence, and conditioning adapter are not yet productized |
| Guide media → Guide validator | DIRECTLY_COMPATIBLE | Existing canonical namespace, media, dimension, and area guards |
| Guide → normalized Control Specification | FUTURE_COMPATIBLE | Reconciled preparation boundary; no current spec module |
| Control Specification → ControlNet graph | ADAPTER_REQUIRED | Exact model/preprocessor capability and runtime experiment are still required |
| CAST → Reference Appearance | ADAPTER_REQUIRED | Reference asset and character area feed the current IPAdapter path |
| MRP → Reference Appearance | SEMANTICALLY_SEPARATE | Spatial text and visual appearance must not be collapsed |
| Guide → Reference Appearance | SEMANTICALLY_SEPARATE | Structural control and appearance conditioning have separate owners |
| Manga attachment ↔ H3 attachment | SHARED_PRIMITIVE_ONLY | Add/replace/remove grammar only; fixed roles and namespaces differ |
| Manga/H3 status projection | SHARED_PRIMITIVE_ONLY | Truthful generic vocabulary may be presented similarly |
| Manga/H3 runtime/state/workflow | SEMANTICALLY_SEPARATE | No common backend, supervisor, timeline, or schema |
| Manga/H3 result → future Asset | FUTURE_COMPATIBLE | Requires an Asset/Assemble owner and explicit provenance contract |
| H3ReferenceSlots → Video Reference preparation | FUTURE_COMPATIBLE | H3-only read-only preparation remains reserved |
| Metadata → future remote provider | ADAPTER_REQUIRED | Remote description must remain optional enrichment with provenance |
| MRP overlap policy ↔ Guide/ControlNet coexistence | UNKNOWN | No proven precedence, feathering, or combined runtime behavior |

## 13. Friction and duplication check

No fixes are made in this map. Findings identify boundaries that a later Card
must respect.

| Check | Severity | Finding |
| --- | --- | --- |
| Duplicate ownership | NONE | Wildcard syntax and Manga catalog resolution each have one current authority |
| Two competing normalizers | LOW | Authoring, Guide projection, and regional compile normalize scoped geometry; no second canonical shape is required |
| Two resource authorities | LOW | Manga catalog owns identity; metadata readers and import proposals deliberately do not resolve or mutate it |
| Parallel geometry types | LOW | Page area, panel-local area, Guide-local Figure area, and H3 media dimensions have different scopes; legacy editor aliases must stay local |
| Metadata fields with different meanings | MEDIUM | Raw PNG/header evidence, normalized hints, availability, import candidates, and provenance must stay in separate layers |
| Equivalent-looking state names | MEDIUM | Manga journal states and H3 Job states overlap in labels but differ in lifecycle and authority |
| MRP overlap / feather policy | HIGH | Existing masks expose branches and feathering, but no single precedence or cross-control policy is proven |
| Accidental Manga/H3 coupling | NONE | Current documents and source preserve separate runtimes, schemas, workflows, and output ownership |

## 14. Contract replacement safety

| Core | Classification | Replacement condition |
| --- | --- | --- |
| Metadata Recovery | ENGINE_SWAPPABLE | Preserve bounded read-only input, raw entries, conservative hints, diagnostics, and no execution |
| Wildcard Core | PARTIALLY_SWAPPABLE | A new engine must preserve supported syntax, safe root, deterministic seed behavior, and choice trace |
| Catalog Resolver | ENGINE_SWAPPABLE | Any backend can replace internals if exact IDs, revision, availability/reason states, and no-fallback behavior remain |
| Regional Compile | PARTIALLY_SWAPPABLE | Normalized regional records and diagnostics are stable, while overlap/conditioning policy is still Manga-specific and unresolved |
| Settings Import Proposal | ENGINE_SWAPPABLE | A different recovery source may feed the same review-only field/provenance/availability contract |
| Model / LoRA Metadata | PARTIALLY_SWAPPABLE | Header reader internals can change, but bounded safetensors framing and explicit-key non-guessing must remain |

Swappability concerns internals, not ownership. A replacement is justified only
after it preserves the contract and has evidence for the same failure and
provenance boundaries.

## 15. Baseline value

The following labels describe current value even when a capability is
experimental or unconnected:

| Capability | Baseline value |
| --- | --- |
| Metadata Recovery | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE |
| Wildcard Core | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE |
| Catalog Resolver | PRODUCTION_CORE; EXECUTABLE_SPECIFICATION; TEST_ORACLE |
| Regional Compile | REFERENCE_IMPLEMENTATION; EXECUTABLE_SPECIFICATION; TEST_ORACLE |
| Settings Import Proposal | REFERENCE_IMPLEMENTATION; TEST_ORACLE |
| Model / LoRA Metadata Enrichment | REFERENCE_IMPLEMENTATION; TEST_ORACLE |
| Guide / ControlNet preparation | REFERENCE_IMPLEMENTATION; EXECUTABLE_SPECIFICATION |
| Manga/H3 result and status projections | PRODUCTION_CORE within each domain; TEST_ORACLE for later interaction comparisons |

No current item is declared obsolete. A future external result must be compared
against these contracts rather than against an unbounded wish list.

## 16. Astra boundary

The compatibility map is intentionally useful before composition review:

| Astra dependence | Current safe scope | Deferred scope |
| --- | --- | --- |
| LOW | Pure validation, normalization, strict resolution, metadata transformation, deterministic compile records | None required for headless contract review |
| MEDIUM | Domain adapter exposure, primary/advanced control grouping, attachment semantic explanation | Exact product wording and disclosure order |
| HIGH | Workspace layout, PreviewFocus, AttachmentCard composition, responsive behavior, panel hierarchy, motion | Do not recommend implementation before Astra review |

GenerationStatus, ProgressProjection, and AttachmentCard have bounded
behavioral contracts. MediaPreviewShell, PreviewFocus, and CompactContext still
need Astra composition review. A visual component may be shared as grammar
without becoming a shared Manga/H3 semantic object.

## 17. Frontier review hooks

This table prepares a later external comparison without naming a winner or
researching a new product.

| Capability | Current TEGAKI approach | Later comparison area | Contract to preserve | Evidence that would justify replacement |
| --- | --- | --- | --- | --- |
| Regional conditioning | Structured Scene/Region records, canonical area, ordered compile diagnostics, domain-local masks | Regional prompting / conditioning systems | Scope, IDs, order, positive/negative separation, strength, overlap diagnostics | Clearer precedence/feather semantics with equivalent failure behavior and acceptable VRAM |
| Guide / ControlNet | Canonical Guide assets, fixed qualified route, future normalized control specification | ControlNet model/preprocessor ecosystems | Guide meaning, safe media identity, explicit target geometry, strict resources | Proven model/preprocessor compatibility, coexistence, latency, and failure policy |
| Metadata recovery | Bounded PNG textual reader and conservative hints | Metadata APIs and workflow readers | Raw evidence, normalized local fields, no execution, provenance | Broader safe format support without unsafe workflow execution or guessed fields |
| Model management | Revisioned server-owned catalog with exact IDs and no fallback | Model management/resource catalogs | Identity, availability, revision, stale/ambiguous states | Stronger authority with the same fail-closed and provenance guarantees |
| Workflow import | Review-only Settings Import Proposal | Workflow import patterns | Field allowlist, explicit review/apply, unchanged authoring until confirmation | Safe broader recovery with field-level ambiguity and no implicit generation |
| Prompt templating | Existing wildcard syntax, path safety, deterministic expansion trace | Prompt templating engines | Syntax, seed, trace, bounded root, failure behavior | Compatible deterministic semantics and materially better diagnostics or coverage |
| Asset / provenance | Manga Journal and H3 Job/History retain source/job/result identity | Asset and provenance systems | Source job, media locator, take/result identity, domain ownership | Explicit Asset owner that preserves both domain histories without merging them |
| H3 video reference/time | Fixed H3ReferenceSlots and reserved H3 Frame/Time helpers | Video reference and time semantics | Start/End roles, H3 timebase, frame identity, safe media policy | Evidence-backed timebase and reference handling with no Manga coupling |

## 18. External-review priority

This ranking is only the need for external review, not implementation priority.

### HIGH REVIEW VALUE

- Regional conditioning and overlap/feather policy
- Guide / ControlNet model, preprocessor, and coexistence behavior
- Model metadata and strict resource management
- H3 video reference, frame, and time semantics

### MEDIUM REVIEW VALUE

- Workflow/result metadata import
- Prompt templating and wildcard ecosystem behavior
- Result provenance and Asset/Assemble boundaries

### LOW REVIEW VALUE

- Wildcard persistence/editor mechanics
- Optional Civitai-style metadata provider
- Final visual composition of PreviewFocus and AttachmentCard (Astra owns the
  first decision; external technology is secondary)

## 19. Current conclusion

Current parts are MOSTLY mutually compatible. The strongest natural
connections are recovery → review proposal → strict catalog checks, prompt →
wildcard compile, Scene/Region → regional compile, CAST →
character_instance → Reference Appearance, and Guide → a future normalized
Control Specification. These connections are useful because each preserves the
existing owner and has a visible adapter boundary.

MRP, CAST/Reference Appearance, and Guide/ControlNet must remain semantically
separate even when they reuse normalized geometry or conditioning primitives.
Manga and H3 can share truthful status grammar, attachment interaction grammar,
provenance vocabulary, and future handoff concepts, but not runtime graphs,
generation state, schemas, workflows, timelines, or output ownership.

The current banked and reserve-derived contracts are valuable as executable
specifications, test oracles, and bounded production cores. They remain useful
if a later engine changes because their replacement conditions are explicit.
External review should concentrate first on regional conditioning,
ControlNet/structural control, resource/metadata management, and H3 temporal
reference semantics. No technology winner is selected here, and no capability
connection is authorized by this document.
