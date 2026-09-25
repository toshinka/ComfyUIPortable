# H3 VIDEO導入・動画スタジオ化・Illustrious漫画統合・H3 MANGA化 段階的開発計画

更新日: 2026-09-08

## 0. この文書の位置づけ

本書は、`D:\GitHub\tegaki` 配下で進める ComfyUI Portable ベースの制作環境について、

1. MiniMax H3 VIDEO を最小手で実働化する
2. H3 VIDEO を段階的に動画スタジオ化する
3. 既存の Illustrious Manga 制作系を完成させ、共通UIへ統合する
4. 最後に H3 MANGA を独立した研究・制作ラインとして立ち上げる

という長期順序を固定するための上位ロードマップである。

この文書は詳細実装仕様ではない。  
各Phaseの具体的な仕様・実装カード・監査結果は別文書に分離する。

また、AIにプロジェクト全体を毎回再説明しないための「方向性の正本」として使用する。

---

# 1. 全体方針

## 1.1 最初にH3 VIDEOを動かす

MiniMax H3 VIDEOは既に複数の公開GUI、ComfyUI Workflow、Director系ツール、低VRAM対応実装などが存在している。

したがって初手では独自実装を最大化しない。

既に他者が作っているものを調査し、利用可能なOSS・Workflow・GUI構造を可能な限り取り込み、

**「ComfyUIのノードを意識せず、H3をすぐ触って遊べるGUI」**

を最小手で成立させる。

最初から究極の動画制作環境を作らない。

H3界隈そのものの進歩が速いため、自分で早期に再実装するよりも、他者の進展を待って取り込んだ方が安い機能については待つことも許容する。


## 1.2 H3 VIDEOから自然発生的にStudioへ進む

H3 GUIが実働化した後、

- Shot
- Take
- Segment
- Timeline
- Continuity
- 部分再生成
- Asset
- Storyboard
- 簡易編集
- NLE連携

などを段階的に追加する。

Storyboardや3D Previzは、最初から必須機能として巨大実装するのではなく、H3 VIDEO Studioを実際に使う中で必要性が明確になった時点から研究・導入する。

既存ツールで有用なものが公開された場合は積極的に参考・利用する。


## 1.3 Illustrious Mangaは独立して中身を完成させる

既存のIllustrious Manga開発は、

- Scene
- Panel
- Region
- Character
- Workflow
- Manga authoring semantics

など、漫画制作の内部構造を完成させることを優先する。

H3側とUIを統合するために、現在のIllustrious設計を途中で曲げない。

ただし将来的にH3 VIDEO側で構築するGUI shellへ「Mangaタブ」として載せられるよう、過度なUI密結合は避ける。

Illustrious Mangaの完成後、H3 VIDEO側のGUI shellへ統合し、

`[ Manga ] [ Video ]`

のようなタブ型制作環境へ進める。


## 1.4 H3 MANGAは最後に開始する

H3 MANGAは本計画で最も実験性・独自性が高い領域とする。

開始条件は、

- H3 VIDEOが実働している
- H3 VIDEO Studioの基本構造が成立している
- Illustrious Mangaが実働レベルまで完成している
- Manga / Video双方のAsset、Project、Reference、Shot/Panel思想に十分な知見が蓄積している

こと。

H3 MANGAは現在のIllustrious Mangaノード群を直接拡張して作ることを前提としない。

独立した制作モードとして研究し、

- Panel
- Shot
- Storyboard
- Motion
- Dialogue
- Audio
- Continuity

を漫画表現へ再構成する可能性を探る。

必要であれば、H3 MANGAで決めたコマ・構図・人物・演出を静止画化した後、

- Illustrious
- Anima
- 将来の画像モデル

で再描画・仕上げする `Image Finish / Bake` 工程を独立Adapterとして追加する。

これは最後の最後に検討する。


---

# 2. 長期的な制作環境イメージ

初期:

```text
H3 VIDEO GUI
    ↓
ComfyUI
    ↓
MiniMax H3
```

中期:

```text
H3 VIDEO Studio
├─ Generate
├─ Shot / Take
├─ Timeline
├─ Continuity
├─ Asset
├─ Storyboard
└─ Preview / Export
```

Illustrious完成後:

```text
Tegaki / ComfyUI Production UI

[Manga] [Video]

Manga
└─ Illustrious Manga

Video
└─ H3 VIDEO Studio
```

長期:

```text
Tegaki / Production Environment

├─ Illustrious Manga
├─ H3 VIDEO
└─ H3 MANGA
       ↓
   Image Finish / Bake
       ↓
 Illustrious / Anima / Future Image Models
```

UI上の最終的なタブ構成は、H3 MANGA実装時点まで固定しない。

候補:

```text
[ Manga ] [ Video ]
```

Manga内部で、

```text
Illustrious
H3 Manga
```

を切り替える方式。

または、

```text
[ Illustrious Manga ] [ H3 Video ] [ H3 Manga ]
```

の3モード方式。

現段階では決定しない。


---

# 3. ComfyUI Portableとの関係

基本リポジトリ:

```text
D:\GitHub\tegaki
```

既存ComfyUI環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

H3も同じPortable基盤を利用する方向を優先する。

理由:

- 既存モデル・ComfyUI環境を再利用できる
- Portable管理を一つにできる
- GitHub上でManga / Videoを一つの制作プロジェクトとして管理できる
- 将来の共通GUI shell統合が容易
- 重複するComfyUI環境を増やさずに済む

ただし、

**Illustrious MangaとH3 VIDEOの実装コード・計画・進捗管理は分離する。**

「同じrepository・Portable基盤」と「同じsubsystem」は別概念とする。


---

# 4. 想定ディレクトリ方針

既存Illustrious Mangaのcanonical pathを無理に移動しない。

まずH3用領域を追加し、将来の統合余地を確保する。

例:

```text
ComfyUIPortable/
│
├─ h3/
│  ├─ app/
│  ├─ adapters/
│  ├─ workflows/
│  └─ tests/
│
├─ docs/
│  ├─ plans/
│  │  ├─ existing manga plans...
│  │  └─ h3/
│  ├─ reports/
│  │  └─ h3/
│  └─ references/
│     └─ h3/
│
├─ GITHUB_ComfyUI.txt
├─ GITHUB_MANGA.txt
└─ GITHUB_H3.txt
```

既存ファイルを大量移動してから開発を始めることはしない。

ディレクトリ整理は「新しい箱を用意する」程度に留め、必要性が確認されてから再編する。


---

# 5. External AI Entryの分離

将来的には以下の三層を推奨する。

```text
GITHUB_ComfyUI.txt
        │
        ├─ GITHUB_MANGA.txt
        └─ GITHUB_H3.txt
```

## GITHUB_ComfyUI.txt

ComfyUIPortable全体の入口。

役割:

- repository
- current global structure
- Manga entryへの誘導
- H3 entryへの誘導
- 共通ルール

詳細な現在進捗を大量に複製しない。


## GITHUB_MANGA.txt

Illustrious Manga専用のExternal AI Entry。

既存の、

- STATUS
- Astra Manga Master Plan
- Minimal-Hand Manga UX Blueprint
- Asset / Workflow Inventory
- Execution Protocol
- Current Card
- Relevant Report

等への読み順を維持する。


## GITHUB_H3.txt

H3専用のExternal AI Entry。

内容候補:

- Current H3 Phase
- Current Card
- Review Target SHA
- H3 Master Plan
- H3 Architecture
- H3 Reference Inventory
- Relevant report
- Current implementation files

これによりH3開発時にIllustrious Mangaの巨大contextを毎回読ませずに済む。


---

# 6. H3参考実装

既存ツールを「丸ごとの正解」としてコピーしない。

各実装から必要な設計だけを拾う。


## AntaresAlice / h3-webui

参考:

- ComfyUIを隠したWebUI
- Workspace
- History
- Reference管理
- Real-time progress
- Continuation
- Web frontendとComfyUI APIの分離

用途:

H3 GUI初期実装の主要参考。


## ComfyUI-MiniMaxH3-Easy

参考:

- H3生成backend
- workflow簡略化
- low VRAM
- model switching
- Segment processing

用途:

H3生成engine候補。


## Director-WebUI / DirectorDeck

参考:

- Unified Timeline
- Segment Job
- Recipe Resolver
- Continuity
- segment-local failure
- partial regeneration
- model cache reuse
- H3固有で不要なparameterをUIに出さない考え方

用途:

H3 Studio化の主要参考。


