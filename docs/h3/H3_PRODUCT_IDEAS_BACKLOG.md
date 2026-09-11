# H3 Product Ideas & Backlog

Status: `LIVING BACKLOG / SSOT`  
Updated: `2026-09-11 JST`  
Authority: `H3 Architecture (SOL/WebGPT) & Owner Decisions`  
Implementation Authorization: `NONE (This backlog document is not an automatic implementation grant)`

---

## 1. Overview & Policy

This backlog tracks user experience refinements, generation pipeline enhancements, and architectural directions for the TEGAKI H3 (MiniMax video/still/prep) track.

### Guiding Principles
- **Truthful Status & Vocabulary**: No fake ETA, no fabricated percentages, no invented states. activeJob != previewJob.
- **Stage is Protagonist**: The generation preview remains central. Stage actions must be compact, intuitive, and non-dominant.
- **Earn Every Slope (Cognitive Level)**: Do not turn simple generation into a bloated NLE video editor. Introduce advanced surfaces progressively when justified by real workflows.
- **Strict Bounded Execution**: Items listed in this backlog require explicit Card authorization before implementation begins.

---

## 2. Categorized Backlog

### NOW (Current Card: H3-G1A)
- **Stage Action Area Compression**:
  - Unify Generate and Cancel into a single primary action slot.
  - Idle / Ready state: One compact Generate button.
  - Active Generation state: Generate is replaced by Cancel in the exact same slot; never show both side-by-side.
  - Compact one-line Stage-top status row to preserve vertical Preview area.
  - Rely on Preview overlay for live elapsed time (`Generating · 126.0s`).
  - Errors remain prominent, truthful, and non-truncated.
- **Media Input & Progress Feasibility Audits**:
  - Sampler-only vs total workflow progress via ComfyUI WebSocket.
  - Aspect ratio distortion root-cause analysis across Standard Start/End and Ref2VA Picture inputs.
  - Reference video trimming and start-offset feasibility using Native core nodes.

---

### NEAR (Next Prioritized Implementations)
- **Truthful Sampler Progress Percentage**:
  - Surface real step counts from ComfyUI's internal `ProgressBar` / WebSocket `progress` events (e.g., `Sampling 7 / 20` or `Sampling 35%`).
  - Label specifically as sampler progress—never misrepresent as total-generation percentage.
  - Expose via `Job` metadata in H3 Skin polling without breaking HTTP polling resilience.
- **Aspect-Safe Image Reference Preparation**:
  - Standard Start Frame aspect-safe center cover-crop: `IMPLEMENTED / VERIFIED SOURCE-LOGIC` (Card H3-G1C1).
    - Materializes ComfyUI's core `ImageScale` (`upscale_method="lanczos"`, `crop="center"`, `width=W`, `height=H`) between `LoadImage` and `MiniMaxH3ImageToVideo.first_frame`.
    - Eliminates anamorphic squashing/stretching for Standard Video Start Frame; center crops outer edges if aspect differs from output resolution.
  - Still Source Image aspect-safe framing: `NEAR / NOT IMPLEMENTED` (Deferred).
  - Contain/pad (letterbox/pillarbox) mode selector: `NEAR / NOT IMPLEMENTED` (Deferred).
  - Dedicated Prep/Edit interactive framing surface: `LATER / NOT IMPLEMENTED` (Deferred).
- **Reference Video Trimming (First N Seconds)**:
  - First-5s Native trim: `IMPLEMENTED / VERIFIED SOURCE-LOGIC` (Card H3-G1B1).
  - Materializes ComfyUI's core `VideoSlice` (`Trim Video`) node (`start_time: 0.0`, `duration: 5.0`, `strict_duration: false`) before frame extraction to avoid memory bloat and excessive frame extraction.
- **Reference Video Start Offset (IN Time)**:
  - Add a single `start_time` (IN point) control in the Reference Video slot (`NEAR / NOT IMPLEMENTED`).
  - Materialize `VideoSlice(start_time=T, duration=5.0)` to consume seconds $T \to T+5$.
  - Avoid requiring an explicit OUT point while output duration is fixed.

---

### LATER (Future Studio & Iteration Features)
- **Stage-Bottom Shot Strip / Compact Timeline (Candidate A)**:
  - Place a horizontal take/shot strip strictly below the left Stage column.
  - Preserve the two-column Wide layout (Stage left, Inspector right).
  - Provide shot sequencing and take selection without expanding into a full-width NLE.
- **Inspector Create / Edit Mode Separation**:
  - Split Inspector into `[ Create ]` and `[ Edit ]` tabs only when substantive editing controls (e.g. shot retiming, continuation tuning, per-shot overrides) exist.
  - Avoid empty placeholder tabs.
- **Dedicated Image Preparation Surface**:
  - Full image cropping, aspect conversion, and reference retouching within TEGAKI before handoff to H3 generation.

---

### DEFERRED / EXTERNAL DEPENDENCY
- **Cross-Track Asset Handoff (H3 <-> Illustrious Manga)**:
  - Shared asset promotion and bidirectional handoff between H3 video/still and Manga panel creation.
  - Blocked pending common supervisor and cross-track integration freeze.
- **Unified TEGAKI Shell (Top-Level Tabs)**:
  - Common application wrapper hosting Video, Still, and Manga workspaces.
  - Implementation deferred to dedicated cross-track integration phase.
- **Dedicated Audio Track & Reference System**:
  - Lip-sync, audio mixing, soundtrack assignment, and voice timeline tracks remain disconnected and deferred.
- **Full Video Editing & Multi-Track NLE (Candidate B)**:
  - Complex multi-track transitions, cutting room, and timeline editing are deferred. The standalone TEGAKI editor may own rich creative manipulation.
- **Runtime Process Supervisor**:
  - Unified process control, automated backend profile switching, and shared-port supervision.

---

## 3. Backlog Status Register

| Item ID | Description | Category | Feasibility Status | Target Card |
|---|---|---|---|---|
| `ACT-01` | Stage action compression & single-slot Cancel swap | NOW | Feasible & Safe | `H3-G1A` |
| `PRG-01` | Truthful sampler progress display (`Sampling X%`) | NEAR | Feasible with limit (WS / sampler-only) | Next Card |
| `MED-01` | Aspect-safe Start Frame center cover-crop | NEAR | IMPLEMENTED / VERIFIED SOURCE-LOGIC | `H3-G1C1` |
| `MED-02` | Still Source & contain/pad framing policies | NEAR | Deferred / Not Implemented | Next Card |
| `VID-01` | Reference video first 5s auto-trim | NEAR | IMPLEMENTED / VERIFIED SOURCE-LOGIC | `H3-G1B1` |
| `VID-02` | Reference video start offset (IN time $T$) | NEAR | NOT IMPLEMENTED | Next Card |
| `STU-01` | Compact Stage Shot strip (Candidate A) | LATER | Architectural direction accepted | Future Studio |
| `STU-02` | Inspector Create/Edit split | LATER | Deferred until edit controls exist | Future Studio |
| `EXT-01` | Cross-track Manga/H3 handoff | DEFERRED | External dependency | Cross-Track |
| `EXT-02` | Shared TEGAKI Shell | DEFERRED | External dependency | Cross-Track |
| `EXT-03` | Dedicated audio references & mixer | DEFERRED | Deferred by policy | Future Audio |
