# M3B-LR1 — Rough Guide Foundation Long-Run Batch

Date: 2026-09-09 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Mode: LONG-RUN BATCH
Owner: repository owner
Milestone gate authority: Web GPT SOL delegated by Owner
Final product review authority: Owner

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR1_ROUGH_GUIDE_FOUNDATION_LONG_RUN_BATCH.md`

---

# 0. Delegated M3A.1 decision

Ownerは2026-09-09、この先の中間Milestone gate判断をWeb GPT SOLへ委任し、完成品または大きな節目でまとめてOwner reviewする運用へ変更した。

Web GPT SOL decision:

```text
ACCEPT M3A1 O1-O5
```

根拠:

```text
Regression: PASS
Runtime: PASS
Browser B0-B9: PASS
Visual evidence: PASS
Unresolved technical blocker: NONE
```

これは:

```text
Milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL
```

を意味する。

以下とは異なる:

```text
Final Owner product review:
DEFERRED
```

Owner本人がO1–O5を逐次目視したと記録してはいけない。

---

# 1. Repository state

Manga OA1 publication:

`3be0ecb027c633a90aecd46b79f32ae47b5aab66`

M3A.1 Core Implementation SHA:

`a7f0baaa89a2e315b0492573c9da19e50727928b`

M3A.1 Closure Review Target:

`ad91c9277715e998663e8c12b6c37cca16e53955`

Repository `main` observed by SOL at issuance:

`5adde38274b4d3646d27acb4f32c1ae080c26d6d`

OA1 publication後のrepository進行はH3側作業。

Manga authorityとの競合を意味しない。

---

# 2. Start commands

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

`git fetch origin`が既知の`.git/FETCH_HEAD` permission boundaryで失敗する場合:

* 失敗をreportへ記録
* 既存`origin/main`
* GitHub上でOwnerから与えられたbaseline
* local diff

を使って判断する。

fetch failureだけで無条件STOPしない。

---

# 3. Baseline drift rule

`origin/main`が

`5adde38274b4d3646d27acb4f32c1ae080c26d6d`

より進んでいる場合:

```bash
git diff --name-status \
  5adde38274b4d3646d27acb4f32c1ae080c26d6d..origin/main
```

を確認。

M3B-LR1 own filesと競合しなければ最新origin/mainをexecution baselineとして継続。

H3だけの変更でSTOPしない。

---

# 4. Long-Run operating rule

このCardは通常Cardと異なり、複数Stageを連続実行してよい。

```text
Stage 0 PASS
↓
Stage 1 PASS
↓
Stage 2 PASS
↓
Stage 3 PASS
↓
Stage 4 PASS
↓
Stage 5 PASS
↓
Stage 6
```

各StageのgateがPASSしたらOwner/SOLの追加確認を待たず次へ進む。

途中で質問を返さない。

安全な既定値をCard内で固定する。

STOP条件に該当した場合だけ終了する。

---

# 5. Long-Run scope

今回の成果物:

```text
Rough Manga / White-Dummy image
↓
persistent Guide asset
↓
Guide preview
↓
rough Figure Regions
↓
Character Instance association
↓
Save / Reload
↓
runtime deterministic guide plan / preview
↓
browser evidence
```

今回含めない:

```text
ControlNetを実際のgenerationへ適用
pose estimation
OpenPose生成
automatic human detection
AI segmentation
automatic character recognition
image-to-image generation
M3B全体完成宣言
M4
Shell integration
H3
```

---

# 6. Product semantics

## Guide ownership

GuideはPageが所有する。

```text
Page
 ├ Scenes
 ├ Visual Frames
 ├ CAST
 ├ Character Instances
 └ Guides
