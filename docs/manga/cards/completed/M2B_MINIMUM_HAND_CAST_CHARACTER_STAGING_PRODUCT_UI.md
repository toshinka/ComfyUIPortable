# ComfyUI Portable — M2B / Phase 3M-2B
# Minimum-Hand CAST & Character Staging Product UI
## — Rough Region + Free Text + Hidden Automatic Spatial Helper —
## Antigravity2 / Gemini 3.8 向け Bounded Product Integration Card

## 推奨モデル

Gemini 3.8

---

# 0. このCardの目的

M0〜M2A.1で研究してきた能力を、初めて「ユーザーが普通に触るMainline UI」へまとめる。

M2Bの中心は:

Resolution / Style / Seed
→ CAST Master
→ Semantic Scene
→ Character Rough Region
→ Free Text Acting Prompt
→ Generate / Seed Brainstorm

今回のProduct方針:

Option A+
= Rough Region
+ Free Text Prompt
+ Hidden Automatic Spatial Helper

ControlNetはCoreへ入れない。
Pose selector、Camera selector、strength sliderもCoreへ入れない。

---

# 1. 最初に必ず読むもの

最初に:

ComfyUIPortable/GITHUB.TXT

次に:

ComfyUIPortable/GITHUB_ComfyUI.txt

本Card発行時のReview Target:

7e9528d751959b62e108aaad8df363548855df92

M2A.1 Implementation Commit:

7e9528d751959b62e108aaad8df363548855df92

remote上のM2A.1 Navigation Commit:

408744b1906349fa3fa9a290bd136706bcc4b45f

注意:
Gemini前回報告の 408744b1bbf8476d059ae21d9ae875faae1baae2 はremote実SHAと一致しない。
repo事実を優先。

また、remote mainにはM2A.1 Commit A / Navigationが既に存在するため、「LOCAL ONLY / Owner push待ち」という旧報告は現在事実と一致しない。次Navigation更新時にpublication wordingを修正すること。

---

# 2. Web GPT Review Verdict

M2A.1の骨格: ACCEPT。

確認された重要点:
- 2-character baseline: 2/8 useful
- horizontal hidden hint: 5/8 useful
- presence hint追加: horizontal-onlyに対して改善なし
- depth geometry-only: 1/8 useful
- derived depth hint: 5/8 useful
- 3 distinct: 1/8 useful、horizontal/presence hintでも改善ほぼ無し
- weak block CN 0.20: ineffective
- weak block CN 0.35: artifacts / stiffness
- same CAST across separate Scenes: 4/4 PASS

よって:

M2B: GO
Core: 1–2 character brainstorming
3+: Advanced / Seed-Sensitive
4+: Experimental / Multi-Cut recommended

---

# 3. 「Production Ready」の意味を限定する

M2Bで「2 characters = deterministic placement」とは書かない。

正しいProduct表現:

2-character rough staging is Brainstorm-Ready.
With the hidden spatial helper, useful drafts appeared in 5/8 fixed seeds.

つまり「1回で絶対に決めるツール」ではなく、「2〜3 seedを回して良いDraftを拾う」ことを想定する。
これはMinimum-Hand方針と一致する。

---

# 4. M2A.1 Spatial HelperからProduction採用する部分

採用:
- Horizontal character hints for clear 2-character layouts
- Derived depth hints for clear area-ratio depth layouts

採用しない:
- 3-person presence hint
- 4-person presence hint
- full research mode
- ControlNet baseline

理由:
B2 presence hint == B1 horizontal hint
3-person H0/H1/H2 all 1/8 useful
であり、presence phraseはProduction defaultにする根拠がない。

---

# 5. Production Auto Spatial Policy

Research用の off / horizontal / horizontal_presence / spatial_depth / full をユーザーに選ばせない。
Productionは AUTO。
Sceneごとに自動解決する。

---

# 6. AUTO Policy

## 0 characters
OFF

## 1 character
OFF
理由: single-character area trackingは既に十分強い。

## 2 characters
Area ratio max(area) / min(area) >= 1.8 かつ有効な大小差がある場合:
SPATIAL_DEPTH

それ以外:
HORIZONTAL

## 3+ characters
OFF をProduction default。
理由: M2A.1ではhorizontal/presence helperで改善しなかった。
3+はUI warningとSeed Brainstormへ送る。

