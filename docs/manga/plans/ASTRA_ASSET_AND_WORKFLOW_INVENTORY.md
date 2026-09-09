# 資産棚卸し — Product Flow順

2026-09-06 / 対象実装SHA `5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8`。
コード/JSONの静的確認。既存報告は過去の主張として区別する。本棚卸しでGPU生成・Browser受入は実施していない。

## 再利用上位10群

以下のsource pathは `custom_nodes_custom/tegaki_manga_nodes/` 相対。KEEPは品質受入を意味しない。

| Product flow / Asset | Path | Category | 確認できた役割 / 証拠の限界 | 方針 / 読む時 |
|---|---|---|---|---|
| 1. Resolution / basic generation | `generation_profile.py`, workflow 01 | EXECUTION_BACKEND | referenceとfast_draft_12の定義、01の基本KSampler配線。モデル全般の最適値は未証明 | KEEP、M1 |
| 2. Global / local Prompt | `scene_compiler.py`, `scene_spec.py` | SEMANTIC_CORE | `compile_panel_data`がREGION_SPECとCASTを解決。空CASTはbindingがなければ許容 | REFACTOR adapter境界、M0 |
| 3. CAST Master | `cast_master.py`, `web/js/cast_master_editor.js`, `scene_spec.py` | SEMANTIC_CORE | Masterとbindingの既存分離。全出演の視覚identity保証は別 | KEEP、M2 |
| 4. Scene content | `panel_content_editor.py`, `web/js/panel_content_editor.js` | UX_REFERENCE | Prompt入力とSubSceneデータ。Panel主語の現UIは新Scene独立要件と差がある | REFACTOR、M0/M1 |
| 5. Character placement | `character_staging_editor.py`, `web/js/character_staging_editor.js` | UX_REFERENCE | 矩形preview/操作の資産。panel/character中心の選択をinstance中心へ改修必要 | REFACTOR、M2 |
| 6. Visual Frame | `panel_layout_spec.py`, `panel_layout_editor.py`, `web/js/panel_layout_editor.js` | SEMANTIC_CORE | polygonの枠データ・編集は存在。semantic Sceneの任意shapeとは別物 | KEEP、M1/M4 |
| 7. Prompt→mask plan | `impact_region_plan.py`, `manga_impact_regional_adapter.py` | EXECUTION_BACKEND | 既存regional計画/adapter、WF54–71の主経路。重なりpolicyの一般保証は未確認 | KEEP/限定拡張、M1/M2 |
| 8. Guide | `layout_guide_generator.py`, `layout_region_bridge.py` | SEMANTIC_CORE | 枠/人物のguide生成資産。ユーザー白ハゲ画像の人物identity対応は別gate | KEEP、M1/M3 |
| 9. Instance / advanced semantics | `interaction_resolver.py`, `subscene_contract.py` | SEMANTIC_CORE | instance ID、対話/SubScene契約。編集UIまで一貫しているとは限らない | KEEP backend、UIは後段 |
| 10. 検証基盤 | `scripts/test_runtime_source_identity.py`, `test_saved_workflow_live_compatibility.py`, `test_character_staging_browser_pointer.py`, `test_page_compile_plan.py` | TEST_INFRA | 実体/互換/操作/契約の検証入口が存在。今回未実行 | KEEP、変更責務だけ選択実行 |

## 今回見つかった重要なギャップ

1. **実証ラベルの過大解釈**: WF71は `TegakiMangaImpactRegionalAdapter` + `RegionalSampler` + core `ControlNetApplyAdvanced`。InspireのRegionalPromptSimpleやACNノードを含まない。WF71だけで外部Backend間のparityは言えない。
2. `scripts/test_phase3l_inspire_regional_parity.py` は外部source内のclass/socket文字列確認と独自Tensor/stringの型確認。外部nodeを実行していない。`test_phase3l_controlnet_backend_comparison.py`もsource文字列と独自Tensor形状確認で、ACN適用の画像比較ではない。
3. `PHASE3L_CANONICAL_VERIFICATION_MANIFEST.json`の`all_passed: true`に対し、`PHASE3L_PRESENCE_EVALUATION.json`は14条件とも`visual_status: PENDING`。`AI_VISUAL_ANNOTATION`というlabelもOwner受入の代用ではない。
4. 現compilerはKOMA/Panel主語。Page直下の独立Scene、Panelを跨ぐ/重なるScene、可変数の新UIは単なるskin差替だけでは完成しない。
5. `web/js/panel_content_editor.js` のAdvanced toggleは二つのSubSceneを初期化し、offで`panel.subscenes = []`にする。非破壊のprogressive disclosureとしてそのまま流用しない。
6. CASTの安定IDと、同一CASTの複数出演をUIから個別選択できることは別問題。新documentと画面選択はinstance_idで統一する。

