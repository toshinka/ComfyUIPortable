# ComfyUI Portable Phase 3K — Pose Contract, Interaction Binding & Scene Composition Foundation 指示書

## 0. Baseline

対象: `D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:
`c627ffcc7cfc6ae09fe3c6db7510d6f6bd79fa9b`

Phase 3J.1 で成立した以下は維持する。

- CAST prompt / Binding prompt_override 契約
- `character_prompt_mode = standalone`
- `remainder_mask_mode = True`
- Background-only Base
- Global Guide: `include_panel_border = False`, `include_character_bbox_outline = False`
- Single Character L/R 4/4
- Two Character LR / Swap 2/2
- Per-Region Hint v2
- Hyper12 operational profile
- Native20 architecture reference
- Workflows 54〜59

Phase 3K は単なるPose UI追加ではなく、最初に `Shot Type / Pose metadata → Staging → Compiler → Impact Plan → ControlNet Guide` の意味保持を end-to-end で閉じ、その後に single pose / two-character relation / handshake / scene distance へ進む。

## 1. Phase名

```text
Phase 3K
Pose Contract
&
Interaction Binding
&
Scene Composition Foundation
```

内部:

```text
3K-0  Phase 3J.1 Review Correction
3K-A  Shot / Pose Metadata Truth Closure
3K-B  Single Character Pose Oracle
3K-C  Two Character Orientation Binding
3K-D  Pair Interaction Guide Prototype
3K-E  Handshake Oracle
3K-F  Scene Camera Distance Contract
3K-G  Minimal Authoring UI Wiring
3K-H  Production Interaction Gate
```

## 2. Phase 3J.1の受理と補正

受理:

```text
CAST PROMPT CONTRACT: PASS
BINDING PROMPT CONTRACT: PASS
COMPILE CHARACTER PROMPT TRUTH: PASS
IMPACT CHARACTER PROMPT TRUTH: PASS
CANONICAL CHARACTER PROMPT MODE: STANDALONE
SCENE REMAINDER MASK: standard canonical path
ALICE L/R: PASS
BOB L/R: PASS
TWO CHARACTER LR / SWAP: PASS
HYPER12: OPERATIONAL AUTHORING PROFILE
```

補正1: Native20は Cond11 の代表1条件でPASSしただけなので `universal equivalence` としない。正式表現は:

```text
NATIVE20:
REPRESENTATIVE COMPATIBILITY PASS
ARCHITECTURE REFERENCE
```

補正2: `remainder_mask_mode=False` は Panel Scene / Character region が重複して destructive competition を起こす。時系列的に「背景samplerが後から上書き」と断定せず、`remainder=True removes region overlap` と記録する。

補正3: Phase 3J.1 Manifest は `USER VISUAL REVIEW REQUIRED: YES`。GitHub上のAI visual annotationは確認できるが、外部AIがPNGそのものを見ていない場合はユーザー確認済みと扱わない。

## 3. 重大Preflight — Shot Type因果の再確認

Phase 3J.1のShot Type実機条件はPrompt自身に:

```text
full body
half body upper body portrait
close-up bust shot face and shoulders
```

を含んでいた。

よって:

```text
SHOT TYPE GUIDE CONTRACT: PASS
SHOT TYPE GUIDE CAUSALITY: UNPROVEN
```

と分離し、Phase 3Kで同一Prompt・同一seed・同一位置、変更点は `shot_type` のみで再検証する。

## 4. Shot Type metadata propagation監査

現状、`CharacterStagingStateManager.apply_to_region_spec()` はoverrideの `shot_type` をREGION_SPECへ書けるが、`scene_compiler.py` の `compiled_c` は top-level `shot_type` を明示コピーしていない。

したがって:

```text
Staging override shot_type
→ REGION_SPEC
→ PAGE_COMPILE_PLAN
→ LayoutRegionBridge
→ IMPACT_REGION_PLAN
→ Guide
```

の途中で消失していないかを実測し、必要なら修正する。

## 5. Pose presetは現時点で未配線

Workflow fixtureに `pose_preset` は存在するが、現 `CharacterStagingStateManager.apply_to_region_spec()` は `area` と `shot_type/shot` しか適用していない。

さらに `_commit_override()` は既存override辞書を `{"area": area}` で置換するため、将来の `shot_type / pose_preset / orientation / interaction metadata` をdrag時に消す危険がある。

Phase 3K最初で:

```text
replace → merge
```

へ修正。

move / resize / save / reload後もmetadataを保持する。

## 6. Canonical Character Pose Contract

Character Binding optional canonical fields:

```json
{
  "character_id": "char_alice",
  "prompt_override": "standing calmly",
  "area": {"x":0.10,"y":0.15,"w":0.35,"h":0.75},
  "shot_type": "full_body",
  "pose_preset": "facing_right",
  "metadata": {}
}
```

既存schema version 1を壊さずoptional fieldとして追加可。Validatorでenum検証。

Shot Type:

```text
full_body
half_body
bust
```

Pose Preset:

```text
standing_neutral
facing_left
facing_right
sitting
```

これ以上増やさない。

## 7. End-to-End Metadata Truth

新規:

```text
scripts/test_phase3k_character_pose_contract.py
```

`shot_type=half_body / pose_preset=facing_right` を入力し:

```text
REGION_SPEC
PAGE_COMPILE_PLAN
LayoutRegionBridge
IMPACT_REGION_PLAN
Adapter debug
Guide generator input
```

まで同じ値が保持されること。

PAGE_COMPILE_PLAN / IMPACT_REGION_PLAN のcharacter entryに `shot_type`, `pose_preset` を正本として保持する。top-levelかmetadataかは一方に統一し、途中で曖昧に行き来させない。

## 8. Layout Guide Generator拡張

以下へ `pose_preset` を追加:

```text
extract_staging_boxes
draw_single_character_mannequin
generate_single_character_guide_image
TegakiMangaLayoutGuideGenerator
```

debug_jsonにも出す。

### standing_neutral
現mannequinを基準。

### facing_left / facing_right
左右mirrorで明確に異なるguide pixel patternを持たせる。最低限 head/profile cue、shoulder/torso asymmetry、arm/hand asymmetryを使う。Text labelや矢印はControlNet guideへ描かない。

### sitting
hipを下げ、膝を曲げ、下腿をvertical/diagonalへ。椅子自体は最初は描かない。

## 9. Pose Pixel Unit Tests

新規:

```text
scripts/test_phase3k_pose_guide_geometry.py
```

検証:

```text
neutral != facing_left
facing_left ≒ horizontal mirror of facing_right
sitting has bent-leg density pattern
shot_type × pose_preset combination remains valid
```

## 10. Shot Type Causality Oracle

Promptは全条件同じ:

```text
1girl, blonde twin tails, school uniform, standing calmly
```

位置・seedも同じ。変えるのは `shot_type` のみ。

```text
full_body
half_body
bust
```

見るもの:

```text
subject present
same identity
crop / scale changes
head-size trend
guide artifact
```

Promptへ `full body / half body / bust / close-up` を入れない。

ここで差が出て初めて:

```text
SHOT TYPE GUIDE CAUSALITY: PASS
```

とする。

## 11. Single Character Pose Oracle

Hyper12 / standalone / remainder=True / clean guide。

固定Alice、同位置、同Prompt:

```text
1girl, blonde twin tails, school uniform
```

変えるのはPoseだけ:

```text
standing_neutral
facing_left
facing_right
sitting
```

厳密Oracleでは `looking left / facing right / sitting / seated` をPromptへ入れない。

Geometry-only Oracle成立後に1ケースだけ `Prompt + Guide` を比較してProduction運用を確認。

## 12. Two Character Orientation Binding

Alice左 / Bob右。

```text
Alice pose = facing_right
Bob pose = facing_left
```

期待: 2人が向かい合う。

次に:

```text
Alice pose = facing_left
Bob pose = facing_right
```

期待: 外向き。

Promptは `standing calmly` 程度のみ。Identity / positionを維持する。

## 13. Interactionの段階

Level 1:
```text
relation without physical contact
facing each other
looking away
```

Level 2:
```text
physical contact
handshake
```

Phase 3KではHandshakeまで。Hug / Fightは次Phase以降。

## 14. Pair Interaction Guide Prototype

Handshakeでは独立Character guideだけでは接触点共有が難しい可能性がある。

まずBase global character guideに:

```text
two mannequins
shared interaction anchor
```

を描くprototype。

Interaction metadata例:

```json
{
  "interaction_id": "interaction_01",
  "interaction_type": "handshake",
  "interaction_role": "left_participant"
}
```

相手側は同じinteraction_id、right_participant。

Compiler内部でpairを解決し、persistent大規模schemaを増やさず derivative `interaction_pairs` を作ってよい。

例:

```json
{
  "interaction_id": "interaction_01",
  "type": "handshake",
  "participants": ["instance_alice","instance_bob"],
  "panel_id": 1,
  "anchor": [0.50,0.48]
}
```

参照は `master_character_id` より `character_instance_id` を優先。同じAliceがSubScene内で複数instanceでも一意に解決できること。

## 15. Handshake Pair Guide

V1 anchorは自動算出:

```text
left participant bbox right-middle
right participant bbox left-middle
midpoint
```

Pair guide:

```text
left mannequin arm → shared anchor
right mannequin arm → shared anchor
```

位置逆転時はmirror。

Character boxesは腕付近で少量overlapしてよい。

Handshake判定:

```text
Alice present
Bob present
identity correct
positions preserved
bodies face each other
hands/arms plausibly contact
no third person
no severe fusion
```

## 16. Interaction Relation Regionは第二手段

Pair Guideだけでcontactが弱い場合のみ:

```text
scope_type = interaction_relation
```

prototype可。

Mask:
```text
participant area union / bridge
```

Prompt:
```text
two people shaking hands
```

Identity名は入れない。

Pair guideで十分なら新region typeは採択しない。

## 17. Scene Camera Distance Contract

Character Shot TypeとScene Cameraを分離。

Character:
```text
full_body
half_body
bust
```

Scene:
```text
near
medium
far
```

Phase 3KではLens/FOV物理simulationを主張せず:

```text
SCENE CAMERA DISTANCE / COMPOSITION PRESET
```

とする。

Panel/Scene metadataにoptional:

```json
{"camera_distance":"medium"}
```

Explicit Character areaがある場合:

```text
Explicit staging > camera default
```

を厳守。

area未指定/autoの時だけ near=large, medium=standard, far=small のdefault stagingへ反映。

Camera Oracleは明示areaなしで near / medium / far を同seed比較し、apparent scale / background amount / perspective stability を見る。

## 18. Minimal Authoring UI Wiring

ComfyUI node UI上で最低限:

Character Staging:
```text
Selected Character
Shot Type
Pose Preset
```

Panel Content / Scene:
```text
Camera Distance
```

を編集可能にする。

Interactionは最初はfixture/backend contract中心でよい。

`Shot Type / Pose Preset` は `staging_overrides` へ保存し、drag/resize後も消えない。



## 19. Live Browser E2E

可能なら今回1ケース。

実ブラウザ:

```text
Alice select
pose preset = facing_right
shot type = half_body
bbox drag
Save
Reload
```

後:

```text
area
pose_preset
shot_type
```

が全保持。

不可能なら:

```text
LIVE BROWSER POINTER/METADATA E2E: PENDING
```

を維持。

## 20. Fixed Canonical Workflows

ユーザーへ内部切替を任せない。

Saved Workflowは最大6本程度。

候補:

```text
60_VERIFY_POSE_FACING_EACH_OTHER.json
61_VERIFY_POSE_FACING_OUTWARD.json
62_VERIFY_POSE_SITTING_SINGLE.json
63_VERIFY_INTERACTION_HANDSHAKE.json
64_VERIFY_CAMERA_DISTANCE_NEAR.json
65_VERIFY_CAMERA_DISTANCE_FAR.json
```

Shot Type full/half/bust causalityはrunner内固定条件でもよい。

`1 Workflow = 1 Hypothesis` を維持。

## 21. Zero-Touch Runner

新規:

```text
scripts/run_phase3k_pose_interaction_suite.py
```

順序:

```text
metadata truth tests
shot type causality 3
single pose 4
orientation pair 2
handshake prototype
camera distance 3
representative Native20
```

目安12〜16条件。Hyper12をPrimary。

## 22. Regression

必須:

```text
WF54 Alice Left
WF55 Alice Right
WF56 Bob Left
WF57 Bob Right
WF58 Two Character LR
WF59 Two Character Swap
```

Pose/Camera追加でPresence基盤を壊さない。

## 23. Visual Evaluation Provenance

Phase 3J.1同様:

```text
evaluation_type
annotator
timestamp
machine_detector
confidence
image_file
```

を保存。

Handshake / facing directionが曖昧なら:

```text
USER VISUAL REVIEW REQUIRED: YES
```

にする。

ユーザーを大量Workflowのテストランナーにしない。

## 24. Contact Sheets

最低限:

### Sheet Z1 — Shot Type Causality
```text
Full | Half | Bust
same prompt
```

### Sheet Z2 — Pose
```text
Neutral | Face Left | Face Right | Sitting
```

### Sheet Z3 — Two Character Orientation
```text
Facing Each Other | Facing Outward
```

### Sheet Z4 — Interaction
```text
Pair Guide OFF | Pair Guide Handshake
```

### Sheet Z5 — Camera Distance
```text
Near | Medium | Far
```

## 25. Phase 3K Report

新規:

```text
PHASE3K_POSE_INTERACTION_AND_SCENE_COMPOSITION_REPORT.md
```

最低限:

```text
1. Phase3J.1 Review Closure
2. Native20 Claim Correction
3. Shot Type Causality Confound
4. Shot Type Metadata Propagation Audit
5. Pose Metadata Contract
6. Staging Override Merge Semantics
7. Compile Pose Truth
8. Impact Pose Truth
9. Guide Pose Truth
10. Shot Type Causality
11. Neutral Pose
12. Facing Left
13. Facing Right
14. Sitting
15. Two Character Facing Each Other
16. Two Character Facing Outward
17. Pair Interaction Contract
18. Handshake Pair Guide
19. Interaction Relation Prototype (if used)
20. Handshake Result
21. Scene Camera Distance Contract
22. Near
23. Medium
24. Far
25. Hyper12 Runtime
26. Native20 Representative Regression
27. UI Metadata Persistence
28. Live Browser E2E
29. Regression WF54-59
30. Known Issues
31. Phase3L Gate
32. Gemini独自判断
```

## 26. Sign-off

```text
PHASE3J.1 REVIEW CLOSURE:
PASS / HOLD

