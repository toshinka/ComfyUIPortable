# ComfyUI Portable Phase 3L — Interaction Truth Closure, Mainline SubScene Integration & Prior-Art Adoption Gate 指示書

## 0. 最初に必ず読むもの

作業開始前に、以下の中間計画書を必ず確認してください。

```text
Tegaki_ComfyUI_Manga_Authoring_Intermediate_Plan_PriorArt_Integration.md
```

このPhaseでは、これまでの「不足部分はTegaki側で補う」という進め方から、一部を明確に転換します。

### ⚠ 方針転換

今後は新しい低レベル機能を追加する前に、

```text
既存ComfyUIノードで同等機能が存在しないか
```

を確認し、

```text
ADOPT
ADAPT
REFERENCE
BUILD
```

のどれに分類するかを決めてください。

特に以下は「自作前提」から外します。

```text
Regional Prompt wrapper
ControlNet propagation
Mask editing
Pose editing
Regional IPAdapter
Regional CFG
Sampler plumbing
```

これらは既存実装の採用・比較を優先します。

一方、以下はTegaki独自Coreとして維持します。

```text
CAST
Panel
Scene
SubScene
Character Instance
Interaction
Staging
Authoring Data
Compiler
```

---

# 1. Baseline

対象:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
97ea1e2e131b320cd642e833ead33c09d6456a4c
```

Phase 3K までに成立した以下は維持します。

```text
CAST prompt / prompt_override
standalone character prompt
remainder_mask_mode
Hyper12 operational profile
Native20 architecture reference
Shot Type contract
Pose metadata contract
Staging deep merge
Directional mannequin geometry
Camera Distance contract
```

ただし以下はPhase 3Lで再確認・修正します。

```text
Pose guide-only causality
WF63 handshake wiring
Interaction canonical format
Visual evaluation provenance
SubScene mainline integration
```

---

# 2. Phase名

```text
Phase 3L
Interaction Truth Closure
&
Mainline SubScene Integration
&
Prior-Art Adoption Gate
```

内部:

```text
3L-0  Phase 3K Review Closure
3L-A  Prior-Art Audit
3L-B  Pose Guide-Only Causality
3L-C  Interaction Contract Repair
3L-D  Handshake Canonical Wiring
3L-E  SubScene Contract v1.1
3L-F  Mainline SubScene Compiler Integration
3L-G  Same-Cast Multi-Instance Oracle
3L-H  Progressive Authoring UI
3L-I  External Backend Adoption Decision
```

---

# 3. Phase 3K Visual Provenance補正

Phase 3K Runnerの:

```text
runtime PASS
```

と、

```text
visual semantic PASS
```

を今後必ず分離してください。

### 禁止

```text
runtime PASS
→ visual PASSを自動付与
```

### 必須

```json
{
  "runtime_status": "PASS",
  "visual_status": "PASS|PARTIAL|FAIL|PENDING",
  "evaluation_source": "AI_VISUAL_ANNOTATION|USER_VISUAL_REVIEW|NONE",
  "machine_detector": false,
  "confidence": null
}
```

実画像を見ていない場合:

```text
visual_status = PENDING
```

とする。

---

# 4. 3L-A — Prior-Art Audit

実装前に、少なくとも以下をローカル環境 / GitHub上で確認してください。

```text
ComfyUI-Inspire-Pack
  RegionalPromptSimple
  RegionalPromptColorMask
  RegionalConditioningSimple
  Regional IPAdapter

ComfyUI-Advanced-ControlNet

Impact Pack
  RegionalPrompt
  RegionalSampler
  PreviewBridge
  MaskEditor連携

OpenPose Editor系

ComfyUI-EasyUseAnima
  Regional Prompt Studio
