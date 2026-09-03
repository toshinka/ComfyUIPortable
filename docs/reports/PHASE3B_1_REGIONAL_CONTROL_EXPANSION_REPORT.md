# Phase 3B.1 Regional Control Expansion & Validation 完了報告書

**コミット対象**: Phase 3B.1 Regional Control Expansion 実装・テスト・Workflow 10・報告書  
**作成日**: 2026-09-03  
**ステータス**: COMPLETED (All Tests Passed, Real Image Generation Verified)

---

## 1. 目的とスコープ

Phase 3B で確立された Manga Regional Generation POC（3階層: Global / Panel / Character）を基盤とし、第4の階層として **`LOCAL_REGION`（コマ内局所領域）** を導入しました。  
本改修の主目的は以下の通りです：
- 特定の Character に属さない情景・背景演出・小道具（窓際の机群、壁面ポスター、夕焼けスポット等）をコマ内の特定矩形へ安全かつ局所的に指示可能とする。
- Global / Panel / Local Region / Character の **4階層統合実行計画** を策定・正規化する。
- Page 座標への投影、マルチレイヤーマスク生成、Core 準拠 Conditioning 合成、実機画像生成による効き確認を一気通貫で検証・実証する。
- 既存の Workflow 07 / 08 / 09 および Character-only 仕様に対する **100% 完全な後方互換性** を担保する。

---

## 2. 現状課題と今回の変更

| 領域 | Phase 3B までの状態 | Phase 3B.1 での解決 |
|---|---|---|
| **制御階層** | Global / Panel / Character の3階層 | `LOCAL_REGION` を加えた4階層モデルへ拡張 |
| **小道具・情景指定** | コマ全体プロンプトに混ぜるしかなく、コマ内の特定位置（窓際、壁面など）に配置できない | コマ内局所領域（`area: {x, y, w, h}`）へダイレクトに配置可能 |
| **データ契約** | `characters` のみ定義 | `regions[i].local_regions` を厳格にスキーマ定義・バリデート |
| **Mask 出力** | Panel Masks, Character Masks | `local_region_masks` を追加。Preview 画像にもシアン／エメラルド系で可視化 |
| **Mask 境界** | ハードエッジ矩形のみ | `mask_feather`（0〜64px）によるガウシアンブラー境界ぼかしを配備 |
| **Conditioning** | Global ──▶ Panel ──▶ Character | Global ──▶ Panel ──▶ Local Region ──▶ Character の優先順位で Core 結合 |
| **Character 重なり** | キャラ同士のみ | Character と Local Region の重なり（Overlap）を安全に共存許容 |

---

## 3. 採用した設計判断

1. **後方互換性ファースト（末尾ポート配置）**:
   - `TegakiMangaMaskBuilder` の出力ポートにおいて、既存の slot 0: `panel_masks`, slot 1: `character_masks`, slot 2: `mask_preview`, slot 3: `debug_json` を維持し、新設の `local_region_masks` を **slot 4（末尾）** に配置しました。
   - `TegakiMangaConditioningBuilder` においても、slot 0: `positive`, slot 1: `negative`, slot 2: `panel_masks`, slot 3: `character_masks`, slot 4: `debug_json` を維持し、`local_region_mask_batch` を **slot 5（末尾）** に配置しました。
   - これにより、既存の `09_MANGA_REGIONAL_GENERATION_POC.json` ワークフローの全リンクが一切壊れずそのまま稼働します。
2. **KOMA-local 正規化座標系**:
   - Local Region の座標系は、Character と同様に「コマ左上を (0,0)、右下を (1,1) とする正規化座標」を採用しました。コマの移動やリサイズが行われても、コマ内の相対配置が自動維持されます。
3. **タグ抽出 LoRA の合流**:
   - `local_regions[i].prompt` に含まれる `<lora:name:weight>` タグは、LoRA Parser により自動抽出され、コマ LoRA プランへ安全に集約されます。

---

## 4. 4階層の境界整理

指示書第20項およびデータ契約に基づく4階層の優先順位と役割分担：

$$\text{Global (unmasked)} \longrightarrow \text{Panel (masked)} \longrightarrow \text{Local Region (masked)} \longrightarrow \text{Character (masked)}$$

1. **Global (`global_prompt`)**: マスクなし・ページ全体へ適用。作風、トーン、モノクロ線画、全体光線。
2. **Panel (`panel.prompt`)**: コマ矩形マスク適用。コマのシチュエーション（教室、廊下、屋上等）。
3. **Local Region (`local_regions[].prompt`)**: コマ内局所マスク適用。コマ内の特定の場所・オブジェクト（窓際の机群、壁の掲示板等）。
4. **Character (`characters[].combined_prompt`)**: キャラクターマスク適用。最も具体的で優先度の高い人物描写（表情、ポーズ、髪型、衣装）。

---

## 5. `LOCAL_REGION` のデータ契約仕様

### スキーマ定義
```json
{
  "id": "lr_window_desks",
  "name": "Window Desks",
  "enabled": true,
  "prompt": "school desks near the window, sunlight streaming",
  "negative_prompt": "dark, shadow",
  "area": {
    "x": 0.10,
    "y": 0.15,
    "w": 0.38,
    "h": 0.70
  },
  "metadata": {}
}
```

