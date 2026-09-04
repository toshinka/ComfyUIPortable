# ComfyUI Portable Phase 3D — Variable N-Region Manga Integration & Layout-Aware Semantic Fusion 指示書

## 0. 対象 / Baseline

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
14a4feb31d5138238c0a385b4346333f1f8e2d2f
```

Phase 3C.1.2で、

```text
Backend Topology
Frontend Split API SSOT
Drag Preview / Commit分離
PANEL_LAYOUT_SPEC厳格化
ControlNet Fusion
```

まで進みました。

方向性は正しいです。

ただし外部コードレビューでは、Phase 3Dへ入る前に小さな契約上の穴が残っています。

今回は新しい小Phaseを独立させず、

```text
Phase 3D-0 Preflight Closure
↓
Phase 3D Variable N-Region Integration
```

として一続きで実施してください。

---

# 1. Phase 3C.1.2のレビュー判定

現状評価:

```text
BACKEND TOPOLOGY:
PASS

BACKEND SPLIT SSOT:
PASS

FRONTEND SPLIT WIRING:
PASS BY CODE REVIEW

TRANSACTIONAL DRAG:
MOSTLY PASS, ONE FAIL-OPEN PATH REMAINS

PANEL LAYOUT CONTRACT:
PASS WITH MINOR FIX

CONTROLNET FUSION:
PROMISING

PHASE 3D:
GO AFTER PRECHECK FIXES
```

Phase 3D-0の修正は軽量です。

ここで数週間止める必要はありません。

---

# 2. Phase 3D-0 — Drag API失敗時をFail-Closedへ

現在 `panel_layout_editor.js` のドラッグ確定処理は、

```text
/tegaki/panel-layout/validate
```

への通信に失敗した場合、

```javascript
node.setSpec(candidate, true)
```

としてLocal Fast Checkだけでcommitするfallbackがあります。

これは、

```text
Backend Validator = 契約上の正本
```

というPhase 3C.1.2の設計と矛盾します。

修正してください。

---

# 3. API unreachable時はcommitしない

推奨:

```text
API success + VALID
→ commit

API returns INVALID
→ rollback

API unreachable / timeout / fetch error
→ rollback
→ warning
```

です。

以下は禁止:

```text
API unreachable
→ local fast checkだけでcommit
```

Panel LayoutはPlanar Subdivision契約なのでFail-Closedにしてください。

---

# 4. committedSpec cleanup

drag transaction終了時、

```text
previewCandidateSpec
dragVertexId
committedSpec
```

の状態を整理してください。

成功・失敗・通信失敗の全経路で次dragへ状態が漏れないこと。

---

# 5. Phase 3D-0 — Vertex raw coordinateをclampしない

`panel_layout_spec.py` は現在raw vertexを:

```python
max(0.0, min(1.0, value))
```

でclampしてからTopology Validatorへ渡します。

Current default frameでは多くの場合Frame Boundsで最終rejectされますが、

```text
frame = full canvas [0,1]
```

の場合、

```text
raw x = 1.2
→ clamp 1.0
→ valid扱い
```

になり得ます。

契約Validatorとしては不適切です。

---

# 6. Vertex strict validation

保存済み `PANEL_LAYOUT_SPEC` のValidatorでは、

```text
x / y numeric
bool reject
finite
0 <= x <= 1
0 <= y <= 1
frame内
```

を満たさなければ `ValueError`。

黙ってclampしないでください。

UI drag側ではclampして構いません。

---

# 7. Phase 3D-0 — 「Frontend Parity」テスト表現を正確にする

現在:

```text
test_panel_layout_frontend_backend_parity.py
```

は実際のJS Frontend操作を実行せず、

```text
validate
generic_split_panel
validate
```

というBackend/API相当経路をテストしています。

またAPI route testもhandlerを直接呼び出しており、

```text
実ComfyUI HTTP route registration
```

までは証明していません。

コード構造は正しく改善されていますが、報告表現を正確にしてください。

---

# 8. テスト分類

以下に分離してください。

```text
A. Backend Geometry Parity
B. API Handler Unit Test
C. Runtime HTTP Route Smoke Test
D. Frontend Wiring Code Review
E. Browser Interaction Test
```

Playwright等が無い場合、Eは:

```text
PENDING
```

で構いません。

---

# 9. Runtime HTTP Route Smoke Test

新規または既存test拡張:

```text
scripts/test_panel_layout_http_routes.py
```

ComfyUIを実際に起動して、

```text
POST /tegaki/panel-layout/validate
POST /tegaki/panel-layout/split
```

をHTTP経由で呼び出してください。

確認:

```text
200 valid
400 invalid
split canonical result
```

これによりroute登録まで確認します。

---

# 10. Phase 3Dへ進むPreflight Gate

以下がPASSしたら、そのままPhase 3D本体へ進んでください。

```text
[ ] Drag API unreachable = rollback
[ ] Vertex raw coordinate fail-closed
[ ] Runtime HTTP route PASS
[ ] Existing Workflow14 PASS
[ ] Existing Workflow15 PASS
```

---

# 11. Phase 3Dの目的

ここから初めて、

```text
通常3〜5コマ
最大6 capacity
```

の漫画ページへ、

```text
Panel Prompt
Character Semantic Region
Local Semantic Region
Panel Layout ControlNet
```

を統合します。

重要なのは、

```text
Panel Layout geometry
```

と、

```text
Semantic Prompt content
```

を再び混同しないことです。

---

# 12. Phase 3Dの基本アーキテクチャ

目標:

```text
PANEL_LAYOUT_SPEC
      │
      ├→ Polygon Panel Masks
      ├→ ControlNet Layout Image
      │
      ▼
