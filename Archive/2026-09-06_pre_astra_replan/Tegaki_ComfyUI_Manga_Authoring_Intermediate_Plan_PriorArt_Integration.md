# Tegaki / ComfyUI 漫画制作システム 中間計画書
## — 既存ツール活用・車輪の再発明回避・Mainline統合方針 —

作成目的:

この計画書は、現在進行中の Tegaki / ComfyUIPortable 漫画制作システムについて、
これまで独自に検証してきた Regional Prompt / ControlNet / Character Staging / SubScene / Interaction / Hyper-SD 等の成果を、
既存ComfyUIツール群の知見と照合し、

```text
何を自作し続けるべきか
何を既存実装へ委譲すべきか
何を設計だけ参考にするべきか
何を比較対象として残すべきか
```

を整理するための中間計画である。

本書は個別Phaseの実装指示書ではない。

---

# 1. 現在の到達点

現行Tegaki / ComfyUIPortableでは、少なくとも以下の研究基盤が成立している。

```text
CAST
Panel
Panel Layout
Character Binding
Character Staging
Character Instance
SubScene
Interaction
Regional Prompt
Regional Mask
ControlNet Layout Assist
Hyper-SD Fast Profile
```

Regional系については、単純なPrompt分割だけではなく、

```text
Prompt Separation
→ Character Presence
→ Character Position
→ Scale
→ Pose
→ Interaction
```

という順で研究を進めてきた。

これまでの結果から、役割分担は概ね以下へ収束している。

```text
Text / Prompt
→ Identity
→ Appearance
→ Acting
→ Semantic relation

Regional Mask / Impact
→ Promptの局所化
→ Character / Sceneの意味分離

ControlNet / Guide
→ Position
→ Scale
→ Pose
→ Rough composition

Panel Geometry
→ Manga frame / page topology

SubScene
→ 1 visible Panel 内の複数独立イベント
```

この上位構造は漫画制作固有であり、今後もTegaki側の中核として保持する。

---

# 2. 基本方針

今後の設計原則を以下とする。

```text
上位の漫画意味構造は自作する
下位の汎用画像生成機能は既存実装を最大限使う
```

具体的には:

```text
Tegakiが持つ:
CAST
Panel
Scene
SubScene
Character Instance
Interaction
Staging
Authoring State
Compiler

既存ComfyUIへ委譲可能:
Regional Prompt execution
Conditioning mask
ControlNet application
Mask editor
Pose editor
IPAdapter regional application
Sampler details
Scheduler details
```

目的はCustom Node数を増やすことではなく、
Tegaki固有の「漫画Authoring Compiler」を薄く保つことである。

---

# 3. Architecture原則

理想的な長期構造:

```text
MANGA_AUTHORING_DATA
        │
        ▼
Semantic Compiler
        │
        ├─ CAST / Character Instance
        ├─ Panel / Scene / SubScene
        ├─ Staging
        ├─ Interaction
        └─ Layout
        │
        ▼
Execution Plan
        │
        ├─ Prompt
        ├─ Mask
        ├─ Guide
        ├─ Control
        └─ Backend Options
        │
        ▼
Backend Adapter
        │
        ├─ Impact RegionalSampler
        ├─ Inspire RegionalPromptSimple
        ├─ Advanced-ControlNet
        ├─ Attention Couple
        └─ Future Backend
```

重要:

```text
Authoring DataはBackendを知らない
```

これを恒久原則とする。

---

# 4. 自作を維持すべき領域

以下は既製品では代替しにくいためTegakiのCoreとする。

## 4.1 CAST

```text
Character Master
Stable Character ID
Base Prompt
Negative Prompt
LoRA Plan
Metadata
```

---

## 4.2 Character Instance

同じMaster Characterを複数のPanel / SubSceneへ再利用する。

例:

```text
Alice Master

P1 Alice instance
P2 Alice instance
P4 Alice instance

SubScene A Alice instance
SubScene B Alice instance
```

