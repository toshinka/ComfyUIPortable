# Manga Studio Authoring & Previs Inventory: Panel, Balloon, and Pre/Post-Generation Workflows

> **STATUS:**  
> **FUTURE RESEARCH INVENTORY ONLY**  
> **LATE / LAST-STAGE STUDIO CAPABILITY**  
> **NO CURRENT IMPLEMENTATION AUTHORIZATION**  

This document inventories modern comic and manga page-authoring tools, interaction models, and vector/layout primitives as long-term architectural reference for a future **TEGAKI Studio** layer. It records mature digital comic creation conventions, evaluates how those primitives intersect with TEGAKI's AI generation pipeline, and establishes strict guardrails to prevent premature UI complexity.

---

## 1. Scope & Non-Goals

### 1.1 Scope
- **Domain Focus**: Panel/frame layout, gutter splitting, image containment/clipping, speech balloons, editable dialogue typography (including vertical Japanese text), reading order, and previs/rough layout semantics.
- **Pipeline Integration**: Analyzing the bidirectional relationship between vector/layout primitives and AI generation (pre-generation spatial framing/reservation vs. post-generation assembly/finishing).
- **Target Layer**: A provisional, late-stage **TEGAKI Studio / Assembler** workspace that consumes generated assets without burdening current generation authoring.

### 1.2 Non-Goals & Strict Guardrails
- **NO Implementation**: This document does NOT authorize code creation, schema changes, node definitions, or UI development.
- **NO Current Priority Displacement**: This research must NOT divert resources from active milestones: Minimum Regional Prompting (MRP), Reference Appearance (CAST / IP-Adapter), Guide / ControlNet conditioning, generation reliability, and core Create workspace UX.
- **NO Re-inventing Art Applications**: TEGAKI is not attempting to clone Photoshop, Clip Studio Paint, or Illustrator. Bitmap painting, complex raster filters, and manual inking remain the domain of dedicated art tools.
- **NO Monolithic ComfyUI SPA Duplication**: Features that impose permanent screen-space costs, multi-tab layout suites, or heavy 3D scene editors are specifically cataloged for architectural critique, not direct emulation.

---

## 2. Current Reference Tools

### 2.1 Primary Reference: ComfyUI Comic Creator
- **Origin & Nature**: Open-source ComfyUI custom node by `ketle-man` functioning as an embedded Single-Page Application (SPA).
- **Core Architecture**: Canvas-based interactive workspace combining SVG/template paneling, nested sub-panels, vector balloon/text engine, raster painting, 3D posing (VRM/Three.js), and script-to-balloon injection.
- **Primary Relevance**: Demonstrates how a ComfyUI web environment can host end-to-end comic assembly, while illustrating the severe UI density and cognitive load risks of packaging an entire desktop DTP suite into a web node.

### 2.2 Comparison Reference: Clip Studio Paint (CSP)
- **Origin & Nature**: Industry standard commercial manga and comic production software (Celsys).
- **Key Mechanics**:
  - *Frame Border Folders (コマ枠フォルダー)*: Vector clipping masks functioning as container layers with dedicated sub-tool splitting.
  - *Gutter Mathematics*: Asymmetric vertical (narrow, ~3-5mm) versus horizontal (wide, ~7-10mm) gutters enforcing Japanese reading flow.
  - *Unified Balloon Engine*: Vector balloon primitives with parametric tails, auto-sizing to text, and seamless pathfinder-style merging.

### 2.3 Comparison Reference: MediBang Paint / FireAlpaca
- **Origin & Nature**: Lightweight, accessible digital manga creation tools (MediBang Inc. / pg-o-shiki).
- **Key Mechanics**:
  - *Slice-First Knife Tool*: Instant edge-to-edge canvas cutting for panel division without vector point manipulation.
  - *Zero-Overhead Cloud Typography*: Simple, non-destructive text overlays with basic balloon presets.

### 2.4 Additional Modern Reference Tools (Targeted Selection)
1. **Comic Life 3 (plasq)**: Originator of parametric "extension balloons" (multi-bubble dialogue chains connected by auto-stretching necks) and drag-and-drop panel photo layout.
2. **Krita (Comic Project & Callout Shapes)**: Vector shape-based panel management with non-destructive grouping and callout shape manipulation.
3. **Clip Studio Webtoon / Scroll Editors**: Continuous vertical strip canvas with dynamic slice markers and reading-pacing metrics, contrasting with fixed print spreads.
4. **Figma / Modern Auto-Layout Systems**: Parametric flex-box layouts where resizing a parent frame automatically adjusts nested children and gutters according to strict layout constraints.

