# TEGAKI Pre-Astra Capability Inventory

**Status:** Bounded headless capability inventory

**Scope:** Functional cores that can be prepared before Astra reviews the
current rendered UI

**Limit:** No product or UI implementation is authorized by this document

This inventory selects user capabilities that can survive a later visual
redesign. It is not an extension shopping list or repository archaeology. A
capability is considered only when its smallest useful boundary can be tested
without choosing a final layout.

Manga and H3 remain separate products, runtimes, schemas, workflows, and state
owners. A reusable capability may have a shared interaction adapter later, but
it must retain domain-specific meaning and validation.

## 1. Current entry route

The bounded source check found the current route unchanged:

```text
h3/run_h3.bat
  -> h3/tools/tegaki_shell_supervisor.mjs
       -> H3 Native backend (8188)
       -> H3 shell (8190)
       -> MangaDomainRuntime
            -> Manga backend (8189)
            -> Manga workspace (8191)
       -> H3 shell MANGA product switch
            -> embedded iframe to the Manga workspace (8191)
```

Evidence is limited to `h3/run_h3.bat`, the supervisor's configured ports and
`--manga-workspace-url`, and the H3 shell product switch/iframe markup. The
route is **UNCHANGED**. Any current visual difference between Manga and H3 is a
workspace/view/composition matter, not a new launch authority. This inventory
does not modify or relaunch that route.

## 2. Inventory method

For each candidate, the question is:

1. What user problem does it solve?
2. What is the smallest UI-independent core?
3. Which available source is technically closest?
4. Is adapting that source better than a small TEGAKI-native core?
5. Can the boundary be tested headlessly?
6. Would doing it now constrain Astra's composition review?

The source pools were inspected only for bounded relevant material:

- **TEGAKI CURRENT:** Manga catalogs, compiler, authoring validators,
  attachment validators, journal, and H3 shell patterns.
- **COMFYUI CORE:** `folder_paths.py`, checkpoint/LoRA/ControlNet loaders,
  regional conditioning primitives, SaveImage metadata, and the bounded asset
  metadata extractor.
- **COMFYUI EXTENSION:** the installed `ComfyUI-Custom-Scripts` metadata and
  LoRA autocomplete helpers.
- **EASYREFORGE:** read-only Manga Prompter parser/attention documentation and
  script behavior for comparison only.
- **H3:** current result, reference, history, and frame/media patterns.
- **TEGAKI-NATIVE:** a small behavior-level core when other sources are too
  coupled or semantically wrong.

## 3. License and copy safety

No external code is copied by this Card.

| Source | License evidence | Direct copying safe to plan? | Decision |
| --- | --- | --- | --- |
| TEGAKI CURRENT | Current project authority; no external source involved | YES for current project work | Reuse current behavior where it is already bounded |
| ComfyUI core | `ComfyUI/LICENSE` is GPL-3.0 | UNKNOWN without a product-license decision | Prefer behavior-level reimplementation or a reviewed adapter |
| ComfyUI-Custom-Scripts | Local `LICENSE` is MIT | YES with notice preservation | Adapt the small behavior; do not import its UI/API coupling wholesale |
| EasyReforge reference | No `LICENSE`, `COPYING`, or `NOTICE` found in the inspected extension | NO | Read-only behavior reference; reimplement semantics |
| H3 current | Current TEGAKI source | YES for TEGAKI changes when separately authorized | Keep H3 state and runtime separate |

EasyReforge's `manga_prompter.py` confirms a BREAK/slot parser, stable panel
ordering, spatial masks, and global extra-network activation. It also reports
that regional LoRA isolation is not enabled. Its Forge hooks, Gradio UI, and
unclear license make direct reuse inappropriate.

## 4. Capability layers

Implementation should proceed from deterministic behavior toward presentation:

1. **PURE CORE** — deterministic logic with no filesystem, network, backend, or
   model side effects.
2. **LOCAL SERVICE** — bounded local catalog, metadata, journal, or file
   identity behavior.
