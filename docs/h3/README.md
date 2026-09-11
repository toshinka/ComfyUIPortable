# MiniMax H3 Document Hub

更新: 2026-09-11 JST

このページは `ComfyUIPortable` における MiniMax H3 の調査・計画・報告・
将来の実装棚とReference Implementation evidenceを一か所から辿るための
document hub です。現在は **IP2 / Experimental Browser Prep/Edit Lens — PASS WITH KNOWN NATIVE LIMIT / VERIFIED BROWSER UI GENERATION / PUBLISHED ON MAIN** であり、Rev.4 は **CURRENT MASTER / DOCS-ONLY / PUBLISHED ON MAIN** です。
H1C / Frame-Bridged Continuation は回帰基盤として保持し、
H1B.1 / Start + End Frame and Native FL2VA vertical slice + UX P0/P1/P2
Fixes は履歴と回帰対象として保持します。H0/H0.1/H1A/H1B の model
isolation、generation smoke、T2V skin、single-Start-Frame I2V も保持します。
H1A implementation commit `925596b9d7fbd731290fe9869ea34a0006249130` is
published on `main`. H1B, H1B.1, and the H1B.1 UX P0/P1/P2 fixes are implemented and
locally/browser verified within their recorded bounds; Owner acceptance remains
pending. H1C evidence/report/canonical docs are recorded in commit `4df2f2a5f29957a9f4ba429ddd8796d13de5de3b`
and are published on GitHub `main`; Owner acceptance remains pending. H2A
still feasibility is implemented and locally verified through a bounded
Native route; no production Still UI was added and H2A is published on GitHub
`main`. H2B source-anchored Still feasibility is implemented and locally
verified through a matched Native pair; its implementation, evidence, and
docs are published on GitHub `main`. Owner acceptance remains pending.
H2-INFRA external model library normalization is `CONFIGURED / VERIFIED` and
`PUBLISHED ON MAIN`:
the four first-wave heavy Portable copies are removed, the Portable fallback
namespace is retained without bundled heavy weights, and the local shortcut
collection is configured. H2C is the bounded Browser-facing Still UI gate over
the H2B source route; production I2I semantics remain out of scope. Its base
implementation, seed-losslessness fix, evidence, and closeout docs are present
in the current `origin/main` history. VP1 adds only the verified Video options
`608 x 352` / `736 x 416` and `5` / `15` seconds; Still remains `608 x 352`
with Duration hidden. VP1 implementation, evidence, and canonical publication
wording are published on `main` at `41da0bf804d049adc40e2ae2d5abfdd59eabc703`.
VP2A audited the Native Ref2VA source contract and its original acquisition-gate
package is published on `main` at `e4e078490cd2f96a953e6261399f268652d49c04`.
Owner later explicitly authorized the exact artifact for the bounded R1
acquisition and runtime resume. R1 acquired and hash-verified that model in
the external store, completed Picture-only and Picture+Video Native rows, and
completed exactly one standard FL2VA/T2V transition. The R1 implementation,
report, and evidence are published on `main` at
`d067a4170edeffee200a6f1a8d279a1c1b68be28`. The current classification is
`FEASIBLE WITH LIMITS`; its Browser R2V boundary was intentionally deferred to
VP2B. VP2B is implemented and published on `main` at
`cfc8161ab0399338824e175b95ea0763281d57e6`; its closeout evidence/report and
verifier-compatibility fix are published on `main` at
`543d8c2c2817743b10f255c168047e4edd1781a9`. Its experimental Reference path
accepts one Character Image and optionally one MP4 Motion Video, uses fixed
`608 x 352 / 5 seconds / 20 steps`, keeps audio disconnected, and completed one
real Picture+Motion Browser generation plus one post-Reference Standard
Text-only baseline. Browser playback, History route labeling, atomic Use
settings, Continue absence for Reference, Standard/Reference isolation, and
Still isolation passed. The result records Picture influence as `OBSERVED` and
Video influence as `NOT CONVINCING`, a known Native mixed-reference limitation;
Owner acceptance remains pending. VP2C adds only same-session History handoff
from completed Still/Video results and scoped drag-and-drop ergonomics for the
existing Character Image and Motion Video slots. Its local server/UI contracts
pass, and the authorized Browser run completed exactly one Still and one
Reference Video at `http://127.0.0.1:8190/`. Character File D&D passed; Motion
File D&D was limited by safe CUA target acceptance, while the exact Motion
picker route passed and supplied the Reference run. VP2C implementation is
published on `main` at `56ad30afa128ef4120f962b6c114fc0e7526aae8`; VP2C
closeout is published on `main` at
`1a869125fa95ef4c7b1e94b0ccedab39fc52b4be`. Rev.4 is the current master
roadmap and is published on `main` at
`3880534af0e26b970a8fd0a1ba564af6bc88c15e`. The IP1 implementation/evidence
package is published on `main` at `d8b1a7ca070db1fe78b6d07ef0db01500e88c828`;
that historical commit also carries concurrent Manga material. The H3-only
IP1 closeout is published at `35e49859f3beb3bd0b4b1b2d2dd793897dc6b479`, and
the current `origin/main` at the IP1 reconciliation was the later Manga-only
descendant `b5c79b85ed2fdeec1bf30254945db569666ecfa4`. IP1 remains the
`FEASIBLE WITH LIMITS` Native-only Image Prep gate. IP2 adds the bounded
experimental Browser Prep/Edit lens over that existing Native route. The
authorized local Browser run at `http://127.0.0.1:8190/` used one Source and
one hash-matched Donor and completed exactly one Source-only Prep and one
Source + Donor Prep. Source preservation was strong; the requested rainy
environment change was observed; donor yellow-coat influence was not
convincing; donor attribute isolation remains not guaranteed. Edit in Prep,
Prep to Character handoff, History `Use settings`, and mode isolation passed
without extra generation. IP2 implementation is present in published main
history; this H3-only closeout adds the report and evidence package. The
current main also contains concurrent Manga development history. Owner
acceptance remains pending.

