# ComfyUI Portable Phase 3C.1.2 — Frontend / Backend Geometry Parity & Topology Contract Closure 指示書

## 0. 対象 / Baseline

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
40df7cebb633d6442709dd0ee643cc5709d8468e
```

Phase 3C.1.1で、`panel_layout_topology.py`、`panel_layout_split.py`、Workflow 15、ControlNet Fusion Oracleまで進みました。Backend側には self-intersection / convexity / T-Junction / edge incidence / area conservation / generic polygon split / ControlNet fusion が実装されています。

この方向性は維持します。

ただし外部コードレビューの結果、Backendで実証した安全なGeometryと、実際にユーザーが触るFrontend Editorがまだ同じアルゴリズムを使っていません。Phase 3Dへ進む前に、この差を閉じてください。

---

# 1. 今回の最重要結論

Phase 3C.1.1は、

```text
BACKEND TOPOLOGY:
大幅前進

CONTROLNET FUSION:
有望

FRONTEND PANEL EDITOR:
まだBackendと同等ではない
```

という状態です。

したがって今回のPhaseは、

```text
Frontend / Backend Geometry Parity
```

を最優先にします。新しい漫画機能は増やさないでください。

---

# 2. Critical Finding 1 — Frontend SplitがBackend generic_split_panelを使っていない

Backend:

```text
custom_nodes_custom/tegaki_manga_nodes/panel_layout_split.py
```

には `generic_split_panel()` が実装され、Sutherland-Hodgman style clipping / intersection propagation / T-Junction防止 / full topology validation を行っています。

一方Frontend:

```text
web/js/panel_layout_editor.js
```

の `node.splitSelectedPanel(...)` は現在も、bounding box、minX/maxX/minY/maxY、手作業のvertex追加、targetPanel.vertex_idsの位置依存による別実装です。

これはPhase 3C.1で問題になった旧方式の変形版であり、Backend generic splitとは別物です。

---

# 3. Frontend SplitをSSOTへ統合する

理想:

```text
Python backend generic_split_panel
=
SplitのSingle Source of Truth
```

としてください。Frontend側に同じ複雑なPolygon Splitを再実装しないことを優先してください。

---

# 4. 推奨方式 — Backend API Route

ComfyUI custom node側で利用可能なRoute機構を実環境から確認し、可能なら:

```text
POST /tegaki/panel-layout/split
POST /tegaki/panel-layout/validate
```

相当の軽量APIを追加してください。正確なpath名は改善可です。

推測で実装せず、現在のComfyUI `PromptServer` / aiohttp route APIを確認してください。

Split API入力例:

```json
{
  "spec": {...},
  "panel_id": "p2",
  "mode": "horizontal",
  "split_ratio": 0.5
}
```

処理:

```text
validate input
↓
generic_split_panel()
↓
validate_panel_layout_spec()
↓
canonical result
```

出力例:

```json
{
  "ok": true,
  "spec": {...},
  "topology_summary": {...}
}
```

失敗時はSpecを変更せずerrorを返してください。

---

# 5. Frontend Split Button

FrontendのSplit Horizontal / Vertical / `/` / `\\` は:

```text
現在Spec
↓
Backend Split API
↓
成功:
  Undo historyへ旧Spec保存
  Canonical specへ置換

失敗:
  Spec変更なし
  UI warning
```

としてください。

API Route方式が現在のComfyUIで不適切な場合のみ、JS側に同等generic splitterを実装して構いません。その場合はPython/JSで同一fixtureを通し、Canonical結果が一致するParity Testを必須にしてください。二重実装は第二選択肢です。

---

# 6. Critical Finding 2 — Frontend DragがTransactionalになっていない

現在Frontendは `node.lastValidSpec` を保存しています。

しかしdrag中は:

```javascript
targetV.x = ...
targetV.y = ...
specWidget.value = ...
```

と直接commitしています。mouse upでもvalidate/rollbackせず `lastValidSpec = null` にしています。

したがって報告書の「candidate moveに対してtopology validation / invalidならrollback」は現Frontendコードでは成立していません。

---

# 7. Drag Transaction設計

推奨:

```text
Committed Spec
+
Preview Candidate Spec
```

を分離してください。

drag start:

```text
committedSpec = deep copy
previewSpec = deep copy
```

drag move:

```text
previewSpecのみ変更
↓
lightweight local validation
↓
Canvas preview
```

この段階ではCanonical `specWidget.value` を壊さないことを推奨します。

pointer/mouse up:

```text
preview candidate
↓
Backend Validate API
↓
VALID:
  specWidgetへcommit
  Undo history追加