3. **DOMAIN ADAPTER** — Manga or H3 meaning, validation, and payload mapping.
4. **RUNTIME GRAPH** — actual ComfyUI graph execution and generation.
5. **UI ADAPTER** — a thin later bridge from controls or cards to a capability.
6. **COMPOSITION** — Astra/later decisions about layout, density, and motion.

This Card recommends no Runtime Graph, UI, or Composition work.

## 5. Capability inventory

There are exactly 12 candidates. `ALREADY OWNED` in the notes means the current
authority is sufficient for now and a duplicate helper should not be created.

| Capability | User Value | Preferred Source | Reuse Strategy | Layer | Astra Coupling | Cost | Color (GREEN/YELLOW/RED) | Headless Testable (YES/NO) | License Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wildcard expansion and strict validation | Repeatable prompt variation without unsafe paths or unresolved tokens | TEGAKI CURRENT | REUSE | PURE CORE + LOCAL SERVICE | LOW | SMALL | GREEN | YES | Current TEGAKI behavior |
| Prompt token, LoRA, and wildcard helpers | Faster editing while preserving manual syntax | TEGAKI CURRENT | REUSE | PURE CORE + UI ADAPTER | LOW | SMALL | GREEN | YES | Current TEGAKI behavior |
| PNG/workflow metadata recovery | Recover prompt, model, LoRA, seed, and workflow context from existing media | COMFYUI CORE | REIMPLEMENT | PURE CORE + LOCAL SERVICE | LOW | MEDIUM | GREEN | YES | GPL-3.0 behavior reference; no direct copy planned |
| Server-owned model/LoRA catalog and strict resolution | Explicit availability and fail-closed selection | TEGAKI CURRENT | REUSE | LOCAL SERVICE + DOMAIN ADAPTER | LOW | SMALL | GREEN | YES | Current Manga capability authority |
| Model/LoRA metadata enrichment | Explain base model, trigger words, hash, and provenance | COMFYUI EXTENSION | ADAPT | LOCAL SERVICE | MEDIUM | MEDIUM | YELLOW | YES | MIT; thin adapter and notices only |
| Region validation and normalization | Keep spatial authoring safe and deterministic | TEGAKI CURRENT | REUSE | PURE CORE | LOW | SMALL | GREEN | YES | Current authoring/region authority |
| MRP region-to-prompt/mask compile representation | Prepare where/what semantics without shipping a final editor | TEGAKI CURRENT | ADAPT | DOMAIN ADAPTER | MEDIUM | MEDIUM | YELLOW | YES | EasyReforge is read-only alternate; no direct copy |
| Guide/ControlNet input preparation and validation | Make future structure/pose controls safe to attach | COMFYUI CORE | ADAPT | DOMAIN ADAPTER | MEDIUM | MEDIUM | YELLOW | YES | Core GPL-3.0; behavior-level adapter preferred |
| Attachment media validation and canonical identity | Prevent foreign paths and ambiguous references | TEGAKI CURRENT | REUSE | LOCAL SERVICE + DOMAIN ADAPTER | LOW | SMALL | GREEN | YES | Current canonical reference validators |
| Result/take/history metadata identity | Preserve the relationship between a result and its settings | TEGAKI CURRENT | REUSE | LOCAL SERVICE | LOW | SMALL | GREEN | YES | Current Manga journal and H3 history patterns |
| PreviewFocus visual implementation | Inspect media with contextual compression | TEGAKI-NATIVE | DEFER | COMPOSITION | HIGH | LARGE | RED | NO | No external code needed; Astra must review first |
| Final AttachmentCard visual system | Give all attachment types a finished visual grammar | TEGAKI-NATIVE | DEFER | COMPOSITION | HIGH | LARGE | RED | NO | No external code needed; Astra must review first |

## 6. Candidate decisions and headless boundaries

### 6.1 Wildcard expansion and strict validation — ALREADY OWNED

**User problem:** Prompt authors need repeatable choices and nested wildcard
files without path traversal, missing names, malformed syntax, or silent
literals.

