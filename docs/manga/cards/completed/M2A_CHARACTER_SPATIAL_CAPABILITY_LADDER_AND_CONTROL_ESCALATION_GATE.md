# ComfyUI Portable — M2A / Phase 3M-2A
# Character Spatial Capability Ladder & Control Escalation Gate
## Antigravity2 / Gemini 3.8 向け Bounded Empirical Capability Card

## 推奨モデル

Gemini 3.8

---

# 0. このCardの目的

M2へ入る前に、Character機能をいきなり大きなUIとして実装しない。

まず、

「普通のPrompt + Character Rough Regionだけで、どこまで漫画制作に使えるか」

を段階的に実画像で測る。

今回の最重要問いは以下。

1. 1人の位置指定は再現可能か。
2. 2人を別々の位置へ置けるか。
3. 左右を入れ替えると、同Seedで人物も入れ替わるか。
4. 遠景 / 中景 / 近景を、まずPromptだけでどこまで誘導できるか。
5. Character Regionのサイズ差を使うと遠近が改善するか。
6. 同じCAST Masterを複数Instanceとして登場させられるか。
7. 同じCAST複数 + 別CAST混在が可能か。
8. 3〜4人以上でどこから破綻し始めるか。
9. Prompt / Rough Regionだけで不足した時、ControlNet block guideをCoreへ入れる必要があるか。

このCardは、

CAST UIを完成させるPhaseではない。

Character Spatial Capabilityの「難易度曲線」を測り、
次のM2B実装範囲を決めるためのPhaseである。

---

# 1. 最初に読むもの

必ず最初に:

ComfyUIPortable/GITHUB.TXT

次に:

ComfyUIPortable/GITHUB_ComfyUI.txt

本Card発行時の固定Review Target:

7e516015f8c6fdfde118a83a9dcfdb04560d02aa

M1.1 Implementation Commit A:

7e516015f8c6fdfde118a83a9dcfdb04560d02aa

remote main上の実Navigation Commit:

b6bea40c9619e24b34d038ac2ce6994f405b36ba

注意:
Gemini前回報告に記載された

b6bea40cf88c75ef5bf54a6db24ec3915bc6784e

はremote上の実SHAと一致しない。

repo事実を優先すること。

---

# 2. Publication Truth Correction

前回報告は PUSH STATUS: LOCAL ONLY としているが、
Web GPTから現在remote main上のImplementation AとNavigation Commitを取得できている。

したがって次回GITHUB_ComfyUI.txt更新時に、
M1.1 publication statusをremote実態へ訂正する。

この訂正だけの別Commitは作らない。

---

# 3. M1.1 Review Verdict

M1.1 code review:

M1 Core Semantic Scene:
PASS

Canonical Seed Wiring:
PASS

Canonical Width/Height Wiring:
PASS

JS/Python Contract Dialect:
PASS

Stable Scene ID fix:
PASS

Manifest v2:
PASS

Automated Tests:
114/114 PASS + JS tests

Browser Canonical Workflow:
まだOwner手動受入が完全には閉じていない

M2A Backend Capability Research:
GO

M2B Product UI:
M2A結果を見てから

---

# 4. Owner手動観察の扱い

Ownerは旧Research Workflowの

64_VERIFY_CAMERA...

系Workflowを手で触り、

「Aliceの大まかな位置移動は効いている」
「sitting等のPose選択は効きが弱い」

と観察している。

これは有用なPrior Evidence。

ただしこれはM1 canonical workflowのBrowser E2Eではなく、
過去のCharacter Staging / Impact / ControlNet系stackの観察である。

M2Aではこの知見を参考にするが、
新MainlineのPASS根拠としてそのまま流用しない。

---

# 5. Product Priority
# 非常に重要

今回の優先順位:

1. Character Rough Position
2. 2人の独立配置
3. Seed variationを残す
4. 遠近 / サイズの粗誘導
5. 同一CAST複数Instance
6. 多人数
7. 必要ならControlNet block assist
8. Pose refinement

Poseは今回Primaryではない。

---

# 6. Pose Selectorを拡張しない

旧UIには:

Shot Type
Pose Preset
Camera Distance

等のselectorがある。

便利ではあるが、
M2AではこれらのProduction UIを拡張しない。

Owner方針:

「まず普通のPrompt入力でどこまで行けるか」

を優先。

---

# 7. Strength SliderもまだUser-facingにしない

既存 ConditioningBuilder には:

character_strength

が存在する。

M2AではDefault 1.0を基本とする。

baselineが失敗した場合だけResearch Diagnosticとして:

0.75
1.00
1.25

程度の小さいsweepを許可。

結果が有意でも、
今回User-facing sliderは追加しない。

Reportへ:

“future tuning candidate”

として記録するだけ。

---

# 8. Backend First Principle

最初はControlNetなし。

使用するもの:

TEGAKI_AUTHORING_DOCUMENT
Scene area
CAST Master
Character Instance
Character Rough Region
Character Prompt
Core masked conditioning
Seed

これだけ。

---

# 9. M2Aで実装する最小Bridge

現在M1 execution bridgeはsimple scene onlyをfail-closedしている。

M2AではProduction UIを作る前に、
テスト用/将来Mainline用の薄いCast execution pathを追加する。

目的:

TEGAKI_AUTHORING_DOCUMENT
↓
Scene
CAST Master
Character Instances
↓
PAGE_COMPILE_PLAN
↓
TegakiMangaConditioningBuilder
↓
Core KSampler

---

# 10. Character Compile Responsibility

Scene:

background / common event / context

CAST Master:

identity prompt

Character Instance:

scene membership
rough area
acting_prompt

を結合。

Character combined prompt:

CAST.identity_prompt
+
Instance.acting_prompt

---

# 11. Character Negative

combined negative:

CAST.negative_prompt
+
Instance.negative_prompt_override

---

# 12. Character LoRA

今回はLoRAをPrimary Testへ入れない。

理由:

まず

text identity + rough position

の限界を測るため。

LoRAを混ぜると、
spatial failureとidentity model effectを分離しにくい。

LoRAはM2B以降の別Gate。

---

# 13. Character Area Coordinate

TEGAKI_AUTHORING_DOCUMENTのCharacter Instance areaは
Page-normalized coordinateとして扱う。

旧KOMA-localへ戻さない。

Sceneの中に入っていることをM2A test fixtureでは基本とする。

---

# 14. Same CAST Multi-instance

同一CASTを複数回使う場合:

cast_id:
same

instance_id:
different

area:
different

acting_prompt:
independent

を必ず維持。

---

# 15. Instance ID

配列indexをidentityにしない。

以下をTest:

Alice Master
Alice Instance 1
Alice Instance 2
Bob Instance 1

全instance_id unique。

---

# 16. M2AではUIを大きく作らない

今回追加しない:

Full CAST Editor
complex Character Inspector
Pose dropdown expansion
Camera controls
strength sliders
Character LoRA browser
ControlNet controls
A1111 skin

---

# 17. Canonical Workflow policy

workflows/ rootには
M1 Canonical Workflow一本を維持する。

M2A研究用Workflowをrootへ大量追加しない。

実証は:

scripts/run_m2a_character_capability_verification.py

等のRunnerとAuthoring fixturesで行う。

必要ならM2A temporary workflowはdocs/verification内へ保存し、
root active workflowへしない。

---

# 18. Archive

workflows/Archive/ はREAD-ONLY。

旧64系Workflowを参照するのは可。

変更・復活・root移動は禁止。

---

# 19. Capability Ladder
# Stage A — Single Character Position Sanity

1 Scene。

CAST:
Alice

Prompt identity例:
blonde twin tails, blue eyes, school uniform

Scene prompt:
school courtyard, daytime

Alice Instance:
acting_promptはneutral。

Area:

A1 = left
A2 = right

同Seed。

重要:
Character Promptに

left
right

を入れない。

---

# 20. A Acceptance

期待:

Alice dominant location follows Character area.

判定:

PASS:
明確にrough locationがareaに追随

PARTIAL:
人物は出るが中心寄り等のbiasあり

FAIL:
area変更しても人物位置がほぼ変わらない / 不在

---

# 21. Stage B — Two Distinct Characters

1 Scene。

CAST:

Alice:
blonde twin tails, blue eyes, school uniform

Bob:
short black hair, glasses, male school uniform

Character Instances:

Alice left
Bob right

同Seed。

Promptにleft/rightを書かない。

---

# 22. Stage B2 — Swap Oracle

