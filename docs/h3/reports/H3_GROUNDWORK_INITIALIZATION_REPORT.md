# H3 Groundwork Initialization Report

更新: 2026-09-08 JST
Stage: Groundwork / Pre-H0
Ready for Web GPT review: YES

## 1. Summary

MiniMax H3を安全に開始するための地均しを行った。H3専用のExternal AI Entry、
document hub、research summary、reference inventory、GUI design principles、
groundwork report、および将来の実装棚を `ComfyUIPortable` 内へ追加した。

H3 GUI、generation backend、custom node、model、workflow、schema、frontend
frameworkは実装していない。候補OSSもclone / install / copyしていない。

## 2. Files added

- `GITHUB_H3.txt`
- `docs/h3/README.md`
- `docs/h3/research/H3_CURRENT_LANDSCAPE.md`
- `docs/h3/references/H3_REFERENCE_INVENTORY.md`
- `docs/h3/plans/H3_GUI_DESIGN_PRINCIPLES.md`
- `docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md`
- `h3/app/.gitkeep`
- `h3/adapters/.gitkeep`
- `h3/config/.gitkeep`
- `h3/tests/.gitkeep`
- `workflows/h3/.gitkeep`

## 3. Added directories

```text
docs/h3/
docs/h3/plans/
docs/h3/references/
docs/h3/research/
docs/h3/reports/
h3/
h3/app/
h3/adapters/
h3/config/
h3/tests/
workflows/h3/
```

## 4. Existing files modified

None in `ComfyUIPortable` existing files.

The following pre-existing worktree state was observed and deliberately left
untouched:

- `ComfyUIPortable/GITHUB.TXT` is already deleted in the worktree.
- `tegaki_work/styles/main.css` is already modified.
- Several untracked files exist under the sibling `MiniMax H3` area, including
  research material and H3 roadmap snapshots.

Those changes are not part of this report and were not cleaned up or mixed into
the H3 groundwork.

## 5. Illustrious Boundary Check

PASS for this slice:

- `GITHUB_ComfyUI.txt` was not changed.
- `docs/STATUS.md` was not changed.
- Existing `docs/plans/` was not changed.
- Existing `docs/reports/` was not changed.
- Existing `workflows/` was not changed; only `workflows/h3/` was added.
- No existing file was moved, renamed, deleted, or archived by this task.
- No Illustrious runtime or workflow was changed.
- No `GITHUB_MANGA.txt` or router was added.

## 6. GitHub review links

These are expected links after the Owner pushes the relevant commit to `main`.
They are not claimed as published from this local worktree.

- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/GITHUB_H3.txt`
- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/README.md`
- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/references/H3_REFERENCE_INVENTORY.md`
- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/research/H3_CURRENT_LANDSCAPE.md`
- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_GUI_DESIGN_PRINCIPLES.md`
- `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md`

The local Rev.3 roadmap was found under an `Archive` path outside this project.
Its public GitHub URL was not confirmed and is intentionally not fabricated.

## 7. Current H3 tree

```text
ComfyUIPortable/
├─ GITHUB_H3.txt
├─ h3/
│  ├─ app/.gitkeep
│  ├─ adapters/.gitkeep
│  ├─ config/.gitkeep
│  └─ tests/.gitkeep
├─ docs/
│  └─ h3/
│     ├─ README.md
│     ├─ plans/
│     │  └─ H3_GUI_DESIGN_PRINCIPLES.md
│     ├─ references/
│     │  └─ H3_REFERENCE_INVENTORY.md
│     ├─ research/
│     │  └─ H3_CURRENT_LANDSCAPE.md
│     └─ reports/
│        └─ H3_GROUNDWORK_INITIALIZATION_REPORT.md
└─ workflows/
   └─ h3/.gitkeep
```

## 8. Research incorporated

- Rev.3 order was preserved: H3 VIDEO → Still acceptance capability → Studio /
  Storyboard / Previz → Illustrious Manga completion → UI integration → H3 MANGA
  research.
- Video WebUI, Easy workflow, Director, Studio, Still, low-VRAM, and fast-path
  candidates were summarized without copying source text.
- Candidate license/provenance and checked revisions were recorded where public
  pages made them easy to confirm.
- Base Quality / Stable Fast / Experimental was recorded as a planning boundary.
- The 7-day normal Fast Path and approximately 14-day new-runtime observation
  gate was recorded.
- ordered references, semantic roles, source anchor, source fidelity, Still
  metadata, and rough/layout → Still → Illustrious finish were recorded as
  research concepts.
- H3-only manga, monochrome manga, screentone, hatching, page consistency, and
  production-grade H3 Manga remain Research Later.

## 9. Observations only

- `docs/TECHNICAL.md` and `docs/README.md` are absent in this live
  ComfyUIPortable checkout. `docs/DOCUMENT_REGISTER.md` already records the
  TECHNICAL absence; this groundwork did not create a replacement authority
  document.
- The task-requested Rev.3 path without `Archive` was not found. The Rev.3 file
  that was read exists under `D:\GitHub\tegaki\MiniMax H3\Archive\`. No path
  correction was attempted.
- The sibling `MiniMax H3` research note dated 2026-09-08 was observed but not
  edited.
- The existing H3 root plan and its snapshots remain outside this project; no
  old document was deleted or renamed.

## 10. Unresolved decisions

- Web GPT must review the hub, landscape, inventory, and the local-roadmap path
  mismatch before H0/H1 implementation.
- Owner must decide whether and where the Rev.3 roadmap is published before a
  canonical public URL is added.
- Any selective OSS reuse requires a pinned full SHA, dependency audit,
  license/provenance decision, and a separate implementation card.
- H3 model terms, applicable territory, Qwen terms, third-party nodes, and
  redistribution boundaries remain unresolved.
- RTX 4070 12GB / 64GB RAM baseline, low-VRAM behavior, quality, and fast-path
  stability have not been runtime verified.
- Astra UI review is intentionally later and is not created by this task.

## 11. Next gate

```text
Web GPT review.
Do not start H3 implementation until the review is complete.
```

No H3 Phase H0/H1 implementation was started automatically.