**Closest source decision:** TEGAKI's `basic_generation.py` is already the
correct bounded core. It resolves a server-owned wildcard root, validates names,
uses the installed `dynamicprompts` API, derives deterministic seed domains,
and records the expanded prompt. EasyReforge's parser is not a better source.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Raw positive/negative text, bounded local wildcard root, effective seed | Expanded text, root/version trace, deterministic seed domains | Root unavailable, unsafe path, missing wildcard, invalid syntax, unresolved token | Read-only local file access; no model, queue, or UI mutation | Existing pure compile tests with temporary wildcard files and fixed seeds |

**UI ADAPTER:** Prompt field asks the capability to compile; it does not own
expansion. `UI COMPOSITION: ASTRA/LATER`.

### 6.2 Prompt token, LoRA, and wildcard helpers — ALREADY OWNED

**User problem:** Editing long prompts is slow and manual LoRA/wildcard syntax
is easy to damage.

**Closest source decision:** `manga/app/src/view/tag_autocomplete.js` already
detects tag, LoRA, and wildcard contexts, queries bounded catalogs, and inserts
syntax without duplicating delimiters. Its pure detection/query functions and
tests are sufficient; no second helper should be introduced.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Text, caret position, normalized catalog | Context classification, bounded suggestions, replacement text/caret | Unavailable catalog, malformed active token, unsupported context | DOM-free computation; insertion emits the existing input path only in the UI adapter | Existing contextual autocomplete unit tests |

**UI ADAPTER:** Existing prompt fields consume a suggestion/replacement result.
No new panel or visual catalog is required. `UI COMPOSITION: ASTRA/LATER`.

### 6.3 PNG/workflow metadata recovery — RECOMMENDED NEXT SLICE

**User problem:** An existing image often contains the only copy of the prompt,
model, LoRA, seed, resolution, or workflow that an author wants to reuse.

**Closest source decision:** ComfyUI core's `SaveImage` metadata behavior and
`app/assets/services/metadata_extract.py` establish useful fields and safe
header reading. A small TEGAKI-native parser is safer than copying the GPL core
service or coupling Manga to ComfyUI's Asset database.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Bounded PNG bytes or a server-owned relative result locator | Normalized optional prompt/workflow/model/LoRA/seed/resolution/provenance metadata plus source kind | Invalid signature, oversized/corrupt metadata, unsupported encoding, foreign locator | Read-only; no path escape, model load, queue, authoring mutation, or automatic generation | Pure fixtures for valid/empty/corrupt PNG text chunks and safe locator tests |

**UI ADAPTER:** A later import action may present recovered values for explicit
user review. It must never auto-populate or generate merely because metadata was
found. `UI COMPOSITION: ASTRA/LATER`.

### 6.4 Server-owned model/LoRA catalog and strict resolution — ALREADY OWNED

**User problem:** A selection must be explicit, available, and reproducible;
missing models and ambiguous LoRA stems must fail closed.

**Closest source decision:** Manga's `basic_generation.py` catalog is already
revisioned from ComfyUI node capabilities and server-owned names. ComfyUI
`folder_paths.py` remains the underlying local enumeration authority. The
current strict resolver preserves full IDs and rejects unsafe or ambiguous
matches.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Node capability snapshot, server-owned checkpoint/LoRA names, requested IDs or prompt tags | Revisioned availability catalog, resolved exact IDs, family confidence | Missing capability, stale revision, unavailable/ambiguous/unsafe ID | Read-only catalog and compile; no fallback or model load | Existing catalog and basic generation tests |

**UI ADAPTER:** Checkpoint and LoRA controls consume the catalog and preserve
unavailable values visibly. `UI COMPOSITION: ASTRA/LATER`.

### 6.5 Model/LoRA metadata enrichment

**User problem:** A catalog name alone does not explain base model, trigger
words, hash, or provenance.

**Closest source decision:** `ComfyUI-Custom-Scripts` has a small MIT-licensed
metadata and LoRA listing path; ComfyUI core's safetensors header extractor is
the alternate reference. Adapt behavior behind a TEGAKI local service rather
than copying PromptServer routes, sidecar policy, or UI.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Server-owned model/LoRA ID resolved through the current catalog | Optional typed metadata (base model, trigger words, hash/provenance) with availability | Missing file, unreadable header, malformed metadata, unsupported format | Read-only cache allowed; never changes catalog authority | Header fixture tests and unavailable-file tests |

