# ComfyUI Portable Phase 3C.1 — Semantic Region Hardening & Panel Layout Guide Foundation 指示書

## 0. 今回の位置づけ

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
673d7e841ee6d7b4ad503c832bd690f4eb14ea61
```

Phase 3Cでは `TWO_REGION_SPEC`、Two Region Oracle、Core/Impact比較、ControlNet Layout Auxまで進みました。

ただし今回の外部レビューでは、実装と報告書の間にいくつか差異があります。また今後は、Regional Prompt / Couple用の「意味領域」と、ControlNetへ渡す漫画コマ割りを明確に分離します。

今回のPhase 3C.1では次の3点を優先してください。

```text
A. Semantic Region Oracleを本当に操作可能な状態へ固める
B. Semantic Regionは「重なり可能」を基本思想にする
C. コマ割り専用の独立Panel Layout Guideを設計・実装する
```

まだ最大6コマの本番Regional生成へ進まないでください。

---

## 1. 最重要設計分離

今後、以下の2つを別物として扱ってください。

### A. Semantic Region

用途:

```text
Regional Prompt
Attention Couple
Character Region
Local Region
将来のRegional LoRA
```

特徴:

```text
重なってよい
隙間があってよい
ページ全体を覆わなくてよい
境界は曖昧でもよい
```

目的:

```text
「この意味をこのあたりへ強く効かせる」
```

ことです。

### B. Panel Layout

用途:

```text
漫画コマ割り
ControlNet Layout Guide
構図補助
```

特徴:

```text
基本的に重ならない
ページを分割する
共有境界を持つ
黒線 / 白地
Promptを持たない
```

目的:

```text
「ページをどういうコマ構造にするか」
```

をControlNetへ渡すことです。

Semantic RegionとPanel Layoutを1対1対応させないでください。1つのコマの中にCharacter A/B RegionやLocal Regionが複数存在できます。

---

## 2. Phase 3Cのレビュー修正

### 2.1 Critical: Two Region Editorの実操作を実装

Phase 3C報告書では矩形のドラッグ作成・移動・Resize対応とされていますが、Review Target `673d7e84...` の `web/js/two_region_editor.js` ではCanvas描画とPreset処理はあるものの、Pointer/Mouse操作処理が確認できません。

最低限:

```text
Region A選択
Region B選択
矩形内部drag → Move
右下handle drag → Resize
空白drag → 選択Regionを新位置へ作成
Delete / Disable
```

を実装してください。

4隅Resizeは今回必須ではありません。表示Handleと実操作を一致させてください。

可能なら `pointerdown / pointermove / pointerup / pointercancel` と pointer capture を使用。ノード削除・Workflow再ロード時にlistenerをcleanupしてください。

---

## 3. Editor State Test

新規:

```text
scripts/test_two_region_editor_state.py
```

最低限:

```text
select A
select B
move A
resize A
move B
resize B
disable A
restore A
Horizontal preset
Vertical preset
Overlap preset
One Region preset
save/reload exact
```

を検証してください。

可能な範囲で実ブラウザでもA/B move, resize, save/reloadを確認。未確認なら `MANUAL BROWSER INTERACTION PENDING` と明記してください。

---

## 4. TWO_REGION_SPECを本当に2領域固定へ

現在Validatorは `regions >= 1` と任意IDを許しますが、Core ConditionerはA/Bしか処理しません。

Phase 3C Oracleでは:

```text
regionsは必ず2 entry
IDは必ず A / B
保存順は A, B
```

としてください。

片方を消す場合はentry削除ではなく:

```text
enabled = false
```

です。

---

## 5. Geometry boundary bug

現在のclampでは `x=1.0` のとき `w=0.001` となり `x+w > 1` になる可能性があります。

既存REGION_SPECで使用している共通の:

```text
MIN_REGION_SIZE
normalize_rect()
```

を再利用できるなら再利用してください。

必ず:

```text
x + w <= 1
y + h <= 1
```

を保証してください。

---

## 6. Schema Errorはfail-closed

Two Region Editor backendの:

```text
parse / validation error
→ warning
→ default spec
```

を見直してください。

推奨:

```text
JSON Syntax Error
→ fallback可 + warning

