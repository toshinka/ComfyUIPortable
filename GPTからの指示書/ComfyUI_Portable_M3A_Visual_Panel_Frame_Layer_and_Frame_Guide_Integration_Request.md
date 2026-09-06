# ComfyUI Portable — M3A / Phase 3M-3A
# Visual Panel Frame Layer & Frame Guide Integration
## — Semantic Sceneと「実際の漫画コマ」を分離したまま、最小手で見える枠と構図ガイドを追加する —
## Antigravity2 / Gemini 3.8 STANDARD/HIGH 向け Bounded Product Integration Card

## 推奨モデル

```text
Gemini 3.8 STANDARD / HIGH
```

今回もLOWは使用しないことを推奨する。

理由は、生成能力研究そのものより:

```text
Live ComfyUI Product UI
Authoring Document persistence
Visual Frame geometry
deterministic frame rendering
optional ControlNet guide
workflow serialization
```

を同時に扱う統合Cardだからである。

---

# 0. 今回の判断

M2B.2のCritical Browser BootstrapはOwner実画面で修正確認できた。

Owner screenshotから確認できる:

```text
Product Custom DOM visible:
PASS

raw document_json primary textarea:
HIDDEN / PASS

unexpected control_after_generate row:
ABSENT / PASS

style_template:
Manga Monochrome / PASS

resolution:
Portrait 832x1216 / PASS

Default Queue:
PASS
(output image generated)
```

一方、この1枚だけでは以下は未証明:

```text
Selected CAST live placement
Save / Reload persistence
```

ただしM2B.1でHeadless ContractとBackend semanticsは既に通っているため、
M3Aへ進んでよい。

M3Aの最初と最後でこれらを回帰確認すること。

---

# 1. 最初に読む正本

必ず最初に:

```text
ComfyUIPortable/GITHUB.TXT
```

次に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

本Card発行時の固定Review Target:

```text
117c5d9a59de5d33a51fedb3819b5a4bae0eba38
```

M2B.2 Navigation Commit:

```text
85cc02452186a41ce6c982584ed6f72b22db6eef
```

本Card発行時点ではremote mainに両Commitが存在する。

したがって旧報告の:

```text
LOCAL COMMITTED / PENDING OWNER PUSH
```

は現在事実ではない。

次Navigation更新時にpublication truthを修正する。

---

# 2. M2B.2 Review Verdict

```text
M2B.2 Bootstrap Fix:
PASS

M2B.2 Default Live Queue:
PASS (Owner screenshot)

M2B.2 Product Surface:
PASS

CAST selected-placement Live Browser:
NOT SHOWN IN CURRENT SCREENSHOT

Save/Reload Live Browser:
NOT SHOWN IN CURRENT SCREENSHOT

M3A:
GO

M3B Rough Character/Dummy Guide:
HOLD until M3A frame layer is stable
```

---

# 3. M3をM3A / M3Bに分ける理由

M3全体の戦略は:

```text
Semantic Scene / CAST staging
+
actual Visual Panel Frame
+
rough manga / white-dummy guide
```

。

しかしM2B.2でFrontend Bootstrapを直した直後に:

```text
Frame editor
Image upload
Character guide
ControlNet
```

を一度に積むと、再びLive Browser failureの原因分離が難しくなる。

よって今回は:

```text
M3A:
Visual Panel Frame layer
+ deterministic frame preview/output
+ optional frame-only ControlNet guide

M3B:
rough manga / white-dummy / character occupancy guide
```

に分離する。

---

# 4. Product Goal

現在ユーザーが扱う:

```text
Scene Rectangle
=
「この辺で何が起きるか」

Character Rectangle
=
「このキャラがだいたいこの辺」
```

に対し、M3Aでは初めて:

```text
Visual Panel Frame
=
「実際に見える漫画のコマ」
```

を追加する。

絶対条件:

```text
Semantic Scene
≠
Visual Panel Frame
```