Recommendation: 既存実装を全廃せず、M0で意味/保存境界を先に確定。Backend置換の未証明部分はM1の必須条件にしない。現Impact経路から製品導線を作り、置換する時だけ実配線比較を追加する。

## Workflow ledger

ファイルは `workflows/` 内。番号は検索key。全16対象JSONをparseしnode種別を確認した。仮説欄はファイル名/既存報告の意図、未証明欄は今回の監査判定。

| ID | 元の仮説 / 静的に確認したもの | 証明していないもの | Product reuse / Research / 後継 |
|---|---|---|---|
| 01 BASIC_ILLUSTRIOUS_TXT2IMG | 基本生成。loader/CLIP/KSampler/SaveImage | 漫画局所制御 | S0、モデル疎通基準、KEEP |
| 03 MANGA_REGIONAL_PROMPT | mask conditioning。ConditioningSetMask/Combine | キャラidentityと位置の安定 | S0参照、旧経路oracle。現Impact系とは別 |
| 07 MANGA_REGION_EDITOR_UI_TEST | Region Editorとpreviewのみ | 生成品質 | S0、編集操作回帰。新M1 surfaceに置換予定 |
| 09 MANGA_REGIONAL_GENERATION_POC | PageCompiler→Mask/Conditioning→KSampler | 新Scene/Frame独立・可変出演 | S0、compiler統合参照。新M1製品workflowへ |
| 54 Alice Left / 55 Alice Right | Prompt truth/remainderの左右fixture、Impact/guide経路 | frame-onlyでの左右因果性、任意Seed一般化 | S0、M2単人swap baseline |
| 56 Bob Left / 57 Bob Right | 別CASTの左右fixture、同経路 | 全CASTの同一性維持 | S0、M2別identity baseline |
| 58 Two Character LR / 59 Swap | 2人左右入替fixture | overlap、同CAST3出演のUI、Promptだけの位置制御 | S0、M2 paired test |
| 66 Pose Guide Only | 向きのguide fixture | 視覚PENDING、主導線の手数 | S1、Refine研究のみ |
| 67 Handshake / Feather | 接触/境界fixture | 一般的握手成功、feather普遍値 | S1、後段研究 |
| 68 Mainline SubScene / 69 Geometry Swap | 1 visible panel内複数Sceneのcompiler経路 | 新Page直下Sceneの自由編集 | S1、契約回帰・M2参考 |
| 70 4Panel Mixed | 4枠/複数内部Sceneのページfixture | Owner制作受入、最小手数、guideなしでの成立 | S0、ページ回帰基準 |
| 71 External Backend Parity | 実際は同じTegaki adapterの配線 | **Inspire/ACNとのparity** | S0監査対象。名称を実証として引用しない、真の比較fixtureが後継 |

54–71にはguideとLoRAを含む共通node種別がある。名前がPrompt Truthでも、そのまま「Promptだけの効果」と呼ばない。入力/guide/Seed固定のablationを新gateで作る。

21–53、60–65は現在の判断に必要な時だけ読む。全履歴再実行はしない。製品workflowは将来 `M1_SCENE_DRAFT` 等の用途名で少数に整理し、oracle番号を削除/使い回ししない。

## Archive / Defer上位10候補

| 候補 | 理由 | 今回の扱い |
|---|---|---|
| 1. 旧GITHUB.TXT本文 | Phase 3L主張を現在地として反復しやすい | Archiveコピー、新入口へのstub |
| 2. 旧GITHUB_ComfyUI.txt本文 | Phase 3Eで古い | Archiveコピー、同名正本を更新 |
| 3. 旧二つの中間計画 | 思想の参考だが新戦略と競合 | Archiveコピー、旧pathは参照保全 |
| 4. v1 Astra依頼書 | v2と最新Owner依頼が優先 | 原本保持、参照優先度を下げる |
| 5. two_region_*群 | 固定2領域研究とgeneric N経路の重複候補 | Research、依存検索前に移動しない |
| 6. single_panel_multiscene_adapter.py | mainline SubSceneとの重複候補 | oracleとして保持、後で参照監査 |
| 7. 21–53旧実験workflow群 | 主UIに必要な数を超える | 索引でResearch、物理移動は別カード |
| 8. 66/67のPose・握手UI昇格 | 最小手Draftより優先しない | Backend保持、UI後段 |
| 9. 独自汎用mask/pose/ControlNet再実装案 | 既存toolとの重複 | 主計画からdefer |
| 10. 04 Regional LoRA / RegionalLoRALab接続 | `KNOWN_ISSUES.md`上も局所適用未成立 | FUTURE。別projectは探索しない |

