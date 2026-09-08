# ComfyUI Portable Phase 3E — Impact Regional Backend Manga Reintegration & Progressive Authoring Foundation 指示書

## 0. 対象 / Baseline

対象環境:

```text
D:\\GitHub\\tegaki\\ComfyUIPortable
```

Review Target baseline:

```text
5409fceec73243ef648a2e1c5ac6f8a74a0522cf
```

Phase 3D.2 では、漫画体裁を一時的に外し、Regional Semanticsそのものを検証した結果、以下が成立しました。

```text
CORE SINGLE-REGION POSITION: INSUFFICIENT
IMPACT SINGLE-REGION POSITION: PARTIAL
CORE TWO-REGION BINDING: INSUFFICIENT
IMPACT TWO-REGION BINDING: PROMISING
PRIMARY REGIONAL BACKEND: IMPACT
MANGA REINTEGRATION: GO
```

特に、White Dog / Black Cat のPromptを変更せずRegion geometryだけを左右交換した時、生成対象の左右位置も反転したことは重要な成果です。

一方で、以下は未解決です。

```text
- Impact単一領域は5位置のうち完全安定ではない
- 小領域ではSubject Missingがある
- 完全非重複2領域では背景Seamが出ることがある
- Dog/Catの大きなOverlapではIdentity Merge / Chimeraが起きた
- Browser上のRegion drag / resize実操作はまだPENDING
- 現Impact Adapterは基本的にA/Bの2領域Oracle
- 漫画側のPAGE_COMPILE_PLAN / CAST / N-PanelへImpactをまだ本格統合していない
```

本Phaseでは、Impactをいきなり「完成Backend」と扱わず、**Primary Candidateとして漫画Authoring構造へ段階的に再統合**してください。

---

# 1. Phase名

```text
Phase 3E
Impact Regional Backend Manga Reintegration
& Progressive Authoring Foundation
```

内部を以下に分けます。

```text
3E-0  Phase 3D.2 Review Closure / Scope Correction
3E-A  Generic N-Region Impact Engine Foundation
3E-B  Recurrent Cast Across Panels Stress Test
3E-C  Panel / Scene / Character Hierarchy Integration
3E-D  Single-Panel Multi-Scene Same-Cast Hostile Test
3E-E  ComfyUI Progressive Authoring Workflow Layout
3E-F  Backend / Data Contract Decision Gate
```

---

# 2. Phase 3D.2の成果を過大解釈しない

Phase 3D.2報告書の:

```text
LAYOUT ASSIST: NOT NEEDED
```

は、**2領域の左右・上下・Geometry Swap実験において、Impact単体で十分な位置誘導が得られた**という限定的な判断として扱ってください。

これを:

```text
今後ControlNet位置補助は一切不要
```

という意味に拡張しないこと。

理由:

```text
Impact single-region directional score = 3.5 / 5
TRではSubject Missing
TLでは部分一致
```

が残っています。

したがってControlNetは:

```text
DEFERRED / OPTIONAL GEOMETRIC ASSIST
```

として維持します。

既存Panel Layout ControlNetも削除しないこと。

---

# 3. Browser InteractionはまだPENDING

`two_region_editor.js` には:

```text
Move
Resize
Create/Reposition
Enable/Disable
5-position presets
Geometry Swap
```

のevent pathがあります。

ただしPhase 3D.2報告では:

```text
BROWSER INTERACTION PENDING
```

です。

したがって:

```text
Interactive Editor Fully Verified
```

とはまだ記載しないでください。

可能なら本Phase中に実ブラウザ自動操作または実操作を行う。
不可能なら、最終報告でもPENDINGを正直に残す。

---

# 4. 今回の中心思想 — Character First, Scene Support, Panel Geometry Independent

漫画側へ再統合する時、以下の役割分担を採用します。

```text
GLOBAL
= 漫画 / 画風 / ページ全体

CAST / CHARACTER MASTER
= 誰か

PANEL / ROOT SCENE
= そのコマで何が起きるか / 背景

CHARACTER INSTANCE / PLACEMENT
= そのコマ・Scene内のどこに誰がいるか

PANEL LAYOUT
= 表面に見える漫画コマ枠

SUBSCENE
= 1つのPanel内に複数の独立した出来事が必要な時だけ使う高度機能
```

