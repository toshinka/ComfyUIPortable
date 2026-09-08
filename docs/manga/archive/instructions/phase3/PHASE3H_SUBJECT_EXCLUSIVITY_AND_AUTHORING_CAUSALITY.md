# ComfyUI Portable Phase 3H — Subject Exclusivity, Authoring Causality & Fast Draft Integration 指示書

## 0. 対象 / Baseline

対象:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
ae02361b0ae4b1d211c00d81112efa264cf30a12
```

Phase 3G では以下を維持します。

```text
PRIMARY REGIONAL BACKEND: IMPACT

CANONICAL VERIFY 25:
PASS

CANONICAL VERIFY 26:
PASS

CANONICAL VERIFY 27:
PASS

CANONICAL VERIFY 28:
PASS

REFERENCE MODE:
20-step Illustrious / Euler / Normal / CFG 7

FAST-12:
ACCEPT as Fast Draft

FAST-8:
REJECT

BROWSER POINTER E2E:
PENDING
```

ただし、Phase 3G の画像確認から新しい重要課題が見つかりました。

---

# 1. Phase名

```text
Phase 3H
Subject Exclusivity
&
Authoring Causality Bridge
&
Fast Draft Integration
```

内部:

```text
3H-0  Phase 3G Review Correction
3H-A  Base / Global Prompt Scope Separation
3H-B  Subject Exclusivity Verification
3H-C  Spatial Verification Overlay & Diagnostics
3H-D  Progressive Authoring → Impact Causality Bridge
3H-E  Fast-12 Generation Profile Integration
3H-F  ControlNet Assist Decision Gate
```

---

# 2. Phase 3Gの成果は有効。ただし表現を補正する

Workflow 25〜28 について、外部レビュー画像では以下が確認できました。

### 成立していること

```text
WF25 → WF26
Region Aを Top-Left → Bottom-Right に変更
↓
White Dogも大きく同方向へ移動
```

```text
WF27 → WF28
Dog / Cat Promptは固定
Region A/B geometryだけ左右Swap
↓
Dog / Catの左右関係も反転
```

したがって:

```text
DIRECTIONAL SPATIAL BINDING:
PROMISING / PASS
```

は維持してよい。

---

# 3. ただし「完全な位置制御」「Subject Exclusivity」はまだ未証明

外部レビュー画像では:

```text
WF25:
Dog以外に大きな少女像が背景側へ生成

WF26:
Dogは右下へ移動するが、別の少女像が大きく生成

WF27 / WF28:
Dog / Catの意味分離は概ね成立するが、
Scale / OccupancyはRegion矩形に厳密ではない。
Region外にも不要な線画・人物的要素が出る。
```

したがってPhase 3G報告の:

```text
strictly in the quadrant
pure geometric control
clean background
complete spatial control
```

等の強い表現があれば補正してください。

推奨表現:

```text
Directional placement causality demonstrated.

Subject semantics follow region geometry,
but strict containment, scale control,
and suppression of unintended subjects outside regions
remain unresolved.
```

---

# 4. 「背景の少女」はモデル癖だけと決めつけない

Illustriousの学習傾向による可能性はあります。

しかし現在のImpact構造では、

```text
Base Sampler
```

がRegion外を生成し、

Global / Base Promptが:

```text
manga illustration
high quality
simple background
```

等の広い意味を持つため、
Base側が独自に人物を生成する余地があります。

したがってこれは:

```text
MODEL PRIOR
+
BASE SAMPLER CONTENT POLICY
```

の両方を疑ってください。

---

# 5. 今回の中心概念 — Subject Exclusivity

Regional Authoringで必要なのは:

```text
「Region AにDogが出た」
```

だけではありません。

必要なのは:

```text
Region AにDogが出る
+
Dogを指定していないBase領域に
勝手なDog / Girl / Characterが増えない
```

です。

これを:

```text
SUBJECT EXCLUSIVITY
```

として正式な検証項目へ追加してください。

---

# 6. Global Promptを3つの責務へ整理

最終データSchemaを大改造する必要はありませんが、
compile-time責務として最低限以下を区別してください。

```text
GLOBAL STYLE
= manga style / monochrome / linework / quality

