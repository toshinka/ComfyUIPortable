# Manga Convenience, Resource, Replay, and Provenance Frontier Review

> **STATUS:**  
> **RESEARCH CONSOLIDATION & ARCHITECTURAL REFERENCE ONLY**  
> **DEFERRED CONVENIENCE CAPABILITY**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**  

This document consolidates external convenience-tool research and architectural findings for the **TEGAKI Manga** authoring environment. It examines generation provenance, result replay / settings recovery, missing-resource resolution, Model/LoRA library metadata, optional sidecar persistence, and future result/asset lineage.

The objective is **knowledge preservation**: documenting the lessons, risks, and authority boundaries of the modern ComfyUI extension ecosystem so future milestones do not need to rediscover these relationships from scratch.

---

## 1. Scope & Roadmap Guardrails

### 1.1 Scope
- **Domain**: Convenience, resilience, recovery, resource lookup, and provenance tools supporting the Manga authoring pipeline.
- **Ecosystem Focus**: Mature ComfyUI community nodes, metadata extractors, local-first image hubs, model resolvers, and LoRA managers.
- **Architectural Boundary**: Establishing clean separation between strict catalog authority, external metadata, user annotations, generation event provenance, and replay proposals.

### 1.2 Strict Roadmap Precedence
Convenience capabilities exist to support authoring, not to compete with core generative milestones.  
**THIS IS NOT A CURRENT IMPLEMENTATION PRIORITY.**

Active generative milestones retain strict precedence over all convenience features:
1. **Manga Controllability & Generation Reliability**
2. **Manga Regional Prompting (MRP)** compile, overlap, and mask stability
3. **Reference Appearance (CAST / IP-Adapter)** character consistency
4. **Guide / ControlNet** spatial and structural guidance
5. **Core Create Workspace & Production UI Completion**

---

## 2. Product Philosophy: Friction Removal vs. Workflow Imposition

TEGAKI evaluates convenience tools against a foundational product principle:

> **TEGAKI convenience capabilities should primarily remove work the user does not want to think about.**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CONVENIENCE EVALUATION                          │
├────────────────────────────────────┬───────────────────────────────────┤
│        HIGH-FIT (FAVOR)            │         LOW-FIT (PENALIZE)        │
├────────────────────────────────────┼───────────────────────────────────┤
│ • Silent background persistence    │ • Permanent UI/palette occupation │
│ • Mistake prevention & diagnostics │ • New workflows user must learn   │
│ • Safe, non-destructive recovery   │ • AI prompt expansion (inventing) │
│ • Exact resource identification    │ • Large, complex config surfaces  │
│ • Actions appearing ONLY on-demand │ • Duplicate resource managers     │
└────────────────────────────────────┴───────────────────────────────────┘
```

### 2.1 The Autocomplete vs. Prompt Expansion Analogy
- **Autocomplete & Danbooru Tag Conversion (High Fit)**: These remove manual typing friction, repair minor syntax slips, and bridge vocabulary gaps without overriding creator intent. The user remains in full control.
- **AI Prompt Expansion / "Idea Generators" (Low Fit as Default)**: These inject unrequested aesthetic modifiers, extra concepts, or generic tropes, corrupting the author's narrative intent and complicating reproducibility.

### 2.2 The Non-Intrusive Standard
A convenience feature is successful if the user rarely notices it operating until something goes wrong (e.g., recovering lost prompt settings after a browser reload, or identifying why a borrowed workflow fails to execute due to a missing checkpoint).

---

## 3. Current TEGAKI Baseline & Banked Contracts

TEGAKI already possesses rigorous, pure, and headless building blocks that serve as the foundation for this frontier. External tools must **never** displace or overwrite these authoritative contracts:

| TEGAKI Building Block | Code Location | Authority Boundary | Architectural Role |
| :--- | :--- | :--- | :--- |
| **Strict Catalog & Resource Resolution** | `custom_nodes_custom/tegaki_manga_nodes/basic_generation.py` | Resource Identity Authority | Exact canonical ID lookup (`CHECKPOINT`, `LORA`, `SAMPLER`, `SCHEDULER`); fail-closed; rejects ambiguous basenames and traversal. |
| **Result Metadata Recovery** | `manga/service/result_metadata_recovery.mjs` | Read-Only Extraction Authority | Extracts PNG textual chunks (`tEXt`/`iTXt`), parses ComfyUI prompt/workflow graphs, derives conservative parameter hints; zero I/O side effects. |
| **Settings Import Proposal** | `manga/service/result_settings_import.mjs` | Reviewable Proposal Authority | Converts recovered hints into a proposal object with explicit evidence classes and warning flags; proposal-only; **no silent state mutation**. |
| **Model / LoRA Metadata Enrichment** | `custom_nodes_custom/tegaki_manga_nodes/model_lora_metadata.py` | Descriptive Metadata Authority | Inspects safetensors headers for base models, training tags, and hash fingerprints for an *already-resolved* canonical path. |
| **Result / History Journal** | `manga/service/generation_journal.mjs` | Execution / Job Fact Authority | Records immutable job tokens, timestamps, validated output locators, and submitted graph digests. |

---

## 4. The Target Replay & Resolution Pipeline

The end-to-end conceptual flow links generation, provenance capture, and safe recovery:

```
[ GENERATE ]
     │
     ▼
