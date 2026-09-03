# PHASE2_1_STABILIZATION_REPORT.md — Phase 2.1 地固め・安定化 報告書

**作成日時**: 2026-09-03 13:24 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  
**Review Target Baseline**: `2a3116b520b25a94879ab621d7fe6317142cacce`  

---

## 1. 修正概要
Phase 2で構築した `Tegaki Manga Region Editor`、`REGION_SPEC`、および `Wildcard Organizer` の基盤を徹底的に安定化・地固めしました。
新機能の追加を厳格に凍結し、**「GitHubでレビューされるコード ＝ ComfyUIが実行するコード ＝ テストされるコード」** の同一性を担保するとともに、状態管理・バリデーション・UIイベント処理・パッチ管理の不整合を網羅的に解消しました。

---

## 2. Git正本 / Runtime同一化方式
- **課題**: ComfyUI本体配下の `ComfyUI/custom_nodes/tegaki_manga_nodes` は `.gitignore` 除外対象であり、Git追跡対象の `custom_nodes_custom/` との乖離リスクがあった。
- **解決策**: Windows Junction（ディレクトリジャンクション）により、`ComfyUI/custom_nodes/tegaki_manga_nodes` -> `custom_nodes_custom/tegaki_manga_nodes` への物理結合を維持。
- **検証保証**: `scripts/test_runtime_source_identity.py` を作成し、Python実行時にロードされたクラスの物理ファイルパスが `custom_nodes_custom` に解決されること、およびSHA256ハッシュが一致することを自動検証。

---

## 3. Runtime Source Identity 結果
`scripts/test_runtime_source_identity.py` 実行結果:
```text
Class: TegakiMangaRegionEditor
  Import Path:   D:\GitHub\tegaki\ComfyUIPortable\ComfyUI\custom_nodes\tegaki_manga_nodes\region_editor.py
  Resolved Path: D:\GitHub\tegaki\ComfyUIPortable\custom_nodes_custom\tegaki_manga_nodes\region_editor.py
  SHA256:        f64d0812dbe8a6ca829b5321ab9b98ec354020a1db4b25687aa6c5b9f7a77d5a
  Canonical Match: PASSED

Class: TegakiLoraPromptLoader
  Import Path:   D:\GitHub\tegaki\ComfyUIPortable\ComfyUI\custom_nodes\tegaki_manga_nodes\lora_loader.py
  Resolved Path: D:\GitHub\tegaki\ComfyUIPortable\custom_nodes_custom\tegaki_manga_nodes\lora_loader.py
  SHA256:        415ed10843c44620d805ea82745a10a3076ff9f25b6624c0c2d24b7de4501a89
  Canonical Match: PASSED
```
結果: **PASS**（Runtimeノードは100% Git正本を参照）。

---

## 4. REGION_SPEC 正式仕様 (v1)
`REGION_SPEC` を永続状態の **Single Source of Truth (唯一の正本)** として定義。
```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "panel_count": 3,
  "global_prompt": "manga page, monochrome, expressive linework...",
  "regions": [
    {
      "id": 1,
      "name": "KOMA 1",
      "enabled": true,
      "x": 0.06,
      "y": 0.05,
      "w": 0.88,
      "h": 0.28,
      "prompt": "1girl, dynamic pose",
      "color": "#E53935"
    }
  ]
}
```
- 座標はすべて `0.0 〜 1.0` の正規化座標。
- 未知のメタデータ（`control_strength`, `lora_tag` 等）が追加されても削除せず保持する前方互換性を確保。

---

## 5. Validator 仕様 (`validate_region_spec`)
- **スキーマバージョン**: `version === 1` を厳格判定。1以外は `ValueError`。
- **Canvas & Panel Count**: `width`, `height` が正の整数、`panel_count` が `1〜6`。
- **Regions 配列**: `id` が 1〜6 の一意な整数（重複時は例外）、`enabled` は bool、`prompt` は str。
- **ジオメトリ検査**: `0.0 <= x <= 1.0`, `0.0 <= y <= 1.0`, `0.001 <= w <= 1.0`, `0.001 <= h <= 1.0`, `x + w <= 1.0`, `y + h <= 1.0`。軽微な逸脱は自動 clamp。
- **未知フィールド**: 破壊せず保持。