---

# 5. Simple Firstを維持

通常のPanelは:

```text
Panel Prompt
+ optional Characters
```

だけで完結できるようにします。

例:

### 背景だけ

```text
Panel Prompt:
garden, flowers, afternoon
```

### 1人物

```text
Panel Prompt:
garden, flowers

Alice:
watering flowers
```

### 2人物だが単純な1演技

```text
Panel Prompt:
Alice and Bob shaking hands in the garden

Alice
Bob
```

この段階ではSubScene不要です。

---

# 6. SubSceneを常設しない

本Phaseで、最終UIのScene/SubScene schemaを確定しないでください。

通常は内部的に:

```text
Panel = Root Scene 1個
```

とみなします。

SubSceneは後述のHostile Testで必要性と生成可能性を確認してから、正式Contract化するか判断します。

---

# 7. CAST_SPECはSSOTとして維持

既存:

```text
CAST_SPEC v1
```

を壊さない。

Character Master:

```text
Aliceとは誰か
Bobとは誰か
```

を保持。

各Panel / Scene側には:

```text
character_id
prompt_override
negative_prompt_override
area
```

等のAppearance / Binding情報を置く。

---

# 8. 同一Characterが複数Panelへ出演できることを本格検証する

本Phaseの重要課題です。

例:

```text
Panel 1: Alice + Bob
Panel 2: Alice
Panel 3: Bob
Panel 4: Alice + Bob
```

同じMaster Characterを複数のCharacter Instanceとして再利用できること。

---

# 9. Character MasterとCharacter Instanceを明示的に区別

内部debugで最低限:

```text
master_character_id
instance_id
panel_id
scene_id / root_scene
prompt_override
area
```

を追跡できるようにしてください。

例:

```text
master_character_id: char_alice
instance_id: p2_alice_1
panel_id: 2
```

Character Masterを複製して別Characterとして扱わないこと。

---

# 10. Phase 3E-A — Generic N-Region Impact Engine

現在の `TegakiTwoRegionImpactAdapter` はA/B専用Oracleです。

漫画へ戻すには:

```text
N Panels
N Character Instances
optional Local / Scene Regions
```

をRegionalSamplerへ渡せる一般化が必要です。

新規候補:

```text
impact_region_plan.py
manga_impact_regional_adapter.py
```

名称は実装に合わせて変更可。

---

# 11. 永続SchemaをImpact依存にしない

以下のようなImpact専用objectを:

```text
REGION_SPEC
CAST_SPEC
PAGE_COMPILE_PLAN
PANEL_LAYOUT_SPEC
```

へ保存しないでください。

Impact向けデータはcompile-time derivativeにします。

例:

```text
IMPACT_REGION_PLAN
```

は派生実行計画であり、ユーザー正本ではない。

---

# 12. IMPACT_REGION_PLANの最低情報

各region entry候補:

```text
region_index
scope_type
source_panel_id
source_scene_id
master_character_id
character_instance_id
prompt
negative_prompt
mask
priority
metadata
```

`scope_type` 候補:

```text
panel_scene
character_instance
local_region
experimental_subscene
```

---

# 13. Impact API実装方式はローカル実物を監査して決める

Impact Packの現在Runtimeで:

```text
RegionalSampler
REGIONAL_PROMPT
KSamplerAdvancedProvider
BASIC_PIPE
```

の実装を確認してください。

理想は:

```text
派生Region Plan
→ 必要なREGIONAL_PROMPT list
```

を自動生成することです。

ただしAPIが安全に内部生成できない場合は、
固定provider nodesをWorkflow内部に置いても構いません。

その場合:

```text
INTERNAL / LOCKED
```

としてユーザー操作対象から外してください。

「動的N対応」と称しながら実際は2領域固定、は不可。

---

# 14. N-regionの最初の対象

最初から6Panel + 多人数を同時にやらない。

順序:

```text
2 character instances
3 character instances
4 character instances
```

まで増やし、RegionalSampler listの挙動を確認。

その後、4Panel recurrent castへ。

---

# 15. Panel SceneとCharacter Regionの階層

初期案:

```text
Global base sampler

Panel / Root Scene regional prompt
  ↓ broad region

Character Instance regional prompt
  ↓ smaller region inside / clipped to panel
```