[ PROVENANCE WRITE ] ──────────────── Embeds full generation graph, settings, & hashes into PNG
     │
     ▼
[ RESULT FILE / JOURNAL ] ─────────── Persistent disk artifact & immutable job history record
     │
     ▼
[ METADATA RECOVERY ] ─────────────── Read-only extraction from PNG chunks (ResultMetadataRecovery)
     │
     ▼
[ REPLAY PROPOSAL ] ───────────────── Structured diff showing candidate vs current authoring state
     │
     ▼
[ STRICT CATALOG RESOLUTION ] ─────── Verifies exact local presence of checkpoint & LoRA assets
     │
     ├───────────────────────────────► [ MISSING RESOURCE DIAGNOSTIC / RESOLVER ]
     ▼                                      (Hash check, remote lookup, user-confirmed fetch)
[ USER-CONFIRMED STATE RESTORE ]
```

*Parallel Auxiliary*: **Model / LoRA Library** (on-demand browser for browsing, tagging, and previewing available assets).  
*Late-Stage Extension*: **Result History & Asset Lineage** (tracking derived variations, inpaint iterations, and page layout usage).

---

## 5. Generation Provenance Writer

### 5.1 External Teachers
- **ComfyUI Image Saver Family** (e.g., standard `SaveImage`, `ComfyUI-Image-Saver`): Teaches standardized embedding of prompt JSON, extra metadata, and formatted subfolders.
- **SeeSee Civitai Metadata / Graph Tracing Nodes**: Teaches automatic inspection of upstream model loaders, LoRA stacks, and samplers to synthesize Civitai-compatible generation parameters without manual node wiring.

### 5.2 Key Architectural Lessons
- **Rich Parameter Envelope**: A generation result must retain: positive prompt, negative prompt, seed, steps, CFG, sampler name, scheduler name, model identity/hash, LoRA identities/strengths/hashes, and source workflow digest.
- **Zero-Friction In-Product Provenance**: Creators must **never** be forced to manually route metadata wires across a spaghetti graph to record provenance. In TEGAKI, the backend service layer and custom generation router already know the complete compilation state and must act as the primary provenance writer.
- **Classification**: **HIGH-VALUE FUTURE CAPABILITY** (TEGAKI-native contract candidate; external implementations serve as behavior references).

---

## 6. Result Replay & Settings Recovery

### 6.1 The Proposal-Only Rule
Recovered metadata must **never silently overwrite** current authoring state. A creator may have spent 20 minutes refining a complex multi-region Scene; dropping an old image into the canvas must not destroy that work.

```
Recovered File ──► [ Read & Normalize ] ──► [ Generate Proposal ] ──► [ Review Diff Modal ] ──► [ User Applies ]
                                                                             │
                                                                       Reject Changes
