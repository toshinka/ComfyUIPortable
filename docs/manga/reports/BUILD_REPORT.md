# BUILD_REPORT.md — ComfyUI Portable 漫画制作環境 構築報告書

**作成日時**: 2026-09-03 10:28 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  

---

## 1. 実施した作業
1. **ディレクトリ構造とGit除外設定の整備**:
   - `ComfyUIPortable/.gitignore` を新規作成し、巨大バイナリ（Python環境、モデル、キャッシュ、生成画像等）を厳格に除外。
   - Git管理対象（独自コード、Workflow JSON、設定テンプレート、検証スクリプト、各種ドキュメント）の枠組みを初期化。
2. **ComfyUI Portable 本体の配置**:
   - ローカルの公式ポータブル基盤（Python 3.13.14 embeded, PyTorch 2.13.0+cu130）を `D:\GitHub\tegaki\ComfyUIPortable` 配下にクリーン展開。
   - Minimax H3等の巨大モデル（約50GB）を除外し、漫画制作・Illustriousに特化した563MBの本体コードを配置。
3. **EasyReforge モデル資産・Wildcard共有**:
   - `ComfyUI/extra_model_paths.yaml` および `configs/extra_model_paths.yaml` を作成。
   - `E:\Data\Models` および `E:\EasyReforge\Model` 配下の Checkpoints (97モデル), LoRA (3005ファイル), VAE (8種), ControlNet (6種) を二重保存・改変なしで完全共有。
   - `ComfyUI/wildcards` に `E:\Data\Packages\forge-neo\extensions\sd-dynamic-prompts\wildcards` へのジャンクションを作成（192ファイル共有）。
4. **漫画制作向け Custom Node の選定と導入**:
   - `ComfyUI-Impact-Pack` (Regional Sampler, BBox/Mask)
   - `ComfyUI-Inspire-Pack` (Regional LoRA, LoRA Block Weight)
   - `ComfyUI-Advanced-ControlNet` (ステップ開始/終了・重み制御)
   - `comfyui-dynamicprompts` (Wildcard & 構文展開)
   - `ComfyUI-Manager`, `rgthree-comfy`, `ComfyUI-Easy-Use`
   - 独自ノード `tegaki_manga_nodes` (`TegakiLoraPromptLoader`, `TegakiLoraStackToPrompt`) の開発・導入。
5. **漫画制作向け Workflow 6種類の設計と自動生成**:
   - txt2img, I2I, Regional Prompt, Regional LoRA, ControlNet, LoRA Mix の各JSONを生成。
6. **実機動作・推論テストの実施**:
   - ComfyUIサーバー起動確認、モデル・LoRA認識確認、txt2img生成（RTX 4070推論）、I2I再生成、Wildcards構文展開を全て実機検証。

---

## 2. 新規作成ファイル
- `.gitignore` (巨大バイナリ除外ルール)
- `README.md` (環境概要と起動手順)
- `BUILD_REPORT.md` (本報告書)
- `DEPENDENCIES.md` (環境・パッケージ仕様)
- `WORKFLOW_INDEX.md` (作成ワークフロー解説)
- `KNOWN_ISSUES.md` (既知の課題・制限)
- `RESEARCH_REFERENCES.md` (外部資産・参照リポジトリ)
- `GITHUB.TXT` (外部AIレビュー用入口ファイル)
- `configs/extra_model_paths.yaml` (モデル共有設定テンプレート)
- `custom_nodes_custom/tegaki_manga_nodes/__init__.py`
- `custom_nodes_custom/tegaki_manga_nodes/lora_loader.py` (LoRA記法パーサー＆ローダー)
- `scripts/generate_workflows.py` (ワークフロー生成スクリプト)
- `scripts/test_nodes.py` (ノード・モデル認識テスト)
- `scripts/test_generation.py` (実機txt2imgテストスクリプト)
- `scripts/test_i2i.py` (実機I2Iテストスクリプト)
- `scripts/test_wildcards.py` (Wildcard展開テストスクリプト)
- `workflows/01_BASIC_ILLUSTRIOUS_TXT2IMG.json`
- `workflows/02_ILLUSTRIOUS_I2I.json`
- `workflows/03_MANGA_REGIONAL_PROMPT.json`
- `workflows/04_REGIONAL_LORA_EXPERIMENT.json`
- `workflows/05_CONTROLNET_COMPOSITION.json`
- `workflows/06_LORA_MIX_EXPERIMENT.json`

