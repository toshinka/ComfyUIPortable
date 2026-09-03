# ComfyUI Portable Phase 3B.1.1 — Workflow Compatibility Hotfix & Zero-Touch Smoke Test 指示書

## 0. 今回の位置づけ

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
33728c1b55e49af2944094d0ca9f105558cae958
```

Phase 3B.1では、

```text
Global
Panel
Local Region
Character
```

の4階層Regional Controlが実装され、

```text
Region Editor
→ Page Compiler
→ Mask Builder
→ Conditioning Builder
→ KSampler
→ VAE Decode
```

まで実生成へ接続されました。

しかしユーザーが実際のWorkflowを開いてQueueしたところ、

```text
Tegaki Manga Conditioning Builder の local_region_strength
に対する値 default は FLOAT に変換できませんでした
```

というComfyUI入力エラーが発生しました。

UI上では、

```text
local_region_strength = NaN
```

となっています。

今回は新しい制御機能を追加する前に、このWorkflow互換性問題を修正します。

---

# 1. 今回の結論

Phase 3B.1のRegional Control設計そのものを撤回する必要はありません。

問題は主に、

```text
Python/APIレベルの生成テスト
```

と、

```text
実際のComfyUI Workflow JSONをブラウザでロードしてQueueする操作
```

の間にテストの穴があったことです。

今回の最優先目標は、

```text
公式Workflow 09
公式Workflow 10

を

ComfyUI再起動
↓
Workflowをロード
↓
何も手修正しない
↓
Queue

で正常生成できる
```

ことです。

これを Zero-Touch Smoke Test と定義します。

---

# 2. GitHub上で確認された直接原因

Phase 3B版の `TegakiMangaConditioningBuilder` は、保存Widget順として概ね、

```text
panel_strength
character_strength
set_cond_area
```

を持っていました。

そのため既存Workflow 09には、

```json
"widgets_values": [
  1.0,
  1.0,
  "default"
]
```

が保存されています。

Phase 3B.1では新しいINPUT_TYPESとして、

```text
panel_strength
character_strength
local_region_strength
set_cond_area
mask_feather
```

という順に変更されました。

この場合、古いWorkflow 09を新しいNode定義で開くと、

```text
panel_strength        = 1.0
character_strength    = 1.0
local_region_strength = "default"
```

と位置対応される可能性があります。

FLOAT Widgetへ `"default"` が入るため、

```text
NaN
```

となりQueue前に停止します。

---

# 3. これはBackward Compatibility不具合として扱う

Phase 3B.1報告書では、

```text
Workflow 09 = 100% 完全互換
```

とされています。

しかし実機ブラウザでは互換性問題が確認されたため、この記述は修正してください。

正確には、

```text
Backend/API named-input compatibility
は確認済み

ComfyUI GUI workflow positional widget compatibility
に不具合あり
```

です。

修正後に初めて「Workflow互換」としてください。

---

# 4. 根本原則: widgets_valuesは位置依存

今後の独自Node開発では、

```text
既存Widgetの途中へ新Widgetを挿入しない
```

ことを原則にしてください。

既存:

```text
A
B
C
```

に新Widget Dを追加する場合、

悪い例:

```text
A
B
D
C
```

推奨:

```text
A
B
C
D
```

です。

Workflow JSONの `widgets_values` は位置による復元の影響を受けるためです。

---

# 5. Conditioning BuilderのCanonical Widget順を修正する

Phase 3B時点の既存Widget順を維持し、新規Widgetを末尾へ追加してください。

推奨Canonical順:

```text
panel_strength
character_strength
set_cond_area
local_region_strength
mask_feather
```

つまり `INPUT_TYPES` のoptional順を、

```python
"panel_strength"
"character_strength"
"set_cond_area"
"local_region_strength"
"mask_feather"
```

へ変更してください。

---

# 6. build_conditioningの引数順も揃える

可能ならPython関数側も、

```python
def build_conditioning(
    clip,
    page_compile_plan,
    panel_strength=1.0,
    character_strength=1.0,
    set_cond_area="default",
    local_region_strength=1.0,
    mask_feather=0,
):
```

のようにCanonical順へ揃えてください。

ComfyUI APIは名前付き入力なので必須ではありませんが、コード可読性と将来事故防止のため推奨します。

---

# 7. Workflow 09をそのままロード可能にする

旧09の、

```json
[1.0, 1.0, "default"]
```

が新Node定義でも、

```text
panel_strength = 1.0
character_strength = 1.0
set_cond_area = default

