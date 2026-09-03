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
 │   └─ reports/                            # 開発フェーズ完了報告書・検証記録集
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
 │   └─ tegaki_manga_nodes/                 # 独自LoRA記法・Region Editor・Scene/Page Compiler・Mask/Conditioningノード
 ├─ scripts/
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
 ├─ workflows/                              # 漫画制作向けワークフローJSON (9種)
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
- `09_MANGA_REGIONAL_GENERATION_POC.json`: REGION_SPEC/CAST_SPEC動的駆動による漫画コマ・キャラクター実画像生成 (EXPERIMENTAL / POC)
- `10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json`: 4階層モデル（Global/Panel/Local Region/Character）による高度構図制御ハーネス (EXPERIMENTAL / HARNESS)
