# PHASE3A_SCENE_DATA_CONTRACT_REPORT.md — Phase 3A Manga Scene Data Contract 報告書

**作成日時**: 2026-09-03 14:37 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  
**Review Target Baseline**: `18becaae25bf3a5e2a0857aa69ec1bee0cdd76fc`  

---

## 1. 境界値修正
Phase 3A開始にあたり、前Phaseレビューで指摘されたRegion境界値の小修正を実施しました：
- **`MIN_REGION_SIZE = 0.001` の定数化**:
  `x = max(0.0, min(1.0 - MIN_REGION_SIZE, x))`, `w = max(MIN_REGION_SIZE, min(1.0 - x, w))` により、`x + w <= 1.0` および `y + h <= 1.0` を厳格保証。
- **極小RegionのPreview描画安全化**:
  Region幅・高さがバッジ描画最小サイズ（`rw >= 40 and rh >= 24`）未満の場合、ラベルバッジ描画をスキップして外枠・半透明塗りつぶしのみ描画。例外送出リスクを完全排除。
- **`regions` 配列内の非dict要素の厳格reject**:
  `regions` 内に文字列や数値等の不正要素が含まれる場合、無言でスキップ（`continue`）せず、`ValueError`（Node execution error）を送出して即時停止。制作データのスキーマ整合性を水際で保護。

---

## 2. REGION_SPEC 変更有無
- **下位互換性**: 既存の `REGION_SPEC` (v1) のルート構造、キャンバス、およびコマ幾何仕様は100%維持。
- **拡張フィールド**: 各Region要素内に `characters: [...]`（Panel ↔ Character Bindingリスト）を保持できるようデータ契約を拡張。バインディングが存在しない場合（従来のWorkflow 07）でも全く問題なく動作します。

---

## 3. CAST_SPEC (v1)
`custom_nodes_custom/tegaki_manga_nodes/scene_spec.py` にキャラクターマスターデータ契約を新設：
- **Schema**:
  ```json
  {
    "version": 1,
    "characters": [
      {
        "id": "char_001",
        "name": "Alice",
        "enabled": true,
        "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
        "negative_prompt": "bad anatomy",
        "loras": [
          {"name": "alice_lora", "weight": 0.8, "enabled": true}
        ],
        "metadata": {}
      }
    ]
  }
  ```
- **特徴**:
  - `id`（不変な内部一意識別子）と `name`（表示名）の完全分離。
  - キャラクターの恒常的特徴（髪・瞳・基本衣装・専用LoRA）のみを一元管理し、コマ単位の一時的演技とは明確に分離。

---

## 4. Binding Schema (Panel ↔ Character Binding)
- **Single Source of Truth**: 「どのキャラクターがどのコマに出演するか」の正本を **KOMA側（`REGION_SPEC.regions[].characters`）** に保持。
- **Schema**:
  ```json
  {
    "character_id": "char_001",
    "enabled": true,
    "prompt_override": "annoyed, looking at Bob",
    "area": {"x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75},
    "lora_override": null,
    "metadata": {}
  }
  ```
- **CAST UIとの関係**: CAST側で「出演コマ一覧: 1, 3」を表示する場合も、KOMA側から動的に逆算。データの二重管理を防止。

---

## 5. Character Local Area (コマ内相対座標)
- **相対座標系の採用**: キャラクターの配置領域 `area` は、ページ全体座標ではなく **KOMA内部の 0.0〜1.0 相対座標** として定義。
  コマを移動・リサイズしても、キャラクターのコマ内構図（例: 左側に立つ、右上に顔アップ）が自動維持されます。
- **`area = null` の許容**: 位置を厳密拘束せずAIの創造的構図に任せるため、`area: null` を正式許可（ブレインストーミング性の維持）。

---

## 6. LoRA 階層設計
1. **GLOBAL LoRA**: モデル全体に適用（絵柄・共通スタイル・全体トーン）。
2. **KOMA LoRA**: 特定コマに指向して適用（アングル・劇的ライティング）。
3. **CHARACTER LoRA**: 特定キャラクター領域に指向して適用（キャラ専用LoRA・衣装LoRA）。
- **LoRA漏れ許容の原則**: Mask外への影響がゼロであることは必須とせず、「目的領域へ相対的に強く効く」実用的な効き方を採用。

---

## 7. Prompt 階層設計
巨大な文字列一本化を排し、意味単位で分離・階層化：
- **Global Prompt**: ページ全体スタイル (`manga page, monochrome, ink lineart...`)
- **Panel Prompt**: コマの情景・カメラ・背景 (`classroom, sunset lighting, two people talking...`)
- **Character Base Prompt**: キャラの恒常外見 (`1girl, blonde twin tails, blue eyes...`)
- **Character Override**: コマ固有の演技・表情 (`annoyed, looking at Bob...`)

---

