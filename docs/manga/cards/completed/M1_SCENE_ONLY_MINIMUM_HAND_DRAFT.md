# ComfyUI Portable — M1 / Phase 3M-1
# Scene-only Minimum-Hand Draft
## Antigravity2 / Gemini 3.8 向け Bounded Implementation Card

## 推奨モデル

```text
Gemini 3.8
```

M0 / M0.1 で永続Authoring Contractと境界条件は固定した。

M1では初めて、

```text
ユーザーが少ない操作で
Sceneを置き
Promptを書き
Seedを変え
実際の画像を生成する
```

ところまで通す。

今回はCASTをまだ要求しない。

---

# 0. 最初に読む正本

必ず最初に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

を読む。

本Card発行時のReview Target:

```text
0a1ccd46fe8160b487ab748b0dfae19092ff7ac3
```

M0.1 Navigation Commit:

```text
36c9098f2d311759d046afddf5f091256092c492
```

作業開始時点のrepo事実を再確認する。

---

# 1. M0.1 Review Verdict

Web GPT確認結果:

```text
M0.1 Architecture:
ACCEPT

M0.1 hardening:
PASS

M1:
GO
```

確認済み:

- FK空集合hole修正
- duplicate page_id検出
- Legacy import validate/fail-closed
- orphan legacy binding fail-closed
- semantic-only legacy export分離
- full legacy exportでScene/Frame divergence fail-closed
- strict reverse coordinate export
- Scene group move common effective delta
- Scene resize atomic reject
- 78/78 tests
- UI/backend/workflow runtime変更なし

M0.1 Report:

```text
docs/reports/M0_1_CONTRACT_HARDENING_REPORT.md
```

---

# 2. Workflow整理方針
# 非常に重要

Ownerが過去Workflowを整理済み。

現在:

```text
ComfyUIPortable/workflows/
└ Archive/
   └ 過去研究Workflow群
```

となっている。

この整理を戻さない。

---

# 3. M1以降のWorkflowルール

`workflows/` 直下は:

```text
現在ユーザーが触るCanonical Workflowだけ
```

とする。

M1では原則1本だけ新規作成。

推奨名:

```text
ComfyUIPortable/workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json
```

追加してよい:

```text
ComfyUIPortable/workflows/README.md
```

READMEには:

```text
root = active/current
Archive = historical research
```

と短く明記。

---

# 4. 禁止 — Workflow増殖

以下のような増殖をしない。

```text
M1_A.json
M1_B.json
M1_C.json
M1_SWAP.json
M1_SEED42.json
M1_SEED43.json
...
```

検証条件は:

```text
同じCanonical Workflow
+
fixture/document/seed差替
+
automation script
```

で行う。

画像検証結果は:

```text
docs/verification/m1/
```

へ置く。

---

# 5. 過去Workflowの扱い

`workflows/Archive/` は:

```text
READ-ONLY REFERENCE
```

。

必要時だけ参照。

M1で優先して見るなら:

```text
Archive/01_BASIC_ILLUSTRIOUS_TXT2IMG.json
Archive/09_MANGA_REGIONAL_GENERATION_POC.json
```

程度。

旧54〜71等を全部再読解しない。

---

# 6. M1 Product Goal

最初の有用Draftを出す。

最小ユーザー導線:

```text
Resolution
↓
Style / Quality Template
↓
Scene Rectangle
↓
Scene Prompt
↓
Seed
↓
Generate
```

CASTなしで成立させる。

---

# 7. Simple Scene-only

M1で扱うSceneは:

```text
input_mode = "simple"
```

のみ。

Scene Prompt内に:

```text
人物
背景
演技
物
```

を自由に書いてよい。

例:

```text
school classroom, 1girl reading by the window
```

M1では人物説明をCASTへ分解しない。

---

# 8. CASTはM2

M1で作らない:

```text
CAST Master UI
Character Rectangle
Character Instance UI
Character LoRA UI
Interaction
Pose
```

契約上のfieldは保持するが、
Primary UIへ出さない。

