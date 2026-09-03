# PHASE2_1_1_REGRESSION_FIX_REPORT.md — Phase 2.1.1 小修正・回帰防止 報告書

**作成日時**: 2026-09-03 14:14 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  
**Review Target Baseline**: `fda210762d25688119dd1338e9887b8f87f64b3e`  

---

## 1. Split 修正
- **問題**: `panel_count = 3` の状態でSplitした際、枠外（KOMA 4〜6）の無効コマが先に取得され、`panel_count` が3のままKOMA 4が有効化されると、`id <= panel_count` 条件を満たさず非Activeとなる不整合が存在した。
- **改修内容**:
  1. 現在の `panel_count` 範囲内の無効コマを優先探索。
  2. 範囲内に空きがない場合、`panel_count < 6` であれば `panel_count += 1` して新枠を確保。
  3. 6コマ満杯時はSplit不可を通知。
- **結果**: 分割後に必ず `enabled == true` かつ `id <= panel_count` となり、即座にActive Regionとして描画・出力されます。

---

## 2. Split Undo 修正
- **改修内容**:
  - `splitSelectedRegion()` の処理先頭（`panel_count` 変更、`unused.enabled` 有効化、geometry分割の前）に `pushHistory()` を配置。
- **結果**:
  - Split後にUndoを実行した場合、`panel_count`、分割先コマの `enabled`（false）、分割元コマのgeometryがSplit直前の状態へ完全復元されることを確認。

---

## 3. Create Undo 修正
- **問題**: 空白ドラッグによる新規作成時、状態変更（`panel_count` 増加、`enabled = true`、座標初期化）の後に `pushHistory()` が呼ばれていたため、Undoしても作成前まで戻れなかった。
- **改修内容**:
  - `canvas.onmousedown` で新規Region作成が成立すると判断した直後、状態を変更する前に `pushHistory()` を実行。
  - 作成不可（6コマ満杯）の場合は `pushHistory()` を呼ばないようガード。
- **結果**:
  - 新規作成後にUndoを実行した場合、`panel_count`、`enabled`、geometryが作成前の状態（非表示・直前座標）へ完全復元されることを確認。

---

## 4. Layout Reset 修正
- **問題**: 「Layout Reset」操作時に `r.enabled = (i < spec.panel_count)` が実行され、ユーザーが意図的に無効化したコマ（Deleteしたもの）が勝手に再有効化される不整合があった。
- **改修内容**:
  - Layout Resetの責務を **矩形座標 (`x, y, w, h`) のみ** を初期レイアウト（`DEFAULT_LAYOUTS`）へ戻す操作に純粋化。
  - `enabled`、`prompt`、`panel_count`、`global_prompt`、`canvas size`、および将来の未知フィールドは100%保持。
- **結果**:
  - 無効化されたコマや入力済みPromptを一切破壊せず、座標レイアウトのみが安全にリセットされます。

---

## 5. Generic Swap 仕様
- **問題**: 以前のSwapは固定列挙（`x, y, w, h, prompt, enabled`）のみを交換していたため、将来追加されるメタデータ（ControlNet強度、局所LoRAタグ、キャラクタバインディング等）が片方に置き去りにされるリスクがあった。
- **改修内容**:
  - KOMA identity として固定するもの: `id`, `name`, `color` のみ。
  - それ以外の全フィールド（既存キーおよび将来の未知キー）を汎用payloadとして動的に丸ごと交換するアルゴリズムを導入。
- **結果**:
  - `control_strength`, `lora_tag`, `char_id` などの未知メタデータが付与されたコマ同士でも、属性を欠落させることなく完全に交換されます。

---

## 6. Schema Error 分類とハンドリング
- **問題**: `execute_editor()` で構文エラーとスキーマエラーが同一に扱われ、不正なバージョン（例: `version = 999`）でも無言でデフォルト3コマに初期化されていた。
- **改修内容**:
  - **Syntax Error (構文エラー)**: `json.loads` での `JSONDecodeError` は warning をログ出力し、安全のため default spec へフォールバック。
  - **Schema Error (スキーマエラー)**: JSONパース成功後のバリデーション違反（`version != 1`、`canvas` 欠落、`regions` 欠落、`enabled` 型不正等）は、**握りつぶさずに `ValueError`（Node execution error）を送出**。
- **結果**:
  - ユーザーの制作データや外部ツールの破損JSONが勝手に初期状態へ上書きされる事故を防止し、ComfyUIノードの実行エラーとして安全に停止させます。

---

## 7. enabled 型仕様 (Strict Boolean)
- **問題**: `bool(r.get("enabled", True))` では、文字列 `"false"` が Python の仕様上 `True` と評価されてしまう。
- **改修内容**:
  - `validate_region_spec()` 内で `isinstance(enabled_val, bool)` を厳格に検査。
  - 文字列 `"false"`, `"true"`, `"1"`, `"0"` や整数 `1`, `0` は即座に `ValueError` を送出。
  - `is_active_region()` も `region.get("enabled") is True` を厳格判定。
- **結果**:
  - 将来の外部GUIやAPI経由での型崩れ・誤判定を水際で防止。

---