INVALID:
  preview破棄
  committedSpecへ戻る
```

としてください。

毎mousemoveでBackend HTTP validationする必要はありません。最大6 Panelなので、Frontendでは最低限 frame bounds / minimum edge / affected panel area / convexity / self-intersection 程度のfast checkを行って構いません。最終確定はBackend validatorを通してください。

---

# 8. Backend Validatorを最終正本とする

Frontend fast validatorはUX用、Backendは契約上の正本です。Frontendチェックだけでデータを信用しないでください。

---

# 9. Critical Finding 3 — Frame Validation不足

`panel_layout_spec.py` のframeは現在float化・roundされていますが、最低限以下の厳格検証を追加してください。

```text
x/y/w/h numeric
bool reject
finite
w > 0
h > 0
x >= 0
y >= 0
x + w <= 1
y + h <= 1
```

不正frameを黙ってclampしないこと。Legacy `frame missing` のdefault補完は維持可です。

---

# 10. VertexはFrame内を保証

Panel Layoutの契約では全PanelがLayout Frameを分割します。

```text
frame.x <= vertex.x <= frame.x + frame.w
frame.y <= vertex.y <= frame.y + frame.h
```

を保証してください。

保存済み契約の厳格Validatorでは invalid → ValueError を推奨します。UI操作段階でclampしてください。Legacy migrationが必要なら別関数にしてください。

---

# 11. Duplicate Coordinate IDs

Planar Shared-Vertex Meshでは、別IDなのに同じ座標を持つ頂点は危険です。

例:

```text
v10 = (0.5, 0.5)
v11 = (0.5, 0.5)
```

これではshared edge incidence / T-Junction / drag propagationの意味が崩れます。

epsilon以内のduplicate coordinatesをrejectすることを推奨します。

---

# 12. Orphan Vertex

どのPanelからも参照されないvertexを検出してください。

推奨方針:

```text
Validatorではreject
Split canonicalizerでは不要vertexをprune
```

---

# 13. Edge Incidenceを厳格化

現在は incidence > 2 のみrejectです。

さらにedgeを分類してください。

Outer Edge:

```text
incidence = 1
かつ
Layout Frame boundary上
```

Internal Edge:

```text
incidence = 2
```

以下をreject:

```text
incidence = 1
かつ
frame boundaryではない
```

これは内部gapの構造的証拠です。

Frame boundary判定はedge両端が同じframe side上にあるかをepsilon付きで確認してください。

---

# 14. Pairwise Panel Overlap Exact Check

現在のgap/overlap raster diagnosticは90x90 gridで、診断には有用ですが、1%以下の小さな不正を契約上許し得ます。

Planar Subdivision validatorではpairwise polygon interior overlapを幾何的に検査してください。

V1はconvex polygon限定なので、edge proper intersection + one polygon vertex strictly inside other polygon等で構いません。

Raster diagnosticはdebug summaryとして残し、契約の唯一のPASS判定にはしないでください。

---

# 15. Area Conservation tolerance

現在 `eps = 0.005` はFrame面積0.81に対して比較的大きいです。

Topology invariantとしてより厳しくしてください。

候補:

```text
1e-4 〜 1e-3
```

程度をfixtureとsplit roundingで評価し、採用理由を報告してください。

---

# 16. Self-Intersectionをより堅牢に

現在の `segments_intersect()` はproper crossing中心です。

以下も検討してください。

```text
non-adjacent edge touch
collinear overlap
same-coordinate different IDs
```

Duplicate coordinate rejectionとzero edge検査を組み合わせても構いません。

---

# 17. Production UIとProduction Algorithmを同じテスト対象へ

今回の最重要改善です。

以下を別々にPASSさせるだけでは不十分です。

```text
Python generic_split_panel PASS
JS button exists
```

必要なのは:

```text
実際にUI Splitを押した結果
=
generic_split_panel canonical result
```

です。

---

# 18. Frontend / Backend Parity Test

新規:

```text
scripts/test_panel_layout_frontend_backend_parity.py
```

または適切なテスト方式を作成してください。

最低限fixture:

```text
1_full H/V///
3_basic selected p1
3_dynamic slanted panel
shared-vertex moved layout
5-panel → 6-panel
```

Frontend操作結果とBackend canonical outputを比較してください。

---

# 19. Browser Automation

既存環境にPlaywright等が既に存在する場合のみ利用してください。新しい大型ブラウザ依存を追加する必要はありません。

可能なら:

```text
Workflow14 load
Panel select
Split button
vertex drag
Undo
Redo
Save
Reload
```

を自動化。

不可能なら:

```text
BROWSER AUTOMATION:
NOT AVAILABLE
```

と正直に記録してください。

ただしBackend API + Frontend route integrationのコードテストは必須です。

---

# 20. Drag Testを修正

現在の `test_panel_layout_drag_validation.py` は、Python側でinvalid specを作り、validatorを呼び、テストコード自身がrollbackしています。

これはFrontend Transactionのテストではありません。

名称・説明を修正するか、本当にFrontend commit/rollback pathを検証してください。

---

# 21. Split Regression Matrix不足を補完

最低限追加:

```text
3_dynamic → Horizontal
3_dynamic → Vertical
3_dynamic → /
3_dynamic → \