```

---

# 5. Prior-Art Audit Report

新規:

```text
docs/reports/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md
```

各候補:

```text
Component:
Existing Tool:
Current Tegaki Equivalent:
Feature Parity:
Missing Features:
Maintenance Risk:
Decision:
ADOPT / ADAPT / REFERENCE / BUILD
```

---

# 6. Inspire RegionalPromptSimple比較

### ⚠ 方針転換

これまで `TegakiMangaImpactRegionalAdapter` を拡張してきましたが、
今後は「Tegaki独自Regional executionを増やす」のではなく、

```text
Tegaki Semantic Compiler
↓
Prompt + Mask + Basic Pipe
↓
Existing Regional Prompt implementation
```

へ寄せられるかを優先確認してください。

比較対象:

```text
A. Current Tegaki adapter
B. Inspire RegionalPromptSimple
```

固定条件:

```text
same model
same seed
same prompt
same masks
same sampler
```

見るもの:

```text
Character Presence
Prompt Separation
ControlNet inheritance
Runtime
Saved Workflow compatibility
Maintenance complexity
```

---

# 7. InspireのControlNet inheritanceを監査

Inspire側の:

```text
controlnet_in_pipe
```

が現在のTegaki Control propagationと同等以上なら、
Tegaki独自Control metadata copyを削減可能か検討。

ただしPer-Region Hintの:

```text
Alice-only guide
Bob-only guide
```

をそのまま置き換えられるとは限らない。

比較してから判断。

---

# 8. Advanced-ControlNet比較

### ⚠ 方針転換

Character-specific ControlNet適用をTegaki内部で複雑化する前に、

```text
Advanced-ControlNet
+
effect mask
+
start/end
```

で同じ結果が得られるか確認してください。

比較:

```text
A. Tegaki current per-region control
B. Advanced-ControlNet masked control
```

見るもの:

```text
Position
Scale
Pose
Identity
Artifacts
Runtime
Implementation complexity
```

同等以上なら:

```text
ADOPT
```

を優先。

---

# 9. Mask Editorは自作拡張しない

Phase 3Lでは独自の自由描画Mask Editorを作らない。

必要なら:

```text
Impact PreviewBridge / MaskEditor
```

を利用可能か調査。

Tegakiは:

```text
Auto-generated mask
↔ edited mask asset
```

の紐付けだけ管理する。

---

# 10. Pose Editorも自作しない

Phase 3LではPose preset / Auto Mannequinは維持。

ただし本格的な関節編集UIは作らない。

必要なら:

```text
OpenPose Editor
```

を将来のManual Pose編集経路として採用できるよう、

```text
Character Instance
↔ Pose Asset
```

という契約だけ用意する。

---

# 11. 3L-B — Pose Guide-Only Causality

Phase 3KではPose promptに方向語が入っていた。

Phase 3Lでは固定Prompt:

```text
1girl, blonde twin tails, school uniform, standing calmly
```

変更点は:

```text
pose_preset
```

だけ。

条件:

```text
standing_neutral
facing_left
facing_right
sitting
```

Promptに:

```text
left
right
facing
profile
sitting
seated
```

を入れない。

---

# 12. Two Character Orientation Guide-Only

Alice Left / Bob Right固定。

### Inward

```text
Alice = facing_right
Bob   = facing_left
```

### Outward

```text
Alice = facing_left
Bob   = facing_right
```

Promptは両者:

```text
standing calmly
```

のみ。

---

# 13. Pose判定

```text
POSE GUIDE GEOMETRY:
PASS / FAIL

POSE GUIDE-ONLY FINAL CAUSALITY:
PASS / PARTIAL / FAIL