BASE SCENE
= background / environment / empty canvas behavior

REGIONAL SUBJECT
= Character / Object / local action
```

---

# 7. Global Styleは「Baseにだけ存在するPrompt」にしない

Global Styleは可能なら:

```text
Base
Panel Scene
Character Region
SubScene
```

すべてのconditioningへ共通appendする。

例:

```text
GLOBAL STYLE:
manga illustration, monochrome expressive linework
```

これは画風指示であり、

```text
少女を出す
犬を出す
```

等のSubject指示ではない。

---

# 8. Base SceneはSubjectを勝手に生成しない方向へ

Subject Verification時のBase候補:

```text
clean empty white background,
simple blank manga background,
no focal subject
```

Base Negative候補:

```text
person, human, girl, boy,
animal, dog, cat,
extra character, face, body
```

ただしこれを即Canonicalにしない。

まず比較してください。

---

# 9. Base SuppressionがRegional Subjectまで壊さないか確認

ImpactのBase sampler negativeが、
Region blend結果へどの程度影響するかは実機検証が必要です。

比較:

```text
MODE A:
Current Base

MODE B:
Subject-Suppressed Base
```

同Seed / 同Prompt / 同Geometry。

観察:

```text
Dog remains?
Cat remains?
Unexpected girl disappears?
Boundary worsens?
Background becomes unstable?
```

---

# 10. MODE Bで問題がある場合の代替

Baseを強くNegativeすることでRegional Subjectまで弱くなる場合:

```text
MODE C:
Neutral Base
+
Full-Canvas Scene Regional Prompt
+
Character Regions on top
```

を試す。

Phase 3Eで決定した:

```text
SCENE_FIRST
```

orderを利用。

---

# 11. 3H-B — Subject Exclusivity Verification Workflow

既存25〜28は保存し変更しない。

比較用として最大4本追加:

```text
29_VERIFY_SINGLE_A_TOP_LEFT_EXCLUSIVE_BASE.json
30_VERIFY_SINGLE_A_BOTTOM_RIGHT_EXCLUSIVE_BASE.json
31_VERIFY_TWO_REGION_DOG_CAT_LR_EXCLUSIVE_BASE.json
32_VERIFY_TWO_REGION_DOG_CAT_SWAP_EXCLUSIVE_BASE.json
```

---

# 12. Workflow29 / 30

25 / 26と以下を完全固定:

```text
model
seed
dog prompt
geometry
sampler
steps
CFG
Impact settings
```

変更:

```text
Base Scene policy only
```

期待:

```text
Dog directionality survives
+
unexpected girl/person/animal outside region decreases
```

---

# 13. Workflow31 / 32

27 / 28と同様。

期待:

```text
Dog / Cat LR + SWAP survives
+
third subject / unbound person disappears
+
background fragment contamination decreases
```

---

# 14. Subject Exclusivity Result

各Workflow:

```text
EXPECTED SUBJECT A:
present / missing

EXPECTED SUBJECT B:
present / missing / N/A

UNEXPECTED HUMAN:
yes / no / ambiguous

UNEXPECTED ANIMAL:
yes / no / ambiguous

DUPLICATE SUBJECT:
yes / no

CHIMERA:
yes / no

REGION DIRECTION:
correct / partial / wrong
```

をJSONへ。

---

# 15. 「背景に少女」が消えた場合

以下を結論にしてよい:

```text
Model prior contributed,
but Base Sampler content policy was a controllable source.
```

「モデル癖だから仕方ない」で終了しない。

---

# 16. 消えない場合

Base suppression後も同様の少女が安定して出る場合:

```text
Illustrious model prior / prompt prior
```

の寄与が強い可能性。

その時だけ別Checkpoint比較を小規模で行ってもよい。

Phase 3Hでモデル探索を広げすぎない。

---

# 17. Verification Contact Sheetを改善

今後の空間検証SheetはFinal Imageだけでなく:

```text
Target Region Map
|
Final Output
|
Evaluation Overlay
```

を並べる。

---

# 18. Evaluation Overlay

生成後のコピーへ半透明で:

```text
Region A outline
Region B outline
```

を重ねる。

これは評価用のみ。

生成入力へは影響させない。

---

# 19. Overlayの目的

人間/GPT/Geminiが:

```text
Subject centerはRegion内か
Subjectがどの程度Regionを越えているか
余計なSubjectはどこにいるか
```

を即座に判断できるようにする。

---

# 20. 厳密Containmentを要求しない

現段階の合格条件は:

```text
Subject center / main mass follows target region
```

です。

手・尻尾・髪などがRegion境界を越えること自体はFAILにしない。

---

# 21. ただしScale Controlは別項目として記録

WF27のように:

```text
Dog very large
Cat very small
```

でもDirectional Bindingは成立し得る。

したがって:

```text
POSITION:
PASS