**UI ADAPTER:** A later catalog detail affordance may show metadata. It does
not change selection or add a final catalog panel. `UI COMPOSITION: ASTRA/LATER`.

### 6.6 Region validation and normalization — ALREADY OWNED

**User problem:** Scene and Region coordinates must remain safe when scenes,
frames, and character placement are edited.

**Closest source decision:** Current `authoring_ops.js`, `region_editor.py`,
`authoring_contract.py`, and related Scene/Guide validators are the authority.
ComfyUI area/mask primitives are downstream consumers, not a replacement for
authoring validation.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Scene/Region rectangles, page dimensions, stable IDs, optional relationships | Normalized bounds, deterministic diagnostics, stable references | Missing IDs, non-finite/out-of-bounds coordinates, invalid relationships | Pure copy/validation; no authoring mutation unless an existing operation explicitly commits | Existing authoring, region, frame, and document tests |

**UI ADAPTER:** Scene and Region editors consume diagnostics and normalized
values; final spatial composition remains open. `UI COMPOSITION: ASTRA/LATER`.

### 6.7 MRP region-to-prompt/mask compile representation

**User problem:** Authors need a deterministic representation of where/what
text applies before a final regional workspace is designed.

**Closest source decision:** Current TEGAKI Scene compiler, page-plan adapter,
conditioning builder, and mask builder preserve authoring meaning and existing
stable IDs. ComfyUI's `ConditioningSetArea` and `ConditioningSetMask` are useful
native primitives. EasyReforge's BREAK-slot and attention-hook behavior is
research context only; it is UI/Forge coupled and has no clear copy license.

**Pre-Astra core only:** region validation, prompt-region mapping, normalized
area/mask preparation, compile representation, and diagnostics. No final MRP
editor, panel layout, or generation integration is proposed here.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Validated Scene/Region records, prompt slots, page dimensions, optional mask feather | Deterministic region mapping, normalized area/mask descriptors, compile digest | Missing/duplicate region, slot mismatch, invalid area, unsupported semantic | Pure representation; no graph submit, model load, or GPU work | Existing scene-generation and mask/conditioning unit tests plus fixture plans |

**UI ADAPTER:** A future Scene/Region editor may show mapping diagnostics and
submit the representation through the domain adapter. `UI COMPOSITION:
ASTRA/LATER`.

### 6.8 Guide/ControlNet input preparation and validation

**User problem:** A future guide should carry structure/pose/geometry safely
without turning ControlNet into an unbounded file or model picker.

**Closest source decision:** ComfyUI core exposes `ControlNetLoader`,
`ControlNetApplyAdvanced`, and control type support. TEGAKI's guide contracts,
contain placement, asset namespace validators, and generation-guide bridge add
Manga meaning. Use a thin domain adapter; do not integrate generation now.

**Pre-Astra core only:** input validation, preprocessor discovery/catalog,
control-image metadata, normalization, and a control specification. No
ControlNet graph path or final AttachmentCard is included.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Canonical guide reference, image dimensions/metadata, control kind, normalized target | Validated control specification and diagnostics | Foreign path, unsupported media/control kind, invalid dimensions, unavailable capability | Read-only preparation; no model load, graph compile, or generation | Pure guide/reference tests and capability fixture tests |

**UI ADAPTER:** A future Guide attachment supplies the validated specification
and displays its status. `UI COMPOSITION: ASTRA/LATER`.

### 6.9 Attachment media validation and canonical identity — ALREADY OWNED

**User problem:** CAST references and Guides need safe, stable identities rather
than arbitrary browser paths.

**Closest source decision:** Manga's canonical `tegaki_manga_references/` and
`tegaki_manga_guides/` validators, workspace asset routes, and H3 reference
verification provide the required bounded behavior. No new shared file
identity helper should be created before a domain decision.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Relative canonical asset reference, expected media type, optional stat/thumbnail metadata | Typed identity, availability, safe preview locator, validation reason | Absolute/traversal path, unsupported extension, missing asset, foreign namespace | Server-owned read-only lookup; no arbitrary filesystem access | Existing CAST/Guide operation and browser-fixture tests |

