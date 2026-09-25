# H3 VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3 MANGA化 段階的開発計画

更新日: 2026-09-08
版: Rev.2 — H3 Still / Patchwork GUI / Adoption Gate 反映

## 0. この文書の位置づけ

本書は `D:\GitHub\tegaki` 配下で進める ComfyUI Portable ベース制作環境の上位ロードマップである。

順序は以下を基本とする。

1. H3 VIDEOを既存実装に乗って最小手で実働化
2. 同じ基盤がH3 Stillを後付け可能な状態にする
3. H3 VIDEOを使いながらPractical化
4. 他者の成果を取り込みながらStudio / Storyboard / Previzへ発展
5. Illustrious Mangaの中身を完成
6. Manga / Videoを共通UIへタブ統合
7. 最後にH3 MANGAを独立研究・実装
8. 必要に応じてH3→Illustrious / Anima Image Finishを追加

本書は詳細実装仕様ではない。
Current Phase / Current Card / Reportは別文書へ分離する。

## 1. 最上位原則

### 1.1 既にあるものは使う

H3 VIDEO周辺は開発速度が速く、GUI、timeline、reference、continuation、Still、quantization、高速化が複数OSSで並行して進んでいる。

Tegakiは最初から全機能を独自実装しない。

既存の有力実装から、
- UI interaction
- workflow
- reference semantics
- queue/history
- timeline
- continuity
- low-VRAM recipe
- still-image route

を必要な単位だけ採用する。

一本の巨大forkへ全面依存するのではなく、薄い統合層で必要部分を縫い止める。
これを本計画では `Patchwork Integration` と呼ぶ。

### 1.2 まずH3 VIDEOで遊べる状態にする

最初の成功条件は、**ComfyUI node graphを意識せずH3 VIDEOを生成できること。**

Studio、Storyboard、3D、Mangaを待たない。

### 1.3 H3 Stillは初期から「受け入れ可能」にする

H3 Stillを初期の主目的にはしない。

ただし現在、
- ordered multi-reference
- source anchor
- semantic reference roles
- T2I / I2I / REF2VA still
- short temporal packet
- experimental T=1
- still-specific decode
- detail refine

が急速に実用化している。

そのためH3 VIDEO Skinの内部schema / adapterは、将来Still requestを追加しても壊れないようにする。
初期UIでStillタブを完成させる必要はない。

### 1.4 Illustrious MangaをH3都合で変更しない

Illustrious Mangaは現在のScene / Panel / Region / Character / authoring semantics完成を優先する。

H3側の共通UIへ将来載せることは意識するが、途中でschemaを共通化しない。

### 1.5 H3 MANGAは最後

H3 VIDEO、Studio、Illustrious Mangaが実働し、Still研究も蓄積した後に開始する。

H3 MANGAは既存Illustrious Manga runtimeの拡張として固定しない。
独立制作モードとする。

## 2. 長期構造

```text
Tegaki / Production Environment

Shared
├─ Project
├─ Asset
├─ Character / Reference
├─ History
├─ Job / Queue
└─ Settings

Production modes
├─ Illustrious Manga
├─ H3 Video
└─ H3 Manga       ← 最後

Generation adapters
├─ Illustrious / Anima
├─ H3 FL2VA
├─ H3 REF2VA
└─ future model
```

H3 Stillは当面独立productではなく、

```text
H3 Generation Capability
├─ Video
└─ Still
```

としてbackend側に余地を作る。

将来的なUIは `[Manga] [Video]` または `[Illustrious Manga] [H3 Video] [H3 Manga]` を候補とし、今は固定しない。

## 3. H3 Patchwork Integration方針

### Minimal Web Skin参考
- AntaresAlice/h3-webui
- onigirikiller/minimax-h3-webui

見るもの:
- app shell
- generate flow
- queue
- history
- workspace
- ComfyUI HTTP/WS separation
- simple form UX

### H3 backend simplification参考
- ComfyUI native H3
- ComfyUI-MiniMaxH3-Easy

見るもの:
- semantic input
- media routing
- model route
- ComfyUI graph abstraction

### H3 Still技術参考
- ComfyUI-MiniMax-H3-Image-Studio
- ComfyUI-MiniMax-H3-Studio
- ComfyUI-MiniMax-H3-Edit系

見るもの:
- ordered references
- semantic role
- source anchor
- still extraction
- T=1 experiments
- route validation
- VAE tiling
- OOM fallback
- Still metadata

### Studio / Timeline参考
- ComfyUI-H3Studio
- MiniMax H3 Director系

