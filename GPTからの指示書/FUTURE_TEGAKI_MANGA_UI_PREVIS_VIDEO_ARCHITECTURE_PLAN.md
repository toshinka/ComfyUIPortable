# FUTURE — Tegaki Manga UI / Dynamic Graph / Previs・Video Architecture Plan
## RookieUI 研究、専用GUI、3D Blocking、Rough Guide、H3/Video Route を一つの将来構想として整理する

---

## ⚠️ READ GATE / 実装エージェント向け最重要注意

**STATUS: FUTURE / DEFERRED / NON-ACTIVE**

**AUTHORITY: Advisory only. 現在のPhase Card / GITHUB_ComfyUI.txt / 現行SSOTを上書きしない。**

### Current implementation agents

現在の実装作業中にこの文書を偶然見つけた場合:

1. **この「READ GATE」と Section 0「Destination Snapshot」だけ読んでよい。**
2. 現在のTask Cardがこの文書を明示的に参照していない限り、**Section 1以降を実装根拠として使わない。**
3. この文書を理由に、Sidebar GUI / Dynamic Graph Builder / RookieUI統合 / 3D editor / H3・Video route / 新ControlNet構成を現在Phaseへ追加しない。
4. 「将来そうなるから今も作っておこう」という先回り実装は禁止。
5. 現在のCanonical workflow / Authoring Contract / Product Cardを優先する。

### このファイルを置く推奨場所

```text
ComfyUIPortable/docs/future/
```

推奨ファイル名:

```text
FUTURE_TEGAKI_MANGA_UI_PREVIS_VIDEO_ARCHITECTURE_PLAN.md
```

### 現時点では行わないこと

この文書を `GITHUB_ComfyUI.txt` の Mandatory Reading Order、現行Active Plans、現行Task Cardの必読資料へ入れない。

Document Registerへ載せる場合も:

```text
FUTURE / DEFERRED / DO NOT READ UNLESS ACTIVATED
```

として別区分にする。

---

# 0. Destination Snapshot
## 将来の着地点だけは見えてよい

将来のTegaki Mangaは、ComfyUIのノードグラフを主画面として操作するツールではなく、

```text
Tegaki Manga Authoring UI
        ↓
TEGAKI_AUTHORING_DOCUMENT
        ↓
Semantic / Execution Compiler
        ↓
Graph Builder
        ↓
ComfyUI Runtime
```

という構造を目標とする。

通常ユーザーが見るもの:

```text
Project
Resolution / Style
CAST
Scene
Character
Visual Frame
Rough Guide
Seed / Brainstorm
Generate
Preview
```

通常ユーザーが見なくてよいもの:

```text
Checkpoint Loader
CLIP Encode
Regional Conditioning
ControlNet Apply
KSampler
VAE
Frame Overlay
Graph Links
Backend Adapter Nodes
```

理想UI:

```text
NORMAL MODE
Tegaki Manga UIのみ

ADVANCED / DEBUG
Generated ComfyUI Graphを開ける
```

現在作っているMinimum-Hand Authoringは、この将来GUIの「意味・状態・操作契約」を先に固めるための実証段階として扱う。

---

# 0.1 Long-term generation routes

同じAuthoring Dataから複数経路へ分岐できる構造を目標とする。

```text
TEGAKI_AUTHORING_DOCUMENT
        │
        ├── Manga Route
        │     └ Illustrious / LoRA / Regional / Guide
        │
        ├── Rough Guide Route
        │     └ White Dummy / Rough Manga / Control
        │
        └── Future Previs / Video Route
              ├ 3D Blocking
              ├ H3 / other video generation
              └ Candidate Frame → Manga Routeへ戻す
```

最終漫画絵の中心は当面 `Illustrious + existing LoRA assets` であり、3D / Videoは置換ではなく補助経路。

---

# 0.2 Short product principle

```text
Place Roughly
Generate Quickly
Explore Variations
Choose Good Ideas
Refine Only What Matters
```

将来GUI、3D、Videoを追加しても、このMinimum-Hand原則を壊さない。

---

# 1. Activation Gates
## この文書を本格的に読んでよい時期

Phase番号ではなく、能力Gateで判定する。

## Gate UI-1 — Dedicated UI Architecture Studyを開始してよい条件

最低限:

```text
Scene authoring: stable
CAST / Character Instance: stable
Visual Frame: stable
Rough Guide / white-dummy path: usable
Live Browser: load / queue / save / reload が安定
TEGAKI_AUTHORING_DOCUMENT: 大きな破壊変更が頻発していない
```

このGateを満たした時だけ、Section 3以降のDedicated GUI設計をCurrent Planningへ昇格してよい。

## Gate UI-2 — Dynamic Graph Builderへ進む条件

```text
Canonical Workflowで主要Product pathが成立
Backend responsibilityが分離済み
Authoring Documentから必要backendが機械的に判断可能
Regression fixtureが十分
```

になるまで、Canonical Workflowを捨てない。

## Gate PV-1 — 3D / Previs研究を開始してよい条件

最低限:

```text
2D Rough Guide pathを一度完成・評価済み
3人以上 / exact depth / exact blocking等で明確な不足が残る
Seed searchやPrompt tuningよりBlockingの方が低コストと判断できる
```

「3Dの方が高度そう」という理由だけで開始しない。

## Gate PV-2 — H3 / Video Routeを開始してよい条件

```text
Scene / CAST / Character Instance mappingが安定
Candidate frameをSceneへ紐付けられる
短尺Video/Frame generationが実用コストで利用可能
Videoで構図候補を作る価値がSeed-only brainstormを上回る
```

---

# 2. Current Priority vs Future Priority

現在本線:

```text
Minimum-Hand Authoring
→ Semantic Scene
→ CAST / Character Rough Region
→ Visual Panel Frame
→ Rough Manga / White Dummy Guide
→ Seed Brainstorm
→ Illustrious
```

将来枝:

```text
Dedicated Sidebar GUI
Dynamic Graph Builder
3D Blocking
H3 / Video Previs
Video Frame → Illustrious bridge
RookieUI interoperability
```

将来枝を現在本線より先に実装しない。

---

# 3. Dedicated GUI Strategy
## 結論

第一候補:

```text
ComfyUI公式Extension API上に
Tegaki専用Sidebar / Authoring Shellを作る
```

RookieUIそのものをHostとして必須依存にはしない。

## 3.1 なぜComfyUI Sidebarが本命か

ComfyUI公式Frontendには、Extensionが独自Sidebar Tabを登録するAPIが存在する。

したがって将来的に:

```text
ComfyUI Sidebar
├ Queue
├ Models
├ RookieUI          [installed if user wants]
└ Tegaki Manga
```

という共存が可能。

Tegakiが独自にComfyUI全体をForkする必要はない。

## 3.2 RookieUIの位置づけ

RookieUIは `DEPENDENCY候補` より先に `ARCHITECTURE PRIOR ART / TEACHER` として扱う。

特に研究価値が高い:

```text
Sidebar bootstrap
Feature registry
Frontend lifecycle
UI state → request normalization
workflow_translation facade
workflow_builders/*
Queue / progress / preview
Model inventory
Capability detection
ControlNet integration
Live-host smoke tests
E2E coverage
Frontend/backend boundary
```

## 3.3 RookieUIから特に学ぶ構造

現在のRookieUIは概ね:

```text
Sidebar UI
↓
Frontend API / typed state
↓
Backend request normalization
↓
workflow_translation facade
↓
workflow_builders/*
↓
ComfyUI queue
```

へ分離されている。

Tegakiも最終的には:

```text
Tegaki Sidebar UI
↓
TEGAKI_AUTHORING_DOCUMENT
↓
Execution Intent
↓
Tegaki Graph Builder
↓
ComfyUI queue
```

へ近づける。

重要なのは見た目ではなく `UIとGraph constructionを分離する` こと。

## 3.4 RookieUIを直接Extension Hostとして使う案

候補として否定しない。

将来RookieUI側に `third-party feature/tab public extension contract` が明確に提供され、versioned / stableな接続点になった場合は再評価。

その時 `RookieUI → Tegaki Manga` も選択肢。

## 3.5 現時点で直接依存を第一候補にしない理由

1. Tegakiの中心データモデルはA1111型生成フォームではなく `Scene / CAST / Character Instance / Visual Frame / Guide`。
2. RookieUI内部構造変更へTegakiが巻き込まれる。
3. Manga-specific UIがRookieUIのtxt2img/img2img設計へ引っ張られる危険。
4. ComfyUI公式Sidebar APIで独立実装可能。
5. RookieUIはAGPL-3.0であり、コード流用・改変時はライセンス判断を明示的に行う必要がある。