。

---

# 5. Visual FrameをSceneへ戻してはいけない

禁止:

```text
Frame ID == Scene ID を必須化
Frame移動でSceneも自動移動
Scene移動でFrameも自動移動
Frame内にSceneを強制clip
Panel owns Scene
```

。

M0以降の契約を維持:

```text
Page
├ Scenes
├ Character Instances
└ Visual Frames
```

。

---

# 6. Visual Frameの役割を2つに分ける
# IMPORTANT

M3Aでは「見える枠」と「生成ガイド」を同一視しない。

## A. Deterministic Visual Frame

最終ページ上へ:

```text
黒い枠線
白いgutter / margin
```

を確実に描く。

これはdiffusionに頼らない。

## B. Optional Generation Guide

同じFrame geometryから白黒Guideを作り、
必要ならControlNetへ送って:

```text
内容がコマ構造を意識する
```

よう補助。

こちらはOFF可能。

---

# 7. なぜDeterministic Frameが必要か

漫画の枠線そのものは:

```text
「AIがうまく描くか」
```

をSeedに委ねる必要がない。

ユーザーが指定したgeometryを
確実に見えるページへ反映する方がProductとして正しい。

ControlNetは:

```text
構図を枠に寄せる補助
```

に限定する。

---

# 8. Authoring Contract

既存:

```text
page.visual_frames
```

を使用する。

新しいparallel SSOTを作らない。

---

# 9. Visual Frame v1 Shape

M3Aではrect-onlyでよい。

候補:

```json
{
  "frame_id": "frame_1",
  "name": "Frame 1",
  "order": 1,
  "area": {
    "shape_type": "rect",
    "x": 0.05,
    "y": 0.05,
    "w": 0.90,
    "h": 0.42
  },
  "metadata": {}
}
```

。

正確なfieldは既存Authoring Contractへ合わせる。

新必須fieldを無駄に増やさない。

---

# 10. Stable Frame ID

```text
frame_id
```

はstable。

Delete-middle → Addでcollisionしない。

Display order:

```text
Frame 1
Frame 2
```

とidentityを分離。

---

# 11. Visual Frame数

固定6に戻さない。

Authoring Documentは可変配列。

M3A UIでは最低限:

```text
1
2
4
```

を扱えること。

---

# 12. Frame 0件

許可。

```text
visual_frames = []
```

なら:

```text
Deterministic frame overlay = OFF
Frame Control guide = OFF
```

。

M2Bまでの既存生成を維持。

---

# 13. Product UI — Edit Layer

Current unified canvasを維持。

新しい別nodeをPrimary UIにしない。

Authoring DOM内に小さく:

```text
Edit:
[Scene] [Frame] [Character]
```

または同等の3-layer switchを追加。

---

# 14. Simple First表示

CAST 0件でも:

```text
Scene
Frame
```

は使える。

Character layerはCASTがある時だけ表示/有効化してよい。

---

# 15. Frame Layerを選んだ時

Canvas上:

```text
Visual Frames = strong outline
Scenes = faint translucent
Characters = faint / non-draggable
```

。

Scene layer選択時:

```text
Scenes = active
Frames = faint reference
```

。

Character layer:

```text
Characters = active
Scene parent = reference
Frames = faint
```

。

---

# 16. 非対象Layerを誤dragしない

重要。

Frame edit中にSceneを誤って動かさない。

Scene edit中にFrameを誤って動かさない。

Visual overlapがあってもactive layerだけpointer操作対象。

---

# 17. Frame操作

最低限:

```text
Add Frame
Select
Drag
4-corner Resize
Delete
```

。

Duplicateは任意。

---

# 18. Frame move invariant

Frameを動かしても:

```text
Scene geometry:
UNCHANGED

Character Instance geometry:
UNCHANGED
```

。

Python/JS test必須。

---

# 19. Scene move invariant

