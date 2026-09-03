# ComfyUI Portable Phase 3A.1 — Scene Contract Hardening 指示書

## 0. 今回の目的

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
b628f3d57699da615eb45ce6f11ab018a38d591d
```

Phase 3A では、

```text
PAGE
 ├ GLOBAL
 ├ KOMA / REGION_SPEC
 └ CAST / CAST_SPEC
```

というManga Scene Data Contractが成立し、

```text
REGION_SPEC
+
CAST_SPEC
+
Panel ↔ Character Binding
↓
COMPILE_PLAN
```

まで実装されました。

今回のPhase 3A.1では、本格的なConditioning接続へ進む前に、Scene Contractの曖昧な部分を固定します。

主な対象:

```text
1. CASTなし + Character Bindingあり の扱い
2. LoRAのSingle Source of Truth
3. 2値/3値LoRA記法の正式仕様
4. Prompt内LoRAタグの階層ルール
5. Negative Prompt階層
6. COMPILE_PLAN Validator
7. Schema strictness
8. panel_count用語整理
9. Scene Contract確認用テストWorkflow
```

今回は画像品質を詰めません。

Phase 3Bで、

```text
COMPILE_PLAN
↓
Global / Panel / Character Conditioning
```

へ安全に接続できる状態を作ることが目的です。

---

# 1. 作業前確認

最初に以下を確認してください。

```text
git rev-parse HEAD
git status
git branch --show-current
git remote -v
```

以下を必ず読んでください。

```text
ComfyUIPortable/GITHUB.TXT
ComfyUIPortable/PHASE3A_SCENE_DATA_CONTRACT_REPORT.md

ComfyUIPortable/docs/MANGA_SCENE_DATA_CONTRACT.md
ComfyUIPortable/docs/CAST_SPEC_V1.md
ComfyUIPortable/docs/COMPILE_PLAN_V1.md

ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/region_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/scene_spec.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/scene_compiler.py

ComfyUIPortable/scripts/test_cast_spec.py
ComfyUIPortable/scripts/test_scene_compiler.py
ComfyUIPortable/scripts/test_region_spec.py
```

既存の、

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG
02_ILLUSTRIOUS_I2I
07_MANGA_REGION_EDITOR_UI_TEST
```

を壊さないでください。

---

# 2. 基本方針は維持する

以下は変更しません。

```text
REGION_SPEC
→ KOMAの正本

CAST_SPEC
→ Character masterの正本

REGION_SPEC.regions[].characters
→ 出演Bindingの正本

COMPILE_PLAN
→ 特定KOMAを生成するための実行計画
```

Character Areaは、

```text
KOMA-local 0〜1座標
```

を維持。

```text
area = null
```

も引き続き正式サポートしてください。

---

# 3. CASTなし + Character Bindingあり を禁止する

現在のScene Compilerでは、

```text
CAST_SPECなし
+
KOMA側にCharacter Bindingあり
```

でも、空のCharacter masterとしてCompileできる余地があります。

これは契約違反とします。

ルール:

```text
KOMAにCharacter Bindingなし
+
CAST_SPECなし
→ OK

KOMAにCharacter Bindingあり
+
CAST_SPECあり
→ OK

KOMAにCharacter Bindingあり
+
CAST_SPECなし
→ ValueError
```

としてください。

---

# 4. CAST JSON Syntax Errorの扱い

CAST_SPEC文字列が、

```text
{ broken json
```

のように壊れている場合、Bindingが存在しないなら警告 + empty CASTへのfallbackでも構いません。

ただしBindingが存在する場合、

```text
CASTが壊れているためCharacter解決不能
```

として明示的に停止する方が安全です。

制作データを「空Character」として続行しないでください。

---

# 5. CASTなしBinding Regression Test

追加してください。

ケースA:

```text
KOMA characters = []
CAST_SPEC = {}
→ PASS
```

ケースB:

```text
KOMA characters = [char_alice]
CAST_SPEC = {}
→ ValueError
```

ケースC:

```text
KOMA characters = [char_alice]
CAST_SPEC = broken JSON
→ ValueError
```

---

# 6. LoRAのSingle Source of Truthを正式化する

LoRAは以下の3階層を維持します。

