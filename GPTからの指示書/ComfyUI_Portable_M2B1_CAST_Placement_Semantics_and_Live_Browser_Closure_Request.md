# ComfyUI Portable — M2B.1 / Phase 3M-2B.1
# CAST Placement Semantics & Live Browser Closure
## — Product UIの選択意味を直し、実ブラウザでMainlineを閉じる —
## Antigravity2 / Gemini 3.8 向け Bounded Correction Card

## 推奨モデル

Gemini 3.8

---

# 0. このCardの目的

M2BのProduct方向は維持する。

M2Bでは以下が成立した。

- Minimum-Hand Mainline UIへCAST Masterを統合
- Character Rough Regionを同一Canvasへ統合
- Free Text Acting Prompt
- Hidden AUTO Spatial Helper
- Seed Randomize
- Scene Move / Resize child semantics
- versionless Canonical Workflow
- 1人物 / 2人物 / Depth / recurrent CAST runtime

しかしWeb GPT reviewで、
M3へ進む前に閉じるべきProduct UI上の問題が2点見つかった。

1. `+ Add Character` がSelected CASTを使わず、Scene内の人数でCASTを自動循環している
2. Reportの `Browser E2E = PASS (Simulated / Contract Verified)` は、実ブラウザ操作PASSではない

今回これだけを修正する。

M3のPanel Frame / Rough Guide / ControlNet施工にはまだ進まない。

---

# 1. 最初に読む正本

最初に:

```text
ComfyUIPortable/GITHUB.TXT
```

次に:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

本Card発行時の固定Review Target:

```text
e676deb53824b97c18058c3dd2fc20cb08d0f822
```

M2B Implementation Commit A:

```text
e676deb53824b97c18058c3dd2fc20cb08d0f822
```

M2B Navigation Commit B:

```text
463ec8f92c79bfb25d2532a6227c7bb4941b3b69
```

本Card発行時のremote `main` head:

```text
0d6da8c147576c9a99db6b98316271eda3591bb3
```

M2B Commit A/Bはremote mainへ既に入っている。

したがって旧報告の:

```text
LOCAL ONLY
Owner push待ち
```

は現在事実ではない。

次Navigation更新でPublication truthを修正する。

---

# 2. Web GPT Review Verdict

M2B Architecture:

```text
ACCEPT
```

M2B Product Direction:

```text
ACCEPT
```

M2B Mainline Runtime:

```text
PASS
```

M2B Product UI Semantics:

```text
REQUIRED FIX
```

Live Browser E2E:

```text
PENDING
```

Next:

```text
M2B.1
→ Web GPT review
→ M3
```

---

# 3. M2Bで成立したもの

壊さない:

```text
TEGAKI_AUTHORING_DOCUMENT
Minimum-Hand single-node Product UI
Scene / Visual Frame separation
CAST Master / Character Instance separation
Hidden AUTO Spatial Helper
1 char helper OFF
2 char horizontal/depth helper
3+ helper OFF + warning
Core masked conditioning
No ControlNet in Core
No Pose/Camera/Strength controls
MINIMUM_HAND_MANGA_DRAFT.json
```

---

# 4. Finding A — Add CharacterがSelected CASTを使わない
# BLOCKER

現在のJSではCAST chipをクリックすると:

```text
selectedCastId
```

が更新される。

しかしSelected Sceneの:

```text
+ Add Character
```

はSelected CASTを参照せず、

```javascript
castList[sceneInstances.length % castList.length]
```

でCASTを自動選択している。

つまり現在:

```text
Aliceを選択
→ Add Character
```

しても、必ずAliceが追加される保証がない。

ユーザーから見るとCAST chipの選択意味と配置動作が一致していない。

---

# 5. Product Contract

M2B.1以降:

```text
Selected CAST
=
次にSceneへ置くCAST
```

とする。

最小手UIとして明確であること。

---

# 6. Add Character Rules

推奨挙動:

## CAST 0件

```text
+ Add Character
→ "Add CAST first"
```

## CAST 1件

```text
selectedCastIdがnullでも
唯一のCASTを追加してよい
```

## CAST 2件以上 + selectedCastIdあり

```text
selected CASTを追加
```

## CAST 2件以上 + selectedCastIdなし

```text
silent cycling禁止
```

