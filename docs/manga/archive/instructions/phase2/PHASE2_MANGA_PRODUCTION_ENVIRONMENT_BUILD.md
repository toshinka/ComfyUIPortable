# ComfyUI Portable 漫画制作環境 構築依頼書

## 0. 目的

Windowsローカル環境に、漫画・イラスト制作向けにカスタマイズした **ComfyUI Portable環境** を新規構築してください。

単なるComfyUIのインストールではなく、現在EasyReforge上で行っているIllustrious系生成を発展させ、

- 構図・ポーズのブレインストーミング
- 複数LoRAの混合
- Region単位のPrompt制御
- 将来的なRegion単位LoRA制御
- I2Iによる修正
- ControlNet等による構図拘束
- Wildcard / Dynamic Promptによるランダム探索
- 漫画制作向けWorkflow
- 将来的なANIMA等の別モデル追加

を行える「漫画制作研究環境」とすることが目的です。

現在EasyReforge上で開発しているMRP（Manga Region Prompter）的な発想をComfyUIへ発展させることを想定しています。

ただし、MRPの完全移植を最初から目標にするのではなく、ComfyUIに既に存在する有用なCustom Node・Workflow・Regional処理等を最大限利用してください。

---

# 1. 設置場所

ComfyUI Portable関連は原則として以下に配置してください。

```text
D:\GitHub\tegaki\ComfyUIPortable
```

既存の `tegaki` プロジェクト本体とは独立性を保ち、このディレクトリ外の既存ソースを不必要に変更しないでください。

Portable版として、このフォルダをバックアップまたは別PCへ移動しやすい構造を維持してください。

---

# 2. 最重要：Git管理方針

`D:\GitHub\tegaki` はGitリポジトリ配下です。

ComfyUI Portable本体には巨大なPython環境、依存パッケージ、生成画像、キャッシュ等が含まれるため、これらを誤ってGitへ登録しないでください。

必要に応じて `ComfyUIPortable/.gitignore` 等を作成してください。

原則としてGit管理対象にするものは、

```text
独自Custom Nodeのソース
独自スクリプト
設定テンプレート
Workflow JSON
ドキュメント
構築手順
依存関係一覧
外部AIレビュー用資料
GITHUB.TXT
```

など、再構築とレビューに必要な小さいファイルに限定してください。

以下は原則Gitへ登録しないでください。

```text
ComfyUI本体の巨大な配布物
embedded Python
site-packages
downloadした外部Custom Node本体
checkpoint
LoRA
VAE
ControlNet model
cache
temp
output画像
input画像
ログの巨大ファイル
```

既存Git履歴を書き換えたり、force pushしたりしないでください。

---

# 3. EasyReforgeとのモデル資産共有

モデル資産を二重保存したくありません。

現在、主な生成資産は

```text
E:\EasyReforge
```

以下に存在します。

ComfyUI側から可能な限りこれを共有利用してください。

最低限、

```text
Checkpoint / Stable Diffusion models
LoRA
VAE
ControlNet等、共用可能なモデル
Embedding等、互換性があるもの
```

を調査してください。

ComfyUIが持つ外部モデルパス設定、`extra_model_paths.yaml` 相当の標準的な仕組みを優先してください。

それだけでは共有できない資産については、必要に応じてWindowsのjunction / symbolic link等も検討して構いません。

ただし、

**E:\EasyReforge側の元ファイルを移動・削除・改変しないこと。**

EasyReforgeを壊さないことを最優先してください。

実際のディレクトリ構造をローカルで確認してから設定してください。推測したパスを設定しないでください。

ComfyUI専用モデルやComfyUI専用資産については、

```text
D:\GitHub\tegaki\ComfyUIPortable
```

側に保存して構いません。

---

# 4. 基本生成モデル

第一段階では **Illustrious / SDXL系を主力** としてください。

理由は、

- 既存LoRA資産が大量にある
- 複数LoRAの混合を多用する
- seedガチャによる構図・画風ブレインストーミングを重視する

ためです。

ANIMA 3.8B等は将来的に追加可能な構造にしてください。

最初からANIMAを主モデルにはしないでください。

ただしWorkflowやCustom Node設計をIllustrious専用に固定しすぎず、

```text
Illustrious / SDXL
ANIMA
将来の別モデル
```

