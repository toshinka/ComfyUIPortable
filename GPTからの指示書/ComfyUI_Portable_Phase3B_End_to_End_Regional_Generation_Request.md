# ComfyUI Portable Phase 3B — End-to-End Manga Regional Generation 指示書

## 0. 今回の目的

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
95ab6023f07183cf9418c6a036c1c0186a3e183a
```

Phase 3A / 3A.1 までで、

```text
REGION_SPEC
CAST_SPEC
Panel ↔ Character Binding
COMPILE_PLAN
Canonical LoRA Entry
Negative Prompt階層
```

というデータ契約はかなり固まりました。

一方、現状の `07` / `08` は、

```text
Region Editor
Scene Compiler
JSON / Preview
```

までで止まっており、

```text
特定KOMAに特定Promptが効く
Character AreaへCharacter Promptが効く
そのConditioningがSamplerへ入り、実際の画像になる
```

というMRPの根幹部分がまだ実生成へ接続されていません。

今回のPhase 3Bではここを最優先で実装します。

目標は、

```text
01 Basic Generation
+
03 Regional Prompt
+
06 Global LoRA
+
07 Visual Region Editor
+
08 Scene / CAST Contract
↓
実際に動く Manga Regional Generation
```

です。

今回の最後に、これまでの成果を一本につないだ実生成Workflowを必ず作成してください。

---

# 1. 今回の優先順位

今回から一定期間、

```text
仕様書を増やすこと
```

より、

```text
実際の生成画像で機能を証明すること
```

を優先してください。

最低限、

```text
REGION_SPECで設定したKOMA Prompt
↓
指定KOMAへ相対的に強く効く

Character Binding Prompt
↓
Character Areaへ相対的に強く効く
```

ことを画像で確認します。

完全な漏れゼロは要求しません。

評価基準は、

```text
Target Region influence
>
Outside Region influence
```

です。

---

# 2. Phase 3Bの進め方

今回は以下の順番で進めてください。

```text
Phase 3B-0
Pre-Conditioning Hardening

Phase 3B-1
Page Compile / Mask Projection

Phase 3B-2
Conditioning Builder

Phase 3B-3
End-to-End Sampling

Phase 3B-4
A/B Artistic Validation

最後:
09_MANGA_REGIONAL_GENERATION_POC.json
```

各段階を小さくテストしてから次へ進んでください。

---

# 3. Phase 3B-0 — 前回レビューの小修正

Conditioning実装前に、以下4点だけ先に修正してください。

## 3.1 COMPILE_PLAN Validatorを境界Validatorとして強化

現在の `validate_compile_plan()` を、Phase 3Bの正式入力境界として十分な深さまで強化してください。

最低限:

```text
version
status
target_panel_id
canvas
panel
global_prompt
global_negative_prompt
characters
lora_plan
```

を検証。

さらに以下も検証してください。

```text
canvas.width / height
→ positive integer
→ boolは禁止

target_panel_id
→ strict int
→ boolは禁止

panel.id
→ strict int
→ target_panel_idと一致

panel.enabled
→ strict bool

panel.geometry
→ valid normalized rect

panel.prompt
panel.negative_prompt
→ strict string

character.area
→ null または valid normalized rect

character.metadata
→ dict

