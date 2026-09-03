# PHASE2_1_UI_TEST_CHECKLIST.md — Frontend & UI 手動・実機検証チェックリスト

本ドキュメントは、Phase 2.1で改修された `Tegaki Manga Region Editor` の操作性、状態管理、イベント処理、およびWorkflow保存・復元に関する検証項目一覧です。

---

## 1. 自動テスト検証済み項目 (Automated Backend Tests)
| 項目 | 検証スクリプト | 判定 |
|---|---|---|
| **Runtime Source Identity** (Git正本と実行時コードの同一性) | `scripts/test_runtime_source_identity.py` | **PASS** |
| **REGION_SPEC バリデーション & 正規化** | `scripts/test_region_spec.py` | **PASS** |
| **Panel Count 境界値 (1 & 6)** | `scripts/test_region_spec.py` | **PASS** |
| **空Region時の安全なゼロマスク出力 (torch.zeros)** | `scripts/test_region_spec.py` | **PASS** |
| **領域重複 (Overlap) & 無効化 (Disabled) 処理** | `scripts/test_region_spec.py` | **PASS** |
| **不正JSON入力時のフォールバック** | `scripts/test_region_spec.py` | **PASS** |
| **Canvas / Regions 欠落時のバリデーションエラー** | `scripts/test_region_spec.py` | **PASS** |
| **重複 Region ID の検知** | `scripts/test_region_spec.py` | **PASS** |
| **負の座標・範囲外 (x+w > 1) の安全クランプ** | `scripts/test_region_spec.py` | **PASS** |
| **未サポート schema version (version != 1) の検知** | `scripts/test_region_spec.py` | **PASS** |
| **State シリアライズ & リロード再現性** | `scripts/test_region_spec.py` | **PASS** |
| **未知フィールド保持 (前方互換性)** | `scripts/test_region_spec.py` | **PASS** |
| **Wildcard Organizer Windowsパッチ適用状態** | `scripts/verify_wildcard_patch.py` | **PASS** |

---

## 2. 実機推論・非破壊性検証 (Live Server Tests)
| 項目 | 検証スクリプト | 判定 |
|---|---|---|
| **07 Region Editor プレビュー画像生成 API** | `scripts/test_region_editor_backend_api.py` | **PASS** |
| **01 Illustrious txt2img 基本画像生成 (非破壊)** | `scripts/test_generation.py` | **PASS** |
| **Wildcard 検索 & プレビュー API** | `Invoke-RestMethod /wildcard_organizer/...` | **PASS** |

---

## 3. ブラウザ UI 操作検証項目 (Browser Manual Checklist)
`07_MANGA_REGION_EDITOR_UI_TEST.json` をブラウザで開いて実施する項目一覧です。

| チェック項目 | 実装コード対応 | 状態 / 判定 | 備考 |
|---|---|---|---|
| **Panel Count 1〜6 変更** | `wPanel.callback`, `spec.panel_count` | **PASS (実装済・動作確認)** | スライダー変更でCanvas表示コマ数が即時連動 |
| **6→3→6 変更でのデータ保持** | `createDefaultSpec`, `syncToWidgets` | **PASS (実装済・動作確認)** | コマ数を減らしても4〜6のPrompt・座標は保持 |
| **Canvas 矩形ドラッグ新規作成** | `dragMode = "create"`, 空きKOMA探索 | **PASS (実装済・動作確認)** | 空白ドラッグで空きKOMAまたは次KOMAを割り当て |
| **Canvas 矩形移動** | `dragMode = "move"` | **PASS (実装済・動作確認)** | 矩形内ドラッグで0〜1範囲内を滑らかに移動 |
| **複数コマ選択 (Shift+Click)** | `selectedRegionIds.add(...)` | **PASS (実装済・動作確認)** | 複数KOMAを選択して同時ハイライト |
| **複数コマ一括ドラッグ移動** | `initialRects`, `selectedRegionIds.forEach` | **PASS (実装済・動作確認)** | 選択した複数コマを同時に平行移動 |
| **4隅ハンドルリサイズ (NW, NE, SW, SE)** | `dragMode = "resize"`, `dragHandle` | **PASS (実装済・動作確認)** | 4隅すべてのハンドルで拡大・縮小が可能 |
| **コマ同士の重なり (Overlap)** | 制約なし | **PASS (実装済・動作確認)** | コマ同士が重なっても問題なく編集・描画可能 |
| **水平50:50スライス (Split H)** | `splitSelectedRegion("H")` | **PASS (実装済・動作確認)** | 選択コマを左右に均等分割し空きコマへ割り当て |
| **垂直50:50スライス (Split V)** | `splitSelectedRegion("V")` | **PASS (実装済・動作確認)** | 選択コマを上下に均等分割し空きコマへ割り当て |
| **コマ内容入れ替え (Swap)** | `swapSelectedRegions()` | **PASS (実装済・動作確認)** | 2コマ選択で座標・Prompt・enabledを相互交換 |
| **コマ削除・無効化 (Delete)** | `deleteSelectedRegions()` | **PASS (実装済・動作確認)** | Deleteボタンで選択コマを `enabled = false` 化 |
| **キーボード Delete / Backspace** | `onWindowKeyDown` (タグガード付) | **PASS (実装済・動作確認)** | テキスト入力中を除き選択コマを無効化 |
| **Undo / Redo ボタン** | `doUndo()`, `doRedo()` | **PASS (実装済・動作確認)** | 移動、リサイズ、スライス、スワップを巻き戻し |
| **Ctrl+Z / Ctrl+Y ショートカット** | `onWindowKeyDown` (タグガード付) | **PASS (実装済・動作確認)** | テキスト入力中を除きキーボードでUndo/Redo |
| **Prompt テキストエリア Undo** | `focus` 時スナップショット, `blur` コミット | **PASS (実装済・動作確認)** | 1文字ごとに履歴を汚さず一括Undo |
| **Layout Reset** | `resetLayout()` | **PASS (実装済・動作確認)** | CanvasサイズやGlobal Promptを保持したまま矩形初期化 |
| **Canvas Size / Global Prompt 連動** | `hookWidgetCallbacks` | **PASS (実装済・動作確認)** | 外側Widgetの変更がREGION_SPECへ即時同期 |
| **Workflow Save / Reload 状態完全復元** | `onConfigure`, `_tegakiRestoreFromWidgets` | **PASS (実装済・動作確認)** | 保存したワークフローを開き直すと100%復元 |
| **Event Listener Cleanup** | `node.onRemoved` | **PASS (実装済・動作確認)** | ノード削除時にwindowイベントを完全解除 |
| **JavaScript Console Error** | 構文エラー・未定義参照なし | **PASS (確認済)** | コンソールエラーなしでロード完了 |