Valid JSONだがSchema Error
→ ValueError
```

制作データを黙って初期化しないこと。

---

## 7. Promptを空文字へ戻せること

現在 `if prompt_A != ""` のため、既存Promptを空にできません。

空文字も有効な値としてA/B両方へ同期してください。

---

## 8. Semantic RegionはOverlapを基本思想に変更

Couple / Regional Prompter用の領域は、重なることを基本とします。

理由:

```text
人物同士の接触
演技
構図上の共有領域
曖昧な責任範囲
```

を許すためです。

初期Preset / ResetはHorizontal Splitではなく `Semantic Overlap` を推奨。

例:

```text
A: x=.05 y=.10 w=.62 h=.80
B: x=.33 y=.10 w=.62 h=.80
```

25〜40%程度の重なりで構いません。

Horizontal / Verticalは比較用Presetとして残します。

```text
Semantic Overlap
Separate Left / Right
Separate Top / Bottom
A Only
B Only
```

のように意味が分かる名前へしてください。

---

## 9. Locality MetricをSpec駆動へ

現在の `test_two_region_locality_metrics.py` はA/B座標が固定されています。

TWO_REGION_SPECからMaskを生成する方式へ変更してください。

Overlapでは:

```text
A-only
B-only
A∩B
Outside
```

を別々に集計。

Pixel differenceはSemantic correctnessではなく `Spatial change locality metric` として扱ってください。

`>=1.5 → PASS` は絶対的品質保証ではなくDiagnosticに留め、raw値を保存してください。

---

## 10. Phase 3C報告書の表現を修正

少数seed / 少数sceneのOracleに対して、

```text
属性漏れは一切発生せず
完全に実証
極めて高品位
圧倒的に有利
```

等は強すぎます。

以下程度へ修正してください。

```text
今回の固定Seedサンプルでは目立つ属性漏れを確認しなかった
Core方式は有望
現段階ではCoreをPrimary Candidateとする
```

Backend表記:

```text
PRIMARY REGIONAL BACKEND:
CORE MASKED CONDITIONING (PROVISIONAL)

