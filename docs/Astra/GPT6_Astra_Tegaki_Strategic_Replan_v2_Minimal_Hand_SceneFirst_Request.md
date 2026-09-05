# GPT-6 Astra 向け
# Tegaki / ComfyUI Manga Authoring
# 戦略再整理・資産棚卸し・UI/GUI再定義 指示書 v2
## — Minimum-Hand / Scene-First / Brainstorm-First / MRP-Inspired —

このv2は、以前のAstra向け指示書を置き換える。

今回の修正理由は、Productの優先順位がさらに明確になったため。

最重要点は:

```text
Pose Editorを作ること
```

ではなく、

```text
最小の入力手数で、
位置・登場人物・コマ構成をそこそこ誘導しながら、
Seedの揺らぎを残した漫画Draftを高速に回せること
```

である。

---

# 0. 最初に必ず確認するもの

GitHub入口:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

必ず最初に読み、

```text
Review Target Commit SHA
```

を固定する。

本指示書作成時点では:

```text
Phase 3L complete
Review Target:
5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8
```

だが、Astra作業開始時点で必ず再確認すること。

---

# 1. Productを一文で理解する

暫定定義:

```text
「解像度とCASTを決め、
SceneとCharacterをキャンバスへ雑に置くだけで、
対応PromptとSeed変化を使って漫画Draftを高速に回し、
必要になった時だけControlNet・Pose・SubSceneへ精密化できる、
MRP発展型の漫画Authoring Frontend」
```

Astraはこれをより良く言い換えてよい。

---

# 2. 最重要Product Principle

中心:

```text
Minimum Hand
+
Useful Guidance
+
Preserved Randomness
```

つまり:

```text
入力を増やしすぎない
しかし完全ランダムにもさせない
```

を最優先する。

---

# 3. Primary User Flow
# 今回最重要

以下をProductのPrimary Pathとして再定義する。

```text
1. Resolution / Aspect Ratio
↓
2. Global Quality / Style Prompt
   （ほぼテンプレート）
↓
3. CAST設定
↓
4. Rough Scene Regionsを雑に配置
↓
5. 各SceneへCAST Character Regionsを雑に配置
↓
6. 必要ならRough Manga / Dummy Figure GuideをControlNetへ
↓
7. Draft Generate
↓
8. Seedを変えてBrainstorm
↓
9. 良い案を選ぶ
↓
10. 必要な部分だけRefine
```

Refineは後段:

```text
Pose
Shot preset
Camera
Mask
Interaction
SubScene
```

---

# 4. 非常に重要
# Scene Region と Panel Frame を分離する

以前の計画では「Panel Rectangle」という言い方が前に出ていたが、
今後は概念を分ける。

## Semantic Scene Region

```text
どの領域で何が起きるか
```

を指定する粗い矩形。

役割:

```text
Scene Prompt scope
Character attendance
Character spatial rough placement
Regional conditioning
```

これは見た目のコマ枠とは限らない。

---

## Visual Panel Frame

```text
実際に漫画として見えるコマ枠
```

役割:

```text
frame topology
border geometry
manga layout
```

こちらは主に:

```text
Panel Layout
ControlNet lineart / guide
```

で制御する。

---

# 5. Scene-firstで考える

初期ユーザー操作:

```text
「この辺でScene A」
「ここにAlice」
「ここにBob」
```

程度でよい。

最初から厳密な漫画枠を描かせない。

その後:

```text
ControlNet Panel Guide
```

で実際のコマ枠を整える。

---

# 6. MRPとの関係

旧MRPはユーザーにとって:

```text
矩形を直接置ける
何番が何処か分かる
Promptと領域の対応が見える
```

という点が良い。

しかし新Toolでは:

```text
MRP Region
```

をそのまま:

```text
Final Panel Frame
```

として扱わない。

MRPのDirect Manipulation UXを継承しつつ、

```text
Semantic Scene Geometry
Visual Panel Geometry
```

を別Layerとして持つ。

---

# 7. 初期Prompt構造

最初の入力順:

```text
Resolution
↓
Quality / Style
↓
CAST
↓
Scene
↓
Character acting
```

Quality PromptはほぼTemplateでよい。

