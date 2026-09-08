# ComfyUI Portable Phase 3G — Canonical Verification Suite, Browser Interaction Closure & Hyper-SD Fast-Mode Feasibility 指示書

## 0. 対象 / Baseline

対象:
`D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:
`cc7d3e4dc8b6fac620df9aee8f69067ca3da564a`

Phase 3F の以下は成立済みとして維持します。

```text
SAVED WORKFLOW21 ZERO-TOUCH: PASS
SAVED WORKFLOW22 ZERO-TOUCH: PASS
WORKFLOW23 ZERO-TOUCH: PASS
WORKFLOW24 ZERO-TOUCH: PASS
EXTERNAL NODE LIVE SCHEMA: PASS
PRIMARY REGIONAL BACKEND: IMPACT
SUBSCENE V1: PASS
```

特に Phase 3F で、保存Workflowを何も直さず実行し、validation error 0で実画像生成する経路が成立しました。

---

# 1. Phase名

```text
Phase 3G
Canonical Verification Suite
&
Browser Interaction Closure
&
Hyper-SD Fast-Mode Feasibility
```

内部:

```text
3G-0  Phase 3F Review Closure
3G-A  Truthful Browser Interaction / Data-Driven Staging
3G-B  Canonical Fixed Verification Workflows
3G-C  Verification Runner / Contact Sheet / Evaluation Tiers
3G-D  Hyper-SD Local Asset Discovery
3G-E  Reference vs Fast Performance Track P0
3G-F  Fast-Mode Decision Gate
```

---

# 2. Phase 3Fの成果を維持するが、UI完成とは扱わない

外部レビューで確認した現状:

### Panel Content Editor
Frontendは現在 Alice / Bob のAttendance / Acting widgetを直接ハードコードしています。

### Character Staging Editor
Frontendは Alice / Bob の矩形を描画していますが、現Review Targetの `character_staging_editor.js` には実際の mouse down / move / up による座標変更処理がありません。

したがって現在の正確な判定:

```text
CAST PROMPT EDITING:
IMPLEMENTED

PANEL CONTENT PROTOTYPE:
IMPLEMENTED / FIXTURE-ORIENTED

CHARACTER STAGING PREVIEW:
IMPLEMENTED

CHARACTER STAGING DRAG/RESIZE:
NOT YET PROVEN / IMPLEMENTATION GAP

BROWSER INTERACTION:
PENDING
```

「drag / resize fully implemented」と過大記載しないこと。

---

# 3. 高解像度Productionへ急がない

Phase 3F報告では次候補としてHigh-Resolution Manga Layout Productionが挙げられていますが、その前に以下を固定します。

```text
1. 検証方法
2. 実ブラウザ操作
3. 性能Baseline
4. Fast Mode候補
```

高解像度化すると実行時間がさらに増え、Regional数による性能問題の原因分離が難しくなるためです。

---

# 4. Character Stagingを実操作へ

`TegakiMangaCharacterStagingEditor` を最小限で実操作可能にしてください。

最低限:

```text
Current Panel select
Active Character select
rectangle select
drag move
resize handle
reset
save workflow
reload workflow
position preserved
```

---

# 5. Staging UIを実データ駆動へ

現在の Alice / Bob 固定矩形を正本にしない。

表示対象は入力 `REGION_SPEC` の:

```text
selected panel
→ enabled character bindings
→ area
```

から動的生成してください。

Active Character selectorも Current Panel に出演するCharacterだけを列挙すること。

---

# 6. staging_overridesのSSOT方針

UI dragで変更したareaは `staging_overrides` へtransactionalに保存し、backend `process()` が既存REGION_SPECへ適用する方式を維持して構いません。

ただし:

```text
frontend display position
backend applied position
saved workflow position
```

が一致すること。

---

# 7. Mouse Interaction Test

新規:

```text
scripts/test_character_staging_state.py
```

最低限:

```text
select panel
select character
move
resize
clamp
overlap allowed
save/reload state
unknown character reject
non-attending character hidden
```

Browser automation可能なら実ブラウザE2Eも実施。

不可なら `BROWSER POINTER E2E: PENDING` を維持。ただしevent handler自体は実装必須。

---

# 8. Panel Contentの固定Alice/Bobは最低限一般化

最終UI Polishは不要。

既存 `cast_spec` 入力からCharacter一覧を得て、Attendance / Acting編集対象を固定Alice/Bobから外してください。

動的widgetが不安定なら:

```text
Selected Panel
Selected Character

