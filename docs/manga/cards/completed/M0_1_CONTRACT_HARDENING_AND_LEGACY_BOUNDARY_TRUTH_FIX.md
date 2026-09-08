# ComfyUI Portable — M0.1 / Phase 3M-0.1
# Contract Hardening & Legacy Boundary Truth Fix
## Antigravity2 / Gemini 3.8 向け Bounded Correction Card

## 推奨モデル

Gemini 3.8

今回の作業は、M0で作られた契約を捨てるものではない。

Claude Opus 4.6が設計・実装したM0は、

- TEGAKI_AUTHORING_DOCUMENT
- Scene / Frame分離
- page-normalized coordinates
- stable IDs
- simple / cast mode
- same CAST multi-instance
- pure operations
- legacy migration

という骨格を成立させた。

一方、Web GPT reviewで、M1へ進む前に修正すべき「契約境界の穴」と「Report上の過大主張」が見つかった。

今回はそれだけを直す。

UI、Backend、Pose、生成品質には進まない。

---

# 0. 現在の正本

必ず最初に:

ComfyUIPortable/GITHUB_ComfyUI.txt

を読む。

本Card発行時のReview Target:

5e57ae2f4f685e78e1b2b911baccb0a6b69292d1

M0 Implementation Commit:

5e57ae2f4f685e78e1b2b911baccb0a6b69292d1
feat(manga): establish versioned authoring contract and scene-frame separation

M0 Navigation Commit:

9e60c83a5fbf850f13ee0c2a81c57d5b5c82a2ed
docs(manga): publish M0 review target

作業開始時点のrepo事実を再確認し、moving mainではなく上記Review TargetをM0基準として読む。

---

# 1. M0 Review Verdict

M0の基本Architectureは ACCEPT。

ただし M1 GO ではなく、

ACCEPT WITH REQUIRED HARDENING
→ M0.1
→ M1

とする。

M0の60/60テストが通っていること自体は否定しない。

問題は、テストされていない境界条件と、Reportが実装より強く主張している箇所があること。

---

# 2. 修正対象ファイル

主対象:

- ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py
- ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/authoring_migration.py
- ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/authoring_operations.py

Test:

- ComfyUIPortable/scripts/test_m0_authoring_contract.py
- ComfyUIPortable/scripts/test_m0_authoring_operations.py
- ComfyUIPortable/scripts/test_m0_legacy_import.py

Docs:

- ComfyUIPortable/docs/reports/M0_3M0_VERSIONED_AUTHORING_CONTRACT_REPORT.md
- ComfyUIPortable/docs/STATUS.md
- ComfyUIPortable/docs/DOCUMENT_REGISTER.md
- ComfyUIPortable/GITHUB_ComfyUI.txt

必要ならM0.1専用Reportを追加。

---

# 3. Finding A — Foreign Key Validationの空集合バグ
# BLOCKER

現在の validate_document() ではCharacter InstanceのFK検証が概ね:

elif cast_ids and ref_cast not in cast_ids:

elif scene_ids and ref_scene not in scene_ids:

となっている。

これは CAST配列が空、かつ instance.cast_id が文字列として存在する場合、
cast_ids == empty set なのでFK違反が検出されない。

Scene側も同じ。

---

# 4. Finding A 修正要件

以下は必ずinvalid。

Character Instance exists
CAST collection empty
instance.cast_id = "ghost"

Character Instance exists
Scene collection empty
instance.scene_id = "ghost"

修正:

ref_cast not in cast_ids
ref_scene not in scene_ids

をコレクション空でも評価する。

---

# 5. Finding A Test追加

最低限:

- test_instance_rejected_when_cast_collection_empty
- test_instance_rejected_when_scene_collection_empty
- test_orphan_cast_reference_rejected
- test_orphan_scene_reference_rejected

既存のinvalid reference testはCAST / Sceneが最低1件存在するfixtureなので、この空集合holeを検出できていなかった。

---

# 6. Finding B — Legacy Importがinvalid documentを返し得る
# BLOCKER

import_from_legacy() は、legacy Character Bindingの character_id がCAST_SPECに存在しない場合でもInstanceを作れる。

さらにM0実装ではimport完了時に validate_document() を強制していない。

Finding AのFK holeと組み合わさると、invalid legacy inputが「validに見える」可能性がある。

---

# 7. Legacy Import Resultを機械可読にする

MigrationResultへ最低限:

- errors[]
- warnings[]
- valid

を持たせる。

既存APIとの互換を壊しにくい形で追加。

推奨:

MigrationResult.document
MigrationResult.errors
MigrationResult.warnings
MigrationResult.valid
MigrationResult.field_mapping_table

---

# 8. Legacy Import終了時Validation

import_from_legacy() 終了前に:

validate_document(imported_document)

を実行。

validation errorsを MigrationResult.errors へ反映。

M1以降は result.valid == False のdocumentをcompileしない。

---

# 9. Orphan Legacy Binding Policy

Legacy Character Bindingが character_id = Alice なのにCAST_SPECにAliceが無い場合、
推奨は FAIL CLOSED。

勝手にPlaceholder CASTを作らない。
勝手にbindingを捨てて成功扱いしない。

必要ならdocumentは診断用に保持してよいが valid=False にする。

---

# 10. Finding C — New → Legacy ExportのVisual Frame主張が実装と不一致
# MAJOR

M0 Report / export_to_legacy() docstringでは、Multiple scenes sharing one frame や Visual Frameとの不整合等をfail closedすると読める。

しかし現在のexport実装は page["visual_frames"] を実質参照せず、Scene.area をそのままLegacy REGION_SPECのpanel geometryへ出している。

したがって Scene geometry != Visual Frame geometry でもexportは成功し得る。

これはM0の最重要原則 Semantic Scene != Visual Panel Frame に対し、Legacy boundaryで黙って再conflationする危険がある。

---

# 11. Legacy Exportの意味を明確化する

無理に「全部Legacyへ戻せる」ようにしない。

以下を分ける。

A. Semantic Region export
B. Visual Frame export
C. Full legacy round-trip

Legacy REGION_SPECがsemantic regionsだけのexecution inputなら、そのことを明記し、

visual_frames are NOT represented by REGION_SPEC

とする。

逆に export_to_legacy() を「Authoring Document全体のround-trip export」と呼ぶなら、Visual Frameの表現不能をfail closedする必要がある。

---

# 12. 推奨方針

M0.1では以下を推奨。

## Semantic bridge

明示的に export_regions_to_legacy(...) 相当の意味を持つadapterを用意する。

これは Scenes / CAST / Instances だけを旧REGION_SPEC / CAST_SPECへ変換。

Visual Framesをexportしたふりをしない。

## Full legacy round-trip

既存 export_to_legacy() を残すなら、Legacy import由来の1:1 pairingが明示されていて、

Scene geometry == paired VisualFrame geometry

の時だけfull round-trip成功とする。

独立編集で両者がdivergeした場合は unsupported / fail closed。

---

# 13. Legacy Pairingはindex推測禁止

Visual FrameとSceneの対応を array index / orderだけ で推測しない。

Legacy import時に必要ならmigration metadataとして:

- legacy_slot_id
- legacy_frame_id
- legacy_scene_id

等の明示mappingを保存する。

名称は既存metadata設計と衝突確認後に決定。

---

# 14. Test — Scene / Frame Divergence

最低限:

import legacy
→ Sceneだけmove
→ Frameはそのまま
→ full legacy export

は FAIL CLOSED。

逆に Frameだけmove もfull round-tripではfail closed。

Semantic-region-only exportなら、Scene側だけを出すことを明示してTestする。

---

# 15. Finding D — page_normalized_to_koma_local がsilent clampする
# MAJOR

現在のreverse transformは x/y/w/h をLegacy KOMA-local [0,1]へclampする。

新契約ではInstanceがpage-normalizedで、Scene外へ出ること自体をvalidatorは禁止していない。

したがって、

InstanceがScene area外へはみ出す
→ legacy export
→ local座標へ変換時にclamp
→ geometryが静かに変わる

可能性がある。

これは No silent data discard / Lossy conversion diagnostics に反する。

---

# 16. Strict Reverse Transform

Legacy exportでは strict transform を使う。

Instance areaがScene geometry内でLegacy KOMA-localへlossless変換できない場合:

unsupported

へ追加しexport fail closed。

---

# 17. Test — Instance outside Scene

最低限:

Scene = x .2 .. .6
Instance extends outside Scene

Legacy exportは:

- must not silently clamp
- must report instance_id
- must fail closed

---

# 18. Finding E — move_sceneの境界clampで「同じdelta」が壊れる
# MAJOR

現在は Scene / Instance A / Instance B それぞれへ同じrequested deltaを足した後、各areaを個別にclampしている。

境界付近では Scene actual delta != Instance actual delta になり得る。

これはcontractの「Scene移動時、所属Instanceも同一delta」を破る。

既存Testは中央部のmoveしか見ていないため発見できない。