---

## 3. Mature Panel-Authoring Primitives

Decades of digital manga tool evolution have converged on a set of universal, mature geometric primitives for paneling:

| Primitive | Industry Standard Pattern | Interaction & Geometry Behavior | User Value |
| :--- | :--- | :--- | :--- |
| **Frame Container** | Layer folder / Group mask | Clipping rectangle or polygon bounding child raster/vector content. Child transforms are masked by the frame boundary. | Isolates artwork per panel; prevents manual cropping. |
| **Knife / Splitter** | Line/Raycast division | Dragging a line across an existing panel cuts it into two polygons. The cut angle determines panel dynamism. | Replaces manual polygon coordinate plotting with direct gestures. |
| **Gutter Spacing** | Configurable gap width | Automatically subtracts uniform or directional margins between adjacent cut edges. Japanese manga defaults to `W_horizontal > W_vertical`. | Maintains clean gutters without manual vertex offsetting. |
| **Linked Edge Adjustment** | Shared boundary manipulation | Dragging a shared edge or gutter moves the boundaries of both adjacent panels simultaneously. | Preserves page layout integrity during proportion edits. |
| **Bleed / Tachi-kiri** | Outer canvas snapping | Snapping panel outer borders past the safe inner margin (版面 / Han-men) to the outer trim/bleed line. | Supports full-bleed dramatic story climaxes. |
| **Sub-Panels / Insets** | Nested frame containment | A child frame parented to a master panel, cropped by the parent if it extends past the parent's boundary. | Small reaction shots or detail insets within an overarching scene. |

---

## 4. Mature Balloon & Dialogue Primitives

Speech balloons in manga are structural narrative elements, not simple text boxes:

| Primitive | Industry Standard Pattern | Interaction & Geometry Behavior | Typography & Layout Behavior |
| :--- | :--- | :--- | :--- |
| **Parametric Bubble** | Vector spline / ellipse / burst | Elliptical, rounded rectangle, cloud (thought), or burst (spiky shout). Burst controls often feature notch/tip curvature sliders. | Vector shape auto-scales to text bounds or maintains fixed bounds with text auto-wrapping. |
| **Targeted Tail** | Connected bezier anchor | Draggable tail base and tip. Moving the tip aims at the speaking character; moving the balloon recalculates the tail base. | Tail length can be set to zero for narration boxes or telepathic dialogue. |
| **Extension Balloon** | Neck-linked bubbles | Adding a linked subsidiary bubble for multi-part sentences. Overlapping geometry merges outer paths without interior lines. | Breaks long dialogue into readable rhythmic cadences without creating multiple independent objects. |
| **Vertical CJK Flow** | `writing-mode: vertical-rl` | Characters stack top-to-bottom; columns advance right-to-left. Punctuation, small kana, and tate-chu-yoko rotate correctly. | Essential for Japanese manga. Requires multi-line column balance and vertical/horizontal alignment toggles. |
| **Manga Typography** | Antique/Gothic pairing | Standard Japanese manga uses Mincho/Antique for kanji and Gothic for kana (e.g., FOT-AntiqueMinDB), with thick strokes. | High contrast readability against screentones and complex artwork. |
| **Reading Order** | Ordered graph / sequence | Dialogue and panels evaluated strictly Right-to-Left, Top-to-Bottom (for Japanese) or Left-to-Right (Western). | Dictates viewer eye travel and narrative timing. |

---

## 5. ComfyUI Comic Creator Lessons

