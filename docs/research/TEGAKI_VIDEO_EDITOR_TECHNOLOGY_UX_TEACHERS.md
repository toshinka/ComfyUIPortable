# TEGAKI Video Editor Technology and UX Teacher Survey

> **VIDEO EDITOR STATUS:**  
> **DEFERRED LONG-PATH WORKSPACE**  
> **SEPARATE FROM CURRENT H3 ROADMAP**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**

This document records an external technology and UX teacher survey for a
provisional, long-path TEGAKI Video Editor workspace/tab. It exists to capture
proven architecture patterns and interaction lessons early so that future
planning does not default to generic assumptions ("build a smaller Premiere" or
"copy DaVinci Resolve").

**CRITICAL ROADMAP GUARDRAIL:**
This is pure research and long-range classification. It is **NOT** current H3
implementation authority, **NOT** current Manga implementation authority,
**NOT** UI composition authority, and **NOT** permission to start editing work.
Current H3 video generation and Manga authoring milestones proceed
independently. The existence of this document does not authorize adding timeline
UI to H3, merging H3 state with editing state, modifying H3 runtime graphs,
adding npm or Python editing dependencies, modifying shell navigation, or
implementing editing/export code. Future Astra H3 tasks must treat this document
as an **OUT-OF-SCOPE REFERENCE** unless an explicit Card authorizes Video Editor
planning.

---

## 1. Project Context and Workspace Boundary

TEGAKI currently operates two distinct production domains:
- **MANGA**: Page/Scene authoring, MRP regional conditioning, CAST identity,
  Guide structure, and Manga generation.
- **H3**: Text-to-Video, Image-to-Video, Frame-Bridged Continuation, Still
  Studio, and temporal generation.

These domains share the Portable runtime base and supervisor shell but maintain
strictly separated runtime semantics, state stores, schemas, workflow
ownership, output locators, and domain controls.

A future Video Editor is conceived as a **third distinct workspace or tab**,
positioned downstream in the creative lifecycle:

```
[ H3 Video / Manga Still / Imported Media ]
                   │
                   ▼ (media output files)
      [ Future Video Editor Workspace ]
                   │
                   ▼ (timeline arrangement / assembly / cuts)
               [ Export ]
```

The boundary is architectural, not merely visual:
- **H3 produces media.**
- **The future Video Editor may later consume media.**
- **The Video Editor must NEVER become the owner of H3 generation logic.**

---

## 2. Why This Survey Exists

Traditional commercial non-linear editors (NLEs)—such as Adobe Premiere Pro,
DaVinci Resolve, and Final Cut Pro—as well as compositor suites like After
Effects, represent deep professional capability. However, their monolithic
desktop architectures, steep learning curves, dense multi-panel layouts, and
heavy parameter hierarchies make them unsuitable as direct product-shape or UX
models for TEGAKI.

Modern open-source, web-native, and creative tools demonstrate compelling
alternative trajectories:
- **CapCut-style directness**: Lightweight, low cognitive burden, creator-first.
- **Browser-local & local-first processing**: WebCodecs, WebGPU, OPFS, and File
  System Access API eliminating server rendering bottlenecks while preserving
  data privacy.
- **Task-specific scope discipline**: Proving that cutting and trimming do not
  require a heavyweight multi-track compositor.
- **Unified command models**: Exposing the same deterministic edit operations to
  human GUI, keyboard shortcuts, script automation, and AI agents.
- **Headless and programmatic composition**: Separating timeline evaluation and
  rendering from interactive DOM rendering.
- **Focused creative axes**: Centering the workspace around musical tempo or
  narrative pacing rather than generic track tracks.

This survey captures these external teachers to guide future design choices.

---

## 3. Teacher Classification Framework

Each surveyed project is classified across two dimensions:

### A. Architectural Layers Taught
- `PRODUCT SHAPE`: Overall product boundaries, feature scope, and user mental model.
- `UX / INTERACTION`: Control layout, gesture vocabulary, direct manipulation, and feedback.
- `BROWSER NLE IMPLEMENTATION`: Real-world browser timeline, worker architecture, and local storage.
- `MEDIA INFRASTRUCTURE`: Low-level container parsing, demuxing, decoding, encoding, and muxing.
- `PROGRAMMATIC COMPOSITION`: Code-driven layout, programmatic animation, templates, and shot assembly.
- `AI / AGENT INTERACTION`: Shared human-AI timeline operations and command abstractions.
- `SPECIALIZED WORKFLOW`: Niche-optimized creative flows (e.g., rhythm, lyric alignment, lossless cut).

### B. TEGAKI Adoption Relationship
- `TECHNOLOGY CANDIDATE`: Candidate for eventual library/dependency evaluation.
- `IMPLEMENTATION TEACHER`: Reference for code architecture, patterns, or data pipelines.
- `UX TEACHER`: Reference for interaction models, density, and direct manipulation.
- `PRODUCT-SHAPE TEACHER`: Reference for scoping and product boundaries.
- `ARCHITECTURE TEACHER`: Reference for system boundaries and command abstractions.
- `REFERENCE ONLY`: Useful reference point; no direct extraction intended.

*(Note: No external application is classified as "ADOPT WHOLESALE".)*

---

## 4. Primary External Teachers

### 4.1 OpenCut
- **Repository**: https://github.com/OpenCut-app/OpenCut
- **Taught Layers**: `PRODUCT SHAPE`, `ARCHITECTURE TEACHER`
- **Adoption Relationship**: `PRODUCT-SHAPE TEACHER`, `ARCHITECTURE TEACHER`
- **Core Findings**:
  - OpenCut represents an ambitious open-source effort aimed at modern,
    accessible, CapCut-style video editing.
  - Its evolving architectural design emphasizes a shared core editor engine, a
    plugin-first foundation, an explicit editor API, headless execution
    capabilities, and interoperability with scripting/MCP automation.
  - The project is undergoing substantial architectural evolution/rewrites.
- **What TEGAKI Learns**:
  - **Single Edit Core**: A human GUI, a programmatic API, headless scripts,
    and an AI agent can conceptually share one unified editing model.
  - **CapCut Alternative**: Demonstrates that modern users prioritize rapid,
    intuitive visual editing over complex professional NLE setup.
- **What TEGAKI Must NOT Copy**:
  - Do not adopt unstable, rewrite-era implementation code or dependencies.
  - Do not copy its entire broad product aspirations (mobile/desktop/cloud
    unification).

### 4.2 FreeCut
- **Repository**: https://github.com/walterlow/freecut
- **Taught Layers**: `BROWSER NLE IMPLEMENTATION`, `UX / INTERACTION`
- **Adoption Relationship**: `PRIMARY BROWSER NLE IMPLEMENTATION TEACHER`
- **Core Findings**:
  - FreeCut is a prominent reference for a modern, browser-native, local-first
    NLE built on React, TypeScript, and Zustand.
  - Leverages modern web standards: WebCodecs, WebGPU, Origin Private File
    System (OPFS), the File System Access API, and dedicated Web Workers.
  - Integrates Mediabunny for media demuxing/decoding/muxing.
  - Implements complete local workflows: media ingestion, thumbnail strip
    generation, audio waveform rendering, transcript display, multi-track
    timeline, real-time preview, and in-browser rendering/export.
- **What TEGAKI Learns**:
  - **Browser Feasibility**: Proves that responsive video editing and export are
    entirely feasible inside modern browsers without server-side rendering
    farms.
  - **Pipeline Separation**: Clean separation between timeline state, preview
    canvas, media caching workers, and export pipelines.
  - **Local-First Workspace**: Practical use of OPFS / File System Access API
    for large media handling without upload friction.
- **What TEGAKI Must NOT Copy**:
  - Do not replicate its full feature density or attempt to build a "browser
    DaVinci Resolve."
  - Avoid feature sprawl that burdens lightweight manga/H3 authoring flows.