です。

ただしImpactでBroad Scene RegionとCharacter Regionを重ねた場合の処理順が重要です。

---

# 16. Region Order Oracle

最低限2方式を比較してください。

```text
A. Scene first → Character later
B. Character first → Scene later
```

同Seedで比較。

見るもの:

```text
Character identity
Scene background
Prompt overwrite
Seam
Bleed
```

結果に基づきCanonical orderを決定。

勝手に順番を固定しない。

---

# 17. Character-first Alternative

必要であれば、Character Instanceのpositive promptを:

```text
Panel Scene Prompt
+
Character Master Prompt
+
Character Override
```

へ事前結合し、Character Region単独でImpact samplerへ渡す方式も比較してください。

この方式は:

```text
Scene RegionとCharacter Regionの二重Overlap
```

を減らせる可能性があります。

---

# 18. Scene / Background-only Area

Character Region外のPanel remainderへ:

```text
Panel Scene Prompt
```

を与える必要があります。

Panel全体をScene Regionとして重ねる方式と、
Character maskを差し引いたremainder mask方式の両方を比較して構いません。

重要:

```text
背景だけのPanel
```

も正常生成できること。

---

# 19. Phase 3E-B — Recurrent Cast 4-Panel Stress Test

新しい主要実証です。

Visible Panels:

```text
4
```

Layout:

```text
4_grid
```

---

# 20. Recurrent Cast Fixture

CAST:

```text
Alice:
1girl, blonde twin tails, blue eyes, school uniform

Bob:
1boy, short black hair, school uniform
```

Panel 1:

```text
Alice + Bob
friendly handshake, facing each other
simple school garden
```

Panel 2:

```text
Alice only
watering flowers with a watering can
flower bed
```

Panel 3:

```text
Bob only
carrying a large potted plant
school garden path
```

Panel 4:

```text
Alice + Bob
arguing, both looking away from each other
school gate
```

---

# 21. このFixtureで確認すること

```text
Alice appears in Panel 1 / 2 / 4
Alice does not unexpectedly appear in Panel 3

Bob appears in Panel 1 / 3 / 4
Bob does not unexpectedly appear in Panel 2

Panel 1 relation = friendly / handshake
Panel 4 relation = conflict / looking away

Panel 2 action = watering flowers
Panel 3 action = carrying plant
```

同じCharacter Masterが、Panelごとに別演技で再利用されることを確認。

---

# 22. Recurrent Cast評価

最低限:

```text
Identity consistency
Panel attendance correctness
Action correctness
Cross-panel action leakage
Duplicate character
Missing character
Unexpected character
Attribute bleed
```

をPanel単位で記録。

---

# 23. Panel Cropped Contact Sheet

4Panel実画像を:

```text
Full Page
Panel1 crop
Panel2 crop
Panel3 crop
Panel4 crop
```

としてContact Sheet化。

Panel Polygon / Layout Specからcrop領域を得ること。

大量画像をGitへcommitしない。

---

# 24. Workflow 21

新規:

```text
21_MANGA_IMPACT_RECURRENT_CAST_POC.json
```

目的:

```text
Impact Regional Backend
+
CAST_SPEC
+
4 Visible Panels
+
Repeated Character Instances
+
Panel-specific Acting
```

の統合実証。

---

# 25. Workflow 21ではPanel Layout ControlNetを最初OFFでもよい

まずRegional semanticsだけで:

```text
4-grid内のCharacter / Scene binding
```

を確認。

その後Panel Layout ControlNet ONを比較。

ControlNetを最初から混ぜて因果を曖昧にしない。

---

# 26. Panel Layout ControlNetの役割

Panel Layout ControlNetは:

```text
表面に見える漫画枠
```

を担当。

Character Positionを主制御するものとして扱わない。

ただしImpact aloneでPanel crossingが増える場合は補助効果を測ってよい。

---

# 27. Phase 3E-C — Panel / Scene / Character Hierarchy

ここでは最終専用GUIを作りません。

データ上・Workflow上の責任分担を確認します。

標準:

```text
Panel
└ Root Scene
   ├ Scene Prompt
   ├ Alice Instance
   └ Bob Instance
```

通常のPanelではこれだけ。

