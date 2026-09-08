# ComfyUI Portable Phase 3I.2 — Reference/Fast Causal Isolation, Per-Region Control Hint & True Browser Gate 指示書

## 0. 対象 / Baseline

対象:

```text
D:\GitHub\tegaki\ComfyUIPortable
```

Review Target baseline:

```text
cfe6a4fa38eedb199b8230bba85a2000331e7e5a
```

Phase 3I.1 で成立したものは維持します。

```text
Runtime PASS / Visual Semantic PASS の分離
ControlNet conditioning = BASE_ONLY の監査
propagate_controlnet_to_regions prototype
WF40〜43
Fast Draft 12 + CN の有望性
Guide SSOT contract
Visual evaluation / Contact Sheet framework
```

ただし、Phase 3I.1 の結果から新しい重要課題が見つかりました。

```text
Native Reference 20-step + Base-Only CN:
人物が消失しやすい

Fast Draft 12 + Hyper-SDXL + CN:
Alice / Bob の双方が成立する

Regional CN propagation:
人物は出るが、同じGlobal Guideを各Regionalへ渡すため
強いMannequin過拘束が発生
```

したがって Adaptive Guide / Camera / Pose UI へ進む前に、
「なぜFast-12だけ成立するのか」と
「Regional ControlNetをどう伝播すべきか」を小さく切り分けます。

---

# 1. Phase名

```text
Phase 3I.2
Reference / Fast Causal Isolation
&
Per-Region Control Hint Prototype
&
True Browser Interaction Gate
```

内部:

```text
3I.2-0  Phase 3I.1 Review Correction
3I.2-A  Browser Test Naming Correction
3I.2-B  Visual Evaluation Provenance
3I.2-C  Native20 vs Native12 vs Hyper12 Causal Ablation
3I.2-D  Impact base_only_steps Ablation
3I.2-E  Shared Global CN vs Per-Region Hint
3I.2-F  Attenuated Regional CN
3I.2-G  Operational Profile Decision
3I.2-H  True Browser E2E Gate
```

---

# 2. Phase 3I.1の評価

以下は受理します。

```text
WF35 Visual: FAIL
WF36 Visual: FAIL
WF37 Visual: FAIL
WF38 Visual: FAIL
WF39 Visual: PASS

Control metadata default:
BASE_ONLY

Regional propagation prototype:
実装済み

Fast Draft 12 + CN:
PROMISING / Draft candidate
```

一方、

```text
PHASE3J: GO
```

は一旦保留。

Native ReferenceとFast-12の挙動差が大きすぎるため、
原因分離を先に行ってください。

---

# 3. 「Browser Pointer E2E: PASS」を名称修正

現:

```text
scripts/test_character_staging_browser_pointer.py
```

は実ブラウザを起動してDOM / LiteGraph canvasへpointer eventを送るテストではありません。

内容は:

```text
SimulatedBrowserPointerSession
```

によるJavaScriptロジックのPython再現
+
backend causality
+
Guide SSOT
```

です。

したがって正確な名称:

```text
POINTER CONTRACT SIMULATION:
PASS

BACKEND GUIDE SSOT:
PASS

LIVE BROWSER POINTER E2E:
PENDING
```

としてください。

報告書・Manifest・GITHUB.TXTで
`Browser Pointer E2E PASS` と断定しないこと。

---

# 4. テストファイル名

既存ファイルを破壊的renameする必要はありませんが、
report上は:

```text
test_character_staging_browser_pointer.py
= Pointer Contract Simulation Test
```

と説明。

可能なら次回整理時に:

```text
test_character_staging_pointer_contract.py
```

へ名称変更してもよい。

---

# 5. Visual Evaluation Provenanceを明示

現:

```text
generate_phase3i1_visual_evaluation.py
```

は画像認識を実行するスクリプトではなく、
既に行われた視覚判断・BBox推定値をJSONへ固定出力する
「annotation generator」です。

したがって:

```text
MACHINE VISION MEASURED
```

と扱わない。

正確には:

```text
AI / MANUAL VISUAL ANNOTATION
```

です。

JSON metadataに:

```json
{
  "evaluation_source": "AI_VISUAL_ANNOTATION",
  "measurement_method": "approximate_manual_bbox",
  "machine_detector": false
}
```

等を追加してください。

---

# 6. BBox数値の扱い

以下は近似値:

```text
[0.08, 0.12, 0.40, 0.85]
```

です。

Pixel detector等で算出していない場合:

```text
approx_bbox
```

の名称を維持し、
precision metricとして過大利用しない。

---

# 7. 最大の疑問 — なぜFast-12だけ成功するのか

現状:

```text
WF38
Native Illustrious
20 steps
CFG 7
Base-Only CN
→ Alice missing

