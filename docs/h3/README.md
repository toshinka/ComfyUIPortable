# MiniMax H3 Document Hub

更新: 2026-09-08 JST

このページは `ComfyUIPortable` における MiniMax H3 の調査・計画・報告・
将来の実装棚とReference Implementation evidenceを一か所から辿るための
document hub です。現在は **H0.1 / model isolation and generation smoke** であり、
H3 GUI、production generation backend、custom node、workflowの実装は開始していません。

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
| `docs/h3/plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md` | TEGAKI visual / brand language | CURRENT DESIGN SUMMARY | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md` |
| `docs/h3/plans/H3_ASTRA_UI_REVIEW_HANDOFF.md` | Astra UI review handoff index | CURRENT HANDOFF INDEX | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_ASTRA_UI_REVIEW_HANDOFF.md` |
| `docs/h3/reports/H3_ASTRA_UI_REVIEW_RESULT.md` | Bounded Astra UI review evidence | CURRENT REVIEW EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_ASTRA_UI_REVIEW_RESULT.md` |
| `docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md` | This groundwork report | CURRENT REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md` |
| `docs/h3/reports/H3_GROUNDWORK_CLOSEOUT_REPORT.md` | Groundwork closeout and publication distinction | CURRENT CLOSEOUT REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_GROUNDWORK_CLOSEOUT_REPORT.md` |
| `docs/h3/reports/H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md` | Astra preparation semantic alignment report | CURRENT PREP REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md` |
| `docs/h3/evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md` | Candidate evidence index | CURRENT H0.1 GATE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md` |
| `docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md` | Official first-wave model provenance, license, size, and hash ledger | CURRENT H0.1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md` |
| `docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md` | Fixed-task generation comparison and H1 ingredient disposition | CURRENT H0.1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md` |
| `docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md` | Historical H0 startup/source evaluation | HISTORICAL H0 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md` |

## External master roadmap

The current local Rev.3 master is:

D:/GitHub/tegaki/MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The preserved source remains:

D:/GitHub/tegaki/MiniMax H3/Archive/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The two files are byte-identical. The Archive source was not deleted, moved,
renamed, merged, or edited.

Expected GitHub URL after Owner push:

https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The local origin/main baseline did not contain the root path before this
closeout. External GitHub fetch was unavailable in this run, so publication
must be verified after Owner push; the URL is not claimed as already live.

The current `GITHUB_MANGA.txt` is the canonical entry for the Manga Authoring
line. `GITHUB_ComfyUI.txt` is a thin compatibility router to the separate Manga
and H3 entries; it does not merge either subsystem's runtime semantics.

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
- [H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md](plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md)
  — Futaba heritage palette as TEGAKI DNA, modern production UI guardrails,
  benchmark roles, and anti-goals.
- [H3_ASTRA_UI_REVIEW_HANDOFF.md](plans/H3_ASTRA_UI_REVIEW_HANDOFF.md) — read
  order and bounded output contract for Astra's separate UI review Chat.

No Astra implementation instruction is created here. The bounded Astra review is
now complete as a separate review pass; its evidence is recorded in
[H3_ASTRA_UI_REVIEW_RESULT.md](reports/H3_ASTRA_UI_REVIEW_RESULT.md). No
implementation follows from that result automatically.

## Reports

- [H3_GROUNDWORK_INITIALIZATION_REPORT.md](reports/H3_GROUNDWORK_INITIALIZATION_REPORT.md)
  — added files, boundaries, observations, review links, and the next gate.
- [H3_GROUNDWORK_CLOSEOUT_REPORT.md](reports/H3_GROUNDWORK_CLOSEOUT_REPORT.md)
  — current Rev.3 path, visual language, Astra handoff, local/public state
  distinction, and closeout gate.
- [H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md](reports/H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md)
  — correction of Cognitive Level / Cognitive Lens roles, H3 Video review scope,
  and Illustrious Manga boundary.
- [H3_ASTRA_UI_REVIEW_RESULT.md](reports/H3_ASTRA_UI_REVIEW_RESULT.md) — bounded
  Astra review evidence: KEEP / ADJUST / DEFER / VALIDATE and the next evaluation gate.
- [H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md](reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md)
  — H0.1 model-backed generation comparison, memory/error record, and H1 ingredient disposition.
- [H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md](reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md)
  — historical H0 Native, H3 Easy, onigirikiller, and AntaresAlice startup/source evaluation.

## Evidence

- [H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md](evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md)
  — H0/H0.1 split, source commit, install/runtime status, blockers, and candidate
  evidence links.
- [H3_MODEL_ACQUISITION_MANIFEST.md](evidence/H3_MODEL_ACQUISITION_MANIFEST.md)
  — official model filenames, source revision, license restrictions, sizes, SHA-256,
  local isolation, and deferred assets.
- [Reference implementation evidence](evidence/reference-implementations/) — dated
  startup history plus H0.1 generation README, manifest, actual local screenshots,
  frame triplets, and contact sheets where generation succeeded.
- Production H3 output is isolated at `output/h3/video/`, with `debug/` and `tests/`
  alongside it. Existing `output/` content and Manga output are outside this slice.

The historical groundwork reports remain historical records. The current gate is the
H0.1 model manifest, evidence index, and generation report above; it does not imply
that any candidate is adopted.

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
2. Read the current Rev.3 master and confirm the Archive source is preserved.
3. Read the landscape and inventory together; do not treat a candidate as
   adopted because it appears in either document.
4. Check licenses and model provenance before any code reuse or installation.
5. Confirm that H3 Video remains first, H3 Still is an acceptance capability,
   and H3 Manga remains later research.
6. Review the visual language and Astra handoff as review boundaries, not
   implementation instructions.
7. Review the empty directory boundary and confirm that existing Illustrious
   files were not changed.
8. Read the H0.1 model manifest and generation evidence; verify that generation,
   startup, blocked, owner-action-required, and not-tested states are not conflated.
9. Stop at the Web GPT H1 ingredient review gate; do not infer adoption or Owner
   acceptance from a local generation result.

## Evidence vocabulary

- `OBSERVED`: public repository/document observation only.
- `VERIFIED LOCAL STARTUP`: a reproducible local startup/API/static result.
- `VERIFIED LOCAL GENERATION`: a reproducible local output with hash and frame
  evidence; it does not imply quality or Owner acceptance.
- `BLOCKED`: a concrete dependency, model, or scope boundary stopped the relevant
  runtime path.
- `NOT TESTED`: the relevant path was not exercised and must not be inferred.
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
