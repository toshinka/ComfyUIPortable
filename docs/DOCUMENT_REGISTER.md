# 文書登録簿 — ComfyUIPortable (Document Register)

2026-09-06 JST 更新。

## 1. CURRENT AUTHORITY (現在正本)
以下の文書群が、ComfyUIPortable の現行戦略・UX設計・資産棚卸し・運用ルールの最高権威を持つ。

| 文書 | 権威レベル | 内容と役割 |
|---|---|---|
| `STATUS.md` | CURRENT STATE | 現在地・方針要約・次の一件のみを保持する最優先入口 |
| `plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md` | STRATEGIC SSOT | 漫画制作環境の全体戦略・Minimum-Hand・マイルストーン定義 |
| `plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md` | CURRENT DESIGN | UX導線・手数設計・画面レイアウト・出現条件 |
| `plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md` | CURRENT AUDIT | 既存ノード/ワークフロー資産棚卸し・証拠の限界・Comic Creator参考 |
| `plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md` | CURRENT PROCESS | Web GPT (設計/Card発行) と Antigravity Gemini (実装) の協調プロトコル |

## 2. CURRENT CARD (現行作業カード)
| カード | 状態 | 役割 |
|---|---|---|
| `3M-Prep` | COMPLETED | Astra成果のGitHub正本化、Product Direction整理、前処理 |
| `M0 / 3M-0` | COMPLETED | Versioned Authoring Contract固定、Scene/Frame分離、Legacy Import/Export基盤 |
| `M0.1 / 3M-0.1` | COMPLETED | 契約境界Hardening（FK空集合、孤立binding遮断、Scene/Frame乖離検出、厳格座標逆変換、境界move等） |
| `M1 / 3M-1` | COMPLETED | Scene-only Minimum-Hand Draft（かんたんモード、粗領域・Scene Prompt・Seed生成導線・実機検証5条件完走） |
| `M1.1 / 3M-1.1` | COMPLETED | Canonical Workflow Wiring & UI SSOT Truth Fix（正本実配線、dimensions方言撤廃、一意ID、Manifest v2、実機配線検証3条件完走） |
| `M2A / 3M-2A` | COMPLETED | Character Spatial Capability Ladder & Control Escalation Gate（左右スワップ因果性実証、Prompt深度実証、3人混成実証、ControlNet不要判定） |
| `M2B / 3M-2B` | NEXT CANDIDATE | Minimum Character & CAST Staging Product UI (Option A: Rough Region + Free Text Prompt) |

## 3. HISTORICAL / SUPERSEDED (過去の参照資料)
過去のPhase指示書や中間計画書は歴史的経緯の参照用であり、次作業の直接指示とはみなさない。

| 文書/群 | 状態 | 扱い |
|---|---|---|
| `CAST_SPEC_V1.md`, `COMPILE_PLAN_V1.md`, `MANGA_SCENE_DATA_CONTRACT.md`, `LORA_ENTRY_V1.md` | EXISTING CONTRACT | M0での旧import互換性照合対象 |
| `reports/PHASE3L_*`, `verification/PHASE3L_*` | HISTORICAL EVIDENCE | Phase 3Lの実装成果（14件PENDING・WF71限界を包含） |
| その他旧Phase reports / verification (Phase 2〜3K) | HISTORICAL EVIDENCE | 必要時のみ個別参照 |
| `../GPTからの指示書/` の旧Phase依頼書・旧中間計画書 | SUPERSEDED STRATEGY | 新戦略と競合するため歴史資料として保持 |
| `../Archive/2026-09-06_pre_astra_replan/` | ARCHIVED SNAPSHOT | 統合前原本のハッシュ保全 |
| `WORKFLOW_INDEX.md`, `DEPENDENCIES.md`, `KNOWN_ISSUES.md` | EXISTING REFERENCE | 古い記述を含む。実装/環境はlive確認 |

※ 本projectには現時点で `TECHNICAL.md` は存在しない。Tegaki本体（`tegaki_work/`）の同名文書やPhase履歴を本環境へ混同しないこと。
