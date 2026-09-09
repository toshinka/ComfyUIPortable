# GPT-6 Astra 向け
# Tegaki / ComfyUI Manga Authoring
# 戦略再整理・資産棚卸し・UI/GUI再定義 指示書

## 0. この作業の役割

あなた（GPT-6 Astra）には、現在かなり長期間研究・実装されてきた
`Tegaki / ComfyUIPortable Manga Authoring` プロジェクトを一度俯瞰し直し、

```text
何が本当に欲しい製品なのか
何が既に使える資産なのか
何が研究用の遺産なのか
何を今後のMainlineに残すべきか
何を既存ComfyUI実装へ委譲すべきか
```

を整理して、新しい上位計画を作ってもらいます。

この作業は **実装Phaseではありません**。

コード変更を大量に始めず、まず:

```text
棚卸し
↓
製品像の再定義
↓
既存資産の再評価
↓
Architecture境界の整理
↓
Roadmap再構築
```

を行ってください。

---

# 1. 最重要の作業目的

このプロジェクトの最終目標は、
「高機能なComfyUI Custom Node群を作ること」ではありません。

ユーザーが欲しているものは、かなり平たく表現すると:

```text
Stable Diffusion WebUI向けに以前作った
Manga Region Prompter (MRP)
の操作感・即応性を、

より構造化し、
Character / Scene / Pose / SubSceneを扱えるように
ブラッシュアップした漫画制作Authoring Tool
```

です。

ただしMRPそのものをComfyUIへ移植するのではありません。

MRPの:

```text
キャンバス上で雑に領域を置ける
領域とPromptが直感的に対応する
色・番号・カードで何がどこに効くか分かる
細かいNode Graphを意識しなくてよい
```

という **Authoring UXの良さ** を継承し、

現在までに研究した:

```text
CAST
Character Instance
Panel
Scene
SubScene
Interaction
Staging
Pose
Backend Adapter
```

を載せ直すことが目的です。

---

# 2. ユーザーが最終的に欲しい基本操作

以下をProductのPrimary Journeyとして理解してください。

```text
1. Canvas resolution / aspect ratioを決める

2. Canvas上へPanel rectangleを雑にドラッグ配置

3. Panel内またはPanelに対応して
   Character A rectangleを雑に配置

4. Character B rectangleも雑に配置

5. Panel PromptはPanel専用UIで入力

6. Character A / B Promptは各Character専用UIで入力

7. すぐDraft Generate

8. Seedを変えて複数案をBrainstorm

9. 良い構図・Pose・表情を選ぶ

10. 必要になったCharacterだけ
    Pose / ControlNet / Mask / Interactionで精密化

11. 複雑なPanelだけSubSceneを開く

12. Final Generate
```

中心思想:

```text
Rapid Staging
→ Brainstorm
→ Select
→ Refine
```

---

# 3. 初期UIに出してよい概念

初期操作でユーザーに理解させる概念は、
できるだけ以下へ絞る。

```text
Canvas
Panel
Character
Prompt
Generate
```

原則:

```text
Simple First
Advanced Later
Hidden Until Needed
```

---

# 4. 初期UIに出し過ぎない概念

以下は技術的に存在していても、
最初から全面露出させない。

```text
Pose Editor
SubScene
Interaction
Mask Editor
Regional Backend
ControlNet schedule
Sampler detail
Advanced Region options
```

必要になった時だけ:

```text
Advanced Pose
Advanced Scene
Interaction
Refine Mask
```

などから段階的に開く。

---

# 5. Character Rectangleの意味

Character rectangleは単なる一時的なマスクではありません。

定義:

```text
Character Rectangle
=
Character Instance の最初の粗いSpatial Representation
```

矩形を後から精密Poseへ変更しても:

```text
Character Master
Character Instance ID
Prompt
Panel / SubScene association
Acting
```

は保持される。

理想:

```text
Rough Character Box
↓
Draft generation
↓
良いPoseを発見
↓
Pose extraction / Pose Asset
↓
同じCharacter Instanceへattach
↓
Pose-aware Control guide
```