shared vertex deformation後 → H/V
5-vertex panel → split
```

---

# 22. Workflow 15

Workflow 15の基本構造:

```text
Core Semantic Region
+
Panel Layout image
+
ControlNetApplyAdvanced
```

は妥当です。

今回は大規模な生成再評価をしなくて構いません。

Regressionとして:

```text
load
no touch
Queue
image
CN OFF
CN 0.60
```

程度を確認してください。

Workflow 15 Zero-Touch PASSは「Default Panel Layoutが生成へ入る」ことの証明であり、UIでSplitしたPanel LayoutやUI dragの安全性を証明するものではありません。報告書で区別してください。

---

# 23. Report Corrections

Phase 3C.1.1報告書の:

```text
Frontend candidate move topology validation
invalid rollback
T-Junction-free UI Split
```

等は、現Review Targetではコード上成立していません。

修正履歴を残してください。

例:

```text
Corrected in Phase 3C.1.2:
Backend topology was hardened in 3C.1.1,
but frontend editor still used a separate legacy split path
and did not perform actual transactional rollback.
```

---

# 24. Semantic Region側

今回変更不要です。

Regressionのみ:

```text
Workflow11
Workflow12
Semantic Overlap
A/B Move/Resize/Create
```

を維持してください。

---

# 25. .pyc cleanup

Phase 3C.1.1で `.gitignore` 対応は入っています。

実際にtracked `.pyc` が残っていないことを確認してください。

---

# 26. 新規報告書

```text
PHASE3C_1_2_FRONTEND_BACKEND_GEOMETRY_PARITY_REPORT.md
```

最低限:

```text
1. Review Findings
2. Backend vs Frontend Split Gap
3. Backend SSOT Strategy
4. Split API / Alternative Architecture
5. Frontend Split Integration
6. Drag Transaction Design
7. Drag Commit/Rollback
8. Frame Validation
9. Vertex Frame Bounds
10. Duplicate Coordinate IDs
11. Orphan Vertices
12. Edge Incidence Classification
13. Pairwise Overlap Check
14. Area Tolerance
15. Raster Diagnostic Role
16. Split Parity Tests
17. Drag Tests
18. Browser Automation / Manual Status
19. Workflow14 Regression
20. Workflow15 Regression
21. Report Corrections
22. Phase3D Readiness
23. Known Issues
24. Gemini独自判断
```

---

# 27. Tests

最低限:

```text
scripts/test_panel_layout_frontend_backend_parity.py
scripts/test_panel_layout_topology.py
scripts/test_panel_layout_split_operations.py
scripts/test_panel_layout_drag_validation.py
```

必要なら:

```text
scripts/test_panel_layout_api_routes.py
```

を追加してください。

---

# 28. Acceptance Criteria — Frontend Split

```text
[ ] UI Horizontal Split uses production geometry path
[ ] UI Vertical Split uses production geometry path
[ ] UI / Split uses production geometry path
[ ] UI \ Split uses production geometry path
[ ] UI result canonical spec equals Backend result
[ ] T-Junction propagation maintained
[ ] 5/6 panel repeated split works
[ ] 7th refuses safely
```

---

# 29. Acceptance Criteria — Drag

```text
[ ] invalid candidate never becomes committed spec
[ ] valid drag commits
[ ] invalid drag rolls back
[ ] Undo gets pre-drag committed state
[ ] Redo works
[ ] outer boundary constraint
[ ] interior move topology-safe
```

---

# 30. Acceptance Criteria — Contract

```text
[ ] strict finite frame validation
[ ] frame normalized bounds
[ ] all vertices inside frame
[ ] duplicate-coordinate IDs handled
[ ] orphan vertices handled
[ ] incidence=1 only on frame boundary
[ ] internal edge incidence=2
[ ] exact pairwise overlap rejection
[ ] self-intersection robust
[ ] area tolerance tightened
[ ] raster gap/overlap retained as diagnostic
```

---

# 31. Acceptance Criteria — Workflow

```text
[ ] Workflow14 Zero-Touch PASS
[ ] Workflow14 edited split survives Save/Reload
[ ] Workflow15 Zero-Touch PASS
[ ] Workflow15 CN OFF generation
[ ] Workflow15 CN ON generation
[ ] Existing 09〜13 non-destructive
```

---

# 32. Phase 3D Gate

以下が揃って初めて:

```text
Phase 3D — Variable N-Region Manga Integration
```

へ進めてください。

```text
BACKEND TOPOLOGY:
PASS