TWO CHARACTER ORIENTATION GUIDE-ONLY:
PASS / PARTIAL / FAIL
```

---

# 14. 3L-C — Interaction canonical contract

現行Handshake周辺のstring/dict混在を解消。

Legacy入力:

```json
"interaction": "handshake"
```

は入口でのみ許可。

Canonical:

```json
{
  "interaction_id": "int_p1_01",
  "type": "handshake",
  "role": "left_participant",
  "target_instance_id": "p1_bob_01"
}
```

へnormalize。

以降:

```text
SceneCompiler
PAGE_COMPILE_PLAN
Impact Plan
Guide
```

はdict形式だけを扱う。

---

# 15. Stable Character Instance ID

Interaction targetは:

```text
master_character_id
```

ではなく:

```text
character_instance_id
```

を参照。

理由:

```text
Alice @ SubScene A
Alice @ SubScene B
```

が同時に存在可能だから。

---

# 16. Instance ID

Character Binding / SubScene Bindingにoptional:

```text
instance_id
```

を許可。

未指定時はdeterministic生成。

ただしbinding array indexだけに依存しない。

---

# 17. Pair Resolver

新規pure logic:

```text
resolve_interaction_pairs(...)
```

最低限検証:

```text
valid target
missing target reject
self target reject
cross-panel target reject
duplicate interaction_id reject
duplicate role reject
```

---

# 18. 3L-D — WF63 Handshake wiring repair

現WF63はstring interactionを使っているため、
Layout Guideのdict-only handshake detectionと一致していない可能性がある。

修正版Canonical Workflowでは:

```text
structured interaction dict
stable instance IDs
target_instance_id
resolved pair
```

を使用。

Guide debugに:

```json
{
  "interaction_id": "...",
  "participants": ["...", "..."],
  "anchor_px": [x,y]
}
```

を出す。

---

# 19. Handshake seam

Phase 3Kで残った:

```text
hard regional boundary
```

を比較。

候補:

```text
feather 0
feather 8
feather 16
```

最大3点。

見るもの:

```text
hand seam
double arm
identity bleed
background hole
blur
```

---

# 20. Interaction Relation Regionは第二手段

Pair Guide + featherで弱い場合だけ:

```text
scope_type = interaction_relation
```

をexperimentalで追加可。

Prompt:

```text
two people shaking hands
```

Identity語を入れない。

改善しなければ採択しない。

---

# 21. 3L-E — SubScene Contract v1.1

### ⚠ 方針転換ではないが重要

これまでSubSceneは実験経路で存在したが、
ここからMainline Authoring Contractへ昇格させる。

SubScene Character Binding:

```json
{
  "instance_id": "p1_sub_a_alice_01",
  "character_id": "char_alice",
  "enabled": true,
  "prompt_override": "angry expression, arms crossed",
  "negative_prompt_override": "",
  "area": {...},
  "shot_type": "full_body",
  "pose_preset": "facing_right",
  "interaction": {...},
  "metadata": {}
}
```

---

# 22. SubScene validator strict化

Canonical path:

```text
strict bool
finite numeric area
dict metadata
shot_type enum
pose_preset enum
canonical interaction
unique instance_id
```

Legacy migrationは別layer。

---

# 23. SubScene mainline compiler

責務:

```text
SceneCompiler:
CAST + SubScene Binding
→ combined prompt
→ stable instance
→ shot / pose / interaction
```

Impact側でmaster promptを再探索しない。

Impact側は:

```text
compiled semantic truth
+
geometry
```

からRegionを作るだけ。

---

# 24. COMPILE_PLAN SubScene shape

```json
{
  "panel": {
    "subscenes": [
      {
        "id": "sub_a",
        "prompt": "...",
        "area": {...},
        "characters": [
          {
            "instance_id": "...",
            "character_id": "char_alice",
            "combined_prompt": "...",
            "combined_negative_prompt": "...",
            "shot_type": "full_body",
            "pose_preset": "facing_right",
            "interaction": {...}
          }
        ]
      }
    ]
  }
}
```

Nested SubSceneは禁止。

---

# 25. Root Scene / SubScene

Simple:

```text
Panel Root Scene
subscenes = []
```

Complex:

```text
Panel Root
├ SubScene A
└ SubScene B
```

Root CharacterをSubSceneへ自動複製しない。

---

# 26. SubScene remainder mask

各SubScene background:

```text
SubScene area
-
characters in that SubScene
-
local regions in that SubScene
```

別SubSceneのCharacterをsubtractしない。

---

# 27. Same CAST Multi-Instance

正式サポート:

```text
SubScene A:
Alice A1
Bob B1

