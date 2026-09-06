# ComfyUI Portable — M2A.1 / Phase 3M-2A.1
# Prompt / Region Calibration & Conditional ControlNet Escalation Gate
## — MRP知見を使って「領域＋短いPrompt」の限界を詰め、ControlNetへ進む条件を再判定する —
## Antigravity2 / Gemini 3.8 向け Bounded Empirical Correction Card

## 推奨モデル

Gemini 3.8

---

# 0. 今回の判断

M2Aの実装骨格はACCEPTする。

ただし、

CORE MINIMUM-HAND CHARACTER CAPABILITY = READY
CONTROLNET NOT NEEDED

という結論は、範囲を限定して読み直す。

現時点の実測から強く言えるのは:

1人物 rough position:
READY

2 distinct characters:
PROMISING / USEFUL

2-character left-right swap causality:
PROVEN

Promptによるforeground/background:
PROMISING

same CAST across separate scenes:
PROMISING

一方で:

2人物のきれいな並列配置:
seed sensitive

3人物:
1/3 clear pass

same CAST twice in same scene:
PARTIAL

4人物:
multi-cut decomposition

Depth prompt-only:
1 seedの強い成功例

Pose sitting:
1 seedの成功例

である。

したがって次はM2B Product UIへ直行せず、

M2A.1
Prompt / Region Calibration
↓
必要条件を満たさないTierだけ
weak ControlNet block study
↓
M2B scope決定

とする。

---

# 1. 最初に読む正本

必ず最初に:

ComfyUIPortable/GITHUB.TXT

次に:

ComfyUIPortable/GITHUB_ComfyUI.txt

本Card発行時のReview Target:

72e032c71d97eed2712552062a75fde5d29c2360

M2A Implementation Commit A:

72e032c71d97eed2712552062a75fde5d29c2360

M2A Navigation Commit B:

88993df08212aa199b0b06f839c9c2d4cbe48529

remote mainから両Commitは取得可能。

前回報告の Ready for Owner push / LOCAL という表現は現在remote事実と一致しないため、
次Navigation更新時に訂正する。

---

# 2. M2Aで成立したものを壊さない

維持:

- TEGAKI_AUTHORING_DOCUMENT
- Scene / VisualFrame separation
- CAST Master
- Character Instance
- page-normalized Character area
- Core masked conditioning
- M1 canonical workflow
- M1/M1.1 regression

---

# 3. M2A ReportのTruth Correction

M2A Reportは削除しない。

新M2A.1 Reportで以下を明記する。

## Two Characters

Presence 3/3
Exact clean parallel placement 1/3
Other 2/3 = useful but staggered/occluded

よって:

2-character capability = USEFUL / SEED-SENSITIVE

## 3 Person

1/3 clear 3-person success
2/3 collapse

よって:

3-person capability = PARTIAL / SEED-SENSITIVE

## 4 Person

single-scene exact role layout = NOT READY

## ControlNet

Not needed for 1–2 character baseline

までは支持される。

しかし:

Not needed for exact 3–4 character composition

は未証明。

---

# 4. 添付MRP資料から採用する原則

今回のCardでは以下の知見をResearch Rulesとして使う。

## Rule A

Promptは長くするのではなく:

人数
→ Character
→ Action
→ Distance
→ Angle
→ Spatial Relation
→ Background

の責務を分ける。

## Rule B

複数人物では:

same scene
both fully visible / all visible
side-by-side
two distinct subjects
group_picture
lineup

等を必要時だけ使う。

## Rule C

人物別位置語は人物と結合する。

悪い:
Alice, Bob, left, right, foreground, background

良い概念:
Alice on the left side
Bob on the right side

または:
Alice large in foreground
Bob smaller in background

## Rule D

人物A/Bの前後差では:
perspective
foreshortening
を先に足さない。

先に:
large in foreground
smaller in background

## Rule E

3–4人物の正確な役割分離は高難度。

Promptを無限に伸ばさず、
必要ならControlNetへ分業する。

## Rule F

重要なPrompt benchmarkは1 seedで結論を出さず、
最低8 seedを基準にする。

---

# 5. 今回のProduct仮説

ユーザーに:

Left
Right
Foreground
Background
Side-by-side
Strength
ControlNet