Sceneを動かしても:

```text
Visual Frame geometry:
UNCHANGED
```

。

Character InstancesはM0 semanticsに従ってSceneと一緒に動く。

---

# 20. Frame resize invariant

Frame resize:

```text
Scenes unchanged
Characters unchanged
```

。

---

# 21. One-shot Copy helper
# Optional

Minimum-Handのため:

```text
Frames from Scenes
```

buttonは有用。

押した瞬間だけ:

```text
current Scene rectangles
→ new Visual Frame rectangles
```

としてcopy。

その後は完全独立。

---

# 22. CopyはLinkではない

禁止:

```text
Sceneを動かすとFrameも追従
```

。

UIに必要なら:

```text
Copy current Scene layout once
```

と明示。

---

# 23. Default Canonical Sample

現在の2 Scene sampleを維持。

M3A canonical workflowでは以下のどちらか。

推奨:

```text
visual_frames = []
```

で既存simple workflowをそのままload可能にし、
UserがAdd Frameする。

Verification fixtureでは:

```text
2 visual frames
```

を使用。

---

# 24. Alternative Default

もしProduct理解のため2 Frame初期sampleが明らかに良いなら:

```text
Scene 1 / Scene 2 geometryを一回copyした2 Visual Frames
```

をdefaultにしてよい。

ただしmetadataにlive bindingを持たせない。

---

# 25. Existing asset reuse audit
# PRIOR-ART / ADOPT GATE

新rendererを書く前に必ず既存:

```text
TegakiMangaPanelLayoutEditor
render_panel_layout_image()
PANEL_LAYOUT_SPEC
```

を監査。

既存`render_panel_layout_image()`は:

```text
white background
black unique edges
no labels
no colors
```

のControlNet向け純粋panel guideを既に生成する。

第一候補は再利用。

---

# 26. Thin VisualFrame Adapter

必要なら:

```text
authoring_visual_frame_bridge.py
```

を追加。

責務:

```text
page.visual_frames
→ derived PANEL_LAYOUT_SPEC
or
→ deterministic frame render plan
```

。

Persistent DocumentへPANEL_LAYOUT_SPECを保存しない。

---

# 27. Adapter policy

M3A rect-only framesから:

```text
vertices
panels
canvas
```

をderived。

Frame IDsとPanelLayout internal IDsのmappingをdebugへ出す。

---

# 28. Adapter fail-closed

以下はsilent correctionしない:

```text
negative size
outside page
invalid shape
duplicate frame_id
```

。

Authoring Contract validationと整合。

---

# 29. Overlap policy

Visual Panel FramesはM3Aでは原則:

```text
non-overlapping
```

をProduct UI推奨。

重なるframeは生成/最終枠として意味が曖昧。

---

# 30. Overlap UI

Authoring Documentがoverlapを技術的に保持できても、
M3A Product UIでは:

```text
warning
```

を出してよい。

勝手にFrameを移動しない。

---

# 31. Gutter / Margin

M3Aで見える最低限:

```text
line_thickness
```

はAdvanced。

Primary UIでは固定defaultでよい。

---

# 32. Product Default

例:

```text
Frame line = 4 px @ 832x1216 basis
```

。

解像度に応じて比例調整するか、
pixel固定かを決めてReportに明記。

---

# 33. Deterministic Frame Preview

Authoring nodeから:

```text
visual_frame_preview
```

を出すか、
既存previewへFrame overlayを重ねてよい。

ただしScene Region previewと区別できること。

---

# 34. Preview color

編集UI:

```text
Frame = dark/black
Scene = current scene colors
Character = cast colors
```

。

生成Control image:

```text
white + black lines only
```

。

編集色をControlNetへ送らない。

---

# 35. Deterministic Final Overlay
# M3A Primary

新規thin node候補:

```text
TegakiMangaFrameOverlay
```

または既存generic image compositingで実現できるなら再利用。

