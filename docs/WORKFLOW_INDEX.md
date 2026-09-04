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

---

### 10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json
- **区分**: 実験版 / 制御拡張検証ハーネス (EXPERIMENTAL / CONTROL EXPANSION HARNESS)
- **目的**: `Global / Panel / Local Region / Character` の 4 階層モデルによる高度な漫画構図制御と実画像生成の観察・評価。
- **必要Custom Node**:
  - `TegakiLoraPromptLoader` (独自 / Global LoRA実適用)
  - `TegakiMangaRegionEditor` (独自 / コマ割り幾何・Local Region定義)
  - `TegakiMangaPageCompiler` (独自 / 4階層集約実行計画)
  - `TegakiMangaMaskBuilder` (独自 / 4階層Page座標投影・フェザー対応・色分けPreview)
  - `TegakiMangaConditioningBuilder` (独自 / Core API準拠 4階層Conditioning結合)
  - `TegakiMangaSceneCompiler` (独自 / 監査用1コマコンパイル)
  - `TegakiCompilePlanInspector` (独自 / 実行計画監査表示)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, KSampler, VAEDecode, SaveImage, PreviewImage
- **他ワークフローとの関係**:
  - **`09` との関係**: `09` は 3 階層（Global / Panel / Character）による基礎 POC。`10` は第 4 の階層として **`LOCAL_REGION`（コマ内局所領域）** を追加導入し、特定のキャラクターに属さない背景小道具（窓際机、壁面掲示板ポスター等）をコマ内の特定位置へ局所制御可能にした拡張ハーネス。
- **出力**: 3コマ漫画完成画像 (`ComfyUI/output/Tegaki/RegionalControl/...`)、マルチレイヤーMask Preview画像、Region Preview画像、監査サマリー。
- **想定用途**: 背景小道具・スポット演出・キャラクター配置が高度に複合した漫画ページの制作および制御強度の視覚的検証。

---

