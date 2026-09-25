# Manga Authoring Snapshot and Natural Rollback Frontier Review

> **STATUS:**  
> **RESEARCH CONSOLIDATION & ARCHITECTURAL REFERENCE ONLY**  
> **DEFERRED CONVENIENCE / SAFETY CAPABILITY**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**  

This document records a bounded architectural study of **Authoring Snapshot / Natural Rollback** for the **TEGAKI Manga** authoring environment. It examines community snapshot and workflow management patterns, evaluates their applicability to manga authoring, establishes clear architectural boundaries separating Snapshots from Undo and Result Replay, and defines a low-cognitive-load safety net for future reference.

---

## 1. Scope & Foundational Definition

### 1.1 Scope
- **Domain**: Authoring-state safety, automated checkpointing, and natural rollback for the TEGAKI Manga authoring workspace.
- **Role**: **Secondary convenience / safety net**.
- **User Need**: Addresses the specific creative scenario:  
  > *"I changed something recently and the previous authoring state was better."*
- **Boundary**: Snapshot is strictly a protective net against recent editing mistakes, unwanted experimentation, or accidental macro changes. It is **not** a primary history architecture, not a visual gallery, and not a recipe discovery mechanism.

### 1.2 Strict Roadmap Precedence
Convenience and safety capabilities must never displace active generative milestones.  
**THIS IS NOT A CURRENT IMPLEMENTATION PRIORITY.**

Active generative milestones retain absolute precedence:
1. **Manga Controllability & Generation Reliability**
2. **Manga Regional Prompting (MRP)** compile, overlap, and mask stability
3. **Reference Appearance (CAST / IP-Adapter)** character consistency
4. **Guide / ControlNet** spatial and structural layout guidance
5. **Core Create Workspace & Production UI Completion**
6. **Result Provenance / Replay** (recovering recipes from generated artifacts)

---

## 2. Priority Relationship: Result Replay vs. Authoring Snapshot

TEGAKI explicitly recognizes a fundamental hierarchy between result recovery and editing checkpoints:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PRIORITY HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. RESULT PROVENANCE / REPLAY  (HIGHER PRODUCT VALUE)                      │
│     • Primary user value: Visual rediscovery of a generated artifact.       │
│     • User selects a pleasing image from history/output.                    │
│     • Recovers prompt, negative, seed, sampler, LoRA, and character states. │
│     • High creative leverage; essential generation loop feature.            │
├─────────────────────────────────────────────────────────────────────────────┤
│  2. AUTHORING SNAPSHOT / ROLLBACK  (SECONDARY CONVENIENCE / SAFETY NET)     │
│     • Secondary user value: Recovery from recent authoring mistakes.        │
│     • User realizes an edit made 5 minutes ago degraded the layout/text.    │
│     • Coarse timeline rollbacks to a recent authoring checkpoint.           │
│     • Safety net only; zero impact on generation algorithm quality.         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why They Must NOT Be Merged
- **Different Triggers**: Result Replay is triggered by inspecting an **output image** (external visual artifact). Snapshot Rollback is triggered by inspecting **current workspace state** (authoring document).
- **Different Lifecycles**: Result Replay persists indefinitely inside generated image metadata (`tEXt`/`iTXt`) and generation journals. Snapshots are transient, bounded rolling caches of work-in-progress authoring states.
- **Different Authority**: Replay deals with what *was executed* on the backend GPU at a specific timestamp. Snapshot deals with what *was authored* in the frontend document model, whether executed or not.

---

## 3. Reference Implementations

The ComfyUI ecosystem provides several historical approaches to state management and versioning:

### 3.1 Primary Teacher: `Comfyui-Workflow-Snapshot-Manager` (ethanfel)
*Repository: `https://github.com/ethanfel/Comfyui-Workflow-Snapshot-Manager`*

Key architectural characteristics:
- **Automatic Background Capture**: Monitors graph changes and triggers automated snapshot writes without user intervention.
- **Quiet Period / Debounce**: Enforces a 3-second quiet period following user activity before writing to disk, avoiding spamming disk I/O during rapid mouse movements.
- **Minimum Interval Throttling**: Limits automatic snapshot frequency (default: 60-second minimum interval between automated saves) even if edits continue continuously.
- **Semantic Change Filtering**: Distinguishes structural graph modifications from pure layout manipulations (ignoring node movements, panning, and resizing until a functional change occurs).
- **Bounded Retention**: Implements automatic count-based pruning (e.g., maximum 50 snapshots) and optional age-based pruning.
- **Safety on Restore**: Automatically creates a "return point" snapshot before applying a destructive restore.
- **Diagnostic Diff**: Provides visual/textual side-by-side JSON diffs highlighting added, removed, and modified nodes between snapshots.

