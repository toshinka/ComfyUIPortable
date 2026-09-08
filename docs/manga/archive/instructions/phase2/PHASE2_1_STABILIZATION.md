# ComfyUI Portable Phase 2.1 地固め・安定化 改修指示書

## 0. 今回の目的

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
2a3116b520b25a94879ab621d7fe6317142cacce
```

Phase 2では、

- Wildcard Organizer
- Tegaki Manga Region Editor
- REGION_SPEC v1
- 最大6コマの矩形Editor
- Prompt欄
- Workflow 07

まで構築されました。

今回は次のPhaseへ機能拡張するのではなく、これらの基礎を安定させます。

最重要目標は、

```text
GitHubでレビューされるコード
=
ComfyUIが実際に実行するコード
=
テストされるコード
```

を保証することです。

また、

```text
REGION_SPEC
```

を将来のMRP / Regional Prompt / ControlNet / RLL / 外部GUIすべてで利用できる安定したデータ契約として固めます。

今回は、

```text
Regional Conditioning Compiler
RLL
ControlNet統合
MCWW等のユーザーGUI化
完成版MRP UI
```

へ進まないでください。

Workflow 07は引き続き「Region Editor開発用試験Workflow」として扱います。

見た目の完成度より、正しい状態管理と検証可能性を優先してください。

---

# 1. 作業開始前確認

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
ComfyUIPortable/PHASE2_MRP_UI_REPORT.md
ComfyUIPortable/KNOWN_ISSUES.md
ComfyUIPortable/DEPENDENCIES.md
ComfyUIPortable/RESEARCH_REFERENCES.md

ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/region_editor.py
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/tegaki_region_editor.js

ComfyUIPortable/scripts/test_region_spec.py
ComfyUIPortable/scripts/test_workflow_07.py

ComfyUIPortable/workflows/07_MANGA_REGION_EDITOR_UI_TEST.json
```

現在動作している、

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG
02_ILLUSTRIOUS_I2I
Wildcard Organizer
```

を壊さないでください。

---

# 2. 最優先: Git正本とRuntimeコードを同一化する

現在Git管理されている独自ノード正本は、

```text
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes
```

です。

一方、現在のテストは、

```python
from custom_nodes.tegaki_manga_nodes...
```

として、

```text
ComfyUIPortable/ComfyUI/custom_nodes/tegaki_manga_nodes
```

側を実行しています。

`ComfyUI/` はGit管理対象外なので、外部AIがレビューしたコードと実際に動作したコードが同一であることを現在は保証できません。

これを解消してください。

推奨構造は、

```text
ComfyUI/custom_nodes/tegaki_manga_nodes
        ↓
junction / directory symlink
        ↓
custom_nodes_custom/tegaki_manga_nodes
```

です。

Windows環境に適したjunction等を使用してください。

既存runtimeコピーが存在する場合は、内容を比較してから安全に置き換えてください。

無断でソースを消さないでください。

---

# 3. Runtime Source Identity Testを作る

新規に例えば、

```text
scripts/test_runtime_source_identity.py
```

を作成してください。

最低限、

```python
import inspect
from custom_nodes.tegaki_manga_nodes.region_editor import TegakiMangaRegionEditor
```

等から、

実際に読み込まれている

```text
region_editor.py
lora_loader.py
```

の物理パスを表示してください。

期待結果:

```text
runtime custom node
→ custom_nodes_custom/tegaki_manga_nodes
```

へ解決されること。

可能なら、

```text
resolved path
file SHA256
```

も表示してください。

最終報告書へ結果を記録してください。

---

# 4. REGION_SPECをSingle Source of Truthにする

現在、

```text
panel_count
canvas_width
canvas_height
global_prompt
region_spec_data
```

の双方に同じ情報が存在しています。

この二重管理を整理してください。

原則として、

```text
REGION_SPEC
```

を永続状態の正本とします。

概念:

```text
UI Widget
    ↓
REGION_SPEC
    ↓
