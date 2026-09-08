# ComfyUI Portable Phase 3J — Semantic Presence Stabilization & Adaptive Character Guide Foundation 指示書

## 0. Baseline

対象: `D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:

`000a7a39b7ff0c8bc95d471719779663aefa258d`

Phase 3I.2 の以下は維持する。

- Runtime PASS / Visual Semantic PASS 分離
- Visual Evaluation Provenance 明示
- Pointer Contract Simulation / Live Browser E2E 分離
- ControlNet metadata BASE_ONLY 監査
- `regional_control_mode = off / shared_global / per_region_hint`
- Single Character Guide Hint
- Reference / Fast Causal Ablation
- Workflows 44〜47

ただし Phase 3J を単純な Pose / Camera 機能追加にしない。最優先は Character Presence、Character Side Binding、Base/Scene/Character Prompt Responsibility、Per-Region Hint Stability である。これらを閉じてから Adaptive Shot / Pose / Camera へ進む。

---

## 1. Phase名

```text
Phase 3J
Semantic Presence Stabilization
&
Adaptive Character Guide Foundation
```

内部:

```text
3J-0  Phase 3I.2 Review Closure
3J-A  Base / Scene / Character Semantic Contract Isolation
3J-B  Character × Side Bias Matrix
3J-C  Region Ordering / Priority Sanity
3J-D  Clean Per-Region Hint v2
3J-E  Hyper12 + Per-Region Hint Operational Candidate
3J-F  Adaptive Shot Type Guide
3J-G  Minimal Pose Foundation
3J-H  Production Authoring Gate
```

---

## 2. Phase 3I.2 の判定補正

以下は受理:

```text
BASE_ONLY_STEPS 0:
HARMFUL in current Impact RegionalSampler workflow

SHARED GLOBAL REGIONAL CN:
REJECT / OVERCONSTRAINED

PER-REGION HINT:
STRUCTURALLY PROMISING

REFERENCE PROFILE:
Native20 architecture regression profile
```

ただし `OPERATIONAL AUTHORING PROFILE = HYPER12` はまだ正式昇格させない。

Phase 3I.2 CondD では:

```text
Alice Left / Bob Right
Hyper12
Base-Only CN
→ 0/2 target subjects
```

過去 WF39 では:

```text
Bob Left / Alice Right
Hyper12
Base-Only CN
→ 2/2 subjects
```

したがって現状は:

```text
FAST-12:
PROMOTE CANDIDATE / CONDITIONAL

OPERATIONAL AUTHORING PROFILE:
NOT YET FULLY STABLE
```

とする。Phase 3Jで左右・人物組合せに対して安定するか確認してからPrimaryへ昇格。

---

## 3. `base_only_steps = 0` の表現

現時点で確定しているのは current Impact RegionalSampler / current latent path / current workflow construction において `base_only_steps=0` が純ノイズ破綻したこと。

「数学的に絶対必要」と一般化せず:

```text
EMPIRICALLY REQUIRED IN CURRENT IMPLEMENTATION
```

と表現すること。

---

## 4. 現Canonical Base Promptの責務競合

`generate_phase3i2_workflows.py` 現状:

```python
COURTYARD_SCENE =
"manga illustration, monochrome expressive linework, high quality,
 simple school courtyard, two students standing"