を大量に操作させるのではない。

ユーザー入力:

Character rectangle
+
free text Prompt

内部Compilerが、
明確なgeometryの時だけ短いSpatial Hintを自動補助する。

---

# 6. 今回作るもの

M2A.1では:

Spatial Prompt Hint Compiler

のResearch implementationを作る。

例:

rough box left
→ optional "on the left side"

rough box right
→ optional "on the right side"

ただしhidden / internal。

まだUser-facing toggleを作らない。

---

# 7. Hint Compilerの入力

最低限:

- Scene geometry
- Character Instance areas
- Character count in Scene
- Character relative centers
- Character relative sizes

Prompt本文から人物性別等を無理に推論しない。

---

# 8. Hint Compilerの出力

各Instanceに:

spatial_hint

をderived execution dataとして付与してよい。

Persistent Authoring Documentの手入力Promptへ文字列を焼き込まない。

Authoring SSOTは汚さない。

---

# 9. Persistent Contractを増やしすぎない

今回:

spatial_hint
presence_hint

等は原則derived runtime data。

TEGAKI_AUTHORING_DOCUMENT v1.0.0へ新必須fieldを追加しない。

---

# 10. Horizontal Hint Classification

Character box center XをSceneまたはPage基準で分類。

例:

left third
center third
right third

出力候補:

on the left side
centered
on the right side

---

# 11. Hintを出さない曖昧帯

centerが境界付近、
boxes overlap大、
sceneが小さい等の場合:

NO_HINT

を許可。

無理にleft/rightを決めない。

---

# 12. Arrangement Hint

2人物で:

vertical overlap high
size ratio near 1
horizontal separation clear

ならResearch候補:

side-by-side
both fully visible
same scene

---

# 13. Presence Hint

Scene内character count:

2:
two distinct people, same scene, both fully visible

3:
three people, same scene, all visible

4:
four people, group composition, all visible

ただしこの語彙はResearch Candidate。

Production採用は実測後。

---

# 14. 性別count tagは自動生成しない

今回:

1girl and 1boy
2girls
3boys

等をidentity promptから推論しない。

fixture側で明示的に比較することは可。

将来必要ならCAST metadataで扱う。

---

# 15. Depth Hint

M2Aではgeometry-only small boxが人物抑止を起こした。

したがって:

small box = background

を無条件にはしない。

---

# 16. Relative-size Depth Candidate

明確なsize ratioがあり、
2人物以上で、
ユーザーgeometryが意図的に大小差を持つ場合だけResearch。

例:
area ratio >= 1.8

候補:

large:
large in the foreground

small:
smaller in the background

閾値はReportで明記。

---

# 17. Shot Typeを自動推論しない

boxが大きいから close-up と自動決定しない。

rectangleは rough occupancy であって、厳密なcamera cropではない。

---

# 18. Pose Hintを自動生成しない

今回Spatial Compilerは standing / sitting / walking をgeometryから推論しない。

Acting PromptはUser free text。

---

# 19. Prompt Composition order

Research variantではCharacter combined promptを概念的に:

identity
+
acting
+
derived spatial hint

とする。

必要なScene-level presence hintは別。

---

# 20. Spatial Hint Weight

最初:
unweighted

それで改善不足の場合だけ:
1.15
1.20
相当を研究。

最初から全Spatial phraseを強重み付けしない。

---

# 21. Character Strength

引き続き:
1.0
baseline。

Spatial Hint実験とcharacter_strength実験を同時に変えない。

---

# 22. Main Benchmark — 8 seed policy

以下は原則8 seeds。

候補:
42
77
101
133
202
303
404
505

他でもよいが固定して全比較で揃える。

---

# 23. Benchmark B — Two Distinct Characters

Fixture:

Alice rough left
Bob rough right

Prompts:
M2Aと同一。

比較:

B0 = current Level 0
B1 = + horizontal instance hints
B2 = + horizontal hints + presence/visibility scene hint

---

# 24. Bの評価軸

各seed:

- Presence Alice
- Presence Bob
- Alice identity
- Bob identity
- Alice slot
- Bob slot
- Both fully visible
- Unwanted occlusion
- Identity leakage

---

# 25. B Score

0:
one/both missing or wrong