---

# 9. Visual Panel Frameとの分離を維持

Semantic Scene Rectangleは:

```text
ここで何が起きるか
```

。

見える漫画コマ枠ではない。

M1 UIでScene矩形を描いたからといって:

```text
Visual Panel Frameを自動作成
Scene ID == Frame ID
```

にしない。

---

# 10. M1 Backend方針

M1の第一候補は:

```text
TEGAKI_AUTHORING_DOCUMENT
↓
semantic execution bridge
↓
existing PAGE_COMPILE_PLAN
↓
existing TegakiMangaConditioningBuilder
↓
ComfyUI Core KSampler
```

とする。

理由:

- Scene areaをsemantic maskとして直接使える
- Visual Panel Frameを必要としない
- Impact/PANEL_LAYOUT_SPECへSceneを偽装しなくてよい
- M1 simple modeには十分薄い
- 既存Core Conditioning Builderを再利用できる

---

# 11. M1でImpactをPrimaryにしない

現行:

```text
TegakiMangaImpactRegionalAdapter
```

は `PANEL_LAYOUT_SPEC` をscene mask境界に使う。

M1の新契約では:

```text
Semantic Scene
≠
Visual Frame
```

なので、

```text
Scene areaをPANEL_LAYOUT_SPECへ偽装
```

してImpact mainlineへ通さない。

M1 Primary BackendはCore masked conditioningから試す。

---

# 12. Core backendが失敗した場合

2-Scene visual oracleでlocalityが実用にならない場合:

```text
M1 FAIL/HOLD
```

とする。

その場で巨大なImpact再実装へ逸脱しない。

Reportへ:

```text
Core masked conditioning insufficient
```

と書き、
次Correction CardでBackend Adapterを検討する。

---

# 13. Authoring Execution Bridge

M0.1の:

```text
export_regions_to_legacy()
```

はsemantic-only bridgeとして使える。

M1ではこれを利用してもよい。

ただし:

```text
Visual Frames are not represented
```

をDebug/Reportで明記。

---

# 14. Bridgeの責務

必要なら新規:

```text
authoring_execution_bridge.py
```

を追加。

目的:

```text
TEGAKI_AUTHORING_DOCUMENT
→ validated simple-scene execution data
```

だけ。

M1でBackend objectsをpersistent documentへ書かない。

---

# 15. 推奨ComfyUI Node

候補名:

```text
TegakiMinimumHandSceneEditor
```

または:

```text
TegakiMangaSceneDraftEditor
```

既存命名と衝突確認後に決定。

---

# 16. EditorのSSOT

UIの編集正本は必ず:

```text
TEGAKI_AUTHORING_DOCUMENT
```

。

JSだけに別stateを持たない。

Workflow保存時に:

```text
document JSON
```

が保存され、
再読込で同じScene/Prompt/Seedを復元する。

---

# 17. M1 Editorに見せるもの

初期表示:

```text
Resolution
Style Template
Scene Canvas
Scene selector / Add Scene
Selected Scene Prompt
Seed
```

程度。

Advanced technical controlsを出さない。

---

# 18. Resolution

最低限:

```text
Portrait 832x1216
Square 1024x1024
Landscape 1216x832
Custom
```

等。

具体preset名は既存運用に合わせて調整可。

Custom width/heightは:

```text
positive
generation compatible
```

でvalidate。

Authoring Contract自体を不要に64刻みへ変更しない。

UI上は64stepでもよい。

---

# 19. Style / Quality Template

M1は大量Presetを作らない。

最大:

```text
Manga Monochrome
Manga Color
Custom
```

程度。

実際のprompt stringは設定dataとして分離してよい。

---

# 20. Style Templateの役割

ユーザーが毎回:

```text
masterpiece
best quality
manga...
```

等を手入力しなくてよいこと。

Style Promptは:

```text
人物identityを含めない
特定Scene内容を含めない
```

。

---

# 21. Style Promptの初期参考

Archive/01の既存baselineには:

```text
masterpiece, best quality, ... manga frame ...
```