Layout-aware Mask Projection
      ▲
      │
REGION_SPEC / PAGE_COMPILE_PLAN
      │
      ├ Panel Prompt
      ├ Character Binding
      └ Local Region
```

最終:

```text
Global Conditioning
+
Panel Polygon Conditioning
+
Character Semantic Conditioning
+
Local Semantic Conditioning
+
Panel Layout ControlNet
↓
KSampler
```

---

# 13. PANEL_LAYOUT_SPECはPromptを持たない

維持してください。

```text
PANEL_LAYOUT_SPEC
=
geometry only
```

以下を入れない:

```text
prompt
negative prompt
character
LoRA
```

---

# 14. REGION_SPEC / Scene ContractをContent正本として維持

既存の:

```text
REGION_SPEC
CAST_SPEC
PAGE_COMPILE_PLAN
```

を捨てないでください。

これらは:

```text
Panel content
Character content
Local content
```

の正本です。

---

# 15. Layout-Driven Modeを追加する

既存Workflow 09/10互換のため、

```text
Legacy Rect Mode
```

を維持してください。

新規:

```text
Layout-Driven Mode
```

では、

```text
Panel mask geometry
=
PANEL_LAYOUT_SPEC polygon
```

を正本とします。

---

# 16. REGION_SPECのx/y/w/hを削除しない

既存Workflow互換とEditor用途のため残します。

Layout-Driven Modeでは:

```text
REGION_SPEC rect
=
legacy fallback / semantic preview