**UI ADAPTER:** AttachmentCard-like controls display the identity and status;
they do not choose a global file schema. `UI COMPOSITION: ASTRA/LATER`.

### 6.10 Result/take/history metadata identity — ALREADY OWNED

**User problem:** A generated result must remain tied to its job, settings, and
safe output while authors iterate.

**Closest source decision:** Manga's `generation_journal.mjs` validates one
record per job, prompt/backend identity, effective settings, output locator,
and atomic replacement. H3's result/history structures provide a useful
parallel pattern but are not a shared state owner.

**Boundary:**

| INPUT | OUTPUT | ERRORS | STATE / SIDE EFFECT | TEST METHOD |
| --- | --- | --- | --- | --- |
| Job record, settings snapshot, result locator, history entry | Validated take identity and current/previous relationship | Corrupt record, foreign job/output, duplicate or missing identity | Atomic local journal write only through existing authority; no UI or runtime change | Existing generation service/journal tests and H3 history normalization tests |

**UI ADAPTER:** History may display or restore a snapshot explicitly; it does
not become an Asset browser or auto-generate. `UI COMPOSITION: ASTRA/LATER`.

### 6.11 PreviewFocus visual implementation — RED / DEFER

The user value is clear, but expansion, compression, motion, ratio, and narrow
behavior are composition decisions explicitly awaiting Astra. A headless test
cannot establish the visual hierarchy. Keep the `PreviewFocus` behavior
contract; do not implement a visual shell before review.

### 6.12 Final AttachmentCard visual system — RED / DEFER

The interaction grammar is already documented, but finished density, grouping,
status treatment, and domain emphasis depend on Astra's Manga/H3 comparison.
Keep domain-specific validation and attachment identity cores; do not build a
visual card system or placeholder panel now.

## 7. UI adapter boundary rule

Every GREEN or YELLOW candidate above has a thin eventual adapter and no screen
placement decision. The adapter may invoke a capability, consume its result,
display validation, or pass a canonical attachment reference. For all of them:

**UI COMPOSITION: ASTRA/LATER**

No pre-Astra implementation should require a visible production panel merely to
prove that the capability exists. Acceptable validation surfaces are pure unit
tests, service/API tests, existing developer harnesses, or direct module
invocation.

## 8. MRP boundary

MRP remains strategically important but UI-sensitive. The inventory separates
the MRP capability core from an eventual MRP workspace:

- **Allowed before Astra:** validation, normalized Scene/Region data, prompt
  mapping, mask/area preparation, compile representation, and diagnostics.
- **Wait for Astra:** panel editor, visual region authoring, final card grammar,
  spatial disclosure, and generation-flow placement.

The source preference is current TEGAKI Scene/Region infrastructure plus
ComfyUI's native area/mask primitives. EasyReforge remains a read-only behavior
reference and is not a code source.

## 9. ControlNet / Guide boundary

Guide/ControlNet is future Manga controllability work:

- **Allowed before Astra:** canonical input validation, control-image metadata,
  preprocessor discovery/catalog, normalization, and a domain control spec.
- **Wait for Astra and a separate product Card:** graph integration, model
  loading, multi-ControlNet policy, final AttachmentCard, and generated output.

This preserves the separation `Guide/ControlNet = structure, pose, geometry`.
It does not replace CAST/IPAdapter or MRP.

## 10. Future H3 / video-derived reserve

These concepts are retained without code or schema work. They may later help
outside the current H3 UI.

| Concept | Why useful | Probable capability layer | Dependency / precondition |
| --- | --- | --- | --- |
| Media/Shot asset metadata | Connect a result to a shot, take, duration, and media type | LOCAL SERVICE | Future Asset/Assemble identity decision |
| Frame/time helpers | Make Start/End, frame index, duration, and playback metadata consistent | PURE CORE | H3 media contract and timebase decision |
| Video reference preparation | Validate and summarize subject/reference media before a job | LOCAL SERVICE + DOMAIN ADAPTER | H3 reference semantics and safe media policy |
| Result-to-Asset conversion | Carry generation provenance into downstream reuse | DOMAIN ADAPTER | Future Asset model; not History redesign |
| Timeline handoff metadata | Pass a take to downstream editing without merging H3/Manga timelines | DOMAIN ADAPTER | Separate Assemble/workflow handoff Card |

