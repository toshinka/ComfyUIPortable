# ComfyUI Portable Phase 2.1.1 小修正・回帰防止 指示書

## 0. 今回の目的

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
fda210762d25688119dd1338e9887b8f87f64b3e
```

Phase 2.1では、Git正本とRuntimeコードの同一化、REGION_SPEC v1のSingle Source of Truth化、Frontend/Backend同期、Validator、Delete、4隅Resize、Undo/Redo、Wildcard patch管理など、基盤の安定化が完了しました。

今回はPhase 3へ進む前の小修正として、状態遷移と回帰防止だけを扱います。

修正対象は以下です。

```text
1. Split時のPanel Count / Undo不整合
2. 新規Region作成時のUndo不整合
3. Layout Resetの意味と実装の不一致
4. Swapの将来拡張フィールド対応
5. REGION_SPEC schema errorの扱い
6. enabled型の安全な検証
7. 上記に対応するRegression Test
```

新しい大機能は追加しないでください。

---

# 1. 作業前確認

最初に以下を確認してください。

```text
git rev-parse HEAD
git status
git branch --show-current
git remote -v
```

以下を必ず読んでください。

```text
ComfyUIPortable/GITHUB.TXT
ComfyUIPortable/PHASE2_1_STABILIZATION_REPORT.md
ComfyUIPortable/PHASE2_1_UI_TEST_CHECKLIST.md
ComfyUIPortable/KNOWN_ISSUES.md

ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/region_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/tegaki_region_editor.js

ComfyUIPortable/scripts/test_region_spec.py
ComfyUIPortable/scripts/test_runtime_source_identity.py
```

現在正常に動いている、

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG
02_ILLUSTRIOUS_I2I
07_MANGA_REGION_EDITOR_UI_TEST
Wildcard Organizer
```

を壊さないでください。

---

# 2. Phase 2.1.1では設計思想を変更しない

以下は維持してください。

```text
REGION_SPEC = Single Source of Truth
外側Widget = REGION_SPECのFacade
Runtime custom node = Git正本へのJunction
Prompt文字列は不用意に解析・改変しない
未知の将来フィールドは可能な限り保持
```

Phase 2.1で固めた構造を再設計しないでください。

---

# 3. Split処理のPanel Count不整合を修正する

現在の `splitSelectedRegion()` では、未使用Region探索が全6Regionから行われるため、

```text
panel_count = 3
KOMA4 = disabled
```

の状態でSplitした場合、

```text
KOMA4.enabled = true
panel_count = 3
```

となり、KOMA4がActive Regionにならない可能性があります。

これを修正してください。

推奨順序:

```text
A. 現在の panel_count 範囲内に disabled KOMA がある
   → それを再利用

B. panel_count 範囲内に空きがない
   かつ panel_count < 6
   → panel_count を1増加
   → 新しく範囲内になったKOMAを利用

C. 6コマすべて使用済み
   → Split不可を通知
```

必ず、

```text
enabled == true
かつ
id <= panel_count
```

となる状態で処理を終了してください。

---

# 4. Split時のUndo履歴を修正する

Split処理では、

```text
panel_count変更
Region有効化
geometry変更
```

より前に元状態のsnapshotを保存してください。

概念:

```text
pushHistory()
↓
panel_count変更
↓
unused Region有効化
↓
geometry分割
```

Split後にUndoした場合、

```text
panel_count
enabled状態
元Regionのgeometry
新Regionのgeometry
```

がすべてSplit直前へ戻ることを保証してください。

---

# 5. Split Regression Test

初期状態:

```text
panel_count = 3
KOMA1〜3 enabled
KOMA4〜6 disabled
```

KOMA1をSplit。

期待:

```text
panel_count = 4
KOMA4 enabled = true
KOMA4 is_active_region = true
```

Undo。

期待:

```text
panel_count = 3
KOMA4 enabled = false
KOMA1 geometry = Split前
```

可能ならRedoも確認してください。

---

# 6. 新規Region作成時のUndoを修正する

現在のCanvas空白ドラッグによる新規Region作成では、

```text
panel_count増加
targetKoma.enabled = true
x/y/w/h初期化
```

後に `pushHistory()` が実行される可能性があります。

この場合Undoしても作成前まで戻れません。

