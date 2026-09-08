# ComfyUI Portable Phase 3D.1 — Regional Locality Validation & Character / CAST Master UI Foundation 補足指示書

## 0. 対象 / Baseline

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
8e6e17ee49cc4d0e0d17e9a0103836062e3db671
```

Phase 3Dでは以下が成立しました。

```text
PANEL_LAYOUT_SPEC
+
PAGE_COMPILE_PLAN
↓
Layout Region Bridge
↓
Polygon Panel Masks
+
Character / Local Region Projection
↓
4階層 Layout-Aware Conditioning
↓
Panel Layout ControlNet
↓
Workflow 16
```

Phase 3Dの構造実装は維持してください。

ただし外部レビューでは、

```text
「データ配線・マスク・Conditioningが正しく作られる」
```

ことと、

```text
「生成画像上でもTarget領域へ意味が十分局所化される」
```

ことの間に、まだ検証ギャップがあります。

今回の補足Phaseでは、そのギャップを先に閉じつつ、
次予定だった Character / CAST Master UI の土台まで進めます。

---

# 1. 今回のPhase名

```text
Phase 3D.1
Regional Locality Validation
&
Character / CAST Master UI Foundation
```

内部を以下へ分けてください。

```text
3D.1-A  Phase 3D Validation Closure
3D.1-B  Character / CAST Master Contract
3D.1-C  Character Master UI Foundation
3D.1-D  Workflow 17 Integration
3D.1-E  Backend Decision Gate
```

---

# 2. Phase 3D全体をやり直さない

以下は成立済みとして維持します。

```text
N Panel Mapping
Polygon Panel Mask
Character bbox-relative projection
Panel Polygon clipping
Semantic Overlap
ControlNet geometry sharing
Layout-Aware Conditioning
Workflow16
```

今回はその上で、

```text
画像上の局所性
+
Character管理UI
```

を追加検証します。

---

# 3. 最重要レビュー修正 — Locality Ratioの解釈

Phase 3D報告書ではKOMA2 Prompt A/Bの:

```text
Locality Ratio = 0.6614
```

が記録されています。

現在の定義:

```text
MeanDiff(target panel)
/
MeanDiff(outside target panel)
```

であるため、

```text
> 1.0
→ Targetの方が相対的に強く変化

< 1.0
→ Target外の平均変化の方が大きい
```

です。

したがって、

```text
0.6614
```

を、

```text
十分な局所性を実証
```

と解釈しないでください。

報告書を修正してください。

---

# 4. Locality MetricはPASS判定ではなくDiagnosticから再出発

現時点では、

```text
ratio > 0
```

をPASS条件にしないでください。

まずraw valueを記録します。

最低限:

```text
Target Panel MeanDiff
Other Panels MeanDiff
Outside Layout Frame MeanDiff
Target / Other
Target / Outside
```

を別々に保存してください。

---

# 5. Panel Prompt A/B実画像検証

Workflow16相当構成を使い、

固定条件:

```text
same model
same seed
same sampler
same steps
same CFG
same ControlNet strength
same layout
same character prompts
```

とします。

変更はKOMA2 Promptだけ。

A:

```text
school corridor, lockers, hallway
```

B:

```text
convenience store interior, brightly lit aisles, shelves with snacks and drinks
```

---

# 6. Panel Prompt局所性の測定

3-panel layoutの各Panel polygonを使い、

```text
KOMA1 MeanDiff
KOMA2 MeanDiff
KOMA3 MeanDiff
Outside Frame MeanDiff
```

を計測。

さらに:

```text
KOMA2 / mean(KOMA1,KOMA3)
KOMA2 / Outside
```

を算出してください。

---

# 7. Panel PromptのSemantic Self-Review

Geminiが生成画像を視覚確認できる場合:

```text
KOMA2が本当に廊下→コンビニへ変化したか
KOMA1内容がどの程度変わったか
KOMA3内容がどの程度変わったか
Panel borderや構図が崩れたか
```

を記録。

不可なら:

```text
VISUAL SEMANTIC REVIEW PENDING
```

と明記。

---

# 8. Character A/Bは実画像で検証する

Phase 3D Test 4はMockCLIPによるRouting検証でした。

今回はKSampler実画像で行ってください。

Alice A:

```text
golden blonde hair, twin tails
```

Alice B:

```text
bright cyan blue hair, twin tails
```

Bobは固定。

---

# 9. Character A/B固定条件

```text
same seed
same panel prompts
same layout
same Bob prompt
same ControlNet
same sampler
same steps
```

変更はAlice master promptの髪色だけ。

---

# 10. Character Locality Metric

KOMA1 Alice projected semantic maskをTargetとし、

最低限:

```text
Alice Mask MeanDiff
Bob Mask MeanDiff
KOMA1 remainder MeanDiff
KOMA2 MeanDiff
KOMA3 MeanDiff
Outside MeanDiff
```

を計測。

---

# 11. Character Locality Ratio

最低限:

```text
Alice / Bob
Alice / same-panel remainder
Alice / other panels
```

を記録。

閾値はPhase 3D.1開始時点で固定しなくて構いません。

まずraw値を比較してください。

---

# 12. Bob側も対称テスト

Bob A:

```text
short brown hair
```

Bob B:

```text
silver white hair
```

Alice固定。

これにより、

```text
Aliceだけ局所化しやすい
```

等の偶然を避けます。

---

# 13. 同一コマSemantic Overlapを維持

KOMA1のAlice/Bob領域は、

```text
重なる
```

配置を基本としてください。

例:

```text
Alice:
x=.05 y=.08 w=.62 h=.84

