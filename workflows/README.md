# Tegaki Manga Workflows Directory

This directory contains the ComfyUI workflows for Tegaki Manga Authoring and Generation.

## Canonical Active Workflow

- **`MINIMUM_HAND_MANGA_DRAFT.json`**
  - **Status**: Active (Phase 3M-2B / M2B Canonical)
  - **Purpose**: Minimum-Hand Manga Draft pipeline. Provides interactive scene rectangle authoring, recurrent CAST Master registration, character rough region staging, free-text acting prompts, and seed control without requiring manual masks or ControlNet.
  - **SSOT**: Powered by `TEGAKI_AUTHORING_DOCUMENT` v1.0.0 backed by `TegakiMinimumHandSceneEditor` (displayed as `Tegaki Minimum-Hand Manga Authoring (Draft)`) and `TegakiMangaConditioningBuilder`.
  - **Architecture Boundary**:
    - **User Workspace**: `TegakiMinimumHandSceneEditor` + `PreviewImage` (region layout preview) + `SaveImage` (draft output).
    - **Internal Pipeline**: `CheckpointLoaderSimple` -> `TegakiMangaConditioningBuilder` -> `KSampler` -> `VAEDecode`.

---

## Historical Archive (`Archive/`)

All workflows within the `Archive/` directory are preserved historical research, exploration, and oracle verification workflows from earlier iterations (e.g. 01–50+ experiment series).

- **Policy**:
  - `Archive/` is **read-only historical provenance**.
  - Do not edit, delete, or move files out of `Archive/` to the root directory without explicit user instruction.
  - All new production and milestone workflows are authored directly in the root `workflows/` directory.