---

## 4.3 Panel / Scene / SubScene

特に:

```text
Visible Panel Count
≠
Semantic Scene Count
```

を扱える構造は漫画制作固有である。

---

## 4.4 Progressive Disclosure

通常Panelでは:

```text
Scene Prompt
Characters
Staging
```

だけ。

必要なPanelだけ:

```text
+ Advanced Scene
→ SubScene
```

を開く。

これは長期UI原則として維持。

---

## 4.5 Character AttendanceとStagingの分離

```text
CAST exists
Panel attendance
Character instance
Character staging
```

を独立概念として保持する。

---

## 4.6 Interaction

```text
handshake
look-away
facing
holding object
fight
```

などはCharacter Instance間のsemantic relationとして保持。

ControlNetやPromptに直接埋め込むだけの構造にはしない。

---

# 5. 自作を減らすべき領域

以下は既存実装で十分な可能性が高く、
今後の比較を経てTegaki独自コードを減らす候補である。

```text
Regional Prompt wrapper
ControlNet metadata propagation
Mask application
Mask editing
Pose editing
Regional IPAdapter
Regional CFG
Regional Seed
Sampler Provider
```

---

# 6. 最優先調査対象 — Inspire Pack Regional Prompt Simple

対象:

```text
ComfyUI-Inspire-Pack
RegionalPromptSimple
RegionalPromptColorMask
RegionalConditioningSimple
RegionalConditioningColorMask
Regional IPAdapter
```

## 6.1 注目点

RegionalPromptSimpleは独自Samplerを再発明していない。

概念:

```text
BASIC_PIPE
+
MASK
+
Prompt
↓
KSamplerAdvancedProvider
↓
Impact RegionalPrompt
```

である。

これはTegakiが今後目指す:

```text
Manga Semantic Compiler
↓
Mask + Prompt
↓
Existing Regional Backend
```

と極めて相性が良い。

---

## 6.2 ControlNet propagation

Inspire PackはPrompt再Encode時にControl metadataが失われる問題へ、

```text
controlnet_in_pipe
```

で対応している。

既存Positive Conditioningから:

```text
control
control_apply_to_uncond
```

を新Positiveへ引き継ぐ。

これはTegakiで独自研究してきた:

```text
BASE_ONLY
shared_global
per_region_hint
```

との直接比較価値が高い。

---

## 6.3 採用判断

将来比較:

```text
Tegaki Current Adapter
vs
Inspire RegionalPromptSimple
```

見るもの:

```text
Character Presence
Prompt Separation
ControlNet inheritance
Mask behavior
Sampler behavior
Runtime
Schema stability
Maintenance cost
```

結果が同等以上なら:

```text
Tegaki Adapterを薄くする
```

方向を優先。

---

# 7. Color Mask方式の活用

Inspire Packには:

```text
RegionalPromptColorMask
```

が存在する。

一枚のRGB画像から指定色をMaskへ変換できる。

## 7.1 向いている用途

```text
Panel
SubScene
Page Layout
```

のような「基本的に一画素一所属」の領域。

例:

```text
Red   = Panel 1
Blue  = Panel 2
Green = Panel 3
Yellow= Panel 4
```

あるいは:

```text
Red  = SubScene A
Blue = SubScene B
```

---

## 7.2 向かない用途

Character / Interactionはoverlap可能なので、
一枚のIndexed RGB mapだけに統合しない。

推奨二層:

```text
Panel / SubScene
→ Indexed Color Map

Character / Interaction
→ independent overlapping masks
```

---

# 8. Advanced-ControlNet

対象:

```text
ComfyUI-Advanced-ControlNet
```

注目機能:

```text
ControlNet effect mask
start / end
strength scheduling
timestep control
mask-weighted control
```

---

## 8.1 Tegakiとの関係

現在Tegakiでは:

```text
Character staging
→ Auto Guide
→ Character-specific ControlNet
```