FRONTEND/BACKEND SPLIT PARITY:
PASS

TRANSACTIONAL DRAG:
PASS

PANEL LAYOUT CONTRACT:
PASS

WORKFLOW14:
PASS

WORKFLOW15:
PASS
```

---

# 33. Phase 3D予定

次Phaseで初めて:

```text
通常3〜5 Panel
最大6 capacity
+
Panel Prompt
+
Panel内Character Semantic Region
+
Local Region
+
Panel Layout ControlNet
```

を統合します。

今回まだ実装しないでください。

---

# 34. ユーザー確認

今回もユーザーへ細かい実装確認を依頼しなくて構いません。

Gemini自己テストとGPTコードレビューを優先。

ユーザーへ次に見せる候補は:

```text
N-Region Regional Prompt
+
Character Region
+
Panel Layout ControlNet
```

が同時に動くPhase 3Dの集約Workflowで構いません。

---

# 35. 終了判定

報告書末尾:

```text
BACKEND TOPOLOGY:
PASS / HOLD

FRONTEND/BACKEND SPLIT PARITY:
PASS / HOLD

TRANSACTIONAL DRAG:
PASS / HOLD

PANEL LAYOUT CONTRACT:
PASS / HOLD

CONTROLNET FUSION REGRESSION:
PASS / HOLD

PHASE 3D READINESS:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 36. GITHUB.TXT 二段Commit

まず:

```text
Commit A
Phase 3C.1.2 Frontend Backend Geometry Parity
```

としてimplementation / routes / frontend integration / tests / reportsをcommit。

そのSHAを取得。

Navigation commitで:

```text
Review Target Commit SHA: A
```

へ更新。

最終回答のLatest GITHUB.TXT Rawは:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

を使用してください。

---

# 37. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3C_1_2_FRONTEND_BACKEND_GEOMETRY_PARITY_REPORT Raw:

Panel Layout Spec Raw:
Panel Layout Topology Raw:
Panel Layout Split Raw:
Panel Layout Editor JS Raw:
Panel Layout API Raw: (if created)

Frontend/Backend Parity Test Raw:
Topology Test Raw:
Split Test Raw:
Drag Test Raw:
API Test Raw: (if created)

Workflow 14 Raw:
Workflow 15 Raw:

BACKEND TOPOLOGY:
FRONTEND/BACKEND SPLIT PARITY:
TRANSACTIONAL DRAG:
PANEL LAYOUT CONTRACT:
CONTROLNET FUSION REGRESSION:
PHASE 3D READINESS:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3C.1.1で重要なBackend基盤は作られました。

しかし、

```text
安全なPython Split
```

と、

```text
ユーザーが押すFrontend Split Button
```

が別アルゴリズムのままでは、制作ツールとしてはまだ地固めが終わっていません。

また `lastValidSpec` という変数があるだけではTransactional Dragではありません。

今回、

```text
Frontend操作
↓
Backend canonical geometry
↓
厳格validator
↓
安全なSpec
```

まで一本化してください。

ここがPASSした後はPanel Layoutについて大きく立ち止まる必要はありません。

次のPhase 3Dでは、

```text
通常3〜5コマ
最大6 capacity
+
各コマPrompt
+
コマ内Character Region
+
Panel Layout ControlNet
```

の本体統合へ進んでください。
