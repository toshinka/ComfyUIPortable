# Minimum-Hand Manga UX Blueprint

2026-09-06 / revision 1 / 設計。実装済み画面ではない。戦略は[Master Plan](ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)。

## 主画面

```text
解像度 [縦 ▼] [幅 × 高さ]   Style [漫画 ▼]   [共通Prompt ▸]
作り方 [かんたん] [CASTを使う]      [モデル/生成設定 ▸]

[Scene編集] [キャラ配置]                  Inspector
┌────────────────────────┐    ┌────────────────────┐
│ Scene 1       Scene 2  │    │ Scene 2            │
│ [A] [B]                │    │ Prompt [           ]│
│      frame/guide淡色表示│    │ [+ Scene] [複製]   │
│ 領域は重なってよい      │    │ [削除] [詳細 ▸]    │
└────────────────────────┘    └────────────────────┘
Scene [1] [2] [+]    [枠・ラフ画像を追加] [表示レイヤー ▸]
Seed [数値] [ランダム] [再利用]    [生成] [4案生成] [進捗/取消]
結果サムネイル  [候補を選択 → Seed再利用 / 入力復元]
```

かんたんではCAST欄/キャラ配置タブを隠す。CASTを使うとCASTチップ列 `[Alice] [Bob] [+]` とキャラ配置タブが出る。Scene InspectorでそのSceneだけ簡単/CASTを切替可能。Page上の切替は初期表示の入口であり、全Sceneの既存入力を破壊しない。

## 最初の30秒

生成環境が準備済みなら、2 Sceneのサンプルを開く→Sceneをクリック→Promptを書き換える→生成、を目標とする。空白状態でも領域dragでScene追加、作成直後にPromptへfocus。モデル導入まで30秒で終わるとはしない。

モデル選択・Styleは前回値を保持。初回はモデルが未選択なら生成欄の近くに設定導線を出す。解像度でcanvasの見かけの縦横比も変える。

## Canvasと入力の対応

- Scene用・キャラ用は**一つのページ座標を共有する二つの編集タブ**。二つの独立documentにしない。非対象レイヤーは薄く表示し、誤ってdragしない。
- 選択Sceneのカード/領域/Promptを色・名前で同期。重なりで隠れた領域は一覧から選べる。重なり順の変更は詳細へ。
- Promptは「Sceneタブで対象選択＋単一Inspector」。人数×Scene数の常時テキスト欄を並べない。入力途中のScene切替も保存し、Undoを保持。
- 領域追加/複製/削除でSceneタブと入力欄が増減。数値でNを減らして末尾データを消すUIにしない。件数は配列から表示する。
- CASTチップを選んで領域をdragすると出演instanceを一つ作る。同じCASTを1/3/4へ置いてもIdentity Promptは一回。必要なら「別Sceneへ出演を複製」を後から追加。
- キャラ領域の大きさは粗い占有範囲。小さい矩形だけで遠景を保証しない。Near/Far、Bust/Full等はM4以降の任意shortcut。
- 矩形の移動/四隅拡縮/重なりはM1/M2、非矩形の頂点変形はM4。初期に精密mask描きを強要しない。

## かんたん→CASTの導線

Scene本文に人物も書いて生成できる。反復登場/位置を揃えたくなったSceneだけ「CASTを使う」を選ぶ。Identityを登録し、領域を置く。既存本文は保持し、本人が本文から重複説明を整理できる。自動で人物抽出したふりをしない。

CAST選択時のInspectorはMasterを編集するボタンと今回の演技欄を明確に分ける。Master変更が何出演に届くか表示。元Scene本文とCASTデータは往復切替で消えず、現在の方式の入力だけをcompilerに渡す。

## Frame / Guide

入口ボタンは「枠・ラフ画像を追加」。画像をdrop→Pageへfitしたpreviewを出す。枠だけ/人物も描いたラフ、の用途を選べる。一般的な枠画像はM1で既存ControlNet経路へ、人物ラフのCAST対応はM3で評価する。

編集用ガイドと生成へ送るガイドを同じだと仮定しない。生成に使う画像をpreviewでき、offも一操作。ガイドの強度・開始終了・preprocessorは詳細を開いた時だけ表示。Frameを動かしてもSceneは勝手に追従しない。将来の枠template→Scene初期配置は一回のcopyとして扱う。

## 手数予算

| ケース | 構造操作の概算上限 | 必須テキスト欄 | Advanced展開 |
|---|---:|---:|---:|
| 既存2 Scene templateを使う | 12 | Scene本文2 | 0 |
| 2 CAST新規＋4出演を追加 | 追加14 | Identity2（演技は任意） | 0 |
| 同条件で再生成 | 1 | 0 | 0 |
| ガイド差替 | drop＋確認の2 | 0 | 通常0 |

上限は設計目標、実測前。ファイル選択等も実測時に数える。キーボード入力時間、初回導入は別に記録。実装により増えた手順はSOLが導線修正し、画面を増やして解決しない。

## ComfyUIからskinへの判断

| 面 | 利点 | 負担 | 判断 |
|---|---|---|---|
| 整理済みnode workflow | 既存接続を再利用、debugが容易 | 複数node間移動、Promptが散る | 実行と互換の基盤として残す |
| ComfyUI extension panel / modal | 一画面にまとめやすい、既存queue利用 | frontend API追従が必要 | **最初のsurfaceの推奨**。既存canvas操作を共通化 |
| 独立SPA / A1111風skin | タブ/条件表示/広いcanvasの自由度 | state保存、queue、認証/接続管理の追加 | M1/M2で手数目標を満たせない時に前倒し |
| Comic Creator fork | 作品/ページ機能が揃う | 大きなeditorとstate移行を背負う | 棚卸しの先行技術監査を参照。即採用しない |

M1でsurfaceを作る際、nodeの内部を寄せ集めた別々のstateを書かない。ComfyUIのgraphは「詳細/Workflowを開く」へ戻せる。後のskinもdocument/compiler/queue adapterを共用する。first draftのために複数nodeのPrompt欄へ移動するならsurface gateは未達。

長期の製品surfaceは、H3動画ツールと同じTEGAKI shell/skin内に置き、上位tabで
`Manga`と`Video (H3)`を切り替える。共通化するのはnavigation、visual language、workspace入口から始め、
Manga document/compilerとH3 job/runtime stateは各tabが所有する。tab切替で入力を失わない契約と
両domainの独立回帰が揃うまで、共通shell実装をM3/M4の機能Cardへ混ぜない。

## 後段の出現条件

- CAST: ユーザーが反復登場/個別配置を必要とした時。
- Negative/解決後mask/重なりpriority: 選択対象の「詳細」。
- Pose/Interaction: 候補選択後の「Refine」。主導線には出さない。
- SubScene: 一つの出来事をさらに分けたい時。既存のadvanced toggleでデータを消す実装は流用しない。
- CAST LoRA/reference: 実際のBackend対応と適用範囲を示せる段階。未配線の入力欄を作らない。

MRPから残すのは領域の直接操作、Promptとの対応、即生成。固定KOMA数、全人物をGlobalへ押し込む運用、Sceneと枠の同一視は引き継がない。EasyReforgeExtensionの計画/実装は今回閲覧せず、Owner説明と現行ComfyUI側を根拠とする。