以下のどちらか。

第一候補:

```text
inline message:
"Select a CAST above first"
```

第二候補:

```text
small chooser
```

Minimum-Handのため第一候補を推奨。

---

# 7. Button Label

Selected CASTがある場合:

```text
+ Place Alice
```

のように動的表示してもよい。

ただし必須ではない。

少なくともtooltip / small statusで:

```text
Place selected CAST into this Scene
```

が分かること。

---

# 8. CAST chip selection

CAST chipクリック:

```text
selectedCastId = cast_id
```

。

再クリックでnullへtoggleする現在挙動を維持してもよい。

ただしmultiple CAST時にnullならAdd Characterは明示停止。

---

# 9. Same CAST Repeated

以下を必ず可能にする。

```text
Alice selected
Scene 1 -> Add Alice
Scene 2 -> Add Alice
```

。

各Appearance:

```text
same cast_id
different instance_id
```

。

---

# 10. Same CAST Twice Same Scene

```text
Alice selected
Add Alice
Add Alice
```

も許可。

2個目以降:

```text
Advanced / Seed-Sensitive
```

statusは可。

Hard blockは禁止。

---

# 11. Arbitrary CAST order

以下が可能であること。

```text
CAST:
Alice
Bob
Carol

Scene 1:
Bob only

Scene 2:
Carol + Alice

Scene 3:
Alice + Alice
```

。

Scene人数による自動循環ではなく、
Selected CASTが配置を決める。

---

# 12. Test — Selection Causality

最低限:

```text
selectedCastId = Bob
+ Add Character
→ instance.cast_id == Bob
```

。

次:

```text
selectedCastId = Alice
+ Add Character
→ instance.cast_id == Alice
```

。

Scene内instance countに依存しない。

---

# 13. Finding B — Browser E2E Provenance
# BLOCKER

M2B Report:

```text
Browser E2E Status:
PASS (Simulated / Contract Verified)
```

はTruthful classificationではない。

Headless JS testはBrowser E2Eではない。

Live ComfyUI runtime generationも、
Custom DOM UIの実操作を証明しない。

---

# 14. Provenanceを3つへ分離

M2B.1 Reportでは:

```text
HEADLESS JS CONTRACT:
PASS / FAIL

LIVE BACKEND RUNTIME:
PASS / FAIL

LIVE BROWSER PRODUCT E2E:
PASS / PENDING / FAIL
```

を別々に記録。

---

# 15. Browser PASSの条件

`LIVE BROWSER PRODUCT E2E = PASS` と書けるのは、
実際のComfyUI browser上でCustom DOMを操作した場合だけ。

以下は代用不可:

```text
Node.js simulation
string/source inspection
API prompt runner
workflow JSON validation
static UI mock image
```

。

---

# 16. Browser操作ができない場合

Antigravity側で実ブラウザ操作が不可能なら:

```text
LIVE BROWSER PRODUCT E2E = PENDING
OWNER MANUAL CHECK REQUIRED
```

とする。

その場合でもコード修正・testsはCommit可。

M3 GOはWeb GPT / Owner判断。

---

# 17. Browser Scenario A — Load

実ComfyUI:

```text
workflows/MINIMUM_HAND_MANGA_DRAFT.json
```

をload。

確認:

```text
one Product Authoring node
backend grouped
no missing node
no JS console fatal error
```

。

---

# 18. Browser Scenario B — CAST Selection

1. Add Alice
2. Identity Prompt edit
3. Add Bob
4. Identity Prompt edit
5. Alice chip select
6. Scene 1 -> Add Character

確認:

```text
Alice instance created
```

。

次:

7. Bob chip select
8. Add Character

確認:

```text
Bob instance created
```

。

---

# 19. Browser Scenario C — Bob-only Scene
# Finding A closure oracle

Scene 2を選択。

```text
Bob chip select
Add Character
```

。

確認:

```text
Scene 2 first instance == Bob
```

。

このTestは旧cycle方式ならSceneのfirst instanceがAliceになり得るため、
必須Oracle。

---

# 20. Browser Scenario D — Repeated Alice

Scene 1:

```text
Alice
Bob
```

。

Scene 2:

```text
Alice
```

。

確認:

```text
same cast_id
different instance_id
```

。

---