---

# 7. AUTO Policyで未実証のfull modeを使わない

full / horizontal_presence をProduct defaultへしない。
Research APIとして残してよい。

---

# 8. Derived HintはAuthoring SSOTへ保存しない

TEGAKI_AUTHORING_DOCUMENT には CAST identity prompt / Instance acting prompt / areas だけ。
Derived left/right/foreground/backgroundはcompile-time。

---

# 9. Research Overrideを隠す

現在TegakiMinimumHandSceneEditorには spatial_hint_mode native widgetが露出している。
M2B Product UIではユーザーへ見せない。

推奨:
production auto policy をserver execution defaultとし、research runnerだけexplicit modeを呼べる構造へする。

---

# 10. Debugでは透明性を維持

Debug JSON:
- spatial_policy = auto
- resolved_scene_hint_mode
- raw_identity_prompt
- raw_acting_prompt
- derived_spatial_hint
- effective_character_prompt

を保持。

---

# 11. M2Bは既存Minimum-Hand Editorを拡張する

Mainlineは TegakiMinimumHandSceneEditor を継続利用。
新たにCAST Node / Character Node / Staging Node / Prompt Nodeをユーザーへ別々に並べない。

---

# 12. 過去のCAST / Staging EditorはReference

既存 TegakiMangaCastMaster / TegakiMangaCharacterStagingEditor / cast_master_editor.js / character_staging_editor.js は実装pattern参考として読んでよい。
しかしM2B Mainlineは TEGAKI_AUTHORING_DOCUMENT 一つへ統合。
旧CAST_SPEC等を新Mainlineの編集正本へ戻さない。

---

# 13. Node Internal ID互換

内部class / node type TegakiMinimumHandSceneEditor は既存Workflow互換のため残してよい。
Display NameはProduct方向へ変更推奨:
Tegaki Minimum-Hand Manga Authoring (Draft)

JS Headerも M1 Scene-Only からProduct-facing名称へ変更。

---

# 14. Canonical Workflowを安定名へRename

現在:
workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json

M2Bで一度だけ:
workflows/MINIMUM_HAND_MANGA_DRAFT.json

へgit mvすることを推奨。
理由: 今後M3/M4ごとにWorkflow名を増やさないため。

---

# 15. Workflow Root Policy

最終:
workflows/
├ MINIMUM_HAND_MANGA_DRAFT.json
├ README.md
└ Archive/

root active workflow 1本を維持。
旧M1ファイルをrootへコピーとして残さない。

---

# 16. Archiveは変更しない

workflows/Archive/ は過去研究資産。今回触らない。

---

# 17. Product UIの見え方

一つのAuthoring Node内で上から:
GLOBAL
CAST
CANVAS
SELECTED SCENE
SELECTED CHARACTER

程度。

---

# 18. GLOBAL Section

最上部:
Resolution
Style
Seed
[Randomize Seed]

既存presetsを維持。
Custom Resolution / Custom Styleは今回必須でない。

---

# 19. Seedを重要な操作として見せる

2-characterが62.5% usefulである以上、Seed Brainstormは逃げではなく正式UX。
最低限 Seed value / Randomize Seed。

---

# 20. Generate x4はまだ作らない

Candidate Browser / Batch Brainstormは後段。
M2Bでは Randomize Seed → Queue が明確ならよい。

---

# 21. CAST Section

最低限:
[Character A] [Character B] [+ Add CAST]
のchip / tab型。

Selected CAST:
Display Name
Identity Prompt

---

# 22. CAST Advanced

折りたたみ:
Negative Prompt
程度。

今回前面へ出さない:
LoRA / Reference Image / IPAdapter / Pose Asset。
Document fieldは壊さず保持。

---

# 23. LoRAはM2B Gateにしない

M2A/M2A.1はtext identityだけで空間能力を測った。
Region-local LoRAは別問題。
M2Bへ無理に混ぜず DEFERRED。

---

# 24. CAST ID

表示名Aliceを変更してもcast_idは変えない。Stable identity。

---

# 25. CAST Add

新CAST:
unique cast_id / display_name / identity_prompt / negative_prompt / metadata。
ID生成はcollision-free。Array lengthから単純生成しない。