## 8. Compile Plan (COMPILE_PLAN v1)
`scene_compiler.py` が出力する単一コマの実行計画データ：
- `target_panel_id`, `canvas`, `panel` (幾何・Prompt), `global_prompt`
- `characters`: 各出演キャラの `base_prompt`, `override_prompt`, `combined_prompt`, `area`, `loras`
- `lora_plan`: `global_loras`, `koma_loras`, `character_loras` を分離集約

---

## 9. Scene Compiler Prototype (`TegakiMangaSceneCompiler`)
- **Node**: `TegakiMangaSceneCompiler`
- **入力**: `region_spec` (REGION_SPEC), `target_panel_id` (INT 1..6), `cast_spec` (STRING/dict, optional), `global_loras` (STRING, optional)
- **出力**: `compile_plan` (COMPILE_PLAN), `compile_plan_json` (STRING), `compiled_prompt` (STRING), `character_count` (INT)
- **機能**:
  - 指定コマの情報を抽出。非Active時は安全な空Planを出力。
  - CAST_SPECとの照合（未知キャラID参照時は `ValueError` を送出）。
  - 自然結合プレビュー用Promptを自動生成。
  - CAST_SPEC未指定時は「Panel prompt only」で完全互換動作。

---

## 10. Validation (バリデーション体系)
- `normalize_rect(x, y, w, h)`: Page RegionとCharacter Areaで共通利用する安全な矩形クランプ。
- `validate_cast_spec`: version=1、ID一意性、enabled厳格bool、lorasリスト形式を検査。
- `validate_character_binding`: character_id存在確認、enabled厳格bool、area座標検査。
- `validate_manga_scene_spec`: ページ全体コンテナの統合検証。

---

## 11. Test 結果
全自動テストスクリプトが完全合格：
1. `scripts/test_cast_spec.py`: **ALL PASSED** (正常系、重複ID拒否、厳格bool、未知フィールド保持、未登録ID参照拒否)
2. `scripts/test_scene_compiler.py`: **ALL 7 SUITES PASSED** (1キャラ/1コマ、2人会話シーン、出演差分、area=None保持、LoRA階層集約、未登録ID検知、CAST_SPECなし互換)
3. `scripts/test_region_spec.py`: **ALL 14 SUITES PASSED** (境界値クランプ、極小Preview安全化、非dict要素拒否を含む)
4. `scripts/test_region_state_transitions.py`: **ALL PASSED**
5. `scripts/test_runtime_source_identity.py`: **PASSED** (SHA256ハッシュ更新・Junction物理一致)
6. `scripts/verify_wildcard_patch.py`: **PATCH PRESENT**
7. `scripts/test_region_editor_backend_api.py`: **PASSED** (実機推論プレビュー生成成功)
8. `scripts/test_generation.py`: **PASSED** (01 txt2img非破壊実証)

---

## 12. 既存 Workflow 互換
- `07_MANGA_REGION_EDITOR_UI_TEST.json` および既存の `TegakiMangaRegionEditor` は100%同一動作。
- `CAST_SPEC` が空または未接続でも、Compilerは安全にコマ単位の通常プロンプトを出力。

---

## 13. 既知の問題
- `04_REGIONAL_LORA_EXPERIMENT.json` のKSampler未合流（NOT YET REGIONAL / Phase 5で改修）。
- Region Prompt内での `<lora:...>` 記法（現段階では全体適用 / Phase 5で改修）。
- （※Region境界値クランプ、極小Preview例外、非dict要素スキップ、CASTデータ契約不整合はすべて本Phaseで解決済）。

---

## 14. Phase 3B 案 (Next Steps)
- **Phase 3B: Manga Scene Compiler → Conditioning 接続**:
  - `COMPILE_PLAN` から `Global Conditioning`、`Panel Conditioning`、`Character Conditioning` を生成。
  - Character Local Area をページ全体座標へ射影し、`Attention Couple` または `ConditioningSetMask` / `ConditioningCombine` へ接続するノードの実装。

---

## 15. Gemini 独自判断で変更した点
- **共通矩形正規化関数 `normalize_rect` の新設**:
  Page RegionとCharacter Areaで全く同一の境界値クランプ（MIN_RECT_SIZE = 0.001）を共有し、将来の矩形バグの再発を防止。
- **LoRAタグパーサーの統合**:
  Prompt文字列内の `<lora:name:weight>` を自動抽出し、クリーンプロンプト（タグ除去済）と `lora_plan` に分離するヘルパーを実装。

---

## 16. PHASE 3B READINESS

```text
PHASE 3B READINESS: GO
```
- REGION_SPEC / CAST_SPEC / Binding / COMPILE_PLAN のデータ契約が完全確立
- 1つのKOMAについて、Prompt、出演Character、LoRA候補、Areaが一意に決定可能
- 全自動テスト100%合格、既存ワークフロー・生成エンジン完全非破壊
- Phase 3B（Conditioning接続）へ直ちに進出可能
