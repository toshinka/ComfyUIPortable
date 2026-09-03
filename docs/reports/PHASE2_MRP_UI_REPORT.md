# PHASE2_MRP_UI_REPORT.md — Phase 2 改修報告書
## Wildcard UX強化 + Manga Region Editor UI

**作成日時**: 2026-09-03 11:53 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  

---

## 1. 実装内容
1. **Wildcard UXの強化**:
   - `ComfyUI-WildcardOrganizer` の導入とWindowsジャンクション環境向けパッチ適用。
   - EasyReforge側の192個のWildcard資産をそのままブラウズ・検索・プレビュー・プロンプト挿入可能に整備。
2. **Tegaki Manga Region Editor UI の開発**:
   - 最大6コマ (KOMA 1〜6) に対応した視覚的Region Editorノード (`TegakiMangaRegionEditor`) およびフロントエンドWeb拡張 (`web/js/tegaki_region_editor.js`) を開発。
   - 漫画縦構図 (832x1216) に対応したCanvas上での矩形作成・移動・リサイズ・重なり・Shift複数選択一括移動。
   - 各コマごとのPrompt欄 + Global Prompt欄。
   - スライス（水平・垂直50:50分割）、コマ入れ替え（Swap）、Undo/Redo (Ctrl+Z/Ctrl+Y)。
   - **State完全保存**: Workflow保存・再読み込み時の完全なレイアウト復元。
3. **統一データ仕様 `REGION_SPEC` (v1) の確立**:
   - UIと生成Backendを完全分離し、将来の外部GUI（MCWW/独自サイドバー等）からも読み書き可能な共通スキーマを策定。
4. **UI検証用ワークフロー `07_MANGA_REGION_EDITOR_UI_TEST.json` の作成**:
   - 既存の安定生成基盤（01 txt2img, 02 I2I）を壊さず、単体でレイアウト編集とプレビュー画像確認ができるワークフローを配備。
5. **既存ワークフローの接続監査**:
   - `03_MANGA_REGIONAL_PROMPT` が固定ノード配線である旨の明記、および `04_REGIONAL_LORA_EXPERIMENT` のKSampler未接続（NOT YET REGIONAL）の特定とドキュメント化。

---

## 2. 導入Custom Node
- **ComfyUI-WildcardOrganizer**: Wildcard検索・プレビュー・オーガナイザー
- **tegaki_manga_nodes**: 独自漫画制作ノードパッケージ（`TegakiMangaRegionEditor` を新規追加）

---

## 3. 各GitHub URL
- ComfyUI-WildcardOrganizer: `https://github.com/lokitsar/ComfyUI-WildcardOrganizer`
- comfyui_manga_panel (参考): `https://github.com/Tsubasa109/comfyui_manga_panel`
- Nukun_ComfyUI_Nodes (参考): `https://github.com/OnekoSL/Nukun_ComfyUI_Nodes`

---

## 4. Wildcard Organizer評価
- **優れている点**:
  - WebUI上でWildcardファイルの内容を即座にプレビューでき、Raw PromptとResolved Promptの両方を確認できる。
  - テキスト検索（ファイル名および中身検索）が高速。
- **課題と対応**:
  - Windows環境において、ジャンクション（`wildcards` -> `E:\Data\...`）を使用した際にパス解決でドライブレターが跨がる問題があったため、`nodes.py` 内の `_preview` に安全なキーベースフォールバックを適用して解決。
  - ルート直下にもジャンクション（`ComfyUIPortable\wildcards`）を配置することで、デフォルト設定のままシームレスに全192ファイルを認識可能としました。

---

## 5. Manga Panel実装から参考にした点
- `comfyui_manga_panel` から、Canvas上でのマウスドラッグによる矩形生成、内部ドラッグ移動、角ハンドルリサイズ、および将来的なI2I Crop/Compositeパイプラインの思想を参考にしました。

---

