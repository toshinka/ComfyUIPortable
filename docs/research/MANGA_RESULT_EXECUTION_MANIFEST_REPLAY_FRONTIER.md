# Manga Result Execution Manifest & Replay Frontier Review

> **STATUS:**  
> **RESEARCH CONSOLIDATION & SEMANTIC ARCHITECTURE ONLY**  
> **DEFERRED CONVENIENCE CAPABILITY**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**  

This document defines the research-level semantic architecture for a future **TEGAKI Execution Manifest** supporting **Result Replay**. It establishes the theoretical boundaries, data taxonomy, and recovery rules necessary to inspect an older generated image and reliably reconstruct the recipe and conditioning that created it.

---

## 1. Purpose, Primary Scenario & Limits

### 1.1 The Primary User Scenario
A creator reviewing past work encounters a superior generation:
> *"This image/page was better than my recent results. How did I make it, and can I continue from there?"*

The goal of the **Execution Manifest** is to provide an authoritative, compact receipt of the exact parameters, models, and conditioning inputs used to generate that image, allowing TEGAKI to propose a faithful replay without requiring the author to manually remember, guess, or reconstruct settings.

### 1.2 What the Execution Manifest Is NOT
To prevent architectural scope creep, the Execution Manifest is explicitly bounded:
- ❌ **NOT the full `AuthoringDocument`**: It does not record unrendered scenes, camera drafts, canvas layout hierarchies, or narrative story metadata.
- ❌ **NOT the full ComfyUI workflow**: It does not record arbitrary node positions, UI canvas coordinates, execution plumbing, or internal virtual links.
- ❌ **NOT a settings file**: It is not a mutable preset, template, or default configuration profile.
- ❌ **NOT a history database**: It is not a database engine, timeline manager, or asset management catalog.

It is conceptually: **A compact, immutable receipt describing what actually ran for one generation event.**

### 1.3 Strict Roadmap Precedence
Convenience, resilience, and replay capabilities exist strictly to assist the creative process; they must not divert implementation resources away from active generative milestones.  
**THIS IS NOT A CURRENT IMPLEMENTATION PRIORITY.**

Active generative milestones retain absolute precedence:
1. **Manga Controllability & Generation Reliability**
2. **Manga Regional Prompting (MRP)** compile, overlap, and mask stability
3. **Reference Appearance (CAST / IP-Adapter)** character consistency
4. **Guide / ControlNet** spatial and structural layout guidance
5. **Core Create Workspace & Production UI Completion**

---

## 2. Central Distinction: The Four Pillars

