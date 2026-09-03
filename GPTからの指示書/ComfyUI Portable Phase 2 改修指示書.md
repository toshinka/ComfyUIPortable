# ComfyUI Portable Phase 2 改修指示書
## Wildcard UX強化 + Manga Region Editor UI

### 0. 今回の目的

既に構築済みの

`D:\GitHub\tegaki\ComfyUIPortable`

を、単なるComfyUI Workflow集から、MRP（Manga Region Prompter）的な漫画制作UIへ段階的に発展させます。

今回の主目的は以下の2点です。

1. EasyReforgeで便利だったWildcardの検索・中身確認をComfyUIでも可能にする。
2. 最大6コマを扱える視覚的なRegion Editorを新規作成する。

今回はRegion Editorを生成処理へ完全接続するところまでは急がないでください。

まず操作UIと状態管理を完成させ、既存の安定生成環境を壊さない状態でレビュー可能にします。

---

# 1. 最初に現在状態を確認する

作業開始時に必ず実行してください。

```text
git rev-parse HEAD
git status
git branch --show-current
git remote -v
```

以下を読み込んでください。

```text
ComfyUIPortable/GITHUB.TXT
ComfyUIPortable/README.md
ComfyUIPortable/BUILD_REPORT.md
ComfyUIPortable/WORKFLOW_INDEX.md
ComfyUIPortable/KNOWN_ISSUES.md
ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/lora_loader.py
ComfyUIPortable/workflows/03_MANGA_REGIONAL_PROMPT.json
ComfyUIPortable/workflows/04_REGIONAL_LORA_EXPERIMENT.json
```

既存の01/02基本生成Workflowが正常に動作している状態をbaselineとしてください。

---

# 2. GITHUB.TXTのCommit SHA方式を修正する

現在の `GITHUB.TXT` は、ファイル生成後にcommitしたため、

```text
Current Commit SHA
```

がComfyUIPortable追加前の親commitを指しています。

この方式を廃止してください。

今後は、

```text
Review Target Commit SHA:
```

としてください。

手順は以下です。

```text
実装・Workflow・報告書を完成
↓
commit
↓
SHA = A を取得
↓
GITHUB.TXTへ Review Target Commit SHA: A を記録
↓
GITHUB.TXTだけcommit
```

外部AIはmain上の最新GITHUB.TXTを読み、

```text
Review Target Commit SHA = A
```

に固定してレビュー対象コードを読むものとします。

GITHUB.TXTには可能なら、

```text
Latest main URL
Review-target pinned URL
Review-target pinned Raw URL
```

を区別して記載してください。

「GITHUB.TXT自身を含むcommit SHA」をGITHUB.TXT自身へ書こうとしないでください。

---

# 3. 現状ドキュメントの監査

`03_MANGA_REGIONAL_PROMPT.json` は現状、

```text
Global
Region A
Region B
SolidMask
ConditioningSetMask
```

による固定Workflowであり、視覚的Region Editorではありません。

その旨をドキュメントへ明記してください。

また `04_REGIONAL_LORA_EXPERIMENT.json` をコードレベルで再確認してください。

現在は2本のLoRA branchのうち、最終KSamplerへ両方のMODEL/ConditioningがRegion別に入っていないように見えます。

本当にRegional LoRAとして成立しているか接続を監査してください。

成立していなければ、

```text
EXPERIMENTAL / NOT YET REGIONAL
```

等としてKNOWN_ISSUESへ記録してください。

今回は無理にRLLを完成させないでください。

---

# 4. Wildcard UIを改善する

現在のWildcard展開自体は維持してください。

EasyReforge側Wildcard資産はコピーせず、現在の共有/Junctionを利用します。

まず以下を調査してください。

```text
https://github.com/lokitsar/ComfyUI-WildcardOrganizer
```

このツールは、

```text
Wildcardフォルダ検索
Wildcard名検索
Wildcard内容検索
ファイル内容プレビュー
Raw Prompt確認
Resolved Prompt確認
Favorites
Recipe
```

を持つため、今回の目的とかなり近いです。

現行ComfyUIとの互換性を確認し、問題なければ導入してください。

Wildcard folderは既存共有先