```

Scene / Frame / Guideを同一化しない。

---

# 7. Rough Guide contract

M3B-LR1のrough guideは既存`page.guides[]`を使用する。

schema versionは上げない。

新しいoptional fieldを加算的に扱う。

Canonical form:

```json
{
  "guide_id": "guide_1",
  "guide_type": "rough_manga",
  "asset_reference": "tegaki_manga_guides/example.png",
  "placement": {
    "shape_type": "rect",
    "x": 0.0,
    "y": 0.1,
    "w": 1.0,
    "h": 0.8
  },
  "enabled": true,
  "figure_regions": [
    {
      "figure_id": "figure_1",
      "area": {
        "shape_type": "rect",
        "x": 0.10,
        "y": 0.08,
        "w": 0.30,
        "h": 0.75
      },
      "instance_id": "inst_1"
    }
  ],
  "metadata": {
    "fit_mode": "contain",
    "source_width": 832,
    "source_height": 1216
  }
}
```

---

# 8. Coordinate semantics

`guide.placement`:

Page-normalized coordinates。

これはGuide画像そのものがPage上で占有するactual content rectangle。

upload時に画像aspect ratioを保った`contain` fitを計算し、Page中央へ置く。

`figure_regions[].area`:

Guide-local normalized coordinates。

```text
0..1 × 0..1
```

Guide画像内の人物位置を表す。

runtimeでは:

```text
guide-local figure area
+
guide placement
→
derived page-normalized area
```

を計算する。

derived page areaをpersistent SSOTとして二重保存しない。

---

# 9. Association semantics

Character associationは必ず:

`instance_id`

へ向ける。

`cast_id`へ直接associationしない。

理由:

同じCASTが複数Sceneへ複数出演できるため。

MVP:

```text
1 figure
→ 0 or 1 Character Instance

1 Character Instance
→ 0 or 1 figure
within one rough guide
```

duplicate associationは禁止。

未割当figureは合法。

---

# 10. No automatic interpretation

禁止:

* 白ハゲを自動認識したふり
* 人物を自動検出したふり
* CAST identityを画像から推測
* FigureとInstanceの自動matchingをProduct機能として主張

M3B-LR1ではUserがassociationを指定する。

---

# 11. Instance deletion rule

Character Instanceが削除された場合:

対応figureを削除しない。

代わりに:

```json
"instance_id": null
```

またはfield除去でunassignする。

rough figureそのものは保持。

Scene cascade delete / CAST cascadeによるinstance削除でも同じ。

dangling foreign keyを残さない。

---

# 12. Guide deletion rule

Guide削除:

* documentからguide entryを除去
* Character Instanceは変更しない
* upload済みasset fileは自動削除しない

理由:

同じassetを別workflow/documentが参照している可能性を排除できない。

asset cleanupは別Card。

---

# 13. Asset reference security

Documentへ保存禁止:

```text
D:\...
C:\...
/home/...
absolute path
../
..\ 
file://
```

保存するのはComfyUI input boundary内のcanonical relative referenceだけ。

例:

`tegaki_manga_guides/guide_abc.png`

runtime resolverはinput directory外へのescapeをfail-closedする。

---

# 14. Supported asset formats

LR1:

```text
PNG
JPEG/JPG
WEBP
```

のみ。

unsupported extension / decode failure:

```text
ERROR
```

documentを破壊しない。

---

# 15. Stage 0 — OA1 closure + governance update

最初に既存OA1を閉じる。

OA1 reportへpost-publication section追加:

```text
Owner delegated milestone gate decisions to Web GPT SOL.

SOL decision:
O1 ACCEPT
O2 ACCEPT
O3 ACCEPT
O4 ACCEPT
O5 ACCEPT

Milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL

M3A.1 gate:
CLOSED

M3B eligibility:
OPEN

Final Owner product review:
DEFERRED
```

OA1 Card:

`cards/current/...OA1...md`

↓

`cards/completed/...OA1...md`

へbyte-identical移動。

---

# 16. Permanent governance update

以下へ今回の新運用を明記:

* `GITHUB_MANGA.txt`
* `docs/manga/STATUS.md`
* `docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
* `docs/manga/plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md`

rule:

```text
Intermediate milestone acceptance:
Owner delegates to Web GPT SOL unless Owner explicitly reserves a gate.

SOL may close a milestone only from recorded technical/browser/visual evidence.

Final production/product acceptance:
Owner retained.

LUNA never self-accepts.
```

過去reportの当時のPENDING記録は書き換えない。

---

# 17. Stage 0 gate

PASS条件:

```text
M3A.1 gate: CLOSED
M3B eligibility: OPEN
OA1: completed
Active M3B Card: M3B-LR1
Final Owner product review: DEFERRED
```