入力:

```text
generated IMAGE
visual frame plan / frame mask
```

出力:

```text
framed IMAGE
```

。

---

# 36. Overlay最低機能

```text
black frame line
optional outside/page margin
```

。

M3Aで吹き出し・文字・crop editorを作らない。

---

# 37. OverlayはSemantic内容を再生成しない

単なるdeterministic post-process。

ControlNet OFFでも枠は正確。

---

# 38. Output path

Canonical Workflow:

```text
KSampler
→ VAE Decode
→ Deterministic Frame Overlay
→ SaveImage
```

。

もしvisual_frames 0件:

```text
pass-through
```

。

---

# 39. Before/After Preview

可能なら:

```text
Generated Raw
Framed Output
```

を両方debug可能。

User-facing primaryはFramed Output。

---

# 40. Optional Frame ControlNet
# Secondary

M3AではControlNetをCore強制しない。

User-facing default:

```text
Frame Guide = OFF
```

または安全な`Auto/Off`。

まずA/B実測。

---

# 41. Existing ControlNet path reuse

優先:

```text
core ControlNet loader
core ControlNetApplyAdvanced
existing compatible Illustrious/SDXL ControlNet
```

。

新ControlNet frameworkを作らない。

Advanced-ControlNet adoptionは今回不要。

---

# 42. Control model

実環境で存在確認。

過去のAnyTest v4 Illustrious-compatible ControlNetを候補。

Reportへ:

```text
exact filename
strength
start_percent
end_percent
```

を記録。

存在しなければControlNet stageをPENDINGにし、
別モデルへ勝手に置換しない。

---

# 43. Frame Control目的

ControlNetの目的:

```text
各コマの内容がframe構造を意識する
```

こと。

目的ではない:

```text
人物poseを固定
identityを固定
exact black borderを描かせる
```

。

---

# 44. Control Strength benchmark

過去の0.75強拘束を避ける。

最低:

```text
0.00
0.20
0.35
```

。

必要なら0.50を追加してよいが、
まず低強度。

---

# 45. Control start/end

既知の安全設定を基準。

変更するなら1条件ずつ。

---

# 46. Test Frame Layout F1

2 horizontal frames:

```text
Frame A top
Frame B bottom
```

。

Semantic Scenesも2つだが、
完全一致させてもよいbaseline。

---

# 47. Test Frame Layout F2
# Independence Oracle

Semantic Scenes:

```text
same geometry
same prompts
same CAST
same seed
```

固定。

変更するのは:

```text
Visual Frame geometry only
```

。

例:

```text
F1 = horizontal 50/50
F2 = left narrow / right large
```

。

---

# 48. Independence Acceptance

Document / compiler上:

```text
Scene areas identical
Character areas identical
Visual Frames changed only
```

が証明されること。

---

# 49. Deterministic Overlay Oracle

F1 / F2で:

```text
framed output border geometry
```

が指定通り変わる。

これはpixel-levelで検証可能。

---

# 50. ControlNet Causality Oracle

ControlNetを使う場合:

```text
same raw semantic inputs
same seed
same frame geometry
Control OFF vs ON
```

。

見る:

```text
content separation
subject placement relative to frame
literal line artifact
composition rigidity
seed freedom
```

。

---

# 51. Frame ≠ Scene causality

重要:

```text
Frameを変えただけで
Scene promptが入れ替わる
```

のはFAIL。

Semantic Sceneの意味割当はScene側。

Visual Frameは意味Prompt所有者ではない。

---

# 52. One visible frame / Two scenes

M3A contract testとして:

```text
2 Semantic Scenes
1 Visual Frame
```

を保存・compile可能にする。

実画像生成は任意。

---

# 53. Two visible frames / One scene

同様:

```text
1 Semantic Scene
2 Visual Frames
```

。

Visual Frame数とScene数を同一に固定しない。

---

# 54. No automatic pairing

禁止:

```text
Frame 1 => Scene 1
Frame 2 => Scene 2
```

を恒久契約にすること。

必要ならUI上のone-shot copy / suggested correspondenceのみ。

---

# 55. Frame Inspector

Selected Frame時:

```text
Frame Name
```

程度。

Advanced:

```text
line thickness
guide enabled
```

等は必要なら。

---

# 56. No per-frame Prompt

Visual FrameにPrompt欄を追加しない。

Prompt ownerはScene。

---

# 57. No CAST assignment to Frame

Character InstanceはSceneへ所属。

FrameにCASTをbindしない。

---

# 58. Save / Reload

最低限:

```text
visual_frames
frame IDs
areas
order
guide settings if persisted
```

が保持。

---

# 59. Guide settings persistence

ControlNetのbackend-specific:

```text
node id
ControlNet model object
connection info
```

をAuthoring Documentへ入れない。

Persistするなら:

```text
guide enabled
guide type
user intent level
```

等のbackend-independent設定だけ。

---

# 60. Backend-independent guide contract

候補:

```text
page.guides[]
```

へ:

```text
guide_id
type = "panel_frame"
enabled
source = "visual_frames"
```

程度。

ただし既存contractに自然に収まる場合のみ。

無理にschema拡張しない。

---

# 61. Rough Manga image upload
# M3AではNOT REQUIRED

Blueprintの:

```text
枠・ラフ画像を追加
```

はM3全体の目標。

しかしM3AではまずVisual Framesを安定させる。

画像drop/uploadは:

```text
M3B
```

へDEFER可。

---

# 62. White-dummy Character Guide
# M3Aでは禁止

今回:

```text
head circle
body block
OpenPose
3D mannequin
```

をCharacter Controlへ繋がない。

M3Bで扱う。

---

# 63. Current Character Rough Regions

M2BのCharacter rectanglesはそのまま。

Frame layer追加で操作を壊さない。

---

# 64. CAST Browser Regression Gate

M3A実装前/後のheadless/live smokeで:

```text
Alice selected
→ Alice instance

Bob selected
→ Bob instance
```

を維持。

---

# 65. Owner screenshot baseline

現Owner screenshotをM2B.2 browser acceptance evidenceとしてReportに記録してよい。

ただしrepoへ画像を取り込めない場合:

```text
external owner screenshot observed
```

と書く。

pathを捏造しない。

---

# 66. Browser E2E — M3A Smoke

最低限Owner/Agent実ブラウザで:

```text
1. workflow load
2. Product Custom DOM visible
3. Add Frame
4. Frame drag
5. Frame resize
6. Scene layerへ戻る
7. Scene drag -> Frame unchanged
8. Queue
9. Framed output visible
10. Save
11. Reload
12. Frame persists
```

。

---

# 67. CAST regression browser

可能なら同時に:

```text
Add Alice
place Alice
```

。

M2B.2で未撮影だったSelected CAST Live Pathをここで閉じる。

---

# 68. Browser Evidence truth

```text
STATIC / HEADLESS
LIVE BACKEND
LIVE BROWSER
OWNER OBSERVATION
```

を分離。

---

# 69. Automated Tests

既存167 Python + 15 JSを維持。

---

# 70. Python新規候補

```text
test_m3a_visual_frame_contract.py
test_m3a_visual_frame_bridge.py
test_m3a_frame_overlay.py
test_m3a_frame_control_plan.py
```

。

---

# 71. Python必須

```text
0 visual frames allowed
1 frame
2 frames
4 frames
stable IDs
delete middle + add unique
frame move does not change scenes
frame resize does not change characters
scene move does not change frames
1 scene / 2 frames valid
2 scenes / 1 frame valid
derived PANEL_LAYOUT_SPEC does not mutate document
overlay geometry matches frames
0 frames => pass-through
```

。

---

# 72. JS必須

