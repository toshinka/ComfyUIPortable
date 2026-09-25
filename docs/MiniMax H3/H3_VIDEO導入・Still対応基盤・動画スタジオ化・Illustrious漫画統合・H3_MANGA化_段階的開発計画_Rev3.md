# H3 VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3 MANGA化 段階的開発計画

更新日: 2026-09-08  
版: Rev.3 — 「思考の水平」「思考のレンズ」「山」GUI設計原則 反映

## 0. この文書の位置づけ

本書は `D:\GitHub\tegaki` 配下で進める ComfyUI Portable ベース制作環境の上位ロードマップである。

基本順序は変えない。

1. H3 VIDEOを既存実装に乗って最小手で実働化
2. 同じ基盤がH3 Stillを受け入れられる状態にする
3. H3 VIDEOを実際に使いながらPractical化
4. Studio / Storyboard / Previzへ必要なものから発展
5. Illustrious Mangaの中身を完成
6. Manga / Videoを共通UIへ統合
7. 最後にH3 MANGAを独立研究・実装
8. 必要に応じてH3→Illustrious / Anima Image Finishを追加

Rev.3では、この順序を変えず、GUI判断の基準を明文化する。

---

# 1. 最上位開発原則

## 1.1 既にあるものは使う

H3周辺はGUI、timeline、reference、continuation、Still、quantization、高速化が複数OSSで並行開発されている。

Tegakiは最初から全機能を独自実装しない。

既存の有力実装から、

- UI interaction
- workflow
- reference semantics
- queue / history
- timeline
- continuity
- low-VRAM recipe
- still-image route

を必要な単位だけ採用する。

一本の巨大forkへ全面依存せず、薄い統合層で良い部分を縫い止める。

これを `Patchwork Integration` とする。

## 1.2 まずH3 VIDEOで遊べる状態にする

最初の成功条件は、

**ComfyUI node graphを意識せずH3 VIDEOを生成できること。**

Studio、Storyboard、3D、Mangaを待たない。

## 1.3 H3 Stillは初期から受け入れ可能にする

Stillを初期の主目的にはしないが、

- ordered multi-reference
- source anchor
- semantic reference roles
- T2I / I2I / REF2VA still
- short temporal packet
- experimental T=1
- still-specific decode
- detail refine

を後から入れても基盤を壊さない。

## 1.4 Illustrious MangaをH3都合で変更しない

現在のScene / Panel / Region / Character / authoring semantics完成を優先する。

## 1.5 H3 MANGAは最後

H3 VIDEO、Studio、Illustrious Mangaが実働し、Still研究が蓄積した後に開始する。

---

# 2. TEGAKI GUI設計哲学

## 2.1 思考の水平

TEGAKIにおける「思考の水平」とは、画面を横方向に並べるという意味ではない。

**ユーザーが既に所属している制作文化圏で身につけた操作知識を、できるだけ段差なく新しいツールへ持ち込める状態**を指す。

広く支持されているUI、操作語彙、配置、アイコン、モード切替、タイムライン、レイヤー、Inspector、Reference、Generate、Historyなどは、その文化圏における基準面として扱う。

多数派だから無条件に正しいのではない。
しかし、独自性のためだけに既知の操作体系を壊さない。

### 原則

**Preserve the Cognitive Level. Earn every slope. Build mountains only where the summit is worth reaching.**

- 水平を守れる場所では守る。
- 改善に価値があるなら緩い傾斜を作る。
- 大きな学習コストを要求するなら、その先に明確な制作上の利益を置く。

## 2.2 階段・傾斜・山

悪い独自UIは、従来と同じことをするために新しい操作を覚えさせる「階段」や「壁」になる。

良い新UIは違う。

```text
既存文化圏 ─────────────────── 思考の水平
                           ／
                         ／
                       ／
                     ★
             新しい制作能力・効率・快感
```

登る必要があるなら、頂上そのものが目標にならなければならない。

Tegaki固有の大きなUI変更は「違うから新しい」ではなく、

