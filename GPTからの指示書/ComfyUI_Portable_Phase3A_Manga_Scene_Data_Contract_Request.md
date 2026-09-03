# ComfyUI Portable Phase 3A — Manga Scene Data Contract 設計指示書

## 0. 今回の目的

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
18becaae25bf3a5e2a0857aa69ec1bee0cdd76fc
```

Phase 2.1.1 までで、

- Git正本とRuntimeコードの同一化
- REGION_SPEC v1 のSingle Source of Truth化
- Region Editorの状態遷移安定化
- Split / Create / Delete / Reset / Swap / Undo / Redo
- schema validation
- Wildcard Organizer
- txt2img / I2I基盤
- 外部AIレビュー経路

が安定しました。

今回のPhase 3Aでは、すぐにRegional Conditioning Compilerを完成させるのではなく、

```text
PAGE
 ├ KOMA
 └ CHARACTER
```

を扱うための **Manga Scene Data Contract** を先に設計します。

目的は、

```text
REGION_SPEC
+
CAST_SPEC
+
Panel ↔ Character Binding
+
将来のLoRA / Control / Prompt Compiler
```

の関係を正式に決めることです。

今回の主眼は「データ契約」です。

完成版の漫画GUIや本格的なRegional Samplingはまだ実装しないでください。

---

# 1. 最初に現在状態を確認する

作業開始時に以下を確認してください。

```text
git rev-parse HEAD
git status
git branch --show-current
git remote -v
```

以下を必ず読んでください。

```text
ComfyUIPortable/GITHUB.TXT
ComfyUIPortable/README.md
ComfyUIPortable/KNOWN_ISSUES.md
ComfyUIPortable/PHASE2_1_STABILIZATION_REPORT.md
ComfyUIPortable/PHASE2_1_1_REGRESSION_FIX_REPORT.md
ComfyUIPortable/PHASE2_1_UI_TEST_CHECKLIST.md

ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/region_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/tegaki_region_editor.js

ComfyUIPortable/scripts/test_region_spec.py
ComfyUIPortable/scripts/test_region_state_transitions.py
```

既存の安定部分を壊さないでください。

---

# 2. Phase 3A開始前の小さな境界値修正

前回レビューで、Phase 3へ進むこと自体はGOと判断していますが、以下3点だけPhase 3Aの冒頭で修正してください。

独立したPhase 2.1.2にはしません。

---

# 3. Region geometryの最小サイズ境界を厳密化する

現在、

```text
x = 1.0
w = 0.001
```

のような組み合わせで、

```text
x + w > 1.0
```

が成立する可能性があります。

最低Regionサイズを定数化してください。

例:

```python
MIN_REGION_SIZE = 0.001
```

そして、

```text
x <= 1.0 - MIN_REGION_SIZE
y <= 1.0 - MIN_REGION_SIZE
w <= 1.0 - x
h <= 1.0 - y
```

を必ず満たしてください。

---

# 4. 極小RegionのPreview描画を安全化する

極端に小さいRegionでは、ラベル描画用badgeがRegion幅より大きくなったり、負サイズになる可能性があります。

以下のような安全策を入れてください。

```text
Regionが一定pixelサイズ未満
→ ラベルbadgeを描かない
→ Region枠だけ描画
```

Preview描画がREGION_SPECの合法値で例外を出さないことを保証してください。

---

# 5. regions配列内の不正要素をrejectする

現在、

```python
if not isinstance(r, dict):
    continue
