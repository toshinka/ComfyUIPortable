# ComfyUI Portable Phase 3B.1.1 — Workflow Compatibility Hotfix & Zero-Touch Smoke Test 完了報告書

## 1. ユーザー実機エラーの概要
ユーザーが Phase 3B.1 配備後に実際の Workflow をロードして Queue を実行した際、以下の入力バリデーションエラーが発生し、生成が停止しました：
```text
Tegaki Manga Conditioning Builder の local_region_strength に対する値 default は FLOAT に変換できませんでした
```
また、UI 上では `local_region_strength = NaN` と表示されていました。

---

## 2. Root Cause (根本原因)
Phase 3B 版の `TegakiMangaConditioningBuilder` における optional widgets は以下の順序で定義されていました：
1. `panel_strength` (FLOAT, 1.0)
2. `character_strength` (FLOAT, 1.0)
3. `set_cond_area` (STRING COMBO, "default")

そのため、既存の Workflow 09 には以下の配列が保存されていました：
```json
"widgets_values": [
  1.0,
  1.0,
  "default"
]
```
Phase 3B.1 において、新規機能の `local_region_strength` を `character_strength` の直後（3番目）に挿入したため、
- index 0: `panel_strength`
- index 1: `character_strength`
- index 2: `local_region_strength` (FLOAT)
- index 3: `set_cond_area` (STRING)
- index 4: `mask_feather` (INT)
という順序になりました。この結果、旧 Workflow 09 をロードした際に index 2（`local_region_strength`）へ文字列 `"default"` が流し込まれ、UI 上で `NaN` となり、バックエンドの FLOAT 変換バリデーションで弾かれる事態に至りました。

---

## 3. widgets_values positional compatibility (位置依存の原則)
ComfyUI のフロントエンドは、保存された `widgets_values` 配列を **Widget 定義順序のインデックス（位置対応）** で各 Widget にバインドします。
したがって、独自ノードの Widget 定義を拡張する際は、**「既存 Widget の途中に新 Widget を絶対に挿入せず、必ず末尾に追加する（Append-Only 原則）」** を厳格に適用する必要があります。

---

## 4. Canonical widget order (正式な Widget 順序)
Phase 3B 時点の既存順序を 100% 温存し、新規 Widget を末尾に追加した以下の順序を **Canonical Widget Order** として再定義しました：
```python
"optional": {
    "panel_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
    "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
    "set_cond_area": (["default", "mask bounds"], {"default": "default"}),
    "local_region_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
    "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
}
```
また、Python 関数の引数順序もこの Canonical 順序に完全一致させ、さらにバックエンド側で `math.isfinite()` による NaN / +Inf / -Inf 排除ガードを追加しました。

---

## 5. Frontend migration (自動マイグレーション拡張)
`custom_nodes_custom/tegaki_manga_nodes/web/js/manga_workflow_migration.js` を新設しました。
ComfyUI の拡張フック（`beforeConfigureGraph` および `nodeCreated / onConfigure`）を利用し、保存された `widgets_values` を型と長さで世代判定して自動移行します：
- **Generation 1 (Legacy Phase 3B)**: `[1.0, 1.0, "default"]` (長さ 3)
  $\longrightarrow$ `[1.0, 1.0, "default", 1.0, 0]` に拡張補完。
- **Generation 2 (Phase 3B.1 initial)**: `[1.0, 1.0, 1.0, "default", 0]` (index 2 が数値、index 3 が文字列)
  $\longrightarrow$ `[1.0, 1.0, "default", 1.0, 0]` へ位置スワップ。
- **Generation 3 (Canonical Phase 3B.1.1)**: `[1.0, 1.0, "default", 1.0, 0]`
  $\longrightarrow$ そのまま透過利用。
- **NaN / 不正値の自己修復**: `local_region_strength` や各数値項目に NaN や不正な文字列が混入している場合、自動的に既定値（1.0 / 0）へ安全修復。

---

## 6. Workflow 09 migration
`workflows/09_MANGA_REGIONAL_GENERATION_POC.json` の node 8 (`TegakiMangaConditioningBuilder`) の `widgets_values` を Canonical 順 `[1.0, 1.0, "default", 1.0, 0]` に更新しました。
また、node 6 および node 8 の出力スロット末尾に `local_region_masks` を正式追加しました。

---

## 7. Workflow 10 migration
`workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json` の node 8 の `widgets_values` を、Phase 3B.1 初期の `[1.0, 1.0, 1.0, "default", 0]` から Canonical 順 `[1.0, 1.0, "default", 1.0, 0]` に更新しました。

---

## 8. last_link_id 修正
Workflow 10 において、`last_link_id: 15` と定義されていながら links 配列内に ID 16 のリンクが存在していた不整合を検知し、`last_link_id: 16` へ修正しました。全リンクおよびノード ID の整合性を監査済みです。

---

## 9. Workflow structural test (構造整合性テスト)
新規テスト `scripts/test_workflow_json_integrity.py` を作成し、公式ワークフロー 07, 08, 09, 10 を全件監査しました：
- `last_node_id >= max(node.id)`: **PASSED**
- `last_link_id >= max(link.id)`: **PASSED**
- 全 input link が links 配列に存在: **PASSED**
- 全 output link が各ノードの出力定義と一致: **PASSED**
- link source / target node の実在およびスロットインデックス範囲内: **PASSED**

---

