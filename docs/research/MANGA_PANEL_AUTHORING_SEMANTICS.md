# Manga Panel Authoring Semantics: Partitioning, Topology, and Generative Affinities

> **STATUS:**  
> **FUTURE RESEARCH & ARCHITECTURE REFERENCE ONLY**  
> **LATE / LAST-STAGE STUDIO CAPABILITY**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**  

This document deepens the Manga Studio research into a focused semantic study of comic and manga panel authoring. It establishes the architectural foundation for how panel geometry, topology, gutters, and borders should be modeled in a very late-stage **TEGAKI Studio / Assembler** layer, and analyzes how structured page partitioning bridges into TEGAKI's AI generation pipeline.

---

## 1. Executive Summary & Roadmap Guardrail

### 1.1 Central Purpose
The objective of this research is **capability banking**: identifying mature, low-cognitive-load panel authoring abstractions so that when a downstream Studio workspace is eventually built, its design does not default to generic, friction-heavy assumptions (e.g., manually drawing independent coordinate rectangles or building a complex CAD layout engine).

### 1.2 Strict Priority & Roadmap Boundary
- **NOT A Current Implementation Priority**: This document does NOT authorize code creation, schema modifications, ComfyUI node additions, or UI development.
- **Current Core Precedence**: Active generative priorities remain strictly ahead of panel authoring:
  1. Manga Controllability & Generation Reliability
  2. Manga Regional Prompting (MRP) compile & mask precision
  3. Reference Appearance (CAST / IP-Adapter integration)
  4. Guide / ControlNet conditioning stability
  5. Core Create workspace layout & UX completion
- **Downstream Positioning**: Panel authoring belongs strictly to a **late / last-stage Studio workspace** (post-generation assembly or pre-generation page framing). It must never burden or complicate the primary generation workspace.

---

## 2. Central Architectural Question: Independent Rectangles vs. Structured Page Partition

A fundamental design decision for digital comic authoring is how panel collections are represented:

| Dimension | Model A: Collection of Independent Rectangles | Model B: Structured Page Partition (Partition Topology) |
| :--- | :--- | :--- |
| **Conceptual Model** | A flat list of standalone boxes: `[{x, y, w, h}, ...]`. | A page-level space recursively divided by cut-lines into adjacent polygonal regions sharing boundary edges. |
| **Gutter Maintenance** | Fragile. Changing one panel requires manually resizing and moving all neighboring panels to maintain uniform gaps. | Inherent. Gutters are defined as spacing attributes along shared cut boundaries; adjusting one edge automatically maintains gaps. |
| **Authoring Interaction** | Tedious. Dragging boxes, aligning edges, measuring gaps with visual rulers or snapping guides. | Direct & Fast. Slice/knife gestures divide areas in one motion. Dragging a shared edge adjusts both neighbors simultaneously. |
| **Cognitive Load** | High. Constant manual micro-adjustments to prevent overlaps, misalignment, or uneven gutters. | Minimal. Edge movements preserve global page rhythm and gutter consistency automatically. |
| **Generative Bridge** | Loose. Panels are merely isolated crop boxes without topological context. | Robust. Panels carry structural reading order, relative scale, and adjacency context useful for prompting and conditioning. |

### Recommendation: Adopt Model B (Structured Page Partition)
**TEGAKI should firmly model panels as a structured page partition.**  
In commercial manga creation, panels are never isolated boxes floating in a void; they are rhythmic subdivisions of the page (版面 / *Han-men*). While the underlying data structure should be flexible enough to evaluate to clean derived bounding boxes for rendering and generation, the authoring model must treat adjacent panels as topologically coupled.

---

## 3. Core Semantic Separations (De-collapsing the Visual Rectangle)