```

のように、regions内の非dict要素を黙って消す挙動が残っている場合は修正してください。

例:

```json
{
  "regions": [
    {...},
    "broken region",
    {...}
  ]
}
```

は、

```text
ValueError
```

として停止させてください。

Phase 2.1.1で決めた、

```text
Schema Error
→ 制作データ保護のため明示的に失敗
```

という方針と統一してください。

---

# 6. 上記3点のRegression Test

最低限以下を追加してください。

```text
x=1.0 / w>0 → 正常化後 x+w<=1
y=1.0 / h>0 → 正常化後 y+h<=1
最小Region Preview → 例外なし
regions内にstring → ValueError
```

ここまでをPhase 3A開始前の安定化処理とします。

---

# 7. 本プロジェクトの漫画制作方針

今後の設計は以下を前提にしてください。

このComfyUI環境は、

```text
ComfyUIだけで漫画を完成させる
```

ためのものではありません。

ComfyUIが主に担当するのは、

```text
構図
カメラ
キャラクター位置
演技
ポーズ
人物間関係
背景
建物
複雑な小物
精度の高い下絵
```

など、描画コストが高い部分です。

一方、

```text
集中線
トーン
効果
吹き出し
文字
細部修正
最終描画
```

は、

```text
別ツール
手描き
他の制作工程
```

と自由に併用します。

既存の漫画制作Custom Nodeを参考にする場合も、この方針を崩さないでください。

---

# 8. ブレインストーミング性を残す

本システムは「完全拘束型生成」だけを目指しません。

必要なのは、

```text
ある程度構図を誘導
ある程度人物位置を固定
ある程度キャラクター性を維持
```

しながら、

```text
seed
ポーズ細部
表情
画面内の偶然性
構図候補
演出候補
```

には探索余地を残すことです。

制御精度を上げるほど良い、という単純な設計にはしないでください。

---

# 9. LoRAの基本方針

LoRAはまず、

```text
GLOBAL LoRA
```

を基本とします。

つまり通常のLoRAはモデル全体へ適用します。

その上で追加機能として、

```text
KOMA LoRA
CHARACTER LoRA
```

を将来的に配置可能にします。

Regional LoRAは、

```text
指定領域以外へ完全に漏れない
```

ことを必須条件にしません。

漫画制作上、

```text
指定したコマ / 人物へ相対的に強く効く
```

なら採用価値があります。

この方針をデータ契約へ反映してください。

---

# 10. 今回の中心設計

これまでの構造:

```text
PAGE
 ├ KOMA 1
 ├ KOMA 2
 ├ KOMA 3
 └ ...
```

を、

```text
PAGE
 ├ GLOBAL
 ├ KOMA
 │   ├ KOMA 1
 │   ├ KOMA 2
 │   └ ...
 │
 └ CAST
     ├ CHARACTER A
     ├ CHARACTER B
     └ ...
```

へ拡張します。

そして各KOMAから、

```text
どのCharacterが出演するか
```

を参照します。

---

# 11. REGION_SPECの責務を維持する

REGION_SPECは引き続き、

```text
ページ上のコマ領域
```

を正本とします。

責務:

```text
Page Canvas
Panel Count
Global Prompt
KOMA identity
KOMA geometry
KOMA enabled
KOMA Prompt
```

を保持します。

ただしCharacterそのものの恒久情報をREGION_SPECへ直接複製しないでください。

---

# 12. CAST_SPECを新設する

新たに、

```text
CAST_SPEC
```

というデータ契約を設計してください。

まだ本格UIを作る必要はありません。

最低限、

```json
{
  "version": 1,
  "characters": []
}
```

のようなRoot構造を持たせます。

---

# 13. Characterの基本Schema

候補:

```json
{
  "id": "alice",
  "name": "Alice",
  "enabled": true,
  "prompt": "1girl, blonde hair, blue eyes",
  "negative_prompt": "",
  "loras": [],
  "metadata": {}
}
```

正確なSchemaは改善して構いません。

ただし以下は分けてください。

```text
Character identity
Character prompt
Character LoRA
Panel-specific state
```

---

# 14. Character ID

Characterの内部参照には、

```text
KOMA1
KOMA2
```

のような位置依存IDではなく、

```text
alice
bob
char_001
```

のような安定IDを使用してください。

表示名と内部IDを分離してください。

例:

```json
{
  "id": "char_001",
  "name": "Alice"
}
```

---

# 15. Character Prompt

Character Promptは、

```text
そのキャラクターの恒常的特徴
```

を持つ場所とします。

例:

```text
hair
eyes
costume baseline
body type
identity tags
character trigger words
```

コマごとの演技や表情を大量にここへ入れないでください。

---

# 16. Character LoRA

CAST_SPEC内にLoRA設定を持てるようにしてください。

例:

```json
{
  "loras": [
    {
      "name": "alice_character",
      "weight": 0.8,
      "enabled": true
    }
  ]
}
```

将来的に、

```text
model_weight
clip_weight
block_weight
```

等を追加できる余地を残してください。

今回Regional LoRA処理自体は実装しないでください。

---

# 17. Global LoRAとの関係

将来的な優先構造:

```text
GLOBAL LoRA
+
KOMA LoRA
+
CHARACTER LoRA
```

を想定します。

基本的にはGLOBAL LoRAがモデル全体へ適用。

KOMA / CHARACTER LoRAは追加の指向性制御です。

---

# 18. Panel ↔ Character Bindingを設計する

「AliceはKOMA1とKOMA3に出演する」のような情報が必要です。

ただし、

```text
CAST側のappears_in
+
KOMA側のcharacters
```

の両方を正本にしないでください。

Single Source of Truthを維持してください。

---

# 19. Bindingの正本候補

推奨はKOMA側です。

概念:

```json
{
  "id": 1,
  "prompt": "classroom, two people talking",
  "characters": [
    {
      "character_id": "char_001"
    },
    {
      "character_id": "char_002"
    }
  ]
}
```

CAST UI側で、

```text
Appears in: 1, 3, 5
```

と表示する場合も、KOMA側Bindingから逆算してください。

---

# 20. Panel-local Character State

同じCharacterでもコマごとに、

```text
表情
ポーズ
向き
行動
位置
服装差分
```

が変わります。

これをCharacter本体へ直接保存しないでください。

KOMA内Bindingに、

```text
panel-local override
```

として保持してください。

---

# 21. Panel-local Character Schema

候補:

```json
{
  "character_id": "char_001",
  "enabled": true,
  "prompt_override": "smiling, looking at Bob",
  "area": {
    "x": 0.05,
    "y": 0.10,
    "w": 0.40,
    "h": 0.80
  },
  "lora_override": null,
  "metadata": {}
}
```

正確なSchemaは改善して構いません。

---

# 22. Character areaはKOMA-local座標にする

Character areaはページ全体座標ではなく、

```text
KOMA内部の0〜1座標
```

を基本としてください。

つまり、

```text
Page coordinate
  ↓