見るもの:
- timeline
- retake
- continuation
- reel
- partial regeneration
- cast
- prompt compiler
- Recipe Resolver

### 長期研究
- MiniMax-H3-Director-Cut-Studio
- Unsloth Desktop
- FastH3 / VSA
- PDD
- future 3D Previz tools

## 4. GUI設計方針

Tegaki H3 UIは「ComfyUIを見せない」だけでなく、制作ツールとして触り続けたくなるUIを目指す。

基本:
- modern dark / neutral visual
- restrained accent
- wide / horizontal production flow
- asset thumbnail中心
- large preview
- persistent workspace
- advanced settingsはprogressive disclosure
- mode / recipeの技術名を通常画面で過剰露出しない
- diagnosticでは実際に使われたrouteを確認可能
- reference roleをchip / badgeで視認
- Generate / Queue / Resultが常に追える

初期レイアウト候補:

```text
┌ Project / Assets ┬──────── Preview / Work Area ────────┬ Inspector ┐
│                  │                                      │           │
│ reference cards  │             RESULT                   │ Prompt    │
│ history          │                                      │ Settings  │
│ cast             │                                      │ Generate  │
└──────────────────┴──────────────────────────────────────┴───────────┘
                         Queue / History
```

TimelineはH1で入れない。
後からbottom areaをTimelineへ成長させる。

### Astra UI Review Gate

GUI本実装前に必要ならAstraをスポット投入する。

Astraには、
- shortlist GUI
- screenshots
- feature matrix
- H1 scope
- Tegaki constraints

だけを渡す。

Astraにrepository全体の再設計を自由にさせない。

出力:
- screen hierarchy
- component inventory
- interaction rules
- visual direction
- what to reuse
- what not to copy

その提案をWeb GPTで監査し、Card化してからLUNAへ渡す。

## 5. H3共通Request Schemaの最小要件

H1段階では完全な共通schemaを作らない。

ただし以下のsemantic fieldをnode IDから分離する。

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

初期Video UIが `generation_kind=video` しか使わなくてもよい。
Stillを後から追加可能にすることが目的。

## 6. Memory Profile

対象PC:
- RTX 4070 12GB VRAM
- 64GB system RAM

H3のmemory behaviorはmodel / ComfyUI version / Ref2VA / decode pathで変動する。

UI上で「12GB対応」を固定値にしない。

例:

```text
SAFE_12GB
BALANCED
QUALITY
EXPERIMENTAL
```

SAFE_12GBではadapterが、
- pruned INT8
- host offload
- model unload
- conservative resolution
- decode tiling
- reference size制限
- conservative temporal length

等を選択できるようにする。

具体値はbenchmarkで確定する。

## 7. Runtime / Sampling Profile

高速化をbase workflowへ埋め込まない。

```text
Base Quality
Stable Fast
Experimental
```

の三段階を基本とする。

- Base Quality: 最も再現性が高いnative path
- Stable Fast: 一定期間実績が積まれたTurbo / LightX等
- Experimental: FastH3 / VSA / PDD / 新Turbo / community T=1等

Experimentalが壊れてもBase Qualityで制作を続行できること。

## 8. Adoption Cooling Gate

新しい高速化・量子化・custom runtimeを即default採用しない。

### 通常Fast Path

最低条件:
1. 公開から7日以上
2. 重大recipe変更が直近72時間ない
3. consumer GPU複数環境で成功報告
4. 12GBまたは16GB帯の実測あり
5. artifact / sampler / steps / strengthを固定可能
6. upstream ComfyUIとの互換性確認
7. Base Qualityへ容易に戻せる
8. license / provenance確認

### 新runtime / sparse kernel / FastH3級

原則14日程度の観察期間を許容する。

研究用Experimental profileとして試すだけなら早期導入可。
ただしdefaultにはしない。

## 9. AI運用

### LUNA

通常実装担当。

ただし最初から大量のreference repositoryをcloneしない。
最初に作るのはReference Inventory。

例:

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

Astra / Web GPTで採用が決まったものだけlocalへ取得する。

### Web GPT
- research
- shortlist
- GitHub diff audit
- gate review
- candidate comparison

### Sol
- difficult implementation
- difficult bug
- bounded refactor

### Astra
- GUI composition
- difficult architecture
- major schema boundary
- integration decision

スポット参戦。
Subagentは原則抑制。

## 10. Phase H0 — Groundwork / Research Freeze

目的:
H3実装を安全に始める。

実施:
- H3 directory / docs / workflow棚作成
- GITHUB_H3.txt
- Reference Inventory
- current ComfyUI H3 support確認
- model / license確認
- shortlist固定
- RTX 4070 12GB向けbaseline確認

