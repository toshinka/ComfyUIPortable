# ComfyUI Portable — M3A.1 / Phase 3M-3A.1
# Frame Runtime Truth, Gutter Semantics & Live Browser Closure
## — Visual Frameを「実際に漫画として使える枠」にし、UI→保存→Overlayの因果を閉じる —
## Antigravity2 / Gemini 3.8 STANDARD/HIGH 向け Bounded Correction Card

## 推奨モデル

```text
Gemini 3.8 STANDARD / HIGH
```

LOWは使わない。

今回の対象は画像研究ではなく、

```text
Live ComfyUI widget serialization
Visual Frame persistent geometry
deterministic raster semantics
Save / Reload
UI → Authoring Document → FrameOverlay
```

の統合境界である。

---

# 0. 最初に読むもの

順序厳守。

```text
ComfyUIPortable/GITHUB.TXT
```

次に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

本Card発行時の固定Review Target:

```text
45ccd226b7a853e6279261a34bbdcdf5e98a1a32
```

M3A Navigation Commit:

```text
858dd7f57cfe31bbcfbc1b5a3d9b4763292acae9
```

moving mainをレビュー対象にしない。

---

# 1. Web GPT Review Verdict

M3A Architecture:

```text
ACCEPT
```

成立:

```text
page.visual_frames SSOT
3-layer UI skeleton
Frame/Scene independence
Frame/Character independence
0-frame regression
deterministic FrameOverlay node
canonical workflow integration
```

しかしOwner screenshotとcode auditから、
M3Bへ進む前に閉じるべきruntime/product不整合がある。

判定:

```text
M3A Architecture: ACCEPT
M3A Browser Frame Path: HOLD
M3B: HOLD
Next: M3A.1
```

---

# 2. Owner Screenshot — 何が確認できたか

Owner実ブラウザ画面で:

```text
Minimum-Hand Custom DOM: visible
Scene Regions layer: visible
Visual Panel Frames tab: visible
Character Staging tab: visible
Default Queue: generated image exists
FrameOverlay node: canonical workflowに存在
```

は確認できた。

---

# 3. Owner Screenshot — まだ確認できていないもの

スクリーンショットでは:

```text
Scenes: 2
Frames: 0
active layer = Scene Regions
```

。

したがってこの画像は:

```text
Visual Frame Add
Frame drag
Frame resize
actual black frame output
white gutter
Frame Save/Reload
```

のBrowser acceptanceにはならない。

M3A ReportのOwner Pendingは正しい。

---

# 4. Finding A — Live FrameOverlay widget値の不一致
# BLOCKER

Owner screenshotのFrameOverlay nodeでは、
画面上:

```text
line_thickness = 3
page_index = 1
```

に見える。

一方、固定Review TargetのCanonical Workflow JSONは:

```json
"widgets_values": [4, 0, ""]
```

であり、実装意図も:

```text
line_thickness = 4
page_index = 0
```

。

まず実ブラウザ実値を確認し、差が本当に存在するかを閉じる。

---

# 5. page_index = 1 が本当なら重大

現在Authoring Documentは1 page。

FrameOverlay:

```python
if 0 <= page_index < len(pages):
```

なので、

```text
page_index = 1
pages = [page_0 only]
```

ならVisual Framesを一切読まない。

その結果:

```text
FrameをUIで追加しても
Overlayは0 frames扱い
```

になり得る。

しかも現在FrameOverlayはこの状態をfailせず、
pass-through PASSとして扱える。

---

# 6. FrameOverlay serialization audit
# REQUIRED

Live ComfyUIで以下を確認。

```text
1. Workflow load直後
2. FrameOverlay visible widget values
3. Save Workflow
4. saved JSON widgets_values
5. Reload
6. values after reload
```

。

Headless JSONだけでPASSにしない。

---

# 7. page_index Product Policy
# 推奨

現Mainlineはsingle-page authoring workflow。

M3A.1ではProduct userに:

```text
page_index
```

を触らせる必要はない。

第一候補:

```text
FrameOverlayはAuthoring Documentのfirst/current pageを明確に使う
page_index native widgetをCanonical Product Workflowから除去
```

。

multi-page routingは後段。

---

# 8. page_indexを残す場合

残すなら:

```text
internal hidden
default 0
stable serialization
out-of-range fail-closed
```

を必須とする。

Owner画面に1が出る状態は禁止。

---

# 9. Finding B — FrameOverlay fail-open
# BLOCKER

現在:

```python
try:
    doc = json.loads(...)
except:
    warning
```

後に:

```text
visual_frames=[]
status=PASS
mode=pass_through
```

へ進み得る。

同様にpage_index out-of-rangeでも
silent 0-frame pass-through。

これはM0以降のfail-closed方針と一致しない。

---

# 10. FrameOverlay validation

Canonical pathでは:

```text
authoring_document_json
→ parse
→ validate_document
→ resolve page
→ visual_frames
```

。

以下は明示ERROR:

```text
invalid JSON
unknown schema/version
invalid page index
invalid frame geometry
duplicate frame_id
```

。

---

# 11. 0 framesとInvalidを分ける

合法:

```text
valid document
valid page
visual_frames=[]
→ pass-through PASS
```

。

違法:

```text
document parse failure
page missing
page index out of range
```

を0 frames扱いしない。

---

# 12. Finding C — per-frame Line Thicknessが最終画像に効かない
# BLOCKER

Frontend Frame Inspectorは:

```text
curFrame.border_thickness
```

を編集。

Canvas Previewも:

```text
fr.border_thickness
```

を使う。

しかし`render_deterministic_frame_overlay()`は
全frameへnode input:

```text
line_thickness
```

を一律適用。

つまり:

```text
UIでFrame 1 thicknessを変更
→ Editor previewは変化
→ Final Outputは変化しない
```

。

Product semanticsとして不一致。

---

# 13. Thickness Fix

推奨:

各frame:

```python
effective_thickness =
    frame.border_thickness
    if valid
    else global_fallback
```

。

Global `line_thickness`はInternal fallback。

Primary user inputはFrame Inspectorの値。

---

# 14. Thickness E2E Oracle

2 frames:

```text
Frame A = 2px
Frame B = 8px
```

。

Queue。

最終outputでpixel thickness差が確認できること。

---

# 15. border_color

現在Document fieldはあるが
FrameOverlayはblack固定。

M3A Productは黒枠でよい。

二択:

```text
A. border_colorを実際にhonor
B. M3A v1はblack-onlyと明示し、UI/Reportからcolor fidelity claimを外す
```

。

未配線fieldをProduct capabilityとして主張しない。

---

# 16. Finding D — 「Gutter」が未実装
# BLOCKER

`authoring_visual_frame_bridge.py`には:

```text
gutter_mask_outside
bg_margin_color
```

引数があるが、
実際の`_render_single_pil_overlay()`は
黒いrectangle outlineを描くだけ。

Frame外の画像は白くならない。

---

# 17. Actual Manga Frame v1 semantics

M3A.1でDeterministic Frameを:

```text
White Page
+
source image visible inside frame interiors
+
black frame borders
+
outside frame union = white gutter / margin
```

とする。

これが「実際の漫画コマ」のv1。

---

# 18. 0 Frame semanticsは維持

```text
visual_frames=[]
```

なら従来画像をpixel-identical pass-through。

勝手に白page化しない。

---

# 19. Frameが存在する時だけpanel cutout

1+ visual frame:

```text
start from white canvas
copy source image inside each frame rectangle
draw black borders
```

。

これによりScene生成画像の
frame外領域はdeterministically隠れる。

---

# 20. No Crop / No Rescale

M3A.1では各frame内部へ画像を
拡大縮小して貼り直さない。

同じpage coordinatesのsource imageを
frame maskで見せるだけ。

---

# 21. Overlap policy

Product推奨はnon-overlap。

M3A.1ではoverlap frameに:

```text
warning
```

。

Raster semanticsはdeterministicに
union-of-frame-interiorsでよい。

複雑なz-order cropは後段。

---

# 22. Gutter pixel tests

既知2-frame geometryで:

```text
inside Frame A:
source pixel preserved

inside Frame B:
source pixel preserved

between frames:
pure white

outside outer margins:
pure white

border:
pure black
```

をassert。

---

# 23. Finding E — `area` / `shape` dual-key drift
# BLOCKER

Python consumers:

```python
f.get("shape") or f.get("area")
```

。

Frontend:

```javascript
fr.area || fr.shape
```

。

優先順が逆。

さらに`copyFramesFromScenes()`は
新frameへ:

```text
area
shape
```

両方を書いている。

JSON Save/Reload後、
これらは別objectとなる。

その後UI dragが`area`だけ更新すると:

```text
UI = new area
Python Overlay = stale shape
```

になり得る。

---

# 24. Canonical Frame geometry key

新Mainline v1は:

```text
area
```

を唯一のcanonical keyにする。

`shape`はlegacy import boundaryだけ。

---

# 25. Normalize legacy shape

Load / migration時:

```text
shape only
→ areaへcopy
→ canonical documentではshape除去
```

。

---

# 26. Both area + shape

両方存在し、値が異なる場合:

```text
silent precedence禁止
```

。

以下どちらか:

```text
fail-closed
or
explicit migration choosing canonical area + diagnostic
```

。

推奨はmigration boundaryでareaへ正規化。

---

# 27. copyFramesFromScenes

出力:

```text
area only
```

。

`shape`を複製しない。

---

# 28. Save/Reload Oracle for geometry

```text
Copy Frames from Scenes
Save
Reload
Frame 1 drag
Queue
```

。

最終FrameOverlayが
Reload後に動かした位置を使うこと。

---

# 29. Finding F — Empty visual_framesがfake full-frame guideになる

`derive_panel_layout_spec_from_frames([])`は現在:

```text
0 visual frames
→ 0.05..0.95 full frame PANEL_LAYOUT_SPEC
```

をfabricateする。

これはM3A policy:

```text
0 frames
→ guide OFF
```

と矛盾。

---

# 30. Empty bridge semantics

0 framesでは:

```text
No frame guide
```

を明示。

推奨:

```text
return None / disabled plan
```

またはcallerが0件時呼ばない。

Fake full-frame layoutを作らない。

---

# 31. ControlNet未接続でも今直す理由

M3B/M3A laterでこのadapterをControlNetへ繋いだ時、
0-frame workflowが勝手にfull-frame guide化する事故を防ぐ。

---

# 32. Finding G — ReportのFrame ID記述がcodeと不一致

M3A Report:

```text
frame_{timestamp}_{random4hex}
```

と記載。

実`getNextFrameId()`:

```text
frame_1
frame_2
...
```

のcollision-free sequential allocation。

実装側は問題ない。

Reportを実装事実へ訂正。

---

# 33. Stable ID requirement

必要なのは:

```text
delete middle
→ add
→ existing ID reuse/collisionなし
```

。

random/timestampである必要はない。

---

# 34. Finding H — Visual provenance自動PASS
# REQUIRED CORRECTION

`run_m3a_visual_frame_verification.py`は生成成功時、
自動で:

```json
"visual_status": "VERIFIED_CORRECT"
```

を書いている。

Runner自身は画像内容を目視評価していない。

---

# 35. Manifest v2 Truth

各task:

```text
runtime_status
structural_frame_status
visual_status
review_method
```

を分離。

例:

```json
{
  "runtime_status": "PASS",
  "structural_frame_status": "PASS",
  "visual_status": "PENDING",
  "review_method": "NOT_REVIEWED"
}
```

。

---

# 36. Deterministic geometryはVisual review不要で検証可能

Pixel oracle:

```text
border coordinate
gutter white
frame interior preservation
```

は:

```text
structural_frame_status=PASS
```

でよい。

「画像として漫画に見える」等はDirect Image Inspectionのみ。

---

# 37. 直接見た場合

Geminiが実際にcontact sheet/raw PNGを開いて確認した場合:

```text
visual_status = PASS/PARTIAL/FAIL
review_method = DIRECT_IMAGE_INSPECTION
```

。

自動queue成功と混同しない。

---

# 38. M2B.1 DOM hardening regression
# SHOULD FIX

M2B.1 Reportではspecial-character安全化を主張したが、
現JSにはCAST chip等でuser `display_name`を含む
`innerHTML`構築が残っている。

M3A.1でJSを触るため、
可能なら:

```text
createElement
textContent
```

へ統一。

少なくとも:

```text
< > " ' &
```

でDOMが壊れないheadless testを維持。

これはM3A.1 primary gateではないが、
Report truthと実装を一致させる。