例:

```text
manga style
monochrome / color
high quality
clean lineart
...
```

ユーザーが毎回長文を入力する必要はない。

---

# 8. CAST

CAST設定では:

```text
Name
Identity Prompt
Negative
optional LoRA
optional Reference
```

を持つ。

例:

```text
Alice
1girl, blonde twin tails, blue eyes, school uniform
```

このMaster PromptをCharacter Regionへ継承。

---

# 9. Rough Scene Region

Sceneには:

```text
Scene Prompt
optional Negative
rough area
CAST attendance
```

を持つ。

Scene rectangleは:

```text
「ここら辺にこの出来事」
```

程度の指定。

厳密なMask編集を初期操作にしない。

---

# 10. Character Rough Region

Character placementは:

```text
Rectangle / rough area
```

でよい。

意味:

```text
Aliceはこの辺
Bobはこの辺
```

。

このRectangleはCharacter Instanceの初期Spatial Representation。

---

# 11. 最優先するControlNet用途
# Pose人形より重要

ユーザーは、

```text
白ハゲ / 棒人間 / 雑な漫画ラフ
```

を描いてControlNetへ渡せれば、
かなりの構図誘導ができる。

したがって最優先すべきは:

```text
Rough Manga Guide
+
Character Region Assignment
```

である。

例:

```text
雑な人物Aの上にAlice Region
雑な人物Bの上にBob Region
```

この対応が崩れないことを優先。

---

# 12. 「白ハゲ漫画」優先原則

AstraはProduct Gateを:

```text
3D Pose mannequin works
```

より先に:

```text
rough dummy manga + CAST regions works
```

へ置く。

重要:

```text
Rough composition image
↓
ControlNet
+
Character semantic regions
↓
CAST identity follows intended figure
```

が成立すること。

---

# 13. Poseの優先順位を下げる

Poseは便利だがCoreではない。

優先順位:

```text
1. Rough Scene
2. Rough Character placement
3. Rough Control guide
4. Seed Brainstorm
5. Prompt template assistance
6. Candidate selection
7. Pose refinement
```

Pose Editorは:

```text
全体が完成してから追加できるAdvanced Capability
```

くらいに扱ってよい。

---

# 14. Seed Randomnessは正式なCreative Feature

Seedは単なるDebug parameterではない。

正式な:

```text
Brainstorm mechanism
```

として扱う。

Goal:

```text
配置・CASTはある程度維持
演技・ポーズ・細部は毎回少し変わる
```

。

---

# 15. 過剰制御を避ける

最初から:

```text
pose skeleton
camera exact angle
joint constraints
strict mask
```

を積みすぎると、
Brainstormの価値が落ちる。

Core Draftでは:

```text
必要最低限の位置誘導
+
Prompt
+
Seed Randomness
```

を優先する。

---

# 16. Randomness Budget

Astraは新Master Plan内で:

```text
何を固定するか
何を揺らすか
```

を明示する。

推奨:

## Draftで固定

```text
CAST identity
rough scene location
rough character location
panel frame topology
```

## Draftで揺らす

```text
pose
gesture
facial expression detail
camera nuance
background detail
cloth / hair variation
```

---

# 17. Character Placement Template
# 後段機能

将来:

```text
Left
Center
Right

Near
Medium
Far

Close-up
Bust
Half
Full
```

などをTemplate selectorとして用意する価値がある。

これを選ぶと:

```text
area preset
+
optional prompt token
```

へ変換できる。

ただし初期MVPのGateにはしない。

---

# 18. Prompt Template
# 後段機能

Regionへ添えるPromptを簡単にする。

例:

```text
Position:
Left / Center / Right

Distance:
Near / Medium / Far

Acting:
Talking / Walking / Looking / Holding
```

選択結果を:

```text
prompt_override
```

へ安全にcomposeする。

しかしこれはCore Draft成立後。

---

# 19. A1111風GUIの重要性

3D Pose Editorより先に、
ユーザーが:

```text
どこから触ればよいか
```

分かる画面が重要。

ComfyUI Node Graphを直接Main UXにしすぎない。

目標:

```text
A1111 / Forgeのように
上から順に設定すれば生成できる
```

