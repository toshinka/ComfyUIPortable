# H3 GUI導入・動画スタジオ化・漫画制作ツール化 段階的開発計画

## 1. 目的

MiniMax H3をローカル環境で扱いやすくする専用GUIを最初の足場として構築し、そこから段階的に動画制作スタジオ、さらに漫画制作機能を統合した制作ツールへ発展させる。

最初から巨大な統合制作ソフトを作るのではなく、

H3を簡単に使う
→ Shot単位で動画を制作する
→ Timelineで複数Shotを扱う
→ Storyboardや素材管理を統合する
→ Mangaタブを追加する
→ 漫画と動画で共通のProject / Asset / Shot基盤を使う

という順序で育てる。

最終的にはMiniMax H3専用品ではなく、H3、Wan系、FramePack系、将来の動画モデルなどを交換可能な生成バックエンドとして扱える構造を目指す。


## 2. 基本思想

### ComfyUIは生成エンジンとして利用し、通常ユーザーにはノードを見せない

基本構造は以下とする。

制作GUI
↓
Project / Shot Schema
↓
Recipe Resolver
↓
Model Adapter
↓
ComfyUI API
↓
MiniMax H3 / H3 Easy

GUIはComfyUIのノードIDやwidget indexを直接意識しない。

GUIでは、

- Prompt
- Reference
- Character
- Start frame
- End frame
- Duration
- Shot
- Continuity
- LoRA
- Seed

など、人間にとって意味のある概念を扱う。

ComfyUI固有のノード接続やmodel loaderなどはAdapter側へ閉じ込める。


### 生成方式をユーザーに選ばせすぎない

T2V / I2V / FL2VA / Ref2VAなどをすべてユーザーが理解して選ぶUIにはしない。

たとえば、

開始画像あり
＋終了画像あり
→ FL2VA

複数キャラクター参照あり
＋音声参照あり
→ Ref2VA

前Shotから継続
→ Continuity

など、Shotに登録された素材と制作意図からRecipe Resolverが適切な生成方式を推測・決定する。


## 3. 参考にする既存実装

既存ツールをそのままコピーするのではなく、それぞれから優れた設計要素を抽出する。

### AntaresAlice/h3-webui

主に参考にするもの：

- ComfyUIを隠したWebUI構成
- Workspace
- History
- Reference管理
- Real-time progress
- Video continuation
- WebUIとComfyUI APIの境界設計

位置づけ：

最初のH3専用GUIを作るうえで、現時点の主要な実装参考。


### JYE-HC/Director-WebUI / DirectorDeck

主に参考にするもの：

- Unified Timeline
- Segment単位Job
- FL2VA / Ref2VAから具体的Recipeを自動導出する思想
- Segment単位の失敗隔離
- ComfyUI cacheを利用するstable loader設計
- Continuity
- Shotごとの部分再生成
- UIに不要な生成パラメータを出さない思想

位置づけ：

動画スタジオ化の中心参考。


### YachiCut

主に参考にするもの：

- StoryboardとTimelineの同期
- 編集中に素材をその場で生成する発想
- 採用 / 不採用Shotの履歴
- 編集と生成の統合
- NLEへのExport
- CLI / MCPによる外部AIエージェント操作
- 将来的な3D Previzとの接続可能性

位置づけ：

現時点では未公開で内部実装不明。

コード参考ではなく、将来の制作ツール像・UX思想の参考とする。


### ちゃんこあ MiniMax H3 WebUI

主に参考にするもの：

- A1111 / Forge型の一般ユーザー向けフォーム
- Library
- Recent
- Reference並べ替え
- LoRA操作
- 部分再生成
- 「基本はPromptを書いてGenerate」の簡潔さ

位置づけ：

一般ユーザー向けUI/UXの参考。

有料かつライセンス・内部実装が不明なため、コードベースとして利用することは前提にしない。


### ComfyUI-MiniMaxH3-Easy

主に参考にするもの：

- H3実行バックエンド
- workflow簡略化
- Low VRAM
- Model swap
- Segment処理
- H3固有処理

位置づけ：

最初の生成バックエンド有力候補。


### Faithful H3

主に参考にするもの：

- 漫画パネル検出
- Storyboard
- Shot並べ替え
- Camera
- Action
- Dialogue
- Sound
- Transition
- Structured JSON

位置づけ：

将来のManga → Storyboard → Video変換部分の参考。


### H3 Prompt Studio

主に参考にするもの：

- Story → Sequences
- Reference library
- LLMによるSequence分割
- Reference自動割当
- Structured JSON
- JSON repair / retry
- Vision modelによるReference説明

位置づけ：

将来のAI制作補助・Storyboard自動化の参考。


## 4. ソフトウェア構成