新規Region作成が成立すると判断した時点で、状態変更より前にsnapshotを保存してください。

概念:

```text
mousedown
↓
新規Region作成が成立すると判断
↓
pushHistory()
↓
panel_count必要なら増加
↓
target KOMA有効化
↓
drag開始
```

作成できない場合は履歴を追加しないでください。

---

# 7. Create → Undo Regression Test

初期:

```text
panel_count = 3
KOMA4 disabled
```

空白ドラッグでKOMA4を新規作成。

期待:

```text
panel_count = 4
KOMA4 enabled
```

Undo。

期待:

```text
panel_count = 3
KOMA4 disabled
```

KOMA4の作成途中geometryが残らないこと。

---

# 8. Layout Resetの仕様を修正する

現在のボタン名は、

```text
Layout Reset
```

です。

したがってこの操作は、

```text
x
y
w
h
```

だけを初期レイアウトへ戻す操作としてください。

以下は保持してください。

```text
enabled
prompt
panel_count
global_prompt
canvas.width
canvas.height
未知の将来フィールド
```

現在の、

```javascript
r.enabled = (i < spec.panel_count)
```

は削除または見直してください。

---

# 9. Layout Reset Regression Test

例:

```text
KOMA2.enabled = false
KOMA2.prompt = "test character"
KOMA2 geometry = custom
```

Layout Reset実行。

期待:

```text
KOMA2.enabled = false
KOMA2.prompt = "test character"
KOMA2 geometry = default geometry
```

Global Prompt、Canvas Sizeも変化しないこと。

Undoでcustom geometryへ戻ること。

---

# 10. Swapをgeneric payload対応にする

現在Swapでは、

```text
x
y
w
h
prompt
enabled
```

のみを交換しています。

将来的にRegionへ、

```text
control
lora
strength
mask
metadata
character bindings
```

等が追加される可能性があります。

固定フィールド列挙式のSwapを続けると、将来Promptだけ移動してControl情報が元のKOMAに残る事故が起きます。

以下をKOMA identityとして固定してください。

```text
id
name
color
```

それ以外のRegionフィールドは原則payloadとします。

未知フィールドを失わないことを最優先してください。

---

# 11. Generic Swap Regression Test

KOMA1:

```json
{
  "id": 1,
  "prompt": "Alice",
  "control_strength": 0.8,
  "lora_tag": "<lora:alice:0.7>"
}
```

KOMA2:

```json
{
  "id": 2,
  "prompt": "Bob",
  "control_strength": 0.3,
  "lora_tag": "<lora:bob:0.6>"
}
```

Swap後:

```text
KOMA1.id = 1
KOMA1.name/color = KOMA1のまま

KOMA1.prompt = Bob
KOMA1.control_strength = 0.3
KOMA1.lora_tag = Bob側
```

KOMA2も逆になること。

---

# 12. REGION_SPECのSyntax ErrorとSchema Errorを分離する

現在 `execute_editor()` は、

```text
JSON parse error
Validator error
unsupported version
その他schema error
```

を同一のexception処理でdefault specへfallbackしています。

これを見直してください。

JSONとして読めない、

```text
{broken json...
```

のようなSyntax Errorは、

```text
明確なwarning
+
default specへfallback
```

でも構いません。

一方、

```json
{
  "version": 999,
  "canvas": {...},
  "regions": [...]
}
```

のようにJSONとしては正しいがREGION_SPECとして不正な場合は、無言でdefaultへ置換しないでください。

原則、

```text
ComfyUI Node execution error
```

として明示的に失敗させてください。

制作データを初期状態へ勝手に置換しないことを優先します。

推奨イメージ:

```python
try:
    parsed = json.loads(...)
except json.JSONDecodeError:
    warning
    fallback default

spec = normalize_region_spec(parsed)  # ValueErrorは上へ伝播
```

---

# 13. Schema Error Regression Test

最低限、

```text
version = 999
```

を `execute_editor()` へ渡してください。

期待:

```text
ValueError / Node execution error
```

default 3コマへ静かに置換されてはいけません。

---

# 14. enabled型を安全に検証する

現在、

```python
bool(r.get("enabled", True))
```

のような変換では、

```python
bool("false") == True
```

になります。