---

# 28. Simple Panelの3種類をテスト

最低限:

```text
A. Background-only Panel
B. Single Character Panel
C. Multi Character / Single Acting Panel
```

これらがSubSceneを意識せず作れること。

---

# 29. Panel CountとScene Countを同一視しない

内部設計上:

```text
Visible Panel Count
!=
Semantic Scene Count
```

になり得ます。

ただし本Phaseの通常Workflowでは:

```text
1 Panel = 1 implicit Root Scene
```

をDefaultとします。

---

# 30. SubSceneはまだ正式Schemaにしない

現在の `REGION_SPEC v1` / `PAGE_COMPILE_PLAN v1` を大規模破壊しない。

Phase 3E-DのHostile Testでは、まず派生・実験的な:

```text
SEMANTIC_SCENE_PLAN
```

または同等の一時構造を使用して構いません。

成功してから永続schema化を検討。

---

# 31. Phase 3E-D — Single Visible Panel / Two Internal Scenes Hostile Test

このPhaseの最も意地悪なテストです。

Visible Panels:

```text
1
```

Internal semantic scenes:

```text
2
```

---

# 32. Hostile Test内容

左側 Scene A:

```text
Alice + Bob
arguing intensely
both looking away from each other
```

右側 Scene B:

```text
Alice + Bob
friendly handshake
facing each other
```

同一のAlice Master / Bob Masterを、左右Sceneへそれぞれ別Instanceとして再利用。

---

# 33. Hostile TestのInstance構造

例:

```text
Scene A / Left
  alice_left
  bob_left

Scene B / Right
  alice_right
  bob_right
```

4つのInstanceが:

```text
master Alice x2
master Bob x2
```

を参照する。

Master Characterを4人に複製しない。

---

# 34. Hostile Testで位置語に依存しない

Promptへ:

```text
left
right
```

を書かない。

左右はSemantic Scene / Character geometryで指定。

---

# 35. Hostile TestのRegion構造

候補:

```text
Scene A = left half
Scene B = right half

Scene A内:
Alice / Bob regions overlap moderately

Scene B内:
Alice / Bob regions overlap moderately
```

Scene A/B自体の境界は:

```text
0% overlap
small 5-10% blend overlap
```

を比較して構いません。

---

# 36. Dog/Cat overlapの教訓を反映

Phase 3D.2では、Dog/Catを35%重ねるとIdentity Merge / Chimeraが起きました。

したがって:

```text
Overlap = always good
```

としない。

人物interactionでは有効でも、異種subjectや逆関係Sceneでは意味混合を起こし得る。

Hostile TestではOverlap量を意図的に管理。

---

# 37. Hostile Test Acceptance

最低限:

```text
Left side contains Alice + Bob
Right side contains Alice + Bob

Left relation resembles conflict / looking away
Right relation resembles friendly handshake

Alice identity remains recognizably same across both scenes
Bob identity remains recognizably same across both scenes

No catastrophic 4-person fusion
No one-side subject disappearance
```

完全一致は最初から要求しない。

---

# 38. Hostile Test判定

```text
SAME-CAST MULTI-SCENE:
PROMISING / PARTIAL / INSUFFICIENT
```

### PROMISING

両側に同じ2人が別関係で概ね成立。

### PARTIAL

人物は出るが関係混線、Identity不安定、片側漏れ等。

### INSUFFICIENT

4人のInstance分離が成立しない、片Scene消失、重大融合。

---

# 39. Hostile Testが失敗してもPhase全体を失敗扱いしない

これは高難度研究です。

Recurrent Cast 4Panelが成功し、Hostile TestがPARTIALでも:

```text
Simple Manga Authoring = GO
Advanced SubScene = HOLD
```

という分岐ができます。

---

# 40. Workflow 22

新規:

```text
22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json
```

区分:

```text
EXPERIMENTAL / ADVANCED SEMANTIC SCENE ORACLE
```

通常漫画Workflowと混同しない。

---

# 41. SubScene UI正式実装Gate

Workflow22が:

```text
PROMISING
```

なら次Phaseで:

```text
+ Split Scene
```

UIを正式化候補へ。

PARTIAL / INSUFFICIENTなら:

```text
SubScene UIはまだ作らない
```

こと。

