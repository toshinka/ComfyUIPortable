# Phase 3L: Prior-Art Adoption and Ecosystem Integration Audit Report

- **Date**: 2026-09-05
- **Author**: Antigravity Assistant & Tegaki Development Engine
- **Scope**: Evaluation of Existing ComfyUI Custom Node Tooling vs. Tegaki Manga Authoring System
- **Governing Architecture Plan**: `Tegaki_ComfyUI_Manga_Authoring_Intermediate_Plan_PriorArt_Integration.md`

---

## 1. Executive Summary & Strategic Shift

Prior to Phase 3L, the development methodology prioritized rapidly building internal components to resolve missing features (e.g. custom regional adapters, mannequin guides, staging editors). While this established essential semantic contracts, continuing to re-implement lower-level generic generation mechanics creates unnecessary maintenance drag and reinvents proven ecosystem wheels.

In accordance with the Intermediate Architecture Plan, Tegaki strictly maintains ownership of **manga-specific semantic authorship**:
- **CAST**: Master Character definitions, identity, style, base/negative prompts, baseline LoRAs.
- **Character Instance**: Re-entrant, panel/subscene-bound appearances with distinct poses and acting overrides.
- **Panel & Page Layout**: Manga panel topologies, shared vertices, gutter preservation.
- **Scene & SubScene**: Separation of visible panels from semantic scenes (`Visible Panels ≠ Internal Scenes`).
- **Staging & Interaction**: Relational binding (e.g., handshake, gaze direction) independent of backend diffusion.
- **Manga Semantic Compiler**: Pure translation layer from authoring state to execution-ready plans.

For lower-level diffusion and UI capabilities, we audit the existing ecosystem below to classify them under:
- **ADOPT**: Use the existing node directly in workflows or runtime adapters.
- **ADAPT**: Adopt the architectural or UI concept while keeping a clean Tegaki interface.
- **REFERENCE**: Keep as an experimental baseline or comparative benchmark.
- **BUILD**: Only build internally when manga-specific domain requirements cannot be met by third parties.

---

## 2. Component Audits

### 2.1 Inspire Pack: Regional Prompt Simple
- **Component**: Regional Prompt Execution & Basic Pipe Plumbing
- **Existing Tool**: `RegionalPromptSimple` (`ComfyUI-Inspire-Pack/inspire/regional_nodes.py`)
- **Current Tegaki Equivalent**: `TegakiMangaImpactRegionalAdapter` (`manga_impact_regional_adapter.py`)
- **Feature Parity**:
  - Encodes positive prompt locally with `ImpactWildcardEncode`.
  - Pairs prompt with `KSamplerAdvancedProvider` and `RegionalPrompt`.
  - Supports `controlnet_in_pipe` to carry control metadata to newly encoded local conditioning.
  - Exposes standard `BASIC_PIPE` input/output.
- **Missing Features**:
  - Does not manage structured manga metadata (Shot Type, Camera Distance, Character ID).
  - Lacks awareness of panel boundary clipping or remainder mask subtractions.
- **Maintenance Risk**: Very low. Maintained actively by ltdrdata; relies on Impact Pack core.
- **Decision**: **ADAPT / ADOPT (Hybrid)**
  - *Rationale*: Tegaki Compiler will output clean masks and prompts into lightweight wrapper workflows that can feed directly into `RegionalPromptSimple` or Impact Pack's `RegionalPrompt`, thinning out Tegaki's internal regional execution logic.

---

### 2.2 Inspire Pack: Color Mask Regional Prompting
- **Component**: Multi-Region Plan via Single Indexed Color Map
- **Existing Tool**: `RegionalPromptColorMask` (`ComfyUI-Inspire-Pack/inspire/regional_nodes.py`)
- **Current Tegaki Equivalent**: `TegakiMangaMaskBuilder` & `layout_aware_mask_builder.py`
- **Feature Parity**:
  - Extracts masks dynamically based on hex color values from an RGB image.
- **Missing Features**:
  - Single color map cannot represent overlapping character regions or mutual interaction zones (one pixel belongs to only one color).
- **Maintenance Risk**: Low.
- **Decision**: **REFERENCE / ADAPT for Panels Only**
  - *Rationale*: Excellent for 1-pixel-1-owner partitions like manga panel layout frames or disjoint SubScenes. Inapplicable to overlapping character bounding boxes or interaction anchors.

---

### 2.3 Advanced-ControlNet: Masked ControlNet Application
- **Component**: Localized ControlNet Conditioning (Pose, Lineart, Depth)
- **Existing Tool**: `ACN_AdvancedControlNetApply_v2` (`ComfyUI-Advanced-ControlNet/adv_control/nodes_main.py`)
- **Current Tegaki Equivalent**: Internal ControlNet propagation logic in `scene_compiler.py` and `controlnet_conditioning_propagation.py`.
- **Feature Parity**:
  - Directly supports `effect_mask` (`mask_optional`).
  - Supports timestep scheduling (`start_percent`, `end_percent`).
  - Directly clips control guidance to character regional masks.
- **Missing Features**:
  - No manga-aware auto-generation of character layout guides (which Tegaki provides via `layout_guide_generator.py`).