## 3.6 推奨Integration Level

```text
LEVEL 1 — REFERENCE
RookieUI architectureを研究

LEVEL 2 — INTEROP
RookieUI ↔ Tegaki間で画像・Prompt・Seed等を送る

LEVEL 3 — OPTIONAL HOST INTEGRATION
RookieUIが安定したpublic seamを提供した場合だけ検討

LEVEL 4 — FORK
最後の手段
```

---

# 4. Future Tegaki Sidebar
## Normal Mode

候補:

```text
TEGAKI MANGA
├ Project
├ Global
│   ├ Resolution
│   ├ Style
│   └ Seed
├ CAST
├ Canvas
│   ├ Scene
│   ├ Frame
│   └ Character
├ Selected Item Inspector
├ Rough Guide
├ Generate
└ Preview / Candidates
```

## 4.1 Advanced Mode

必要時のみ:

```text
Model
Sampler
CFG
LoRA details
Control details
Debug Prompt
Execution Plan
Open Generated Graph
```

Primary UIへtechnical controlsを常時出さない。

## 4.2 Generated Graph

将来 `Open Generated Graph` を用意。

通常はGraph hidden、Debug時だけ現在のAuthoring Documentから構築された実Graphを開く。

これによりComfyUIの透明性を失わない。

---

# 5. Canonical WorkflowからDynamic Graphへ

現在の `MINIMUM_HAND_MANGA_DRAFT.json` は重要なGolden Workflow。

すぐ廃止しない。

## Phase DG-0

Canonical Workflowを:

```text
Product Reference
Regression Fixture
Debug Graph
```

として維持。

## Phase DG-1

Authoring Documentから `Execution Intent Plan` を生成。

例:

```text
has_characters
has_visual_frames
has_rough_guide
needs_regional_conditioning
needs_control
needs_frame_overlay
```

## Phase DG-2

Feature-specific builder:

```text
builders/
├ base_generation
├ regional_conditioning
├ character_regions
├ rough_guide
├ frame_overlay
└ future_previs
```

巨大な一枚Graph builderを作らない。

## Phase DG-3

実行時:

```text
Authoring Document
↓
Execution Intent
↓
Builder Registry
↓
ComfyUI Graph
↓
Queue
```

## 5.1 Graph Builder原則

```text
Scene 1人 → 不要なControl branchを作らない
2人 → Character regional path
Rough Guideあり → Guide path追加
Visual Frameあり → deterministic frame output追加
Previs referenceあり → future reference path追加
```

ユーザーは同じGUIを使う。

---

# 6. Why Current Work Is Not Wasted

現在の:

```text
TEGAKI_AUTHORING_DOCUMENT
Authoring Operations
Scene Compiler
Character Instance
Visual Frame
Frame Overlay
Regional Conditioning
```

は将来GUIからも利用する。

移行:

```text
Current: Custom DOM inside node
Future: Sidebar / Authoring Shell
Backend: mostly retained
```

現在作るProduct semanticsは将来GUIの仕様書でもある。

---

# 7. Rough Guide Route Remains First Escalation
## 3Dより先

ユーザーがPrompt + Rectangleだけで足りない時の第一候補:

```text
Rough Manga
White Dummy
Simple Silhouette
Uploaded Sketch
```

理由:

```text
入力が速い
2D漫画と対応が直感的
カメラ投影をユーザーが意識しなくてよい
IllustriousへそのままGuide化しやすい
```

## 7.1 Rough Guideの役割

```text
人物Aのrough occupancy
人物Bのrough occupancy
前後関係
大まかな姿勢
prop
```

精密Pose editorではない。

## 7.2 Product hierarchy

```text
Level 0: Rectangle + Prompt + Seed
Level 1: Rough 2D Guide
Level 2: 3D Blocking / Previs
Level 3: Precise Pose / Animation
```

---

# 8. Future 3D Blocking Route
## 目的

3Dの価値は `正しいworld-space関係を2D projectionへ変換する` こと。

Illustriousに3D空間を直接理解させる必要はない。

## 8.1 3D output

3D / Blockingから得る候補:

```text
RGB blockout
Depth
Edge / Line
Silhouette
Segmentation
Pose skeleton
Camera matrix
Object masks
```

Illustriousへは2D Guideとして渡す。

## 8.2 3D Editorを一から作らない

第一候補:

```text
既存lightweight blocking tool
Blender-based tool
browser scene blocking tool
external app
```

を利用。

Tegakiは `Import / Mapping / Guide conversion` に集中。

## 8.3 Tegakiが3D UIを作る条件

既存ツールで:

```text
必要な操作が過剰
Scene/Instance mappingが困難
export integrationが致命的
```

な時だけ。

その場合でもfull Blender cloneを作らない。

## 8.4 3D mapping

Core IDsを使う。

```text
scene_id
instance_id
cast_id
```

例:

```text
3D Object "AliceProxy"
→ instance_id = alice_scene2_001
```

## 8.5 3D dataを今Authoring Documentへ追加しない

現在v1 contractへ `world_position / rotation / camera_matrix` を先回りで必須追加しない。

初期研究ではPREVIS sidecarまたはderived adapter dataで十分。

必要性が証明されてからschema versionを上げる。

---

# 9. Future H3 / Video Route
## 基本思想

H3等の動画モデルを `最終漫画描画器` ではなく `Temporal Composition / Acting Candidate Generator` として使う。

## 9.1 Shared Prompt / Shared Authoring

同じ:

```text
Scene Prompt
CAST identity
Character acting
rough placement
camera intent
```

をManga RouteとVideo Routeが共有。

## 9.2 Dual Route

```text
Scene Data
   │
   ├── Illustrious Route
   └── H3 Route
```

H3結果を再びManga Routeへ戻せる。

## 9.3 H3 output duration

漫画用途では長尺不要。

初期候補:

```text
数フレーム
または
2〜5秒
```

目的は `良い瞬間 / 良いblocking / 良いcameraを拾う` こと。

## 9.4 Candidate Frames

H3 outputの候補から `Use as Manga Guide` を選択。

## 9.5 Scene mapping

重要:

```text
H3 Scene count
≠
Visual Frame count
```

H3 candidateは `scene_id` へ紐付く。

Visual Frameは別。

## 9.6 H3 frameをIllustriousへ送る方法

初期候補はselected RGB frame。

必要時:

```text
Depth extraction
Edge extraction
Pose extraction
Silhouette
```

へ変換。

## 9.7 Illustriousの役割

```text
Composition / Pose / Depth = H3 / Previs
Identity / Manga Style / LoRA assets = Illustrious
```

という分業。

---

# 10. ControlNet Architecture for Previs
## Scene数だけControlNetを増やさない

ControlNet unit countはScene数よりGuide modality数を基準にする。

## 10.1 Visual Frame

実際の黒枠はDeterministic Overlay。

原則ControlNet不要。

Frame ControlNetはcomposition assistが必要な時だけ。

## 10.2 H3 / Previs Guide

可能ならSceneごとのcandidate guideをPage-sized Guide CanvasへScene geometryに合わせて合成。

例:

```text
Scene A selected frame → Scene A area
Scene B selected frame → Scene B area
```

これを1枚のDepth ControlまたはEdge Controlとして使う。

## 10.3 推奨Control Unit数

例:

```text
Control 1: Page-composited Depth
Control 2: optional Page-composited Edge
```

`Scene A Control / Scene B Control / Scene C Control / Frame Control` と無条件に増殖させない。

## 10.4 Strict isolationが必要な場合

Page-composite Guideで混線するならAdvanced path:

```text
Scene Aを個別生成
Scene Bを個別生成
...
↓
PageへComposite
↓
Deterministic Frame Overlay
```

強いが計算量増。

## 10.5 3つの実行戦略

### Strategy P1 — Page Composite Guide
最初に試す。Fast / Simple / Minimum-Hand。

### Strategy P2 — Regional Guide / Regional Control
必要な場合。More precise / More complex。

### Strategy P3 — Per-Scene Generation + Composite
最終手段。Highest isolation / Highest compute。

---

# 11. Candidate Browserとの関係

Video Routeを作る前に、still Seed BrainstormのCandidate Browserは有用。

共通UI:

```text
Candidate
├ Image Seed Candidate
├ Video Frame Candidate
└ Future 3D Camera Candidate
```