KOMA coordinate
      ↓
Character local coordinate
```

です。

これによりKOMAを移動・Resizeしても、

```text
Characterの相対位置
```

を維持できます。

---

# 23. Character areaは必須にしない

ブレインストーミング性維持のため、

```text
area = null
```

を許可してください。

意味:

```text
キャラクターは出演するが、位置はAIへ任せる
```

です。

必要なときだけareaを指定します。

---

# 24. Character areaの厳密性

Character areaはControlNetほど厳密な拘束ではありません。

将来的に、

```text
Attention Couple
Regional Prompt
Mask
Regional LoRA
```

等へ利用できます。

「この人物はだいたいこの辺」という誘導領域と考えてください。

---

# 25. KOMA PromptとCharacter Promptを分離する

KOMA Promptには、

```text
scene
camera
background
action
composition
lighting
```

等を書きます。

Character Promptには、

```text
identity
appearance
baseline style
```

等を書きます。

Panel-local overrideには、

```text
expression
pose
action variation
```

等を書きます。

---

# 26. 巨大Prompt一本化を避ける

将来的なCompilerでは、

```text
Global
+
KOMA
+
Character A
+
Character B
```

を単純に巨大なSTRING一本へ連結するだけの設計は避けてください。

ComfyUIでは、

```text
Global Conditioning
Panel Conditioning
Character Conditioning
```

へ分離できる構造を優先します。

---

# 27. BREAK依存を減らす

必要ならBREAK互換は残して構いません。

ただし内部の基本思想は、

```text
文字列をBREAKで無理に分割
```

ではなく、

```text
意味単位でConditioningを分離
```

としてください。

---

# 28. Manga Scene Specを検討する

REGION_SPECとCAST_SPECをまとめる上位データ構造として、

```text
MANGA_SCENE_SPEC
```

または、

```text
PAGE_SPEC
```

を設計して構いません。

例:

```json
{
  "version": 1,
  "region_spec": {...},
  "cast_spec": {...},
  "generation": {...},
  "metadata": {}
}
```

ただし既存REGION_SPECを破壊する必要はありません。

---

# 29. 正本の分離を明確にする

推奨:

```text
REGION_SPEC
→ Page / KOMA geometry & prompt

CAST_SPEC
→ Character master data

Panel Character Binding
→ KOMAごとの出演・位置・override

