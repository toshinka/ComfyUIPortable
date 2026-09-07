# FUTURE — Tegaki Manga UI / Dynamic Graph / H3 Still・Previs・Video Architecture Plan v2
## RookieUI研究、専用GUI、Rough Guide、H3静止画、3D Blocking、Video Routeを統合した将来構想

---

## ⚠️ READ GATE / 実装エージェント向け最重要注意

**STATUS: FUTURE / DEFERRED / NON-ACTIVE**

**AUTHORITY: Advisory only. 現在のPhase Card / GITHUB_ComfyUI.txt / 現行SSOTを上書きしない。**

### Current implementation agents

現在の実装作業中にこの文書を偶然見つけた場合:

1. **このREAD GATEと Section 0「Destination Snapshot」だけ読んでよい。**
2. 現在のTask Cardがこの文書を明示参照していない限り、**Section 1以降を実装根拠として使わない。**
3. この文書を理由に現在Phaseへ以下を先回り追加しない。
   - Tegaki専用Sidebar
   - Dynamic Graph Builder
   - RookieUI統合
   - H3 Still / Reference Edit
   - H3 Video
   - 3D editor
   - 新しいControlNet構成
4. 「将来使うから今作っておく」は禁止。
5. 現在のCanonical Workflow / Authoring Contract / Product Cardを優先。

### 推奨配置

```text
ComfyUIPortable/docs/future/
```

推奨ファイル名:

```text
FUTURE_TEGAKI_MANGA_UI_PREVIS_VIDEO_ARCHITECTURE_PLAN_v2.md
```

### 現時点ではしないこと

この文書を以下へ入れない。

```text
GITHUB_ComfyUI.txt Mandatory Reading Order
現行Active Plans
現行Task Cardの必読資料
```

Document Registerへ載せる場合も:

```text
FUTURE / DEFERRED / DO NOT ACT UNLESS ACTIVATED
```

として別区分にする。

---

# 0. Destination Snapshot
## 将来の着地点は見せる。実装はGateする。

将来のTegaki Mangaは、ComfyUIノードグラフを主画面として操作するツールではなく、

```text
Tegaki Manga Authoring UI
        ↓
TEGAKI_AUTHORING_DOCUMENT
        ↓
Semantic / Execution Compiler
        ↓
Route Selector
        ↓
Graph Builder
        ↓
ComfyUI Runtime / External Model Route
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
Preview / Candidates
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
H3 internal workflow
```

理想UI:

```text
NORMAL MODE
Tegaki Manga UIのみ

ADVANCED / DEBUG
Generated ComfyUI Graph / execution planを開ける
```

現在作っているMinimum-Hand Authoringは、この将来GUIの「意味・状態・操作契約」を先に固めるための実証段階。

---

# 0.1 Long-term generation routes

同じAuthoring Dataから複数経路へ分岐できる構造を目標とする。

```text
TEGAKI_AUTHORING_DOCUMENT
        │
        ├── Route I — Illustrious Direct
        │     └ Regional / LoRA / Rough Guide / Frame Overlay
        │
        ├── Route Hs — H3 Still
        │     ├ T2I-like still extraction
        │     ├ I2I anchor
        │     └ Multi-reference / Reference Edit
        │
        ├── Route Hv — H3 Video / Previs
        │     └ Few-frame / short clip → Candidate Frames
        │
        ├── Route HI — H3 → Illustrious Finish
        │     └ H3 composition / acting → Illustrious style / LoRA finish
        │
        └── Route P — 3D / Blocking Assist
              └ RGB / Depth / Edge / Silhouette → Manga or H3 route
```

最終漫画絵の中心は当面:

```text
Illustrious + existing LoRA assets
```

だが、将来H3 Stillが十分な漫画品質を持つ場合は:

```text
H3-only completion
```

も許可する。

---

# 0.2 Short product principle

```text
Place Roughly
Generate Quickly
Explore Variations
Choose Good Ideas
Refine Only What Matters
```

将来GUI、H3、3D、Videoを追加してもMinimum-Hand原則を壊さない。

---

# 0.3 v2での重要な変更点

旧版では概ね:

```text
Rough Guide
→ 3D
→ H3 Video
```

を将来順序として想定していた。

v2ではH3静止画利用の先行実装・実例を受けて:

```text
Rough Guide
→ H3 Still / Reference Edit
→ H3 Video
→ 3D Blocking
```