---

# 6. Poseに関する重要なProduct判断

最初から3D Pose人形を配置させない。

最初は:

```text
Aliceはだいたいここ
Bobはだいたいここ
```

という矩形だけでよい。

生成AIのSeed variationをBrainstormに利用する。

良いPoseが出た後:

```text
generated image
↓
DWPose / OpenPose extraction
↓
optional manual pose editor
↓
Character Instance Pose Asset
```

へ昇格できるのが望ましい。

本格Pose Editorの再発明は避ける。

---

# 7. 最初に必ず確認するGitHubナビゲーション

必ず最初に:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

を読むこと。

このファイルに記載された:

```text
Review Target Commit SHA
```

を固定し、そのcommitを基準に現状を読む。

moving `main` を現状の正本として盲目的に読まない。

---

# 8. 現在確認済みの基準

本指示書作成時点では:

```text
Phase 3L complete
Review Target:
5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8
```

となっている。

ただしAstraが作業開始する時点で、
必ずGITHUB.TXTを再確認して最新値を使うこと。

---

# 9. 長期方針の既存文書

共有ファイル側に存在する場合、以下を読む。

```text
Tegaki_ComfyUI_Manga_Authoring_Intermediate_Plan_v2_Rapid_Staging_and_PriorArt.md
Tegaki_ComfyUI_Handoff_2026-09-06.md
```

これらは現在の意図を整理した文書だが、
**Astraは無条件に踏襲する必要はない**。

現資産とMRPを見た上で:

```text
KEEP
CHANGE
MERGE
DEFER
DROP
```

を判断し、新しいMaster Planで再整理する。

---

# 10. MRPを必ず見る

ユーザーが欲しいUIを理解するには、
旧Stable Diffusion WebUI / reForge用:

```text
EasyReforge Manga Prompter
Manga Region Prompter (MRP)
```

を見ることが重要。