Naïve graphic systems collapse panels into a single "rectangle object." TEGAKI must strictly separate these seven distinct concerns:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PANEL SEMANTIC LAYERS                           │
├────────────────────────┬───────────────────────────────────────────────┤
│ 1. Panel Geometry      │ Pure normalized polygonal/rectangular bounds  │
│ 2. Topology/Adjacency  │ Shared cut-edges, split ancestry, neighbors   │
│ 3. Gutter              │ Void space/margin between adjacent boundaries │
│ 4. Border Appearance   │ Stroke thickness, line color, corner style    │
│ 5. Border Visibility   │ Boolean toggle per edge/panel (Hidden != Gone)│
│ 6. Content Viewport    │ Transform, pan, zoom, and clipping of media   │
│ 7. Generative Semantics│ Mapping to Scene, MRP, Guide, and aspect ratio│
└────────────────────────┴───────────────────────────────────────────────┘
```

1. **Panel Geometry**: The pure spatial boundary within normalized page space `[0.0, 1.0]`. Expressed as coordinates independent of strokes or resolution.
2. **Topology & Adjacency**: Knowledge of which panels share an edge and which cut-line generated them. Governs coupled movement.
3. **Gutter**: The negative space between panel boundaries. A global or edge-specific spacing rule, not part of the artwork container.
4. **Border Appearance**: Cosmetic rendering rules (stroke width in points/mm, color, corner joints, screentone frame fills).
5. **Border Visibility**: A display flag determining whether a border line is rendered. **A borderless panel remains a fully active spatial and generative container.**
6. **Content Viewport**: The clipping mask and inner placement transform (pan, scale, rotation) for placed or generated artwork.
7. **Generative Semantics**: The role of the panel in directing AI execution (prompt scope, attention masks, aspect ratio suggestion).

---

## 4. Split-First Authoring & Interaction Dynamics

### 4.1 The Split-First Workflow
Decades of comic tool history (Clip Studio Paint, MediBang Paint, Comic Life) confirm that **split-first authoring** is vastly superior to drawing individual boxes:

1. **Base Page**: Author starts with the full inner printable area (版面).
2. **Primary Horizontal Splits**: The page is sliced into 3 or 4 tiers (段) matching narrative beats.
3. **Secondary Vertical Splits**: Individual tiers are cut vertically into 1, 2, or 3 panels.
4. **Coupled Boundary Tuning**: Boundary lines are slid up, down, left, or right to balance visual weight.
5. **Edge Visibility Toggles**: Specific borders are hidden for borderless panels or bleeding art.

### 4.2 Split Scope & Hierarchy
- **Orthogonal Cuts First**: Horizontal and vertical splits cover >90% of manga layouts.
- **Repeated Subdivision (Binary Space Partitioning)**: Slicing a panel creates two sibling children within the same spatial parent.
- **Diagonal Splits (Later Scope)**: Angled/slanted cuts are common in dynamic action manga (shonen action). However, initial semantic models should prioritize axis-aligned rectilinear cuts while designing the geometric representation to accommodate arbitrary polygonal vertices later.

---

## 5. Gutter Mathematics & Asymmetric Spatial Directionality

### 5.1 The Law of Asymmetric Gutters
In Japanese manga (read Right-to-Left, Top-to-Bottom), gutter widths are deliberately asymmetric:
- **Horizontal Gutters (Tier Gaps)**: Substantially wider (**typically 18–25 pt / 6–10 mm**).
- **Vertical Gutters (Panel Gaps)**: Substantially narrower (**typically 6–12 pt / 2–4 mm**).

```
┌────────────────────────────────────────────────────────┐
│                        PANEL 1                         │
├────────────────────────────────────────────────────────┤
│           ▲ WIDE HORIZONTAL GUTTER (e.g. 8mm)          │
├───────────────────────────┬─ NARROW VERTICAL GAP (3mm) │
│          PANEL 2          │          PANEL 3           │
├───────────────────────────┴────────────────────────────┤
│           ▲ WIDE HORIZONTAL GUTTER (e.g. 8mm)          │
├────────────────────────────────────────────────────────┤
│                        PANEL 4                         │
└────────────────────────────────────────────────────────┘
```

### 5.2 Cognitive & Narrative Rationale
The human eye follows the path of least resistance. A narrow vertical gap encourages the reader's gaze to travel horizontally across panels within the same tier. The wide horizontal gutter acts as a visual barrier, preventing the eye from prematurely dropping down into the next tier.

### 5.3 Authoring Requirement
A panel authoring system must provide **independent horizontal and vertical gutter presets**. Applying a single uniform margin around every panel destroys traditional manga reading rhythm.

---

## 6. Shared-Edge Topology & Coupled Movement Models

When a user drags a dividing line between `Panel A` and `Panel B`, both panels must respond while preserving the gutter gap.

### 6.1 Evaluation of Conceptual Topology Models

| Model Type | Mechanics | Advantages | Failure Modes / Disadvantages |
| :--- | :--- | :--- | :--- |
| **1. Split Tree (BSP Tree)** | Recursive binary tree of cuts: each node is a split line (orientation + position), leaves are panels. | Extremely fast; guaranteed no overlapping panels; naturally preserves hierarchy and clean serialization. | Cannot easily represent complex non-hierarchical layouts (e.g., a "pinwheel" layout of 4 interlocking panels). |
| **2. Shared-Edge Graph / Topology** | Nodes are vertices, edges are line segments shared between adjacent polygonal panels. | Supports arbitrary layouts, diagonal cuts, and complex shared junctions. | High algorithmic complexity; risk of self-intersecting polygons or edge-collapsing degeneracy during drag operations. |
| **3. Constraint Graph (Flex / Grid)** | CSS-grid-like rows and columns with fractional track weights (`1fr 2fr`). | Highly responsive to whole-page aspect changes; mathematically robust. | Manga layouts rarely fit pure rectangular grids; broken tiers and staggered panels require awkward column/row spans. |
| **4. Derived Rectangles with Alignment Snapping** | Independent rectangles with soft magnetic alignment heuristics during movement. | Simple initial implementation; familiar from general vector design tools (Figma). | Degrades quickly. Moving an edge leaves gaps or creates overlaps; fails to maintain true gutter invariants without constant user cleanup. |

### 6.2 Architectural Recommendation
- **Initial Structural Abstraction**: A **hierarchical split tree (BSP model)** with orthogonal cuts. It covers standard manga page composition, enforces clean gutter spacing, and prevents geometric corruption.
- **Future Expansion**: Support for arbitrary polygonal boundaries as leaf-node geometry overrides for specialized action panels.

---

## 7. Border Geometry, Thickness, and Visibility Semantics

### 7.1 Separation of Border from Geometry
- **Geometry is the Centerline or Outer Hull**: In mathematical modeling, the panel boundary is an ideal zero-width boundary.
- **Stroke Alignment**: Border thickness should be rendered **inset** (inner stroke) from the geometric boundary, so that increasing border thickness does not expand the panel into the gutter or shrink adjacent panels.

### 7.2 Border Visibility: "Hidden != Absent"
A vital manga convention is the **borderless panel** (枠線なし / 白ヌキ):
- **Visual Expression**: The artwork has no black enclosing line, blending seamlessly into the white page gutter. Frequently used for quiet moments, establishing background shots, dreamscapes, or emotional shock.
- **Semantic Reality**: The panel still exists! It still defines:
  - The image clipping boundary.
  - The Scene spatial prompt conditioning area.
  - The character instance placement zone.
  - The reading order index.
- **Design Rule**: Border visibility must be an independent boolean flag (or per-edge visibility flags) that never destroys the underlying panel container.

---

## 8. Generative Pipeline Affinities: Guide / ControlNet Conditioning

### 8.1 The Structural Conditioning Bridge
One of the highest-value opportunities in combining comic authoring with AI is using structured panel geometry to generate **ControlNet Guide inputs**:

```
[ Structured Panel Topology ]
             │
             ▼