PANEL_LAYOUT_SPEC polygon
=
physical panel mask / ControlNet panel structure
```

と定義してください。

---

# 17. Panel Mappingが必要

REGION_SPECの:

```text
KOMA 1
KOMA 2
KOMA 3
...
```

と、

PANEL_LAYOUT_SPECの:

```text
p1
p2
p3
...
```

を対応付ける必要があります。

---

# 18. Phase 3D初期Mapping

最初はシンプルで構いません。

条件:

```text
active KOMA count
==
layout panel count
```

を必須。

Default mapping:

```text
Active KOMAをID昇順
↕
PANEL_LAYOUT_SPEC.panelsの保存順
```

例:

```text
KOMA1 → p1
KOMA2 → p2
KOMA3 → p3
```

---

# 19. MappingをDebug出力へ明示

新規derived object候補:

```text
PANEL_CONTENT_MAP
```

または単なる内部dictで構いません。

例:

```json
{
  "1": "p1",
  "2": "p2",
  "3": "p3"
}
```

別スキーマを増やす必要がないなら増やさないでください。

重要なのはdebugで明示されることです。

---

# 20. Panel count mismatchはFail-Closed

Layout-Driven Modeで:

```text
active content panels = 3
layout panels = 4
```

なら、

勝手に余りを無視しないでください。

```text
ValueError
```

または明示的BLOCK。

将来Mapping UIで解決します。

---

# 21. 新規: Layout-Aware Mask Builder

名称候補:

```text
Tegaki Manga Layout-Aware Mask Builder
```

または既存 `TegakiMangaMaskBuilder` のoptional拡張でも構いません。

ただし既存Workflowを壊さないこと。

---

# 22. Panel Polygon Mask

PANEL_LAYOUT_SPECの各Panel polygonから、

```text
MASK [N,H,W]
```

を生成してください。

PIL polygon / torch rasterization等で可。

Panel MaskはLayout polygonそのもの。

---

# 23. Panel Maskの順序

必ずMapping順と一致。

例:

```text
panel_masks[0] = KOMA1 mapped p1
panel_masks[1] = KOMA2 mapped p2
...
```

Debug JSONにindexを保存。

---

# 24. Character RegionのLayout-aware projection

既存Character Bindingの:

```text
area = KOMA-local x/y/w/h
```

を維持します。

Layout-driven panelがpolygonの場合、

まずそのPanel polygonのbbox:

```text
min_x
min_y
max_x
max_y
```

を計算。

KOMA-local rectをbboxへ投影。

その後:

```text
Character Rect Mask
AND
Panel Polygon Mask
```

してください。

---

# 25. Character Regionは重なってよい

人物A/Bは:

```text
overlap allowed
```

です。

同一コマ内で、

```text
A mask
B mask
```

が重なって構いません。

これはSemantic Regionの設計思想です。

---

# 26. Local Regionも同じ投影方式

Local Region:

```text
KOMA-local rect
→ panel polygon bbox
→ panel maskとintersection
```

としてください。

---

# 27. Panel bbox projectionの制約

これはV1方式です。

斜めPanel内でlocal coordinatesを簡単に扱うための妥協として妥当です。

報告書へ:

```text
Panel-local semantic coordinates are bbox-relative and clipped by polygon.
```

と明記してください。

将来必要ならbilinear / polygon local coordinatesへ拡張。

---

# 28. Polygon mask renderer utilityを共通化

Panel Layout Editorのgeometryから、

```text
ControlNet Guide
Panel Binary Masks
```

を別々のロジックで作りすぎないでください。

共通:

```text
validated PANEL_LAYOUT_SPEC
↓
canonical polygon points
```

から派生。

---

# 29. Layout-aware Conditioning Builder

既存 `TegakiMangaConditioningBuilder` は内部でLegacy Mask Builderを呼びます。

次のどちらかを選択してください。

### Option A

既存Conditioning Builderへoptional:

```text
panel_layout_spec
```

を追加。

存在時:

```text
layout-aware masks
```

を使用。

未接続:

```text
legacy rect masks
```

### Option B

新規:

```text
TegakiMangaLayoutAwareConditioningBuilder
```

を作り、共通Conditioning生成関数を共有。

外部互換性リスクが低い方を選択してください。

---

# 30. Widget Compatibilityを壊さない

もし既存Nodeへoptional inputを追加する場合、

既存 `widgets_values` positional compatibilityを再確認。

Link input追加によるFrontend restoreもテスト。

---

# 31. Conditioning順

維持:

```text
Global
Panel
Local Region
Character
```

ただし「上書きpriority」ではなく:

```text
Scope / append order
```

です。

---

# 32. Panel PromptはPolygon maskへ

これがPhase 3Dの中心です。

例:

```text
KOMA1:
classroom, two people talking

KOMA2:
school corridor

KOMA3:
rooftop sunset
```

が、

```text
Panel Layout p1/p2/p3 polygon
```

へ対応して効くこと。

---

# 33. Character Test

KOMA1:

```text
Alice:
blonde girl, left-ish area

Bob:
black-haired boy, right-ish area
```

A/B areaは重なりを持たせてください。

例:

```text
Alice:
x=.05 y=.08 w=.60 h=.85

