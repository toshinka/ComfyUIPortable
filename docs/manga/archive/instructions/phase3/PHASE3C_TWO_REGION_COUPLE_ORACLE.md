# ComfyUI Portable Phase 3C — Two-Region Couple / Regional Prompter Oracle 指示書

## 0. 今回の位置づけ

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

ユーザー提示の次Review Target候補:

```text
43e57c05afc0496dd3fab23ea06013ae02dca90f
```

ただし外部レビュー時点では、このSHAはGitHub公開側からまだ解決できていません。

GitHubで解決可能になった場合は、

```text
43e57c05afc0496dd3fab23ea06013ae02dca90f
```

をPhase 3Cのbaselineとして使用してください。

解決できない場合は作業を開始する前に、

```text
git rev-parse HEAD
git status
git log -5 --oneline
git ls-remote origin main
```

を確認し、Phase 3B.1.1 Hotfixがcommit / push済みであることを確認してください。

今回の目的は、新しい完成GUIを作ることではありません。

Phase 3B系で、

```text
Region Editor
→ Page Compiler
→ Mask Builder
→ Conditioning Builder
→ KSampler
→ VAE Decode
```

まで実画像生成が成立しました。

しかし現状はまだ、

```text
「コマ枠らしきマスクがある」
「PromptがRegional Conditioningへ入る」
```

ところまでです。

次に必要なのは、

```text
矩形A
矩形B

Prompt A
Prompt B
```

の対応が人間にもコードにも明確な、最小の2領域Regional Oracleです。

このOracleで、

```text
横並び
縦並び
重なり
同一シーン内の2人物
```

を固定条件で検証し、どのRegional Backendが漫画用途に向いているか判断します。

---

## 1. 今回の最重要方針

今回からしばらく、ユーザーへ細かなUI確認を求めないでください。

Gemini側で、

```text
実装
Unit Test
API Integration Test
Workflow Zero-Touch Test
固定Seed生成
局所性メトリクス
比較画像保存
```

まで行ってください。

ユーザーによる次の実画像確認は、

```text
Couple / Regional Prompter相当の2領域制御が
実際に動く段階
```

まで原則不要です。

GPT側はGitHub固定commitをコードレビューします。

ユーザーは後段で、

```text
レイアウト
操作感
制作上の使い勝手
```

を確認する役割とします。

---

## 2. 最終目標との関係

将来の本番目標は、

```text
最大6 KOMA
+
各KOMA内のCharacter Region
+
必要ならLocal Region
```

です。

概念:

```text
PAGE
├ KOMA1
│  ├ Character A
│  ├ Character B
│  └ Local Regions
├ KOMA2
│  └ Character A
...
└ KOMA6
```

ただし今回これを一気に実装しないでください。

最初は、

```text
Region A
Region B
```

の2個だけです。

2領域でRegional Promptの挙動が理解できなければ、6コマ化しても問題が見えにくくなるためです。

---

## 3. Phase構成

```text
3C-0  Hotfix verification
3C-1  Two-Region Spec
3C-2  Two-Region Rectangle Editor
3C-3  Core Masked Conditioning Oracle
3C-4  Impact RegionalSampler Oracle
3C-5  One-Scene Two-Subject Test
3C-6  Optional ControlNet Layout Assist
3C-7  Backend comparison and recommendation
```

---

## 4. 3C-0 — Phase 3B.1.1 Hotfix確認

まず09 / 10について、

```text
ZERO-TOUCH PASS
```

が維持されていることを再確認してください。

最低限:

```text
09 load → no touch → Queue → image
10 load → no touch → Queue → image
```

を確認。

今回の2領域実装で既存Workflowを壊さないこと。

---

## 5. TWO_REGION_SPEC v1

今回の2領域Oracleは本体REGION_SPECへ急いで混ぜず、

```text
TWO_REGION_SPEC
```

として独立させて構いません。

候補:

```json
{
  "version": 1,
  "canvas": {
    "width": 832,
    "height": 1216
  },
  "global_prompt": "",
  "global_negative_prompt": "",
  "regions": [
    {
      "id": "A",
      "enabled": true,
      "prompt": "1girl, blonde hair",
      "negative_prompt": "",
      "x": 0.05,
      "y": 0.10,
      "w": 0.42,
      "h": 0.80
    },
    {
      "id": "B",
      "enabled": true,
      "prompt": "1boy, black hair",
      "negative_prompt": "",
      "x": 0.53,
      "y": 0.10,
      "w": 0.42,
      "h": 0.80
    }
  ],
  "metadata": {}
}
```

今回のみA/B固定で構いませんが、コード構造は将来N regionへ拡張できるようにしてください。

---

## 6. 2領域Rectangle Editor

名称候補:

```text
Tegaki Two Region Couple Editor
```

または

```text
Tegaki Regional Oracle Editor
```

本番Manga Region Editorとは分けてください。

Canvasは指定width/heightのアスペクト比を維持して表示してください。

必須機能は最低限:

```text
Region A選択
Region B選択
矩形をドラッグ作成
矩形を移動
矩形をResize
矩形を削除 / disable
```

今回不要:

```text
隣接RegionへのSnap
自動整列
複雑なGroup Move
高度なUndo履歴
6コマUI
```

---

## 7. Promptと矩形の対応を明確にする

最低限、

```text
Region A Prompt
Region B Prompt
```

がCanvasと同じNodeまたは隣接Nodeで明確に見えること。

Oracle段階では、

```text
A = Blue
B = Orange
```

など固定色で構いません。

矩形色とPrompt欄見出しを一致させてください。

Canvas上には、

```text
A: <prompt先頭>
B: <prompt先頭>
```

を表示してください。

---

## 8. Preset Layout

最低限:

```text
Horizontal Split
Vertical Split
Overlap
One Region A
One Region B
Reset
```

を用意してください。

Horizontal Split:

```text
[A][B]
```

Vertical Split:

```text
[A]
[B]
```

Overlapは中央で25〜35%程度重なるPresetで構いません。

One Regionでは片方をdisabledにしてください。

---

## 9. Mask Preview

Editor / Mask Builderから、

```text
Region A Mask
Region B Mask
Combined Preview
```

を出力してください。

---

## 10. 3C-3 — Core Masked Conditioning Oracle

現行のCore Masked Conditioningを2領域専用に単純化したOracleを作ってください。

名称候補:

```text
Tegaki Two Region Core Conditioner
```

入力:

```text
CLIP
TWO_REGION_SPEC
```

出力:

```text
positive
negative
mask_A
mask_B
debug_json
```

今回の目的はRegional Backendそのものを見ることなので、

```text
CAST_SPEC
PAGE_COMPILE_PLAN
LOCAL_REGION
```

等を必須にしないでください。

最短経路:

```text
2 rectangles
+
2 prompts
+
global prompt
↓
masked conditioning
↓
sampler
```

にしてください。

---

## 11. Workflow 11

新規:

```text
workflows/11_TWO_REGION_CORE_COUPLE_ORACLE.json
```

区分:

```text
EXPERIMENTAL / REGIONAL ORACLE
```

最低構成:

```text
Checkpoint
↓
Global LoRA optional
↓
Two Region Editor
↓
Two Region Core Conditioner
↓
KSampler
↓
VAE Decode
↓
Save / Preview
```

Debug:

```text
Mask Preview
Spec Inspector
```

公式Workflowとして、

```text
load
no touch
Queue
image
```

を必須にしてください。

---

## 12. 3C-4 — Impact RegionalSampler Oracle

既に導入済みのImpact Packを実環境で調査してください。

特に:

```text
RegionalSampler
RegionalPrompt
KSamplerProvider
```

等の現在の実装/APIを確認。

Runtime `/object_info` とインストール済みコードを確認し、推測でNode名やslotを作らないでください。

目的は、

```text
Forge Couple / Regional Prompter的に
領域Aと領域BのPromptがどの程度分離できるか
```

を見ることです。

Coreと同じ `TWO_REGION_SPEC` を使用してください。

必要なら、

```text
TWO_REGION_SPEC
↓
Impact Regional Prompt A/B
```

へ変換する小さなAdapter Nodeを作って構いません。

