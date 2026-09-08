# ComfyUI Portable — M2B.2 / Phase 3M-2B.2
# Live UI Bootstrap, Widget Serialization & Owner Workflow Repair
## — Custom DOMを実際に起動し、Canonical Workflowのwidgetずれを修復する —
## Antigravity2 / Gemini 3.8 向け Bounded Correction Card

## 推奨モデル

```text
Gemini 3.8 STANDARD / HIGH
```

今回はLOWを使わないことを推奨する。

理由は能力研究ではなく、

```text
ComfyUI frontend module path
widget auto-generation
workflow serialization
live browser compatibility
```

という実ブラウザ統合境界を扱うため。

ただし、今回見つかった主要不具合はLOWが新しく作ったものではない。
少なくともCustom UIの`app.js` import path誤りはM1時点から存在していた。
主因は「Live Browserが長くPENDINGのまま、headless/backend evidenceでProduct UIを推定していたこと」。

---

# 0. このCardの目的

M2B.1のBackend/CAST semanticsは維持する。

しかしOwnerがCanonical Workflowを実ブラウザで開いた結果、

```text
1. Product Custom DOMが表示されない
2. Raw document_json widgetだけが巨大表示される
3. seedの後に「生成後の制御 / control_after_generate」が追加される
4. style_templateに "Portrait 832x1216" がずれて入る
5. Queue時に Invalid Input
```

が実際に確認された。

したがってOwner Manual Browser Checkの結果は:

```text
LIVE BROWSER PRODUCT E2E = FAIL
```

であり、M3へは進まない。

今回の目的:

```text
Custom UI module load
+
native widget serialization stability
+
Canonical Workflow load/queue
+
CAST UI visibility
```

を先に閉じる。

---

# 1. 最初に必ず読むもの

順序厳守。

```text
ComfyUIPortable/GITHUB.TXT
```

次に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

本Card発行時のReview Target:

```text
1b3bd2246c6a2f440d7a7f810a8a75a798fb9bc2
```

M2B.1 Navigation Commit:

```text
4bc82536b3d15a42d4e45fb9496b3a3a7733040d
```

本Card発行時点で両Commitはremote `main`へ存在する。

---

# 2. Web GPT Review Verdict

```text
M2B.1 CAST selection semantics:
PASS structurally

M2B.1 Backend runtime:
PASS

M2B.1 Headless tests:
PASS

M2B.1 Live Browser:
FAIL (Owner observed)

M2B.1 Product Path:
HOLD

M3:
HOLD

Next:
M2B.2
```

---

# 3. Owner Live Browser Evidence

Ownerが実際に:

```text
workflows/MINIMUM_HAND_MANGA_DRAFT.json
```

をComfyUIでロード。

観察:

```text
Tegaki Minimum-Hand Manga Authoring (Draft)
```

nodeにProduct Custom UIが出ず、

```text
巨大なdocument_json
seed
control_after_generate
style_template
resolution
```

だけが表示された。

さらに:

```text
style_template = Portrait 832x1216
```

という不正状態になり、

```text
Invalid Input:
style_template に Portrait 832x1216 は使用できない
```

でQueueが停止。

これは今回の最優先再現条件。

---

# 4. Root Cause A — Frontend app import path
# BLOCKER

現在の:

```text
custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js
```

先頭:

```javascript
import { app } from "../../scripts/app.js";
```

。

しかし同じpackageの既存稼働Editor:

```text
web/js/panel_content_editor.js
```

等は:

```javascript
import { app } from "../../../scripts/app.js";
```

を使用。

`WEB_DIRECTORY = "./web"` かつJSが `web/js/` にあるため、
Minimum-Hand Editorのimport pathは既存Extension patternと一致していない。

---

# 5. Root Cause A Fix

第一候補:

```javascript
import { app } from "../../../scripts/app.js";
```

へ修正。

既存のworking Tegaki extensionsと同じpath conventionへ揃える。

独自absolute path hackを作らない。

---

# 6. 重要 — このimport bugはM2B.1固有ではない

履歴確認上、M1 Review Target:

```text
c9a8dc1b937b97866a49ff41affc929a1fb8f9a3
```

時点でも:

```javascript
../../scripts/app.js
```

だった。

したがって:

```text
LOW modelでM2B.1を行ったからUIが崩れた
```

と単純化しない。

M1以降Custom DOM自体がLive Browserで未実証だった可能性が高い。

M2B.2 Reportに明記。

---

# 7. Root Cause A Acceptance

ComfyUI browser dev consoleで最低限:

```text
minimum_hand_scene_editor.js module load error = none
minimum_hand_authoring_ops.js load error = none
app.js 404 = none
```

。

Product nodeに:

```text
DRAFT header
Randomize Seed
CAST MASTER
Canvas
Scene Inspector
```

が表示される。

Custom DOM不在ならFAIL。

---

# 8. Root Cause B — seed auto control widget
# BLOCKER

`minimum_hand_scene_editor.py`では現在:

```python
"seed": ("INT", {
    "default": 42,
    "min": 0,
    "max": ...,
    "step": 1,
})
```

。

現行ComfyUI frontendではINT inputのnameが:

```text
seed
noise_seed
```

の場合、`control_after_generate`が未指定なら自動でcontrol widgetを追加する挙動がある。

Owner画面に表示された:

```text
生成後の制御
```

がこれ。

---

# 9. Why Widget Values Shift

Canonical WorkflowのEditor nodeは現在:

```json
"widgets_values": [
  document_json,
  42,
  "Manga Monochrome",
  "Portrait 832x1216"
]
```

の4値。

Live frontendでは実widget列が:

```text
document_json
seed
control_after_generate
style_template
resolution
```

の5個になる。

結果:

```text
document_json -> correct
seed -> 42
control_after_generate -> Manga Monochrome
style_template -> Portrait 832x1216
resolution -> default Portrait 832x1216
```

と1段ずれる。

Owner screenshotとInvalid Inputに完全一致する。

---

# 10. Root Cause B Fix
# 推奨

Seed controlはProduct独自の:

```text
Randomize Seed
+
page.generation.seed SSOT
```

を既に持つ。

よってPython INPUT_TYPESのseedに明示:

```python
"control_after_generate": False
```

を追加。

期待:

```text
document_json
seed
style_template
resolution
```

の4 native widgetsへ固定。

---

# 11. Seed input renameは原則しない

代替として:

```text
seed -> generation_seed
```

ならauto controlを避けられる可能性があるが、

```text
workflow
JS
tests
runner
wiring
```

への影響が大きい。

まず:

```python
control_after_generate: False
```

で直す。

---

# 12. Canonical Seed SSOTを維持

禁止:

```text
ComfyUI automatic randomize
+
Tegaki Randomize Seed
```

の二重authority。

M2B方針:

```text
page.generation.seed
→ Editor seed output
→ KSampler
```

を維持。

---

# 13. Canonical Workflow Repair
# BLOCKER

修正後に:

```text
workflows/MINIMUM_HAND_MANGA_DRAFT.json
```

を現在のnode schemaへ合わせて更新。

ただし手作業で値のindexだけ直して終わらない。

---

# 14. Live-save優先

可能なら:

```text
1. ComfyUI restart
2. browser hard reload
3. Canonical Workflow load
4. node values確認
5. Save Workflow
```

した実Workflow JSONをcanonicalへ採用。

Live frontendが実際にserializeした形を優先。

---

# 15. Workflow Widget Acceptance

Editor nodeの保存値が最低限:

```text
document_json = valid TEGAKI_AUTHORING_DOCUMENT
seed = 42
style_template = Manga Monochrome
resolution = Portrait 832x1216
```

。

以下は禁止:

```text
control_after_generate = Manga Monochrome
style_template = Portrait...
```

。

---

# 16. Static Workflow Regression Test

新規testでCanonical workflowのEditor nodeを読み:

```text
widgets_values[0] parses document
widgets_values[1] is integer seed
widgets_values[2] in STYLE_TEMPLATES
widgets_values[3] in RESOLUTION_PRESETS
```

をassert。

さらに:

```text
len == expected serialized user widgets
```

を確認。

---

# 17. INPUT_TYPES Regression Test

以下をassert:

```python
seed options["control_after_generate"] is False
```

。

ComfyUI frontend側のdefault挙動に再び依存しない。

---

# 18. Frontend Import Regression Test

最低限static test:

```text
minimum_hand_scene_editor.js
uses ../../../scripts/app.js
```

。

可能なら同packageの他frontend extensionsと同一root resolutionであることをcheck。

---

# 19. Better Frontend Smoke Harness
# 推奨

ComfyUI server起動時にHTTPで:

```text
/extensions/tegaki_manga_nodes/js/minimum_hand_scene_editor.js
/extensions/tegaki_manga_nodes/js/minimum_hand_authoring_ops.js
/scripts/app.js
```

が200で取得できることを確認。

ただし:

```text
HTTP 200 != module execution PASS
```

。

Live browser checkは別。

---