```

を Base CLIPTextEncode Positive と Panel Scene Prompt の双方へ使用している。

これは Character Region が人物Identity/Attendanceを担当する設計と競合している。

Phase 3Jでは以下へ整理する。

### Base / Global
担当:
- style
- medium
- global atmosphere
- broad environment

原則担当しない:
- Alice / Bob
- character count
- left/right character placement
- specific acting

### Panel / Scene
担当:
- background
- place
- time
- event / relation context

Canonical spatial testでは人物存在を直接要求する語を避ける。

### Character Region
担当:
- identity
- appearance
- acting override
- rough location
- shot / pose metadata

---

## 5. Canonical Base v2

研究用fixture:

```text
Base Positive:
manga illustration,
monochrome expressive linework,
high quality,
empty school courtyard,
clear open foreground,
simple architectural background
```

Base Positiveへ `two students / girl / boy / person / character` を入れない。

Base Negativeは研究Oracle限定で extra person / extra girl / extra boy / duplicate subject 等を検討するが、Regional character自体を消すほど強くしない。

Base NegativeとRegional Character Negativeは別責務として扱う。

---

## 6. Semantic Contract A/B

同じ seed / geometry / model で:

### A — Legacy Base
`school courtyard, two students standing`

### B — Background-Only Base
`empty school courtyard, clear open foreground`

Character Regionsは同一。

比較:
- Alice present
- Bob present
- generic tiny student
- background landmark dominance
- left/right binding

Panel Scene PromptもCanonicalでは `school courtyard background, open walkway, afternoon` 程度とし、人物数を重複記述しない。

Production UIの自由記述は制限しない。これはCanonical backend testの責務分離である。

---

## 7. Character × Side Bias Matrix

Phase 3I.2最大の未解決は:

```text
Bob Left / Alice Right
→ success case exists

Alice Left / Bob Right
→ repeated failure
```

Hyper12をFast candidateとして固定し、まず単一人物を分離検証する。

```text
A1 Alice Left only
A2 Alice Right only
B1 Bob Left only
B2 Bob Right only
```

共通:
- same seed
- background-only Base
- same box size
- same CN schedule
- `regional_control_mode = off` から開始

各ケースで:
- subject present
- identity
- expected side
- approx bbox
- scale
- extra subjects

を記録。

その後:

```text
C1 Alice Left / Bob Right
C2 Bob Left / Alice Right
```

を比較。

代表ケースだけ第二seedでも確認し、seed 42のみでOperational Profileを決めない。

分類:

```text
SIDE_BIAS:
NONE / LEFT / RIGHT / CHARACTER_DEPENDENT / SEED_DEPENDENT / MIXED
```

---

## 8. Region Ordering Sanity

片方向だけ失敗する場合はgeometryだけでなくexecution orderも疑う。

同じgeometryで:

```text
Character list order:
Alice, Bob
Bob, Alice
```

を1ケース比較。

必要なら `scene_first / character_first` も1ケースだけ比較。

分類:

```text
REGION_ORDER_EFFECT:
NONE / SIGNIFICANT / UNCLEAR
```

無目的な全Sweepは禁止。

---

## 9. Clean Per-Region Hint v2

現 `generate_single_character_guide_image()` は他CharacterやPanel Borderを描かないが、`mannequin_capsule` 内部で Character Bounding Rectangle outline をまだ描いている。

つまり完全な character-only silhouette ではない。

`draw_single_character_mannequin()` / `generate_single_character_guide_image()` に:

```text
include_bbox_outline: bool
```

を追加。

推奨:
- Global Guide: 必要なら True
- Per-Region Hint: Default False

CondGで中央doorframe / architectureが強かったため:

```text
PRH-v1: bbox outline ON
PRH-v2: bbox outline OFF
```

を固定比較。

見るもの:
- frame / door hallucination
- subject presence
- scale
- position

---

## 10. Per-Region Hint Style / Strength

最大候補:

```text
mannequin_capsule_no_box
flat_silhouette
minimal_skeleton
```

ただし最初は `mannequin_capsule_no_box @ 0.35`。

必要なら strength:
`0.25 / 0.35 / 0.45` の上下1点だけ追加。

全Style×全Strength総当たりは禁止。

Regional CN scheduleも必要ならBase CNと分離:

```text
Base CN:
strength .75
end .80