Backend-specific情報をTWO_REGION_SPEC本体へ混ぜないこと。

---

## 13. Workflow 12

利用可能なら:

```text
workflows/12_TWO_REGION_IMPACT_COUPLE_ORACLE.json
```

区分:

```text
EXPERIMENTAL / REGIONAL BACKEND ORACLE
```

ImpactがRuntimeで利用不能なら無理にfake workflowを作らず、

```text
IMPACT ORACLE:
BLOCKED
reason: ...
```

と報告してください。

---

## 14. Dog / Cat Test

Global:

```text
simple outdoor scene, full body, clear subjects
```

A:

```text
a golden retriever dog
```

B:

```text
a black cat
```

以下を固定Seedで生成:

```text
Horizontal
Vertical
Overlap
```

期待:

```text
dog predominantly A
cat predominantly B
```

完全分離は必須ではありません。

---

## 15. Man / Woman Test

A:

```text
1man, black hair, dark jacket
```

B:

```text
1woman, blonde hair, light dress
```

背景は共通。

以下を生成:

```text
Horizontal
Vertical
Overlap
```

属性混線を観察してください。

---

## 16. One Scene / Two Subject Test

ユーザーが特に確認したいケースです。

2つの独立コマではなく、

```text
1つのシーン
+
人物A領域
+
人物B領域
```

としてテストしてください。

Global Prompt例:

```text
two people standing together, friendly interaction
```

A/BはIdentity中心。

A/B矩形を接近させたケースと重ねたケースを作り、

```text
肩を組む
接近する
向き合う
単に左右端へ分離される
属性混線
身体融合
```

の傾向を観察してください。

---

## 17. One Region比較

A/Bの地域指定を使わず、

```text
1man and 1woman, standing together
```

をGlobalだけで生成する比較も行ってください。

以下を別テストとして記録してください。

```text
A. Region = 別シーン領域
B. Region = 同一シーン内の人物領域
```

同じ結果を期待しないこと。

---

## 18. 自動局所性メトリクス

新規候補:

```text
scripts/test_two_region_locality_metrics.py
```

固定Seedで、

Base:

```text
A = blonde woman
```

Variant:

```text
A = blue-haired woman
```

Bは固定。

生成画像差分を取り、

```text
mean absolute difference inside A
mean difference inside B
mean difference outside A/B
```

を計測してください。

報告:

```text
A_target_change / B_change
A_target_change / outside_change
```

最初から厳格な閾値を固定せずraw valueを保存してください。

B側も同様に行うこと。

Overlap Testでは可能なら、

```text
A-only
B-only
A∩B
Outside
```

を別集計してください。

---

## 19. Semantic Self-Review

Gemini環境で生成画像を直接視覚確認できる場合は、

```text
subject A correct
subject B correct
position A
position B
attribute bleed
fusion
background contamination
```

を自己評価してください。

視覚確認できない場合は、

```text
MANUAL SEMANTIC REVIEW PENDING
```

とし、勝手にPASSにしないでください。

---

## 20. ユーザー確認Gate

Workflow 11 / 12が成立しても、ユーザーへ毎回確認依頼しないでください。

Gemini自己テスト + GPTコードレビューを先に行います。

ユーザーへ確認を求めるのは、

```text
Core vs Impactのどちらを採るか候補が絞れた時
```

で構いません。

---

## 21. 3C-6 — ControlNet Layout Assist

2領域Regionalだけでは、

```text
コマ分割
人物位置
画面分離
```

が不安定な場合の補助候補です。

ユーザーが示したような、

```text
[A][B]
```

または

```text
[A]
[B]
```

の単純な矩形ガイドをTWO_REGION_SPECから自動生成してください。

出力候補:

```text
Panel outline image
Binary block image
Color block image
```

---

## 22. ControlNetモデル監査

現在共有されているControlNet群を確認し、

```text
scribble
lineart
canny
segmentation
depth
openpose
etc.
```

のどれがあるか記録してください。

矩形レイアウトに適している場合のみ実験します。

候補:

```text
Segmentation ControlNet
または
Scribble / Canny / LineartでPanel border
```