やNegative:

```text
worst quality, low quality, bad anatomy, bad hands,
missing fingers, extra digits, watermark, text
```

がある。

ただしM1では:

```text
1girl
solo
expressive pose
```

等のScene/人物内容はGlobal Templateへ入れない。

---

# 22. Template変更は破壊的にしない

ユーザーがStyle Promptを手編集した後、
dropdown変更だけで文章を勝手に消さない。

推奨:

```text
template_id
+
resolved style_prompt
```

。

必要なら:

```text
Apply Template
```

を明示操作にする。

---

# 23. Scene Canvas

M1で必要:

- Scene rectangle追加
- Scene選択
- drag移動
- 四隅または辺でresize
- delete
- duplicateは任意
- overlap許可

---

# 24. Scene操作はM0 operationを尊重

Scene-onlyなのでCharacter Instanceはまだ無いが、
新UIのgeometry operationはM0 contract:

```text
page-normalized coordinates
```

を直接扱う。

旧KOMA-localへ戻さない。

---

# 25. Scene数

固定6枠に戻さない。

M1実装では少なくとも:

```text
1
2
4
```

Sceneを扱えること。

内部は可変配列。

---

# 26. Scene 0件

編集状態として:

```text
0 Scene
```

は保存可。

Generate時:

```text
Sceneを追加してください
```

でfail clearly。

勝手に全画面Sceneを作らない。

---

# 27. Selected Scene Inspector

M1で見せる最低限:

```text
Scene Name
Prompt
```

Negative Promptは:

```text
Advanced ▸
```

でもよい。

---

# 28. Prompt入力

Scene切替前に入力内容を必ずdocumentへ同期。

```text
click Scene 1
type
click Scene 2
click Scene 1
```

で文章が消えない。

---

# 29. Undo

M1で専用Undo stackを新作する必要はない。

ただしBrowser編集で:

```text
drag失敗
selection変更
prompt切替
```

によりdocumentを壊さない。

既存ComfyUI undoへ安全に乗れるなら利用。

難しい場合はM1 Reportへ明記してM4へDEFER。

---

# 30. Seed

Seedは:

```text
page.generation.seed
```

等、Authoring Documentへ保存する。

M1 UIで:

```text
Seed number
Randomize
Reuse current
```

の最低限を提供。

---

# 31. Seedは正式なCreative Feature

M1検証では:

```text
同じScene geometry
同じPrompt
異なるSeed
```

で生成を比較。

目標:

```text
大まかなScene割当は残る
細部・人物姿勢・背景等は変わる
```

。

---

# 32. KSamplerへのSeed

Authoring EditorまたはBridgeから:

```text
INT seed
```

を出力し、
Canonical WorkflowのKSamplerへ接続してよい。

Seedの正本を二重管理しない。

---

# 33. Style Prompt Composition

Simple Scene regionのPositiveは概念的に:

```text
Style Prompt
+
Scene Prompt
```

。

Negative:

```text
Style Negative
+
Scene Negative
```

。

---

# 34. GlobalとRegionalの二重責務

禁止:

```text
Globalに全Scene文章を連結
```

。

Globalはstyle / quality中心。

各Scene内容はそのScene maskへ。

---

# 35. Scene Mask

Scene.area:

```text
page normalized rect
```

から直接mask化。

M1では:

```text
strict containment
panel clipping
```

を要求しない。

Scene同士はoverlap可。

---

# 36. Overlap Policy

M0でorder persistenceは成立しているが、
runtime overlap semanticsは未確定。

M1 UIで:

```text
priority slider
blend mode
complex feather
```

を前面に出さない。

M1 visual oracleは非overlap Sceneを主に使う。

---

# 37. Mask Preview

M1では必須。

ユーザー/AIが:

```text
どのSceneがどこに効くか
```

を確認できるpreviewを出す。

色分け:

```text
Scene 1
Scene 2
...
```

程度。

---

# 38. Mask PreviewはPanel Frameではない

Previewに矩形線が見えても:

```text
生成画像へ見えるコマ線を入れるControl
```

とは呼ばない。

Label:

```text
Scene Regions Preview
```

等。

---

# 39. Visual Panel / ControlNet Guide

M1のCore GO条件には:

```text
本格Panel ControlNet
```

を入れない。

理由:

M1の第一目的は:

```text
Scene-only semantic draft
```

だから。

---

# 40. Optional Guide Path

既存ControlNet経路を新custom codeなしで安全に再利用できるなら、
Canonical Workflow内に:

```text
OPTIONAL / INTERNAL — Frame Guide
```

groupとして置いてよい。

Default:

```text
OFF / bypass
```

。

---

# 41. Optional Guideで禁止

M1のために:

```text
新ControlNet framework
新Panel topology engine
新Pose guide
```

を作らない。

Guideが簡単に繋がらなければ:

```text
DEFERRED
```

でよい。

M3でRough Guideを扱う。

---

# 42. Canonical Workflow

新規:

```text
workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json
```

。

目的:

```text
ロードして
Sceneを触って
Promptを書いて
Seedを変えて
Queueすれば
画像が出る
```

。

---

# 43. Canonical Workflowの見た目

ユーザー作業領域:

```text
LEFT / TOP:
Minimum-Hand Scene Editor

RIGHT:
Output Preview / Save
```

Backend nodes:

```text
INTERNAL — DO NOT TOUCH
```

groupへまとめる。

---

# 44. Backend Nodeの見せ方

内部:

```text
Checkpoint
optional Hyper-SDXL
Authoring Bridge
Page Compiler
Conditioning Builder
Latent
KSampler
VAE Decode
Save
```

など。

ユーザーに初見で編集させない。

---

# 45. Fast Draft Profile

M1 Operational候補:

```text
fast_draft_12
```

。

既存generation_profileを再利用。

Hyper-SDXL assetが実環境で見つからない場合は
勝手に別LoRAへ置換しない。

---

# 46. Fallback Profile

Fast Draft依存が解決しない場合:

```text
reference
```

profileでM1成立を優先。

Reportへ:

```text
profile actually used
```

を明記。

---

# 47. Model

既存Illustrious/SDXL assetを使う。

Archive/01のcheckpoint名は参考にできるが、
実行開始時にローカルで実在するcheckpointを確認。

Reportへ:

```text
checkpoint filename
VAE
profile
LoRA
```

を記録。

---

# 48. M1 Runtime Test A
# One Scene

Document:

```text
1 Scene
full page or broad area
simple mode
```

。

実際に生成成功。

確認:

```text
runtime PASS
output image exists
```

。

---

# 49. M1 Runtime Test B
# Two Distinct Scenes

同一pageに非overlap Sceneを2つ。

例:

```text
Scene A:
school classroom, windows, desks, a student reading

Scene B:
outdoor train platform, bicycle, a student waiting
```

必要なら内容をより視覚的に区別できるよう変更可。

---

# 50. Test Bの目的

厳密pixel containmentではなく:

```text
Scene A content predominantly appears in A region
Scene B content predominantly appears in B region
```

を確認。

多少の境界越えはM1では許容。

---

# 51. M1 Runtime Test C
# Geometry Swap Oracle

Test Bと:

```text
same prompts
same seed
same style
same generation settings
```

。

変更するのは:

```text
Scene A area
Scene B area
```

のswapだけ。

期待:

```text
dominant semantic content swaps location
```

。

---

# 52. Geometry Swapの意味

これが通れば:

```text
Scene rectangle
→ regional conditioning locality
```

が実画像で効いている根拠になる。

Promptに:

```text
left
right
top
bottom
```

等の位置語を入れない。

---

# 53. M1 Runtime Test D
# Seed Brainstorm

Test Bのgeometry/promptを固定。

Seedのみ:

```text
Seed 1
Seed 2
Seed 3
```

程度変更。

---

# 54. Seed Brainstorm Acceptance

期待:

```text
各Sceneの大まかな意味位置は維持
+
姿勢/細部/背景/カメラ nuanceは変化
```

。

完全一致を求めない。

むしろ:

```text
揺らぎが存在する
```

ことも確認。

---

# 55. Seedの評価で過剰Controlを求めない

M1で:

```text
同じ人物Pose
同じ背景
同じカメラ
```

をSeed間で固定しようとしない。

それはProduct意図と逆。

---

# 56. 画像Evidence

最低限:

```text
A_one_scene.png
B_two_scene_seedX.png
C_swap_same_seed.png
D_seedY.png
E_seedZ.png
```

程度。

名前は実装に合わせてよい。

---

# 57. Contact Sheet

新規:

```text
docs/verification/m1/M1_SCENE_DRAFT_CONTACT_SHEET.png
```

。

表示:

```text
Condition
Seed
Scene geometry summary
```

。

---

# 58. Verification Manifest

新規:

```text
docs/verification/m1/M1_SCENE_DRAFT_MANIFEST.json
```

。

各condition:

```text
runtime_status
visual_status
review_method
seed
prompt_hash or prompt summary
geometry
output_path
```

。

---

# 59. Visual Provenance

実画像をGemini自身が実際に見た場合:

```text
review_method = DIRECT_IMAGE_INSPECTION
```

。

見ていない場合:

```text
visual_status = PENDING
review_method = NOT_REVIEWED
```

。

fake detector名、固定confidenceを付けない。

---

# 60. Visual StatusとRuntime Statusを分離

例:

```text
runtime_status = PASS
visual_status = FAIL
```

は許容。

「Queue成功したからScene locality PASS」としない。

---

# 61. Browser E2E
# M1では重要

今回は初のuser-facing editorなので、
可能なら実ComfyUI browserで確認。

最低限:

```text
1. Canonical Workflow load
2. Scene rectangle select
3. Scene rectangle drag
4. Scene resize
5. Scene Prompt edit
6. Scene切替
7. Seed変更
8. Save workflow
9. Reload workflow
10. geometry/prompt/seed persistence
11. Queue
12. output image
```

。

---

# 62. Browser E2EのTruth

実ブラウザで操作していない場合:

```text
BROWSER E2E = PENDING
```

。

pointer simulationやJS unit testを
live browser PASSと呼ばない。

---

# 63. M1 UI Hand Count

Reportで簡単に計測。

Canonical 2-Scene sampleから:

```text
Prompt変更
Seed変更
Generate
```

まで何操作か。

空白から2 Sceneを作る場合も概算。

---

# 64. Product Gate

目標:

```text
既存2 Scene sample
→ Promptを2つ編集
→ Seed選択
→ Generate
```

が迷わず行える。

---

# 65. M1で作らないUI

- CAST
- Character placement
- Pose
- SubScene
- Interaction
- Manual Mask
- Full A1111 skin
- Standalone SPA
- Comic Creator fork

---

# 66. A1111風Skin

依然として将来候補。

M1では:

```text
single clear authoring node
+
backend grouped away
```

でまず手数を測る。

これで不十分ならM4より前にsurface再評価可能。

---

# 67. Comic Creator

M1ではREFERENCEのまま。

コード流用を始めない。

---

# 68. New Authoring Editor JS

必要なら:

```text
web/js/minimum_hand_scene_editor.js
```

等を追加。

既存:

```text
tegaki_region_editor.js
panel_content_editor.js
```

からCanvas interaction patternを参考にしてよい。

ただし旧REGION_SPECをSSOTにしない。

---

# 69. JS state rule

hidden/widget JSON:

```text
TEGAKI_AUTHORING_DOCUMENT
```

を正本とする。

Canvas objectだけにstateを持たない。

---

# 70. Python node validation

Queue時は必ず:

```text
from_dict / validate_document
```

。

invalid:

```text
fail clearly
```

。

JSだけのvalidationを信頼しない。

---

# 71. M1 Simple-mode Validator

M1 execution bridgeは:

```text
all scenes input_mode == simple
```

を要求してよい。