### 4.3 Mediabunny
- **Repository**: https://github.com/Vanilagy/mediabunny
- **Taught Layers**: `MEDIA INFRASTRUCTURE`
- **Adoption Relationship**: `PRIMARY MEDIA INFRASTRUCTURE CANDIDATE`
- **Core Findings**:
  - Mediabunny is **NOT an editor UI** or application; it is a specialized,
    modular, browser-oriented media toolkit.
  - Written in TypeScript around standard WebCodecs and web streams.
  - Handles container parsing, demuxing, decoding, encoding, muxing, and format
    conversion across modern video/audio containers (MP4, WebM, etc.).
  - Emphasizes low overhead, precise frame timing, and streaming I/O.
- **What TEGAKI Learns**:
  - **Modular Media Engine**: Media container and codec operations can and
    should be isolated from UI and timeline semantics.
  - **Toolkit Independence**: TEGAKI can maintain its own bespoke UI and edit
    graph while delegating low-level binary container work to a tested web
    toolkit.
- **What TEGAKI Must NOT Copy / Premature Action**:
  - **NO dependency installation is authorized now.**
  - Mediabunny remains a high-value candidate for a future standalone
    evaluation pass once a Video Editor workspace is formally chartered.

### 4.4 LosslessCut
- **Repository**: https://github.com/mifi/lossless-cut
- **Taught Layers**: `PRODUCT SHAPE`, `UX / INTERACTION`, `SPECIALIZED WORKFLOW`
- **Adoption Relationship**: `PRODUCT-SHAPE TEACHER`, `UX TEACHER`
- **Core Findings**:
  - LosslessCut is an established utility focused on fast, lossless trimming,
    cutting, slicing, and joining of video and audio files using FFmpeg stream
    copying without re-encoding.
  - Strips away all traditional NLE clutter: no complicated track headers, no
    effects stacks, no transition managers.
  - Delivers exceptional speed, minimal cognitive load, and instant output.
- **What TEGAKI Learns**:
  - **"Video Editor" does NOT imply "Full NLE"**: A video editing workspace can
    deliver immense user value by providing fast, precise trimming and
    assembly of generated clips without full compositing overhead.
  - **Low Cognitive Overhead**: Expose only the controls needed for the active
    operation.
  - **Avoid Unnecessary Re-encoding**: When assembling cuts of identical format,
    direct stream operations save compute and avoid generational quality loss.
- **What TEGAKI Must NOT Copy**:
  - Do not restrict the future editor exclusively to lossless cut operations if
    transitions or titles are eventually needed.
  - Do not replicate its Electron-specific desktop assumptions into TEGAKI's web
    shell.

### 4.5 Timeline Studio / AI Video Editor
- **Repository**: https://github.com/MartinDelophy/ai-video-editor
- **Taught Layers**: `AI / AGENT INTERACTION`, `UX / INTERACTION`
- **Adoption Relationship**: `PRIMARY AI / AGENT INTERACTION TEACHER`
- **Core Findings**:
  - Explores direct human and AI/agent collaboration on the same physical
    timeline structure.
  - Operations (split, delete, duplicate, add caption, adjust volume, fade,
    marker, insert asset, export) are represented as first-class domain commands.
  - Natural language or automated agent requests are translated into concrete
    timeline operations rather than maintaining a disconnected generative chat.
- **What TEGAKI Learns**:
  - **Unified Timeline Operations**: Human users interacting via mouse/keyboard
    and AI agents interacting via tool calls manipulate the exact same underlying
    edit model.
  - **No Parallel AI Editing Engine**: Prevents the antipattern of an "AI video
    generator" that produces an un-editable video file side-by-side with a manual
    editor.
- **What TEGAKI Must NOT Copy**:
  - Do not introduce agent automation before the deterministic manual timeline
    model is proven and stable.

