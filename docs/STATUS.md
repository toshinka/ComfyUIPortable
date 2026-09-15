# ComfyUIPortable — Current Status

Updated: 2026-09-15 JST  
Repository: https://github.com/toshinka/ComfyUIPortable  
Branch: codex/tegaki-shell-manga-play1  
Public baseline: 483f71604cb32c08ab4a5c5b0c4b5888731b8604  
Local HEAD: 483f71604cb32c08ab4a5c5b0c4b5888731b8604  

## New Chat — Read This First

ComfyUIPortable is a standalone portable ComfyUI environment hosting two distinct visual authoring subsystems:
1. **Manga Authoring**: Minimum-Hand / Scene-first manga creation using Illustrious/SDXL, structured around Scene regions, CAST character identities, and Guide conditioning.
2. **MiniMax H3**: Video and still generation studio based on MiniMax H3 models.

The project operates on an **Architecture Lead / Commander vs. Worker Card** model. Autonomous agents execute bounded, non-overlapping Cards with explicit scope, verification gates, and stop conditions.

### Canonical Reading Order
1. [../AGENTS.md](../AGENTS.md) — Operating rules, mode behaviors, and safety boundaries.
2. [STATUS.md](STATUS.md) (this file) — Single source of truth for active state and handoff.
3. Domain routers: [../GITHUB_MANGA.txt](../GITHUB_MANGA.txt) and [../GITHUB_H3.txt](../GITHUB_H3.txt).
4. Relevant domain status (e.g. [docs/manga/STATUS.md](manga/STATUS.md) or [docs/h3/README.md](h3/README.md)).
5. Current explicit Card issued by the commander.
6. Only then inspect specific source files, tests, or runtime contracts.

## Current Operational State

- **Worktree**: Clean on branch `codex/tegaki-shell-manga-play1`.
- **Public Remote**: In sync with local HEAD (`483f71604cb32c08ab4a5c5b0c4b5888731b8604`).
- **Ports (8188, 8189, 8190, 8191)**: Free when idle; managed via supervisor `h3\run_h3.bat`.
- **Runtime Dependencies**: `ComfyUI_IPAdapter_plus` pinned locally at commit `a0f451a5113cf9becb0847b92884cb10cbdec0ef`.
- **Model Directory State**: SDXL IP-Adapter Plus (`ip-adapter-plus_sdxl_vit-h.safetensors`) and CLIP Vision (`CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors`) are present in local untracked `ComfyUI/models/`.
- **Current Active Card**: `PORTABLE-AGENT-ENTRY-AND-HANDOFF1` (Document Architecture & Handoff).

## Manga — Current State

Accepted technical milestones:
- **Scene Composer & Editor**: Horizontalized UI layout with single-click Scene creation, coordinate adjustment, and active layer synchronization (`MANGA-UX-HORIZONTALIZATION-CLEANUP2`).
- **Tag Autocomplete**: Fast Danbooru-style prompt autocomplete powered by a safe local catalog builder (`manga/tools/build_tag_catalog.py`, `MANGA-AUTOCOMPLETE-CATALOG1`).
- **Contextual Autocomplete**: Smart prefix switching between Danbooru tags, `<lora:...>`, and `__wildcard__` completions (`MANGA-CONTEXTUAL-AUTOCOMPLETE1`).
- **CAST Reference Data**: Authoring document contract extended (`reference_asset: "tegaki_manga_references/<name>.<ext>"`), hardened workspace upload/view endpoints (`/api/reference-assets/*`), and inspector thumbnail preview (`MANGA-CAST-REFERENCE-DATA1`).
- **IPAdapter Pinned Runtime**: `ComfyUI_IPAdapter_plus` pinned at commit `a0f451a5113cf9becb0847b92884cb10cbdec0ef`; `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` and `ip-adapter-plus_sdxl_vit-h.safetensors` placed under `ComfyUI/models/` (`REFERENCE_RUNTIME_SETUP1`).
- **Global GPU Proof**: 1-generation GPU proof confirmed Illustrious + IPAdapter Plus SDXL successfully imparts character appearance (hair, face, costume motif) globally (`REFERENCE_GLOBAL_GPU_PROOF1`).
- **Regional Identity Proof**: 1-generation GPU proof tested regional reference isolation using Manga's normalized mask (`TegakiTwoRegionCoreConditioner.mask_A`) into `IPAdapterAdvanced.attn_mask` (`REGIONAL_IDENTITY_PROOF1`).
  - *Setup*: Checkpoint `waiIllustriousSDXL_v170.safetensors`, resolution `1024x768`, seed `20260915`, IPAdapter weight `0.70`, step count `16`, CFG `5.0`.
  - *Reference*: Reused `tegaki_manga_references/ref_c789751db904319d.png` (originating from H3 Manga Tone comparison Route C Illustrious finish).
  - *Geometry*: Left Region A (`x=0.05, y=0.08, w=0.42, h=0.84`) vs. Right Region B (`x=0.53, y=0.08, w=0.42, h=0.84`).
  - *Result*: **B — PARTIAL**. Reference signal visibly concentrated in target Region A (sailor uniform, dark flowing hair, large-eyed face); control Region B remained blonde/casual without material reference bleed. Overlapping figure observed on left; structural architecture is verified **VIABLE**.

