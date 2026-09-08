# MiniMax H3 Document Hub

更新: 2026-09-08 JST

このページは `ComfyUIPortable` における MiniMax H3 の調査・計画・報告・
将来の実装棚を一か所から辿るための document hub です。現在は
**Groundwork / Pre-H0** であり、H3 GUI、generation backend、custom node、
model、workflowの実装は開始していません。

この文書は Web GPT / Astra / LUNA が新しいChatから同じ状態を復元するための
入口です。候補OSSの採用決定やソースコードの再配布を意味しません。

## Canonical files

| Path | Role | Status | GitHub URL after Owner push |
|---|---|---|---|
| `GITHUB_H3.txt` | H3 External AI Entry | CURRENT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/GITHUB_H3.txt` |
| `docs/h3/README.md` | H3 document hub | CURRENT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/README.md` |
| `docs/h3/research/H3_CURRENT_LANDSCAPE.md` | Current candidate landscape summary | CURRENT RESEARCH | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/research/H3_CURRENT_LANDSCAPE.md` |
| `docs/h3/references/H3_REFERENCE_INVENTORY.md` | Candidate and provenance inventory | CURRENT RESEARCH | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/references/H3_REFERENCE_INVENTORY.md` |
| `docs/h3/plans/H3_GUI_DESIGN_PRINCIPLES.md` | Rev.3 GUI principle summary | CURRENT DESIGN SUMMARY | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_GUI_DESIGN_PRINCIPLES.md` |
| `docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md` | This groundwork report | CURRENT REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md` |

## External master roadmap

The local Rev.3 file observed during this pass is:

```text
D:\GitHub\tegaki\MiniMax H3\Archive\H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md
```

The path requested by the original task, without `Archive`, was not found in the
live checkout. The file was not moved or renamed. A public GitHub URL for the
Rev.3 file was not confirmed, so none is supplied here. This is an unresolved
path/publication observation, not a reason to change the existing H3 documents.

The current `GITHUB_ComfyUI.txt` remains the canonical entry for the existing
Illustrious Manga line and is intentionally not routed through this hub.

## Research

- [H3_CURRENT_LANDSCAPE.md](research/H3_CURRENT_LANDSCAPE.md) — summarized
  Video, Still, low-VRAM, and fast-path findings; separates observation from
  adoption.
- [H3_REFERENCE_INVENTORY.md](references/H3_REFERENCE_INVENTORY.md) — repository,
  license/provenance, role, status, and checked revision when available.

## Plans

- [H3_GUI_DESIGN_PRINCIPLES.md](plans/H3_GUI_DESIGN_PRINCIPLES.md) — short
  summary of Rev.3's cognitive-level, cognitive-lens, progressive-disclosure,
  and "mountain" principles.

No Astra implementation instruction is created here. The later Astra UI review
must be a separate, bounded task after Web GPT reviews this groundwork.

## Reports

- [H3_GROUNDWORK_INITIALIZATION_REPORT.md](reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md)
  — added files, boundaries, observations, review links, and the next gate.

## Empty implementation shelves

These paths exist only to make the future H3 boundary visible:

```text
h3/app/
h3/adapters/
h3/config/
h3/tests/
workflows/h3/
```

They contain no implementation. Do not infer a schema or backend contract from
their names.

## Review recipe

1. Start at `GITHUB_H3.txt`.
2. Read the landscape and inventory together; do not treat a candidate as
   adopted because it appears in either document.
3. Check licenses and model provenance before any code reuse or installation.
4. Confirm that H3 Video remains first, H3 Still is an acceptance capability,
   and H3 Manga remains later research.
5. Review the empty directory boundary and confirm that existing Illustrious
   files were not changed.
6. Stop at the Web GPT review gate.

## Evidence vocabulary

- `OBSERVED`: public repository/document observation only.
- `INSPECT`: keep as a review target; no adoption decision.
- `ADOPT-CANDIDATE`: possible future design or code candidate, pending a pinned
  source and license audit.
- `DEFER`: useful later, not a current H0/H1 input.
- `RESEARCH-LATER`: candidate family or runtime whose evidence is insufficient
  for a current decision.
- `VERIFIED`: reserved for a reproducible local/runtime result; no H3 item in
  this groundwork is marked `VERIFIED`.

## Scope boundary

This hub does not replace the existing ComfyUIPortable STATUS, planning SSOT,
reports, or workflow index. It adds an H3-only path beside them. No existing
Illustrious file, workflow, runtime, or canonical entry was edited for this
groundwork.
