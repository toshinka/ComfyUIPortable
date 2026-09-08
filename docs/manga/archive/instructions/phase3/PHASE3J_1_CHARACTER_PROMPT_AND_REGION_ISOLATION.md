# ComfyUI Portable Phase 3J.1 — Character Prompt Contract Repair & Region Isolation Closure 指示書

## 0. Baseline

対象: `D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:
`450ee446d88d9f34579758792320381cb04b2f22`

Phase 3J の以下は保持する。

- Background-only Base v2
- Character × Side Matrix framework
- Clean Per-Region Hint v2
- `regional_control_end_percent`
- `include_bbox_outline`
- Adaptive Shot Type guide contract
- Workflows 48〜53
- Hyper12 conditional profile
- Native20 architecture reference

ただし外部レビューで、Phase 3J の「人物が出ない」結果を解釈する前に修正すべき Canonical Fixture / Prompt Contract の重大な不整合が確認された。Phase 3K Pose / Interactionへはまだ進まず、Phase 3J.1 でこの契約を閉じること。

## 1. Phase名

```text
Phase 3J.1
Character Prompt Contract Repair
&
Region Isolation Closure
```

内部:

```text
3J.1-0  Phase 3J Claim Correction
3J.1-A  CAST / Binding Fixture Contract Repair
3J.1-B  Compile-Plan Prompt Truth Gate
3J.1-C  Character-vs-Scene Conditioning Isolation
3J.1-D  Background Remainder Mask Gate
3J.1-E  Character Guide Geometry Deconfounding
3J.1-F  Presence Matrix v2
3J.1-G  Shot-Type Semantic Revalidation
3J.1-H  Phase 3K Gate
```

## 2. 最重要問題 — Phase 3J Canonical CAST fixture が契約フィールドを使っていない

Phase 3J の `generate_phase3j_workflows.py` / `run_phase3j_presence_matrix.py` では Character Master を `appearance` で記述している。

しかし現在の `CAST_SPEC v1` validator / compiler が正本として読むCharacter Positiveは `prompt`。

Canonical fixtureは必ず:

```json
{
  "id": "char_alice",
  "name": "Alice",
  "enabled": true,
  "prompt": "1girl, blonde twin tails, blue eyes, school uniform, pleated skirt",
  "negative_prompt": "1boy, male, duplicate person, blurry",
  "loras": [],
  "metadata": {}
}
```

へ修正。Bobも同様。

## 3. Character Binding fixture もCanonical fieldへ修正

Phase 3J generatorでは `acting` / `importance` を使っているが、`validate_character_binding()` / compilerがPositive overrideとして読むのは `prompt_override`。

Canonical fixture:

```json
{
  "character_id": "char_alice",
  "enabled": true,
  "prompt_override": "standing calmly",
  "negative_prompt_override": "",
  "area": {"x":0.10,"y":0.15,"w":0.35,"h":0.75},
  "metadata": {"semantic_role":"primary"}
}
```

`acting` / `importance` を将来UIの高位語彙として残すなら、Compilerへ明示変換するまではCanonical backend testに使わない。

## 4. Phase 3J Presence結果の解釈を補正

Workflows 48〜53はRuntime / Schema fixtureとしては有効だが、Character Positive Contractが欠落していたため、

```text
Alice/Bobが出ない
→ Model / perspective / side biasの限界
```

と断定しない。

正確には:

```text
Character Identity Prompt was not proven to reach the regional sampler.
```

再検証対象:

```text
ALICE LEFT
ALICE RIGHT
BOB LEFT
BOB RIGHT
TWO-CHARACTER SWAP
SIDE BIAS
PER-REGION HINT semantic presence
SHOT TYPE final-image semantics
```

## 5. Compile-Plan Prompt Truth Gate

新規:

```text
scripts/test_phase3j1_character_prompt_contract.py
```

最低限:

```text
Alice master prompt != empty
Bob master prompt != empty
Alice override prompt accepted
Bob override prompt accepted
```

PAGE_COMPILE_PLAN各Characterの `combined_prompt` にIdentity tokenが含まれること。

## 6. Impact Region Planまで検証

新規または同テスト内:

```text
scripts/test_phase3j1_impact_character_prompt_truth.py
```

`scope_type == character_instance` の各regionについて:

```text
prompt is not empty
prompt is not identical to panel scene prompt
master_character_id is correct
pixel_bounds is correct
```

を検証。

Canonical Presence testをqueueする前にPASS必須。

## 7. Debug JSONへPrompt Provenanceを追加

Impact Adapter debugに各Character region:

```json
{
  "master_character_id": "char_alice",
  "character_instance_id": "...",
  "prompt_mode": "standalone",
  "character_prompt_nonempty": true,
  "prompt_preview": "1girl, blonde twin tails..."
}
```

等を追加。

## 8. 第二の重要問題 — `character_prompt_mode = scene_composed`

Phase 3J generatorは現在 `scene_composed`。この場合 `Panel Scene Prompt + Character Prompt` がCharacter regionへ結合される。

Canonical Presence Oracle v2では:

```text
character_prompt_mode = standalone
```

を使用。

Character regionはAlice/Bob identity + actingのみ。Scene semanticsはPanel Scene regionへ分離。

`standalone` が人物存在を回復した後にだけ、Production quality用に `standalone vs scene_composed` を1ケース比較してよい。

## 9. 第三の重要問題 — Panel Scene mask がCharacter領域まで全面被覆

`impact_region_plan.py` には既に `remainder_mask_mode` があるが、Phase 3J generatorは:

```text
include_panel_backgrounds = True
remainder_mask_mode = False
```

を使用している。

そのためPanel Scene regionがCharacter masksを含むPanel全域を覆う。

Canonical Presence Oracle v2では:

```text
remainder_mask_mode = True
```

を必須比較。

```text
Panel Scene Mask
=
Panel Polygon
-
Character Masks
-
Local Region Masks
```

とし、Background regional samplerがCharacter staging areaを再描画しないようにする。

## 10. Remainder Mask A/B

同じPrompt / Seed / Geometryで:

```text
A. remainder_mask_mode = False
B. remainder_mask_mode = True
C. include_panel_backgrounds = False (diagnostic only)
```

を比較。

見るもの:

```text
character presence
identity
side binding
background continuity
seam
unpainted holes
```

## 11. 第四の重要問題 — Global Character Guideの矩形線

Phase 3J単独人物WorkflowsではRegional CN offでもGlobal Character Guideのbbox outlineが有効なfixtureがあり、評価でも `shutter / door / panel` へ解釈されている。

Presence OracleではGlobal Character Guideも:

```text
include_character_bbox_outline = False
include_panel_border = False
```

を原則にする。

Canonical Character Guide:

```text
no panel border
no character bbox rectangle
no text labels
no diagonal box lines
only character body guide
```

Panel Layout ControlNetは別テスト。

## 12. Character Prompt Truthを先に証明

順序:

```text
1. CAST prompt contract
2. Binding override contract
3. PAGE_COMPILE_PLAN prompt
4. IMPACT_REGION_PLAN prompt
5. Mask isolation
6. Guide isolation
7. Runtime generation
```

画像を見て原因を推測する前にPrompt/Maskを検査する。

## 13. Presence Matrix v2

Contract修正後、まずHyper12 / seed42:

```text
Alice Left only
Alice Right only
Bob Left only
Bob Right only
```

条件:

```text
CAST prompt correct
prompt_override correct
character_prompt_mode = standalone
remainder_mask_mode = True
Global bbox outline OFF
Panel border OFF
Background-only Base
```

最低判定:

```text
subject exists
identity broadly correct
subject center direction matches target half
```

Exact containmentはまだ不要。

Single Character 4/4成立後:

```text
Alice Left / Bob Right
Bob Left / Alice Right
```

を比較。

Promptへleft/right位置語を入れずGeometryだけで位置を決める。

## 14. Canonical Character Prompt

Alice例:

```text
1girl,
blonde twin tails,
blue eyes,
school uniform,
pleated skirt,
full body
```

Bob例:

```text
1boy,
short black hair,
dark school uniform,
male student,
full body
```

Actingは `standing calmly` 程度。背景語を入れない。

## 15. Per-Region Hint再評価

Character Promptが正しく流れ、Remainder Scene Maskが成立してから `per_region_hint` を再評価。

Phase 3Jの:

```text
PER-REGION HINT V2: USABLE FOUNDATION
```

は分離して扱う。

```text
PER-REGION HINT V2 GEOMETRY:
PROMISING

