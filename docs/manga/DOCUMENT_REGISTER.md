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

## 1. DOCUMENT AUTHORITY & CLASSIFICATION (文書権威分類)

運用・設計の最上位権威は `../../AGENTS.md` (Level 1) および `../STATUS.md` (Level 2) であり、ドメイン入口は `../../GITHUB_MANGA.txt` (Level 3) である。横断プロダクションUI/UXの現行設計権威は `../ui/*` に委譲される。

### Current Operational & Domain Authority (現行運用・ドメイン正本)
| 文書 | 権威レベル | 内容と役割 |
|---|---|---|
| `../../AGENTS.md` | STABLE CONTRACT (Level 1) | 全社運用ルール・Agent Mode・Card統制 |
| `../STATUS.md` | CURRENT STATE (Level 2) | 全社現在地・優先度・決定シーケンス・次Cardの単一正本 |
| `../../GITHUB_MANGA.txt` | DOMAIN ROUTER (Level 3) | Mangaドメインの公式外部AIルーター |
| `STATUS.md` | MANGA DOMAIN DETAIL | Mangaドメイン固有の現在地・マイルストーン詳細履歴 |
| `../ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md` 等 | CURRENT UI AUTHORITY | 横断プロダクションUI原則・Createモデル・コンポーネント規約 |
| `README.md` | MANGA DOCUMENT HUB | Mangaドメイン文書・レポート・検証へのnavigation |
| `cards/README.md` | CARD ROUTER | 完了Cardの保管場所・Card規約 |

### Domain Strategic Baseline & References (ドメイン戦略基準・参照資料)
| 文書 | 権威レベル | 内容と役割 |
|---|---|---|
| `plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md` | DOMAIN STRATEGIC BASELINE | 漫画制作環境の初期全体戦略（docs/STATUS.mdやdocs/uiを上書きしない） |
| `plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md` | HISTORICAL DESIGN REFERENCE | Minimum-Hand UX設計構想（現行UIはdocs/ui/*に従う） |
| `plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md` | HISTORICAL ASSET AUDIT | 既存ノード/ワークフロー資産棚卸し・Comic Creator参考 |
| `MANGA_DOCUMENT_NAMESPACE_MIGRATION_MAP.md` | HISTORICAL MIGRATION AUDIT | 文書/outputのmove/retain判断と参照監査 |

### Legacy Operating Handoff & Protocols (旧運用資料 — 実行不可)
| 文書 | 権威レベル | 内容と役割 |
|---|---|---|
| `WEBGPT_SOL_LUNA_HANDOFF.md` | LEGACY HANDOFF | 2026-09-11時点の旧チャット引き継ぎ記録（新チャット入口ではない） |
| `plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md` | LEGACY OPERATING PROTOCOL | 旧SOL/LUNA実行プロトコル（AGENTS.mdおよびCardが優先） |

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
| `M3B-LR4` | PUBLISHED / SOL REVIEWED | Figure-union mask locality A/B research slice; exact six-output comparison; LOCALITY_SUPPORTED; no schema or production integration |
| `M3B-LR5` | PUBLISHED / SOL REVIEWED | CAST plus Figure-masked CLEAN compatibility research; exact four-output comparison; CAST_MASKED_CONFLICT; hard effect-mask boundary / quality degraded; no schema or production integration |
| `M3B-LR6` | COMPLETED LOCAL / SOL REVIEW PENDING | CAST soft-edge Figure-mask compatibility research; exact six-output OFF/HARD/SOFT comparison; fixed radius-16 derivation; SOFT_MASK_CONFLICT; no schema or production integration |

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
