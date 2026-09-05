# ComfyUI Portable 漫画制作環境 (Tegaki Manga Edition)

Windowsローカル環境に、漫画・イラスト制作向けに特化して構築された **ComfyUI Portable環境** です。
Illustrious / SDXL系モデルを主力とし、構図・ポーズ探索、複数LoRAブレンド、コマ・Region単位のPrompt/LoRA制御、I2I修正、ControlNet構図制御、Wildcards/Dynamic Promptsによるアイデア出し、および最大6コマの視覚的Region Editorを支援します。

---

## 1. 特徴と設計方針

1. **EasyReforge モデル資産の完全共有 (二重保存ゼロ)**:
   - `E:\EasyReforge` および `E:\Data\Models` に保管されている Checkpoint (97モデル), LoRA (3005ファイル), VAE, ControlNet を読み取り専用で共有。
   - 元のファイル配置やEasyReforge環境を一切改変・複製しません。
2. **Wildcards 共有 & Wildcard Organizer (Phase 2強化)**:
   - EasyReforgeの既存Wildcard (192ファイル) をJunction共有。
   - WebUI上でのWildcard検索、ファイル内容プレビュー、Prompt構築に対応。
3. **Tegaki Manga Region Editor (Phase 2新設)**:
   - 最大6コマ (KOMA 1〜6) の視覚的レイアウト編集、コマごとのPrompt管理、スライス (Split H/V)、コマ入れ替え (Swap)、Undo/Redo、およびWorkflow完全復元。
   - `REGION_SPEC` (v1) データ構造によるUIと生成Backendの疎結合化（将来のMCWWや外部GUIにも対応）。
4. **直感的な LoRA 記法 (独自Custom Node)**:
   - Prompt欄に `<lora:LoRA名:0.7>` や `<lora:LoRA名:0.8:0.5>` と書くだけで自動的にモデルにパッチを適用。
   - 拡張子省略やサブフォルダ内のLoRA名も自動解決。
5. **漫画制作向け 7大標準ワークフロー**:
   - 基本txt2img、I2I修正、コマ別Regional Prompt、Region別LoRA実験、ControlNet構図拘束、LoRAブレンド探索、Region Editor UI検証を完備。
6. **ポータブル & クリーンなGit管理**:
   - 巨大なPython環境、モデル、生成画像は `.gitignore` で除外。
   - 設定、独自コード、ワークフローJSON、ドキュメントのみをGit管理。

---

## 2. 起動方法

### 通常起動 (NVIDIA GPU推奨)
`D:\GitHub\tegaki\ComfyUIPortable` に移動し、以下のバッチファイルを実行してください。

```bat
run_nvidia_gpu.bat
```

起動後、ブラウザで以下にアクセスします。
```text
http://127.0.0.1:8188
```

### 高速・低VRAMモード (FP16 accumulation)
```bat
run_nvidia_gpu_fast_fp16_accumulation.bat
```

---

## 3. ディレクトリ構成