```text
D:\GitHub\tegaki\ComfyUIPortable\ComfyUI\wildcards
```

またはその実体であるEasyReforge側資産を使用してください。

Wildcardファイルを複製しないでください。

---

# 5. Wildcard動作確認

単にPythonライブラリがWildcardを展開できるだけでなく、

実際のComfyUI UI上で以下を確認してください。

```text
Wildcardを検索できる
Wildcardファイルの中身を確認できる
Promptへ追加できる
__wildcard__ を解決できる
{A|B|C} を解決できる
Resolved Promptを確認できる
```

192ファイル程度存在する現在のWildcard資産で実際にテストしてください。

結果を報告してください。

---

# 6. Generic Prompt Autocompleteについて

Wildcard Browserとは別に、通常tag補完も有用です。

参考候補:

```text
https://github.com/pythongosssss/ComfyUI-Custom-Scripts
```

このRepositoryにはAutocompleteがあります。

ただし現在の保守状況・ComfyUI互換性を確認してください。

Wildcard Organizerだけで今回の要求を満たすなら、無理に追加しないでください。

Custom Nodeを増やしすぎないことを優先します。

---

# 7. Manga Region Editor候補実装を調査する

新規実装前に、最低限以下を読んでください。

```text
https://github.com/Tsubasa109/comfyui_manga_panel
```

特に、

```text
ドラッグで矩形作成
矩形内部ドラッグで移動
corner handleでresize
Clear
座標出力
Mask出力
crop
composite
```

の実装を参考にしてください。

また、

```text
https://github.com/OnekoSL/Nukun_ComfyUI_Nodes
```

も確認してください。

Regional Rect Masks等のbrowser-side rectangle editorと、Native Regional Conditioning / DenseDiffusionとの接続方法を調査してください。

既存実装だけで今回の要求の大半を満たす場合は、それを利用・adapter化することを優先してください。

満たさない場合のみ独自Editorを実装してください。

コードを直接流用する場合は必ずライセンスを確認し、

`RESEARCH_REFERENCES.md`

へ記録してください。

---

# 8. Tegaki Manga Region Editorを作る

今回の中心機能です。

名称候補:

```text
Tegaki Manga Region Editor
```

既存

```text
tegaki_manga_nodes
```

パッケージへ追加してください。

Python backendだけでなく、ComfyUI frontend JSを使用した視覚的Editorを作って構いません。

---

# 9. 最大6コマ

最大6 Regionを扱えること。

UI上では、

```text
KOMA 1
KOMA 2
KOMA 3
KOMA 4
KOMA 5
KOMA 6
```

を明確に区別してください。

各コマに対応するPrompt欄を用意してください。

---

# 10. Prompt欄の表示

各Prompt欄にはサンプルとして、

```text
koma1: character, action, background...
koma2: character, action, background...
koma3: ...
```

のように何を書く場所か分かる表示をしてください。

ただし、この `koma1:` 自体をモデルへ送る必要はありません。

可能ならplaceholder/help表示とし、

ユーザーが入力しない限りconditioningへ混ざらないようにしてください。

---

# 11. Global Prompt

Region Promptとは別に、

```text
Global Prompt
```

を持たせてください。

例えば、

```text
manga page
monochrome
style
overall lighting
common background rule
```

などを記述する領域です。

現在のGlobal Prompt思想を維持してください。

Negative Promptは今回Editorへ無理に統合しなくて構いません。

---

# 12. コマ数

以下の入力を用意してください。

```text
Panel Count: 1～6
```

Panel Countが3なら、

```text
KOMA1 ON
KOMA2 ON
KOMA3 ON
KOMA4 OFF
KOMA5 OFF
KOMA6 OFF
```

を基本状態とします。

ただし各Regionには個別ON/OFFも持たせてください。

Panel Countを減らした場合も、OFFになったPrompt・矩形状態を即座に破棄しないでください。

後で数を戻したとき復元可能な方が望ましいです。

---

# 13. Region Canvas

Editor内にページ全体を表すCanvasを表示してください。

初期値は現在の漫画縦長設定、

```text
832 x 1216
```

で構いません。

ただし座標はpixel固定ではなく、

```text
x
y
width
height
```

を0～1 normalized coordinateとして内部保存することを推奨します。

