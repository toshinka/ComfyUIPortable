# WORKFLOW_INDEX.md — 漫画制作ワークフロー解説

ComfyUIPortableに同梱されている漫画制作向けワークフロー一覧です。
すべてのワークフローは `workflows/` ディレクトリに格納されており、ComfyUIのUI画面へドラッグ＆ドロップすることで読み込めます。

---

## ワークフロー一覧

### 01_BASIC_ILLUSTRIOUS_TXT2IMG.json
- **区分**: 安定版 (STABLE)
- **目的**: Illustrious / SDXL による漫画・イラストの高品質txt2img生成。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自)
- **入力**:
  - Positive Prompt（`<lora:name:weight>` 記法対応）
  - Negative Prompt
  - Checkpoint（既定: `waiIllustriousSDXL_v170.safetensors`）
  - Latent解像度（既定: 832x1216 漫画縦構図）
- **出力**: 生成画像 (`ComfyUI/output/Tegaki/Txt2Img/...`)
- **想定用途**: キャラクターデザイン、コマのラフ出し、アイデア探索。

---

### 02_ILLUSTRIOUS_I2I.json
- **区分**: 安定版 (STABLE)
- **目的**: 既存ラフ・生成画像のディテールアップ、線画強調、画風調整。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自)
- **入力**:
  - 入力画像 (`LoadImage`)
  - Denoise Strength（既定: 0.60）
  - 修正・強化Prompt & LoRA
- **出力**: 修正画像 (`ComfyUI/output/Tegaki/I2I/...`)
- **想定用途**: 構図を維持したまま絵柄の統一、線画の清書風変換、パーツ修正。

---

### 03_MANGA_REGIONAL_PROMPT.json
- **区分**: 安定版 (STABLE)
- **目的**: コマ割りや画面左右でのキャラクター描き分け（属性汚染・混色の防止）。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自), ComfyUI標準ConditioningSetMask
- **入力**:
  - Global Prompt（背景・全体トーン）
  - Region A Prompt（例: 左側キャラ/上段コマ）+ マスク
  - Region B Prompt（例: 右側キャラ/下段コマ）+ マスク
- **出力**: コマ・領域分割画像 (`ComfyUI/output/Tegaki/Regional/...`)
- **想定用途**: 2人以上のキャラクターの髪色・服装の混ざり防止、上下段コマの描き分け。

---

### 04_REGIONAL_LORA_EXPERIMENT.json
- **区分**: 実験版 (EXPERIMENTAL)
- **目的**: 領域ごとに異なるLoRA（キャラA用LoRA、キャラB用LoRA）を独立適用するRLL先行実験。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自), `ComfyUI-Impact-Pack`
- **入力**:
  - Region A: LoRA A + Prompt A
  - Region B: LoRA B + Prompt B
- **出力**: 領域別LoRA合成画像 (`ComfyUI/output/Tegaki/RegionalLoRA/...`)
- **想定用途**: 異なるキャラクターLoRAを同一画面の別領域にだけ効かせる高度な漫画制作。

---

### 05_CONTROLNET_COMPOSITION.json
- **区分**: 実験版 (EXPERIMENTAL)
- **目的**: ポーズ・下絵による構図の固定と、ステップ制御（自由度と拘束のバランス）。
- **必要Custom Node**: `ComfyUI-Advanced-ControlNet`, `TegakiLoraPromptLoader`
- **入力**:
  - ポーズ・下絵画像 (`LoadImage`)
  - ControlNetモデル (`controlnet/`)
  - 開始ステップ (0.0) / 終了ステップ (0.75) / 強度 (0.85)
- **出力**: 構図拘束生成画像 (`ComfyUI/output/Tegaki/ControlNet/...`)
- **想定用途**: 漫画のネーム・棒人間ラフからの構図そのままの作画化。

---

### 06_LORA_MIX_EXPERIMENT.json
- **区分**: 安定版 (STABLE)
- **目的**: 複数LoRAの配合比率探索、絵柄ブレンド、LoRAスタックのテキスト可視化。
- **必要Custom Node**: `TegakiLoraPromptLoader`, `TegakiLoraStackToPrompt`
- **入力**:
  - 複数LoRAタグ記述（例: `<lora:StyleA:0.4> <lora:StyleB:0.3>`）
- **出力**:
  - 生成画像 (`ComfyUI/output/Tegaki/LoraMix/...`)
  - 適用中LoRAスタックのテキスト一覧
- **想定用途**: オリジナルの漫画タッチを作るための複数スタイルLoRAの黄金比率探索。