IMPACT:
REFERENCE / FALLBACK ORACLE
```

6-KOMAについては:

```text
N-REGION BACKEND READINESS: PROMISING
FULL MULTI-PANEL INTEGRATION: HOLD
```

Character Regionも:

```text
CHARACTER-REGION BACKEND READINESS: PROMISING
```

程度へ修正してください。

---

# 11. 新設: Manga Panel Layout Editor

Semantic Regionとは独立した漫画コマ割り専用Editorを作ってください。

名称候補:

```text
Tegaki Manga Panel Layout Editor
```

指定Canvas width/heightの白紙ページを表示し、それをSlice / Splitしてコマへ分割します。

ControlNet用出力:

```text
白地
黒いコマ境界線
番号なし
Promptなし
```

です。

---

## 12. 可変コマ数

本番想定:

```text
通常3〜5コマ
最大6コマ
```

データ契約上は1〜6を許可して構いません。

6はCapacityであり、常時6コマを出す意味ではありません。

存在するコマだけUIへ表示してください。

---

## 13. PANEL_LAYOUT_SPEC v1

新規:

```text
PANEL_LAYOUT_SPEC v1
```

候補:

```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "vertices": [],
  "panels": [],
  "metadata": {}
}
```

Panel LayoutはPrompt/Character/LoRAを持たない純粋な幾何契約とします。

---

## 14. Shared Vertex Mesh

各Panelが独立x/y/w/hを持つのではなく、

```text
shared vertices
shared edges
panel polygons
```

方式を推奨します。

例:

```json
{
  "vertices": [
    {"id": "v1", "x": 0.0, "y": 0.0},
    {"id": "v2", "x": 1.0, "y": 0.0}
  ],
  "panels": [
    {
      "id": "p1",
      "vertex_ids": ["v1", "v2", "v5", "v4"]
    }
  ]
}
```

Editor内ではDebug用IDを表示してもよいですが、ControlNet用画像には描かないでください。

---

## 15. 初期状態とSplit

初期はページ全体1 Panel。

選択中Panelへ:

```text
Horizontal Split
Vertical Split
Diagonal /
Diagonal ```

を適用。

Panel Countが1増える。最大6。

水平/垂直には `split_ratio`、default 0.5。

Diagonalは最初はcorner-to-cornerで構いません。

---

## 16. Shared Edge / Shared Vertex Drag

Splitで生成した境界は2 Panelが同じvertex/edgeを共有。

共有vertexをdragすると、そのvertexを参照する全Panelが同時に変形すること。

これにより:

```text
隙間
重なり
```

を発生させずコマ変形します。

外周vertexはページ外へ出ないよう制約。

内部vertexはCanvas内で移動可能。

---

## 17. Polygon Validation

最低限:

```text
self-intersectionなし
area > minimum
winding統一
canvas内
```

不正dragは直前のvalid位置へ戻す方式で構いません。

---

## 18. 実装優先順位

V1:

```text
Horizontal split
Vertical split
Diagonal corner split
Shared vertex drag
```

Later:

```text
任意edge endpoint
任意quadrilateral warp
複雑なpolygon split
```

最初から完全自由変形を狙いすぎないでください。

---

## 19. Undo / Redo

Panel Layout Editorでは重要です。

最低限:

```text
Split
Vertex Move
Reset
```

をUndo / Redo可能にしてください。

Merge/Deleteが複雑なら、V1では `Undo Last Split` で代用して構いません。

---

## 20. Presets

補助Preset候補:

```text
3 Panels Basic
3 Panels Dynamic
4 Panels Grid-ish
4 Panels Manga
5 Panels Manga
```

自由Splitを本体としてください。

Defaultは3 Panels程度を推奨します。

---

## 21. 出力

最低限:

```text
layout_image
panel_layout_spec
debug_json
```

`layout_image` は:

```text
White background
Black lines
No panel numbers
No labels
No colors
```

line_widthは1〜16px程度で調整可能。

---

## 22. Direct IMAGE output

Screenshot運用も可能ですが、既にComfyUI custom nodeからIMAGE出力可能なので最初から:

```text
Editor
↓
IMAGE
```

を実装してください。

普通の `PreviewImage / SaveImage / ControlNet` へ接続できること。

---

## 23. Workflow 14

新規:

```text
14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json
```

区分:

```text
DEVELOPMENT / PANEL LAYOUT TOOL
```

構成:

```text
Panel Layout Editor
↓
PreviewImage
↓
SaveImage optional
```

生成モデル不要。

Loadすると3-panel default layoutが表示されること。

---

## 24. Browser Interaction Test

最低限:

```text
3-panel preset
split horizontal
split vertical
diagonal split
shared vertex drag
undo
redo
save workflow
reload
layout一致
```

---

## 25. Tests

新規:

```text
scripts/test_panel_layout_spec.py
scripts/test_panel_layout_state.py
scripts/test_panel_layout_renderer.py
```

Spec Test:

```text
1〜6 panels
unique vertex id
unique panel id
shared vertex reference
polygon area
self-intersection
canvas bounds
save/reload
```

Renderer Test:

```text
white background
black line only
no text
correct dimensions
```

---

## 26. ControlNet統合

Workflow 14でPanel Layout Editorが安定した後に:

```text
layout_image
↓
ControlNet
```

を試します。

既存 `TegakiTwoRegionLayoutGuide` は:

```text
Oracle / legacy experiment
```

とし、

```text
PanelLayoutEditor = 漫画コマ割り正本
```

へ分離してください。

低リスクなら新規:

```text
15_MANGA_PANEL_LAYOUT_CONTROLNET_TEST.json
```

まで進めても構いません。

---

## 27. 最終的な組み合わせ

将来的には:

```text
Panel Layout ControlNet
+
Semantic Regions
```

を同時利用します。

例:

```text
ControlNet:
ページを3コマへ分割