Bob:
x=.33 y=.08 w=.62 h=.84
```

目的:

```text
属性分離
+
人物 interaction
```

の両立確認。

---

# 14. Overlap率をDebug出力

KOMA1について:

```text
Alice area
Bob area
intersection area
overlap ratio
```

をdebugへ記録してください。

---

# 15. Panel PromptとCharacter Promptを同時変更しない

局所性評価では、

```text
1 variable at a time
```

を厳守してください。

---

# 16. ControlNet OFF / ON両方でPanel Prompt A/B

最低限:

```text
CN OFF
CN ON 0.60
```

の両方でKOMA2 A/Bを生成。

目的:

```text
ControlNetがPanel Prompt localityを改善するか
悪化させるか
```

を見ること。

---

# 17. Character A/Bは最初CN ONだけでもよい

計算量節約のため、

Character hair A/Bは最初:

```text
CN 0.60
```

のみで構いません。

問題がある場合だけCN OFF比較。

---

# 18. 5 Panelは実画像を最低1枚生成する

Phase 3Dでは5 Panelは主に:

```text
mapping
mask
conditioning
guide
```

まででした。

今回は少なくとも1枚:

```text
5 Panel
+
Core Layout-Aware Conditioning
+
ControlNet
+
KSampler
```

を実画像生成してください。

---

# 19. 5 Panelは局所性A/Bまで必須ではない

今回の5 Panel目的は:

```text
N=5 actual generation viability
```

です。

固定Seed1枚で十分。

---

# 20. 6 PanelはCapacityのままでよい

6 Panelは今回も:

```text
structural / mapping / mask / branch count
```

までで構いません。

毎回6 Panel実画像は要求しません。

---

# 21. Canvas mismatchをFail-Closedへ

`PAGE_COMPILE_PLAN.canvas` と `PANEL_LAYOUT_SPEC.canvas` が一致することを、
Bridgeで必須化してください。

確認:

```text
width equal
height equal
```

不一致:

```text
ValueError
```

---

# 22. Canvas mismatch Test

新規テスト:

```text
Plan = 832x1216
Layout = 1024x1024
→ reject
```

同サイズ:

```text
PASS
```

---

# 23. Pixel Geometryの正本

Layout-Driven Modeでは:

```text
PANEL_LAYOUT_SPEC.canvas
```

と、

```text
PAGE_COMPILE_PLAN.canvas
```

が一致して初めて、

```text
ControlNet guide
Polygon masks
Character projections
```

を生成してください。

---

# 24. Mask Boundaryについて

PIL polygon rasterizationでは共有edge上の1px程度が両Panel maskへ含まれる可能性があります。

これは既知のraster detailとして扱って構いません。

ただし報告書では:

```text
100% pixel-perfect non-overlap
```

とは書かないでください。

---

# 25. Phase 3D報告書の表現修正

以下を修正してください。

例:

```text
Panel Prompt locality fully proven
Character image locality fully proven
3〜6 panels fully generated
```

のような表現があれば、

```text
Routing / structural support proven
3-panel actual generation proven
5-panel generation added in 3D.1
Character image locality evaluated in 3D.1
```

へ補正。

---

# 26. Validation結果によるBackend Gate

Phase 3D.1-A終了時、以下を判定してください。

```text
CORE PANEL LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT

CORE CHARACTER LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT
```

---

# 27. Core Panel Locality = PROMISINGの目安

厳密な閾値ではなく目安:

```text
Target Panel changeが
他Panel平均より明確に大きい
```

かつ視覚的にもTarget内容変化が確認できる。

---

# 28. PARTIALの場合

例:

```text
Targetは変わるが
他Panelも同程度変わる
```

場合。

Coreは継続しつつ、

```text
Impact RegionalSampler comparison
```

を次候補へ。

---

# 29. INSUFFICIENTの場合

例:

```text
Target外の変化がTarget以上
Semantic bindingが弱い
```

が複数seedで続く。

この場合:

```text
Phase 3D.2
Core vs Impact RegionalSampler
```

を優先。

CAST UIだけ先に完成させすぎないでください。

---

# 30. Seed Robustness

局所性が曖昧な場合のみ、

```text
3 seeds
```

へ増やしてください。

最初から大量seedは不要。

---

# 31. ここからCharacter / CAST Master UI Foundation

Validationが完全終了するまでUI作業を止める必要はありません。

低結合部分は並行して進めて構いません。

---

# 32. CAST_SPECを再確認する

既存CAST_SPECをSSOTとして維持。

新UIが独自Character JSONを作らないこと。

---

# 33. Character Master UIの目的

ユーザーが1ページごとに、

```text
Alice promptを何度も書く
Bob promptを何度も書く
```

必要をなくします。

Character Master:

```text
ID
Name
Base Prompt
Base Negative
LoRA Plan
Enabled
Metadata
```

を一元管理。

---

# 34. Character Masterと出演情報を分離

重要。

Character Master:

```text
Aliceとは誰か
```

KOMA Binding:

```text
Aliceがこのコマで何をするか
```

です。

既存設計:

```text
CAST_SPEC
+
KOMA-side Binding
```

を維持。

---

# 35. Character Master UI名称

候補:

```text
Tegaki Manga Cast Master
```

または:

```text
Tegaki Manga Character Cast Editor
```

---

# 36. 最大Character数

最初は:

```text
1〜6 characters
```

程度で構いません。

本番上限を永続固定する必要はありません。

---

# 37. Character Card UI

各Characterをカードとして:

```text
[Name]
[ID]
[Base Prompt]
[Negative Prompt]
[LoRA entries]
[Enabled]
```

を確認可能にしてください。

---

# 38. 不使用Characterは折り畳み / 非表示

ComfyUI custom nodeで可能な範囲で:

```text
selected characterだけ詳細表示
```

を推奨。

全Characterの巨大Prompt欄を常時並べない。

---

# 39. Character List

左または上:

```text
Alice
Bob
+ Add Character
```

選択すると詳細編集。

---

# 40. Character ID

内部ID:

```text
char_001
char_alice
```

等。

一度Bindingで使用されたIDをName変更で勝手に変更しないこと。

---

# 41. NameとIDを分離

```text
Name:
Alice