この文書は Web GPT / Astra / LUNA が新しいChatから同じ状態を復元するための
入口です。候補OSSの採用決定やソースコードの再配布を意味しません。

## Canonical files

| Path | Role | Status | GitHub URL after Owner push |
|---|---|---|---|
| `GITHUB_H3.txt` | H3 External AI Entry | CURRENT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/GITHUB_H3.txt` |
| `docs/h3/README.md` | H3 document hub | CURRENT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/README.md` |
| `MiniMax H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md` | Current H3 master roadmap | CURRENT / DOCS-ONLY | `https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md` |
| `MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md` | Historical H3 master roadmap | HISTORICAL / SUPERSEDED | `https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md` |
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
| `docs/h3/reports/H2A_H3_STILL_NATIVE_FEASIBILITY_REPORT.md` | H2A bounded Native still feasibility route, telemetry, visual review, and closeout boundary | CURRENT H2A REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H2A_H3_STILL_NATIVE_FEASIBILITY_REPORT.md` |
| `docs/h3/evidence/h2a-still/2026-09-09/README.md` | H2A Native still output and runtime evidence | CURRENT H2A EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2a-still/2026-09-09/README.md` |
| `docs/h3/evidence/h2a-still/2026-09-09/manifest.json` | Machine-readable H2A still/runtime/output manifest | CURRENT H2A EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2a-still/2026-09-09/manifest.json` |
| `docs/h3/reports/H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md` | H2B single-source anchored Still feasibility route, matched comparison, telemetry, and closeout boundary | CURRENT H2B REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md` |
| `docs/h3/evidence/h2b-source-anchor/2026-09-10/README.md` | H2B source image, prompt-only/anchored outputs, source-influence review, and runtime evidence | CURRENT H2B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2b-source-anchor/2026-09-10/README.md` |
| `docs/h3/evidence/h2b-source-anchor/2026-09-10/manifest.json` | Machine-readable H2B source/runtime/output manifest | CURRENT H2B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2b-source-anchor/2026-09-10/manifest.json` |
| `docs/h3/reports/H2C_STILL_UI_VERTICAL_SLICE_REPORT.md` | H2C Still UI Browser acceptance, state separation, visual review, and closeout | CURRENT H2C REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H2C_STILL_UI_VERTICAL_SLICE_REPORT.md` |
| `docs/h3/evidence/h2c-still-ui/2026-09-10/README.md` | H2C prompt-only/source Still Browser, History, cross-media, and visual evidence | CURRENT H2C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2c-still-ui/2026-09-10/README.md` |
| `docs/h3/evidence/h2c-still-ui/2026-09-10/manifest.json` | Machine-readable H2C Browser/runtime/output manifest | CURRENT H2C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/h2c-still-ui/2026-09-10/manifest.json` |
| `docs/h3/reports/VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md` | VP1 safe Video resolution/duration envelope, Native matrix, Browser unlock, and closeout boundary | CURRENT VP1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md` |
| `docs/h3/evidence/vp1-video-envelope/2026-09-10/README.md` | VP1 Native/Browser media, config, History, Still-isolation, and telemetry evidence | CURRENT VP1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp1-video-envelope/2026-09-10/README.md` |
| `docs/h3/evidence/vp1-video-envelope/2026-09-10/manifest.json` | Machine-readable VP1 runtime/output manifest | CURRENT VP1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp1-video-envelope/2026-09-10/manifest.json` |
| `docs/h3/reports/VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md` | VP2A Native Ref2VA/R2V R1 acquisition, source contract, feasibility, transition, and historical stop | CURRENT VP2A-R1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md` |
| `docs/h3/evidence/vp2a-ref2va-r2v-feasibility/2026-09-10/README.md` | VP2A-R1 exact model verification, Native Picture/Video rows, telemetry, visual review, and historical gate | CURRENT VP2A-R1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2a-ref2va-r2v-feasibility/2026-09-10/README.md` |
| `docs/h3/evidence/vp2a-ref2va-r2v-feasibility/2026-09-10/manifest.json` | Machine-readable VP2A-R1 acquisition/runtime manifest | CURRENT VP2A-R1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2a-ref2va-r2v-feasibility/2026-09-10/manifest.json` |
| `docs/h3/reports/VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md` | VP2B experimental Reference Video playground, Browser acceptance, fixed contract, visual limitation, and closeout boundary | CURRENT VP2B REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md` |
| `docs/h3/evidence/vp2b-r2v-playground/2026-09-10/README.md` | VP2B authorized Picture+Motion Browser run, Standard regression, History/Use settings, isolation, and telemetry | CURRENT VP2B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2b-r2v-playground/2026-09-10/README.md` |
| `docs/h3/evidence/vp2b-r2v-playground/2026-09-10/manifest.json` | Machine-readable VP2B Browser/runtime/media manifest | CURRENT VP2B EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2b-r2v-playground/2026-09-10/manifest.json` |
| `docs/h3/reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md` | VP2C same-session Reference handoff, scoped D&D, local contracts, and Browser gate | CURRENT VP2C REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md` |
| `docs/h3/evidence/vp2c-reference-handoff/2026-09-11/README.md` | VP2C implementation, authorized Browser acceptance, and bounded D&D limitation | CURRENT VP2C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2c-reference-handoff/2026-09-11/README.md` |
| `docs/h3/evidence/vp2c-reference-handoff/2026-09-11/manifest.json` | Machine-readable VP2C acceptance manifest | CURRENT VP2C EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/vp2c-reference-handoff/2026-09-11/manifest.json` |
| `docs/h3/reports/IP1_NATIVE_IMAGE_PREP_REFERENCE_EDIT_FEASIBILITY_REPORT.md` | IP1 Native Ref2VA Image Prep feasibility, runtime, visual limits, and non-scope | CURRENT IP1 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/IP1_NATIVE_IMAGE_PREP_REFERENCE_EDIT_FEASIBILITY_REPORT.md` |
| `docs/h3/evidence/ip1-native-image-prep/2026-09-11/README.md` | IP1 Native audit, donor, three edit cases, frame-0, telemetry, and visual evidence | CURRENT IP1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/ip1-native-image-prep/2026-09-11/README.md` |
| `docs/h3/evidence/ip1-native-image-prep/2026-09-11/manifest.json` | Machine-readable IP1 Native/runtime/output manifest | CURRENT IP1 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/ip1-native-image-prep/2026-09-11/manifest.json` |
| `docs/h3/reports/IP2_BROWSER_PREP_EDIT_LENS_REPORT.md` | IP2 experimental Browser Prep/Edit Source/Donor acceptance, handoff, limits, and closeout | CURRENT IP2 REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/IP2_BROWSER_PREP_EDIT_LENS_REPORT.md` |
| `docs/h3/evidence/ip2-browser-prep-edit/2026-09-11/README.md` | IP2 authorized local Browser acceptance, visual review, and handoff evidence | CURRENT IP2 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/ip2-browser-prep-edit/2026-09-11/README.md` |
| `docs/h3/evidence/ip2-browser-prep-edit/2026-09-11/manifest.json` | Machine-readable IP2 Browser/runtime/output manifest | CURRENT IP2 EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/ip2-browser-prep-edit/2026-09-11/manifest.json` |
| `docs/h3/reports/H3_MODEL_LIBRARY_SHORTCUT_NORMALIZATION_REPORT.md` | H2-INFRA external model migration, isolation, shortcuts, cold restart, and closeout | CURRENT H2-INFRA REPORT | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_MODEL_LIBRARY_SHORTCUT_NORMALIZATION_REPORT.md` |
| `docs/h3/evidence/model-library/2026-09-10/README.md` | H2-INFRA inventory, migration, deletion, shortcut, and runtime evidence index | CURRENT H2-INFRA EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/model-library/2026-09-10/README.md` |
| `docs/h3/evidence/model-library/2026-09-10/inventory.json` | Machine-readable before/after H3 model inventory | CURRENT H2-INFRA EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/model-library/2026-09-10/inventory.json` |
| `docs/h3/evidence/model-library/2026-09-10/migration_manifest.json` | Machine-readable migration, deletion, runtime, and regression manifest | CURRENT H2-INFRA EVIDENCE | `https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/evidence/model-library/2026-09-10/migration_manifest.json` |

