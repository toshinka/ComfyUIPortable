# ComfyUI Portable — M0 / Phase 3M-0
# Versioned Authoring Contract & Scene / Frame Separation Foundation
## Antigravity2 / Claude Opus 向け Bounded Implementation Card

## 推奨実行モデル

```text
Claude Opus
```

このCardは、通常のUI改修や反復実装よりも、
後続M1〜M4全体へ影響する「永続データ契約・ID・座標・互換境界」を固定する工程である。

そのため今回は、速度より

```text
既存契約の読解
矛盾検出
将来UIとの境界設計
破壊的変更の回避
```

を優先し、Opusを推奨する。

Sonnetでも施工可能だが、Sonnetを使う場合は本書の
「契約監査」「fixture」「legacy import」「fail-closed」Gateを省略しないこと。

---

# 0. このCardの性格

これは

```text
UIを作るPhase
```

ではない。

また、

```text
新しいRegional Backendを作るPhase
Poseを改善するPhase
生成品質を詰めるPhase
```

でもない。

目的はただ一つ。

```text
将来のMinimum-Hand Manga Authoring UIが、
Scene / CAST / Character Instance / Visual Panel Frame / Guideを
Backendから独立した一つの永続Authoring Documentとして安全に扱えるよう、
Versioned Contractと旧形式境界を固定する。
```

---

# 1. 最初に必ず読む順番

作業開始時、以下の順番を守る。

## 1

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

Raw:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB_ComfyUI.txt
```

ここから現在の:

```text
Review Target Commit SHA
Planning Commit SHA
Current direction
Current Card
```

を確認。

---

## 2

```text
ComfyUIPortable/docs/STATUS.md
```

---

## 3

```text
ComfyUIPortable/docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
```

---

## 4

```text
ComfyUIPortable/docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md
```

---

## 5

```text
ComfyUIPortable/docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
```

---

## 6

既存Contract:

```text
ComfyUIPortable/docs/CAST_SPEC_V1.md
ComfyUIPortable/docs/COMPILE_PLAN_V1.md
ComfyUIPortable/docs/MANGA_SCENE_DATA_CONTRACT.md
ComfyUIPortable/docs/LORA_ENTRY_V1.md
```

存在pathが異なる場合はDocument Registerから実体を特定する。

---

## 7

現在の実装でAuthoring Contractに関係するsourceのみ読む。

最低限候補:

```text
scene_spec.py
scene_compiler.py
cast_master.py
subscene_contract.py
interaction_resolver.py
impact_region_plan.py
panel_content_editor.py
character_staging_editor.py
```

必要な範囲だけ読む。

過去Phase全コードを再調査しない。

---

# 2. 現在のGitHub状態に関する注意

本Card発行前にWeb GPTが確認したremote mainでは:

Planning Commit A:

```text
261a3d7297455931d391e62f2d8a1335193d8d90
docs(manga): publish Astra SSOT and reset minimum-hand product direction
```

Navigation Commit B:

```text
09c48e42598f9cec4e720c9332eb251f58373663
docs(manga): update canonical external AI entry
```

である。

Gemini前回報告の:

```text
09c48e4266baee2834b6b158448f71295b9c065f
```

はremote上の実SHAと一致しないため使用しない。

ただしClaude作業開始時点で必ずGit履歴を再確認し、
この記載より現在のrepo事実を優先する。

---

# 3. 3M-Prep後の訂正

現在remoteにはPlanning文書が存在する。

したがって旧Entry内に:

```text
Push pending
LOCAL ONLY
```

等の記述が残っている場合は、
今回のCommit Bで現在事実へ修正する。

この訂正だけの独立Cardは作らない。

---

# 4. Product Context
# 契約設計時に絶対に忘れないこと

最終Productの基本導線:

```text
Resolution / Aspect Ratio
↓
Quality / Style Template
↓
CAST
↓
Rough Semantic Scene Regions
↓
Character Rough Regions
↓
Optional Rough Manga / Dummy Guide
↓
Visual Panel Frame / Control Guide
↓
Seed / Generate / Brainstorm
↓
Optional Refinement
```

ただしDevelopment Orderは:

```text
Scene-only
→ CAST
→ Rough Guide
→ UX Shell
```

である。

この二つを混同しない。

---

# 5. 最重要概念分離

## Semantic Scene Region

意味:

```text
この辺で何が起きるか
```

所有:

```text
Scene Prompt
Scene Negative
rough spatial area
input mode
instance membership
```

Regional Prompt / semantic placementの基準。

---

## Visual Panel Frame

意味:

```text
実際に見える漫画のコマ枠
```

所有:

```text
frame geometry
border / layout intent
guide linkage
```

Sceneと独立。

---

## 禁止

```text
Scene ID == Panel ID
Panel owns Scene
SceneをPanel frameの別名として保存
```

を新契約の基本にしない。

旧形式import時のみ明示Adapterで対応。

---

# 6. M0で固定する契約の対象

新Authoring Documentには少なくとも、
以下の概念を表現できること。

```text
Document
Page
Style / Global settings
Scenes[]
Visual Frames[]
CAST[]
Character Instances / Appearances[]
Guides[]
Generation settings / candidate-related stable inputs
```

ただしM0ではCandidate Browser自体は実装しない。

---

# 7. 正式名称は既存コードと衝突確認後に決める

Astra文書では:

```text
MANGA_AUTHORING_DATA
```

が設計上の呼称として使われることがある。

これは既存API名として仮定しない。

Claudeは既存namespaceを調べ、

```text
衝突しない正式Contract名
schema identifier
schema version
```

を決める。

例:

```text
TEGAKI_MANGA_AUTHORING_DOCUMENT
```

等でもよいが、独断で既存名を上書きしない。

---

# 8. Versioning

必須:

```text
schema_id
schema_version
```

を持つ。

要件:

```text
known older version
→ explicit migration/import

