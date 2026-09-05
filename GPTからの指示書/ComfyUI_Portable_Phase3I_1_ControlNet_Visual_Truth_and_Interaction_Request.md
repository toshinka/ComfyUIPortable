# ComfyUI Portable Phase 3I.1 — ControlNet Visual Truth, Conditioning Ablation & Authoring Interaction Closure 指示書

## 0. 対象 / Baseline
対象: `D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:
`6d34c1ebd8b33f8b41e0116e8eecb1699e77599c`

Phase 3I で成立した実装は維持します。

- TegakiMangaLayoutGuideGenerator
- AnyTest v4 Illustrious ControlNet integration
- Workflows 35〜39
- Zero-Touch runtime
- Reference 20-step SSOT
- Fast Draft 12 profile
- Impact Regional Backend

ただし、Phase 3I の自動スイートは主に validation error 0 / timeoutなし / output image exists を検証しており、画像意味上の成功を自動判定していません。

したがって Phase 3J の機能拡張へ直行せず、短い Phase 3I.1 で ControlNet の「何が本当に解決したか」を閉じます。

---

# 1. Phase名

```text
Phase 3I.1
ControlNet Visual Truth
&
Conditioning Ablation
&
Authoring Interaction Closure
```

内部:

```text
3I.1-0  Phase 3I Claim Correction
3I.1-A  Subject Presence / Scale / Placement Visual Gate
3I.1-B  Regional-only vs Base-ControlNet Ablation
3I.1-C  ControlNet Propagation Instrumentation
3I.1-D  ControlNet Strength / Schedule Sanity
3I.1-E  Fast-12 ControlNet Semantic Regression
3I.1-F  Browser Pointer E2E Closure
3I.1-G  Phase 3J Gate
```

---

# 2. Zero-Touch PASSとVisual Semantic PASSを分離

今後すべての検証結果は最低限:

```text
RUNTIME STATUS
VISUAL SEMANTIC STATUS
```

を分離してください。

例:

```json
{
  "workflow": "WF37",
  "runtime_status": "PASS",
  "visual_semantic_status": "PASS|PARTIAL|FAIL|PENDING"
}
```

Phase 3I の `run_phase3i_verification_suite.py` は output file existenceで `PASS` としているため、そのPASSを人物配置・人物数・スケール成功と同義にしないこと。

---

# 3. Phase 3I報告書の過大表現を補正

以下の表現は、画像測定または明瞭な視覚証拠がない限り使用しない。

```text
definitively solved
exact staging boundaries
100% maintained
strictly lock
perfectly bounding
complete
```

代わりに:

```text
subject present
directionally matched
scale improved
bbox coverage increased
no obvious shrinkage
promising
```

等を使用。

---

# 4. WF35〜39の期待Subjectを全部確認

Phase 3I報告書ではSubject presenceの記録が弱いです。

特に:
- WF35 は白犬TLが目的だが報告文は背景を主に記述
- WF36 はAlice tall portraitが目的だがAlice存在を明示していない
- WF37 はAlice Left / Bob Rightが目的だがBobのみ明示
- WF38 はBob Left / Alice Rightが目的だがBobのみ明示
- WF39 は両者を明示

以下を再評価してください。

---

# 5. WF35 Visual Gate

期待:

```text
White Dog
Top-Left target
no extra human
```

記録:

```text
Dog present:
Dog observed bbox:
Target bbox: [0.10,0.10,0.40,0.40]
Direction:
Scale:
Extra subjects:
```

犬が存在しない場合、Visual PASSにしない。

---

# 6. WF36 Visual Gate

期待:

```text
Alice
single character
tall portrait
target h = .75
```

記録:

```text
Alice present
approx bbox
vertical coverage
full body / bust / cropped
extra person
guide artifact
```

目的は「clean background」ではなく character scale locking。

---

# 7. WF37 Visual Gate

期待:

```text
Alice = Left
Bob = Right
both present
```

必須:

```text
Alice present:
Bob present:
Alice side:
Bob side:
Alice approx bbox:
Bob approx bbox:
Identity bleed:
Duplicate subject:
Missing subject:
```

片方しか存在しない場合 Visual Semantic = FAIL。

---

# 8. WF38 Visual Gate

期待:

```text
Bob = Left
Alice = Right
both present
```

WF37と同じ項目を記録。

Geometry Swap成功条件は WF37 と WF38 の両方で2人が存在すること。

---

# 9. WF39 Visual Gate

Fast Draft 12。

期待:

```text
Bob = Left
Alice = Right
both present
scale maintained
no obvious seam
```

WF38 Referenceと比較。

---

# 10. Visual Evaluation JSON

新規:

`output/Tegaki/Phase3I1/phase3i1_visual_evaluation.json`

例:

```json
{
  "WF37": {
    "runtime_status": "PASS",
    "visual_semantic_status": "PASS",
    "subjects": [
      {
        "id": "Alice",
        "present": true,
        "expected_side": "left",
        "observed_side": "left",
        "approx_bbox": [0.08,0.15,0.36,0.70]
      }
    ]
  }
}
```

数値が判断不能なら `null`。

---

# 11. Gemini Visual Confidence

各Visual判定へ confidence 0.0〜1.0 を追加。

目安:

```text
>= .85  AI visual judgment accepted
.60-.84 PARTIAL / cautious
< .60    USER VISUAL REVIEW REQUIRED
```

---

# 12. Diagnostic Overlay

Phase 3I outputへ expected staging box / observed approximate subject box / label を重ねた診断画像を生成。

候補:
`sheet_j_phase3i_subject_presence_and_bbox.png`

最低限 WF36 / WF37 / WF38 / WF39。

---

# 13. Regional-onlyとControlNet-assistedを直接比較

Phase 3H:
`WF33 / WF34`

Phase 3I:
`WF37 / WF38`

可能な限り same seed / prompts / staging / model / sampler を揃え、

```text
WF33 vs WF37
WF34 vs WF38
```

を比較。

---

# 14. 比較項目

```text
subject presence
left/right placement
bbox height coverage
bbox width coverage
perspective shrinkage
feet/body truncation
identity
background quality
pose rigidity
ControlNet artifacts
```

---

# 15. Scale Lock Metric

人物検出器は不要。

Visual approximate bboxで:

```text
coverage_h = observed_subject_bbox_height / target_staging_height
coverage_w = observed_subject_bbox_width / target_staging_width
```

を記録。

目的は exact containment ではなく、Regional-onlyよりCNでscale shrinkageが改善したか。

---

# 16. 過拘束も確認

Mannequin guideで:

```text
棒立ち化
同じPoseへの収束
手足の不自然な固定
顔/頭身崩れ
```

が起きていないか確認。

---

# 17. Guide露出Artifacts

確認:

```text
box線が背景線として残る
対角線が服/背景へ混入
mannequin capsuleが人体線として露出
panel borderが不要な構図線になる
```

---

# 18. Conditioning mechanicsを計測

現 `TegakiMangaImpactRegionalAdapter` は:

```python
pos_cond = self._encode_text(...)
regional_sampler = base_sampler.clone_with_conditionings(pos_cond, neg_cond)
```

なので、regional conditioningsへControlNet metadataが残るかは明示確認が必要。

新規:

`scripts/test_controlnet_conditioning_propagation.py`

最低限:

```text
Base positive conditioning: control metadata present?
Regional encoded positive: control metadata present?
clone_with_conditionings result: which conditioning stored?
Regional sampler receives control: YES / NO / UNKNOWN
```

inspect不能なら UNKNOWN とし、推測で断定しない。

---

# 19. 「Steps 1〜6」表現を修正

WF37保存Workflow上 `ControlNetApplyAdvanced` は:

```text
strength = .75
start_percent = 0.0
end_percent = 0.8
```

です。

「Steps 1〜6だけ作用」という表現は根拠不足。

Runtime semanticsを確認し、原則 start/end percentage で記録。

---

# 20. ControlNet Schedule Sanity

大規模Sweep不要。

Reference 20-stepで1ケースのみ:

```text
Strength .50 / End .60
Strength .75 / End .80  ← current
Strength .90 / End .90
```

程度。

目的は scale lock vs overconstraint の妥当点を見ること。

---

# 21. Adaptive Guide Scalingはまだ本実装しない

close-up / bust / half-body / full-body / long-shot はPhase 3J候補。

今回は現在の mannequin_capsule が本当にScale Lockへ寄与することを確定。

---

# 22. Regional ControlNet PropagationはA/B実験から

いきなり本線実装しない。

A:
```text
Current: ControlNet in base conditioning only
```

B:
```text
Experimental: Control metadata copied/re-applied to regional positive conditionings
```

見るもの:

```text
individual pose adherence
character scale
identity
seam
overconstraint
runtime
VRAM
```

Bが明確に改善しないならCurrent方式を維持。

---

# 23. Fast Draft 12 + CN回帰

WF38 Reference と WF39 Fast-12 を比較。

必須:

```text
both subjects present
same left/right binding
similar scale coverage
no new seam
no increased guide artifacts
```

PASSなら:

`FAST_DRAFT_12 + CONTROLNET: ACCEPT AS DRAFT`

---

# 24. Fast-12速度表現

WF38 48.08s、WF39 30.08s なので:

```text
1.60x speedup
約37.4% time reduction
```

を実測として記録。

---

# 25. Browser Pointer E2Eを閉じる

長くPENDINGなので1ケースだけ。

可能ならブラウザ自動化で:

```text
production authoring fixture load
P1 Alice select
Alice rectangle left → center-rightへdrag
save / queue
generation
reload
position persists
```

見るもの:

```text
mouse event works
staging_overrides changes
backend receives changed area
saved workflow preserves
generation reacts directionally
```

---

# 26. 自動ブラウザ不可の場合

ユーザーへ依頼するのは1操作だけ。

```text
Character StagingでAlice矩形を左から右へドラッグ
そのままExecute
スクリーンショット1枚
```

Gemini側で可能な検証を終えてから依頼。

---

# 27. Guide Source SSOT

ControlNet guideとImpact maskの座標を別入力にしない。

必ず:

```text
same staging box
→ Impact mask
→ ControlNet guide
```

二重座標管理禁止。

---

# 28. Panel Layoutとの責務分離

Character Guide:
```text
character scale / pose / rough placement
```

Panel Guide:
```text
comic panel borders / page composition
```

将来同一画像へ統合可能だが内部契約は別。

---

# 29. Raw Sketch ControlNetを残す

将来UIでは:

```text
A. User supplied rough image / pose / lineart
B. Auto-generated staging guide
C. Panel slicer generated layout guide
```

の3系統があり得る。

今回Bのみ検証。A/Cを消さない。

---

# 30. Canonical Workflows

新規は最大4本程度。

候補:

```text
40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json
41_VERIFY_CN_STRENGTH_SANITY.json
42_VERIFY_REGIONAL_CN_PROPAGATION_AB.json
43_VERIFY_BROWSER_STAGING_CAUSALITY.json
```

1 Workflow = 1 Hypothesis維持。

---

# 31. Contact Sheets

```text
Sheet J:
WF33 vs WF37
WF34 vs WF38