Generation Config
→ sampler / seed / global LoRA等
```

それぞれの責務をドキュメント化してください。

---

# 30. Global LoRA集約構造

将来的にユーザーが、

```text
<lora:AAA:0.2>
<lora:BBB:0.7>
```

等を全体へ適用するための、

```text
GLOBAL LORA STACK
```

を一箇所に集約できる設計を考えてください。

今回GUI実装は不要です。

Schema候補だけ定義してください。

---

# 31. KOMA LoRA

KOMAごとに追加LoRAを配置できるSchema余地を用意してください。

例:

```json
{
  "loras": [
    {
      "name": "dramatic_angle",
      "weight": 0.4
    }
  ]
}
```

ただし今回実際のRegional LoRA適用は行わないでください。

---

# 32. Character LoRA

Character masterにCharacter LoRAを持つ。

必要ならPanel Binding側でoverrideできる。

例:

```text
Character baseline LoRA = 0.8

KOMA3だけ
override = 0.5
```

等。

---

# 33. LoRA漏れは許容する設計

今後のRegional LoRA研究では、

```text
Mask外 influence = 0
```

を必須にしないでください。

評価基準は、

```text
Target Region influence
>
Outside Region influence
```

です。

漫画下絵用途で実用的なら採用します。

---

# 34. Character Panel UIは今回最小限

今回、本格的なCharacter Panel UIを作る必要はありません。

必要なら、

```text
CAST_SPEC JSON editor
```

または簡単なテストNodeを作る程度で構いません。

まずSchemaの正しさを優先してください。

---

# 35. 将来のCharacter UI構想

今後は、

```text
CAST ▶
```

として折り畳み可能なUIを想定します。

展開時:

```text
[ Alice ]
Prompt
LoRA
Reference
Appears in

[ Bob ]
Prompt
LoRA
Reference
Appears in