Backend
```

としてください。

---

# 5. 外側Widgetの位置付け

現在存在する、

```text
panel_count
canvas_width
canvas_height
global_prompt
```

Widgetを直ちに削除する必要はありません。

ただし、

```text
REGION_SPECを編集するためのFacade
```

として扱ってください。

Widget変更時、

```text
Widget
↓
REGION_SPEC更新
↓
region_spec_data同期
```

が必ず発生するようにしてください。

逆にWorkflowロード時は、

```text
region_spec_data
↓
REGION_SPEC復元
↓
各Widgetへ反映
```

としてください。

---

# 6. Backendでの優先順位を明文化する

Python側では、入力値が矛盾した場合のルールを明確にしてください。

推奨:

```text
有効なregion_spec_dataが存在
→ REGION_SPECを正本として使用

region_spec_dataが {} / 空
→ panel_count / canvas / global_prompt から初期REGION_SPEC生成
```

有効なREGION_SPECが存在するのに、

```text
panel_count等で無条件上書き
```

する現在の処理は見直してください。

外部API / 将来GUIもREGION_SPECを直接渡せる構造を優先します。

---

# 7. REGION_SPEC v1を正式に定義する

最低限以下を仕様化してください。

```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "panel_count": 3,
  "global_prompt": "",
  "regions": []
}
```

Region:

```json
{
  "id": 1,
  "name": "KOMA 1",
  "enabled": true,
  "x": 0.0,
  "y": 0.0,
  "w": 0.5,
  "h": 0.5,
  "prompt": ""
}
```

必要なpresentation metadataを追加して構いません。

ただし生成ロジックに不要なUI情報と生成情報をなるべく混同しない設計を優先してください。

---

# 8. REGION_SPEC validator / normalizerを作る

例えば、

```text
validate_region_spec()
normalize_region_spec()
```

等を作成してください。

最低限検査するもの:

```text
version
canvasの存在
width / height
regionsがlist
region ID 1～6
ID重複なし
enabled型
x / y / w / h型
座標範囲
prompt型
panel_count 1～6
```

Active Regionについて、

```text
0 <= x <= 1
0 <= y <= 1
0 < w <= 1
0 < h <= 1
x + w <= 1
y + h <= 1
```

を保証してください。

軽微な範囲逸脱はclampしても構いません。

構造そのものが壊れている場合は、無言で異常なREGION_SPECを使用しないでください。

明確なwarning / errorを出してください。

---

# 9. Schema versionを実際に利用する

`version: 1`

を単に保存するだけでなく、

```text
unsupported version
```

を検知してください。

将来、

```text
REGION_SPEC v2
```

へ移行できる構造にしてください。

---

# 10. Color仕様を整理する

現在REGION_SPEC内に、

```text
color
```

がありますが、Python/JS描画では実際には、

```text
KOMA ID → KOMA_COLORS
```

を使用しています。

どちらを正本とするか決めてください。

今回の推奨は、

```text
KOMA ID
↓
固定palette
```

です。

つまり色はKOMA identityのpresentation情報とし、生成データとして扱わない方法です。

既存workflowとの互換性のため `color` を残す場合は、optional compatibility fieldとして扱って構いません。

少なくとも、

```text
保存されたcolor値
実際の表示色
```

が矛盾する状態はなくしてください。

---

# 11. Panel Count同期を修正する

現在Panel Count Widgetの変更をFrontend REGION_SPECへ反映する処理が不足しています。

以下を保証してください。

```text
Panel Count変更
↓
REGION_SPEC.panel_count変更
↓
Editor再描画
↓
region_spec_data保存
```

逆方向も、

```text
Workflow reload
↓
REGION_SPEC.panel_count
↓
Panel Count widget
```

へ反映してください。

---

# 12. Panel Countを減らしてもデータを破棄しない

例:

```text
6 → 3 → 6
```

と変更した場合、

KOMA4～6の、

```text
位置
Prompt
ON/OFF
```

を不必要に破棄しないでください。

非表示状態として保持してください。

---

# 13. Canvas Width / Height同期

現在JSのdefault specが、

```text
832 x 1216
```

へ固定されています。

Canvas Widgetを変更した場合、

```text
REGION_SPEC.canvas.width
REGION_SPEC.canvas.height
```

へ同期してください。

Reset時にもユーザー設定済みCanvas Sizeを勝手に832x1216へ戻さないでください。

---

# 14. Global Prompt同期

同様に、

```text
global_prompt widget
REGION_SPEC.global_prompt
```

を同期してください。

ResetによってGlobal Promptを勝手に空にしないでください。

Resetの意味は基本的に、

```text
Region layout reset
```

としてください。

Global Prompt等までResetする必要があるなら、別操作にしてください。

---

# 15. Resize UIの整合性

現在Canvasには4隅のresize handleが描画されていますが、実際のhit testは右下のみです。

これは修正してください。

以下どちらでも構いません。

推奨:

```text
NW
NE
SW
SE
```

4隅resizeを実装。

もしPhase 2.1で4隅対応を避ける場合は、実際に操作可能な右下handleだけ表示してください。

見た目と挙動を一致させることを必須とします。

---

# 16. Deleteを実装する

現在Delete操作がありません。

最低限、

```text
Delete Selected
```

を追加してください。

可能なら、

```text
Deleteキー
Backspace
```

も対応してください。

ただしPrompt textarea入力中は文字削除を優先し、Region Deleteを発火させないこと。

---

# 17. Delete時の状態

Regionオブジェクトそのものを配列から削除するより、

```text
enabled = false
```

として保持する方式を推奨します。

これにより、

```text
後から再使用
Undo
panel count増加
```

が容易になります。

必要ならgeometryは保持してください。

---

# 18. 新規矩形作成時の空きRegion処理

現在の新規作成処理を確認してください。

期待する動作:

```text
disabled KOMAあり
→ 再利用