Sheet K:
WF38 Reference vs WF39 Fast-12

Sheet L:
Base-only CN vs Regional CN propagation
```

---

# 32. Report

新規:

`PHASE3I_1_CONTROLNET_VISUAL_TRUTH_AND_INTERACTION_REPORT.md`

最低限:

```text
1. Phase3I Review Closure
2. Runtime PASS vs Visual PASS
3. WF35 Subject Presence
4. WF36 Scale Lock
5. WF37 Alice/Bob Semantic Result
6. WF38 Swap Semantic Result
7. WF39 Fast-12 Semantic Result
8. Approximate BBox / Coverage Metrics
9. Regional-only vs CN Comparison
10. CN Artifact Review
11. Conditioning Metadata Inspection
12. ControlNet Schedule Correction
13. Strength/Schedule Sanity
14. Regional CN Propagation Prototype
15. Propagation A/B Result
16. Fast-12 CN Regression
17. Browser Pointer E2E
18. Guide SSOT
19. Known Issues
20. Phase3J Gate
21. Gemini独自判断
```

---

# 33. Sign-off

```text
PHASE3I REVIEW CLOSURE:
PASS / HOLD

WF35 SUBJECT PRESENCE:
PASS / PARTIAL / FAIL

WF36 SCALE LOCK:
PASS / PARTIAL / FAIL

