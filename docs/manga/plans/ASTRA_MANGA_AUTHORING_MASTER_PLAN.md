# 最小手数で漫画Draftを作る — Strategic Master Plan

発行: 2026-09-06 / revision 1 / 状態: 計画発行、実装・Owner制作受入は未実施。
対象は `ComfyUIPortable/` のみ。上位戦略の正本は本書。個別実装はWEB GPT-SOLが限定カードにしてGemini 3.8 / Antigravity2へ渡す。

## 1. 結論と優先順位

**コマ枠と短いシーンPromptから漫画案を回し、必要なキャラだけ登録・配置して、Seedによる発想の幅を残したまま狙いを強める。**

最優先は入力手数、次に登場・位置の誘導、その範囲で生成の揺らぎを残す。Pose Editorの完成や研究Workflowの全再実行を先行条件にしない。

最新Owner依頼を優先し、v2依頼書の「最初にCAST必須」は採らない。**かんたん（Scene内に人物も記述）→ CAST配置 → ラフガイド補強 → 必要部分のRefine**の順。両モードの契約は最初から共通にし、画面・実装カードは分ける。

| 優先 | 利用者ができること | 最初から要求しないもの |
|---|---|---|
| M1 | 解像度・テンプレート・Scene領域・Prompt・任意コマ枠画像から生成、Seed変更 | CAST登録、人物矩形、骨格、個別LoRA |
| M2 | CASTを一度書き、複数Sceneへ複数回配置 | 全SceneをCAST方式へ変換 |
| M3 | 白ハゲ・漫画ラフを読み、人物領域との対応を強める | 自作Pose/描画ツール |
| M4 | 必要な領域だけ形状・遠近・Refineを細かくする | 常時表示の詳細設定 |

## 2. 現状固定と証拠の扱い

- Local HEAD: `743ce53a5d3f02554699ebc7afa4859a9e6d2716`。
- 実装Review Target: `5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8`。ローカル旧入口と公開rawを照合。同SHAからHEADまで本projectの `custom_nodes_custom/ workflows/ scripts/ docs/` に差分なし。
- 旧入口はPhase 3L完了を宣言。ただし `docs/manga/verification/PHASE3L_PRESENCE_EVALUATION.json` の視覚評価はPENDING。`all_passed`は制作受入を意味しない。
- 既存の型・compiler・workflowは再利用候補。Backend採用報告、Workflow配線、実行ログ、画像、Owner評価を別々に読む。監査詳細は[棚卸し](ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)。本ターンは生成/Browser検証をしていない。
- 本projectに `docs/manga/STATUS.md` / `docs/TECHNICAL.md` は作業開始時存在しなかった。Tegaki本体のPhaseへ接続しない。今後の現在地は今回追加の `docs/manga/STATUS.md`。

## 3. ユーザーの概念

| 概念 | 意味 / 所有する情報 |
|---|---|
| Page | 解像度、共通Style、Scene配列、Visual Frame、Guide、生成設定 |
| Scene | 「この辺で何が起こるか」。独立ID、Prompt、粗い領域、入力モード |
| CAST | 「誰か」。恒久ID、表示名、Identity Prompt、任意Negative |
| Appearance / Instance | 「このSceneのこの辺に出演」。固有ID、cast_id、scene_id、領域、演技差分 |
| Visual Panel Frame | 見える枠線・余白・境界。意味領域と別レイヤー |
| Guide | コマ枠画像/漫画ラフなどの入力assetとページへの配置変換 |
| Candidate | Seedだけでなく、その生成時の入力・モデル・設定・画像への参照 |

SceneとPanelを同一視しない。`Panel owns Scene`は旧互換importに限定。`Scene owns rough region`を、`Page ├ Scenes / └ Visual Frames`として実現する。Sceneは重なってよく、見える一コマに複数Sceneも可能。人物はコマ1・3・4へ同一CASTを参照する三つのinstanceとして配置する。

## 4. Architecture境界と最初の技術判断