character_loras
→ character_id / character_name + Canonical LoRA Entry
```

## 3.2 Legacy `weight` をCanonical出力から除去

入力互換:

```json
{
  "name": "A",
  "weight": 0.8
}
```

は維持。

正規化後:

```json
{
  "name": "A",
  "model_weight": 0.8,
  "clip_weight": 0.8
}
```

とし、legacy `weight` はCanonical出力から削除してください。

## 3.3 LoRA weightをfinite値に限定

以下をrejectしてください。

```text
NaN
+Infinity
-Infinity
```

`math.isfinite()` 等を使用してください。

負値や1.0超えは研究用途があるため、現時点では禁止しなくて構いません。

## 3.4 Workflow 08はDebug Harnessとして最低限改善

`08_MANGA_SCENE_CONTRACT_TEST.json` は残します。

ただし、Scene Compilerが実行されず出力も見えない構造なら改善してください。

必要なら独自の小さな、

```text
Tegaki Compile Plan Inspector
```

を作成して構いません。

条件:

```text
OUTPUT_NODE = True
```

等を利用し、Queue時にScene Compilerまで実行されること。

最低限表示:

```text
Compiled Positive
Compiled Negative
Character Count
Global LoRA
KOMA LoRA
Character LoRA
Character Area
```

新しい大型依存Custom Nodeは追加しないでください。

08はあくまでDebug用です。

---

# 4. Phase 3B-1 — Page Compile Planを作る

現在の `COMPILE_PLAN` は1 KOMA単位です。

Whole Page Regional Generationでは、

```text
KOMA1
KOMA2
KOMA3
...
```

すべてのActive Panelを一回の生成へ渡す必要があります。

そのため、ページ単位のCompile結果を作ってください。

名称候補:

```text
PAGE_COMPILE_PLAN
```

または、

```text
MANGA_PAGE_COMPILE_PLAN
```

---

# 5. PAGE_COMPILE_PLANの目的

PAGE_COMPILE_PLANは、

```text
REGION_SPEC
CAST_SPEC
↓
active KOMAすべてのCOMPILE_PLAN
```

を集約します。

例:

```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "active_panel_ids": [1, 2, 3],
  "global_prompt": "...",
  "global_negative_prompt": "...",
  "global_loras": [],
  "panels": [
    {...},
    {...},
    {...}
  ]
}
```

正確なSchemaは改善して構いません。

---

# 6. 既存Scene Compilerロジックを再利用する

1 KOMA用の既存ロジックをコピーして別実装にしないでください。

推奨:

```text
compile_panel_data(...)
```

等の純粋関数へ切り出し、

```text
Tegaki Manga Scene Compiler
Tegaki Manga Page Compiler
```

の双方から再利用してください。

---

# 7. Active Panelだけを対象にする

対象:

```text
get_active_panel_ids(REGION_SPEC)
```

を使用。

```text
1..panel_count
```

を無条件処理しないでください。

---

# 8. CASTなし互換

ページ内のすべてのActive KOMAにCharacter Bindingが無い場合、

```text
CASTなし
```

でも生成可能。

1つでもCharacter Bindingがあれば、

```text
有効なCAST_SPEC必須
```

です。

---

# 9. PAGE_COMPILE_PLAN Validator

Phase 3Bで新しい契約を作る場合はValidatorも同時に作ってください。

最低限:

```text
version
canvas
active_panel_ids
panels
global prompt/negative
global loras
```

を確認。

各panel planは既存 `validate_compile_plan()` を通してください。

---

# 10. Phase 3B-1 — Page座標Maskへ投影する

REGION_SPECのKOMA geometryはPage座標です。

これをCanvas解像度へ投影し、

```text
KOMA Mask
```

を生成してください。

---

# 11. Character AreaをPage座標へ変換

Character AreaはKOMA-localです。

```text
KOMA:
x = kx
y = ky
w = kw
h = kh

Character:
x = cx
y = cy
w = cw
h = ch
```

Page座標:

```text
page_x = kx + kw * cx
page_y = ky + kh * cy
page_w = kw * cw
page_h = kh * ch
```

としてください。

その後Canvas pixel maskへ変換。

---

# 12. Character Area = null

`area = null` のCharacterは、初期POCでは、

```text
当該KOMA全体をCharacter Maskとして使用
```

するか、

```text
Character regional conditioningを無効にし、
KOMA Prompt側へ自然結合する
```

かのどちらかにしてください。

推奨は初期段階では、

```text
KOMA全体をMask
```

です。

理由を報告書へ明記してください。

---

# 13. Mask Builder

名称候補:

```text
Tegaki Manga Mask Builder
```

またはConditioning Builder内部機能でも構いません。

最低限出力:

```text
Panel Mask Batch
Panel IDs JSON

Character Mask Batch
Character Binding IDs JSON

Mask Preview Image
```

デバッグできることを優先してください。

---

# 14. Mask Preview

生成前に、

```text
KOMA Mask
Character Mask
```

がどこへ投影されているか画像で確認できるようにしてください。

特にKOMA1内部の、

```text
Alice = 左
Bob = 右
```

が視覚的に確認できること。

---

# 15. Phase 3B-2 — Conditioning Builder

今回の中心実装です。

名称候補:

```text
Tegaki Manga Conditioning Builder
```

入力は可能な限り、

```text
CLIP
PAGE_COMPILE_PLAN
```

としてください。

REGION_SPEC / CAST_SPECを直接再解釈せず、Compile Planを境界として使用してください。

---

# 16. Conditioning Builderの責務

以下を実際のComfyUI `CONDITIONING` へ変換してください。

```text
Global Positive
Panel Positive
Character Positive