current known version
→ read/write

unknown newer version
→ fail closed
→ silent overwrite禁止
```

---

# 9. 永続正本は一つ

Authoring Documentを唯一の編集正本とする。

禁止:

```text
Canvas stateが別正本
Prompt panel stateが別正本
Compiler planが別正本
Backend node stateが別正本
```

Compiler outputはderived data。

UI stateはview/editor state。

Persistent authoring truthではない。

---

# 10. Unknown Field Preservation

forward compatibilityのため、
既知version内の未知フィールドを:

```text
read
→ edit unrelated known field
→ save
```

しても可能な限り保持する。

未知version全体を理解したふりをして保存しない。

---

# 11. Page Contract

最低限:

```text
page_id
width_px
height_px
normalized coordinate basis
style / global prompt intent
scenes[]
visual_frames[]
guides[]
generation settings
```

を表現できること。

Resolution変更時:

```text
normalized region geometry
```

は維持。

---

# 12. 座標系

新契約の基準:

```text
Page-normalized coordinates
x, y, w, h ∈ [0,1]
```

を基本とする。

Canvas pixel:
表示変換。

Panel-local:
legacy import / derived transform。

---

# 13. Rect contract

M0で実装するshape:

```text
rect
```

。

ただし将来:

```text
polygon
freeform
```

を追加できるよう、

```text
shape_type
```

を拡張可能にする。

M0でpolygon editorは作らない。

---

# 14. Geometry Validation

最低限:

```text
finite
not NaN
x/y/w/h numeric
w > 0
h > 0
normalized bounds policy explicit
```

を検証。

範囲外を黙ってclampするかrejectするかを契約で明文化。

推奨はAuthoring inputではfail clearly、
legacy importのみmigration policyを明示。

---

# 15. Stable IDs

最低限:

```text
page_id
scene_id
frame_id
cast_id
instance_id
guide_id
```

を安定IDとして扱う。

配列indexを永続identityにしない。

---

# 16. ID要件

```text
reorderしても変わらない
serialize / deserializeで維持
duplicate時は新ID
copy/moveでは規則明示
legacy importはdeterministicまたはexplicit mapping
```

。

---

# 17. Scene Contract

最低限:

```text
scene_id
name / label
prompt
negative_prompt
input_mode
area
order / priority
metadata
```

。

`input_mode`:

```text
simple
cast
```

をScene単位で持てること。

---

# 18. Simple Scene

Simple modeでは:

```text
Scene Promptに人物記述を含めてもよい
```

。

CAST必須ではない。

M1の最小導線を支える。

---

# 19. CAST Scene

Cast modeでは責務を分離。

```text
Scene
= background / common event / context

CAST Master
= identity