単純な色ブロックを意味なくDepth/OpenPoseへ入れないこと。

---

## 23. Workflow 13

適切なControlNetが存在する場合のみ:

```text
workflows/13_TWO_REGION_CONTROLNET_LAYOUT_AUX.json
```

を作成してください。

役割は、

```text
Two Region Regional Backend
+
Panel Layout ControlNet
```

です。

ControlNet単体でRegional Promptを代替しません。

適切なモデルが無い場合:

```text
CONTROLNET LAYOUT AUX:
NOT TESTED
reason: suitable model unavailable
```

で構いません。

---

## 24. Workflow整理

```text
09 = Manga End-to-End POC
10 = 4-scope Regional Control Expansion

11 = Two Region Core Oracle
12 = Two Region Impact Oracle
13 = Layout Assist Oracle
```

09/10を置き換えないでください。

---

## 25. Backend比較

CoreとImpactが両方動いた場合、最低限以下を比較してください。

| 項目 | Core Masked Conditioning | Impact RegionalSampler |
|---|---|---|
| Horizontal separation | | |
| Vertical separation | | |
| Overlap | | |
| Dog/Cat binding | | |
| Man/Woman binding | | |
| Attribute leakage | | |
| Interaction | | |
| Seam | | |
| Speed | | |
| VRAM | | |
| Workflow complexity | | |
| ComfyUI compatibility | | |

同一model / seed / resolution / steps / samplerで比較してください。

---

## 26. 今回やらないこと

以下は今回実装しないでください。

```text
6 KOMA完成UI
CAST Master完成UI
Character Panel完成UI
KOMA LoRA
Character LoRA
Spatial LoRA
RLL
人物OpenPose統合
```

ControlNetはPanel Layout補助まで。

---

## 27. Tests

最低限新規:

```text
scripts/test_two_region_spec.py
scripts/test_two_region_editor_state.py
scripts/test_two_region_core_backend.py
scripts/test_two_region_locality_metrics.py
```

Impact実装時:

```text
scripts/test_two_region_impact_backend.py
```

ControlNet時:

```text
scripts/test_two_region_controlnet_layout.py
```

---

## 28. TWO_REGION_SPEC / Editor Test

最低限:

```text
A/B fixed IDs
enabled bool
strict prompt type
valid geometry
delete/disable
horizontal preset
vertical preset
overlap preset
one-region preset

create A
create B
move
resize
delete A
restore A
save/reload exact
```

---

## 29. Zero-Touch Workflow Test

11 / 12 / 13について、存在するものはすべて:

```text
ComfyUI restart
load
no touch
Queue
image
```

を確認してください。

既存:

```text
test_workflow_json_integrity.py
test_workflow_widget_compatibility.py
```

対象へ11/12/13も追加してください。

---

## 30. 生成結果保存

例:

```text
output/Tegaki/TwoRegionOracle/
```

以下を保存:

```text
Core_DogCat_Horizontal
Core_DogCat_Vertical
Core_DogCat_Overlap

Core_ManWoman_Horizontal
Core_ManWoman_Vertical
Core_ManWoman_Overlap
Core_ManWoman_OneScene

Impact_...
ControlNet_...
```

可能ならBackendごとに、

```text
horizontal / vertical / overlap / one-scene
```

を並べたContact Sheetを作成してください。

生成画像をGitへ大量追加しないこと。

Gitにはfilename / seed / prompt / metric / 結果要約だけ記録してください。

---

## 31. Phase 3C報告書

新規:

```text
PHASE3C_TWO_REGION_COUPLE_ORACLE_REPORT.md
```

最低限:

```text
1. Baseline verification
2. TWO_REGION_SPEC
3. Two Region Editor
4. Rectangle interaction
5. Horizontal preset
6. Vertical preset
7. Overlap preset
8. One Region mode
9. Core Oracle implementation
10. Core generation tests
11. Impact Pack runtime audit
12. Impact Oracle implementation/result
13. Dog/Cat comparison
14. Man/Woman comparison
15. One Scene Two Subject
16. Locality metrics
17. Attribute leakage
18. Interaction behavior
19. Performance
20. ControlNet model audit
21. ControlNet layout assist result
22. Recommended Regional Backend
23. N-region / 6 KOMA readiness
24. Character Region readiness
25. Known issues
26. Next phase
27. Gemini独自判断
```