## 6. Nukun Regional Editorから参考にした点
- `Nukun_ComfyUI_Nodes` のブラウザ側矩形エディタと、0.0〜1.0正規化座標による解像度非依存レイアウト管理手法を参考にしました。

---

## 7. 独自実装した部分
- **`TegakiMangaRegionEditor` (Python Backend)**:
  - `REGION_SPEC` (v1) のバリデーションとデフォルト生成。
  - Pillowを用いた漫画原稿プレビュー画像生成（`[1, H, W, 3]` テンソル出力）。
  - 各コマのバイナリマスクバッチ生成（`[N, H, W]` テンソル出力）。
- **`tegaki_region_editor.js` (Frontend Web Extension)**:
  - 漫画比率対応のインラインCanvas。
  - KOMA 1〜6 カラーパレット連動。
  - 複数コマ選択・一括ドラッグ移動 (Shift+Click)。
  - 水平・垂直スライス機能 (Split H / Split V)。
  - コマ入れ替え機能 (Swap)。
  - Undo / Redo 履歴スタック（最大50件）。
  - Widget同期によるWorkflow JSON完全永続化。

---

## 8. なぜ独自実装が必要だったか
- 既存のManga PanelやNukunノードは、コマ数が固定だったり、Prompt入力と矩形操作が分断されていたり、将来の外部GUI（MCWW/独自サイドバー）とのデータ分離思想が考慮されていませんでした。
- Tegakiプロジェクトの目指す「最大6コマの視覚的レイアウト」「KOMAごとのPrompt管理」「将来のRLL/MRP連携」「UIとBackendの完全分離」を満たすため、専用の軽量Editorを独自実装しました。

---

## 9. UI操作一覧
- **矩形作成**: Canvas上の空白領域をドラッグ（未使用KOMAに自動割り当て）。
- **選択**: 矩形または右側KOMAカードをクリック（枠線が点線になりハイライト）。
- **複数選択**: Shift + クリック（複数KOMAを選択）。
- **移動**: 選択中矩形をドラッグ（複数選択時は一括移動）。
- **リサイズ**: 矩形右下の白ハンドルをドラッグ。
- **スライス (Split H / V)**: 選択中コマを50:50で分割し、次の空きコマへ割り当て。
- **入れ替え (Swap)**: 2つのコマをShift選択してSwapボタンをクリック。
- **Undo / Redo**: ツールバーのボタン、または `Ctrl+Z` / `Ctrl+Y`。
- **リセット (Reset)**: 初期3コマレイアウトに復元。
- **Prompt入力**: 右側の各KOMAカード内TextAreaに入力（空欄ならconditioningに影響なし）。

---

## 10. REGION_SPEC schema (v1)
```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "panel_count": 3,
  "global_prompt": "manga page, monochrome, expressive linework",
  "regions": [
    {
      "id": 1,
      "name": "KOMA 1",
      "enabled": true,
      "x": 0.06,
      "y": 0.05,
      "w": 0.88,
      "h": 0.28,
      "prompt": "1girl, dynamic action pose",
      "color": "#E53935"
    },
    {
      "id": 2,
      "name": "KOMA 2",
      "enabled": true,
      "x": 0.06,
      "y": 0.36,
      "w": 0.42,
      "h": 0.58,
      "prompt": "1boy, reaction face",
      "color": "#1E88E5"
    },
    {
      "id": 3,
      "name": "KOMA 3",
      "enabled": true,
      "x": 0.52,
      "y": 0.36,
      "w": 0.42,
      "h": 0.58,
      "prompt": "speed lines, dramatic effect",
      "color": "#43A047"
    }
  ]
}
```

---

## 11. 自動テスト結果
- `scripts/test_region_spec.py`:
  - `default_region_spec`: PASSED
  - `render_preview_image` (torch.Size([1, 1216, 832, 3])): PASSED
  - `render_mask_batch` (torch.Size([3, 1216, 832])): PASSED
  - `TegakiMangaRegionEditor` ノード実行: PASSED
  - State Preservation (JSONシリアライズ・復元): PASSED