Instance
= acting / rough placement
```

。

---

# 20. Mode Switching

禁止:

```text
simple → cast 時にScene本文を解析して人物語を自動削除
cast → simple 時にCAST設定を破棄
```

。

要求:

```text
入力を保持
current execution modeだけ切替
```

。

---

# 21. CAST Contract

最低限:

```text
cast_id
display_name
identity_prompt
negative_prompt
metadata
```

。

LoRA / referenceはfieldを将来拡張可能にしてもよいが、
M0で実Backend対応を偽装しない。

---

# 22. Character Instance / Appearance Contract

意味:

```text
このSceneに、このCASTが、この辺へ出演する
```

。

最低限:

```text
instance_id
cast_id
scene_id
area
acting_prompt
negative_prompt_override
metadata
```

。

既存shot / pose / interaction情報を破壊せず保存できる余地を持つ。

---

# 23. PoseはM0の主対象ではない

既存:

```text
shot_type
pose_preset
interaction
camera-related metadata
```

を消さない。

しかし今回:

```text
新しいPose体系
3D skeleton
Pose Asset UI
```

を作らない。

---

# 24. Scene移動

Scene area移動時の契約:

```text
所属Instanceも同一deltaで移動
```

をAuthoring operationとして定義。

ただし単純Document validatorで勝手に移動させず、
pure operation helperとして実装する。

---

# 25. Scene resize

Sceneを拡縮した時:

```text
所属InstanceをScene基準で比例変換
```

するoperationを定義。

旧panel-local coordinate migrationとの整合をTest。

---

# 26. Visual Frame移動

Frameを移動しても:

```text
Scene
Character Instance
```

を自動移動しない。

SceneとFrameの独立性をTestで固定。

---

# 27. Visual Frame Contract

最低限:

```text
frame_id
shape
order
metadata
```

。

M0ではBorder style等を必要以上に増やさない。

既存Panel Layoutへ変換可能な最低限を優先。

---

# 28. Scene ↔ Frame relation

M0では:

```text
必須1:1 relation
```

を要求しない。

許可:

```text
1 Scene / multiple Frames
multiple Scenes / 1 visible Frame
Scene without Frame during editing
Frame without semantic Scene during editing
```

。

ただし生成可能条件はM1で定義してもよい。

---

# 29. Overlap

Scene regionは重なってよい。

Instance regionも重なってよい。

重要:

```text
editor z-order
semantic order
mask resolution order
```

を同一視しない。

---

# 30. M0 overlap contract

M0では少なくとも:

```text
stable explicit order / priority field
```

を保存できるようにする。

実生成mask semanticsは:

```text
PLANNED
```

として明示し、
M0 contract testで画像品質を証明したことにしない。

---

# 31. Mask policy

Astra提案:

```text
Scene:
deterministic priority

same Scene Character overlap:
weight normalization候補