禁止:
- Studio全部入り
- H3 Manga
- Illustrious変更
- 大量fork
- 新Fast runtimeのdefault採用

Gate:
Web GPT review。

必要ならこの後にAstra UI Review。

## 11. Phase H1 — H3 VIDEO Minimum Skin

目的:
最小手で遊べるもの。

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

Still UIを完成させない。
ただし内部request / asset / reference表現がStill追加を妨げないこと。

GUIはPatchwork Integrationで構築する。

## 12. Phase H1S — H3 Still Capability Spike

H1 VIDEOを壊さず、短い検証Cardとして実施可能。

目的:
H3 Stillを将来取り込めることだけ確認。

試すもの:
- T2I
- source anchored I2I
- ordered multi-reference
- semantic reference roles
- output still
- metadata restore

参考:
- MiniMax H3 Image Studio
- H3 Still Studio

成功条件:
Stillのproduction UI完成ではない。

`H3 request -> adapter -> still output`
が成立すること。

このPhaseはH1とH2の間、またはH2中に差し込める。

## 13. Phase H2 — Practical Skin

H1を実使用して不足を補う。

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

この段階でもTimelineを必須にしない。

## 14. Phase H3 — H3 VIDEO Studio

候補:
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

Recipe ResolverはユーザーへT2V/I2V/FL2VA/REF2VAを毎回選ばせない方向。

## 15. Phase H4 — Storyboard / Editing / Previz

必要性が実使用で確認されたものから追加。

- Storyboard
- Storyboard ↔ Timeline
- camera
- action
- dialogue
- sound
- simple editor
- NLE export
- 3D Previz

3D PrevizはResearch扱いから開始。
他者が先に良いものを作れば待って取り込む。

## 16. Illustrious Manga完成Phase

H3 VIDEOが実働したらIllustrious Mangaへ比重を戻す。

優先:
- Scene
- Visual Panel
- Region
- Character
- Workflow reliability
- Minimum-Hand UX
- browser acceptance
- production stability

H3側へ合わせるために途中でschemaを変更しない。

## 17. UI統合Phase

H3 VIDEOとIllustrious Mangaが双方実働した後、`[Manga] [Video]` 等の共通shellへ統合。

共通化候補:
- shell
- project selector
- asset
- character/reference
- history
- queue/job
- settings

共通化しない:
- Manga Scene semantics
- Manga Region semantics
- H3 Timeline runtime
- backend-specific recipe

## 18. H3 MANGA — 最終研究Phase

開始条件:
- H3 VIDEO実働
- Studio基本構造成立
- Illustrious Manga実働
- H3 Still知見蓄積
- ordered reference / CAST / rough anchorの実績あり

研究候補:
- Page
- Panel
- Shot
- Storyboard
- Character refs
- motion-aware panel
- temporal continuity
- animated comic
- cinematic manga
- video-to-panel
- panel-to-video

現在のIllustrious Manga runtimeへ直接結合することを前提としない。

## 19. Image Finish / Bake

将来:

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

H3をcomposition / reference reasoning側に使い、静止画モデルを最終漫画画質側に使える余地を保持する。

## 20. Current Priority

```text
1. LUNAでH3地均し
        ↓
2. Web GPT監査
        ↓
3. H0 Reference Inventory / shortlist
        ↓
4. 必要ならAstra UI Review
        ↓
5. LUNAでH1 Minimum Skin
        ↓
6. H1S Still Capability Spike
        ↓
7. H2 Practical
        ↓
8. H3 Studio
        ↓
9. Illustrious Manga完成
        ↓
10. UI統合
        ↓
11. H3 MANGA
```

H1Sは小さな検証であり、H3 MANGA開始を意味しない。

## 21. 禁止事項

- 最初から一本の巨大GUI forkへ固定しない
- 最初からStudio全部入りにしない
- 新Turboを即defaultにしない
- FastH3/VSAを現時点で必須化しない
- H3 Stillの進展を理由にH3 MANGAを前倒ししない
- H3都合でIllustrious Mangaを変更しない
- GUIをnode IDへ密結合しない
- reference OSSを無差別cloneしない
- Astraに無制限の再設計をさせない
- LUNAへ候補選定前の大量移植をさせない

## 22. 開発思想

**既にあるものは使う。**

**まず動かす。**

**良い部分だけ縫い止める。**

**他者が進める部分は待てる。**

**高速化は本線と分離する。**

**Stillの進歩は受け入れるが、H3 MANGAを急がない。**

**独自性が必要な部分へ開発時間を残す。**