---

# 26. CAST Delete

CASTがCharacter Instanceに参照されている場合、silent cascade delete禁止。
推奨: Delete disabled または "Remove appearances first" message。

---

# 27. Scene UIを壊さない

M1のScene rectangle / Scene name / Scene prompt / Add/Remove / drag/resizeを維持。

---

# 28. Scene Promptの意味

Cast Sceneでは:
common background / common event / scene context。
人物identityはCAST。人物の個別演技はInstance。

---

# 29. Simple Sceneも維持

M2Bは全SceneをCAST必須にしない。
一つのPageに Scene A=simple / Scene B=cast を許可。

---

# 30. Add CharacterでCast Modeへ

Selected Sceneがsimpleで、ユーザーが初めてCharacter Instanceを追加した場合 input_mode=cast へ自動切替してよい。
ただしScene Promptを削除・解析・書換えしない。

---

# 31. Mode変更でPromptを破壊しない

simple→cast時に1girl/student等を自動消去しない。
必要ならUIに小さく "Scene Prompt is preserved as common context." と表示。

---

# 32. Scene Modeを過度に前面へ出さない

通常 Characterを追加 → CAST scene でよい。
Advancedに Use as Simple Scene 等を置くのは可。

---

# 33. CanvasにCharacter Rough Regionを統合

Scene rectangleと同じCanvasへCharacter Instance Rectangleを描画。

---

# 34. Canvas Visual Hierarchy

Scene: thin / translucent border
Character: stronger colored box
label: Alice / Bob

SceneとCharacterの意味が見た目で区別できること。

---

# 35. Character color

Castごとに安定colorを割当。
同一CASTの別Instanceはsame base color + Alice #1 / Alice #2等で識別。

---

# 36. Canvas Selection

クリック:
Scene area → Scene select
Character box → Character Instance select

別の大きなMode selectorを増やさず、selectionで編集対象を決めることを第一候補とする。

---

# 37. Character Drag

Selected Character boxをdrag/resize。
page-normalized instance.areaへ即反映。

---

# 38. Character boxはScene内へ基本clip

M2B UIではCharacter Instanceを親Semantic Scene内へ保つことを第一候補。
ただしAuthoring Contract自体へ永続的な「必ずinside」の制約を追加しない。

---

# 39. Scene Move時

M1 JSはCharacter Instanceが無かった。
M2BではScene移動時、Scene + belonging Character InstancesへM0 contractと同じcommon effective deltaを適用。
Sceneだけ動かしてCharacterが取り残されるのは禁止。

---

# 40. Scene Resize時

Scene resize時、belonging Character Instancesを比例変換。
M0 resize_scene() semanticsと一致。
個別silent clampでrelative positionを壊さない。

---

# 41. JS Operation Parity

Frontend operationはM0/M0.1 Python contract semanticsと一致させる。
JS test必須: move scene with characters / resize scene with characters。

---

# 42. Scene Delete時

Sceneを削除したら、そのSceneに属するCharacter Instancesはorphanにしない。
推奨: confirmation → delete Scene + its Instances → keep CAST Masters。

---

# 43. Scene Delete Test

Scene A + Alice/Bob Instancesをdelete後:
Alice/Bob CAST Masters remain
Instances removed
validate_document PASS。

---

# 44. Add Character UI

Selected Scene Inspector:
Characters in Scene [Alice] [Bob] [+ Add]
または同等。

---

# 45. Add Character from CAST

+ Add は既存CAST Master一覧から選択。
CASTが0件ならAdd CAST firstへの明確な導線。

---

# 46. Instance ID

Character追加ごとにunique instance_id。
同一CASTを別Sceneへ追加しても別ID。

---

# 47. Same CAST Across Scenes

CORE。
CAST Alice / Scene1 Alice Instance A / Scene2 Alice Instance B を普通に可能にする。
M2A.1で4/4成功した重要能力。

---

# 48. Same CAST Twice Same Scene

許可してよい。
ただし2件目を同じSceneへ追加したら Advanced / Seed-Sensitive warning。
禁止しない。

---

# 49. 3+ Character Warning

Scene instance count == 3:
"3 characters — Advanced / Seed-Sensitive. Try new seeds or split the scene if needed."
程度。