```text
GLOBAL LoRA
KOMA LoRA
CHARACTER LoRA
```

ただし文字列と構造化配列を別々の正本にしないでください。

基本原則:

```text
ユーザー入力
↓
LoRA Parser / Normalizer
↓
Canonical LoRA Entry
↓
COMPILE_PLAN
```

です。

---

# 7. Canonical LoRA Entryを定義する

Phase 3Bへ入る前に、LoRA Entryを正式に定義してください。

推奨Canonical形式:

```json
{
  "name": "alice_character",
  "enabled": true,
  "model_weight": 0.8,
  "clip_weight": 0.5,
  "metadata": {}
}
```

`model_weight` / `clip_weight` を分離してください。

理由:

```text
<lora:name:0.8>
<lora:name:0.8:0.5>
```

の双方を失わず表現するためです。

---

# 8. 既存weightフィールドとの互換

現在のCAST_SPEC等では、

```json
{
  "name": "alice_v1",
  "weight": 0.8,
  "enabled": true
}
```

が使用されています。

既存データを壊さないでください。

入力互換として、

```text
weightのみ
→ model_weight = weight
→ clip_weight = weight
```

へ正規化してください。

Canonical出力側は、

```text
model_weight
clip_weight
```

を優先してください。

---

# 9. LoRA入力の競合検出

以下のように、

```json
{
  "weight": 0.8,
  "model_weight": 0.5
}
```

と意味の異なる値が同時指定された場合は、

```text
conflicting values
→ ValueError
```

を推奨します。

明確な優先順位を採用する場合は仕様書へ記載してください。

---

# 10. 1値LoRAタグ

```text
<lora:Alice:0.8>
```

は、

```text
model_weight = 0.8
clip_weight = 0.8
```

としてCanonical化してください。

---

# 11. 2値LoRAタグ

```text
<lora:Alice:0.8:0.5>
```

は、

```text
model_weight = 0.8
clip_weight = 0.5
```

として情報を保持してください。

現在のように第3値を無言で捨てないでください。

---

# 12. LoRAタグ不正値

以下はrejectしてください。

```text
<lora::0.8>
<lora:Alice:notnumber>
<lora:Alice:0.8:notnumber>
```

不完全なタグを無言でPromptへ残すか、部分解釈しないでください。

---

# 13. LoRA weightの型

Pythonでは、

```python
True == 1
```

のような挙動があります。

したがって、

```json
"model_weight": true
```

等を数値として受け入れないでください。

strict numeric:

```text
int / float
ただし bool は除外
```

としてください。

---

# 14. Prompt内LoRAタグの方針を統一する

本プロジェクトでは、ユーザー利便性のため、

```text
Prompt欄へ <lora:...> を直接書く
```

ことも許容します。

一方、

```text
専用LoRA設定欄
```

も将来使用します。

両方とも最終的に同じCanonical LoRA Entryへ集約してください。

---

# 15. Prompt階層すべてでLoRA Parserを共通化する

対象:

```text
Global Prompt
KOMA Prompt
Character Base Prompt
Character Override Prompt
```

に `<lora:...>` が含まれている場合、同じParserで抽出してください。

現状のように階層ごとに挙動が違う状態をなくしてください。

---

# 16. PromptからLoRAタグを除去したClean Promptを保持する

Compiler内部では、

```text
raw_prompt
clean_prompt
lora_entries
```

を分離する考え方を採用してください。

モデルへConditioningとして送る候補は、

```text
clean_prompt
```

です。

---

# 17. LoRA tag sourceを残す

COMPILE_PLAN内で、

```json
{
  "source": "prompt_tag"
}
```

など、由来を保持して構いません。

候補:

```text
global_prompt_tag
koma_prompt_tag
character_prompt_tag
character_override_tag
structured_global
structured_koma
structured_character
```

デバッグ時に役立ちます。

---

# 18. 重複LoRAの扱いを決める

同じLoRAが、

```text
Global
KOMA
Character
```

に重複する可能性があります。

Phase 3A.1では自動加算・自動統合しすぎないでください。

推奨:

```text
COMPILE_PLANではscope別に分離したまま保持
```

してください。

実際の適用合成ルールはPhase 5で決めます。

---