[ Deterministic Canvas Rasterizer ] ──► Clean Black-and-White Lineart / Wireframe
             │
             ▼
[ Optional Rough Sketch Overlay ] ────► Hand-drawn character pose or background line
             │
             ▼
[ ComfyUI Guide / ControlNet ] ───────► Strict Structural & Frame Preservation
             │
             ▼
[ Manga Generation KSampler ] ────────► Art generated with exact panel borders respected
```

### 8.2 Why Structured Panels Excel as Guides
1. **Pixel-Perfect Geometry**: Hand-drawn panel lines in rough sketches are often wobbly, uneven, and poorly aligned. Exporting the editor's vector panel borders creates clean, unambiguous lineart for Lineart or Canny ControlNets.
2. **Stable Gutters**: Generative models frequently bleed background art across gutters if not firmly constrained. High-contrast white gutters in the Guide image instruct the model to keep borders pure.
3. **Repeatable Conditioning**: If a prompt or character seed is re-run, the structural framing remains mathematically identical.

*Boundary Guardrail*: ControlNet numeric strength policies (e.g., 0.8 vs 1.0) and visual border survival require future GPU testing; do not freeze static weights.

---

## 9. Rough Guide vs. Exact Panel Structure

TEGAKI must accommodate two distinct creative starting points:

| Dimension | Exact Structured Panel Geometry (Editor Vector) | Rough Hand-Drawn Guide (Ponchi / E-konte Sketch) |
| :--- | :--- | :--- |
| **Origin** | Created via editor knife splits and parametric gutters. | Drawn loosely by the artist with pen tablet or on paper. |
| **Conditioning Role** | Strong structural anchor. High ControlNet fidelity. | Loose compositional intent. Lower ControlNet fidelity. |
| **Precision** | Mathematical millimeter alignment; exact right angles. | Organic, sketchy, expressive, and variable. |
| **Downstream Usage** | Becomes the permanent clipping mask and final vector border. | Used strictly for initial image synthesis; replaced by clean vector borders during post-generation assembly. |

Both starting points are valid. A creator can rough out a sketchy layout, fit exact vector panels over the sketch, and use both signals harmoniously.

---

## 10. Semantic Boundaries: Panel vs. Scene vs. MRP vs. Guide

A critical architectural pitfall is treating `Panel`, `Scene`, `MRP Region`, and `Guide` as synonyms. They must remain semantically distinct:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC AFFINITY MATRIX                          │
├─────────────────┬─────────────────┬────────────────────────────────────┤
│ Pairing         │ Affinity Status │ Architectural Boundary             │
├─────────────────┼─────────────────┼────────────────────────────────────┤
│ Panel ↔ Scene   │ NATURAL         │ Geometry maps directly; Scene owns │
│                 │                 │ narrative text, Panel owns layout. │
├─────────────────┼─────────────────┼────────────────────────────────────┤
│ Panel ↔ MRP     │ PLAUSIBLE       │ Panel bounds can feed MRP regional │
│                 │                 │ areas, but MRP can be sub-panel.   │
├─────────────────┼─────────────────┼────────────────────────────────────┤
│ Panel ↔ Guide   │ NATURAL         │ Panel borders export directly to   │
│                 │ (Future Bridge) │ ControlNet structural lineart.     │
├─────────────────┼─────────────────┼────────────────────────────────────┤
│ Panel = Scene   │ RISKY / REJECT  │ A single Scene could span multiple │
│ (Direct merge)  │                 │ panels; a panel could host 2 Scenes│
├─────────────────┼─────────────────┼────────────────────────────────────┤
│ Panel = MRP     │ RISKY / REJECT  │ Destroys character-level regional  │
│ (Direct merge)  │                 │ conditioning inside a panel.       │
└─────────────────┴─────────────────┴────────────────────────────────────┘
```