- 明確に速い
- 明確に分かりやすい
- 従来できなかったことができる
- 制作工程が統合される
- 触ること自体にブランド価値を感じる

場合にだけ許容する。

新GUIは階段ではなく「山の頂点」であることを目指す。

## 2.3 モダンとは新奇さではない

「モダン」は単に最新の見た目を採用することではない。

現在の制作文化圏で支持されている水平面を理解し、その上で次の標準になり得る改善を提示すること。

古い多数派UIを無条件に残すことも、流行しているから全面刷新することも避ける。

---

# 3. 現代的制作UIから学ぶ範囲

GUIのbenchmarkは生成AI GUIだけに限定しない。

特にタブレット／ペン入力対応の制作アプリは、限られた画面面積で複雑な機能を扱うため、現在の「思考の水平」を観察する重要な対象とする。

## 3.1 CLIP STUDIO PAINT Simple Mode

見るもの:

- 高機能なStudio Modeを捨てず、Simple Modeを別レンズとして追加する考え方
- 画面を制作物へ返す
- タブレット／スマートフォンで迷いにくい選択肢
- 必要なら高機能側へ戻れる構造
- 初学者向けヒント／チュートリアル
- 既存ユーザーと新規ユーザーを同じUIへ無理に押し込まない

Tegakiでは「高度機能を削除する」のではなく「必要な時だけ見せる」設計の参考にする。

## 3.2 Callipeg / Callipeg Studio

CallipegはiPad / Apple Pencil前提から始まり、現在はdesktopへ展開している。

見るもの:

- canvas中心
- top bar / side controls / timelineという理解しやすい骨格
- 指・ペン・マウス・キーボードの役割分担
- left/right-handed対応
- modular panel
- Studio → Shot → Timelineの制作単位
- desktop化してもtablet由来の単純さを完全には捨てないこと

特に動画／アニメーションUIのbenchmarkとして扱う。

## 3.3 Procreate Dreams

見るもの:

- Theater / Timeline / Stage / Canvasという明確なscope
- modeによって同じ素材への操作意味を切り替える考え方
- gesture中心でも制作構造を失わないこと
- timelineを常時「全部入り」にしないこと

## 3.4 ToonSquid系・Procreate系・Fresco系

個々の外観をコピーする対象ではない。

見るもの:

- 2020年代のtablet-first制作UIの密度
- アイコン中心のtoolbar
- muted neutral surface
- 過剰に黒くしないdark surface
- light modeでも純白一色にしないsurface hierarchy
- 強い色を常時大量に使わず、状態・選択・重要actionへ限定する
- canvas / previewを主役にする
- panelを必要時に出す

実際の採用時は各製品の現行UIを再確認する。

---

# 4. 視覚的な「思考の水平」

色、線、面、アイコンにも認知的段差がある。

## 4.1 色を情報階層として乱用しない

色数を増やして機能カテゴリを説明しすぎない。

基本surfaceはneutral寄りとし、

- 選択
- active state
- warning
- destructive action
- primary action

など、意味がある場所へ色を使う。

## 4.2 Dark = Black ではない

「モダンだから真っ黒」にしない。

制作物とUIを分離でき、長時間見ても過度に強くないneutral grayを基準候補とする。

Light Modeも純白一色を前提にせず、淡いgray surfaceでpanel hierarchyを作れる。

具体色はAstra UI Reviewでbenchmark screenshotを比較して決める。

## 4.3 二階調的な視覚整理

企業ロゴや近年のアプリUIで見られるような、細かな装飾より

- 面
- silhouette
- icon
- typography
- restrained accent

で状態を認識させる方向を優先する。

ただしflatnessそのものを目的化しない。

---

# 5. 思考のレンズ

TEGAKIでは、全機能を常に同じ画面へ露出しない。

ユーザーが今している仕事によって、必要な情報だけを見る。

これを `思考のレンズ / Cognitive Lens` と呼ぶ。

例:

```text
Project Lens
Asset Lens
Generate Lens
Reference Lens
Still Lens
Video Lens
Timeline Lens
Diagnostic Lens
```