local_region_strength = default value 1.0
mask_feather = default value 0
```

として復元されることを保証してください。

これが最優先です。

---

# 8. Workflow 10をCanonical順へ更新する

現在の10はPhase 3B.1順で、

```json
[
  1.0,
  1.0,
  1.0,
  "default",
  0
]
```

となっています。

Canonical順へ変更した後は、

```json
[
  1.0,
  1.0,
  "default",
  1.0,
  0
]
```

へ更新してください。

---

# 9. 既に保存されたPhase 3B.1 Workflowも考慮する

ユーザーがPhase 3B.1版のWorkflowを既にローカル保存している可能性があります。

そのため可能ならFrontend migrationを追加してください。

対象:

```text
TegakiMangaConditioningBuilder
```

---

# 10. Workflow Widget Migration

ComfyUI frontend extensionの、

```text
onConfigure
beforeRegisterNodeDef
```

等、現在のComfyUI frontendで適切なLifecycleを利用してください。

Workflowロード時の生 `info.widgets_values` を確認し、

少なくとも以下3世代を識別してください。

### Legacy Phase 3B

```json
[1.0, 1.0, "default"]
```

意味:

```text
panel
character
set_cond_area
```

不足分:

```text
local_region_strength = 1.0
mask_feather = 0
```

### Phase 3B.1 initial

```json
[1.0, 1.0, 1.0, "default", 0]
```

意味:

```text
panel
character
local
set_cond_area
feather
```

Canonicalへ:

```json
[1.0, 1.0, "default", 1.0, 0]
```

### Canonical Phase 3B.1.1

```json
[1.0, 1.0, "default", 1.0, 0]
```

そのまま使用。

---

# 11. Migration判定を型で行う

単純なlengthだけでなく、

```text
3番目がstringかnumberか
4番目がstringかnumberか
```

も確認してください。

例:

```text
widgets_values[2] is number
widgets_values[3] is string
→ Phase 3B.1 initial

widgets_values[2] is string
widgets_values[3] is number
→ Canonical
```

など。

曖昧な場合は無理に変換せずwarningを出してください。

---

# 12. NaN状態を自動修復する

既にUI上で、

```text
local_region_strength = NaN
```

になっているケースについても、

Workflow再ロード時に、

```text
1.0
```

へ復旧できるようにしてください。

ただし任意の有効なユーザー値を勝手に1.0へ戻さないこと。

Migration対象と確定できる場合だけ修復してください。

---

# 13. Backend側でもFinite Validationを行う

`local_region_strength` を含め、

```text
panel_strength
character_strength
local_region_strength
```

について、

```text
finite number
```

であることをBackendでも確認してください。

```text
NaN
+Inf
-Inf
```

をrejectしてください。

ただし今回のようなComfyUI FLOAT変換失敗はBackend呼び出し前に起きるため、Frontend migrationとWidget順修正が本命です。

---

# 14. Workflow 10の構造上の小不整合も修正する

現在のWorkflow 10は、

```json
"last_link_id": 15
```

となっている一方、linksには、

```text
link id = 16
```

が存在します。

これを修正してください。

少なくとも、

```json
"last_link_id": 16
```

以上にしてください。

既存link / node IDも全件監査してください。

---

# 15. Workflow Structural Validatorを作る

新規:

```text
scripts/test_workflow_json_integrity.py
```

を作成してください。

最低限07〜10を対象に、

```text
last_node_id >= max(node.id)
last_link_id >= max(link.id)

