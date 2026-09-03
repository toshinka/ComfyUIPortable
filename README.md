# ComfyUI Portable 漫画制作環境 (Tegaki Manga Edition)

Windowsローカル環境に、漫画・イラスト制作向けに特化して構築された **ComfyUI Portable環境** です。
Illustrious / SDXL系モデルを主力とし、構図・ポーズ探索、複数LoRAブレンド、コマ・Region単位のPrompt/LoRA制御、I2I修正、ControlNet構図制御、Wildcards/Dynamic Promptsによるアイデア出しを支援します。

---

## 1. 特徴と設計方針

1. **EasyReforge モデル資産の完全共有 (二重保存ゼロ)**:
   - `E:\EasyReforge` および `E:\Data\Models` に保管されている Checkpoint (97モデル), LoRA (3005ファイル), VAE, ControlNet を読み取り専用で共有。
   - 元のファイル配置やEasyReforge環境を一切改変・複製しません。
2. **Wildcards 共有 & Dynamic Prompts**:
   - EasyReforgeの既存Wildcard (192ファイル) をJunction共有。
   - `__pose__` や `{option A|option B}` などのランダム展開に対応。
3. **直感的な LoRA 記法 (独自Custom Node)**:
   - Prompt欄に `<lora:LoRA名:0.7>` や `<lora:LoRA名:0.8:0.5>` と書くだけで自動的にモデルにパッチを適用。
   - 拡張子省略やサブフォルダ内のLoRA名も自動解決。
4. **漫画制作向け 6大標準ワークフロー**:
   - 基本txt2img、I2I修正、コマ別Regional Prompt、Region別LoRA実験、ControlNet構図拘束、LoRAブレンド探索を完備。
5. **ポータブル & クリーンなGit管理**:
   - 巨大なPython環境、モデル、生成画像は `.gitignore` で除外。
   - 設定、独自コード、ワークフローJSON、ドキュメントのみをGit管理し、他PCへの移行や外部AIレビューを容易にします。

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
 ├─ BUILD_REPORT.md                         # 構築・検証詳細レポート (全20項目)
 ├─ DEPENDENCIES.md                         # パッケージ・ハードウェア環境仕様
 ├─ WORKFLOW_INDEX.md                       # ワークフロー解説
 ├─ KNOWN_ISSUES.md                         # 未解決課題・制限事項
 ├─ RESEARCH_REFERENCES.md                  # 参照リポジトリ・ライセンス
 ├─ GITHUB.TXT                              # 外部AIレビュー用リンク集
 ├─ configs/
 │   └─ extra_model_paths.yaml              # 外部モデルパス定義テンプレート
 ├─ custom_nodes_custom/
 │   └─ tegaki_manga_nodes/                 # 独自LoRA記法・漫画制作ノード
 ├─ scripts/
 │   ├─ generate_workflows.py               # ワークフロー自動生成スクリプト
 │   ├─ test_nodes.py                       # ノード・モデルインポート検証
 │   ├─ test_generation.py                  # 実機txt2img生成検証スクリプト
 │   ├─ test_i2i.py                         # 実機I2Iパイプライン検証スクリプト
 │   └─ test_wildcards.py                   # Wildcard/Dynamic Prompts検証
 ├─ workflows/                              # 漫画制作向けワークフローJSON (6種)
 ├─ python_embeded/                         # [Git除外] Python 3.13 組み込み環境
 └─ ComfyUI/                                # [Git除外] ComfyUI本体 & 外部Custom Nodes
```

---

## 4. ワークフローの使い方

ComfyUIをブラウザで開いた後、画面右上の「Load」または画面上へ `workflows/` フォルダ内の `.json` ファイルをドラッグ＆ドロップしてください。

- `01_BASIC_ILLUSTRIOUS_TXT2IMG.json`: まず最初に試すべき基本生成ワークフロー
- `02_ILLUSTRIOUS_I2I.json`: 生成画像のディテールアップ・修正用
- `03_MANGA_REGIONAL_PROMPT.json`: コマ割り・複数キャラ描き分け用
- `04_REGIONAL_LORA_EXPERIMENT.json`: 領域ごとに別LoRAを適用するRLL先行実験
- `05_CONTROLNET_COMPOSITION.json`: ポーズ・構図の固定
- `06_LORA_MIX_EXPERIMENT.json`: 複数LoRAの配合比率探索
