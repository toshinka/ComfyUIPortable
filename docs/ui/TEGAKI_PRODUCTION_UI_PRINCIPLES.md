# TEGAKI Production UI Principles

**Status:** Stable interaction specification

**Scope:** TEGAKI production tools and the future work that extends them

This document defines interaction laws that should remain recognizable while
Manga and H3 evolve. It stabilizes behavior before visual composition. It does
not select a final layout, palette, type scale, animation timing, or component
implementation.

The principles describe UI relationships only. They do not merge Manga and H3
runtime schemas, generation state, workflows, or ownership boundaries.

## 1. Tool families

TEGAKI has three useful UI families.

### Production siblings

**Manga** and **H3** are production siblings. They should share a strong
cognitive map: a person who moves between them should recognize where intent,
subject material, structure, control, generation, and results are handled.
Their labels, validation, domain semantics, runtimes, and workflows remain
independent.

### Downstream production workspaces

Future **Assemble**, **Video Editing**, and **Page Assembly** workspaces serve a
different task from generation authoring. They may change layout substantially
to support assets, timelines, page strips, takes, and editing operations.

### Utilities

Civitai helpers, wildcard editors, prompt extraction, metadata utilities, and
other specialized tools are utilities. They may use a layout suited to their
own task. Production sibling geometry must not be imposed on them merely for
visual consistency.

## 2. Core law: cognitive coordinates

### Principle

Production siblings preserve **cognitive coordinates**, not identical feature
sets.

### Rationale

The domain meaning of a reference, frame, region, or control can differ. A
stable interaction grammar still lowers the cost of switching tools.

### Implication

When moving between Manga and H3, the user should continue to know, without
relearning the whole application:

- where textual intent is entered;
- where a subject or reference is attached;
- where spatial or structural control lives;
- where generation is initiated; and
- where the current result and its state are observed.

The approximate location and interaction grammar should remain recognizable;
the domain explanation and validation remain specific to each tool.

## 3. Five cognitive slots

The production-authoring model has five provisional slots. They are cognitive
locations, not a shared data model.

| Slot | Manga meaning | H3 meaning |
| --- | --- | --- |
| **INTENT** | Prompt and textual generation intent, including negative intent where supported | Prompt and textual video or still intent |
| **SUBJECT** | CAST identity and reference appearance | Subject/reference material and R2V-related input |
| **SPACE / STRUCTURE** | Scene, Region, and MRP spatial application | Frame, Start/End, and spatial or temporal framing concepts |
| **CONTROL** | Guide, ControlNet, and composition constraints | Pose, camera, motion, and applicable control systems |
| **OUTPUT** | Generate, generation state, and the current Preview/Result | Generate, generation state, and the current Preview/Result |

The same slot name does not imply that the two domains are semantically equal.
It must not be used as a reason to merge schemas or backend state.

## 4. Same place, same shape, different meaning

### Principle

Features with the same interaction pattern may share component grammar even
when their meanings differ.

### Rationale

A familiar attach-and-review interaction is useful when the attached object is
a Manga CAST reference, a ControlNet guide, or an H3 R2V reference. Familiar
mechanics should not hide different runtime behavior.

### Implication

A reusable attachment grammar may contain:

- thumbnail or media preview;
- name and availability state;
- attach, replace, and remove actions;
- strength where the domain supports strength;
- target or scope where the domain supports targeting; and
- progressive disclosure for advanced settings.

Labels, explanations, validation, limits, and runtime meaning stay
domain-specific. A common visual card is not a common semantic contract.

## 5. Domain identity

Manga and H3 can share a cognitive house plan while feeling like different
rooms. Domain identity should be expressed through a combination of:

- domain title and navigation context;
- accent and surface treatment;
- iconography;
- terminology and microcopy;
- contextual help; and
- domain-specific controls and status language.

Color alone must not carry the distinction. Final colors and branding remain
open design decisions for a later review.

## 6. Preview law: Create takes priority before a useful result

### Principle

Before a useful result exists, Preview should not dominate the Create
workspace.

### Rationale

The first tasks are usually prompt, model, LoRA or reference selection,
resolution, duration where relevant, and basic generation setup. An empty stage
cannot answer those questions.

### Implication

During ordinary authoring, the directional priority is **Create > Preview**.
Preview may remain compact and still provide a clear place for the next result.
Once useful media exists, the balance may shift toward inspection. No fixed
70:30, 65:35, or other final percentage is defined here.

## 7. Preview container law

The surrounding Preview container or dock should remain spatially stable when
media aspect ratio changes. Its internal media viewport may adapt to Manga
page-like portrait media, 16:9, 4:3, 1:1, 9:16, or another supported ratio.

The media changes inside the container; the application's cognitive geometry
should change as little as practical. This reduces reorientation when switching
between Manga pages and H3 video or still results.

## 8. Focus is not navigation

Inspecting a generated result should normally feel like a continuous attention
shift inside the Create workspace, not like leaving the workspace for a new
page or a modal viewer.

The provisional progression is:

- **GLANCE** — compact Preview for rapid output confirmation;
- **FOCUS** — larger in-place media inspection while Create context remains
  perceptible; and
- **INSPECT** — an optional later deep inspection mode for cases that need
  maximum detail.

GLANCE and FOCUS are current concepts. INSPECT is provisional and is not a
required implementation scope.

## 9. Contextual information compression

When Preview enters FOCUS, Create information should be compressed rather than
erased. Useful context may remain visible as a compact summary:

- prompt summary;
- CAST or subject name;
- reference thumbnail;
- Scene or Shot name;
- model; and
- seed.

Lower-priority controls may collapse. The user should be able to understand
what produced the inspected result without returning through a separate
navigation step.

## 10. Hover, click, and contextual help

Hover should provide a small affordance, highlight, or explanation. It should
not trigger a major layout expansion while the pointer merely passes through a
control area.

Click may enter FOCUS. A later implementation may allow click outside, Escape,
or an explicit toggle to leave FOCUS; the exact choice is not fixed here.

Controls that occupy similar cognitive coordinates but have different meanings
may expose concise progressive help:

1. short label;
2. brief hover or focus explanation; and
3. advanced detail when requested.

For example, Manga Reference Appearance should explain CAST appearance and
area relation, while H3 Reference/R2V should explain its video subject and
motion purpose. Guide / ControlNet help should explain geometric or
compositional control.

## 11. Truthful generation feedback

After Generate is pressed, the UI must immediately communicate that work has
started. Feedback is ordered by truthfulness:

1. real measurable progress, such as sampling step 7 / 16;
2. a real execution phase, such as Preparing, Loading, Conditioning,
   Sampling, Decoding, or Saving; and
3. an indeterminate activity indicator when reliable progress is unavailable.

Precise percentages must not be invented merely to appear responsive. If an
older verified result remains visible while a new job runs, status may overlay
that Preview without destroying the old result.

Generation status should not consume a permanent large region. It can be
projected near Generate, over the current Preview, or in both places when the
projection is concise and truthful.

## 12. Media controls

Preview interaction grammar should stay recognizable while controls follow the
media:

- Manga may expose zoom, pan, and image inspection.
- H3 video may expose play, pause, seek, and time information.

Controls may appear as overlays when that avoids unnecessary permanent chrome.
Their final placement is a later composition decision.

## 13. Workspace law

### Same workspace

Within the same production workspace, preserve cognitive coordinates as much as
practical. Manga Create and H3 Create should keep intent, subject,
space/structure, control, and output discoverable through a related grammar.

### Workspace change

When the task changes, major layout changes are allowed. Create to a future
Assemble or Video Editor may move from form-oriented generation controls to a
viewer, timeline or page strip, asset browser, and inspector. Create to a
Wildcard Editor may use a task-specific editor layout.

This distinction prevents false uniformity across fundamentally different
work.

## 14. Assemble is provisional

A future downstream Assemble workspace may treat generated images, videos,
pages, shots, and takes as reusable **Assets**. A likely information model is:

- Viewer;
- Timeline or page strip;
- Asset browser; and
- Inspector.

This is an architectural direction only. It does not specify or implement an
Assemble workspace.

## 15. Result semantics

A generated PNG or video should eventually be understood as more than a file.
Where possible, TEGAKI should retain the semantic relationship between a
result and its:

- Scene;
- CAST or subject;
- Reference;
- Guide or control;
- seed;
- prompt;
- model;
- LoRA; and
- Shot or Frame context.

This principle does not authorize an authoring-schema change in this document.

## 16. Behavior before composition

Behavior should be stabilized before visual composition. Safe early abstractions
may eventually include concepts such as:

- `MediaPreviewShell`;
- `PreviewFocus` state;
- `GenerationStatus`;
- `ProgressOverlay`;
- `AttachmentCard` interaction grammar; and
- `CompactContext`.

These names are conceptual boundaries, not implementation authorization.

The following remain open for later design and review: exact column ratio,
left-versus-right placement, card density, spacing, transition curve, final
accent palette, and typography.

## 17. Anti-patterns

Avoid:

- an empty Preview dominating the first launch;
- large layout jumps when switching Manga and H3;
- hover accidentally causing major rearrangement;
- a full-screen or modal viewer for every inspection;
- hiding all generation context while examining a result;
- invented progress percentages;
- forcing Utilities into the Production layout;
- sharing runtime or domain semantics merely because UI components look alike;
- prematurely locking layout percentages; and
- treating the current generated image or video as the end of the workflow.

## 18. Current implementation relationship

This is a small source-reality check against the current entry points, not a
full UI audit.

### ALREADY ALIGNED

1. Manga and H3 expose distinct product/domain labels and keep their generation
   surfaces and runtime routes separate.
2. Both provide an explicit prompt/create area and a visible Generate action.
3. Both use recognizable attachment grammar with media readouts or thumbnails,
   Add/Replace/Remove actions, and domain-specific reference explanations.
4. Both expose generation status and a history/result surface separate from the
   authoring or form state; Manga Restore settings is explicitly non-generating.

### PARTIALLY ALIGNED

5. Manga Generate has a stage/Create grid with a sticky stage, scrollable
   Create panel, and history below; H3 has a related wide Preview/control grid
   with lower status and History. Manga Authoring still uses its own canvas and
   Inspector arrangement.
6. H3 has an explicit narrow Create/Result switch, while Manga currently
   collapses its grid responsively without the same explicit Preview focus
   state.
7. Both first-launch empty stages can occupy substantial visual space even
   though the current forms remain available; the Create > Preview direction
   is therefore only partially expressed.

### FUTURE DIRECTION

8. In-place GLANCE → FOCUS with contextual information compression, optional
   INSPECT, and downstream Asset/Assemble semantics are not current product
   behavior and remain future work.

## 19. Decision boundary

This specification governs later layout and component decisions, but it does
not close the composition questions listed above. A future card should define
the Create Workspace information architecture and state flow before any GUI
implementation applies these laws.