NATIVE20 CLAIM:
REPRESENTATIVE_COMPATIBILITY / HOLD

SHOT TYPE METADATA PROPAGATION:
PASS / FAIL

SHOT TYPE GUIDE CAUSALITY:
PASS / PARTIAL / FAIL

POSE METADATA CONTRACT:
PASS / FAIL

STAGING OVERRIDE MERGE:
PASS / FAIL

POSE GUIDE GEOMETRY:
PASS / PARTIAL / FAIL

NEUTRAL POSE:
PASS / PARTIAL / FAIL

FACING LEFT:
PASS / PARTIAL / FAIL

FACING RIGHT:
PASS / PARTIAL / FAIL

SITTING:
PASS / PARTIAL / FAIL

TWO CHARACTER FACING:
PASS / PARTIAL / FAIL

TWO CHARACTER OUTWARD:
PASS / PARTIAL / FAIL

PAIR INTERACTION GUIDE:
PROMISING / NEUTRAL / REJECT

HANDSHAKE:
PASS / PARTIAL / FAIL

INTERACTION RELATION REGION:
HELPFUL / NEUTRAL / NOT USED / REJECT

SCENE CAMERA DISTANCE CONTRACT:
PASS / PARTIAL / FAIL

CAMERA NEAR:
PASS / PARTIAL / FAIL