WF39
Hyper-SDXL LoRA
12 steps
CFG 6
Base-Only CN
→ Alice + Bob both present
```

差分が複数あります。

```text
Hyper-SDXL LoRA
20 → 12 steps
CFG 7 → 6
sampling dynamics
```

したがって、

```text
Hyper-SDが「単なる高速化」
```

という前提はまだ確定していません。

むしろ現在のCN + Regional構成において
semantic survivalを改善している可能性があります。

---

# 8. Causal Ablation Matrix

同じ:

```text
seed
prompt
staging
ControlNet guide
CN strength/end
Regional masks
Alice/Bob
```

を固定。

最小4条件:

### A — Native Reference
```text
No Hyper
20 steps
CFG 7
base_only_steps = current
```

### B — Native Short
```text
No Hyper
12 steps
CFG 6
base_only_steps = current
```

### C — Native CFG Control
```text
No Hyper
20 steps
CFG 6
base_only_steps = current
```

### D — Hyper 12
```text
Hyper-SDXL 12-step
12 steps
CFG 6
base_only_steps = current
```

目的:

```text
step reduction
CFG reduction
Hyper LoRA
```

のどれが人物survivalに効いているかを見る。

---

# 9. Optional 5th Ablation

必要な場合のみ:

```text
Hyper-SDXL LoRA
20 steps
CFG 6
```

を追加。

ただしHyper-SD本来の推奨運用外なら、
結果はdiagnostic限定と明記。

---

# 10. Impact base_only_stepsを切り分ける

RegionalSamplerの初期Base-only期間が
背景latentを強く固定し、
後段Regional Promptが人物を復元できなくしている可能性があります。

同一Native20条件で:

```text
base_only_steps = 2  (current)
base_only_steps = 0
```

を比較。

必要なら:

```text
base_only_steps = 1
```

も追加。

---

# 11. Base-only Steps Gate

もし:

```text
Native20 / base_only_steps 2:
FAIL

Native20 / base_only_steps 0:
PASS
```

なら、根本問題はTurboではなく
Impact sampling scheduleの可能性が高い。

この場合Hyper-SDをsemantic fixとして扱わない。

---

# 12. Ablation Outcome分類

報告:

```text
SEMANTIC SURVIVAL DRIVER:

HYPER_LORA
STEP_COUNT
CFG
BASE_ONLY_STEPS
MIXED
UNRESOLVED
```

---

# 13. Reference SSOT Policyを条件付き再評価

現在:

```text
Reference 20-step = permanent SSOT
```

ですが、主要Authoring taskでReferenceが恒常的にFAILし、
Hyper-12だけが成功するなら、

```text
Reference = Architectural Regression Profile
```

と:

```text
Operational Authoring Profile
```

を分けることを検討。

例:

```text
ARCHITECTURE_REFERENCE:
Native20