`comfyui-comic-creator` provides a comprehensive blueprint of an all-in-one AI comic tool inside ComfyUI. Analyzing its specific mechanisms yields distinct classifications:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   COMFYUI COMIC CREATOR ARCHITECTURE                   │
├────────────────────────┬───────────────────────┬───────────────────────┤
│    Page Management     │      Layout Tab       │    AI / Generation    │
│  - Work / Page groups  │  - Vector paneling    │  - Nanobanana T2I/I2I │
│  - SVG Template import │  - Parametric balloon │  - Image Tab editing  │
│  - Split line wizard   │  - Extension balloons │  - Background removal │
│  - Multi-format export │  - VRM 3D Pose / Text │  - Workflow Studio    │
└────────────────────────┴───────────────────────┴───────────────────────┘
```

### 5.1 Component Breakdown & Classification

#### 1. SVG-Based Panel Templates & Normalization
- *Mechanism*: Panels defined as clean SVG paths (`rect`, `polygon`, `path`), normalized to internal coordinates (0.01mm units). Major vector tools (Inkscape, Illustrator, Affinity) can author templates.
- *Classification*: **TEACHER**
- *Lesson*: Using standard vector geometry (SVG) for panel definitions decouples layout from rendering resolutions and allows lossless external interchange.

#### 2. Split Wizard
- *Mechanism*: Visual knife tool allowing the user to draw a dividing line across the page to split panels with automated gutter spacing.
- *Classification*: **POSSIBLE FUTURE TEGAKI PRIMITIVE**
- *Lesson*: Panel splitting is the fastest, lowest-friction UX for comic composition. Manually typing coordinate bounding boxes is too tedious for real page layout.

#### 3. Extension Balloons (Linked Multi-Bubble)
- *Mechanism*: "Add Extension" links a child bubble via a neck. Dragging moves the neck; overlapping bubbles unite their outer perimeter cleanly.
- *Classification*: **TEACHER**
- *Lesson*: Solves the common comic problem where an AI generation leaves awkward narrow vertical space requiring dialogue to be broken across stacked bubbles.

#### 4. Embedded Vertical Japanese Text Engine
- *Mechanism*: True vertical text layout with font selection, outline/stroke, line-height control, and auto-wrapping within balloon contours.
- *Classification*: **TEACHER**
- *Lesson*: Vertical text cannot be treated as a simple CSS rotation hack; it requires proper column wrapping, tate-chu-yoko, and baseline alignment.

#### 5. Script-to-Layout Tab
- *Mechanism*: Hierarchical script tree (Story -> Page -> Panel -> Dialogue) with buttons to inject dialogue text directly into layout balloons.
- *Classification*: **POSSIBLE FUTURE TEGAKI PRIMITIVE**
- *Lesson*: Maintaining dialogue as structured text linked to panel identifiers bridges the gap between pre-generation intent and post-generation layout.

#### 6. Nested Sub-Panels
- *Mechanism*: Dragging an inset sub-panel into an existing panel, inheriting parent clipping and transformation.
- *Classification*: **REFERENCE ONLY**
- *Lesson*: High utility for inset detail shots, but introduces hierarchy complexity that should remain secondary until basic panels are rock-solid.

#### 7. Full 3D Pose & Lighting Suite (VRM / Three.js / Keyframe Timeline)
- *Mechanism*: Integrated 3D viewport inside the layout canvas to load VRM characters, manipulate bones, adjust lighting, and bake poses.
- *Classification*: **TOO HEAVY / UI COST**
- *Lesson*: While powerful, embedding a full 3D DCC suite inside the page canvas creates immense cognitive overhead, high bundle size, and UI clutter. In TEGAKI, pose guidance belongs in dedicated Guide/ControlNet routes or external tools, not embedded permanently in page composition.

#### 8. Full Layer-Based Raster Paint Suite & Custom Brush Engine
- *Mechanism*: In-canvas raster drawing with pressure sensitivity, layer blending, and manual painting.
- *Classification*: **TOO HEAVY / UI COST**
- *Lesson*: Competing with established art tools (CSP, Krita, Photoshop) on brush engines is a trap. TEGAKI should focus on generative coordination and assembly, leaving deep painting to dedicated art software.

#### 9. Disconnected Nanobanana AI Node Routing
- *Mechanism*: Uses a proprietary generation wrapper or connects to external Workflow Studio instances.
- *Classification*: **DUPLICATES EXISTING TEGAKI CONCEPT**
- *Lesson*: TEGAKI already has superior, disciplined domain architecture (Manga Basic Generation, Scene Compilers, MRP Regional Conditioning, and Authoring Contracts). Comic Creator's generation wiring is ad-hoc compared to TEGAKI's strict contracts.

---

## 6. Traditional Manga-Tool Lessons (CSP & MediBang)

### 6.1 Panel Division: The "Knife" Gesture vs. Coordinate Inputs
- In Clip Studio Paint, artists almost never create panels by entering width/height or drawing individual rectangles. They start with a single full-page inner border (版面) and make 3 to 5 quick slices with the "Divide frame border" tool.
- *Key Takeaway*: Panel authoring must be gesture-driven (cut, slide, drag-gutter) rather than numeric property entry.

### 6.2 Non-Destructive Vector Geometry
- CSP stores frame borders as editable vector paths. If a user shifts a character or changes an angle later, they drag a vertex or an entire gutter, and the underlying artwork's clipping mask instantly updates without re-rasterizing.
- *Key Takeaway*: Layout geometry must remain dynamic vector data throughout the entire project lifecycle.

### 6.3 Asymmetric Gutter Mathematics
- Japanese manga storytelling relies on unambiguous reading flow. Horizontal gutters (between tiers) are intentionally wide (typically 18–25 pt / 6–10 mm) to act as visual dams, preventing the reader's eye from dropping down prematurely. Vertical gutters (between panels in the same tier) are narrow (typically 6–12 pt / 2–4 mm) to encourage horizontal scanning.
- *Key Takeaway*: Gutter tools must support independent horizontal and vertical spacing presets as standard defaults.

### 6.4 Text-Driven vs. Shape-Driven Balloons
- In MediBang and CSP, typing text automatically expands the balloon envelope if auto-sizing is active; conversely, resizing the balloon reflows the text.
- *Key Takeaway*: Dialogue length is highly variable. Rigid, fixed-size balloon templates force the user into tedious manual resizing; text-first auto-bounding provides a vastly faster authoring flow.

---

## 7. Pre-Generation Opportunities

Combining comic authoring primitives with an AI generation pipeline unlocks capabilities that traditional DTP software cannot provide:

```
[ Pre-Generation Intent ]
   │
   ├── Panel Aspect Ratio / Crop ──────► KSampler Latent Dimensions (Bucket matching)
   ├── Panel Boundary / Coordinates ───► Scene / MRP Regional Conditioning Area
   ├── Character Instance Placement ───► IP-Adapter Regional Attention Mask (attn_mask)
   ├── Guide / Structural Pose ────────► ControlNet Preprocessor Boundary (OpenPose/Lineart)
   └── Balloon Spatial Reservation ────► Inpainting Mask / Negative Prompt Spatial Bias
