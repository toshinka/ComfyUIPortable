# Tegaki ComfyUI Manga Authoring System
## 中間構想計画書 — Semantic Region / Cast / Panel / Scene / Preset Architecture

作成日: 2026-09-05  
位置づけ: 長期構想の中間まとめ / 非拘束的計画書  
対象: `D:\GitHub\tegaki\ComfyUIPortable`

---

# 0. この計画書の位置づけ

本書は、現在進行中の Regional Prompt / Couple / Character / Panel Layout / ControlNet 研究を踏まえた、**「最終的に漫画制作ツールとしてどういう姿を目指すか」** の中間整理です。

これは実装指示書ではありません。現在の研究結果によって、Backend、UI構成、Scene / SubScene の名称、Preset形式、Character管理方式、Regional LoRA、ControlNet統合方式などは今後変わる可能性があります。

したがって本書は、将来の設計判断を縛る仕様書ではなく、現時点で見えている制作思想とユーザー作業フローを保存する計画メモとして扱います。

---

# 1. 最終的に作りたいもの

目標は単なる「漫画っぽい画像生成Workflow」ではありません。

ユーザーが、

```text
誰が
どのコマに
どの場面で
どの位置に
どういう関係で
何をしているか
```

を分解して指定し、それをAI生成へ渡せる漫画制作システムを目指します。

生成AIに対する制御軸は概ね次のように分離します。

```text
Global / Style
Character Identity
Panel / Scene Content
Semantic Region
Character Placement
Panel Geometry
ControlNet
LoRA
Regional Backend
```

すべてを一つの巨大Promptへ押し込まないことを基本方針とします。

---

# 2. 基本思想

## 2.1 Character / Scene / Panelを分離する

最終的には以下を別概念として扱います。

```text
Character
= 誰か

Scene
= 何が起きているか

Panel
= 漫画上で見えるコマ枠

Character Region
= その人物がどこにいるか

Scene Region
= その出来事がどこで起きるか
```

## 2.2 Panelは最小の意味単位とは限らない

通常は `1 Panel = 1 Scene` で十分です。

ただし複雑な例では、

```text
1 Panel
├ SubScene A
└ SubScene B
```

のような状態があり得ます。

例:

```text
同じ1コマの左側:
AliceとBobが喧嘩してそっぽを向いている

同じ1コマの右側:
AliceとBobが握手している
```

見た目は1コマですが、内部の意味単位は2つです。

したがって、Visible Panel Count と Internal Semantic Scene Count は一致しない可能性があります。

例:

```text
Visible Panels = 4

Panel 1 = 2 Scenes
Panel 2 = 1 Scene
Panel 3 = 1 Scene
Panel 4 = 2 Scenes

Internal Scenes = 6
```

---

# 3. Simple First / Progressive Disclosure

重要なUI方針として、**単純な漫画は単純なまま作れる**ことを優先します。

SubSceneや高度なRegional設定を最初から常時表示しません。

## 3.1 Simple Panel

通常はPanelだけで完結できます。

### 背景のみ

```text
Panel Prompt
```

### 単一キャラクター

```text
Panel Prompt
+
Alice
```

### 複数キャラクターだが単純な演技

```text
Panel Prompt:
Alice and Bob talking

Characters:
Alice
Bob
```

この場合はSubScene不要です。

## 3.2 複雑なPanelだけ拡張する

ユーザーが「このコマだけ複雑だ」となった時だけ、`+ Split Scene` / `Advanced Scene` / `SubScene` 等の操作を使います。

すると、

```text
Panel 1
├ Root Scene / Shared Prompt
├ SubScene A
└ SubScene B
```

へ展開します。

## 3.3 Simple / Advancedを別システムにしない

内部データ形式はできるだけ共通化します。

```text
Simple Panel
= Root Sceneのみ

Advanced Panel
= Root Scene + SubScenes
```

表示だけ段階的に複雑化します。

---

# 4. Character Master

Characterはコマごとに毎回再定義しません。Character Masterで一度定義します。

例:

```text
Alice

ID:
char_alice

Base Prompt:
1girl, blonde twin tails, blue eyes, school uniform

Negative Prompt:
...

LoRA Plan:
...
```

## 4.1 Character Masterと出演情報を分離

Character Master は「Aliceとは誰か」、Panel / Scene Binding は「Aliceがこの場面で何をするか」を表します。

例:

```text
Alice Master
= blonde twin tails, blue eyes, school uniform
```

Panel 1:

```text
smiling, talking to Bob
```

Panel 2:

```text
watering flowers
```

Panel 4:

```text
angry, looking away from Bob
```

## 4.2 同じCharacterが複数コマに出演する

```text
Panel 1:
Alice + Bob

Panel 2:
Alice

Panel 3:
Carol

Panel 4:
Alice + Bob
```

このような再出演を自然に扱えることを重要な能力とします。

## 4.3 同じCharacterが同一Panel内に複数回現れる可能性

高度なSubSceneでは、

```text
Alice Master
├ Alice Appearance in SubScene A
└ Alice Appearance in SubScene B
```

のように、同じCharacter Masterから複数のAppearance / Instanceを派生させる必要があります。

---

# 5. Scene / SubScene

仮称として `Scene` を使用します。将来的には `Scene` / `SubScene` / `Semantic Scene` / `Semantic Region` などの名称を再検討して構いません。

## 5.1 Sceneの役割

Sceneは「その場所で何が起きているか」を定義します。

例:

```text
Scene:
school classroom, two students talking
```

または:

```text
Scene:
Alice watering flowers in the garden
```

## 5.2 SceneとCharacterの責任分担

Scene:

```text
教室
会話
夕方
机
窓
```

Character:

```text
Alice
blonde hair
smiling
left side
```

というように役割を分離します。

---

# 6. Panel Layout

Panel LayoutはSceneとは別物です。

```text
Panel Layout
= 漫画として見える物理的なコマ枠
```

主に Panel Polygon / Shared Vertices / Panel Split / ControlNet Layout Guide を担当します。

## 6.1 Hard Geometry / Soft Semantic Geometry

### Hard Geometry

```text
Panel Polygon
ControlNet guide
```

### Soft Semantic Geometry

```text
Scene Region
Character Region
```

Semantic Regionは重なって構いません。Panel Geometryは基本的に平面分割として整合性を保ちます。

---

# 7. Character Placement

Character Masterで「誰か」を定義し、Panel / Sceneで「何をするか」を決め、最後にCharacter Placementで「どこにいるか」を決めます。

例:

```text
Panel 1

Alice:
left

Bob:
right
```

Semantic Regionは重なって構いません。Interactionを妨げないためです。

---

# 8. ControlNetの役割

ControlNetは最初から全制御を担うものではなく、**Semantic Promptだけでは位置関係が弱い場合の幾何補助**として扱います。

研究順としては、

```text
Prompt Separation
→ Position Binding
→ 必要ならControlNet Assist
→ Manga Panel Integration
```

を基本とします。

## 8.1 Panel Layout ControlNet

最終的には漫画のコマ割りを誘導する用途。

## 8.2 Character / Scene Layout Assist

Semantic Regionだけで位置誘導が弱い場合には、Character Region / Scene Region から簡易ControlNet Guideを生成することも将来候補です。

---

# 9. ユーザーから見た標準作業フロー

最終的な標準導線の叩き台:

```text
1. Global / Project
2. Cast
3. Panel Count / Page Plan
4. Panel Content
5. Panel Layout
6. Character Placement
7. 必要なPanelだけSubScene化
8. Generate
```

---

# 10. Global / Project

最初に「これは漫画」「モノクロ」「基本画風」等を決めます。ただし普段はPresetのままでもよい。

最終UIでは `Global Settings ▸` のように折り畳み可能でも構いません。

---

# 11. Cast

登場キャラクターを定義します。

```text
Alice
Bob
Carol
```

この時点ではまだどのコマに出るか決めなくてもよい。

---

# 12. Panel Count / Page Plan

例:

```text
4 Panels
```

を選択。すると4つのPanel Cardが用意されます。

---

# 13. Panel Cards

各Panel Cardで Characters / Scene / Action / Background / Acting / Negative 等を編集します。

例:

```text
Panel 1
Characters:
Alice, Bob

Scene:
classroom

Acting:
talking closely
```

---

# 14. Panel Layout

Panel Cardの意味情報とは独立して、漫画上の配置を決めます。

例:

```text
Panel 1 → top wide
Panel 2 → bottom left
Panel 3 → bottom right upper
Panel 4 → bottom right lower
```

Panelの内容はLayout変更で消えません。

---

# 15. Character Placement