## H3 — Current State

Accepted technical milestones:
- **H1A–H1C**: Verified local Native and browser UI generation for Text-to-Video (T2V), Image-to-Video (I2V Start-only, Start+End, End-only), and Frame-Bridged Continuation.
- **H2A Still Studio**: Short temporal packet to selected frame feasibility verified on local GPU.
- **Manga Tone Comparison (Exp1 Retry2)**: 3-route comparison verified Route A (Normal), Route B (Manga Tone), and Route C (Illustrious Finish). Screentone categorized as flat line/tone rather than fine halftone dots.
- **Boundary**: Shared shell integration and H3 Manga unification remain deferred.

## Current Architecture Boundaries

- **Subsystem Isolation**: Manga and H3 share the Portable installation but maintain distinct schemas, workflows, runtime PIDs, and evidence directories. Cross-domain modifications require explicit integration Cards.
- **Manga Semantic Separation**:
  - *Scene / Region*: Spatial bounding boxes for prompt text conditioning.
  - *CAST / Reference*: Visual character appearance via IP-Adapter.
  - *Guide / ControlNet*: Structural lineart/pose guidance.
  - *character_instance*: Placement of a CAST member inside a Scene.
- **Runtime Lifecycle**: Supervisor scripts own port listeners. Cards must shut down spawned processes at completion unless explicitly authorized to keep running.

## Current Priority

Stabilize repository-level agent orientation and handoff (`PORTABLE-AGENT-ENTRY-AND-HANDOFF1`). Establish clear boundaries between stable rules (`AGENTS.md`) and operational status (`docs/STATUS.md`) before undertaking subsequent character reference conditioning or UI horizontalization cards.

## Evidence Locations

### Tracked Evidence & Indices
- [docs/ui/LOCAL_REVIEW_ARTIFACTS.md](ui/LOCAL_REVIEW_ARTIFACTS.md) — Index of local visual review artifacts.
- [docs/manga/reports/](manga/reports/) — Historical Manga milestone and closure reports.
- [docs/h3/](h3/) — H3 roadmap, research, and verification reports.

### Local Uncommitted Review Artifacts
*(Marked as LOCAL / GITIGNORED / MAY NOT EXIST ON OTHER CLONES)*
- `output/ui-review/2026-09-15/MANGA-UX-CLEANUP2/`
  - Manifest: `REVIEW_MANIFEST.txt`
  - Artifacts: `H3_VIDEO_BASELINE.png`, `MANGA_GENERATE.png`, `MANGA_AUTHORING.png`
- `output/experiments/h3-manga-tone/2026-09-15/EXP1_RETRY2/`
  - Report: `H3_MANGA_TONE_COMPARISON_EXP1_RETRY2_REPORT.md`
  - Artifacts: `comparison/route_A_h3_normal.png`, `comparison/route_B_h3_manga_tone.png`, `comparison/route_C_illustrious_finish.png`
- `output/runtime-deps/manga-reference/REFERENCE_RUNTIME_SETUP1_MANIFEST.txt` — IPAdapter & CLIP Vision asset manifest.
- `output/experiments/manga-reference/2026-09-15/REFERENCE_GLOBAL_GPU_PROOF1/`
  - Report: `REFERENCE_GLOBAL_GPU_PROOF1_REPORT.md`
  - Artifacts: `comparison/source_reference.png`, `comparison/global_reference_result.png`
- `output/experiments/manga-reference/2026-09-15/REGIONAL_IDENTITY_PROOF1/`
  - Report: `REGIONAL_IDENTITY_PROOF1_REPORT.md`
  - Artifacts: `comparison/source_reference.png`, `comparison/previous_global_result.png`, `comparison/regional_identity_result.png`

## Active Card / Last Completed Card

- **Active Card**: `PORTABLE-AGENT-ENTRY-AND-HANDOFF1`
- **Last Completed GPU Card**: `MANGA-REGIONAL-IDENTITY-PROOF1` (Outcome: Partial regional isolation, architecture viable).

## Do Not Auto-Start

A fresh agent or new chat must **not** begin a new implementation Card automatically from this status document. The architecture lead / commander issues the next bounded Card.