State management in generative art frequently suffers from conflating authoring intent with execution plumbing. TEGAKI enforces four distinct concepts:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          THE FOUR PILLARS                              │
├───────────────────┬────────────────────────────────────────────────────┤
│ CONCEPT           │ DEFINITION & BOUNDARY                              │
├───────────────────┼────────────────────────────────────────────────────┤
│ AUTHORING STATE   │ What the user is currently editing in the UI       │
│                   │ (pages, scenes, characters, draft prompt text).    │
├───────────────────┼────────────────────────────────────────────────────┤
│ WORKFLOW          │ How the execution graph is wired and assembled     │
│                   │ (node types, link topologies, custom node wiring). │
├───────────────────┼────────────────────────────────────────────────────┤
│ EXECUTION         │ What values, resources, and conditioning actually  │
│ MANIFEST          │ resolved and executed for one specific generation. │
├───────────────────┼────────────────────────────────────────────────────┤
│ RESULT ARTIFACT   │ The generated media file (e.g. PNG/WebP) that      │
│                   │ carries or links to the Execution Manifest.        │
└───────────────────┴────────────────────────────────────────────────────┘
```

### Core Principle: `WORKFLOW != EXECUTION MANIFEST`
- A **Workflow** describes *mechanism* (e.g. "Take CLIP text encode node #14 and route conditioning into KSampler node #3"). Workflows are brittle: if custom nodes update, node IDs shift, or engines change, older workflows become unrunnable.
- An **Execution Manifest** describes the *resolved event* (e.g. "Generated with checkpoint hash `abc123`, prompt '1girl, silver hair', seed `42`, sampler `euler`").
- The manifest survives engine rewrites, node deprecations, and custom node replacements.

---

## 3. The Replay Priority Ladder

Replay capabilities are categorized into three conceptual tiers based on product value and technical feasibility:

```
┌────────────────────────────────────────────────────────────────────────┐
│                         REPLAY PRIORITY LADDER                         │
├────────────────────────────────────────────────────────────────────────┤
│ LEVEL 1: RECIPE RECOVERY ───► PRIMARY PRODUCT VALUE                    │
│   • Base model checkpoint (canonical ID + hash)                        │
│   • LoRA models and exact applied weights                              │
│   • Final resolved positive & negative prompts                         │
│   • Core sampling: seed, steps, CFG, sampler, scheduler, denoise       │
│   • Resolution: width, height                                          │
├────────────────────────────────────────────────────────────────────────┤
│ LEVEL 2: CONDITIONING RECOVERY ───► HIGH-VALUE EXTENSION               │
│   • MRP / Regional conditioning bounds, prompts, & strengths           │
│   • Guide / ControlNet kinds, settings, & referenced source assets     │
│   • Reference Appearance (CAST) assets & conditioning weights          │
│   • Resolved wildcard / dynamic prompt expansions                      │
├────────────────────────────────────────────────────────────────────────┤
│ LEVEL 3: FULL AUTHORING RECOVERY ───► LONG-TERM / DEFER                │
│   • Entire multi-page authoring document structure                     │
│   • CAST library state and unreferenced character definitions          │
│   • Full scene editor hierarchy, camera angles, and UI viewport        │
│   • Workspace panels and scratchpad state                              │
└────────────────────────────────────────────────────────────────────────┘
```

- **Level 1 (Recipe)** delivers 80% of user value: the user can immediately replicate the artistic style, character baseline, and generation quality.
- **Level 2 (Conditioning)** ensures complex multi-subject or guided scenes do not degrade into unconditioned single-subject outputs upon replay.
- **Level 3 (Full Authoring)** is out of scope for single-image replay and belongs to document-level backup/snapshot architectures.

---

## 4. Resolved Execution Values vs. User Input

A foundational requirement for high-fidelity replay is:

> **SAVE THE VALUE THAT ACTUALLY RAN.**

Where input and execution diverge, the manifest must record the final resolved value, while optionally preserving the input token as provenance context:

```
┌───────────────────┬─────────────────────────┬─────────────────────────┐
│ PARAMETER         │ USER / AUTHORING INPUT  │ RESOLVED EXECUTION      │
├───────────────────┼─────────────────────────┼─────────────────────────┤
│ Dynamic Wildcard  │ "__hair_color__, smile" │ "silver hair, smile"    │
│ Seed Mode         │ "randomize" (-1)        │ 84920491823             │
│ LoRA Weight Slider│ 0.85 (UI state)         │ 0.85000000 (Compiled)   │
│ Regional Prompt   │ Page global + Scene text│ Concatenated & parsed   │
└───────────────────┴─────────────────────────┴─────────────────────────┘
```

- **Wildcard Expansion**: If the manifest only recorded `__hair_color__`, replaying the image might produce "green hair" instead of the "silver hair" that made the original generation great. The resolved text (`silver hair`) is essential for visual reproducibility.
- **Seed Resolution**: Replay requires the concrete numerical seed integer (`84920491823`). An import proposal can then present this exact seed with an option to apply it in fixed mode.

---

## 5. Core Recipe Manifest Envelope

The Level 1 Recipe envelope comprises the fundamental diffusion parameters. Each field is evaluated by necessity:

| Manifest Field | Classification | Replay Role & Strict Constraint |
| :--- | :--- | :--- |
| **final_positive_prompt** | `ESSENTIAL` | Complete, fully resolved positive prompt string sent to text encoder. |
| **final_negative_prompt** | `ESSENTIAL` | Complete negative prompt string sent to text encoder. |
| **seed** | `ESSENTIAL` | Concrete 64-bit integer seed actually sampled by the backend. |
| **steps** | `ESSENTIAL` | Total sampling steps executed. |
| **cfg** | `ESSENTIAL` | Classifier-Free Guidance scale. |
| **sampler_name** | `ESSENTIAL` | Canonical sampler identifier (e.g. `euler_ancestral`). |
| **scheduler** | `ESSENTIAL` | Canonical scheduler identifier (e.g. `normal`, `karras`). |
| **width** | `ESSENTIAL` | Generated image width in pixels. |
| **height** | `ESSENTIAL` | Generated image height in pixels. |
| **checkpoint** | `ESSENTIAL` | Canonical ID and content hash of the base diffusion model. |
| **loras** | `ESSENTIAL` | List of applied LoRAs with canonical IDs, hashes, and model/clip weights. |
| **denoise** | `USEFUL` | Denoising strength (critical for img2img, upscale, or continuation). |
| **clip_skip** | `USEFUL` | Stop layer for CLIP text encoder if modified from model default. |
| **latent_dimensions** | `OPTIONAL` | Latent width/height before VAE decode (usually derived from width/height). |
| **vae_name** | `OPTIONAL` | Separate VAE model identity if an external VAE was loaded. |

---

## 6. Strict Resource Identity & Hashing Architecture

TEGAKI maintains a strict fail-closed resource identity policy:

> **NO SILENT SUBSTITUTION. NO BASENAME GUESSING.**

A resource reference in an Execution Manifest must distinguish between an advisory hint and an authoritative identifier:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RESOURCE IDENTIFIER MODEL                       │
├───────────────────┬────────────────────────────────────────────────────┤
│ FIELD             │ ROLE & AUTHORITY                                   │
├───────────────────┼────────────────────────────────────────────────────┤
│ canonical_id      │ Primary local identifier (e.g. "illustrious-xl-v1")│
├───────────────────┼────────────────────────────────────────────────────┤
│ content_hash      │ Strong content fingerprint (SHA-256 or truncated   │
│                   │ 16-hex prefix). Authoritative identity proof.      │
├───────────────────┼────────────────────────────────────────────────────┤
│ filename_hint     │ Advisory basename (e.g. "illustriousXL_v01.safetensors")│
│                   │ strictly a fallback hint for user diagnostics.     │
├───────────────────┼────────────────────────────────────────────────────┤
│ applied_weight    │ Exact numerical float used for model and clip.     │
└───────────────────┴────────────────────────────────────────────────────┘
```