```

### 6.2 Strict Anti-Patterns to Reject
- **No Silent Substitution**: Never swap `illustrious-v0.1` for `illustrious-v1.0` without explicit notice.
- **No Basename Guessing**: A file named `lora_style.safetensors` in a different directory must not be blindly assumed to match an ambiguous `lora_style`.
- **No Unconfirmed State Overwrite**: All fields must display provenance, evidence tier (`EXPLICIT_GRAPH`, `EXTRACTED_HINT`, `FALLBACK`), and diff status.

### 6.3 Progressive Replay Levels
1. **Level A — Generation Settings Replay (Near-Term)**: Recovers flat generation parameters (prompt, negative prompt, checkpoint, LoRAs, seed, steps, sampler, CFG, dimensions).
2. **Level B — Workflow Replay (Intermediate)**: Restores the exact ComfyUI execution graph. Valuable for debugging, but does not reconstruct authoring semantics.
3. **Level C — TEGAKI Authoring Replay (Long-Path Reserve)**: Fully restores Scenes, CAST identities, Reference Appearance anchors, MRP regional boundaries, and Guide references. *Level C is not currently implemented and remains a reserved goal.*

---

## 7. Missing Resource Resolution

### 7.1 Primary External Teacher: ComfyUI-ModelResolver
- **Repository**: [`https://github.com/21omen/ComfyUI-ModelResolver`](https://github.com/21omen/ComfyUI-ModelResolver)
- **Key Concepts Taught**:
  - Scans execution graphs to extract only *strictly required* model resources.
  - Distinguishes between genuinely missing files and files present-but-renamed (via SHA-256 / BLAKE3 hashes).
  - Queries multiple remote registries (Civitai, HuggingFace) by hash to identify exact source assets.
  - Enforces verified downloads into temporary quarantine before moving to production directories.
  - Surface clear diagnostic summaries showing ambiguous or unresolved assets.

### 7.2 The TEGAKI Iron Law: "Related != Exact"
A resolver must complement TEGAKI's strict catalog, never undermine it:
- **Never silently substitute**:
  - Different checkpoint revisions or pruned vs full weights.
  - Different LoRA training epochs or versions.
  - Converted or quantized derivatives (e.g., GGUF vs fp16).
  - Cross-architecture models (e.g., SDXL vs Illustrious vs SD 1.5).
- **Classification**: **STRONG ENGINE / UX TEACHER** (High value as a future optional diagnostic helper; not a current implementation milestone).

---

## 8. Model & LoRA Library Management