# 19. MANGA_SCENE_SPEC.generation.global_lorasをCanonical正本とする

上位Scene Specでは、

```text
generation.global_loras
```

をGlobal LoRAの構造化正本としてください。

現在のScene Compilerの、

```text
global_loras STRING
```

入力は削除しなくて構いません。

ただしこれは、

```text
UI Facade / Prompt-style input
```

として扱い、ParserでCanonical global_lorasへ変換する位置付けにしてください。

---

# 20. 二重永続化を避ける

将来的にScene Specへ保存する場合、

```text
global_loras文字列
+
generation.global_loras配列
```

を同時に正本として保存しないでください。

文字列表現はUI用再構築値でも構いません。

---

# 21. Negative Prompt階層を正式化する

Phase 3BではConditioningを作るため、Negative Promptをここで契約化してください。

最低限以下を設計してください。

```text
Global Negative Prompt
KOMA Negative Prompt
Character Base Negative Prompt
Character Override Negative Prompt
```

---

# 22. REGION_SPEC拡張

既存互換を壊さず、optionalとして、

```json
{
  "global_negative_prompt": ""
}
```

をRootへ追加できるようにしてください。

各KOMAにもoptionalで、

```json
{
  "negative_prompt": ""
}
```

を許可してください。

既存Workflowには無くても問題ないこと。

---

# 23. CAST_SPECのNegative

現在ある、

```text
character.negative_prompt
```

を正式にCompile Planへ流してください。

---

# 24. Binding側Negative Override

Panel-local Character Bindingへoptionalで、

```json
{
  "negative_prompt_override": ""
}
```

を追加してください。

---

# 25. Negative Promptを巨大文字列一本へ統合しすぎない

COMPILE_PLANでは、

```text
global_negative_prompt
panel_negative_prompt

character:
  base_negative_prompt
  override_negative_prompt
```

として分離保持してください。

Phase 3BでConditioningへ変換します。

---

# 26. compiled_negative_promptはDebug用なら可

`compiled_prompt` と同様に、

```text
compiled_negative_prompt
```

をデバッグ用に出力して構いません。

ただしCanonicalな情報源は分離フィールドです。

---

# 27. COMPILE_PLAN Validatorを実装する

新規:

```python
validate_compile_plan()
```

を作成してください。

Phase 3BのConditioningノードは、

```text
COMPILE_PLAN
```

を受け取るため、境界で必ずvalidate可能にしてください。

---

# 28. COMPILE_PLAN Validator最低要件

検査対象:

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

activeの場合はpanel必須。

inactiveの場合はpanel=nullを許可。

---

# 29. COMPILE_PLAN Character検査

各Characterについて、

```text
character_id
name
base_prompt
override_prompt
base_negative_prompt
override_negative_prompt
area
loras
```

を検査してください。

---

# 30. COMPILE_PLAN LoRA Plan検査

```text
global_loras
koma_loras
character_loras
```

をCanonical LoRA Entryとして検査してください。

---

# 31. Scene Compiler自身の出力をValidatorへ通す

Scene Compilerの最後で、

```text
compile_plan = validate_compile_plan(compile_plan)
```

相当を実行してください。

Compiler自身が不正なPlanを出さないことを保証します。

---

# 32. `characters` フィールドのstrict化

以下は不正です。

```json
"characters": {}
```

```json
"characters": ""
```

たとえempty/falsyでも、

```text
characters keyが存在
→ listでなければValueError
```

としてください。

---

# 33. REGION_SPEC側Bindingもstrict化

`validate_manga_scene_spec()`だけでなく、Scene Compilerが直接REGION_SPECを受けた場合も、

```text
regions[].characters
```

を同じルールで検証してください。

---

# 34. Character ID型をstrict string化する

現在、

```python
str(123)
```

で `"123"` に変換するような処理がある場合は見直してください。

Character IDは、

```text
JSON string
```

のみ許可してください。

数値やboolを暗黙変換しないでください。

---

# 35. Prompt系も型を明確にする

以下:

```text
prompt
negative_prompt
prompt_override
negative_prompt_override
```

は、

```text
string
```

のみを正式型にしてください。

推奨:

```text
field missing → ""
null → ""
number / bool / object → ValueError
```

です。

---

# 36. Character name

