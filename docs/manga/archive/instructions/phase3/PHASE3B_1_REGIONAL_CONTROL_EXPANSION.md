# ComfyUI Portable Phase 3B.1 — Regional Control Expansion & Validation 指示書

## 0. 今回の位置づけ

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review baseline:

```text
95ab6023f07183cf9418c6a036c1c0186a3e183a
```

現状、少なくとも開発ワークフロー上では、

```text
Region Editor
→ Page Compiler
→ Mask Builder
→ Conditioning Builder
→ KSampler
→ VAE Decode
→ 漫画っぽい出力
```

まで到達しています。

これは重要な前進です。

ここまでは、

```text
「データ契約」
↓
「実際のRegional生成へ接続」
```

の最小成立確認とみなします。

ただし現段階ではまだ、

```text
“なんとなく漫画っぽいものは出る”
```

状態であり、

```text
「どの領域に、どのPrompt / Character / 制御が、どの程度効くのか」
```

を制作上の意味があるレベルで検証・拡張する段階には入っていません。

今回のPhase 3B.1では、ここを前進させます。

---

# 1. 今回の主目的

今回の目的は、

```text
漫画っぽいものが出る
```

から、

```text
コントロールしたい領域を増やし、
その効き方を確認しながら、
制作に使えるRegional基盤へ寄せる
```

へ進めることです。

大きく分けて以下を行ってください。

```text
1. 現行Regional生成の検証強化
2. Control scopeの拡張
3. 局所制御の調整パラメータ追加
4. 必要ならRegional backend比較
5. その成果を集約した新ワークフロー作成
```

---

# 2. 先に結論

次にやるべき筋は、**UI美化ではなく、コントロール領域の拡張と実画像での効き確認**です。

つまり、

```text
Global
Panel
Character
```

まで来たので、次は必要に応じて

```text
Panel内追加Local Region
Character Area
ControlNetの将来接続点
```

を増やし、

```text
何がどこに効くか
```

を実際の画像で観察・報告してください。

---

# 3. 今回の作業単位

以下の順で進めてください。

```text
Phase 3B.1-0
Current POC Validation Hardening

Phase 3B.1-1
Control Scope Expansion

Phase 3B.1-2
Regional Tuning Parameters

Phase 3B.1-3
Backend Comparison Gate

Phase 3B.1-4
Aggregated Experimental Workflow
```

---

# 4. Phase 3B.1-0 — Current POC Validation Hardening

今の09系ワークフローは、「実際に出る」こと自体は確認できています。

次に必要なのは、

```text
効いているのか
どこに効いているのか
どの程度漏れているのか
```

の観察です。

---

# 5. Debug / Inspectionを強化する

現行Workflowで、最低限以下が視覚的に確認できるようにしてください。

```text
1. Panel Mask Preview
2. Character Mask Preview
3. Compiled Positive Summary
4. Compiled Negative Summary
5. Global / Panel / Character LoRA Plan
6. Active Panel IDs
7. Character Binding Summary
```

必要なら、既存のInspectorを改善してください。

---

# 6. Debug JSONを見やすくする

現在の `debug_json` / `compile_plan_json` が読みにくい場合は、

```text
pretty JSON
summary text
```

の両方を出して構いません。

目的は、開発者が

```text
KOMA1には何が入ったか
Aliceには何が入ったか
Bobには何が入ったか
```

を即座に理解できることです。

---

# 7. A/B Testを最初に行う

現行Core backendのまま、まずは以下を必ず行ってください。

---

## 7.1 Panel Localization Test

固定Seed。

A:

```text
KOMA1 = classroom
```

B:

```text
KOMA1 = convenience store interior
```

他は完全固定。

期待:

```text
KOMA1中心に変化
KOMA2 / KOMA3は相対的に維持
```

---

## 7.2 Character Localization Test: Alice

固定Seed。

A:

```text
Alice = blonde hair
```

B:

```text
Alice = blue hair
```

期待:

```text
Aliceの主担当領域を中心に変化
Bobや他コマへの漏れは相対的に弱い
```

---

## 7.3 Character Localization Test: Bob

同様にBobだけ変更。

---

## 7.4 Global Prompt Test

Global Promptのみ変更。

期待:

```text
ページ全体に影響
```

---

## 7.5 Global LoRA Test

