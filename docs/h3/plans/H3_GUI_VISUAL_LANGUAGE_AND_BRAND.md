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

## Authoring UX direction

H3 の入口は Scene-first / minimum-action を基本とする。

- 最初の画面は Scene を成立させるための最小入力、preview、次の一手を示す。
- CAST、pose、interaction、runtime tuning は必要になった時だけ progressive
  disclosure する。
- semantic Scene region（意味上の人物・背景・action 領域）と visual Panel
  Frame（見た目のコマ矩形）は同一視しない。可変・重複・再配置の余地を残す。
- UI は操作の結果を preview と state で返し、設定項目の数で「本格的」に見せない。
- H3 Video、Still、Studio、Illustrious Manga の境界は navigation と wording
  で読めるようにし、早すぎる統合で一つの巨大な mode menu にしない。

## Cognitive design anchors

Rev.3 の cognitive level、cognitive lens、mountain を visual language
にも適用する。

| Anchor | UI での意味 | Review question |
|---|---|---|
| Cognitive level | 今ユーザーが扱っている粒度（Scene、Shot、Asset、Runtime、Review） | 画面は現在の粒度を隠していないか |
| Cognitive lens | 同じ素材を別の目的で見る切替 | lens の切替がデータの複製や混乱を生まないか |
| Mountain | 乗り越える価値のある authoring の山 | complexity は結果の品質や再現性に見合うか |

「山」は常に表示する階段ではない。Scene-only entry から始め、必要な
complexity だけを段階的に現すことが、H3 の review 基準である。

## Benchmark roles

参考対象は見た目をコピーするためではなく、役割を比較するために使う。

| Reference role | 取り出す観点 | 取り出さないもの |
|---|---|---|
| TEGAKI / Futaba heritage | palette、軽さ、文化的な識別性 | 古い掲示板の layout そのもの |
| 現行 Illustrious authoring | scene / panel / layer の production semantics | H3 実装への早期統合 |
| ComfyUI / workflow tools | runtime、queue、再現性、debug の可視化 | node graph を H3 の入口にすること |
| 現代の creative production tools | hierarchy、preview、status、undo、focus | generic dark SaaS の外観 |
| Manga / storyboard tools | Scene、Shot、Panel Frame の思考単位 | semantic region と frame の固定的同一視 |

## Explicit anti-goals

- generic dark SaaS、黒紫中心、意味のない gradient、過剰な glassmorphism
- 画面全体を maroon にすること、または maroon を状態色の代わりに使うこと
- category / mode / setting を増やして authoring の難しさを隠すこと
- 実装前の mockup や screenshot を canonical UI として扱うこと
- H3 のために既存 Illustrious Manga の保存正本、runtime、workflow を変更すること
- この文書だけを根拠に CSS、asset、component、route を作り始めること

## Review output expected from Astra

Astra はこの文書をもとに、(a) palette の役割分担、(b) Scene-first の階層、
(c) semantic Scene と visual Panel Frame の分離、(d) H3 Video / Still /
Studio の境界、(e) anti-goal への抵触リスクを review する。具体的な
画面実装や最終配色の決定は、Web GPT が別途発行する実装前の指示まで保留する。