### 3.2 Secondary Teacher: `comfyui-workspace-manager` (11cafe)
*Repository: `https://github.com/11cafe/comfyui-workspace-manager`*

Key architectural characteristics:
- **IndexedDB & File-Backed Storage**: Uses local browser storage alongside backend JSON persistence.
- **Workflow Versioning**: Maintains named versions and automatic operation logs.
- **Heavyweight UI Integration**: Integrates permanent sidebar navigation, workflow trees, tag managers, and cloud sync options.
- **Lesson for TEGAKI**: While powerful for multi-workflow repository management, its persistent UI footprint and workspace overhead violate TEGAKI's focus-first Manga authoring ergonomics.

### 3.3 Optional Reference: `ComfyPilot`
- Explored branch-based workflow versioning and execution logging.
- Concludes that developer-centric version control (Git analogies) creates friction for creative authoring.

---

## 4. Snapshot-Manager Lessons & TEGAKI Classifications

Evaluating external patterns against TEGAKI's architectural requirements:

| Snapshot Pattern | Classification | Rationale & TEGAKI Relevance |
| :--- | :--- | :--- |
| **Meaningful-Change Detection** | `USEFUL CORE LESSON` | Must filter out trivial UI noise (e.g. selection toggles, hover states, minor scroll/pan adjustments) and only trigger on semantic edits (prompt text, character assignment, scene bounds, LoRA weight). |
| **Debounced Capture** | `USEFUL CORE LESSON` | A 3–5 second quiet period after the last input event ensures the user has paused editing before snapshot serialization begins. |
| **Minimum Interval Throttling** | `USEFUL CORE LESSON` | Cooldown period (e.g. 60–120 seconds between auto-snapshots) prevents snapshot inflation during sustained typing or continuous slider scrubbing. |
| **Layout-Only Change Filtering** | `USEFUL CORE LESSON` | Purely aesthetic or viewport shifts (scrolling the canvas, zooming) should not consume snapshot slots until accompanied by real authoring changes. |
| **Bounded Retention (Pruning)** | `USEFUL CORE LESSON` | Strict FIFO cap (e.g. keep last 20–30 snapshots) prevents unbounded disk or database growth. Older non-pinned checkpoints expire naturally. |
| **Return-Point Before Restore** | `USEFUL CORE LESSON` | Restoring an older snapshot must never permanently destroy current state. An automatic return point ("State before rollback") must be captured immediately before restoring. |
| **Manual Pin / Lock** | `OPTIONAL ADVANCED` | Allowing the user to star/pin an explicit milestone prevents automatic pruning, but must remain strictly optional. |
| **Open-Copy vs. In-Place Replace** | `OPTIONAL ADVANCED` | Opening an older snapshot into a secondary scratch tab or side comparison rather than overwriting the active document. Useful later, but non-essential initially. |
| **Snapshot Diff Modal** | `OPTIONAL ADVANCED` | Textual or visual diff showing what changed between snapshots is a helpful diagnostic aid, but rollback can function safely with just timestamps and preview thumbnails. |
| **Permanent Timeline / History Dock** | `TOO HEAVY FOR TEGAKI` | Constant visual timeline bars, history docks, or scrub sliders clutter the interface and steal canvas real estate from manga pages and scene framing. |
| **Git-Style Branching / DAGs** | `TOO HEAVY FOR TEGAKI` | Forking branches, merge conflicts, and commit graphs introduce extreme cognitive overhead completely inappropriate for creative visual authoring. |
| **Mandatory Save Naming / Messages** | `TOO HEAVY FOR TEGAKI` | Forcing users to type "commit descriptions" or names when saving checkpoints paralyzes creative flow. |
| **Cloud Workspace Synchronization** | `TOO HEAVY FOR TEGAKI` | External sync layers introduce authentication, network latency, and data privacy issues incompatible with TEGAKI's local-first portable philosophy. |

---

## 5. Minimum TEGAKI Hypothesis

If TEGAKI later implements an authoring snapshot capability, it should follow a **deliberately small, concealed operational loop**:

```
[ Authoring Edit Occurs ]
         │
         ▼
[ Meaningful Semantic Change Detected? ] ──(No)──► [ Ignore / Idle ]
         │ (Yes)
         ▼
[ Debounce Timer (3-5s Quiet) ]
         │
         ▼
[ Cooldown Check (>60s since last auto-snapshot?) ] ──(No)──► [ Defer until cooldown ]
         │ (Yes)
         ▼
[ Serialize AuthoringDocument ] ──────────────────► [ Write to Rolling Local Cache ]
                                                    [ Enforce Bounded Retention (e.g. max 25) ]
```