# 21. Browser Scenario E — Character drag / resize

Alice boxをdrag。

Bob boxをresize。

確認:

```text
document_json即更新
parent Scene内に保持
```

。

---

# 22. Browser Scenario F — Acting Prompt

Alice:

```text
reading a book
```

Bob:

```text
looking outside
```

切替。

戻る。

確認:

```text
prompt preserved
```

。

---

# 23. Browser Scenario G — Scene Move

Alice/Bobを持つSceneをdrag。

確認:

```text
Scene
Alice
Bob
```

がcommon effective delta。

---

# 24. Browser Scenario H — Scene Resize

Scene resize。

確認:

```text
Alice/Bob relative geometry scales
```

。

---

# 25. Browser Scenario I — Save / Reload

Workflow save。

Reload。

最低限確認:

```text
CAST names
Identity Prompts
Scenes
Scene prompts
Character instances
CAST assignments
Acting prompts
Areas
Seed
Resolution
Style
```

。

---

# 26. Browser Scenario J — Seed

Randomize Seed。

Queue。

再Randomize。

Queue。

確認:

```text
actual sampler seed changes
```

。

---

# 27. Browser Scenario K — Two-character Runtime

Alice left
Bob right。

最大3 seeds。

目標:

```text
最低1 usable draft
```

。

M2A.1 8-seed benchmarkは再実施不要。

---

# 28. Browser Scenario L — Depth

Alice large
Bob small。

Debug:

```text
resolved_mode = spatial_depth
Alice = large in foreground
Bob = smaller in background
```

。

Queue。

---

# 29. Browser Scenario M — Delete Scene

Alice/BobのSceneを削除。

確認:

```text
instances removed
CAST masters remain
validate_document PASS
```

。

---

# 30. Browser Scenario N — Delete CAST

使用中Alice削除:

```text
blocked
```

。

Alice instance削除後:

```text
Alice CAST delete allowed
```

。

---

# 31. Character Removal and Scene Mode
# SHOULD FIX

現在、最後のCharacter InstanceをSceneから外した後も:

```text
input_mode = cast
```

が残り得る。

Product上は見えない状態なので、
最後のinstance削除時:

```text
input_mode = simple
```

へ戻すことを推奨。

Scene Promptは絶対に変更・削除しない。

---

# 32. Test — Last Character Removed

```text
Scene input_mode=cast
1 Alice instance
remove Alice
```

期待:

```text
0 instances
input_mode=simple
scene prompt unchanged
```

。

もし既存Contract上cast-emptyを意図的に許す理由があるなら、
Reportで説明し、UI上で意味を明確化。
黙って残さない。

---

# 33. CAST negative prompt
# NON-BLOCKING

M2B requestではAdvancedとして候補だったが、
現在Product inspectorはName / Identity Prompt中心。

これはM2B.1 BLOCKERではない。

Minimum-Hand優先のため:

```text
DEFERRED
```

でもよい。

---

# 34. Security / Rendering Robustness
# SHOULD FIX

CAST `display_name` / prompt文字列を
`innerHTML` attributeへ直接埋め込む箇所がある。

最低限:

```text
Display Name containing:
"
'
<
>
&
```

でUI DOMが壊れないことを確認。

可能なら:

```text
createElement
textContent
input.value
```

方式を優先。

ローカルAuthoring UIでも、
ユーザー入力でInspector DOMが壊れるのは避ける。

---

# 35. Browser Scenario — Special Characters

CAST name:

```text
Alice "A" <test>
```

など。

保存・再描画で:

```text
DOM corruptionなし
text preserved
```

。

---

# 36. Headless JS TestをSource-Coupledにする

現在の`test_m2b_minimum_hand_editor.mjs`は
Production JSと同じ計算式を別途再記述したsimulation。

これは有用だが、
実Production関数を直接実行していない。

M2B.1では可能なら:

```text
pure frontend operations module
```

へ小さく切り出す。

例:

```text
web/js/minimum_hand_authoring_ops.js
```

に:

```text
chooseCastForPlacement
moveSceneWithChildren
resizeSceneWithChildren
removeSceneWithInstances
```

等のpure logicを置き、

Production JS
+
Node.js tests

が同じ関数を使う。

---

# 37. ただし大規模Refactor禁止