Bob:
x=.35 y=.08 w=.60 h=.85
```

---

# 34. Character Interaction Prompt

KOMA1 Panel Prompt:

```text
two students talking closely, friendly interaction
```

Character PromptはIdentity中心。

目的:

```text
Regional separation
+
interaction
```

の両立確認。

---

# 35. 3 Panelを最初の実生成Targetにする

最初は3コマ。

理由:

```text
通常3〜5
```

の下限かつ観察しやすい。

Default Layout:

```text
3_basic
```

---

# 36. 4 Panel Test

次に:

```text
4_grid
```

またはDynamic layout。

Panel Prompt 4個を対応。

---

# 37. 5 Panel Test

PANEL_LAYOUT_SPECを安全Splitで5Panel化。

5 Panel Promptを対応。

Zero-Touch fixtureとして保存して構いません。

---

# 38. 6 PanelはCapacity Test中心

6コマ全部を毎回生成比較する必要はありません。

最低限:

```text
mapping
mask count
conditioning branches
workflow structural
```

を確認。

実画像1枚程度で十分。

---

# 39. N-Region Panel Locality Test

固定Seed。

3-panel layout。

Baseline:

```text
KOMA2 = school corridor
```

Variant:

```text
KOMA2 = convenience store aisle
```

KOMA1/KOMA3固定。

画像差分:

```text
mapped panel 2 inside
other panels
outside layout frame
```

を計測。

---

# 40. Polygon Locality Metric

既存Two Region Locality Metricの思想を再利用。

ただしPanel polygon maskから計測。

出力:

```text
target_panel_change
other_panel_change
outside_change
target/other ratio
```

raw値保存。

---

# 41. Character Locality Test

KOMA1 Aliceのみ:

```text
blonde hair
→ blue hair
```

Bob / Panel Prompt / Seed固定。

計測:

```text
Alice semantic mask
Bob semantic mask
Panel remainder
Other panels
```

---

# 42. Character Semantic Correctness

Pixel localityはSemantic correctnessではありません。

Geminiが画像を視覚確認可能なら:

```text
Alice identity
Bob identity
position
attribute bleed
interaction
```

を記録。

不可なら:

```text
VISUAL SEMANTIC REVIEW PENDING
```

としてください。

---

# 43. ControlNetとのFusion

PANEL_LAYOUT_SPECから:

```text
layout_image
```

を生成。

同じSpecから:

```text
panel polygon masks
```

を生成。

つまり:

```text
ControlNet geometry
=
Prompt mask geometry
```

を保証してください。

これがPhase 3Dの重要な統合ポイントです。

---

# 44. ControlNet Strength

最初:

```text
0.60
```

を基準。

必要なら:

```text
0.35
0.60
0.85
```

比較。

Phase 3C.1.1で得た知見を再利用。

---

# 45. ControlNet OFF比較

同じPanel mask Conditioningで:

```text
CN OFF
CN ON
```

を比較。

目的:

```text
Panel Prompt locality自体
+
Panel Layout framing補助
```

を分離して見ること。

---

# 46. Panel LayoutをPrompt mask sourceにも使う理由

今回から、

```text
Panel Layout ControlNet
```

と、

```text
Panel Prompt mask
```

は同一geometryから派生します。

ただし:

```text
Character semantic areas
```

は独立して重なります。

設計分離は維持されています。

---

# 47. Region Editorとの関係

既存 `TegakiMangaRegionEditor` を捨てない。

当面:

```text
REGION_SPEC content editor / legacy geometry
```

として維持。

Phase 3DではPanel physical geometryはPANEL_LAYOUT_SPECを優先。

---

# 48. Panel Prompt UI

今は完成GUI不要。

最低限:

```text
KOMA1 Prompt
KOMA2 Prompt
KOMA3 Prompt
...
```

がDebug/Workflow上で確認できればよい。

全6欄を常時巨大表示する必要はありません。

---

# 49. 可変UIは後段Shellで行う

本番思想:

```text
通常3〜5
最大6 capacity
Activeだけ表示
```

を維持。

ComfyUI Node内部ではJSON / custom canvasで十分。

---

# 50. CAST UIはまだ完成させない

Character Master UIは将来必要ですが、

Phase 3Dでは:

```text
CAST_SPEC fixture / JSON
```

でも構いません。

今回の優先は:

```text
Panel + Character Regional Fusion
```

の生成実証。

---

# 51. LoRA方針

Global LoRA:

```text
実際にMODELへ適用してよい
```

Panel / Character LoRA:

```text
Compile Planには保持
```

しますが、

まだRegional LoRA実装はしない。

以下を絶対に誤認させない:

```text
character_lora_plan exists
≠
spatial LoRA is applied
```

---

# 52. RLLはまだ行わない

Phase 3DではCore Masked ConditioningをPrimary。

RLLは別研究Phase。

---

# 53. Workflow 16

新規:

```text
16_MANGA_VARIABLE_N_REGION_LAYOUT_FUSION_POC.json
```

区分:

```text
EXPERIMENTAL / END-TO-END MANGA REGIONAL FUSION
```

---

# 54. Workflow 16の最低構成

左から:

```text
[MODEL]
Checkpoint
Global LoRA