1:
both present but major slot/identity collapse

2:
both present, useful composition, some occlusion/deviation

3:
both present, correct rough slots, clear identity, usable

8 seed平均を計算。

---

# 26. B Product Threshold

M2B coreとして:

score >=2 on at least 6/8 seeds

を目安。

Exact side-by-side 8/8は要求しない。

---

# 27. Benchmark B-SWAP

Bで最も代表的な3 seedsを選び、

same seed
same prompt
boxes swap only

B0/B1/B2で比較。

Derived left/right hintもswapに追随すること。

---

# 28. Benchmark C — Depth

M2A C1を8 seedsへ拡張。

比較:

C0 = equal boxes + manually written depth acting prompt
C1 = equal boxes + shorter depth phrase
C2 = geometry size difference + no derived depth
C3 = geometry size difference + derived depth hints

---

# 29. Depth Prompt Candidate

MRP参考:

foreground:
large in the foreground

background:
smaller in the background

避ける:

foreshortening
hand focus
85mm
200mm

を主制御にすること。

---

# 30. Depth評価

- Both present
- Foreground subject scale
- Background subject scale
- Depth hierarchy
- Occlusion usefulness
- Background subject dropout

---

# 31. Depth Product Decision

以下から一つ:

FREE_TEXT_SUFFICIENT
DERIVED_DEPTH_HINT_USEFUL
GEOMETRY_TOO_RISKY
CONTROL_REQUIRED

---

# 32. Benchmark H — 3 Distinct / Mixed Characters

M2Aの Alice + Alice + Bob はsame-identity duplicationという別難度も混ざる。

今回はまず:

Alice
Bob
Carol

の3 distinct CASTを先に試す。

3 non-overlap rough regions。

---

# 33. 3 Distinct比較

H0 = current Level 0
H1 = + horizontal/slot hints
H2 = + presence/all-visible scene hint
H3 = + arrangement hint when geometry supports

8 seeds。

---

# 34. 3 Distinct Acceptance

M2B general-purpose UIで「3人も普通にいける」と表現するには:

score >=2 on at least 5/8

程度を要求。

満たさなければ:

3 PERSON = ADVANCED / SEED-SENSITIVE

とする。

---

# 35. Same CAST + Other CASTは別評価

次に:

Alice_A
Alice_B
Bob

これは:
3-person count
+
same identity duplicate

の複合難度。

3 distinctと混同しない。

---

# 36. Same CAST Twice Same Scene

同一人物を一つのSceneに2体置くことは一般漫画では特殊ケース。

M2B coreをこれでHOLDしない。

Research status:
ADVANCED / SPECIAL

---

# 37. Same CAST Across Separate Scenes

これは漫画制作では重要。

最低4 seedで:

same CAST Master
different Scene
different Instance

を確認。

M2B coreではこちらを優先。

---

# 38. 4 Person

M2Aでmulti-cut化が出ている。

Prompt calibration後に最大4 seedsだけ再試験。

M2B core Gateにはしない。

---

# 39. 4 Person Product label

改善しても:
Advanced / Experimental

扱いでよい。

「4人完全制御」をM2B完成条件にしない。

---

# 40. Background Budget

Character spatial benchmarkでは背景情報量を抑える。

原則:
simple background

または空間成立に必要な家具だけ。

---

# 41. Background A/B

必要ならhard conditionのみ:

normal classroom detail
vs
simple classroom background

比較。

背景がsubject recallを奪っていないか確認。

---

# 42. Prompt order

Research promptは可能な限り:

subject / identity
→ acting
→ distance/depth
→ spatial relation
→ minimal background

---

# 43. No giant spell

失敗したconditionに20個タグを追加しない。

1仮説1変更。

---

# 44. ControlNet Escalation Gate v2

以下をPrompt/Region Calibration後に判断。

## Do not escalate

2-character:
6/8以上 useful

3-distinct:
5/8以上 useful

Depth:
6/8以上 useful

ならControlNet研究は後段。

---

# 45. Escalate weak block Control if

以下のどれか:

- 2-character slot adherence < 6/8
- 3-distinct usable < 5/8
- depth hierarchy < 6/8
- prompt helper improves little and seed collapse remains large

---

# 46. ControlNetを試す場合の目的

Poseではない。