AUTHORING_STABLE:
Hyper12
```

ただしPhase 3I.2のAblation結果が出るまで変更しない。

---

# 14. Regional ControlNet Propagationの現在の構造

現prototypeは:

```text
base_sampler.params[4] の "control" object
```

を取り出し、
**同じControl object / same global guide hint** を
各Regional positive conditioningへ付与しています。

これはControl metadataの伝播確認としては正しい実験です。

しかし、

```text
Alice region
Bob region
```

の各Regional samplerに
同じ2人物Global Guideを見せるため、
個体別Controlとしてはまだ粗い。

---

# 15. WF42のMannequin過拘束の原因仮説

WF42で:

```text
両regionがfull scale
しかしliteral mannequin / framed artifact
```

になった原因は、

```text
strength .75
end .80
```

だけでなく、

```text
each regional sampler receives the entire global guide
```

である可能性があります。

したがって、単純にstrengthだけ下げて本実装へ進まない。

---

# 16. Per-Region Hint Prototype

新prototype:

```text
regional_control_mode:
off
shared_global
per_region_hint
```

を検討。

Default:

```text
off
```

維持。

`shared_global` は現Phase 3I.1 prototype。

`per_region_hint` は実験専用。

---

# 17. Per-Region Hintの作り方

Character Instanceごとに:

```text
same staging geometry SSOT
→ character-only guide
```

を生成。

例:

```text
Alice Regional Sampler
→ Alice mannequin only

Bob Regional Sampler
→ Bob mannequin only
```

Panel borderや他Character mannequinを含めない。

---

# 18. Guide SSOT

必ず:

```text
Character Staging area
```

から、

```text
Impact mask
Global ControlNet guide
Per-region ControlNet guide
```

を派生。

別座標の手書き禁止。

---

# 19. Control objectの安全なclone

`control` object内部APIを推測で直接書き換えない。

実Runtime classをinspectし:

```text
copy()
set_cond_hint()
strength
timestep_range
previous_controlnet
```

等の利用可能APIを確認。

未対応ならfail-closed。

---

# 20. Per-Region Hint A/B

固定Alice/Bob fixtureで:

### A
```text
Base-Only CN
```

### B
```text
Shared Global Regional CN
strength .30〜.40
```

### C
```text
Per-Region Hint CN
strength .30〜.40
```

を比較。

---

# 21. Strength

Regional CNは最初から:

```text
0.75
```

を使わない。

候補:

```text
0.25
0.35
0.45
```

最大3点。

Base ControlNet strengthは既存値を維持してよい。

---

# 22. Per-Region Control評価

見るもの:

```text
Alice present
Bob present
identity
left/right
scale
pose
mannequin artifact
frame artifact
seam
runtime
VRAM
```

---

# 23. 採択基準

`per_region_hint` が:

```text
2/2 subjects present
identity separated
scale improved
no literal mannequin
```

を満たす場合:

```text
REGIONAL CONTROL MODE:
PER_REGION_HINT = PROMISING
```

満たさない場合はBase-Only / Hyper12へ戻す。

---

# 24. Regional PropagationはCharacterだけから開始

Scene / Panel background Regionalへ
ControlNetを伝播しない。

最初は:

```text
scope_type == character_instance
```

のみ。

Scene regionへのCN伝播は後段。

---

# 25. Poseはまだ追加しない

Per-Region Hintの成立前に:

```text
OpenPose
pose editor
adaptive camera
```

を追加しない。

まずMannequin Capsuleだけで
個体別Controlの責務を確認。

---

# 26. True Browser Pointer E2E

Python simulationとは別に、
実際のComfyUIブラウザ上で:

```text
Character Staging rectangle
```

をpointer dragできるかを確認。

可能ならPlaywright等、利用可能なbrowser automationを使用。

---

# 27. True Browser E2E Scenario

1ケースだけ。

```text
Workflow Authoring fixture load

Alice:
x ~ .05
↓ actual pointer drag
x ~ .55

staging_overrides widget/value changed

save workflow
reload workflow
x ~ .55 preserved

queue
output generated
```

---

# 28. Browser Gateの判定

```text
POINTER CONTRACT SIMULATION:
PASS