Attend: true/false
Acting Prompt
Negative Override
```

という切替型UIを推奨。

---

# 9. SubScene UIは拡張しすぎない

SubScene v1 Contractは維持。

今回 nested subscene / polygon subscene / 3+ subscene complex UI は不要。

1 visible Panel / 2 subscenes の固定Oracleが維持できればよい。

---

# 10. Canonical Verification Workflow方針

今後の研究では:

```text
1 Workflow = 1 hypothesis
```

を基本にします。

ユーザーに Aを動かす、Bと入れ替える、seedを戻す等の比較操作を任せないこと。

研究用Workflowは多少重複しても:

```text
固定条件
固定Seed
固定Prompt
固定Geometry
Zero-Touch
```

を優先。

---

# 11. Canonical Spatial Verification Set

新規Workflowを最大4本:

```text
25_VERIFY_SINGLE_A_TOP_LEFT.json
26_VERIFY_SINGLE_A_BOTTOM_RIGHT.json
27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json
28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json
```

名称は既存命名規則へ調整可。

### Workflow25 / 26
共通:
- Global Prompt: same
- Region A Prompt: `a white dog, full body`
- Region B: disabled
- Seed: 42
- Backend: Impact
- Sampler / steps / CFG: identical

差分はRegion A Geometryのみ。

25 = Top Left  
26 = Bottom Right

### Workflow27 / 28
共通Prompt:

```text
A: a white dog, full body
B: a black cat, full body
```

Promptに left/right/top/bottom 等の位置単語を入れない。

27 = A left / B right  
28 = A right / B left

GeometryのみSwap。

---

# 12. Canonical Authoring Verification Set

既存:

```text
21 = Recurrent Cast
22 = Same-Cast Multi-Scene hostile
23 = Progressive 4-panel authoring
24 = Progressive SubScene
```

をCanonical Authoring Setとして維持。

つまり:

```text
Spatial Set: 25-28
Authoring Set: 21-24
```

---

# 13. Verification Manifest

新規:

```text
docs/verification/PHASE3G_CANONICAL_VERIFICATION_MANIFEST.json
```

各Workflowについて:

```text
workflow
hypothesis
seed
invariants
changed_variable
expected
human_review_default
```

を保持。

---

# 14. Verification Runner

新規:

```text
scripts/run_canonical_verification_suite.py
```

機能:

```text
server start
workflows in deterministic order
timeout breaker
save outputs
record runtime
record validation
server stop
```

Phase 3E/3Fの安全なprocess teardown helperを再利用。

---

# 15. Contact Sheet

新規:

```text
scripts/generate_phase3g_verification_contact_sheet.py
```

最低限:

```text
Sheet A: 25 TL | 26 BR
Sheet B: 27 Dog/Cat LR | 28 Dog/Cat SWAP
Sheet C: 必要なら 21 | 22 | 23 | 24
```

---

# 16. 検証成果物

ComfyUI画面のスクリーンショットより:

```text
fixed workflow
+
generated final image
+
contact sheet
+
diagnostic JSON
```

を研究正本にする。

UI操作確認だけは別。

---

# 17. Evaluation Tier

### LEVEL 1 — Automatic
```text
schema
zero-touch
output exists
region masks
attendance
instance mapping
runtime
```

### LEVEL 2 — Gemini / AI Visual
```text
subject position
identity separation
acting
bleed
scene separation
chimera
```

Geminiがローカル出力画像を視覚確認できる場合は自己判定。

### LEVEL 3 — User
以下の時だけ依頼:

```text
AI visual judgment ambiguous
UI mouse feel required
generated result semantic interpretation uncertain
```

ユーザーを通常のテストランナーにしない。

---

# 18. User Review Request Rule

ユーザー確認が必要な場合は、必ず1つの目的を指定。

例:

```text
Workflow 28をZero-Touchで1回実行
Final Imageだけ提示
確認点: dog/catが27と左右反転しているか
```

---

# 19. Hyper-SD Local Asset Discovery

Early Performance Track P0。

Hyper-SDはユーザー環境に既に存在する可能性が高いため、最初にローカル資産を探索してください。

ComfyUI / EasyReforge共有モデルパスを確認し:

```text
Hyper-SD
HyperSD
Hyper-SDXL
Hyper SDXL
```

等でLoRA / model assetを検索。

対象候補は SDXL CFG-compatible Hyper-SD の 8-step / 12-step を優先。

---

# 20. Asset重複禁止

既存Hyper-SDが見つかった場合、そのファイルを共有パス経由で使用し、コピーや再ダウンロードをしない。

報告:

```text
actual filename
actual path
file size
variant identification
```

可能ならhash。

---

# 21. 既存Assetが見つからない場合

その場合のみ、公式ByteDance Hyper-SD配布元から SDXL CFG-compatible LoRA を取得してよい。

第三者reuploadを優先しない。

保存先は既存EasyReforge / ComfyUI共有LoRA設計へ合わせる。

Lightning / LCM / Turbo checkpointへ勝手に置き換えない。

---

# 22. Hyper-SD Variant

理想比較:

```text
REFERENCE:
20-step current Illustrious