disabled KOMAなし
かつ panel_count < 6
→ 次のKOMAを有効化
→ panel_countを増加

6コマ使用中
→ 作成不可を明示
```

ユーザーがCanvas上でドラッグしても何も起きず理由も分からない状態は避けてください。

---

# 19. Undo / Redoを修正する

現在Prompt textareaは、

```text
oninputで値変更
↓
onchangeでpushHistory
```

となっているため、変更後の状態を履歴へ積んでしまう可能性があります。

Prompt編集についても正しくUndoできるようにしてください。

推奨:

```text
focus時に編集前snapshot
↓
input
↓
blur/change時に1回commit
```

等。

キー入力1文字ごとに巨大な履歴を作る必要はありません。

---

# 20. Ctrl+Z / Ctrl+Y

報告書には記載されていますが、現在実装コードでは確認できません。

以下を実装してください。

```text
Ctrl+Z → Region Editor Undo
Ctrl+Y → Region Editor Redo
```

Windowsでは必要なら、

```text
Ctrl+Shift+Z
```

もRedoとして対応して構いません。

ただし、

```text
input
textarea
contenteditable
```

へフォーカス中は、ブラウザ標準のテキストUndo/Redoを優先してください。

---

# 21. Swap仕様を明確にする

現在Swapは、

```text
geometry
prompt
```

だけ交換しています。

将来的にRegionには、

```text
ControlNet
LoRA
Mask metadata
その他設定
```

が増えます。

そのためSwapの意味を定義してください。

推奨:

```text
KOMA identity:
id
name
UI color
```

は固定。

それ以外のRegion payloadをSwapする。

例:

```text
x/y/w/h
prompt
enabled
将来のcontrol
将来のlora
```

等。

あるいは、

```text
Swap Position
Swap Content
```

を分離しても構いません。

今回は簡単で壊れにくい設計を優先してください。

仕様を報告書へ明記してください。

---

# 22. Active Region判定を共通化する

現在各所で、

```text
enabled
かつ
id <= panel_count
```

という判定があります。

これを可能なら共通関数化し、

```text
is_active_region()
```

相当の同一ルールを、

```text
preview
mask
frontend
future compiler
```

で使えるよう整理してください。

---

# 23. 空Maskの意味を修正する

現在有効Regionが0件の場合、

```python
torch.ones(...)
```

つまり全画面白Maskを返しています。

これは将来的なRegional Conditioning接続時に危険です。

有効Regionが0件の場合は原則、

```python
torch.zeros(...)
```

等、「何も選択されていない」意味になるよう変更してください。

---

# 24. Mask BatchとKOMA IDの対応を明示する

現在、

```text
MASK batch
```

のみでは、

```text
batch[0] = KOMA何番？
```

が外部から分かりにくいです。

必要なら追加出力として、

```text
active_region_ids_json
```

等を追加してください。

例:

```json
[1, 3, 5]
```

既存出力slotをずらしてWorkflow 07を壊さないよう、追加する場合は末尾へ追加してください。

ただし将来CompilerがREGION_SPECから直接Maskを生成する方が適切なら、その方針を報告書へ記録するだけでも構いません。

---

# 25. Frontend Event Listenerをcleanupする

現在Region Editorノード生成時に、

```javascript
window.addEventListener("mousemove", ...)
window.addEventListener("mouseup", ...)
```

を登録しています。

ノード削除時にremoveしていないため、長時間利用・Workflow再読み込みでlistenerが蓄積する可能性があります。

修正してください。

推奨:

```text
onRemoved
↓
removeEventListener
```

または、

```text
AbortController
```

等。

ComfyUI本来のonRemoved処理が存在する場合は破壊しないでください。

---

# 26. Drag stateを毎回明示的に初期化する

mousedown開始時に、

```text
activeRegion
dragHandle
dragMode
```

等を明示的に初期化してください。

過去操作の参照を残さないようにしてください。

---

# 27. Workflow復元のsetTimeout依存を減らす

現在、

```javascript
setTimeout(..., 50)
```

によってWidget復元後の読み込みを期待しています。

ComfyUI frontend更新で壊れやすいため、現在使用しているComfyUI / frontend versionで利用可能な正式なlifecycle callbackを調査してください。

例えば、

```text
onConfigure
graph configure後hook
widget callback
```

等。

現行APIで適切な方法が存在するならそちらへ移行してください。

どうしてもsetTimeoutが必要なら、

```text
なぜ必要か
何に依存しているか
```

をコメントと報告書へ残してください。

---

# 28. Workflow 07の位置付けを明確にする

`07_MANGA_REGION_EDITOR_UI_TEST.json`

は完成漫画GUIではありません。

以下の位置付けへ変更・明記してください。

```text
DEVELOPMENT / UI TEST HARNESS
```

目的:

```text
REGION_SPEC
Region Editor
Frontend state
Mask
Preview
```

の検証。

UIの最終完成度を追求する必要はありません。

---

# 29. test_workflow_07.pyを修正する

現在このスクリプトはWorkflow JSONを読み込んでいますが、その内容を実際には使用せず、別の手書きAPI Promptを実行しています。

そのため、

```text
Workflow 07そのものをテストした
```

とは言えません。

名前または実装を修正してください。

選択肢:

```text
A.
実際に07をAPI形式へ変換して実行する