- **Maintenance Risk**: Very low. Kosinkadink's Advanced-ControlNet is the gold standard for ControlNet execution in ComfyUI.
- **Decision**: **ADOPT**
  - *Rationale*: Tegaki generates the semantic guide image and effect mask; applying the ControlNet should be delegated entirely to `ACN_AdvancedControlNetApply_v2` or ComfyUI core rather than custom conditioning hacks.

---

### 2.4 Impact Pack: Regional Sampler & MaskEditor
- **Component**: Core In-Diffusion Spatial Conditioning & Freehand Mask Editing
- **Existing Tool**: `RegionalSampler` & `PreviewBridge` / Clipspace MaskEditor (`ComfyUI-Impact-Pack`)
- **Current Tegaki Equivalent**: `TegakiMangaImpactRegionalAdapter`
- **Feature Parity**:
  - Native differential sampling across regional prompts.
  - Interactive mask painter built into ComfyUI canvas.
- **Missing Features**:
  - Native Clipspace mask painter is generic; does not know about manga character identities or panel borders.
- **Maintenance Risk**: Low. Impact Pack is ubiquitous and stable.
- **Decision**: **ADOPT (Sampling) / DEFER (Custom Mask Editor)**
  - *Rationale*: Retain Impact's `RegionalSampler` as the proven reference regional backend. Do not build a custom freehand brush canvas node; when users need manual pixel tweaks, route through standard Clipspace / PreviewBridge.

---

### 2.5 OpenPose Editor Tooling
- **Component**: Manual Skeletal Joint & Pose Editing
- **Existing Tool**: `ComfyUI-OpenPose-Editor` / `openpose_editor`
- **Current Tegaki Equivalent**: `layout_guide_generator.py` (Directional Mannequin Auto Guide)
- **Feature Parity**:
  - 18-joint interactive drag handles for full-body skeletal posing.
- **Missing Features**:
  - Manual joint editing requires tedious user effort per frame; Tegaki's automated mannequin presets (`standing_neutral`, `facing_left`, `facing_right`, `sitting`) provide zero-touch instant guides.
- **Maintenance Risk**: Moderate (multiple unmaintained forks).
- **Decision**: **ADAPT / DEFER**
  - *Rationale*: Tegaki will NOT build a custom canvas joint editor. Tegaki maintains the automated mannequin generator for zero-touch workflows, and establishes a clean `Character Instance ↔ Pose Asset` contract so external OpenPose image assets can be bound directly.

---

### 2.6 EasyUseAnima & Krea2 / Krita AI Diffusion UX
- **Component**: Multi-Region Canvas UI & State Serialization
- **Existing Tool**: `ComfyUI-EasyUseAnima` (Regional Prompt Studio), Krita AI Diffusion
- **Current Tegaki Equivalent**: `TegakiMangaCharacterStagingEditor` & `TegakiMangaPanelLayoutEditor`
- **Feature Parity**:
  - Single consolidated state container with tabs / list view.
  - Hidden serialized JSON state preventing spaghetti wiring across dozens of node sockets.
  - Progressive disclosure of advanced settings.
- **Missing Features**:
  - None are designed for manga page topology or SubScene decomposition.
- **Maintenance Risk**: N/A (conceptual reference).
- **Decision**: **ADAPT**
  - *Rationale*: Adopt the single-state JSON architecture for future `MANGA_AUTHORING_DATA`. Keep node count lean and prevent socket sprawl.

---

## 3. Summary Classification Matrix

| Component Area | Candidate Tool | Tegaki Role | Classification | Action Plan |
| :--- | :--- | :--- | :--- | :--- |
| **Regional Execution** | Inspire `RegionalPromptSimple` | Backend Provider | **ADAPT / ADOPT** | Test parity in WF71; provide clean pipe interface |
| **ControlNet Injection** | Advanced-ControlNet (`ACN_v2`) | Control Application | **ADOPT** | Delegate effect masks & start/end scheduling |
| **Regional Sampling** | Impact `RegionalSampler` | Primary Sampler | **ADOPT** | Maintain as standard reference backend |
| **Mask Painting** | Impact `PreviewBridge` / Clipspace | Manual Mask Adjust | **DEFER** | Avoid building custom freehand canvas brush |
| **Pose Joint Editing** | OpenPose Editor | Manual Pose Asset | **DEFER** | Retain Auto Mannequin; link external pose images |
| **Authoring State UI** | EasyUseAnima / Krita AI | UI Architecture | **ADAPT** | Model `MANGA_AUTHORING_DATA` on single-state JSON |

---

## 4. Architectural Boundary Commitment

```
┌────────────────────────────────────────────────────────┐
│                   TEGAKI CORE DOMAIN                   │
│   CAST Master  •  Character Instance  •  Panel Layout  │
│   Scene & SubScene  •  Staging  •  Semantic Compiler   │
└───────────────────────────┬────────────────────────────┘
                            │ (PAGE_COMPILE_PLAN)
                            ▼
┌────────────────────────────────────────────────────────┐
│             ADOPTED COMFYUI BACKEND LAYER              │
│   Inspire Regional Pipe  •  Impact RegionalSampler     │
│   Advanced-ControlNet Masked Apply  •  OpenPose Assets │
└────────────────────────────────────────────────────────┘
```

This strict separation ensures Tegaki remains maintainable, agile, and aligned with standard ComfyUI ecosystem advances without redundant custom node baggage.