---

# 42. Phase 3E-E — ユーザーから見たComfyUI作業順

専用GUIスキン前の暫定形として、Workflow21を左→右、または上→下で明確な作業導線にしてください。

推奨:

```text
01 GLOBAL
→
02 CAST
→
03 PANEL CONTENT
→
04 PANEL LAYOUT
→
05 CHARACTER STAGING
→
06 GENERATE
```

---

# 43. Globalは軽く扱う

Globalは:

```text
Manga preset
style
monochrome / color
```

など。

Defaultで済む場合は触らなくてよい位置づけ。

---

# 44. CASTをPanelより先に置く

ユーザーがまず:

```text
Alice
Bob
Carol
```

を決められる流れ。

Character Masterは作品を跨いで繰り返す重要要素です。

---

# 45. Panel Contentは「Prompt Nodeの羅列」にしすぎない

4Panelならデータ上4つのPanel内容を持つ。

ただしComfyUI上で巨大Nodeを4つ並べる必要はありません。

可能なら:

```text
selected panel
```

方式のEditorを将来候補とする。

本Phaseでは既存Region Editor / Workflow構造を大改造しなくてよい。

---

# 46. Character Staging

Panelを選択した時、そのPanelへ出演するCharacter InstanceのRegionだけを編集できるUIが最終候補です。

Phase 3Eでは完全UI実装は不要。

ただしデータContractとdebug outputはこの考えに沿わせる。

---

# 47. Internal NodesをUser Flowから離す

以下はユーザー作業列の下側または右側へまとめる。

```text
Compiler
Impact Adapter
Provider Nodes
Mask Builder
RegionalSampler
ControlNet Apply
VAE
Debug
```

Group名例:

```text
INTERNAL ENGINE — DO NOT TOUCH
```

---

# 48. Internal Nodesは可能ならLock

ComfyUI WorkflowでNode lock / group / bypass保護が可能な範囲で:

```text
移動・誤編集しにくい
```

状態にする。

ただし独自GUI frameworkはまだ作らない。

---

# 49. Previewを整理

ユーザー作業列に必要なPreviewのみ:

```text
Semantic Region / Staging Preview
Panel Layout Preview
Final Image
```

Debug用PreviewはInternal groupへ。

謎のPreviewが多数並ぶ状態を避ける。

---

# 50. Workflow21 Zero-Touch

Default状態で:

```text
Load
No touch
Queue
Image
```

PASS。

同時に、ユーザーが実際に触るNodeがどれか視覚的に分かること。

---

# 51. User Manual AcceptanceはPhase末まで要求しない

実装途中で細かい手動確認を求めなくてよい。

Phase終了時に、ユーザー向けに最大3項目の確認手順を出す。

例:

```text
1. AliceをPanel2内で右へdrag
2. Queue
3. Aliceの位置が右へ変わるか確認
```

---

# 52. Browser InteractionをPhase末で再度判定

```text
SEMANTIC REGION BROWSER INTERACTION:
PASS / PENDING
```

を明記。

コードが存在するだけでPASSにしない。

---

# 53. Preset / Libraryは今回実装しない

長期構想として:

```text
Character Preset
Scene Preset
Panel/Layout Preset
Page Preset
Project Preset
Export / Import / Duplicate / Delete
```

があります。

ただし今はデータContract自体を検証中です。

Phase 3Eでは実装しない。

---

# 54. Presetを見越したContractだけ守る

将来Preset化しやすいよう:

```text
Character Master
Panel Content
Scene Content
Layout
Instance Placement
```

を分離しておく。

Backend固有objectを上位データへ混ぜない。

---

# 55. Existing Regression

最低限:

```text
12 Impact Oracle
16 Variable N Manga
17 Cast Master Manga
18 Single Region Compare
19 Two Region Binding
20 Layout Assist Oracle
```

を壊さない。

---

# 56. 新規Test候補

最低限:

```text
scripts/test_impact_n_region_plan.py
scripts/test_impact_region_order.py
scripts/test_recurrent_cast_instances.py
scripts/test_manga_impact_recurrent_cast_runtime.py
scripts/test_single_panel_multiscene_contract.py
scripts/test_single_panel_multiscene_runtime.py
scripts/generate_recurrent_cast_contact_sheet.py
```