これにより生成解像度を変更してもRegion layoutを維持できます。

---

# 14. Region基本操作

最低限以下を実装してください。

```text
矩形作成
矩形選択
矩形移動
矩形resize
矩形重ね合わせ
矩形削除
Undo
Redo
Reset
```

空いている場所をドラッグして矩形作成。

矩形内ドラッグで移動。

handleでresize。

Region同士のoverlapは禁止しないでください。

---

# 15. 複数矩形の同時移動

複数Regionを選択して一緒に移動できる仕組みが欲しいです。

例えば、

```text
Shift + clickでmulti select
Group Move ON/OFF
```

等で構いません。

操作方法はより良い案があれば変更可能です。

その場合は報告してください。

---

# 16. Region Color

KOMA 1～6に安定した色を割り当ててください。

例:

```text
KOMA1 赤系
KOMA2 青系
KOMA3 緑系
KOMA4 黄系
KOMA5 紫系
KOMA6 水色系
```

正確な色は任せます。

重要なのは、

```text
Canvas矩形
Prompt欄header
Region一覧
```

で同じ色が対応することです。

---

# 17. Region入れ替え

Regionの意味を入れ替える操作を用意してください。

例えばKOMA1とKOMA3を交換した場合、

```text
Prompt
色
Region ID
必要なら将来Control設定
```

も一緒に交換してください。

単に矩形位置だけを交換するのか、

KOMA IDそのものを交換するのかが曖昧にならないUIにしてください。

---

# 18. Slice機能

選択したRegionを分割する機能を作ってください。

最低限、

```text
Split Horizontal
Split Vertical
```

を用意してください。

初期実装は50:50分割で構いません。

例えばKOMA1をVertical Splitした場合、

```text
KOMA1
+
次の未使用KOMA
```

へ分割します。

空きRegionがない場合は処理せず、UI上で理由を表示してください。

将来的には分割比率を変更可能にして構いません。

---

# 19. Undo / Redo

最低限以下を履歴対象にしてください。

```text
create
move
resize
delete
split
swap
panel count変更
enable / disable
```

可能なら、

```text
Ctrl+Z
Ctrl+Y
```

も対応してください。

---

# 20. State保存

最重要項目です。

ComfyUI Workflowを保存して再読み込みした際、

```text
Panel Count
ON/OFF
各Prompt
各矩形座標
色対応
選択状態以外のEditor設定
```

が復元されること。

Frontendだけに状態を持たないでください。

workflow JSONへ保存されるWidget値またはHidden JSON等を使用してください。

---

# 21. REGION_SPEC

今後6本のMask/Prompt配線を動的に増減させるとWorkflowが非常に複雑になります。

そのため今回、

```text
REGION_SPEC
```

相当の統一データ形式を設計してください。

例えば概念上、

```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "panel_count": 3,
  "global_prompt": "...",
  "regions": [
    {
      "id": 1,
      "enabled": true,
      "x": 0.0,
      "y": 0.0,
      "w": 0.5,
      "h": 0.4,
      "prompt": "...",
      "color": "..."
    }
  ]
}
```

のような構造です。

正確なschemaは改善して構いません。

ただしversion番号を持たせてください。

---

# 22. 今回の出力

Phase 2では少なくとも、

```text
region_spec_json
```

を出力してください。

可能であれば、

```text
Mask batch
Color preview image
```

等も出力し、Editorの状態をbackend側でも検証できるようにしてください。

ただし無理に6本の固定Mask outputを作る必要はありません。

今後Region Compilerノードで利用できる設計を優先してください。

---

# 23. 今回は生成処理へ直結させすぎない

今回の主要目的はUI設計です。

現在正常に動いている

```text
01_BASIC_ILLUSTRIOUS_TXT2IMG
02_ILLUSTRIOUS_I2I
03_MANGA_REGIONAL_PROMPT
```

を壊さないでください。

新Editorはまず独立Workflowとして作成してください。

例:

```text
07_MANGA_REGION_EDITOR_UI_TEST.json
```

---

# 24. Region Prompt内LoRAについて

現時点の

```text
<lora:name:weight>
```

はMODEL全体へLoRAを適用します。

まだRLLを実装していない段階で、

