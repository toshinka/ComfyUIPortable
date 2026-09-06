# ComfyUI Portable — M1.1 / Phase 3M-1.1
# Canonical Workflow Wiring & UI SSOT Truth Fix
## Antigravity2 / Gemini 3.8 向け Bounded Correction Card

## 推奨モデル

```text
Gemini 3.8
```

M1の基本方針とCore regional generationは維持する。

今回の目的は、

```text
「Verification Scriptでは動く」
```

から、

```text
「ユーザーがCanonical Workflowを開いて、
Editor上のResolution / Scene / Prompt / Seedを触れば、
その値が本当に生成へ届く」
```

へ閉じることである。

CAST / Character Stagingへはまだ進まない。

---

# 0. 最初に読むもの

必ず最初に:

```text
ComfyUIPortable/GITHUB.TXT
```

を読み、canonical entryへのpointerを確認。

次に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

を読む。

本Card発行時の固定Review Target:

```text
c9a8dc1b937b97866a49ff41affc929a1fb8f9a3
```

M1 Navigation Commit:

```text
644569296625e009eb952dbaecf91e4ba348554d
```

moving mainではなく、まず固定M1実装SHAを基準に監査すること。

---

# 1. Web GPT Review Verdict

M1は全面FAILではない。

以下は成立した。

```text
M1 Authoring Contract integration:
PASS

Scene-only execution bridge:
PASS

Core masked conditioning backend:
PASS

1-scene runtime:
PASS

2-scene runtime:
PASS

Geometry swap backend oracle:
PASS / strong evidence

Seed variation backend capability:
PASS

Canonical user-facing workflow wiring:
HOLD

Browser UX truth:
PENDING
```

したがって:

```text
M1 Architecture:
ACCEPT

M1 Product Integration:
ACCEPT WITH REQUIRED WIRING FIX

M2:
HOLD

Next:
M1.1
```

---

# 2. 重要 — M1で何が実証されたか

`run_m1_verification.py` は実際にComfyUI APIへqueueし、

```text
document
seed
latent width
latent height
```

をPrompt Workflowへ直接設定している。

したがってM1画像群は、

```text
Core Scene Semantic Backendが動く
Scene geometry swapに因果性がある
Seed variationで画像が変化する
```

という証拠として有効。

このEvidenceを捨てない。

---

# 3. ただしVerification ScriptはCanonical Workflowそのものではない

現在のVerification Runnerでは概ね:

```python
KSampler.seed = seed
EmptyLatentImage.width = w
EmptyLatentImage.height = h
```

をscript側で直接設定している。

そのため、

```text
Editorのseed output
Editorのwidth output
Editorのheight output
```

が実際のCanonical Workflow生成へ届くことは証明していない。

M1.1はここを閉じる。

---

# 4. Finding A — Seed outputがKSamplerへ接続されていない
# BLOCKER

現在:

```text
TegakiMinimumHandSceneEditor
output: seed
```

はCanonical Workflowで未接続。

KSampler側は:

```text
seed = 42
control_after_generate = fixed
```

のwidget値を使っている。

つまりユーザーがEditorのSeedを変更しても、
Canonical Workflowの実画像Seedは変わらない。

---

# 5. Seed Wiring修正

Canonical Workflowで:

```text
Editor.seed
↓
KSampler.seed
```

を実接続する。

第一候補:

```text
ComfyUI native widget-to-input conversion
```

。

既存Core nodeだけで可能なら新Samplerを作らない。

どうしてもCore KSampler seed widgetへ直接link不能な場合のみ、
最小wrapper / native primitive利用を比較して最も薄い方法を選ぶ。

---

# 6. Seed SSOT

最終的なSeedの正本は:

```text
TEGAKI_AUTHORING_DOCUMENT
page.generation.seed
```

。

Editorに表示するSeed controlは
このfieldを編集するAuthoring Control。

Backend output:

```text
seed
```

はDocumentから導出する。

---

# 7. 禁止 — 二重Seed正本

以下を許可しない。

```text
document seed = 101
Editor widget seed = 101
KSampler widget seed = 42
```

。

Queue時に実際に使われたSeedをdebugへ必ず出す。

---

# 8. Finding B — Width / Height outputsがLatentへ接続されていない
# BLOCKER

現在Canonical Workflowの:

```text
EmptyLatentImage
```

は:

```text
832 x 1216
```

固定。

Editorが:

```text
1216 x 832
1024 x 1024
```

を出してもLatentへ届かない。

---

# 9. Resolution Wiring修正

Canonical Workflow:

```text
Editor.width
↓
EmptyLatentImage.width

Editor.height
↓
EmptyLatentImage.height
```