最初の入口:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/EasyReforgeExtension/GitHubURL_ERE.txt
```

---

# 11. MRPで最優先で読む資料

## Tier MRP-S

### Navigation

```text
EasyReforgeExtension/GitHubURL_ERE.txt
```

### Architecture / knowledge

```text
EasyReforgeExtension/docs/ARCHITECTURE_AND_KNOWLEDGE_BASE.md
```

### Frontend Canvas

```text
EasyReforgeExtension/javascript/manga_canvas.js
```

### CSS

```text
EasyReforgeExtension/style.css
```

### Latest Report

```text
EasyReforgeExtension/計画書/MRP_v3.7.7_改修完了報告書.md
```

### Main UI / Pipeline source

```text
EasyReforgeExtension/scripts/manga_prompter.py
```

---

# 12. MRPから見るべきUX要素

MRPには少なくとも以下の思想がある。

```text
Canvas上の直接操作
Select / Slice / Draw Rectangle
色分けされたPanel
Stable physical region
Logical panel number assignment
Panel number swap
Undo / Redo
Reading order assignment
Exclusive / Overlap
Color / Lineart display
Panel summary / prompt relation
```

これらを「そのまま移植する機能一覧」としてではなく、

```text
なぜユーザーが直感的に使えるのか
```

という観点で分析する。

---

# 13. MRPから継承したいもの

特に評価してほしい:

```text
A. Canvas-first authoring
B. Rough drag operation
C. GeometryとLogical assignmentの分離
D. Color-coded visual correspondence
E. PromptとRegionの直接対応
F. Stable ID
G. Undo / Redo
H. ユーザーがBackendを意識しない
```

---

# 14. MRPからそのまま継承しないもの

旧MRPの以下はLegacy Backend固有。

```text
BREAK slot parser
Attention Hook implementation
Forge-specific pipeline
Extra Networks handling
旧Region Prompt mapping
```

これらを新ComfyUI Mainlineへ機械的に移植しない。

新Projectでは:

```text
Structured Authoring Data
Semantic Compiler
Backend Adapter
```

を優先する。

---

# 15. 「MRPをブラッシュアップ」の意味

Astraは最終UIを次のように捉えてよい。

```text
MRPのCanvas操作
+
MRPのRegion ↔ Promptの分かりやすさ
+
現在のCAST / Character Instance
+
Panel / SubScene
+
Progressive Pose Refinement
+
ComfyUI backend reuse
```

つまり:

```text
MRP 2.0
```

ではあるが、

```text
旧MRP Backend 2.0
```

ではない。

---

# 16. Repository全体を最初に棚卸しする

Repository top-levelを一覧し、
最低限以下を分類する。

```text
ComfyUIPortable
EasyReforgeExtension
RegionalLoRALab
tegaki_work
docs
関連ツール / 開発資料
```

分類軸:

```text
CURRENT MAINLINE
UX REFERENCE
RESEARCH REFERENCE
LEGACY
FUTURE
DO NOT TOUCH
```

---

# 17. 重要なRepository境界

## CURRENT MAINLINE

```text
ComfyUIPortable/
```

現在の漫画制作ComfyUI環境。

---

## UX REFERENCE / LEGACY PRODUCT

```text
EasyReforgeExtension/
```

MRP。

UI/UXと失敗・成功知見を参照。

Backendをそのまま移植する前提ではない。

---

## RESEARCH REFERENCE

```text
RegionalLoRALab/
```

Regional LoRA研究。

現在のRapid Staging UI Coreではない。

将来:

```text
Character-specific LoRA locality
Spatial LoRA
```

が必要になった時に参照。

入口:

```text
RegionalLoRALab/GPT_GITHUB_LINKS.txt
RegionalLoRALab/CURRENT_STATUS.md
RegionalLoRALab/MASTER_PLAN.md
```

---

## DO NOT TOUCH

```text
tegaki_work/
```

既存の別開発領域として、
本計画整理だけの都合で変更しない。

---

# 18. Astraは全Workflowを最初から逐語読解しない

Astraは細部まで見る能力があるが、
このRepositoryには大量の研究Workflowがある。

最初に全55本を同じ深さで読むと、
過去の実験に引きずられてProduct像を見失う可能性がある。

以下の順で読む。

```text
Product intent
↓
Current stable spine
↓
Latest complex capabilities
↓
Backend decisions
↓
Historical workflow only when a question remains
```

---

# 19. Workflow Inspection Ladder

## Tier S — 必須

### 03

```text
03_MANGA_REGIONAL_PROMPT.json
```

初期Regional Promptの基本構造。

目的:

```text
どこから始まったか
```

だけ確認。

---

### 07

```text
07_MANGA_REGION_EDITOR_UI_TEST.json
```

ComfyUI側初期Region Editor UI。

MRPとの比較用。

---

### 09

```text
09_MANGA_REGIONAL_GENERATION_POC.json
```

Authoring → actual regional generationの初期接続。

---

### 54〜59

Phase 3J.1 stable spatial foundation。

特に:

```text
54 Alice Left
55 Alice Right
56 Bob Left
57 Bob Right
58 Two Character LR
59 Two Character Swap
```

これらは:

```text
Prompt truth
standalone character semantics
remainder mask
basic Character rectangle staging
```

の安定基盤として読む。

---

### 66

```text
66_VERIFY_POSE_GUIDE_ONLY_INWARD.json
```

Pose guide-only causality。

「矩形からPose refinementへ進む」後段の参考。

---

### 67

```text
67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json
```

Interaction / stable instance / pair resolutionの現在地。

初期UIには出さないがAdvanced Layerの能力として確認。

---

### 68

```text
68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json
```

非常に重要。

```text
1 visible Panel
2 internal SubScenes
same CAST multiple instances
```

がMainlineでどう表現されているかを見る。

---

### 70

```text
70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json
```

最重要の「漫画ページとしての現在地」。

```text
4 visible panels
5 internal scenes
simple + complex mixed
```

を確認。

---

### 71

```text
71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json
```

Backendを薄くする方針の根拠。

---

# 20. Workflow Tier A — 疑問が出たら読む

## 21〜32

Regional execution / spatial locality研究。

読む条件:

```text
Impact RegionalSamplerの設計理由を再確認したい
Character localityの歴史が必要
```

---

## 35〜43

ControlNet / conditioning propagation研究。

読む条件:

```text
なぜ独自ControlNet propagationを減らすのか
なぜAdvanced-ControlNet採用なのか
```

---

## 44〜47

Fast / causal / per-region control研究。

---

## 48〜53

Background responsibility / semantic presence / Per-Region Hint。

---

## 60〜65

Pose / Interaction / Camera Distance foundation。

---

# 21. Workflowを読む時の分類

各Workflowについて以下だけ記録する。

```text
Workflow ID
Original Hypothesis
What It Proved
What It Failed To Prove
Current Relevance
Product Reuse
Research Only
Superseded By
```

単純に:

```text
PASSだから残す
```

とはしない。

---

# 22. Current Mainline Source — Tier S

Astraは現在のAuthoring architectureを理解するため、
以下を優先して読む。

```text
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/scene_spec.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/scene_compiler.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/panel_content_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/character_staging_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/impact_region_plan.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/layout_guide_generator.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/interaction_resolver.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/subscene_contract.py
```

Frontend:

```text
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/panel_content_editor.js
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/character_staging_editor.js
```

必要に応じて:

```text
region_editor
panel_layout
layout_region_bridge
manga_impact_regional_adapter
```

も確認。

---

# 23. Phase 3Lの必読資料

GITHUB.TXTからPinned SHAを使って読む。

最低限:

```text
PHASE3L_INTERACTION_SUBSCENE_AND_PRIORART_REPORT.md
PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md
PHASE3L_BACKEND_ADOPTION_DECISIONS.md
PHASE3L_CANONICAL_VERIFICATION_MANIFEST.json
PHASE3L_PRESENCE_EVALUATION.json
```

---

# 24. Phase 3Lで既に示されたBackend方針

Astraはこれを「確定不可侵」とはせず、
Evidenceを確認して再評価してよい。

現時点の決定は:

```text
Regional Prompt:
ADAPT
Thin semantic compiler over Inspire / Impact style backend