全input linkがlinksに存在
全output linksがlinksに存在
link source node存在
link target node存在
source slot有効
target slot有効
```

を確認してください。

---

# 16. Widget Schema Compatibility Testを作る

新規:

```text
scripts/test_workflow_widget_compatibility.py
```

を作成してください。

最低限、

```text
08
09
10
```

内のTegaki独自Nodeについて、

保存された `widgets_values` と現在のNode Widget schemaの型整合を確認してください。

特に、

```text
TegakiMangaConditioningBuilder
```

は必須対象です。

---

# 17. 09 Legacy Fixtureを固定保存する

今回のRegression Testのため、

旧09のConditioning Builder値:

```json
[1.0, 1.0, "default"]
```

をfixtureとしてテストしてください。

期待:

```text
load/migrate
↓
valid
```

---

# 18. 10 Phase3B.1 Fixtureもテストする

Phase 3B.1 initial:

```json
[1.0, 1.0, 1.0, "default", 0]
```

もfixtureとしてテスト。

期待Canonical:

```json
[1.0, 1.0, "default", 1.0, 0]
```

---

# 19. API Generation TestだけではWorkflowテスト扱いしない

現在の、

```text
test_regional_poc_generation.py
test_regional_control_expansion_generation.py
```

は有用です。

ただしこれらは、

```text
PythonコードでAPI Prompt dictを新規構築
```

しており、

```text
workflows/09_....json
workflows/10_....json
```

そのもののBrowser復元を検証していません。

今後報告書では明確に分けてください。

---

# 20. テスト分類を正式化する

### A. Unit Test

```text
validator
compiler
mask
conditioning
```

### B. API Integration Test

```text
Pythonからnamed inputでComfyUI /prompt
```

### C. Workflow GUI Smoke Test

```text
実際のWorkflow JSONをComfyUIへロード
↓
無修正Queue
```

この3つを別カテゴリーとして報告してください。

---

# 21. Zero-Touch Smoke Testを必須化する

今回のAcceptance Criteriaで最重要です。

ComfyUIを一度再起動してください。

その後、

```text
Workflow 09
```

を新しいGraphへロード。

一切Widgetを触らず、

```text
Queue
```

してください。

期待:

```text
Input validation error 0
NaN 0
生成成功
```

---

# 22. Workflow 10も同様にZero-Touch Test

ComfyUI再起動後、

```text
10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json
```

を新規Graphへロード。

一切手修正せずQueue。

期待:

```text
local_region_strength = 1.0
set_cond_area = default
mask_feather = 0