将来外部GUIからJSONが入る場合に危険です。

推奨:

```text
true / false のJSON booleanのみ許可
```

文字列の、

```text
"true"
"false"
"1"
"0"
```

などは原則rejectしてください。

Pythonの `bool(value)` に任せないでください。

---

# 15. enabled Regression Test

最低限、

```json
"enabled": "false"
```

を入力。

期待:

```text
ValueError
```

または明示仕様に基づく安全なFalse変換。

推奨はValueErrorです。

`is_active_region()` もValidator通過済みのstrict booleanを前提にしてください。

---

# 16. Frontendで未知フィールドを破壊しない

JS側でSwap / Reset / Delete / Split / Createを行う際、未知フィールドを不必要に削除しないでください。

Phase 3以降、

```text
character bindings
control info
regional lora data
```

が追加される可能性があります。

---

# 17. 今後の漫画制作方針を設計メモとして記録する

今回実装はしませんが、以下を今後の設計方針としてドキュメントへ残してください。

本ツールは「ComfyUI上だけで漫画を完成させる」ことを主目的にしません。

ComfyUIには主に、

```text
構図
キャラクター位置
演技
カメラ
背景・建物など高コスト要素
精度の高い下絵生成
```

を担当させます。

一方、

```text
集中線
トーン
効果
最終描画
修正
```

は別ツールや手描きと自由に併用する前提です。

既存の `comfyui-comic-creator` 等から利用可能な技術は今後参考にして構いませんが、「ComfyUIだけで完成漫画を作る」設計へ固定しないでください。

---

# 18. ブレスト性を失わない

制御を強くしすぎないでください。

将来の設計では、

```text
構図をある程度誘導
キャラクター位置をある程度拘束
LoRAをある程度地域的に強める
```

一方で、

```text
seed
pose
表情
細部
画面内の偶然性
```

には探索余地を残します。

「完全な厳密制御」より、

```text
漫画制作で使える方向へ強く誘導する
```

ことを優先します。

---

# 19. LoRAの将来方針メモ

LoRAは将来的に複数階層で利用する予定です。

基本:

```text
GLOBAL LoRA
→ ページ/生成全体へ適用
```

追加:

```text
KOMA LoRA
→ コマへ寄せて適用

CHARACTER LoRA
→ キャラクター領域へ寄せて適用
```

Regional LoRAについては、Mask外への影響が完全に0である必要はありません。

```text
指定領域へ相対的に強く効く
```

程度でも漫画制作上の価値があれば採用します。

今回実装しないでください。

---

# 20. Character / Cast構想メモ

Phase 3以降、複数人物問題を巨大Promptだけで解決しないため、

```text
PAGE
 └ KOMA
     └ CHARACTER
```

の階層構造を検討します。

候補:

```text
REGION_SPEC
CAST_SPEC
Panel ↔ Character Binding
Panel-local Character Region
```

Characterは将来的に、

```text
Prompt
LoRA
Reference
出演コマ
コマ内位置
```

等を保持できる構造を想定します。

今回schemaへ追加しないでください。

ただし未知フィールド保持など、将来この拡張を妨げないこと。

---

# 21. Panel Sequential Generation構想メモ

将来的にはページ全体を一度に生成するだけではなく、

```text
KOMA1
↓
KOMA2
↓
KOMA3
↓
...
↓
Page Composite
```

というPanel Sequential Generationを検討します。

目的:

```text
Prompt肥大化回避
複数人物干渉低減
コマ単位再生成
コマ単位I2I
コマ単位Control
```

今回実装しないでください。

---

# 22. Regression Testを追加する

既存 `scripts/test_region_spec.py` を拡張するか、

```text
scripts/test_region_state_transitions.py
```

を新設してください。

最低限以下を自動化してください。

```text
1. Split 3→4 panel
2. Split Undo 4→3
3. Create 3→4 panel
4. Create Undo 4→3
5. Delete → Layout Resetでenabled保持
6. Swap unknown metadata
7. execute_editor unsupported version error
8. enabled="false" 型検査
```

可能ならRedoも検証してください。

---

# 23. Frontend手動テスト

以下も実機確認してください。

```text
Split → Undo → Redo
Create → Undo → Redo
Delete → Layout Reset
Generic Swap
```