Global LoRA ON / OFF。

期待:

```text
ページ全体の画風に影響
```

---

# 8. 画像評価を誇張しない

報告では、以下を区別してください。

```text
動いた
局所性がある
局所性が弱い
制作に使える
まだ検証用
```

同義にしないでください。

---

# 9. 次に増やす制御領域の考え方

今回の重要な判断はこれです。

現在すでにある制御階層:

```text
Global
Panel (KOMA)
Character
```

今後必要になるもの:

```text
Panel内の追加局所領域
Optional subregion
Control hint
```

つまり「コントロールする領域を増やす方向」で合っています。

ただし、いきなりUIを巨大化させないでください。

---

# 10. Phase 3B.1-1 — Control Scope Expansion

今回、新しい概念として

```text
LOCAL_REGION
```

または同等の名前の補助領域を導入して構いません。

役割:

```text
Characterではないが、
そのPanel内の一部にだけ効かせたい補助制御
```

例:

```text
手前机
窓側
背景人物位置
小物の集まる位置
演出スポット
```

---

# 11. LOCAL_REGIONの目的

Characterだけでは扱いにくいケースがあります。

例:

```text
KOMA1の左奥にロッカーを出したい
KOMA2の右上だけ夕焼けを強めたい
KOMA3の下半分に机群を寄せたい
```

こうした「人物ではない局所指示」を扱うための層です。

---

# 12. LOCAL_REGIONは最小限にする

いきなり無制限に増やさないでください。

初期案:

```text
各KOMAにつき 0〜2 個程度
```

で十分です。

理由:

```text
まずは構造と効き方を見る
```

ためです。

---

# 13. LOCAL_REGIONの座標系

Character Areaと同様、

```text
KOMA-local 0〜1座標
```

を使用してください。

これによりKOMA移動後も相対位置を保てます。

---

# 14. LOCAL_REGION schema候補

正確な名前は改善して構いませんが、概念的には以下です。

```json
{
  "id": "local_1",
  "enabled": true,
  "prompt": "school desks near the window",
  "negative_prompt": "",
  "area": {
    "x": 0.55,
    "y": 0.10,
    "w": 0.35,
    "h": 0.50
  },
  "metadata": {}
}
```

---

# 15. 正本位置

LOCAL_REGIONは、Character masterのような再利用単位ではありません。

したがって、

```text
REGION_SPEC.regions[i]
```

の下に持たせる方向を推奨します。

例:

```text
Region (KOMA)
 ├ prompt
 ├ negative_prompt
 ├ characters[]
 └ local_regions[]
```

---

# 16. CharacterとLOCAL_REGIONの違い

Character:

```text
再利用される登場人物
```

LOCAL_REGION:

```text
そのKOMA限りの局所制御
```

です。

混同しないでください。

---

# 17. LOCAL_REGIONは必須ではない

存在しない場合は今まで通り動くこと。

既存Workflow互換を壊さないでください。

---

# 18. LOCAL_REGIONの使い道

最初の用途は以下です。

```text
Promptだけを局所的に効かせる
```

まだLoRAやControlNetをLOCAL_REGIONへ結びつける必要はありません。

---

# 19. LOCAL_REGIONのMask投影

Character Areaと同様にPage座標へ投影してください。

最低限:

```text
local_region_mask_batch
local_region_debug_json
mask preview
```

を持たせてください。

---

# 20. Conditioning優先順位

初期POCでは以下の重なり順を採用してください。

```text
Global
→ Panel
→ Local Region
→ Character
```

理由:

```text
Characterが最も具体的
Local Regionが次
Panelがその土台
Globalが最も広い
```

この順を報告書へ明記してください。

---

# 21. Phase 3B.1-2 — Regional Tuning Parameters

現在 `panel_strength` と `character_strength` はあるようなので、これを少し拡張してください。

最低限候補:

```text
panel_strength
character_strength
local_region_strength
set_cond_area mode
```

必要ならさらに、

```text
mask_feather / blur
overlap policy
```

を検討して構いません。

ただし増やしすぎないでください。

---

# 22. Mask edgeの調整

境界が固すぎる、または不自然な切れ目が出る場合に備えて、

```text
mask feather
```

またはそれに準ずる簡易パラメータを検討してください。

初期状態では固定でも構いません。

ただし将来調整可能な余地を残してください。