FAILならSTOP。

---

# 18. Stage 1 — Contract implementation

対象候補:

* `authoring_contract.py`
* `authoring_operations.py`
* relevant JS pure operations
* tests

既存`create_guide()`を拡張してよい。

rough_manga guide validation追加。

必須validation:

```text
guide_id unique
guide_type valid enough to route
asset_reference valid relative string
placement valid normalized area
figure_regions list
figure_id unique per guide
figure local area valid
instance_id exists or null
duplicate instance association rejected
```

既存unknown guide typeを突然hard failしない。

legacy compatibilityを維持。

---

# 19. Stage 1 tests

最低限:

```text
legacy document guides=[] PASS
existing guide roundtrip PASS
rough_manga valid PASS
unknown optional fields preserved
duplicate figure_id FAIL
unknown instance_id FAIL
duplicate instance association FAIL
invalid placement FAIL
invalid figure area FAIL
absolute asset path FAIL
path traversal FAIL
```

既存M0–M3A regressionも必要部分を実行。

Stage 1 gate:

```text
Contract tests PASS
Existing regression PASS
No schema version bump
```

---

# 20. Stage 2 — Asset upload + Guide UI

Primary surface:

`TegakiMinimumHandSceneEditor`

へ第四layerを追加:

```text
Scene Regions
Visual Panel Frames
Character Staging
Rough Guide
```

ただしGuideが無い時、Primary Draft操作を邪魔しない。

---

# 21. Rough Guide UI

最低限:

```text
[Add Rough Guide Image]
[Enable / Disable]
[Replace Image]
[Remove Guide]

Guide preview
Figure list
Association inspector
```

drag & dropも可能なら実装。

File pickerだけでもfallbackとして維持。

---

# 22. Upload behavior

browserからstandard ComfyUI image upload boundaryを使用。

独自filesystem書込APIを増やさない。

server responseのcanonical filename/subfolderをdocumentへ保存。

source image dimensionsを取得し、

`contain`

placementを計算。

---

# 23. Guide visual layer

Guide画像はcanvasへ薄く表示。

Scene / Frame / Character overlaysと混同しない。

Rough Guide layer選択時のみfigure regionsを操作可能。

他layerではGuideは薄いreference表示。

---

# 24. Figure creation UX

MVP操作:

```text
1. Character Instanceを選択
2. Add Figure
3. Guide画像上でdrag
```

で、

```text
figure_id
guide-local area
selected instance_id
```

を一度に作れることを推奨。

Instance未選択でもUnassigned Figureを作成可能。

---

# 25. Same CAST test

同じCASTから:

```text
inst_1
inst_2
```

を作り、

```text
figure_1 → inst_1
figure_2 → inst_2
```

として独立associationできること。

CAST IDだけでassociationしてはいけない。

---

# 26. Stage 2 gate

headless JS testで:

```text
add guide
replace guide
enable/disable
remove guide
add figure
move/resize figure
assign
unassign
delete figure
instance deletion unassigns figure
same CAST multiple instance association
```

PASS。

---

# 27. Stage 3 — Save / Reload persistence

canonical workflowで:

```text
upload rough guide
create ≥2 figures
associate ≥2 instances
save workflow
reload
```

後も:

```text
asset_reference retained
placement retained
figure IDs retained
areas retained
instance associations retained
enabled retained
```

こと。

Windows local pathがJSONへ入っていないこと。

---

# 28. Stage 3 regression

確認:

```text
Scenes unchanged
Visual Frames unchanged
CAST unchanged
Character Instance geometry unchanged
Seed unchanged
0-guide workflow unchanged
```

Guide操作がScene/Frame/Characterを暗黙変更しない。

---

# 29. Stage 4 — Runtime Guide Bridge

新規候補:

`rough_guide_bridge.py`

必要ならComfyUI node:

`TegakiMangaRoughGuideBridge`

を追加してよい。

責務:

```text
authoring document
→ validate
→ active rough guide
→ secure asset resolution
→ image load
→ placement
→ figure association plan
→ deterministic preview/debug
```

---

# 30. Runtime output

最低限:

```text
rough_guide_image
figure_union_mask
debug_json
```

または同等のbounded output。

debug_json:

```json
{
  "guide_id": "guide_1",
  "asset_reference": "...",
  "enabled": true,
  "figure_count": 2,
  "associations": [
    {
      "figure_id": "figure_1",
      "instance_id": "inst_1",
      "page_area": {}
    }
  ],
  "generation_influence": "NOT_IMPLEMENTED"
}
```

---

# 31. Important runtime boundary

LR1ではrough guideを:

```text
KSampler conditioning
ControlNet
IPAdapter
img2img
```

へ接続しない。

Product/UI/reportで:

```text
Generation influence: NOT IMPLEMENTED IN LR1
```

を明示。

「Guideを入れたので生成に効く」と主張しない。

---

# 32. Runtime zero-guide behavior

Guide無し:

```text
NO_GUIDE
```

合法。

既存Manga generationを一切変化させない。

canonical generation outputはLR1導入前と同じ経路を通る。

---

# 33. Runtime error behavior

以下はfail-closed diagnostic:

```text
missing referenced asset
path escape
unsupported format
decode failure
invalid placement
dangling instance association
duplicate association
```

Manga生成Coreをsilentに別動作へ変えない。

---

# 34. Stage 4 gate

最低test:

```text
valid image resolution PASS
contain mapping PASS
figure local→page mapping PASS
union mask PASS
disabled guide ignored
no guide NO_GUIDE
missing asset FAIL
path traversal FAIL
same CAST multi-instance plan PASS
```

---

# 35. Stage 5 — Live Browser Long-Run Verification

server restart。

browser hard reload。

canonical Manga workflow使用。

computer-use/browser capabilityを利用して実操作。

---

# 36. Browser R0

Existing draft regression:

```text
canonical workflow loads
Default Queue works
Scene UI works
Visual Frames works
Character Staging works
```

PASS。

---

# 37. Browser R1

Rough Guide layer visible。

Guide無しでPrimary UXを邪魔しない。

---

# 38. Browser R2

実PNG fixtureをupload/drop。

preview表示。

documentへrelative asset_reference。

---

# 39. Browser R3

2 Character Instancesを作る。

可能なら同一CASTの2 instances。

Guide上に2 figure regionsを作る。

各Instanceへ別々にassociation。

---

# 40. Browser R4

figure drag / resize。

Character Rough Region geometryが勝手に動かない。

---

# 41. Browser R5

Save / Reload。

Guide/figures/association全保持。

---

# 42. Browser R6

Instance削除。

対応Figureは残りassociationだけ解除。

---

# 43. Browser R7

Guide disable。

Guide preview/runtime planがinactive。

既存generationは正常。

---

# 44. Browser R8

Guide remove。

documentからGuide消失。

Character dataは保持。

asset fileを自動削除しない。

---

# 45. Browser evidence

作成:

`docs/manga/verification/m3b_lr1/`

例:

```text
R1_ROUGH_GUIDE_LAYER.png
R2_GUIDE_UPLOADED.png
R3_TWO_FIGURE_ASSOCIATIONS.png
R4_FIGURE_EDIT.png
R5_SAVE_RELOAD.png
R6_INSTANCE_UNASSIGN.png
R7_GUIDE_DISABLED.png
R8_GUIDE_REMOVED.png
M3B_LR1_MANIFEST.json
```

---

# 46. Manifest truth

最低:

```json
{
  "card": "M3B-LR1",
  "contract": "PASS",
  "regression": "PASS",
  "browser": "PASS",
  "visual_ui_evidence": "PASS",
  "runtime_guide_bridge": "PASS",
  "generation_influence": "NOT_IMPLEMENTED",
  "controlnet": "NOT_ADDED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 47. Stage 5 stop rule

同じroot causeのBrowser failureを2回修正してもPASSしなければSTOP。

無限デバッグしない。

---

# 48. Stage 6 — Documentation closure

作成:

`docs/manga/reports/M3B_LR1_ROUGH_GUIDE_FOUNDATION_LONG_RUN_REPORT.md`

内容:

```text
Execution baseline
Stages completed
Changed files

Contract
Asset persistence
Figure association
UI
Save/Reload
Runtime bridge
Browser results
Regression

Generation influence:
NOT IMPLEMENTED

ControlNet:
NOT ADDED