# 20. Root Cause C — Raw document_json on Product Surface
# PRODUCT BLOCKER

Owner screenshotではraw:

```text
TEGAKI_AUTHORING_DOCUMENT JSON
```

がnode面積の大半を占める。

Minimum-Hand Product UIとして不適切。

Custom DOMが起動しても、
raw JSONが主UIとして残るならProduct surfaceは煩雑。

---

# 21. document_jsonはInternal SSOTとして隠す

`document_json`は:

```text
保存・同期の正本
```

として保持。

しかし通常ユーザーには非表示またはcollapsed internal widget。

---

# 22. Hiding Requirements

方法は現ComfyUI frontendの安全な手法を調査して選択してよい。

要件:

```text
widget objectはJSから取得可能
value serializeされる
workflow save/reloadで保持
API executionへ送られる
画面では巨大textareaを占有しない
```

。

単にDOMから削除してserializationを壊さない。

---

# 23. Keep User-facing Native Controls

M2B.2では最低限:

```text
Seed
Style Template
Resolution
```

は見えてよい。

Custom DOMで完全置換する必要はない。

今回大規模UI redesignしない。

---

# 24. Expected Product Surface

OwnerがWorkflowをloadした直後:

```text
Tegaki Minimum-Hand Manga Authoring
------------------------------------
Seed / Style / Resolution
Randomize Seed
CAST MASTER
Canvas
Selected Scene
Selected Character
```

程度。

Raw JSONを読ませない。

---

# 25. CAST Semantics Fixは維持

M2B.1の:

```text
chooseCastForPlacement
selectedCastId
single CAST auto
multiple CAST selection required
same CAST repeated
```

を変更しない。

---

# 26. Ops moduleは維持

```text
minimum_hand_authoring_ops.js
```

のpure helper splitは採用。

今回のimport/bootstrap修正で戻さない。

---

# 27. Owner Browser EvidenceによりStatus更新

M2B.1 Reportの:

```text
LIVE_BROWSER = PENDING
```

は、Owner check後の現在は:

```text
LIVE_BROWSER = FAIL
```

。

M2B.2 ReportでCorrectionを明記。

---

# 28. Report Baseline SHA Correction
# REQUIRED

M2B.1 Reportには:

```text
Preceding Implementation Commit:
e676deb5df25d481412d26f63393437e408ec228
```

とあるが、このSHAはrepoで解決できない。

正しいM2B Commit A:

```text
e676deb53824b97c18058c3dd2fc20cb08d0f822
```

。

---

# 29. M2B Navigation Truth Correction

M2B.1 ReportではPreceding Navigationとして:

```text
0d6da8c147576c9a99db6b98316271eda3591bb3
```

を記載している。

実M2B Navigation Commitは:

```text
463ec8f92c79bfb25d2532a6227c7bb4941b3b69
```

。

`0d6da8c1`はその後の指示書publication commit。

混同を修正。

---

# 30. Current Publication Truth

本Card発行時remote main head:

```text
4bc82536b3d15a42d4e45fb9496b3a3a7733040d
```

。

したがって:

```text
M2B.1 Commit A/B = remote published
```

。

`LOCAL ONLY`と書かない。

---

# 31. Browser E2E — Mandatory Smoke A
# Load

修正後:

```text
ComfyUI server restart
browser hard reload (cache bypass)
load MINIMUM_HAND_MANGA_DRAFT.json
```

。

PASS:

```text
Custom DOM visible
No raw JSON dominating UI
No invalid combo values
No missing module
No fatal console error
```

。

---

# 32. Browser E2E — Mandatory Smoke B
# Native Widgets

確認:

```text
Seed = 42
Style = Manga Monochrome
Resolution = Portrait 832x1216
```

。

以下が存在しないこと:

```text
control_after_generate row
```

Product policy上不要。

---

# 33. Browser E2E — Mandatory Smoke C
# Queue Default

Workflowを変更せずQueue。

期待:

```text
No Invalid Input
generation starts
output image exists
```

。

---

# 34. Browser E2E — Mandatory Smoke D
# CAST UI

確認:

```text
CAST MASTER section visible
+ Add CAST visible
Canvas visible
Scene Inspector visible
```

。

---

# 35. Browser E2E — CAST Selection

Alice / Bob作成。

Bob select。

Scene 1:

```text
+ Place Bob
```

。

押下。

期待:

```text
Bob instance only
```

。

---

# 36. Browser E2E — No Selection

2 CAST状態。

selection解除。

Add Character。

期待:

```text
explicit selection required
no silent placement
```

。

---

# 37. Browser E2E — Character Box