---

# 23. set_cond_area mode

現在 `set_cond_area = default` のような設定が見えるため、これをちゃんと検証してください。

少なくとも、

```text
default
mask bounds
```

等の選択肢が存在するなら比較してください。

無ければ現状維持で構いません。

---

# 24. Overlap時の扱い

Panel内で、

```text
Character Area
Local Region
```

が重なった場合の扱いを明記してください。

POC段階では、

```text
重なりを許容
Conditioningはそのまま重なる
```

で構いません。

複雑なpriority消去までは不要です。

---

# 25. Phase 3B.1-3 — Backend Comparison Gate

Core Masked Conditioningだけで十分な局所性が得られるかを評価してください。

もしA/B画像上で、

```text
TargetよりOutsideが同程度以上に変わる
```

なら、初めて比較として

```text
Impact Pack RegionalSampler
```

を検討してください。

---

# 26. 比較の順番

順番を守ってください。

```text
A. Core Masked ConditioningでA/B評価
↓
B. 不十分ならImpact RegionalSampler比較
```

最初から複数backendを混ぜないでください。

---

# 27. RLL / DenseDiffusionはまだ行わない

今回は、

```text
RLL
DenseDiffusion
Omost
IPAdapter
```

へ広げないでください。

まず必要なのは、

```text
“今ある基礎で、どこまで局所制御できるか”
```

の把握です。

---

# 28. Phase 3B.1-4 — 集約ワークフローを作る

今回の最後に、集大成ワークフローを1本作成してください。

新規:

```text
workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json
```

区分:

```text
EXPERIMENTAL / CONTROL EXPANSION HARNESS
```

---

# 29. Workflow 10 の目的

このWorkflowは、

```text
Global
Panel
Local Region
Character
```

の各階層が、実際の出力へどう作用するかを確認するためのものです。

UI完成版ではありません。

---

# 30. Workflow 10 の最低構成

概ね左から右へ:

```text
[MODEL]
Checkpoint
Global LoRA

[PAGE]
Tegaki Manga Region Editor

[CAST]
CAST_SPEC / Scene Input

[PAGE COMPILE]
Page Compiler

[MASK]
Panel Mask Builder
Local Region Mask Builder
Character Mask Builder
Mask Preview

[CONDITIONING]
Manga Conditioning Builder

[SAMPLE]
KSampler

[OUTPUT]
VAE Decode
Preview
Save

[DEBUG]
Compile Plan Inspector
Summary Text
```

---

# 31. Workflow 10 の初期サンプル

最低限3コマ。

例:

```text
KOMA1:
classroom, two people talking

Alice:
左側
Bob:
右側

Local Region 1:
窓側机群

KOMA2:
corridor, Alice only

Local Region 1:
posters on wall

KOMA3:
rooftop, background only
```

---

# 32. Workflow 10 で確認したいこと

最低限以下を確認できること。

```text
1. KOMA Prompt変更
2. Character Prompt変更
3. Local Region Prompt変更
4. Global Prompt変更
5. Global LoRA ON/OFF
```

---

# 33. Workflow 10 の設計原則

配線が多少多くても構いません。

大事なのは、

```text
どこが入力か
どこが内部変換か
どこがデバッグか
```

がGroupで明示されることです。

---

# 34. ControlNetは今回まだ主役ではない

次に必要になる可能性は高いですが、今回の主眼は

```text
Prompt / Character / Local Region の局所制御
```

です。

Workflow 10 へControlNetを本格統合しないでください。

必要なら将来の接続点だけ考慮して構いません。

---

# 35. ControlNetの将来接続点

将来的に導入するなら接続先は主に:

```text
Panel単位
Character単位
Page全体
```

です。

ただし今はSchema上の余地だけで十分です。

---

# 36. UI完成度は求めない

今回の10は、

```text
ちゃんと動くこと
効き方を観察できること
```

が目的です。

見た目を整えすぎる必要はありません。

---

# 37. 新しいテスト

最低限新規:

```text
scripts/test_local_region_spec.py
scripts/test_regional_control_expansion.py
```

を作成してください。

---

# 38. test_local_region_spec.py

最低限:

```text
local_regions absent compatibility
local_regions list validation
enabled bool
prompt / negative_prompt string
area valid rect
duplicate local id handling
```