ID:
char_alice
```

Name変更:

```text
Alicia
```

でもIDは維持。

---

# 42. Duplicate IDは禁止

CAST_SPEC validatorで既に検証されている場合は再利用。

UI側でも早期warning。

---

# 43. Base Prompt

Characterの恒常属性:

```text
1girl
blonde twin tails
blue eyes
school uniform
```

等。

---

# 44. KOMA Binding Prompt Override

一時属性:

```text
annoyed expression
looking right
walking away
```

はCharacter Masterへ入れない。

KOMA Binding側。

---

# 45. Costumeについて

将来:

```text
default costume
alternate costume
```

を持ちたくなる可能性があります。

今回はBase Promptだけ。

複雑なOutfit Presetは後回し。

---

# 46. Character LoRA Plan

既存Canonical LoRA Entryを再利用。

Character Master UIで:

```text
LoRA name
model weight
clip weight
enabled
```

を編集できてもよい。

---

# 47. ただしSpatial LoRAは未実装

UI上で明記:

```text
Character LoRA Plan
NOT YET SPATIALLY APPLIED
```

またはdebug status。

ユーザーへ、

```text
Character領域だけLoRAが効く
```

と誤認させないこと。

---

# 48. Global LoRAとは分離

Global LoRA:

```text
MODELへ実適用
```

Character LoRA:

```text
Plan only / future regional application
```

---

# 49. 出演コマ一元管理

Character Master UI側で、

```text
Appearances
KOMA 1
KOMA 2
KOMA 3
```

を確認できるViewは有用です。

---

# 50. Binding SSOTを壊さない

ただし編集正本は引き続き:

```text
KOMA-side Binding
```

です。

Cast UIの出演コマ一覧は:

```text
derived view
```

としてください。

---

# 51. 逆編集を行う場合

将来Cast UIから:

```text
Alice → KOMA2へ出演追加
```

を行う場合も、

内部では:

```text
KOMA2 Binding
```

を書き換える形にしてください。

二重保存禁止。

---

# 52. Phase 3D.1ではRead-only Appearance Viewでもよい

最初は:

```text
Alice:
KOMA1
KOMA2