[CONTENT]
Manga Region Editor / REGION_SPEC
CAST_SPEC

[LAYOUT]
Manga Panel Layout Editor
PANEL_LAYOUT_SPEC
Layout Preview

[COMPILE]
Page Compiler
Layout Mapping / Layout-Aware Bridge

[MASK]
Polygon Panel Masks
Character Semantic Masks
Local Semantic Masks
Mask Preview

[CONDITIONING]
Layout-Aware Conditioning Builder

[CONTROL]
Panel Layout ControlNet

[SAMPLE]
KSampler
VAE Decode

[OUTPUT]
Preview
Save

[DEBUG]
Panel Map
Compile Plan
Mask Debug
Conditioning Debug
```

---

# 55. Workflow 16 Default content

3 Panels Basic。

KOMA1:

```text
classroom, two students talking closely
Alice + Bob
```

KOMA2:

```text
school corridor, walking
Alice only
```

KOMA3:

```text
rooftop, sunset sky
Bob only
```

---

# 56. Character master fixture

例:

```text
Alice:
1girl, blonde twin tails, school uniform

Bob:
1boy, short black hair, school uniform
```

Negativeは簡潔。

---

# 57. Workflow 16で見えるべきDebug

最低限:

```text
Active KOMA Count = 3
Layout Panel Count = 3

Mapping:
KOMA1 → p1
KOMA2 → p2
KOMA3 → p3

