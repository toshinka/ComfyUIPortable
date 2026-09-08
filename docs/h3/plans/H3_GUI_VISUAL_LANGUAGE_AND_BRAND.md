# H3 GUI Visual Language and Brand Direction

更新: 2026-09-08 JST

## Status

これは H3 GUI の実装仕様ではなく、Astra の UI review に渡す visual
language の基盤である。コンポーネント、CSS、frontend framework、workflow、
custom node、model、schema はこの文書から導入しない。

## Brand position

TEGAKI の Futaba 系 maroon / cream は、古い掲示板 UI を再現するための
テーマではない。これは TEGAKI の文化的な DNA として保持する一方、H3 は
2020年代の production tool として、階層、余白、状態表示、キーボード操作、
preview、progressive disclosure を現代的に設計する。

目標は「懐かしい配色の generic dark SaaS」でも「全部を maroon に塗った
theme」でもない。軽い workspace と明確な production control を持つ、TEGAKI
らしい authoring surface である。

Brand identity may be distinctive. Basic interaction grammar should remain
familiar unless there is a clear production benefit. Known words such as
Generate, Reference, History, Queue, Timeline, Inspector, Project, Shot, and
Take are not renamed merely to make the brand appear more original.

## Canonical palette evidence

値は live repository の tegaki_work/styles/main.css にある既存 token を
参照する。ここで新しい RGB 値や別名 token を増やさない。

| Token | Value | 初期の役割 |
|---|---|---|
| --futaba-maroon | #800000 | identity、primary text、primary action |
| --futaba-light-maroon | #9c3835 | selected rail、強調 surface |
| --futaba-medium | #b8706b | secondary emphasis、disabled / muted の基準 |
| --futaba-light-medium | #d4a8a0 | border、divider、supporting surface |
| --futaba-cream | #f0e0d6 | warm panel、section、入力領域 |
| --futaba-background | #ffffee | 主 workspace、page background |
| --text-primary | #800000 | primary readable text |

意味色（たとえば success、info、warning、error）は、状態を伝えるために
既存の TEGAKI token / semantic token を先に確認する。green / blue / orange
を追加するとしても、ブランド主色の代替ではなく、状態を区別するための
限定的な accent とする。ここでは値を新規決定しない。

## Surface and hierarchy rules

1. Workspace は --futaba-background と --futaba-cream を基礎に、長時間
   見ても疲れにくい明るい面を作る。
2. Maroon は identity と重要な action / selected state に集中させ、全ての
   border、label、background を maroon にしない。
3. Primary action、current selection、warning、rendering / queue state は、
   色だけでなく形、位置、text、icon、status copy でも区別する。
4. Rail、panel、canvas、timeline、status は面と階層を分ける。余白を削って
   情報を一画面へ詰め込むことを「professional」とみなさない。
5. Light / dark surface の採用はブランド都合ではなく、preview、focus、
   contrast、長時間作業の視認性で判断する。dark surface を採る場合も
   generic dark SaaS の黒紫一色にはしない。

## H3 Video initial authoring direction

H3 初期 GUI review の入口は、H3 VIDEO を minimum-action で生成できる
production surface とする。

- Project、Shot、Take、Prompt、Reference、Generate、Preview、Queue、History、
  Continuation、Resolution、Duration、Seed、LoRA、Runtime Profile を主要語彙
  とする。
- Studio 以降では Timeline、Storyboard、Continuity、Retake、Segment が加わる。
- UI は操作の結果を preview、progress、queue、history、error/status visibility
  で返し、設定項目の数で「本格的」に見せない。
- 必要な設定だけを段階的に出し、H3 Video / Still / Studio の境界を navigation
  と wording で読めるようにする。
- Panel、Page、Manga semantic region は初期 H3 VIDEO GUI review の必須論点に
  しない。

Illustrious Manga has its own Scene / Panel / Region / Character semantics.
Do not redesign or merge those semantics during this H3 Video review.

## Cognitive design anchors

### 思考の水平 / Cognitive Level

TEGAKI の「思考の水平」は、同じ利用文化圏で広く定着している UI・操作概念を
基準面とし、ユーザーが既存知識をそのまま転用できる範囲では、不要な認知的段差を
作らないという設計原則である。

新しい操作体系を導入して基準面から高さを作る場合、その高さには明確な制作上の
利益が必要である。既知の production-tool convention をブランド独自性だけで
改名・破壊しない。

### Scope and information hierarchy

Scene、Shot、Asset、Runtime、Review は「思考の水平」の定義ではない。これらは
現在の context、workspace scope、information hierarchy として、今どの粒度を
扱っているかを示す。

### 思考のレンズ / Cognitive Lens

Cognitive Lens は、同じ Project / Asset / Job を目的別に見る切替である。
Project、Asset、Generate、Reference、Still、Video、Timeline、Diagnostic、
Review などを tab、segmented button、drawer、inspector、workspace switch 等で
扱う。新しい保存正本や別アプリを意味しない。

### Mountain

「山」は常に表示する階段ではない。新しい操作体系を要求する場合は、明確な速度、
明瞭さ、制御性、再現性、または新しい制作能力が頂上に必要である。必要な
complexity だけを progressive disclosure で現すことが H3 の review 基準である。

## Benchmark roles

参考対象は見た目をコピーするためではなく、役割を比較するために使う。

| Reference role | 取り出す観点 | 取り出さないもの |
|---|---|---|
| TEGAKI / Futaba heritage | palette、軽さ、文化的な識別性 | 古い掲示板の layout そのもの |
| 現行 Illustrious authoring | Manga-specific semantics と境界の確認 | H3 Video review への Panel / Region data model の持ち込み |
| ComfyUI / workflow tools | runtime、queue、再現性、debug の可視化 | node graph を H3 の入口にすること |
| 現代の creative production tools | hierarchy、preview、status、undo、focus | generic dark SaaS の外観 |
| Manga / storyboard tools | Studio later の Timeline、Storyboard、Continuity、Retake、Segment | 初期 H3 Video の必須論点にすること |

## Explicit anti-goals

- generic dark SaaS、黒紫中心、意味のない gradient、過剰な glassmorphism
- 画面全体を maroon にすること、または maroon を状態色の代わりに使うこと
- category / mode / setting を増やして authoring の難しさを隠すこと
- 実装前の mockup や screenshot を canonical UI として扱うこと
- H3 のために既存 Illustrious Manga の保存正本、runtime、workflow を変更すること
- この文書だけを根拠に CSS、asset、component、route を作り始めること

## Review output expected from Astra

Astra はこの文書をもとに、(a) palette の役割分担、(b) minimum-action H3 Video
entry の階層、(c) familiar production-tool convention と cognitive lens の
scope separation、(d) H3 Video / Still / Studio の境界、(e) queue / progress /
error / status visibility、(f) anti-goal への抵触リスクを review する。
Panel / Page / Manga schema、Illustrious semantic redesign はこの初期 review の
設計対象にしない。具体的な画面実装や最終配色の決定は、Web GPT が別途発行する
実装前の指示まで保留する。