---

## 32. 6 KOMA化へのGate

以下が最低限満たされてから、

```text
2 Region → N Region / 6 KOMA
```

へ進みます。

```text
A/B Prompt mappingが明確
Horizontalで位置傾向あり
Verticalで位置傾向あり
Overlapが破綻しすぎない
One Scene Two Subjectが観察済み
Backend採用候補あり
```

---

## 33. Character RegionへのGate

同一シーン2人物テストで、

```text
人物A
人物B
```

の属性と位置をある程度誘導できるBackendが見つかったら、

そのBackendを、

```text
KOMA内Character Region
```

へ統合します。

---

## 34. 終了判定

報告書末尾:

```text
CORE TWO-REGION:
PASS / PARTIAL / FAIL

IMPACT TWO-REGION:
PASS / PARTIAL / FAIL / BLOCKED

CONTROLNET LAYOUT AUX:
PASS / PARTIAL / NOT TESTED / BLOCKED

RECOMMENDED REGIONAL BACKEND:
CORE / IMPACT / CONTINUE COMPARISON

6-KOMA READINESS:
GO / HOLD

CHARACTER-REGION READINESS:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

を必ず記載してください。

---

## 35. GITHUB.TXT二段Commit

まず実装・テスト・報告書を:

```text
Commit A
Phase 3C Two-Region Couple Oracle
```

としてcommit。

そのSHAを取得。

その後:

```text
Review Target Commit SHA: A
```

をGITHUB.TXTへ記載。

GITHUB.TXTのみ別commit。

---

## 36. GITHUB.TXTに追加

最低限:

```text
PHASE3C_TWO_REGION_COUPLE_ORACLE_REPORT.md

TWO_REGION_SPEC implementation
Two Region Editor implementation
Core Oracle implementation

Impact Adapter implementation（作成時）
ControlNet Layout implementation（作成時）

test_two_region_spec.py
test_two_region_editor_state.py
test_two_region_core_backend.py
test_two_region_locality_metrics.py

Workflow 11
Workflow 12（作成時）
Workflow 13（作成時）
```

Pinned Rawを追加。

---

## 37. 最終回答

作業完了時:

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3C_TWO_REGION_COUPLE_ORACLE_REPORT Raw:

Two Region Spec Raw:
Two Region Editor Raw:
Core Oracle Raw:
Impact Adapter Raw: (if created)
ControlNet Layout Raw: (if created)

Workflow 11 Raw:
Workflow 12 Raw: (if created)
Workflow 13 Raw: (if created)

Two Region Spec Test Raw:
Core Backend Test Raw:
Impact Backend Test Raw: (if created)
Locality Metrics Test Raw:

CORE TWO-REGION:
IMPACT TWO-REGION:
CONTROLNET LAYOUT AUX:
RECOMMENDED REGIONAL BACKEND:
6-KOMA READINESS:
CHARACTER-REGION READINESS:
NEXT RECOMMENDED PHASE:
```

を提示してください。

---

# 最終方針

ここから必要なのは完成GUIではありません。

まず、

```text
Canvas
+
矩形A
+
矩形B
+
Prompt A
+
Prompt B
```

だけで、

```text
どのBackendなら
どの程度「場所」と「意味」を結びつけられるか
```

を明らかにしてください。

漫画制作上は、

```text
6コマ
複数人物
人物同士の演技
背景
```

へ最終的に拡張しますが、最初は2領域だけで十分です。

2領域Oracleが成立した後に、そのBackendを、

```text
最大6 KOMA
+
KOMA内Character Region
```

へ拡張してください。

また2領域の境界自体が不安定な場合は、

```text
Regional Prompt
+
Panel Layout ControlNet
```

を補助候補として比較してください。

ユーザー確認はCouple / Regional Prompter相当の動作が揃うまで最小限とし、それまではGemini自己テストとGPTコードレビューを中心に進めてください。