Semantic Region:
人物AとBの領域は同じコマ内で重なる
```

これが狙いです。

---

## 28. 今回はN-Region / Character統合しない

以下は次Phaseです。

```text
3〜5 Active Panel Regional Prompt
最大6 capacity
Character Regions
CAST UI
```

今回は:

```text
Two Region Oracleを正しくする
Panel Layout Guideを独立完成させる
```

ことに集中してください。

---

## 29. 将来の可変UI方針

本番では:

```text
通常3〜5
最大6
```

です。

データ上は最大6 capacity。

UI上は:

```text
Active Regionだけ表示
```

を目標にします。

ComfyUI Node段階ではcustom Canvas + JSON state中心で構いません。

最終Shell / Wrapperでは不要Region / Character設定を非表示にできるUIを目標としてください。

---

## 30. 報告書

新規:

```text
PHASE3C_1_SEMANTIC_REGION_AND_PANEL_LAYOUT_REPORT.md
```

最低限:

```text
1. Phase 3C Review Fixes
2. Two Region Editor Interaction
3. TWO_REGION_SPEC strict contract
4. Geometry fix
5. Prompt clearing
6. Semantic overlap default
7. Locality metric correction
8. Core provisional backend status
9. Semantic Region vs Panel Layout separation
10. PANEL_LAYOUT_SPEC
11. Shared vertex mesh
12. Split operations
13. Diagonal split
14. Shared vertex drag
15. Polygon validation
16. Layout renderer
17. Workflow 14
18. Browser interaction tests
19. Existing 09〜13 regression
20. Known issues
21. Next phase
22. Gemini独自判断
```

---

## 31. Acceptance Criteria — Semantic Region

```text
[ ] TWO_REGION_SPEC exactly A/B
[ ] enabled=falseで片領域OFF
[ ] x+w/y+h boundary safe
[ ] schema error fail-closed
[ ] Promptを空へ変更可能
[ ] Two Region EditorでA Move
[ ] B Move
[ ] A Resize
[ ] B Resize
[ ] Disable/Restore
[ ] Overlapがdefault
[ ] Separate Horizontal preset
[ ] Separate Vertical preset
[ ] save/reload exact
[ ] browser interaction evidence
```

---

## 32. Acceptance Criteria — Metrics / Report

```text
[ ] Locality mask is derived from TWO_REGION_SPEC
[ ] Overlap metric
[ ] Pixel localityとSemantic correctnessを区別
[ ] Phase3C報告書の過剰表現修正
[ ] Core = provisional primary
```

---

## 33. Acceptance Criteria — Panel Layout

```text
[ ] PANEL_LAYOUT_SPEC v1
[ ] Canvas aspect ratio
[ ] panel count 1〜6
[ ] default ~3 panels
[ ] Horizontal split
[ ] Vertical split
[ ] Diagonal split
[ ] shared vertices
[ ] shared vertex drag updates adjacent panels
[ ] no gaps/overlap in layout topology
[ ] invalid polygon reject
[ ] Undo/Redo
[ ] white/black layout image
[ ] no number/text in output
[ ] direct IMAGE output
[ ] Workflow 14
[ ] Zero-Touch / Preview PASS
```

---

## 34. Existing Workflow Regression

最低限:

```text
09
10
11
12
13
```

を壊さないこと。

11 / 12はZero-Touch生成を再確認してください。

---

## 35. 次Phase Gate

Phase 3C.1完了後:

```text
SEMANTIC TWO-REGION UI:
PASS / HOLD

PANEL LAYOUT GUIDE:
PASS / HOLD

CORE REGIONAL BACKEND:
PROVISIONAL PRIMARY / REOPEN COMPARISON
```

を記載。

PASSなら次Phase候補:

```text
Phase 3D
Variable N-Region Manga Integration
```

目標:

```text
通常3〜5
最大6
+
Character Region
```

ただしPanel Layoutは独立したControlNet補助として維持します。

---

## 36. GITHUB.TXT二段Commit

まず:

```text
Commit A
Phase 3C.1 Semantic Region Hardening & Panel Layout Guide
```

としてcode / tests / workflow 14 / reportをcommit。

そのSHAを取得し:

```text
Review Target Commit SHA: A
```

をGITHUB.TXTへ記載。

GITHUB.TXTのみ別commitしてください。

---

## 37. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3C_1_SEMANTIC_REGION_AND_PANEL_LAYOUT_REPORT Raw:

Two Region Spec Raw:
Two Region Editor Raw:
Two Region Editor JS Raw:
Locality Metric Raw:

Panel Layout Spec Raw:
Panel Layout Editor Raw:
Panel Layout Editor JS Raw:
Panel Layout Renderer Raw:

Workflow 11 Raw:
Workflow 12 Raw:
Workflow 14 Raw:

Two Region Editor State Test Raw:
Panel Layout Spec Test Raw:
Panel Layout State Test Raw:
Panel Layout Renderer Test Raw:

SEMANTIC TWO-REGION UI:
PASS / HOLD

PANEL LAYOUT GUIDE:
PASS / HOLD

CORE REGIONAL BACKEND:
PROVISIONAL PRIMARY / REOPEN COMPARISON

NEXT RECOMMENDED PHASE:
```

---

# 最終方針

今後は `Semantic Region` と `Panel Layout` を混同しないでください。

Semantic Regionは:

```text
重なってよい
曖昧でよい
意味を場所へ寄せる
```

ものです。

Panel Layoutは:

```text
重ならない
共有境界
ページを切り分ける
ControlNetへ渡す
```

ものです。

この二つを独立させることで、

```text
Panel Layout ControlNetで漫画のコマ構造を固定しつつ、
同一コマ内では人物A/BのSemantic Regionを重ねて
演技や関係性を保つ
```

構造を最終的に実現します。

また「6コマ」は常時6コマを使う意味ではありません。

本番想定は:

```text
通常3〜5コマ
最大6コマ
可変
```

です。

最終Shell / Wrapperでは、不使用コマや不使用Character設定を非表示にできるUIを目標としてください。