を検証してください。

---

# 39. test_regional_control_expansion.py

最低限:

```text
Page compile with local_regions
Mask projection for local_regions
Conditioning count includes local regions
Overlapping character/local region supported
Existing character-only compile remains valid
```

---

# 40. Runtime generation tests

必ず実画像を生成してください。

最低限:

```text
09 current baseline
10 control expansion harness
```

を実行。

---

# 41. 保存する比較画像

最低限以下を保存してください。

```text
panel_ab_A / B
alice_ab_A / B
bob_ab_A / B
local_region_ab_A / B
global_ab_A / B
lora_ab_A / B
```

---

# 42. 報告書

新規:

```text
PHASE3B_1_REGIONAL_CONTROL_EXPANSION_REPORT.md
```

最低限以下を記載してください。

```text
1. 現行09の再評価
2. Debug強化
3. A/B Test結果
4. Local Region導入
5. Local Region schema
6. Local Region mask投影
7. Conditioning順序
8. 強度パラメータ
9. Overlap挙動
10. Core backendの局所性評価
11. RegionalSampler比較の要否
12. Workflow 10
13. 既存Workflow互換
14. 既知の問題
15. 次Phase候補
16. Gemini独自判断
```

---

# 43. 次Phase候補の整理

報告書末尾で次候補を整理してください。

候補:

```text
A. Character / CAST UI phase
B. ControlNet integration phase
C. RegionalSampler backend comparison phase
D. Panel Sequential phase
```

どれが最も筋が良いか理由付きで評価してください。

---

# 44. 既存Workflowへの扱い

```text
07 = Layout / Region Editor
08 = Data Contract / Debug
09 = End-to-End Regional POC
10 = Regional Control Expansion Harness
```

として整理してください。

---

# 45. Acceptance Criteria

以下を満たした場合のみ今回完了としてください。

```text
[ ] 09が引き続き動く
[ ] A/B TestでPanel局所性を確認
[ ] A/B TestでCharacter局所性を確認
[ ] Global Prompt影響を確認
[ ] Global LoRA影響を確認
[ ] Debug表示強化
[ ] Local Region schema追加
[ ] Local Region mask投影
[ ] Local Region conditioning追加
[ ] Character / Local overlapが処理可能
[ ] Workflow 10作成
[ ] Workflow 10で実画像生成成功
[ ] 既存07/08/09非破壊
```

---

# 46. やらないこと

今回は以下を行わないでください。

```text
完成版UIの仕上げ
RLL本格実装
DenseDiffusion導入
Panel Sequential生成
Regional LoRA本実装
ControlNet本格統合
```

---

# 47. GITHUB.TXT 更新

まず、

```text
Commit A
Phase 3B.1 Regional Control Expansion
```

として、

```text
実装
テスト
Workflow 10
報告書
```

をcommit。

そのSHAを取得。

その後、

```text
Review Target Commit SHA: A
```

を `GITHUB.TXT` に記載し、GITHUB.TXTのみ別commitしてください。

---

# 48. GITHUB.TXTに追加するもの

最低限:

```text
PHASE3B_1_REGIONAL_CONTROL_EXPANSION_REPORT.md
workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json

local region関連実装
regional control関連test
updated workflow index
```

のPinned Raw / Raw URLを掲載してください。

---

# 49. 最終回答

作業終了時に以下を提示してください。

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3B_1_REGIONAL_CONTROL_EXPANSION_REPORT Raw:

Workflow 09 Raw:
Workflow 10 Raw:

Local Region Spec Raw:
Regional Control Test Raw:

REGIONAL CONTROL RESULT:
PASS / PARTIAL / FAIL

NEXT RECOMMENDED PHASE:
```

---

# 最終方針

今回のポイントは、

```text
「出た」
```

で止まらず、

```text
「どこにどう効いたか」
```

を見ながら制御面を増やすことです。

つまり、今後しばらくは

```text
UI美化
```

よりも、

```text
Regional control capability
```

の増強を優先してください。

最終的に目指すのは、

```text
構図
人物配置
演技
背景
局所要素
```

を、漫画下絵として使える程度に段階的に誘導できる制作支援環境です。

Phase 3B.1では、そのための次の一歩として、

```text
Global / Panel / Character / Local Region
```

の4階層を意識した制御拡張を行ってください。