レンズは別アプリではない。

同じProject / Asset / Jobを別の目的から見るscopeである。

## 5.1 レンズのUI表現

候補:

- tab
- segmented button
- mode button
- drawer
- popover
- contextual inspector
- temporary panel
- workspace switch

何でも新規ウィンドウにしない。

## 5.2 Progressive Disclosure

A1111的な「必要な設定がそこにある」という直接性は捨てない。

ただし全設定を常時露出する必要もない。

```text
よく使う
    ↓ 常時

今回必要
    ↓ contextで表示

専門設定
    ↓ Advanced / Inspector

故障解析
    ↓ Diagnostic Lens
```

これにより初心者向けに機能を削らず、熟練者向け機能で初期画面を埋めない。

---

# 6. H3 GUIへの適用

## 6.1 水平を守るもの

既存文化で十分定着しているものは独自名称にしない。

- Prompt
- Seed
- Reference
- LoRA
- Resolution
- Generate
- Preview
- Queue
- History
- Timeline
- Project
- Shot
- Take

## 6.2 緩い傾斜を作ってよいもの

Referenceを単なるfile inputから、

```text
[Character A] Identity
[Rough]       Composition
[Image C]     Pose
```

のsemantic cardへ進化させる。

既知のReference概念を拡張するので、完全な新概念より学習負荷が低い。

## 6.3 山にしてよいもの

### Recipe Resolver

ユーザーへ毎回 T2V / I2V / FL2VA / REF2VA を理解させず、

- 素材
- intent
- continuity
- reference

からTegakiがrouteを決める。

完成度が高ければ、既存UIとの差を学ぶ価値がある。

### Storyboard → Generate → Retake → Timeline

Storyboardと生成と編集が一続きになるなら、独自UIを学ぶ価値がある。

単なる独自Timelineなら山ではなく壁になる。

---

# 7. H3 Patchwork Integration

## Minimal Web Skin参考

- AntaresAlice/h3-webui
- onigirikiller/minimax-h3-webui

見るもの:
- generate flow
- queue
- history
- workspace
- ComfyUI HTTP/WS separation
- A1111的な直接性

## H3 backend simplification参考

- ComfyUI native H3
- ComfyUI-MiniMaxH3-Easy

## H3 Still技術参考

- ComfyUI-MiniMax-H3-Image-Studio
- ComfyUI-MiniMax-H3-Studio

見るもの:
- ordered references
- semantic role
- source anchor
- still extraction
- route validation
- VAE tiling
- OOM fallback
- metadata

## Studio / Timeline参考

- ComfyUI-H3Studio
- MiniMax H3 Director系

## 制作UI benchmark

- CLIP STUDIO PAINT Simple Mode
- Callipeg / Callipeg Studio
- Procreate Dreams
- Procreate
- Adobe Fresco
- ToonSquid

コードを流用する対象と、UXを観察する対象を混同しない。

---

# 8. 初期H3画面の方向

固定デザインではなくAstraへ渡すbaseline。

```text
┌──────────────────────────────────────────────────────────┐
│ Project / Mode / Context                         Status │
├──────────────┬─────────────────────────┬─────────────────┤
│ Assets       │                         │ Inspector       │
│ References   │     Preview / Work      │                 │
│ Cast         │                         │ contextual only │
│              │                         │                 │
├──────────────┴─────────────────────────┴─────────────────┤
│ Queue / History → later Timeline Lens                   │
└──────────────────────────────────────────────────────────┘
```

重要なのは三列であることではない。

- 主役がPreview / Workである
- 現在必要なscopeが分かる
- 不要なpanelを隠せる
- Assetは別modeでも再利用できる
- Timelineへ自然に成長できる

こと。

---

# 9. Astra UI Review Gate

AstraはGUIの「山」を設計する役として使う。

ただし自由な全面再設計はさせない。

渡すもの:

1. 本計画
2. H3 OSS shortlist
3. 実際のcandidate screenshots
4. CLIP STUDIO Simple Mode
5. Callipeg
6. Procreate Dreams
7. ToonSquid / Fresco等の現行benchmark
8. Tegaki既存Web drawing UI
9. H1 scope
10. desktop + 将来tabletを含むinput条件