### 5.1 The Recovery Loop (On-Demand Only)
1. **Normal State**: The primary authoring workspace features **NO visible history dock or permanent timeline**. The user focuses entirely on pages, scenes, characters, and panels.
2. **User Trigger**: If a mistake is made, the user accesses an on-demand recovery dialog (e.g., *File > Recent Revisions...* or *Ctrl+Shift+Z / Rollback*).
3. **Selection**: A clean, compact list shows recent checkpoints with timestamps, relative ages ("5 minutes ago"), and brief change summaries (e.g., "Edited Scene 2 prompt; added CAST reference").
4. **Safe Restore**:
   - Step A: Capture an immediate **Return Point** representing the current dirty state.
   - Step B: Atomically deserialize and mount the selected snapshot into the active workspace.
   - Step C: Present a subtle notification with an instant "Undo Rollback" option.

---

## 6. Target State Definition: AuthoringDocument vs. Raw ComfyUI Graph

A critical architectural finding of this study is the definition of what constitutes a "Snapshot":

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SNAPSHOT TARGET COMPARISON                      │
├───────────────────────────────────┬────────────────────────────────────┤
│    RAW COMFYUI EXECUTION GRAPH    │      TEGAKI AUTHORING DOCUMENT     │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Massive payload (hundreds of    │ • Ultra-compact JSON payload       │
│   nodes, links, widgets, coords)  │   (pages, scenes, characters)      │
│ • Engine-coupled: breaks across   │ • Engine-decoupled: pure semantic  │
│   node version / custom node updates│ authoring intent                 │
│ • Hard to diff or reason about    │ • Natural semantic diffing         │
│ • Leaks implementation plumbing   │ • Independent of backend changes   │
│ • High I/O and storage cost       │ • Fast serialization (<5ms)        │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 6.1 Architectural Recommendation
The future snapshot target **must be the high-level TEGAKI `AuthoringDocument` / product state**, rather than the low-level ComfyUI prompt/workflow execution graph.

### 6.2 Key Advantages
1. **Semantic Fidelity**: Preserves authoring concepts directly (scenes, regional prompt text, panel coordinates, character identity references) rather than low-level node IDs.
2. **Backend Agnosticism**: If TEGAKI's underlying generation graph compiler evolves, older authoring snapshots remain fully valid and can be recompiled into the new graph structure without migration friction.
3. **Storage Efficiency**: Serialized authoring documents are typically tens of kilobytes, allowing dozens of rolling snapshots to occupy negligible disk space (<2 MB total).
4. **Boundary Note**: This recommendation does not freeze the internal storage format; schema evolution and serialization contracts will be finalized when authoring persistence is formally scheduled.

---

## 7. Distinguishing Undo, Snapshot, and Result Replay