ComfyUI Portable本体の内部にアプリ本体を置かず、独立した兄弟ディレクトリとして管理する。

例：

D:\AI\
├─ ComfyUI_portable\
├─ LunaMax\
└─ Models\

LunaMaxからComfyUIへHTTP / WebSocketで接続する。

必要になった場合のみ、

ComfyUI/custom_nodes/LunaMaxBridge/

のような薄い専用Bridgeを追加する。

アプリ本体はComfyUI更新と独立してGit管理できる状態を保つ。


## 5. 初期ディレクトリ構想

LunaMax/
├─ app/
│  ├─ video/
│  └─ manga/
├─ core/
│  ├─ project/
│  ├─ assets/
│  ├─ jobs/
│  └─ history/
├─ schemas/
│  ├─ project/
│  ├─ shot/
│  └─ asset/
├─ adapters/
│  ├─ comfy/
│  └─ h3/
├─ recipes/
│  └─ h3/
├─ workflows/
│  └─ h3/
├─ config/
├─ docs/
└─ tests/

Manga部分は初期段階では空でもよい。

重要なのはVideo専用データ構造を作るのではなく、後からMangaと共有できるProject / Asset / Shot構造を最初から用意することである。


# 6. 段階的ロードマップ

## Phase 0 — 調査・設計固定

目的：

実装開始前に「何を作らないか」まで決める。

作業：

- 参考ツールの整理
- H3 Easyの現在workflow確認
- ComfyUI APIの接続方法確認
- Shot Schemaの初版作成
- Project Schemaの初版作成
- Adapter境界の決定
- 採用技術の決定

このPhaseでは大規模実装をしない。


## Phase 1 — H3 Skin

目的：

ComfyUIを直接触らずH3を生成できる最小の専用GUIを作る。

機能：

- Prompt
- Reference
- Resolution
- Duration
- Steps
- Seed
- LoRA
- Generate
- Preview
- Queue
- History
- ComfyUI connection
- Workflow execution

ここではTimelineを作らない。

成功条件：

「ComfyUIを開かなくても通常の生成アプリとしてH3を使える」。


## Phase 2 — Shot制作

追加：

- Project
- Asset library
- Shot
- Segment
- ShotごとのPrompt / Reference / Seed
- Regenerate Shot
- Continue
- Previous frame / Last frame
- Shot履歴
- Take管理

生成履歴と作品構造を分離する。

1 Shotに複数Takeを持たせ、

Take 1
Take 2
Take 3 ★採用

という管理を可能にする。


## Phase 3 — Video Studio

追加：

- Timeline
- Shot reorder
- Duration表示
- Main Preview
- Continuity
- Recipe Resolver
- FL2VA / Ref2VA等の自動選択
- Shot単位の再生成
- Shot結合
- Project export
- NLE export検討

ここで「H3 GUI」から「動画制作ツール」へ変化する。


## Phase 4 — Storyboard

追加：

- Storyboard view
- Storyboard ↔ Timeline同期
- Shot planning
- Camera
- Action
- Dialogue
- Sound
- Character / Reference assignment
- Structured Shot JSON

必要に応じてVision LLM / Local LLMを利用する。


## Phase 5 — Mangaタブ

UI：

[ Video ] [ Manga ]

Manga側に追加：

- Page
- Panel
- Layer
- Character
- Asset
- Balloon / Dialogue
- Panel ordering

重要：

MangaのPanelとVideoのShotを完全に別概念にしない。

例：

Manga Panel
↓
Shot Schema
↓
Video Timeline
↓
H3 Recipe Resolver

という変換を可能にする。


## Phase 6 — Manga → Animation

追加候補：

- Panel detection
- Panel → Shot
- Character reference自動割当
- Story → Sequences
- Camera suggestion
- Motion suggestion
- Dialogue / Voice
- Continuity
- Animation draft
- partial regeneration

ここまで来て初めて漫画制作ツールと動画制作ツールが一つの制作環境として結び付く。


## Phase 7 — Backend抽象化

H3専用構造を外し、

Shot
↓
Generation Adapter
├ MiniMax H3
├ Wan
├ FramePack系
└ Future Models

へ拡張する。

モデルごとの特殊機能はAdapterとCapability Schemaで吸収する。


# 7. AIの役割分担

## Web ChatGPT

役割：

- 調査
- 設計方針
- 機能整理
- 既存実装比較
- GitHub監査
- Architecture review
- 実装後の差分レビュー
- 開発方向が逸れていないかのチェック

基本的には「監督・監査・整理」を担当する。

ローカル環境を直接変更する作業担当にはしない。


## Astra

役割：

難しい設計問題だけを深く考えるArchitecture specialist。

毎回プロジェクト全体を再設計させない。

依頼例：