M1 workflowでCAST mode documentを入れた場合:

```text
M1 does not support CAST yet
```

と明示fail。

---

# 72. 0 Scene Queue

Queue時:

```text
No scenes to generate
```

等でfail。

Editor state保存自体は許可。

---

# 73. No silent Scene cap

旧Legacy bridgeは6まで。

M1 UIは6固定にしない。

ただし現Backend bridgeが6制限なら:

```text
execution_limit
```

としてUI/Debugへ明示。

---

# 74. 6超の扱い

M1で7+ Sceneを生成できない場合:

```text
authoring document save = allowed
generation = explicit unsupported
```

。

勝手に6へ削るな。

---

# 75. Long prompt

M1ではtoken/chunk詳細UIは不要。

ただしBackendがPromptをtruncateする場合は
黙って隠さずdebugへ警告。

既存CLIP behaviorに従う。

---

# 76. Debug JSON

最低限:

```text
schema version
page resolution
scene count
scene IDs
scene areas
style template
seed
backend path
profile
warnings
```

。

---

# 77. Automated Tests

最低限:

```text
test_m1_scene_editor_document.py
test_m1_authoring_execution_bridge.py
test_m1_scene_mask_plan.py
```

等。

---

# 78. Test内容

Pure logic:

- blank document
- 1 Scene
- 2 Scene
- 4 Scene
- add/delete
- area persistence
- prompt persistence
- seed persistence
- style template resolution
- simple-only gate
- 0 Scene generation reject
- >backend limit explicit reject
- semantic bridge does not create VisualFrame
- Scene/Frame separation regression

---

# 79. M0 / M0.1 regression

既存:

```text
78 tests
```

をすべて再実行。

M1 testを追加しても旧testを削除しない。

---

# 80. Workflow regression policy

Archive配下を含め既存JSONがparseできること。

ただし:

```text
ArchiveをCurrentとしてload test
```

する必要はない。

---

# 81. Active Workflow Verification

`workflows/` 直下について:

```text
M1 canonical workflow
+
README
+
Archive directory
```

程度に保つ。

---

# 82. M1 Report

新規:

```text
ComfyUIPortable/docs/reports/M1_3M1_SCENE_ONLY_MINIMUM_HAND_DRAFT_REPORT.md
```

。

---

# 83. Report必須項目

```text
1. Baseline fixed SHA
2. Workflow root policy
3. New UI surface
4. Authoring Document persistence
5. Resolution UI
6. Style Template
7. Scene Canvas
8. Prompt Inspector
9. Seed flow
10. Execution bridge
11. Backend actually used
12. Model/profile actually used
13. One-scene runtime
14. Two-scene runtime
15. Geometry swap
16. Seed brainstorm
17. Browser E2E
18. Hand count
19. Visual evidence
20. Test summary
21. Known limitations
22. M2 recommendation
```

---

# 84. M1 Acceptance Gates

必須:

```text
M0/M0.1 REGRESSION:
PASS

AUTHORING DOCUMENT IS UI SSOT:
PASS

SIMPLE SCENE ONLY:
PASS

RESOLUTION:
PASS

STYLE TEMPLATE:
PASS

SCENE ADD/SELECT/MOVE/RESIZE:
PASS

SCENE PROMPT PERSISTENCE:
PASS

SEED PERSISTENCE:
PASS

0 SCENE FAIL-CLOSED:
PASS

SCENE/FRAME SEPARATION:
PASS

ONE-SCENE RUNTIME:
PASS

TWO-SCENE RUNTIME:
PASS

GEOMETRY SWAP VISUAL:
PASS / PARTIAL / FAIL

SEED BRAINSTORM:
PASS / PARTIAL / FAIL

BROWSER E2E:
PASS / PENDING / FAIL

ACTIVE WORKFLOW COUNT:
1 canonical workflow

ARCHIVE RESTORED TO ROOT:
NO

CAST UI ADDED:
NO

POSE/INTERACTION ADDED:
NO
```

---

# 85. M1 Product PASS条件