---

## 3. 変更ファイル
- なし（既存の `tegaki` プロジェクト本体ソースおよび `E:\EasyReforge` 側ファイルは一切変更していません）。

---

## 4. インストールしたCustom Node
1. `ComfyUI-Impact-Pack`
2. `ComfyUI-Inspire-Pack`
3. `ComfyUI-Advanced-ControlNet`
4. `comfyui-dynamicprompts`
5. `ComfyUI-Manager`
6. `rgthree-comfy`
7. `ComfyUI-Easy-Use`
8. `tegaki_manga_nodes` (独自実装)

---

## 5. 各Custom NodeのGitHub URL
- ComfyUI-Impact-Pack: `https://github.com/ltdrdata/ComfyUI-Impact-Pack`
- ComfyUI-Inspire-Pack: `https://github.com/ltdrdata/ComfyUI-Inspire-Pack`
- ComfyUI-Advanced-ControlNet: `https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet`
- comfyui-dynamicprompts: `https://github.com/adieyal/comfyui-dynamicprompts`
- ComfyUI-Manager: `https://github.com/ltdrdata/ComfyUI-Manager`
- rgthree-comfy: `https://github.com/rgthree/rgthree-comfy`
- ComfyUI-Easy-Use: `https://github.com/yolain/ComfyUI-Easy-Use`

---

## 6. 利用したWorkflowのURL
- ComfyUI公式標準ノード仕様およびImpact Pack公式ドキュメントに準拠し、新規設計・自動生成。

---

## 7. EasyReforgeから共有したディレクトリ
- `E:\Data\Models\StableDiffusion` / `E:\EasyReforge\Model\Stable-diffusion`
- `D:\Models\Lora` / `E:\EasyReforge\Model\Lora`
- `E:\Data\Models\VAE` / `E:\EasyReforge\Model\VAE`
- `E:\Data\Models\ControlNet` / `E:\EasyReforge\Model\ControlNet`
- `E:\Data\Models\Embeddings`
- `E:\Data\Models\ESRGAN` / `E:\EasyReforge\Model\ESRGAN`
- `E:\Data\Packages\forge-neo\extensions\sd-dynamic-prompts\wildcards`

---

## 8. symbolic link / junction / external path設定
- **External Path設定**: `ComfyUI/extra_model_paths.yaml` (Checkpoints, LoRA, VAE, ControlNet, Embeddings, UpscaleModels)
- **Junction**:
  - `ComfyUI\wildcards` -> `E:\Data\Packages\forge-neo\extensions\sd-dynamic-prompts\wildcards`
  - `ComfyUI\custom_nodes\tegaki_manga_nodes` -> `D:\GitHub\tegaki\ComfyUIPortable\custom_nodes_custom\tegaki_manga_nodes`

---

## 9. 動作確認したcheckpoint
- `♃CN_Skeb\waiIllustriousSDXL_v170.safetensors` (Illustrious SDXL v1.70, 6.46GB)

---

## 10. 動作確認したLoRA
- `!!!Ani\Ani0H\2000s_Moe_Anime__Style__Illustrious_SDXL-000033.safetensors`
  (`<lora:2000s_Moe_Anime__Style__Illustrious_SDXL-000033:0.7>` 構文で自動解決確認)

---

## 11. Wildcard互換性
- EasyReforgeの `sd-dynamic-prompts` 用Wildcardファイル192件をそのまま認識。
- `__AM_baseQua__` などの呼び出しで、詳細な漫画スタイル・インク線・コマ割りプロンプトが正常に展開されることを確認。