を独自に研究している。

今後:

```text
Tegaki per-region CN
vs
Advanced-ControlNet masked CN
```

を比較する。

---

## 8.2 採用候補

もしAdvanced-ControlNetで:

```text
Alice Mask
Bob Mask
SubScene Mask
```

ごとに十分な制御が可能なら、
Tegaki独自ControlNet propagation codeを削減する。

---

# 9. EasyUseAnima Regional Prompt Studio

対象:

```text
ComfyUI-EasyUseAnima
Regional Prompt Studio
```

Backendそのものより、
UI / State設計を参考にする。

---

## 9.1 重要な設計

一つのNodeに:

```text
multiple prompts
multiple masks
mask assignment
canvas size
settings
```

を持つ。

内部状態:

```text
regional_config JSON
```

として保持。

下流へ大量のsocketを増やさず:

```text
typed structured data
```

として渡す。

---

## 9.2 Tegakiへの応用

長期的には:

```text
MANGA_AUTHORING_DATA
```

を一つのstructured stateとして保持する。

例:

```json
{
  "cast": [],
  "panels": [],
  "layout": {},
  "staging": {},
  "subscenes": [],
  "interactions": []
}
```

Compilerが必要な:

```text
CAST_SPEC
REGION_SPEC
PAGE_COMPILE_PLAN
CONTROL_PLAN
```

へ変換する。

---

# 10. Omostから借りる設計思想

対象:

```text
ComfyUI_omost
```

重要なのはAlgorithmそのものではなく:

```text
Canvas Conditioning
→ multiple backend
```

という設計。

Tegakiも将来的に:

```text
MANGA_AUTHORING_DATA
→ Impact
→ Inspire
→ Attention Couple
→ Future Backend
```

を選べる構造へする。

---

# 11. Attention Couple

対象:

```text
Prompt Control
Attention Couple
```

位置づけ:

```text
Reference Regional:
Impact RegionalSampler

Fast Regional Candidate:
Attention Couple
```

Attention Coupleは高速化余地がある一方、
latent全体のdiffusionが続くため、
mask外へのsemantic leakが完全に防げるとは限らない。

したがってReference backendに即置換しない。

Hyper12と同様:

```text
Fast Preview Backend
```

候補として評価する。

---

# 12. Pose Editorの車輪を再発明しない

現在のTegaki mannequinは:

```text
Auto Pose Guide
```

として有効。

しかしユーザーが:

```text
腕
脚
頭
骨格
```

を直接編集する本格Pose EditorをTegakiで自作しない。

---

## 12.1 推奨構造

```text
通常:
Auto Mannequin

必要:
Edit Pose
↓
Existing OpenPose Editor
↓
Pose Image
↓
Character Instance
```

対象候補:

```text
ComfyUI OpenPose Editor
3D OpenPose Editor
```

---

## 12.2 Tegaki側の責務

TegakiはPose Editorを作るのではなく:

```text
Character Instance
↔ Pose Asset
```

の紐付けを管理する。

---

# 13. Mask Editorも自作を急がない

Impact Pack:

```text
PreviewBridge
Clipspace MaskEditor
```

を利用可能。

初期運用:

```text
Auto-generated mask
↓
必要なら Edit Mask
↓
Existing MaskEditor
```

専用漫画GUIを作る段階でのみ
Tegaki独自Canvasへ統合。

---

# 14. Krita AI Diffusion RegionsからのUX知見

注目:

```text
Root Prompt
+
Regional Prompt
+
Layer / Layer Group
+
Control Layer
```

RegionはLayerのalpha領域へ紐付く。

長期Tegaki GUIへの参考:

```text
Aliceを選択
↓
Alice instance
Prompt
Region
Pose
Control
```

を同期して選択する。

---

# 15. Krea2 Regional BuilderからのUX知見

BackendはKrea2専用なので採用しない。

UI参考:

```text
Rectangle
Freehand Lasso
Vertex Edit
Prompt
Per-Region LoRA
Overlap Priority
Grid / Snap
Background Reference
Pop-out Canvas
Hidden serialized state
```

Tegakiで参考にするが、
overlap priorityをそのままwinner-take-allにはしない。

---

# 16. 長期Authoring UI構造

最終的なユーザー作業順:

```text
01 Global / Project
02 CAST
03 Panel Count
04 Panel Content
05 Panel Layout
06 Character Staging
07 Advanced SubScene if needed
08 Interaction if needed
09 Generate
```

---

# 17. CAST UI

```text
[Alice][Bob][Carol][+]
```

Selected Character:

```text
Name
Base Prompt
Negative Prompt
LoRA
Reference Image
Pose Asset
```

---

# 18. Panel UI

```text
[P1][P2][P3][P4]
```

Selected Panel:

```text
Scene Prompt
Background Prompt
Attendance
Acting Override
Camera Distance
```

---

# 19. Character Staging UI

Selected Panel内の出演Characterだけ表示。

```text
Alice
Bob
```

Canvas:

```text
drag
resize
overlap
shot type
pose preset
```

---

# 20. SubScene UI

通常非表示。

```text
+ Advanced Scene
```

選択時だけ:

```text
SubScene A
SubScene B
```

を編集。

---

# 21. Interaction UI

必要時のみ:

```text
Interaction Type
Target Character Instance
```

例:

```text
Alice @ sub_b
handshake
Bob @ sub_b
```

---

# 22. Backend非依存Persistent Contract

Persistent Authoring Dataへ以下を入れない。

```text
Impact RegionalPrompt object
RegionalSampler object
Advanced-ControlNet object
Sampler Provider object
ComfyUI link id
```

Persistent側には:

```text
Prompt
Mask geometry
Guide intent
Control intent
Instance relation
```

だけ保持。

---

# 23. Backend Adapter層

例:

```text
ImpactBackendAdapter
InspireRegionalBackendAdapter
AttentionCoupleBackendAdapter
```

同じAuthoring Dataを変換。

---

# 24. Adopt / Adapt / Reference分類

## ADOPT候補

そのまま使う可能性が高い:

```text
Impact RegionalSampler
Inspire RegionalPromptSimple
Advanced-ControlNet
OpenPose Editor
Impact MaskEditor
```

---

## ADAPT候補

設計を借りる:

```text
EasyUseAnima Regional Studio
Omost Canvas Conditioning
Krea2 Regional Builder UI
Krita AI Diffusion Region UX
```

---

## REFERENCE候補

比較対象として残す:

```text
Attention Couple
DenseDiffusion
Regional Conditioning
```

---

# 25. External Prior-Art Audit Gate

今後の主要新機能では、
実装前に必ず:

```text
既存ComfyUI nodeで同機能がないか
```

を調査する。

Gate:

```text
ADOPT
ADAPT
REFERENCE
BUILD
```

のどれかを決めてから実装。

---

# 26. Build判断基準

自作してよいのは:

```text
漫画固有
既存実装と契約が合わない
既存依存が不安定
UX上不可欠
```

の場合。

---

# 27. Buildを避ける基準

以下は原則既存利用:

```text
Sampler
Scheduler
ControlNet application
OpenPose editor
Mask editor
IPAdapter application
Regional CFG
Seed variation
```

---

# 28. Research WorkflowとProduction Workflowの分離

Research:

```text
fixed
deterministic
1 Workflow = 1 hypothesis
fixed seed
fixed prompt
fixed geometry
```

Production:

```text
dynamic
user editable
tabs / selected item
progressive disclosure
```

---

# 29. Verification Evidence Pack

各重要機能:

```text
Workflow
Final Output
Contact Sheet
Diagnostic JSON
```

を残す。

---

# 30. Validation Hierarchy

