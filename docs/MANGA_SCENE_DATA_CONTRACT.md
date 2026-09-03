# MANGA_SCENE_DATA_CONTRACT.md — Manga Scene Data Contract 総合仕様書

本ドキュメントは、Tegaki ComfyUI Portable 漫画制作環境における漫画シーン構造（`PAGE ├ KOMA └ CHARACTER`）のデータ契約、責務境界、および将来の生成パイプラインとの連携仕様を定めた正本です。

---

## 1. PAGE / KOMA / CHARACTER 関係の階層構造
本システムは、漫画のページを以下の3層階層としてモデル化します。

```text
PAGE (MANGA_SCENE_SPEC / ページ全体)
 ├ GLOBAL (キャンバス寸法、全体Prompt、全体LoRA、生成パラメータ)
 ├ KOMA (REGION_SPEC / コマ割り幾何、コマ演出Prompt、カメラ、背景)
 │   ├ KOMA 1 ── [Binding] ──▶ 出演 Character A (Override, Local Area)
 │   │                   └──▶ 出演 Character B (Override, Local Area)
 │   ├ KOMA 2 ── [Binding] ──▶ 出演 Character A (Override)
 │   └ ...
 └ CAST (CAST_SPEC / キャラクターマスター定義)
     ├ CHARACTER A (Alice: 恒常Prompt, 固有LoRA, メタデータ)
     ├ CHARACTER B (Bob: 恒常Prompt, 固有LoRA, メタデータ)
     └ ...
```

---

## 2. REGION_SPEC の責務
- **責務**: ページ上の「原稿用紙とコマの幾何配置」および「コマ単位の演出」の正本。
- **保持する情報**:
  - `canvas`: 原稿の解像度（幅・高さ）。
  - `panel_count`: 有効なコマ数（1〜6）。
  - `global_prompt`: ページ全体に共通する絵柄・トーン・画質プロンプト。
  - `regions`: 各コマの幾何座標（0〜1の正規化座標 `x, y, w, h`）、有効フラグ（`enabled`）、コマの情景Prompt（背景・カメラ・アクション）。
  - 各コマ内の `characters` バインディングリスト。
- **制約**: キャラクターそのものの静的マスター情報（恒久外見や固有LoRA）は保持せず、IDによる参照にとどめます。

---

## 3. CAST_SPEC の責務
- **責務**: 漫画プロジェクトに登場する「キャラクターの恒久的マスター定義」の正本。
- **保持する情報**:
  - `id`: 不変かつ一意な内部参照ID（例: `char_alice`, `char_001`）。
  - `name`: 表示名（UI表示用。重複可能）。
  - `prompt`: キャラクターの基本外見（髪型、瞳、体格、基本衣装、固有トリガーワード）。
  - `negative_prompt`: キャラクター固有のネガティブプロンプト。
  - `loras`: キャラクター固有のLoRA定義。
  - `metadata`: キャラクター設定資料、参照画像パス等の将来属性。
- **制約**: コマごとの一時的な表情、ポーズ、特定コマでの位置は保持しません。

---

## 4. Panel ↔ Character Binding (出演バインディング)
- **Single Source of Truth**: 「どのキャラクターがどのコマに出演するか」の正本は **KOMA側（`REGION_SPEC.regions[].characters`）** に保持します。
- **データ構造**:
  ```json
  {
    "character_id": "char_001",
    "enabled": true,
    "prompt_override": "annoyed, looking at Bob",
    "area": { "x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75 },
    "lora_override": null,
    "metadata": {}
  }
  ```
- **CAST UI側での「出演コマ一覧」**: CAST側から逆算して表示し、二重管理によるデータ不整合を防止します。

---

## 5. Character Local Area (コマ内相対座標)
- **座標系**: ページ全体座標ではなく、**コマ内部の 0.0 〜 1.0 相対座標** を採用。
  ```text
  Page Coordinate (REGION_SPEC)
    └── KOMA Coordinate (rx, ry, rw, rh)
          └── Character Local Coordinate (ax, ay, aw, ah)
  ```
- **利点**: コマのサイズ変更（リサイズ）や位置移動（ドラッグ・スライス）を行っても、キャラクターのコマ内相対配置（例: 左側に立つ、右上に顔アップ）が自動的に維持されます。
- **`area = null` の許容**: 位置を厳密に拘束せずAIの創造的構図に任せるため、`area: null` を正式に許可（ブレインストーミング性の維持）。

---

## 6. Global / KOMA / Character LoRA 階層設計
LoRAの適用範囲を3段階の階層として設計します。
1. **GLOBAL LoRA**: ページ全体・モデル全体へ適用（絵柄、全体トーン、質感）。
2. **KOMA LoRA**: 特定コマに指向して適用（アングル、劇的ライティング、背景スタイル）。
3. **CHARACTER LoRA**: 特定キャラクター領域に指向して適用（キャラクター専用LoRA、衣装LoRA）。

※ **LoRA漏れ許容の原則**: Mask外への影響が数学的に0であることは必須とせず、「目的の領域へ相対的に強く効く」実用的な効き方を基準とします。

---

## 7. Prompt 階層設計
プロンプトを巨大な単一文字列へ一本化せず、意味単位で分離管理します。
1. **Global Prompt**: `manga page, monochrome, ink lineart, high contrast`
2. **KOMA Prompt**: `classroom, sunset lighting, two people talking, medium shot`
3. **Character Base Prompt**: `1girl, blonde twin tails, blue eyes, school uniform`
4. **Character Panel Override**: `annoyed, looking at Bob, clenched fist`

---

## 8. Single Source of Truth (SSOT) 原則
- コマの幾何・Prompt ──▶ `REGION_SPEC`
- キャラクターの静的定義 ──▶ `CAST_SPEC`
- 出演関係・コマ内演技 ──▶ `REGION_SPEC.regions[].characters`
- 実行時の統合 ──▶ `Manga Scene Compiler` が `COMPILE_PLAN` として一意に動的合成。

---

## 9. Unknown Field Policy (未知フィールド保持方針)
- 将来の拡張（`actor_voice`, `character_skeleton`, `depth_control`, `expression_mesh` 等）に対応するため、バリデータは既知フィールドを型検証し、未知のフィールドを破棄せず透過保持します。

---

## 10. Schema Versioning (バージョン管理)
- `REGION_SPEC`: `version: 1`
- `CAST_SPEC`: `version: 1`
- `MANGA_SCENE_SPEC`: `version: 1`
- `COMPILE_PLAN`: `version: 1`
- すべてのデータ構造に `version` を義務付け、将来のマイグレーションを保証。未サポートバージョンは明示的に `ValueError` で停止します。

---

## 11. Whole Page / Panel Sequential 両対応設計
将来の生成エンジンとして、以下の2モードを同一データ契約からコンパイル可能とします。
1. **Whole Page Generation**: ページ全体のMaskバッチと全コマConditioningを同時にサンプラーへ渡し、1枚の原稿用紙として一括生成。
2. **Panel Sequential Generation**: KOMA 1から順に個別生成・Inpaint・I2Iを行い、最終的に原稿用紙へ貼り込み（Prompt肥大化回避、コマ単位のガチャ・修正が可能）。

---

## 12. 将来の ControlNet / RLL (Regional LoRA) 拡張余地
- Character Area は将来的に Attention Couple、Regional Conditioning Mask、および ControlNet（人物ポーズ・深度拘束）の入力領域として直接マッピング可能です。
- データ契約を先行確立したことで、生成バックエンドの実装時にもUIやデータ構造の破壊的変更が一切不要となります。