「現在のShot Schemaについて、Timeline、Manga Panel、将来の複数動画モデル対応という3条件から破綻点だけを探せ」

「Recipe ResolverについてDirectorDeckの方式と比較し、より堅牢な方法があれば提案せよ。ただしUI構成や他機能は変更しない」

「このPhaseの実装計画に重大な抜けがあるかだけを調べよ」

禁止に近い依頼：

「最高のAI漫画動画制作ソフトを自由に設計して」

Astraには意図的に探索範囲を狭く与える。


## LUNA

役割：

ローカル実装担当。

- repository作成
- directory構築
- coding
- ComfyUI接続
- workflow integration
- dependency installation
- test実行
- UI実装
- bug fix

仕様の大幅変更は独断で行わない。

設計上の疑問が生じた場合は、GitHub上にIssue / TODO / DESIGN QUESTIONとして残す。


## Codex等

必要に応じて：

- code review
- regression確認
- bug調査
- tests追加
- security / architecture review

を担当。

常時使う必要はない。


# 8. GitHubを開発の正本にする

AI同士で巨大な会話履歴を渡さない。

GitHubに必要情報を残す。

最低限：

README.md
ROADMAP.md
ARCHITECTURE.md
DECISIONS.md
docs/
issues/

を使用する。

特にDECISIONS.mdには、

- なぜこの方式を採用したか
- 検討した代替案
- 採用しなかった理由

を短く残す。

これにより別AIへ毎回長い説明をする必要を減らす。


# 9. 開発サイクル

基本サイクル：

ChatGPT
↓
方向・仕様を決める

必要な場合のみ
↓
Astra
難所を深掘り

↓
仕様をGitHubへ固定

↓
LUNA
ローカル実装

↓
commit / push

↓
ChatGPT
GitHub監査

問題なし
→ 次Phase

軽微な問題
→ LUNA修正

設計問題
→ ChatGPTで整理

難しい設計問題
→ Astraへ限定質問

というループを基本とする。


# 10. Phase Gate

各Phaseの途中で何度も全体レビューしない。

節目でのみ監査する。

例：

Phase 1実装
↓
GitHub監査
↓
PASS
↓
Phase 2

この単位で進める。

監査項目：

- Architecture違反がないか
- ComfyUI node IDへの直接依存が増えていないか
- GUIとbackendが密結合していないか
- Project / Shot Schemaを壊していないか
- 不要な機能を増やしていないか
- 後続Phaseを困難にしていないか
- test可能な構造になっているか


# 11. トークン節約方針

AIへ毎回プロジェクト全体を説明しない。

原則：

AIが読むもの
1. ROADMAP
2. ARCHITECTURE
3. 現在Phase
4. 関連コードのみ

Astraへ渡す場合も、

「全コードを読んで改善して」

ではなく、

「ARCHITECTURE.mdとShot Schemaだけを読み、この問題だけ検討」

とする。

LUNAにもPhase単位の作業指示を渡す。

ChatGPTの監査も原則として、

前回監査commit
→ 現在commit

の差分を見る。


# 12. Scope Creep防止

新しいアイデアが見つかっても、その場ですぐ実装しない。

以下に分類する。

NOW
現在Phaseに必要

NEXT
次Phase

LATER
将来候補

RESEARCH
要調査

これをROADMAPへ残す。

Astraが新機能を提案した場合も、現在Phaseに必須でなければLATERへ送る。


# 13. 最初の具体的作業

実装開始前に以下を行う。

1. LunaMax用の独立repositoryを作る。
2. ROADMAP.mdを置く。
3. ARCHITECTURE.mdを作る。
4. 参考プロジェクトと「拾う機能」をREFERENCES.mdへ記録する。
5. Phase 1の仕様をSPEC-PHASE1.mdとして固定する。
6. AstraにPhase 1設計だけをレビューさせる。
7. 必要部分だけ修正する。
8. LUNAにrepositoryを立ち上げさせる。
9. Phase 1を実装する。
10. GitHubへpushする。
11. ChatGPTで初回Architecture監査を行う。


# 14. 現時点での原則

「全部入りを先に作らない」

「ComfyUIをforkしない」

「H3 Easyを直接改造しない」

「GUIをComfyUI node IDへ密結合させない」

「Project / ShotをH3固有形式にしない」

「AIに全設計を丸投げしない」

「AI同士の会話ではなくGitHubへ知識を残す」

「Astraは広げるためではなく、難所を深く掘るために使う」

「LUNAは考え続ける担当ではなく、決めたものを実装する担当とする」

最初の目標は壮大な漫画・アニメ制作環境ではない。

まず、

「H3をComfyUIを意識せず快適に生成できるGUI」

を完成させる。

そのGUIの内部構造が正しければ、そこからShot、Timeline、Storyboard、Mangaへ段階的に育てる。