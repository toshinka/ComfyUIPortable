# MiniMax H3 Document Hub

更新: 2026-09-09 JST

このページは `ComfyUIPortable` における MiniMax H3 の調査・計画・報告・
将来の実装棚とReference Implementation evidenceを一か所から辿るための
document hub です。現在は **H1C / Frame-Bridged Continuation** であり、
H1B.1 / Start + End Frame and Native FL2VA vertical slice + UX P0/P1/P2
Fixes は履歴と回帰対象として保持します。H0/H0.1/H1A/H1B の model
isolation、generation smoke、T2V skin、single-Start-Frame I2V も保持します。
H1A implementation commit `925596b9d7fbd731290fe9869ea34a0006249130` is
published on `main`. H1B, H1B.1, and the H1B.1 UX P0/P1/P2 fixes are implemented and
locally/browser verified within their recorded bounds; Owner acceptance remains
pending. H1C evidence/report/canonical docs are recorded in commit `4df2f2a5f29957a9f4ba429ddd8796d13de5de3b`
on local `main`; no push was performed.

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
| `docs/h3/evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md` | Candidate evidence index | HISTORICAL H0.1 GATE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/H3_REFERENCE_IMPLEMENTATION_EVALUATION_INDEX.md` |
| `docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md` | Official first-wave model provenance, license, size, and hash ledger | HISTORICAL H0.1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md` |
| `docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md` | Fixed-task generation comparison and H1 ingredient disposition | HISTORICAL H0.1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md` |
| `docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md` | Historical H0 startup/source evaluation | HISTORICAL H0 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md` |
| `docs/h3/reports/H1A_MINIMUM_VIDEO_SKIN_NATIVE_T2V_REPORT.md` | H1A implementation, Native runtime, browser UI, and closeout boundary | CURRENT H1A REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1A_MINIMUM_VIDEO_SKIN_NATIVE_T2V_REPORT.md` |
| `docs/h3/evidence/h1a/2026-09-08/README.md` | H1A browser/UI generation evidence and frame review | CURRENT H1A EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1a/2026-09-08/README.md` |
| `docs/h3/evidence/h1a/2026-09-08/manifest.json` | Machine-readable H1A runtime/output manifest | CURRENT H1A EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1a/2026-09-08/manifest.json` |
| `docs/h3/reports/H1B_SINGLE_REFERENCE_NATIVE_I2V_REPORT.md` | H1B implementation, single-reference contract, Native runtime, browser UI, and closeout boundary | CURRENT H1B REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1B_SINGLE_REFERENCE_NATIVE_I2V_REPORT.md` |
| `docs/h3/evidence/h1b/2026-09-09/README.md` | H1B T2V regression, reference controls, Native I2V, and media evidence | CURRENT H1B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b/2026-09-09/README.md` |
| `docs/h3/evidence/h1b/2026-09-09/manifest.json` | Machine-readable H1B runtime/output manifest | CURRENT H1B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b/2026-09-09/manifest.json` |
| `docs/h3/reports/H1B1_START_END_FRAME_NATIVE_FL2VA_REPORT.md` | H1B.1 fixed-slot Start/End implementation, Native runtime, browser UI, and closeout boundary | CURRENT H1B.1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1B1_START_END_FRAME_NATIVE_FL2VA_REPORT.md` |
| `docs/h3/evidence/h1b1/2026-09-09/README.md` | H1B.1 Start-only, Start+End, End-only, T2V regression, and media evidence | CURRENT H1B.1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b1/2026-09-09/README.md` |
| `docs/h3/evidence/h1b1/2026-09-09/manifest.json` | Machine-readable H1B.1 runtime/output manifest | CURRENT H1B.1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b1/2026-09-09/manifest.json` |
| `docs/h3/reports/H1B1_UX_INTEGRITY_P0_FIX_REPORT.md` | H1B.1 Astra P0-A/P0-B UX integrity fix, verification, and deferred findings | CURRENT H1B.1 UX P0 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1B1_UX_INTEGRITY_P0_FIX_REPORT.md` |
| `docs/h3/evidence/h1b1-ux/2026-09-09/README.md` | H1B.1 UX P0 browser/static evidence and one bounded Native completion | CURRENT H1B.1 UX P0 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b1-ux/2026-09-09/README.md` |
| `docs/h3/reports/H1B1_UX_P1_PRIMARY_ACTION_VISIBILITY_REPORT.md` | H1B.1 primary Generate visibility, compactness, measurement, and deferred findings | CURRENT H1B.1 UX P1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1B1_UX_P1_PRIMARY_ACTION_VISIBILITY_REPORT.md` |
| `docs/h3/evidence/h1b1-ux-p1/2026-09-09/README.md` | H1B.1 P1 layout measurements and Browser evidence | CURRENT H1B.1 UX P1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b1-ux-p1/2026-09-09/README.md` |
| `docs/h3/reports/H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md` | H1B.1 state semantics and History settings reuse contract, verification, and boundary | CURRENT H1B.1 UX P2 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md` |
| `docs/h3/evidence/h1b1-ux-p2/2026-09-09/README.md` | H1B.1 P2 status/history source, logic, and bounded Browser evidence | CURRENT H1B.1 UX P2 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1b1-ux-p2/2026-09-09/README.md` |
| `docs/h3/reports/H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md` | H1C Browser bridge, Native continuation, evidence, and closeout boundary | CURRENT H1C REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md` |
| `docs/h3/evidence/h1c/2026-09-09/README.md` | H1C source/bridge/continuation Browser and media evidence | CURRENT H1C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1c/2026-09-09/README.md` |
| `docs/h3/evidence/h1c/2026-09-09/manifest.json` | Machine-readable H1C runtime/bridge/output manifest | CURRENT H1C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h1c/2026-09-09/manifest.json` |