## Comic Creatorの限定監査と判断

2026-09-06に公式README、入口、route実装、state、template wizardを閲覧。GitHub APIのSHA取得はこの環境でできず、ページ取得時点のキャッシュも異なる。**単一commitでの全体監査・動作確認は未実施**。採用前にGeminiが一つのSHAへ固定して再確認する。今回コードをvendor/installしていない。

| Area | 実source / 観察 | 再利用判断 |
|---|---|---|
| ComfyUIへの入口 | [`web/comfyui/ccc_menu.js`](https://raw.githubusercontent.com/ketle-man/comfyui-comic-creator/master/web/comfyui/ccc_menu.js) はactionBarから `/ccc` を別tabで開く | 小さな入口patternは参考になる |
| SPA配信/route | [`__init__.py`](https://raw.githubusercontent.com/ketle-man/comfyui-comic-creator/master/__init__.py) は空node mappings＋route登録。[`py/ccc.py`](https://raw.githubusercontent.com/ketle-man/comfyui-comic-creator/master/py/ccc.py)はPromptServer/aiohttp、template/config等を参照 | route境界の参考。backend全体をコピーしない |
| Work/Pageとcanvas state | [`01-state.js`](https://github.com/ketle-man/comfyui-comic-creator/blob/master/static/js/main/01-state.js) の取得snapshotはactiveWork/activePage/selectedPanelIdと画像・文字・Pose等の編集stateを共有 | そのまま新authoring保存正本にしない |
| Split wizard | [`06c-template-wizard.js`](https://raw.githubusercontent.com/ketle-man/comfyui-comic-creator/master/static/js/main/06c-template-wizard.js)にpolygon split、undo、SVG生成。DB/state/template/page/i18n等をimport | 必要な純粋幾何だけ将来SELECTIVE候補。丸ごと独立componentとは言えない |
| Work/UI/生成橋の候補 | [`main一覧`](https://github.com/ketle-man/comfyui-comic-creator/tree/master/static/js/main)に `11a-work-manager.js`, `07-pages.js`, `08-panels-images.js`, `14-integrations.js` | 前三者は所在確認、詳細監査は未実施。生成橋は下記の取得範囲に限定 |

[`14-integrations.js`](https://github.com/ketle-man/comfyui-comic-creator/blob/master/static/js/main/14-integrations.js)では `requestPanelImageFromWorkflowStudio(prompt, width, height, negative, wfOverride)`、Workflow Studio iframe、`/api/wfm/workflows/raw`からのworkflow取得を確認した。I2I/Inpaintもiframe側関数へ渡す。推論: この橋は独立したComfyUI queue adapterではなくWorkflow Studioとの結合を持ち、そのままTegakiへ移植すると追加依存になる。Generate UIの考え方は参考にし、M1では既存ComfyUI実行経路への薄い橋を使う。なおstateの古い取得snapshotはglobal共有、wizardの新しい取得snapshotはESM importであり、現行module構成を一律に断定できない。

README上のOverall/Panel Prompt、Draft、Workflow Studio導線はUX参考。ただしTegakiのGlobal/Scene/CAST compilerへ接続できる実証ではない。[公式README](https://github.com/ketle-man/comfyui-comic-creator)。

| 選択 | 保守/結合/移行/不要機能 | 結論 |
|---|---|---|
| A REFERENCE | 独自surface分の保守はあるがdocumentを保てる。既存Tegaki canvas操作を活用可能 | **現時点の採用** |
| B SELECTIVE REUSE | 幾何/入口など切出し単位を限定できれば有利。DB/state/DOM依存を外すコストがある | SHA固定・依存表・必要コード量の確認後に判断 |
| C FORK | Work/出力等は得られるが大きな編集suite、state移行、upstream追従を持つ | 現時点不採用。最小手導線には過剰 |

MRP的な粗い領域＋Promptが主操作の土台に近い。Comic Creatorは広い制作shellの参考。MRP実コードは今回閲覧せずOwner説明に基づく比較。

LicenseファイルはMIT、copyrightは2026 Statsuと確認。[LICENSE](https://raw.githubusercontent.com/ketle-man/comfyui-comic-creator/master/LICENSE)。コードを取り込む場合は元の表示とlicenseを保持し、同梱vendor/assetsの条件も取り込み範囲ごとに確認する。