```text
Edit layer selection
Frame add/select
Frame drag
Frame resize
Frame delete
non-active layer not draggable
Scene move leaves frames unchanged
Character move leaves frames unchanged
Save/reload mock
M2B CAST selection regression
```

。

---

# 73. Existing renderer reuse test

もし:

```text
render_panel_layout_image()
```

を再利用した場合:

```text
white background
black line
no labels/colors
expected output size
```

をassert。

---

# 74. Deterministic Frame pixel test

既知Frame geometryで:

```text
expected border pixel = black
inside non-border = unchanged / expected
```

を小さいfixtureで確認。

---

# 75. ControlNet testは条件付き

Compatible ControlNet assetが存在した時だけ。

Assetなし:

```text
CONTROLNET FRAME GUIDE = PENDING
```

でもM3A frame-layer architectureはPASS可能。

---

# 76. M3A Product Gate

M3AのPrimary successは:

```text
Visual Frame layer exists
Frame ≠ Scene independence proven
Final visible frame deterministic
```

。

ControlNet qualityはSecondary。

---

# 77. Frame ControlNetが有害な場合

もし:

```text
literal grid artifacts
character suppression
composition rigidity
```

が強いなら:

```text
Frame ControlNet = OPTIONAL / REJECTED FOR CORE
```

。

Deterministic frame layerはそのまま採用。

---

# 78. Seed Brainstorm Freedom

Control OFFとONで複数seedを少数比較。

求める:

```text
frame respect improves
but gesture/background nuance still varies
```

。

---

# 79. Benchmark seed

大量生成不要。

例:

```text
42
101
202
```

。

---

# 80. M3A Verification Conditions

最低限:

```text
V0: no frames / regression
V1: 2-frame deterministic overlay
V2: alternate frame layout same semantics
V3: 1 scene + 2 frames
V4: 2 scenes + 1 frame
```

。

ControlNetあり:

```text
C0: OFF
C1: 0.20
C2: 0.35
```

。

---

# 81. Contact Sheet

新規:

```text
docs/verification/m3a/M3A_VISUAL_FRAME_ORACLE.png
```

。

ControlNet実施時:

```text
M3A_FRAME_CONTROLNET_ORACLE.png
```

。

---

# 82. Manifest

```text
docs/verification/m3a/M3A_VISUAL_FRAME_MANIFEST.json
```

。

各condition:

```text
condition_id
seed
scene_geometry_hash
frame_geometry
frame_overlay_status
controlnet_enabled
controlnet_model
control_strength
runtime_status
visual_status
review_method
output_raw
output_framed
notes
```

。

---

# 83. Runtime / Visual分離

生成成功:

```text
runtime_status = PASS
```

。

Frame geometry:

pixel/structural testで評価可。

ControlNet semantic effect:

直接画像を見た時だけVisual PASS。

---

# 84. Canonical Workflow

Root:

```text
workflows/MINIMUM_HAND_MANGA_DRAFT.json
```

1本を維持。

---

# 85. Workflow internal groups

User workspace:

```text
Minimum-Hand Authoring
Frame preview/output
```

。

Internal:

```text
frame bridge
optional control
overlay
```

をDO NOT TOUCH groupへ。

---

# 86. ControlNet node exposure

ControlNetを追加してもPrimary user workspaceへ生nodeを出さない。

---

# 87. M3A UI Complexity Gate

初見画面に以下を増やさない:

```text
Control model dropdown
start_percent
end_percent
preprocessor
Control strength slider
topology JSON
PANEL_LAYOUT_SPEC JSON
```

。

---

# 88. Product user action

理想:

```text
Frame layer
→ Add Frame
→ drag/resize
→ Generate
```

。

Control detailなしで成立。

---

# 89. Frame Control level

もしUser-facing制御が必要なら最大:

```text
Guide: Off / On
```

程度。

StrengthはAdvancedへ。

M3AではOff固定でも可。

---