[ + Character ]
```

等。

パネルだらけにならないよう、

```text
collapsed by default
```

を前提にします。

今回実装しないでください。

---

# 36. KOMA選択時のCharacter Layout Mode

将来的にRegion Editorには、

```text
Page Layout Mode
Character Layout Mode
```

を持たせることを検討します。

Page Layout Mode:

```text
KOMA矩形を編集
```

Character Layout Mode:

```text
選択KOMA内のCharacter areaだけ編集
```

これによりUIの矩形過多を避けます。

今回実装しないでください。

---

# 37. Character参照構文

将来的なPrompt補助として、

```text
@alice
@bob
```

のようなCharacter参照を検討して構いません。

ただしモデルへその文字列を送る必要はありません。

Compilerが、

```text
@alice
↓
CAST_SPEC char_001
```

へ解決する内部マクロとして使えます。

今回実装は不要です。

---

# 38. Panel Sequential Generationを設計に入れる

将来的に、

```text
Whole Page Generation
```

だけでなく、

```text
Panel Sequential Generation
```

を正式な候補にしてください。

概念:

```text
PAGE SPEC
↓
KOMA 1 compile
↓
generate
↓
KOMA 2 compile
↓
generate
↓
...
↓
Page Composite
```

---

# 39. Panel Sequentialの利点

目的:

```text
Prompt肥大化回避
複数人物混線低減
KOMA単位のSeedガチャ
KOMA単位I2I
KOMA単位ControlNet
KOMA単位LoRA
KOMA単位再生成
```

です。

---

# 40. Whole Page Generationも残す

一方、

```text
Whole Page
```

は、

```text
全体構図
ページ全体の統一感
偶発的な面白さ
```

に価値があります。

したがって将来的には、

```text
Whole Page
Panel Sequential
```

の両モードを持てる構造を目標にしてください。

---

# 41. 今回のCompilerはまだ本格実装しない

Phase 3Aでは、

```text
Manga Scene Compiler
```

の入力・出力契約まで設計してください。

実際のConditioning生成は最低限の試験で構いません。

---

# 42. Manga Scene Compilerの将来入力

候補:

```text
REGION_SPEC
CAST_SPEC
Generation Config
Global Prompt
Global LoRA
```

---

# 43. Manga Scene Compilerの将来出力

候補:

```text
Compiled Page Prompt
Panel Compile Result
Character Compile Result
Mask Batch
Character Mask Batch
LoRA Plan
Control Plan
Debug JSON
```

今回すべて実装する必要はありません。

---

# 44. Compile Planを作る

Phase 3Aでは実際の生成より、

```text
このKOMAを生成する場合に何が適用されるか
```

をJSONで出力するNodeを作るとよいです。

例:

```json
{
  "panel_id": 1,
  "global_prompt": "...",
  "panel_prompt": "...",
  "characters": [
    {
      "character_id": "char_001",
      "base_prompt": "...",
      "override_prompt": "...",
      "area": {...},
      "loras": [...]
    }
  ],
  "global_loras": [...]
}
```

---

# 45. Scene Compiler Prototype

名称候補:

```text
Tegaki Manga Scene Compiler
```

Phase 3Aでは、

```text
REGION_SPEC + CAST_SPEC
↓
COMPILE_PLAN JSON
```

までで構いません。

まだCLIPやSamplerへ直結しなくてよいです。

---

# 46. Compilerで検証すること

最低限、

```text
KOMA1を指定
↓
KOMA1 Promptを取得
↓
出演Characterを取得
↓
Character Promptを取得
↓
Panel-local overrideを取得
↓
Global LoRA / Character LoRA / KOMA LoRA計画を集約
```

できること。

---

# 47. Character未登録Binding

KOMA側が、

```text
character_id = char_999
```

を参照しているがCAST_SPECに存在しない場合、

```text
ValueError
```

または明確なvalidation errorにしてください。

無言で無視しないでください。

---

# 48. 重複Character ID

CAST_SPEC内のCharacter ID重複は禁止してください。

---

# 49. Character name重複

表示名の重複は許容して構いません。

内部IDだけ一意にしてください。

---

# 50. Character数

初期設計では、

```text
固定最大人数
```

を極力設けないでください。

UI表示上は折り畳み等で整理します。

ただし安全上適切な上限が必要なら理由を明記してください。

---

# 51. Character area validation

areaが存在する場合:

```text
x
y
w
h
```

を0〜1のKOMA-local座標としてvalidateしてください。

REGION_SPEC geometryと同様の安全なNormalizerを再利用できるなら共通化してください。

---

# 52. Geometry validationの共通化

今回の境界値修正を機に、

```text
normalize_rect()
validate_rect()
```

等へ共通化して構いません。

Page RegionとCharacter Regionで同じバグを繰り返さないためです。

---

# 53. Schema version

以下すべてversionを持たせてください。

```text
REGION_SPEC
CAST_SPEC
MANGA_SCENE_SPEC / PAGE_SPEC
COMPILE_PLAN
```

将来migration可能な形にしてください。

---

# 54. Unknown field preservation

Phase 2.1と同様、

```text
既知フィールドを検証
未知フィールドは可能なら保持
```

してください。

ただし危険な型や壊れた構造はrejectしてください。

---

# 55. Test fixtureを作る

最低限、

```text
1 Character / 1 Panel
2 Characters / 1 Panel
1 Character / 2 Panels
2 Characters / 3 Panels
Character areaなし
Character areaあり
Global LoRAあり
Character LoRAあり
KOMA LoRAあり
```

のfixtureを用意してください。

---

# 56. 2人会話Sceneのテスト

重要な代表ケースです。

例:

```text
KOMA1
Alice
Bob
```

KOMA Prompt:

```text
classroom, two people talking, medium shot
```

Alice override:

```text
annoyed, looking at Bob
```

Bob override:

```text
laughing, looking at Alice
```

Compile Planでそれぞれが分離されること。

---

# 57. Panelごとの出演差分テスト

例:

```text
KOMA1: Alice + Bob
KOMA2: Alice only
KOMA3: Bob + Carol
```

Compile Planが正しく切り替わること。

---

# 58. Global LoRA集約テスト

例:

```text
Global:
StyleA 0.4
LineArtB 0.2

Alice:
AliceCharacter 0.8
```

KOMA1にAliceが出演する場合、

```text
Global LoRA Plan
+
Character LoRA Plan
```

が区別されて出力されること。

---

# 59. LoRAを実際にApplyしない

Phase 3Aでは、

```text
LoRA Plan
```

を作るだけで構いません。

本格適用は後Phaseです。

---

# 60. ControlNetもPlanだけ

将来的に、

```text
Panel Control
Character Control
```

を追加できるSchema余地を作って構いません。

今回ControlNet実処理は不要です。

---

# 61. 既存comfyui-comic-creator等の調査

既存漫画系Custom Nodeから、

```text
Panel handling
Crop / Composite
Character handling
Scene organization
```

等で参考になるものは調査して構いません。

ただし本プロジェクトへ丸ごと依存しないでください。

流用する場合は、

```text
何を参考にしたか
何を流用したか
ライセンス
なぜ必要か
```

を記録してください。

---

# 62. 既存PromptChain / Regional系も参考にする

複数Character Prompt分離の参考として、

```text
named prompt blocks
regional prompt
Attention Couple
mask based conditioning
```

系の既存実装を調査して構いません。

目的は、

```text
先人の設計を参考にする
```

ことであり、今回すべて導入することではありません。

---

# 63. UIは増やしすぎない

Phase 3Aで、

```text
Character Panel
Scene Editor
LoRA Browser
ControlNet UI
```

を一気に作らないでください。

まずデータ契約とCompile Planを固めます。

---

# 64. 新規ファイル候補

必要に応じて以下を作成してください。

```text
custom_nodes_custom/tegaki_manga_nodes/scene_spec.py
custom_nodes_custom/tegaki_manga_nodes/scene_compiler.py