Character nameも原則string。

missingの場合だけ、

```text
name = id
```

へfallbackして構いません。

数値等の暗黙string化は避けてください。

---

# 37. metadata

`metadata` が存在する場合は、

```text
dict/object
```

であることを検査してください。

未知フィールド保持方針は維持します。

---

# 38. LoRA metadata

LoRA Entryのmetadataも、存在するならobjectのみ。

---

# 39. panel_count用語を修正する

JSONフィールド名 `panel_count` は互換性のため変更しなくて構いません。

ただし仕様書の意味を、

```text
有効なコマ数
```

ではなく、

```text
KOMA slot range
表示/参照可能なコマ番号の上限
```

に修正してください。

---

# 40. Active Panelとの区別

例:

```text
panel_count = 3

KOMA1 enabled
KOMA2 disabled
KOMA3 enabled
```

なら、

```text
panel_count = 3
active panels = [1, 3]
```

です。

この区別をドキュメントへ明記してください。

---

# 41. active_panel_ids helperを検討する

必要なら、

```python
get_active_panel_ids(region_spec)
```

等を作って構いません。

Panel Sequential Generationでは、

```text
1..panel_count
```

ではなく、

```text
active_panel_ids
```

を処理対象にします。

---

# 42. Binding Instance IDは今回検討のみ

将来的に同一Characterを1コマ内へ複数配置する可能性があります。

例:

```text
鏡
分身
回想オーバーレイ
同一人物の複数像
```

そのため、

```text
binding_id
instance_id
```

の必要性を設計メモへ記録してください。

今回必須実装にはしません。

Phase 3CのCharacter UI前までに決定する予定です。

---

# 43. Test Workflowを今回作成する

今回はデータ契約がある程度まとまったため、現状確認用のWorkflowを作成してください。

新規:

```text
workflows/08_MANGA_SCENE_CONTRACT_TEST.json
```

名称:

```text
DEVELOPMENT / CONTRACT INSPECTION HARNESS
```

と明記してください。

---

# 44. Workflow 08の目的

完成版漫画GUIではありません。

目的は、

```text
REGION_SPEC
CAST_SPEC
Target KOMA
Scene Compiler
COMPILE_PLAN
```

が現在どのようにまとまっているかを人間が確認することです。

---

# 45. Workflow 08の構成

可能なら以下を左→右へ並べてください。

```text
[PAGE / REGION]
Tegaki Manga Region Editor
        ↓
[CAST]
CAST_SPEC JSON
        ↓
[TARGET]
Target Panel ID
        ↓
[COMPILER]
Tegaki Manga Scene Compiler
        ↓
[DEBUG OUTPUT]
Compiled Prompt
Compile Plan JSON
Character Count
```

---

# 46. Workflow 08には生成Samplerを入れない

Phase 3A.1では、

```text
Checkpoint
CLIP
KSampler
VAE Decode
```

までつなぐ必要はありません。

Scene Contractの可視化・確認だけにしてください。

---

# 47. Workflow 08のサンプルScene

初期状態として、分かりやすい2人会話Sceneを入れてください。

例:

```text
KOMA1:
classroom, two people talking, medium shot

Alice:
blonde twin tails, blue eyes, school uniform
override:
annoyed, looking at Bob

Bob:
short brown hair, school uniform
override:
laughing, looking at Alice
```

Character Area:

```text
Alice = 左側
Bob = 右側
```

---

# 48. Workflow 08のCAST_SPEC例

```json
{
  "version": 1,
  "characters": [
    {
      "id": "char_alice",
      "name": "Alice",
      "enabled": true,
      "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
      "negative_prompt": "",
      "loras": []
    },
    {
      "id": "char_bob",
      "name": "Bob",
      "enabled": true,
      "prompt": "1boy, short brown hair, school uniform",
      "negative_prompt": "",
      "loras": []
    }
  ]
}
```

---

# 49. Workflow 08でRegion Bindingを見える形にする

現在Region Editor UIにCharacter Binding専用UIが無い場合、

`region_spec_data` の初期JSONへBindingを埋め込んで構いません。

ただし、

```text
これは一時的なDebug入力
```

と明記してください。

将来Character UIを作った後は不要になります。

---

# 50. Workflow 08のText表示