---

## 6. Widget / REGION_SPEC 同期仕様
- **関係性**: 外側Widget（`panel_count`, `canvas_width`, `canvas_height`, `global_prompt`）は、内部の `REGION_SPEC` に対する **Facade（窓口）** として位置付け。
- **Widget変更時**: 各Widgetの `callback` から `spec` を更新し、`region_spec_data`（JSON文字列）へ即時シリアライズ。
- **Backend優先度**: 有効な `region_spec_data` が存在する場合はそれを正本とし、外側引数での無条件上書きを廃止。`{}` または空の場合のみ外側引数から初期Specを生成。

---

## 7. Panel Count 仕様
- `panel_count` を `6 -> 3 -> 6` と変更した場合でも、非アクティブとなった KOMA 4〜6 の座標・Prompt・設定は配列内に保持され、破棄されません。

---

## 8. Delete 仕様
- ツールバーに「🗑 Delete」ボタンを追加。またキーボードの `Delete` / `Backspace` に対応。
- テキストエリア（`input`, `textarea`, `contenteditable`）フォーカス時は文字編集を優先し、Region削除を発火させない安全ガードを実装。
- 削除時はオブジェクトを配列から破棄せず、`enabled = false` として保持（再利用・Undoを容易化）。

---

## 9. Resize 仕様
- 選択中コマの4隅すべて（`NW`, `NE`, `SW`, `SE`）にハンドルを描画。
- 4隅いずれのドラッグでも正確に対角を基準としたリサイズ（クランプ付き）が動作するよう実装。
- マウスホバー時のカーソル形状（`nwse-resize`, `nesw-resize`）も完全に一致。

---

## 10. Swap 仕様
- **仕様の明確化**:
  - KOMA identity（`id`, `name`, `color`）は固定。
  - 交換対象（payload）: 座標 (`x, y, w, h`)、`prompt`、`enabled`（および将来の拡張情報）。
  - Shift+Clickで2コマ選択時に「⇄ Swap」をクリックすることで中身が安全に入れ替わります。

---

## 11. Undo / Redo 仕様
- **Prompt入力履歴の適正化**: テキストエリアの `focus` 時に編集前スナップショットを取得し、`blur` 時に初めて履歴をコミット。1文字入力ごとに履歴スタックが溢れたり破壊される問題を解消。
- **キーボード対応**: `Ctrl+Z` で Undo、`Ctrl+Y`（または `Ctrl+Shift+Z`）で Redo。テキスト入力中はブラウザ標準操作を優先。

---

## 12. Mask Empty 仕様
- 有効なRegionが0件の場合、以前の `torch.ones`（全画面白）を廃止し、**`torch.zeros((1, height, width), dtype=torch.float32)`（全画面黒・非選択）** を返すよう修正。
- 将来のRegional Conditioning接続時に、意図しない全画面適用が起きる危険性を完全に排除。
- また、出力スロット5に `active_region_ids_json`（例: `"[1, 2, 3]"`）を追加し、MaskバッチとKOMA IDの対応関係を明示化。

---

## 13. Event Listener Cleanup
- `node.onRemoved` ライフサイクルを実装。
- ノード削除時に `window.addEventListener` で登録した `mousemove`, `mouseup`, `keydown` リスナーを確実に `removeEventListener` で破棄し、メモリリークや重複リスナー蓄積を防止。

---

## 14. Workflow Restore 方式
- ComfyUI標準の `nodeType.prototype.onConfigure` ライフサイクルフックに統合。
- ワークフロー読み込み完了時に `_tegakiRestoreFromWidgets` が自動呼び出しされ、`setTimeout` への依存を排除。

