# COMPILE_PLAN_V1.md — Manga Scene Compile Plan Specification (v1)

## 1. 概要
`COMPILE_PLAN` は、`Manga Scene Compiler` が `REGION_SPEC` と `CAST_SPEC` を照合・集約し、特定の1コマ（KOMA）を生成・サンプリングするために必要な全情報を構造化した実行計画データです。
巨大Promptによる混線を排し、意味単位（Global, Panel, Character, Area, LoRA, Negative）で分離された契約を提供します。

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
    "prompt": "classroom, two people talking, medium shot",
    "negative_prompt": "empty room, solo"
  },
  "global_prompt": "manga page, monochrome, expressive linework, high contrast",
  "global_negative_prompt": "bad anatomy, color, realistic photo",
  "compiled_prompt": "manga page, monochrome, expressive linework, high contrast, classroom, two people talking, medium shot, 1girl, blonde twin tails, blue eyes, school uniform, annoyed, looking at Bob, 1boy, short brown hair, school uniform, laughing, looking at Alice",
  "compiled_negative_prompt": "bad anatomy, color, realistic photo, empty room, solo, blurry, low quality, happy, smiling, bad anatomy, crying, serious",
  "characters": [
    {
      "character_id": "char_001",
      "name": "Alice",
      "base_prompt": "1girl, blonde twin tails, blue eyes, school uniform",
      "override_prompt": "annoyed, looking at Bob",
      "combined_prompt": "1girl, blonde twin tails, blue eyes, school uniform, annoyed, looking at Bob",
      "base_negative_prompt": "blurry, low quality",
      "override_negative_prompt": "happy, smiling",
      "combined_negative_prompt": "blurry, low quality, happy, smiling",
      "area": {
        "x": 0.05,
        "y": 0.15,
        "w": 0.40,
        "h": 0.75
      },
      "loras": [
        {
          "name": "alice_costume",
          "model_weight": 0.8,
          "clip_weight": 0.6,
          "enabled": true,
          "source": "structured_character",
          "metadata": {}
        }
      ],
      "metadata": {}
    }
  ],
  "lora_plan": {
    "global_loras": [
      {
        "name": "manga_lineart",
        "model_weight": 0.5,
        "clip_weight": 0.5,
        "enabled": true,
        "source": "structured_global",
        "metadata": {}
      }
    ],
    "koma_loras": [
      {
        "name": "dramatic_angle",
        "model_weight": 0.35,
        "clip_weight": 0.35,
        "enabled": true,
        "source": "koma_prompt_tag",
        "metadata": {}
      }
    ],
    "character_loras": [
      {
        "character_id": "char_001",
        "character_name": "Alice",
        "name": "alice_costume",
        "model_weight": 0.8,
        "clip_weight": 0.6,
        "enabled": true,
        "source": "structured_character",
        "metadata": {}
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
| `panel` | `object \| null` | 対象コマの幾何座標・Prompt・Negative Prompt。非Active時は `null`。 |
| `global_prompt` | `string` | ページ全体のグローバルプロンプト（LoRAタグ除去済）。 |
| `global_negative_prompt` | `string` | ページ全体のグローバルネガティブプロンプト。 |
| `compiled_prompt` | `string` | デバッグ・プレビュー用の自然結合Positive文字列。 |
| `compiled_negative_prompt` | `string` | デバッグ・プレビュー用の自然結合Negative文字列。 |
| `characters` | `array` | 当該コマに出演するキャラクターの集約配列（strict list）。 |
| `lora_plan` | `object` | 階層別Canonical LoRA適用計画。 |