「KOMA1 Promptへ書いたLoRAだからKOMA1だけに効く」

ように見せないでください。

Region Prompt内に `<lora:...>` がある場合、

今回の段階では、

```text
Region-local LoRA is not implemented yet
```

と警告するか、Region Prompt内LoRAを無効扱いにする設計を検討してください。

Global LoRAは従来どおり使用可能です。

---

# 25. ControlNetについて

ControlNetをRegion Editorへ近づける方向性は採用します。

ただし今回は未実装のControlボタンを大量に置かないでください。

次Phaseで、

```text
Region Mask
↓
Region-specific ControlNet
↓
Advanced ControlNet
```

へ接続します。

今回のREGION_SPECは将来、

```text
control_enabled
control_strength
control_start
control_end
```

等を追加できる拡張性だけ確保してください。

実際に動かないUIを表示する必要はありません。

---

# 26. I2Iについて

次Phaseでは選択Regionを、

```text
Crop
↓
I2I
↓
Composite
```

する予定です。

以下の実装を研究資料として確認してください。

```text
https://github.com/Tsubasa109/comfyui_manga_panel
```

今回は既存 `02_ILLUSTRIOUS_I2I` を壊さないことを優先します。

---

# 27. 将来Phase

今回完成後、次の順序で発展予定です。

```text
Phase 3
Region Editor
↓
Regional Conditioning Compiler
↓
6 Region Prompt対応

Phase 4
Region Mask
↓
ControlNet
I2I Crop / Composite

Phase 5
Region A → LoRA A
Region B → LoRA B
Impact RegionalSampler等
↓
疑似RLL

Phase 6
必要であればsingle-pass spatial LoRA modulation
```

今回Phase 5以降を先走って実装しないでください。

---

# 28. Test

最低限以下を自動または手動テストしてください。

```text
ComfyUI起動
01 workflowが従来通り生成可能
02 workflowが従来通りI2I可能
Wildcard検索
Wildcard内容表示
Wildcard展開
Region Editor表示
Panel Count 1～6
Region ON/OFF
drag create
move
resize
overlap
multi move
split horizontal
split vertical
delete
undo
redo
swap
workflow save
workflow reload
state復元
```

JavaScript console errorも確認してください。

---

# 29. 報告書

新規に、

```text
PHASE2_MRP_UI_REPORT.md
```

を作成してください。

最低限、

```text
1. 実装内容
2. 導入Custom Node
3. 各GitHub URL
4. Wildcard Organizer評価
5. Manga Panel実装から参考にした点
6. Nukun Regional Editorから参考にした点
7. 独自実装した部分
8. なぜ独自実装が必要だったか
9. UI操作一覧
10. REGION_SPEC schema
11. 自動テスト結果
12. 手動テスト結果
13. 既知の問題
14. 今後のPhase 3案
15. 指示外でGemini自身が追加したもの
16. それを追加した理由
17. 削除しても基本機能へ影響しないか
```

を記載してください。

---

# 30. GITHUB.TXT更新

Phase 2完成後、

```text
PHASE2_MRP_UI_REPORT.md
Region Editor Python
Region Editor JS
REGION_SPEC関連コード
07_MANGA_REGION_EDITOR_UI_TEST.json
更新したKNOWN_ISSUES
```

へのGitHub / Rawリンクを `GITHUB.TXT` へ追加してください。

前述の二段commit方式を使用し、

```text
Review Target Commit SHA
```

を必ず記録してください。

---

# 31. 最終回答

作業終了時には、

```text
Review Target Commit SHA:
GITHUB.TXT Raw:
PHASE2_MRP_UI_REPORT Raw:
Region Editor source:
Region Editor frontend JS:
UI test workflow:
```

を提示してください。

こちらで外部AIレビューを行います。

---

# 今回の最重要原則

現在のComfyUI環境は既に画像生成可能です。

したがって今回は、

「動くものを全部作り直す」

のではなく、

**既存の安定したIllustrious生成基盤の前段に、漫画制作専用の操作UIを追加する**

という考え方で進めてください。

まずWildcard UXとRegion Editor UIを完成させます。

Regional Conditioning、ControlNet、I2I、RLLは、そのUIが使いやすいことを確認した後で段階的に接続します。