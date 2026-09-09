# CAST_SPEC_V1.md — Character Master Data Specification (v1)

## 1. 概要
`CAST_SPEC` は、漫画制作プロジェクトに登場するキャラクターの恒久的・静的マスターデータを定義するデータ構造です。
コマごとの一時的な表情やポーズとは明確に分離され、キャラクターの基本外見、専用LoRA、基本トリガーワードなどを一元管理します。

---

## 2. JSON スキーマ定義 (v1)

```json
{
  "version": 1,
  "characters": [
    {
      "id": "char_001",
      "name": "Alice",
      "enabled": true,
      "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
      "negative_prompt": "bad anatomy, blurry",
      "loras": [
        {
          "name": "alice_official_v1",
          "model_weight": 0.8,
          "clip_weight": 0.6,
          "enabled": true,
          "metadata": {}
        }
      ],
      "metadata": {
        "role": "protagonist",
        "description": "Main heroine"
      }
    }
  ]
}
```

---

## 3. フィールド仕様

### ルート要素
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `version` | `integer` | 必須 | スキーマバージョン。現在は `1` 固定。 |
| `characters` | `array` | 必須 | キャラクター定義オブジェクトのリスト。存在する場合は必ず `list`（非listは即時 `ValueError`）。 |

### Character オブジェクト
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | `string` | 必須 | 内部参照用の安定識別子（例: `char_alice`, `char_001`）。**strict string（非空文字列、数値・boolの暗黙変換不可）**。プロジェクト内で一意。 |
| `name` | `string` | 任意 | 表示名（例: "Alice", "アリス"）。省略時は `id`。重複可能。 |
| `enabled` | `boolean` | 必須 | 厳格な真偽値（`true` / `false`）。`isinstance(val, bool)` を必須化。 |
| `prompt` | `string` | 必須 | キャラクターの恒常的特徴（髪型、瞳、基本衣装、固有特徴タグ）。strict string。 |
| `negative_prompt` | `string` | 任意 | キャラクター個別のネガティブプロンプト。strict string。 |
| `loras` | `array` | 任意 | キャラクター固有のCanonical LoRA定義リスト。 |
| `metadata` | `object` | 任意 | 将来属性用dict（設定資料、参照画像パス等）。非dictは `ValueError`。 |

### Canonical LoRA Entry オブジェクト
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `string` | 必須 | LoRAモデル識別名。非空文字列。 |
| `model_weight` | `number` | 必須 | モデル適用強度。strict numeric（bool除外）。 |
| `clip_weight` | `number` | 必須 | テキストエンコーダー適用強度。strict numeric（bool除外）。 |
| `enabled` | `boolean` | 必須 | 厳格な真偽値。 |
| `metadata` | `object` | 任意 | 将来属性用dict。 |

※ レガシー入力 `weight` は `model_weight = weight, clip_weight = weight` として自動正規化されます。