- **Panel**: A visual, geometric, and spatial layout container on a physical page.
- **Scene**: A unit of narrative intent, text prompting, and visual atmosphere.
- **MRP Region**: A localized spatial conditioning mask for prompt isolation (e.g., character hair, clothing).
- **Guide**: A visual structural constraint (pose, depth, lineart) feeding ControlNet.

*Conclusion*: A Panel may inform the coordinates of a Scene or MRP area, but its data model must remain decoupled from prompt conditioning engines.

---

## 11. Latent Aspect Ratio & Crop Viewport Affinities

### 11.1 The Aspect Ratio Bucketing Affinity
Modern diffusion models (SDXL, Illustrious-XL) use discrete **latent aspect ratio bucketing** (e.g., 768x1344, 832x1216, 1024x1024, 1216x832, 1344x768) to prevent distortion.

### 11.2 The Suggested Ratio Rule
- When generating artwork for an authored panel, the panel's physical aspect ratio (`width / height`) should be compared against supported model buckets.
- **The system should suggest or default to the closest matching aspect ratio bucket.**
- *Preserve User Override*: The system must **never force** mandatory crop locking. A creator may deliberately choose to generate a wide 16:9 landscape image and crop a tall vertical slice for dramatic compositional tension.

---

## 12. Content Container Dynamics & Non-Destructive Viewports

### 12.1 The Clipping Viewport Pattern
Once an image is placed into a panel, the panel acts as a **non-destructive visual aperture**:
- **Independent Transform**: The placed image possesses its own translation `(dx, dy)`, scale `(sx, sy)`, and optional rotation `(deg)`.
- **Clipping Mask**: The image is rendered strictly within the panel polygon. Pixels extending beyond the panel boundary are masked, not discarded.
- **Re-Framing**: The artist can pan or zoom the artwork at any time to re-compose the shot without re-generating.

---

## 13. Deferred Expressive Capabilities (Bleed-Through & Frame Breaking)

Certain advanced manga layout techniques must be acknowledged but strictly **deferred**:

```
[ Deferred Expressive Techniques ]
   ├── Frame Breaking (枠線はみ出し): Character sword/head bursting outside panel
   ├── Inter-Panel Bleed: Action effect crossing over an entire tier gutter
   └── Page-Edge Full Bleed (裁ち落とし): Art extending past trim lines
```