Bob box:

```text
drag
resize
```

。

document SSOT更新。

---

# 38. Browser E2E — Save / Reload

最低限:

```text
CAST
identity prompt
scene
character assignment
areas
acting prompt
seed
style
resolution
```

を保存。

Reload後同一。

---

# 39. Browser E2E — Default Queue after Reload

Reload直後Queue。

Invalid Inputなし。

---

# 40. Live Browser Truth

Gemini側でbrowser automation不能なら:

```text
AGENT LIVE BROWSER = PENDING
```

。

しかし今回はOwnerが実ブラウザで確認するため、
Owner結果を明示的にReportへ反映する運用にする。

---

# 41. Owner Acceptance State

Commit時点でOwner再確認前なら:

```text
M2B.2 CODE FIX = COMPLETE
LIVE OWNER ACCEPTANCE = PENDING
M3 READY = NO
```

。

OwnerからPASS報告後にM3を発行する。

---

# 42. Do Not Fake Browser PASS

禁止:

```text
source grep
Node test
API runtime
static screenshot generator
```

だけで:

```text
LIVE BROWSER PASS
```

とすること。

---

# 43. Headless JS Test

既存13 testsを維持。

追加:

```text
app import path contract
selected CAST semantics regression
document JSON hidden-state serialization helper if added
```

。

---

# 44. Python Tests

既存165を維持。

追加最低限:

```text
seed control_after_generate=False
canonical workflow widget order/types
canonical document validates
default style/resolution values valid
```

。

---

# 45. Frontend Source-Coupled Test

可能ならproduction fileの実export/pure functionsを使用。

M2B.1で改善したsource couplingを維持。

---

# 46. Canonical Workflow Count

root:

```text
1 JSON
```

維持。

新たに:

```text
OWNER_CHECK.json
M2B2_TEST.json
```

等をrootへ増やさない。

---

# 47. Owner CheckはCanonicalそのもの

今回重要。

Owner用Workflowを別fixtureにしない。

```text
MINIMUM_HAND_MANGA_DRAFT.json
```

自体がload/queue可能であること。

---

# 48. Archive

変更しない。

---

# 49. Backend能力再研究は禁止

今回:

```text
2-character 8seed
depth benchmark
3-character benchmark
ControlNet strength
```

を再実施しない。

既存M2A.1結果を維持。

---

# 50. ControlNet / M3禁止

今回追加しない:

```text
Visual Panel Frame
ControlNet
Rough Dummy
Pose
Camera
LoRA UI
Candidate Browser
```

。

---

# 51. M2B.2 Report

新規:

```text
docs/reports/M2B2_LIVE_UI_BOOTSTRAP_AND_WORKFLOW_REPAIR_REPORT.md
```

。

---

# 52. Report必須項目

1. Fixed Review Target
2. Owner live failure evidence summary
3. M2B.1 status correction: PENDING -> FAIL
4. app import root cause
5. app import historical origin
6. seed control_after_generate root cause
7. workflow widget shift explanation
8. seed policy fix
9. canonical workflow repair
10. raw document_json visibility fix
11. CAST semantics regression
12. tests
13. backend smoke
14. browser agent status
15. owner acceptance status
16. publication truth correction
17. M3 readiness

---

# 53. Manifest

新規:

```text
docs/verification/m2b2/M2B2_LIVE_UI_SMOKE_MANIFEST.json
```

。

最低限:

```text
custom_dom_loaded
app_import_ok
ops_import_ok
raw_json_hidden
seed_control_after_generate
style_widget_value
resolution_widget_value
default_queue
cast_section_visible
selected_cast_placement
save_reload
evidence_type
status
```

。

---

# 54. Evidence Type

```text
STATIC_CODE
HEADLESS_TEST
LIVE_RUNTIME
LIVE_BROWSER_OWNER
LIVE_BROWSER_AGENT
```

を区別。

---

# 55. Screenshot

Agent live browserがないなら偽造しない。

Owner screenshotをrepoへ取り込む仕組みが無ければ:

```text
Owner screenshot observed externally
```

とReportへ記述し、
ファイルpathを捏造しない。

---

# 56. Product UI Raw JSON Policy

M2B.2成功後:

```text
Raw Authoring JSON
```

は通常操作には不要。

将来必要なら:

```text
Advanced Debug
```

で見せる。

Primary surfaceへ戻さない。

---

# 57. Error Handling

style/resolution等のenum不正時:

```text
fail clearly
```

は維持。

ただしCanonical workflowが最初から不正値をロードする状態は禁止。

---

# 58. Browser cache note