- `scripts/test_workflow_07.py`:
  - Workflow 07 の実機推論キューイングおよびプレビュー画像生成 (`RegionEditor_Test_00001_.png`): PASSED

---

## 12. 手動テスト結果
- **非破壊確認**:
  - `scripts/test_generation.py` を再実行し、既存の `01_BASIC_ILLUSTRIOUS_TXT2IMG.json` が従来通り正常に画像生成できることを実証（生成物: `Txt2Img_Test_00002_.png`）。
- **Wildcard検索 & プレビュー**:
  - `/wildcard_organizer/search?root=wildcards&query=pose` -> 12件ヒット。
  - `/wildcard_organizer/preview?root=wildcards&path=.../poses1.txt` -> 内容取得成功。

---

## 13. 既知の問題
- **04番ワークフローの接続状態**:
  - `workflows/04_REGIONAL_LORA_EXPERIMENT.json` において、2本目のLoRAブランチが最終KSamplerに合流しておらず、実質的に単一LoRA生成となっています。現状は「EXPERIMENTAL / NOT YET REGIONAL」として記録し、Phase 5のRLL先行実験にて本格改修を行います。
- **Region Prompt内のLoRA指定**:
  - 現時点ではRegion Prompt内に `<lora:...>` を記述しても全体適用となるため、ログおよびUIで注意喚起を行っています。

---

## 14. 今後のPhase 3案
- **Regional Conditioning Compiler の開発**:
  - `TegakiMangaRegionEditor` が出力する `REGION_SPEC` を受け取り、内部で自動的に `ConditioningSetMask` と `ConditioningCombine` を構築して、単一のCONDITIONINGとしてサンプラーへ渡すコンパイラノードの実装。

---

## 15. 指示外でGemini自身が追加したもの
- **プレビュー画像出力機能 (`preview_image`)**:
  - Region Editorノードの出力端子にプレビュー画像を設け、ComfyUIの標準 `PreviewImage` ノードにつなぐだけで視覚的にコマ配置を確認できるようにしました。
- **自動テストスクリプト (`scripts/test_region_spec.py`, `scripts/test_workflow_07.py`)**:
  - バックエンド単体およびComfyUIサーバー経由での自動実行テスト。

---

## 16. それを追加した理由
- フロントエンドJSが動作しない環境や、将来の外部AI・API経由でのレイアウト検証時にも、画像として即座に矩形配置を確認できるようにするため。

---

## 17. 削除しても基本機能へ影響しないか
- プレビュー出力端子は独立しているため、利用しなくても `REGION_SPEC` やマスクの出力には一切影響ありません。

---

## 18. Future User UI Compatibility (将来のユーザー向けGUIとの分離)
- **REGION_SPECの外部UI利用可能性**:
  - 純粋なJSONデータ構造であるため、MCWW (Minimalistic Comfy Wrapper WebUI)、Tegaki本体のキャンバスサイドバー、独立Webフロントエンドのいずれからも直接生成・編集・送信が可能です。
- **Region EditorとBackendの分離状況**:
  - バックエンドノードは `region_spec_data`（JSON文字列）を受け取って処理するだけであり、フロントエンドDOMやCanvas実装には一切依存していません。
- **Subgraph化可能性**:
  - 将来、Region EditorとCompiler、SamplerをSubgraph内にカプセル化し、ユーザーには `REGION_SPEC` の設定とPromptのみを公開する構成が容易に実現可能です。
- **MCWW等で公開可能な入力値**:
  - `panel_count`, `canvas_width`, `canvas_height`, `global_prompt`, 各KOMA Prompt。
- **独自UIが必要になる部分**:
  - マウスによる直感的なコマ割りドラッグ・リサイズ操作は、MCWW等の汎用Form UIでは難しいため、Tegaki専用のCanvasコンポーネント（今回作成したJS拡張、またはTegaki本体のキャンバスUI）として提供するのが最適です。