### 8.1 Primary External Teacher: ComfyUI-LoRA-Manager
- **Repository**: [`https://github.com/willmiao/ComfyUI-Lora-Manager`](https://github.com/willmiao/ComfyUI-Lora-Manager)
- **Key Concepts Taught**:
  - Visual card-based browsing with thumbnail previews and trained trigger words.
  - Inspection of embedded safetensors metadata (base model architecture, training rank).
  - User notes, custom usage tips, recommended strength ranges, and favorite toggles.
  - Association of local files with external Civitai/HuggingFace model IDs.

### 8.2 Authority Separation in Library Management
A common pitfall in community managers is collapsing file facts, remote descriptions, and user notes into a single mutable blob. TEGAKI enforces strict separation:
1. **Physical File**: Read-only binary safetensors asset on disk.
2. **Embedded Header**: Immutable metadata written by the trainer (rank, base model, training epochs).
3. **External Registry Data**: Remote descriptions, sample gallery, and community ratings.
4. **User Annotations**: Personal notes, favorite status, preferred trigger words, and calibrated weights.

### 8.3 UX Surface Discipline
- **No Permanent Create Workspace Invasion**: A 500-item LoRA gallery must **never** permanently occupy the main Create canvas.
- **On-Demand Drawer or Modal**: Library browsing belongs in an on-demand drawer, popup palette, or dedicated secondary management surface.
- **Classification**: **STRONG UX / METADATA TEACHER** (Separate-surface candidate; strictly decoupled from runtime execution authority).

---

## 9. Sidecar Metadata Persistence

### 9.1 External Teacher: ComfyUI-Save-Separate-Metadata
- **Repository**: [`https://github.com/Kuroi961/ComfyUI-Save-Separate-Metadata`](https://github.com/Kuroi961/ComfyUI-Save-Separate-Metadata)
- **Concept**: Emits a companion `.json` file alongside each generated image containing full prompt, execution, and environment metadata.

### 9.2 Trade-off Analysis
- **Advantages**: Text-editor readable, fully archivable, completely immune to metadata stripping caused by external image editors (Photoshop/CSP often strip PNG `tEXt` chunks upon saving), easily indexed by external tools.
- **Weaknesses**: Vulnerable to desynchronization (moving or renaming the image breaks the link; disk file clutter).
- **TEGAKI Policy**: **Sidecar JSON is an OPTIONAL REDUNDANCY STRATEGY**, not a replacement for embedded PNG chunks or the internal Generation Journal. *Implementation is deferred.*

---

## 10. WebP Output Strategy: Deferred Optimization

### 10.1 Technical Potential vs Priority Reality
- **The Promise**: WebP offers 25–40% smaller file sizes compared to PNG, supports lossless compression, and can embed EXIF/XMP metadata chunks.
- **The Architectural Decision**: **WEBP-FIRST OUTPUT IS DEFERRED.**
- **Rationale**: Debugging metadata extraction across diverse image readers is substantially easier on standard PNG. Current engineering capacity must remain focused on making generation, regional conditioning, and recovery 100% reliable on PNG first before spending resources on image container transitions.
- **Classification**: **TECHNICALLY PROMISING, LOW CURRENT PRIORITY, DEFER.**

---

## 11. Result History, Asset Promotion, and Lineage

### 11.1 Primary External Teacher: Image MetaHub
- **Repository**: [`https://github.com/LuqP2/Image-MetaHub`](https://github.com/LuqP2/Image-MetaHub)
- **Key Concepts Taught**:
  - Local-first background indexing of output directories.
  - Multi-parameter search (filter by prompt keyword, checkpoint, sampler, or rating).
  - Lineage tracking: parent-to-child relationships across img2img, inpaint, and upscale iterations.
  - Re-hydration of historical generation state back into active workflows.

### 11.2 The Production Asset Lifecycle
In manga authoring, an image is not merely a terminal gallery item; it has a lifecycle:

```
[ Raw Generation Result ]
            │
            ▼ (author tags / stars / selects)
[ Candidate Selection ]
            │
            ▼ (promoted to character reference, scene asset, or guide)
[ Tracked Production Asset ]
            │
            ▼ (inserted into physical page)
[ Page / Panel Layout Placement ]
```

- **Policy**: Deep asset lineage and media management belong to a later production milestone. TEGAKI will not attempt to build a full standalone digital asset manager (DAM) today.
- **Classification**: **STRONG FUTURE ASSET/HISTORY TEACHER; DEFER IMPLEMENTATION.**

---

## 12. Forge / Automatic1111 Migration & Knowledge Preservation

### 12.1 The Migration Friction Risk
Creators transitioning from Automatic1111 or WebUI-Forge into ComfyUI frequently experience severe dislocation:
- Familiar prompt weighting conventions differ.
- Hand-curated LoRA combinations, trigger word collections, and tested model recipes are lost or scattered.
- The cognitive burden of node graphs replaces familiar single-page form controls.

### 12.2 The Illustrious Preservation Directive
Current TEGAKI Manga production is centered on the **Illustrious-XL / SDXL** architecture.  
- **Core Directive**: Save sufficient structured provenance now so that favorite recipes, character trigger words, and working LoRA weights remain permanently recoverable without relying on human memory.
- *Boundary*: This does NOT authorize building broad backward-compatibility converters for arbitrary WebUI scripts or extensions.

---

## 13. Ultra-Long-Path Architecture Guard: Anima & Cross-Model Migration

- **Concept**: Future foundation model transitions (e.g., migrating weights or LoRAs across disparate architectures via Activation Capture or latent alignment).
- **Policy Guardrail**: **ULTRA-LONG-PATH / RESEARCH WATCH ONLY.**
- **Rules**:
  - No Activation Capture code or experiments.
  - No Anima model integration.
  - No cross-architecture weight conversion tooling.
  - Maintain absolute focus on stabilizing TEGAKI's current Illustrious ComfyUI production path.

---

## 14. Strict Architectural Authority Separation

To prevent cross-subsystem pollution, TEGAKI enforces non-overlapping authority boundaries across all resource concepts:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AUTHORITY BOUNDARY MAP                          │
├──────────────────────────┬─────────────────────────────────────────────┤
│ Concern                  │ Authoritative Owner / Layer                 │
├──────────────────────────┼─────────────────────────────────────────────┤
│ Resource Identity        │ TEGAKI Strict Catalog (Canonical IDs)       │
│ External Metadata        │ Source Registries (Civitai / HuggingFace)   │
│ User Notes & Favorites   │ Local Author Annotation Store               │
│ Generation Provenance    │ Generation Service & Written Image Metadata │
│ Replay Proposal          │ Result Settings Import (Non-destructive)   │
│ Missing Resource Fetch   │ Operational Resolver Helper (Quarantine)    │
│ Asset Lineage            │ Future Studio Asset Manager                 │
└──────────────────────────┴─────────────────────────────────────────────┘
```

**Anti-Pattern Warning**: Do not merge these into a monolithic `ModelInfo` or `ResourceRecord` object where catalog identity, remote descriptions, and user notes overwrite each other.

---

## 15. Candidate Classification & Comparative Analysis

| Project / Family | TEGAKI Classification | What It Teaches | What NOT to Import | UI / Runtime Cost | Affinity with TEGAKI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ComfyUI Image Saver Family** | `TEACHER` / `TEGAKI-NATIVE CANDIDATE` | Standardized parameter embedding, prompt chunk serialization. | Spaghetti node wiring; complex custom token formatters. | Low UI cost; backend write operation. | **HIGH** (Matches TEGAKI GenerationService). |
| **SeeSee Civitai Metadata** | `TEACHER` / `PATTERN ONLY` | Graph-tracing parameter synthesis; Civitai hash generation. | In-graph metadata node chains; heavy external API dependencies. | Zero UI cost; graph inspection utility. | **HIGH** (Automates provenance extraction). |
| **ComfyUI-ModelResolver** | `STRONG ENGINE TEACHER` / `OPTIONAL HELPER` | Hash-based asset identification, remote source matching, quarantine fetch. | Silent model swapping; auto-downloading unverified weights without consent. | Low (on-demand modal during workflow failure). | **HIGH** (Direct complement to strict catalog). |
| **ComfyUI-LoRA-Manager** | `STRONG UX TEACHER` / `SEPARATE SURFACE` | Visual card browsing, trigger word display, user annotation tagging. | Massive permanent galleries embedded inside generation canvas; complex custom databases. | High if permanent; Low if an on-demand drawer. | **MEDIUM** (Belongs in separate resource drawer). |
| **ComfyUI-Save-Separate-Metadata** | `REFERENCE ONLY` / `DEFER` | Resilient sidecar JSON pairing; protection against metadata-stripping editors. | Two-file disk management; cluttering storage directories. | Zero UI cost; filesystem redundancy. | **LOW** (Secondary to embedded PNG chunks). |
| **Image MetaHub** | `FUTURE ASSET TEACHER` / `DEFER` | Local-first metadata indexing, search filtering, img2img lineage tracking. | Standalone desktop app complexity; premature full-featured DAM. | High if embedded; distinct downstream workspace. | **HIGH (Long-Term)** (Informs future Asset layer). |

---

## 16. Recommended Capability Sequence

Without authorizing current development, future convenience capability integration should proceed in this logical sequence:

```
[ Phase 1: Provenance Write ] ────────── Embed full parameters into generated PNGs automatically
           │
           ▼
[ Phase 2: Replay / Recovery ] ───────── Complete non-destructive Settings Import Proposal UX
           │
           ▼
[ Phase 3: Missing Resource Resolver ] ── Hash-based missing asset diagnostics & verified lookup
           │
           ▼
[ Phase 4: Model / LoRA Library ] ────── On-demand browser for tags, notes, and trigger words
           │
           ▼
[ Phase 5: Asset Promotion & Lineage ] ─ Track selected outputs into reusable production assets
```

*(WebP container optimization remains strictly outside this linear progression until PNG paths are fully mature).*

---

## 17. Open Architectural Questions

The following questions remain unresolved and should guide future bounded investigations:

1. **Minimum Provenance Envelope**: What is the strict minimum set of fields required in every output PNG to guarantee Level A settings recovery without bloating file headers?
2. **Embedded Chunks vs Journal Authority**: When a discrepancy occurs between an on-disk PNG's embedded metadata and the server's internal `GenerationJournal`, which source represents ground truth?
3. **Quarantine & Safety Policy**: Where should an automated resolver stage downloaded models before strict catalog validation promotes them to production model directories?
4. **Sidecar Necessity**: Do user workflows in external tools (e.g., Photoshop/CSP stripping PNG metadata) justify offering an optional `.json` sidecar toggle?
5. **Exact Hash Representation**: Should TEGAKI standardize on SHA-256 (matching existing `canonical_serialization`) or adopt BLAKE3 (matching modern Civitai/ComfyUI model hashing)?
6. **Library Surface Boundary**: Should the LoRA/Model library exist as a slide-out drawer inside Create, or as a distinct workspace accessible via shell navigation?
7. **Transient vs Stored Metadata**: Should external Civitai metadata (descriptions, previews) be cached locally in a lightweight database or queried strictly on-demand?
8. **Lineage Transition Boundary**: At what exact moment does an ephemeral generation "Result" become an immutable "Asset" eligible for page panel placement?

---

## 18. Next Strategic Direction

Following this consolidation, architectural authority returns to the Commander.  
Future investigations may choose between:
- **Direction A**: Deeper technical extraction of `ComfyUI-ModelResolver` / `ComfyUI-LoRA-Manager` hash lookup and metadata parsing logic.
- **Direction B**: Focused UI interaction study for the on-demand Settings Replay Diff Modal.

*No further convenience work, Anima research, or WebP optimization is authorized at this time.*