をバックエンドとして追加できる構成が望ましいです。

---

# 5. LoRA記法

LoRAを大量に使用するため、通常のComfyUIのLoRA Loaderを大量に配線する操作は避けたいです。

最低限、Prompt欄から以下のように記述できるようにしてください。

```text
<lora:AAA:0.2>
<lora:BBB:0.65>
<lora:CCC:-0.3>
```

複数記述可能にしてください。

Prompt入力を解析して、

```text
LoRA名
weight
適用順
```

を自動的にLoRA stack / model patchへ反映する方式で構いません。

既に安定したCustom Nodeで実現できる場合はそれを利用してください。

適切な既存実装がない場合のみ、小規模な独自Custom Nodeを作ってください。

ファイル名検索については、拡張子の有無やサブフォルダにもある程度耐えられるようにしてください。

LoRAが見つからない場合には生成全体を謎の状態で失敗させるのではなく、どのLoRAが見つからなかったか分かるエラーを出してください。

将来的には、

```text
<lora:name:modelWeight:clipWeight>
```

のような拡張が可能な設計なら望ましいですが、初期実装で必須ではありません。

---

# 6. Wildcard共有

EasyReforgeで使用しているWildcard資産があります。

`E:\EasyReforge` 以下を調査し、既存WildcardをComfyUIでも共有可能か確認してください。

可能ならコピーせず、そのまま共用してください。

Dynamic Prompts系Custom Node等が現在のComfyUIで安定して使用できる場合は導入候補としてください。

少なくとも、

```text
__pose__
__camera__
__background__
```

のようなWildcard呼び出しと、

```text
{option A|option B|option C}
```

等のランダム選択が実用的に行える環境を希望します。

既存Wildcardファイルの構文との互換性を実際に確認してください。

EasyReforge用Wildcardを壊す変換はしないでください。

必要ならComfyUI側にcompatibility layerを作ってください。

---

# 7. 漫画制作向け基本Workflow

単純なtxt2imgだけではなく、漫画制作を意識したWorkflowを作成してください。

第一段階では最低限、

```text
Global Prompt
Region Prompt
LoRA
Wildcard / Dynamic Prompt
Seed variation
txt2img
I2I
Control系への拡張入口
```

を扱えることを目標とします。

最終的にはMRPのように、

```text
Canvas
 ├─ Global Prompt
 ├─ Region A Prompt
 ├─ Region B Prompt
 ├─ Region C Prompt
 ├─ Region Mask
 ├─ LoRA assignment
 └─ Control information
```

を扱える漫画制作ツールへ発展させたいです。

---

# 8. Regional Prompt / Regional Sampling

ComfyUIには既に複数のRegional系実装が存在するため、まず既存資産を調査・利用してください。

候補として、

```text
ComfyUI Impact Pack / RegionalSampler
Omost系
DenseDiffusion系
その他、現在保守されているRegional Prompt系
```

を比較してください。

古い記事や古いWorkflowを無条件に採用しないでください。

2026年現在のComfyUIで実際に動作するものを優先してください。

特に興味があるのは、

**領域ごとに別MODEL / 別LoRA stackを適用する実験**

です。

例えば、

```text
Region A
Illustrious + LoRA A

Region B
Illustrious + LoRA B

Region C
Illustrious + LoRA A + LoRA C
```

のような構成を既存RegionalSampler等で実現可能なら、概念実証Workflowを作成してください。

これは将来開発予定のRLL（Regional LoRA Lab / Region方向へLoRA効果を制御する仕組み）の先行実験に使用します。

---

# 9. LoRA Block Weight

現在利用可能で安定しているなら、

```text
Inspire Pack
LoRA Block Weight系
```

も調査してください。

目的はLoRAを単に全層へ適用するだけではなく、

```text
LoRA Aの構図寄りblock
LoRA Aのstyle寄りblock
LoRA Bの別block
```

のような探索が可能か検証することです。

Regional Samplingとの組み合わせも検討してください。

ただし、最初から複雑すぎるWorkflowにしないでください。

基本Workflowと研究Workflowは分離してください。

---

# 10. I2I導線

漫画制作では生成後の修正が重要なので、txt2imgとは別にI2Iへの分かりやすい導線を作ってください。

最低限、