SubScene B:
Alice A2
Bob B2
```

Master IDs:

```text
Alice = same
Bob = same
```

Instance IDs:

```text
A1 != A2
B1 != B2
```

Acting / Pose / Interactionはinstanceごとに独立。

---

# 28. 3L-F — Hostile Oracle

1 visible Panel / 2 internal SubScenes。

Promptにleft/right位置語を入れない。

### SubScene A

```text
school gate
Alice angry
Bob annoyed
look-away relation
```

### SubScene B

```text
school garden
Alice smiling
Bob smiling
handshake
```

---

# 29. Hostile Oracleの意味

```text
Visible Panels = 1
Internal Scenes = 2
Character Masters = 2
Character Instances = 4
```

これがPhase 3Lの本命。

---

# 30. Mainlineのみで検証

既存:

```text
TegakiSinglePanelMultiSceneImpactAdapter
```

は参考・回帰として残す。

しかし正本PASSは:

```text
Panel Content
→ REGION_SPEC
→ Compiler
→ PAGE_COMPILE_PLAN
→ Backend Adapter
→ RegionalSampler
```

で成立した場合のみ。

---

# 31. 3L-G — Progressive SubScene UI

通常Panel:

```text
Scene Prompt
Attendance
Acting
Staging
```

だけ。

必要なPanelのみ:

```text
+ Advanced Scene
```

---

# 32. SubScene UI最低限

ON時:

```text
Selected SubScene
Add
Delete
Prompt
Negative
Area x/y/w/h
Character Instances
```

V1最大:

```text
4 SubScenes
```

程度。

---

# 33. Character Instance UI

SubScene内:

```text
Selected Character
Attend
Acting Prompt
Shot Type
Pose Preset
Interaction Type
Target Instance
```

表示:

```text
Alice @ sub_a
Alice @ sub_b
```

---

# 34. External UI design reference

### ⚠ 中間計画書参照

UIを独自node増殖で作る前に、
以下の設計を参照。

```text
EasyUseAnima Regional Prompt Studio
Krea2 Regional Builder
Krita AI Diffusion Regions
```

参考にする点:

```text
single structured state
tabs / selected item
hidden serialized JSON
canvas + list
progressive disclosure
```

Backend自体をコピーする意味ではない。

---

# 35. MANGA_AUTHORING_DATAへの移行準備

Phase 3L中に全面移行は不要。

ただし新しいSubScene / Interaction stateは、
将来:

```text
MANGA_AUTHORING_DATA
```

へ統合可能な構造にする。

ComfyUI link ID等をpersistent stateへ保存しない。

---

# 36. 3L-H — Mixed Page Oracle

4 visible Panels:

```text
P1:
Advanced Scene
Conflict + Friendship

P2:
Simple
Alice watering flowers

P3:
Simple
Bob carrying plant

P4:
Simple
Alice + Bob conversation
```

Internal Scenes:

```text
5
```

Visible Panels:

```text
4
```

を実証。

---

# 37. Simple Panel Regression

SubScene未使用時:

```text
WF54〜59
```

相当のsimple pathを壊さない。

---

# 38. External Backend Adoption Gate

Phase 3L終盤に以下を決定。

```text
REGIONAL EXECUTION:
Current Tegaki Adapter / Inspire Wrapper / Hybrid

CONTROLNET:
Current / Advanced-ControlNet / Hybrid

MASK EDIT:
Existing Impact MaskEditor / Future Custom

POSE EDIT:
Auto Mannequin + Existing OpenPose Editor
```

---

# 39. Adoption Decision Report

```text
docs/reports/PHASE3L_BACKEND_ADOPTION_DECISIONS.md
```

形式:

```text
Regional Prompt:
ADOPT / ADAPT / KEEP

ControlNet:
ADOPT / ADAPT / KEEP

Mask Editor:
ADOPT / DEFER