最低限:

```text
ONE-SCENE RUNTIME = PASS
TWO-SCENE RUNTIME = PASS
GEOMETRY SWAP = PASS or defensible PARTIAL
SEED BRAINSTORM = PASS or defensible PARTIAL
```

。

Geometry swapが明確FAILなら:

```text
M1 HOLD
```

。

---

# 86. PARTIALを許す理由

M1の目標は:

```text
最小手でそれなりに誘導
```

であり、

```text
厳密な完全分離
```

ではない。

したがって:

- Scene境界を少し越える
- 背景が混ざる
- 人物の一部が領域を越える

だけでFAILにしない。

---

# 87. ただしFAILにするもの

以下はFAIL:

```text
Scene A/Bの内容がほぼ逆
geometry swapしても位置が変わらない
片方Scene promptがほぼ無視される
Seed variationで毎回localityが崩壊
```

。

---

# 88. Optional Frame Guide status

M1 Reportで:

```text
OPTIONAL FRAME GUIDE:
WIRED / DEFERRED
```

を明記。

DEFERREDでもM1 Core PASS可。

---

# 89. Next M2

M1成功後:

```text
M2 / 3M-2
CAST Master + Repeated Character Rough Placement
```

。

ここで初めて:

```text
Alice Master
Alice Instance
Character Rectangle
```

を追加。

---

# 90. M2へ持ち越す重要目標

M2では:

```text
同じCASTをScene 1 / 3 / 4へ置く
```

を最小手で実現。

M1のScene UIを壊さず拡張する。

---

# 91. Commit A

推奨:

```text
feat(manga): add scene-only minimum-hand draft workflow
```

含む:

- M1 editor/backend bridge
- JS
- tests
- single canonical workflow
- workflow README
- verification evidence
- M1 Report
- STATUS / DOCUMENT_REGISTER

---

# 92. Commit B

推奨:

```text
docs(manga): publish M1 review target
```

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current card = M1 completed / hold
Next = M2 or correction
```

。

---

# 93. Publication wording

現在remote mainへM0.1が存在する。

GITHUB_ComfyUIの:

```text
Local M0.1 Review Target
```

等の古い表現を
M1 Commit Bで現在事実へ直す。

---

# 94. Push

Owner運用に従う。

最終回答とEntryの:

```text
LOCAL ONLY / PUSHED
```

を一致させる。

---

# 95. 最終回答Format

```text
MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
0a1ccd46...

M1 IMPLEMENTATION COMMIT A:
M1 NAVIGATION COMMIT B:
PUSH STATUS:

CANONICAL WORKFLOW:
ACTIVE WORKFLOW COUNT:

AUTHORING EDITOR:
AUTHORING DOCUMENT SSOT:
RESOLUTION:
STYLE TEMPLATE:
SCENE CANVAS:
PROMPT INSPECTOR:
SEED FLOW:

EXECUTION BRIDGE:
BACKEND PATH:
MODEL:
PROFILE:

ONE SCENE RUNTIME:
TWO SCENE RUNTIME:
GEOMETRY SWAP:
SEED BRAINSTORM:
OPTIONAL FRAME GUIDE:

BROWSER E2E:
HAND COUNT:

OLD M0/M0.1 TESTS:
NEW M1 TESTS:
TOTAL:

VISUAL MANIFEST:
CONTACT SHEET:
M1 REPORT:

M1 STATUS:
PASS / PARTIAL / HOLD

NEXT RECOMMENDED CARD:
M2 / correction

USER ACTION REQUIRED:
```

---

# 96. 最終原則

M1で証明するものは:

```text
少ない操作
+
粗いScene領域
+
Prompt
+
Seed
=
実用的なDraftの入口
```

。

まだ証明しなくてよいもの:

```text
CAST identity
Character placement
Pose
Interaction
SubScene
Strict panel framing
```

。

Workflow整理を維持し、
過去研究Workflowを再びrootへ並べない。

M1完了後、Web GPTが固定Review Targetを確認してからM2へ進む。