### 4.6 Lyrica
- **Store / Reference**: https://store.steampowered.com/app/5106770/Lyrica/
- **Taught Layers**: `UX / INTERACTION`, `SPECIALIZED WORKFLOW`
- **Adoption Relationship**: `UX / INTERACTION TEACHER`, `SPECIALIZED WORKFLOW TEACHER`
- **Core Findings**:
  - Lyrica is a specialized Japanese lyric video / MV creation environment.
  - Centered on a clear, dominant primary axis: musical tempo (BPM), audio
    waveforms, and syllable timing.
  - Features real-time live preview directly adjacent to editing controls.
  - Restrained, modern visual aesthetics: lightweight buttons, clean typography,
    minimal panel borders, muted dark theme, and high-contrast accents.
  - Progressive sophistication: simple direct use out of the box with
    expressive typography and motion effects available without exposing a full
    broadcast NLE interface.
- **What TEGAKI Learns**:
  - **Visual Discipline & Restraint**: Demonstrates how a specialized video tool
    can feel modern, fluid, and delightful without looking like industrial
    editing software.
  - **Primary Creative Axis**: Centering the workspace around what matters
    most (e.g., rhythm or shot flow) creates immediate cognitive clarity.
  - **Direct Feedback**: Tight visual coupling between the preview monitor and
    the timeline cursor.
- **What TEGAKI Must NOT Copy**:
  - Do not copy its specific lyric-video layout, typographic presets, or Steam
    packaging.
  - Visual styling (colors, button weights, panel density) is an aesthetic
    teacher, not a binding style guide for Astra UI review.

### 4.7 Remotion
- **Repository**: https://github.com/remotion-dev/remotion
- **Taught Layers**: `PROGRAMMATIC COMPOSITION`
- **Adoption Relationship**: `PROGRAMMATIC COMPOSITION TEACHER`
- **Core Findings**:
  - Remotion enables video creation using React components, CSS, and
    TypeScript.
  - Treats video frames as a function of time (`useCurrentFrame()`).
  - Excels at parametric motion graphics, automated captions, data-driven
    compositions, programmatic transitions, and reproducible batch rendering.
- **What TEGAKI Learns**:
  - **Parametric Motion & Templates**: Dynamic manga panel transitions, title
    cards, credits, and layout animations can be defined programmatically as
    reusable components.
  - **Deterministic Frame Rendering**: Clean mathematical mapping of time to
    visual properties.
- **What TEGAKI Must NOT Copy**:
  - **Do NOT mistake Remotion for an interactive timeline editor.**
  - Writing code to edit a montage is a developer flow, not a replacement for an
    interactive, visual video workspace for manga creators and directors.

### 4.8 OpenReel
- **Repository**: https://github.com/Augani/openreel-video
- **Taught Layers**: `BROWSER NLE IMPLEMENTATION`, `PRODUCT SHAPE`
- **Adoption Relationship**: `CAPABILITY REFERENCE`, `BROWSER NLE IMPLEMENTATION TEACHER`
- **Core Findings**:
  - OpenReel demonstrates an advanced multi-track browser-based video editor
    built on modern web technologies.
  - Features keyframe animation, color adjustments, audio filters, WebGPU
    previewing, and client-side rendering/export.
- **What TEGAKI Learns**:
  - **Browser Capability Ceiling**: Proves that advanced features (keyframes,
    color correction, multi-track mixing) can execute entirely within a client
    browser session.
- **What TEGAKI Must NOT Copy**:
  - **Do NOT build to this complexity initially.**
  - OpenReel illustrates what is *possible*, not what TEGAKI *needs*. Adopting
    its full complexity upfront would result in immediate cognitive and
    maintenance overload.

---

## 5. Emerging Architecture Pattern: Unified Command Model

Surveying newer projects (including exploratory references like MakeMyClip and
Inkstone) highlights a crucial architectural pattern:

```
┌────────────────────────────────────────────────────────┐
│               Human UI (Direct Manipulation)          │
│               Keyboard Shortcuts / Macros              │
│               Undo / Redo History Stack                │
│               AI Agent / Tool Execution                │
│               Automation Script / Headless API         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             DETERMINISTIC COMMAND CORE                 │
│  (e.g., placeClip, moveClip, trimClip, splitClip,      │
│         deleteClip, setVolume, addText, setMarker)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                TIMELINE PROJECT STATE                  │
└────────────────────────────────────────────────────────┘
```

### Key Principles of the Command Pattern:
1. **Single Point of Truth**: Every state change on the timeline passes through
   discrete, serializable command objects or methods.
2. **First-Class Undo/Redo**: Commands provide forward execution and inverse
   patches natively.
3. **Agent Parity Without Magic**: An AI agent does not require special hooks;
   it calls the exact same command dispatchers that the human mouse drag
   triggers.
4. **Auditability**: Produces a clean, inspectable operation log that fits
   TEGAKI's established provenance principles.

*(Note: This is an architectural reference pattern, not an authorization to
implement command schemas now.)*

---

## 6. Relationship to Traditional Broadcast NLEs

Professional NLEs (Premiere Pro, DaVinci Resolve, Final Cut Pro, Avid) and
compositors (After Effects, Nuke) serve specific, valuable roles:
- **Comprehensive vocabulary references**: Standardizing terms such as ripple
  delete, roll edit, slip/slide, J/L cuts, playhead, snapping, and timecode.
- **Edge-case stress testing**: Understanding audio-video synchronization drift,
  variable framerate (VFR) footage, and color space management.

However, TEGAKI explicitly rejects the following traditional NLE assumptions:
- **NO monolithic multi-window workspaces**: Do not force users to manage
  bin browsers, source monitors, program monitors, track patch matrices, and
  audio mixers simultaneously.
- **NO mandatory ingest/transcode hurdles**: Users expect to drag a generated H3
  clip straight onto the timeline and scrub instantly.
- **NO feature completeness goal**: TEGAKI does not aim to replace DaVinci
  Resolve for film color grading or Premiere for multi-cam television editing.

---

## 7. Cross-Teacher Synthesis

The surveyed teachers occupy complementary layers across the editing stack:

| Teacher | Primary Layer Taught | TEGAKI Role / Extraction Target |
| :--- | :--- | :--- |
| **OpenCut** | Product Shape / Architecture | Shared core concept (human GUI + headless API + agent access) |
| **FreeCut** | Browser NLE Implementation | Local-first browser architecture (WebCodecs, OPFS, workers) |
| **Mediabunny** | Media Infrastructure | High-value candidate for container demux/decode/mux engine |
| **LosslessCut** | Product Shape / UX | Radical scope discipline; trimming/joining without NLE bloat |
| **Timeline Studio** | AI / Agent Interaction | Shared human-agent timeline command model |
| **Lyrica** | UX / Interaction | Clear primary creative axis, restrained aesthetic, tight preview |
| **Remotion** | Programmatic Composition | Component-driven templates, titles, and motion graphics |
| **OpenReel** | Browser Implementation | Proof of browser capability ceiling (what *not* to build first) |

No single project should be adopted wholesale. The ideal TEGAKI direction is a
disciplined synthesis:
- **Product Scope** inspired by LosslessCut and CapCut simplicity;
- **Interaction & Tone** guided by Lyrica-like restraint and direct preview;
- **Browser Plumbing** informed by FreeCut's local-first web standards;
- **Media Codec Engine** potentially backed by a focused library like Mediabunny;
- **Command Architecture** structured like Timeline Studio / MakeMyClip;
- **Template Motion** informed by Remotion.

---

## 8. Provisional TEGAKI Video Editor Shape (Non-Binding Hypothesis)

To prevent premature drift into full-NLE complexity, any future Video Editor
should adhere to a strictly bounded minimum core:

```
[ MEDIA POOL ] ──▶ [ DIRECT-MANIPULATION TIMELINE ] ──▶ [ LIVE PREVIEW ] ──▶ [ LOCAL EXPORT ]
```

### Minimal Initial Verbs:
- `PLACE`: Insert an H3 video, Manga still, or local file into the sequence.
- `MOVE`: Reposition a clip horizontally on the timeline.
- `TRIM`: Adjust the in-point or out-point of a clip.
- `SPLIT`: Cut a clip at the playhead into two independent segments.
- `DELETE`: Remove a clip and choose ripple or gap behavior.

### Possible Progressive Additions (Deferred):
- `TEXT`: Simple titles, subtitles, or dialogue captions.
- `AUDIO`: Background music / sound effect placement and volume curves.
- `TRANSITION`: Dissolves, cross-fades, and cuts between adjacent clips.
- `TRANSFORM`: Basic crop, scale, and pan (especially for Manga still pan/zoom).

*(This hypothesis is non-binding and does not establish a schema or timeline
version.)*

---

## 9. Core Design Principles for a Future Editor

### 9.1 Primary-Axis Principle
Every creative workspace in TEGAKI must center around a single, unambiguous
primary axis:
- **Manga Workspace**: Centered on **Page & Scene Structure**.
- **H3 Studio**: Centered on **Shot, Frame, & Temporal Flow**.
- **Drawing Canvas**: Centered on **Canvas & Layer Geometry**.
- **Future Video Editor**: Centered on **Timeline Sequence & Media Arrangement**.

A shared visual design language (typography, token styling) across TEGAKI does
**not** require identical workspace layouts or control arrangements.

### 9.2 Direct Manipulation Principle
Prefer direct, tactile actions over indirect parameter forms:
- Drag clips, trim edges directly, scrub the playhead with immediate feedback,
  and split with a single shortcut/button.
- Do not require users to configure node graphs, fill out nested coordinate
  forms, or edit raw JSON to assemble a video cut.
- Advanced settings must remain tucked behind progressive disclosure.

### 9.3 Local-First Principle
Video editing should execute entirely local-first:
- **Zero upload/download roundtrips**: Work directly against local H3/Manga
  output directories or browser-managed OPFS storage.
- **Privacy & Speed**: High-resolution video scrubbing must not depend on cloud
  bandwidth or server-side render queues.
- **Native Efficiency**: Leverage hardware acceleration via WebCodecs and
  WebGPU.

---

## 10. Workspace Isolation Boundaries

### 10.1 Video Editor / H3 Boundary (MANDATORY & ABSOLUTE)
- **H3 Owns**: Model loading, prompt compilation, sampling schedules, latent
  dimensions, motion scale, IP-Adapter reference conditioning, ComfyUI
  execution graphs, and generating raw `.mp4` video results.
- **Future Video Editor Owns**: Cataloging generated/imported media files,
  arranging clips along a timeline, audio synchronization, cut/trim operations,
  and rendering composite exports.
- **Permitted Relationship**:
  $$\text{H3 Validated Result MP4} \longrightarrow \text{Video Editor Media Source}$$
- **Prohibited Relationship**:
  - The Video Editor must **NEVER** mutate H3 prompt state, KSampler settings,
    or generation graphs.
  - H3 must **NEVER** depend on timeline or video editing packages.
  - Regeneration workflows (e.g., "re-roll shot at 00:04") must pass through
    an explicit future adapter Card, not shared internal state.

### 10.2 Video Editor / Manga Boundary
- Manga authoring remains strictly focused on multi-panel page layout, prompt
  conditioning, and static image output.
- The Video Editor may later import rendered manga pages or panel crops to
  create "motion comic" or animatic sequences, but Manga authoring code will not
  absorb video playback, timeline state, or editing concepts.

### 10.3 Shell / Navigation Boundary
- A future Video Editor will exist as an independent top-level tab/workspace.
- **No shell modifications are authorized now.**
- No port is reserved, no HTTP route is registered, and no background service
  is defined.