```text
画像読み込み
↓
必要に応じてresize
↓
VAE Encode
↓
denoise strength指定
↓
Prompt / LoRA適用
↓
再生成
```

を行えること。

可能なら後から、

```text
Mask
Inpaint
ControlNet
Reference image
Regional I2I
```

へ拡張しやすい構造にしてください。

txt2imgとI2Iで不要な部分を二重実装しない設計を希望します。

---

# 11. ControlNet等

漫画のポーズ・構図制御用として、現在保守されているものを調査した上で、

```text
Advanced ControlNet
ControlNet Aux
OpenPose / DWPose
Depth
LineArt
Anime LineArt
```

などを利用可能にしてください。

すべてを最初から常時ロードする必要はありません。

「ブレインストーミング時は自由度を維持し、構図を詰める段階だけControlを強くする」使い方を想定しています。

可能ならControl適用開始step / 終了stepを制御できる構成を優先してください。

---

# 12. Workflowの鮮度

インターネット上には古いComfyUI Workflowが大量にあります。

以下を守ってください。

古いWorkflowを拾ってきて、そのまま動く前提にしないこと。

可能な限り、

```text
最近更新されたRepository
現行ComfyUI対応
現在メンテナンスされているCustom Node
現在取得可能なWorkflow
```

を優先してください。

有用だが古いWorkflowしか存在しない場合は、現在のComfyUI API / node仕様に合わせて修正して構いません。

修正した場合は、

```text
元Workflow URL
何が壊れていたか
何を変更したか
なぜその変更でよいのか
```

を報告してください。

---

# 13. Custom Nodeの導入方針

Custom Nodeを大量に無計画に入れないでください。

候補を調査し、

```text
目的
Repository URL
最終更新状況
ライセンス
現行ComfyUIとの互換性
代替Nodeの有無
今回本当に必要か
```

を見た上で採用してください。

まず「少数の信頼できるNodeで基本環境を成立させる」ことを優先してください。

候補例は、

```text
Impact Pack
Inspire Pack
Advanced ControlNet
ControlNet Aux
Dynamic Prompts系
rgthree系
Omost / DenseDiffusion系
```

ですが、これは強制指定ではありません。

より新しく安定した選択肢が存在する場合は置き換えて構いません。

その場合は変更理由を報告してください。

---

# 14. 独自実装について

指示書に存在しない機能でも、

「漫画制作環境として明らかに有用」
「保守性が上がる」
「既存機能の重複を減らせる」
「将来のMRP/RLL実装に必要」

と判断したものは追加して構いません。

ただし独自判断で追加したものについては、最終報告書に必ず、

```text
何を追加したか
なぜ必要だと思ったか
既存の何が不足していたか
将来どの機能に利用できるか
削除しても基本動作するか
```

を書いてください。

「なんとなく便利そうだから大量に追加」は禁止します。

---

# 15. 外部AIレビュー可能な構造

この環境は、ローカルファイルへ直接アクセスできないChatGPT等にもレビューさせます。

そのため、外部AIがGitHub経由で必要なソース・Workflow・設定・報告書へアクセスできる構造を作ってください。

以下のようなレビュー入口ファイルを作成してください。

```text
D:\GitHub\tegaki\ComfyUIPortable\GITHUB.TXT
```

既存リポジトリ内に `GitHubURL.txt` / `GPT_GITHUB_LINKS.txt` 等の既存規約が存在する場合は、それを確認して形式を揃えて構いません。

GITHUB.TXTには少なくとも、

```text
Project name
Purpose
Updated日時（JST）
Repository URL
Branch
Commit SHA
Current status

Required first reads
重要ソース
Workflow
Custom Node
設定
BUILD_REPORT.md
KNOWN_ISSUES.md
WORKFLOW_INDEX.md

各ファイルのGitHub通常URL
各ファイルのraw.githubusercontent.com URL
```

を掲載してください。

外部AIが

**GITHUB.TXT → 必要資料 → 実装**

の順で追えるようにしてください。

URLは推測で生成せず、

```text
git remote
branch
実際のrepository path
```

を確認して作成してください。

可能ならRaw URLを優先して併記してください。

---

# 16. GitHubへ公開されていない状態について

外部AIがレビューするファイルはGitHubから実際に取得できる必要があります。

ローカルにしか存在しない変更について、GitHub URLを書いて「読めることにする」のは禁止です。