Panelを選択すると、そのPanelに出演するCharacterだけ位置編集できるようにします。

```text
Current Panel: 1

Alice Region
Bob Region
```

他PanelのCharacter Regionは通常隠します。

---

# 16. SubSceneへの拡張

通常のPanelで表現できない時だけ `+ Split Scene` を使用します。

例:

```text
Panel 1

Shared:
classroom

SubScene A:
Alice and Bob arguing

SubScene B:
Alice and Bob shaking hands
```

それぞれにCharacter Placementを持てます。

---

# 17. ComfyUI上での暫定UI方針

専用GUIを作る前は、ComfyUI上でユーザーが触る部分だけを一本道にします。

```text
GLOBAL
→ CAST
→ PAGE / PANEL
→ PANEL LAYOUT
→ CHARACTER STAGING
→ GENERATE
```

## 17.1 Internal Engineは離す

下側または右側へ、Compiler / Bridge / Mask Builder / Regional Backend / ControlNet / KSampler / VAE / Debug をまとめます。

ユーザーが触る必要のないNodeは `Locked` / `DO NOT TOUCH` / `INTERNAL` 等として整理します。

---

# 18. 最終専用GUI

ComfyUI上の研究Workflowが安定してから、専用GUI / Skinを検討します。

候補構成:

```text
Project
Characters
Panels
Scenes
Layout
Staging
Control
Generate
```

ただし実際のUIはより簡素化して構いません。

---

# 19. Preset / Library 構想

これは長期構想です。

ある程度システムが完成した後、制作物の統一性と作品切替を容易にするため、Preset / Library機能を持たせる案があります。

## 19.1 Character Preset

保存対象例:

```text
Character ID
Name
Base Prompt
Negative Prompt
LoRA Plan
Metadata
Optional Costume
Optional Style Notes
```

例:

```text
Alice.school_uniform
Alice.casual
Bob.default
```

## 19.2 Scene Preset

Sceneの再利用。

例:

```text
school_classroom_day
rooftop_sunset
garden_watering
friendly_conversation
argument_scene
```

保存対象候補:

```text
Scene Prompt
Background
Acting template
Character slots
Semantic Region defaults
Control hints
```

## 19.3 Panel / Layout Preset

例:

```text
3_basic
4_grid
4_dynamic
5_action
dialogue_page
```

Panel Geometryを再利用。

## 19.4 Page Preset

Character / Scene / Panel Layout等を統合した、ページ全体のPreset。

例:

```text
School Manga Page Template

Global
Cast references
Panel count
Panel cards
Scene definitions
Panel Layout
Character placements
Control settings
```

## 19.5 Project Preset

より大きな単位では、作品単位のProject Profileも考えられます。

```text
作品A
├ Global Style
├ Character Library
├ Scene Library
├ Layout Library
└ Default Generation Settings
```

作品を切り替えることで、作品A / 作品B / 作品C を混在させず管理できます。

---

# 20. Export / Import / Delete

各Preset / Library Itemについて、将来的に以下を持たせる案があります。

```text
Export
Import
Duplicate
Rename
Delete
```

## 20.1 Export

外部JSON / Package等へ書き出し。

用途:

```text
バックアップ
別PC移行
他ユーザーとの共有
作品アーカイブ
```

## 20.2 Import

Character / Scene / Page / Project Presetを読み込み。

Conflict時:

```text
Keep Existing
Replace
Import as Copy
```

等を将来検討。

## 20.3 Delete

参照中Presetを消す場合はFail-Closed。

例:

```text
Alice preset is referenced by 12 scenes.
Delete blocked.
```

または参照一覧を表示。

---

# 21. Presetの重要な原則

Presetは生成画像を固定するものではありません。

目的は、

```text
作品の統一性
設定再利用
制作速度
作品切替
```

です。

---

# 22. Character PresetとCharacter Instanceを分離

Preset は「Aliceとは誰か」、Instance は「このページのこのSceneにいるAlice」を表します。

Presetを書き換えた時に、既存Pageへどう反映するかは将来重要な設計課題になります。

候補:

```text
Linked
Snapshot
Update manually
```

など。

---

# 23. Page PresetとProject Presetの違い

### Page Preset

```text
1ページ分の構造テンプレ
```

### Project Preset

```text
作品全体の世界観・キャスト・スタイル
```

とします。

---

# 24. 作品の統一性

Preset / Libraryが有効になると、