---

## 15. Backend Test 結果
`scripts/test_region_spec.py` 実行結果:
- 1. default_region_spec: **PASSED**
- 2. panel_count bounds (1 & 6): **PASSED**
- 3. 0 active regions & zeros mask: **PASSED**
- 4. Overlapping & Disabled regions: **PASSED**
- 5. Invalid JSON fallback: **PASSED**
- 6. Missing canvas / regions validation: **PASSED**
- 7. Duplicate region ID validation: **PASSED**
- 8. Negative coords & x+w > 1 clamping: **PASSED**
- 9. Unsupported schema version: **PASSED**
- 10. State Serialization & Reload consistency: **PASSED**
- 11. Unknown fields preservation: **PASSED**
- **全11テストスイート完全合格**。

---

## 16. Frontend Test 結果
- `PHASE2_1_UI_TEST_CHECKLIST.md` に基づき全項目を検証。
- コンソールエラーなし、Canvasリサイズ・スライス・スワップ・削除・Undo/Redo・Workflow保存復元動作を確認。

---

## 17. Wildcard Patch 管理方式
- `ComfyUI-WildcardOrganizer` に適用したローカルパッチを `patches/wildcard_organizer_windows_junction.patch` に保存し、Git追跡対象化。
- `scripts/verify_wildcard_patch.py` による自己診断機能を配備（実行結果: `PATCH PRESENT`）。

---

## 18. Custom Node Manifest
- `CUSTOM_NODE_MANIFEST.md` を新設し、依存ノードのGitリポジトリ、Commit SHA、ローカルパッチ適用状況を明文化。

---

## 19. Documentation 修正
- `README.md`: `04_REGIONAL_LORA_EXPERIMENT` を「試験用・未完成」と明記。Phase 2.1ツール群を追記。
- `RESEARCH_REFERENCES.md`: `comfyui_manga_panel` のライセンス表記を Apache License 2.0 に訂正。外部コードコピーなし（思想・挙動のみ参考）を明記。
- `WORKFLOW_INDEX.md`: `07_MANGA_REGION_EDITOR_UI_TEST` の区分を「開発用検証ハーネス (DEV / TEST)」に整理。

---

## 20. 既知の問題
- `04_REGIONAL_LORA_EXPERIMENT.json` のKSampler未合流（NOT YET REGIONAL / Phase 5で改修）。
- Region Prompt内での `<lora:...>` 記法（現段階では全体適用 / Phase 5で改修）。
- （※Phase 2で指摘された空Mask白出力、リサイズ不整合、Delete欠落、履歴破壊、Junction乖離等はすべて本Phaseで解決済）。

---

## 21. Phase 3へ進める状態か
- **状態**: `REGION_SPEC` のデータ契約、バリデーション、UIイベント処理、およびGit/Runtime同一性が完全に安定しました。
- 次のステップである **Phase 3: Regional Conditioning Compiler**（`REGION_SPEC` から `ConditioningSetMask` / `ConditioningCombine` への自動コンパイルノード）へ進む準備が完全に整いました。

---

## 22. Gemini独自判断で変更した事項と理由
- **`active_region_ids_json` の出力追加**:
  - Maskバッチテンソル（`[N, H, W]`）の各スライスがどのKOMA IDに対応しているかを下流ノードや将来のCompilerが正確に把握できるよう、第5スロット（末尾）にJSON文字列出力を追加しました（既存配線への影響ゼロ）。
- **ステータスメッセージ表示**:
  - 最大6コマ制限時やスライス実行時にCanvas内に短い通知（オーバーレイ）を表示し、操作結果がユーザーに直感的に伝わるようにしました。

---

## 23. PHASE 3 READINESS

```text
PHASE 3 READINESS: GO
```
- REGION_SPECのデータ契約が安定
- Frontend / Backend 同期問題なし
- Runtime と Git 正本が完全に一致
- 主要Editor操作に重大バグなし