```text
D:\GitHub\tegaki\ComfyUIPortable\
 ├─ run_nvidia_gpu.bat                      # 起動バッチ
 ├─ .gitignore                              # Git除外設定
 ├─ README.md                               # 本ドキュメント
 ├─ GITHUB.TXT / GITHUB_ComfyUI.txt         # 外部AIレビュー用リンク集
 ├─ configs/
 │   └─ extra_model_paths.yaml              # 外部モデルパス定義テンプレート
 ├─ docs/                                   # 漫画制作データ契約・仕様書・設計資料集
 │   ├─ MANGA_SCENE_DATA_CONTRACT.md        # 漫画シーンデータ契約総合仕様書 (PAGE/KOMA/CAST)
 │   ├─ CAST_SPEC_V1.md                     # キャラクターマスター定義仕様書 (CAST_SPEC v1)
 │   ├─ COMPILE_PLAN_V1.md                  # コマ実行計画仕様書 (COMPILE_PLAN v1)
 │   ├─ LORA_ENTRY_V1.md                    # Canonical LoRA Entry仕様書 (v1)
 │   ├─ KNOWN_ISSUES.md                     # 既知の課題・解決済み履歴
 │   ├─ WORKFLOW_INDEX.md                   # ワークフロー解説・索引
 │   ├─ DEPENDENCIES.md                     # パッケージ・ハードウェア環境仕様
 │   ├─ RESEARCH_REFERENCES.md              # 参照リポジトリ・ライセンス
 │   ├─ CUSTOM_NODE_MANIFEST.md             # 外部Custom Nodeコミット追跡
 │   ├─ verification/                           # 正準検証マニフェスト (PHASE3G / PHASE3H / PHASE3I / PHASE3J / PHASE3J.1)
 │   └─ reports/                            # 開発フェーズ完了報告書・検証記録集
 │       ├─ PHASE3J_1_CHARACTER_PROMPT_AND_REGION_ISOLATION_REPORT.md
 │       ├─ PHASE3J_SEMANTIC_PRESENCE_AND_ADAPTIVE_GUIDE_REPORT.md
 │       ├─ PHASE3I_2_REFERENCE_FAST_CAUSAL_AND_PER_REGION_CONTROL_REPORT.md
 │       ├─ PHASE3I_1_CONTROLNET_VISUAL_TRUTH_AND_INTERACTION_REPORT.md
 │       ├─ PHASE3I_CONTROLNET_LAYOUT_ASSIST_REPORT.md
 │       ├─ PHASE3H_SUBJECT_EXCLUSIVITY_AND_AUTHORING_CAUSALITY_REPORT.md
 │       ├─ PHASE3G_CANONICAL_VERIFICATION_AND_FAST_MODE_REPORT.md
 │       ├─ PHASE3F_ZERO_TOUCH_AND_PROGRESSIVE_AUTHORING_REPORT.md
 │       ├─ PHASE3E_IMPACT_MANGA_REINTEGRATION_AND_PROGRESSIVE_AUTHORING_REPORT.md
 │       ├─ PHASE3D_2_REGIONAL_SEMANTICS_FIRST_REPORT.md
 │       ├─ PHASE3D_1_REGIONAL_LOCALITY_AND_CAST_MASTER_REPORT.md
 │       ├─ PHASE3D_VARIABLE_N_REGION_MANGA_INTEGRATION_REPORT.md
 │       ├─ PHASE3C_1_2_FRONTEND_BACKEND_GEOMETRY_PARITY_REPORT.md
 │       ├─ PHASE3C_1_1_PANEL_TOPOLOGY_AND_CONTROLNET_FUSION_REPORT.md
 │       ├─ PHASE3C_1_SEMANTIC_REGION_AND_PANEL_LAYOUT_REPORT.md
 │       ├─ PHASE3C_TWO_REGION_COUPLE_ORACLE_REPORT.md
 │       ├─ PHASE3B_1_1_WORKFLOW_COMPATIBILITY_HOTFIX_REPORT.md
 │       ├─ PHASE3B_1_REGIONAL_CONTROL_EXPANSION_REPORT.md
 │       ├─ PHASE3B_END_TO_END_REGIONAL_GENERATION_REPORT.md
 │       ├─ PHASE3A_1_SCENE_CONTRACT_HARDENING_REPORT.md
 │       ├─ PHASE3A_SCENE_DATA_CONTRACT_REPORT.md
 │       ├─ PHASE2_1_1_REGRESSION_FIX_REPORT.md
 │       ├─ PHASE2_1_STABILIZATION_REPORT.md
 │       ├─ PHASE2_MRP_UI_REPORT.md
 │       ├─ BUILD_REPORT.md
 │       └─ PHASE2_1_UI_TEST_CHECKLIST.md
 ├─ custom_nodes_custom/
 │   └─ tegaki_manga_nodes/                 # 独自LoRA記法・Region Editor・Scene/Page Compiler・Mask/Conditioning・Panel Layout API・Cast Masterノード
 ├─ scripts/
 │   ├─ test_phase3d1_character_locality.py # Phase 3D.1 人物A/B差分測定・5コマ実画像生成スクリプト
 │   ├─ test_phase3d1_panel_locality.py     # Phase 3D.1 コマ別マルチゾーン局所性・CN ON/OFF診断スクリプト
 │   ├─ test_canvas_contract_match.py       # Phase 3D.1 Canvas寸法一致Fail-Closed単体テスト
 │   ├─ test_cast_master_state.py           # Phase 3D.1 Cast Master状態遷移・不変ID単体テスト
 │   ├─ test_cast_binding_references.py     # Phase 3D.1 参照中キャラ削除防御・無効化スキップ単体テスト
 │   ├─ generate_workflow_17.py             # Phase 3D.1 Workflow 17自動生成スクリプト
 │   ├─ test_phase3d_variable_region_generation.py # Phase 3D 実機N領域・幾何融合生成検証スクリプト
 │   ├─ test_layout_aware_conditioning.py   # Phase 3D 4階層Conditioning結合単体テスト
 │   ├─ test_layout_aware_masks.py          # Phase 3D 多角形パネル/人物BBox投影マスク単体テスト
 │   ├─ test_layout_region_mapping.py       # Phase 3D 幾何・意味シーン決定論的Bridge単体テスト
 │   ├─ test_panel_layout_http_routes.py    # Phase 3D-0 実稼働HTTP REST API検証
 │   ├─ test_panel_layout_api_routes.py     # Phase 3C.1.2 Panel Layout REST API単体テスト
 │   ├─ test_panel_layout_frontend_backend_parity.py # Phase 3C.1.2 Frontend/Backend Splitパリティテスト
 │   ├─ test_panel_layout_drag_validation.py# Phase 3C.1.2 トランザクショナルドラッグ・ロールバック検証
 │   ├─ test_panel_layout_split_operations.py # Phase 3C.1.1/3C.1.2 一般分割幾何アルゴリズムテスト
 │   ├─ test_panel_layout_topology.py       # Phase 3C.1.1/3C.1.2 平面分割トポロジー契約テスト
 │   ├─ test_panel_layout_fusion_generation.py # Phase 3C.1.1 実機ControlNet融合生成スクリプト
 │   ├─ test_two_region_couple_editor.py    # Phase 3C.1 Two Regionエディター幾何テスト
 │   ├─ test_two_region_oracle_generation.py# Phase 3C 実機Two Region A/B生成検証スクリプト
 │   ├─ test_regional_control_expansion_generation.py # Phase 3B.1 実機A/B生成検証スクリプト
 │   ├─ test_regional_control_expansion.py  # Phase 3B.1 4階層統合・Mask投影・Conditioningテスト
 │   ├─ test_local_region_spec.py           # Phase 3B.1 LOCAL_REGIONデータ契約単体テスト
 │   ├─ test_regional_poc_generation.py     # Phase 3B 実機A/B生成検証スクリプト
 │   ├─ test_page_compile_plan.py           # PAGE_COMPILE_PLAN & Mask投影単体テスト
 │   ├─ test_conditioning_builder.py        # Manga Conditioning Builder単体テスト
 │   ├─ test_scene_compiler.py              # Manga Scene Compiler統合実行計画検証
 │   ├─ test_cast_spec.py                   # CAST_SPEC & Bindingバリデーション検証
 │   ├─ test_region_spec.py                 # Region Editor単体ロジック・バリデーション検証
 │   ├─ test_region_state_transitions.py    # Region Editor状態遷移・回帰テストスイート
 │   ├─ test_region_editor_backend_api.py   # Region Editor バックエンド実行API検証
 │   ├─ test_runtime_source_identity.py     # Git正本・実行時コード同一性検証
 │   ├─ verify_wildcard_patch.py            # Wildcardパッチ適用診断
 │   ├─ generate_workflows.py               # ワークフロー自動生成スクリプト
 │   ├─ test_nodes.py                       # ノード・モデルインポート検証
 │   ├─ test_generation.py                  # 実機txt2img生成検証スクリプト
 │   ├─ test_i2i.py                         # 実機I2Iパイプライン検証スクリプト
 │   └─ test_wildcards.py                   # Wildcard/Dynamic Prompts検証
 ├─ patches/                                # 外部Custom Node向けローカルパッチ集
 ├─ workflows/                              # 漫画制作向けワークフローJSON (53種)
 ├─ python_embeded/                         # [Git除外] Python 3.13 組み込み環境
 └─ ComfyUI/                                # [Git除外] ComfyUI本体 & 外部Custom Nodes
```