LIVE BROWSER POINTER E2E:
PASS / PENDING
```

を必ず別記。

---

# 29. Browser automation不可の場合

PENDINGでよい。

ユーザーへ依頼する場合は最後に1操作のみ:

```text
Aliceの矩形を左→右へドラッグ
Save
Reload
位置が残るか
```

生成画像確認まで同時に要求しない。

まずUI stateだけ確認。

---

# 30. Visual Contact Sheets

新規候補:

### Sheet M — Causal Ablation
```text
Native20 CFG7
Native12 CFG6
Native20 CFG6
Hyper12 CFG6
```

### Sheet N — base_only_steps
```text
2
0
```

### Sheet O — Regional Control
```text
Base-only
Shared Global .35
Per-Region Hint .35
```

---

# 31. User Review Rule

Geminiが実画像を直接視覚評価できた場合は自己判定可。

ただしvisual annotation generatorへ
手書き値を書いただけで:

```text
USER VISUAL REVIEW REQUIRED: NO
```

にしない。

以下をreport:

```text
visual reviewer
actual image files reviewed
review timestamp
confidence
```

---

# 32. Canonical Workflow方針

新規Saved Workflowは最大4本程度。

全条件をSaved Workflowへ増殖させなくてよい。

固定scriptで比較可能ならscriptを優先。

ユーザー確認が必要になった比較だけ:

```text
1 Workflow = 1 hypothesis
```

で発行。

---

# 33. Workflow候補

必要なら:

```text
44_VERIFY_NATIVE20_BASEONLY_ZERO.json
45_VERIFY_NATIVE12_CONTROL.json
46_VERIFY_HYPER12_CAUSAL_CONTROL.json
47_VERIFY_PER_REGION_HINT_ATTENUATED.json
```

命名は実際の仮説に合わせて調整。

---

# 34. Regression

壊してはいけないもの:

```text
WF29〜32 Subject Exclusivity
WF33〜34 Regional-only Authoring
WF39 Fast Draft + CN successful fixture
WF40〜43 historical diagnosis
```

---

# 35. Performance

速度は測定するが、
Phase 3I.2の主目的はsemantic causality。

Hyper12の約1.60xは既存値を維持。

Per-region hintでruntimeが大幅増加する場合は記録。

---

# 36. Report

新規:

```text
PHASE3I_2_REFERENCE_FAST_CAUSAL_AND_PER_REGION_CONTROL_REPORT.md
```

最低限:

```text
1. Phase3I.1 Review
2. Browser E2E Terminology Correction
3. Visual Evaluation Provenance
4. Native20 Baseline
5. Native12 Result
6. Native20 CFG6 Result
7. Hyper12 Result
8. Semantic Survival Driver
9. base_only_steps Ablation
10. Reference SSOT Decision
11. Current Shared-Global Propagation Analysis
12. Per-Region Hint Architecture
13. Attenuated Regional CN Test
14. Per-Region Hint Result
15. Artifact Comparison
16. Runtime / VRAM
17. True Browser E2E
18. Operational Profile Decision
19. Known Issues
20. Phase3J Gate
21. Gemini独自判断
```

---

# 37. Sign-off

```text
PHASE3I.1 REVIEW CLOSURE:
PASS / HOLD

POINTER CONTRACT SIMULATION:
PASS / FAIL

LIVE BROWSER POINTER E2E:
PASS / PENDING

VISUAL EVALUATION PROVENANCE:
VERIFIED / HOLD

NATIVE20 BASE-ONLY CN:
PASS / FAIL

NATIVE12 BASE-ONLY CN:
PASS / FAIL

NATIVE20 CFG6:
PASS / FAIL

HYPER12 BASE-ONLY CN:
PASS / FAIL

SEMANTIC SURVIVAL DRIVER:
HYPER_LORA / STEP_COUNT / CFG / BASE_ONLY_STEPS / MIXED / UNRESOLVED

BASE_ONLY_STEPS 0:
HELPFUL / NEUTRAL / HARMFUL / NOT TESTED

SHARED GLOBAL REGIONAL CN:
HELPFUL / OVERCONSTRAINED / REJECT