To prevent architectural confusion, TEGAKI enforces strict separation across three distinct recovery tiers:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            THE THREE RECOVERY TIERS                              │
├───────────────────┬──────────────────────────┬───────────────────────────────────┤
│ CAPABILITY        │ GRANULARITY & LIFECYCLE  │ PRIMARY INTENT & MECHANISM        │
├───────────────────┼──────────────────────────┼───────────────────────────────────┤
│ **UNDO / REDO**   │ • Fine-grained           │ • Immediate mechanical reversal   │
│                   │ • In-memory only         │ • Granular action command stack   │
│                   │ • Cleared on reload      │ • e.g. typo fix, nudge slider     │
├───────────────────┼──────────────────────────┼───────────────────────────────────┤
│ **AUTHORING       │ • Coarse-grained         │ • Macro safety net                │
│   SNAPSHOT**      │ • Persistent local cache │ • Periodic document checkpointing │
│                   │ • Rolling bounded window │ • e.g. restore layout from 15m ago│
├───────────────────┼──────────────────────────┼───────────────────────────────────┤
│ **RESULT          │ • Generative artifact    │ • Creative recipe rediscovery     │
│   REPLAY**        │ • Indefinite lifespan    │ • PNG metadata & execution journal│
│                   │ • Portable with image    │ • e.g. recover exact prompt/seed  │
└───────────────────┴──────────────────────────┴───────────────────────────────────┘
```

---

## 8. Low-Cognitive-Load Principles

Authoring tools must minimize administrative friction. A compliant snapshot system must adhere to five "Zero-Burden" rules:

1. **NO Mandatory Naming**: Checkpoints must never prompt the user for a title or description. Timestamps, automatic activity badges, and page/scene identifiers are sufficient.
2. **NO Manual Save Discipline**: Checkpoints occur automatically based on debounced activity. Users do not need to remember to "save a version."
3. **NO Timeline Management**: Users are not expected to prune, archive, organize, or label historical entries. The system manages its own bounded rolling FIFO queue.
4. **NO Merge Conflicts**: Rollback is a simple document replacement (with a safety return point). There are no multi-head branches or branch reconciliations.
5. **NO Visual Distraction**: Zero permanent canvas or toolbar clutter during normal authoring operations.

---

## 9. Failure Modes & Cost Concerns

Future implementation must account for specific technical risks:

- **Excessive Filesystem I/O**: Naive snapshotting on every keypress causes write amplification, disk churn, and SSD wear. Must be mitigated via debouncing and cooldown intervals.
- **Payload Bloat from Binary Assets**: If an authoring document accidentally embeds base64-encoded raster masks, sketches, or guide images, snapshot sizes explode. Binary assets must be referenced via hashes/locators, not inlined.
- **UI Thread Freezes**: Synchronous JSON serialization of complex documents can cause dropped frames or input lag. Serialization must be asynchronous or off-loaded.
- **Restore Corruption**: Deserializing an invalid or truncated snapshot could corrupt active workspace memory. Restores must be strictly validated before mounting.
- **Schema Evolution Drift**: Snapshots captured in an older version of TEGAKI must either migrate cleanly via schema upconverters or fail visibly with an explanatory warning.
- **Stale External Resource References**: A snapshot restored from days ago may reference a LoRA or checkpoint that has since been deleted or moved. The restore mechanism must rely on TEGAKI's strict catalog resolver to flag missing dependencies rather than crashing.

---

## 10. Restore Safety Contract

The safety of natural rollback relies on one inviolable rule:

> **RESTORE MUST NEVER DESTROY THE CURRENT STATE.**

### Implementation Invariants:
1. **Automatic Return Point**: Immediately prior to overwriting the current workspace with an older snapshot, the system must capture an implicit snapshot tagged as `PRE_RESTORE_RETURN_POINT`.
2. **Fail-Closed Deserialization**: The candidate snapshot must be parsed and schema-validated in an isolated sandbox. If parsing fails, the current workspace remains untouched, and a diagnostic alert is presented.
3. **Non-Destructive Alternate Option**: If feasible, users should be offered the choice to "Inspect in Read-Only Mode" or "Restore into Active Workspace."

---

## 11. Explicitly Rejected: The Version Control Anti-Pattern

TEGAKI explicitly rejects turning the Manga authoring workspace into a software version control system. The following features are **explicitly out of scope**:

- ❌ **Git-like Branching and Merging**: Branches, detached HEADs, and merge conflict resolution.
- ❌ **Commit Log Semantics**: Requiring commit messages or author sign-offs.
- ❌ **Permanent History Dock**: A desktop-style perpetual history tree consuming screen space.
- ❌ **Complex Graph / Visual Node Diffs**: Node-by-node wire diagrams showing connection differences.
- ❌ **Multi-User Cloud Sync / Collaborative Repositories**: Remote locking, cloud sync engines, or central repository servers.

These concepts solve developer collaboration problems, not solo manga creator authoring problems.

---

## 12. Capability Classification & Architectural Placement

```
============================================================
TEGAKI CAPABILITY CLASSIFICATION: AUTHORING SNAPSHOT
============================================================

CAPABILITY IDENTITY:
  Manga Authoring Snapshot & Natural Rollback

ROLE:
  Secondary Convenience / Safety Net

UI FOOTPRINT:
  LOW (Strictly hidden / on-demand modal)

IMPLEMENTATION PRIORITY:
  DEFER (Post-core generation milestones)

ARCHITECTURAL AFFINITY:
  HIGH with Authoring Document Resilience & Persistence

DEPENDENCY ON RESULT REPLAY:
  NONE (Completely independent parallel subsystem)
============================================================
```

---

## 13. Roadmap Guardrails

The existence of this architectural study must **NOT** trigger immediate implementation.  
Core generative and authoring milestones remain paramount:

- Controllable generation, Regional Prompting (MRP), Character Consistency (CAST / IP-Adapter), and Layout Guidance (Guide / ControlNet) directly determine whether comic panels can be successfully produced.
- Snapshot rollback merely provides a safety cushion for workspace state.

**No implementation Card should follow automatically.** Future work on authoring snapshots will be scheduled only after core generation, workspace UI, and primary Result Provenance/Replay are stabilized.