- **Replay Validation**: When replaying an old manifest, TEGAKI queries its local catalog. If a file with the same basename exists but its content hash differs, TEGAKI flags an `AMBIGUOUS_RESOURCE` warning and requires user confirmation. It will **never** silently execute with an altered checkpoint.

---

## 7. Hash Cost & Caching Architecture

Computing cryptographic hashes (e.g. full SHA-256) over 6 GB checkpoint files takes 5–15 seconds per file on standard NVMe drives and much longer on HDDs.

> **RESOURCE HASHING MUST NOT REQUIRE REHASHING LARGE FILES EVERY GENERATION.**

### Verified Ecosystem Patterns:
1. **Hash on Catalog Ingest**: Calculate and store the model hash once during catalog indexing or first discovery.
2. **Metadata Cache Integration**: Store model hashes alongside header metadata (base model, trigger tags) in TEGAKI's local metadata cache (`model_lora_metadata.py`).
3. **Existing Hash Sidecars**: Respect existing SHA-256 files (`.sha256`), Civitai model cache entries, or safetensors embedded header hashes when available.
4. **Fast Header Fingerprints**: For runtime verification, combine file size + modification timestamp + header hash before resorting to a full payload rehash.

---

## 8. Manga Regional Prompting (MRP) Semantic Manifest

