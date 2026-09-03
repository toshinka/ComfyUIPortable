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
          "weight": 0.8,
          "enabled": true
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
| `characters` | `array` | 必須 | キャラクター定義オブジェクトのリスト。 |

### Character オブジェクト
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | `string` | 必須 | 内部参照用の安定識別子（例: `char_alice`, `char_001`）。**プロジェクト内で一意**。 |
| `name` | `string` | 任意 | 表示名（例: "Alice", "アリス"）。重複可能。 |
| `enabled` | `boolean` | 必須 | 厳格な真偽値（`true` / `false`）。無効化時はコンパイル対象から除外。 |
| `prompt` | `string` | 必須 | キャラクターの恒常的特徴（髪型、瞳色、標準衣装、固有特徴タグ）。 |
| `negative_prompt` | `string` | 任意 | キャラクター個別のネガティブプロンプト。 |
| `loras` | `array` | 任意 | キャラクター固有のLoRA定義リスト。 |
| `metadata` | `object` | 任意 | 未知の将来属性（設定資料、参照画像URI、声優情報等）。前方互換性のため保持。 |

### LoRA Entry オブジェクト
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `string` | 必須 | LoRAモデルファイル名または識別名。 |
| `weight` | `number` | 必須 | 適用強度（例: `0.8`）。 |
| `enabled` | `boolean` | 必須 | 厳格な真偽値。 |

---

## 4. 設計原則
1. **IDと表示名の分離**: コマ割り変更や表示名変更でバインディングが壊れないよう、不変の `id` をキーとします。
2. **演出・差分の分離**: 表情（smiling, crying）やコマごとのポーズ（looking at Bob）はここには含めず、KOMA側の `prompt_override` で指定します。
3. **前方互換性**: 将来の属性（`actor_voice`, `control_net` 等）が追加されても、バリデータは未知フィールドを破棄せず透過保持します。