WF37 TWO-CHARACTER SEMANTICS:
PASS / PARTIAL / FAIL

WF38 TWO-CHARACTER SWAP:
PASS / PARTIAL / FAIL

WF39 FAST-12 CN SEMANTICS:
PASS / PARTIAL / FAIL

REGIONAL-ONLY VS CN SCALE IMPROVEMENT:
YES / NO / UNCLEAR

CONTROLNET ARTIFACTS:
NONE / ACCEPTABLE / PROBLEMATIC

CONTROL METADATA PROPAGATION:
BASE_ONLY / REGIONAL_TOO / UNKNOWN

CONTROLNET SCHEDULE:
VERIFIED / HOLD

REGIONAL CN PROPAGATION:
HELPFUL / NEUTRAL / HARMFUL / NOT TESTED

FAST_DRAFT_12 + CN:
ACCEPT AS DRAFT / CONDITIONAL / REJECT

BROWSER POINTER E2E:
PASS / PENDING

USER VISUAL REVIEW REQUIRED:
YES / NO

PHASE3J:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

---

# 34. Phase 3Jへ進む条件

最低限:

```text
WF37/38でAlice/Bob双方の存在確認
ControlNetによるscale改善が確認
ControlNet artifactsが許容範囲
Schedule表現が正確
Fast-12 + CNの位置づけ確定
```