---

# 50. 4+ Character Warning

"4+ characters — Experimental. Multi-cut / additional scenes are usually more reliable."
ControlNet設定を急に表示しない。

---

# 51. Warningは邪魔しない

Modal連発は禁止。小さいstatus / badgeでよい。

---

# 52. Selected Character Inspector

最低限:
Character: Alice
Acting Prompt

---

# 53. Acting PromptはFree Text

Placeholder例:
standing casually / reading a book / sitting on a chair / looking away / walking。
Preset selectorを主にしない。

---

# 54. Pose Selectorを追加しない

M2Aではsitting on a chairが通る例はあるが1 seed result。
これを理由にPose dropdownをCoreへ戻さない。

---

# 55. Distance selectorを追加しない

Near/Far等も現時点ではFree Text + Auto Depth Hint。
User-facing Near/Mid/Far buttonsは後段。

---

# 56. Strength Sliderを追加しない

Character Strength 1.0をinternal default維持。
M2A.1でUI sliderの根拠なし。

---

# 57. Hidden Spatial Helper — Product Behavior

ユーザーが2人のboxを左右へ置いたら内部で on the left side / on the right side。
ユーザーが明確な大小差を作ったら内部で large in the foreground / smaller in the background。

---

# 58. Helper OFF conditions

以下では無理にhintしない:
1 character / ambiguous overlap / 3+ characters / unclear size ratio。

---

# 59. Presence HintをDefaultで付けない

M2A.1でB2==B1、H2==H1。
よってtwo distinct people...等はProduction defaultにしない。
Research optionとして残してよい。

---

# 60. Default AUTOのUnit Test

最低限:
1 char -> off
2 equal-ish left/right -> horizontal
2 ratio >=1.8 -> spatial_depth
2 ambiguous -> no forced hint
3 chars -> off
4 chars -> off

---

# 61. Auto HelperはScene単位

Page全体でmodeを一つ選ばない。
例: Scene1=1 char off / Scene2=2 char horizontal / Scene3=2 char depth。

---

# 62. Debug UI

通常ユーザーには出さなくてよい。
Advanced Debugに raw / auto hint / effective を確認できれば十分。

---

# 63. Canvas Preview

既存preview tensorはScene regions + Character rough regionsを描ける。
M2B UI CanvasとServer previewで同じdocument geometryを表示していることを確認。

---

# 64. Seed Randomize

Custom DOM内に Randomize を追加。
安全な整数範囲でseed更新。
更新先: page.generation.seed。
Backend seed outputとのSSOT一致を維持。

---

# 65. Randomizeで即Queueしない

Randomizeはseedだけ変更。Generate/Queueはユーザー操作。

---

# 66. Canonical Sample

Default M2B Workflowは既存M1 simple sampleを壊さなくてよい。
起動時 Simple Scene sample / CAST empty でもよい。
M2B test fixtureでCAST pathを実証。

---

# 67. Reset 2-Sceneの破壊性

現在ResetはDocument全体を作り直す。
M2BでCASTが存在する状態だとCAST Masterまで消す。

以下のどちらかに修正。
推奨: Reset Draftへ名称変更し、CAST/Scene/Instanceを全削除することを明示してconfirm。
またはReset LayoutとしてCASTを保持する別挙動。
黙ってCASTを消さない。

---

# 68. Product-facing Workflow Name

M2B Commit Aで M1_MINIMUM_HAND_SCENE_DRAFT.json を MINIMUM_HAND_MANGA_DRAFT.json へrenameする場合、tests / README / runner refsを全部更新。
rootに両方残さない。

---

# 69. README

workflows/README.md:
MINIMUM_HAND_MANGA_DRAFT.json = current canonical workflow
Archive/ = historical research
を明確に。

---

# 70. Backend

維持:
TEGAKI_AUTHORING_DOCUMENT → PAGE_COMPILE_PLAN → TegakiMangaConditioningBuilder → Core KSampler。
Impactへ切替えない。

---

# 71. ControlNet

M2B Core: OFF。
M2A.1のCN 0.20/0.35 branchをCanonical Workflowへ混ぜない。

---

# 72. Future Rough Guideの余地

M3以降rough manga / dummy guideを追加できるが、M2B UIにControlNet controlsを先置きしない。