同Prompt
同Seed
同Scene
同Character areas size

変更:

Alice area ↔ Bob area

期待:

Alice / Bobのdominant locationがswap。

これはM2A最重要Oracleの一つ。

---

# 23. Two-character評価

以下を別々に見る。

Presence:
Aliceがいる
Bobがいる

Identity:
Alice特徴
Bob特徴

Position:
各rough area

Leakage:
Alice特徴がBob側へ混ざる
Bob特徴がAlice側へ混ざる

Do not reduce to one PASS flag.

---

# 24. Stage C — Prompt-only Depth
# Owner Question

「遠中近・接写をPromptでどこまで行けるか」

を検証。

2 CASTまたは1 CAST + 1 generic subject。

Character Regionは同程度のサイズに固定。

Promptだけ変える。

例:

Alice:
close foreground, upper body prominently in foreground

Bob:
far in the background, small distant full body

重要:
Character areaサイズで答えを教えすぎない。

---

# 25. Stage C Acceptance

見るもの:

apparent subject scale
occlusion
perspective hierarchy
foreground/background impression

位置だけでなくDepthとして評価。

---

# 26. Stage D — Geometry-assisted Depth

Stage Cと同一Seed。

Prompt depth wordingを弱める、または固定。

変更:

Alice region = large
Bob region = small

を用いる。

---

# 27. Depth 3-way Comparison

最低限:

C1 Prompt-only depth
C2 Geometry-size-only depth
C3 Prompt + Geometry

を比較。

結論として:

PROMPT_SUFFICIENT
GEOMETRY_HELPS
COMBINED_REQUIRED
UNRELIABLE

のどれかを記録。

---

# 28. Stage E — Pose Prompt Ceiling
# Non-gating diagnostic

Owner手動観察:

sittingが弱い。

M2Aで一度だけ定量化。

Same Alice
same area
same seed

E1:
standing casually

E2:
sitting on a chair

Promptのみ変更。

---

# 29. PoseはM2 Gateではない

Sitting FAILでもM2AはFAILにしない。

目的:

Prompt-only Poseの限界を記録し、
Pose UI / ControlNetが「後から必要になる場所」を知ること。

この結果を理由にPose Editorを今回作らない。

---

# 30. Stage F — Same CAST Across Multiple Scenes

2 Semantic Scenes。

CAST:
Alice 1 Master

Scene 1:
Alice Instance A

Scene 2:
Alice Instance B

instance_idは別。

Prompt identityは同Master。

Acting promptは別でもよい。

---

# 31. F Acceptance

Presence:
両SceneにAliceが存在

Rough identity:
両方ともAlice特徴を概ね共有

Position:
各Instance areaに追随

完全な顔一致は要求しない。

M2Aはreference/IPAdapter段階ではない。

---

# 32. Stage G — Same CAST Twice In One Scene
# Harder

1 Scene。

CAST:
Alice Master 1つ

Instances:

Alice_A left
Alice_B right

同じidentity prompt。

acting_promptだけ変えてよい。

例:

Alice_A:
smiling

Alice_B:
looking away

---

# 33. G Acceptance

重要:

2人存在するか
1人へcollapseしないか
両者がrough positionsを守るか
同系統のAlice外観になるか

完全clone一致は不要。

---

# 34. Stage H — Same CAST + Other CAST Mixed

1 Scene。

Alice Master
Bob Master

Instances:

Alice_A
Alice_B
Bob_A

計3人物。

Character rough regionsは非overlapから開始。

---

# 35. H Acceptance

Count:
3人物が概ね存在

Repeated identity:
Alice系2人

Distinct identity:
BobがAlice化しない

Spatial:
3 rough areasへ分布

---

# 36. Stage I — Crowd / Large Count Scalability

最低限:

3 people
4 people

必要なら6までResearch。

ただし大量生成しない。

---

# 37. Crowd Fixture Design

まず4 distinct spatial slots。

例:

upper-left
upper-right
lower-left
lower-right

Promptに位置語を入れない。

---

# 38. Crowdで測るもの

Presence count
rough slot occupancy
identity leakage
subject merging
missing subjects
unwanted duplicates
composition collapse

---

# 39. Crowd Gate

MVPで4人物を完全制御できる必要はない。

重要なのは:

どの人数から急激に失敗率が増えるか

を測ること。

---

# 40. Seed Robustness

重要条件:

B two-character
G same-cast double
H mixed 3-person

は最低:

3 seeds

で確認。

単Seed成功をProduction能力と呼ばない。

---

# 41. Seed choice

固定候補:

42
101
202

既存M1と揃えてよい。

---

# 42. Capability Matrix

Reportへ:

| Tier | Scenario | Seed Pass Rate | Presence | Identity | Position | Depth | Notes |
|---|---|---:|---|---|---|---|---|

を作る。

---

# 43. Control Escalation Gate
# 非常に重要

最初からControlNetを足さない。

以下の順番。

Level 0:
Prompt + Character Rough Region

Level 1:
internal character_strength small sweep
研究のみ

Level 2:
Prompt + Rough Region + weak block/dummy ControlNet
必要時のみ

Level 3:
Pose / OpenPose
今回禁止

---

# 44. ControlNet escalation条件

以下ならControlNetを試さない:

Two distinct characters:
PASS

3-person mixed:
PASS or useful PARTIAL

Depth:
Prompt or geometryでuseful PARTIAL以上

---

# 45. ControlNetを試す条件

以下のどれか:

Two distinct charactersが複数SeedでFAIL

Character areaに対して位置が頻繁にcollapse

3-personで人物slotが大きく崩れる

DepthがPrompt+Geometryでもほぼ制御不能

---

# 46. ControlNetの目的

M2AでControlNetを使う場合も:

Poseを固定する

ためではない。

目的:

rough block occupancy
foreground/background block
character slot separation

を補助すること。

---

# 47. Weak Block Guide

ControlNet testを行うなら、

白ハゲ漫画の前段として:

simple silhouette / dummy blocks

を使う。

例:

circle head
rect/line torso
rough body block

Character regionとの対応をvisualize。

---

# 48. 新Pose Mannequinは禁止

既存Guide generatorを再利用できるなら使う。

できない場合でも、
Research-onlyの単純block guideまで。

3D Pose UIを作らない。

---

# 49. Control strength

比較は最大:

0.20
0.35

程度。

過去の0.75 literal mannequin overconstraintを繰り返さない。

必要なら0.0 baselineを含む。

---

# 50. Per-character ControlNet

今回Production implementationしない。

まずglobal/rough occupancy guideで効果を見る。

per-region ControlNetが必要と分かった場合:

NEXT RESEARCH REQUIRED

とする。

---

# 51. Existing historical evidence

必要に応じてArchiveの:

54–59 spatial character foundation
60–65 pose/camera foundation
64 camera distance
66 pose guide
67 handshake
68 subscene

を参照してよい。

ただしM2A Mainline evidenceは
新TEGAKI_AUTHORING_DOCUMENT pathで取り直す。

---

# 52. Character strength diagnostic

baselineがPARTIAL以下の場合のみ:

0.75
1.00
1.25

を同一条件・同一Seedで比較。

目的:

区域condition strength tuningで改善するのか

を見る。

---

# 53. Strength UI判断

Reportに:

NO NEED
POSSIBLE ADVANCED CONTROL
NEEDS OPERATIONAL DEFAULT TUNING

のどれかを出す。

M2Aではslider UIを作らない。

---

# 54. Acting Prompt

Actingは普通のtext fieldで十分。

例:

smiling
looking away
holding a book
sitting on chair
walking

Selector化しない。

---

# 55. Camera / Shot Prompt

Near / Medium / Far等も
M2Aではordinary text promptをPrimaryとする。

既存selectorは参考。

新Production selectorは作らない。

---

# 56. Mainline Contract Extension

必要ならAuthoring bridgeを以下まで拡張。

Scene input_mode:

simple
cast

Cast mode時:

page.cast
page.character_instances

をcompile。

---

# 57. Simple mode regression

M2Aでcast path追加後も、
M1 simple modeは完全に維持。

既存M1 canonical workflowを壊さない。

---

# 58. Mixed Page

将来に備えて:

Scene 1 = simple
Scene 2 = cast

をDocument上保持できること。

M2A compile testでは最低1件。

実画像生成は必須ではない。

---

# 59. Character mask preview

Research/debug用に:

Scene regions
+
Character regions

が確認できるpreviewを生成してよい。