ControlNet:
ADOPT
Advanced-ControlNet

Mask Editor:
DEFER custom
Use existing Impact / Clipspace tooling

Pose Editor:
DEFER custom
Auto mannequin + external OpenPose asset
```

---

# 25. Astraに求める棚卸し成果物 1
# Asset / Workflow Ledger

新規文書:

```text
ComfyUIPortable/docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
```

最低限のTable:

| Asset | Path | Category | Current Role | Proven Truth | Product Reuse | Keep/Refactor/Archive | Read Priority |
|---|---|---|---|---|---|---|---|

Category例:

```text
UX_REFERENCE
SEMANTIC_CORE
EXECUTION_BACKEND
WORKFLOW_ORACLE
TEST_INFRA
RESEARCH_ONLY
LEGACY
FUTURE
```

---

# 26. 棚卸し成果物 2
# Product / UX Blueprint

新規文書:

```text
ComfyUIPortable/docs/plans/ASTRA_RAPID_MANGA_AUTHORING_UX_BLUEPRINT.md
```

必ず以下を描く。

```text
Primary user journey
Canvas layout
Panel manipulation
Character manipulation
Prompt panels
Draft generation
Seed brainstorming
Candidate selection
Pose refinement
SubScene progressive disclosure
Interaction progressive disclosure
```

WireframeはASCIIでもよい。

---

# 27. UX Blueprintで必ず答える問い

1.

```text
MRPの何を残すか
```

2.

```text
MRPの何を捨てるか
```

3.

```text
ComfyUI上で当面どう表現するか
```

4.

```text
Dedicated GUIへ移る時も維持されるcontractは何か
```

5.

```text
ユーザーは最初の30秒で何を操作するか
```

6.

```text
Advanced Poseをいつ見せるか
```

7.

```text
SubSceneをいつ見せるか
```

8.

```text
Candidate / Seed brainstormをどこへ置くか
```

---

# 28. 棚卸し成果物 3
# New Master Plan

最重要成果物:

```text
ComfyUIPortable/docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
```

これをAstra整理後の新しいStrategic SSOT候補とする。

---

# 29. Master Planの構造

最低限:

```text
1. Product Definition
2. User Mental Model
3. MRP Lessons
4. Existing Asset Inventory Summary
5. Architecture Boundary
6. MANGA_AUTHORING_DATA direction
7. Rapid Staging
8. Brainstorm / Candidate Flow
9. Progressive Refinement
10. Pose Asset Flow
11. Panel / Character / SubScene Model
12. Backend Reuse Strategy
13. Workflow Reuse Strategy
14. UI Progressive Disclosure
15. Research vs Production Separation
16. Deprecated / Archived Concepts
17. Roadmap
18. Acceptance Gates
19. Risks
20. Explicit Non-Goals
```

---

# 30. Astraは既存計画との差分を書く

新Master Planには:

```text
KEEP FROM CURRENT PLAN
CHANGE
NEW
DEFER
DROP
```

のSectionを作る。

現在のv2中間計画を黙って上書きしない。

---

# 31. Product vs Technologyを分離する

Astraの新計画では:

```text
User Goal
Product Concept
Authoring Contract
Execution Backend
```

を混同しない。

例:

```text
Character Rectangle
```

はProduct概念。

```text
Impact mask
```

はBackend実装。

この二つを同じレイヤーへ置かない。

---

# 32. 必ず「最小実用版」を定義する

最初の実用版は高度なInteractionを必要としない。

例:

```text
Canvas
Panel rectangles
Character rectangles
Panel prompt
Character prompt
Draft generate
Seed change
```

これだけで:

```text
「漫画のラフ案を素早く出せる」
```

ことを最初のProduct Gateとして定義してよい。

---

# 33. Advanced機能はCapabilityとして保持

現在既に作った:

```text
Pose
Interaction
SubScene
Camera Distance
```

を捨てる必要はない。

ただし:

```text
Core Entry Flow
```

から分離する。

---

# 34. 「何を消せるか」も計画対象

Astraは積極的に:

```text
duplicate node
obsolete wrapper
old experimental adapter
superseded workflow
backend-specific glue
```

を特定する。

ただしこの計画作業中に削除はしない。

`Archive / Deprecate Candidate` として記録。

---

# 35. Prior-Art再発明回避

以下は原則自作しない。

```text
Sampler
Scheduler
Generic Mask Editor
Generic Pose Editor
Generic ControlNet framework
Generic Regional Prompt engine
```

Tegakiが作るのは:

```text
Manga Authoring Semantics
```

である。

---

# 36. RegionalLoRALabの扱い

RegionalLoRALabは捨てない。

ただし現在のRapid Staging Product計画へ
無理に混ぜない。

Astraは:

```text
Future Capability
```

として、

```text
Character-specific LoRA spatial locality
```

が必要になるPhaseを定義する程度でよい。

---

# 37. Reportを盲信しない

Gemini報告書は重要なEvidenceだが、
Astraは必要に応じて:

```text
code
workflow JSON
test
manifest
```

を照合する。

特に:

```text
visual PASS
runtime PASS
```

を混同しない。

---

# 38. Astraの推論経路

必ず次の順で進める。

```text
STEP 1
GITHUB.TXTで現状固定