---

# 73. Browser E2E

M1.1でBrowser E2EはPENDINGだった。
M2Bでは可能な限り実ComfyUI browserで閉じる。

---

# 74. Browser Scenario A — Simple regression

Canonical Workflow load。
Simple Scene / Prompt edit / Seed randomize / Queue。
画像生成成功。

---

# 75. Browser Scenario B — Add CAST

Add CAST
Name = Alice
Identity Prompt = blonde twin tails, blue eyes, school uniform

Save/reload後も保持。

---

# 76. Browser Scenario C — Single Character

Selected SceneへAlice追加。
Character boxをleftへdrag。
Acting: standing casually。
Queue。
確認: Alice appears roughly left。

---

# 77. Browser Scenario D — Two Character

Bob CAST追加。
SceneへBob instance追加。
Alice left / Bob right。
Free text acting。

AUTO helper debug:
Alice -> on the left side
Bob -> on the right side

Queue。

---

# 78. Two-character E2Eの判定

1回FAILでもProduct FAILにしない。
最大3 seedsで at least 1 useful draft をProduct-path sanityとして確認。
M2A.1の8-seed benchmarkを再実施しない。

---

# 79. Browser Scenario E — Depth

Alice box large / Bob box small / area ratio >=1.8。
AUTO debug:
Alice -> large in the foreground
Bob -> smaller in the background
Queue。

---

# 80. Browser Scenario F — Repeated CAST across Scenes

Scene1 Alice instance / Scene2 same Alice CAST new instance_id。
Save/reload。Queue。

---

# 81. Browser Scenario G — Scene move with Character

SceneにAlice/Bobがいる状態でSceneをdrag。
Scene/Alice/Bobがcommon deltaで移動。

---

# 82. Browser Scenario H — Scene resize with Character

Scene resize。
Character relative placementが比例。validation PASS。

---

# 83. Browser Scenario I — Delete Scene

Character付きScene削除。
Instances removed / CAST masters remain / No orphan refs。

---

# 84. Browser Scenario J — Save / Reload

最低限保存確認:
Resolution / Style / Seed / CAST Masters / Identity Prompts / Scenes / Scene Prompts / input_mode / Character Instances / instance_id / Character areas / Acting Prompts。

---

# 85. Browser Scenario K — 3 Character Warning

3rd CAST instance追加。
warning appears / no ControlNet UI appears / generation still allowed。

---

# 86. Browser E2E Truth

実ブラウザで触っていない場合 PENDING。
JS testをBrowser PASSと呼ばない。

---

# 87. UI Screenshot Evidence

可能なら docs/verification/m2b/ へ:
M2B_UI_SIMPLE.png
M2B_UI_TWO_CAST.png
M2B_UI_REPEATED_CAST.png
等。

---

# 88. Runtime Image Evidence

最低限:
M2B_single_char.png
M2B_two_char_seedX.png
M2B_depth_seedX.png
M2B_same_cast_multi_scene.png
程度。
大量生成不要。

---

# 89. Manifest

docs/verification/m2b/M2B_PRODUCT_PATH_MANIFEST.json。
各条件: runtime_status / visual_status / review_method / seed / scene count / cast count / instance count / auto hint modes / output / notes。

---

# 90. Visual Truth

自動でvisual PASSにしない。直接見た時のみ DIRECT_IMAGE_INSPECTION。

---

# 91. Automated Tests

既存139 testsを全部維持。

---

# 92. 新規Python Test候補

test_m2b_auto_spatial_policy.py
test_m2b_cast_instance_authoring.py
test_m2b_product_document_roundtrip.py

---

# 93. 新規JS Test候補

test_m2b_minimum_hand_editor.mjs 等。

---

# 94. Python Test必須

- auto policy 1 char off
- auto policy 2 char horizontal
- auto policy 2 char depth
- auto policy 3+ off
- research modes still explicit-call compatible
- add cast
- stable cast id
- add instance
- stable instance id
- same CAST multi-scene
- same CAST same-scene allowed
- missing FK fail closed
- scene delete cascade instances only
- cast delete referenced rejected
- roundtrip persistence

---

# 95. JS Test必須