SCALE FIDELITY:
PARTIAL
```

と分離して報告。

---

# 22. 3H-D — OracleからAuthoring Pipelineへ因果性を移す

25〜32は `Two Region Oracle` 系の検証です。

次に必要なのは:

```text
Cast
→ Panel Content
→ Character Staging
→ Impact Region Plan
→ RegionalSampler
```

という実制作経路そのものが
位置制御の正本になることです。

---

# 23. Progressive Authoring Causality Workflows

新規2本:

```text
33_VERIFY_AUTHORING_ALICE_LEFT_BOB_RIGHT.json
34_VERIFY_AUTHORING_ALICE_RIGHT_BOB_LEFT.json
```

---

# 24. Workflow33 / 34 共通条件

Visible Panels:

```text
1
```

Cast:

```text
Alice:
blonde twin tails

Bob:
short black hair
```

Scene:

```text
simple school courtyard,
two students standing
```

Promptへ:

```text
left
right
```

を書かない。

---

# 25. 33のStaging

```text
Alice Region:
left

Bob Region:
right
```

---

# 26. 34のStaging

Panel Content / Cast / Seedは完全同一。

変更:

```text
Alice / Bob Character Staging geometry only swap
```

期待:

```text
Alice / Bob positions also swap
```

---

# 27. これが重要な理由

33 / 34が成立すれば:

```text
TwoRegion experimental editorだけで位置制御できる
```

から、

```text
ユーザーが最終的に触るCharacter Stagingが
実際の生成位置へ因果的に接続されている
```

へ進めます。

これはPhase 3Hの重要Gateです。

---

# 28. Character Identity評価

Alice / Bobは動物ほど識別しやすくないため:

```text
hair color / style
gender
uniform
```

等を評価。

完全な顔同一性は今回要求しない。

---

# 29. Actingは固定

33 / 34では:

```text
standing calmly
```

程度に固定。

Interaction / Poseを同時に変えない。

今回は位置因果だけを見る。

---

# 30. 次のHostile Testは別Phase

以下は既に有望ですが、3Hで広げすぎない。

```text
same Alice/Bob
left subscene = arguing
right subscene = handshake
```

これは既存22/24を維持。

33/34でProduction Staging因果を先に確立。

---

# 31. Character Staging Browser Pointer

Phase 3Gでevent handlerは実装されていますが:

```text
BROWSER POINTER E2E:
PENDING
```

です。

可能ならGemini側で実ブラウザ確認。

不可能ならPENDING維持。

---

# 32. ユーザー手動確認の扱い

33 / 34のZero-Touch結果までAI側で判断できるなら、
ユーザーへ確認依頼しない。

Browser pointer E2Eだけ残る場合、
Phase終了後に必要ならGPTから:

```text
Workflow33を開き、
Alice矩形を少し右へドラッグし、
Save/Reloadで位置が残るか
```

の1テストだけ依頼できる状態にする。

途中でユーザーをテストランナーにしない。

---

# 33. Fast-12を正式に「Fast Draft Profile」として組み込む

Phase 3G結果:

```text
Hyper-SD 12-step:
ACCEPT