## External master roadmap

The current local Rev.4 master is:

D:/GitHub/tegaki/MiniMax H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md

The historical Rev.3 master is:

D:/GitHub/tegaki/MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The preserved source remains:

D:/GitHub/tegaki/MiniMax H3/Archive/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

The two files are byte-identical. The Archive source was not deleted, moved,
renamed, merged, or edited.

Current Rev.4 canonical GitHub URL:

https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md

Historical Rev.3 canonical GitHub URL:

https://github.com/toshinka/tegaki/blob/main/MiniMax%20H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md

Rev.4 is the current master roadmap and is published on `main` at
`3880534af0e26b970a8fd0a1ba564af6bc88c15e`. The current `origin/main` is the
later Manga-only descendant `df0ad3b389db5149e1b6ab1edb24c568c147a10e`. Rev.3
remains historical and the root/Archive sources are byte-identical. Publication
does not imply Owner acceptance or final production acceptance.

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
- [H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md](reports/H2B_SOURCE_ANCHORED_STILL_FEASIBILITY_REPORT.md)
  — H2B one-source anchored Still feasibility, matched prompt-only comparison,
  Native conditioning semantics, source influence, and explicit non-scope.
- [H2C_STILL_UI_VERTICAL_SLICE_REPORT.md](reports/H2C_STILL_UI_VERTICAL_SLICE_REPORT.md)
  — H2C Still Browser acceptance, source upload, History restore, mode crossing,
  cross-media active/preview separation, visual review, and explicit limits.