---

# 39. Canonical Workflow only

Root:

```text
workflows/MINIMUM_HAND_MANGA_DRAFT.json
```

1本。

M3A1_TEST.json等をrootへ増やさない。

---

# 40. FrameOverlay node Product surface

FrameOverlayはInternal group。

Userが:

```text
page_index
global line_thickness
raw document JSON
```

を直接触らない構成を優先。

---

# 41. Browser Closure — mandatory
# Owner canonical workflow

今回はOwnerに別fixtureを渡さない。

```text
MINIMUM_HAND_MANGA_DRAFT.json
```

そのものを使う。

---

# 42. Browser Step 1

Server restart + browser hard reload。

Canonical Workflow load。

確認:

```text
Custom DOM visible
Default Queue works
```

。

---

# 43. Browser Step 2 — Frame Layer

クリック:

```text
Visual Panel Frames
```

。

確認:

```text
Frame toolbar visible
Scene inspector hidden
```

。

---

# 44. Browser Step 3 — Fastest Owner path

推奨:

```text
Copy Frames from Scenes
```

を一回押す。

これで2 Scene sampleから
2 independent Visual Framesを作る。

---

# 45. Browser Step 4 — Visible Frame output

Queue。

期待:

```text
top frame
white gutter
bottom frame
outer white margins
black borders
```

が最終SaveImageに見える。

---

# 46. Browser Step 5 — Independence

Frame 1だけdrag。

Queue。

確認:

```text
black frame位置が変わる
Scene Region自体は動かない
```

。

---

# 47. Browser Step 6 — Thickness

Frame 1:
2px

Frame 2:
8px

Queue。

最終画像でも差が出る。

---

# 48. Browser Step 7 — Save / Reload

Workflow save。

Reload。

確認:

```text
2 frames retained
frame IDs retained
frame geometry retained
thickness retained
```

。

---

# 49. Browser Step 8 — Post-reload drag

Reload後Frameをdrag。

Queue。

最終Overlayが新geometryを使う。

`area/shape` driftが無いことの実証。

---

# 50. Browser Step 9 — Overlay internal values

Canonical first pageで:

```text
effective_page = 0
```

。

もしpage_index widgetを残すなら0。

Owner screenshotで1にならない。

---

# 51. Browser Step 10 — CAST regression

余力があれば同じsessionで:

```text
Add Alice
select Alice
Place Alice
```

。

M2B Browser live regressionを閉じる。

---

# 52. Browser Step 11 — Save/reload CAST

Alice placementもSave/Reloadで保持。

M3A.1でM2B未閉鎖項目をまとめて閉じる。

---

# 53. Browser Evidence

最低限:

```text
M3A1_BROWSER_TWO_FRAMES.png
M3A1_BROWSER_FRAME_MOVED.png
M3A1_BROWSER_RELOADED.png
```

。

Agentがbrowserを操作できない場合、
Owner evidence pendingでよい。

Static mockをLIVE_BROWSERと呼ばない。

---

# 54. Runtime verification

画像研究を再実施しない。

必要なのは:

```text
V0 no frame
V1 two frame gutter
V2 thickness difference
V3 save/reload serialized fixture
```

程度。

---

# 55. New Pixel Oracles

最低限:

```text
0-frame exact passthrough
frame interior exact source preservation
gutter pure white
border pure black
per-frame thickness respected
post-reload area respected
```

。

---

# 56. FrameOverlay debug JSON

最低限:

```text
document_id
resolved_page_index
frame_count
frame_id
effective_area
effective_border_thickness
render_mode
validation_status
```

。

---

# 57. Render Mode

Product v1:

```text
comic_panels
```

をdefault。

意味:

```text
white gutter + black border + source inside frame
```

。

必要なら研究用:

```text
borders_only
```

をinternalに残してよいが、
Primary UIへ出さない。

---

# 58. Per-frame thickness range

Frontend:

```text
1–24 px
```

程度でよい。

Backendも同範囲をvalidate。

---

# 59. Frame line scaling

`border_thickness`をpixel値とするなら、
final generated resolutionに対してそのpixel数を使う。

Canvas previewの縮尺だけ表示上scale。

Reportに明記。

---

# 60. Canonical Frame representation

新規frame:

```json
{
  "frame_id": "frame_1",
  "order": 1,
  "area": {
    "shape_type": "rect",
    "x": 0.08,
    "y": 0.06,
    "w": 0.84,
    "h": 0.42
  },
  "border_thickness": 4,
  "metadata": {}
}
```

。

`shape`は新規保存しない。

---

# 61. Visual Frame validation

最低限:

```text
frame_id unique
area rect valid
inside page
border_thickness valid int
```

。

---

# 62. Automated Python tests

既存174相当を全部維持。

追加候補:

```text
test_m3a1_frame_overlay_runtime_truth.py
test_m3a1_frame_geometry_normalization.py
test_m3a1_frame_workflow_serialization.py
```

。

---

# 63. Python必須tests

```text
invalid JSON -> fail
page out-of-range -> fail
valid 0 frames -> pass-through
2 frames -> white gutter
per-frame thickness 2/8 -> reflected
area-only canonical
legacy shape-only -> normalized
area+shape mismatch -> diagnostic/fail
empty frames -> no PANEL_LAYOUT_SPEC fake guide
```

。

---

# 64. JS必須tests

既存19を維持。

追加:

```text
Copy Frames creates area-only canonical frames
Frame drag after JSON roundtrip updates effective area
Frame resize after roundtrip
Frame thickness persistence
Edit layer pointer isolation
special-character CAST chip safety
```

。

---

# 65. Canonical Workflow serialization test

FrameOverlay nodeについて、
実Live-save JSONに基づいて:

```text
widget order
linked authoring_document input
page selection
line thickness fallback
```

を固定。

以前のseed widget shift問題を繰り返さない。

---

# 66. Do not guess widget order

ComfyUI frontendが実際にsaveしたJSONを確認。

手書きJSONの想定だけでPASSにしない。

---

# 67. M3A Report truth correction

元Reportは削除しない。

新M3A.1 Reportで:

```text
M3A headless architecture = accepted
M3A live frame browser = unproven at baseline
```

を明記。

---

# 68. Correct specific claims

訂正:

```text
Frame ID scheme:
sequential collision-free, not timestamp/random

Gutter:
M3A baseline did not actually white-mask outside frames

Per-frame thickness:
M3A baseline UI did not causally reach final overlay

Visual manifest:
runtime success had been labeled VERIFIED_CORRECT automatically
```

。

---

# 69. New Report

```text
docs/reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md
```

。

---

# 70. Manifest

```text
docs/verification/m3a1/M3A1_FRAME_RUNTIME_MANIFEST.json
```

。

---

# 71. Contact Sheet

最低限:

```text
M3A1_FRAME_GUTTER_AND_THICKNESS_ORACLE.png
```

。

中身:

```text
0 frame
2 frame 4px
2 frame 2px/8px
moved frame
```

。

---

# 72. ControlNet
# 今回禁止

Frame ControlNetはまだPENDINGでよい。

M3A.1で:

```text
AnyTest
0.20
0.35
```

を再開しない。

まずdeterministic frameを完成。

---

# 73. M3B
# 今回禁止

追加しない:

```text
rough manga upload
white dummy
silhouette guide
character ControlNet
OpenPose
```

。

---

# 74. Product Minimal-Hand

User operation:

```text
Visual Panel Frames
→ Copy Frames from Scenes
→ optional drag/resize
→ Generate
```

で漫画枠が確実に出ること。

---

# 75. M3A.1 Acceptance Gates

```text
M0–M3A REGRESSION:
PASS

OWNER CUSTOM DOM:
PASS

CANONICAL FRAMEOVERLAY LIVE VALUES:
STABLE

FIRST PAGE RESOLUTION:
CORRECT

PAGE INDEX SILENT PASS-THROUGH:
NO

INVALID DOC FAIL-CLOSED:
PASS

0 FRAME:
PIXEL-IDENTICAL PASS

FRAME CANONICAL GEOMETRY KEY:
AREA ONLY

AREA/SHAPE DRIFT:
NO

COPY FRAMES SAVE/RELOAD:
PASS / OWNER PENDING

WHITE GUTTERS:
PASS

BLACK BORDERS:
PASS

PER-FRAME THICKNESS:
PASS

FRAME/SCENE INDEPENDENCE:
PASS

EMPTY FRAME CONTROL GUIDE:
OFF / NO FAKE FULL FRAME

VISUAL MANIFEST AUTO-PASS:
NO

LIVE BROWSER FRAME EDIT:
PASS / OWNER PENDING

LIVE BROWSER FINAL FRAMES:
PASS / OWNER PENDING

CAST LIVE REGRESSION:
PASS / OWNER PENDING

ACTIVE ROOT WORKFLOW:
1

CONTROLNET ADDED:
NO

M3B FEATURES ADDED:
NO
```