## YachiCut

参考:

- TimelineとStoryboardの統合
- 編集中生成
- Take / Accept / Reject思想
- 素材管理
- NLE export
- 将来的な3D Previz方向

用途:

長期的な動画制作環境のUX参考。

公開実装がない限り、コードベースとして前提にしない。


## Chankoa H3 WebUI

参考:

- 一般ユーザー向けフォームUI
- Library
- Recent
- Reference操作
- LoRA操作
- 部分再生成
- Generate中心の簡潔さ

用途:

エンドユーザー向けUX参考。


## Faithful H3

参考:

- comic panel detection
- storyboard
- shot order
- timing
- camera
- action
- dialogue
- sound
- structured JSON

用途:

将来のStoryboard / H3 MANGA研究。


## H3 Prompt Studio

参考:

- Story → Sequence
- Reference Library
- LLMによるSequence分割
- Reference再割当
- JSON repair / retry

用途:

将来のAI制作補助・H3 MANGA研究。


---

# 7. 開発Phase

# Phase H0 — H3導入調査と最小設計

目的:

既存のH3 GUI / Workflow / ComfyUI backendを調査し、最も少ない独自実装でH3 VIDEOを動かす構成を決める。

実施:

- H3 Easy等のbackend確認
- AntaresAlice等のGUI構造確認
- fork / reuse / adapter方針確認
- license確認
- RTX 4070 12GB環境での実用条件整理
- Portable内の配置決定
- 最小H3 Schema決定

重要:

このPhaseでStudioを設計しすぎない。


# Phase H1 — H3 VIDEO Minimum Skin

目的:

まず遊べるものを作る。

最低限:

- Prompt
- Reference
- Model
- Resolution
- Duration
- Steps
- Seed
- LoRA
- Generate
- Preview
- Progress
- Queue
- History
- ComfyUI connection

成功条件:

**ComfyUIノード画面を触らなくてもH3動画を生成できる。**

この時点では既存OSSを最大限利用してよい。


# Phase H2 — H3 VIDEO Practical Skin

H1を実際に使用して、欠けている実用機能を補う。

候補:

- Reference library
- parameter metadata restore
- generation preset
- low VRAM preset
- model auto switching
- error recovery
- workflow version handling
- Take management
- output management

既存H3ツールの進展も再調査する。

既に良い実装が公開された場合は、自前実装より取り込み・適応を優先する。


# Phase H3 — H3 VIDEO Studio

H3 GUIを動画制作環境へ発展させる。

候補:

- Project
- Shot
- Take
- Segment
- Timeline
- partial regeneration
- continuation
- continuity
- asset binding
- shot reorder
- join / export
- Recipe Resolver

ユーザーに、

T2V / I2V / FL2VA / Ref2VA

を毎回直接選ばせるのではなく、素材と制作意図からbackend側が適切なrecipeを導出する方向を研究する。


# Phase H4 — Storyboard / Editing / Previz

H3 Studioを使用して必要性が確認されたものから追加する。

候補:

- Storyboard view
- Storyboard ↔ Timeline
- Shot planning
- camera
- action
- dialogue
- sound
- simple editor
- NLE export
- 3D Previz

3D Previzは必須機能ではない。

他者のツール・研究進展が十分成熟してから取り込むことも許容する。


---

# 8. Illustrious Manga開発ライン

H3 VIDEOがある程度実働した時点で、Illustrious Mangaの完成へ比重を戻す。

Illustrious側ではGUI統合を急がない。

優先:

- Manga authoring core
- Scene
- Visual Panel
- Region
- Character placement
- Workflow reliability
- minimum-hand UX
- browser acceptance
- production stability

H3 VIDEO側のUI shellに将来載せる可能性は考慮するが、H3都合による中途半端な共通化はしない。

完成後にMangaタブとして統合する。


---

# 9. UI統合Phase

H3 VIDEOとIllustrious Mangaが双方実働した後、

共通Production UI化を行う。

第一候補:

```text
[Manga] [Video]
```

共通化候補:

- App shell
- Project selector
- Asset storage
- Character / Reference library
- History
- Generation Job
- Queue
- Settings
- Model path / ComfyUI connection

共通化しない可能性が高いもの:

- Manga Scene semantics
- Manga Region semantics
- H3 Shot semantics
- H3 Timeline runtime
- model-specific workflow
- backend-specific generation recipe