PER-REGION HINT V2 CHARACTER SEMANTICS:
PENDING REVALIDATION
```

## 16. Shot Type PASSも分離

Phase 3Jの Full/Half/Bust は:

```text
SHOT TYPE GUIDE CONTRACT:
PASS
```

として維持。

Final Character Image SemanticはCharacter prompt contractが壊れたfixtureに依存するため:

```text
PENDING REVALIDATION
```

へ。

人物Presence成立後のみ:

```text
Alice full_body
Alice half_body
Alice bust
```

を同位置で生成し、Aliceが実際に存在してcropが変わることを確認する。

## 17. Canonical Fixture Builder

再発防止のため:

```text
make_canonical_character(...)
make_character_binding(...)
```

等のhelperを作ってよい。

Raw dictを各Phaseで手書きしない。

Canonical generatorは:

```text
assert character["prompt"].strip()
assert "prompt_override" in binding
```

相当をfail-closedで実行。

将来 `appearance -> prompt` / `acting -> prompt_override` をUI convenienceとして対応するなら、明示migration layerとして実装し、unknown-field preservationに依存しない。



## 18. New Canonical Workflows

新規最大6本:

```text
54_VERIFY_ALICE_LEFT_PROMPT_TRUTH_REMAINDER.json
55_VERIFY_ALICE_RIGHT_PROMPT_TRUTH_REMAINDER.json
56_VERIFY_BOB_LEFT_PROMPT_TRUTH_REMAINDER.json
57_VERIFY_BOB_RIGHT_PROMPT_TRUTH_REMAINDER.json
58_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_LR.json
59_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_SWAP.json
```

Zero-Touch必須。

比較の一部はrunner生成fixtureでもよいが、ユーザー確認が必要なものは固定Workflow化。

## 19. Runner

新規:

```text
scripts/run_phase3j1_character_presence_closure.py
```

段階:

```text
Contract tests
Mask diagnostics
Single 4
Two-character 2
Optional remainder A/B
Optional shot-type 3
```

## 20. Mask Diagnostic

Panel Scene remainder mask / Alice mask / Bob mask をContact Sheet化。

期待:

```text
Scene mask has holes exactly where characters are assigned.
```

Character masksはPanel polygon内にclipされる既存契約を維持。

## 21. Prompt Diagnostic JSON

出力:

```text
output/Tegaki/Phase3J1/phase3j1_prompt_truth.json
```

各Character:

```json
{
  "master_id": "char_alice",
  "cast_prompt": "...",
  "binding_override": "...",
  "compile_combined_prompt": "...",
  "impact_prompt": "...",
  "prompt_mode": "standalone"
}
```

## 22. Presence Result JSON

```text
output/Tegaki/Phase3J1/phase3j1_presence_results.json
```

各条件:

```text
runtime
visual status
expected subject
present
identity
expected side
observed side
extra subject
mask mode
prompt mode
guide mode
```

Visual provenance metadataはPhase 3I.2/3Jと同じ形式を保持。

## 23. Contact Sheets

最低限:

```text
Sheet U:
Legacy Broken Fixture | Contract-Fixed Fixture

