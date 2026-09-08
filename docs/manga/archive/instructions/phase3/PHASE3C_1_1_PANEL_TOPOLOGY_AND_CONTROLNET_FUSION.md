# ComfyUI Portable Phase 3C.1.1 — Panel Topology Hardening & ControlNet Fusion Oracle 指示書

## 0. Baseline

対象:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
a1175f6f79ee91e34102dec23ef7d8e69057aa87
```

Phase 3C.1 で成立した設計分離は維持します。

```text
Semantic Region
= 重なってよい意味領域

Panel Layout
= 重ならない漫画コマ割り幾何
```

ただし、Panel Layout は現状まだ「shared vertexを使ったPolygon集合」の段階であり、安全なPlanar Subdivisionとしては未完成です。

Gemini提案の Phase 3D へ直接進まず、まず本PhaseでPanel Layoutのトポロジーを固めてください。

---

# 1. 今回の優先順位

```text
1. Panel Layout Validatorの実装と報告書を一致させる
2. Splitを任意の有効Panel形状で安全にする
3. Shared Vertex Dragをvalidate/rollback方式へする
4. gap / overlap / T-junctionを検査する
5. Panel LayoutをControlNetへ実接続する
6. Overlap Semantic Regionとの共存を生成で確認する
7. その後にPhase 3Dへ進む
```

今回はまだ本番N-Region / 3〜5コマRegional Prompt統合を行いません。

---

# 2. GITHUB.TXT運用

Phase 3C.1実装Commit:

```text
a1175f6f79ee91e34102dec23ef7d8e69057aa87
```

Navigation commit:

```text
55aa38c149924e06b3108ec95a2a68a93aaa8e7f
```

二段commit方式は正常です。

今後、最終報告では:

```text
Review Target Commit SHA:
<implementation commit>

Latest GITHUB.TXT Raw:
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

を提示してください。

---

# 3. Critical Review Finding — Validator不足

Phase 3C.1報告書では、

```text
self-intersectionなし
winding統一
隙間/重なりなし
```

が成立したように記載されています。

しかしReview Targetの `panel_layout_spec.py` で確認できる主検査は:

```text
canvas
vertex type/range
unique IDs
panel count 1〜6
vertex references
minimum area
```

までです。

最低限以下を追加してください。

```text
self-intersection
duplicate vertex in panel cycle
zero-length edge
consistent winding
edge crossing
T-junction
panel overlap
panel gap
shared-edge incidence
```

既存報告書も、実装完了までは「full topology validation pending」相当に修正してください。

---

# 4. PANEL_LAYOUT_SPECをPlanar Subdivisionとして定義

単なるPolygon集合ではなく:

```text
1つのLayout Frameを
1〜6枚のPanelが分割する
planar subdivision
```

として扱ってください。

Invariant:

```text
各Panelはsimple polygon
面積 > minimum
Panel内部は互いに重ならない
内部境界は隣接Panelで共有
T-junctionなし
全Panel unionはLayout Frameを覆う
```

---

# 5. Layout Frameを明示

現在Presetは `.05〜.95` の余白を持っています。

これを暗黙値にせず、optional/canonicalな:

```json
"frame": {
  "x": 0.05,
  "y": 0.05,
  "w": 0.90,
  "h": 0.90
}
```

として扱うことを推奨します。

既存v1互換:

```text
frame missing
→ current defaultを補完
```

で構いません。

全Panelはframe内、unionはframeと一致させてください。

---

# 6. Topology Utilityを独立

新規候補:

```text
custom_nodes_custom/tegaki_manga_nodes/panel_layout_topology.py
```

最低限:

```python
signed_area()
normalize_winding()
segments_intersect()
polygon_self_intersects()
polygon_is_convex()
point_on_segment()
edge_key()
build_edge_incidence()
validate_layout_topology()
```

V1ではPanelをconvex polygon限定にして構いません。

漫画コマとして当面必要なのは:

```text
矩形
台形
斜め四角
三角
```

程度であり、convex制約は安全性に有利です。

---

# 7. Panel Cycle Validation

各Panel:

```text
vertex_ids >= 3
同じvertex IDをcycle内で重複使用しない
先頭IDを末尾へ重複保存しない
zero-length edgeなし
self-intersectionなし
area >= MIN_PANEL_AREA
winding統一
```

を保証してください。

CWをCCWへCanonicalizeするか、rejectするか方針を統一してください。

---

# 8. Edge Incidence

全Panel edgeからcanonical edge tableを構築。

期待:

```text
frame outer edge:
incidence = 1

internal shared edge:
incidence = 2
```

3Panel以上が同じedgeを共有する状態はrejectしてください。

---

# 9. T-Junctionを禁止

重要です。

共有edge:

```text
v1 -------- v2
```

の途中でsplit intersection `v_new` を作る場合、