```

### 7.1 Panel Geometry as Generation Target (Aspect Ratio & Bucketing)
- Instead of generating a generic square or 3:4 image and awkwardly cropping it to fit a tall vertical panel, the panel's exact aspect ratio informs the latent generation resolution (snapped to standard 64px or SDXL/Illustrious aspect ratio buckets).
- The AI generates artwork specifically composed for the panel's physical proportions.

### 7.2 Panel as Scene & Regional Conditioning Scope (MRP Affinity)
- In TEGAKI Manga, a `Scene` defines spatial prompts, while MRP (Manga Regional Prompting) localizes characters.
- When panel geometry is recognized pre-generation, a panel directly defines a `Scene` coordinate boundary. Multi-panel pages can be compiled into a unified generation pass or cleanly separated into discrete panel-level execution graphs with zero manual coordinate entry.

### 7.3 Balloon Spatial Reservation (Preventing Character Occlusion)
- A persistent problem in AI manga creation is placing speech bubbles directly over characters' faces or key focal points because the image was generated blindly without knowing where dialogue would sit.
- *Pre-generation opportunity*: If the user places a provisional balloon or dialogue marker *before* generation, that area can serve as:
  1. A negative prompt conditioning bias (e.g., negative attention on faces/details in that corner).
  2. A spatial mask hint instructing the composition engine to keep that corner low-contrast or background-only.
  3. A composition guide ensuring the primary subject is framed away from the dialogue zone.

### 7.4 Rough / Previs Sketch Guidance
- A simple brush stroke, rough line, or 3D stick-figure placed inside a panel pre-generation acts directly as the ControlNet / Guide input, anchoring character scale, eye-line, and camera distance.

---

## 8. Post-Generation Opportunities

Once raw imagery is generated by the diffusion model, the authoring layer transitions into non-destructive finishing:

```
[ Generated Imagery ]
   │
   ▼
[ Frame Container Clipping ] ──────── Non-destructive pan/zoom/rotate inside panel
   │
   ▼
[ Bleed-Through / Tachi-kiri ] ────── Character limb/weapon pops outside panel border
   │
   ▼
[ Vector Balloon & Dialogue ] ─────── Crisp 600dpi vector text over 72-96dpi AI raster
   │
   ▼