docs/CAST_SPEC_V1.md
docs/MANGA_SCENE_SPEC_V1.md
docs/COMPILE_PLAN_V1.md

scripts/test_cast_spec.py
scripts/test_scene_compiler.py
```

正確な配置は既存構成に合わせて改善して構いません。

---

# 65. REGION_SPEC既存互換

既存Workflow 07を壊さないでください。

REGION_SPEC v1単体でも今まで通り動作すること。

CAST_SPECが存在しない場合、

```text
Characters = none
```

として安全に扱える設計を推奨します。

---

# 66. CAST_SPECなしの互換モード

例:

```text
REGION_SPEC only
↓
Compile Plan
↓
Panel prompt only
```

が成立すること。

---

# 67. CAST_SPEC validator

最低限:

```text
version
characters list
character id
id uniqueness
enabled bool
prompt str
negative_prompt str
loras list
```

をvalidateしてください。

---

# 68. LoRA entry validator

最低限:

```text
name = string
weight = number
enabled = bool
```

将来的な未知フィールドは保持。

---

# 69. Panel Binding validator

最低限:

```text
character_id exists
enabled bool
prompt_override string
area null or valid rect
```

をvalidateしてください。

---

# 70. Compile Plan validator

Compilerが出力するJSONもテスト可能にしてください。

---

# 71. データ契約ドキュメント

最低限以下を新規作成してください。

```text
CAST_SPEC_V1.md
MANGA_SCENE_DATA_CONTRACT.md
COMPILE_PLAN_V1.md
```

これらを外部AIが単独で読んでも構造が理解できるようにしてください。

---

# 72. MANGA_SCENE_DATA_CONTRACT.md に書くこと

最低限:

```text
1. PAGE / KOMA / CHARACTER関係
2. REGION_SPEC責務
3. CAST_SPEC責務
4. Panel Character Binding
5. Character local area
6. Global / KOMA / Character LoRA階層
7. Prompt階層
8. Single Source of Truth
9. Unknown field policy
10. Schema versioning
11. Whole Page / Panel Sequential両対応
12. 将来ControlNet / RLL拡張
```

---

# 73. Scene Compiler Report

新規に、

```text
PHASE3A_SCENE_DATA_CONTRACT_REPORT.md
```

を作成してください。

最低限:

```text
1. 境界値修正
2. REGION_SPEC変更有無
3. CAST_SPEC v1
4. Binding schema
5. Character local area
6. LoRA階層設計
7. Prompt階層設計
8. Compile Plan
9. Scene Compiler prototype
10. Validation
11. Test結果
12. 既存Workflow互換
13. 既知の問題
14. Phase 3B案
15. Gemini独自判断で変更した点
```

---

# 74. Test

最低限:

```text
Existing REGION_SPEC tests
Existing state transition tests
Runtime source identity
Wildcard patch
txt2img regression

CAST_SPEC validation
Duplicate character id
Invalid character binding
Character local rect
1 char / 1 panel compile
2 char / 1 panel compile
panel appearance differences
Global LoRA plan
Character LoRA plan
KOMA LoRA plan
CAST_SPEC absent compatibility
```

を確認してください。

---

# 75. Phase 3Aでは画像品質評価をしない

今回のCompilerはまだ生成画像へ本格接続しないため、

```text
Regional Promptが効いたか
Characterが分離できたか
LoRAが局所化したか
```

の画質評価はまだ不要です。

まずデータが正しくcompileされることを確認します。

---

# 76. Phase 3Bへの予定

Phase 3A完了後、

```text
Phase 3B
Manga Scene Compiler → Conditioning
```

へ進みます。

予定:

```text
Global Prompt
↓
Global Conditioning