### 11_TWO_REGION_CORE_COUPLE_ORACLE.json
- **区分**: 実験・検証オラクル (EXPERIMENTAL / REGIONAL ORACLE)
- **目的**: 2領域（Region A / Region B）に特化した最小・最速の Core Masked Conditioning 検証オラクル。横並び・縦並び・重なり・同一シーン内2人物の演技をクリーンに検証可能。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自 / 2領域専用Rectangle Editor, Presets完備)
  - `TegakiTwoRegionCoreConditioner` (独自 / Core API準拠 最短経路結合)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: 2領域制御画像 (`ComfyUI/output/Tegaki/TwoRegionOracle/Core/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 12_TWO_REGION_IMPACT_COUPLE_ORACLE.json
- **区分**: 実験・検証オラクル (EXPERIMENTAL / REGIONAL BACKEND ORACLE)
- **目的**: Impact Pack の `RegionalSampler` / `RegionalPrompt` によるサンプラー分離方式の挙動・性能検証オラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自)
  - `TegakiTwoRegionImpactAdapter` (独自 / Impact連携アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage, PreviewImage
- **出力**: Impactサンプリング画像 (`ComfyUI/output/Tegaki/TwoRegionOracle/Impact/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 13_TWO_REGION_CONTROLNET_LAYOUT_AUX.json
- **区分**: 実験・レイアウト補助オラクル (EXPERIMENTAL / CONTROLNET LAYOUT AUX)
- **目的**: 矩形外枠線（Panel Outline）をガイド画像として Illustrious 向け ControlNet へ投入し、Regional Prompt の境界制御・コマ割り誘導を補助するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自)
  - `TegakiTwoRegionCoreConditioner` (独自)
  - `TegakiTwoRegionLayoutGuide` (独自 / パネル枠線生成)
  - ComfyUI標準: ControlNetLoader, ControlNetApplyAdvanced, CheckpointLoaderSimple, EmptyLatentImage, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: ControlNet補助画像 (`ComfyUI/output/Tegaki/TwoRegionOracle/ControlNetAux/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json
- **区分**: 開発・レイアウトツール (DEVELOPMENT / PANEL LAYOUT TOOL)
- **目的**: 漫画コマ割り専用の独立幾何エディター（`TegakiMangaPanelLayoutEditor`）による、Shared-Vertex Mesh コマ分割・共有頂点ドラッグ変形および ControlNet ガイド画像（白地・黒枠線・文字なし）のプレビュー検証ハーネス。
- **必要Custom Node**:
  - `TegakiMangaPanelLayoutEditor` (独自 / コマ割り専用エディター, 共有頂点メッシュ, H/V/D Split, Undo/Redo)
  - ComfyUI標準: PreviewImage, SaveImage
- **出力**: コマ割りガイド画像 (`ComfyUI/output/Tegaki/PanelLayout/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 15_MANGA_PANEL_LAYOUT_CONTROLNET_FUSION_ORACLE.json
- **区分**: 構図統合オラクル (EXPERIMENTAL / COMPOSITION FUSION ORACLE)
- **目的**: 厳格な平面分割（Planar Subdivision）に基づく `TegakiMangaPanelLayoutEditor` の ControlNet 白黒枠線ガイド画像と、上段コマ内に配置された `TegakiTwoRegionCoupleEditor`（Semantic Overlap 2人物）の Core Masked Conditioning を完全融合し、コマ割り構図と人物演技が矛盾なく共存することを実証するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自 / 2領域 Semantic Overlap エディター)
  - `TegakiTwoRegionCoreConditioner` (独自 / Core Masked Conditioning)
  - `TegakiMangaPanelLayoutEditor` (独自 / コマ割り幾何エディター, Unique-Edge レンダラー)
  - ComfyUI標準: ControlNetLoader, ControlNetApplyAdvanced, CheckpointLoaderSimple, EmptyLatentImage, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: 融合生成画像 (`ComfyUI/output/Tegaki/PanelLayoutFusion/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 16_MANGA_VARIABLE_N_REGION_LAYOUT_FUSION_POC.json
- **区分**: 可変N領域・幾何融合オラクル (STABLE / VARIABLE N-REGION & LAYOUT FUSION POC)
- **目的**: 3〜6コマの任意の多角形コマ割り幾何（`PANEL_LAYOUT_SPEC`）と意味シーン計画（`PAGE_COMPILE_PLAN`）を純粋関数 Bridge を介して完全統合。ControlNet 枠線誘導、多角形コママスク、コマ内相対人物 BBox 投影・多角形クリップ、局所背景領域、大域漫画スタイルを 4 階層 Conditioning で結合し、物理コマ枠と登場人物演技が完全調和した本格漫画ページを生成する実証ワークフロー。
- **必要Custom Node**:
  - `TegakiLoraPromptLoader` (独自 / LoRA構文ローダー)
  - `TegakiMangaRegionEditor` (独自 / 意味コマ領域エディター)
  - `TegakiMangaPageCompiler` (独自 / シーン・キャスト・ローカル領域コンパイラー)
  - `TegakiMangaPanelLayoutEditor` (独自 / 多角形コマ割りエディター & ControlNet白線ガイド)
  - `TegakiMangaLayoutAwareConditioningBuilder` (独自 / 4階層多角形レイアウト融合ノード)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, ControlNetLoader, ControlNetApplyAdvanced, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: 漫画ページ完成画像 (`ComfyUI/output/Tegaki/MangaLayoutFusion/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json
- **区分**: 登場人物マスター管理・局所性検証オラクル (STABLE / CAST MASTER & REGIONAL LOCALITY VALIDATION)
- **目的**: 登場人物の基本プロンプト・ネガティブ・有効/無効を一元管理する独立ノード（`TegakiMangaCastMaster`）と専用 UI エディター（`cast_master_editor.js`）を統合。3コマ基本レイアウト（`3_basic`）上で、同一コマ内の人物 Semantic Overlap（Alice & Bob）およびコマ別出演バインディングを行い、ControlNet (0.60) 枠線誘導下でのキャラクタープロンプト A/B 局所性・5コマ生成成立性を実機検証する本番ワークフロー。
- **必要Custom Node**:
  - `TegakiLoraPromptLoader` (独自 / LoRA構文ローダー)
  - `TegakiMangaCastMaster` (独自 / キャスト・登場人物マスター管理ノード)
  - `TegakiMangaRegionEditor` (独自 / 意味コマ領域エディター)
  - `TegakiMangaPageCompiler` (独自 / シーン・キャスト・ローカル領域コンパイラー)
  - `TegakiMangaPanelLayoutEditor` (独自 / 多角形コマ割りエディター & ControlNet白線ガイド)
  - `TegakiMangaLayoutAwareConditioningBuilder` (独自 / 4階層多角形レイアウト融合ノード)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, ControlNetLoader, ControlNetApplyAdvanced, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: 漫画ページ生成画像 (`ComfyUI/output/Tegaki/MangaCastLocality/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json
- **区分**: 単一領域配置・Backend比較オラクル (EXPERIMENTAL / REGIONAL SEMANTICS ORACLE)
- **目的**: Canvas内の単一指定矩形（Region A, B無効）に対し、対象Prompt（a white dog, full body）をTL/TR/BL/BR/Centerの5位置へ移動させた際、Core Masked Conditioning と Impact RegionalSampler が意図通り対象を空間誘導できるかを同一起点・同一Seed（42）で直接比較・実証するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自 / 5位置プリセット対応エディター)
  - `TegakiTwoRegionCoreConditioner` (独自 / Core Masked Conditioning)
  - `TegakiTwoRegionImpactAdapter` (独自 / Impact連携アダプター, 単一領域対応)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, KSampler, VAEDecode, SaveImage, PreviewImage
- **出力**: Core / Impact 単一領域配置画像 (`ComfyUI/output/Tegaki/Phase3D2/SingleRegion/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json
- **区分**: 2領域意味分離・幾何スワップオラクル (EXPERIMENTAL / TWO-REGION SEMANTIC BINDING ORACLE)
- **目的**: 2つの独立領域（Region A: White Dog, Region B: Black Cat または Man / Woman）において、Promptを一切変更せずに矩形幾何のみを左右入れ替える（Geometry Swap）ことで生成対象の物理位置が反転するかを実証。さらに垂直配置および約35%のSemantic Overlapでの演技相互作用と境界シーム解消を検証するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自 / 2領域エディター)
  - `TegakiTwoRegionImpactAdapter` (独自 / Impact連携アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage, PreviewImage
- **出力**: 2領域意味分離生成画像 (`ComfyUI/output/Tegaki/Phase3D2/TwoRegion/...`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json
- **区分**: 幾何補助オラクル (EXPERIMENTAL / LAYOUT ASSIST ORACLE)
- **目的**: 意味領域幾何から生成された外枠線ガイド（`TegakiTwoRegionLayoutGuide`）を ControlNet へ投入し、Regional Backend 単体と幾何補助併用時での位置拘束力および生成画質・境界アーティファクトへの影響を比較評価するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionCoupleEditor` (独自 / 2領域エディター)
  - `TegakiTwoRegionLayoutGuide` (独自 / パネル枠線生成)
  - `TegakiTwoRegionImpactAdapter` (独自 / Impact連携アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: ControlNetLoader, ControlNetApplyAdvanced, CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage, PreviewImage
- **出力**: ControlNet幾何補助生成画像 (`ComfyUI/output/Tegaki/Phase3D2/LayoutAssist/...`)
- **Zero-Touch Smoke Test**: **PASS**

### 21_MANGA_IMPACT_RECURRENT_CAST_POC.json
- **区分**: 漫画統合・反復出演オラクル (STABLE / MANGA IMPACT RECURRENT CAST POC)
- **目的**: 登場人物マスター（`CAST_SPEC`）の同一キャラクター（Alice / Bob）を複数コマ（Panel 1, 2, 4 および Panel 1, 3, 4）へ繰り返し出演させ、コマごとの演技指示（握手・花壇水やり・植木鉢運搬・対立背向）を独立サンプリング。4コマ漫画グリッドにおいて、コマ背景の先行描画（`scene_first`）とコマ内人物の局所サンプリングを Impact Pack 汎用 N 領域エンジンで一括統合する実証ワークフロー。
- **必要Custom Node**:
  - `TegakiMangaCastMaster` (独自 / キャストマスター管理)
  - `TegakiMangaRegionEditor` (独自 / 4コマ意味領域エディター)
  - `TegakiMangaPageCompiler` (独自 / ページコンパイラー)
  - `TegakiMangaPanelLayoutEditor` (独自 / 4分割コマ割り幾何エディター)
  - `TegakiMangaImpactRegionalAdapter` (独自 / 動的 N 領域 Impact アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage, PreviewImage
- **出力**: 4コマ漫画ページ画像 (`ComfyUI/output/Tegaki/Phase3E/manga_recurrent_cast_4panel.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json
- **区分**: 意地悪テスト・単一コマ内複数シーンオラクル (EXPERIMENTAL / SINGLE PANEL MULTI-SCENE SAME CAST ORACLE)
- **目的**: 単一の可視コマ枠（1 Visible Panel）内部に、独立した 2 つのシーン（Scene A: 夕暮れ校門・対立 vs Scene B: 朝花壇・握手）を幾何分割（Split Scene）配置。同一の Alice Master x2、Bob Master x2 をインスタンスとして共存させ、プロンプトに一切の方位語（left, right）を含めずに 2 つの対照的な人間関係・演技・背景が同一コマ内に成立するかを実機検証するオラクル。
- **必要Custom Node**:
  - `TegakiMangaCastMaster` (独自 / キャストマスター管理)
  - `TegakiMangaPanelLayoutEditor` (独自 / 1コマ全画面幾何エディター)
  - `TegakiSinglePanelMultiSceneImpactAdapter` (独自 / 意地悪テスト専用マルチシーンアダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage, PreviewImage
- **出力**: 単一コマ内複数シーン画像 (`ComfyUI/output/Tegaki/Phase3E/single_panel_multiscene_hostile.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json
- **区分**: 段階的オーサリング標準 (STABLE / PROGRESSIVE AUTHORING 4-PANEL)
- **目的**: ユーザーの制作心理に沿った 6 段階パイプライン（01 GLOBAL → 02 CAST → 03 PANEL CONTENT → 04 PANEL LAYOUT → 05 CHARACTER STAGING → 06 GENERATE）を確立。内部エンジン（Impact Adapter + ToBasicPipe + RegionalSampler）を視覚的に完全隔離し、制作ノード 5 つのみとの対話で 4 コマ漫画を直感的にオーサリング・生成する標準ワークフロー。
- **必要Custom Node**:
  - `TegakiMangaCastSpecEditor` (独自 / キャスト定義)
  - `TegakiMangaPanelContentEditor` (独自 / コマ演出プロンプト・出演管理)
  - `TegakiMangaPanelLayoutEditor` (独自 / コマ割り幾何エディター)
  - `TegakiMangaCharacterStagingEditor` (独自 / キャラクター配置・プレビュー)
  - `TegakiMangaImpactRegionalAdapter` (独自 / 動的 N 領域 Impact アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 段階的オーサリング 4 コマ画像 (`ComfyUI/output/Tegaki/Phase3F/wf23_zero_touch_progressive_4panel.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 24_SINGLE_PANEL_PROGRESSIVE_SUBSCENE_IMPACT.json
- **区分**: 段階的サブシーン・オラクル (EXPERIMENTAL / PROGRESSIVE SUBSCENE ORACLE)
- **目的**: 単一パネル内において、オプションの SubScene v1 Contract を用いて高度な複数シーン（左: Alice の教室、右: Bob の夕暮れ）を展開。通常は不要なサブシーン設定を Progressive Disclosure（段階的開示）により必要な場合のみ有効化し、Impact Pack による動的 N 領域結合でシームレスにサンプリング・描画するオラクル。
- **必要Custom Node**:
  - `TegakiMangaCastSpecEditor` (独自 / キャスト定義)
  - `TegakiMangaPanelContentEditor` (独自 / コマ演出・SubScene 定義)
  - `TegakiMangaPanelLayoutEditor` (独自 / コマ割り幾何エディター)
  - `TegakiMangaCharacterStagingEditor` (独自 / キャラクター・サブシーン配置)
  - `TegakiMangaImpactRegionalAdapter` (独自 / 動的 N 領域 Impact アダプター)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 段階的サブシーン画像 (`ComfyUI/output/Tegaki/Phase3F/wf24_zero_touch_progressive_subscene.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 25_VERIFY_SINGLE_A_TOP_LEFT.json
- **区分**: 正準空間オラクル (CANONICAL SPATIAL ORACLE: SINGLE A TOP-LEFT)
- **目的**: 領域幾何学（Region Geometry）のみによる被写体配置の因果性を実証する固定オラクル。プロンプトに方位語（top, left等）を一切含めず、「`a white dog, full body`」を左上領域 `[0.05, 0.05, 0.45, 0.45]` に配置し、厳格な固定条件（Seed 42, 20 steps, Euler/Normal, CFG 7.0, Impact Regional Backend）で検証。
- **必要Custom Node**:
  - `TegakiTwoRegionImpactAdapter` (独自)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 左上配置犬画像 (`ComfyUI/output/Tegaki/Phase3G/canonical/wf25_canonical_single_a_top_left.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json
- **区分**: 正準空間オラクル (CANONICAL SPATIAL ORACLE: SINGLE A BOTTOM-RIGHT)
- **目的**: Workflow 25 と完全同一の Prompt・Seed (42)・サンプラー条件を維持し、Region A の領域幾何学のみを右下 `[0.50, 0.50, 0.45, 0.45]` に移動。「1 Workflow = 1 Hypothesis」に基づき、幾何変更のみで犬が右下へ正確に移動することを実証するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionImpactAdapter` (独自)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 右下配置犬画像 (`ComfyUI/output/Tegaki/Phase3G/canonical/wf26_canonical_single_a_bottom_right.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json
- **区分**: 正準意味結合オラクル (CANONICAL SEMANTIC BINDING: DOG LEFT, CAT RIGHT)
- **目的**: 2 領域における明確な意味分離と被写体結合を実証するオラクル。方位語抜きの「`a white dog, full body`」を左領域 `[0.05, 0.15, 0.45, 0.70]`、「`a black cat, full body`」を右領域 `[0.50, 0.15, 0.45, 0.70]` に割り当て、混色・キメラ化・位置崩れのない共存を検証（Seed 42）。
- **必要Custom Node**:
  - `TegakiTwoRegionImpactAdapter` (独自)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 犬（左）／猫（右）画像 (`ComfyUI/output/Tegaki/Phase3G/canonical/wf27_canonical_two_region_dog_cat_left_right.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

### 28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json
- **区分**: 正準空間スワップオラクル (CANONICAL SPATIAL SWAP: DOG RIGHT, CAT LEFT)
- **目的**: Workflow 27 と完全同一の Prompt・Seed (42)・サンプラー条件のもと、犬と猫の幾何領域のみを完全反転（犬: 右 `[0.50, 0.15, 0.45, 0.70]`、猫: 左 `[0.05, 0.15, 0.45, 0.70]`）。幾何スワップのみによって左右の被写体位置が完全に入れ替わることを実証するオラクル。
- **必要Custom Node**:
  - `TegakiTwoRegionImpactAdapter` (独自)
  - `ComfyUI-Impact-Pack` (ToBasicPipe, KSamplerAdvancedProvider, RegionalSampler)
  - ComfyUI標準: CheckpointLoaderSimple, EmptyLatentImage, CLIPTextEncode, VAEDecode, SaveImage
- **出力**: 猫（左）／犬（右）スワップ画像 (`ComfyUI/output/Tegaki/Phase3G/canonical/wf28_canonical_two_region_dog_cat_swap.png`)
- **Zero-Touch Smoke Test**: **PASS**

---

## 5. 互換性保証について (Phase 3B.1.1 〜 Phase 3G)
- **Zero-Touch Smoke Test 検証済み**:
  `09_MANGA_REGIONAL_GENERATION_POC.json`、`10`〜`20`、`21`〜`24`、および最新の正準空間検証セット `25`〜`28` は、ComfyUI 起動後に新規ロードして **一切の手動修正なし（Zero-Touch）** でそのまま Queue して処理・生成が正常完了することが実機検証されています。
- **Zero-Touch Parity & Canonical Spatial Verification (Phase 3G)**:
  「1 Workflow = 1 Hypothesis」原則に基づき、手動変更を排した固定比較オラクル（25〜28）を確立。Impact Pack Regional Sampler の 12 ウィジェット整合性および ToBasicPipe 接続要件を常設テストハーネス化。さらに Character Staging のマウスイベントハンドラー（移動・リサイズ・クランプ）と動的キャスト UI 連携を導入し、検証とオーサリング双方の信頼性を確立しました。