---

## 11. Dependency Evaluation and Licensing Policy

External projects surveyed here are **TEACHERS FIRST, NOT DEPENDENCIES**.

When a future Card explicitly authorizes evaluating dependencies for media
infrastructure:
1. **Scope Discrimination**: Distinguish strictly between:
   - A *whole application* (e.g., FreeCut, LosslessCut) $\rightarrow$ examine
     patterns only;
   - A *focused library* (e.g., Mediabunny) $\rightarrow$ potential dependency
     candidate;
   - An *architectural pattern* (e.g., command model) $\rightarrow$ implement
     cleanly inside TEGAKI.
2. **Vetting Requirements**: Any candidate package must be evaluated for:
   - Permissive open-source license (MIT, Apache 2.0, BSD);
   - Active maintenance and community health;
   - Clean browser / Windows portability;
   - Zero native compilation friction on target platforms;
   - Minimal bundle footprint and zero invasive transitive dependencies.

*No dependency is adopted, installed, or approved by this document.*

---

## 12. Explicit List of What NOT to Build Yet

To prevent scope creep, the following are strictly **FORBIDDEN** under current
roadmap milestones:
- ❌ NO Video Editor tab or workspace UI
- ❌ NO timeline component or timeline state store
- ❌ NO timeline data schema (no `timeline_spec.py` or `timeline.json`)
- ❌ NO keyframe animation engine
- ❌ NO transition or effects shaders
- ❌ NO FFmpeg native wrapper or ffmpeg.wasm integration
- ❌ NO installation of Mediabunny, Remotion, or other video libraries
- ❌ NO audio decoding/mixing engine
- ❌ NO video rendering/muxing pipeline
- ❌ NO integration hooks inside H3 or Manga
- ❌ NO shared H3/Video state objects
- ❌ NO autonomous AI video editing agent
- ❌ NO MCP video editing server

---

## 13. Astra / Agent Guardrails

For all future autonomous agents and Astra architecture reviewers:

1. **Do NOT use this survey to alter current H3 tasks.** Current H3 work centers
   on native model execution, Still Studio, and video quality. Do not burden H3
   with editing requirements.
2. **Do NOT reserve UI space in H3 for video editing.** H3 UI reviews must judge
   H3 on its own merits without placeholder timeline panels.
3. **Do NOT attempt to unify H3 and Manga into a "multimedia studio"** using the
   Video Editor as an excuse.
4. **Treat teacher features as possibilities, not commitments.** Just because
   OpenReel or FreeCut has a feature does not mean TEGAKI will ever implement
   it.

---

## 14. Open Future Research Questions

The following questions remain deliberately open and must NOT be answered
without dedicated future Cards:
1. What is the single smallest video editing task that provides 80% of creator
   value for H3 users? (e.g., simple 2-clip stitching vs. multi-layer montage?)
2. Should the media pipeline be 100% browser-internal (WebCodecs/WebGPU), or is
   a lightweight local Python/headless helper beneficial on Windows?
3. How should project state persist? (Single `.tegaki-project` file, OPFS
   workspace, or directory of sidecar JSON files?)
4. Where should the boundary lie between immutable generated shots and mutable
   timeline trims?
5. How should audio tracks (BGM, voiceover, SFX) enter and align with generated
   silent H3 video?
6. How should undo/redo history integrate with potential AI tool operations?

---

## 15. Next Logical Document

When the project leadership decides to begin preparing for video editing, the
single authorized next document will be:

**`docs/architecture/TEGAKI_VIDEO_EDITOR_WORKSPACE_PREP.md`**

Its bounded charter will be to:
- Inventory existing TEGAKI media outputs and locators.
- Survey installed Windows/Portable media tools (if any).
- Define the formal workspace boundary and data handoff contract.
- Specify the minimal non-NLE assembly user journey.

*(DO NOT create this document now. It is reserved for a future explicit Card.)*