感覚。

---

# 20. A1111風Shellの候補

概念的には:

```text
[ Resolution / Project ]

[ Global Quality / Style Prompt ]

[ CAST ]
[Alice] [Bob] [+]

[ Scene / Canvas ]
 ┌──────────────────┐
 │ Scene A          │
 │  [Alice] [Bob]   │
 └──────────────────┘

[ Scene Prompt / Character Inspector ]

[ Seed / Generate ]
[ Generate ] [Generate x4]
```

Advanced:

```text
▸ Panel Frame Control
▸ Rough Guide / ControlNet
▸ Advanced Pose
▸ SubScene
▸ Interaction
```

---

# 21. 既存 ComfyUI Comic Creator を必ず監査する

対象:

```text
https://github.com/ketle-man/comfyui-comic-creator
```

これはPhase 3LのPrior-Art候補に追加する。

Astraは必ず実コード / README / architectureを確認する。

---

# 22. ComfyUI Comic Creatorで既に確認できる重要機能

現README上、少なくとも:

```text
ComfyUI上で動くStandalone SPA
Work / Page management
Width / Height / Resolution
Panel template
Panel split wizard
Layout canvas
Image drag/drop
Draft layer
Generate modal
Overall prompt
Panel N prompt tabs
T2I / I2I
Workflow Studio integration
3D pose
Mask/Image editor
```

を持つ。

これは単なる参考以上の価値がある。

---

# 23. ComfyUI Comic CreatorのLicense

現Repositoryは:

```text
MIT License
```

。

したがってLicense上は:

```text
use
modify
merge
publish
sublicense
```

が可能。

ただし著作権表示とLicense条件は遵守。

Astraは技術的再利用可能性を評価する。

---

# 24. Comic Creatorで最優先で見る部分

全部を統合しようとしない。

優先監査:

```text
A. SPA shell
B. ComfyUIから独立したauthoring surface
C. Work resolution management
D. Panel template / split wizard
E. Layout Canvas
F. Draft Layer
G. Generate modal
H. Overall / Panel prompt tabs
I. Workflow Studio bridge
J. ComfyUIへの戻し方
```

---

# 25. Comic Creatorで初期的に不要なもの

以下は今回のCore Goalではない。

```text
Speech balloons
Font manager
3D text
EPUB export
Nanobanana
Full layer image editor
Manga effects
Complex painting suite
Advanced 3D pose editor
```

これらの存在にProduct計画を引っ張られない。

---

# 26. Comic Creatorとの統合パターンを比較する

Astraは最低3案を比較。

## Option A
UX / architecture reference only

```text
Tegaki独自 Authoring SPA
Comic Creatorは参考
```

## Option B
Selective reuse

```text
Canvas / Work / Generate UI等だけ一部流用
```

## Option C
Fork / merge base

```text
Comic CreatorをShellとして
Tegaki Semantic Compilerを接続
```

---

# 27. Comic Creator統合判断

次を比較:

```text
Maintenance burden
Code coupling
Authoring state compatibility
Canvas object model
Workflow execution bridge
Custom Node dependency
Upgradeability
UX complexity
How much unused editor code comes along
```

「機能が多いから採用」ではなく、

```text
Minimum-Hand Productに近づくか
```

で判断。

---

# 28. 特に注目するGenerate UI

Comic Creatorは:

```text
Overall prompt
Panel N prompt
T2I / I2I
Generate
```

を一つのModalで扱う。

これはMRPの:

```text
Region ↔ Prompt
```

思想と近い。

Astraは:

```text
Global
Scene
CAST
```

へ再構成できるか検討する。

---

# 29. 「Panel Prompt」ではなく「Scene Prompt」も検討

Comic CreatorのPanel Prompt tabをそのまま使う必要はない。

Tegakiでは:

```text
Visual Panel
Semantic Scene
```

が違う。

UI上:

```text
Scene 1
Scene 2
```

をPrompt tabとして扱い、

Visual Panel Frameは別Control Layerでもよい。

---

# 30. Scene / Panel関係のData Model

Astraは少なくとも以下を比較。

## Model A

```text
Panel owns Scene
```

## Model B