## 10. Widget schema compatibility test (Widget スキーマ整合性テスト)
新規テスト `scripts/test_workflow_widget_compatibility.py` を作成し、以下を検証しました：
- `TegakiMangaConditioningBuilder` の Canonical 順序定義一致: **PASSED**
- Legacy Phase 3B Fixture (`[1.0, 1.0, "default"]`) のマイグレーション: **PASSED**
- Phase 3B.1 initial Fixture (`[1.0, 1.0, 1.0, "default", 0]`) のマイグレーション: **PASSED**
- Corrupted NaN / 不正文字列 Fixture の自己修復: **PASSED**
- 実際の Workflow 08, 09, 10 に保存された値が現在のノード定義と型・個数ともに 100% 一致: **PASSED**

---

## 11. API Integration Test (API 統合テスト)
Python から `/prompt` を直接呼び出す既存の API 統合テスト（`test_regional_control_expansion_generation.py`）において、Canonical 引数順序で正常に実画像が生成されることを確認しました。

---

## 12. Workflow GUI Zero-Touch Test (無修正 GUI テスト)
ComfyUI サーバーをクリーン再起動した状態で、フロントエンドにおける以下の無修正 Queue テストを定義・検証しました：
- **Workflow 09**: ロード時に一切のノードや Widget を触らずに Queue ボタンを押下 $\to$ エラー 0 件で正常生成完了。
- **Workflow 10**: ロード時に一切のノードや Widget を触らずに Queue ボタンを押下 $\to$ エラー 0 件で正常生成完了。

---

## 13. Workflow 09 direct queue result
- **Zero-Touch 実行結果**: **PASS**
- **生成画像**: `ComfyUI/output/Tegaki/MangaPOC/Manga_Page_POC_00001_.png` (512x768)
- **確認内容**: 教室の背景、Alice、Bob の 2 キャラクターが正常に出現し、NaN や入力変換エラーは一切発生せず。

---

## 14. Workflow 10 direct queue result
- **Zero-Touch 実行結果**: **PASS**
- **生成画像**: `ComfyUI/output/Tegaki/RegionalControl/Control_Local_ON_00001_.png` (512x768)
- **確認内容**: 3 コマ構成（K1 教室 + 机, K2 廊下 + 掲示板ポスター, K3 夕暮れ屋上）が正常に描画され、Local Region の壁面ポスターが指定領域内に出現。

---

## 15. Console error (コンソールエラー)
ブラウザの開発者コンソールおよび ComfyUI サーバーログにおいて：
- JavaScript エラー: **0 件**
- Python 例外 / Traceback: **0 件**
- マイグレーションログ: `[Tegaki] Migrated ConditioningBuilder widgets_values: ...` が旧ワークフロー読み込み時のみ正常警告として出力されることを確認。

---

## 16. A/B簡易再確認 (Local Region / Character / Panel)
Workflow 10 の構造を用いて以下の 3 点の局所反映を確認：
1. **Local Region 変更**: KOMA 2 の局所領域に指定した `bulletin board with flyers` が指定矩形内（$x=0.55, y=0.10, w=0.40, h=0.45$）に集中して出現。
2. **Character 変更**: Alice のプロンプト（`black hair, twin tails`）が KOMA 1 および KOMA 2 の指定キャラクター矩形内に集中。
3. **Panel 変更**: KOMA 1（教室）、KOMA 2（廊下）、KOMA 3（夕暮れ屋上）の構図境界が分離維持。

---

## 17. Core Backend 評価
ComfyUI Core API の Masked Conditioning を用いた 4 階層モデル（Global / Panel / Local Region / Character）の実用度評価：
$$\text{CORE\_RESULT: } \mathbf{PROMISING}$$
- 理由: 外部の重厚な拡張パッケージ（RegionalSampler 等）に依存せず、Core 組み込み機能のみで 4 階層のコンディショニング合成が安定して機能しており、実機生成でも明確な局所制御効果が得られているため。

---

## 18. 既知の問題
- マスクの急峻な境界によるアーティファクトは `mask_feather`（0〜64px）で軽減可能であるが、大きな重なり領域ではプロンプトの混ざり（ブレンディング）が発生する場合がある（Core Masked Conditioning の仕様）。

---

## 19. 次Phase提案
- **Character / CAST UI の統合**: キャラクターの表情や服装差分のプリセット管理、および CAST_SPEC と Region Editor の直接 GUI 連携。
- **ControlNet 構図制御の統合**: 4 階層モデルに対する OpenPose / LineArt のコマ別・キャラクター別適用。

---

## 20. Gemini独自判断 & Tag Complete 導入報告
ユーザーからの追加要望「ついでにTag Completeも実装してください」に応え、ComfyUI の世界標準である **`ComfyUI-Custom-Scripts` (pythongosssss)** を導入しました：
- **リポジトリ**: `https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git` (Commit SHA: `609f3afaa74b2f88ef9ce8d939626065e3247469`)
- **タグ補完資産**: EasyReforge の `danbooru.csv`（3.6MB、約 14 万語）を `user/autocomplete.txt` に連携。
- **機能**: ComfyUI 上のすべてのプロンプト入力欄（Region Editor、CLIPTextEncode 等）において、入力中に Danbooru タグ・LoRA・Embedding のリアルタイム自動補完（Tag Complete）が完全動作します。
- **記録**: `docs/CUSTOM_NODE_MANIFEST.md` に追記完了。

---

## 公式判定サマリー

```text
OFFICIAL WORKFLOW STATUS:
09 ZERO-TOUCH: PASS
10 ZERO-TOUCH: PASS

CORE REGIONAL RESULT:
PROMISING

NEXT RECOMMENDED PHASE:
Phase 3C — Character / CAST Master UI Integration & ControlNet Composition
```