Regional Character CN:
strength .35
end .45〜.65
```

Regional側を早めに解除して後半のCharacter Prompt自由度を戻す。

必要ならAdapterへ `regional_control_end_percent` を追加。実Runtime Control object APIを確認して安全に適用する。

Character scopeだけに適用し、Panel Sceneへ自動伝播しない。

---

## 11. Per-Region Hint Success Gate

最低限:

```text
Alice Left only PASS
Alice Right only PASS
Bob Left only PASS
Bob Right only PASS
```

かつ Two Characterで少なくとも1方向のswap pairが2/2 present。

これを満たしたら:

```text
PER_REGION_HINT:
USABLE FOUNDATION
```

それ未満は `PROMISING / EXPERIMENTAL` のまま。

---

## 12. Hyper12 + Per-Region Hint

Phase 3I.2 CondGはNative20だったため、Fast candidateであるHyper12とPer-Region Hintを必ず実測する。

まず過去成功geometry:

```text
Bob Left / Alice Right
```

次に:

```text
Alice Left / Bob Right
```

を比較。

Operational Profile正式昇格条件:

```text
both swap directions:
at least directionally usable

representative 2 seeds:
no complete collapse

no severe guide artifact
zero-touch
```

満たさない場合:

```text
HYPER12 = FAST DRAFT CANDIDATE
```

に留める。

Native20は `ARCHITECTURE_REFERENCE` を維持するが、Visual Golden Referenceとは呼ばない。

---

## 13. Adaptive Shot Type Guide

Presence Gate通過後のみ開始。

最初は3種:

```text
full_body
half_body
bust
```

Shot Typeは Character guide proportions / staging interpretation / rough crop expectation を担当し、Camera FOV simulationはまだ行わない。

Character Instance metadataへoptional:

```json
{"shot_type":"full_body"}
```

等を追加可能。

### full_body
現在のmannequin相当。頭・胴・腕・脚を全高へ。

### half_body
頭・上半身・腕・腰まで。下半身をguideに描かない。

### bust
頭・肩・胸上部。box上側中心を使用。

1 Character / same seed で Alice Full / Half / Bust を比較し:
- presence
- crop
- scale
- head size
- guide artifact

を評価。

BBoxサイズだけから自動推測せず、まず明示 `shot_type` で指定する。

---

## 14. Minimal Pose Foundation

Shot Type PASS後のみ。

Pose Editorはまだ作らずpreset程度:

```text
standing_neutral
facing_left
facing_right
```

必要なら seated を4つ目。

screen position と body orientation は別metadata。

```text
screen position: left/right
orientation: facing_left/facing_right/front
```

handshake / hug / fight / holding object は今回本格対応しない。

OpenPose本格統合も次Phase以降。

---

## 15. Camera / FOV

Phase 3J後半で研究メモまで。

将来:
- Scene Camera Distance
- Character Shot Type

を分離する。

`near / medium / far` 程度は候補だが、Lens mm等の写真用語を主要UIにしない。

---

## 16. Canonical Verification Workflow

`1 Workflow = 1 hypothesis` を維持。

Saved Workflow候補 最大6本:

```text
48_VERIFY_BASE_BACKGROUND_ONLY_CHARACTER_PRESENCE.json
49_VERIFY_ALICE_LEFT_ONLY_HYPER12.json
50_VERIFY_ALICE_RIGHT_ONLY_HYPER12.json
51_VERIFY_BOB_LEFT_ONLY_HYPER12.json
52_VERIFY_BOB_RIGHT_ONLY_HYPER12.json
53_VERIFY_HYPER12_PER_REGION_HINT_SWAP.json
```

Workflow53は可能なら:

```text
Hyper12
background-only Base
per_region_hint
bbox outline OFF
regional strength .35
```

を統合し、Phase 3J主要Oracleとする。

---

## 17. Runner / Result

新規:

```text
scripts/run_phase3j_presence_matrix.py
output/Tegaki/Phase3J/phase3j_presence_matrix.json
```

実行:
- Base Contract A/B
- Single Character Side 4
- Two Character Swap 2
- Hyper12 + PRH

記録:
- runtime
- visual semantic
- subject presence
- expected/observed side
- extra subjects
- guide mode
- seed

Visual provenanceはPhase 3I.2と同じ metadata を必須とする。

---

## 18. Contact Sheets

最低限:

```text
Sheet P:
Legacy Base | Background-only Base