B.
現在のテストを
test_region_editor_backend_api.py
等へ改名し、
「Backend Node execution test」と正しく位置付ける
```

無理にWorkflow JSON変換ロジックを追加する必要はありません。

テスト名称と実際に検証している範囲を一致させることを優先してください。

---

# 30. Region Editor Backend Testを強化する

`test_region_spec.py` に以下を追加してください。

```text
panel_count = 1
panel_count = 6
0 active regions
disabled region
overlapping regions
invalid JSON
missing canvas
missing regions
duplicate region ID
negative coordinate
x+w > 1
unsupported schema version
state serialize/reload
```

validatorの期待動作も検証してください。

---

# 31. Frontend手動試験表を作る

Browser操作はPython unit testだけでは検証できません。

例えば、

```text
PHASE2_1_UI_TEST_CHECKLIST.md
```

を作ってください。

最低限:

```text
[ ] Panel Count 1→6
[ ] 6→3→6で状態保持
[ ] Region create
[ ] Region move
[ ] multi select
[ ] multi move
[ ] resize
[ ] overlap
[ ] Split H
[ ] Split V
[ ] Swap
[ ] Delete
[ ] Undo
[ ] Redo
[ ] Ctrl+Z
[ ] Ctrl+Y
[ ] Prompt編集Undo
[ ] Workflow Save
[ ] Browser reload
[ ] Workflow Load
[ ] REGION_SPEC一致
[ ] JavaScript Console Errorなし
```

実際に確認したもののみPASSにしてください。

---

# 32. RuntimeでUIテストを行う

Antigravityから可能な範囲で実際のブラウザを操作してください。

自動Browser操作が難しい項目は無理にPASS扱いしないでください。

```text
未自動化
手動確認必要
```

と明記してください。

「コード上存在する」だけで「動作確認済み」にしないでください。

---

# 33. Wildcard Organizer patchをGit管理可能にする

Phase 2では、

```text
ComfyUI-WildcardOrganizer/nodes.py
```

へWindows Junction用修正を加えています。

しかし `ComfyUI/` はGit除外されているため、現在その修正内容を外部AIがレビューできません。

これを改善してください。

推奨:

```text
ComfyUIPortable/patches/
```

を作成し、

```text
wildcard_organizer_windows_junction.patch
```

等を保存してください。

または、

```text
scripts/apply_wildcard_organizer_patch.py
```

等でも構いません。

---

# 34. 外部Custom Node更新でpatchが消えることを考慮する

ComfyUI Manager等でWildcard Organizerを更新すると、ローカル修正が消える可能性があります。

最低限、

```text
upstream repository
upstream commit
patch適用済みか
```

を確認できる仕組みを作ってください。

自動patch適用までは必須ではありません。

起動時または検証スクリプトで、

```text
PATCH PRESENT
PATCH MISSING
```

が分かれば十分です。

---

# 35. Custom Node version/commitを記録する

現在DEPENDENCIESではCustom Node名は記録されていますが、レビュー再現性のためcommit SHAも欲しいです。

新規に、

```text
CUSTOM_NODE_MANIFEST.md
```

またはJSONを作って構いません。

例:

```text
ComfyUI-Impact-Pack
repo:
commit:
dirty:

ComfyUI-Inspire-Pack
repo:
commit:
dirty:

ComfyUI-WildcardOrganizer
repo:
commit:
local patch:
```

最低限今回依存している主要Nodeを記録してください。

---

# 36. DEPENDENCIES.mdを更新する

今回導入した、

```text
ComfyUI-WildcardOrganizer
```

がDEPENDENCIESへ不足しているので追加してください。

可能なら、

```text
version / commit
```

も記録してください。

---

# 37. ライセンス記録を修正する

`RESEARCH_REFERENCES.md` では、

```text
comfyui_manga_panel = MIT
```

となっていますが、実RepositoryはApache License 2.0です。

修正してください。

他の参照Repositoryについても、今回触る範囲で明らかな誤記がないか再確認してください。

---

# 38. 外部コード流用の有無を明記する

Manga Panel / Nukun等について、

```text
思想・挙動のみ参考
コードコピーなし
```

なのか、

```text
一部ロジックを改変利用
```

なのかを明記してください。

もし直接コードを利用している部分がある場合は、その出典とライセンス要件を記録してください。

---

# 39. READMEの表現を修正する

現在READMEでは、

```text
04_REGIONAL_LORA_EXPERIMENT
```

を「領域ごとに別LoRAを適用するRLL先行実験」と読める表現があります。

現在はNOT YET REGIONALなので、誤解しない表現に修正してください。

例:

```text
Regional LoRA接続構造の試験用・未完成
```

等。

KNOWN_ISSUESとの記述を一致させてください。

---

# 40. Phase 2.1では新しい大機能を追加しない

以下は今回行わないでください。

```text
Regional Conditioning Compiler
ControlNet Region統合
I2I Region統合
Regional LoRA
RLL
ANIMA
MCWW本導入
RookieUI本導入
完成版漫画GUI
Model Manager全面導入
```

明確なバグ修正・テスト補助のための小機能は追加して構いません。

---

# 41. MRPの完成UIを今回追求しない

現在のRegion Editorは、

```text
MRP実装に向けたデータ構造・矩形編集・Prompt管理の研究用UI
```

として扱ってください。

完成版MRPの操作感を再現しようとして、大規模なFrontend再設計は行わないでください。

今後、

```text
REGION_SPEC
↓
Regional Conditioning
↓
Control
↓
RLL
```

が実際に動作してからユーザーUIを再設計します。

---

# 42. 将来のPrompt解析を邪魔しない

MRP側では今後、

```text
Global Prompt
KOMA Prompt
Wildcard
LoRA構文
構図情報
Control情報
```

等を解析・コンパイルする可能性があります。

今回のRegion EditorはPromptを単純なSTRINGとして保持し、

Prompt内容を不用意に加工・破壊しないでください。

---

# 43. REGION_SPECに将来情報を追加できる設計を維持する

将来的にはRegionへ、

```text
control
lora
mask
strength
metadata
```

等が追加される可能性があります。

validatorは未知フィールドを即座に破棄する設計より、

```text
既知フィールドを検査
未知フィールドは可能なら保持
```

する前方互換性を検討してください。

ただし危険な型は使用しないでください。

---

# 44. 今回の新規報告書

新規に、

```text
PHASE2_1_STABILIZATION_REPORT.md
```

を作成してください。

最低限:

```text
1. 修正概要
2. Git正本 / Runtime同一化方式
3. Runtime source identity結果
4. REGION_SPEC正式仕様
5. validator仕様
6. Widget / REGION_SPEC同期仕様
7. Panel Count仕様
8. Delete仕様
9. Resize仕様
10. Swap仕様
11. Undo/Redo仕様
12. Mask empty仕様
13. Event listener cleanup
14. Workflow restore方式
15. Backend test結果
16. Frontend test結果
17. Wildcard patch管理方式
18. Custom Node manifest
19. Documentation修正
20. 既知の問題
21. Phase 3へ進める状態か
22. Gemini独自判断で変更した事項と理由
```

を記載してください。

---

# 45. KNOWN_ISSUESを更新する

今回解決した問題は、

```text
RESOLVED IN PHASE 2.1
```

として削除または履歴化してください。

未解決項目だけが現在のKNOWN_ISSUESとして分かる状態にしてください。

「直したがテストしていない」はResolved扱いしないでください。

---

# 46. GITHUB.TXT更新

Phase 2.1実装終了後、

まず実装一式をcommitしてください。

例:

```text
Commit A
Phase 2.1 stabilization implementation
```

そのSHAを取得して、

```text
Review Target Commit SHA: A
```

をGITHUB.TXTへ記載。

その後GITHUB.TXTだけ別commitしてください。

以前確立した二段commit方式を維持してください。

---

# 47. GITHUB.TXTに追加するリンク

最低限:

```text
PHASE2_1_STABILIZATION_REPORT.md
PHASE2_1_UI_TEST_CHECKLIST.md