## External master roadmap

The current local Rev.3 master is:

D:/GitHub/tegaki/MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The preserved source remains:

D:/GitHub/tegaki/MiniMax H3/Archive/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The two files are byte-identical. The Archive source was not deleted, moved,
renamed, merged, or edited.

Canonical GitHub URL:

https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The root master path is present in the local `origin/main` tracking ref at
commit `47056a7c972f187f0ce9686db1ae7bb93ce8aca3`. This confirms the repository
publication state represented by `origin/main`; it does not imply Owner
acceptance or final production acceptance.

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
- [H1A_MINIMUM_VIDEO_SKIN_NATIVE_T2V_REPORT.md](reports/H1A_MINIMUM_VIDEO_SKIN_NATIVE_T2V_REPORT.md)
  — current H1A implementation, contract, verification, runtime result, and explicit non-scope.
- [H1B_SINGLE_REFERENCE_NATIVE_I2V_REPORT.md](reports/H1B_SINGLE_REFERENCE_NATIVE_I2V_REPORT.md)
  — current H1B single-Start-Frame implementation, verification, runtime result, and explicit non-scope.
- [H1B1_START_END_FRAME_NATIVE_FL2VA_REPORT.md](reports/H1B1_START_END_FRAME_NATIVE_FL2VA_REPORT.md)
  — current H1B.1 fixed Start/End slot implementation, Native/browser generation,
  evidence, and explicit non-scope.
- [H1B1_UX_INTEGRITY_P0_FIX_REPORT.md](reports/H1B1_UX_INTEGRITY_P0_FIX_REPORT.md)
  — H1B.1 Reference visibility and Active Job/History Preview integrity fix,
  bounded browser evidence, and deferred Astra findings.
- [H1B1_UX_P1_PRIMARY_ACTION_VISIBILITY_REPORT.md](reports/H1B1_UX_P1_PRIMARY_ACTION_VISIBILITY_REPORT.md)
  — H1B.1 primary Generate visibility, control-column compaction, measurements,
  and P0 regression boundary.
- [H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md](reports/H1B1_UX_P2_STATUS_HISTORY_REUSE_REPORT.md)
  — H1B.1 state semantics, History `Use settings`, atomic restore, Browser
  acceptance, and explicit non-scope.
- [H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md](reports/H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md)
  — H1C same-origin near-final frame bridge, atomic Start/End preparation,
  Native continuation, evidence, and explicit non-scope.

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
- [H1A evidence](evidence/h1a/2026-09-08/) — Native T2V API and browser UI
  completion evidence, output hashes, UI screenshot, frame triplet, and contact sheet.
- [H1B evidence](evidence/h1b/2026-09-09/) — T2V regression, single-reference
  controls, Native I2V browser run, output hashes, frame triplet, and contact sheet.
- [H1B.1 evidence](evidence/h1b1/2026-09-09/) — fixed Start/End controls,
  Start-only, Start+End, End-only, and T2V browser runs, output hashes, Native
  prompt binding, frame triplet, and contact sheet.