JavaScript Console Errorがないこと。

既存UIチェックリストへ追記して構いません。

---

# 24. 既存テストを再実行する

最低限:

```text
test_runtime_source_identity.py
test_region_spec.py
test_region_editor_backend_api.py
verify_wildcard_patch.py
test_generation.py
```

を再実行してください。

可能ならI2Iも再確認してください。

---

# 25. 報告書

新規に、

```text
PHASE2_1_1_REGRESSION_FIX_REPORT.md
```

を作成してください。

最低限:

```text
1. Split修正
2. Split Undo修正
3. Create Undo修正
4. Layout Reset修正
5. Generic Swap仕様
6. Schema Error分類
7. enabled型仕様
8. 新規Regression Test
9. Frontend手動確認
10. 既存機能回帰テスト
11. 既知の問題
12. Phase 3 Readiness
13. 将来設計メモ
14. Gemini独自判断で変更した項目
```

を記録してください。

---

# 26. KNOWN_ISSUES更新

今回見つかった問題について、修正・テスト済みなら、

```text
RESOLVED IN PHASE 2.1.1
```

として履歴化してください。

未確認の項目をResolved扱いしないでください。

---

# 27. GITHUB.TXTの二段commit方式を維持する

まず実装・テスト・報告書をcommitしてください。

```text
Commit A
Phase 2.1.1 regression fixes
```

そのSHAを取得。

その後、

```text
Review Target Commit SHA: A
```

を `GITHUB.TXT` に記載。

GITHUB.TXTのみ別commitしてください。

---

# 28. GITHUB.TXTに追加するもの

最低限:

```text
PHASE2_1_1_REGRESSION_FIX_REPORT.md
更新した region_editor.py
更新した tegaki_region_editor.js
新規/更新 Regression Test
更新した UI Test Checklist
KNOWN_ISSUES.md
```

のPinned URL / Raw URLを追加してください。

---

# 29. Acceptance Criteria

以下を満たした場合のみPhase 2.1.1完了としてください。

```text
[ ] Splitでpanel_countが正しく増える
[ ] Split後のRegionがActiveになる
[ ] Split Undoで完全に元状態へ戻る
[ ] Create Undoでpanel_count/enabled/geometryが元に戻る
[ ] Layout Resetでenabledを変更しない
[ ] Layout ResetでPromptを変更しない
[ ] Swapで未知フィールドも移動する
[ ] id/name/colorはSwapで固定
[ ] unsupported schemaをdefaultへ黙って置換しない
[ ] enabled文字列をbool()で誤変換しない
[ ] 新規Regression Test PASS
[ ] 既存Backend Test PASS
[ ] Runtime Source Identity PASS
[ ] Wildcard Patch PASS
[ ] 基本txt2img非破壊
[ ] JavaScript Console Errorなし
```

---

# 30. Phase 3判定

報告書末尾に、

```text
PHASE 3 READINESS:
GO / HOLD
```

を記載してください。

今回の修正とRegression TestがすべてPASSなら、原則GOで構いません。

ただしPhase 3本体は今回実装しないでください。

---

# 31. 最終回答

作業完了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:
PHASE2_1_1_REGRESSION_FIX_REPORT Raw:
region_editor.py Pinned Raw:
tegaki_region_editor.js Pinned Raw:
Regression Test Raw:
Updated UI Test Checklist Raw:

PHASE 3 READINESS:
```

外部AIで再レビューします。

---

## 最終方針

このプロジェクトの目的は、ComfyUI内だけで漫画制作を完結させることではありません。

ComfyUIには、

```text
高コストな構図設計
人物配置
演技
カメラ
背景・建物
複数キャラクター関係
精度の高い下絵生成
```

を担当させます。

一方、

```text
集中線
トーン
効果
最終描画
修正
```

は別ツールや手描きと自由に組み合わせます。

また、制御を強くしすぎてブレインストーミング性を失わないことを重視します。

将来のRegional LoRAも、

```text
指定場所以外へ完全に漏れない
```

ことを必須条件とはせず、

```text
指定領域へ相対的に強く効く
```

程度でも実制作上有効なら採用します。

Phase 2.1.1ではこれらを実装せず、Phase 3以降の設計方針として保持してください。
