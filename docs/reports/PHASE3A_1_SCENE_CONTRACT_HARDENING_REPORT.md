# PHASE3A_1_SCENE_CONTRACT_HARDENING_REPORT.md — Phase 3A.1 Scene Contract Hardening 報告書

**作成日時**: 2026-09-03 15:52 (JST)  
**対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`  
**ホストGPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)  
**Review Target Baseline**: `b628f3d57699da615eb45ce6f11ab018a38d591d`  

---

## 1. CAST / Binding 契約修正
- **問題**: 以前のScene Compilerでは、KOMA側にCharacter Bindingが存在するにもかかわらず `CAST_SPEC` が未指定（または構文エラー）の場合、空のCharacter masterとしてフォールバックし、キャラクター解決不能のまま処理が続行されるリスクがあった。
- **改修内容**:
  - KOMAにCharacter Bindingが存在する場合、`CAST_SPEC` の存在を必須化。
  - `CAST_SPEC` が空・未指定、または構文エラー（`JSONDecodeError`）の場合は、制作データ保護のため **即時 `ValueError` を送出して安全に停止**。
  - Bindingが存在しない場合（通常コマ生成）は、CAST_SPECが空でも構文エラー（warning出力）でも安全にフォールバックして続行（下位互換性を100%維持）。

---

## 2. LoRA Canonical Entry
- `docs/LORA_ENTRY_V1.md` に基づき、Canonical LoRA Entry 仕様を正式確立：
  ```json
  {
    "name": "alice_costume",
    "enabled": true,
    "model_weight": 0.8,
    "clip_weight": 0.5,
    "source": "structured_character",
    "metadata": {}
  }
  ```
- レガシーな `weight` フィールドは `model_weight = weight`, `clip_weight = weight` として自動正規化。
- `weight` と `model_weight`/`clip_weight` が異なる値で同時指定された場合は競合エラー（`ValueError`）を送出。
- `bool` 値（Pythonの `True == 1`）を重みとして受け入れないよう厳格に型排除。

---

## 3. 1値 / 2値 LoRA タグ
- `<lora:name:0.8>` (1値) ──▶ `model_weight=0.8, clip_weight=0.8`
- `<lora:name:0.8:0.5>` (2値) ──▶ `model_weight=0.8, clip_weight=0.5`
- 不正構文（`<lora::0.8>`, `<lora:name:abc>`, `<lora:name:0.8:abc>`）は無言で放置せず、即時 `ValueError` で拒絶。

---

## 4. LoRA Single Source of Truth (SSOT)
- 文字列表現とJSON構造化設定を別々の正本にせず、すべてのLoRAをパース・正規化して同一のCanonical LoRA Entryへ集約。
- `COMPILE_PLAN` の `lora_plan` にて `global_loras`, `koma_loras`, `character_loras` を一元管理。

---

## 5. Prompt階層 LoRA Parser 共通化
- Global Prompt, KOMA Prompt, Character Base Prompt, Character Override Prompt の全4階層において、共通関数 `parse_lora_tags()` を適用。
- 各階層からタグを除去した `clean_prompt` を抽出し、モデルへ送るプロンプトとLoRA計画を明確に分離。
- 各LoRA Entryに `source`（`global_prompt_tag`, `koma_prompt_tag`, `character_prompt_tag`, `character_override_tag`）を付与し、由来の追跡性を向上。

---

## 6. Negative Prompt 階層
- Negative Prompt を巨大文字列へ一本化せず、4階層で構造化保持：
  1. `global_negative_prompt`: ページ全体共通の除外要素
  2. `panel_negative_prompt`: コマ固有の除外要素
  3. `base_negative_prompt`: キャラクター固有の除外要素
  4. `override_negative_prompt`: コマ演技差分固有の除外要素
- `COMPILE_PLAN` に各フィールドを分離保持しつつ、デバッグ・プレビュー用として `compiled_negative_prompt` を出力。

---

## 7. COMPILE_PLAN Validator
- 新設関数 `validate_compile_plan(plan: Any) -> Dict[str, Any]` を実装。
- スキーマバージョン（`version: 1`）、ステータス（active/inactive）、target_panel_id（1..6）、canvas、panel、characters、lora_plan を厳格に検査。
- `TegakiMangaSceneCompiler` 自身が出力直前にこのValidatorを実行し、出力データの整合性を自己保証。

---

## 8. Schema Strictness
- `character_id`: strict string（数値やboolの暗黙変換を禁止、非空文字列必須）。
- 各種Prompt / Negative: strict string（None/missingは空文字、数値やbool、dictは `ValueError`）。
- `characters` フィールド: 存在する場合は必ず `list`（`{}` や `""` は即時 `ValueError`）。
- `metadata`: 存在する場合は必ず `dict`。

---

## 9. panel_count 用語整理と Active Panel
- `panel_count` の定義を「有効コマ数」から **「表示/参照可能なコマ番号の上限（スロット範囲 1..6）」** へ修正。
- 実際に描画・推論対象となるコマを **「Active Panel (`id <= panel_count` かつ `enabled == True`)」** と定義。
- ヘルパー関数 `get_active_panel_ids(region_spec)` を提供。

---

## 10. Workflow 08 (MANGA_SCENE_CONTRACT_TEST.json)
- `workflows/08_MANGA_SCENE_CONTRACT_TEST.json` を新設。
- 区分: `DEVELOPMENT / CONTRACT INSPECTION HARNESS`
- 外部の不安定な拡張ノードを一切含めず、Tegaki独自ノード（Region Editor / Scene Compiler）と標準PreviewImageノードのみで構成。
- 2人会話シーン（Alice & Bob、左右Area分割、Prompt Override、LoRAタグ）をサンプルとして内包し、人間が視覚的にデータ契約の集約結果を検査可能。

---

## 11. Test 結果
すべてのテストが完全合格（**ALL PASSED**）：
1. `scripts/test_cast_spec.py`: **ALL PASSED**
   - default_cast_spec, multi-character, unsupported version, duplicate ID, strict boolean, unknown fields, area & area=None, unknown character ID
   - 新規追加: strict string character_id, strict string prompt, bool LoRA weight reject, legacy weight normalizer, conflicting weights reject, invalid characters list type
2. `scripts/test_scene_compiler.py`: **ALL PASSED**
   - 1 char / 1 panel, 2 chars dialogue, panel appearance differences, area=None, LoRA hierarchy aggregation, unknown character ID, CAST absent compatibility
   - 新規追加: CAST absent + binding reject, Broken CAST + binding reject, 1-value / 2-value LoRA tags, Invalid LoRA tag reject, Negative Prompt hierarchy propagation, COMPILE_PLAN validator integration
3. `scripts/test_region_spec.py`: **ALL 14 SUITES PASSED**
4. `scripts/test_region_state_transitions.py`: **ALL PASSED**
5. `scripts/test_runtime_source_identity.py`: **PASSED**
6. `scripts/verify_wildcard_patch.py`: **PATCH PRESENT**
7. `scripts/test_region_editor_backend_api.py`: **PASSED**
8. `scripts/test_generation.py`: **PASSED** (01 txt2img非破壊実証)

---

## 12. 既存 Workflow 互換
- `01_BASIC_ILLUSTRIOUS_TXT2IMG.json`, `02_ILLUSTRIOUS_I2I.json`, `07_MANGA_REGION_EDITOR_UI_TEST.json` の動作は完全非破壊。
- `CAST_SPEC` を接続しない通常利用でも、100%下位互換で動作。

---

## 13. 既知の問題
- `04_REGIONAL_LORA_EXPERIMENT.json` のKSampler未合流（NOT YET REGIONAL / Phase 5で改修）。
- （※CASTなしBindingの暗黙フォールバック、LoRAタグ2値情報脱落、LoRAへのbool値混入、Negative Prompt未定義、COMPILE_PLAN出力検証欠落はすべて本Phaseで解決済）。

---

## 14. Phase 3B Readiness
- `COMPILE_PLAN` のデータ契約が強固に確定し、誰が見ても同じ意味に解釈できる基盤が完成。
- 次Phase（Phase 3B: Manga Scene Compiler → Conditioning 接続）へ直ちに進出可能。

---

## 15. Gemini 独自判断で変更した項目
- **Markdownファイルの分類・整理（ユーザー指示）**:
  `README.md` をルート直下に残し、報告書・チェックリストを `docs/reports/` へ、仕様・参照文書を `docs/` へ系統的に整理・再編。
- **LoRAタグパーサーの空白・カンマ自動クリーンアップ**:
  タグ除去後のプロンプトから `,,` や不要な前後カンマを自動整形し、モデルへ渡す `clean_prompt` を自然なプロンプト文字列に維持。

---

## 16. PHASE 3B READINESS

```text
PHASE 3B READINESS: GO
```