```text
ComfyUI Authoring Surface → versioned Authoring Document
                           ↓ validate / normalize
                      Semantic Compiler
                           ↓ derived prompts / masks / guides / generation plan
                       Backend Adapter
                           ↓
              existing regional execution + ControlNet + sampler
```

決定: この方向を採用する。既存 `REGION_SPEC/CAST_SPEC/PAGE_COMPILE_PLAN` の意味を黙って変えない。新しい永続形式の詳細・version・移行表はM0カードで固定し、SOLレビュー後に実装する。`MANGA_AUTHORING_DATA`は設計上の呼称であり実在APIとして扱わない。

既存KOMAがSceneと枠を兼ねる部分には明示的な旧形式adapterを置く。新UIから旧REGION_SPECへ無損失で表現できる範囲だけ変換する。独立Scene・重なりを表現できない場合は、compiler入力をversion追加して拡張し、Sceneを無理にPanelへ偽装しない。旧workflowの読み込みを壊さない。

### 契約で固定すべきこと

1. Page正規化座標を新文書の基準とし、canvas表示変換/画像fit変換は明示保持。旧panel-local座標はimportで変換。解像度変更は正規化領域を維持する。
2. Scene移動は所属instanceも同じ移動量で移す。Scene拡縮時は所属instanceを比例変換する。枠線の移動はSceneを動かさない。後段の「Scene領域だけ編集」は別操作。
3. Scene数・CAST数・出演数は可変配列。追加/複製/削除で入力欄と領域が連動し、固定6枠の隠し制限を引き継がない。初期性能確認は1/2/4/8 Sceneと同一CAST3出演。対応上限は実測して表示する。

   Sceneが0件なら空の編集状態を保存できるが、生成時は「Sceneを追加」を案内してqueueしない。勝手に全画面Sceneを作らない。
4. CASTを複製してもinstanceの編集と混同しない。CAST削除は参照数を表示し、使用中は解除/置換を明示。Scene削除とUndoは所属instance・Promptを一括復元。
5. `simple` / `cast`はScene単位。簡単モードには人物もScene Promptへ書ける。CASTモードではidentityはCAST、演技はinstance、共通出来事/背景はSceneへ。ページ内混在可。
6. モード切替はテキストを解析して自動削除しない。簡単モードの文面を保持し、CAST化時は人物説明の二重適用をInspectorで確認できる。簡単へ戻すときはCAST設定を退避保持し実行から外す。トグルで情報を消さない。
7. 保存の正本はauthoring document一つ。UI表示stateとcompiler出力を別の編集正本にしない。未知フィールドを保持し、未知versionは上書きせず拒否。workflow保存→再読込も同じdocumentを復元する。
8. MVPは矩形の移動・拡縮・重なり。変形要求を削除せずM4にpolygon/頂点編集を置く。shape種別を拡張可能にし、旧adapterが矩形化して情報を落とす場合は黙って出力しない。

### 重なりとPromptの意味

重なりは「人物の前後関係を保証」しない。編集の重なり順と生成マスクの解決順を混同しない。M0で順序とmask policyを固定する。初期提案は、Scene同士は保存順による決定的優先順位、同じSceneの人物は重複部分のweightを正規化、Scene背景は人物maskのunionを差し引く。生成用maskプレビューで解決後を見せる。これらは未実装の提案であり、既存Impactの順次処理にそのまま保証があるとはしない。M2でswap・overlapを比較し、失敗を隠すfeather調整を増やさない。

Promptは全CASTをGlobalへ連結しない。必要なScene/instanceごとにencodeし、Styleだけを共有。簡単モードではScene Prompt、CASTモードではScene context + 当該CAST identity + 当該actingを責務ごとにcomposeする。人物を含まないGlobal/baseとbackground経路が重要。BREAKを増やせば解決するという設計は採らない。長い入力のtoken/chunk状況は詳細に出し、黙って切り捨てない。