各作業終了時に、

```text
Repository
Branch
Commit SHA
GITHUB.TXT update
GitHub上から取得可能か
```

を確認してください。

既存の開発運用上commit / pushして問題ない場合のみ通常のcommit / pushを行ってください。

認証や既存運用が不明な場合、force push等はせず、

「ここまでcommit可能」
「pushすれば外部レビュー可能」

という状態で報告してください。

---

# 17. 作成してほしいドキュメント

最低限、以下を作成・維持してください。

```text
README.md
    この環境の目的と起動方法

BUILD_REPORT.md
    今回実際に何をしたか

DEPENDENCIES.md
    ComfyUI / Custom Node / Python等のバージョン

WORKFLOW_INDEX.md
    Workflow一覧と用途

KNOWN_ISSUES.md
    未解決問題・制限事項

RESEARCH_REFERENCES.md
    参考にしたGitHub等

GITHUB.TXT
    外部AIレビュー入口
```

`RESEARCH_REFERENCES.md` では各主要外部資産について、

```text
Repository URL
Relevant file / document
License
今回何を参考にしたか
何を直接コピーしたか／していないか
ComfyUI / Illustriousへの適用内容
```

を記録してください。

ライセンス未確認の場合は明示してください。

---

# 18. BUILD_REPORT.md の内容

作業後の報告書は非常に重要です。

最低限、以下を記録してください。

```text
1. 実施した作業
2. 新規作成ファイル
3. 変更ファイル
4. インストールしたCustom Node
5. 各Custom NodeのGitHub URL
6. 利用したWorkflowのURL
7. EasyReforgeから共有したディレクトリ
8. symbolic link / junction / external path設定
9. 動作確認したcheckpoint
10. 動作確認したLoRA
11. Wildcard互換性
12. Dynamic Prompt動作
13. txt2imgテスト結果
14. I2Iテスト結果
15. Regional Promptテスト結果
16. Regional LoRA概念実証結果
17. ControlNetテスト結果
18. 起動時error / warning
19. 未解決問題
20. 今後の推奨作業
```

さらに、

```text
指示通りに作ったもの
Gemini自身の判断で追加したもの
当初案から変更したもの
```

を分けて記載してください。

変更した場合は理由も書いてください。

---

# 19. Workflow構成

Workflowを一個の巨大なものにしないでください。

最低でも、

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG.json

02_ILLUSTRIOUS_I2I.json

03_MANGA_REGIONAL_PROMPT.json

04_REGIONAL_LORA_EXPERIMENT.json

05_CONTROLNET_COMPOSITION.json

06_LORA_MIX_EXPERIMENT.json
```

のように目的別に分けることを推奨します。

実際のファイル名は変更して構いません。

また、各Workflowについて `WORKFLOW_INDEX.md` に、

```text
目的
必要Custom Node
入力
出力
想定用途
安定版 / 実験版
```

を書いてください。

---

# 20. 安定版と研究版を分離する

漫画制作で常用できる部分と、実験的な部分を分けてください。

例えば、

```text
STABLE
├ Illustrious txt2img
├ LoRA syntax
├ Wildcard
├ Dynamic Prompt
└ I2I

EXPERIMENTAL
├ RegionalSampler
├ Region別LoRA
├ LoRA Block Weight
├ DenseDiffusion
├ Omost
└ ANIMA 3.8B
```

のような扱いです。

Experimental機能が壊れても基本生成環境まで起動不能にならない構造を希望します。

---

# 21. 構図ブレインストーミングを重視する

このツールは「完全に指定した一枚を作る」だけではありません。

漫画の構図・カメラ・ポーズ・画風候補を大量に探索する用途を重視します。

そのため、

```text
seed random
Wildcard
Dynamic Prompt
LoRA mix
camera variation
pose variation
composition variation
```

を手軽に変化させられる構成にしてください。

将来的には、

```text
Exploration Mode
    自由なガチャ・候補探索

Control Mode
    Region / Pose / ControlNet等で詰める
```

という二段階の制作思想へ発展させる予定です。

Workflow設計もこの方向を邪魔しないようにしてください。

---

# 22. MRP / RLLへの将来拡張

現在想定している将来構造は、

```text
Prompt / Wildcard
       ↓
MRP的 Region定義
       ↓
Region Prompt
       ↓