Scene background:
character union subtraction候補
```

はある。

しかしM0でBackend挙動を断定しない。

Contractとして:

```text
mask_policy / overlap policyを後から表現可能
```

な拡張点を設ける。

---

# 32. Guide Contract

Guideは:

```text
Visual Frame Guide
Rough Manga / Dummy Guide
```

等を将来扱う。

M0最低限:

```text
guide_id
guide_type
asset reference
placement / fit transform
enabled
metadata
```

。

---

# 33. Guide AssetはBackend Objectではない

保存禁止:

```text
ControlNet tensor
ComfyUI runtime object
node link IDだけ
```

。

保存するのは:

```text
asset reference
intent
transform
```

。

---

# 34. Rough Dummy / 白ハゲはM3

M0ではGuide contractだけ。

人物ラフ:

```text
rough figure A → Alice
rough figure B → Bob
```

の対応生成は今回実装しない。

ただし後で対応情報を追加できるschema余地を残す。

---

# 35. Generation Settings

Minimum-Hand向けに最低限:

```text
seed
model/profile reference
optional basic generation settings
```

をAuthoring snapshotへ持てる構造を確認。

Sampler等Backendの巨大設定をAuthoring Coreへ直埋めしない。

---

# 36. Seedの意味

Seedはcreative brainstorm parameter。

M0では:

```text
seedを保存・復元できる
```

ことだけ固定。

Generate x4やCandidate UIは後段。

---

# 37. Legacy Import
# M0の最重要項目の一つ

既存:

```text
REGION_SPEC
CAST_SPEC
PAGE_COMPILE_PLAN関連source
旧KOMA / Panel-based authoring
```

を監査。

---

# 38. 旧契約を黙って意味変更しない

禁止:

```text
既存REGION_SPECのpanelを新Sceneとして扱うよう意味を書き換える
既存workflow JSONを一括変換
```

。

新契約とは明示Adapterで接続。

---

# 39. Legacy Import Table

Reportへ:

| Legacy Field | New Field | Transform | Lossless? | Warning |
|---|---|---|---|---|

を作る。

---

# 40. Legacy Panel-local coordinates

旧instanceがpanel-local座標の場合:

```text
panel geometry
+
local instance geometry
↓
page-normalized area
```

へ変換。

fixtureで数値検証。

---

# 41. Lossy conversion

旧形式→新形式でlossyなら:

```text
warning
diagnostic
```

を返す。

黙って捨てない。

---

# 42. New → Legacy adapter

新契約が旧Backendへ無損失で落とせる範囲は変換してよい。

表現不能:

```text
overlapping independent Scenes
multi-Scene one Frame
future non-rect
```

等は:

```text
fail closed / explicit unsupported
```

。

Sceneを偽Panelへ捏造しない。

---

# 43. Compiler Boundary

最終:

```text
Authoring Document
↓ normalize / validate
Semantic Compiler
↓
existing execution plan
```

。

M0では必要最小限のbridge/interfaceまで。

Regional Backend全面書換えは禁止。

---

# 44. Backend independence

Authoring Documentへ入れない:

```text
Impact RegionalPrompt object
Advanced-ControlNet object
KSampler provider
ComfyUI graph link ID
```

。

---

# 45. Suggested module structure

既存構造を確認してから決める。

候補:

```text
authoring_contract.py
authoring_migration.py
authoring_operations.py
```

。

既存適切moduleがあるなら統合してよい。

無意味にfile数を増やさない。

---

# 46. Pure Logic優先

M0 coreは:

```text
pure Python
```

でTest可能にする。

ComfyUI server起動を必須にしない。

---

# 47. Fixture 0
# Empty editable state

```text
0 Scenes
0 Frames
0 CAST
```

を保存可能。

GenerateはM1で拒否してよい。

Validatorが勝手に全画面Sceneを追加しない。

---

# 48. Fixture 1
# Two independent Scenes + Two Frames

```text
Scene A left-ish
Scene B right-ish

Frame 1 top
Frame 2 bottom
```

のように、

```text
Scene geometry
≠
Frame geometry
```

を明確にする。

SceneとFrameが別配列 / 別IDであることをTest。

---

# 49. Fixture 2
# Overlapping Scenes

```text
Scene A
Scene B
```

が一部overlap。

保存→再読込でgeometry / orderを保持。

---

# 50. Fixture 3
# Same CAST repeated

```text
CAST Alice = 1 Master