FAST-12:
Hyper-SD SDXL CFG 12-step

FAST-8:
Hyper-SD SDXL CFG 8-step
```

ローカルに一方しか無い場合は存在するvariantだけでよい。

variantを推測で誤認しない。

---

# 23. Reference Modeを絶対に残す

Phase 3G開始時点でHyper-SDを標準化しない。

Canonical Reference:

```text
waiIllustriousSDXL
20 steps
Euler / Normal
CFG 7
current Impact settings
```

を維持。

Fast Modeは比較Branch。

---

# 24. Hyper-SDを全Workflowへ一括適用しない

Performance Track P0は代表負荷3種類まで:

```text
A. Two Region Geometry Swap
B. Recurrent Cast 4-Panel
C. Same-Cast Multi-Scene
```

---

# 25. Performance Test A

Workflow27 / 28相当。

目的:

```text
Fast化でgeometry causalityが壊れないか
dog/cat identity mergeが増えないか
```

---

# 26. Performance Test B

Workflow21または23相当。

測定:

```text
total runtime
sampling runtime if obtainable
peak VRAM if obtainable
attendance
acting separation
identity consistency
panel bleed
```

---

# 27. Performance Test C

Workflow22または24相当。

目的:

```text
同一人物複数instance
subscene separation
```

Fast化で identity merge / scene collapse が増えないかを見る。

---

# 28. Hyper-SD適用方法

既存MODEL / CLIP / Impact pipelineを壊さない標準LoRA Loader経路を使用。

Fast検証専用Branch:

```text
Checkpoint
→ Hyper-SD LoRA
→ ToBasicPipe / Impact
```

Character LoRA PlanやRegional LoRAと混同しない。

Hyper-SDは generation accelerator として扱う。

---

# 29. Fast Modeで変えてよいもの

原則:

```text
Hyper-SD acceleration asset
steps
Hyper-SD公式推奨に必要なsampler/scheduler/cfg設定
```

のみ。

比較のため:

```text
seed
prompts
region geometry
layout
cast
subscene
```

は固定。

---

# 30. Fast Mode評価

最低限:

```text
Runtime
Subject Missing
Position Direction
Identity Separation
Attendance
Acting Separation
Scene Separation
Seam
Chimera / Merge
```

速度だけで採択しない。

---

# 31. Fast Mode Decision Gate

各variant:

```text
FAST-12:
ACCEPT / CONDITIONAL / REJECT