見た目を共通化しても、内部modelを無理に統合しない。


---

# 10. 最終研究Phase — H3 MANGA

H3 VIDEOとIllustrious Mangaが完成・実働した後に開始する。

目的:

H3の動画生成能力を、漫画制作そのものへ応用した独立制作モードを研究する。

候補:

- Page
- Panel
- Shot
- Storyboard
- Character Reference
- motion-aware panel generation
- Dialogue / Audio
- temporal continuity
- panel-to-video
- video-to-panel
- animated comic
- cinematic manga
- 3D Previz connection

H3 MANGAは既存Illustrious Mangaの単なる拡張ではない。

独立subsystemとして設計し、必要な共通情報だけを共有する。


## Image Finish / Bake

H3 MANGAで生成・決定した素材を、

- Illustrious
- Anima
- future image models

へ渡して高品質静止画として仕上げる工程を将来検討する。

例:

```text
H3 Manga
   ↓
Selected Panel / Frame
   ↓
Image Finish Adapter
   ↓
Illustrious / Anima
```

既存Illustrious Manga runtimeへ直接結合することを前提としない。

---

# 11. AI開発運用方針

本プロジェクトでは、最大性能のAIを常時使うことより、

**総トークン消費を抑えながら、必要な場所だけ高性能AIを投入する**

ことを優先する。


## 11.1 LUNA / LUNAMAX — 通常実装担当

基本的な実装作業はLUNA側へまとめて渡す。

担当:

- coding
- directory creation
- dependency setup
- ComfyUI integration
- test
- routine bug fix
- UI implementation
- documentation update

細かい一操作ごとに人間へ確認させない。

代わりに、明確なGoal / Card単位でまとまった作業を渡す。


### 推奨Goal形式

```text
Goal:
H3 Reference入力からGenerateまでを完成させる。

Success:
- referenceを登録できる
- schemaへ変換できる
- ComfyUIへ送信できる
- progressが表示される
- generationが成功する
- failureがUI表示される
- relevant tests pass

Out of scope:
- Timeline
- Storyboard
- Manga
- global UI redesign
```

一度に大きすぎるPhase全体を渡さず、かといってボタン一個単位まで分割しない。


## 11.2 Web ChatGPT — 節目監査

通常の監視は行わない。

GitHubへまとまった実装がpushされた節目で監査する。

基本:

```text
Previous Review SHA
        ↓
Current Review SHA
        ↓
Diff-based audit
```

見るもの:

- architecture violation
- regression
- hidden coupling
- unnecessary complexity
- tests
- phase scope
- documentation consistency

毎回repository全体を最初から読み直さない。


## 11.3 GPT-5.6 Sol — スポット参戦

通常実装より難しいが、全体architecture再検討までは不要な問題に使う。

例:

- difficult bug
- complex refactor
- implementation + design boundary
- performance issue
- test strategy
- code review

常用しない。


## 11.4 Astra — Wild Card / Architecture Specialist

Astraは常勤設計者にしない。

以下のような場合だけ投入する。

- LUNAが同じ問題で複数回失敗
- Schema変更が複数Phaseへ波及
- Manga / H3境界に関わる
- backend abstractionに関わる
- forkか再実装かの重大判断
- architecture由来の性能問題
- Web GPT監査で重大設計問題が発見された
- 次の大Phase開始前に構造レビューが必要

Astraには質問範囲を狭く与える。


---

# 12. Astra Subagent方針

AstraのSubagentは原則としてデフォルト利用しない。

理由:

複数agentが同じrepositoryやcontextを再読すると、並列化による時間短縮以上に総token使用量が増える可能性があるため。

Astraへの基本ルール:

```text
Subagents are not the default.

Do the task yourself unless delegation provides a clear material advantage.

Do not spawn agents merely to:
- re-read the repository,
- monitor another agent repeatedly,
- duplicate review,
- perform routine file inspection,
- re-run already passing checks.

If delegation is useful, use the minimum number of narrowly scoped agents.

Each subagent should receive only the files and context required for its task.

Do not continuously poll or supervise another agent.

Prefer one handoff and one final result inspection.

Optimize for total token consumption, not wall-clock parallelism.
```

Subagentを使う場合でも、

