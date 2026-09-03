# KNOWN_ISSUES.md — 既知の問題・制限事項

## 1. 04_REGIONAL_LORA_EXPERIMENT.json の接続状態 (EXPERIMENTAL / NOT YET REGIONAL)
- **現状**: `04_REGIONAL_LORA_EXPERIMENT.json` は2本のLoRAブランチを持つ構造として配置されていますが、コードレベル監査の結果、最終KSamplerには第1ブランチのMODELのみが接続されており、第2ブランチのMODEL/Conditioningが合流していません。
- **影響**: 現状は領域別LoRA（Regional LoRA）として完全には成立しておらず、実質的に単一LoRA生成となります。
- **対応方針**: Phase 2/2.1/2.1.1では安定基盤の維持を最優先とし、Phase 5の「疑似RLL（Impact RegionalSampler等を用いた領域別LoRA実験）」にて本格改修を行います。

---

## 2. Region Prompt内での <lora:...> 記法 (局所適用未対応)
- **現象**: `TegakiMangaRegionEditor` の各コマPrompt内に `<lora:name:weight>` を記述した場合、現段階のバックエンドではMODEL全体にLoRAが適用されます（KOMA 1にのみ効くわけではありません）。
- **対策**: ノード実行時にコンソールへ注意喚起ログを出力しています。局所LoRA適用は将来のPhase 5で実装予定です。

---

## 3. LoRAファイル名解決の競合
- **現象**: 3000個以上のLoRAが存在するため、別々のサブフォルダ（例: `Ani0H/hoge.safetensors` と `Style/hoge.safetensors`）に同名のファイルがある場合、ベースファイル名のみで指定すると先に見つかった方が適用されます。
- **回避策**: `TegakiLoraPromptLoader` は競合を検知した際にログ（コンソール）へ警告を出力します。

---

## 4. ControlNetモデルの事前配置
- **現象**: `05_CONTROLNET_COMPOSITION.json` では汎用ControlNetノードを配置していますが、EasyReforge側のControlNetモデル名が一致しない場合はロードエラーになります。
- **対処**: ワークフローを開いた後、`ControlNetLoader` ノードのドロップダウンから所持しているモデルを選択してください。

---

## 5. Windows Tritonの非対応
- **現象**: 一部のTriton依存拡張はWindowsネイティブではスキップされます。
- **影響**: 標準のPyTorch Attention / VAEデコードが使用されるため、画像の生成結果や品質には一切影響ありません。

---

## [RESOLVED IN PHASE 2.1.1] 解決済みの課題履歴
- **Split処理のPanel Count / Undo不整合**: 未使用コマ探索順序を「panel_count枠内の無効コマ → panel_count<6時の自動拡張」とし、変更前の事前pushHistoryによりUndoで完全復元されるよう修正・テスト完了。
- **新規Region作成時のUndo不整合**: 空白ドラッグ開始の判定成立直後にpushHistoryを呼び、Undoで作成前の非表示・元状態へ完全復元されるよう修正・テスト完了。
- **Layout Resetによるenabled / promptリセット問題**: 矩形座標 (`x, y, w, h`) のみを初期化し、enabled, prompt, panel_count, Canvas Size, Global Prompt, 未知フィールドを100%保持するよう修正・テスト完了。
- **Swapの固定フィールド限定問題**: KOMA identity (id, name, color) のみを固定し、将来の未知メタデータを含む全payloadを汎用交換するよう修正・テスト完了。
- **Syntax Error と Schema Error の同一混同**: 構文エラー（JSONDecodeError）はwarningフォールバック、スキーマ違反（version != 1等）は制作データ保護のため明示的にValueError（Node execution error）を送出するよう分離・テスト完了。
- **enabled型の曖昧性 ('false'文字列の誤判定)**: `bool("false") == True` を防ぐため、厳格な `bool` 型のみを許可し、文字列 `"false"` や `1` は `ValueError` を送出するよう修正・テスト完了。

---

## [RESOLVED IN PHASE 2.1] 解決済みの課題履歴
- **空Region時に全画面白Maskが出力される問題**: 有効Regionが0件の場合に `torch.zeros`（全画面黒・非選択）を出力するよう修正・テスト完了。
- **リサイズハンドルと実動作の不整合**: Canvas描画上の4隅（NW, NE, SW, SE）すべてで正確にリサイズできるよう修正・テスト完了。
- **Delete操作の欠落**: ツールバーのDeleteボタンおよびキーボードDelete/Backspace（テキスト入力中除外）による安全な無効化 (`enabled = false`) を実装。
- **Prompt編集Undoの履歴破壊**: `focus` 時スナップショット取得・`blur` 時コミット方式により、キー入力ごとに履歴が汚れる問題を解消。
- **Git正本とRuntimeコードの乖離リスク**: `ComfyUI/custom_nodes/tegaki_manga_nodes` が `custom_nodes_custom/` へのJunctionであることを保証し、`scripts/test_runtime_source_identity.py` で自動検証。
- **Wildcard Organizerローカル修正の非追跡**: `patches/wildcard_organizer_windows_junction.patch` としてGit管理下に保存し、`scripts/verify_wildcard_patch.py` で自己診断可能に整備。
- **REGION_SPEC二重管理・無条件上書き**: REGION_SPEC (v1) をSingle Source of Truthとし、外側WidgetはFacadeとして双方向同期。有効なSpecが存在する場合は外側引数での上書きを廃止。