FAST-8:
ACCEPT / CONDITIONAL / REJECT
```

ACCEPT:
- 明確な速度短縮
- Canonical semantic controlsを大きく損なわない

CONDITIONAL:
- Preview / Draftには有効
- Final / Verificationには不安定

REJECT:
- 位置・identity・scene separationを明確に壊す

---

# 32. 二本立て

Hyper-SDが採択されても:

```text
REFERENCE MODE
FAST MODE
```

を維持。

重要Backend研究のAcceptanceは当面Reference Modeを正本にする。

Fast ModeはDraft / Preview / UI iterationへ先に使う。

---

# 33. ControlNetとのFast併用は次段階

Performance P0ではControlNetを主比較へ入れない。

Hyper-SDがACCEPTされた後にのみ:

```text
Impact + Hyper-SD + Panel Layout ControlNet
```

の小規模検証を次Phase候補にする。

---

# 34. Semantic-Neutral高速化

Phase 3Gでは調査メモのみ可。

候補:

```text
torch.compile
attention backend
VRAM / model caching
server lifetime reuse
```

環境リスクがあるものを勝手に標準化しない。Hyper-SD P0と混ぜない。

---

# 35. Saved Fast Workflowsは必要時のみ

Geminiが自動生成・視覚判定できるなら:

```text
scripts/test_phase3g_hypersd_performance.py
```

で比較し、Hyper-SD用Saved Workflowを大量追加しなくてよい。

AI判定が曖昧な場合だけ最大3本:

```text
29_VERIFY_RECURRENT_CAST_REFERENCE_20STEP.json
30_VERIFY_RECURRENT_CAST_HYPER_12STEP.json
31_VERIFY_RECURRENT_CAST_HYPER_8STEP.json
```

等を生成。

ユーザーに内部切替を任せない。

---

# 36. Performance Result

新規:

```text
output/Tegaki/Phase3G/hypersd_performance_results.json
```

記録:

```text
Reference runtime
Fast runtime
speedup x
time reduction %
semantic result
```

---

# 37. 1024x1024基準

Phase 3Gでは現在の1024x1024で比較。

高解像度化はFast Mode候補が決まってから。

---

# 38. 全新規Workflow Zero-Touch必須

25〜28および必要なら29〜31:

```text
saved workflow live schema validation
zero-touch queue
validation error 0
output exists
```

を必須。

Phase 3Fの教訓を常設ルール化。

---

# 39. Production UIは3Gで完成させない

後段:

```text
custom skin
preset library
page project switching
ControlNet freehand input
Clip Studio-like panel slicer polish
high-resolution production
```

---

# 40. Phase 3G Report

新規:

```text
PHASE3G_CANONICAL_VERIFICATION_AND_FAST_MODE_REPORT.md
```

最低限:

```text
1. Phase3F Review Closure
2. Character Staging Claim Correction
3. Data-Driven Character Staging
4. Mouse Interaction Implementation
5. Dynamic Cast Panel Content
6. Browser Interaction Status
7. Canonical Verification Philosophy
8. Workflow25
9. Workflow26
10. Workflow27
11. Workflow28
12. Spatial Contact Sheet
13. Authoring Verification Set
14. Evaluation Tier
15. Hyper-SD Asset Discovery
16. Hyper-SD Variant Identification
17. Reference Baseline
18. Hyper-SD 12-step Result
19. Hyper-SD 8-step Result
20. Two-Region Semantic Comparison
21. Recurrent Cast Performance
22. Multi-Scene Performance
23. Runtime / VRAM Table
24. Semantic Regression Table
25. Fast Mode Decision
26. User Review Requirement
27. Known Issues
28. Next Phase
29. Gemini独自判断
```

---

# 41. Phase Sign-off

```text
PHASE3F REVIEW CLOSURE:
PASS / HOLD