生成成功
```

---

# 23. 「ロード後に値を直して生成」はPASSにしない

今回の目的はポン出し確認です。

したがって、

```text
NaNを手で1.0へ修正
↓
Queue成功
```

はSmoke Test PASSではありません。

必ず、

```text
Load
↓
No Touch
↓
Queue
```

で判定してください。

---

# 24. 07 / 08も軽く確認する

07 / 08についても、

```text
Load
Console Errorなし
Node value破損なし
```

を確認してください。

生成不要のWorkflowはQueue可能範囲だけで構いません。

---

# 25. Browser Consoleも確認

Workflowロード時:

```text
JS error
Widget migration warning
NaN
undefined
```

がないか確認してください。

Migrationを実行した場合は、

```text
[Tegaki] Migrated ConditioningBuilder widget schema:
Phase3B.1 -> Canonical
```

のようなdebug logを出して構いません。

通常利用では過剰ログを出さないでください。

---

# 26. Runtime Object Info確認

実際に起動しているComfyUIへ、

```text
/object_info
```

等を利用可能なら、

```text
TegakiMangaConditioningBuilder
```

の現在Runtime schemaを確認してください。

Git正本だけでなく、

```text
Runtime Node Definition
```

が期待順になっていることを記録してください。

---

# 27. Runtime Source Identityも再確認

既存:

```text
test_runtime_source_identity.py
```

を再実行。

Git正本 = Runtime正本を確認してください。

---

# 28. Workflow 10そのものから生成された画像を証拠にする

今回の報告書では、

```text
APIスクリプトが生成した画像
```

だけではなく、

```text
Workflow 10をブラウザでZero-Touch Queueして生成された画像
```

を1枚以上記録してください。

filename / timestampを報告書へ記載してください。

---

# 29. Workflow 09も生成証拠を残す

Backward Compatibilityの証拠として、

```text
Workflow 09 direct browser queue
```

の生成結果も記録してください。

---

# 30. 報告書の「100%互換」表現を修正する

既存報告書:

```text
100% 完全な後方互換性
```

は、今回の不具合を踏まえて修正してください。

修正後に、

```text
Backend/API compatibility
Workflow GUI compatibility
```

を分けて記載。

Zero-Touch Test後にのみ、

```text
Official Workflow 09 backward compatibility verified
```

としてください。

---

# 31. Scope HierarchyとPriorityを区別する

Phase 3B.1文書では、

```text
Global → Panel → Local Region → Character
```

を「優先順位」と表現しています。

ComfyUI CoreのMasked Conditioningでは、重なり部分のConditioningは単純な上書きPriorityとは限りません。

したがって文書では、

```text
Scope hierarchy / specificity order
```

または、

```text
Conditioning append order
```

として説明してください。

以下のような保証はしないでください。

```text
CharacterがLocal Regionを必ず上書きする
```

実際にはOverlap時に両Conditioningが共存する設計です。

---

# 32. Local Region設計自体は維持する

今回、

```text
LOCAL_REGION
```

を撤回する必要はありません。

以下はそのまま維持してください。

```text
Global
Panel
Local Region
Character
```

Local Regionは、

```text
そのKOMA限りの背景・小物・局所情景Prompt
```

として妥当です。

---

# 33. 今回は新しい制御機能を増やさない

Workflowがポン出しできない状態で、

```text
ControlNet
RegionalSampler
RLL
新Local scope
```

を追加しないでください。

まず公式Workflowを正常化します。

---

# 34. Zero-Touch PASS後のA/B確認

Workflow 10が正常ロードできるようになった後、固定Seedで最低3種類だけ再確認してください。

```text
A. Panel Prompt変更
B. Character Prompt変更
C. Local Region Prompt変更
```

これらはWorkflow 10自体を使って実行してください。

---

# 35. Local Region Test

例:

A:

```text
Window Desks:
school desks near window
```

B:

```text
Window Desks:
large flower pots near window
```

他固定。

Target周辺へ相対的に強く影響するか観察。

完全局所化は要求しません。

---

# 36. Character Test

Aliceだけ髪色変更。

他固定。

Target Character Area中心に変化するか。

---

# 37. Panel Test

KOMA1だけ、

```text
classroom
→ convenience store
```

へ変更。

---

# 38. ここでCore Backendの判断をする

Zero-Touch修正と簡易A/B確認後、

```text
Core Masked Conditioning
```

がどの程度使えるか判断してください。

以下のいずれか:

```text
CORE_RESULT:
PROMISING
PARTIAL
INSUFFICIENT
```

---

# 39. 次Phaseは結果で決める

### PROMISING

次候補:

```text
Character / CAST UI
または
ControlNet integration
```

### PARTIAL

次候補:

```text
Impact RegionalSampler A/B comparison
```

### INSUFFICIENT

Regional backend比較を優先。

RLLへ直行しないこと。

---

# 40. 新規報告書

新規:

```text
PHASE3B_1_1_WORKFLOW_COMPATIBILITY_HOTFIX_REPORT.md
```

最低限:

```text
1. ユーザー実機エラー
2. Root Cause
3. widgets_values positional compatibility
4. Canonical widget order
5. Frontend migration
6. Workflow 09 migration
7. Workflow 10 migration
8. last_link_id修正
9. Workflow structural test
10. Widget schema compatibility test
11. API Integration Test
12. Workflow GUI Zero-Touch Test
13. Workflow 09 direct queue result
14. Workflow 10 direct queue result
15. Console error
16. A/B簡易再確認
17. Core Backend評価
18. 既知の問題
19. 次Phase提案
20. Gemini独自判断
```

---

# 41. 新規テスト

最低限:

```text
scripts/test_workflow_json_integrity.py
scripts/test_workflow_widget_compatibility.py
```

を作成。

既存:

```text
test_regional_poc_generation.py
test_regional_control_expansion_generation.py
```

も再実行してください。

---

# 42. UI Test Checklist

新規または更新:

```text
WORKFLOW_ZERO_TOUCH_TEST_CHECKLIST.md
```

最低限:

```text
[ ] ComfyUI restart
[ ] Load 09 fresh
[ ] 09 NaNなし
[ ] 09 no-touch Queue
[ ] 09 image generated
[ ] Load 10 fresh
[ ] 10 local_region_strength=1.0
[ ] 10 set_cond_area=default
[ ] 10 mask_feather=0
[ ] 10 no-touch Queue
[ ] 10 image generated
[ ] Browser console error 0
```

実際に確認した項目だけPASSにしてください。

---

# 43. Acceptance Criteria

以下すべてを満たした場合のみ完了。

```text
[ ] Conditioning Builder widget順がappend-only互換
[ ] 09 legacy workflow load compatibility
[ ] Phase3B.1 initial workflow migration
[ ] NaN自動修復
[ ] Workflow 10 canonical widgets_values
[ ] Workflow 10 last_link_id修正
[ ] Workflow JSON integrity PASS
[ ] Widget compatibility test PASS
[ ] Runtime source identity PASS
[ ] 09 Zero-Touch Queue PASS
[ ] 10 Zero-Touch Queue PASS
[ ] 09 actual image generated
[ ] 10 actual image generated
[ ] Console error 0
[ ] 報告書の互換性表現修正
```

---

# 44. 今回の完了判定

報告書末尾に:

```text
OFFICIAL WORKFLOW STATUS:
09 ZERO-TOUCH PASS / FAIL
10 ZERO-TOUCH PASS / FAIL