Global Negative
Panel Negative
Character Negative
```

---

# 17. ComfyUI Core APIを優先する

現在インストールされているComfyUI versionを確認し、

可能なら、

```text
CLIPTextEncode
ConditioningSetMask
ConditioningCombine
```

等のCore Node実装を再利用してください。

内部Tensor構造を独自に手組みするより、

```text
現在のComfyUI Core API / Core Node class
```

を利用する方を優先してください。

バージョン依存がある場合は報告書へ記録してください。

---

# 18. Global Conditioning

Global Prompt:

```text
ページ全体
```

へunmasked conditioningとして適用。

Global Negativeも同様。

---

# 19. Panel Conditioning

各KOMA Prompt:

```text
そのKOMA Mask
```

へ適用してください。

概念:

```text
Panel Prompt
↓ CLIP encode
↓ ConditioningSetMask(panel mask)
```

---

# 20. Character Conditioning

各Character:

```text
base_prompt
+
override_prompt
```

のPositiveを、

```text
Character Mask
```

へ適用。

Negative:

```text
base_negative
+
override_negative
```

もCharacter Maskへ適用してください。

---

# 21. Conditioning Strength

初期POCでは、

```text
Panel Mask Strength = 1.0
Character Mask Strength = 1.0
```

をdefaultにしてください。

将来UI調整可能にする余地を残してください。

---

# 22. Conditioning Combine

概念:

```text
Global
+
Panel 1
+
Panel 2
+
Panel 3
+
Character Alice
+
Character Bob
...
```

をComfyUI ConditioningとしてCombine。

Positive / Negativeを別々に作成。

---

# 23. Conditioning Builder出力

最低限:

```text
positive CONDITIONING
negative CONDITIONING

panel_mask_batch
character_mask_batch

debug_json
```

---

# 24. Dynamic Character数

Character数は固定2人にしないでください。

ComfyUI Nodeの入出力仕様上難しい場合、

```text
PAGE_COMPILE_PLAN内部をループ
```

して内部的にCombineしてください。

---

# 25. 最初はCore Masked ConditioningをOracleにする

最初の実証は、

```text
ConditioningSetMask
+
ConditioningCombine
```

相当で構いません。

これは03の固定2領域Workflowを、

```text
REGION_SPEC / CAST_SPEC driven
```

へ一般化する工程です。

---

# 26. Isolationが弱い場合のFallback

Core Masked Conditioningで局所性が不足する場合のみ、

既に導入済みの、

```text
Impact Pack RegionalSampler
```

を比較候補にしてください。

順番:

```text
A. Core ConditioningSetMask
↓
A/B画像評価
↓
不足が明確
↓
B. Impact RegionalSampler
```

最初から複数Backendを混ぜないでください。

---

# 27. 今回は広げすぎない

今回は、

```text
Omost
DenseDiffusion
IPAdapter
RLL
```

へ広げないでください。

Regional Promptの基本動作をまず通します。

---

# 28. Phase 3B-3 — End-to-End Sampling

Conditioning Builderが通ったら、

既存01/03を参考に、

```text
Checkpoint
↓
Global LoRA
↓
CLIP
↓
Manga Conditioning Builder
↓
KSampler
↓
VAE Decode
↓
Preview / Save
```

まで接続してください。

---

# 29. Global LoRAは実際に適用する

今回、

```text
GLOBAL LoRA
```

は実際に機能させてください。

KOMA / Character LoRAはまだPlanだけでも構いません。

---

# 30. Global LoRAの適用方法

既存の、

```text
TegakiLoraPromptLoader
```

を再利用してください。

Canonical Global LoRAから必要なら、

```text
<lora:name:model_weight:clip_weight>
```

相当へ変換する小さなAdapterを作って構いません。

同じLoRAを別々のUI欄へ二重入力する最終構造にはしないでください。

---

# 31. Global LoRA SSOT

最終的には、

```text
PAGE_COMPILE_PLAN.global_loras
↓
Global LoRA Adapter
↓
TegakiLoraPromptLoader
```

を優先してください。

POC段階でどうしても困難な場合のみ一時的重複入力を許可します。

その場合は、

```text
TEMPORARY / DEBUG ONLY
```

と明記してください。

---

# 32. KOMA / Character LoRAは今回まだ適用しなくてよい

今回の必須条件は、

```text
Regional Prompt
Character Prompt
Global LoRA
```

です。

以下はまだPlan表示のみで構いません。

```text
KOMA LoRA
Character LoRA
```

Phase 5でRegional LoRAとして扱います。

---

# 33. Phase 3B-4 — 画像A/B検証

Unit Test PASSだけでは完了にしないでください。

固定Seedで実際の生成画像を比較してください。

---

# 34. 基準Scene

最低限3 KOMAページ。

```text
KOMA1:
classroom, two people talking, medium shot