へ研究優先順位を更新する。

理由:

```text
H3 Still / Reference Editは
複数画像参照
自然言語による役割指定
構図anchor
画像編集
```

を持ち、3Dを作らずに一部の位置関係・CAST整合問題を解ける可能性がある。

---

# 1. Activation Gates

## Gate UI-1 — Dedicated UI Architecture Study

最低限:

```text
Scene authoring stable
CAST / Character Instance stable
Visual Frame stable
Rough Guide path usable
Live Browser load / queue / save / reload stable
TEGAKI_AUTHORING_DOCUMENTが頻繁に破壊変更されていない
```

このGate後だけDedicated GUI設計をCurrent Planningへ昇格。

---

## Gate H3S-1 — H3 Still研究開始

最低限:

```text
Current Minimum-Hand Illustrious routeが一度完成
Rough Guide / Character mappingが安定
Scene / CAST / Character Instance IDsが安定
H3 Stillがローカルまたは実用コストで利用可能
```

なら研究開始可能。

3D完成を待つ必要はない。

---

## Gate H3S-2 — H3 StillをProduct候補へ昇格

以下を同入力で比較:

```text
A. Illustrious Direct
B. H3 Still
C. H3 → Illustrious Finish
```

評価:

```text
CAST identity
rough position
depth
acting
manga style
seed/candidate efficiency
user effort
VRAM / runtime cost
```

H3 routeが実用的に勝つケースがある時だけProduct route候補へ。

---

## Gate PV-1 — 3D / Blocking研究

以下が成立した時だけ:

```text
2D Rough Guideでもexact spatial relationが高コスト
H3 Stillでも不足
3D blockoutなら短時間で解決できそう
既存tool reuse可能
```

。

---

## Gate HV-1 — H3 Video Route

```text
Scene / CAST mapping stable
Few-frame / short clipが実用コスト
Still seed brainstormより時間軸候補が明確に有用
```

で開始。

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

将来研究優先順位:

```text
1. H3 Still / Reference Edit
2. H3 → Illustrious Finish
3. H3 Few-frame / Video Candidate
4. 3D Blocking
5. Dedicated dynamic execution optimization
```

Dedicated SidebarはProduct semanticsが安定した時点で別軸で進める。

---

# 3. Dedicated GUI Strategy

第一候補:

```text
ComfyUI公式Extension API上に
Tegaki専用Sidebar / Authoring Shell
```

。

RookieUIを必須Hostにしない。

RookieUIは:

```text
ARCHITECTURE PRIOR ART / TEACHER
```

として研究。

特に見る:

```text
Sidebar bootstrap
Feature registry
UI state → execution payload
workflow translation
workflow builders
queue / progress / preview
capability detection
live-host tests
```

。

---

# 4. Future Tegaki Sidebar

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
├ Selected Inspector
├ Rough Guide
├ Route
│   ├ Auto
│   ├ Illustrious
│   ├ H3 Still
│   └ Advanced
├ Generate
└ Candidates
```

通常はRoute選択すらAutoでよい。

---

# 5. Canonical WorkflowからDynamic Graphへ

現在:

```text
MINIMUM_HAND_MANGA_DRAFT.json
```

はGolden Workflow。

すぐ廃止しない。

将来:

```text
Authoring Document
↓
Execution Intent
↓
Route Selector
↓
Builder Registry
↓
ComfyUI Graph / H3 request
↓
Queue
```

。

Builder候補:

```text
base_generation
regional_conditioning
character_regions
rough_guide
frame_overlay
h3_still
h3_video
previs_3d
```

。

---

# 6. Why Current Work Is Not Wasted

現在の:

```text
TEGAKI_AUTHORING_DOCUMENT
Scene
CAST Master
Character Instance
Visual Frame
Rough Guide
Frame Overlay
Regional Conditioning
```

は将来どのRouteでも上流共通資産。

---

# 7. Rough Guide Route Remains First Escalation

Prompt + Rectangleだけで足りない時の第一候補:

```text
Rough Manga
White Dummy
Simple Silhouette
Uploaded Sketch
```

。

重要:

```text
Rough Guide
=
Illustrious専用assetではない
```

。

将来:

```text
Rough Guide
├→ Illustrious ControlNet
├→ H3 I2I anchor
└→ H3 Reference Edit composition source
```

へ共用。

---

# 8. H3 Still / Reference Edit Route
## v2で最重要の将来研究枝

H3を動画モデルとしてだけでなく:

```text
Multimodal Still Composition / Reference Generator
```

として使う。

---

# 8.1 H3 Still input roles

候補:

```text
Picture 1 = rough composition / white dummy / source image
Picture 2 = Alice reference
Picture 3 = Bob reference
Picture 4 = Carol reference
Picture 5 = prop reference
Picture 6 = background/style reference
```

。

参照枠数が多いからといって全て使わない。

役割を明示してambiguityを抑える。

---

# 8.2 Tegaki Reference Assignment Compiler

Tegaki側で:

```text
CAST Alice
→ reference slot 2
role = identity