Hyper-SD 8-step:
REJECT
```

を維持。

---

# 34. ただしReferenceがSSOT

Canonical verification:

```text
REFERENCE_20
```

を正本とする。

Fast-12は:

```text
FAST_DRAFT_12
```

という明示的な別Profile。

---

# 35. Generation Profile Contract

新規軽量Contractまたは既存Global設定へ:

```text
generation_profile:
reference
fast_draft_12
```

程度を追加してよい。

Impact / Cast / Panel schemaには混ぜない。

---

# 36. Profile内容

### reference

```text
No Hyper-SD
20 steps
CFG 7
Euler / Normal
```

### fast_draft_12

```text
Hyper-SDXL-12steps-CFG-lora
12 steps
CFG 6
validated sampler / scheduler
```

Phase 3G実測設定を正本にする。

---

# 37. Asset pathはabsolute pathを永続保存しない

ローカル実体:

```text
D:\Models\Lora\調整\Hyper-SDXL-12steps-CFG-lora.safetensors
```

は発見済み。

永続Workflow / Contractでは可能なら
ComfyUI search path上の相対asset名を使用。

ファイルをGitへ追加しない。

---

# 38. Fast-8はUIへ出さない

Fast-8はPhase 3GでREJECT。

研究用記録は残すが、
通常のGeneration Profile候補へ表示しない。

---

# 39. Fast DraftでSubject Exclusivityを再確認

29〜34のReferenceがPASSした後、
代表2ケースのみFast-12で確認。

推奨:

```text
32 Dog/Cat SWAP
34 Alice/Bob Authoring SWAP
```

---

# 40. Fast Draft Acceptance

Fast-12で:

```text
Subject Exclusivity regression
Tile seam
Character clipping
Position inversion failure
```

がなければ:

```text
FAST DRAFT PROFILE:
READY
```

とする。

---

# 41. Fast DraftはControlNetなしでまず確認

今回:

```text
Hyper-SD + Impact
```

まで。

ControlNetを同時追加しない。

原因分離を維持。

---

# 42. ControlNet Assist Decision Gate

Phase 3H終了時に以下を判断。

### Case A

```text
Position direction:
good

Subject exclusivity:
good

Scale / exact placement:
acceptable
```

ならControlNet位置補助は後回し。

次:

```text
Production Authoring UX
Panel Tool
Preset foundation
```

---

# 43. Case B

```text
Identity separation:
good

Direction:
good

But:
scale unstable
subject center often misses target
character overlap relation difficult
```

なら次Phase:

```text
Character / Scene Layout ControlNet Assist
```

を優先。

---

# 44. ControlNetの役割を限定する

ControlNetは:

```text
Prompt分離の代用品
```

にしない。

役割:

```text
position
scale
pose
rough composition
panel geometry
```

の幾何補助。

---

# 45. Clip Studio風Panel Slicerはまだ後段

既存Panel Layout Editorは維持。

最終的には:

```text
drag split line
shared handles
panel frame edit
ControlNet guide
```

へ育てる。

Phase 3HではUI polishしない。

---

# 46. Canonical Verification Rule継続

新規Workflowも:

```text
1 Workflow = 1 Hypothesis
Zero-Touch
Fixed Seed
No user parameter switching
```

を守る。

---

# 47. Zero-Touchは常設Gate

新規29〜34:

```text
saved workflow live schema valid
validation errors = 0
output exists
```

必須。

---

# 48. Evaluation Tier継続

### Level 1
自動。

### Level 2
Gemini / GPT image review。

### Level 3
ユーザーは必要時のみ。

---

# 49. Phase 3H Report

新規:

```text
PHASE3H_SUBJECT_EXCLUSIVITY_AND_AUTHORING_CAUSALITY_REPORT.md
```

最低限:

```text
1. Phase3G Review
2. External Screenshot Review
3. Claim Corrections
4. Unexpected Girl / Subject Leakage Analysis
5. Base / Global Prompt Scope
6. Subject Exclusivity Contract
7. Current Base Baseline
8. Exclusive Base Mode
9. Workflow29
10. Workflow30
11. Workflow31
12. Workflow32
13. Region Overlay Contact Sheet
14. Subject Exclusivity Metrics
15. Position vs Scale Fidelity
16. Authoring Pipeline Causality
17. Workflow33
18. Workflow34
19. Character Staging → Impact Mapping
20. Browser Pointer E2E
21. Fast Draft Profile
22. Fast-12 Regression Check
23. Reference SSOT
24. ControlNet Assist Decision
25. Known Issues
26. User Review Requirement
27. Next Phase
28. Gemini独自判断
```

---

# 50. Sign-off

```text
PHASE3G REVIEW CLOSURE:
PASS / HOLD