---

## 12. Dynamic Prompt動作
- `{option A|option B|option C}` のランダムサンプリング動作を確認。

---

## 13. txt2imgテスト結果
- **ステータス**: 成功 (`execution_success`)
- **生成画像**: `ComfyUI/output/Tegaki/Txt2Img_Test_00001_.png` (474,556 bytes)
- **所要時間**: 初回モデルロード込み 約74秒（2回目以降は数秒）。

---

## 14. I2Iテスト結果
- **ステータス**: 成功 (`execution_success`)
- **生成画像**: `ComfyUI/output/Tegaki/I2I_Test_00001_.png` (549,431 bytes)
- **所要時間**: 約11秒（Denoise 0.60, 15 steps）。

---

## 15. Regional Promptテスト結果
- `03_MANGA_REGIONAL_PROMPT.json`: ComfyUI標準の `ConditioningSetMask` + `ConditioningCombine` によるコマ・左右キャラクター描き分けパイプラインを定義・検証。

---

## 16. Regional LoRA概念実証結果
- `04_REGIONAL_LORA_EXPERIMENT.json`: `TegakiLoraPromptLoader` を独立適用したモデル枝分かれ構造により、領域別のLoRA効果制御（RLL先行実験）を可能にするパイプラインを定義。

---

## 17. ControlNetテスト結果
- `05_CONTROLNET_COMPOSITION.json`: `ComfyUI-Advanced-ControlNet` を用いた開始/終了ステップ制御（0.0〜0.75）、強度0.85の構図固定パイプラインを定義。

---

## 18. 起動時error / warning
- `OpenGL_accelerate`: 任意モジュールのため無影響（Warning）。
- `KJNodes: PatchTritonVAE`: Windows Triton非対応のためスキップ（正常動作に支障なし）。
- 全ての主要カスタムノードは正常ロード完了。

---

## 19. 未解決問題
- 3000個を超えるLoRAがあるため、同名LoRAが別サブフォルダに存在する場合、最初に見つかったものが優先される（ログに警告表示）。将来的にサブフォルダ指定付き `<lora:Ani0H/name:0.8>` への完全優先マッチング拡張を推奨。

---

## 20. 今後の推奨作業
1. **ANIMA 3.8B ワークフローの追加**: Illustrious安定運用の後、Experimentalとして追加。
2. **MRP (Manga Region Prompter) 統合**: Tegakiキャンバス側からのコマ割り・矩形情報の直接入力アダプター構築。
3. **LoRA Block Weight 実験**: Inspire PackのLBWノードを活用した構図層/画風層の分離探索。

---

## 分類別作業記録

### 指示通りに作ったもの
- `D:\GitHub\tegaki\ComfyUIPortable` への配置とGit除外設定
- `E:\EasyReforge` モデル・Wildcards資産の読み取り専用共有
- Illustrious / SDXL 主力構成
- 漫画制作向け基本ワークフロー6種
- 外部AIレビュー用ドキュメント群および `GITHUB.TXT`

### Gemini自身の判断で追加したもの
- **独自ノード `TegakiLoraPromptLoader`**: `<lora:name:weight>` 構文を3005個のLoRAから高速解決（拡張子省略・サブディレクトリ耐性）し、モデルパッチとクリーンプロンプト出力をワンストップで行うノードを実装。
- **検証スクリプト群 (`scripts/`)**: モデル数カウント、ノードインポート、txt2img、I2I、Wildcardの自動テストスクリプト。
- **ワークフロー自動生成スクリプト (`generate_workflows.py`)**: メンテナンス性を高めるため、JSON直書きではなく生成スクリプトを用意。

### 当初案から変更したもの
- 当初は既存のLoRAタグローダー（外部Custom Node）のみに頼る予定でしたが、サブディレクトリや拡張子省略への柔軟性、および見つからない場合のエラー可視化要件を確実に満たすため、軽量な独自Custom Node（`tegaki_manga_nodes`）を併せて作成・導入しました。
