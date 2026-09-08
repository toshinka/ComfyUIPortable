# ComfyUI Portable Phase 3D.2 — Regional Semantics First
## Single-Region Placement → Two-Region Separation → Impact Comparison → Optional Layout Assist 指示書

## 0. 対象 / Baseline

対象環境:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
13e6e6b988dc2edf596c8ad5f73bd00c8f3de43a
```

Phase 3D.1 では以下が成立しました。

```text
CAST_SPEC / Cast Master Foundation
Variable N-Panel Mapping
Polygon Panel Conditioning
Character / Local Semantic Masks
Panel Layout ControlNet
Workflow 17
5-Panel Actual Generation
```

一方、実画像局所性評価では:

```text
CORE PANEL LOCALITY: PARTIAL
CORE CHARACTER LOCALITY: PARTIAL
```

でした。

本Phaseでは、漫画ページ全体の体裁・CAST UI・コマ数拡張をいったん主役から外します。

次に確認すべき最重要課題は、

```text
「明示的に指定した矩形へ、
その矩形に対応するPromptの対象を
本当に移動・分離できるか」
```

です。

この能力を最小構成で先に確立してください。

---

# 1. 今回の設計判断

今後の制御を3層へ明確に分離します。

```text
A. Semantic Region
   Prompt / Character / Object を
   「この辺へ出したい」と指定する意味領域

B. Regional Backend
   Core Masked Conditioning
   Impact RegionalSampler
   将来の別Backend

C. Geometric Assist
   ControlNetによる位置・構図補助
   漫画コマ割り
```

重要な順序は:

```text
Semantic Regionが意味を分離できる
↓
Semantic Regionが位置を誘導できる
↓
必要ならControlNetで位置を補助
↓
その後に漫画コマへ統合
```

です。

---

# 2. 今回は「漫画らしい成果物」を目標にしない

Workflow 17のような:

```text
3コマ漫画
Cast Master
Panel Layout
ControlNet
複数Preview
```

は既存成果として残します。

ただしPhase 3D.2の研究Workflowでは、

```text
漫画ページらしく見えること
```

をAcceptance Criteriaにしないでください。

今回必要なのは:

```text
指定矩形
Prompt
生成結果
```

の因果関係が明確であることです。

既存のCast Master / Workflow16 / Workflow17 / Panel Layout Editor / 5-Panel生成はRegression維持のみとし、UI Polishを追加しないでください。

---

# 3. 最初の関門 — Single Semantic Region Placement

最初に、

```text
Canvas全体
+
Semantic Region A 1個
+
Prompt A
```

だけの実験を行います。

Region Bはdisabled。

既存 `TWO_REGION_SPEC` を再利用し、Single Region Modeでは:

```text
A.enabled = true
B.enabled = false
```

としてください。

---

# 4. Two Region EditorをSemantic Control UIの正本にする

既存:

```text
Tegaki Two Region Couple Editor
```

をRegional Prompt研究UIとして使用してください。

必要なら表示名を:

```text
Tegaki Semantic Region Oracle Editor
```

へ変更しても構いませんが、内部TWO_REGION_SPEC互換を維持してください。

ノード上で最低限以下を明確に表示:

```text
Canvas Width
Canvas Height
Region A Prompt
Region A Negative
Region B Prompt
Region B Negative
Region A Enabled
Region B Enabled
Canvas Preview
```

Canvasは指定解像度のアスペクト比を反映。

固定Identity:

```text
Region A = Blue
Region B = Orange
```

Prompt欄の見出しも対応させ、Canvas上には短いPrompt previewを表示してください。

---

# 5. Semantic Regionの操作は実際に機能すること

最低限:

```text
矩形内部drag → Move
handle drag → Resize
空白drag → Create/Reposition
Disable
Reset
```

を実際に機能させてください。

今回の主役です。

見た目だけHandleを描いて操作不能、は不可。

Gemini自身で可能な範囲で:

```text
Aを右上へ移動
Save Workflow
Reload
位置維持