- Add CAST
- Edit identity prompt
- Add instance
- Character select
- Character drag
- Character resize
- Acting prompt persistence
- Scene move carries children
- Scene resize scales children
- Delete scene no orphan
- Save/reload mock lifecycle
- 3+ warning
- Randomize seed sync

---

# 96. M0〜M2A.1 Regression

全てPASS。既存testを削除して数を合わせない。

---

# 97. Workflow Structural Test

root active JSON = 1。
Canonical workflowで Authoring Editor seed -> KSampler / width,height -> Latent / page_compile_plan -> ConditioningBuilder を維持。

---

# 98. Research mode leakage test

Canonical workflow内にspatial_hint_mode user-tunable研究dropdownが露出していないこと。
Production AUTOが使われること。

---

# 99. M2B Report

新規:
docs/reports/M2B_MINIMUM_HAND_CAST_STAGING_PRODUCT_UI_REPORT.md

---

# 100. Report必須内容

1. Baseline fixed SHA
2. M2A.1 review decision
3. Product AUTO helper policy
4. Research controls hidden
5. Canonical workflow rename/root policy
6. Global UI
7. CAST UI
8. Scene UI regression
9. Character rough region UI
10. Acting Prompt
11. Stable IDs
12. Mixed simple/cast
13. Same CAST multi-scene
14. 3+ warning policy
15. Scene move/resize child semantics
16. Scene/Cast delete policy
17. Seed randomize
18. Browser E2E
19. Runtime evidence
20. Visual evidence
21. Hand count
22. Automated tests
23. Known limits
24. Deferred features
25. Next recommendation

---

# 101. Hand Count

最低限測る。
- 既存2-Scene Simple sample: Prompt edit / Seed randomize / Queue
- 1 CAST追加してSceneへ置くまで
- 2 CAST追加して左右へ置くまで

目的: Minimum-Handが本当に維持されたか確認。

---

# 102. UI Complexity Gate

初見画面に以下を出さない:
ControlNet strength / Pose preset / Camera distance preset / character_strength / mask feather / set_cond_area / spatial_hint_mode / SubScene / Interaction / LoRA region tuning。

---

# 103. M2B Acceptance Gates

M0–M2A.1 REGRESSION: PASS
CANONICAL ACTIVE WORKFLOW: 1
PRODUCT WORKFLOW NAME: STABLE / VERSIONLESS
AUTHORING DOCUMENT SSOT: PASS
SIMPLE SCENE REGRESSION: PASS
CAST ADD/EDIT: PASS
CAST STABLE ID: PASS
CHARACTER INSTANCE ADD: PASS
INSTANCE STABLE ID: PASS
CHARACTER DRAG: PASS
CHARACTER RESIZE: PASS
ACTING PROMPT: PASS
SAME CAST ACROSS SCENES: PASS
AUTO SPATIAL HELPER: PASS
AUTO 1 CHAR OFF: PASS
AUTO 2 CHAR HORIZONTAL: PASS
AUTO 2 CHAR DEPTH: PASS
AUTO 3+ OFF: PASS
PRESENCE HINT DEFAULT: NO
RESEARCH MODE USER-FACING: NO
SCENE MOVE CARRIES INSTANCES: PASS
SCENE RESIZE SCALES INSTANCES: PASS
SCENE DELETE ORPHANS: NONE
CAST DELETE ORPHANS: NONE
SEED RANDOMIZE: PASS
3+ WARNING: PASS
CONTROLNET CORE: OFF
POSE UI: NOT ADDED
STRENGTH UI: NOT ADDED
BROWSER E2E: PASS / PENDING
RUNTIME SAMPLE: PASS
SAVE/RELOAD: PASS / PENDING

---

# 104. M2B Product Status

以下から: PASS / PARTIAL / HOLD。
Browser E2Eが完全PENDINGならPARTIALを推奨。

---

# 105. Known Limitsを隠さない

1 char: strong
2 chars: brainstorm-ready, seed-sensitive
3 chars: advanced / seed-sensitive
4+: experimental / multi-cut recommended

ただし毎回大きく表示する必要はない。

---

# 106. M2Bで「3人不可」とhard capしない

DocumentとUIは3+を保持可能。warningだけ。
将来Control/model改善の余地を残す。

---

# 107. M2Bで自動Multi-Cutを作らない