CAST Bob
→ reference slot 3
role = identity

Rough Scene
→ reference slot 1
role = composition anchor
```

を生成。

Persistent Authoring DocumentへH3固有slot番号を直接保存しない。

Derived execution mapping。

---

# 8.3 Multimodal Semantic Regional Generation

H3 Reference EditはMRPそのものではない。

MRP:

```text
Prompt A → Mask A
Prompt B → Mask B
```

H3:

```text
Picture A = Alice
Picture B = Bob
Promptで役割と空間関係を記述
```

。

将来:

```text
Multimodal Semantic Regional Generation
```

として比較研究する。

---

# 8.4 Spatial Compiler再利用

現在の:

```text
Alice area = left
Bob area = right
```

からH3用に:

```text
Alice occupies the left side
Bob occupies the right side
```

等をderived promptへ変換可能。

深度:

```text
Alice large in foreground
Bob smaller in background
```

。

---

# 8.5 H3 manga-style prompt

研究候補:

```text
black-and-white Japanese manga
screentone
fine cross-hatching
ink line art
high contrast
no color
```

。

ただしH3だけで完璧なモノクロ・トーン・枠を保証しない。

---

# 8.6 H3-only route

H3出力が十分なら:

```text
H3 Still
→ deterministic Visual Frame Overlay
→ final
```

も許可。

---

# 8.7 H3 → Illustrious Finish

H3で:

```text
composition
acting
depth
multi-character relation
```

を作り、

Illustriousで:

```text
LoRA identity/style
manga cleanup
monochrome refinement
regional re-bake
```

を行う。

---

# 8.8 H3 Static packet

漫画用途では長動画不要。

初期研究:

```text
few-frame packet
代表frame 1枚
```

。

---

# 9. H3 Video / Previs Route

H3 Videoは:

```text
Temporal Composition / Acting Candidate Generator
```

として扱う。

初期:

```text
数フレーム
または2〜5秒
```

。

---

# 9.1 Scene mapping

```text
H3 Scene count
≠
Visual Frame count
```

。

H3 candidateは`scene_id`へ紐付く。

---

# 10. 3D Blocking Route
## H3 Stillより後

3Dの価値:

```text
world-space関係を正しい2D projectionへ落とす
```

こと。

3D editorは第一候補として外部既存toolを使う。

TegakiはImport / Mapping / Guide conversionへ集中。

---

# 11. ControlNet Architecture
## Scene数だけControlNetを増やさない

基本:

```text
Control unit count
≠
Scene count
```

。

Guide modality数を基準にする。

Visual Frameの黒枠はDeterministic Overlay。

SceneごとのGuideはPage-sized Guide Canvasへ合成し、

```text
Control 1 = Page-composited Depth
Control 2 = optional Page-composited Edge
```

のように扱う。

Strict isolationが必要な場合のみPer-Scene generationへ。

---

# 12. Route Strategy

```text
R0 — Illustrious Direct
R1 — H3 Still
R2 — H3 → Illustrious
R3 — Rough Guide → Illustrious
R4 — 3D / H3 Video
```

。

---

# 13. Candidate Browser

将来共通:

```text
Candidate
├ Seed Still
├ H3 Still
├ H3 Video Frame
└ 3D Camera Candidate
```

操作:

```text
Use Composition
Use Pose
Use as Guide
Use Seed
```

。

---

# 14. RookieUI Interop

独立Tegaki Sidebarを本命。

RookieUIとはoptional interop。

RookieUI内部stateへ直接侵入しない。

---

# 15. Licensing / Dependency Policy

External projectは:

```text
REFERENCE
ADAPT CONCEPT
DEPENDENCY
CODE COPY
```

を分離。

RookieUIはAGPL-3.0。

H3関連extensionも採用前にlicense確認。

---

# 16. Architecture Guardrails

```text
TEGAKI_AUTHORING_DOCUMENT = Persistent SSOT
Backend Graph = Derived
Scene ≠ Visual Frame
Character Rough Region ≠ Pose
H3 / 3D / Video = Optional escalation
ControlNet = Optional assist
Normal user ≠ Graph engineer
```

。

---

# 17. Anti-Goals

```text
Mandatory H3
Mandatory 3D
Mandatory Video
Mandatory per-Scene ControlNet
Mandatory Pose editor
Full Blender clone
RookieUI hard dependency
H3 scene count == Frame count
One huge graph builder
Backend-specific H3 slot IDs in Authoring Document
```

。

---

# 18. Roadmap — GUI Branch

```text
GUI-R0 Prior Art Audit
GUI-R1 Tegaki Sidebar Shell
GUI-R2 Current Minimum-Hand parity
GUI-R3 Dynamic Graph Builder
GUI-R4 Normal / Advanced mode
GUI-R5 Optional RookieUI Interop
```

。

---

# 19. Roadmap — H3 / Previs Branch

```text
H3-R0 Research only
H3-R1 H3 Still Smoke
H3-R2 H3 vs Illustrious A/B
H3-R3 Multi-CAST / Reference Assignment
H3-R4 Manga Style Direct
H3-R5 Few-frame / Video Candidate
PV-R1 3D Still Blockout
PV-R2 3D mapping
```

。

---

# 20. Future Experiment A
## 最重要

同じ入力:

```text
Rough:
2人物white dummy