---

# 76. M3B GO条件

最低限Owner Browserで:

```text
1. Visual Panel Frames layerを開ける
2. Copy/Add Frameできる
3. Frameをdrag/resizeできる
4. Queueすると白gutter+黒frameが見える
5. Save/Reloadでframeが保持
```

。

これが通ってから:

```text
M3B — Rough Manga / White-Dummy Character Guide Integration
```

へ進む。

---

# 77. Publication truth

本Card開始時にGitHubから:

```text
M3A Commit A:
45ccd226...

M3A Navigation:
858dd7f5...
```

を取得可能。

次Entryで:

```text
LOCAL PENDING OWNER PUSH
```

という古い表記を現在remote事実へ訂正。

---

# 78. Commit A

推奨:

```text
fix(manga): close visual frame runtime semantics and live framing path
```

含む:

```text
frame_overlay.py
authoring_visual_frame_bridge.py
authoring_contract.py if normalization needed
minimum_hand_authoring_ops.js
minimum_hand_scene_editor.js
tests
canonical workflow if serialization changes
verification
M3A.1 report
STATUS / DOCUMENT_REGISTER
```

。

---

# 79. Commit B

推奨:

```text
docs(manga): publish M3A.1 review target
```

。

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current card = M3A.1
Next = M3B only after owner browser acceptance
```

。

---

# 80. Final Response Format

```text
MODEL USED:
Gemini 3.8 STANDARD/HIGH

BASELINE REVIEW TARGET:
45ccd226b7a853e6279261a34bbdcdf5e98a1a32

M3A.1 IMPLEMENTATION COMMIT A:
M3A.1 NAVIGATION COMMIT B:
PUSH STATUS:

OWNER SCREENSHOT BASELINE:
FRAME COUNT IN BASELINE:

FRAMEOVERLAY LIVE LINE_THICKNESS:
FRAMEOVERLAY LIVE PAGE:
CANONICAL SERIALIZATION:
PAGE RESOLUTION POLICY:

INVALID DOCUMENT:
OUT-OF-RANGE PAGE:
0 FRAME:

FRAME GEOMETRY CANONICAL KEY:
LEGACY SHAPE MIGRATION:
AREA/SHAPE DRIFT:

WHITE GUTTERS:
BLACK BORDERS:
PER-FRAME THICKNESS:
BORDER COLOR POLICY:

EMPTY FRAME GUIDE:
PANEL_LAYOUT ADAPTER:

MANIFEST RUNTIME/VISUAL SPLIT:
FRAME ID REPORT CORRECTION:

BROWSER FRAME LAYER:
BROWSER COPY FRAMES:
BROWSER DRAG/RESIZE:
BROWSER FINAL FRAME OUTPUT:
BROWSER SAVE/RELOAD:
BROWSER CAST REGRESSION:

OLD TESTS:
NEW TESTS:
TOTAL:
JS TESTS:

WORKFLOW:
ACTIVE ROOT COUNT:

CONTACT SHEET:
MANIFEST:
REPORT:

M3A PRODUCT PATH:
PASS / PARTIAL / HOLD

M3B READY:
YES / NO

OWNER ACTION REQUIRED:
```

---

# 81. 最終原則

M3A.1で証明するものは:

```text
UIで見えているFrame
=
保存されたFrame
=
FrameOverlayが読むFrame
=
最終画像に出るFrame
```

という因果の一致。

そして「漫画の枠」は:

```text
white gutter
+
black deterministic border
```

としてAI任せにしない。

0 Frameは従来画像をそのまま。

Visual Frameがある時だけ
実際の漫画ページとして切り出す。

このProduct pathが実ブラウザで閉じてから、
M3Bの白ハゲ / Rough Manga Guideへ進むこと。