## 5. Workflow / Backend戦略

主経路は一枚のページへ複数の局所conditioningを渡す。**キャラ別に最終画像を生成して貼り合わせる方式は初期主経路にしない**。人物間接触や背景の連続性が必要なため。局所再生成やScene別生成/合成は、ページ一括方式の品質が実測で不足する場合の後段候補。

- 再利用: 現行compiler、CAST参照、mask計画、Impact adapterと既存regional sampler。
- Inspireはregional prompt構築、Impactはsampling等の役割として分ける。名前だけで交換可能とはしない。ACN採用は実ノード配線・実画像比較を済ませてから昇格。
- Sampler、scheduler、汎用ControlNet、汎用Mask/Pose editorは新作しない。
- Illustrious/SDXLの具体的checkpointと互換ControlNetを実装カード開始時に確認する。SD1.5 ControlNetを代用しない。モデル名/hash、VAE、拡張SHA、profileを記録。
- referenceを基準にする。既存fast_draft_12は任意の高速化候補。速度のためにHyper-SD LoRAを必須化せず、対象checkpointで画質と所要時間を比較する。
- Generate x4は原則4回の逐次queueで、latent batch=4を必須にしない。VRAM、elapsed time、途中失敗を記録。確定Seedと入力snapshotをqueue前に保存する。
- Style LoRA/CAST LoRAはlocalityが違う。CAST個別LoRAとreferenceは後段、実行可能と証明するまで装飾だけの有効欄を出さない。RegionalLoRALabは別projectの将来候補。