STEP 2
MRPを見てProductの原型を理解

STEP 3
Current Phase3Lで現在の技術能力を把握

STEP 4
WF54-59で最小Character staging spineを理解

STEP 5
WF68 / WF70でComplex capabilityを理解

STEP 6
WF71 / Backend Decisionsで既存Backend再利用方針を理解

STEP 7
Current UI sourceとMRP canvasを比較

STEP 8
Asset Ledgerを作る

STEP 9
Primary UXを再定義

STEP 10
Architecture / Roadmapを組み直す
```

---

# 39. 読み過ぎ防止ルール

過去Phaseを調べるのは:

```text
現在の設計判断の理由が分からない時
```

だけ。

過去実験を時系列に全再現することは目的ではない。

---

# 40. Astraの最終成果物 4
# Web GPT → Antigravity2 実行プロトコル

新規:

```text
ComfyUIPortable/docs/plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md
```

目的:

```text
Astra Master Plan
↓
Web ChatGPT
↓
Phase実装指示書
↓
Antigravity2 Gemini
↓
GitHub
↓
Web ChatGPT Review
```

を標準化。

---

# 41. Web GPTの今後の役割

Web版ChatGPTは:

```text
Strategic Planを毎回再発明しない
```

。

まず:

```text
GITHUB.TXT
↓
ASTRA_MANGA_AUTHORING_MASTER_PLAN
↓
最新Phase Report
```

を読んでから、

```text
次の具体的なGemini実装指示書
```

を作る。

---

# 42. Gemini Antigravity2の役割

Geminiは:

```text
implementation
tests
runtime execution
reports
workflow generation
```

を担当。

Strategic architectureを独断で全面変更しない。

独自判断はReportへ分離。

---

# 43. GitHubをAI間の共有メモリとして使う

Web GPTはローカル会話だけではなく:

```text
GITHUB.TXT
```

をEntry PointとしてProject stateを取得する。

したがってAstra整理後はGITHUB.TXTを必ず更新する。

---

# 44. GITHUB.TXT更新方針
# 非常に重要

AstraのPlan追加だけで、

```text
Review Target Commit SHA
```

を計画文書commitへ置き換えない。

これは実装レビュー用SHAである。

現在の実装Review Targetは、
次の実装PhaseまでPhase3L commitを保持してよい。

代わりにGITHUB.TXTへ新Sectionを追加:

```text
Strategic Planning SSOT
```

---

# 45. GITHUB.TXTへ追加する内容

例:

```text
--------------------------------------------------------------------------------
0. Strategic Planning SSOT
--------------------------------------------------------------------------------