### バリデーション制約
- `id`: 空文字不可の strict string。コマ内で一意（重複は `ValueError`）。
- `name`: strict string。省略時は `id`。
- `enabled`: strict bool（`"true"` などの文字列は拒絶）。
- `prompt` / `negative_prompt`: strict string。
- `area`: 必須 dict。`normalize_rect` を通過（$0.0 \le x, y \le 1.0$, $x+w \le 1.0$, $y+h \le 1.0$, $w, h \ge 0.05$）。

---

## 6. `scene_spec.py` の実装差分

- **`validate_local_region(local_region, context_name)` 新設**:
  - 各フィールドの型、有限値、境界クランプ、正規化を検証。
- **`validate_compile_plan(plan)` 拡張**:
  - `panel.local_regions` が存在する場合に全要素の型・重複IDを深層検証。省略時は空リスト `[]` を補完。
- **`validate_page_compile_plan(page_plan)` 互換維持**:
  - 各パネルが自動的に深層検証を通過。

---

## 7. `scene_compiler.py` の実装差分

- **`compile_panel_data(...)` 拡張**:
  - `target_koma.get("local_regions", [])` を走査し、バリデーションと重複検出を実施。
  - LoRA Parser を適用し、Clean prompt 化とコマ LoRA プランへの合流を実行。
  - 自然結合プレビュー（`compiled_prompt` / `compiled_negative_prompt`）において 4 階層の優先順序で結合。
  - `compile_plan["panel"]["local_regions"]` へ格納。
- **`TegakiMangaPageCompiler` 拡張**:
  - 全 Active コマの Local Regions を集約して `PAGE_COMPILE_PLAN` を構築。

---

## 8. `mask_builder.py` の実装差分

- **Page 座標投影計算**:
  - $page\_x = k_x + k_w \cdot l_x$
  - $page\_y = k_y + k_h \cdot l_y$
  - $page\_w = k_w \cdot l_w$
  - $page\_h = k_h \cdot l_h$
- **フェザー処理（`mask_feather`）**:
  - `mask_feather > 0` の場合、PIL `ImageFilter.GaussianBlur` によりマスク境界を滑らかにぼかし。
- **Mask Preview 画像の強化**:
  - KOMA 枠線（ベージュ）に加え、Local Region をシアン系パレット（`#06b6d4`、ラベル: `K{pid}:L:{name}`）で半透明合成。Character オーバーレイと美しく重なり表示。
- **出力ポート構成**:
  - `("panel_masks", "character_masks", "mask_preview", "debug_json", "local_region_masks")`

---

## 9. `conditioning_builder.py` の実装差分

- **パラメータ追加**:
  - `local_region_strength` (FLOAT, default 1.0, min 0.0, max 2.0)
  - `mask_feather` (INT, default 0, min 0, max 64)
- **4階層 Conditioning 合成**:
  - Global (unmasked) ──▶ Panel (masked) ──▶ Local Region (masked) ──▶ Character (masked)
- **Overlap 許容**:
  - Character Area と Local Region の重複ピクセルに対して、Core API のリスト結合によって両方の Conditioning を共存適用。
- **出力ポート構成**:
  - `("positive", "negative", "panel_masks", "character_masks", "debug_json", "local_region_masks")`

---

## 10. `TegakiCompilePlanInspector` の監査強化

- Inspector 出力テキストに `--- Local Regions ({count}) ---` セクションを追加。
- 各 Local Region の ID, Name, Positive/Negative Prompt, 領域座標（`[x, y, w, h]`）を一覧表示。

---

## 11. ワークフロー 10 の設計と配置

- **ファイルパス**: `workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json`
- **区分**: `EXPERIMENTAL / CONTROL EXPANSION HARNESS`
- **ノード配置**:
  - Group 1: Model & Global LoRA (`CheckpointLoaderSimple`, `TegakiLoraPromptLoader`)
  - Group 2: Page / Region (`TegakiMangaRegionEditor` with Local Regions, `PreviewImage`)
  - Group 3: Cast & Page Compiler (`TegakiMangaPageCompiler`)
  - Group 4: Mask Builder & Preview (`TegakiMangaMaskBuilder`, `PreviewImage`)
  - Group 5: Conditioning Builder (`TegakiMangaConditioningBuilder`)
  - Group 6: Sampling & Decode (`EmptyLatentImage`, `KSampler`, `VAEDecode`)
  - Group 7: Output & Inspector (`SaveImage`, `TegakiMangaSceneCompiler`, `TegakiCompilePlanInspector`)

---

## 12. 既存ワークフロー（07〜09）への影響と後方互換性

- **07 (CAST Editor & Binding)**: 完全互換。
- **08 (Scene Contract Test)**: 完全互換。
- **09 (Regional Generation POC)**: 出力ポートの末尾配置により、既存のリンク（slot 0〜3, slot 0〜4）が完全に一致し、100% 互換動作。
- `local_regions` が省略された旧形式データは、自動的に空リスト `[]` として処理され、エラーなく動作します。