Astraへの問い:

- どこが現在の思考の水平か
- 何をそのまま借りるべきか
- どこなら傾斜を作ってよいか
- Tegaki固有の「山」は何か
- どの機能をどのレンズへ隠すか
- 初見5分で迷う箇所はどこか
- 熟練後に遅くなる箇所はどこか
- 見た目だけモダンで操作が悪化していないか
- ブランドを感じる固有性をどこへ集中させるか

出力:

- screen hierarchy
- component inventory
- lens / scope model
- interaction rules
- visual language
- benchmark inheritance map
- deliberate departures
- what NOT to redesign

Web GPTで監査後、LUNA向けCardへ変換する。

---

# 10. H3共通Request Schemaの最小要件

```text
generation_kind
  video
  still

prompt
seed
resolution
steps
sampler_profile

references[]
  id
  media_type
  semantic_role
  order
  retention
  source_anchor

start_frame
end_frame

loras[]
memory_profile
runtime_profile
```

GUIをComfyUI node IDへ密結合しない。

---

# 11. Memory Profile

対象:

- RTX 4070 12GB VRAM
- 64GB system RAM

候補:

```text
SAFE_12GB
BALANCED
QUALITY
EXPERIMENTAL
```

adapterがmodel、offload、resolution、reference size、decode tiling等を決める。

---

# 12. Runtime / Sampling Profile

```text
Base Quality
Stable Fast
Experimental
```

高速化をbase workflowへ埋め込まない。

---

# 13. Adoption Cooling Gate

通常Fast Path:

1. 公開から最低7日
2. 重大recipe変更が直近72時間ない
3. consumer GPU複数環境で成功
4. 12GBまたは16GB帯の実測
5. artifact / sampler / stepsを固定可能
6. upstream互換性確認
7. Base Qualityへ容易に戻せる
8. license / provenance確認

FastH3 / VSA等の新runtimeは原則14日程度観察してよい。

Experimental profileでの早期試験は可。
default化とは分離する。

---

# 14. AI運用

## LUNA

通常実装。

無差別にOSSをcloneしない。

最初はReference Inventory:

```text
repo
pinned commit
license
role
status:
  inspect
  adopt
  defer
```

採用後だけ取得・移植。

## Web GPT

- research
- shortlist
- diff audit
- gate review
- candidate comparison

## Sol

- difficult implementation
- difficult bug
- bounded refactor

## Astra

- GUI composition
- cognitive-level review
- lens design
- major architecture boundary

スポット投入。

---

# 15. Phase H0 — Groundwork / Research Freeze

- H3 directory / docs / workflow棚
- GITHUB_H3.txt
- Reference Inventory
- current H3 support確認
- model / license確認
- shortlist固定
- RTX 4070 12GB baseline

Gate: Web GPT review。

その後、H1 GUI実装前にAstra UI Reviewを行う価値が高い。

---

# 16. Phase H1 — H3 VIDEO Minimum Skin

最低限:

- Prompt
- Reference
- Resolution
- Duration
- Steps/Profile
- Seed
- LoRA
- Generate
- Preview
- Progress
- Queue
- History
- ComfyUI connection

成功条件:

**Node graphを触らずH3 VIDEO生成。**

UI成功条件:

- 初見で既存生成AI経験が転用できる
- 必要な設定へ短距離で到達できる
- 不要な設定が制作物を圧迫しない
- advanced機能への入口が見失われない
- 見た目の新しさだけで操作を再学習させない

---

# 17. Phase H1S — H3 Still Capability Spike

- T2I
- source anchored I2I
- ordered multi-reference
- semantic reference roles
- output still
- metadata restore

Still production UI完成ではない。

`H3 request -> adapter -> still output` の成立確認。

---

# 18. Phase H2 — Practical Skin

候補:

- Reference library
- Cast
- preset
- metadata restore
- low-VRAM profile
- model auto switching
- error recovery
- output organization
- Take
- workspace persistence
- H3 Still入口
- Lens切替の改善