Alice:
left area
Bobと明確に異なる髪色・服装

Bob:
right area
Aliceと明確に異なる髪色・服装

KOMA2:
corridor
Alice only

KOMA3:
sunset rooftop
no character
```

既存08サンプルを流用して構いません。

---

# 35. A/B Test 1 — Panel Localization

固定Seed。

A:

```text
KOMA1 = classroom
```

B:

```text
KOMA1 = convenience store interior
```

他は完全固定。

期待:

```text
KOMA1中心に変化
KOMA2 / KOMA3は相対的に維持
```

完全不変は要求しません。

---

# 36. A/B Test 2 — Alice Localization

固定Seed。

A:

```text
Alice = blonde hair
```

B:

```text
Alice = blue hair
```

期待:

```text
KOMA1左側 / Alice対象領域を中心に変化
Bob側への影響は相対的に弱い
```

---

# 37. A/B Test 3 — Bob Localization

同様にBobだけ変更してください。

---

# 38. A/B Test 4 — Global Prompt

Global Promptだけ変更。

期待:

```text
ページ全体へ影響
```

Regional Promptとの作用範囲差が確認できること。

---

# 39. A/B Test 5 — Global LoRA

Global LoRA ON / OFF。

期待:

```text
ページ全体へ画風影響
```

---

# 40. 評価は定性的でよい

現段階では数値的な画像差分スコアは必須ではありません。

報告書へ、

```text
Targetへの影響
Leakage
構図崩れ
境界Seam
Character属性混線
```

を記録してください。

---

# 41. Leakageは失敗扱いしすぎない

以前の方針どおり、

```text
指定領域外へ多少効く
```

ことは許容します。

問題は、

```text
TargetよりOutsideの方が同程度以上に変わる
```

場合です。

---

# 42. 失敗時の切り分け

Regional Promptが弱い場合、

以下を分けて確認してください。

```text
Mask位置が間違っている
CLIP Conditioningが間違っている
ConditioningSetMaskの挙動
Prompt自体が弱い
Illustrious側の属性混線
```

いきなりRLLや別Backendへ飛ばないでください。

---

# 43. Character Areaの見本

KOMA1では、

```text
Alice:
x=.05
y=.10
w=.42
h=.80

Bob:
x=.53
y=.10
w=.42
h=.80
```

程度の左右分割で構いません。

重なりも多少許容します。

---

# 44. 09_MANGA_REGIONAL_GENERATION_POC.json を作成する

今回の最終成果として新規:

```text
workflows/09_MANGA_REGIONAL_GENERATION_POC.json
```

を必ず作成してください。

区分:

```text
EXPERIMENTAL / END-TO-END POC
```

---

# 45. Workflow 09の意味

このWorkflowは、

```text
これまで01〜08で作ったものが、
実際の生成へどうつながるか
```

を示す最初の集大成Workflowです。

---

# 46. Workflow 09の最低構成

左から右へ概ね:

```text
[1 MODEL]
Checkpoint
Global LoRA

[2 PAGE]
Tegaki Manga Region Editor

[3 CAST / SCENE]
CAST_SPEC
Page Compiler

[4 MASK DEBUG]
Panel Masks
Character Masks
Mask Preview

[5 CONDITIONING]
Manga Conditioning Builder

[6 SAMPLE]
KSampler

[7 OUTPUT]
VAE Decode
Preview
Save
```

---

# 47. Workflow 09で実際に生成する

09は07/08と違い、

```text
KSampler
VAE Decode
PreviewImage / SaveImage
```

まで必ず接続してください。

Queue Promptで本当に生成されること。

---

# 48. Workflow 09の初期サンプル

3 KOMA + 2 Characters。

最低限:

```text
KOMA1 = Alice + Bob
KOMA2 = Alice
KOMA3 = background only
```

を初期値として入れてください。

---

# 49. Workflow 09のUI完成度は求めない

まだ開発用Workflowです。

配線が多くても構いません。

ただし、

```text
どこがUser Input
どこがInternal
どこがDebug
```

かGroupで明示してください。

---

# 50. User Input Group

最低限:

```text
Global Prompt
Global Negative
Global LoRA

KOMA Layout / KOMA Prompt

