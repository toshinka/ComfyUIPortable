# 文書登録簿 — ComfyUIPortable (Document Register)

2026-09-10 JST 更新。

## 0. DOMAIN ENTRY MAP

| Domain | Canonical Entry | Document Hub | Boundary |
|---|---|---|---|
| Router / compatibility | `../../GITHUB_ComfyUI.txt` | `../README.md` | 詳細なstatusを所有しない |
| Manga Authoring | `../../GITHUB_MANGA.txt` | `README.md` | Illustrious/Anima等の画像backendを扱うManga subsystem |
| MiniMax H3 | `../../GITHUB_H3.txt` | `../h3/README.md` | H1B.1。Manga runtimeへ直接接続しない |

MangaとH3はrepository/Portable baseを共有するが、現在は別production subsystem。
製品目標は共通TEGAKI shellの上位tabでMangaとVideo (H3)を切り替える構成。
両者が独立して回帰可能になるまで、schema/runtime/workflow/evidence/outputはdomain別に維持する。

## 1. CURRENT AUTHORITY (現在正本)
以下の文書群が、ComfyUIPortable の現行戦略・UX設計・資産棚卸し・運用ルールの最高権威を持つ。

| 文書 | 権威レベル | 内容と役割 |
|---|---|---|
| `STATUS.md` | CURRENT STATE | 現在地・方針要約・次の一件のみを保持する最優先入口 |
| `plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md` | STRATEGIC SSOT | 漫画制作環境の全体戦略・Minimum-Hand・マイルストーン定義 |
| `plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md` | CURRENT DESIGN | UX導線・手数設計・画面レイアウト・出現条件 |
| `plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md` | CURRENT AUDIT | 既存ノード/ワークフロー資産棚卸し・証拠の限界・Comic Creator参考 |
| `plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md` | CURRENT PROCESS | Web GPT SOLのCard発行とlocal LUNA実装、GitHub review loop |
| `README.md` | MANGA DOCUMENT HUB | Mangaの正本、report、research、verificationへのnavigation |
| `MANGA_DOCUMENT_NAMESPACE_MIGRATION_MAP.md` | CURRENT MIGRATION AUDIT | 文書/outputのmove/retain判断と参照監査 |
| `WEBGPT_SOL_LUNA_HANDOFF.md` | CURRENT HANDOFF | 過去会話を知らないSOL向け全体像、現在地、LUNA Card発行条件 |
| `cards/README.md` | CARD ROUTER | Cardのcurrent/completed境界と保管場所。旧Cardを現行指示として使わないための入口 |