Bob:
KOMA1
KOMA3
```

を表示するだけでも十分。

---

# 53. CAST_SPEC Editor Output

最低限:

```text
CAST_SPEC
CAST_SPEC JSON
selected_character_id
character_count
```

---

# 54. Character Preview Summary

Debug出力:

```text
Alice
Prompt preview
Negative preview
LoRA count
Appearance count
```

程度。

画像Character Sheet生成は今回不要。

---

# 55. CAST UI State Test

新規:

```text
scripts/test_cast_master_state.py
```

最低限:

```text
add
select
rename
ID stable
prompt edit
negative edit
enable/disable
delete unused
duplicate ID reject
save/reload
```

---

# 56. Binding Reference Validation

Character削除時:

```text
Bindingから参照されている
```

なら勝手に削除しない。

選択肢:

```text
Delete blocked
```

を推奨。

---

# 57. Disabled Character

disabled characterがBindingに存在する場合、

現在Compiler仕様に従って:

```text
skip
warning
or fail
```

のどれかを統一。

既存仕様を確認し、勝手に変更しない。

---

# 58. Workflow 17

新規:

```text
17_MANGA_CAST_MASTER_AND_LOCALITY_VALIDATION.json
```

区分:

```text
DEVELOPMENT / CHARACTER MASTER + REGIONAL VALIDATION
```

---

# 59. Workflow 17目的

一つのWorkflowで:

```text
Cast Master
Region Editor
Panel Layout
Layout-Aware Conditioning
ControlNet
KSampler
Mask Preview
```

まで繋ぎます。

---

# 60. Workflow 17 Default

3 Panels Basic。

Cast:

```text
Alice
Bob
```

KOMA1:

```text
Alice + Bob overlap
```

KOMA2:

```text
Alice
```

KOMA3:

```text
Bob
```

---

# 61. Workflow 17で確認すべきこと

```text
Cast Masterを変更
↓
Compiler
↓
Character Conditioning
↓
実画像
```

が繋がること。

---

# 62. Workflow 17 A/B Test

Alice hair:

```text
blonde
→ cyan
```

Cast Master UIのBase Promptだけ変更。

他固定。

実画像生成。

---

# 63. Workflow 17 Zero-Touch

Default:

```text
load
no touch
Queue
image
```

PASS。

---

# 64. CAST UIは最終Shellではない

今回はComfyUI研究Nodeです。

最終的な:

```text
A1111風の漫画制作Shell
```

の完成UIをここで作らない。

---

# 65. Final Shellでの将来像

将来:

```text
Characters
Panels
Layout
Control
Generate
```

程度のタブ/セクションへ整理。

Phase 3D.1ではデータ契約と操作性の検証。

---

# 66. User確認Gate

今回も途中で細かくユーザー確認を求めなくて構いません。

次にユーザーへ見せる価値がある状態:

```text
Workflow17
Cast MasterからAlice/Bob編集可能
3-panel manga generation
Character overlap
Panel Layout ControlNet
Alice hair A/B
```

が揃った時。

---

# 67. Phase 3D.1報告書

新規:

```text
PHASE3D_1_REGIONAL_LOCALITY_AND_CAST_MASTER_REPORT.md
```

最低限:

```text
1. Phase3D Review Corrections
2. Canvas Contract Fix
3. Panel Prompt A/B
4. Panel Polygon Locality Metrics
5. CN OFF/ON Comparison
6. Alice Image A/B
7. Bob Image A/B
8. Character Locality Metrics
9. Same-Panel Semantic Overlap
10. 5-Panel Actual Generation
11. Core Backend Evaluation
12. CAST_SPEC SSOT
13. Character Master UI
14. Character Card
15. ID Stability
16. Base Prompt / Negative
17. Character LoRA Plan Status
18. Appearance Derived View
19. Binding SSOT Preservation
20. Workflow17
21. Zero-Touch
22. Existing Workflow Regression
23. Known Issues
24. Backend Decision
25. Next Phase
26. Gemini独自判断
```

---

# 68. Existing Workflow Regression

最低限:

```text
09
10
11
12
14
15
16
```

を壊さない。

特に:

```text
16 Zero-Touch
```

維持。

---

# 69. 新規Tests

最低限:

```text
scripts/test_phase3d1_panel_locality.py
scripts/test_phase3d1_character_locality.py
scripts/test_canvas_contract_match.py
scripts/test_cast_master_state.py
scripts/test_cast_binding_references.py
```

---

# 70. Panel Locality Test結果JSON

例:

```json
{
  "target_panel": "2",
  "target_mean_diff": 12.3,
  "other_panels_mean_diff": 8.1,
  "outside_mean_diff": 5.4,
  "target_to_other": 1.52,
  "target_to_outside": 2.28
}
```

数値は例。

---

# 71. Character Locality Test結果JSON

例:

```json
{
  "character": "Alice",
  "target_mean_diff": 15.0,
  "other_character_mean_diff": 6.0,
  "panel_remainder_mean_diff": 7.0,
  "other_panels_mean_diff": 4.5
}
```

---

# 72. MetricだけでBackend合否を決めない

最終判断:

```text
Pixel locality
+
Visual semantic review
+
attribute leakage
+
interaction preservation
```

を総合。

---

# 73. Backend Decision Gate

Phase終了時:

```text
CORE PANEL LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT

CORE CHARACTER LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT
```

---

# 74. COREがPROMISINGなら

次Phase候補:

```text
Phase 3E
Character / Panel User Shell & Production UX
```

または:

```text
ControlNet Pose Integration
```

---

# 75. COREがPARTIALなら

次Phase:

```text
Phase 3D.2
Core vs Impact RegionalSampler
```

を優先。

Cast Master UIはFoundationのまま維持。

---

# 76. COREがINSUFFICIENTなら

N-region UIを増築しすぎない。

まずRegional Backendを再評価。

候補:

```text
Impact RegionalSampler
DenseDiffusion
Omost
later RLL
```

---

# 77. Impact比較時もCAST UIは再利用

CAST_SPEC / Binding contractはBackend非依存に保ってください。

---

# 78. Acceptance Criteria — Validation

```text
[ ] Phase3D locality report wording corrected
[ ] PAGE canvas == LAYOUT canvas enforced
[ ] mismatch reject test

