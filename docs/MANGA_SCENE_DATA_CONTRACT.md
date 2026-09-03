# MANGA_SCENE_DATA_CONTRACT.md — Manga Scene Data Contract 総合仕様書

本ドキュメントは、Tegaki ComfyUI Portable 漫画制作環境における漫画シーン構造（`PAGE ├ KOMA └ CHARACTER`）のデータ契約、責務境界、および将来の生成パイプラインとの連携仕様を定めた正本です。

---

## 1. PAGE / KOMA / CHARACTER 関係の階層構造
本システムは、漫画のページを以下の3層階層としてモデル化します。

```text
PAGE (MANGA_SCENE_SPEC / ページ全体)
 ├ GLOBAL (キャンバス寸法、全体Prompt、全体Negative、全体LoRA、生成パラメータ)
 ├ KOMA (REGION_SPEC / コマ割り幾何、コマ演出Prompt、コマNegative、カメラ、背景)
 │   ├ KOMA 1 ── [Binding] ──▶ 出演 Character A (Override Prompt, Neg Override, Local Area)
 │   │                   └──▶ 出演 Character B (Override Prompt, Neg Override, Local Area)
 │   ├ KOMA 2 ── [Binding] ──▶ 出演 Character A (Override Prompt, Neg Override)
 │   └ ...
 └ CAST (CAST_SPEC / キャラクターマスター定義)
     ├ CHARACTER A (Alice: 恒常Prompt, 恒常Negative, 固有LoRA, メタデータ)
     ├ CHARACTER B (Bob: 恒常Prompt, 恒常Negative, 固有LoRA, メタデータ)
     └ ...
```

---

## 2. REGION_SPEC の責務
- **責務**: ページ上の「原稿用紙とコマの幾何配置」および「コマ単位の演出」の正本。
- **保持する情報**:
  - `canvas`: 原稿の解像度（幅・高さ）。
  - `panel_count`: コマ番号の上限（スロット範囲 1..6）。
  - `global_prompt`: ページ全体に共通する絵柄・トーン・画質プロンプト。
  - `global_negative_prompt`: ページ全体共通のネガティブプロンプト。
  - `regions`: 各コマの幾何座標（0〜1の正規化座標 `x, y, w, h`）、有効フラグ（`enabled`）、コマの情景Prompt（背景・カメラ・アクション）、コマ個別Negative Prompt。
  - 各コマ内の `characters` バインディングリスト。
- **制約**: キャラクターそのものの静的マスター情報（恒久外見や固有LoRA）は保持せず、IDによる参照にとどめます。

---

## 3. CAST_SPEC の責務
- **責務**: 漫画プロジェクトに登場する「キャラクターの恒久的マスター定義」の正本。
- **保持する情報**:
  - `id`: 不変かつ一意な内部参照ID（例: `char_alice`, `char_001`）。strict string。
  - `name`: 表示名（UI表示用。重複可能）。
  - `prompt`: キャラクターの基本外見（髪型、瞳、体格、基本衣装、固有トリガーワード）。
  - `negative_prompt`: キャラクター固有のネガティブプロンプト。
  - `loras`: キャラクター固有のCanonical LoRA定義（`model_weight`, `clip_weight`）。
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
    "negative_prompt_override": "happy, smiling",
    "area": { "x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75 },
    "lora_override": null,
    "metadata": {}
  }
  ```
- **CASTなしBindingの禁止 (Strict Reject)**:
  KOMA内にCharacter Bindingが存在するにもかかわらず、`CAST_SPEC` が空・未指定、または構文破損している場合は、制作データ保護のため **即時 `ValueError` を送出して停止** します。

---

## 5. Character Local Area (コマ内相対座標)
- **座標系**: ページ全体座標ではなく、**コマ内部の 0.0 〜 1.0 相対座標** を採用。
  ```text
  Page Coordinate (REGION_SPEC)
    └── KOMA Coordinate (rx, ry, rw, rh)
          └── Character Local Coordinate (ax, ay, aw, ah)
  ```
- **利点**: コマのサイズ変更（リサイズ）や位置移動を行っても、キャラクターのコマ内相対配置（例: 左側に立つ、右上に顔アップ）が自動維持されます。
- **`area = null` の許容**: 位置を厳密に拘束せずAIの創造的構図に任せるため、`area: null` を正式に許可（ブレインストーミング性の維持）。

---

## 6. LoRA Canonicalization & 階層設計
LoRAのSingle Source of Truthを正式化：
- **Canonical形式**: `name`, `enabled`, `model_weight` (float), `clip_weight` (float), `source`, `metadata`。
- **2値タグ対応**: `<lora:name:0.8:0.5>` を `model_weight=0.8, clip_weight=0.5` として完全保持。
- **全Prompt階層でのParser共通化**: Global Prompt, KOMA Prompt, Character Base Prompt, Character Override Prompt すべてで共通の `parse_lora_tags()` を実行し、タグを除去した `clean_prompt` と Canonical LoRA を分離抽出。
- **不正タグ拒絶**: `<lora::0.8>` や `<lora:name:abc>` は無言で放置せず `ValueError` で停止。
- **3階層スコープ**:
  1. `global_loras`: ページ全体・モデル全体へ適用（絵柄、共通トーン）。
  2. `koma_loras`: 特定コマ領域へ適用（アングル、劇的ライティング）。
  3. `character_loras`: 特定キャラクター領域へ適用（キャラ専用LoRA、衣装LoRA）。

---

## 7. Negative Prompt 階層設計
Negative Prompt も巨大文字列へ一本化せず、4階層で構造化保持：
1. **Global Negative Prompt**: ページ全体共通の除外要素（`bad anatomy, color, realistic photo`）。
2. **Panel Negative Prompt**: 当該コマ固有の除外要素（`empty room, solo, outdoor`）。
3. **Character Base Negative Prompt**: キャラクター固有の除外要素（`glasses, short hair`）。
4. **Character Override Negative Prompt**: 当該コマの演技差分固有の除外要素（`happy, smiling`）。

---

## 8. panel_count 用語と Active Panel
- **`panel_count`**: コマ番号の上限（スロット範囲 1..6）。
- **Active Panel**: `is_active_region` (`enabled === true` かつ `id <= panel_count`) を満たすコマ。
  - 例: `panel_count = 3` で KOMA 1 (有効), KOMA 2 (無効), KOMA 3 (有効) の場合、`active_panel_ids = [1, 3]`。
  - 将来の Panel Sequential Generation では `active_panel_ids` を対象に順次生成を実行。

---

## 9. COMPILE_PLAN Validation Boundary
- `Scene Compiler` の出力および次Phase（Conditioning）の入力境界として、`validate_compile_plan()` を配備。
- スキーマ適合性、strict型（string, numeric, list, dict）、active時のpanel必須性を厳格に保証。