---

# 57. Impact N-region Plan Test

確認:

```text
2 / 3 / 4 region entries
stable ordering
unique instance IDs
source panel traceability
mask shape
canvas consistency
```

---

# 58. Recurrent Cast Contract Test

確認:

```text
Alice master is one object
Alice instances exist in 1/2/4
Bob instances exist in 1/3/4
Panel-specific override preserved
Area preserved
No accidental master mutation
```

---

# 59. Hostile Multi-Scene Contract Test

確認:

```text
1 visible panel
2 semantic scenes
Alice master referenced twice
Bob master referenced twice
4 unique instance IDs
scene geometry independent
character geometry scene-local or correctly projected
```

---

# 60. Character Coordinate Model

通常Panelでは既存通り:

```text
Character area = Panel-local normalized rect
```

を維持。

Experimental SubSceneでは:

```text
Character area = Scene-local normalized rect
```

を候補とし、

```text
Scene bbox projection
→ Scene mask clip
→ Parent Panel clip
```

でページ座標へ投影。

これは実験構造であり、まだ永続schemaとして固定しない。

---

# 61. Scene RegionとPanel Polygon

通常Root Scene:

```text
Scene Region = Parent Panel Polygon
```

でよい。

Advanced SubSceneだけ:

```text
SubScene Region ⊂ Parent Panel
```

となる。

---

# 62. Panel PromptとCharacter Promptの責任分担

Panel / Root Scene:

```text
background
location
overall action / relation
lighting / time
```

Character Instance:

```text
identity
pose / expression
panel-specific acting
```

同じ情報を両方へ過剰重複しない。

---

# 63. Relationship Promptの扱い

複数人物の:

```text
handshake
argument
conversation
```

はCharacter単独Promptだけでなく、Root Scene / SubSceneのrelationship promptとして持つ方が自然です。

本Phaseでは専用Relationship schemaまでは作らなくてよい。

Scene Prompt内で検証。

---

# 64. LoRAは今回拡張しない

Global LoRAは既存通り。

Character LoRA Planは保持。

Impact RegionalSamplerへCharacter LoRAを空間適用する機能は今回の主課題ではありません。

RLLは別Phase。

---

# 65. Performance計測

CoreよりImpactは計算量が増えます。

Workflow21で最低限:

```text
VRAM peak
runtime
region count
```

を記録。

2 / 4 / recurrent-cast regionsで比較。

---

# 66. N-regionが計算的に重すぎる場合

すぐ最適化に走らず、まずボトルネックを報告。

候補:

```text
region count cap
sequential panel generation
hybrid Core + Impact
```

は次判断。

---

# 67. Phase 3E Report

新規:

```text
PHASE3E_IMPACT_MANGA_REINTEGRATION_AND_PROGRESSIVE_AUTHORING_REPORT.md
```

最低限:

```text
1. Phase3D.2 Review Closure
2. ControlNet Scope Correction
3. Browser Interaction Status
4. Impact N-Region Architecture
5. IMPACT_REGION_PLAN
6. Region Ordering Oracle
7. Scene / Character Composition Strategy
8. Recurrent Cast Contract
9. Recurrent Cast 4-Panel Runtime
10. Panel Attendance Correctness
11. Panel-specific Acting
12. Identity Consistency
13. Panel ControlNet OFF/ON
14. Simple Panel Modes
15. Panel / Root Scene Model
16. Experimental SubScene Model
17. Same-Cast Multi-Scene Hostile Test
18. Overlap / Seam Analysis
19. ComfyUI User Flow Layout
20. Internal Node Lock / Grouping
21. Preview Cleanup
22. Performance
23. Regression
24. Known Issues
25. Backend Decision
26. Scene Contract Decision
27. Next Phase
28. Gemini独自判断
```

---

# 68. Phase終了Gate

報告書末尾:

```text
PHASE3D.2 REVIEW CLOSURE:
PASS / HOLD

IMPACT N-REGION ENGINE:
PASS / HOLD

REGION ORDERING:
<canonical result>

RECURRENT CAST 4-PANEL:
PASS / PARTIAL / HOLD

PANEL ACTION SEPARATION:
PASS / PARTIAL / HOLD

SIMPLE PANEL AUTHORING:
READY / HOLD

SAME-CAST MULTI-SCENE:
PROMISING / PARTIAL / INSUFFICIENT / NOT RUN

SUBSCENE CONTRACT:
FORMALIZE NEXT / KEEP EXPERIMENTAL / REJECT FOR NOW

SEMANTIC REGION BROWSER INTERACTION:
PASS / PENDING

PANEL LAYOUT CONTROLNET:
KEEP / OPTIONAL / REQUIRED

PRIMARY REGIONAL BACKEND:
IMPACT / HYBRID / UNDECIDED

MANGA AUTHORING REINTEGRATION:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 69. 次Phase分岐

## A. Recurrent Cast PASS + Hostile Test PROMISING

次:

```text
Phase 3F
Progressive Panel / Scene Authoring UI
```

ここで:

```text
Simple Panel
+ Split Scene
Character Staging
selected Panel / Scene editing
```

を本格UI化。

---

## B. Recurrent Cast PASS + Hostile Test PARTIAL/INSUFFICIENT

次:

```text
Simple Manga Authoring UI
```

は進めてよい。

ただし:

```text
SubScene = Experimental / Hidden
```

のまま。

---

## C. Recurrent CastがPARTIAL

Impact N-regionのPrompt hierarchy / mask orderを再検討。

専用GUIはまだ拡張しすぎない。

---

## D. N-region Impact自体が重すぎる / 不安定

次候補:

```text
Hybrid Core + Impact
Panel-sequential generation
Impact only for Character regions
```

を比較。

---

# 70. GITHUB.TXT二段Commit

まず:

```text
Commit A
Phase 3E Impact Manga Reintegration & Progressive Authoring Foundation
```

として:

```text
Impact N-region engine
Recurrent cast Workflow21
Multi-scene Workflow22
Tests
Report
Workflow layout cleanup
```

をcommit。

Commit A SHA取得後、Navigation Commit Bで:

```text
Review Target Commit SHA: <A>
```

へ更新。

Latest:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

---

# 71. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3E_IMPACT_MANGA_REINTEGRATION_AND_PROGRESSIVE_AUTHORING_REPORT Raw:

Impact N-Region Engine Raw:
Impact Region Plan Raw:
Recurrent Cast Contract Raw:
Experimental Multi-Scene Contract Raw:

Workflow 21 Raw:
Workflow 22 Raw:

Impact N-Region Test Raw:
Region Order Test Raw:
Recurrent Cast Test Raw:
Recurrent Cast Runtime Raw:
Multi-Scene Contract Test Raw:
Multi-Scene Runtime Raw:

PHASE3D.2 REVIEW CLOSURE:
IMPACT N-REGION ENGINE:
REGION ORDERING:
RECURRENT CAST 4-PANEL:
PANEL ACTION SEPARATION:
SIMPLE PANEL AUTHORING:
SAME-CAST MULTI-SCENE:
SUBSCENE CONTRACT:
SEMANTIC REGION BROWSER INTERACTION:
PANEL LAYOUT CONTROLNET:
PRIMARY REGIONAL BACKEND:
MANGA AUTHORING REINTEGRATION:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3D.2で得られた重要な成果は:

```text
Promptを変えず、Region Geometryだけ変えると
Dog / CatやMan / Womanの位置が追従した
```

ことです。

次はその能力を、漫画の実際の制作構造へ戻します。

ただし戻し方は:

```text
漫画コマを増やす
```

だけではありません。

まず:

```text
Character Masterを再利用し
同じAlice / Bobが複数Panelへ出演し
Panelごとに違う演技をし
Character Regionで位置を持つ
```

ことを証明してください。

その後、難しいPanelだけ:

```text
1 Visible Panel
→ 2 Internal Semantic Scenes
```

へ展開できる可能性をHostile Testで確認します。

最終UI思想は:

```text
Simple by default
Complex only when requested
```

です。

普通の4コマは:

```text
Global
→ Cast
→ 4 Panel Contents
→ Panel Layout
→ Character Placement
→ Generate
```

だけで作れること。

そして必要な1コマだけ:

```text
+ Split Scene
```

で高度化できる構造を目指します。

Preset / Library / Export / Import / Dedicated GUI Skinは、このContractが安定してからの後段です。