Astra Master Plan:
Pinned Raw: ...

Astra Asset / Workflow Inventory:
Pinned Raw: ...

Astra Rapid Manga UX Blueprint:
Pinned Raw: ...

Astra WebGPT → Antigravity Execution Protocol:
Pinned Raw: ...

MRP Legacy UX Navigation:
https://raw.githubusercontent.com/toshinka/tegaki/main/EasyReforgeExtension/GitHubURL_ERE.txt

Planning Commit SHA:
<PLAN_COMMIT_SHA>
```

---

# 46. GITHUB.TXTのReading Orderも更新

外部Web GPT向けに:

```text
FIRST:
GITHUB.TXT

THEN:
Astra Master Plan
Asset Inventory
UX Blueprint

THEN:
Current Phase report

ONLY THEN:
code / workflows
```

と明記。

---

# 47. 次回実装Phase後

Geminiが次Phaseを実装した場合は:

```text
Commit A:
implementation

Commit B:
GITHUB.TXT update
```

を維持。

その時:

```text
Review Target Commit SHA = implementation Commit A
```

へ更新。

Astra Strategic Plan linksは消さない。

---

# 48. Planning documentのCommit

AstraがRepoへ書き込み可能な場合:

### Commit A

```text
docs(manga): add Astra strategic replan and asset inventory
```

内容:

```text
ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
ASTRA_RAPID_MANGA_AUTHORING_UX_BLUEPRINT.md
ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md
```

### Commit B

```text
docs(manga): expose Astra strategic plan in GITHUB.TXT
```

GITHUB.TXTへPinned URLsを追加。

---

# 49. Planning Commitでは実装コードを変えない

変更禁止:

```text
custom_nodes runtime behavior
workflow production behavior
model config
sampler
ControlNet
tegaki_work
```

今回の目的は計画整理。

---

# 50. Astraが新Roadmapを作る時の原則

Phase番号を無理に現在の延長へ合わせる必要はない。

ただしWeb GPT / Geminiが追跡できるよう:

```text
Current completed:
Phase 3L