[ Multi-Lingual Re-Typeset ] ──────── Swap script text without re-running diffusion
```

### 8.1 Non-Destructive In-Panel Pan, Zoom, and Crop
- The generated image is placed inside the panel container as a masked layer. The artist can pan, scale, or rotate the artwork within the frame to perfect the composition, without altering the underlying generated source file.

### 8.2 Dynamic Bleed-Through (Frame Breaking / 枠線はみ出し)
- A classic manga technique: a dramatic character sword, hair strand, or explosion breaks through the panel border into the gutter or adjacent panel.
- *Post-generation opportunity*: By providing a simple "foreground pop-out" mask or AI background removal layer, elements of the generated image can effortlessly break outside the panel mask while the background remains cleanly clipped.

### 8.3 Vector Typography & Independence from Diffusion Text
- AI models notoriously struggle with small, crisp, legible typography, and cannot render vertical Japanese dialogue reliably.
- *Post-generation rule*: Never bake dialogue into the diffusion generation. Keeping balloons and dialogue as vector/text overlays ensures:
  - Perfect vector sharpness at any export resolution (print-ready 300/600dpi).
  - Effortless typos corrections and editorial rewrites in seconds.
  - Multi-language translation without touching the artwork.
  - Independent styling (screaming fonts, thought fonts, narration boxes).

---

## 9. Potential TEGAKI Semantic Affinities

Mapping mature external comic primitives to current TEGAKI architecture reveals strong natural affinities:

```
┌─────────────────────────────────┬──────────────────────────────────────────┐
│ External Comic Authoring Model  │ Current TEGAKI Architecture Counterpart  │
├─────────────────────────────────┼──────────────────────────────────────────┤
│ Panel / Frame Boundary          │ Scene Area / Page Layout Geometry        │
│ Inset Sub-Panel                 │ Sub-Scene / Nested Regional Area         │
│ Character In-Panel Placement    │ character_instance Area                  │
│ Rough Sketch / Previs Pose      │ Guide Conditioning (Lineart / ControlNet)│
│ Character Sheet Reference       │ CAST Reference Asset (IP-Adapter)        │
│ Dialogue Script Entry           │ Scene Narrative Intent / Prompt Metadata │
│ Gutter & Bleed Specifications   │ Canonical Page Margin Constants          │
│ Page Spread                     │ Document / Page Spec                     │
└─────────────────────────────────┴──────────────────────────────────────────┘
```

### 9.1 Panel Geometry ↔ Scene / Regional Area
- TEGAKI already possesses a pure geometry core (`tegaki_manga_nodes/canonical_area_geometry.py`) operating on page-normalized coordinates `[0.0, 1.0]`.
- Future paneling primitives map 1:1 onto normalized `area` rectangles `{ x, y, w, h }`, allowing panel layouts to directly feed the Manga Regional Compiler without translation overhead.

### 9.2 Dialogue ↔ Scene Metadata & Prompt Enrichment
- In current TEGAKI authoring contracts, prompt text is tied to Scenes.
- Dialogue assigned to a panel can automatically enrich the Scene's prompt conditioning (e.g., extracting emotional state: "angry shout" -> adds `(angry, yelling:1.1)` to the regional prompt) while keeping the literal dialogue text reserved for the vector overlay.

---

## 10. UI-Cost & Learning-Cost Risks

Tools like ComfyUI Comic Creator demonstrate that cramming desktop publishing (DTP) workflows into an AI tool carries immense product hazards:

| Danger Area | Specific Manifestation in External Tools | TEGAKI Design Risk | Prevention Rule |
| :--- | :--- | :--- | :--- |
| **Monolithic Workspace Overload** | 7+ permanent tabs, nested menus, 3D viewports, and full raster brush palettes. | Overwhelms the user; obscures core AI generation workflow; destroys the GLANCE/FOCUS UI model. | Studio must be a separate downstream workspace. Authoring stays minimal until finishing is needed. |
| **Duplicate Abstractions** | Having separate "layers", "panels", "sub-panels", and "objects" all with independent coordinate systems. | Users lose mental model of what feeds generation vs what is just visual markup. | Unified coordinate space; clear boundary between generation inputs and post-generation overlays. |
| **Premature Rigidity** | Forcing the user to build a 6-panel finished template before generating a single concept test. | Discourages rapid ideation and iterative visual exploration. | Generation must remain possible from a single loose panel or freeform canvas without formal templates. |
| **Heavy Vector Curve Clutter** | Exposing Pen/Bézier node handles for every balloon tail and panel edge. | Requires Illustrator-level mouse dexterity; high cognitive cost. | Constrain vector manipulation to simple parametric handles, presets, and direct knife cuts. |
| **Font Management Nightmare** | Requiring local filesystem font scanning, Base64 font embedding, and font licensing alerts. | High web bundle overhead, cross-platform font rendering inconsistencies. | Curate standard open-source manga font pairings (e.g., Shippori Mincho, M PLUS 1p) with sensible fallbacks. |

---

## 11. KEEP / STUDY LATER / REJECT-AS-PRODUCT-PATTERN

To protect TEGAKI's architectural focus, external capabilities are strictly triaged:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CAPABILITY TRIAGE                             │
├────────────────────────┬───────────────────────┬───────────────────────┤
│          KEEP          │      STUDY LATER      │        REJECT         │
│  (High affinity, low   │ (Valuable, but late-  │ (Anti-patterns, high  │
│      cognitive cost)   │    stage / deferred)  │  cost, low AI return) │
├────────────────────────┼───────────────────────┼───────────────────────┤
│ • Knife split gesture  │ • SVG template export │ • Embedded 3D DCC     │
│ • Asymmetric gutters   │ • Linked multi-bubble │ • Full raster paint   │
│ • Container clipping   │ • Bleed-through mask  │ • Pen/Bézier curves   │
│ • Vector text overlay  │ • Script-to-balloon   │ • Permanent palettes  │
│ • Aspect bucket sync   │ • Pre-gen reservation │ • In-image text bake  │
└────────────────────────┴───────────────────────┴───────────────────────┘
```

