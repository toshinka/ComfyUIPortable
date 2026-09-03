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
- **注意**: 本ワークフローは `SolidMask` と `ConditioningSetMask` による固定2分割ノード配線です（視覚的Editorではありません）。視覚的レイアウトは `07` を参照してください。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自), ComfyUI標準ConditioningSetMask
- **入力**:
  - Global Prompt（背景・全体トーン）
  - Region A Prompt（例: 左側キャラ/上段コマ）+ マスク
  - Region B Prompt（例: 右側キャラ/下段コマ）+ マスク
- **出力**: コマ・領域分割画像 (`ComfyUI/output/Tegaki/Regional/...`)
- **想定用途**: 2人以上のキャラクターの髪色・服装の混ざり防止、上下段コマの描き分け。

---

### 04_REGIONAL_LORA_EXPERIMENT.json
- **区分**: 実験版 (EXPERIMENTAL / NOT YET REGIONAL)
- **目的**: 領域ごとに異なるLoRA（キャラA用LoRA、キャラB用LoRA）を独立適用するRLL先行実験。
- **注意**: Phase 2コード監査の結果、2本目のLoRAブランチが最終KSamplerに未接続のため、実質的に単一LoRA生成状態となっています。Phase 5にて本格改修予定です。
- **必要Custom Node**: `TegakiLoraPromptLoader` (独自), `ComfyUI-Impact-Pack`
- **入力**:
  - Region A: LoRA A + Prompt A
  - Region B: LoRA B + Prompt B
- **出力**: 領域別LoRA合成画像 (`ComfyUI/output/Tegaki/RegionalLoRA/...`)

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

---

### 07_MANGA_REGION_EDITOR_UI_TEST.json
- **区分**: 開発用検証ハーネス (DEVELOPMENT / UI TEST HARNESS)
- **目的**: 最大6コマ対応の視覚的Region Editorノード (`TegakiMangaRegionEditor`) の単体操作・レイアウトプレビュー・状態保存検証。
- **必要Custom Node**: `TegakiMangaRegionEditor` (独自)
- **特徴**:
  - Canvas上でのドラッグ矩形作成・移動・リサイズ・重なり・Shift一括移動。
  - 水平・垂直スライス (Split H / Split V)、コマ入れ替え (Swap)、Undo/Redo。
  - `REGION_SPEC` (v1) JSON文字列およびプレビュー画像の出力。
  - 生成Backendから完全に分離されており、将来の外部GUI連携にも対応。
- **出力**: コマレイアウトプレビュー画像 (`ComfyUI/output/Tegaki/RegionEditor_Test_...`)
- **想定用途**: ネーム・コマ割りレイアウトの視覚的設計とPromptの整理。

---

### 08_MANGA_SCENE_CONTRACT_TEST.json
- **区分**: 開発用検証ハーネス (DEVELOPMENT / CONTRACT INSPECTION HARNESS)
- **目的**: `REGION_SPEC`、`CAST_SPEC`、Target KOMA、および `TegakiMangaSceneCompiler` による `COMPILE_PLAN` の生成関係を視覚的に検査・確認するためのハーネス。
- **必要Custom Node**: `TegakiMangaRegionEditor` (独自), `TegakiMangaSceneCompiler` (独自), `PreviewImage` (Core)
- **特徴**:
  - SamplerやCheckpoint等の重い生成ノードに依存せず、Tegaki独自ノードとComfyUI標準ノードのみで構成。
  - サンプルとして2人会話シーン（KOMA 1: Alice + Bob、Area左右分割、Prompt Override、LoRAタグ）を内包。
  - `COMPILE_PLAN` (v1) のデータ構造、Clean Prompt、および出演キャラクター数を即座に確認可能。
- **出力**: Regionプレビュー画像、および `COMPILE_PLAN` 実行計画。
- **想定用途**: Scene Contract（PAGE ├ KOMA └ CAST）の構造整合性とコンパイル結果の可視化・監査。

---

### 09_MANGA_REGIONAL_GENERATION_POC.json
- **区分**: 実験版 / エンドツーエンド検証 (EXPERIMENTAL / END-TO-END POC)
- **目的**: `REGION_SPEC` + `CAST_SPEC` ──▶ `PAGE_COMPILE_PLAN` ──▶ `Mask Projection` ──▶ `Conditioning Builder` ──▶ `KSampler` による動的漫画コマ・キャラクター実画像生成。
- **必要Custom Node**:
  - `TegakiLoraPromptLoader` (独自 / Global LoRA実適用)
  - `TegakiMangaRegionEditor` (独自 / コマ割り幾何・演出)
  - `TegakiMangaPageCompiler` (独自 / ページ集約実行計画)
  - `TegakiMangaMaskBuilder` (独自 / Page座標投影・マスク生成)
  - `TegakiMangaConditioningBuilder` (独自 / Core API準拠階層Conditioning結合)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, KSampler, VAEDecode, SaveImage, PreviewImage
- **他ワークフローとの関係**:
  - **`03` との関係**: `03` は固定2領域の手動配線による Oracle / Reference。`09` は `REGION_SPEC` と `CAST_SPEC` に駆動される完全動的・多領域生成への一般化。
  - **`08` との関係**: `08` はデータ契約の整合性と Inspector による静的監査。`09` は Sampler まで直結した実際の実画像生成（Actual Generation）。
  - **`04` との関係**: `04` は領域別LoRA接続の先行実験（NOT YET REGIONAL）。`09` では Global LoRA のみをモデル実適用し、Character LoRA は Plan 保持にとどまります（Character LoRA の領域適用は Phase 5 で改修予定）。
- **出力**: 3コマ漫画完成画像 (`ComfyUI/output/Tegaki/RegionalPOC/...`)、Mask Preview画像、Region Preview画像。
- **想定用途**: コマごとの演出およびキャラクター局所プロンプト（MRP）が反映された漫画原稿の実画像生成。