# 90. Hand Count

測る。

既存2 Scene draftに2 Frame追加:

```text
Edit Frame
Add
drag
Add
drag
Queue
```

程度。

不要なmodalを増やさない。

---

# 91. Reset policy

既存Reset Draftがあるなら:

Visual Framesを消すか保持するかを明示。

推奨:

```text
Reset Draft = Scenes / CAST / Instances / Framesをreset
```

ならconfirm。

曖昧にFrameだけ残さない。

---

# 92. Frame delete

Frameを消しても:

```text
Scene
Character
CAST
```

を削除しない。

---

# 93. Scene delete

Sceneを削除しても:

```text
Visual Frame
```

は削除しない。

これは独立性Oracle。

---

# 94. Resolution change

Page resolution変更時:

```text
normalized frame geometry
```

を保持。

pixel rendererだけ新resolutionへ。

---

# 95. Style change

Style template変更はFrame geometryへ影響しない。

---

# 96. Candidate / Seed

Seed変更はFrame geometryへ影響しない。

Deterministic borderはseed-independent。

---

# 97. M3A Report

新規:

```text
docs/reports/M3A_VISUAL_PANEL_FRAME_AND_FRAME_GUIDE_REPORT.md
```

。

---

# 98. Report必須内容

1. Fixed Review Target
2. M2B.2 Owner Browser acceptance evidence
3. Remaining M2B browser regression status
4. Visual Frame contract
5. Scene/Frame independence
6. Product UI edit-layer design
7. Frame stable IDs
8. Existing PanelLayout renderer reuse decision
9. VisualFrame adapter
10. Deterministic frame preview
11. Deterministic final overlay
12. 0-frame regression
13. 1 Scene / 2 Frame
14. 2 Scene / 1 Frame
15. Frame-only geometry swap
16. ControlNet asset actually used
17. Control OFF/0.20/0.35 if run
18. Brainstorm freedom
19. Browser E2E
20. Save/reload
21. Tests
22. Known limitations
23. M3B recommendation

---

# 99. Product labels

Reportでは:

```text
Visual Panel Frame:
READY / PARTIAL / FAIL

Deterministic Frame Rendering:
READY / PARTIAL / FAIL

Frame ControlNet:
USEFUL / OPTIONAL / HARMFUL / PENDING
```

を分ける。

---

# 100. M3A Acceptance Gates

```text
M0–M2B.2 REGRESSION:
PASS

OWNER CUSTOM DOM BASELINE:
PASS

DEFAULT QUEUE REGRESSION:
PASS

VISUAL FRAME SSOT:
page.visual_frames

FRAME STABLE ID:
PASS

FRAME ADD/SELECT/DRAG/RESIZE:
PASS

FRAME DELETE:
PASS

FRAME MOVE CHANGES SCENE:
NO

SCENE MOVE CHANGES FRAME:
NO

FRAME RESIZE CHANGES CHARACTER:
NO

1 SCENE / 2 FRAMES:
VALID

2 SCENES / 1 FRAME:
VALID

0 FRAMES:
VALID / M2B behavior preserved

DETERMINISTIC FRAME PREVIEW:
PASS

DETERMINISTIC FINAL FRAME:
PASS

PANEL_LAYOUT BACKEND DATA IN AUTHORING SSOT:
NO

CONTROLNET CORE REQUIRED:
NO

FRAME CONTROLNET:
USEFUL / OPTIONAL / HARMFUL / PENDING

RAW JSON USER-FACING:
NO

ACTIVE ROOT WORKFLOW:
1

BROWSER LOAD:
PASS / OWNER PENDING

BROWSER FRAME EDIT:
PASS / OWNER PENDING

BROWSER SAVE/RELOAD:
PASS / OWNER PENDING
```

---

# 101. M3B GO条件

最低限:

```text
Visual Frame layer stable
Frame/Scene independence stable
Deterministic frame output stable
M2B CAST path regression stable
```