Next implementation:
Phase 3M or renamed equivalent
```

の対応表を作る。

---

# 51. RoadmapはProduct Gate中心にする

研究機能中心ではなく:

```text
Gate A:
Rough Panels usable

Gate B:
Rough Character placement usable

Gate C:
Prompt panels usable

Gate D:
Fast draft usable

Gate E:
Seed brainstorm usable

Gate F:
Candidate → Pose refine usable

Gate G:
Advanced SubScene usable

Gate H:
Production UX coherent
```

のようにProduct Gateを重視。

---

# 52. 技術Gateも分離

例:

```text
Semantic compiler stable
Backend adapter thin
Advanced-ControlNet adopted
External pose asset contract
SubScene contract
Interaction contract
```

Product Gateと技術Gateを同じ表へ混ぜ過ぎない。

---

# 53. Astraが特に判断してほしい問い

以下へ明確に回答する。

### Q1

```text
ComfyUI上で
MRPのような直接Canvas操作を
どこまでMainline UIとして実現すべきか
```

### Q2

```text
Panel Rectangle EditorとCharacter Rectangle Editorは
一つのCanvasに統合すべきか
段階的に切り替えるべきか
```

### Q3

```text
Prompt Panelは
Panel tab / Character tab / Inspector
のどれが最も自然か
```

### Q4

```text
Character rectangleからPose Assetへ昇格する
最も自然なData Modelは何か
```

### Q5

```text
Seed Brainstorm / Candidate Browserを
どの段階で実装すべきか
```

### Q6

```text
SubSceneをAdvanced機能として
どのUI位置に隠すか
```

### Q7

```text
ComfyUI node UIで限界が来る地点はどこか
Dedicated GUIへ移るGateは何か
```

---

# 54. 出力には「推論」と「事実」を分離する

各重要判断に:

```text
Repository Fact
Inference
Recommendation
```

を区別して書く。

---

# 55. Astraの最終回答フォーマット

最低限:

```text
Current GITHUB Review Target:
Phase3L reflection:
MRP understanding:
Desired product in one sentence:

Top 10 reusable assets:
Top 10 archive/defer candidates:

Primary UX:
Architecture:
Backend strategy:
Workflow reuse strategy:

Next Product Gate:
Next Technical Gate:

Created Planning Docs:
Planning Commit SHA:
GITHUB.TXT Updated:
```

---

# 56. 最終的な製品像の一文

Astraは最終的に、
このProductを一文で説明できる状態にする。

暫定候補:

```text
「コマとキャラをキャンバスへ雑に置き、
対応Promptで即座に漫画案を出し、
良い生成結果だけPoseやSubSceneで段階的に詰められる、
MRP発展型の漫画Authoring Frontend」
```

これより良い定義があれば置き換えてよい。

---

# 57. 最終注意

細部まで読むこと自体は歓迎する。

ただし目的は:

```text
全過去実験を完全理解すること
```

ではなく:

```text
今ある資産から
最短で使える漫画制作Productへ収束させること
```

である。

成果として:

```text
新しいNodeを増やす
```

だけでなく:

```text
使える既存資産を発見する
重複を減らす
不要研究をMainlineから外す
UIを単純にする
```

ことを高く評価する。

---

# 58. 最終フロー

Astra整理後の標準運用:

```text
GPT-6 Astra
→ Strategic Master Planを整備

GitHub GITHUB.TXT
→ Astra PlanへのEntry Pointを保持

Web ChatGPT
→ GITHUB.TXT + Astra Planを読んで
   小さなPhase実装指示書を作る

Antigravity2 Gemini
→ 実装 / Test / Runtime / Report

GitHub
→ GITHUB.TXTを更新

Web ChatGPT
→ 固定SHAをレビュー

必要時
→ Astraへ再度Strategic Review
```

この役割分担を明確に維持すること。
