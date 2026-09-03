# LORA_ENTRY_V1.md — Canonical LoRA Entry Specification (v1)

## 1. 概要
`Canonical LoRA Entry` は、Tegaki Manga Edition における LoRA 設定の正本データ構造です。
プロンプト文字列内の `<lora:...>` 記法（1値・2値）と構造化JSON設定の双方から正規化され、Single Source of Truth（SSOT）として `COMPILE_PLAN` および将来のサンプラーへ受け渡されます。

---

## 2. Canonical JSON スキーマ (v1)

```json
{
  "name": "alice_costume",
  "enabled": true,
  "model_weight": 0.8,
  "clip_weight": 0.5,
  "source": "structured_character",
  "metadata": {}
}
```

### フィールド仕様
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `string` | 必須 | LoRAモデル識別名（非空文字列）。 |
| `enabled` | `boolean` | 必須 | 厳格な真偽値（`true` / `false`）。 |
| `model_weight` | `float` | 必須 | UNet / Diffusion Model への適用強度。strict numeric（bool除外）。 |
| `clip_weight` | `float` | 必須 | テキストエンコーダー（CLIP）への適用強度。strict numeric（bool除外）。 |
| `source` | `string` | 任意 | 由来スコープ（`global_prompt_tag`, `koma_prompt_tag`, `character_prompt_tag`, `character_override_tag`, `structured_global`, `structured_koma`, `structured_character`）。 |
| `metadata` | `object` | 任意 | 将来属性用dict（trigger words、block weights設定等）。 |

---

## 3. 入力タグ記法と正規化ルール

### 1値LoRAタグ
- 構文: `<lora:name:0.8>`
- 正規化:
  - `model_weight = 0.8`
  - `clip_weight = 0.8`

### 2値LoRAタグ
- 構文: `<lora:name:0.8:0.5>`
- 正規化:
  - `model_weight = 0.8`
  - `clip_weight = 0.5`

### タグ省略形
- 構文: `<lora:name>`
- 正規化:
  - `model_weight = 1.0`
  - `clip_weight = 1.0`

### レガシー `weight` フィールドとの互換
- 入力データに `weight` のみが存在する場合:
  - `model_weight = weight`
  - `clip_weight = weight`
- `weight` と `model_weight` / `clip_weight` が矛盾する値で同時指定された場合:
  - 競合エラーとして `ValueError` を送出。

### 不正タグの拒絶 (Strict Reject)
以下の不正構文は無言で放置せず、即時 `ValueError` を送出して停止します：
- `<lora::0.8>` (名前欠落)
- `<lora:name:notnumber>` (重みが非数値)
- `<lora:name:0.8:notnumber>` (clip重みが非数値)
- `<lora:name:0.8:0.5:extra>` (過剰な引数)

---

## 4. 階層スコープ
LoRAは以下の階層に分類され、`COMPILE_PLAN` の `lora_plan` に分離集約されます：
1. `global_loras`: ページ全体・モデル全体へ適用（絵柄、共通トーン）。
2. `koma_loras`: 特定コマ領域へ適用（アングル、劇的ライティング）。
3. `character_loras`: 特定キャラクター領域へ適用（キャラ外見LoRA、専用衣装LoRA）。