Pose Editor:
ADOPT / DEFER
```

理由を各3〜5行。

---

# 40. Canonical Workflows

最大6本程度。

```text
66_VERIFY_POSE_GUIDE_ONLY_INWARD.json
67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json
68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json
69_VERIFY_MAINLINE_SUBSCENE_GEOMETRY_SWAP.json
70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json
71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json
```

---

# 41. Workflow71

目的:

```text
Current Tegaki Regional backend
vs
Inspire RegionalPromptSimple
```

固定条件比較。

同じ画像生成結果を要求しない。

見るもの:

```text
subject presence
region isolation
ControlNet inheritance
runtime
schema stability
```

---

# 42. Tests

推奨:

```text
test_phase3l_visual_provenance_contract.py
test_phase3l_pose_causality_fixture.py
test_phase3l_interaction_contract.py
test_phase3l_pair_resolution.py
test_phase3l_subscene_contract_v11.py
test_phase3l_subscene_compile_truth.py
test_phase3l_subscene_instance_ids.py
test_phase3l_subscene_masks.py
test_phase3l_inspire_regional_parity.py
test_phase3l_controlnet_backend_comparison.py
```

---

# 43. Contact Sheets

```text
AA Pose Guide Only
AB Orientation In/Out
AC Handshake
AD SubScene Conflict/Friendship
AE SubScene Geometry Swap
AF Backend Parity
```

---

# 44. Runtime

Hyper12をOperational Profileとして使用。

Native20は代表回帰のみ。

Semantic correctness優先。

---

# 45. User Review Rule

Geminiが実際に画像を見た場合のみAI Visual判定。

曖昧な:

```text
handshake
look-away
same-cast acting separation
```

だけユーザー確認可。

大量実行を依頼しない。

---

# 46. Report

新規:

```text
PHASE3L_INTERACTION_SUBSCENE_AND_PRIORART_REPORT.md
```

最低限:

```text
1. Phase3K Review Closure
2. Visual Provenance Correction
3. Prior-Art Audit
4. Inspire RegionalPromptSimple Comparison
5. Advanced-ControlNet Comparison
6. Mask Editor Decision
7. Pose Editor Decision
8. Pose Guide-Only
9. Interaction Canonicalization
10. Stable Instance IDs
11. Pair Resolution
12. Handshake Wiring
13. Feather Comparison
14. Interaction Relation Region Decision
15. SubScene Contract v1.1
16. Mainline Compiler SubScene
17. Mainline Impact SubScene
18. Same-Cast Multi-Instance
19. Conflict/Friendship Oracle
20. Geometry Swap
21. Mixed 4-Panel/5-Scene Page
22. Progressive SubScene UI
23. External Backend Adoption Decisions
24. Runtime / VRAM
25. Regression
26. Live Browser
27. Known Issues
28. Next Phase
29. Gemini独自判断
```

---

# 47. Sign-off

```text
PHASE3K REVIEW CLOSURE:
PASS WITH CORRECTIONS / HOLD

PRIOR-ART AUDIT:
PASS / HOLD

REGIONAL BACKEND DECISION:
CURRENT / INSPIRE / HYBRID / UNRESOLVED

CONTROLNET BACKEND DECISION:
CURRENT / ADVANCED / HYBRID / UNRESOLVED

MASK EDITOR DECISION:
IMPACT / CUSTOM_LATER / UNRESOLVED

POSE EDITOR DECISION:
AUTO_PLUS_EXISTING_EDITOR / CUSTOM / UNRESOLVED

POSE GUIDE-ONLY CAUSALITY:
PASS / PARTIAL / FAIL

INTERACTION CANONICAL CONTRACT:
PASS / FAIL

STABLE INSTANCE IDS:
PASS / FAIL

HANDSHAKE CANONICAL WIRING:
PASS / FAIL

HANDSHAKE:
PASS / PARTIAL / FAIL

MASK FEATHERING:
HELPFUL / NEUTRAL / HARMFUL

SUBSCENE CONTRACT V1.1:
PASS / FAIL

SUBSCENE COMPILE TRUTH:
PASS / FAIL

SUBSCENE MAINLINE:
PASS / FAIL

SAME CAST MULTI-INSTANCE:
PASS / PARTIAL / FAIL

HOSTILE CONFLICT/FRIENDSHIP:
PASS / PARTIAL / FAIL

SUBSCENE GEOMETRY SWAP:
PASS / PARTIAL / FAIL

MIXED 4PANEL/5SCENE PAGE:
PASS / PARTIAL / FAIL

SIMPLE PANEL REGRESSION:
PASS / HOLD

HYPER12:
PASS / CONDITIONAL / HOLD