Sheet Q:
Alice L | Alice R
Bob L   | Bob R

Sheet R:
Alice L/Bob R | Bob L/Alice R

Sheet S:
Per-region bbox ON | bbox OFF | Hyper12 + per-region no-box
```

---

## 19. UI範囲

Phase 3Jでは大型UI化しない。

追加可:
- Shot Type dropdown程度

まだ作らない:
- pose canvas
- camera editor
- FOV slider
- timeline
- project preset
- polished custom skin

---

## 20. Live Browser E2E

Phase 3I.2の正確な状態:

```text
POINTER CONTRACT SIMULATION: PASS
LIVE BROWSER POINTER E2E: PENDING
```

可能なら今回1ケースだけ実ブラウザで確認。

不可ならPENDING維持。

ユーザーへ依頼する場合も最後に1操作だけ:
Alice矩形を左右にdrag → Save → Reloadで位置保持確認。

Backend matrix実行をユーザーへ任せない。

---

## 21. Performance

Hyper12 + per-region の:
- total runtime
- VRAM
- regional count

を記録。

Native20 + per-region 72.54sより改善するか確認。

速度だけで採択しない。

---

## 22. Report

新規:

`PHASE3J_SEMANTIC_PRESENCE_AND_ADAPTIVE_GUIDE_REPORT.md`

最低限:

```text
1. Phase3I.2 Review Closure
2. Operational Profile Claim Correction
3. Base-only Steps Wording Correction
4. Base / Scene / Character Semantic Contract
5. Legacy Base Result
6. Background-only Base Result
7. Alice Left
8. Alice Right
9. Bob Left
10. Bob Right
11. Two-Character Swap Matrix
12. Seed Robustness
13. Character-Side Bias
14. Region Order Effect
15. Per-Region BBox Outline Analysis
16. Clean Per-Region Hint v2
17. Per-Region Strength / Schedule
18. Hyper12 + Per-Region Result
19. Operational Profile Decision
20. Adaptive Shot Type Contract
21. Full Body
22. Half Body
23. Bust
24. Minimal Pose Foundation
25. Runtime / VRAM
26. Live Browser E2E
27. Known Issues
28. Next Phase
29. Gemini独自判断
```

---

## 23. Sign-off

```text
PHASE3I.2 REVIEW CLOSURE:
PASS / HOLD

BASE PROMPT RESPONSIBILITY:
CLOSED / HOLD

BACKGROUND-ONLY BASE:
HELPFUL / NEUTRAL / HARMFUL

ALICE LEFT:
PASS / PARTIAL / FAIL

ALICE RIGHT:
PASS / PARTIAL / FAIL

BOB LEFT:
PASS / PARTIAL / FAIL

BOB RIGHT:
PASS / PARTIAL / FAIL

TWO-CHARACTER ALICE-L / BOB-R:
PASS / PARTIAL / FAIL

TWO-CHARACTER BOB-L / ALICE-R:
PASS / PARTIAL / FAIL

SIDE BIAS:
NONE / LEFT / RIGHT / CHARACTER_DEPENDENT / SEED_DEPENDENT / MIXED

REGION ORDER EFFECT:
NONE / SIGNIFICANT / UNCLEAR

PER-REGION BBOX OUTLINE:
REMOVE / KEEP / NEUTRAL

PER-REGION HINT V2:
USABLE FOUNDATION / PROMISING / REJECT

HYPER12 + PER-REGION HINT:
PASS / PARTIAL / FAIL

ARCHITECTURE REFERENCE:
NATIVE20

OPERATIONAL AUTHORING PROFILE:
HYPER12 / CONDITIONAL HYPER12 / UNRESOLVED

SHOT TYPE FULL BODY:
PASS / PARTIAL / NOT TESTED

SHOT TYPE HALF BODY:
PASS / PARTIAL / NOT TESTED