rough character occupancy
slot separation
foreground/background block hierarchy

だけ。

---

# 47. ControlNet guide source

既存資産を最優先。

候補:

- TegakiMangaLayoutGuideGenerator
- existing simple mannequin / block output
- existing ControlNet loader/application
- AnyTest v4 Illustrious ControlNet

新しい3D Pose systemを作らない。

---

# 48. Block Guide

最小:

head circle
body rectangle / line
rough person block

程度。

白ハゲ漫画の簡易版。

---

# 49. Block GuideとCharacter Instance mapping

Research previewで:

block A -> Alice instance_id
block B -> Bob instance_id

を明示。

ただしControlNet自体がidentityを理解するのではない。

identityはregional prompt側。

---

# 50. Control strength

最大比較:

0.00
0.20
0.35

過去の0.75強拘束を繰り返さない。

---

# 51. Control schedule

既存AnyTest v4の安全な既知設定を参考。

必要以上に全step拘束しない。

具体値を変えるならReportに明記。

---

# 52. ControlNet A/B

ControlNetを発動した場合、
同じhard seedで:

Prompt+Region
vs
Prompt+Region+BlockCN 0.20
vs
Prompt+Region+BlockCN 0.35

---

# 53. ControlNet Success定義

改善:

- subject count
- rough slot occupancy
- depth separation

悪化:

- literal mannequin artifacts
- pose stiffness
- identity loss
- seed variation消失

---

# 54. Brainstorm Freedomを測る

Minimum-Handでは拘束しすぎもFAIL。

同じlayoutでseedを変えた時:

gesture
expression
camera nuance

に違いが残ること。

---

# 55. Freedom Score

簡易:

HIGH
MEDIUM
LOW

ControlNetでslotが改善しても Freedom LOW ならCore採用しない。

---

# 56. ControlNet採用判断

最終的に:

CORE_NOT_NEEDED
OPTIONAL_FOR_3PLUS
OPTIONAL_FOR_EXACT_LAYOUT
REQUIRED_FOR_CORE

のどれか。

---

# 57. 期待される可能性

現時点の仮説:

1–2 characters:
Core Prompt + Regionで十分

3 characters:
Prompt helper + seed searchで実用圏の可能性

4+ exact roles:
ControlNet/rough manga guideへ早めに送る可能性が高い

この仮説を実測。

---

# 58. Product Complexity Tier

Reportで:

Tier 1:
1 character

Tier 2:
2 distinct characters

Tier 3:
3 characters / depth hierarchy

Tier 4:
4+ / same-Cast duplicate same scene / exact interaction

と整理してよい。

---

# 59. UIへ戻す時の原則

M2B user surfaceはTier 1–2を中心にする。

Tier 3は works, seed-sensitive かもしれない。

Tier 4はAdvanced。

---

# 60. User-facing Spatial Selectorはまだ作らない

今回の結果が良くても:

Left
Center
Right
Near
Far

selectorをM2A.1で追加しない。

まずhidden compilerの有効性を見る。

---

# 61. Free Text First

M2BではActing Prompt:
普通のtext field
を主とする。

Presetは後段Shortcut。

---

# 62. Prompt helperの透明性

Debug JSONには:

- raw_identity_prompt
- raw_acting_prompt
- derived_spatial_hint
- scene_presence_hint
- effective_character_prompt

を出す。

何を足したか追跡可能にする。

---

# 63. Prompt helper OFF path

Research runnerでは:

spatial_hint_mode = off

を必ず保持。

Baseline比較を失わない。

---

# 64. Suggested modes

Research-only:

off
horizontal
horizontal_presence
spatial_depth

Production UIへそのまま出さない。

---

# 65. Region mask tuning

Prompt helper後も位置が弱い場合だけ:

set_cond_area = default
vs
mask bounds

を小規模比較してよい。

---

# 66. Feather tuning

必要な場合のみ:

0
8

16以上や大規模sweepは今回不要。

---

# 67. 一度に変えない

禁止:

spatial hint
+
strength 1.25
+
mask bounds
+
feather 16

を一度に投入。

因果性を失う。

---

# 68. Verification Runner

新規:

scripts/run_m2a1_prompt_region_calibration.py

推奨。

---

# 69. Automated Tests