DIRECTIONAL BINDING:
PASS / HOLD

SUBJECT EXCLUSIVITY:
PASS / PARTIAL / HOLD

UNEXPECTED SUBJECT LEAK:
RESOLVED / REDUCED / UNRESOLVED

POSITION FIDELITY:
PASS / PARTIAL

SCALE FIDELITY:
PASS / PARTIAL

AUTHORING STAGING CAUSALITY:
PASS / HOLD

WORKFLOW29:
PASS / HOLD

WORKFLOW30:
PASS / HOLD

WORKFLOW31:
PASS / HOLD

WORKFLOW32:
PASS / HOLD

WORKFLOW33:
PASS / HOLD

WORKFLOW34:
PASS / HOLD

BROWSER POINTER E2E:
PASS / PENDING

REFERENCE PROFILE:
READY / HOLD

FAST DRAFT 12:
READY / CONDITIONAL / HOLD

FAST 8:
REJECTED

CONTROLNET POSITION ASSIST:
NEXT / DEFERRED

USER VISUAL REVIEW REQUIRED:
YES / NO

NEXT RECOMMENDED PHASE:
```

---

# 51. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3H Subject Exclusivity and Authoring Causality
```

内容:

```text
base/global scope separation
subject exclusivity verification
overlay diagnostics
workflows 29-34
authoring staging causality
fast draft profile
tests
report
```

Commit A SHA取得後、
Navigation Commit Bで:

```text
ComfyUIPortable/GITHUB.TXT
```

のReview TargetをCommit Aへ。

---

# 52. GITHUB.TXTへ追加

最低限:

```text
Phase3H report
Base / global compile logic
Subject exclusivity test
Overlay generator
Workflow29-34
Generation Profile contract
Fast Draft regression test
```

---

# 53. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3H_SUBJECT_EXCLUSIVITY_AND_AUTHORING_CAUSALITY_REPORT Raw:

Base Prompt Scope Raw:
Subject Exclusivity Test Raw:
Overlay Generator Raw:
Generation Profile Raw:

Workflow29 Raw:
Workflow30 Raw:
Workflow31 Raw:
Workflow32 Raw:
Workflow33 Raw:
Workflow34 Raw:

PHASE3G REVIEW CLOSURE:
DIRECTIONAL BINDING:
SUBJECT EXCLUSIVITY:
UNEXPECTED SUBJECT LEAK:
POSITION FIDELITY:
SCALE FIDELITY:
AUTHORING STAGING CAUSALITY:
BROWSER POINTER E2E:
REFERENCE PROFILE:
FAST DRAFT 12:
CONTROLNET POSITION ASSIST:
USER VISUAL REVIEW REQUIRED:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3Gで最も重要だった成果は:

```text
Promptに左右を書かず、
Region geometryだけで
Dog / Catの左右関係を変えられた
```

ことです。

これは維持します。

しかし次に必要なのは:

```text
指定したSubjectが指定Regionへ行く
```

だけでなく、

```text
指定していないSubjectが
Region外へ勝手に増えない
```

ことです。

また、実験用TwoRegion Oracleで成立した空間制御を、
最終ユーザー導線である:

```text
Cast
→ Panel Content
→ Character Staging
→ Impact
```

へ移す必要があります。

Phase 3Hではこの2点を中心にしてください。

Hyper-SD 12-stepは既に十分有望なので、
Referenceを壊さない `Fast Draft Profile` として組み込みます。

ControlNet位置補助はまだ自動採択しません。

Subject ExclusivityとAuthoring Stagingの位置因果を確認した後、
「方向は合うがScale / exact positionが弱い」と判定された場合に、
次PhaseでCharacter / Scene Layout Assistとして導入してください。