SHOT TYPE BUST:
PASS / PARTIAL / NOT TESTED

MINIMAL POSE:
READY / EXPERIMENTAL / DEFERRED

POINTER CONTRACT SIMULATION:
PASS

LIVE BROWSER POINTER E2E:
PASS / PENDING

USER VISUAL REVIEW REQUIRED:
YES / NO

NEXT RECOMMENDED PHASE:
```

---

## 24. Phase 3J終了条件

最低限:

```text
Base / Scene / Character責務が整理
Single Character左右が把握
Two Character swapの失敗原因がある程度判明
Per-region hint no-boxの有効性判明
Hyper12 Operational Profileの安定性判定
```

Shot Typeは `full_body / half_body / bust` のContractまで出来ればよい。

Poseが不安定なら次Phaseへ送って構わない。

---

## 25. 次Phase候補

Phase 3J成功後:

```text
Phase 3K
Pose & Interaction Authoring
+
Camera Distance / Scene Composition
```

候補:
- standing
- sitting
- facing
- handshake
- two-character relation
- near/far
- scene camera

ここで初めてInteractionを本格化する。

---

## 26. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3J stabilize semantic presence and adaptive character guides
```

内容:
- semantic contract fixtures
- presence matrix
- per-region no-box hint
- regional schedule control
- Hyper12 operational verification
- shot type metadata
- tests
- report

Commit A SHA取得後、Navigation Commit Bで `ComfyUIPortable/GITHUB.TXT` のReview TargetをCommit Aへ更新。

---

## 27. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3J_SEMANTIC_PRESENCE_AND_ADAPTIVE_GUIDE_REPORT Raw:

Presence Matrix Runner Raw:
Presence Result Raw:
Per-Region Hint v2 Raw:
Layout Guide Raw:
Shot Type Contract Raw:

Workflow48 Raw:
Workflow49 Raw:
Workflow50 Raw:
Workflow51 Raw:
Workflow52 Raw:
Workflow53 Raw:

PHASE3I.2 REVIEW CLOSURE:
BASE PROMPT RESPONSIBILITY:
BACKGROUND-ONLY BASE:
ALICE LEFT:
ALICE RIGHT:
BOB LEFT:
BOB RIGHT:
TWO-CHARACTER ALICE-L / BOB-R:
TWO-CHARACTER BOB-L / ALICE-R:
SIDE BIAS:
REGION ORDER EFFECT:
PER-REGION BBOX OUTLINE:
PER-REGION HINT V2:
HYPER12 + PER-REGION HINT:
ARCHITECTURE REFERENCE:
OPERATIONAL AUTHORING PROFILE:
SHOT TYPE FULL BODY:
SHOT TYPE HALF BODY:
SHOT TYPE BUST:
MINIMAL POSE:
POINTER CONTRACT SIMULATION:
LIVE BROWSER POINTER E2E:
USER VISUAL REVIEW REQUIRED:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3I.2の最大の成果は「Fast-12が常に解決策ではない」と分かったことです。

Hyper12は高速ですが `Alice Left / Bob Right` では0/2へ崩壊し、過去の `Bob Left / Alice Right` では成功しました。

いまCameraやPoseの機能数を増やすより、まず「なぜ人物が出たり消えたりするのか」をAuthoring Contract側から整理する必要があります。

特に現Canonical Base Promptが `two students standing` を持つことは Character Region と Base Scene の責務競合です。

Phase 3Jでは:

```text
Base = style/background
Scene = environment/context
Character Region = identity/acting/location
```

を検証可能な形へ整理し、

```text
Alice Left / Right
Bob Left / Right
two-character swap
```

を固定条件で確認します。

さらに、Per-Region Hintのmannequinに残っているBounding Rectangleを外したClean Hint v2を試します。

このPresence Gateが閉じてから `full body / half body / bust` のAdaptive Shot Typeへ進み、Pose / Camera / Interactionは次段へ送ってください。