Panel mask type = polygon
Character areas = panel-bbox-local + clipped
ControlNet guide source = same PANEL_LAYOUT_SPEC
```

---

# 58. Workflow 16 Zero-Touch

必須:

```text
ComfyUI restart
load
no touch
Queue
image
```

---

# 59. Workflow 17 — 5 Panel Stress Test

Phase 3D後半で余力があれば:

```text
17_MANGA_5_PANEL_REGIONAL_STRESS_TEST.json
```

を作成。

目的:

```text
N=5
mapping
conditioning count
memory
generation
```

完成UIではない。

---

# 60. Workflow 17は必須ではない

Phase3Dの必須はWorkflow16。

5Panelはtest scriptだけでも可。

---

# 61. 新規コード候補

実装判断はGeminiに任せますが候補:

```text
layout_region_bridge.py
layout_aware_mask_builder.py
layout_aware_conditioning.py
```

不要にNodeを増やすより純粋関数を優先。

---

# 62. Bridge責務

新しいBridgeは最低限:

```text
validate REGION_SPEC
validate PAGE_COMPILE_PLAN
validate PANEL_LAYOUT_SPEC
active panel count check
stable mapping
polygon extraction
bbox extraction
debug mapping
```

---

# 63. PAGE_COMPILE_PLANを破壊的変更しない

既存09/10互換のため、

V1構造を壊す大変更は避ける。

Layout情報は:

```text
external optional context
```

または未知フィールドとしてappend。

---

# 64. geometry type拡張を行う場合

もしCompile PlanへPolygon geometryを入れる方が明快なら、

Backward-compatibleに:

```json
"geometry": {
  "type": "polygon",
  "points": [...],
  "bbox": {...},
  "layout_panel_id": "p1"
}
```

を追加して構いません。

Legacy:

```text
type missing
→ rect
```

とすること。

既存Validator/Workflowを破壊しない。

---

# 65. Mask Builderの戻り順を壊さない

既存Nodeを拡張する場合、Return index互換に注意。

新Nodeの方が安全なら新Node。

---

# 66. Test — Layout Mapping

新規:

```text
scripts/test_layout_region_mapping.py
```

最低限:

```text
N=1
N=3
N=4
N=5
N=6
mismatch reject
stable order
disabled KOMA ignored
```

---

# 67. Test — Polygon Mask Builder

新規:

```text
scripts/test_layout_aware_masks.py
```

最低限:

```text
3_basic panel masks
3_dynamic polygon masks
4_grid
5-panel generated layout
mask count
non-overlap panel masks
frame coverage
```

---

# 68. Character Mask Tests

最低限:

```text
single character
two overlapping characters
character area clipped by polygon
slanted panel
disabled character
```

---

# 69. Local Region Tests

最低限:

```text
local rect projected in bbox
clipped by polygon
overlap with character allowed
```

---

# 70. Conditioning Tests

新規候補:

```text
scripts/test_layout_aware_conditioning.py
```

確認:

```text
Global branch
N panel branches
local branches
character branches
mask indices match debug map
```

---

# 71. Runtime Generation Test

新規:

```text
scripts/test_phase3d_variable_region_generation.py
```

最低限:

```text
3 panel CN OFF
3 panel CN ON
KOMA2 prompt A/B
Alice A/B
5 panel one generation optional
```

---

# 72. Performance

記録:

```text
N=3 generation time
N=5 generation time
VRAM if available
conditioning branch count
```

厳密benchmark不要。

---

# 73. Prompt長の観察

ユーザー懸念:

```text
漫画ページではPromptが長くなりやすい
```

があります。

Phase 3D報告で:

```text
Global token scope
Panel prompt scope
Character prompt scope
```

の文字列長/概算tokenを記録して構いません。

ただし今回Sequential Panel Samplingは実装しない。

---

# 74. BREAKについて

Prompt結合Previewでは必要ならBREAK研究を記録して構いません。

しかしCore Masked Conditioningでは各branchが別encodeされるため、

```text
全Promptを1本へ無理にBREAKで押し込む
```

必要はありません。

この利点を報告書へ明記してください。

---

# 75. Sequential Panel Processingは今回しない

ユーザーが以前考えた:

```text
コマ毎に順に処理
```

は将来候補。

Phase3Dでは:

```text
single KSampler
multi masked conditioning
```

を優先。

必要性が見えたらImpact RegionalSampler / Sequential backendと比較。

---

# 76. User Manual Testはまだ要求しない

今回もGemini Self Test + GPT Code Reviewを優先。

ユーザーへ次に見せるべき状態:

```text
Workflow16
+
3-panel ControlNet layout
+
Panel-specific Prompt
+
same-panel overlapping Alice/Bob Character Regions
+
actual manga generation
```

が揃った時。

---

# 77. Phase 3D報告書

新規:

```text
PHASE3D_VARIABLE_N_REGION_MANGA_INTEGRATION_REPORT.md
```

最低限:

```text
1. 3C.1.2 Preflight Corrections
2. Runtime HTTP Route Test
3. Architecture Overview
4. Layout-Driven Mode
5. Content/Layout Separation
6. Panel Mapping
7. Polygon Panel Masks
8. Character Projection
9. Local Region Projection
10. Layout-Aware Conditioning
11. ControlNet Geometry Sharing
12. 3 Panel Test
13. 4 Panel Test
14. 5 Panel Test
15. 6 Capacity Test
16. Panel Prompt Locality
17. Character Locality
18. Semantic Visual Review
19. CN OFF/ON
20. Prompt Scope / Length
21. Performance
22. Workflow16
23. Regression 09〜15
24. Known Issues
25. Next Phase
26. Gemini独自判断
```

---

# 78. Existing Workflow Regression

最低限:

```text
09
10
11
12
13
14
15
```

を壊さない。

特に:

```text
09 Zero-Touch
10 Zero-Touch
14 Preview
15 Zero-Touch Generate
```

を確認。

---

# 79. Acceptance Criteria — Preflight

```text
[ ] Drag API failure is fail-closed
[ ] No local-only commit fallback
[ ] Raw vertex outside [0,1] rejected
[ ] Runtime HTTP split route PASS
[ ] Runtime HTTP validate route PASS
[ ] Report terminology corrected
```

---

# 80. Acceptance Criteria — N Panel

```text
[ ] Active KOMA count 1〜6
[ ] Layout panel count 1〜6
[ ] Count mismatch rejected
[ ] Stable KOMA ↔ Layout mapping
[ ] N=3
[ ] N=4
[ ] N=5
[ ] N=6 structural
```

---

# 81. Acceptance Criteria — Masks

```text
[ ] Polygon panel masks
[ ] Layout mask matches ControlNet layout source
[ ] Character bbox-local projection
[ ] Character mask clipped by polygon
[ ] Character overlap allowed
[ ] Local Region clipped by polygon
```

---

# 82. Acceptance Criteria — Conditioning

```text
[ ] Global conditioning
[ ] Panel polygon conditioning
[ ] Character conditioning
[ ] Local conditioning
[ ] debug mapping correct
[ ] legacy rect mode still works
```

---

# 83. Acceptance Criteria — Generation

```text
[ ] Workflow16 Zero-Touch
[ ] 3-panel image generated
[ ] CN OFF generated
[ ] CN ON generated
[ ] Panel Prompt A/B generated
[ ] Character Alice A/B generated
[ ] 5-panel generation or runtime integration test
```

---

# 84. Phase終了判定

報告書末尾:

```text
3C.1.2 PREFLIGHT:
PASS / HOLD