一次資料: [Illustrious model card](https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0)、[Inspire](https://github.com/ltdrdata/ComfyUI-Inspire-Pack)、[Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)。2026-09-06閲覧。これらの存在は手元の組合せの品質保証ではない。

## 6. 揺らぎの扱い

| Draftで入力を固定する | Seedで揺らしてよい |
|---|---|
| CAST identity、出演先、Scene/人物の粗い位置、指定した枠ガイド | 演技・ポーズ・表情細部、髪/服の細部、背景、camera nuance |

固定とは条件を一定に保つ意味。生成画像の同一性/人数/枠一致を保証する語にしない。候補の「再利用」はSeed + 入力snapshot + model/profileを戻す。モデルや実行環境が変わった完全画素再現は保証しない。「構図固定」という強いラベルは制御経路ができるまで使わない。

## 7. Roadmap（旧Phase 3M以降の対応）

| Card | 範囲 / 先行条件 | Product gate | 技術gate |
|---|---|---|---|
| M0 / 3M-0 | Scene独立契約・旧import境界。最初の一件 | 2 Scene＋独立枠のfixtureを説明できる | version、ID、mode、座標、重なり、serialize、旧import表をSOLが固定 |
| M1 / 3M-1 | かんたんAuthoring Surface＋実行 | 2 Sceneでコマ枠＋Prompt→生成→Seed変更、graph配線編集ゼロ | CAST空でcompile、0/1/2/4/8配列、save/reload、queue/error、Browser |
| M2 / 3M-2 | CAST/複数instance。同じsurfaceを拡張 | 同一CASTが1/3/4へ出演、2人同Scene、simple/cast混在 | ID維持、mode往復、swap/重複mask、prompt局所性 |
| M3 / 3M-3 | ユーザー漫画ラフ入力と適合ControlNet | 白ハゲA→CAST A、B→Bの誘導比較 | guide fit、入力hash、control on/off、実ACN経路があればその比較 |
| M4 / 3N | polygon等の変形＋必要部分のRefine | 非矩形領域を保存して生成、遠近補助を任意表示 | shape migration、mask一致、未対応adapterの明示拒否 |
| M5 / 3O | 必要性を測ってskin拡張、候補管理、H3共通shellへのManga tab接続 | 初回/反復手数を削減し同一GUIからManga/Videoを切替 | 同じdocument・queue bridgeを再利用しdomain stateを混同しない |
| Later | Pose asset、SubScene、Interaction、local LoRA | 利用者が必要な時のみ | 機能ごとの契約・画像評価 |

順序はM0→M1→M2→M3。M1に任意コマ枠画像の既存ControlNet経路を含め、M3まで枠入力を待たせない。M1/M2を一枚の巨大カードにまとめない。M3と形状/skinの優先を変えるのはOwnerの実操作結果を受けたSOL判断でよい。

## 8. Acceptance gates

全カードで `code/test`, `runtime`, `visual`, `Owner UX acceptance` を分ける。PENDINGはPASSへ丸めない。既存の自動評価JSONを生成するだけで視覚評価済みにしない。

| Gate | Fixture / 比較 | 提案合格線（未測定） |
|---|---|---|
| 手数 | preset読込済・2 Scene・2 Prompt・コマ枠あり | 初生成までUI操作12以内、必須本文2欄、Advanced展開0、配線変更0 |
| 反復 | 同じ入力で別Seed | 1操作。候補Seed再利用も1操作 |
| CAST | 2 CAST初回登録→2 Scene→4出演 | 追加の構造操作14以内、Identity本文2欄だけ。既存CASTなら再入力0 |
| 視覚M1 | 2/4 Scene、frame only、固定Seed 42/123/2026/9001 | 全出力提示。各fixtureで4案中3案以上がScene内容/大まかな配置に使えることをOwnerが判定 |
| 視覚M2 | 左右swap、同CASTを1/3/4、2人同Scene、Scene重なり、人物重なり | 指定出演の欠落/余計な登場/identity混線/大位置を別採点。代表fixtureで4案中3案を使えること |
| 視覚M3 | 同Seedでframe only vs dummy guide、A/B位置入替 | rough対応が改善し、演技の揺らぎを残せる。改善がなければガイド経路未受入 |

手数はクリック/タブ選択/drag/drop/ファイル選択確定を各1、文字入力欄数と入力時間は別計測。初回インストール/モデル設定は別計測し隠さない。上記数値は製品目標であり実績でもモデル成功率の主張でもない。SOLは生成前に評価fixtureと基準をカードで固定し、失敗後に閾値を下げてcloseしない。4 Seedで一般化せず、Ownerの異なる題材でも一巡確認する。

失敗時はframe-only → CAST regions → rough guideの各差分を固定条件で調べる。新しいPose/Interaction機能を増やして原因を隠さない。図形編集と画面整合はCPU/Browser、画質は実GPU出力で評価する。

## 9. 旧計画との差分

| 分類 | 判断 |
|---|---|
| KEEP | CAST/instance分離、semantic compiler、既存Backend活用、直接canvas操作、後段Refine |
| CHANGE | CAST必須入口→Scene-only先行。Panel中心入力→Scene/Frame独立。Phase完了宣言→証拠別gate |
| NEW | Scene単位の簡単/CAST混在、手数予算、Seed snapshot、可変数、非破壊mode切替、旧入口統合 |
| DEFER | Pose/握手/SubScene専用UI、汎用mask editor、個別LoRA locality、candidate pose抽出 |
| DROP（主導線から） | 全人物Global連結、BREAK頼み、全Phase再読、node数を成果とする評価、独立二重保存正本 |

旧中間計画は戦略正本ではなく履歴。型仕様書・実行コードは本書だけで変更済みにはならない。[整理指示書](ASTRA_GEMINI_CLEANUP_INSTRUCTIONS.md)に従い参照を保全する。

## 10. SOLが次に作る一枚

M0だけを発行する。読む範囲は本書→UX→棚卸しの契約ギャップ→該当source。成果はversioned document提案、2 Scene/独立Frame/空CAST/繰返し出演のJSON fixture、旧形式移行表、M1対象file一覧。実装変更・Sampler変更・Pose追加を含めない。承認はSOLの技術レビューで進め、製品方針の変更だけAstra/Ownerへ戻す。詳細運用は[実行プロトコル](ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md)。