MRP is structured semantic data. For rectangular regions, it does **not** require raster image assets.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MRP SEMANTIC SPECIFICATION                      │
├─────────────────┬──────────────────────────────────────────────────────┤
│ FIELD           │ SEMANTIC DEFINITION                                  │
├─────────────────┼──────────────────────────────────────────────────────┤
│ region_id       │ Stable identifier (e.g. "scene_1_region_A")          │
├─────────────────┼──────────────────────────────────────────────────────┤
│ canonical_area  │ Normalized coordinates: {x, y, w, h} within [0..1]   │
├─────────────────┼──────────────────────────────────────────────────────┤
│ prompt          │ Resolved positive text specific to this region       │
├─────────────────┼──────────────────────────────────────────────────────┤
│ negative_prompt │ Resolved negative text specific to this region       │
├─────────────────┼──────────────────────────────────────────────────────┤
│ strength        │ Numerical influence weight (0.0 to 1.0)              │
├─────────────────┼──────────────────────────────────────────────────────┤
│ order           │ Deterministic sorting index                          │
└─────────────────┴──────────────────────────────────────────────────────┘
```

### Engine Swappability Principle
- **Semantic Truth**: The manifest records *what* the author intended spatially: "Region A [0.0, 0.0, 0.5, 1.0] contains 'hero, shouting'".
- **Runtime Hint**: The manifest records the engine used as an advisory hint: `engine_hint: "prompt_control_attention_couple"`.
- If TEGAKI later migrates to native ComfyUI mask conditioning or an alternative regional sampler, the semantic manifest remains 100% intelligible and re-compilable.

---

## 9. Guide / ControlNet Conditioning Manifest

Guide conditioning combines numerical settings with visual structural inputs:

```
[ Source Image ] ──► [ Preprocessor ] ──► [ Processed Control Image ] ──► [ ControlNet ]
 (e.g. Photo/Line)   (e.g. DWPose/Canny)    (e.g. Pose Skeleton)
```

### 9.1 Three Replay Fidelity Levels

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GUIDE REPLAY FIDELITY                           │
├───────────┬────────────────────────────────────────────────────────────┤
│ LEVEL     │ PREREQUISITES & FIDELITY                                   │
├───────────┼────────────────────────────────────────────────────────────┤
│ BEST      │ Processed control image is available (via asset hash).     │
│           │ Bypasses preprocessor drift; 100% deterministic guidance.  │
├───────────┼────────────────────────────────────────────────────────────┤
│ GOOD      │ Source image available + preprocessor settings available.  │
│           │ Preprocessor runs again to regenerate control image.       │
├───────────┼────────────────────────────────────────────────────────────┤
│ PARTIAL   │ ControlNet settings/model available, but images missing.   │
│           │ Recovers strength, timing, and model; user must provide    │
│           │ a new guide image.                                         │
└───────────┴────────────────────────────────────────────────────────────┘
```

### 9.2 Manifest Representation
- `guide_kind`: Semantic type (`POSE`, `LINE`, `DEPTH`, `ROUGH_MANGA`).
- `source_asset_ref`: Hash-based reference to original input asset.
- `processed_asset_ref`: Optional reference to preprocessed control map.
- `control_model`: Canonical ID and hash of the ControlNet model.
- `strength`, `start_percent`, `end_percent`: Standard guidance timing parameters.

---

## 10. Reference Appearance (CAST) Manifest

Reference Appearance (character visual identity via IP-Adapter) requires referencing character portrait assets:

### 10.1 Core Policy: References by Hash, Not Base64
- **DO NOT** embed multi-megabyte reference images as base64 strings inside the image's textual metadata chunks.
- **DO** reference external assets by content hash and internal workspace locator (`reference_asset: "sha256:7f8a9b..."`, `hint: "cast_hero_front.png"`).

### 10.2 Decoupling Semantic CAST from Runtime IP-Adapter
- **Semantic Record**: Identifies the character appearance reference: `cast_id: "hero_ren"`, `asset_ref: "sha256:..."`, `spatial_scope: "region_A"`.
- **Runtime Hint**: `adapter_kind: "ip_adapter_plus_sdxl"`, `weight: 0.75`, `weight_type: "ease_in_out"`.
- The semantic identity intent is preserved even if the IP-Adapter implementation changes.

---

## 11. The Asset Reference Table Concept

To prevent redundant asset metadata when multiple conditioning channels (e.g. two Guide poses and three Reference portraits) use the same files, the Execution Manifest defines an **Asset Reference Table**:

```json
{
  "assets": {
    "asset_ref_01": {
      "content_hash": "sha256:d41d8cd98f00b204e9800998ecf8427e...",
      "filename_hint": "chara_alice_concept.png",
      "dimensions": [1024, 1536],
      "media_type": "image/png",
      "semantic_role": "reference_appearance"
    },
    "asset_ref_02": {
      "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
      "filename_hint": "panel_3_pose_wire.png",
      "dimensions": [768, 1024],
      "media_type": "image/png",
      "semantic_role": "guide_source"
    }
  }
}
```

### Architectural Benefits:
1. **Deduplication**: Multiple references to the same asset point to a single table key.
2. **Rename Resilience**: If the user renamed `alice_final.png` to `alice_v2.png`, the file can still be located instantly across local asset libraries via its `content_hash`.
3. **Asset Library Affinity**: Bridges cleanly into future TEGAKI asset-management systems.

---

## 12. Component Recovery States: Tolerating Partial Recovery

Replay in the real world is rarely all-or-nothing. Users delete LoRAs, move models across disks, or update pipelines.

> **DO NOT TREAT REPLAY AS BINARY SUCCESS / FAILURE.  
> DO NOT INVENT A SYNTHETIC PERCENTAGE REPLAY SCORE.**

Every recovered component receives an explicit, qualitative state label:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        COMPONENT RECOVERY STATES                       │
├─────────────────┬──────────────────────────────────────────────────────┤
│ STATE           │ MEANING & SYSTEM ACTION                              │
├─────────────────┼──────────────────────────────────────────────────────┤
│ EXACT           │ Hash-verified exact match found locally. Ready.      │
├─────────────────┼──────────────────────────────────────────────────────┤
│ RECOVERED       │ Value recovered directly from metadata (e.g. steps). │
├─────────────────┼──────────────────────────────────────────────────────┤
│ PARTIAL         │ Parameters recovered, but dependent asset missing    │
│                 │ (e.g. Guide settings present, guide image missing).  │
├─────────────────┼──────────────────────────────────────────────────────┤
│ MISSING         │ Resource unavailable locally (e.g. LoRA deleted).    │
│                 │ Clearly flagged in proposal; requires resolution.    │
├─────────────────┼──────────────────────────────────────────────────────┤
│ AMBIGUOUS       │ Multiple conflicting candidates or basename matches  │
│                 │ with differing hashes. Requires user disambiguation. │
├─────────────────┼──────────────────────────────────────────────────────┤
│ UNSUPPORTED     │ Metadata field recognized but cannot be executed by  │
│                 │ current local engine.                                │
└─────────────────┴──────────────────────────────────────────────────────┘
```

---

## 13. Qualitative Replay Confidence Model

Confidence in a replayed setting reflects the authenticity of its source:

```
[ EXACT HASH MATCH ]          ──► Highest confidence: mathematically identical model/asset.
[ DIRECT METADATA VALUE ]     ──► High confidence: explicitly recorded in TEGAKI manifest.
[ WORKFLOW-DERIVED ]          ──► Medium confidence: parsed from ComfyUI node graphs.
[ HEURISTIC / BEST-EFFORT ]   ──► Low confidence: inferred from A1111/Forge raw text blocks.
[ MISSING ]                   ──► Zero confidence: unavailable.
```

### Non-TEGAKI External Image Fallback Hierarchy
When ingesting an external image created outside TEGAKI, the recovery service applies a graceful fallback ladder:
1. **ComfyUI `prompt` JSON**: Parse exact input dictionary submitted to execution engine.
2. **ComfyUI `workflow` JSON**: Parse visual node graph widgets where `prompt` chunk is missing.
3. **A1111 / Forge Parameter Text**: Regular expression parsing of standard `parameters` chunk (`Steps: 20, Sampler: Euler a, CFG scale: 7...`).
4. **Advisory Posture**: For external images, TEGAKI marks all recovered fields as `HEURISTIC / BEST-EFFORT` and warns the user that reproducibility is approximate.

---

## 14. The Role of ComfyUI Workflow Storage

While the Execution Manifest is the primary replay authority, the raw ComfyUI `workflow` metadata remains useful as a secondary diagnostic record.

### Why Workflow Cannot Be the Sole Replay Authority:
1. **Graph Churn**: Internal node implementations change, inputs are renamed, and links break across ComfyUI versions.
2. **Custom Node Loss**: If an external node pack is uninstalled, the entire workflow becomes un-loadable in ComfyUI, even if the core diffusion parameters are standard.
3. **Dynamic Discrepancy**: A workflow node might display `Seed: -1` (randomize), whereas the manifest records the actual generated seed `84920491823`.

**Rule**: Store workflow metadata as an optional diagnostic appendix, but rely on the Execution Manifest as the operational replay contract.

---

## 15. The Provenance Lifecycle & Write Point

Where should provenance be recorded?

```
[ Authoring State ]
        │
        ▼