LIVE BROWSER SUBSCENE E2E:
PASS / PENDING

USER VISUAL REVIEW REQUIRED:
YES / NO

NEXT RECOMMENDED PHASE:
```

---

# 48. 終了Gate

最低限:

```text
Prior-Art Audit complete

Pose guide-only truth known

Interaction uses canonical dict
Stable instance IDs established
Handshake workflow truly reaches pair guide

SubScene survives:
Editor
Compiler
PAGE_COMPILE_PLAN
Backend

same CAST multiple instances works

1 visible Panel / 2 internal scenes works

Simple Panel remains simple

Regional/Control/Mask/Pose external adoption decision recorded
```

---

# 49. 次Phase候補

成功した場合:

```text
Phase 3M
Progressive Manga Authoring UX Integration
```

ここで:

```text
Global
CAST
Panel
Layout
Staging
Advanced SubScene
Interaction
Generate
```

をユーザー作業順に再編。

### ⚠ 方針転換

このPhase以降は、
Custom Node追加より:

```text
既存ノード再利用
Structured Authoring State
Backend Adapter薄型化
```

を優先する。

中間計画書を常に参照。

---

# 50. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3L integrate mainline subscenes and adopt prior-art backends
```

内容:

```text
prior-art audit
pose guide-only oracle
interaction canonicalization
stable instance ids
handshake repair
subscene v1.1
mainline subscene compiler
backend parity tests
workflows 66-71
reports
```

Commit A SHA取得後、
Navigation Commit Bで:

```text
ComfyUIPortable/GITHUB.TXT
```

Review TargetをCommit Aへ更新。

---

# 51. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3L_INTERACTION_SUBSCENE_AND_PRIORART_REPORT Raw:
PHASE3L_PRIOR_ART_ADOPTION_AUDIT Raw:
PHASE3L_BACKEND_ADOPTION_DECISIONS Raw:

Interaction Contract Test Raw:
Pair Resolver Test Raw:
SubScene Contract Test Raw:
SubScene Compile Truth Test Raw:
Inspire Parity Test Raw:
Advanced-ControlNet Comparison Raw:

Workflow66 Raw:
Workflow67 Raw:
Workflow68 Raw:
Workflow69 Raw:
Workflow70 Raw:
Workflow71 Raw:

PRIOR-ART AUDIT:
REGIONAL BACKEND DECISION:
CONTROLNET BACKEND DECISION:
MASK EDITOR DECISION:
POSE EDITOR DECISION:
POSE GUIDE-ONLY CAUSALITY:
INTERACTION CANONICAL CONTRACT:
STABLE INSTANCE IDS:
HANDSHAKE CANONICAL WIRING:
HANDSHAKE:
SUBSCENE CONTRACT V1.1:
SUBSCENE COMPILE TRUTH:
SUBSCENE MAINLINE:
SAME CAST MULTI-INSTANCE:
HOSTILE CONFLICT/FRIENDSHIP:
SUBSCENE GEOMETRY SWAP:
MIXED 4PANEL/5SCENE PAGE:
SIMPLE PANEL REGRESSION:
HYPER12:
LIVE BROWSER SUBSCENE E2E:
USER VISUAL REVIEW REQUIRED:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

このPhaseから明確に、

```text
「足りない機能をTegakiで作る」
```

だけではなく、

```text
「既存ComfyUI実装へ置換できるTegakiコードを減らす」
```

ことも成果として扱います。

### ⚠ 方針転換部分

特に:

```text
Regional Prompt
ControlNet application
Mask editing
Pose editing
```

は既存実装の採用可能性を必ず先に検討してください。

詳細な背景は必ず:

```text
Tegaki_ComfyUI_Manga_Authoring_Intermediate_Plan_PriorArt_Integration.md
```

を参照してください。

一方で:

```text
CAST
Panel
SubScene
Character Instance
Interaction
Staging
Compiler
```

は漫画制作固有のTegaki Coreとして維持します。

最終目標はCustom Nodeの数を増やすことではなく、

```text
薄い Manga Authoring Compiler
+
交換可能な ComfyUI Backend
```

を作ることです。