色:

Scene = translucent base
Alice = one color
Bob = another

---

# 60. Previewの目的

User-facing final UIを完成させるためではなく:

どのmaskがどこへ行ったか

を検証するため。

---

# 61. No new active workflow

M2Aでは:

workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json

をM2A機能で無理に増築しない。

Backend capabilityを確認してからM2BでUI統合する。

---

# 62. Verification Runner

新規:

scripts/run_m2a_character_capability_verification.py

推奨。

---

# 63. Verification output

docs/verification/m2a/

へ:

raw selected outputs
preview maps
contact sheets
manifest
capability matrix

を保存。

---

# 64. Contact Sheets

最低限別sheet:

M2A_TWO_CHARACTER_ORACLE.png
M2A_DEPTH_ORACLE.png
M2A_REPEATED_CAST_ORACLE.png
M2A_CROWD_ORACLE.png

ControlNetを試した場合:

M2A_CONTROL_ESCALATION_ORACLE.png

---

# 65. Manifest

各condition:

condition_id
tier
seed
cast
instances
areas
prompts
character_strength
control_mode
runtime_status
visual_status
review_method
presence_result
identity_result
position_result
depth_result
notes
output_path

---

# 66. Visual Truth

Runtime成功:
runtime_status=PASS

画像を見た:
review_method=DIRECT_IMAGE_INSPECTION

見ていない:
visual_status=PENDING

自動でvisual PASSにしない。

---

# 67. User review対象

大量の全画像をOwnerへ投げない。

Gemini自身でcontact sheetを作り、
曖昧な条件だけ:

OWNER REVIEW RECOMMENDED

とする。

---

# 68. Pose評価のOwner review

sitting等が曖昧なら、
Pose tierだけOwner確認候補。

しかしM2A GO/HOLDをPoseで決めない。

---

# 69. Automated Tests

M0/M0.1/M1/M1.1の既存testを全部維持。

新規候補:

test_m2a_cast_execution_bridge.py
test_m2a_character_instance_plan.py
test_m2a_same_cast_multi_instance.py
test_m2a_mixed_simple_cast.py

---

# 70. Pure tests

最低限:

1 CAST 1 Instance
2 CAST 2 Instance
same CAST 2 Instance
same CAST + other CAST
instance_id uniqueness
missing cast FK fail-closed
missing scene FK fail-closed
combined prompt composition
negative composition
page-normalized area retained
simple scene regression

---

# 71. LoRA tests

今回はLoRA runtimeを増やさない。

既存field preservationを壊さないことのみtest可。

---

# 72. M2A Report

新規:

docs/reports/M2A_CHARACTER_SPATIAL_CAPABILITY_LADDER_REPORT.md

---

# 73. Report必須構造

1. Baseline fixed SHA
2. Owner manual prior observation
3. M1.1 status
4. Cast execution bridge
5. Character prompt contract
6. Single-character position
7. Two-character presence
8. Two-character swap
9. Depth prompt-only
10. Depth geometry-only
11. Depth combined
12. Pose prompt ceiling diagnostic
13. Same CAST across scenes
14. Same CAST twice same scene
15. Same CAST + other CAST
16. Crowd scalability
17. Seed robustness
18. Character strength diagnostic if used
19. ControlNet escalation decision
20. ControlNet evidence if used
21. Capability matrix
22. Product recommendation
23. M2B scope recommendation
24. Known ceiling
25. UI features explicitly deferred

---

# 74. Product Recommendation

Report最終部で:

Core Minimum-Hand Character Capability:

READY
PARTIAL
NOT READY

を出す。

---

# 75. M2B Scope Decision

M2A結果から次を選ぶ。

Option A:
Rough Region + free text PromptだけでM2Bへ

Option B:
Rough Region + free text + hidden tuned strength

Option C:
Rough Region + optional weak block guide

Option D:
Character MainlineはControlNet researchを先に追加

---

# 76. UI判断

以下はM2A後まで保留:

Near/Far selector
Shot selector
Pose selector
Character strength slider
Control strength slider

---

# 77. M2A Acceptance

最低限:

SINGLE CHARACTER POSITION:
PASS

TWO DISTINCT CHARACTER PRESENCE:
PASS / useful PARTIAL

TWO CHARACTER SWAP:
PASS / useful PARTIAL