---

# 19. Scene Group Move Policy

推奨:

Scene + belonging Instances 全体について、Page bounds内に収まる最大の effective_dx / effective_dy を一度だけ計算。

その共通effective deltaを全対象へ適用。

個別clampしない。

これによりrelative geometryを維持。

---

# 20. Test — Boundary Scene Move

SceneまたはInstanceがpage edge付近にあるfixtureで requested dx = +0.5 等を行う。

確認:

- scene actual delta == every instance actual delta
- relative offsets unchanged
- all remain in bounds

---

# 21. Finding F — resize_sceneの個別clampによる比例関係破壊
# MAJOR

現在 resize_scene() はInstanceを比例変換した後 _clamp_area() を個別適用する。

変換結果がPage外へ出るケースでは、比例関係を静かに歪める。

---

# 22. Scene Resize Policy

推奨:

1. new Scene areaをvalidate
2. 全Instanceのproportional resultを事前計算
3. 全結果をvalidate
4. 1つでもPage bounds外ならoperation reject
5. 全validなら一括commit

個別clampして成功扱いしない。

---

# 23. Test — Resize Out of Bounds

InstanceがScene外側寄りにあるcaseでScene resizeするとInstanceがPage外へ出るfixtureを作る。

期待:

- ValueError / structured failure
- document unchanged

---

# 24. Frame MoveもSemanticsを明確化

move_frame() もrequested deltaをsilent clampする現在実装。

Frame単体なのでrelative relation問題は小さいが、API名 move by dx/dy に対しsilent clampがある。

以下のどちらかへ統一:

A. effective deltaでclampすることを明示
B. out-of-bounds requestはreject

Scene move policyとの一貫性を優先。

---

# 25. Finding G — Duplicate page_id未検出
# SHOULD FIX

現在 validate_document() は各Page内部IDを検証するが、Document内の page_id 重複を明示的に検出していない。

Stable Page IDを使う以上、duplicate page_idはreject。

Test追加。

---

# 26. ID ScopeをDocumentへ明記

Reportに:

page_id:
document-global unique

scene/frame/cast/instance/guide:
page-local unique

なのか、

all document-global

なのかを明記。

推奨:

page_id = document-global
child IDs = page-local FK scope

生成UUIDは実質globalでも、validation contractを曖昧にしない。

---

# 27. Finding H — make_area docstring truth

現在 make_area() は "Create a validated area" と読めるが、実際にはroundしてdictを返すだけでvalidateを呼ばない。

推奨は docstringをtruthfulに修正。

M0.1で無理にbehaviorを変えない。

---

# 28. Report Truth Correction

既存M0 Reportで以下を訂正。

特に:

- Legacy Export fail closed
- VisualFrame round-trip
- Lossless conversion
- 60/60 tests

60/60は当時Test suite上PASSだった事実として残してよい。

M0.1後は:

Original M0 suite: 60/60
M0.1 added regression tests: N/N

と分離。

---

# 29. M0 Reportを改竄しない

既存Reportを最新truthへ更新してよいが、M0時点で何をclaimしていたかが分からなくならないよう、

M0.1 Review Correction

sectionを追加することを推奨。

または別M0.1 Reportを正本にする。

---

# 30. 推奨M0.1 Report

新規:

ComfyUIPortable/docs/reports/M0_1_CONTRACT_HARDENING_REPORT.md

---

# 31. M0.1 Report必須項目

1. Baseline fixed SHA
2. Web GPT review findings
3. FK empty-collection bug
4. Legacy import validation
5. Legacy export semantic scope
6. Scene / Frame divergence policy
7. Strict reverse coordinate export
8. Boundary move semantics
9. Resize failure semantics
10. page_id uniqueness
11. New tests
12. Old tests regression
13. No UI/backend changes
14. Remaining known limitations
15. M1 readiness

---

# 32. M0.1 Tests

最低限追加:

FK:
- empty CAST orphan
- empty Scene orphan

Migration:
- legacy binding missing CAST
- imported document validation result

Export:
- scene/frame diverged
- frame/scene diverged
- instance outside scene
- semantic-only export scope

Operations:
- scene move at page edge
- relative offsets preserved
- scene resize producing out-of-bounds instance rejected
- frame boundary behavior

IDs:
- duplicate page_id rejected

---

# 33. 既存60 Testsは全部維持

M0.1修正後:

existing M0 60 tests
+
M0.1 regression tests

を全実行。

既存Testを削除してPASS数を作らない。

---

# 34. 実行Evidence