を実接続。

Core widget-to-input conversionを優先。

---

# 10. Resolution E2E

最低限以下を実生成。

```text
Portrait 832x1216
Landscape 1216x832
Square 1024x1024
```

。

確認:

```text
Authoring Document resolution
==
PAGE_COMPILE_PLAN canvas
==
EmptyLatent resolution
==
actual output PNG dimensions
```

。

---

# 11. Finding C — JSとPythonでAuthoring Document shapeが違う
# BLOCKER

Python canonical contract:

```json
{
  "page_id": "...",
  "width_px": 832,
  "height_px": 1216
}
```

。

一方M1 JSの`createDefaultDoc()`と
Canonical Workflow内のdocument_jsonは:

```json
{
  "dimensions": {
    "width_px": 832,
    "height_px": 1216
  }
}
```

を使っている。

これは同じDocumentに2 dialectが存在する状態。

---

# 12. Canonical Page Shapeを一本化

唯一の正本:

```text
page.width_px
page.height_px
```

。

削除 / 使用停止:

```text
page.dimensions.width_px
page.dimensions.height_px
```

。

---

# 13. 修正箇所

最低限:

```text
web/js/minimum_hand_scene_editor.js
  createDefaultDoc()
  syncToWidgets()
  resolution callback
  Reset 2-Scene

workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json
  document_json fixture
```

。

Python:

```text
minimum_hand_scene_editor.py
```

と完全に同じContractを使う。

---

# 14. Canonical Workflow document_json自体をvalidateする

M1.1 automated testで:

```text
workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json
↓
TegakiMinimumHandSceneEditor.document_json
↓
json.loads
↓
validate_document()
```

を実行。

Backendが後で補正しないとvalidにならないfixtureは禁止。

---

# 15. Finding D — document_jsonがSSOTなのにBackend Widget Overrideが存在する
# MAJOR

現在Python nodeは:

```text
document_json
+
seed widget
+
style_template widget
+
resolution widget
```

を受け取り、

Queue時にresolution / seed等でDocumentを書き換える。

これは実用上動くが、

```text
TEGAKI_AUTHORING_DOCUMENT is the single source of truth
```

というM1の主張と緊張する。

---

# 16. M1.1でSSOTを明確化する

推奨構造:

```text
Authoring Controls
↓
TEGAKI_AUTHORING_DOCUMENT
↓
Node execution derives seed / width / height / prompts
```

。

つまり:

```text
UI controlはDocumentを編集する
Execution parameterはDocumentから読む
```

。

---

# 17. 実装方式の選択

最も単純な方法を選んでよい。

## Option A — 推奨

Resolution / Style / Seed controlsを
Custom DOM Authoring UI内へ置き、

```text
document_json
```

だけをserver側Authoring input正本とする。

Server nodeは:

```text
document_json
→ validate
→ derive seed,width,height,plan
```

。

## Option B

既存native widgetsを残す。

ただし:

```text
widget change
→ immediately writes document_json
```

を保証し、

Queue backendでは
Documentとwidgetに不一致があればsilent overrideせず
explicit diagnostic / synchronization policyを持つ。

---

# 18. SSOT Acceptance

最終的に:

```text
Save workflow
Reload workflow
Queue
```

した時、

```text
表示されるResolution
表示されるStyle
表示されるSeed
表示されるScene geometry
表示されるPrompt
```

がDocument JSONと一致すること。

---

# 19. Finding E — Reset 2-Sceneが非Canonical documentを作る
# BLOCKER

JS `Reset 2-Scene` はJS版`createDefaultDoc()`を使うため、
現状では`dimensions` dialectへ戻る。

修正後:

```text
Reset
→ valid TEGAKI_AUTHORING_DOCUMENT
```

。

そのままQueue可能であること。

---

# 20. Finding F — Resolution callbackのContract mismatch
# BLOCKER

現JS:

```javascript
p.dimensions.width_px = ...
p.dimensions.height_px = ...
```

。

修正:

```javascript
p.width_px = ...
p.height_px = ...
```

。

---

# 21. Finding G — Add Scene ID衝突
# MAJOR

現状:

```javascript
const count = scenes.length + 1;
const newId = `scene_${count}`;
```

。

中間Sceneを削除後に追加すると、
既存`scene_3`, `scene_4`等と衝突し得る。

M2ではCharacter InstanceがScene IDを参照するため、
ここは今直す。

---

# 22. Stable Scene ID生成

以下のいずれか。

推奨:

```text
existing IDsを走査し未使用IDを生成
```

または:

```text
UUID-based scene ID
```

。

要件:

```text
delete middle scene
→ add scene
→ no duplicate
```

。

Scene orderとScene identityを分ける。

---

# 23. Scene label ≠ ID

UI表示:

```text
Scene 1
Scene 2
```

はorder / label。

永続identity:

```text
scene_id
```

は並べ替えやdelete/addで安易に再利用しない。

---

# 24. Finding H — Custom Resolutionが実質未完成
# MAJOR

UI optionには:

```text
Custom
```

があるが、
M1ではwidth / heightを編集するUser-facing controlが無い。

JS `parseResolution("Custom")` は
実質defaultへfallbackする。

---

# 25. Custom Resolution方針

二択。

## 推奨

M1.1でCustom width / height fieldsを追加。

例:

```text
Width
Height
```

。

入力は:

```text
positive integer
generation-safe
```

。

UIは64 stepにしてよいが、
Authoring Contract自体を64 multiple限定へ変更しない。

## 代替

M1.1ではCustomをUI選択肢から削除し:

```text
Deferred
```

と正直にする。

「Customがあるが使えない」は禁止。

---

# 26. Style Template

Manga Monochrome / Manga Color切替について:

```text
UI selection
↓
page.metadata.style_template
page.style_prompt
page.style_negative_prompt
```

の同期を確認。

---

# 27. Custom Style

現`Custom` optionも同様にtruthfulにする。

Custom選択時にstyle promptを編集するUIが無いなら:

```text
A. style prompt fieldをAdvancedとして追加
B. Custom optionを一旦外す
```

のどちらか。

未完成optionを残さない。

---

# 28. Canonical Workflow wiring test
# 必須

新規automated testでWorkflow JSONをparseし、
少なくとも以下をassert。

```text
1. root active workflowは1本
2. Editor page_compile_plan → ConditioningBuilder
3. Editor seed → actual sampler seed
4. Editor width → actual latent width
5. Editor height → actual latent height
6. Editor document_json validates without backend patch
7. no hidden second seed authority
8. no fixed latent resolution authority
```

。

---

# 29. API Prompt VerificationもCanonical wiringへ寄せる

現在`run_m1_verification.py`は
seed / width / heightを直接複製している。

M1.1では可能な限り:

```python
"seed": ["1", 2]
"width": ["1", 3]
"height": ["1", 4]
```

のように、

```text
Editor output
```

を実execution inputへ接続する。

ComfyUI API contract上別の表現が必要なら
実際に使える方法へ調整。

---

# 30. Verification Runnerの原則

禁止:

```text
Editor says Seed 101
Runner independently sets KSampler 101
```

だけでSeed wiring PASSとすること。

必ず:

```text
Editor output is the causal source
```

を実証。

---

# 31. Browser E2E
# BLOCKER

M1 ReportではBrowser E2Eの明示結果が無い。

M1.1では実ブラウザ確認必須。

---

# 32. Browser E2E Scenario A — Persistence

Canonical Workflowを開き:

```text
Scene 1 prompt変更
Scene 2 prompt変更
Scene 1へ戻る
```

。

確認:

```text
text preserved
```

。

その後:

```text
Save workflow
Reload
```

。

確認:

```text
prompt
scene geometry
seed
style
resolution
```

が一致。

---

# 33. Browser E2E Scenario B — Geometry

実ブラウザで:

```text
select
drag
resize
```

。

document_jsonを確認し:

```text
page-normalized area
```

が変化。

Queue後preview / generated image pathが正常。

---

# 34. Browser E2E Scenario C — Seed

同一Document:

```text
seed 42
→ Queue
seed 101
→ Queue
```

。

確認:

```text
actual KSampler received seed 42 / 101
output files differ
debug seed matches
```

。

---

# 35. Browser E2E Scenario D — Resolution

```text
Portrait
→ Queue

Landscape
→ Queue
```

。

確認:

```text
actual output PNG dimensions
832x1216
1216x832
```

。

---

# 36. Browser E2E Scenario E — Reset

Sceneを編集後:

```text
Reset 2-Scene
→ Queue
```

。

確認:

```text
no schema validation error
```

。

---

# 37. Browser E2E Scenario F — ID Collision

4 Scenes作成。

```text
Scene 2またはScene 3を削除
↓
Add Scene
```

。

確認:

```text
all scene_id unique
validate_document PASS
```

。

---

# 38. Browser E2E Truth

本当にブラウザ操作していないものを:

```text
PASS
```

にしない。

不能なら:

```text
BROWSER E2E = PENDING
```

でM2 HOLD。

---

# 39. Hand Count

M1 Cardで要求していたがReportに実質記録が無い。

M1.1で最低限:

```text
Canonical sampleから
Prompt変更
Seed変更
Generate
```

までの操作数を記録。

また:

```text
empty-ish stateから
2 Scene draft生成
```

までの概算も記録。

---

# 40. Manifest Provenance
# REQUIRED CORRECTION

現Manifestは各conditionに:

```text
status: PASS
provenance: LIVE_COMFYUI_GENERATION
```

のみ。

これはruntimeとvisualを分けていない。

---

# 41. Manifest v2

各condition最低限:

```json
{
  "runtime_status": "PASS",
  "visual_status": "PASS|PARTIAL|FAIL|PENDING",
  "review_method": "DIRECT_IMAGE_INSPECTION|NOT_REVIEWED",
  "visual_notes": "...",
  "seed": 42,
  "resolution": "832x1216",
  "output_path": "..."
}
```

。

---

# 42. 自動PASS禁止

Runnerは:

```text
generation succeeded
```

なら:

```text
runtime_status = PASS
```

にしてよい。

しかし自動で:

```text
visual_status = PASS
```

にしない。

Visualは実目視後に記録。

---

# 43. Existing M1 Images

既存5画像は削除不要。

M1.1 Reportでは:

```text
M1 backend semantic evidence
```

として利用可。

必要ならManifest v2へ目視結果を移記。

---

# 44. M1.1新規Generationは最小限

Core semantic imagesを全部再生成する必要はない。

M1.1ではwiring proofとして最低限:

```text
W1 Seed 42
W2 Seed 101
W3 Landscape
```

程度でよい。

必要ならSquare追加。

---

# 45. Image content再評価の主眼

M1.1の目的は:

```text
semantic quality benchmark
```

ではない。

確認対象:

```text
Seed actually changed
Resolution actually changed
Canonical UI path actually controls generation
```

。

---

# 46. Report Truth Correction

既存M1 Reportは削除・改竄しない。

新規:

```text
docs/reports/M1_1_CANONICAL_WORKFLOW_WIRING_REPORT.md
```

を正本Correctionとして追加。

---

# 47. M1.1 Reportで明記

```text
Original M1 proved backend semantic locality.
Web review found canonical workflow wiring defects:
- seed disconnected
- width/height disconnected
- JS/Python resolution schema mismatch
- browser E2E unproven
- manifest runtime/visual conflated
```

。

その後修正結果を書く。

---

# 48. M1 statusの表現

修正前を:

```text
M1 Core Backend:
PASS

M1 Canonical Workflow:
PARTIAL
```

と記録。

M1.1成功後:

```text
M1 Product Path:
PASS
```

へ更新可。

---

# 49. M1.1 Automated Tests

既存98 testsを全部維持。

追加候補:

```text
test_m1_1_canonical_workflow_wiring.py
test_m1_1_authoring_ui_contract_fixture.py
test_m1_1_scene_id_uniqueness.py
```

。

---

# 50. 必須Test

少なくとも:

```text
canonical workflow document validates
no page.dimensions legacy dialect
seed output is causally wired
width output is causally wired
height output is causally wired
Reset fixture validates
delete-middle + add => unique IDs
resolution change persists
style change persists
seed change persists
```

。

---

# 51. JS Testについて

可能なら軽量JS test / harnessを使う。

ただしBrowser E2Eの代用とは呼ばない。

---

# 52. Workflow Root Policy

引き続き:

```text
workflows/
├ M1_MINIMUM_HAND_SCENE_DRAFT.json
├ README.md
└ Archive/
```

。

M1.1用Workflowを別名で増やさない。

同じCanonical Workflowを修正。

---

# 53. Archive

```text
workflows/Archive/
```

は変更しない。

---

# 54. M2へ進まない

今回追加禁止:

```text
CAST Master UI
Character Rectangle
Character LoRA
Character assignment
Pose
Interaction
SubScene
ControlNet
Panel Frame
```

。

---

# 55. Optional Frame Guide

M1.1でも不要。

---

# 56. Backend

Core masked conditioning路線を維持。

Impactへ切り替えない。

---

# 57. Scene semantic behavior

既存Geometry Swap Evidenceを維持。

M1.1でlocalityを過剰に再調整しない。

---

# 58. Canonical Node UI

M1.1後のUser-facing surfaceは最低限:

```text
Resolution
Style
Seed
Scene Canvas
Selected Scene Prompt
Add / Remove / Reset
```

。

どの値もDocumentに保存されること。

---

# 59. Debug JSON

Queue時に最低限:

```text
document seed
effective sampler seed
document width/height
effective latent width/height
style template
scene IDs
scene areas
```

を確認可能にする。

---

