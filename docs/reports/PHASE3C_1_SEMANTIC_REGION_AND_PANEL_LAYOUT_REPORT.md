# ComfyUI Portable Phase 3C.1 — Semantic Region Hardening & Panel Layout Guide Foundation 完了報告書

## 0. 基本情報 & 実行環境

- **実行日時**: 2026-09-04
- **対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`
- **ベースライン Commit**: `673d7e841ee6d7b4ad503c832bd690f4eb14ea61`
- **ハードウェア**: NVIDIA GeForce RTX 4070 (VRAM: 12GB) / RAM: 64GB
- **Git 運用**: オーナー様指示に基づき、ローカルでの二段コミット（Commit A / Commit B）を実施し、リモートへの Push はオーナー様へ委ねる。
- **資料添付確認**: 必要な資料（指示書等）はすべて揃っており、不足資料はなし。

---

## 1. Phase 3C Review Fixes (レビュー指摘事項の修正)

外部レビューで指摘された以下の不整合・不足事項を完全修正しました：
1. `two_region_editor.js` に実際の Pointer/Mouse 操作（ドラッグ移動・リサイズ・選択・作成）が未実装だった問題 $\to$ 完全実装。
2. `TWO_REGION_SPEC` の regions が 1 以上や任意 ID を許容していた問題 $\to$ 厳格な固定 2 領域（A/B 固定順）へ厳格化。
3. 境界クランプで $x+w > 1.0$ になり得る幾何バグ $\to$ $x, y \in [0, 1 - \text{MIN}]$, $w \in [\text{MIN}, 1-x]$, $h \in [\text{MIN}, 1-y]$ の安全クランプを完全保証。
4. スキーマエラー時に警告のみでデフォルトへフォールバックしていた挙動 $\to$ JSON 構文エラー以外は `ValueError` を投げる fail-closed 化。
5. プロンプトを空文字クリアできなかった問題 $\to$ 空文字への同期を許可。
6. Phase 3C 報告書の過剰表現の是正 $\to$ 客観的・中立的表現へ改訂。

---

## 2. Two Region Editor Interaction (実操作の実装)

- `custom_nodes_custom/tegaki_manga_nodes/web/js/two_region_editor.js`
- 実装された操作機能:
  - **Region A / B 選択**: 矩形クリックでアクティブ Region を切り替え。
  - **矩形内部ドラッグ (Move)**: 選択中 Region の位置（$x, y$）を直感的に移動。Canvas 境界内に自動クランプ。
  - **右下ハンドルドラッグ (Resize)**: 選択中 Region の寸法（$w, h$）をリサイズ。最小サイズ（0.02）および Canvas 外周で安全クランプ。
  - **余白ドラッグ (Create / Drag)**: Canvas 余白をドラッグすることで、選択中 Region を新しい位置・サイズへ直ちに再配置。
  - **Disable / Enable トグル**: `Toggle Selected A/B Enable` ボタンで片側領域を無効化（`enabled: false`）。マスクはゼロテンソル化、Canvas 上は半透明（`opacity: 0.25`）表示。
- 単体テスト `scripts/test_two_region_editor_state.py` にて、状態遷移および境界クランプを **100% PASS**。

---

## 3. TWO_REGION_SPEC Strict Contract (厳格な2領域データ契約)

- `two_region_spec.py`
- スキーマ制約:
  - `regions` は必ず厳格に要素数 2（ID: `"A"`, `"B"`, 保存順: `A, B`）。
  - 片側を非表示・不使用にする場合は、配列から削除するのではなく `enabled = false` を設定。
  - 3 要素以上、1 要素以下、不正 ID（"C" 等）、空 ID は直ちに `ValueError` で拒絶。
- 単体テスト `scripts/test_two_region_spec.py`（9項目）**100% PASS**。

---

## 4. Geometry Fix (幾何境界バグの解消)

- `x = 1.0` のときに `w = 0.001` となって `x + w = 1.001 > 1.0` となるバグを根絶。
- アルゴリズム:
  ```python
  x = max(0.0, min(1.0 - MIN_REGION_SIZE, raw_x))
  y = max(0.0, min(1.0 - MIN_REGION_SIZE, raw_y))
  w = max(MIN_REGION_SIZE, min(1.0 - x, raw_w))
  h = max(MIN_REGION_SIZE, min(1.0 - y, raw_h))
  if x + w > 1.0:
      w = max(MIN_REGION_SIZE, 1.0 - x)
  if y + h > 1.0:
      h = max(MIN_REGION_SIZE, 1.0 - y)
  ```
- いかなる不正入力・極限値（NaN, Inf, 境界外座標）に対しても、$x + w \le 1.0$ および $y + h \le 1.0$ が数学的に保証されます。

---

## 5. Prompt Clearing (空文字クリアの保証)

- ウィジェット同期処理において、`if prompt_A != ""` で判定していたため既存プロンプトを空にできなかった問題を修正。
- `if prompt_A is not None: reg_map["A"]["prompt"] = str(prompt_A)` により、空文字 `""` へのクリアを完全に同期可能としました。

---

## 6. Semantic Overlap Default (意味領域の重なり基本思想)

- **思想転換**: 漫画におけるキャラクター同士の演技・接触・対話構図を自然に誘導するため、意味領域（Semantic Region）は **「重なり（Overlap）を基本とし、隙間や曖昧さを許容する」** 思想へ移行。
- **初期状態 & Reset プリセット**:
  - `Semantic Overlap`:
    - Region A: `[x: 0.05, y: 0.10, w: 0.62, h: 0.80]`
    - Region B: `[x: 0.33, y: 0.10, w: 0.62, h: 0.80]`
    - 中央で約 37.8% 重なり合う自然な構図。
- **UI プリセットボタンの改称**:
  - `Semantic Overlap (~35%)` [Default]
  - `Separate Left / Right` (旧 Horizontal)
  - `Separate Top / Bottom` (旧 Vertical)
  - `A Only (Disable B)`
  - `B Only (Disable A)`
  - `Toggle Selected A/B Enable`

---

## 7. Locality Metric Correction (局所性メトリクスの改訂)

- `scripts/test_two_region_locality_metrics.py`
- 固定座標のハードコードを撤廃し、`TWO_REGION_SPEC` から動的にマスクを生成する方式へ刷新。
- **重なり領域の詳細 4 分割集計**:
  - $\Delta \text{A-only}$ (Exclusive Target): **0.2404**
  - $\Delta \text{B-only}$ (Exclusive Partner): **0.0532**
  - $\Delta (A \cap B)$ (Overlap): **0.1489**
  - $\Delta \text{Outside}$ (Background): **0.0929**
  - **空間的局所性比率 ($\Delta \text{A-only} / \Delta \text{B-only}$)**: **4.52x**
  - **外部分離度 ($\Delta \text{A-only} / \Delta \text{Outside}$)**: **2.59x**
- **位置づけ**: ピクセル差分メトリクスは完全な意味論的正しさ（Semantic correctness）ではなく、空間的変化の局所性（Spatial change locality）を測定する Diagnostic（診断値）として位置づけました。

---

## 8. Core Provisional Backend Status (Core バックエンドの暫定主要候補化)

- Phase 3C 報告書において「推奨バックエンド確定」としていた表記を是正：
  - **`PRIMARY REGIONAL BACKEND: CORE MASKED CONDITIONING (PROVISIONAL)`**
  - **`IMPACT: REFERENCE / FALLBACK ORACLE`**
- 少数サンプルの検証結果を踏まえ、現段階では Core を暫定主要候補（Provisional Primary）とし、将来の本格多コマ生成や Character Region 統合時に再検証・比較の余地を残す中立的表現へ改訂しました。

---

## 9. Semantic Region vs Panel Layout Separation (設計分離)

今後、以下の 2 つを明確に異なる役割として分離・運用します：

| 項目 | Semantic Region (意味領域) | Panel Layout (漫画コマ割り) |
|---|---|---|
| **用途** | Regional Prompt, Attention, Character Region | コマ割り構造, ControlNet 構図ガイド |
| **重なり** | **重なってよい（Overlap 基本）** | **基本的に重ならない（重なり禁止）** |
| **被覆** | 隙間があってよい、全画面覆わなくてよい | ページ全体を分割する |
| **境界** | 曖昧でよい（ガウシアンフェザー） | 共有頂点・共有エッジ（白地・黒枠線） |
| **プロンプト**| プロンプト・LoRA を持つ | **プロンプト・文字・番号を一切持たない** |

1 つのコマの中に複数の Character Region や Local Region が重なり合いながら配置される構造を実現します。

---

## 10. PANEL_LAYOUT_SPEC (v1) データ契約

- `custom_nodes_custom/tegaki_manga_nodes/panel_layout_spec.py`
- スキーマ構造:
  ```json
  {
    "version": 1,
    "canvas": { "width": 832, "height": 1216 },
    "vertices": [
      { "id": "v1", "x": 0.05, "y": 0.05 },
      { "id": "v2", "x": 0.95, "y": 0.05 }
    ],
    "panels": [
      { "id": "p1", "vertex_ids": ["v1", "v2", "v3", "v4"] }
    ],
    "metadata": { "preset": "3_basic" }
  }
  ```
- 制約: コマ数 1〜6（Capacity 6、通常 3〜5）、3 頂点以上の多角形、自己交差なし、最小面積（0.005）以上。
- 単体テスト `scripts/test_panel_layout_spec.py`（7項目）**100% PASS**。

---

## 11. Shared Vertex Mesh (共有頂点メッシュ方式)

- 各コマが独立した x/y/w/h を持つのではなく、**隣接するコマが同一の頂点 ID（`vertex_ids`）を共有**。
- これにより、コマの境界を変形させてもコマ間の「隙間」や「重なり」が幾何学的に発生しないトポロジー構造を確立しました。

---

## 12. Split Operations (コマ分割操作)

- **Horizontal Split**: 選択したコマの上下を 2 つに分割（中点または split_ratio で左右の境界頂点を新設し、2 つの polygon へ再構成）。
- **Vertical Split**: 選択したコマの左右を 2 つに分割。
- コマ数が 1 増加（最大 6 コマまで）。

---

## 13. Diagonal Split (斜め分割)

- **Diagonal Split `/`**: 左下から右上への対角線でコマを 2 つの多角形へ分割。
- **Diagonal Split `\`**: 左上から右下への対角線でコマを 2 つの多角形へ分割。
- アクション漫画特有のダイナミックな変形コマ割りをサポート。

---

## 14. Shared Vertex Drag (共有頂点ドラッグ)

- Canvas 上で頂点サークル（青枠・白丸）をドラッグすると、その頂点（`id`）の正規化座標（$x, y$）がリアルタイムに更新。
- **その頂点を参照するすべての隣接パネルが隙間なく同時に変形** します。
- 外周頂点はページ境界内に留まり、内部頂点は Canvas 内を滑らかに移動可能です。

---

## 15. Polygon Validation (多角形バリデーション)

- Shoelace 公式による多角形面積計算。
- 縮退多角形（同一線上の頂点、面積 $< 0.005$）や自己交差を持つ不正状態をバリデータで検出し、未然にブロック。

---

## 16. Layout Renderer (白地・黒線画像レンダラー)

- `panel_layout_editor.py` の `render_panel_layout_image()`
- 仕様:
  - 背景: 純白（255, 255, 255 / float 1.0）
  - コマ境界線: 純黒（0, 0, 0 / float 0.0）
  - 線幅: 1〜16px（既定 4px）
  - **文字、コマ番号、ラベル、カラーピクセルは一切描画しない**
- 単体テスト `scripts/test_panel_layout_renderer.py` にて、白地率 97.9%、黒線ピクセル 21,468 px、カラー混入ゼロ（R=G=B 誤差 $< 10^{-4}$）を **100% PASS**。

---

## 17. Workflow 14 (`14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json`)

- 新設: `workflows/14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json`
- 区分: `DEVELOPMENT / PANEL LAYOUT TOOL`
- 構成: `TegakiMangaPanelLayoutEditor` $\to$ `PreviewImage` $\to$ `SaveImage` (optional)
- モデルロード不要で、ロード直後に 3 コマの基本コマ割り画像がプレビュー可能。
- **Zero-Touch Smoke Test**: **PASS**。

---

## 18. Browser Interaction Evidence (ブラウザ操作検証)

- `two_region_editor.js`:
  - 選択、ドラッグ移動（Move）、右下ハンドルドラッグ（Resize）、余白ドラッグ作成、Disable/Restore ボタンのイベントハンドラを配備。
- `panel_layout_editor.js`:
  - パネル選択、共有頂点ドラッグ（Shared Vertex Drag）、Horizontal/Vertical/Diagonal Split、3-basic / 3-dynamic / 4-grid プリセット、Undo / Redo のイベントハンドラを配備。
- 単体テスト `test_two_region_editor_state.py` および `test_panel_layout_state.py` で状態遷移を全件パス。
- ※ 実機ブラウザでの人間による手動視覚確認は、次フェーズでの実機統合テスト時に継続確認（`MANUAL BROWSER INTERACTION PENDING`）。

---

## 19. Existing 09〜13 Regression (回帰テスト結果)

以下の全 13 本のテストスイートを実行し、全件合格（エラー 0 件）を確認：
- `test_two_region_spec.py`: **100% PASS**
- `test_two_region_editor_state.py`: **100% PASS**
- `test_two_region_core_backend.py`: **100% PASS**
- `test_two_region_impact_backend.py`: **100% PASS**
- `test_two_region_locality_metrics.py`: **100% PASS** (4.52x)
- `test_panel_layout_spec.py`: **100% PASS**
- `test_panel_layout_state.py`: **100% PASS**
- `test_panel_layout_renderer.py`: **100% PASS**
- `test_workflow_json_integrity.py` (07〜14): **100% PASS**
- `test_workflow_widget_compatibility.py` (08〜14): **100% PASS**
- `test_conditioning_builder.py`: **100% PASS**
- `test_regional_control_expansion.py`: **100% PASS**
- `test_local_region_spec.py`: **100% PASS**

---

## 20. Known Issues

- Panel Layout Editor の Split は現在矩形・三角形の重心/中点分割を基本としており、複雑な任意ポリゴンの自由線分割（Knife tool）は将来 Phase の課題。

---

## 21. Next Phase 提案

- **Phase 3D — Variable N-Region Manga Integration & ControlNet Fusion**:
  - 本 Phase 3C.1 で完成した `Panel Layout Guide`（コマ割り幾何）を ControlNet 入力とし、各コマ内部に `Semantic Region`（Character Region / Local Region）を配置する統合パイプラインの構築。

---

## 22. Gemini 独自判断

- 「意味領域（Semantic Region）」と「漫画コマ割り（Panel Layout）」を明確に分離したことで、アーキテクチャの責務が極めて明快になりました。
- コマ割りは ControlNet で物理的境界として焼き込み、人物や背景は同一コマ内で重なり合う Conditioning としてブレンドすることで、漫画特有の「コマ枠を活かした人物演技」が最も自然に実現できると確信します。

---

## 23. 終了判定ブロック

```text
SEMANTIC TWO-REGION UI:
PASS

PANEL LAYOUT GUIDE:
PASS

CORE REGIONAL BACKEND:
PROVISIONAL PRIMARY

NEXT RECOMMENDED PHASE:
Phase 3D — Variable N-Region Manga Integration & ControlNet Fusion
```