既にインストール済みCustom Nodeに、

```text
Show Text
Text Preview
Any Display
```

等が安全に使えるなら利用して構いません。

ただし新しい依存パックを増やさないでください。

適切な表示Nodeが無い場合は、Scene Compilerの出力だけでも構いません。

このWorkflowのためだけに大きなCustom Nodeを追加しないでください。

---

# 51. Workflow 08は壊れやすい外部依存を避ける

可能な限り、

```text
Tegaki独自Node
ComfyUI core
既存導入済みNode
```

だけで作ってください。

---

# 52. Workflow 08で確認したいこと

人間がWorkflowを開いて、

```text
PAGE
CAST
Binding
Target KOMA
Compile Plan
```

の関係を視覚的に理解できること。

---

# 53. Workflow 08はPhase 3Bで更新予定

今回作成した08は、

```text
Phase 3B
→ Conditioning接続確認

Phase 3C
→ Character UI確認
```

へ段階的に発展させて構いません。

今はInspection Harnessです。

---

# 54. テスト追加

最低限以下を追加してください。

```text
CAST absent + no binding → PASS
CAST absent + binding → ValueError
Broken CAST + binding → ValueError

1-value LoRA tag
2-value LoRA tag
Invalid LoRA tag

Legacy weight → canonical model/clip weights
Conflicting LoRA weight definitions → error

Global Prompt LoRA extraction
KOMA Prompt LoRA extraction
Character Prompt LoRA extraction
Character Override LoRA extraction

Global negative propagation
Panel negative propagation
Character negative propagation
Character negative override propagation

COMPILE_PLAN validation
characters={} reject
characters="" reject

Character ID numeric reject
Prompt numeric reject
LoRA weight bool reject
```

---

# 55. 既存Scene Compilerテストを更新する

現在の7ケースは残してください。

追加で、

```text
Negative Prompt hierarchy
LoRA canonicalization
Compile Plan validator
```

を確認してください。

---

# 56. 既存Region Testsも再実行

最低限:

```text
test_region_spec.py
test_region_state_transitions.py
test_runtime_source_identity.py
verify_wildcard_patch.py
test_generation.py
```

を再実行してください。

---

# 57. Schema Versionについて

今回の変更は、Phase 3B前の契約確定工程です。

既存v1データを正常化して互換性を保てる範囲なら、

```text
CAST_SPEC v1
COMPILE_PLAN v1
```

のままで構いません。

ただし既存v1を意味的に破壊する変更になる場合は、

```text
v2
```

を検討してください。

安易にversionだけ上げないでください。

---

# 58. ドキュメント更新

更新対象:

```text
docs/MANGA_SCENE_DATA_CONTRACT.md
docs/CAST_SPEC_V1.md
docs/COMPILE_PLAN_V1.md
```

必要なら新規:

```text
docs/LORA_ENTRY_V1.md
```

を作成してください。

LoRA仕様が複雑になった場合は独立文書を推奨します。

---

# 59. MANGA_SCENE_DATA_CONTRACTへ追記すること

最低限:

```text
CASTなしBinding禁止
Negative Prompt階層
LoRA Canonicalization
Prompt LoRA tag → Canonical LoRA
panel_count vs active panels
COMPILE_PLAN validation boundary
```

---

# 60. Phase 3A.1報告書

新規:

```text
PHASE3A_1_SCENE_CONTRACT_HARDENING_REPORT.md
```

最低限:

```text
1. CAST / Binding契約修正
2. LoRA Canonical Entry
3. 1値 / 2値LoRAタグ
4. LoRA SSOT
5. Prompt階層LoRA Parser
6. Negative Prompt階層
7. COMPILE_PLAN Validator
8. Schema strictness
9. panel_count用語整理
10. Workflow 08
11. Test結果
12. 既存Workflow互換
13. 既知の問題
14. Phase 3B Readiness
15. Gemini独自判断で変更した項目
```

---

# 61. KNOWN_ISSUES

今回発見した契約上の問題を修正した場合は、

```text
RESOLVED IN PHASE 3A.1
```

として履歴化してください。

---

# 62. Phase 3A.1ではまだConditioningを実装しない

以下は今回行わないでください。