Aを左下へ移動
Save Workflow
Reload
位置維持
```

を確認してください。

Browser automationが無い場合も、Frontend event pathをコード上確認し、実操作未確認なら明記してください。

---

# 6. Workflow 18 — Single Region Placement Oracle

新規:

```text
18_SINGLE_REGION_PLACEMENT_CORE_VS_IMPACT_ORACLE.json
```

区分:

```text
EXPERIMENTAL / REGIONAL SEMANTICS ORACLE
```

同じ:

```text
Model
Seed
Prompt
Region A geometry
```

から、

```text
Core Masked Conditioning branch
Impact RegionalSampler branch
```

を比較できるHarnessを推奨します。

複雑すぎる場合は:

```text
18A_SINGLE_REGION_CORE_ORACLE.json
18B_SINGLE_REGION_IMPACT_ORACLE.json
```

へ分けて構いません。

Base / Global PromptにはSubjectを入れない。

例:

```text
masterpiece, simple clean outdoor background, full composition
```

Negative:

```text
worst quality, bad anatomy, duplicate subject
```

Subject Promptは最初:

```text
a white dog, full body
```

または:

```text
1girl, red dress, full body
```

のどちらか1種類で十分です。

---

# 7. Single Region Placement Matrix

固定SeedでRegion Aを:

```text
Top Left
Top Right
Bottom Left
Bottom Right
Center
```

へ移動。

サイズ例:

```text
w=.35
h=.45
```

Core 5枚、Impact 5枚を生成。

各画像について:

```text
SubjectがRegion方向へ移動したか
Subject centerが指定Region内/近傍か
duplicate subject
subject missing
outside-region contamination
background破綻
```

を記録。

「完全にRegion内へ収容」は最初から要求しません。

Acceptanceは:

```text
Region位置を変えると
Subject位置も方向的に追従する
```

ことです。

---

# 8. Directional Placement Score

Geminiが画像を視覚確認できる場合:

```text
Expected: TL/TR/BL/BR/C
Observed: TL/TR/BL/BR/C/ambiguous
```

を記録。

目安:

```text
4/5以上 → PROMISING
2〜3/5 → PARTIAL
0〜1/5 → INSUFFICIENT
```

研究Gateとして使用してください。

Phase 3D.1のMeanDiffだけではなく、今回は「Region geometryを動かした時にSubject位置が動くか」を主評価にします。

---

# 9. Core vs Impact

CoreはFallbackとして維持。

```text
Core = low dependency baseline / fallback
```

Impact RegionalSamplerをPrimary Candidateとして再評価します。

既存:

```text
TegakiTwoRegionImpactAdapter
Workflow 12
```

を再利用してください。

Runtimeの:

```text
RegionalSampler
KSamplerAdvancedProvider
REGIONAL_PROMPT
```

API / object_info / zero-touchを再確認。

Single Region終了時:

```text
CORE SINGLE-REGION POSITION:
PROMISING / PARTIAL / INSUFFICIENT

IMPACT SINGLE-REGION POSITION:
PROMISING / PARTIAL / INSUFFICIENT
```

を出してください。

---

# 10. 第二関門 — Two-Region Semantic Separation

Single Regionの次に:

```text
Region A
Region B
Prompt A
Prompt B
```

へ進みます。

最初はDog / Cat。

A:

```text
a white dog, full body
```

B:

```text
a black cat, full body
```

Global:

```text
simple park background, two subjects
```

---

# 11. Dog / Cat Test Matrix

### Test 1 — Left / Right

```text
A = left
B = right
```

期待:

```text
white dog mostly left
black cat mostly right
```

### Test 2 — Geometry Swap

Promptは一切変更しない。

```text
A = right
B = left
```

期待:

```text
dog / cat位置も入れ替わる
```

位置語をPromptへ書かないこと。

これは本Phaseで最重要の位置制御試験です。

### Test 3 — Vertical

```text
A = top
B = bottom
```

### Test 4 — Overlap

```text
A/B 30〜40% overlap
```

観察:

```text
identity merge
duplicate
attribute bleed
physical interaction
```

---

# 12. Man / Woman Test

Dog/Catで十分な結果が出たBackendに対し:

A:

```text
1man, black hair, dark jacket
```

B:

```text
1woman, blonde hair, light dress
```

を実施。

左右配置とGeometry Swapを行い、Promptへleft/rightを書かない。

Couple / Interaction TestではGlobal Promptへ:

```text
two people standing close together, friendly conversation
```

を入れ、A/B Regionを重ねます。

目的:

```text
人物Identityを分けつつ
interactionを維持できるか
```

です。

---

# 13. Two-Region評価

最低限:

```text
Subject A identity correct
Subject B identity correct
A position correct
B position correct
attribute bleed
fusion
duplicate
missing
```

Backend結果:

```text
CORE TWO-REGION BINDING:
PROMISING / PARTIAL / INSUFFICIENT