region_editor.py
tegaki_region_editor.js

test_region_spec.py
runtime source identity test

Wildcard Organizer patch
patch verification script

CUSTOM_NODE_MANIFEST
KNOWN_ISSUES
DEPENDENCIES
```

へPinned URL / Raw URLを追加してください。

---

# 48. 最終Acceptance Criteria

以下を満たした場合のみPhase 2.1完了としてください。

```text
[ ] Git管理コード = Runtimeコード
[ ] Runtime source identity確認
[ ] REGION_SPECが正本
[ ] Widget同期に矛盾なし
[ ] Panel Count同期
[ ] Canvas size同期
[ ] Global Prompt同期
[ ] validator実装
[ ] invalid spec test
[ ] Delete動作
[ ] resize表示と実動作一致
[ ] Undo/Redo正常
[ ] Prompt編集Undo正常
[ ] Keyboard Undo/Redo正常
[ ] Swap仕様確定
[ ] 空Region時に全画面Maskを返さない
[ ] Event listener cleanup
[ ] Workflow save/reloadでstate維持
[ ] Backend test PASS
[ ] 実Frontendチェック実施
[ ] Wildcard patchがGitからレビュー可能
[ ] Custom Node commit記録
[ ] LICENSE記録修正
[ ] README / KNOWN_ISSUES整合
[ ] 既存txt2imgが壊れていない
[ ] 既存I2Iが壊れていない
[ ] Wildcard検索が壊れていない
```

---

# 49. Phase 3への移行判定

報告書末尾に、

```text
PHASE 3 READINESS:
GO / HOLD
```

を記載してください。

GO条件:

```text
REGION_SPECの契約が安定
Frontend/Backend同期問題なし
RuntimeとGit正本が一致
主要Editor操作に重大バグなし
```

です。

GOであっても今回はPhase 3を実装しないでください。

---

# 50. 最終回答

作業完了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:
PHASE2_1_STABILIZATION_REPORT Raw:
UI Test Checklist Raw:
region_editor.py Pinned Raw:
tegaki_region_editor.js Pinned Raw:
Wildcard Patch Raw:
Custom Node Manifest Raw:

PHASE 3 READINESS:
```

外部AIで再レビューします。

---

## 今回の設計原則

今回の工程は機能を増やすためではありません。

```text
Region Editor
↓
REGION_SPEC
↓
将来の生成処理
```

という境界を信用できるものにするための工程です。

現在の07 WorkflowやRegion Editor UIは開発用であり、完成された漫画制作GUIである必要はありません。

まず、

```text
状態が壊れない
保存できる
復元できる
外部から読める
テストできる
GitHub上のコードと実行コードが同じ
```

ことを優先してください。

これが成立した後に、

```text
Phase 3: Regional Conditioning Compiler
```

へ進みます。