CAMERA MEDIUM:
PASS / PARTIAL / FAIL

CAMERA FAR:
PASS / PARTIAL / FAIL

HYPER12 OPERATIONAL PROFILE:
PASS / CONDITIONAL / HOLD

NATIVE20 ARCHITECTURE REFERENCE:
PASS / HOLD

WF54-59 REGRESSION:
PASS / HOLD

POINTER CONTRACT SIMULATION:
PASS / FAIL

LIVE BROWSER METADATA E2E:
PASS / PENDING

USER VISUAL REVIEW REQUIRED:
YES / NO

NEXT RECOMMENDED PHASE:
```

## 27. Phase 3K終了Gate

最低限:

```text
shot_type metadata is truly end-to-end
pose_preset is truly end-to-end
drag/resize does not erase metadata

single character:
facing L/R + sitting usable

two characters:
facing relation usable

handshake:
at least PARTIAL with clear causal improvement

camera_distance:
contract defined, no false optical claims

WF54-59:
non-destructive
```

HandshakeがFAILでも:

```text
Pose Contract PASS
Facing Relation PASS
Pair Guide architecture understood
Handshake limitation clearly isolated
```

ならPhase 3K自体は:

```text
PASS WITH HANDSHAKE DEFERRED
```

でよい。

## 28. 次Phase候補

Phase 3K後:

```text
Phase 3L
Advanced Interaction & SubScene Authoring
```

候補:

```text
handshake refinement
holding object
hug
fight / look-away
same-cast multiple instances
SubScene interaction groups
scene-level near/far composition
```

Handshakeが十分なら代わりに:

```text
Phase 3L
Progressive Authoring UX Integration
```

としてCharacter / Panel / Scene UI統合へ進んでもよい。

## 29. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3K add pose interaction and scene composition foundation
```