。

その後:

```text
M3B — Rough Manga / White-Dummy Character Guide Integration
```

へ進む。

---

# 102. M3Bで扱うもの

次段候補:

```text
rough manga image drop
white-dummy / silhouette
Character Instance ↔ rough figure association
weak occupancy ControlNet
```

。

Pose Editorではない。

---

# 103. 今回やらないもの

```text
OpenPose editor
3D mannequin
interaction
SubScene
speech balloons
text layout
regional LoRA
IPAdapter
full Candidate Browser
A1111 skin
```

。

---

# 104. Publication Truth

本Card開始時にはremote:

```text
M2B.2 A:
117c5d9a...

M2B.2 B:
85cc0245...
```

が取得可能。

`LOCAL ONLY`表記を次Entryで訂正。

---

# 105. Commit A

推奨:

```text
feat(manga): add independent visual panel frame layer and deterministic framing
```

含む:

```text
Authoring visual frame operations
Frontend frame layer
VisualFrame adapter
deterministic renderer/overlay
optional ControlNet frame guide if verified
tests
canonical workflow update
verification
M3A report
STATUS
DOCUMENT_REGISTER
```

。

---

# 106. Commit B

推奨:

```text
docs(manga): publish M3A review target
```

。

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current card = M3A complete / partial
Next = M3B or correction
```

。

---

# 107. Final Response Format

```text
MODEL USED:
Gemini 3.8 STANDARD/HIGH

BASELINE REVIEW TARGET:
117c5d9a59de5d33a51fedb3819b5a4bae0eba38

M3A IMPLEMENTATION COMMIT A:
M3A NAVIGATION COMMIT B:
PUSH STATUS:

M2B.2 OWNER BOOTSTRAP:
M2B CAST LIVE REGRESSION:
M2B SAVE/RELOAD REGRESSION:

VISUAL FRAME CONTRACT:
FRAME EDIT UI:
FRAME STABLE IDS:
FRAME/SCENE INDEPENDENCE:
FRAME/CHARACTER INDEPENDENCE:

PANEL LAYOUT REUSE:
VISUAL FRAME BRIDGE:
DETERMINISTIC FRAME PREVIEW:
DETERMINISTIC FINAL OVERLAY:

0 FRAME REGRESSION:
1 SCENE / 2 FRAMES:
2 SCENES / 1 FRAME:
FRAME GEOMETRY SWAP:

CONTROLNET MODEL:
CONTROL OFF:
CONTROL 0.20:
CONTROL 0.35:
FRAME CONTROLNET DECISION:

BRAINSTORM FREEDOM:

BROWSER FRAME EDIT:
BROWSER DEFAULT QUEUE:
BROWSER SAVE/RELOAD:

OLD TESTS:
NEW TESTS:
TOTAL:
JS TESTS:

WORKFLOW:
ACTIVE ROOT COUNT:

CONTACT SHEET:
MANIFEST:
REPORT:

M3A STATUS:
PASS / PARTIAL / HOLD

M3B READY:
YES / NO

OWNER REVIEW RECOMMENDED:
YES / NO
CONDITIONS:

USER ACTION REQUIRED:
```

---

# 108. 最終原則

M3Aで追加する「コマ」は、
これまでのScene Rectangleとは別物。

```text
Scene
=
意味 / 出来事 / Promptの領域

Character
=
誰がだいたいどこ

Visual Frame
=
実際に見える漫画コマ
```

。

さらに:

```text
Deterministic Frame
=
正確な枠線

Frame ControlNet
=
構図を枠へ寄せる任意補助
```

と分ける。

枠線をAIへ丸投げしない。
SceneとFrameを再結合しない。
ControlNetを入口の必須操作にしない。

まず:

```text
枠を置く
→ 確実に見える
→ 必要なら構図だけ弱くGuideする
```

までをM3Aで完成させること。