最終的に:

```text
Use Composition
Use Pose
Use as Guide
```

へ統合可能。

---

# 12. Future UI Integration

将来Sidebar:

```text
GENERATE
[Draft]

BRAINSTORM
Seed Candidates

ADVANCED SOURCE
[Use Rough Guide]
[Use 3D Blockout]
[Generate Motion Candidates]

REFERENCE CANDIDATES
[frame A]
[frame B]
[frame C]
```

初見ユーザーにはAdvanced Sourceを閉じる。

---

# 13. RookieUI Interop
## Optional

独立Sidebarを採用してもRookieUIと共存可能。

候補:

```text
Tegaki output → Send to RookieUI Img2Img
RookieUI output → Use as Tegaki Rough Guide
RookieUI Prompt → Import into Tegaki selected Scene
Tegaki seed/model settings → optional handoff
```

## 13.1 Interopはファイル/metadata/API境界

RookieUI内部stateへ直接侵入しない。

第一候補:

```text
image artifact
PNG metadata
prompt text
seed
model identifier
```

等の明示境界。

---

# 14. Licensing / Dependency Policy

External projectを研究する時:

```text
REFERENCE
ADAPT CONCEPT
DEPENDENCY
CODE COPY
```

を分ける。

RookieUIはAGPL-3.0。

したがって `構造を研究 → 公式API上に独自実装` を第一候補。

コードを直接複製・改変する場合は、その時点でライセンス方針を明示決定する。

---

# 15. Architecture Guardrails

将来も絶対に維持。

```text
A. TEGAKI_AUTHORING_DOCUMENT = Persistent Authoring SSOT
B. Backend Graph = Derived
C. Scene ≠ Visual Frame
D. Character Rough Region ≠ Pose
E. 3D / Video = Optional escalation
F. ControlNet = 必要時の補助
G. Normal user ≠ Graph engineer
```

---

# 16. Anti-Goals

作らない:

```text
Full Blender clone
Mandatory 3D workflow
Mandatory Video workflow
Mandatory ControlNet per Scene
Mandatory Pose editor
RookieUI hard dependency
RookieUI fork without explicit reason
H3 scene count == comic frame count contract
One huge dynamic graph builder
Backend-specific objects inside Authoring Document
```

---

# 17. Roadmap — GUI Branch

## GUI-R0 — Prior Art Audit
Activation Gate UI-1後。

研究:

```text
ComfyUI Sidebar API
RookieUI bootstrap
RookieUI workflow translation
RookieUI queue/preview
state persistence
live-host testing
```

成果はADOPT / ADAPT / REFERENCE / BUILD matrix。

## GUI-R1 — Tegaki Sidebar Shell

最小:

```text
Open Authoring Document
Canvas
Selected Scene
Generate
Preview
```

まだ全機能移植しない。

## GUI-R2 — Current Minimum-Hand parity

```text
Global
CAST
Scene
Character
Frame
Rough Guide
Seed
```

をSidebarへ。

Node Custom DOMと同じDocumentを共有。

## GUI-R3 — Dynamic Graph Builder

Canonical WorkflowとA/B。

同じ結果を出せることを検証。

## GUI-R4 — Normal / Advanced mode

NormalはGraph hidden、AdvancedはOpen Generated Graph。

## GUI-R5 — Optional RookieUI Interop

stable boundaryがある時だけ。

---

# 18. Roadmap — Previs / Video Branch

## PV-R0 — Research memo only
今。実装しない。

## PV-R1 — External Still Blockout Import

最初の実装候補。

```text
3D tool / external blockout
→ screenshot / depth / silhouette
→ Tegaki Scene Guide
```

H3なし。

## PV-R2 — 3D Mapping

```text
scene_id
instance_id
camera
```

mapping。

## PV-R3 — Short Video / Few-frame Candidate

```text
Scene
→ H3
→ 2–5 sec / few candidates
```

## PV-R4 — Candidate Frame → Manga

```text
selected video frame
→ RGB/Depth/Edge
→ Scene region
→ Illustrious + LoRA
```

## PV-R5 — Automated Dual Route

```text
Generate Scene Candidates
→ choose
→ Manga Bake
```

---

# 19. Decision Gates
## Dedicated Sidebarを作るか

GO if:

```text
Current Custom Node UIが窮屈
Product semantics stable
Authoring Document stable
Live browser path stable
```

## RookieUIへ直接載せるか

GO only if:

```text
Stable public extension seam exists
Maintenance coupling acceptable
License policy accepted
Tegaki data modelを歪めない
```

OtherwiseはIndependent Tegaki Sidebar。

## 3Dへ進むか

GO if:

```text
2D Rough Guideではexact spatial relationが高コスト
3D blockoutなら短時間
existing tool reuse possible
```

## H3へ進むか

GO if:

```text
Short video produces useful composition/acting candidates
Candidate extraction is cheap
Still seed brainstormingより価値がある
```

---

# 20. Cost Metric
## 技術的に出来るかだけで決めない

比較:

```text
Prompt tuning cost
Seed search cost
2D rough drawing cost
3D blocking cost
Video generation cost
Review / candidate selection cost
```

最小のユーザー負担を選ぶ。

---

# 21. Future Experiment Design

### Experiment A — 2D Rough Guide vs 3D Still Blockout

同じScene / CAST / promptで:

```text
time-to-first-usable
position accuracy
depth accuracy
user actions
seed freedom
```

を測る。

### Experiment B — Still Seed Brainstorm vs H3 Few-frame Brainstorm

```text
usable composition count
usable pose count
generation cost
selection cost
```

を比較。

### Experiment C — H3 RGB vs Depth vs Edge

同じcandidate frameをIllustriousへ:

```text
RGB reference
Depth
Edge
RGB + Depth
```

で比較。

最小のGuideで十分なものを採用。

---

# 22. Do Not Change Current Schema Yet

このFuture Planを読んだからといって、現在の`TEGAKI_AUTHORING_DOCUMENT v1`へ:

```text
previs
video
3d
world_position
camera matrix
```

を追加しない。

必要時にsidecar / derived execution planから開始。

実需が確定した時だけversioned migration。

---

# 23. When This Plan Becomes Active

Current Cardが明示的に:

```text
Activate FUTURE_TEGAKI_MANGA_UI_PREVIS_VIDEO_ARCHITECTURE_PLAN
```

または同等の宣言を行った時だけActive Planningへ昇格。

それまでは:

```text
Direction Reference
not Implementation Instruction
```

---

# 24. Short Handoff Summary for Future AI

このProjectの将来目標は:

```text
ComfyUIの強力なruntimeは残す
しかし通常ユーザーにはNode Graphを要求しない
```

こと。

RookieUIはSidebar + Workflow TranslationのPrior Artとして学ぶ。

第一候補はComfyUI公式Extension API上の独立Tegaki Manga Sidebar。

現在のAuthoring Document / Compilerを継承し、将来Dynamic Graph Builderへ移行。

位置・演技の難しいケースでは:

```text
Rectangle + Prompt
→ 2D Rough Guide
→ 3D Blocking
→ H3 / Video Candidate
```

の順に段階的Escalation。

Video routeは漫画routeとPrompt / Scene / CASTを共有し、選ばれたvideo frameをIllustriousへGuideとして戻す。

Comic Visual FrameはSceneとは独立し、最終枠線はdeterministic renderingを基本とする。

最重要:

```text
Future architecture must not make current authoring harder.
```

---

# 25. External Prior-Art Notes
## 2026-09確認時点

### ComfyUI

公式Frontend Extension APIでcustom Sidebar Tabを登録可能。

したがってTegaki専用Sidebarは正式なExtension形態として実現可能。

### ComfyUI-RookieUI

現在の公開READMEでは:

```text
frontend sidebar shell / bootstrap registry
workflow_translation facade
workflow_builders/*
backend/frontend integrated feature registry
typed frontend API seams
queue / preview / runtime integration
live-host validation
```

等へ分離されている。

Tegakiの将来GUI / Graph Builder設計を考える際の重要なPrior Art。

License:

```text
AGPL-3.0
```

---

# 26. Final Rule

この文書が将来の着地点を示していること自体は有益。

ただし現在のAgentへ渡すべき情報は:

```text
「将来、独立GUI / Dynamic Graph / Previsにも拡張可能なよう
現在のAuthoring ContractをBackend-independentに保つ」
```

まで。

詳細機能を先取りさせない。

つまり:

```text
Destination is visible.
Implementation is gated.
```

を正式方針とする。