CAST:
Alice ref
Bob ref

Prompt:
Alice left foreground
Bob right background
black-and-white manga
```

比較:

```text
A. H3 Still
B. H3 → Illustrious
C. Current Illustrious Regional
```

評価:

```text
identity
position
depth
manga style
user effort
seed/candidate count
runtime
VRAM
```

。

---

# 21. Future Experiment B

比較:

```text
source only
source + Alice
source + Alice + Bob
source + Alice + Bob + style ref
```

。

参照枚数増加とambiguityの境界を測る。

---

# 22. Future Experiment C

同じH3 candidateから:

```text
RGB
Depth
Edge
RGB + Depth
```

をIllustriousへ。

最小guideで十分なものを採用。

---

# 23. Future Experiment D

比較:

```text
Illustrious seed 8枚
vs
H3 few-frame packet
```

測る:

```text
usable composition count
usable pose count
time
review burden
```

。

---

# 24. Cost Metric

```text
Prompt tuning cost
Seed search cost
2D rough drawing cost
H3 generation cost
reference preparation cost
3D blocking cost
review cost
Illustrious re-bake cost
```

で比較。

---

# 25. Do Not Change Current Schema Yet

現行v1へ:

```text
h3_reference_slots
previs
video
world_position
camera_matrix
```

を追加しない。

初期研究は:

```text
sidecar
derived execution plan
runtime mapping
```

。

---

# 26. When This Plan Becomes Active

Current Cardが明示的に:

```text
Activate FUTURE_TEGAKI_MANGA_UI_PREVIS_VIDEO_ARCHITECTURE_PLAN_v2
```

または同等宣言を行った時だけActive Planningへ。

それまでは:

```text
Direction Reference
not Implementation Instruction
```

。

---

# 27. Short Handoff Summary for Future AI

将来目標:

```text
ComfyUI runtimeは残す
Node Graphは通常ユーザーへ要求しない
```

。

RookieUIはSidebar / workflow translationのPrior Art。

第一候補は独立Tegaki Manga Sidebar。

生成Routeは:

```text
Illustrious Direct
H3 Still
H3 Video
H3 → Illustrious
3D / Blocking
```

を共通Authoring Dataから選べる。

H3 Still / Reference Editはv2で研究優先度を上げ、3Dより先に検証する。

Rough GuideはIllustrious / H3 I2I / H3 Reference Editへ共用。

Comic Visual FrameはSceneと独立し、最終枠線はdeterministic renderer。

最重要:

```text
Future architecture must not make current authoring harder.
```

---

# 28. Final Rule

```text
Destination is visible.
Implementation is gated.
```

現在Agentへ渡すべき将来情報は:

```text
Authoring ContractをBackend-independentに保つ
Rough Guideをroute-neutral assetとして扱う
H3 Stillを3Dより先の研究候補として予約する
```

まで。

詳細機能を先取りしない。