Sheet V:
Scene Overlap | Remainder Mask | No Panel Region

Sheet W:
Alice L | Alice R
Bob L   | Bob R

Sheet X:
AliceL/BobR | BobL/AliceR

Sheet Y:
Full | Half | Bust
```

必要なものだけ生成。

## 24. Operational Profile

Hyper12の高速性は保持。

ただしPhase 3J.1で人物presenceが成立して初めて:

```text
OPERATIONAL AUTHORING PROFILE:
HYPER12
```

へ正式昇格可能。

Native20 Architecture Referenceは維持し、Prompt/Mask修正版fixtureを代表1ケースだけNative20でも実行して、Hyper12固有の成功かArchitecture全体の修復かを見る。

## 25. Live Browser E2E

今回の主Gateではない。

```text
POINTER CONTRACT SIMULATION: PASS
LIVE BROWSER POINTER E2E: PENDING
```

維持可。

人物presenceが回復してからUI操作テストの価値が上がる。

## 26. Phase 3Kへ進む条件

最低限:

```text
CAST prompt contract repaired
Binding prompt contract repaired
Impact Character Prompt truth PASS

Canonical character_prompt_mode = standalone

Remainder background mask effect understood

Global character guide:
bbox outline OFF
panel border OFF

Single Character:
Alice L/R, Bob L/R
at least 3/4 directional PASS
preferably 4/4