```text
Scene owns rough region
Panel Frame is independent visual layer
```

## Model C

```text
Page
├ Semantic Scenes
└ Visual Panels
```

今回のProduct意図からはCが有力。

ただし実装複雑度も評価。

---

# 31. 最小手MVP Gate
# Astraに最優先で再定義させる

最初の実用Gate:

```text
Resolution
Quality Template
CAST A/B
Rough Scene Regions
Rough Character Regions
Panel Frame Guide
Seed
Generate
```

だけで:

```text
「それなりに誘導された漫画Draft」
```

が出ること。

---

# 32. MVPで不要

MVP Gateに含めない:

```text
3D pose editor
handshake precision
complex interaction UI
manual mask painting
SubScene editing
candidate pose extraction
advanced LoRA locality
```

既存Capabilityとして裏に残してよい。

---

# 33. 白ハゲ / Rough Guide MVP Gate

もう一つの重要Gate:

```text
User rough manga guide
+
Scene regions
+
Character regions
+
CAST
```

で、

```text
rough figure A → Alice
rough figure B → Bob
```

をある程度維持して生成できること。

これはPose Editorより上位のProduct Gate。

---

# 34. ControlNet Strategy

ControlNetは:

```text
Final determinism
```

のためだけではない。

初期用途:

```text
rough frame
rough dummy body
rough composition
```

をそこそこ守らせるため。

細かいPose固定は後段。

---

# 35. Seed UI

A1111風に:

```text
Seed
Randomize
Reuse
Batch Count
```

程度が直感的。

Brainstormでは:

```text
Generate x4
```

等を重視。

---

# 36. Candidate UI
# 後段

最初から高度なCandidate Browserは不要。

まず:

```text
Seedを変えて回せる
```

で十分。

後から:

```text
thumbnail grid
reuse seed
lock composition
extract pose
```

へ拡張。

---

# 37. Current Technical AssetsをProduct順で棚卸しする

AstraのAsset Ledgerは、
研究Phase順ではなくProduct Flow順にも並べる。

例:

```text
Resolution
Global Prompt
CAST
Scene
Character Placement
Panel Frame
Control Guide
Generate
Seed
Refinement
```

---

# 38. Workflow Inspection Priorityを更新

## Tier S0 — Product Spine

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG
03_MANGA_REGIONAL_PROMPT
07_MANGA_REGION_EDITOR_UI_TEST
09_MANGA_REGIONAL_GENERATION_POC
54-59 Character Spatial Foundation
70 Mixed Manga Page
71 Backend Parity
```

## Tier S1 — Advanced Capability

```text
66 Pose Guide Only
67 Handshake
68 Mainline SubScene
69 SubScene Swap
```

Pose / HandshakeをS0から下げる。

---

# 39. Phase 3Lの成果の扱い

Phase 3Lは重要。

しかし:

```text
SubScene
Handshake
Pose
```

がPrimary UIになったという意味ではない。

これらは:

```text
Advanced capability
```

が成立したと理解。

次はProduct入口を簡単にするPhaseへ進むべき。

---

# 40. Astra成果物を更新

以下4文書:

```text
ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md
ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md
```

旧名称:

```text
ASTRA_RAPID_MANGA_AUTHORING_UX_BLUEPRINT.md
```

でもよいが、
中身ではMinimum-Handを最上位に置く。

---

# 41. UX Blueprintで必ず描く画面

最低限:

## Screen / Area 1
Global

```text
Resolution
Style / Quality Template
Model / optional basic generation settings
```

## Screen / Area 2
CAST

```text
Alice
Bob
+
```

## Screen / Area 3
Canvas

```text
Semantic Scene Region
Character Region
Visual Panel overlay
Rough Control Guide
```

## Screen / Area 4
Inspector

```text
Selected Scene Prompt
Selected Character Prompt
```

## Screen / Area 5
Generate

```text
Seed
Randomize
Batch
Generate
```

---

# 42. ComfyUI内のUX限界も判断する

Astraは:

```text
Node-based UIを頑張って整える
```

だけでなく、

```text
Standalone SPA
ComfyUI extension panel
A1111-like skin
```

を比較。

Comic CreatorはStandalone SPAの実例として扱う。

---

# 43. A1111風Skinを正式候補へ

比較:

```text
A. Current node workflow
B. ComfyUI sidebar / extension panel
C. Standalone SPA
D. Comic Creator reuse/fork
```

判断基準:

```text
First-time clarity
Minimum clicks
Canvas usability
Prompt readability
ComfyUI maintenance
Backend portability
```

---

# 44. Product Acceptance Metric

技術PASSだけでは不足。

AstraはProduct Gateに:

```text
First useful draftまでの操作数
```

を加える。

例:

```text
Resolution select
2 CAST setup
2 Scene rectangles
2 Character rectangles
Generate
```

程度。

---

# 45. 「操作数」を計画に書く

Astraは主要Flowごとに:

```text
Required clicks
Required text fields
Advanced controls exposed
```

を概算。

目的:

```text
Minimum-Hand
```

を定量的に守る。

---

# 46. 過度なTemplateも避ける

Template selectorを増やしすぎると、
結局設定UIが複雑になる。

位置 / 距離Prompt Templateは:

```text
optional shortcut
```

として後段。

まずCanvas rectangleが主。

---

# 47. Final Architecture Principle

```text
User:
rough semantics