IMPACT TWO-REGION BINDING:
PROMISING / PARTIAL / INSUFFICIENT
```

優先順位:

```text
1. Position direction
2. Identity separation
3. Attribute leakage
4. Interaction preservation
5. Seam / artifact
6. Runtime
7. Complexity
```

画質だけで決めないでください。

---

# 14. ここで初めてControlNet Assistを検討

過去ReForge系の研究順:

```text
White Dog / Black CatをPromptで分離
↓
Identityは分離する
↓
しかし位置関係が弱い
↓
ControlNetで配置を補助
```

を今回も再現できるようにします。

この順序は合理的です。

---

# 15. ControlNetは最初から漫画コマ枠にしない

最初のControlNet Assistは:

```text
3〜5コマ漫画
```

ではありません。

TWO_REGION_SPECから:

```text
simple layout guide
```

を生成します。

例:

```text
white background
black rectangle/block A
black rectangle/block B
```

No labels。

利用可能なControlNetモデルを監査し、単純線/ブロックが適する場合だけ使用。

---

# 16. Layout Assistを使う条件

Regional Backend単体で:

```text
位置が4/5以上安定
```

ならControlNet Assistは後回しでも構いません。

位置が弱い場合のみ:

```text
Regional Backend
+
Region Layout ControlNet
```

をテスト。

---

# 17. Workflow 19 / 20

新規:

```text
19_TWO_REGION_SEMANTIC_BINDING_ORACLE.json
```

推奨Backendで:

```text
Dog/Cat
Man/Woman
Geometry Swap
Overlap
```

を確認。

必要な場合のみ:

```text
20_TWO_REGION_LAYOUT_ASSIST_ORACLE.json
```

構成:

```text
Semantic Region Editor
↓
Chosen Regional Backend
+
Same Region Geometry → ControlNet Guide
↓
Sampler
```

Workflow 20の目的は漫画ページ生成ではなく:

```text
「分離したPrompt」
+
「分離した位置」
```

の成立です。

---

# 18. 既存Panel Layout / Cast Masterは主役にしない

既存:

```text
Tegaki Manga Panel Layout Editor
Cast Master
Workflow 16
Workflow 17
```

は維持。

Phase 3D.2では:

```text
Cast UI Polish
Appearance UI拡張
LoRA UI拡張
漫画Preview追加
```

を行わない。

Backend決定後に再開します。

---

# 19. 漫画Panelへ戻るGate

以下が揃ってから:

```text
Single Region Position PASS
Two Region Identity Binding PASS
Two Region Position PASS
```

そのBackendを:

```text
Panel Prompt
Character Region
Manga Panel Layout
Cast Master
```

へ再統合します。

---

# 20. Debug / Previewを整理

今回の研究Workflowでは:

```text
Mask Preview
Region Preview
Final Image
Backend Compare
```

以外のPreviewを極力増やさない。

Single Region debug:

```text
Region A normalized rect
Region A pixel rect
Prompt A
Backend
Seed
```

Two Region debug:

```text
A rect
B rect
overlap ratio
Prompt A
Prompt B
Backend
```

「成果物らしく見える」より因果関係を優先。

---

# 21. Contact Sheet

Runtime outputへ以下を生成。

### Single Region

```text
TL | TR
BL | BR
C
```

### Two Region

```text
Left/Right
Swapped
Vertical
Overlap
```

可能ならCore / Impactを横並び。

Gitへ大量画像は追加しない。

---

# 22. 自動評価と視覚評価を分離

自動:

```text
mask geometry
output exists
seed fixed
runtime
region mapping
```

視覚:

```text
subject position
identity
attribute bleed
interaction
```

Pixel MeanDiffは補助に留め、Subject Position / Identity Bindingを主評価にしてください。

---

# 23. 新規Tests

最低限:

```text
scripts/test_single_region_oracle_contract.py
scripts/test_single_region_core_runtime.py
scripts/test_single_region_impact_runtime.py
scripts/test_two_region_geometry_swap.py
scripts/test_two_region_backend_runtime.py
```

ControlNet Assist時:

```text
scripts/test_two_region_layout_assist.py
```

Single Region Contract:

```text
B disabled
A move
A resize
A preset TL/TR/BL/BR/C
save/reload
mask follows rect
prompt mapping stable
```

Geometry Swap Test:

```text
Prompt A/B unchanged
A/B geometry swapped
mask centers swapped
backend receives swapped masks
```

---

# 24. Runtime / UI Test

各Workflow:

```text
load
no touch
Queue
image
```

Two Region Editor:

```text
drag
resize
save
reload
```

についてGemini環境で可能なら実ブラウザ確認。

不可ならコード確認 + `BROWSER INTERACTION PENDING` を記録。

---

# 25. Acceptance — Single Region

```text
[ ] 指定解像度でCanvas aspect変化
[ ] Region Aが明示表示
[ ] Prompt Aが明示表示
[ ] A dragが機能
[ ] A resizeが機能
[ ] Save/Reload位置維持