```text
毎ページ同じAlice
毎ページ同じ基本Style
毎ページ同じ学校背景
```

を再利用しやすくなります。

これは漫画制作で非常に大きな利点があります。

---

# 25. 将来の制作イメージ

例:

```text
Project:
School Story

Characters:
Alice
Bob
Carol

Scenes:
Classroom
Hallway
Rooftop
Garden

Layouts:
3_basic
4_dialogue
5_action
```

新規ページ作成:

```text
Page Preset:
4_dialogue

Cast:
Alice + Bob

Panel 1:
Classroom / conversation

Panel 2:
Alice / hallway

Panel 3:
Bob / rooftop

Panel 4:
Alice + Bob / garden
```

必要なPanelだけSubScene化。

---

# 26. Regional Backendとの独立性

Character / Scene / Panel / Presetのデータは、できるだけRegional Backendから独立させます。

Backend候補:

```text
Core Masked Conditioning
Impact RegionalSampler
DenseDiffusion
Omost
Future RLL
```

Backendを変更しても、Character / Scene / Pageデータを再利用できることを目標にします。

---

# 27. LoRAとの関係

```text
Global LoRA
= ページ / 作品全体

Character LoRA
= Character Master

Scene LoRA
= 将来候補

Regional LoRA
= 将来のRLL等
```

Preset LibraryはこれらのPlanを保存できますが、実際の適用方式はBackendと分離します。

---

# 28. 長期ロードマップ概念

現時点の能力獲得順の概念:

```text
A. Single Character Placement
B. Two Character Separation
C. Same-Scene Interaction
D. Recurrent Cast Across Panels
E. Scene / SubScene
F. Optional ControlNet Assist
G. Manga Panel Reintegration
H. Production Authoring UX
I. Preset / Library
J. Dedicated GUI / Skin
```

---

# 29. Preset / Libraryは後段

Preset機能は魅力的ですが、先に保存すべきデータ構造自体が安定する必要があります。

したがって、Character / Scene / Panel / Binding Contract が固まってから着手します。

---

# 30. 現時点で固定しないもの

以下はまだ固定しません。

```text
Scene / SubSceneの正式名称
Presetファイル形式
Page Preset schema
Project format
Preset保存場所
Database使用有無
専用GUI framework
Regional Backend
ControlNet構成
Regional LoRA方式
```

---

# 31. 現時点で比較的強く維持したい原則

```text
Character MasterとAppearanceを分離する
Panel GeometryとSemantic Regionを分離する
Simple Panelを最初から複雑にしない
必要なPanelだけSubScene化する
Semantic Regionは重なり可能
通常3〜5コマ
最大6はcapacity目安
Regional BackendをデータContractから分離する
ComfyUI上ではUser NodesとInternal Nodesを分離する
専用GUIはBackend / Contract安定後
```

---

# 32. 最終イメージ

ユーザーは最終的に、

```text
作品を選ぶ
↓
Characterを選ぶ
↓
Panelを作る
↓
各Panelの内容を書く
↓
Panelを配置する
↓
Characterを配置する
↓
必要なPanelだけSubScene化
↓
Generate
```

という作業を行います。

必要に応じて、

```text
Character Preset
Scene Preset
Panel Preset
Page Preset
Project Preset
```

を再利用できます。

---

# 33. 本計画書の役割

今後の開発で迷った際、

```text
この機能は誰のためのものか
ユーザーはいつ触るのか
Panel / Scene / Characterのどこへ属するのか
Simple workflowを壊していないか
Backend固有機能を上位Contractへ漏らしていないか
```

を確認するための中間基準とします。

---

# 34. 中間結論

現在の方向性は、

```text
「漫画生成Workflowを作る」
```

から、

```text
「漫画制作に必要な意味・人物・配置・構図を
別々に制御できるAuthoring Systemを作る」
```

方向へ変化しています。

これは望ましい変化です。

最終的な強みは、単に漫画らしい画像を出すことではなく、

```text
Character
Scene
Panel
Position
Relation
Style
```

を再利用可能な単位として分離し、必要に応じて組み合わせられることにあります。

Preset / Library構想はその延長線上にあり、完成後の制作効率・作品の一貫性・複数作品の切替に大きく寄与する可能性があります。

ただし今はまだ長期構想です。

今後の検証結果を受けて、本計画書自体も更新・再構成される前提とします。