# 60. Effective runtime truth

可能なら:

```text
effective_sampler_seed
effective_latent_width
effective_latent_height
```

をdebugへ明示。

これはM2以降の診断にも役立つ。

---

# 61. M1.1 Acceptance Gates

```text
M0/M0.1/M1 OLD TESTS:
ALL PASS

CANONICAL DOCUMENT VALID BEFORE BACKEND PATCH:
PASS

JS/PYTHON PAGE SHAPE:
ONE DIALECT ONLY

PAGE.DIMENSIONS LEGACY FIELD:
ABSENT

SEED UI → DOCUMENT:
PASS

DOCUMENT SEED → SAMPLER:
PASS

RESOLUTION UI → DOCUMENT:
PASS

DOCUMENT WIDTH/HEIGHT → LATENT:
PASS

STYLE UI → DOCUMENT:
PASS

CUSTOM RESOLUTION:
IMPLEMENTED / HONESTLY DEFERRED

CUSTOM STYLE:
IMPLEMENTED / HONESTLY DEFERRED

RESET 2-SCENE:
VALID DOCUMENT

SCENE ID UNIQUENESS:
PASS

WORKFLOW ROOT ACTIVE COUNT:
1

BROWSER PROMPT PERSISTENCE:
PASS

BROWSER GEOMETRY EDIT:
PASS

BROWSER SAVE/RELOAD:
PASS

BROWSER SEED E2E:
PASS

BROWSER RESOLUTION E2E:
PASS

MANIFEST RUNTIME/VISUAL SPLIT:
PASS

ARCHIVE MODIFIED:
NO

CAST ADDED:
NO
```

---

# 62. M2 GO条件

以下すべてPASS後のみ:

```text
M2 / 3M-2
Minimum Character & CAST Staging
```

へ進む。

特に:

```text
Seed
Resolution
Scene ID
Document persistence
```

が不安定な状態でCASTを載せない。

---

# 63. Commit A

推奨:

```text
fix(manga): wire M1 canonical authoring controls to generation
```

含む:

```text
minimum_hand_scene_editor.py
minimum_hand_scene_editor.js
canonical workflow
verification runner
tests
manifest v2 / wiring evidence
M1.1 report
STATUS / DOCUMENT_REGISTER
```

。

---

# 64. Commit B

推奨:

```text
docs(manga): publish M1.1 review target
```

。

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current Card = M1.1 completed
Next = M2 candidate
```

。

---

# 65. Publication wording

現在GitHub remoteからM1 Commit A / Bを取得できている。

`GITHUB_ComfyUI.txt`に残る:

```text
Local M1 Review Target
```

はremote事実と一致しない。

Commit Bで:

```text
Published on remote main
```

等へ訂正。

---

# 66. Push

Owner運用に従う。

最終回答:

```text
LOCAL ONLY
PUSHED
```

を実態と一致させる。

---

# 67. 最終回答フォーマット

```text
MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
c9a8dc1b937b97866a49ff41affc929a1fb8f9a3

M1.1 IMPLEMENTATION COMMIT A:
M1.1 NAVIGATION COMMIT B:
PUSH STATUS:

CANONICAL DOCUMENT VALID:
PAGE.DIMENSIONS REMOVED:
SEED DOCUMENT SYNC:
SEED SAMPLER WIRING:
RESOLUTION DOCUMENT SYNC:
WIDTH LATENT WIRING:
HEIGHT LATENT WIRING:
STYLE DOCUMENT SYNC:
CUSTOM RESOLUTION:
CUSTOM STYLE:
RESET VALIDITY:
SCENE ID UNIQUENESS:

CANONICAL WORKFLOW:
ACTIVE WORKFLOW COUNT:

BROWSER PROMPT PERSISTENCE:
BROWSER GEOMETRY:
BROWSER SAVE/RELOAD:
BROWSER SEED E2E:
BROWSER RESOLUTION E2E:
HAND COUNT:

OLD TESTS:
NEW TESTS:
TOTAL TESTS:

WIRING VERIFICATION:
MANIFEST V2:
M1.1 REPORT:

M1 PRODUCT PATH:
PASS / HOLD

M2 READY:
YES / NO

USER ACTION REQUIRED:
```

---

# 68. 最終原則

M1.1で直すのは画像品質ではない。

直すのは:

```text
見えているControl
=
保存されるAuthoring Data
=
Backendが実際に使う値
```

という一致。

特に:

```text
Editor Seed
→ actual KSampler Seed

Editor Resolution
→ actual Latent Resolution

JS Document
=
Python Contract
```

を必ず成立させる。

この3点が閉じてからM2 CASTへ進むこと。
