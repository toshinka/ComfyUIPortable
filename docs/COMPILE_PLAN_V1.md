# COMPILE_PLAN_V1.md — Manga Scene Compile Plan Specification (v1)

## 1. 概要
`COMPILE_PLAN` は、`Manga Scene Compiler` が `REGION_SPEC` と `CAST_SPEC` を照合・集約し、特定の1コマ（KOMA）を生成・サンプリングするために必要な全情報を構造化した実行計画データです。
巨大Promptによる混線を排し、意味単位（Global, Panel, Character, Area, LoRA）で分離された契約を提供します。

---

## 2. JSON スキーマ定義 (v1)

```json
{
  "version": 1,
  "status": "active",
  "target_panel_id": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "panel": {
    "id": 1,
    "enabled": true,
    "geometry": {
      "x": 0.06,
      "y": 0.05,
      "w": 0.88,
      "h": 0.28
    },
    "prompt": "classroom, two people talking, medium shot"
  },
  "global_prompt": "manga page, monochrome, ink lineart, high contrast",
  "characters": [
    {
      "character_id": "char_001",
      "name": "Alice",
      "base_prompt": "1girl, blonde twin tails, blue eyes, school uniform",
      "override_prompt": "annoyed, looking at Bob",
      "combined_prompt": "1girl, blonde twin tails, blue eyes, school uniform, annoyed, looking at Bob",
      "area": {
        "x": 0.05,
        "y": 0.15,
        "w": 0.40,
        "h": 0.75
      },
      "loras": [
        {
          "name": "alice_official_v1",
          "weight": 0.8,
          "enabled": true
        }
      ],
      "metadata": {}
    }
  ],
  "lora_plan": {
    "global_loras": [
      {
        "name": "shinkai_style",
        "weight": 0.5,
        "enabled": true,
        "source": "tag"
      }
    ],
    "koma_loras": [
      {
        "name": "dramatic_angle",
        "weight": 0.35,
        "enabled": true,
        "source": "tag"
      }
    ],
    "character_loras": [
      {
        "character_id": "char_001",
        "character_name": "Alice",
        "name": "alice_official_v1",
        "weight": 0.8,
        "enabled": true
      }
    ]
  }
}
```

---

## 3. フィールド仕様

### ルート要素
| フィールド | 型 | 説明 |
|---|---|---|
| `version` | `integer` | スキーマバージョン（`1` 固定）。 |
| `status` | `string` | コマのコンパイル状態（`"active"` または `"inactive"`）。 |
| `target_panel_id` | `integer` | コンパイル対象のコマ番号（1〜6）。 |
| `canvas` | `object` | ページ解像度（`width`, `height`）。 |
| `panel` | `object \| null` | 対象コマの幾何座標・Prompt。非Active時は `null`。 |
| `global_prompt` | `string` | ページ全体のグローバルプロンプト。 |
| `characters` | `array` | 当該コマに出演するキャラクターの集約配列。 |
| `lora_plan` | `object` | 階層別LoRA適用計画。 |

### Character 要素
| フィールド | 型 | 説明 |
|---|---|---|
| `character_id` | `string` | CAST_SPECの参照ID。 |
| `name` | `string` | キャラクター名。 |
| `base_prompt` | `string` | CAST_SPEC由来の恒常プロンプト。 |
| `override_prompt` | `string` | 当該コマ固有の演技・表情・服装プロンプト。 |
| `combined_prompt` | `string` | base と override を自然結合したプロンプト。 |
| `area` | `object \| null` | コマ内部（0〜1）の相対配置領域。`null` の場合は位置制約なし（AIお任せ）。 |
| `loras` | `array` | キャラクター固有LoRAリスト。 |

### LoRA Plan 要素
| フィールド | 型 | 説明 |
|---|---|---|
| `global_loras` | `array` | モデル全体に適用するGlobal LoRA一覧。 |
| `koma_loras` | `array` | コマ領域に適用するKOMA LoRA一覧。 |
| `character_loras` | `array` | キャラクター領域に指向するCharacter LoRA一覧。 |