Known limitations
Remaining risks
Next candidate
```

---

# 49. Current authority after LR1

更新:

* `GITHUB_MANGA.txt`
* STATUS
* handoff
* Card Router
* reports index

必須truth:

```text
M3A.1 milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL

Final Owner product review:
DEFERRED

M3B-LR1:
ROUGH GUIDE FOUNDATION IMPLEMENTED

Guide upload:
PASS

Figure association:
PASS

Save/Reload:
PASS

Runtime guide bridge:
PASS

Generation influence:
NOT IMPLEMENTED

ControlNet:
NOT ADDED
```

---

# 50. Card routing

Long-Run開始時:

OA1 completed。

M3B-LR1 current。

LR1の全StageがPASSした場合:

M3B-LR1はcompletedへ移してよい。

current:

```text
Active Card: NONE
```

次Cardを勝手に作らない。

---

# 51. Do not touch

絶対禁止:

* H3
* H3 docs/workflows/output
* ComfyUI core/frontend
* shared model store
* Tegaki core
* EasyReforgeExtension
* RegionalLoRALab
* M3A historical evidence
* Visual Frame semantics
* Scene semantics
* CAST identity semantics
* M4
* common shell

---

# 52. Meaning-boundary STOP

以下が必要になったら即STOP:

```text
schema_version bump
Scene/Frame/CAST meaning change
Character Instance ownership change
GuideをScene所有へ変更
ComfyUI core変更
new external dependency必須
ControlNetなしではFoundation自体が成立しない
persistent asset contractを安全に作れない
```

---

# 53. ControlNet STOP boundary

ControlNetを試したくなってもLR1では止める。

以下は次Card判断:

```text
Which SDXL/Illustrious-compatible control model
Control strength
start/end
preprocessor
white-dummy vs scribble vs lineart
Seed freedom impact
```

LR1の成功条件ではない。

---

# 54. Astra

このLong-Run中はAstraを呼ばない。

LR1成果物完成後、SOLがGitHubをreviewする。

その後必要ならAstraへ一括構造監査を依頼する。

---

# 55. Long-Run philosophy

「隣に問題がありそうだから調べる」でscopeを広げない。

各Stageで:

```text
必要な実装
必要なtest
必要なevidence
```

だけを行う。

PASSなら前へ進む。

---

# 56. Expected useful overnight result

成功時、Ownerが次に見るものはコード断片ではなく:

```text
実際のRough Guide UI
実際にuploadされたラフ画像
Figure Region
Character Instance association
Save/Reload状態
browser evidence
runtime plan
まとめreport
```

であること。

---

# 57. Required final response

```text
Card:
M3B-LR1

Execution baseline:
Final local HEAD:
origin/main:

Stage 0 OA1 closure:
PASS / FAIL

M3A.1 milestone acceptance:
ACCEPTED_BY_DELEGATED_SOL

Final Owner product review:
DEFERRED

Stage 1 Contract:
PASS / FAIL

Stage 2 UI / Asset:
PASS / FAIL

Stage 3 Persistence:
PASS / FAIL

Stage 4 Runtime Bridge:
PASS / FAIL

Stage 5 Browser:
PASS / FAIL

Stage 6 Documentation:
PASS / FAIL

Changed files:

Tests:
PASS / FAIL
<counts>

Browser:
R0:
R1:
R2:
R3:
R4:
R5:
R6:
R7:
R8:

Guide upload:
PASS / FAIL

Figure association:
PASS / FAIL

Same CAST multi-instance:
PASS / FAIL

Save / Reload:
PASS / FAIL

Runtime guide bridge:
PASS / FAIL

Generation influence:
NOT IMPLEMENTED

ControlNet:
NOT ADDED

Evidence manifest:
<path>

Report:
<path>

Known limitations:
- ...

Stopped early:
YES / NO

If YES:
Stage:
Reason:

M3B-LR1 publication:
LOCAL

Owner push required:
YES
```

---

# 58. Final instruction

Stage gateがPASSする限り、途中でOwner/SOLへ確認を返さず最後まで進める。

安全に判断できない意味境界だけSTOPする。

M3B-LR1完了後は次機能へ自動進行しない。

成果物、report、evidenceを残して終了する。