```text
LEVEL 1
schema / mask / runtime

LEVEL 2
AI visual review

LEVEL 3
human review
```

ユーザーを通常テストランナーにしない。

---

# 31. Hyper12の位置づけ

現状:

```text
Reference:
Native20

Operational:
Hyper12
```

ただし重要Backend研究ではNative20 Referenceを残す。

Fast profileは:

```text
Preview
Draft
UI iteration
candidate search
```

で優先利用可能。

---

# 32. ControlNetの位置づけ

```text
Prompt / Regional
→ semantic separation

ControlNet
→ geometric assist
```

を原則とする。

ControlNetだけでIdentityを担わせない。

---

# 33. Auto GuideとManual Guide

将来:

```text
Auto Mannequin
User Rough Sketch
OpenPose
Lineart
```

を選択可能にする。

---

# 34. Panel Layout ControlとCharacter Controlを分離

```text
Panel Layout Control
→ Manga frame geometry

Character Control
→ position / scale / pose
```

内部契約を分離。

必要なら生成Guide画像上では合成可能。

---

# 35. Preset / Libraryは後段

Backend / Authoring Contract安定後:

```text
Character Preset
Scene Preset
Page Preset
Project Preset
```

を追加。

---

# 36. Preset操作

将来:

```text
Save
Load
Duplicate
Rename
Delete
Export
Import
```

---

# 37. 専用GUIはさらに後段

ComfyUI上で:

```text
backend
contract
interaction
subscene
```

を安定させてから、
専用GUI / skinへ進む。

---

# 38. 専用GUIで参考にするもの

```text
Krita AI Diffusion
Krea2 Regional Builder
EasyUseAnima Regional Studio
OpenPose Editor
```

---

# 39. 今後のロードマップ

## Stage A — Semantic Foundation

```text
CAST
Panel
Character Instance
SubScene
Interaction
```

---

## Stage B — Backend Simplification

```text
Impact vs Inspire
Advanced-ControlNet
MaskEditor
OpenPose Editor
```

---

## Stage C — Mainline Manga Authoring

```text
mixed simple / complex panels
subscene
same-cast instances
interaction
```

---

## Stage D — Fast Backend

```text
Hyper12
Attention Couple
```

---

## Stage E — Production UX

```text
Cast tabs
Panel tabs
Staging canvas
SubScene progressive disclosure
Interaction picker
```

---

## Stage F — Presets / Projects

```text
Character Library
Scene Library
Page Library
Project
```

---

## Stage G — Dedicated GUI

```text
Manga authoring frontend
ComfyUI backend
```

---

# 40. 最重要な設計判断

今後Tegakiは:

```text
「ComfyUIの代替」を作るのではない
```

。

作るものは:

```text
漫画制作の意味構造
```

である。

ComfyUIは:

```text
execution engine
```

として使う。

---

# 41. 最終原則

```text
漫画固有:
自作

汎用生成処理:
既存利用

Backend固有:
Adapterへ隔離

User Authoring Data:
Backend非依存

Research:
固定

Production:
動的

Simple Panel:
Simple

Complex Panel:
Progressive SubScene

Character:
MasterとInstanceを分離

Position:
Promptだけに頼らない

Control:
必要な場所だけ

Pose Editor:
再発明しない

Mask Editor:
再発明しない

Sampler:
再発明しない
```

---

# 42. 中間判断

現状のTegaki方向は大きく間違っていない。

むしろ既存ツール調査によって明確になったのは、

```text
上位Authoring構造はTegaki独自でよい
下位Regional / Control / Pose / Mask機能は
もっと既存実装へ委譲できる
```

という点である。

今後の開発では、

```text
独自機能を追加する
```

より先に、

```text
既存ノードへ置換できる部分を減らす
```

ことも成果として扱う。

最終的に理想なのは、

```text
Tegaki Manga Authoring Compiler
```

が薄く、

```text
ComfyUI ecosystem
```

を下側で交換可能に利用する構造である。