既存128 testsを維持。

新規候補:

- test_m2a1_spatial_hint_compiler.py
- test_m2a1_prompt_composition.py
- test_m2a1_control_escalation_policy.py

---

# 70. Pure tests

最低限:

- left box -> left hint
- right box -> right hint
- center box -> centered/no hint policy
- ambiguous box -> no hint
- 2 side-by-side -> arrangement candidate
- large/small clear ratio -> depth candidate
- small ratio -> no depth hint
- derived hints do not mutate authoring document
- same raw document with hint off remains M2A-equivalent

---

# 71. Regression

M0/M0.1/M1/M1.1/M2A:
all existing tests PASS

---

# 72. Workflow root

変更しない。

workflows/
M1_MINIMUM_HAND_SCENE_DRAFT.json
README.md
Archive/

を維持。

M2A.1研究Workflowをrootへ追加しない。

---

# 73. Evidence directory

docs/verification/m2a1/

---

# 74. Contact Sheets

最低限:

- M2A1_TWO_CHARACTER_PROMPT_REGION.png
- M2A1_DEPTH_PROMPT_REGION.png
- M2A1_THREE_CHARACTER_PROMPT_REGION.png

ControlNet発動時だけ:

- M2A1_BLOCK_CONTROL_ESCALATION.png

---

# 75. Manifest

各condition:

- condition_id
- seed
- raw prompts
- derived hints
- effective prompts
- areas
- hint mode
- mask mode
- control mode
- control strength
- runtime_status
- visual_status
- review_method
- presence score
- identity score
- position score
- depth score
- freedom score
- output path

---

# 76. Visual score 0–3

MRP benchmark思想を採用。

0 = fail
1 = partial / poor
2 = useful
3 = clear success

Presence / Identity / Position / Depthは別採点。

---

# 77. Automated visual PASS禁止

生成成功:
runtime_status=PASS

Visualは目視後のみ。

---

# 78. M2A.1 Report

新規:

docs/reports/M2A1_PROMPT_REGION_CALIBRATION_AND_CONTROL_GATE_REPORT.md

---

# 79. Report必須内容

1. Fixed baseline SHA
2. M2A truth correction
3. MRP-derived rules used
4. Spatial hint compiler design
5. Two-character 8-seed baseline
6. Two-character hint variants
7. Swap causality
8. Depth 8-seed benchmark
9. 3-distinct 8-seed benchmark
10. Same CAST across scenes
11. Same CAST same scene special-case
12. 4-person result
13. Background budget finding
14. Mask-bound tuning if used
15. ControlNet escalation gate result
16. ControlNet comparison if used
17. Brainstorm freedom
18. Product complexity tiers
19. M2B recommendation
20. Advanced/ControlNet recommendation
21. Known limits
22. UI features still deferred

---

# 80. M2A.1 Acceptance

TWO-CHAR 8-SEED:
MEASURED

TWO-CHAR BEST MODE:
DECIDED

SWAP:
PRESERVED

DEPTH 8-SEED:
MEASURED

DEPTH POLICY:
DECIDED

3-DISTINCT 8-SEED:
MEASURED

SAME CAST ACROSS SCENES:
MEASURED

SAME CAST SAME SCENE:
CLASSIFIED SPECIAL / ADVANCED

4-PERSON:
CLASSIFIED

SPATIAL HINT COMPILER:
USEFUL / NOT USEFUL

AUTHORING DOCUMENT MUTATED BY DERIVED HINTS:
NO

CONTROLNET GATE:
DECIDED

BRAINSTORM FREEDOM:
MEASURED

OLD TESTS:
ALL PASS

---

# 81. M2B GO Option A

以下なら:

1–2 character capability useful
Prompt/Region mode robust enough

M2B:
Rough Region + Free Text

---

# 82. M2B GO Option A+

Spatial hintが明確に改善するなら:

Rough Region
+
Free Text
+
hidden automatic spatial helper

ユーザー手数は増やさない。

---

# 83. M2B GO Option C

3-personやexact slotで weak Block Controlが明確改善し、
Freedomを壊さない場合:

M2B Coreへ即強制しない。

まず:

Advanced Guide / 3+ Assist

候補とする。

---

# 84. M2A.2へ進む条件