- **Assessment**: These techniques require foreground/background layer separation, semantic alpha masking, and complex z-ordering rules.
- **Classification**: **STUDY LATER**. They are not required for a viable first-generation Studio paneling system.

---

## 14. Speech Balloon & Dialogue Boundary

The detailed design of speech balloons belongs to a separate investigation, but the semantic boundary relative to panels must be locked:
1. **Dialogue is Structured Vector Data**: Never baked into diffusion pixel outputs.
2. **Panel Owns Narrative Context**: A balloon is typically parented to a panel for reading order and script tracking.
3. **Balloon Does NOT Reshape the Panel**: The speech bubble floats as an independent vector overlay layer above the clipped artwork.
4. **Pre-Gen Spatial Reservation**: An authored balloon area can optionally provide a negative spatial bias to prevent character faces from appearing under text.

---

## 15. Lessons from Traditional Manga Tools & ComfyUI Comic Creator

| Teacher | Primary Lesson | Architectural Warning / Anti-Pattern to Avoid |
| :--- | :--- | :--- |
| **Clip Studio Paint** | Frame Border folders are the gold standard of non-destructive clipping and knife-based subdivision. | Do not replicate CSP's hundreds of dense sub-tool preference panels and tiny numeric coordinate fields. |
| **MediBang Paint** | Pure simplicity: click-and-drag knife tool makes paneling accessible to absolute beginners in 5 seconds. | Avoid purely raster panel cuts that cannot be adjusted topologically after the cut is made. |
| **Comic Life 3** | Parametric extension balloons and direct asset placement create an intuitive, playful layout experience. | Avoid rigid photo-comic templates that feel too stiff for dynamic manga storytelling. |
| **ComfyUI Comic Creator** | Proves an SPA can manage multi-page comic layouts inside ComfyUI with SVG normalization. | **Anti-Pattern**: Embedding full 3D DCC editors, keyframe animators, and full raster paint suites destroys workspace focus. |

---

## 16. Cognitive-Load & Direct Manipulation Principles

Adhering to TEGAKI's **GLANCE / FOCUS** and low-friction principles, panel authoring must follow these interaction laws:

1. **Direct Manipulation over Forms**: Creating and adjusting panels must happen directly on the canvas via split lines and edge-dragging handles. Users must never be forced into a "Panel Properties" modal to enter `{ x: 0.12, y: 0.45, w: 0.38, h: 0.22 }`.
2. **Invisible Gutters Until Sliced**: The canvas starts clean. Slicing automatically introduces gutters without requiring gutter setup wizards.
3. **Transient Tooling**: Knife and edge-drag tools appear contextually on hover or active selection, leaving the canvas unobstructed during reading and evaluation.
4. **Zero-Configuration Defaults**: Sensible manga standards (asymmetric gutters, 2pt black border, auto-snapping to inner margins) must work out of the box without manual tweaking.

---

## 17. Strategic Maturity Classification Table

Every evaluated panel authoring concept is categorized according to TEGAKI's architectural vocabulary:

| Capability / Primitive | Strategic Maturity Classification | Rationale & Architectural Status |
| :--- | :--- | :--- |
| **Split-first panel creation** | `CORE LATE-STUDIO PRIMITIVE` | The universal, lowest-friction interaction pattern for manga paneling. |
| **Asymmetric horizontal/vertical gutters** | `CORE LATE-STUDIO PRIMITIVE` | Essential for correct manga reading cadence; must be supported by default. |
| **Independent border width** | `CORE LATE-STUDIO PRIMITIVE` | Basic graphic presentation; cleanly decoupled from coordinate geometry. |
| **Coupled shared-boundary movement** | `CORE LATE-STUDIO PRIMITIVE` | The core defining feature separating structured partitions from crude box drawing. |
| **Border visibility toggle** | `CORE LATE-STUDIO PRIMITIVE` | Supports borderless frames while preserving container and generative semantics. |
| **Non-destructive clipping viewport** | `CORE LATE-STUDIO PRIMITIVE` | Fundamental post-generation placement; allows pan/zoom without re-running diffusion. |
| **Panel → ControlNet Guide export** | `HIGH-AFFINITY FUTURE GENERATIVE BRIDGE` | High leverage: transforms clean vector panel lines into structural lineart guides. |
| **Panel → MRP geometry affinity** | `HIGH-AFFINITY FUTURE GENERATIVE BRIDGE` | Panel coordinates can directly seed regional prompting bounding boxes. |
| **Panel → Scene affinity** | `HIGH-AFFINITY FUTURE GENERATIVE BRIDGE` | Natural narrative mapping: one panel usually represents one visual Scene. |
| **Aspect ratio bucket suggestion** | `HIGH-AFFINITY FUTURE GENERATIVE BRIDGE` | Translates panel dimensions into optimal SDXL/Illustrious latent generation sizes. |
| **Dynamic frame breaking (Bleed-through)** | `STUDY LATER` | Highly expressive, but requires complex multi-layer alpha masking. Defer. |
| **Diagonal / non-orthogonal cuts** | `STUDY LATER` | Valuable for action shonen manga; defer until orthogonal split tree is solid. |
| **Pre-generation balloon reservation** | `STUDY LATER` | High potential to prevent occluded faces, but requires negative mask conditioning. |
| **Full SVG template library** | `REFERENCE ONLY` | Useful external bridge (Inkscape/Affinity), but secondary to native direct cuts. |
| **Embedded 3D posing in panel canvas** | `REJECT / TOO HEAVY` | Massive UI clutter and bundle bloat; belongs in external tools or isolated Guides. |
| **In-canvas raster brush / paint suite** | `REJECT / TOO HEAVY` | Outside TEGAKI's scope; users should ink/paint in dedicated art applications. |