Browser Pointer E2EがPENDINGでも、event/state contractが成立し、ユーザー確認要求が明確ならPhase 3J進行可。

---

# 35. Phase 3J候補

Phase 3I.1がPASSなら:

```text
Phase 3J
Adaptive Character Guide
&
Pose / Camera Shot Authoring
```

候補:

```text
shot type:
close-up
bust
half-body
full-body
long-shot

pose guide:
basic mannequin
optional user OpenPose
optional regional pose

camera:
near / far
simple FOV intent
```

今回は実装しない。

---

# 36. Two-stage Commit

Commit A:

```text
fix(manga): Phase 3I.1 ControlNet visual truth and interaction closure
```

内容:

```text
visual evaluation
bbox diagnostics
report correction
conditioning propagation instrumentation
schedule sanity
optional propagation prototype
browser E2E
tests
report
```

Commit A SHA取得後、Navigation Commit Bで `ComfyUIPortable/GITHUB.TXT` Review TargetをCommit Aへ。

---

# 37. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3I_1_CONTROLNET_VISUAL_TRUTH_AND_INTERACTION_REPORT Raw:

Visual Evaluation Raw:
Conditioning Propagation Test Raw:
Browser E2E Raw:

Workflow40 Raw:
Workflow41 Raw:
Workflow42 Raw:
Workflow43 Raw:

PHASE3I REVIEW CLOSURE:
WF35 SUBJECT PRESENCE:
WF36 SCALE LOCK:
WF37 TWO-CHARACTER SEMANTICS:
WF38 TWO-CHARACTER SWAP:
WF39 FAST-12 CN SEMANTICS:
REGIONAL-ONLY VS CN SCALE IMPROVEMENT:
CONTROLNET ARTIFACTS:
CONTROL METADATA PROPAGATION:
CONTROLNET SCHEDULE:
REGIONAL CN PROPAGATION:
FAST_DRAFT_12 + CN:
BROWSER POINTER E2E:
USER VISUAL REVIEW REQUIRED:
PHASE3J:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3Iの方向性は有望です。

Regionalは identity / semantic separation、ControlNetは scale / silhouette / rough geometry という役割分担は、これまでの結果と整合します。

ただし現在の自動PASSは「生成処理が成功した」ことを主に保証しており、

- AliceとBobが双方正しく存在する
- 指定scaleを本当に使い切る
- exact boundaryに一致する
- ControlNetがRegionalへどう伝播する

までは自動的に証明していません。

Phase 3I.1では新機能を増やすより先にこの境界を明確化してください。

Current Base-Only ControlNet方式で十分なら構造を簡潔に維持し、不足する場合だけRegional ControlNet Propagationへ進みます。

Adaptive Guide / Pose / Camera Distanceはこの検証が閉じた後のPhase 3Jへ回してください。