CAST_SPEC
Character Prompt / Area

Seed
Steps
CFG
```

が見つけやすいこと。

---

# 51. Internal Group

```text
Compile Plan
Mask conversion
Conditioning
```

はInternalとして分けてください。

---

# 52. Debug Group

```text
Mask Preview
Compile Plan Inspector
```

を置いてください。

---

# 53. ControlNetは今回必須ではない

05のControlNetは重要ですが、

今回の最優先は、

```text
Regional Promptを実際に動かす
```

ことです。

09でRegional Promptが安定する前にControlNetまで詰め込まないでください。

---

# 54. 次の統合先はControlNet

09がPASSしたら、

```text
09
+
05 ControlNet
```

を次統合候補にします。

必要なら将来、

```text
10_MANGA_COMPOSITION_INTEGRATION_TEST.json
```

として分けて構いません。

今回09が安定した場合だけ、低リスクならControlNet branchをdisabled groupとして置いても構いません。

無理に入れないでください。

---

# 55. I2Iも今回必須ではない

02 I2Iも最終的には重要ですが、

まずtxt2img Whole Page Regional Generationを成立させます。

---

# 56. Panel Sequential Generationは今回まだ行わない

今回:

```text
Whole Page
+
Regional Prompt
```

を先に証明。

その後、

```text
Panel Sequential
```

と比較します。

---

# 57. 将来の比較

Whole Page:

```text
全体統一感
偶発性
```

Panel Sequential:

```text
Prompt短縮
混線低減
コマ単位再生成
```

の比較はPhase 4以降。

---

# 58. テストスクリプト

最低限新規:

```text
scripts/test_page_compile_plan.py
scripts/test_conditioning_builder.py
```

を作成してください。

---

# 59. test_page_compile_plan.py

最低限:

```text
active panel ids
3 KOMA compile
CASTなし背景KOMA
2 Characters in KOMA1
1 Character in KOMA2
0 Character in KOMA3
Character area page projection
area=null
invalid binding
```

---

# 60. test_conditioning_builder.py

実行可能な範囲で、

```text
Global conditioning作成
Panel conditioning数
Character conditioning数
Positive output
Negative output
Mask shape
```

を確認してください。

ComfyUI runtime依存が強い場合はintegration testとして扱って構いません。

---

# 61. Runtime Generation Test

必ず実際のComfyUI API / Queueで、

```text
Workflow 09相当
```

を実行してください。

最低1枚生成。

---

# 62. A/B生成結果を保存

例:

```text
output/Tegaki/RegionalPOC/
```

へ、

```text
panel_A
panel_B
alice_A
alice_B
bob_A
bob_B
global_A
global_B
```

等、比較可能な名前で保存してください。

---

# 63. 報告書

新規:

```text
PHASE3B_END_TO_END_REGIONAL_GENERATION_REPORT.md
```

最低限:

```text
1. Pre-3B Hardening
2. PAGE_COMPILE_PLAN
3. Mask Projection
4. Character Local → Page座標
5. Conditioning Builder
6. Positive階層
7. Negative階層
8. Global LoRA実適用
9. Workflow 09
10. Runtime生成結果
11. Panel A/B
12. Alice A/B
13. Bob A/B
14. Leakage評価
15. Seam評価
16. Illustriousでの属性混線
17. Core Masked Conditioningの限界
18. Impact RegionalSampler比較の要否
19. 既知の問題
20. 次Phase提案
21. Gemini独自判断
```

---

# 64. 画像評価結果は誇張しない

以下を区別してください。

```text
動いた
局所性がある
十分な局所性がある
制作に使える
```

同じ意味にしないでください。

---

# 65. Workflow Index更新

`docs/WORKFLOW_INDEX.md` に09を追加。

例:

```text
09_MANGA_REGIONAL_GENERATION_POC
区分: EXPERIMENTAL / END-TO-END POC
目的: REGION_SPEC + CAST_SPEC → Masked Conditioning → 実画像生成
```

---

# 66. 03との関係

03:

```text
Fixed 2-region manual wiring
```

09:

```text
REGION_SPEC / CAST_SPEC driven dynamic regional generation
```

と説明してください。

03はOracle / referenceとして残します。

---

# 67. 08との関係

08:

```text
Data Contract / Debug
```

09:

```text
Actual Generation
```

です。

---

# 68. 04との関係

04は引き続き、

```text
NOT YET REGIONAL LoRA
```

です。

09でCharacter LoRAをRegional適用できたと誤記しないでください。

---

# 69. Acceptance Criteria — コード

以下を満たすこと。

```text
[ ] COMPILE_PLAN Validator強化
[ ] legacy weight除去
[ ] NaN/Inf LoRA reject
[ ] Workflow 08 Inspector実行可能
[ ] PAGE_COMPILE_PLAN実装
[ ] PAGE_COMPILE_PLAN Validator
[ ] Active Panel compile
[ ] Panel Mask生成
[ ] Character Local → Page Mask
[ ] area=null安全処理
[ ] Conditioning Builder実装
[ ] Global Positive/Negative
[ ] Panel Positive/Negative
[ ] Character Positive/Negative
[ ] Global LoRA実適用
```

---

# 70. Acceptance Criteria — 実生成

以下を満たすこと。

```text
[ ] Workflow 09 Queue実行成功
[ ] 実画像生成成功
[ ] KOMA1 Prompt変更がKOMA1へ相対的に強く反映
[ ] Alice変更がAlice領域へ相対的に強く反映
[ ] Bob変更がBob領域へ相対的に強く反映
[ ] Global Promptが全体へ反映
[ ] Global LoRAが全体へ反映
[ ] Mask Previewが実領域と一致
```

---

# 71. 完全分離はAcceptanceにしない

以下は必須ではありません。

```text
Outside influence = 0
完全な属性分離
完全なSeamなし
```

POCでは、

```text
相対的局所性
```

が確認できれば進めます。

---

# 72. Core方式が弱すぎた場合

A/B比較の結果、

```text
TargetとOutsideがほぼ同程度に変化
```

する場合は、

```text
Core ConditioningSetMask Oracle result:
INSUFFICIENT
```

と明記。

その上で、

```text
Impact RegionalSampler comparison required
```

としてください。

勝手にRLL実装へ進まないでください。

---

# 73. Phase 3B終了判定

報告書末尾:

```text
REGIONAL PROMPT POC:
PASS / PARTIAL / FAIL