ControlNetが有望だが今回の小試験だけでは採用判断できない場合:

M2A.2 — Rough Manga / Block Control Assist Study

を挟む。

---

# 85. ControlNetへ早々に流れない理由

Minimum-Handの価値は:

rectangle
+
prompt
+
seed

でまず回せること。

2人程度で十分ならControlNetを入口に置かない。

---

# 86. ControlNetを避けすぎない理由

MRP資料が示す通り:

3–4 people exact roles
complex foreground/background
contact
props

はPrompt-onlyの難度が急上昇する。

そこでSeedを何十回も回すより雑な白ハゲを描く方が早い場合は、
早めにAdvanced Assistへ送る。

---

# 87. Cost判断

Reportで各Tierについて:

Prompt tuning cost
Seed search cost
Control guide cost

を定性的に比較。

---

# 88. 最終Product判断の問い

「ControlNetなしで可能か？」

だけではなく、

「何回Seedを回せば使えるか？」
「Promptをどこまで書けばよいか？」
「それより雑な白ハゲを描く方が早いか？」

で判断。

---

# 89. Commit A

推奨:

feat(manga): calibrate prompt-region character staging before control escalation

含む:

- derived spatial hint research path
- tests
- verification runner
- evidence
- M2A.1 report
- STATUS / DOCUMENT_REGISTER

---

# 90. Commit B

推奨:

docs(manga): publish M2A.1 review target

GITHUB_ComfyUI:

Review Target = Commit A
Current Card = M2A.1
Next = M2B or M2A.2

---

# 91. Publication truth

実際にremoteへpush済みなら:
Published on remote main

localだけなら:
LOCAL ONLY

報告とGitHub実態を一致させる。

---

# 92. 最終回答Format

MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
72e032c71d97eed2712552062a75fde5d29c2360

M2A.1 IMPLEMENTATION COMMIT A:
M2A.1 NAVIGATION COMMIT B:
PUSH STATUS:

M2A TRUTH CORRECTION:
DONE / NOT DONE

TWO-CHAR B0 8-SEED:
TWO-CHAR B1 8-SEED:
TWO-CHAR B2 8-SEED:
BEST TWO-CHAR MODE:

SWAP CAUSALITY:
PASS / PARTIAL / FAIL

DEPTH C0:
DEPTH C1:
DEPTH C2:
DEPTH C3:
DEPTH POLICY:

3-DISTINCT H0:
3-DISTINCT H1:
3-DISTINCT H2:
3-DISTINCT H3:
BEST 3-PERSON MODE:

SAME CAST ACROSS SCENES:
SAME CAST SAME SCENE:
4 PERSON:

SPATIAL HINT COMPILER:
USEFUL / NEUTRAL / HARMFUL

MASK BOUNDS TEST:
NOT RUN / RESULT

FEATHER TEST:
NOT RUN / RESULT

CONTROLNET ESCALATION:
NOT TRIGGERED / TRIGGERED

BLOCK CN 0.20:
NOT RUN / RESULT

BLOCK CN 0.35:
NOT RUN / RESULT

BRAINSTORM FREEDOM:
HIGH / MEDIUM / LOW

PRODUCT CORE:
1 PERSON:
2 PERSON:
3 PERSON:
4+ PERSON:

M2B RECOMMENDATION:
OPTION A / OPTION A+ / OPTION C / HOLD

NEXT CARD:
M2B / M2A.2 / OTHER

OLD TESTS:
NEW TESTS:
TOTAL:

CONTACT SHEETS:
MANIFEST:
REPORT:

OWNER REVIEW RECOMMENDED:
YES / NO
CONDITIONS:

USER ACTION REQUIRED:

---

# 93. 最終原則

今回の目的はPromptだけに執着することでも、
ControlNetを避けることでもない。

優先順は:

Rough Region
↓
Short Prompt
↓
Hidden Spatial Hint if useful
↓
Seed Brainstorm
↓
必要な難度だけWeak Block Control
↓
Pose等はさらに後

M2Aで見えた:

1–2人物はかなり有望
3人物からseed sensitivityが急増
4人物でmulti-cut化

を正面から扱う。

「できた1枚」ではなく、
8-seed再現性とユーザー手数で次の設計を決めること。