CHARACTER STAGING DATA-DRIVEN:
PASS / HOLD

CHARACTER STAGING MOVE/RESIZE:
PASS / HOLD

PANEL CONTENT DYNAMIC CAST:
PASS / HOLD

BROWSER POINTER E2E:
PASS / PENDING

CANONICAL VERIFY 25:
PASS / HOLD

CANONICAL VERIFY 26:
PASS / HOLD

CANONICAL VERIFY 27:
PASS / HOLD

CANONICAL VERIFY 28:
PASS / HOLD

HYPER-SD LOCAL ASSET:
FOUND / FETCHED / NOT AVAILABLE

REFERENCE MODE:
PASS / HOLD

FAST-12:
ACCEPT / CONDITIONAL / REJECT / NOT TESTED

FAST-8:
ACCEPT / CONDITIONAL / REJECT / NOT TESTED

FAST MODE:
AVAILABLE / DEFERRED

USER VISUAL REVIEW REQUIRED:
YES / NO

PRIMARY REGIONAL BACKEND:
IMPACT

NEXT RECOMMENDED PHASE:
```

---

# 42. Next Phase分岐

Fast Mode ACCEPT + Browser interaction PASS:
```text
Phase 3H
Production Authoring UX
+
Optional ControlNet / Fast Mode Integration
```

Fast Mode CONDITIONAL:
Referenceを研究正本に維持し、Fast Draft Modeとして後段UIに置く。

Fast Mode REJECT:
Hyper-SDを研究本線から外す。

Browser interaction HOLD:
High-resolutionへ進む前にInteraction Closureを継続。

---

# 43. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3G Canonical Verification and Hyper-SD Fast Mode Feasibility
```

内容:

```text
staging interaction
dynamic cast UI minimum
verification workflows
verification manifest
runner
contact sheets
Hyper-SD performance test
report
tests
```

Commit AのSHA取得後、Navigation Commit Bで `ComfyUIPortable/GITHUB.TXT` のReview TargetをCommit Aへ更新。

Hyper-SD model binary自体をGitへ追加しない。

---

# 44. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3G_CANONICAL_VERIFICATION_AND_FAST_MODE_REPORT Raw:

Character Staging Raw:
Character Staging JS Raw:
Panel Content Raw:
Panel Content JS Raw:

Verification Manifest Raw:
Verification Runner Raw:
Verification Contact Sheet Script Raw:

Workflow25 Raw:
Workflow26 Raw:
Workflow27 Raw:
Workflow28 Raw:

Hyper-SD Performance Test Raw:
Performance Result Raw:

PHASE3F REVIEW CLOSURE:
CHARACTER STAGING DATA-DRIVEN:
CHARACTER STAGING MOVE/RESIZE:
PANEL CONTENT DYNAMIC CAST:
BROWSER POINTER E2E:
CANONICAL VERIFY 25:
CANONICAL VERIFY 26:
CANONICAL VERIFY 27:
CANONICAL VERIFY 28:
HYPER-SD LOCAL ASSET:
REFERENCE MODE:
FAST-12:
FAST-8:
FAST MODE:
USER VISUAL REVIEW REQUIRED:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3Gの目的は新機能の数を増やすことではありません。

まず:

```text
1 Workflow = 1 hypothesis
```

で検証を固定し、比較のための切替操作をユーザーへ任せません。

次に、Phase 3Fで見た目まで用意されたCharacter Stagingを実データ駆動・実ドラッグへ進めます。

そして性能についてはHyper-SDを早期に一度だけ適性評価します。

ただしReference Modeを残し、Fast Modeを別Branchとして評価してください。

これによりTurbo化による構造制御の劣化と、Regional / SubScene / ControlNetそのものの限界を混同せずに済みます。

Hyper-SDが十分な意味分離を保ったまま高速化できるなら、以後の大量PreviewやDraft生成に早期採用する価値があります。

不安定なら、重要検証は20-step Referenceで継続します。