---

## 13. 実装・結合テスト結果一覧

| テストスクリプト | 項目数 | 結果 | 主な検証内容 |
|---|---|---|---|
| `scripts/test_local_region_spec.py` | 7 | **PASSED** | 正常系、未指定互換、非list拒絶、非bool拒絶、非str拒絶、area不正拒絶、重複ID拒絶 |
| `scripts/test_page_compile_plan.py` | 8 | **PASSED** | 3コマ集約、キャラ分散、Mask投影、area=Noneフォールバック、CAST欠落互換 |
| `scripts/test_conditioning_builder.py` | 4 | **PASSED** | Conditioning生成、Mask形状、ブランチ数整合 |
| `scripts/test_regional_control_expansion.py` | 5 | **PASSED** | 4階層コンパイル、Local Region投影、9ブランチ合成、Overlap共存、旧形式完全互換 |
| `scripts/test_cast_spec.py` | 10 | **PASSED** | CAST_SPEC 境界値、Canonical LoRA 検証 |
| `scripts/test_scene_compiler.py` | 13 | **PASSED** | 1コマコンパイル、LoRA Plan、タグ解析 |
| `scripts/test_region_spec.py` | 14 | **PASSED** | REGION_SPEC 境界クランプ、Preview 生成 |
| `scripts/test_region_state_transitions.py` | 7 | **PASSED** | コマ分割・Undo/Redo・厳格bool検証 |
| `scripts/test_runtime_source_identity.py` | 2 | **PASSED** | Git正本（`custom_nodes_custom`）との完全一致 |
| `scripts/verify_wildcard_patch.py` | 2 | **PASSED** | WildcardOrganizer パッチ生存確認 |

---

## 14. 実画像 A/B 生成評価（Local ON vs OFF）

実機 ComfyUI API（Seed=42 固定、Euler 15 steps）による生成テスト結果：

- **出力保存先**: `ComfyUI/output/Tegaki/RegionalControl/`
- **生成ファイル**:
  1. `Control_Local_ON_00001_.png` (Local Region 有効)
  2. `Control_Local_OFF_00001_.png` (Local Region 無効)

### A/B 比較観察結果
1. **KOMA 2 (廊下の壁面ポスター)**:
   - **Local OFF**: 廊下を歩く少女の後ろ姿の右側壁面は、何もない平坦な白い壁面として生成された。
   - **Local ON**: 指定された局所領域（`area: x=0.55, y=0.10, w=0.40, h=0.45`）に、明確に掲示板・フライヤー・貼り紙（`posters on school wall, bulletin board with flyers`）が出現した。
2. **KOMA 1 (教室の窓際机)**:
   - **Local ON**: 左側の少女（Alice）の周囲に、机とノートのディテールがより明確にレイアウトされ、光の差し込みが強調された。
3. **他領域への非侵食性（局所性の証明）**:
   - Local Region を ON にしても、KOMA 1 の Bob の笑顔や KOMA 3 の夕暮れ屋上風景は破壊されず、指定矩形内のみに効果が集中していることが実証された。

---

## 15. 残存課題と次のステップ（Phase 4 / UI統合への道筋）

1. **GUI エディタでの矩形ドラッグ指定**:
   - 現在は JSON / パラメータ指定となっている Local Region を、将来の Region Editor UI 上で Character と同様にドラッグ＆ドロップ描画可能とする。
2. **LoRA 強度個別チューニング**:
   - Local Region ごとに LoRA を適用する機能はタグ抽出でサポート済みだが、Region 単位での LoRA 重みスライダー UI の提供。
3. **Phase 4 への移行**:
   - 漫画 1 ページ全体の完成度を高める Inpainting / Refiner パイプラインとの接続。

---

## 16. 成果物一覧

### ソースコード
- `custom_nodes_custom/tegaki_manga_nodes/scene_spec.py`: `validate_local_region` 新設、COMPILE_PLAN 深層検証拡張
- `custom_nodes_custom/tegaki_manga_nodes/region_editor.py`: `local_regions` リスト型チェック追加
- `custom_nodes_custom/tegaki_manga_nodes/scene_compiler.py`: 4階層自然結合プレビュー、Local Region LoRA 抽出、Inspector 拡張
- `custom_nodes_custom/tegaki_manga_nodes/mask_builder.py`: Page 座標投影、`local_region_masks`、フェザー処理、色分け Preview
- `custom_nodes_custom/tegaki_manga_nodes/conditioning_builder.py`: 4階層 Conditioning 合成、`local_region_strength`、フェザー対応

### ワークフロー
- `workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json` (新規)

### テストスクリプト
- `scripts/test_local_region_spec.py` (新規)
- `scripts/test_regional_control_expansion.py` (新規)
- `scripts/test_regional_control_expansion_generation.py` (新規)
- `scripts/test_page_compile_plan.py` (更新)
- `scripts/test_conditioning_builder.py` (更新)

### ドキュメント
- `docs/reports/PHASE3B_1_REGIONAL_CONTROL_EXPANSION_REPORT.md` (新規・本報告書)
- `docs/WORKFLOW_INDEX.md` (更新)
- `README.md` (更新)