---

## 18. Proposed Future Implementation Slicing

When authorized for implementation in a future late-stage Studio milestone, the panel capability should be divided into no more than **five bounded slices**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PROPOSED STUDIO SLICING SEQUENCE                     │
├────────────────────────────────────────────────────────────────────────┤
│ Slice 1: Pure Panel Partition Geometry (Split Tree & Normalized Bounds)│
│ Slice 2: Coupled Edge Manipulation & Asymmetric Gutter Rules           │
│ Slice 3: Non-Destructive Content Viewport (Image Placement, Pan/Zoom)  │
│ Slice 4: Cosmetic Border Presentation & Edge Visibility Toggles        │
│ Slice 5: Generative Bridge (Aspect Ratio Sync & ControlNet Guide Export│
└────────────────────────────────────────────────────────────────────────┘
```

1. **Slice 1: Pure Panel Partition Geometry**  
   - Pure, zero-I/O data structure representing recursive orthogonal cuts.
   - Computes derived normalized bounding boxes `[0.0, 1.0]` for all leaf panels.
2. **Slice 2: Coupled Edge Manipulation & Gutter Math**  
   - Interactive shared-edge dragging logic.
   - Independent horizontal and vertical gutter subtraction.
3. **Slice 3: Non-Destructive Content Viewport**  
   - In-panel image placement with localized translation and scaling.
   - SVG/CSS clipping mask evaluation.
4. **Slice 4: Cosmetic Border Presentation & Visibility**  
   - Stroke width and color styling.
   - Per-panel border visibility toggle (borderless frames).
5. **Slice 5: Generative Bridge & Guide Export**  
   - Deterministic export of clean panel lineart to ComfyUI Guide / ControlNet inputs.
   - Suggested aspect ratio bucket mapping for generation requests.

---

## 19. Questions for Future Astra Architecture Review

The following six questions summarize the critical trade-offs for future architecture review:

1. **Split-Tree vs. Planar Graph**: Does a recursive binary split tree provide sufficient expressive freedom for manga storytelling, or will creators immediately demand non-hierarchical interlocking cuts that require a full planar topology graph?
2. **Panel vs. Scene Ownership**: Should a `Panel` own a `Scene` (structural container owns narrative intent), or does a `Scene` reference a `Panel` (narrative intent references a physical display viewport)?
3. **Boundary Inset vs. Centered Stroke**: Should panel stroke thickness strictly render inward (inset) to preserve exact gutter voids, or is centered stroke acceptable if gutters absorb stroke variance?
4. **Guide Export Authority**: Should panel border lineart be generated as a synthetic PIL/canvas image inside the frontend before dispatch, or compiled deterministically by a backend ComfyUI node from panel coordinates?
5. **Pre-Generation Cognitive Burden**: How can panel-guided generation remain spontaneous without forcing creators to author a full multi-panel page before testing their first prompt?
6. **Deliberate DTP Omissions**: What vector desktop-publishing tools (e.g., pathfinder operations, arbitrary Bézier warping, complex text threading) must TEGAKI permanently refuse to implement to maintain UX simplicity?