[ Compile Regional & Guide Directives ]
        │
        ▼
[ Resolve Runtime Values & Generate Concrete Request ]
        │
        ▼
[ CONSTRUCT EXECUTION MANIFEST ] ──► (Snapshot of what is being submitted)
        │
        ▼
[ Execute Generation via Engine (/prompt) ]
        │
        ▼
[ Image Generated & Saved ]
        │
        ├───────────────────────────────────────────────┐
        ▼                                               ▼
[ ATTACH TO MEDIA METADATA ]               [ RECORD IN INTERNAL JOURNAL ]
  (Portable PNG/WebP chunk)                  (Local GenerationJournal)
```

### Storage Channel Division of Labor:
- **Embedded Media Metadata**: Travels everywhere with the image file; enables zero-configuration single-file import.
- **Internal Generation Journal**: Preserves richer local history, job execution durations, exact disk locators, and links to authoring document IDs.
- **Optional Sidecar (`.json`)**: Serves as a redundancy safety net if images are run through external graphic optimization tools that strip EXIF/PNG chunks.

---

## 16. Privacy, Security & Local Path Scrubbing

A generated image may be published, shared, or distributed publicly. Execution metadata must respect user privacy:

### 16.1 Local Path Privacy Rule
> **DO NOT REQUIRE OR LEAK ABSOLUTE LOCAL PATHS IN PORTABLE RESULT METADATA.**

- **Forbidden**: `D:\Users\Alice\Documents\SecretProject\models\loras\hero_v2.safetensors`
- **Permitted**: `hero_v2.safetensors` (basename hint) + `sha256:c0ffee1234...` (content hash).
- Absolute filesystem paths expose personal usernames, folder hierarchies, and operating system details, while breaking immediately when moved to another machine.

### 16.2 Clean Export Separation
TEGAKI must distinguish between:
1. **Internal / Archive Results**: Full provenance embedded for complete studio reproducibility.
2. **Clean Export / Publishing Copies**: An intentional "Strip Provenance" export option that removes prompts, model hashes, and metadata for public sharing or privacy preservation.

---

## 17. Format Assessment: PNG vs. WebP

### 17.1 Technical Posture on WebP
- **ComfyUI Core Evidence**: Recent ComfyUI core releases support writing metadata into WebP files via EXIF user comments and custom chunks. WebP metadata retention is technically viable.
- **Storage Efficiency**: WebP offers substantial file size savings (25–40% smaller than lossless PNG) for manga draft sheets.

### 17.2 Roadmap Guard
- **WEBP-FIRST OUTPUT IS NOT A CURRENT PRIORITY.**
- Formats are transport containers; the Execution Manifest is a data model. Replay must be fully solved and verified on standard PNG baselines first.
- **Classification**: `PROMISING; DEFER`.

---

## 18. Minimum Useful Product Target

To deliver immediate creative value without getting trapped in infinite edge cases, TEGAKI's first replay target should be:

```
MINIMUM VIABLE REPLAY TARGET:
  Level 1 Core Recipe (Prompts, Model, LoRAs, Seed, Steps, CFG, Sampler)
  +
  Level 2 Identity Fingerprints (MRP region count, Guide kind, CAST asset hash)