Compiler:
structured translation

Backend:
precise execution
```

ユーザーにBackend precisionを直接入力させすぎない。

---

# 48. Astraが必ず答える追加質問

### Q1
Semantic Scene RegionとVisual Panel Frameを分けるべきか。

### Q2
Rough Manga Guide + CAST Region assignmentを
どのData Modelで保持するか。

### Q3
Pose機能をどこまでCoreから外すべきか。

### Q4
A1111風Skin / SPAのどれが最短か。

### Q5
comfyui-comic-creatorを:
REFERENCE / SELECTIVE REUSE / FORK
のどれにするか。

### Q6
Comic Creatorから再利用するとしたら:
どのfiles / modules / state model / UI piecesか。

### Q7
MRP CanvasとComic Creator Canvasのどちらを
新UIの土台に近いと評価するか。

### Q8
First Useful Draftを何操作以内にするか。

---

# 49. GITHUB.TXT更新

Astra計画がまとまったら、
GITHUB.TXTに:

```text
Strategic Planning SSOT
```

sectionを追加。

さらに:

```text
External UI / Prior-Art References
```

として最低限:

```text
MRP Navigation
ComfyUI Comic Creator
```

へのリンクを残す。

---

# 50. GITHUB.TXT Reading Order

外部Web GPT向け:

```text
1. GITHUB.TXT
2. Astra Master Plan
3. Minimal-Hand UX Blueprint
4. Asset Inventory
5. Current Phase Report
6. Only relevant Workflow / Code
```

---

# 51. 次Phaseの性格

Astraが整理した後の次実装は、
さらにPoseを増やすPhaseではなく、

```text
Minimum-Hand Authoring Shell
```

を作る方向を第一候補として評価。

暫定:

```text
Phase 3M
Minimum-Hand Manga Authoring Shell
&
Scene-First Rapid Staging
```

---

# 52. Phase 3M暫定Product Gate

```text
Resolution
Style template
CAST
Scene rectangle
Character rectangle
Panel frame guide
Seed
Generate
```

を一続きに操作できる。

---

# 53. Advanced features are preserved, not promoted

```text
Pose
SubScene
Interaction
Mask edit
```

は捨てない。

しかし:

```text
Advanced / Refine
```

へ移す。

---

# 54. 最終原則

```text
最小手で漫画Draftが出る
```

ことが最優先。

次に:

```text
Seedで案を出せる
```

。

次に:

```text
良い案を固定できる
```

。

最後に:

```text
PoseやInteractionを精密化できる
```

。

順番を逆にしない。

---

# 55. 最終フロー

```text
Resolution
↓
Quality Template
↓
CAST
↓
Semantic Scene Regions
↓
Character Rough Regions
↓
Optional Rough Manga / Dummy Guide
↓
Visual Panel Control
↓
Seed Brainstorm
↓
Generate
↓
Select
↓
Optional Refinement
```

AstraはこのProduct Flowを基準に、
現在のRepository資産を再整理すること。