- [VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md](reports/VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md)
  — VP1 safe Video resolution/duration envelope, Native T2V/Start+End matrix,
  Browser unlock, History restore, Still isolation, and explicit limits.
- [H3_MODEL_LIBRARY_SHORTCUT_NORMALIZATION_REPORT.md](reports/H3_MODEL_LIBRARY_SHORTCUT_NORMALIZATION_REPORT.md)
  — H2-INFRA external model locations, Portable fallback semantics, shortcut
  collection, cold restart, post-delete Still, and closeout boundary.
- [VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md](reports/VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md)
  — experimental one-picture/optional-motion Reference Video playground,
  Browser acceptance, fixed settings, History restore, isolation, visual
  limitation, and explicit non-scope.

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
- [H2B evidence](evidence/h2b-source-anchor/2026-09-10/) — one source image,
  matched prompt-only and anchored Still outputs, contact sheet, hashes, and
  RTX 4070 telemetry.
- [H2C evidence](evidence/h2c-still-ui/2026-09-10/) — prompt-only and
  source-anchored Still Browser results, History `Use settings`, mode crossing,
  active-job/preview-job separation, Video regression, and visual review.
- [VP1 evidence](evidence/vp1-video-envelope/2026-09-10/) — baseline and
  candidate Native media, Browser dropdown/completion records, config source of
  truth, 64-bit seed-safe History restore, Still isolation, and telemetry.