```text
Panel A: v1 -- v_new -- v2
Panel B: v1 -- v_new -- v2
```

のように、そのedgeを共有する全Panel cycleへ同じvertex IDを挿入してください。

片側だけ:

```text
v1 -- v_new -- v2
```

にならないこと。

---

# 10. Current Split Algorithmを置き換える

現在FrontendのHorizontal / Vertical Splitは:

```text
bounding box
+
pts.find(...)
```

を使っています。

Diagonalは実質:

```text
targetPanel.vertex_ids[0..3]
```

前提です。

これは:

```text
5頂点Panel
斜めPanel
変形後Panel
再Split
```

で頂点欠落・範囲外生成・gap/overlapを起こし得ます。

本番利用しないでください。

---

# 11. Generic Split by Line

新しいSplitは:

```text
panel polygon
+
split line
```

から2polygonを生成する一般アルゴリズムにしてください。

V1はconvex前提で可。

候補:

```text
half-plane clipping
Sutherland-Hodgman style clipping
```

---

# 12. Horizontal / Vertical / Diagonal

Horizontal:

```text
polygonと y = split position の交点
```

Vertical:

```text
polygonと x = split position の交点
```

を使う。

split_ratio default 0.5。

Diagonalは「最初の4頂点」を使わず:

```text
/  direction
\  direction
```

のlineでpolygonをclipしてください。

---

# 13. Intersection VertexのGlobal Mesh統合

split lineとedgeの交点が既存vertexへepsilon以内ならreuse。

edge途中ならnew vertex。

そのedgeを共有する全Panelへ同じvertexをinsertしてください。

---

# 14. Area Conservation

Split前:

```text
A_before
```

Split後:

```text
A1 + A2
```

で:

```text
abs(A_before - (A1 + A2)) <= epsilon
```

を必須化。

Split後はfull topology validationを行い、失敗時rollback。

---

# 15. Shared Vertex DragをTransactionalにする

現在はdrag中に座標を直接更新しています。

変更:

```text
last valid spec
↓
candidate vertex move
↓
topology validation
```

VALIDならcommit。

INVALIDなら:

```text
candidateを捨て
last valid geometryを維持
```

してください。

---

# 16. Outer Boundary Constraint

frame boundary上のvertexは、そのframe edge上だけ移動させる方式を推奨。

例:

```text
top edge vertex:
xのみ可
y = frame.y固定
```

Cornerは固定でも構いません。

Interior vertexは2D移動可。ただしvalidate必須。

---

# 17. Gap / Overlap Diagnostic

2系統用意してください。

Structural:

```text
edge incidence
T-junction
area conservation
```

Diagnostic Raster:

frame内を低解像度maskへrasterizeし:

```text
coverage=0 → gap
coverage>=2 → overlap
```

を計測。

出力例:

```text
gap_ratio
overlap_ratio
frame_area
panel_area_sum
shared_edge_count
t_junction_count
```

---

# 18. Production Algorithmをテストする

現在の `test_panel_layout_state.py` はSplit結果をテスト側で手作業構築しており、Frontendの実Split algorithm自体を検証していません。

これを改めてください。

可能なら共通fixture:

```text
tests/fixtures/panel_layout_cases.json
```

を作成。

---

# 19. 必須Split Regression Matrix

```text
1_full → H
1_full → V
1_full → /
1_full → \

3_basic p1 → H
3_basic p1 → V
3_basic p1 → diagonal

3_dynamic slanted panel → H
3_dynamic slanted panel → V
3_dynamic slanted panel → diagonal

shared vertex移動後 → split

repeat split → 5 panels
repeat split → 6 panels
7th split → refuse
```

---

# 20. 必須Invalid Cases

```text
bow-tie self-intersection
duplicate cycle vertex
zero-length edge
panel inversion
invalid shared vertex drag
T-junction
gap
overlap
```

を明示的にテストしてください。

---

# 21. RendererをUnique Edge駆動へ

現在RendererはPanelごとに外周を描くため、shared internal edgeが二重描画されます。

大きな問題ではありませんが、トポロジー正本として:

```text
PANEL_LAYOUT_SPEC
↓
canonical unique edge table
↓
each edge exactly once
```

で描画する方を推奨します。

ControlNet出力は:

```text
white background
black line
no label
no panel number
no vertex handle
```

を維持。

---

# 22. Accidental __pycache__ / .pycを除去

Phase 3C.1 diffに:

```text
scripts/__pycache__/run_two_region_oracle_experiments.cpython-313.pyc
```

が追加されています。

Git管理から削除し:

```text
__pycache__/
*.pyc
```

が `.gitignore` で除外されることを確認してください。

---

# 23. Semantic Two-Region側はRegressionのみ

今回Semantic Regionへ大きな機能追加はしません。

維持確認:

```text
Overlap default
A/B Move
A/B Resize
Create
Disable
Prompt clear
save/reload
Workflow 11
Workflow 12
```

ユーザーへ手動確認依頼はまだ不要です。

---

# 24. ControlNet Fusionへ進むGate

Panel topology関連テストが全PASSした後だけ、以下へ進んでください。

---

# 25. Workflow 15

新規:

```text
15_MANGA_PANEL_LAYOUT_CONTROLNET_FUSION_ORACLE.json
```

区分:

```text
EXPERIMENTAL / COMPOSITION FUSION ORACLE
```

構造:

```text
Checkpoint
↓
Two Region Semantic Editor
↓
Core Masked Conditioner
        +
Panel Layout Editor
↓
layout_image
↓
ControlNet
        ↓
KSampler
↓
VAE Decode
↓
Save / Preview
```

---

# 26. Specは独立を維持

Workflow上では合流しますが:

```text
TWO_REGION_SPEC
PANEL_LAYOUT_SPEC
```

を1つへ混ぜないでください。

Panel LayoutはPromptを持たない。

Semantic Regionはコマ割り幾何を持たない。

---

# 27. Workflow 15初期Scene

Panel Layout:

```text
3 Panels Basic
```

Semantic Regions:

```text
上段Panel付近へ
A = woman
B = man
Semantic Overlap
```

Global Prompt例:

```text
manga page, three panels, two people talking in the upper panel
```

---

# 28. ControlNet

Phase 3Cで利用した:

```text
CN-anytest4_illustrious2_A.safetensors
```

をまず使用。

固定Seedで:

```text
CN OFF
0.35
0.60
0.85
```

程度を比較。

---

# 29. Layout Variant Test

最低限:

```text
3_basic
3_dynamic
4_grid
safe diagonal split
```

を生成。

確認:

```text
panel framing tendency
panel boundary response
Semantic A/B placement
attribute leakage
A/B interaction
composition rigidity
```

---

# 30. ControlNetがInteractionを壊さないか確認

ControlNetが強すぎると:

```text
A/Bが離れる
interactionが弱まる
人物が枠へ引っ張られる
```

可能性があります。

今回の固定Sceneで観察し、強度の目安を記録。

一般化しすぎないこと。

---

# 31. Layout Edge Response Metric

可能なら:

```text
layout_edge_response_metric
```

をDiagnosticとして追加。

Guide黒線付近と生成画像のedge responseを比較。

これは構図の意味的正しさを証明する指標ではありません。

---

# 32. Contact Sheet

Runtime outputへ:

```text
CN OFF / .35 / .60 / .85
```

および:

```text
3_basic / 3_dynamic / 4_grid / diagonal
```

のContact Sheetを作成して構いません。

Gitへ大量画像は追加しないこと。

---

# 33. Tests — 新規

最低限:

```text
scripts/test_panel_layout_topology.py
scripts/test_panel_layout_split_operations.py
scripts/test_panel_layout_drag_validation.py
scripts/test_panel_layout_controlnet_fusion.py
```

---

# 34. topology test

最低限:

```text
valid presets
self intersection reject
duplicate cycle vertex reject
zero edge reject
winding
edge incidence
T-junction
gap diagnostic
overlap diagnostic
frame area
panel area sum
```

---

# 35. split test

前述Regression Matrix全件。

---

# 36. drag validation test

```text
valid shared vertex move
invalid crossing move reject
degenerate move reject
outer boundary constraint
rollback exact
```

---

# 37. ControlNet Fusion Test

API/runtimeで:

```text
Workflow15 equivalent
CN OFF
CN ON
image generation
output path
```

を確認。

---

# 38. Workflow Regression

最低限:

```text
09
10
11
12
13
14
```

を壊さない。

Workflow 14:

```text
load
no touch
Preview
```

PASS。

Workflow 15:

```text
ComfyUI restart
load
no touch
Queue
image
```

PASS必須。

`test_workflow_json_integrity.py` と `test_workflow_widget_compatibility.py` も15まで拡張。

---

# 39. Phase 3C.1報告書を訂正

既存:

```text
PHASE3C_1_SEMANTIC_REGION_AND_PANEL_LAYOUT_REPORT.md
```

の、現実装以上に強い:

```text
self-intersection防止済み
gap/overlapが幾何学的に不可能
```

等の主張は修正してください。

履歴:

```text
Corrected in Phase 3C.1.1
```

を記録。

---

# 40. 新規報告書

```text
PHASE3C_1_1_PANEL_TOPOLOGY_AND_CONTROLNET_FUSION_REPORT.md
```

最低限:

```text
1. Phase3C.1 Review Findings
2. Report Corrections
3. Planar Subdivision Definition
4. Layout Frame
5. Polygon Validation
6. Convex V1 Policy
7. Edge Incidence
8. T-Junction Handling
9. Generic Split Algorithm
10. H/V/Diagonal Split
11. Intersection Vertex Propagation
12. Area Conservation
13. Transactional Vertex Drag
14. Gap/Overlap Diagnostic
15. Unique Edge Renderer
16. Workflow14 Regression
17. Workflow15
18. ControlNet OFF/ON
19. Layout Variants
20. Semantic Region Coexistence
21. ControlNet Strength Observation
22. Tests
23. Browser Test
24. Known Issues
25. Phase3D Readiness
26. Gemini独自判断
```

---

# 41. Phase 3Dへ進む条件

以下が揃ってから:

```text
PANEL_LAYOUT_TOPOLOGY: PASS
SAFE SPLIT: PASS
SAFE VERTEX DRAG: PASS
NO T-JUNCTION: PASS
NO GAP/OVERLAP: PASS
WORKFLOW 14: PASS
WORKFLOW 15: PASS
SEMANTIC + PANEL FUSION: PROMISING
```

Phase 3Dへ進んでください。

---

# 42. Phase 3D予定

次Phaseの目標だけ記録:

```text
通常3〜5 active panels
最大6 capacity

Global Prompt
Panel Prompt
各Panel内 Character Semantic Regions
Local Regions
Panel Layout ControlNet
```

ただし今回実装しない。

Panel LayoutとPrompt契約の独立は維持します。

---

# 43. Acceptance Criteria

```text
[ ] self-intersection validator
[ ] duplicate cycle vertex validator
[ ] winding rule
[ ] zero edge validator
[ ] edge incidence
[ ] T-junction detection
[ ] split intersection propagation
[ ] area conservation

[ ] generic H split
[ ] generic V split
[ ] generic diagonal split
[ ] split after deformation
[ ] repeat split to 5
[ ] repeat split to 6
[ ] reject 7th

[ ] transactional vertex drag
[ ] invalid move rollback
[ ] outer boundary constraint

[ ] gap diagnostic
[ ] overlap diagnostic
[ ] unique-edge renderer

[ ] accidental .pyc removed

[ ] Workflow14 regression PASS
[ ] Workflow15 Zero-Touch PASS
[ ] CN OFF/ON generated
[ ] Semantic A/B + Panel Layout CN coexistence evaluated
[ ] Existing 09〜13 non-destructive
```

---

# 44. 終了判定

報告書末尾:

```text
PANEL_LAYOUT_TOPOLOGY:
PASS / HOLD

SAFE SPLIT:
PASS / HOLD

SAFE VERTEX DRAG:
PASS / HOLD

CONTROLNET PANEL LAYOUT:
PROMISING / PARTIAL / FAIL

SEMANTIC + PANEL FUSION:
PROMISING / PARTIAL / FAIL

PHASE 3D READINESS:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 45. GITHUB.TXT二段Commit

まず:

```text
Commit A
Phase 3C.1.1 Panel Topology Hardening & ControlNet Fusion Oracle
```

としてimplementation / tests / Workflow15 / reportsをcommit。

そのSHAを取得。

Navigation commitで:

```text
Review Target Commit SHA: A
```

へ更新。

最終回答のLatest GITHUB.TXTは:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

を提示してください。

---

# 46. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3C_1_1_PANEL_TOPOLOGY_AND_CONTROLNET_FUSION_REPORT Raw:

Panel Layout Spec Raw:
Panel Layout Topology Raw:
Panel Layout Editor Raw:
Panel Layout Editor JS Raw:

Workflow 14 Raw:
Workflow 15 Raw:

Topology Test Raw:
Split Test Raw:
Drag Validation Test Raw:
ControlNet Fusion Test Raw:

PANEL_LAYOUT_TOPOLOGY:
SAFE SPLIT:
SAFE VERTEX DRAG:
CONTROLNET PANEL LAYOUT:
SEMANTIC + PANEL FUSION:
PHASE 3D READINESS:
NEXT RECOMMENDED PHASE:
```

を提示してください。

---

# 最終方針

Phase 3C.1で得た:

```text
Semantic Region
= 重なってよい

Panel Layout
= 重ならない共有境界
```

という設計分離は正しいので維持します。

ただしShared Vertexを採用しただけでは、安全な漫画コマ割りMeshとは言えません。

```text
Split交点の共有
T-junction防止
自己交差防止
gap/overlap検査
invalid drag rollback
```

まで成立して初めて、

```text
「一つの境界を動かすと隣接コマも正しく変形する」
```

ツールになります。

そこを固めた上でWorkflow 15により:

```text
Panel Layout ControlNet
+
Overlap Semantic Regions
```

を同時に実証し、有望ならPhase 3Dで

```text
通常3〜5コマ
最大6 capacity
+
各コマ内Character Regions
```

へ進んでください。