Two Character:
at least one 2/2 separated PASS

Shot Type:
Guide Contract PASS
Final Character Semantic at least one clear comparison PASS
```

## 27. Phase 3Kはその後

上記Gate通過後:

```text
Phase 3K
Pose & Interaction Authoring
+
Camera Distance / Scene Composition
```

へ進む。

この順序なら standing / facing / sitting が「人物が出ない問題」と混同されない。

## 28. Report

新規:

```text
PHASE3J_1_CHARACTER_PROMPT_AND_REGION_ISOLATION_REPORT.md
```

最低限:

```text
1. Phase3J Review Closure
2. Canonical Fixture Contract Bug
3. CAST prompt repair
4. Binding prompt repair
5. Compile prompt truth
6. Impact prompt truth
7. scene_composed vs standalone
8. Scene mask overlap diagnosis
9. remainder_mask_mode A/B
10. No-panel-region diagnostic
11. Global guide bbox/panel-border deconfounding
12. Alice Left
13. Alice Right
14. Bob Left
15. Bob Right
16. Two Character LR
17. Two Character Swap
18. Region Order Recheck
19. Per-Region Hint semantic revalidation
20. Hyper12 decision
21. Native20 representative
22. Shot Type semantic revalidation
23. Live Browser E2E
24. Known Issues
25. Phase3K Gate
26. Gemini独自判断
```

## 29. Sign-off

```text
PHASE3J REVIEW CLOSURE:
PASS WITH FIXTURE CORRECTION / HOLD

CAST PROMPT CONTRACT:
PASS / FAIL

BINDING PROMPT CONTRACT:
PASS / FAIL

COMPILE CHARACTER PROMPT TRUTH:
PASS / FAIL

IMPACT CHARACTER PROMPT TRUTH:
PASS / FAIL

CANONICAL CHARACTER PROMPT MODE:
STANDALONE / OTHER

SCENE REMAINDER MASK:
HELPFUL / NEUTRAL / HARMFUL

NO PANEL REGIONAL DIAGNOSTIC:
HELPFUL / NEUTRAL / NOT TESTED

GLOBAL GUIDE BBOX OUTLINE:
OFF

GLOBAL GUIDE PANEL BORDER:
OFF

ALICE LEFT V2:
PASS / PARTIAL / FAIL

ALICE RIGHT V2:
PASS / PARTIAL / FAIL

BOB LEFT V2:
PASS / PARTIAL / FAIL

BOB RIGHT V2:
PASS / PARTIAL / FAIL

TWO CHARACTER LR V2:
PASS / PARTIAL / FAIL

TWO CHARACTER SWAP V2:
PASS / PARTIAL / FAIL

SIDE BIAS V2:
NONE / LEFT / RIGHT / CHARACTER_DEPENDENT / SEED_DEPENDENT / MIXED

REGION ORDER EFFECT V2:
NONE / SIGNIFICANT / UNCLEAR

PER-REGION HINT GEOMETRY:
PROMISING / USABLE / REJECT