[ ] TL generation
[ ] TR generation
[ ] BL generation
[ ] BR generation
[ ] Center generation

[ ] Core評価
[ ] Impact評価
```

---

# 26. Acceptance — Two Region

```text
[ ] A/B Prompt分離
[ ] A/B Rect分離
[ ] A/B overlap可能

[ ] Dog/Cat LR
[ ] Dog/Cat geometry swap
[ ] Dog/Cat vertical
[ ] Dog/Cat overlap

[ ] Man/Woman LR
[ ] Man/Woman geometry swap
[ ] Couple overlap

[ ] identity bleed評価
[ ] position評価
```

---

# 27. Acceptance — Optional Layout Assist

必要な場合:

```text
[ ] Region geometryからGuide
[ ] CN OFF
[ ] CN ON
[ ] same seed
[ ] position improvement評価
[ ] semantic separation維持評価
```

---

# 28. Backend選定結果

報告書末尾:

```text
CORE SINGLE-REGION POSITION:
PROMISING / PARTIAL / INSUFFICIENT

IMPACT SINGLE-REGION POSITION:
PROMISING / PARTIAL / INSUFFICIENT

CORE TWO-REGION BINDING:
PROMISING / PARTIAL / INSUFFICIENT

IMPACT TWO-REGION BINDING:
PROMISING / PARTIAL / INSUFFICIENT

LAYOUT ASSIST:
HELPFUL / NEUTRAL / HARMFUL / NOT NEEDED

PRIMARY REGIONAL BACKEND:
CORE / IMPACT / HYBRID / UNDECIDED

MANGA REINTEGRATION:
GO / HOLD
```

---

# 29. 次Phase分岐

### A. Impact単体でPosition + Identityが十分

次:

```text
Phase 3E
Chosen Regional Backend → Manga Panel / Character Integration
```

ControlNetは漫画Panel framing用途へ。

### B. ImpactでIdentityは良いがPositionが弱い

標準候補:

```text
Impact RegionalSampler
+
Region Layout ControlNet
```

### C. Coreが同等以上

Coreを維持し、Impact依存を増やさない。

### D. どちらも弱い

次Backend比較:

```text
DenseDiffusion
Omost
later RLL
```

---

# 30. Phase 3Eで漫画ページへ戻す

Backend決定後:

```text
通常3〜5 panels
最大6 capacity