NEXT BACKEND:
CORE MASKED CONDITIONING
or
IMPACT REGIONAL SAMPLER COMPARISON
```

を記載。

---

# 74. 次Phase

09が十分動けば、

```text
Phase 3C
Character / CAST UI
```

へ進んでも構いません。

または実制作上ControlNetが先なら、

```text
Phase 4A
ControlNet Integration
```

でも構いません。

画像結果を見て判断します。

---

# 75. GITHUB.TXT 二段Commit

まず、

```text
Commit A
Phase 3B End-to-End Regional Generation
```

として、

```text
実装
テスト
Workflow 09
報告書
```

をcommit。

そのSHAを取得。

次にGITHUB.TXTへ、

```text
Review Target Commit SHA: A
```

を書き、

GITHUB.TXTだけ別commit。

---

# 76. GITHUB.TXTへ追加

最低限:

```text
PHASE3B_END_TO_END_REGIONAL_GENERATION_REPORT.md

PAGE_COMPILE_PLAN仕様
Conditioning Builder実装
Mask Builder実装

test_page_compile_plan.py
test_conditioning_builder.py

08_MANGA_SCENE_CONTRACT_TEST.json
09_MANGA_REGIONAL_GENERATION_POC.json

A/B Test output path / summary
```

のPinned Rawを追加してください。

---

# 77. 最終回答

作業終了時:

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3B_END_TO_END_REGIONAL_GENERATION_REPORT Raw:

Page Compiler Raw:
Conditioning Builder Raw:
Mask Builder Raw:

Page Compile Test Raw:
Conditioning Test Raw:

Workflow 08 Raw:
Workflow 09 Raw:

REGIONAL PROMPT POC:
PASS / PARTIAL / FAIL

NEXT BACKEND:
```

を提示してください。

---

# 最終方針

今回のPhase 3Bは、

```text
新しいデータ形式を作るためのPhase
```

ではありません。

今まで作った、

```text
REGION_SPEC
CAST_SPEC
COMPILE_PLAN
```

を、

```text
実際のIllustrious生成
```

へ接続するPhaseです。

成功の判定は、

```text
JSONが正しい
```

だけではありません。

```text
KOMA PromptがそのKOMAへ効く
Character PromptがそのCharacter領域へ効く
Global Prompt / Global LoRAは全体へ効く
```

ことを、実際の固定Seed A/B画像で確認してください。

Workflow 09は、

```text
01〜08の成果を初めて実画像生成へまとめた
集大成の最小実働版
```

として作成してください。