SEED ROBUSTNESS:
MEASURED

DEPTH PROMPT ONLY:
MEASURED

DEPTH GEOMETRY:
MEASURED

DEPTH COMBINED:
MEASURED

SAME CAST ACROSS SCENES:
PASS / useful PARTIAL

SAME CAST TWICE SAME SCENE:
MEASURED

SAME CAST + OTHER CAST:
MEASURED

3–4 PERSON SCALE:
MEASURED

POSE PROMPT CEILING:
MEASURED, NON-GATING

CONTROLNET NEED:
DECIDED

---

# 78. M2B GO条件

最低限:

Single Character Position = PASS

Two distinct characters = PASS or useful PARTIAL

Character Instance contract = PASS

Same CAST repeated = at least structurally valid and empirically measured

Seed robustness = not catastrophic

---

# 79. M2A HOLD条件

以下ならM2BへUI実装しない:

2人配置が複数SeedでほぼFAIL

identity leakageが常時深刻

Character regionsが位置へほぼ寄与しない

same-cast instance pathがstructurally破綻

---

# 80. ControlNet escalation result

もしControlNetでのみ2人配置が成立するなら:

M2B core designにControlNetを即入れる

のではなく、

M2A.1 Regional / Block Control Study

を挟むことを推奨。

---

# 81. Current screenshotsからの仮説

Owner screenshotでは旧64系stack上で
Alice rough areaの変更に生成人物位置が追随する兆候がある。

一方sittingは不安定。

したがって現時点仮説:

POSITION:
PROMISING

POSE PROMPT / PRESET:
WEAK / LATER

この仮説を新Mainline pathで再検証する。

---

# 82. Commit A

推奨:

feat(manga): validate minimum-hand character spatial capability

含む:

authoring cast execution bridge extension
tests
verification runner
evidence
M2A report
STATUS / DOCUMENT_REGISTER

UI large changesは含めない。

---

# 83. Commit B

推奨:

docs(manga): publish M2A review target

GITHUB_ComfyUI.txt:

Review Target = Commit A

Current card = M2A complete / hold

Next =
M2B
or M2A.1 control study

publication truthをremote実態と一致させる。

---

# 84. Workflow root

root active workflowはM1一本維持。

M2BでProduct UIへ入る時に、
同じcanonical workflowを更新するか、
M2として正式に置換するかを決める。

M2Aで増やさない。

---

# 85. 最終回答フォーマット

MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
7e516015...

M2A IMPLEMENTATION COMMIT A:
M2A NAVIGATION COMMIT B:
PUSH STATUS:

SINGLE CHARACTER POSITION:
TWO CHARACTER PRESENCE:
TWO CHARACTER SWAP:
TWO CHARACTER SEED RATE:

DEPTH PROMPT ONLY:
DEPTH GEOMETRY ONLY:
DEPTH COMBINED:

POSE PROMPT CEILING:

SAME CAST ACROSS SCENES:
SAME CAST TWICE SAME SCENE:
SAME CAST + OTHER CAST:

3 PERSON:
4 PERSON:
CROWD FAILURE THRESHOLD:

CHARACTER STRENGTH SWEEP:
NOT RUN / RESULT

CONTROLNET ESCALATION:
NOT NEEDED / TESTED / REQUIRED FOR NEXT STUDY

CONTROLNET CONDITIONS:
NONE / ...

OLD TESTS:
NEW TESTS:
TOTAL:

CONTACT SHEETS:
MANIFEST:
M2A REPORT:

CORE MINIMUM-HAND CHARACTER CAPABILITY:
READY / PARTIAL / NOT READY

NEXT RECOMMENDED CARD:
M2B / M2A.1

OWNER REVIEW RECOMMENDED:
YES / NO
CONDITIONS:

USER ACTION REQUIRED:

---

# 86. 最終原則

位置がPrompt + Rough Regionで十分なら、
それ以上のControlを足さない。

Poseが難しくても、
今はPoseを解決しに行かない。

2人・遠近・同一CAST複数・混成・多人数の順で
難易度曲線を測る。

ControlNetは、

“先に入れる機能”

ではなく、

“Prompt + Rough Regionの限界が確認された時だけ上げる補助段階”

として扱う。

Minimum-Handを壊さないこと。