---

## 4. ワークフローの使い方

ComfyUIをブラウザで開いた後、画面右上の「Load」または画面上へ `workflows/` フォルダ内の `.json` ファイルをドラッグ＆ドロップしてください。

- `01_BASIC_ILLUSTRIOUS_TXT2IMG.json`: まず最初に試すべき基本生成ワークフロー (STABLE)
- `02_ILLUSTRIOUS_I2I.json`: 生成画像のディテールアップ・修正用 (STABLE)
- `03_MANGA_REGIONAL_PROMPT.json`: コマ割り・複数キャラ描き分け用 (固定2分割配線 / STABLE)
- `04_REGIONAL_LORA_EXPERIMENT.json`: 領域別LoRA接続構造の試験用・未完成 (EXPERIMENTAL / NOT YET REGIONAL)
- `05_CONTROLNET_COMPOSITION.json`: ポーズ・構図の固定 (EXPERIMENTAL)
- `06_LORA_MIX_EXPERIMENT.json`: 複数LoRAの配合比率探索 (STABLE)
- `07_MANGA_REGION_EDITOR_UI_TEST.json`: 最大6コマ視覚的Region Editor UI操作・プレビュー検証ハーネス (DEV / TEST)
- `08_MANGA_SCENE_CONTRACT_TEST.json`: Manga Scene Contract（PAGE/CAST/Binding）検査・可視化ハーネス (DEV / TEST)
- `09_MANGA_REGIONAL_GENERATION_POC.json`: REGION_SPEC/CAST_SPEC動的駆動による漫画コマ・キャラクター実画像生成 (Zero-Touch Verified / STABLE POC)
- `10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json`: 4階層モデル（Global/Panel/Local Region/Character）による高度構図制御ハーネス (Zero-Touch Verified / EXPERIMENTAL HARNESS)
- `11_TWO_REGION_CORE_COUPLE_ORACLE.json`: 2領域専用Rectangle EditorとCore Masked Conditioningによる最短・最速Regional検証オラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `12_TWO_REGION_IMPACT_COUPLE_ORACLE.json`: Impact Pack RegionalSampler連携によるサンプラー分離方式検証オラクル (Zero-Touch Verified / EXPERIMENTAL BACKEND ORACLE)
- `13_TWO_REGION_CONTROLNET_LAYOUT_AUX.json`: 矩形外枠線（Panel Outline）によるControlNet構図・境界誘導補助オラクル (Zero-Touch Verified / EXPERIMENTAL AUX)
- `14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json`: 漫画コマ割り専用の独立幾何エディター（Shared-Vertex Mesh）によるコマ分割・共有頂点ドラッグ変形・ControlNetガイド画像検証 (Zero-Touch Verified / DEVELOPMENT TOOL)
- `15_MANGA_PANEL_LAYOUT_CONTROLNET_FUSION_ORACLE.json`: 平面分割（Planar Subdivision）コマ割りControlNetと上段コマ内Semantic Overlap（2人物）の構図統合オラクル (Zero-Touch Verified / EXPERIMENTAL FUSION)
- `16_MANGA_VARIABLE_N_REGION_LAYOUT_FUSION_POC.json`: 3〜6コマ可変多角形コマ割りと意味シーン計画（人物・ローカル背景）のControlNet統合漫画生成POC (Zero-Touch Verified / STABLE POC)
- `17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json`: 登場人物マスター管理（`TegakiMangaCastMaster`）・同一コマ内 Semantic Overlap・局所性検証オラクル (Zero-Touch Verified / STABLE ORACLE)
- `18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json`: 単一領域5位置配置・Core vs Impact比較オラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json`: 2領域意味分離・幾何スワップ・Semantic Overlapオラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json`: 意味領域幾何外枠線ControlNet補助評価オラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `21_MANGA_IMPACT_RECURRENT_CAST_POC.json`: 4コマ漫画反復出演（Recurrent Cast）・Impact N領域エンジン実証 (Zero-Touch Verified / STABLE POC)
- `22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json`: 単一コマ内複数シーン（Split Scene）・同一キャスト共存意地悪オラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json`: 段階的オーサリング（01 Global → 02 Cast → 03 Content → 04 Layout → 05 Staging → 06 Generate）4コマ標準ワークフロー (Zero-Touch Verified / STABLE)
- `24_SINGLE_PANEL_PROGRESSIVE_SUBSCENE_IMPACT.json`: 段階的開示（Progressive Disclosure）SubScene v1 オラクル (Zero-Touch Verified / EXPERIMENTAL ORACLE)
- `25_VERIFY_SINGLE_A_TOP_LEFT.json`: 正準空間オラクル (単一犬・左上配置 / Zero-Touch Verified)
- `26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json`: 正準空間オラクル (単一犬・右下配置 / Zero-Touch Verified)
- `27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json`: 正準意味結合オラクル (犬左・猫右 / Zero-Touch Verified)
- `28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json`: 正準空間スワップオラクル (犬右・猫左 / Zero-Touch Verified)
- `29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE.json`: 正準排他オラクル (犬左上・Exclusive Base 背景人物完全抑制 / Zero-Touch Verified)
- `30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE.json`: 正準排他オラクル (犬右下・Exclusive Base 背景人物完全抑制・98%内包 / Zero-Touch Verified)
- `31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE.json`: 正準排他・意味結合オラクル (犬左・猫右・フキダシ/岩完全排除 / Zero-Touch Verified)
- `32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE.json`: 正準排他・空間スワップオラクル (犬右・猫左・背景人物ゼロ / Zero-Touch Verified)
- `33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT.json`: 本番オーサリング因果性オラクル (Alice左・Bob右・校庭1コマ・UI幾何駆動 / Zero-Touch Verified)
- `34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT.json`: 本番オーサリング因果スワップオラクル (Alice右・Bob左・UI幾何スワップ駆動 / Zero-Touch Verified)
- `35_VERIFY_CONTROLNET_ANYTEST_BASELINE.json`: ControlNet 基礎検証オラクル (単一白犬・Wireframeガイド・AnyTest v4 / Zero-Touch Verified)
- `36_VERIFY_CONTROLNET_SCALE_LOCK_SINGLE_CHARACTER.json`: 単一人物スケール拘束オラクル (Alice縦長肖像・Mannequin Capsuleガイド / Zero-Touch Verified)
- `37_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT_CN_ASSIST.json`: 本番オーサリング ControlNet 補助オラクル (Alice左・Bob右・マネキン拘束 / Zero-Touch Verified)
- `38_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT_CN_ASSIST.json`: 本番オーサリング ControlNet 補助スワップオラクル (Bob左・Alice右・空間反転拘束 / Zero-Touch Verified)
- `39_VERIFY_FAST_DRAFT_12_CONTROLNET_REGRESSION.json`: 高速ドラフト ControlNet 回帰オラクル (Hyper-SDXL 12-Step・シルエット完全拘束・~30s生成 / Zero-Touch Verified)
- `40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json`: ControlNet オーサリング参照ペアオラクル (Alice左・Bob右・Euler 20s・Base-only CN伝播 / Zero-Touch Verified)
- `41_VERIFY_CN_STRENGTH_SANITY.json`: ControlNet 強度・スケジュール健全性オラクル (CN 0.50/0.60 緩和・過拘束抑制評価 / Zero-Touch Verified)
- `42_VERIFY_REGIONAL_CN_PROPAGATION_AB.json`: リージョナル ControlNet 伝播 A/B オラクル (propagate_controlnet_to_regions: True プロトタイプ / Zero-Touch Verified)
- `43_VERIFY_BROWSER_STAGING_CAUSALITY.json`: ブラウザポインタ演出因果性オラクル (Alice右ドラッグ移動・Fast Draft 12同期・Guide SSOT実証 / Zero-Touch Verified)
- `44_VERIFY_NATIVE20_BASEONLY_ZERO.json`: 初期ベースステップ切り分けオラクル (base_only_steps=0 有害性実証・純粋ノイズ化 / Zero-Touch Verified)
- `45_VERIFY_NATIVE12_CONTROL.json`: Native 短ステップ因果対照オラクル (Native 12s・CFG 6.0・ステップ短縮単独の効果単離 / Zero-Touch Verified)
- `46_VERIFY_HYPER12_CAUSAL_CONTROL.json`: Hyper-12 因果対照オラクル (Hyper-SDXL 12s・Alice左/Bob右・配置幾何との相互作用実証 / Zero-Touch Verified)
- `47_VERIFY_PER_REGION_HINT_ATTENUATED.json`: キャラクター個別 Hint 減衰オラクル (per_region_hint 0.35・マネキン線画複写の根絶実証 / Zero-Touch Verified)

### Tag Complete (Phase 3B.1.1 導入)
- 全テキスト入力欄（Region Editor Prompt、CLIPTextEncode 等）で、Danbooru 14万タグ、LoRA名、Embeddingのリアルタイム自動補完（Tag Complete）が完全動作します（`ComfyUI-Custom-Scripts` 統合）。

### Semantic Region Hardening & Panel Topology ControlNet Fusion (Phase 3C / 3C.1 / 3C.1.1 成果)
- **意味領域（Semantic Region）とコマ割り幾何（Panel Layout）の完全分離と融合**:
  - **Semantic Region**: 2領域（Region A / Region B）に特化した最小データ契約 `TWO_REGION_SPEC` (v1) と `TegakiTwoRegionCoupleEditor`（ドラッグ移動・リサイズ・選択・作成完備）。演技・対話構図のため **「Semantic Overlap（重なり前提）」** を基本思想とし、局所性比率 4.52x の高い空間分離性を実証。
  - **Panel Layout Topology**: 漫画コマ割り専用契約 `PANEL_LAYOUT_SPEC` (v1) を **Planar Subdivision（平面分割）** として硬化。自己交差（bow-tie 検出）、Winding CCW 正規化、Edge Incidence（外枠1/内枠2）、T-Junction 検出・排除、面積保存則、Gap/Overlap 診断（0.0%）を完全実装。
  - **Generic Split by Line**: Sutherland-Hodgman 半平面クリッピングによる H/V/Diagonal 4方向分割、交点頂点の全メッシュ伝播（T-Junction 根本防止）を完備。
  - **ControlNet Fusion 実機実証 (Workflow 15)**: RTX 4070 実機において、ControlNet 強度 0.60 で明瞭なコマ枠線形成（Edge Response: 0.1099, +222%）と上段コマ内での自然な 2 人物演技（Semantic Overlap）の完全共存を実証。

### Frontend / Backend Geometry Parity & Topology Contract Closure (Phase 3C.1.2 成果)
- **Frontend / Backend Split 操作の Single Source of Truth (SSOT) 統合**:
  - フロントエンドの Split ボタン（H, V, /, \）を Python バックエンド REST API (`POST /tegaki/panel-layout/split`) 呼び出しへ完全一本化。
  - フロントエンド独自の手作業 bbox スライスロジックを撤廃し、Backend の Sutherland-Hodgman 多角形クリッピングと新設頂点伝播によるトポロジー整合性をブラウザ上でも 100% 保証。
- **ドラッグ操作の完全トランザクション化 & ロールバック保証**:
  - `committedSpec`（確定状態）と `previewCandidateSpec`（プレビュー候補）を物理分離。
  - ドラッグ中は Canvas 描画のみを candidate で更新し、ComfyUI の widget 値を非破壊に保護。
  - `mouseup` 時に幾何事前検査および Backend API (`POST /tegaki/panel-layout/validate`) を実行。自己交差・面積不整合・境界逸脱等のトポロジー違反発生時は即座に `committedSpec` へロールバックし、不整合状態の永続化をゼロ化。
- **幾何契約（Planar Subdivision Contract）の完全硬化**:
  - 厳格 Frame 検証（finite float, bool 拒絶, 境界整合性）、頂点 Frame 包含チェック、重複座標排除、孤立頂点排除、厳格外枠 Incidence（内部 Gap 排除）、ペアワイズ多角形重なり判定（Exact Pairwise Overlap Check）、面積保存許容誤差の引き締め（0.001）を完全達成。
  - テストスイート 17本（単体・結合・パリティ・回帰）すべてで 100% PASS を達成。

### Variable N-Region Manga Integration & Layout-Aware Semantic Fusion (Phase 3D 成果)
- **コマ割り幾何（PANEL_LAYOUT_SPEC）と意味シーン計画（PAGE_COMPILE_PLAN）の完全統合**:
  - **純粋関数 Bridge (`layout_region_bridge.py`)**: 物理幾何と意味シーンのデータ契約を混同・汚染することなく、Active KOMA と Layout Panel を決定論的に 1:1 対応付け。パネル数不一致時は Fail-Closed（`ValueError`）で安全停止。
  - **多角形パネルマスク & 人物 BBox 相対投影 (`layout_aware_mask_builder.py`)**: パネル多角形マスクの正確な二値ラスタライズ、コマ内相対人物 BBox の大域キャンバス投影および親パネル多角形による厳格クリッピング（枠外へのプロンプト漏れを完全防止）。同一コマ内での人物同士の Semantic Overlap は許容して豊かな会話・演技表現を保証。
  - **4階層 Layout-Aware Conditioning (`layout_aware_conditioning.py`)**: 新設ノード `TegakiMangaLayoutAwareConditioningBuilder` により、Global / Panel Polygon / Local Region / Character の 4 階層プロンプトを階層結合。
  - **ControlNet 幾何共有 & 実機画像生成 (Workflow 16)**: RTX 4070 実機において、ControlNet 強度 0.60 によるシャープなコマ枠線形成（Edge Response: 0.1341 vs OFF: 0.1052, +27.5%）と各コマ個別プロンプト、人物アリスの髪色局所制御を実証。

### Regional Locality Validation & Character / CAST Master UI Foundation (Phase 3D.1 成果)
- **局所性検証の是正とマルチゾーン診断**:
  - 単一比率 PASS 判定（0.6614 の過大解釈）を撤退・是正し、多角形コマ・他コマ・外枠・人物マスク・同一コマ背景を分離したマルチゾーン診断メトリクスを確立。
  - KOMA 2 A/B（廊下 vs コンビニ）で Target/Other 比率 1.04〜1.08 を記録。ControlNet ON (0.60) / OFF (0.00) 比較により、ControlNet がコマ内意味変化を阻害しないことを実証。
  - KOMA 1 において Alice & Bob の Semantic Overlap（37.78% 重複）を維持しながら、Alice 髪色 A/B で同一コマ背景比 4.02倍の強い人物局所変化を実証。
  - 変則 5 コマレイアウトでの実機 SDXL 画像生成（18.1s）を完了し、5コマ漫画生成の成立性を証明。
  - Core Conditioning は追加拡張なしで動く基盤として極めて有用（`PARTIAL` 判定）であり、次 Phase での Impact RegionalSampler（Attention Masking 方式）比較へ向けた客観的ベースラインを確立。
- **Canvas 寸法一致の Fail-Closed 化**:
  - `PAGE_COMPILE_PLAN.canvas == PANEL_LAYOUT_SPEC.canvas` を Bridge で厳格検査し、寸法不一致時は直ちに `ValueError` で停止。
- **Character / CAST Master 契約と UI Foundation**:
  - `CAST_SPEC` (v1) を SSOT として管理する新設ノード `TegakiMangaCastMaster` およびフロントエンド拡張 `cast_master_editor.js` を実装。
  - 不変 ID（Immutable ID）、アクティブ KOMA 参照中キャラの誤削除 Fail-Closed 防御、無効化キャラの安全スキップ、出演コマ逆引きバッジ表示、未適用の人物 LoRA 計画表示（`[NOT YET SPATIALLY APPLIED - Plan Only]`）を完備。
  - 本番ワークフロー `17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json` を整備し、Zero-Touch 100% 稼働を実証。

### Zero-Touch Workflow Parity & Progressive Authoring UI (Phase 3F 成果)
- **Zero-Touch 互換性の確立 (3F-0 Schema Closure)**:
  - ComfyUI Web フロントエンドが `seed` / `noise_seed` の直後に `control_after_generate` コンボウィジェットを自動挿入する仕様を完全解明。
  - `RegionalSampler` の保存ウィジェット配列を 12 要素に整合（`"fixed"` 明示挿入）し、ウィジェット位置ずれによる型・範囲バリデーションエラーを完全根絶。
  - `ToBasicPipe` の `clip` 必須ソケット配線を全保存ワークフローで完全接続。
  - 稼働中 ComfyUI の `/object_info` を正本とする自動テスト `scripts/test_live_external_node_schema.py` および全主要ワークフローの互換性テスト `scripts/test_saved_workflow_live_compatibility.py`（全 8 ワークフロー 100% PASS）を整備。
- **段階的オーサリング UI (Progressive Authoring Pipeline)**:
  - ユーザーの制作心理に即した 6 段階パイプライン `01 GLOBAL -> 02 CAST -> 03 PANEL CONTENT -> 04 PANEL LAYOUT -> 05 CHARACTER STAGING -> 06 GENERATE` を構築。
  - `TegakiMangaPanelContentEditor`: コマ演出プロンプトとキャストの出演（Attendance）・演技（Acting）をチェックボックス等で直感的に一括管理。
  - `TegakiMangaCharacterStagingEditor`: 各コマのキャラクター立ち位置矩形（BBox）のドラッグ＆リサイズ、および Canvas 枠線と人物配置のリアルタイムカラーテンソルプレビュー出力を実装。
  - 内部エンジン（Impact Adapter + ToBasicPipe + RegionalSampler）を `INTERNAL ENGINE / DO NOT TOUCH` として視覚的に隔離。
### Canonical Spatial Verification & Fast Mode (Phase 3G 成果)
- **正準空間オラクル (Canonical Spatial Verification Set)**:
  - 方位語（left/right等）を一切含まないプロンプトと同一Seed（42）のもと、領域幾何学（Region Geometry）のみで被写体位置および左右反転が完全に成立することを実証（WF25〜28）。
  - Impact Regional Sampler と ToBasicPipe 接続の 100% Zero-Touch 実行を実機確認。
- **Hyper-SD 12-Step Fast Mode**:
  - Reference（20 steps, CFG 7.0）の品質を維持しながら、12 steps, CFG 6.0 で約 1.7x の高速生成を達成。Fast 8-step はアーティファクト多発のため安全に却下。

### Subject Exclusivity & Authoring Causality (Phase 3H 成果)
- **Base / Global プロンプトスコープ分離と背景人物抑制 (Exclusive Base)**:
  - Illustrious SDXL のモデル学習傾向による意図しない背景美少女人物の発生（Figure Leakage）を解明。
  - プロンプトを Global Style / Exclusive Base Scene / Regional Subjects の 3 責務へ分離し、Base Negative で人物・動物を厳格に抑止することで、背景人物発生を 100% 根絶（WF29〜32）。
- **3 パネル診断コンタクトシート (Target Map | Output | Evaluation Overlay)**:
  - 領域幾何学と生成画像、および半透明カラーオーバーレイを結合した診断画像（Sheet D, E, F, G）を自動生成し、被写体内包率・局所重心・境界精度を客観評価。
- **本番オーサリング因果性実証 (Production Staging Causality)**:
  - 段階的オーサリングチェーン（Cast → Content → Layout → Staging → Page Compiler → Impact Regional Adapter）において、Character Staging UI の幾何変更のみで Alice と Bob の位置が因果的に完全反転することを実証（WF33, WF34）。
- **Generation Profile 契約**:
  - `custom_nodes_custom/tegaki_manga_nodes/generation_profile.py` を整備し、品質基準正本（Reference 20-step）と高速下描き（Fast Draft 12-step）の切り替え契約を確立。
- **ControlNet Assist Decision Gate**:
  - Case B 判定（領域による左右位置誘導は成立するが、厳格なスケール内包・シルエット拘束には補助が必要）が確定し、次期 Phase 3I での ControlNet 構図・ポーズ補助導入を決定。

### Character Prompt Contract Repair & Region Isolation Closure (Phase 3J.1 成果)
- **Canonical CAST / Binding プロンプト正本契約の修復**:
  - キャラクターマスター正本を `prompt` / `negative_prompt`、バインディングを `prompt_override` / `negative_prompt_override` へ厳格化。
  - マイグレーションフォールバックおよび `make_canonical_character` / `make_character_binding` ヘルパーを新設し、空文字プロンプトによる背景テキストフォールバックを完全根絶。
- **Compile & Impact キャラクタープロンプト正本 Gate**:
  - `PAGE_COMPILE_PLAN` および `IMPACT_REGION_PLAN` へのプロンプト伝播を自動テストで保証（8/8 PASS）。
  - `character_prompt_mode: standalone` を採用し、キャラクター領域への背景テキスト混入を遮断。
- **コマ背景マスクの穴あき減算 (Remainder Mask Mode)**:
  - `remainder_mask_mode = True` により、コマ背景サンプラーがキャラクター配置矩形を上書き・塗り潰す問題を完全解決。
  - マスク診断（`Phase3J1_Mask_Diagnostic.png`）により、背景とキャラクターの重なり（Intersection = 0）を幾何学的に証明。
- **Global ガイドの枠線交絡排除**:
  - `include_panel_border = False`、`include_character_bbox_outline = False` により、ControlNet による窓・格子・ドア枠幻覚を根絶。
- **単一人物左右配置 & 2人物空間入替の実証 (Workflows 54〜59)**:
  - 単一人物 4/4 PASS（Alice L, Alice R, Bob L, Bob R）。
  - 2人物左右分離および空間入替 2/2 PASS（WF58, WF59）。プロンプト内に位置語彙を含めず BBox 幾何のみで Alice / Bob の配置が決定論的に反転。
- **Operational Authoring Profile 昇格**:
  - Hyper12（12 steps, CFG 6.0, 22〜30s）を正式オーサリングプロファイルへ昇格。Native20 との等価性を実証。