Region Mask
       ↓
Regional LoRA / RLL
       ↓
ControlNet
       ↓
Sampler
```

です。

RLLでは最終的に、

**LoRA効果そのものへ空間的な指向性を与える**

ことを研究したいです。

ただし今回の構築では本格RLL実装までは要求しません。

まず既存ComfyUI資産で、

```text
Region A → LoRA A
Region B → LoRA B
```

を疑似的に行えるWorkflowを作り、研究価値があるか確認できる環境を作ってください。

---

# 23. ANIMAについて

ANIMA 3.8Bは興味がありますが、今回の主目的ではありません。

Illustrious環境完成後、現在のComfyUIで安定して使用可能なら、

```text
ANIMA 3.8B test workflow
```

をExperimentalとして追加して構いません。

旧Anima LoRAのremap等が必要なら、現在の仕様と対応Custom Nodeを調査してください。

Illustrious資産や基本環境を壊してまで導入しないでください。

---

# 24. 動作確認

「ファイルを配置したので完成」にはしないでください。

実際に可能な範囲で起動・生成確認してください。

最低限、

```text
ComfyUI起動
Custom Node import
モデル認識
VAE認識
LoRA認識
EasyReforgeとの共有
基本txt2img
LoRA syntax
Wildcard
Dynamic Prompt
I2I
Regional Workflow
```

を確認してください。

失敗した場合はログを調査し、古いWorkflow / Node API / import / Python package等が原因なら、現行環境で動作するよう修正してください。

修正内容はBUILD_REPORTに残してください。

---

# 25. 不具合調査のために残す情報

後からChatGPTへ不具合調査を依頼するため、エラー発生時に必要になる情報を取得しやすくしてください。

最低限、

```text
ComfyUI version / commit
Python version
PyTorch version
CUDA version
GPU情報
Custom Node一覧
各Custom Nodeのcommitまたはversion
Workflow
起動ログ
エラートレース
関連ソース
```

が追えるようにしてください。

そして関連ファイルを `GITHUB.TXT` からGitHub経由で辿れる状態にしてください。

巨大なログそのものをGit管理する必要はありません。

必要なエラー部分だけ報告書へ転載してください。

---

# 26. 作業上の原則

最優先順位は以下です。

```text
1. EasyReforgeを壊さない
2. 既存モデル資産を重複させない
3. 基本Illustrious生成を安定させる
4. LoRA / Wildcard資産を継承する
5. I2I導線を成立させる
6. Regional Promptを成立させる
7. Regional LoRA実験を成立させる
8. Control系を追加する
9. Experimental機能を追加する
10. ANIMA等を追加する
```

一度に全部を複雑化して基本生成まで壊さないでください。

各段階で最低限の動作確認をしてから次へ進んでください。

---

# 27. 最終的に報告してほしいこと

作業終了時、ユーザーへの最終回答では単に「完成しました」と言わず、

```text
何が完成したか
何が動作確認済みか
何がExperimentalか
何が未完成か
何をEasyReforgeから共有しているか
何をComfyUIPortable側へ独自保存したか
今回追加したCustom Node
各GitHub URL
作成Workflow一覧
GITHUB.TXTの場所
BUILD_REPORT.mdの場所
次に試すべきWorkflow
既知の問題
Gemini独自判断で変更・追加したものと理由
```

を簡潔にまとめてください。

最後に、外部ChatGPTへそのまま渡せる形で、

```text
External review entry:
<GitHub上のGITHUB.TXT Raw URL>

Current commit:
<commit SHA>

Review target:
<今回主に見てほしい部分>
```

を提示してください。

---

## 最終目標

これは単なるComfyUI環境構築ではなく、

**Illustriousの既存資産と自由なブレインストーミング能力を残しながら、ComfyUIのRegional / LoRA / ControlNet / I2I等の既存資産を組み合わせ、将来的にMRP・RLLを統合できる漫画制作専用環境の土台を作る**

ための作業です。

既存資産で実現できることは極力再発明せず利用してください。

一方、既存ツールでは目的を満たせない部分については、その不足点を明確化した上で小さな独自実装を行って構いません。

最初から完成形を一気に作るより、

**安定した基本環境 → 漫画Workflow → Regional実験 → RLL研究**

の順で、壊れにくく検証可能な環境を構築してください。