4人を入れた瞬間Sceneを勝手に分割しない。Recommendationのみ。

---

# 108. M2BでControlNetへ自動Escalateしない

3人になったら自動ControlNet ONは禁止。M2A.1で0.35が有害だった。

---

# 109. M2BでPromptを長文化しすぎない

AUTO helperは短く。left/right/foreground/background程度。

---

# 110. Next Phase候補

M2Bが通った後の優先候補:
M3 — Rough Manga / Visual Panel Guide Integration

Semantic Scene / CAST staging
+
rough white-dummy manga / user rough guide
+
Visual Panel Frame Control

へ進む。

---

# 111. M3の意味

M2Bまで: 誰が / どのSceneに / だいたいどこ。
M3: 実際の漫画枠 / 粗い人物シルエット / 構図拘束を直交して足す。
Pose Editorではない。

---

# 112. Candidate Browserはその後でもよい

Generate x4 / thumbnail compare / reuse seed は高価値だが、M2BではSeed randomizeまで。

---

# 113. Commit A

推奨:
feat(manga): integrate minimum-hand CAST and character staging UI

含む:
minimum_hand_scene_editor.py
minimum_hand_scene_editor.js
auto helper production policy
tests
canonical workflow rename/update
README
verification
M2B report
STATUS / DOCUMENT_REGISTER

---

# 114. Commit B

推奨:
docs(manga): publish M2B review target

GITHUB_ComfyUI.txt:
Review Target = Commit A
Current card = M2B completed / partial
Next = M3 or correction

---

# 115. Publication wording

remote実態と一致させる。
既にpush済みならPublished on remote main。
localのみならLOCAL ONLY。
報告SHAとremote SHAが違う場合はremote SHAを別途明記。

---

# 116. 最終回答Format

MODEL USED:
Gemini 3.8

BASELINE REVIEW TARGET:
7e9528d751959b62e108aaad8df363548855df92

M2B IMPLEMENTATION COMMIT A:
M2B NAVIGATION COMMIT B:
PUSH STATUS:

CANONICAL WORKFLOW:
ACTIVE ROOT WORKFLOW COUNT:

DISPLAY NAME:
AUTHORING SSOT:

GLOBAL UI:
CAST UI:
SCENE UI:
CHARACTER ROUGH REGION:
ACTING PROMPT:
SEED RANDOMIZE:

AUTO HELPER POLICY:
1 CHAR MODE:
2 CHAR NORMAL MODE:
2 CHAR DEPTH MODE:
3+ MODE:
PRESENCE HINT DEFAULT:
RESEARCH MODE EXPOSED:

CAST STABLE IDS:
INSTANCE STABLE IDS:
SAME CAST MULTI-SCENE:
SAME CAST SAME-SCENE:

SCENE MOVE CHILDREN:
SCENE RESIZE CHILDREN:
SCENE DELETE:
CAST DELETE:

3+ WARNING:
CONTROLNET CORE:
POSE UI:
STRENGTH UI:

BROWSER SIMPLE:
BROWSER CAST:
BROWSER CHARACTER DRAG:
BROWSER TWO-CHAR:
BROWSER DEPTH:
BROWSER REPEATED CAST:
BROWSER SAVE/RELOAD:

HAND COUNT SIMPLE:
HAND COUNT 1-CHAR:
HAND COUNT 2-CHAR:

OLD TESTS:
NEW TESTS:
TOTAL:

MANIFEST:
UI SCREENSHOTS:
RUNTIME OUTPUTS:
REPORT:

M2B STATUS:
PASS / PARTIAL / HOLD

NEXT RECOMMENDED CARD:
M3 / correction

OWNER REVIEW RECOMMENDED:
YES / NO
CONDITIONS:

USER ACTION REQUIRED:

---

# 117. 最終原則

M2A.1で得た答えをProductへ素直に落とす。

1人: Regionだけで強い
2人: Region + hidden horizontal/depth hint + Seed Brainstorm
3人: Advanced / seed-sensitive
4+: Multi-cut / future guide

ユーザーへ必要以上のControlを見せない。

CASTを作る
Sceneへ置く
矩形を動かす
普通のPromptを書く
Seedを回す

でまず漫画Draftが出ることをM2Bの成功条件とする。