- [H2-INFRA model-library evidence](evidence/model-library/2026-09-10/) —
  before/after inventory, external hashes, exact Portable deletion, shortcut
  regeneration, cold-start path observation, and post-delete H2B Still.
- [VP2B evidence](evidence/vp2b-r2v-playground/2026-09-10/) — authorized local
  Picture+Motion Browser completion, public History/Use settings, Standard
  baseline, media hashes/ffprobe, sampled VRAM, OOM/retry, and isolation checks.
- Production H3 output is isolated at `output/h3/video/`, with `debug/` and `tests/`
  alongside it. Existing `output/` content and Manga output are outside this slice.

The historical groundwork reports remain historical records. VP1 is the
published Video baseline, and VP2A-R1 remains the Native feasibility gate with
its known mixed-reference quality limits. The VP2B and VP2C packages record
bounded experimental Browser Reference and handoff paths. The current IP2
report and evidence record the bounded Browser Prep/Edit path over the IP1
Native route. These packages do not imply production identity locking,
multiple references, audio conditioning, donor-attribute isolation, Owner
acceptance, or adoption of a broader candidate implementation.

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
generic multi-reference, production I2I semantics, source-fidelity controls,
Segment, Studio, Timeline, Storyboard, Cast, 3D, Manga, or a persistent project
schema from these paths. H2C adds only the bounded Still Source Image lens over
the H2B first-frame route. VP1 adds only the two verified Video resolution
enums and two verified Video duration enums; `/api/config` is the source of
truth, and Still receives no Video option automatically. VP2B adds only the
experimental one-picture/optional-MP4 Reference Video lens over the Native
Ref2VA adapter; Standard remains the default, Reference audio is disconnected,
and Reference settings are server-enforced at `608 x 352 / 5 seconds / 20
steps`. IP1 adds only the separate Native-only source-plus-optional-donor
Image Prep feasibility adapter. IP2 adds only the experimental Browser
Prep/Edit lens over that adapter: one Source plus an optional Donor, fixed
Native settings, History settings reuse, bounded Edit in Prep, and Prep to
Character handoff. Donor attribute isolation is not guaranteed; IP2 is not a
production Image Studio or identity-locking feature.