- 役割を明確化
- 読むファイルを限定
- 同じ調査を重複させない
- LUNAの進捗を何度も見に行かせない
- 必要以上に並列化しない

こと。


---

# 13. 実装Card運用

Phaseの中をCardへ分ける。

例:

```text
H3 Phase H1

Card H1-A
ComfyUI connection

Card H1-B
Prompt / Generate

Card H1-C
Reference

Card H1-D
Model / LoRA / Resolution / Seed

Card H1-E
Queue / Progress / History

Gate Review
```

LUNAには原則Card単位で作業を渡す。

関連が強ければ2 Card程度をまとめてもよい。

Card完了ごとに必ずWeb GPT監査する必要はない。

複数CardがまとまったところでGate Reviewを行う。


---

# 14. Phase Gate

各主要Phase終了時に監査する。

```text
LUNA implementation
      ↓
tests
      ↓
commit / push
      ↓
Web GPT audit
      ↓
PASS
      ↓
next Phase
```

問題分類:

### Minor

LUNAへ戻す。

### Medium

Web GPT / Solで分析してLUNAへ戻す。

### Architecture

Astraをスポット投入する。

この階層を崩して最初からAstraへ投げない。


---

# 15. Token節約原則

1. AIへrepository全体を毎回読ませない。
2. External AI Entryから必要文書だけを読む。
3. Current Phase / Current Cardだけを基本contextとする。
4. Reviewはcommit差分中心。
5. LUNAへ細切れ指示を連続発行しない。
6. Goal単位である程度まとめて作らせる。
7. Astraは限定質問。
8. Astra Subagentは原則OFF。
9. 同じ調査を複数AIへ重複して依頼しない。
10. 新アイデアは即実装せず、ROADMAPへ退避する。


---

# 16. Scope分類

新機能や研究対象は以下に分類する。

### NOW

現在のCardに必要。

### NEXT

次Phaseで必要。

### LATER

将来候補。

### RESEARCH

まだ実装判断しない研究対象。

例:

- 3D Previz → RESEARCH
- H3 MANGA → LATER / RESEARCH
- H3 VIDEO minimum skin → NOW
- Timeline → NEXT
- Illustrious Image Finish → LATER


---

# 17. 現在の優先順位

現時点の優先順位は以下。

```text
1. H3 VIDEOを最小手で導入・実働
        ↓
2. H3 VIDEOを使いながらPractical化
        ↓
3. 他者進展を取り込みつつStudio化
        ↓
4. Illustrious Mangaを完成
        ↓
5. Manga / Videoのタブ統合
        ↓
6. H3 MANGA研究・実装
        ↓
7. Image Finish / Bake等の高度統合
```

H3 VIDEOについては、競争して全てを先行実装する必要はない。

他者が解決しているものは使う。

他者が近く解決しそうなものは待つ。

自分にしか必要でない制作workflowや、最終的な漫画・動画統合に時間を使う。


---

# 18. 当面の禁止事項

- 最初からH3 VIDEO Studio全部入りを作らない
- 最初から3D Previzを作らない
- H3 MANGAを先行実装しない
- H3都合でIllustrious Manga architectureを変更しない
- GUIをComfyUI node IDへ直接密結合しない
- 既存OSSを理由なく再実装しない
- ComfyUI本体を不必要にforkしない
- Astraへプロジェクト全体を自由設計させない
- Astra Subagentへ常時監視させない
- AI同士の長大な会話履歴を正本にしない


---

# 19. 開発思想

このプロジェクトでは、

**「既にあるものは使う」**

**「まず動かす」**

**「使ってから必要なものを作る」**

**「他者の進歩を待てるものは待つ」**

**「独自性が必要な部分にだけ開発コストを使う」**

を基本とする。

H3 VIDEOは最速で実働化する入口。

Illustrious Mangaは独自の漫画制作基盤。

H3 MANGAは両者の知見が蓄積した後に挑む最終研究ライン。

AIは常に最大能力を投入するのではなく、

```text
LUNA      = 通常実装
Web GPT   = 節目監査
Sol       = 難所の実装・分析
Astra     = Architecture Wild Card
GitHub    = 共通知識・正本
```

として使い分ける。

最終目的は巨大な計画を最初に完成させることではない。

**最小手で動く制作環境を作り、実際に使いながら段階的に育てること。**