ここで実使用から「水平」「傾斜」「壁」を再評価する。

---

# 19. Phase H3 — H3 VIDEO Studio

- Project
- Shot
- Take
- Segment
- Timeline
- continuation
- continuity
- retake
- partial regeneration
- reel
- join/export
- Recipe Resolver

Timeline Lensを本格化。

---

# 20. Phase H4 — Storyboard / Editing / Previz

必要性が確認されたものから追加。

- Storyboard
- Storyboard ↔ Timeline
- camera
- action
- dialogue
- sound
- simple editor
- NLE export
- 3D Previz

他者が良いものを先に作れば待って取り込む。

---

# 21. Illustrious Manga完成Phase

優先:

- Scene
- Visual Panel
- Region
- Character
- Workflow reliability
- Minimum-Hand UX
- browser acceptance
- production stability

H3へ合わせるために途中schemaを変更しない。

ただしGUI統合時には同じ「思考の水平／レンズ」原則で評価する。

---

# 22. UI統合Phase

双方実働後、

```text
[Manga] [Video]
```

等の共通shellを検討。

共通化候補:

- shell
- project selector
- asset
- character/reference
- history
- queue/job
- settings
- visual language
- lens mechanics

共通化しない:

- Manga Scene semantics
- Manga Region semantics
- H3 Timeline runtime
- backend-specific recipe

---

# 23. H3 MANGA — 最終研究Phase

開始条件:

- H3 VIDEO実働
- Studio基本構造成立
- Illustrious Manga実働
- H3 Still知見蓄積
- ordered reference / CAST / rough anchor実績

現在のIllustrious Manga runtimeへ直接結合する前提にしない。

---

# 24. Image Finish / Bake

```text
rough / layout
      ↓
H3 Still / H3 Manga
      ↓
selected panel / frame
      ↓
Image Finish Adapter
      ↓
Illustrious / Anima / future image model
```

---

# 25. Current Priority

```text
1. LUNAでH3地均し
        ↓
2. Web GPT監査
        ↓
3. H0 Reference Inventory / shortlist
        ↓
4. Astra UI Review
   「思考の水平／レンズ／山」を具体化
        ↓
5. Web GPT監査・Card化
        ↓
6. LUNAでH1 Minimum Skin
        ↓
7. H1S Still Capability Spike
        ↓
8. H2 Practical
        ↓
9. H3 Studio
        ↓
10. Illustrious Manga完成
        ↓
11. UI統合
        ↓
12. H3 MANGA
```

---

# 26. 禁止事項

- 「モダン」を単なるdark UIと解釈しない
- 「シンプル」を機能削除と解釈しない
- 独自性のために一般的なUI語彙を変更しない
- 色数で機能階層を説明しすぎない
- 全設定を常時表示しない
- 全設定を隠して到達不能にもしない
- tablet UIをdesktopへそのまま拡大しない
- desktop UIをtabletへ縮小しただけにしない
- 一本の巨大GUI forkへ固定しない
- 新Turboを即defaultにしない
- H3 Still進展を理由にH3 MANGAを前倒ししない
- H3都合でIllustrious Mangaを変更しない
- Astraに制約なしの全面再設計をさせない
- LUNAへ候補確定前の大量移植をさせない

---

# 27. 開発思想

**既にあるものは使う。**

**多数のユーザーが既に知っていることには価値がある。**

**古いという理由だけで水平面を壊さない。**

**新しいという理由だけで山を作らない。**

**必要な時だけ必要な選択肢を見る。**

**レンズを切り替え、同じ制作物を別のscopeから扱う。**

**傾斜を作るなら、その先に利益を置く。**

**大きく違うなら、登りたくなる頂上を作る。**

**Tegakiのブランドは、奇抜さではなく「登った価値がある」と感じる制作体験から生む。**

**まず動かし、良い部分だけ縫い止める。**

**高速化は本線と分離する。**

**Stillの進歩は受け入れるが、H3 MANGAを急がない。**