Frontend JS修正後は:

```text
ComfyUI server restart
browser hard reload
```

をOwner checklistへ必ず書く。

古いextension cacheを新コードのFAILと混同しない。

---

# 59. LOW modelについてのReport注記

今回のfailureを:

```text
LOW model caused Product collapse
```

とは記録しない。

正確には:

```text
- app import bug predates M2B.1
- live browser was never closed
- M2B.1 headless/backend tests could not detect frontend bootstrap failure
- M2B.1 LOW run also failed to discover these browser-only defects
```

と整理。

---

# 60. M2B.2 Acceptance Gates

```text
M0–M2B.1 REGRESSION:
PASS

APP IMPORT PATH:
PASS

CUSTOM DOM LOAD:
PASS / OWNER PENDING

RAW DOCUMENT JSON PRIMARY UI:
NO

SEED control_after_generate:
FALSE

WORKFLOW WIDGET SHIFT:
FIXED

STYLE TEMPLATE DEFAULT:
Manga Monochrome

RESOLUTION DEFAULT:
Portrait 832x1216

DEFAULT WORKFLOW QUEUE:
PASS / OWNER PENDING

CAST SECTION VISIBLE:
PASS / OWNER PENDING

SELECTED CAST PLACEMENT:
PASS

SAVE/RELOAD:
PASS / OWNER PENDING

INVALID INPUT ON LOAD:
NO

ACTIVE ROOT WORKFLOW:
1

CONTROLNET ADDED:
NO

M3 FEATURES ADDED:
NO
```

---

# 61. M3 GO条件

Web GPTは以下を確認してからM3を発行する。

最低限Owner Browserで:

```text
1. Product Custom DOMが見える
2. Invalid Inputなし
3. Default Queue可能
4. CASTを選んで配置可能
5. Save/Reloadで壊れない
```

。

---

# 62. Commit A

推奨:

```text
fix(manga): repair minimum-hand live UI bootstrap and workflow serialization
```

含む:

```text
minimum_hand_scene_editor.py
minimum_hand_scene_editor.js
必要ならUI hide helper
tests
MINIMUM_HAND_MANGA_DRAFT.json
M2B.2 report
manifest
STATUS
DOCUMENT_REGISTER
```

。

---

# 63. Commit B

推奨:

```text
docs(manga): publish M2B.2 review target
```

。

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current card = M2B.2
Next = M3 only after owner browser acceptance
```

。

---

# 64. Navigation Truth Corrections

次Entryで少なくとも:

```text
M2B Navigation = 463ec8f92c79bfb25d2532a6227c7bb4941b3b69
M2B.1 = 1b3bd224...
M2B.1 Navigation = 4bc82536...
```

へ整理。

`0d6da8c1`をM2B Navigationと誤記しない。

---

# 65. Final Response Format

```text
MODEL USED:
Gemini 3.8 STANDARD/HIGH

BASELINE REVIEW TARGET:
1b3bd2246c6a2f440d7a7f810a8a75a798fb9bc2

M2B.2 IMPLEMENTATION COMMIT A:
M2B.2 NAVIGATION COMMIT B:
PUSH STATUS:

APP IMPORT BEFORE:
APP IMPORT AFTER:
CUSTOM DOM MODULE:
OPS MODULE:

SEED CONTROL_AFTER_GENERATE:
CANONICAL WIDGET ORDER:
STYLE VALUE:
RESOLUTION VALUE:

RAW DOCUMENT JSON:
CANONICAL WORKFLOW:
ACTIVE ROOT COUNT:

HEADLESS TESTS:
PYTHON TESTS:
LIVE BACKEND:

AGENT LIVE BROWSER:
OWNER LIVE BROWSER:
DEFAULT QUEUE:
CAST UI:
SELECTED CAST PLACEMENT:
SAVE/RELOAD:

M2B.1 TRUTH CORRECTION:
REPORT SHA CORRECTION:
NAVIGATION TRUTH CORRECTION:

M2B.2 STATUS:
PASS / PARTIAL / HOLD

M3 READY:
YES / NO

OWNER ACTION REQUIRED:
```

---

# 66. 最終原則

今回の最重要確認は画像品質ではない。

```text
Workflowを開く
↓
Product UIが見える
↓
値がずれない
↓
Queueできる
↓
Alice/Bobを意図通り置ける
```

これが成立すること。

Backendが正しくても、
Custom UIがロードされずCanonical WorkflowがInvalid Inputなら
Product Pathは完成していない。

M2B.2でこのBrowser境界を閉じてからM3へ進むこと。
