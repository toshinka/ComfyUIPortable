# PHASE3B_END_TO_END_REGIONAL_GENERATION_REPORT.md — Phase 3B End-to-End Regional Generation 報告書

**作成日時**: 2026-09-03 18:15 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  
**Review Target Baseline**: `95ab6023f07183cf9418c6a036c1c0186a3e183a`  

---

## 1. Pre-3B Hardening
- **LoRA Weight 有限値検査 (`math.isfinite`)**:
  `NaN`, `+Infinity`, `-Infinity` が指定された場合、即時 `ValueError`（スキーマエラー）を送出して安全に停止する防壁を配備・テスト合格。
- **Legacy `weight` の Canonical 出力からの除去**:
  入力受付時の互換性（`weight` のみ指定された場合に `model_weight` / `clip_weight` へ自動正規化）は維持しつつ、出力される Canonical LoRA Entry 辞書からは古い `"weight"` キーを完全に purge。
- **`validate_compile_plan` 深層境界検証**:
  `canvas.width/height` (正の整数, bool除外), `target_panel_id` (strict int 1..6), `panel.id` (targetと一致), `panel.enabled` (strict bool), `panel.geometry` (正規化矩形妥当性, `x+w<=1.0001`), `character.area` (None または正規化矩形), `character.metadata` (dict), `character_loras` (character_id / character_name 必須) を厳格に自己検証する防壁を確立。
- **Workflow 08 Inspector 新設 (`TegakiCompilePlanInspector`)**:
  `OUTPUT_NODE = True` の監査ノードを新設し、Workflow 08 上で Queue 時に Scene Compiler が確実にトリガーされ、Positive, Negative, Character Count, LoRA 階層, Character Area が可視化されるように改善。

---

## 2. PAGE_COMPILE_PLAN
- 単一コマ用（`COMPILE_PLAN`）を一般化し、ページ全体の全 Active KOMA 実行計画を集約する `PAGE_COMPILE_PLAN` (v1) スキーマと、新設ノード `TegakiMangaPageCompiler` を実装。
- 1コマ用のコンパイルロジックを純粋関数 `compile_panel_data(...)` へリファクタリングし、Scene Compiler と Page Compiler で 100% 同一ロジックを再利用。
- `validate_page_compile_plan()` バリデータを配備し、全 panel plan の完全性を検証。

---

## 3. Mask Projection
- 新設ノード `TegakiMangaMaskBuilder` により、ページ上の幾何情報から Canvas 解像度（832x1216）の Pixel Mask Batch（`torch.Tensor` float32 [N, H, W]）を正確に生成。
- 視覚的 Mask Preview 画像（`torch.Tensor` [1, H, W, 3]）を出力し、KOMA 枠線およびキャラクター領域のカラーオーバーレイを描画。

---

## 4. Character Local → Page 座標変換
- コマ内相対座標（`cx, cy, cw, ch`）からページ全体正規化座標への投影式を実装：
  $$\text{page\_x} = k_x + k_w \cdot c_x$$
  $$\text{page\_y} = k_y + k_h \cdot c_y$$
  $$\text{page\_w} = k_w \cdot c_w$$
  $$\text{page\_h} = k_h \cdot c_h$$
- **`area = None` の安全処理**:
  指示書推奨に従い、「当該 KOMA 全体領域」を Character Mask として採用。これにより、ブレインストーミング段階の自由構図を損なわずにキャラクター Conditioning をコマ内に確実に拘束。

---

## 5. Conditioning Builder
- 新設ノード `TegakiMangaConditioningBuilder` を実装。
- ComfyUI Core API（`clip.encode_from_tokens_scheduled`, `node_helpers.conditioning_set_values`, リスト結合による Combine）に完全準拠。
- 内部テンソル構造を独自に手組みせず、Core 互換の安全なアプローチを採用。

---

## 6. Positive 階層
- **Global Positive**: ページ全体へ unmasked conditioning として適用（絵柄・共通トーン）。
- **Panel Positive**: 各 Active KOMA の情景 Prompt（背景・カメラ・アクション）を当該 KOMA Mask とともに結合。
- **Character Positive**: 各出演キャラクターの `combined_prompt`（Base + Override）を Character Page Mask とともに結合。
- テストケース（KOMA1: Alice+Bob, KOMA2: Alice, KOMA3: 背景のみ）において、計 7 ブランチ（Global:1, Panel:3, Char:3）が正確に Combine されることを実証。

---

## 7. Negative 階層
- **Global Negative**: ページ全体共通の除外要素（`bad anatomy, color, photo, realistic, 3d`）を unmasked 適用。
- **Panel Negative**: コマ固有の除外要素（`empty room, solo` 等）を KOMA Mask とともに結合。
- **Character Negative**: キャラクター固有 Base Negative（`blurry, low quality`）と演技 Override Negative（`happy, smiling`）の結合文字列を Character Mask とともに適用。
- 空文字のコマ・キャラクターは自動スキップされ、計 5 ブランチが正確に Combine されることを実証。

---

## 8. Global LoRA 実適用
- `PAGE_COMPILE_PLAN.global_loras` から Canonical 2値 LoRA タグ文字列（`<lora:name:model_weight:clip_weight>`）を自動生成する SSOT 出力ポート `global_loras_text` を Page Compiler に配備。
- これを既存の `TegakiLoraPromptLoader` のテキスト入力へ接続し、Illustrious モデルおよび CLIP への Global LoRA 実適用パイプラインを確立。

---