VARIABLE N-PANEL MAPPING:
PASS / HOLD

POLYGON PANEL CONDITIONING:
PASS / HOLD

CHARACTER SEMANTIC FUSION:
PASS / HOLD

PANEL LAYOUT CONTROLNET FUSION:
PASS / PARTIAL / FAIL

WORKFLOW16:
PASS / HOLD

PHASE 3D RESULT:
PASS / PARTIAL / FAIL

NEXT RECOMMENDED PHASE:
```

---

# 85. 次Phase候補

Phase 3DがPASSした場合、次を比較検討してください。

### Candidate A — Character / CAST Master UI

ユーザーが以前提案した:

```text
キャラクターカード
出演コマ指定
Prompt
LoRA
```

のUI。

### Candidate B — N-Region User Shell

```text
3〜5 active panels
不要項目を隠す
selected panel editor
```

### Candidate C — ControlNet Pose Integration

```text
OpenPose / Depth
```

をCharacter単位へ。

### Candidate D — Regional Backend Comparison

Coreで不足が見えた場合のみ:

```text
Impact RegionalSampler
```

へ。

Phase 3D結果から優先順位を決めてください。

---

# 86. LoRAの次段階

Phase 3D終了後でもRegional LoRAは別扱い。

```text
Global LoRA
```

と、

```text
Character / Panel LoRA Plan
```

を明確に区別。

RLLを開始するなら別Phaseとしてレビューする。

---

# 87. GITHUB.TXT二段Commit

まず:

```text
Commit A
Phase 3D Variable N-Region Manga Integration
```

として:

```text
Preflight fixes
implementation
tests
Workflow16
report
```

をcommit。

SHA取得。

Navigation commitで:

```text
Review Target Commit SHA: A
```

へ更新。

Latest URL:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

---

# 88. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3D_VARIABLE_N_REGION_MANGA_INTEGRATION_REPORT Raw:

Layout Region Bridge Raw:
Layout-Aware Mask Builder Raw:
Layout-Aware Conditioning Raw:

Workflow 16 Raw:
Workflow 17 Raw: (if created)

Layout Mapping Test Raw:
Layout-Aware Mask Test Raw:
Layout-Aware Conditioning Test Raw:
Runtime Generation Test Raw:
HTTP Route Test Raw:

3C.1.2 PREFLIGHT:
VARIABLE N-PANEL MAPPING:
POLYGON PANEL CONDITIONING:
CHARACTER SEMANTIC FUSION:
PANEL LAYOUT CONTROLNET FUSION:
WORKFLOW16:
PHASE 3D RESULT:

NEXT RECOMMENDED PHASE:
```

---

# 最終方針

ここまでの地固めで、

```text
Panel Layout
=
安全な漫画コマ割り幾何

Semantic Region
=
重なってよい意味領域
```

という二系統はかなり明確になりました。

Phase 3Dでは初めてこの二つを制作上の構造として統合します。

ただしデータ契約は混ぜません。

```text
PANEL_LAYOUT_SPEC
→ panel polygon
→ ControlNet
→ panel mask

REGION_SPEC / CAST_SPEC
→ Prompt / Character / Local Region
```

をBridgeで結びます。

これにより、

```text
3〜5コマのページ構造をControlNetで誘導しつつ、
各コマへ別Promptを効かせ、
同じコマ内では人物A/BのSemantic Regionを重ねて
会話・接触・演技の余地を残す
```

ことを目指してください。

最大6はcapacityです。

常時6コマを表示・生成する思想にはしません。

Phase 3DのWorkflow16が成立した段階で、次回はユーザーが実画像とレイアウトを確認する価値が出てきます。