Browser E2E closureが主目的。

Frontend pure module化で
UIを壊すリスクが高ければ:

```text
selected CAST placement logicだけpure helper化
```

でもよい。

---

# 38. Automated Test追加

既存161 Python + 7 JSを維持。

最低限新規:

```text
selected CAST controls placement
multiple CAST + no selection = explicit block
single CAST auto-placement
same CAST repeated different scene
same CAST twice same scene
last instance removal mode policy
special-character display name does not corrupt state
```

。

---

# 39. Python tests

Backend Auto helper等は再変更しない。

必要なのはregressionのみ。

M0〜M2B Python suites:

```text
ALL PASS
```

。

---

# 40. Runtime generation

画像品質の再研究はしない。

最低限:

```text
Bob-only first instance Scene
Alice+Bob Scene
Repeated Alice across Scenes
```

でqueue成功すればよい。

---

# 41. M2B Visual benchmarkを再実施しない

以下は既にM2A.1で固定。

```text
2-character 5/8 useful
Depth 5/8 useful
3-character 1/8
```

。

M2B.1でSeedを大量に消費しない。

---

# 42. Workflow Root

維持:

```text
workflows/
├ MINIMUM_HAND_MANGA_DRAFT.json
├ README.md
└ Archive/
```

。

新Workflowを増やさない。

---

# 43. ControlNet禁止

今回:

```text
ControlNet
Panel Frame Guide
Dummy Guide
Pose
```

へ進まない。

---

# 44. M3禁止

M2B.1が終わるまで:

```text
Visual Panel Frame UI
Rough Manga Guide
white-dummy guide
ControlNet guide pipeline
```

を実装しない。

---

# 45. M2B Report Truth Correction

元Reportは削除しない。

以下を追記するか、
M2B.1 ReportからCorrectionを明示。

修正対象:

```text
Browser E2E:
PASS (Simulated / Contract Verified)
```

を:

```text
Headless Contract:
PASS

Live Browser:
PENDING at M2B baseline
```

と読み替える。

---

# 46. 新規Report

```text
ComfyUIPortable/docs/reports/M2B1_CAST_PLACEMENT_AND_BROWSER_CLOSURE_REPORT.md
```

。

---

# 47. Report必須項目

1. Fixed M2B SHA
2. Web GPT review findings
3. Selected CAST placement defect
4. Corrected placement semantics
5. One/multiple CAST behavior
6. Same CAST repeated
7. Last-character scene mode policy
8. Frontend source-coupled tests
9. Headless contract status
10. Live backend status
11. Live Browser E2E status
12. Browser scenarios actually executed
13. Screenshots
14. Runtime samples
15. Save/reload evidence
16. Known remaining UI limits
17. M3 readiness

---

# 48. Screenshot Evidence

Live browserを操作できた場合:

```text
docs/verification/m2b1/
```

へ最低限:

```text
M2B1_BROWSER_CAST_SELECTION.png
M2B1_BROWSER_TWO_CAST_STAGING.png
M2B1_BROWSER_REPEATED_CAST.png
```

。

Static mockではなくlive browser screenshotであることを明記。

---

# 49. Manifest

```text
docs/verification/m2b1/M2B1_PRODUCT_E2E_MANIFEST.json
```

。

最低限:

```text
condition_id
evidence_type
runtime_status
browser_status
visual_status
review_method
selected_cast_id
created_instance_cast_id
seed
output_path
screenshot_path
notes
```

。

---

# 50. Provenance

```text
evidence_type:
HEADLESS_TEST
LIVE_BROWSER
LIVE_RUNTIME
STATIC_UI_RENDER
```

を区別。

STATIC_UI_RENDERをLIVE_BROWSERと呼ばない。

---

# 51. Hand Count再計測

Selected CAST semantics修正後:

## 1 Character

```text
Add CAST
Identity Prompt
select CAST if needed
Add Character
Acting Prompt
drag
Queue
```

。

## 2 Character

Alice/Bobを意図的に選んで配置した場合の手数。

10以下を絶対Gateにはしないが、
Minimum-Hand維持を確認。

---

# 52. M2B.1 Acceptance Gates