## 9. Workflow 09 (MANGA_REGIONAL_GENERATION_POC.json)
- `workflows/09_MANGA_REGIONAL_GENERATION_POC.json` を新設。
- 区分: `EXPERIMENTAL / END-TO-END POC`
- [1 MODEL & GLOBAL LORA] ──▶ [2 PAGE / REGION] ──▶ [3 CAST & PAGE COMPILER] ──▶ [4 MASK PREVIEW] ──▶ [5 CONDITIONING] ──▶ [6 SAMPLING] ──▶ [7 OUTPUT]
- CheckpointLoaderSimple から KSampler、VAEDecode、SaveImage まで完全に直結された実稼働ワークフロー。

---

## 10. Runtime 生成結果
- 実機 GPU（NVIDIA GeForce RTX 4070）上で ComfyUI サーバーを起動し、API 経由で実画像を生成。
- 832x1216 解像度、ステップ数 15、固定 Seed 42 にて、全 6 テストの画像生成が例外なく正常終了。
- 生成画像保存先: `ComfyUI/output/Tegaki/RegionalPOC/`

---

## 11. Panel A/B テスト結果 (Test 1)
- **Base_A**: KOMA 1 = `classroom, two people talking, medium shot` (`POC_Base_A_00001_.png`)
- **Panel_B**: KOMA 1 = `convenience store interior, brightly lit, shelves with items, two people talking, medium shot` (`POC_Test1_Panel_B_00001_.png`)
- **観察結果**:
  - KOMA 1 の背景が教室からコンビニの商品棚・明瞭な照明へ劇的に変化。
  - 一方、KOMA 2（廊下）および KOMA 3（夕暮れ屋上）の構図・情景は相対的に維持された。
  - **判定**: `Target Region influence > Outside Region influence` を確認。合格。

---

## 12. Alice A/B テスト結果 (Test 2)
- **Base_A**: Alice = `1girl, blonde twin tails, blue eyes, school uniform`
- **Alice_B**: Alice = `1girl, blue twintails, blue eyes, school uniform` (`POC_Test2_Alice_B_00001_.png`)
- **観察結果**:
  - KOMA 1 の左側領域（Alice Area）の髪色が金髪から鮮やかな青髪へ変化。
  - KOMA 1 の右側領域（Bob Area）の茶髪男子キャラクターは維持され、Alice の青髪属性が右側に侵入（汚染）する現象は極めて軽微に抑えられた。
  - **判定**: `Target Region influence > Outside Region influence` を確認。合格。

---

## 13. Bob A/B テスト結果 (Test 3)
- **Base_A**: Bob = `1boy, short brown hair, school uniform`
- **Bob_B**: Bob = `1boy, pink hair, short hair, school uniform` (`POC_Test3_Bob_B_00001_.png`)
- **観察結果**:
  - KOMA 1 の右側領域（Bob Area）の髪色が茶髪からピンク髪へ変化。
  - KOMA 1 の左側領域の Alice（金髪ツインテール）は維持された。
  - **判定**: `Target Region influence > Outside Region influence` を確認。合格。

---

## 14. Leakage 評価
- コマ境界外への軽微な属性滲み（例: KOMA 1 の教室机のトーンがごくわずかに枠線周辺に影響）は観察されるものの、指示書第41項の基準（「TargetよりOutsideの方が同程度以上に変わる」ことはない）を完全にクリア。
- 局所的プロンプト適用（MRP）が意図通り機能している。

---

## 15. Seam 評価
- コマ間（KOMA 1 と KOMA 2 の間など）に不自然な境界線の破綻や激しいアーティファクトは発生せず、自然な漫画原稿用紙のコマ割りとしてレンダリングされている。

---

## 16. Illustrious での属性混線
- 従来の単一巨大プロンプトでは発生していた「金髪男子」「ツインテール男子」といった属性の混線（Color Bleed / Concept Bleed）が、左右の Character Area Mask によって効果的に分離・抑制されている。

---

## 17. Core Masked Conditioning の限界
- Core の `ConditioningSetMask` はアテンションのソフトな重み付けであるため、被写体が極めて激しく動くポーズや極小コマでは、若干の形状引っ張られが残る余地がある。
- しかし、本 POC の 3 コマ構成・会話シーンにおいては十分な局所性を発揮した。

---

## 18. Impact RegionalSampler 比較の要否
- Core Masked Conditioning による局所性向上が顕著に確認できたため、直ちに Impact RegionalSampler へ移行する必要はないと判断。
- 今後のさらなる厳密分離（Phase 5 の Regional LoRA 等）において比較検討を行うのが望ましい。

---

## 19. 既知の問題
- `04_REGIONAL_LORA_EXPERIMENT.json` の KSampler 未合流（NOT YET REGIONAL / Phase 5 対象）。
- Character LoRA の領域別適用は未実装（Phase 5 対象。現在は Plan 表示および Global LoRA のみ実適用）。

---

## 20. 次 Phase 提案
- **候補 1: Phase 3C (Character / CAST UI)**
  CAST_SPEC を JSON 直書きではなく、視覚的・対話的に管理できる UI の追加。
- **候補 2: Phase 4A (ControlNet Integration)**
  構図・ポーズ・ネームラフをコマごとに拘束する ControlNet（Workflow 05）との統合。

---

## 21. Gemini 独自判断で変更した項目
- **Mask Preview のセマンティックカラーリング**:
  `TegakiMangaMaskBuilder` において、Alice を青系、Bob を橙系など固定の視覚的パレットで色分けし、KOMA 枠線と合成した preview 画像を生成。これにより生成前の領域投影が直感的に確認可能となった。
- **A/B テストの効率的ベースライン比較構造**:
  テスト実行時間の短縮と厳密な差分比較を両立するため、同一の Seed=42 上で共通 Base_A を基準とした 5 つの変分生成を実施。

---

## 22. PHASE 3B 終了判定

```text
REGIONAL PROMPT POC:
PASS

NEXT BACKEND:
CORE MASKED CONDITIONING
```