## Review recipe

1. Start at `GITHUB_H3.txt`.
2. Read the current Rev.4 master and confirm the Rev.3 root/Archive sources are preserved.
3. Read the historical Rev.3 master for inherited GUI and phase principles.
4. Read the landscape and inventory together; do not treat a candidate as
   adopted because it appears in either document.
5. Check licenses and model provenance before any code reuse or installation.
6. Confirm that H3 Video remains first, H3 Still is an acceptance capability,
   and H3 Manga remains later research.
7. Review the visual language and Astra handoff as review boundaries, not
   implementation instructions.
7a. Review the H1A/H1B implementation boundary and confirm that existing
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
15. Read the H2B report and dated evidence; verify the single source path,
    matched prompt-only comparison, Native first-frame binding, source
    influence, and 12GB telemetry separately.
16. Read the H2C report and dated evidence; verify prompt-only and source
    Browser completions, the authorized upload path, `Use settings`, mode
    crossing, active-job/preview-job separation, Video regression, and the
    recorded viewport qualification separately.
17. Read the VP1 report and dated evidence; verify the Native baseline,
    duration-only and resolution-only candidate matrices, Browser option
    population/completions, History restore, 64-bit seed preservation, and
    Still isolation separately.
18. Read the VP2A report and dated evidence; verify the historical acquisition
    gate, exact model filename/bytes/SHA-256, Native source contract, Picture
    and Video rows, telemetry, visual classifications, and one FL2VA/T2V
    transition separately.
19. Read the VP2B report and dated evidence; verify the one-picture/optional-
    motion Browser path, deterministic prompt adapter, fixed settings, public
    History route, atomic `Use settings`, Continue absence, Standard regression,
    state isolation, Still isolation, media hashes, telemetry, and visual limit.
20. Read the VP2C report and dated evidence; verify same-session completed-job
    handoff, opaque public asset metadata, source preservation, active-job and
    atomic failure guards, and the two scoped Reference-slot D&D paths. Keep
    the real Browser acceptance and Owner acceptance separate from local tests.
21. Review the IP1 Native Image Prep report and dated evidence after the VP2C
    package; keep source preservation, donor influence, Native packet/frame-0
    behavior, runtime qualification, Browser UI, publication, and Owner
    acceptance distinct.
22. Review the IP2 Browser Prep/Edit report and dated evidence; verify the
    exact Source and Donor selection methods, two-generation budget, separate
    Source/Donor ownership, Preview and History routes, materialized Picture
    roles, `Use settings`, `Edit in Prep`, `Use as Character`, mode isolation,
    visual classifications, telemetry limits, and no file-scheme permission.
23. Stop after IP2 review; do not infer Owner acceptance, production identity
    locking, arbitrary multi-reference editing, donor-attribute isolation,
    IP3, Image Studio, Qwen Image Edit, T=1 diffusion, LoRA, audio conditioning,
    Segment, Studio, or production deployment from this evidence.

## Evidence vocabulary

- `OBSERVED`: public repository/document observation only.
- `VERIFIED LOCAL STARTUP`: a reproducible local startup/API/static result.
- `VERIFIED LOCAL GENERATION`: a reproducible local output with hash and frame
  evidence; it does not imply quality or Owner acceptance.
- `VERIFIED BROWSER UI GENERATION`: the prompt and, for H1B, the single Start
  Frame were submitted through the browser controls and the job reached a visible
  completed Preview; it does not replace runtime/media evidence or Owner acceptance.
- `IMPLEMENTED`: the bounded H1A/H1B/H1C/H2C/VP1 source and canonical launcher are present and tested;
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
H1C/H2A/H2B did not modify the existing Illustrious file, workflow, runtime,
Manga docs, or shared ComfyUI core/frontend.