No H3-derived concept is an implementation target for this Card.

## 11. Top 5 pre-Astra capabilities

These are the five highest practical values, including capabilities that should
be retained as current authority rather than duplicated.

1. **Server-owned model/LoRA catalog and strict resolution** — It protects
   explicit selection and fail-closed behavior now. TEGAKI CURRENT already
   provides the correct revisioned catalog and resolver. Remaining work is
   metadata enrichment only; no new selector or fallback is proposed.
2. **Wildcard expansion and strict validation** — It gives repeatable prompt
   variation with deterministic, testable behavior. TEGAKI CURRENT is already
   stronger and safer than copying EasyReforge. Remaining work is maintaining
   the core while leaving any final editor/catalog composition to Astra.
3. **PNG/workflow metadata recovery** — It restores context from existing media
   and has a bounded, read-only, headless boundary. ComfyUI core is the best
   behavior reference, while a small TEGAKI-native parser avoids license and
   Asset-database coupling. UI import and auto-apply remain unimplemented.
4. **MRP region-to-prompt/mask compile representation** — It advances the
   Manga-specific where/what capability without choosing an editor layout.
   Current TEGAKI Scene/Region plus ComfyUI area/mask primitives win over the
   Forge-specific EasyReforge hook. Final MRP workspace and graph integration
   remain unimplemented.
5. **Guide/ControlNet input preparation and validation** — It prepares future
   structure/pose control safely while keeping generation out of scope.
   ComfyUI core supplies the control primitives and TEGAKI supplies Manga
   meaning. Model loading, graph execution, and final attachment composition
   remain unimplemented.

## 12. One next implementation slice

Exactly one slice is recommended; it is not implemented by this Card.

**Capability:** PNG/workflow metadata recovery

**Preferred source:** TEGAKI-NATIVE behavior-level implementation informed by
ComfyUI core's bounded PNG/safetensors metadata behavior

**Reuse strategy:** REIMPLEMENT a small core; do not copy external code

**Layer:** PURE CORE + LOCAL SERVICE

**Color / Astra coupling:** GREEN / LOW

**Proposed boundary:**

- likely pure module: `manga/service/result_metadata_recovery.mjs`;
- likely targeted tests: `manga/tests/test_result_metadata_recovery.mjs`;
- input: PNG bytes or an existing server-owned relative result locator;
- output: optional normalized prompt/workflow/model/LoRA/seed/resolution and
  provenance fields with source type;
- errors: invalid or oversized metadata, unsupported encoding, corrupt PNG, or
  foreign/unsafe locator;
- side effects: read-only; no authoring schema change, model load, queue,
  runtime, or generation;
- headless validation: byte fixtures and locator tests only.

**Forbidden integration work:** no visible import panel, no Create/Preview
layout change, no automatic settings application, no automatic generation, no
History browser redesign, no new dependency, no GPU, and no `/prompt`.

## 13. Non-goals and decision boundary

- No product implementation, UI implementation, HTML, CSS, JavaScript edit,
  runtime launch, GPU work, model download, dependency install, or internet
  download.
- No tab addition, workspace redesign, PreviewFocus implementation, final
  AttachmentCard visual system, responsive redesign, or panel ratio decision.
- No shared Manga/H3 runtime schema, timeline, supervisor, or generation state.
- No ControlNet or MRP generation integration in this inventory.
- No direct code copy from EasyReforge or external extensions.
- No new capability should be added when the current authority already owns it
  sufficiently.

The purpose of this inventory is to choose functional work that survives Astra's
later review. Astra may change composition, density, grouping, placement,
proportion, motion, or styling; the GREEN cores remain useful only when their
boundaries stay UI-independent. A capability whose usefulness depends on final
workspace flow remains YELLOW or RED.

## 14. Validation scope for this document

The Card's validation is limited to this document's diff. No product tests,
runtime, GPU, generation, model download, dependency installation, or `/prompt`
call is part of this inventory.