最終Reportへ:

- command
- test files
- passed
- failed
- skipped
- elapsed

を記録。

可能ならconsole summaryを保存。

---

# 35. Workflow Regression

引き続き workflow JSON unchanged を確認。

M0.1でWorkflow編集禁止。

---

# 36. Runtime Boundary

今回も変更禁止:

- scene_compiler.py
- impact_region_plan.py
- manga_impact_regional_adapter.py
- KSampler
- ControlNet
- workflows
- frontend JS
- Canvas UI

ただしM0新module3本とtests/docsは修正可。

---

# 37. UI禁止

今回作らない:

- Scene Canvas
- Resolution UI
- Style Template UI
- Prompt Inspector
- Seed UI
- Generate UI

それはM1。

---

# 38. Pose / Interaction禁止

今回 Pose / Handshake / SubScene / Interaction を拡張しない。

metadata preservationのみ維持。

---

# 39. Backend比較禁止

今回 Inspire / Advanced-ControlNet / Attention Couple / Comic Creator fork の比較を開始しない。

---

# 40. M1 Gate

M0.1完了後にのみ:

M1 / 3M-1
Scene-only Minimum-Hand Draft

へ進む。

---

# 41. M1へ進めるAcceptance

以下すべて必要。

FK EMPTY COLLECTION: PASS

LEGACY IMPORT ALWAYS VALID OR EXPLICIT INVALID: PASS

LEGACY EXPORT SCOPE TRUTHFUL: PASS

SCENE / FRAME DIVERGENCE:
NO SILENT CONFLATION

INSTANCE OUTSIDE SCENE:
NO SILENT CLAMP

BOUNDARY SCENE MOVE:
COMMON EFFECTIVE DELTA OR EXPLICIT REJECT

SCENE RESIZE:
NO INDIVIDUAL SILENT CLAMP

DUPLICATE PAGE ID:
REJECTED

OLD 60 TESTS:
ALL PASS

NEW M0.1 TESTS:
ALL PASS

WORKFLOW JSON MODIFIED:
NO

UI MODIFIED:
NO

BACKEND MODIFIED:
NO

---

# 42. Current Entry Publication Status修正

現在GitHub remoteから 5e57ae2f と 9e60c83a の両Commitを取得できている。

したがって GITHUB_ComfyUI.txt に残る

Push to remote is pending Owner execution
Published in local repository

は現在事実と矛盾する。

M0.1 Commit Bで Published on remote main 等、現在事実へ更新。

---

# 43. Commit A

推奨:

fix(manga): harden M0 authoring contract boundaries

含む:

- authoring_contract.py
- authoring_migration.py
- authoring_operations.py
- tests
- M0.1 report
- STATUS / DOCUMENT_REGISTER

---

# 44. Commit B

推奨:

docs(manga): publish M0.1 review target

GITHUB_ComfyUI.txt:

- Review Target Commit SHA = Commit A
- Current card = M0.1 completed
- Next card candidate = M1
- publication truth corrected

---

# 45. Push

Owner運用に従う。

実際にremote mainへ反映したら PUSHED。
localのみなら LOCAL ONLY。

Entryと最終回答を一致させる。

---

# 46. 最終回答Format

MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
5e57ae2f...

M0.1 IMPLEMENTATION COMMIT A:
M0.1 NAVIGATION COMMIT B:
PUSH STATUS:

FK EMPTY CAST:
FK EMPTY SCENE:
LEGACY IMPORT VALIDATION:
ORPHAN LEGACY BINDING:
LEGACY EXPORT SCOPE:
SCENE/FRAME DIVERGENCE:
STRICT INSTANCE EXPORT:
BOUNDARY SCENE MOVE:
SCENE RESIZE STRICTNESS:
FRAME MOVE POLICY:
DUPLICATE PAGE ID:

ORIGINAL M0 TESTS:
NEW M0.1 TESTS:
TOTAL TESTS:
WORKFLOW REGRESSION:

UI CHANGED:
BACKEND CHANGED:
POSE/INTERACTION CHANGED:

M0.1 REPORT:
M1 READY:
YES / NO

USER ACTION REQUIRED:

---

# 47. 最終原則

M0のArchitectureは維持する。

今回直すのは「契約が正しい」だけではなく、「契約境界で嘘をつかない」こと。

特に:

Semantic Scene != Visual Frame

page-space Instance != legacy panel-local Instance

requested move != individual clamp result

を黙って同一視しない。

M0.1完了後、Web GPTが固定SHAをレビューしてからM1へ進む。