KOMA Prompt
↓
Panel Conditioning

Character Prompt
↓
Character Conditioning

Character area
↓
Mask / Attention Couple等

Conditioning Combine
```

---

# 77. Phase 3Cへの予定

Phase 3Bの後、

```text
Character Panel UI
```

を実装予定です。

それまではSchemaとCompile Planを優先してください。

---

# 78. Phase 4予定

```text
Panel Sequential Generation
I2I
ControlNet
Crop / Composite
```

---

# 79. Phase 5予定

```text
Global LoRA
KOMA LoRA
Character LoRA
Regional LoRA / RLL
```

既存RegionalSampler / LoRA Hooks等も比較します。

---

# 80. GITHUB.TXT更新

Phase 3A実装後、

まず実装・テスト・報告書をcommitしてください。

```text
Commit A
Phase 3A Manga Scene Data Contract
```

そのSHAを取得。

その後、

```text
Review Target Commit SHA: A
```

をGITHUB.TXTへ記載。

GITHUB.TXTのみ別commitしてください。

---

# 81. GITHUB.TXTへ追加するリンク

最低限:

```text
PHASE3A_SCENE_DATA_CONTRACT_REPORT.md
MANGA_SCENE_DATA_CONTRACT.md
CAST_SPEC_V1.md
COMPILE_PLAN_V1.md

scene_spec.py
scene_compiler.py

test_cast_spec.py
test_scene_compiler.py

更新した region_editor.py
更新した test_region_spec.py
```

のPinned URL / Raw URLを掲載してください。

---

# 82. Acceptance Criteria

以下を満たした場合のみPhase 3A完了としてください。

```text
[ ] REGION_SPEC境界値問題修正
[ ] 極小Region Preview安全化
[ ] regions不正要素reject
[ ] 既存REGION_SPEC互換
[ ] CAST_SPEC v1定義
[ ] Character ID一意
[ ] Panel Character Binding定義
[ ] Character local area定義
[ ] area=null対応
[ ] Global/KOMA/Character LoRA階層定義
[ ] Prompt階層定義
[ ] Single Source of Truth維持
[ ] CAST_SPECなし互換
[ ] Compile Plan生成
[ ] 2 Character / 1 Panel compile成功
[ ] Panelごとの出演差分compile成功
[ ] Invalid binding検知
[ ] Unknown fields保持
[ ] 全新規テストPASS
[ ] 既存Region test PASS
[ ] 既存txt2img非破壊
[ ] GITHUB.TXT更新
```

---

# 83. Phase 3B Readiness

報告書末尾に、

```text
PHASE 3B READINESS:
GO / HOLD
```

を記載してください。

GO条件:

```text
REGION_SPEC
CAST_SPEC
Binding
Compile Plan
```

のデータ契約が安定し、

```text
1つのKOMAについて
何をPromptとして使うか
どのCharacterが出演するか
どのLoRAが候補か
どのareaが対応するか
```

を一意に決定できることです。

---

# 84. 最終回答

作業終了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3A_SCENE_DATA_CONTRACT_REPORT Raw:
MANGA_SCENE_DATA_CONTRACT Raw:
CAST_SPEC_V1 Raw:
COMPILE_PLAN_V1 Raw:

scene_spec.py Pinned Raw:
scene_compiler.py Pinned Raw:

CAST Test Raw:
Scene Compiler Test Raw:

PHASE 3B READINESS:
```

外部AIでレビューします。

---

# 最終設計原則

今回のPhase 3Aで重要なのは、

```text
Promptを増やすこと
```

ではありません。

漫画シーンの意味を、

```text
Global
KOMA
Character
LoRA
Area
Control
```

へ分離し、

```text
必要なKOMAを生成するときだけ
必要な情報をCompilerが取り出す
```

構造を作ることです。

最終的には、

```text
User UI
↓
Manga Scene Data
↓
Manga Scene Compiler
↓
ComfyUI Backend
```

とします。

UIは後で何度でも変更できます。

そのためPhase 3Aでは、GUIよりもデータ契約を優先してください。

また本プロジェクトは、

```text
完全制御された最終漫画生成機
```

ではなく、

```text
精度の高い下絵
構図候補
キャラクター配置
演技
背景
複数人物シーン
```

を効率よく作りながら、

```text
ブレインストーミング性
```

も残す制作支援環境を目標とします。