### 11.1 KEEP (High Affinity / Essential Studio Primitives)
- **Direct Knife/Split Gesture**: Dividing panels by drawing a line with automatic gutter subtraction.
- **Asymmetric Gutter Defaults**: Built-in Japanese manga spacing (`W_horiz > W_vert`).
- **Non-Destructive In-Panel Container Clipping**: Image masked by panel border with free pan/scale.
- **Separated Vector Typography**: Dialogue strictly maintained as structured vector data, never baked into diffusion.
- **Aspect Ratio Bucket Synchronization**: Panel proportions directly setting generation latent sizes.

### 11.2 STUDY LATER (High Value, Deferred to Late-Stage Studio)
- **SVG Template Import/Export**: Lossless vector layout interchange with Inkscape/Affinity/CSP.
- **Extension Balloons (Comic Life Style)**: Parametric multi-bubble dialogue chains connected by auto-stretching necks.
- **Dynamic Bleed-Through Masking**: Easily popping character elements outside the panel border.
- **Script-to-Balloon Data Binding**: Flowing dialogue from a text script into page layout containers.
- **Pre-Generation Balloon Space Reservation**: Biasing composition/attention maps away from speech areas.

### 11.3 REJECT-AS-PRODUCT-PATTERN (Anti-Patterns for TEGAKI)
- **Embedded 3D DCC Viewport (Three.js/VRM Editor in Canvas)**: Heavy, awkward, and redundant. 3D posing belongs in specialized apps or lightweight Guide inputs.
- **Full In-Canvas Raster Brush / Paint Suite**: Trying to replace CSP/Photoshop with web canvas brushes is an unnecessary drain on development.
- **Fine-Grained Vector Bézier Node Editing**: Complex path manipulation creates high user fatigue; manga layout thrives on simple geometric constraints.
- **Permanent Monolithic Palettes**: Crowding the generation canvas with dozens of persistent DTP toolbars violates TEGAKI's minimal cognitive load principles.
- **Baking Dialogue into Diffusion Output**: Pure anti-pattern for professional manga; destroys resolution and editability.

---

## 12. Questions for Future Astra Review

When the time arrives for an authorized architecture review of the Studio layer, the following questions should guide the evaluation:

1. **Workspace Boundary**: Should page paneling live in the same canvas where single-image generation is triggered, or must it be an explicitly separated downstream "Studio / Assembly" workspace that ingests results?
2. **Authoring Data Authority**: Does a `Panel` become the parent of a `Scene`, or is `Scene` the pure generation intent and `Panel` merely one physical visual representation of that scene on a printed page?
3. **Pre-Generation Constraint Balance**: How much layout detail can be asked of a creator before AI generation without turning a spontaneous idea-generation flow into a tedious pre-planning chore?
4. **Dialogue Pipeline Direction**: Is script-to-layout flow primarily top-down (script written first, generating panels to match) or visual-first (images generated first, balloons positioned to fit the resulting composition)? How does TEGAKI accommodate both styles?
5. **Vector Output Authority**: Should the final export of a TEGAKI page be a single flat raster (PNG/JPEG) with baked metadata, or a standards-compliant SVG / PDF containing separated raster art layers and editable vector text elements?