Alice Instance 1 @ Scene A
Alice Instance 2 @ Scene B
Alice Instance 3 @ Scene C
```

。

全instance_idは別。

cast_idは同じ。

---

# 51. Fixture 4
# Mixed simple / cast

```text
Scene A = simple
Scene B = cast
Scene C = simple
```

を同Pageで保持。

---

# 52. Fixture 5
# Resolution change

```text
832x1216
→
1216x832
```

など解像度を変更しても、
normalized Scene / Instance / Frame areaを保持。

---

# 53. Fixture 6
# Scene move

Scene delta:

```text
dx / dy
```

。

所属instancesが同delta。

別Scene instanceは不変。

Framesは不変。

---

# 54. Fixture 7
# Scene resize

Scene resize後、
所属instanceが比例変換。

---

# 55. Fixture 8
# Frame move

Frameのみ移動。

Scene / Instanceは不変。

---

# 56. Fixture 9
# Legacy import

代表的な旧:

```text
Panel/KOMA + Character binding
```

fixtureを新documentへimport。

ID / coordinate / prompt / CAST associationを検証。

---

# 57. Fixture 10
# Invalid references

以下reject:

```text
instance.cast_id missing
instance.scene_id missing
duplicate stable ID
invalid schema version
NaN geometry
```

。

---

# 58. Fixture 11
# Unknown field round-trip

current schema documentに:

```text
future_vendor_extension
```

等未知field追加。

read → unrelated edit → saveで保持。

---

# 59. Fixture 12
# Unknown newer schema

```text
schema_version = current + 99
```

。

上書き禁止。

明示エラー。

---

# 60. Serialization

最低限:

```text
dict
JSON
```

round-trip。

同一semanticsを維持。

Key orderingの文字列一致は必須でない。

---

# 61. Canonical validation report

Validatorは:

```text
errors[]
warnings[]
normalized_document
```

等、機械可読diagnosticを返せる設計が望ましい。

既存設計に合わせて調整可。

---

# 62. Fail Closed

特に:

```text
unknown version
invalid foreign key
lossy unsupported new→legacy conversion
```

はfail closed。

---

# 63. UI実装禁止

今回作らない:

```text
Canvas
Scene Editor
CAST Chips
Inspector
A1111 skin
SPA
Comic Creator integration
```

。

---

# 64. Backend比較禁止

今回やらない:

```text
Inspire parity
Advanced-ControlNet parity
Attention Couple comparison
```

。

これらは別Card。

---

# 65. Pose / Interaction施工禁止

今回:

```text
新Pose UI
Handshake改善
SubScene UI
```

を追加しない。

既存データを壊さず保持するだけ。

---

# 66. Comic Creator

今回:

```text
REFERENCE
```

のまま。

Fork / selective reuse調査へ逸脱しない。

---

# 67. Visual generation

M0の合格に新規生成画像は必須ではない。

主Evidence:

```text
schema
migration
operations
fixtures
tests
```

。

---

# 68. Existing workflows regression

最低限:

```text
既存workflow JSONを変更しない
既存load pathを壊さない
```

ことを確認。

全55 workflowのlive generation再実行は不要。

構造checkで十分。

---

# 69. Test naming

候補:

```text
test_m0_authoring_contract_versioning.py
test_m0_scene_frame_separation.py
test_m0_authoring_ids.py
test_m0_authoring_coordinates.py
test_m0_authoring_operations.py
test_m0_legacy_import.py
test_m0_unknown_fields.py
test_m0_fail_closed.py
```

既存test layoutに合わせて命名変更可。

---

# 70. Required M0 report

新規:

```text
ComfyUIPortable/docs/reports/M0_3M0_VERSIONED_AUTHORING_CONTRACT_REPORT.md
```

。

---

# 71. Report structure

最低限:

```text
1. Scope
2. Read Baseline
3. Contract Name / Version
4. Authoring Document Shape
5. Page / Scene / Frame / CAST / Instance / Guide
6. Scene vs Frame Separation
7. Coordinate Contract
8. Stable ID Contract
9. Simple / Cast Mode
10. Overlap / Order Contract
11. Serialization
12. Unknown Field Policy
13. Unknown Version Policy
14. Legacy Import Mapping
15. Lossy Conversion Policy
16. Pure Operations
17. Fixtures
18. Tests
19. Existing Workflow Regression
20. Runtime / UI Non-Changes
21. Known Limitations
22. Next Card Recommendation
23. Claude独自判断
```

---

# 72. 「事実」と「提案」を分ける

Reportで:

```text
VERIFIED
IMPLEMENTED
PLANNED
DEFERRED
UNSUPPORTED
```

を区別。

---

# 73. M0 Acceptance Gates

必須:

```text
VERSIONED AUTHORING DOCUMENT:
PASS / FAIL

SCENE / FRAME SEPARATION:
PASS / FAIL

STABLE IDS:
PASS / FAIL

PAGE-NORMALIZED COORDINATES:
PASS / FAIL

SIMPLE / CAST PER-SCENE MODE:
PASS / FAIL

SAME CAST MULTI-INSTANCE:
PASS / FAIL

OVERLAP ORDER PERSISTENCE:
PASS / FAIL

SERIALIZATION ROUNDTRIP:
PASS / FAIL

UNKNOWN FIELDS PRESERVED:
PASS / FAIL

UNKNOWN NEWER VERSION FAIL-CLOSED:
PASS / FAIL

LEGACY IMPORT:
PASS / PARTIAL / FAIL

LOSSY CONVERSION DIAGNOSTICS:
PASS / FAIL

SCENE MOVE OPERATION:
PASS / FAIL

SCENE RESIZE OPERATION:
PASS / FAIL

FRAME INDEPENDENCE:
PASS / FAIL

EXISTING WORKFLOW STRUCTURAL REGRESSION:
PASS / FAIL