- [H1B.1 UX P0 evidence](evidence/h1b1-ux/2026-09-09/) — empty Reference
  visibility, Active Job/Preview separation, one bounded browser completion,
  and explicit limits of the live History-during-Running replay.
- [H1B.1 UX P1 evidence](evidence/h1b1-ux-p1/2026-09-09/) — initial viewport
  layout measurements and live Generate visibility evidence without generation.
- [H1B.1 UX P2 evidence](evidence/h1b1-ux-p2/2026-09-09/) — state-copy mapping,
  History `Use settings`, atomic restore logic, and bounded Text-only Browser
  evidence.
- [H1C evidence](evidence/h1c/2026-09-09/) — source output, Browser canvas
  bridge provenance, atomic continuation form result, Native continuation, and
  extracted media/contact-sheet evidence.
- Production H3 output is isolated at `output/h3/video/`, with `debug/` and `tests/`
  alongside it. Existing `output/` content and Manga output are outside this slice.

The historical groundwork reports remain historical records. The current gate is
the H1C report and evidence above; it does not imply Owner acceptance, public
production deployment, or adoption of a candidate implementation.

## H3 implementation boundary

H1A, H1B, H1B.1, and H1C own the following narrow production paths:

```text
h3/app/
h3/adapters/
h3/config/
h3/tests/
workflows/h3/
h3/run_h3.bat
h3/run_h1a.bat  (compatibility wrapper)
```

The local skin is a small vanilla UI plus a stdlib HTTP server. Native ComfyUI
remains the execution, queue, history, and output authority. The semantic
adapter is the only UI-to-workflow boundary. H1A remains the no-reference T2V
route; historical H1B keeps its single legacy Start Frame route; H1B.1 adds
only the fixed `start_frame` / `end_frame` slots and binds them to optional
`first_frame` / `last_frame` edges. H1C adds only the completed-History-output
near-final Browser canvas bridge into `start_frame`, clears `end_frame`, and
permits one manual continuation through the existing Native route. `h3/run_h3.bat`
is canonical and `run_h1a.bat` delegates to it. Do not infer REF2VA, ordered
generic multi-reference, Still, Segment, Studio, Timeline, Storyboard, Cast,
3D, Manga, or a persistent project schema from these paths.

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
7. Review the H1A/H1B implementation boundary and confirm that existing
   Illustrious files, shared ComfyUI core/frontend, and Manga runtime were not changed.
8. Read the H0.1 model manifest and generation evidence; verify that generation,
   startup, blocked, owner-action-required, and not-tested states are not conflated.
9. Read the H1A and H1B reports and dated evidence; verify the browser UI path
   separately from direct API/runtime evidence.
10. Read the H1B.1 report and dated evidence; verify Start-only, Start+End,
    End-only, and text-only browser paths separately from Native media evidence.
11. Read the H1B.1 UX P0 report and dated evidence; verify Reference hidden
    semantics and the separate Active Job/History Preview authorities.
12. Read the H1B.1 UX P1 report and dated evidence; verify the 1280 x 720
    primary-action measurement and that Advanced remains optional.
13. Read the H1B.1 UX P2 report and dated evidence; verify state semantics,
    atomic History reuse, Preview-only selection, and the bounded Browser result.
14. Read the H1C report and dated evidence; verify the source video URL,
    near-final capture time, bridge Reference provenance, atomic Start/End
    result, and one manual Native continuation separately.
15. Stop at the Web GPT / Astra H1C review gate; do not infer Owner
    acceptance, REF2VA, Still, Segment, Studio, or production deployment from a
    local generation result.

## Evidence vocabulary

- `OBSERVED`: public repository/document observation only.
- `VERIFIED LOCAL STARTUP`: a reproducible local startup/API/static result.
- `VERIFIED LOCAL GENERATION`: a reproducible local output with hash and frame
  evidence; it does not imply quality or Owner acceptance.
- `VERIFIED BROWSER UI GENERATION`: the prompt and, for H1B, the single Start
  Frame were submitted through the browser controls and the job reached a visible
  completed Preview; it does not replace runtime/media evidence or Owner acceptance.
- `IMPLEMENTED`: the bounded H1A/H1B/H1C source and canonical launcher are present and tested;
  it does not mean the whole H3 roadmap is implemented.
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
reports, or workflow index. It adds an H3-only path beside them. H1A/H1B/H1B.1/
H1C did not modify the existing Illustrious file, workflow, runtime, Manga
docs, or shared ComfyUI core/frontend.