## 2. CURRENT CARD (現行作業カード)
| カード | 状態 | 役割 |
|---|---|---|
| `3M-Prep` | COMPLETED | Astra成果のGitHub正本化、Product Direction整理、前処理 |
| `M0 / 3M-0` | COMPLETED | Versioned Authoring Contract固定、Scene/Frame分離、Legacy Import/Export基盤 |
| `M0.1 / 3M-0.1` | COMPLETED | 契約境界Hardening（FK空集合、孤立binding遮断、Scene/Frame乖離検出、厳格座標逆変換、境界move等） |
| `M1 / 3M-1` | COMPLETED | Scene-only Minimum-Hand Draft（かんたんモード、粗領域・Scene Prompt・Seed生成導線・実機検証5条件完走） |
| `M1.1 / 3M-1.1` | COMPLETED | Canonical Workflow Wiring & UI SSOT Truth Fix（正本実配線、dimensions方言撤廃、一意ID、Manifest v2、実機配線検証3条件完走） |
| `M2A / 3M-2A` | COMPLETED | Character Spatial Capability Ladder & Control Escalation Gate（左右スワップ因果性実証、Prompt深度実証、3人混成実証、ControlNet不要判定） |
| `M2A.1 / 3M-2A.1` | COMPLETED | Prompt-Region Calibration & Conditional ControlNet Escalation Gate（8-seed実証、Spatial Hint Compiler、Option A+採択） |
| `M2B / 3M-2B` | COMPLETED | Minimum-Hand CAST & Character Staging Product UI (Option A+: Rough Region + Free Text + Hidden Spatial Helper) |
| `M2B.1 / 3M-2B.1` | COMPLETED / FAIL (Browser) | CAST Placement Semantics & Live Browser Closure (選択CAST配置因果性修正、純粋操作分離、実機閉域検証; Owner Browser check FAIL) |
| `M2B.2 / 3M-2B.2` | COMPLETED / OWNER ACCEPTED | Live UI Bootstrap, Widget Serialization & Workflow Repair |
| `M3A / 3M-3A` | COMPLETED (Headless) / OWNER PENDING (Browser) | Visual Panel Frame Layer & Frame Guide Integration |
| `M3A.1 / 3M-3A.1` | PASS (Headless) / OWNER PENDING | Frame Runtime Truth, Gutter Semantics & Live Browser Closure (fail-closed、comic_panels white gutter、per-frame thickness、area canonical key、derive→None) |
| `M3B-LR2R1` | PUBLISHED / SOL REVIEWED | AnyTest v4 shared-storage acquisition, ControlNet loader, bounded Guide A/B research, and canonical no-Guide regression |
| `M3B-LR3` | COMPLETED LOCAL / SOL REVIEW PENDING | Derived Figure-geometry CLEAN Guide versus RAW/OFF bounded A/B research slice; provisional result OPTION_A_INCONCLUSIVE; no schema or production integration |

## 3. HISTORICAL / SUPERSEDED (過去の参照資料)
過去のPhase指示書や中間計画書は歴史的経緯の参照用であり、次作業の直接指示とはみなさない。

| 文書/群 | 状態 | 扱い |
|---|---|---|
| `contracts/CAST_SPEC_V1.md`, `contracts/COMPILE_PLAN_V1.md`, `contracts/MANGA_SCENE_DATA_CONTRACT.md`, `contracts/LORA_ENTRY_V1.md` | EXISTING CONTRACT | M0での旧import互換性照合対象 |
| `reports/PHASE3L_*`, `verification/PHASE3L_*`, `manga/research/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md` | HISTORICAL EVIDENCE / RESEARCH | Phase 3Lの実装成果（14件PENDING・WF71限界を包含） |
| その他旧Phase reports / verification (Phase 2〜3K) | HISTORICAL EVIDENCE | 必要時のみ個別参照 |
| `cards/completed/` | COMPLETED EXECUTION CARDS | 3M-Prep〜M3A.1の実行契約。実績確認用であり再実行しない |
| `archive/instructions/` | SUPERSEDED INSTRUCTIONS | Phase 2〜3Lの旧依頼書。新戦略と競合するため歴史資料として保持 |
| `archive/plans/` | SUPERSEDED / DEFERRED PLANS | 旧中間計画、GUI追補、将来構想。現行戦略の根拠にはしない |
| `archive/duplicates/` | PRESERVED DUPLICATE | byte-identicalなM1.1複製を削除せず隔離保管 |
| `plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md` | SUPERSEDED PROCESS | 旧SOL/Gemini運用。新Cardへ使用しない |
| `MANGA_GEMINI_RESTART_CONTEXT.md` | HISTORICAL PAUSE SNAPSHOT | 2026-09-08のGemini停止時点。現在地には使用しない |
| `../../Archive/2026-09-06_pre_astra_replan/` | ARCHIVED SNAPSHOT | 統合前原本のハッシュ保全 |
| `references/WORKFLOW_INDEX.md`, `references/DEPENDENCIES.md`, `references/KNOWN_ISSUES.md` | EXISTING REFERENCE | 古い記述を含む。実装/環境はlive確認 |
| `references/RESEARCH_REFERENCES.md` | CURRENT REFERENCE INVENTORY | Manga外部asset・license・provenance |

※ 本projectには現時点で `TECHNICAL.md` は存在しない。Tegaki本体（`tegaki_work/`）の同名文書やPhase履歴を本環境へ混同しないこと。