```text
M0–M2B PYTHON REGRESSION:
PASS

JS REGRESSION:
PASS

SELECTED CAST -> NEW INSTANCE:
PASS

SCENE INSTANCE COUNT DOES NOT CHOOSE CAST:
PASS

MULTIPLE CAST + NO SELECTION:
EXPLICIT / NON-SILENT

SINGLE CAST PLACEMENT:
PASS

SAME CAST MULTI-SCENE:
PASS

SAME CAST SAME-SCENE:
PASS / allowed

LAST INSTANCE REMOVAL:
TRUTHFUL MODE POLICY

CAST DELETE REFERENCED:
BLOCKED

SCENE DELETE ORPHANS:
NONE

SAVE/RELOAD:
PASS / PENDING

HEADLESS CONTRACT:
PASS

LIVE BACKEND:
PASS

LIVE BROWSER:
PASS / PENDING / FAIL

WORKFLOW ROOT ACTIVE COUNT:
1

CONTROLNET ADDED:
NO

POSE UI ADDED:
NO

PANEL FRAME ADDED:
NO
```

---

# 53. M3 GO条件

最低限:

```text
Selected CAST placement semantics = PASS
Save/reload semantics = structurally PASS
No orphan refs
Regression all PASS
```

。

Live BrowserがAgent側で実施不能でも、
Ownerが実ブラウザで主要操作を確認すればM3 GO可。

ただしReport上は
Agent未実施のBrowser E2EをPASSにしない。

---

# 54. M3次候補

M2B.1 closure後:

```text
M3 / 3M-3
Rough Manga / Visual Panel Guide Integration
```

。

M3で初めて:

```text
Semantic Scene
≠
Visual Panel Frame
```

のVisual Frame側をProductへ追加。

さらに必要なら:

```text
rough white-dummy / silhouette guide
```

をOptional Controlとして統合する。

---

# 55. Commit A

推奨:

```text
fix(manga): correct CAST placement semantics and close M2B product path
```

含む:

```text
minimum_hand_scene_editor.js
必要なfrontend pure helper
tests
verification
M2B.1 report
STATUS / DOCUMENT_REGISTER
```

。

---

# 56. Commit B

推奨:

```text
docs(manga): publish M2B.1 review target
```

。

`GITHUB_ComfyUI.txt`:

```text
Review Target = Commit A
Current card = M2B.1 completed / partial
Next = M3 candidate
Publication truth = remote実態
```

。

---

# 57. Push

Owner運用に従う。

ただし報告:

```text
LOCAL ONLY
```

と書いた後、Ownerが即pushしている可能性があるため、
Navigation作成直前と最終報告時に:

```text
git status
git log
remote main
```

を確認。

Entryと実態を一致させる。

---

# 58. 最終回答Format

```text
MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
e676deb53824b97c18058c3dd2fc20cb08d0f822

M2B.1 IMPLEMENTATION COMMIT A:
M2B.1 NAVIGATION COMMIT B:
PUSH STATUS:

SELECTED CAST PLACEMENT:
MULTIPLE CAST NO-SELECTION:
SINGLE CAST AUTO:
SAME CAST MULTI-SCENE:
SAME CAST SAME-SCENE:
LAST INSTANCE MODE POLICY:

CAST DELETE:
SCENE DELETE:
SAVE/RELOAD:

HEADLESS JS:
LIVE BACKEND:
LIVE BROWSER:
BROWSER PROVENANCE:

HAND COUNT 1-CHAR:
HAND COUNT 2-CHAR:

OLD PYTHON TESTS:
NEW TESTS:
TOTAL:
JS TESTS:

WORKFLOW:
ACTIVE ROOT COUNT:

SCREENSHOTS:
MANIFEST:
REPORT:

M2B PRODUCT PATH:
PASS / PARTIAL / HOLD

M3 READY:
YES / NO

OWNER MANUAL CHECK REQUIRED:
YES / NO

USER ACTION REQUIRED:
```

---

# 59. 最終原則

M2B.1で直すのは能力研究ではない。

直すのは:

```text
ユーザーがAliceを選んだ
=
Aliceが置かれる
```

という最も基本的なProduct semantics。

そして:

```text
Simulation PASS
≠
Live Browser PASS
```

をEvidence上でも分離する。

この2点が閉じてから、
M3のVisual Panel Frame / Rough Manga Guideへ進むこと。