UI CHANGED:
NO / YES

BACKEND CHANGED:
NO / YES

POSE / INTERACTION EXPANDED:
NO / YES
```

---

# 74. Product sanity gate

Claude自身で最後に確認:

```text
このContractは将来、
Resolution
→ Style
→ CAST
→ Scene
→ Character
→ Guide
→ Seed
というUIを、Backendの都合で歪めず表現できるか？
```

YESでなければGOしない。

---

# 75. M1へ進める条件

M0後、M1では:

```text
Scene-only Minimum-Hand Draft
```

へ進む。

つまり:

```text
Resolution
Style Template
Scene rectangle
Scene Prompt
optional frame guide
Seed
Generate
```

。

M0の時点でM1 UIを作らない。

---

# 76. Commit A
# Implementation / Contract

推奨message:

```text
feat(manga): establish versioned authoring contract and scene-frame separation
```

含む:

```text
contract
migration
operations
fixtures
tests
M0 report
STATUS / Document RegisterのCurrent Card更新
```

。

---

# 77. Commit B
# Navigation

推奨message:

```text
docs(manga): publish M0 review target
```

変更:

```text
ComfyUIPortable/GITHUB_ComfyUI.txt
```

必要なら:

```text
GITHUB.TXT
```

はpointerとしてのみ維持。

---

# 78. Commit Bで更新するもの

```text
Review Target Commit SHA:
<Commit A SHA>
```

。

Planning Commit SHA:

```text
261a3d7297455931d391e62f2d8a1335193d8d90
```

は戦略SSOT commitとして維持してよい。

---

# 79. GITHUB_ComfyUI Reading Order更新

Current Cardを:

```text
M0 / 3M-0
```

完了状態へ。

Next Card candidate:

```text
M1 / 3M-1 — Scene-only Minimum-Hand Draft
```

へ更新。

---

# 80. Publication status correction

remoteへ実際にpush済みなら:

```text
Push pending
LOCAL ONLY
```

等の古い文言を残さない。

最終remote事実を書く。

---

# 81. Push policy

Owner / Antigravity環境の現在ルールに従う。

もしpush権限を持っていても、
既存運用がOwner pushなら勝手に変更しない。

最終報告:

```text
LOCAL COMMIT ONLY
PUSHED
```

を明示。

---

# 82. 最終回答フォーマット

```text
MODEL USED:
Claude Opus / Claude Sonnet

BASELINE GITHUB_COMFYUI SHA:
BASELINE REVIEW TARGET:
BASELINE MAIN HEAD:

CONTRACT NAME:
SCHEMA ID:
SCHEMA VERSION:

IMPLEMENTATION COMMIT A:
NAVIGATION COMMIT B:
PUSH STATUS:

VERSIONED AUTHORING DOCUMENT:
SCENE / FRAME SEPARATION:
STABLE IDS:
PAGE-NORMALIZED COORDINATES:
SIMPLE / CAST MODE:
SAME CAST MULTI-INSTANCE:
OVERLAP ORDER:
SERIALIZATION:
UNKNOWN FIELD PRESERVATION:
UNKNOWN VERSION FAIL-CLOSED:
LEGACY IMPORT:
LOSSY CONVERSION DIAGNOSTICS:
SCENE MOVE:
SCENE RESIZE:
FRAME INDEPENDENCE:
WORKFLOW REGRESSION:

UI CHANGED:
BACKEND CHANGED:
POSE / INTERACTION EXPANDED:

M0 REPORT:
NEXT RECOMMENDED CARD:
USER ACTION REQUIRED:
```

---

# 83. Claudeへの最終注意

今回、良かれと思って:

```text
UIまで作る
Canvasまで作る
Backendまで整理する
Poseを改善する
Comic CreatorをForkする
```

ところまで進まないこと。

このCardの価値は:

```text
後続のすべてのUIが乗れる、
小さく明確で壊れにくいAuthoring Contractを固定すること
```

にある。

---

# 84. 最終原則

```text
Product meaning
≠
Backend representation
```

。

```text
Semantic Scene
≠
Visual Panel Frame
```

。

```text
Character Rough Region
≠
Pose
```

。

```text
Development order
≠
Final user flow
```

。

この4つを契約で壊さないこと。

M0完了後、Web GPTが固定CommitをレビューしてからM1へ進む。