PER-REGION HINT CHARACTER SEMANTICS:
PASS / PARTIAL / FAIL

SHOT TYPE GUIDE CONTRACT:
PASS

SHOT TYPE FINAL CHARACTER SEMANTICS:
PASS / PARTIAL / PENDING

ARCHITECTURE REFERENCE:
NATIVE20

OPERATIONAL AUTHORING PROFILE:
HYPER12 / CONDITIONAL HYPER12 / UNRESOLVED

POINTER CONTRACT SIMULATION:
PASS

LIVE BROWSER POINTER E2E:
PASS / PENDING

USER VISUAL REVIEW REQUIRED:
YES / NO

PHASE3K:
GO / HOLD

NEXT RECOMMENDED PHASE:
```

## 30. Two-stage Commit

Commit A:

```text
fix(manga): Phase 3J.1 repair character prompt contract and isolate regional masks
```

内容:

```text
canonical fixture repair
prompt truth tests
remainder mask verification
standalone character prompt oracle
guide geometry deconfounding
workflows 54-59
presence runner
report
```

Commit A SHA取得後、Navigation Commit Bで `ComfyUIPortable/GITHUB.TXT` のReview TargetをCommit Aへ更新。

## 31. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3J_1_CHARACTER_PROMPT_AND_REGION_ISOLATION_REPORT Raw:

Character Prompt Contract Test Raw:
Impact Prompt Truth Test Raw:
Prompt Truth JSON Raw:
Presence Result Raw:

Impact Region Plan Raw:
Workflow Generator Raw:

Workflow54 Raw:
Workflow55 Raw:
Workflow56 Raw:
Workflow57 Raw:
Workflow58 Raw:
Workflow59 Raw:

PHASE3J REVIEW CLOSURE:
CAST PROMPT CONTRACT:
BINDING PROMPT CONTRACT:
COMPILE CHARACTER PROMPT TRUTH:
IMPACT CHARACTER PROMPT TRUTH:
CANONICAL CHARACTER PROMPT MODE:
SCENE REMAINDER MASK:
NO PANEL REGIONAL DIAGNOSTIC:
GLOBAL GUIDE BBOX OUTLINE:
GLOBAL GUIDE PANEL BORDER:
ALICE LEFT V2:
ALICE RIGHT V2:
BOB LEFT V2:
BOB RIGHT V2:
TWO CHARACTER LR V2:
TWO CHARACTER SWAP V2:
SIDE BIAS V2:
REGION ORDER EFFECT V2:
PER-REGION HINT GEOMETRY:
PER-REGION HINT CHARACTER SEMANTICS:
SHOT TYPE GUIDE CONTRACT:
SHOT TYPE FINAL CHARACTER SEMANTICS:
OPERATIONAL AUTHORING PROFILE:
LIVE BROWSER POINTER E2E:
USER VISUAL REVIEW REQUIRED:
PHASE3K:
NEXT RECOMMENDED PHASE:
```

# 最終方針

Phase 3J の最重要な結果は、「モデルが人物を出せない」と断定することではない。

現Canonical fixtureでは:

```text
CAST:
appearance
```

を使っていた一方、実Compiler契約は:

```text
prompt
```

を読む。

Bindingも:

```text
acting
```

を使っていた一方、Compiler契約は:

```text
prompt_override
```

を読む。

このためAlice/BobのIdentity PromptがRegional samplerまで正しく到達していなかった可能性が極めて高い。

さらに現在:

```text
character_prompt_mode = scene_composed
remainder_mask_mode = False
```

なのでCharacter Region内へScene Promptが入り、Panel Scene RegionもCharacter領域全体を重複被覆している。

加えてGlobal Character Guideのbbox rectangleが shutter / door として解釈されていた。

したがって次に必要なのはPoseではなく:

```text
Character Prompt Truth
+
Character / Scene Region Isolation
+
Guide Geometry Isolation
```

である。

これを閉じた上で人物が左右へ安定して出るなら、Phase 3KのPose / Interaction / Cameraへ進む。