PER-REGION HINT CN:
PROMISING / NEUTRAL / REJECT / NOT TESTED

REFERENCE PROFILE ROLE:
ARCHITECTURE_REFERENCE / QUALITY_REFERENCE / BOTH

OPERATIONAL AUTHORING PROFILE:
NATIVE20 / HYPER12 / OTHER / UNRESOLVED

FAST_DRAFT_12:
ACCEPT AS DRAFT / PROMOTE CANDIDATE / CONDITIONAL / REJECT

USER VISUAL REVIEW REQUIRED:
YES / NO

PHASE3J:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 38. Phase 3Jへ進む条件

最低限:

```text
なぜHyper12だけ成功したかがある程度判明
Reference profileの役割を正しく定義
Regional CN shared-global方式の限界を記録
Per-region hintが有効か否か判明
Browser testの名称・状態が正確
```

Per-region hintがREJECTでもPhase 3Jへ進んでよい。

重要なのは:

```text
現在のOperational Authoring Profileが何か
```

が決まっていること。

---

# 39. Phase 3J候補

3I.2後:

```text
Phase 3J
Adaptive Character Guide
&
Pose / Camera Shot Authoring
```

へ進行。

ただしOperational Profileを基盤にする。

もし:

```text
Hyper12 only stable
```

なら、Adaptive Guideの研究もHyper12をPrimary operational profileとして行い、
Native20はArchitecture regressionに残す。

---

# 40. Two-stage Commit

Commit A:

```text
fix(manga): Phase 3I.2 isolate reference fast causality and regional control hints
```

Commit Aには:

```text
ablation scripts
per-region hint prototype
visual provenance correction
browser nomenclature correction
tests
report
```

を含める。

Commit A SHA取得後、
Navigation Commit Bで:

```text
ComfyUIPortable/GITHUB.TXT
```

Review TargetをCommit Aへ更新。

---

# 41. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3I_2_REFERENCE_FAST_CAUSAL_AND_PER_REGION_CONTROL_REPORT Raw:

Causal Ablation Script Raw:
Per-Region Control Prototype Raw:
Visual Evaluation Raw:
Pointer Contract Test Raw:
Live Browser E2E Raw:

Workflow44 Raw:
Workflow45 Raw:
Workflow46 Raw:
Workflow47 Raw:

PHASE3I.1 REVIEW CLOSURE:
POINTER CONTRACT SIMULATION:
LIVE BROWSER POINTER E2E:
VISUAL EVALUATION PROVENANCE:
NATIVE20 BASE-ONLY CN:
NATIVE12 BASE-ONLY CN:
NATIVE20 CFG6:
HYPER12 BASE-ONLY CN:
SEMANTIC SURVIVAL DRIVER:
BASE_ONLY_STEPS 0:
SHARED GLOBAL REGIONAL CN:
PER-REGION HINT CN:
REFERENCE PROFILE ROLE:
OPERATIONAL AUTHORING PROFILE:
FAST_DRAFT_12:
USER VISUAL REVIEW REQUIRED:
PHASE3J:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3I.1で最も重要な発見は、

```text
ControlNetを入れれば解決
```

ではなく、

```text
ControlNetの入れ方とsampling profileによって
人物が出る / 消える / 過拘束になる
```

ことです。

現時点では:

```text
Native20 + Base-Only CN
→ 失敗しやすい

Hyper12 + Base-Only CN
→ 2人物成立

Shared Global Regional CN
→ 2人物は出るが過拘束
```

です。

したがって次に必要なのは
Guide形状を増やすことではなく、
この3者の因果関係を切り分けることです。

さらにRegional CNを使う場合、
同じGlobal Guideを全Regionalへ配るのではなく、

```text
Alice region → Alice-only hint
Bob region   → Bob-only hint
```

というPer-Region Hintの方が構造的に自然です。

ここが成立すれば、
その先のOpenPose / Pose / Camera Shot / Adaptive Guideへ
かなり安全に進めます。
