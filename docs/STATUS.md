# ComfyUIPortable — Current Status

Updated: 2026-09-15 JST  
Repository: https://github.com/toshinka/ComfyUIPortable  
Branch: codex/tegaki-shell-manga-play1  
Public baseline: 3b98a499e1e652254644064ecd3ac0513000f8fb
Local HEAD: 3b98a499e1e652254644064ecd3ac0513000f8fb

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
- **Public Remote**: In sync with local HEAD (`3b98a499e1e652254644064ecd3ac0513000f8fb`).
- **Ports (8188, 8189, 8190, 8191)**: Free when idle; managed via supervisor `h3\run_h3.bat`.
- **Runtime Dependencies**: `ComfyUI_IPAdapter_plus` pinned locally at commit `a0f451a5113cf9becb0847b92884cb10cbdec0ef`.
- **Model Directory State**: SDXL IP-Adapter Plus (`ip-adapter-plus_sdxl_vit-h.safetensors`) and CLIP Vision (`CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors`) are present in local untracked `ComfyUI/models/`.
- **Current Active Card**: NONE.

## Manga — Current State

Accepted technical milestones:
- **Scene Composer & Editor**: Horizontalized UI layout with single-click Scene creation, coordinate adjustment, and active layer synchronization (`MANGA-UX-HORIZONTALIZATION-CLEANUP2`).
- **Tag Autocomplete**: Fast Danbooru-style prompt autocomplete powered by a safe local catalog builder (`manga/tools/build_tag_catalog.py`, `MANGA-AUTOCOMPLETE-CATALOG1`).
- **Contextual Autocomplete**: Smart prefix switching between Danbooru tags, `<lora:...>`, and `__wildcard__` completions (`MANGA-CONTEXTUAL-AUTOCOMPLETE1`).
- **CAST Reference Data**: Authoring document contract extended (`reference_asset: "tegaki_manga_references/<name>.<ext>"`), hardened workspace upload/view endpoints (`/api/reference-assets/*`), and inspector thumbnail preview (`MANGA-CAST-REFERENCE-DATA1`).
- **IPAdapter Pinned Runtime**: `ComfyUI_IPAdapter_plus` pinned at commit `a0f451a5113cf9becb0847b92884cb10cbdec0ef`; `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` and `ip-adapter-plus_sdxl_vit-h.safetensors` placed under `ComfyUI/models/` (`REFERENCE_RUNTIME_SETUP1`).
- **Global GPU Proof**: 1-generation GPU proof confirmed Illustrious + IPAdapter Plus SDXL successfully imparts character appearance (hair, face, costume motif) globally (`REFERENCE_GLOBAL_GPU_PROOF1`).
- **Regional Identity Proof**: 1-generation GPU proof tested regional reference isolation using Manga's normalized mask (`TegakiTwoRegionCoreConditioner.mask_A`) into `IPAdapterAdvanced.attn_mask` (`REGIONAL_IDENTITY_PROOF1`, portable code baseline `483f71604cb32c08ab4a5c5b0c4b5888731b8604`).
  - *Status*: **ACCEPTED TECHNICAL ARCHITECTURE PROOF** (Commander accepted).
  - *Technical Result*: Illustrious + IPAdapter regional path PASS; mask path `TegakiTwoRegionCoreConditioner.mask_A` -> `IPAdapterAdvanced.attn_mask`; 1 GPU generation, 1 `/prompt`, peak dedicated GPU memory 11,687 MiB, product source modification NONE.
  - *Regional Isolation*: **B — PARTIAL** (reference signal visibly concentrated in target Region A; control Region B remained blonde/casual without material reference bleed; overlapping figure observed on left; identity is NOT solved and isolation is not clear/final).
  - *Reference Appearance*: **EXPERIMENTAL** (useful appearance carryover without production-quality claim).
  - *Regional Reference Architecture*: **VIABLE** (proves spatial reference conditioning feasibility via Manga's existing mask primitives).

- **Reference product path**: Public accepted commit `17dabbec31d710180deb45d7fe5f8e42cf6b9927` records one CAST, one `character_instance`, and one `reference_asset` through the regional IPAdapter path. The existing character area feeds the regional `attn_mask`; the real product route and SaveImage output passed, with visible reference effect. Identity solved remains **NO**; multi-reference and multi-referenced-character remain unsupported, and ControlNet coexistence is not yet verified.
- **Manga runtime VRAM policy**: Accepted in commit `3b98a499e1e652254644064ecd3ac0513000f8fb`. Manga alone launches `--vram-headroom 2.0`; H3 is unaffected. The existing DynamicVRAM/AIMDO mechanism remains in use. The accepted Reference product passed with observed peak `10222 MiB`, no obvious host thrash, and normal product output authority.
- **Optimization branch**: **CLOSED for now**. Reference pre-encoding and `VAEDecodeTiled` were low-value at 768x1024 and were not productized. Current attention remains PyTorch SDPA; no safe installed alternative was selected. The `--vram-headroom 2.0` Manga policy is the accepted runtime choice.

## H3 — Current State

Accepted technical milestones:
- **H1A–H1C**: Verified local Native and browser UI generation for Text-to-Video (T2V), Image-to-Video (I2V Start-only, Start+End, End-only), and Frame-Bridged Continuation.
- **H2A Still Studio**: Short temporal packet to selected frame feasibility verified on local GPU.
- **Manga Tone Comparison (Exp1 Retry2)**: 3-route technical experiment passed across Route A (Normal), Route B (Manga Tone), and Route C (Illustrious Finish). manga-like line / flat-tone rendering observed; clear regular screentone-dot evidence NOT established.
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

Return to Manga controllability / production-flow planning. Immediate design space is Scene / Region, CAST / Reference, Guide / ControlNet, and LoRA. Keep H3 separate.

## UI Planning State

- **TEGAKI Production UI pre-Astra specification phase**: **COMPLETE**.
- **Authoritative UI design documents**: `docs/ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md`, `docs/ui/TEGAKI_CREATE_WORKSPACE_MODEL.md`, `docs/ui/TEGAKI_ASTRA_UI_REVIEW_BRIEF.md`, and `docs/ui/TEGAKI_UI_COMPONENT_CONTRACTS.md`.
- **Current design state**: Manga/H3 Production sibling cognitive model, Create workspace state flow, GLANCE/FOCUS principles, truthful `GenerationStatus`, component behavioral contracts, and the Astra review contract are defined.
- **Implementation state**: major Create redesign **NOT implemented**; `PreviewFocus` **NOT implemented**; `MediaPreviewShell` redesign **NOT implemented**; `CompactContext` **NOT implemented**.
- **Prototype-safe contracts identified**: `GenerationStatus`, `ProgressProjection / ProgressOverlay`, and `AttachmentCard` grammar. **No prototype is currently authorized.**
- **Next UI action**: bounded Astra review of the current rendered Manga/H3 UI against the prepared specifications. Astra review performed: **NO**.

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

- **Active Card**: NONE
- **Last Completed Operational Card**: `MANGA-VRAM-HEADROOM-CLOSEOUT1` (Manga reference and runtime policy status recorded; optimization branch closed).
- **Last Completed GPU Card**: `MANGA-VRAM-HEADROOM-PRODUCT1` (Manga-only `--vram-headroom 2.0`; accepted Reference product route, SaveImage, and normal output authority; observed peak 10,222 MiB; no obvious host thrash; identity solved remains NO).

## Do Not Auto-Start

A fresh agent or new chat must **not** begin a new implementation Card automatically from this status document. The architecture lead / commander issues the next bounded Card.