```text
CLIP encodeの本格接続
Attention Couple
ConditioningSetMask
RegionalSampler
ControlNet
RLL
Character UI完成版
Panel Sequential生成
```

Workflow 08にもSamplerは不要です。

---

# 63. Phase 3Bで行うこと

次Phase:

```text
COMPILE_PLAN
↓
Global Positive / Negative Conditioning
↓
Panel Positive / Negative Conditioning
↓
Character Positive / Negative Conditioning
↓
Character Area Mask
```

です。

---

# 64. Acceptance Criteria

以下を満たした場合のみPhase 3A.1完了としてください。

```text
[ ] CASTなし + Bindingあり をreject
[ ] Broken CAST + Bindingあり をreject
[ ] LoRA canonical entry確定
[ ] legacy weight互換
[ ] model_weight / clip_weight保持
[ ] 1値LoRA tag対応
[ ] 2値LoRA tag対応
[ ] 不正LoRA tag検知
[ ] Global Prompt LoRA解析
[ ] KOMA Prompt LoRA解析
[ ] Character Prompt LoRA解析
[ ] Character Override LoRA解析
[ ] LoRAの二重正本なし
[ ] Global Negative契約
[ ] KOMA Negative契約
[ ] Character Negative契約
[ ] Binding Negative Override契約
[ ] COMPILE_PLAN Validator実装
[ ] Scene Compiler出力がValidator PASS
[ ] characters不正型reject
[ ] Character ID strict string
[ ] Prompt strict string
[ ] LoRA bool weight reject
[ ] panel_countの意味修正
[ ] Workflow 08作成
[ ] Workflow 08が既存Nodeだけで開ける
[ ] 既存07非破壊
[ ] txt2img非破壊
```

---

# 65. Phase 3B Readiness

報告書末尾に、

```text
PHASE 3B READINESS:
GO / HOLD
```

を記載してください。

GO条件:

```text
COMPILE_PLANだけを見れば、
Positive / Negative Prompt
Character
Area
Global/KOMA/Character LoRA
```

を一意に解釈できること。

---

# 66. GITHUB.TXT更新

Phase 3A.1実装終了後、まず実装・テスト・報告書・Workflow 08をcommitしてください。

```text
Commit A
Phase 3A.1 Scene Contract Hardening
```

そのSHAを取得。

その後、

```text
Review Target Commit SHA: A
```

をGITHUB.TXTへ記載。

GITHUB.TXTのみ別commitしてください。

---

# 67. GITHUB.TXTへ追加するリンク

最低限:

```text
PHASE3A_1_SCENE_CONTRACT_HARDENING_REPORT.md

MANGA_SCENE_DATA_CONTRACT.md
CAST_SPEC_V1.md
COMPILE_PLAN_V1.md
LORA_ENTRY_V1.md（作成した場合）

scene_spec.py
scene_compiler.py

test_cast_spec.py
test_scene_compiler.py

08_MANGA_SCENE_CONTRACT_TEST.json
```

のPinned URL / Raw URLを追加してください。

---

# 68. 最終回答

作業終了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3A_1_SCENE_CONTRACT_HARDENING_REPORT Raw:

MANGA_SCENE_DATA_CONTRACT Raw:
CAST_SPEC_V1 Raw:
COMPILE_PLAN_V1 Raw:
LORA_ENTRY_V1 Raw: (if created)

scene_spec.py Pinned Raw:
scene_compiler.py Pinned Raw:

CAST Test Raw:
Scene Compiler Test Raw:

Workflow 08 Raw:

PHASE 3B READINESS:
```

外部AIでレビューします。

---

# 最終設計原則

Phase 3A.1で優先するのは、

```text
GUIを増やすこと
```

ではありません。

```text
同じデータを誰が見ても同じ意味に解釈できる
```

ことです。

特にLoRAとNegative Promptは、Conditioning接続後に曖昧さがあると修正コストが急増します。

今回、

```text
REGION_SPEC
CAST_SPEC
COMPILE_PLAN
LoRA Entry
Negative Prompt
```

までを固めた後にPhase 3Bへ進みます。

Workflow 08は完成版GUIではなく、

```text
今のScene Contractがどのように整理されているか
```

を確認するためのInspection Harnessとして作成してください。