## 8. 新規 Regression Test 結果
新設スクリプト: `scripts/test_region_state_transitions.py`
実行結果:
```text
Phase 2.1.1 State Transitions & Regression Tests
--- 1. Testing Split 3 -> 4 Panel & Active Region State ---
Split 3 -> 4: PASSED
--- 2. Testing Split Undo 4 -> 3 & Redo 3 -> 4 ---
Split Undo: PASSED
Split Redo: PASSED
--- 3. Testing Create 3 -> 4 Panel & Undo 4 -> 3 ---
Create & Undo: PASSED
--- 4. Testing Delete -> Layout Reset preserves enabled & prompt ---
Layout Reset preserves state: PASSED
--- 5. Testing Generic Swap with unknown metadata ---
Generic Swap unknown metadata: PASSED
--- 6. Testing execute_editor Unsupported Schema Error propagation ---
Unsupported schema error propagated successfully
Schema error propagation: PASSED
--- 6b. Testing Syntax Error fallback to default ---
Syntax error fallback: PASSED
--- 7. Testing Strict boolean validation on 'enabled' ---
String 'false' rejected successfully
Integer 1 rejected successfully
Strict boolean validation: PASSED

[SUCCESS] ALL PHASE 2.1.1 REGRESSION TESTS PASSED PERFECTLY!
```

---

## 9. Frontend 手動・実機確認
- `PHASE2_1_UI_TEST_CHECKLIST.md` に基づき、全項目を検証。
- ブラウザコンソールエラーなし（0 errors）。
- Split時のPanel Count自動追従、Split Undo/Redo、Create Undo/Redo、Layout Resetでの状態保持、Generic Swapを実機確認。

---

## 10. 既存機能回帰テスト結果
全既存テストを再実行し、回帰がないことを確認：
1. `scripts/test_runtime_source_identity.py`: **PASSED** (Git正本と完全一致)
2. `scripts/test_region_spec.py`: **PASSED** (全11テストスイート合格)
3. `scripts/verify_wildcard_patch.py`: **PASSED** (`PATCH PRESENT`)
4. `scripts/test_region_editor_backend_api.py`: **PASSED** (`RegionEditor_Test_00003_.png` 生成成功)
5. `scripts/test_generation.py`: **PASSED** (`Txt2Img_Test_00004_.png` 生成成功・非破壊実証)

---

## 11. 既知の問題
- `04_REGIONAL_LORA_EXPERIMENT.json` のKSampler未合流（NOT YET REGIONAL / Phase 5で改修）。
- Region Prompt内での `<lora:...>` 記法（現段階では全体適用 / Phase 5で改修）。
- （※Phase 2.1.1 で指摘されたSplit/CreateのUndo不整合、Layout Resetのenabled破壊、Swapの固定フィールド限定、スキーマエラーの無言置換、enabled型曖昧性はすべて本Phaseで解決済）。

---

## 12. 将来設計メモ (Phase 3以降の基本方針)
指示書第17〜21項に基づき、以下の思想をプロジェクト方針として記録・保持します：
1. **ComfyUIの役割分担**:
   - ComfyUIは「高コストな構図・キャラクター位置・演技・カメラ・背景・精度の高い下絵生成」を担当する。
   - 集中線、トーン、効果、最終仕上げ、微細修正は、手描きや外部ツールと自由に併用する前提とする（「ComfyUI内だけで完結する漫画制作」へ固定しない）。
2. **ブレインストーミング性の維持**:
   - 厳密すぎる拘束によって偶然性や創造性を損なわないよう配慮する。
   - 完全な厳密制御よりも「漫画制作で使える方向へ強く誘導する」バランスを重視する。
3. **将来のLoRA階層構想**:
   - Global LoRA（ページ全体） + KOMA LoRA（コマ単位） + Character LoRA（人物領域単位）。
   - 指定領域外への漏れが完全にゼロでなくても、相対的に強く効く実用性があれば積極的に採用する。
4. **Character / Cast 構想**:
   - `PAGE -> KOMA -> CHARACTER` の階層構造（`CAST_SPEC`、Panel-Character Binding等）をPhase 3以降で検討。
5. **Panel Sequential Generation**:
   - 1コマずつ順次生成して合成するパイプラインを検討（Prompt肥大化回避、コマ単位再生成/I2I/Control）。

---

## 13. Gemini独自判断で変更した項目
- **Split実行時メッセージの拡張**:
  - Split成功時のCanvas通知に割り当てられたKOMA IDだけでなく、更新後の総コマ数（`コマ数: 4` など）を表示し、パネル数が連動して増えたことをユーザーが視覚的に認識できるようにしました。
- **Generic Swapの双方向キー削除対応**:
  - 一方のコマにのみ存在するメタデータキー（例: KOMA 1にのみ `char_id` がある場合）をSwapした際、交換元（KOMA 1）から `char_id` が安全に `delete` され、交換先（KOMA 2）へ確実に移譲されるよう設計しました。

---

## 14. PHASE 3 READINESS

```text
PHASE 3 READINESS: GO
```
- Split / Create / Swap / Reset / Delete の全状態遷移とUndo/Redoが完全に整合
- スキーマエラーの例外化および厳格な型検証によりデータ堅牢性が大幅向上
- 新規回帰テストスイートを含む全自動テストが100%合格
- 既存のtxt2img/I2IおよびWildcard基盤が完全に非破壊
- Phase 3（Regional Conditioning Compiler）へ直ちに進出可能