内容:

```text
shot/pose metadata contract
staging merge fix
pose guide generator
pair interaction prototype
camera distance contract
tests
workflows 60-65
runner
report
```

Commit A SHA取得後、Navigation Commit Bで:

```text
ComfyUIPortable/GITHUB.TXT
```

Review TargetをCommit Aへ更新。

## 30. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3K_POSE_INTERACTION_AND_SCENE_COMPOSITION_REPORT Raw:

Pose Contract Test Raw:
Pose Guide Test Raw:
Interaction Test Raw:
Camera Distance Test Raw:
Phase3K Runner Raw:

Layout Guide Generator Raw:
Character Staging Raw:
Impact Region Plan Raw:
Impact Adapter Raw:

Workflow60 Raw:
Workflow61 Raw:
Workflow62 Raw:
Workflow63 Raw:
Workflow64 Raw:
Workflow65 Raw:

PHASE3J.1 REVIEW CLOSURE:
NATIVE20 CLAIM:
SHOT TYPE METADATA PROPAGATION:
SHOT TYPE GUIDE CAUSALITY:
POSE METADATA CONTRACT:
STAGING OVERRIDE MERGE:
POSE GUIDE GEOMETRY:
NEUTRAL POSE:
FACING LEFT:
FACING RIGHT:
SITTING:
TWO CHARACTER FACING:
TWO CHARACTER OUTWARD:
PAIR INTERACTION GUIDE:
HANDSHAKE:
INTERACTION RELATION REGION:
SCENE CAMERA DISTANCE CONTRACT:
CAMERA NEAR:
CAMERA MEDIUM:
CAMERA FAR:
HYPER12 OPERATIONAL PROFILE:
NATIVE20 ARCHITECTURE REFERENCE:
WF54-59 REGRESSION:
LIVE BROWSER METADATA E2E:
USER VISUAL REVIEW REQUIRED:
NEXT RECOMMENDED PHASE:
```

# 最終方針

Phase 3J.1で人物Presence / Identity / 左右配置の基礎は大きく改善したので、次はPoseへ進んでよい。

ただし現状のコードでは `pose_preset` がWorkflow fixtureに存在しても Staging → Compiler → Impact → Guideへ正式には流れていない。

またShot Typeの最終画像比較もPrompt自身に `full body / half body / bust shot` を入れていたため、Guide metadata単独の因果はまだ証明されていない。

Phase 3Kではここを最初に閉じ、その後:

```text
1人の向き
↓
2人が向かい合う
↓
接触なしrelation
↓
Handshake
```

の順に複雑化する。

CameraもCharacter Shot Typeとは別の `Scene Composition Distance` として near / medium / far を定義し、光学FOVそのものとは過大主張しない。

このPhaseでPoseとRelationがCharacter領域へ正しく乗ることが確認できれば、次はSubSceneを使った同一キャラ複数演技や、Handshake / Fight / Look-awayの本格Interactionへ進める。