Panel Prompt
Character Semantic Region
Local Region
Cast Master
Panel Layout ControlNet
```

へ戻します。

---

# 31. Phase 3D.2報告書

新規:

```text
PHASE3D_2_REGIONAL_SEMANTICS_FIRST_REPORT.md
```

最低限:

```text
1. Phase3D.1 Review Summary
2. Why Manga Formatting Was Deprioritized
3. Semantic Region UI
4. Single Region Interaction
5. Single Region Core Test
6. Single Region Impact Test
7. Five-Position Contact Sheet
8. Single Region Backend Evaluation
9. Dog/Cat Two-Region
10. Geometry Swap
11. Vertical Test
12. Overlap Test
13. Man/Woman Test
14. Couple Interaction
15. Identity Leakage
16. Position Binding
17. Core vs Impact
18. Layout Assist Decision
19. ControlNet Assist Test
20. Existing Workflow Regression
21. Primary Backend Decision
22. Manga Reintegration Gate
23. Known Issues
24. Next Phase
25. Gemini独自判断
```

---

# 32. Existing Regression

最低限:

```text
11
12
16
17
```

を壊さない。

Workflow Indexへ:

```text
18 = Single Region placement / backend comparison
19 = Two Region semantic binding
20 = optional layout assist
```

を追加。

---

# 33. ユーザー確認Gate

Phase途中でユーザー確認を求めなくて構いません。

次にユーザーへ見せるべきものは:

```text
Single Region Contact Sheet
Two Region Dog/Cat Contact Sheet
Two Region Man/Woman Contact Sheet
Core vs Impact comparison
ControlNet Assist comparison（必要なら）
```

です。

漫画ページの完成見本ではありません。

---

# 34. GITHUB.TXT 二段Commit

まず:

```text
Commit A
Phase 3D.2 Regional Semantics First
```

として:

```text
UI fixes
comparison workflows
runtime tests
contact sheet generator
report
```

をcommit。

そのSHA取得。

Navigation commitで:

```text
Review Target Commit SHA: A
```

へ更新。

Latest:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB.TXT
```

---

# 35. 最終回答

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3D_2_REGIONAL_SEMANTICS_FIRST_REPORT Raw:

Semantic Region Editor Raw:
Semantic Region Editor JS Raw:
Core Oracle Raw:
Impact Adapter Raw:
Layout Assist Raw: (if used)

Workflow 18 Raw:
Workflow 19 Raw:
Workflow 20 Raw: (if created)

Single Region Contract Test Raw:
Core Runtime Test Raw:
Impact Runtime Test Raw:
Geometry Swap Test Raw:
Layout Assist Test Raw: (if created)

CORE SINGLE-REGION POSITION:
IMPACT SINGLE-REGION POSITION:
CORE TWO-REGION BINDING:
IMPACT TWO-REGION BINDING:
LAYOUT ASSIST:
PRIMARY REGIONAL BACKEND:
MANGA REINTEGRATION:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 最終方針

現在の問題は、

```text
漫画らしいページを生成できるか
```

ではありません。

先に必要なのは:

```text
「このPromptを、この矩形へ」
```

が実際に成立することです。

最小Gate:

```text
1 Region
↓
Prompt対象を右上・左下へ動かせる

2 Regions
↓
White Dog / Black Catを分離
↓
GeometryだけSwapすると位置もSwap

Man / Woman
↓
Identityを分離
↓
Overlapではinteractionを許す
```

ここまでをRegional Backend単体で確認してください。

その後、

```text
Identityは分かれるが位置が弱い
```

なら、

```text
Regional Backend
+
ControlNet Layout Assist
```

を追加します。

さらにその後に初めて、

```text
漫画Panel Layout
3〜5コマ
Cast Master
Character Regions
```

へ戻してください。

つまり今後の順序は:

```text
Prompt Separation
→ Position Binding
→ Optional ControlNet Geometric Assist
→ Manga Panel Integration
```

を基本とします。

既存のPanel Layout / Cast Master開発は無駄ではありません。
それらはBackendが決まった後に再利用します。

Phase 3D.2では、
「それっぽい漫画成果物を見せること」より、
「指定矩形と生成内容の因果関係を証明すること」
を最優先にしてください。