```

### Why This Is the Sweet Spot:
- Enables the primary user flow: "I liked this image; give me its settings and models so I can iterate."
- Prevents "hallucinated replays": If the image used a regional prompt or a pose guide, TEGAKI detects that conditioning was present and warns the user if it cannot be fully re-engaged, rather than silently applying global prompts and producing unexpected results.
- Avoids the immense complexity of reconstructing multi-page authoring documents from a single raster PNG.

---

## 19. External Technology Lessons & Classification

Evaluating community metadata and replay practices:

| Pattern / Technology | Classification | Strategic Takeaway for TEGAKI |
| :--- | :--- | :--- |
| **Runtime Value Capture** | `STRONG LESSON` | Record the final expanded string and actual seed; never rely on input tokens like `-1` or wildcards alone. |
| **Resource Hash Caching** | `STRONG LESSON` | Hash model files once on discovery; never re-hash gigabyte weights on every single generation. |
| **Asset Hash Referencing** | `STRONG LESSON` | Reference external guide/reference images by hash; avoid bloating image metadata with base64 blobs. |
| **Fail-Closed Resolution** | `STRONG LESSON` | Require explicit user consent when a resource hash is mismatched; never guess basenames. |
| **Full Graph Reverse Inference** | `FALLBACK ONLY` | Reverse-engineering prompt/settings by crawling arbitrary ComfyUI node graphs is fragile and should only be used for external non-TEGAKI images. |
| **Asset Binary Embedding** | `AVOID BY DEFAULT`| Inlining raster image assets directly into PNG metadata chunks causes extreme file bloat and breaks portability. |

---

## 20. Open Architectural Questions (Max 10)

1. **Manifest Chunk Identity**: Should the TEGAKI manifest be stored in a custom PNG chunk (e.g. `tegaki:manifest`) or inside the standard ComfyUI `prompt` / `extra_pnginfo` dictionary to maintain third-party viewer compatibility?
2. **Hash Algorithm Precision**: Is a truncated 16-character SHA-256 hex digest sufficient for collision-free model identification across local installations, or is the full 64-character hex mandatory?
3. **Processed Guide Asset Lifecycle**: Where should preprocessed control maps (e.g. DWPose skeletons) be stored if retained for "Best" fidelity replay, and when should they be garbage-collected?
4. **Wildcard Provenance Granularity**: Should the manifest record only the final string, or both the unexpanded template (`__clothing__`) and the expanded result (`kimono`) for dual editing modes?
5. **Multi-Reference Combine Semantics**: When multiple CAST images are applied, how should their relative attention weights and combine modes be represented in an engine-neutral syntax?
6. **Negative Prompt Coupling in MRP**: How should regional negative prompts be bound when the underlying engine only supports global negative conditioning?
7. **Clean Export UI Boundary**: Should "Clean Export" be a global setting or a per-export checkbox in the image save/share dialog?
8. **Stale Asset Fallback UX**: When a referenced Guide image is missing from disk, what is the cleanest user flow to allow replacing the asset while preserving all guidance parameters?
9. **Schema Versioning Marker**: What is the minimal version header required in the manifest JSON to allow safe forward and backward migration as fields evolve?
10. **Internal Journal vs. Disk Sync**: If an image is moved or renamed outside of TEGAKI using the OS file explorer, how should the internal GenerationJournal re-synchronize its locator?

---

## 21. Cross-Architecture Policy & Strategic Alignment

### 21.1 Anima Migration Boundary
- This capability must **NOT** be expanded into cross-model-architecture translation (e.g. translating SDXL/Illustrious recipes into Anima/Pony/Flux pipelines).
- Cross-architecture migration remains: **ULTRA-LONG-PATH / RESEARCH WATCH ONLY**.
- However, capturing clean, engine-neutral semantic manifests today ensures that future migration tools have structured data to translate rather than unparseable node graphs.

### 21.2 Roadmap Guard
**RESULT REPLAY IS A CONVENIENCE AND RESILIENCE CAPABILITY.**  
It provides immense polish and creative safety, but it does not generate images.

Active development must remain focused on:
- Core Manga generation controllability
- MRP compiler and mask reliability
- CAST Reference Appearance quality
- Guide / ControlNet structural integration
- Production Create UI completion

**No implementation authorization follows from this document.**