CORE REGIONAL RESULT:
PROMISING / PARTIAL / INSUFFICIENT

NEXT RECOMMENDED PHASE:
```

を記載してください。

---

# 45. GITHUB.TXT 二段Commit

まず、

```text
Commit A
Phase 3B.1.1 Workflow Compatibility Hotfix
```

として、

```text
実装
Workflow 09/10修正
Migration
Tests
Report
Checklist
```

をcommit。

そのSHAを取得。

次にGITHUB.TXTへ、

```text
Review Target Commit SHA: A
```

を記載し、

GITHUB.TXTのみ別commitしてください。

---

# 46. GITHUB.TXTへ追加

最低限:

```text
PHASE3B_1_1_WORKFLOW_COMPATIBILITY_HOTFIX_REPORT.md
WORKFLOW_ZERO_TOUCH_TEST_CHECKLIST.md

conditioning_builder.py
workflow migration JS

09_MANGA_REGIONAL_GENERATION_POC.json
10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json

test_workflow_json_integrity.py
test_workflow_widget_compatibility.py
```

のPinned Rawを追加してください。

---

# 47. 最終回答

作業終了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3B_1_1_WORKFLOW_COMPATIBILITY_HOTFIX_REPORT Raw:
WORKFLOW_ZERO_TOUCH_TEST_CHECKLIST Raw:

Conditioning Builder Raw:
Workflow Migration JS Raw:

Workflow 09 Raw:
Workflow 10 Raw:

Workflow Integrity Test Raw:
Widget Compatibility Test Raw:

09 ZERO-TOUCH:
PASS / FAIL

10 ZERO-TOUCH:
PASS / FAIL

CORE REGIONAL RESULT:
PROMISING / PARTIAL / INSUFFICIENT

NEXT RECOMMENDED PHASE:
```

---

# 最終方針

今回の問題で最も重要なのは、

```text
Backend testがPASS
=
ユーザーがWorkflowを開いてそのまま使える
```

ではないことが確認できた点です。

今後は、

```text
Unit
API Integration
GUI Workflow Zero-Touch
```

の3段階で検証してください。

特にユーザーへ提出する公式Workflowについては、

```text
ロード
↓
何も直さない
↓
実行
↓
画像が出る
```

ことをAcceptance Criteriaへ含めます。

Phase 3B.1のRegional Control自体は維持し、まずWorkflow互換性を修復した後に、局所制御性能の評価へ戻ってください。