[ ] KOMA2 A/B actual images
[ ] Panel diff by each polygon
[ ] CN OFF locality
[ ] CN ON locality

[ ] Alice A/B actual images
[ ] Bob A/B actual images
[ ] Character locality metrics
[ ] same-panel overlap retained

[ ] 5-panel actual image generated
```

---

# 79. Acceptance Criteria — Cast Master

```text
[ ] CAST_SPEC remains SSOT
[ ] Character add
[ ] Character select
[ ] Name edit
[ ] stable ID
[ ] Base Prompt edit
[ ] Negative edit
[ ] enabled
[ ] duplicate ID reject
[ ] referenced character delete blocked
[ ] save/reload
[ ] appearance derived view
[ ] LoRA plan status clearly labeled
```

---

# 80. Acceptance Criteria — Workflow17

```text
[ ] Cast Master connected
[ ] Region Editor connected
[ ] Panel Layout connected
[ ] Layout-Aware Conditioning
[ ] ControlNet
[ ] KSampler
[ ] Preview
[ ] Zero-Touch PASS
[ ] Alice master prompt A/B reaches actual image
```

---

# 81. Phase終了判定

報告書末尾:

```text
PHASE3D VALIDATION CLOSURE:
PASS / HOLD

CORE PANEL LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT

CORE CHARACTER LOCALITY:
PROMISING / PARTIAL / INSUFFICIENT

5-PANEL ACTUAL GENERATION:
PASS / HOLD

CAST MASTER FOUNDATION:
PASS / HOLD

WORKFLOW17:
PASS / HOLD

NEXT REGIONAL BACKEND:
CORE / IMPACT COMPARISON / OTHER

NEXT RECOMMENDED PHASE:
```

---

# 82. GITHUB.TXT二段Commit

まず:

```text
Commit A
Phase 3D.1 Regional Locality Validation & Cast Master Foundation
```

として:

```text
validation fixes
metrics
CAST UI
Workflow17
tests
report
```

をcommit。

そのSHAを取得。

次にNavigation commitで:

```text
Review Target Commit SHA: A
```

を更新。

Latest:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

---

# 83. GITHUB.TXTへ追加

最低限:

```text
PHASE3D_1_REGIONAL_LOCALITY_AND_CAST_MASTER_REPORT.md

Cast Master implementation
Cast Master JS
Canvas contract fix
Locality test scripts
Workflow17
```

Pinned Rawを追加。

---

# 84. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3D_1_REGIONAL_LOCALITY_AND_CAST_MASTER_REPORT Raw:

Cast Master Raw:
Cast Master JS Raw:
Canvas Contract Raw:

Workflow 16 Raw:
Workflow 17 Raw:

Panel Locality Test Raw:
Character Locality Test Raw:
Canvas Match Test Raw:
Cast Master State Test Raw:
Cast Binding Reference Test Raw:

PHASE3D VALIDATION CLOSURE:
CORE PANEL LOCALITY:
CORE CHARACTER LOCALITY:
5-PANEL ACTUAL GENERATION:
CAST MASTER FOUNDATION:
WORKFLOW17:
NEXT REGIONAL BACKEND:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3Dで最も重要な土台:

```text
Panel Layout geometry
+
Semantic content
+
Character areas
+
ControlNet
```

はできています。

今回確認するのは、

```text
その構造が「コード上正しい」だけでなく、
生成画像でも本当にTargetへ効いているか
```

です。

同時に、次予定だったCharacter / CAST Master UIの低結合部分を進めます。

ただし順序は:

```text
局所性を測る
↓
Core Backendが十分か判断
↓
十分ならCast / UXを拡張
↓
弱ければImpact RegionalSampler比較
```

です。

UIを先に完成させすぎて、Regional Backendの性能不足を後から発見する形は避けてください。

また、本番の漫画制作思想は引き続き:

```text
通常3〜5コマ
最大6 capacity
Character semantic regionsは重なり可能
Panel Layoutは独立したControlNet幾何
```

を維持してください。
