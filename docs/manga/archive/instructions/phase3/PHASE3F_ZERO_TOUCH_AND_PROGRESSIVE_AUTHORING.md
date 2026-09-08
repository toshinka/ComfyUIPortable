# ComfyUI Portable Phase 3F — Zero-Touch Workflow Parity & Progressive Panel / Scene Authoring UI 指示書

## 0. Baseline

対象:
`D:\GitHub\tegaki\ComfyUIPortable`

Review Target baseline:
`eeb63e4faf8d2736eb40b8b30931ab3758b95c44`

Phase 3E の技術成果は維持します。

- PRIMARY REGIONAL BACKEND: IMPACT
- IMPACT N-REGION ENGINE: PASS
- REGION ORDERING: SCENE_FIRST
- RECURRENT CAST 4-PANEL: PASS
- PANEL ACTION SEPARATION: PASS
- SAME-CAST MULTI-SCENE: PROMISING
- MANGA AUTHORING REINTEGRATION: GO

ただし、Phase 3F は新UIを作る前に、保存WorkflowをComfyUI上でそのまま実行できない問題を最優先で閉じてください。

---

## 1. 最優先問題

ユーザーが現行Workflowを読み込み、そのまま実行したところ、Workflow 22を中心に6件のvalidation errorが出ました。

確認された例:

- `ToBasicPipe - clip`: 必須入力未接続
- `RegionalSampler - denoise`: 入力値が許可範囲外
- `RegionalSampler - additional_*`: 無効な入力
- `RegionalSampler - seed_2nd / seed_2nd_mode`: 型・値不整合

Phase 3Eの生成スクリプトが成功していても、保存WorkflowのZero-Touch実行PASSとはみなしません。

Phase 3E runtime scriptはAPI promptをnamed inputsで動的構築してqueueしている一方、保存Workflowはfrontend用links / widgets_valuesを持つため、現在のImpact Pack / frontend schemaとの差が発生し得ます。

今後は次を別々に報告してください。

```text
PROGRAMMATIC API RUNTIME:
PASS / FAIL

SAVED WORKFLOW BROWSER LOAD:
PASS / FAIL

SAVED WORKFLOW ZERO-TOUCH EXECUTION:
PASS / FAIL
```

---

## 2. Phase名

```text
Phase 3F
Zero-Touch Workflow Parity
&
Progressive Panel / Scene Authoring UI
```

内部:

```text
3F-0  Saved Workflow / Live Node Schema Closure
3F-A  Progressive Authoring Data Contract
3F-B  Cast Authoring UI
3F-C  Panel Content Authoring UI
3F-D  Character Staging UI
3F-E  Optional SubScene Progressive Disclosure
3F-F  Impact Runtime Integration
3F-G  User-Visible Zero-Touch Gate
```

---

## 3. 3F-0 Gate

最初に成立させること:

```text
Workflowを開く
↓
何も修正しない
↓
Execute
↓
ComfyUI validation error 0件
↓
画像生成
```

Workflow 21 / 22をこの状態へ直すまで、新UI部分を完了扱いしないでください。

---

## 4. Live `/object_info` を外部ノードSchemaの正本にする

実際に起動中のComfyUIから最低限:

- ToBasicPipe
- KSamplerAdvancedProvider
- RegionalSampler

の `/object_info` を取得してください。

確認:

```text
required inputs
optional inputs
widget order
types
enum values
numeric min/max
```

Impact Packの過去Workflowや記憶上のwidget順を正本にしないこと。

---

## 5. ToBasicPipe `clip`

現行Workflow 21 / 22では `ToBasicPipe.clip` が未接続です。

現在の実ブラウザでは必須入力としてvalidation errorになるため:

```text
CheckpointLoaderSimple.CLIP
→ ToBasicPipe.clip
```

を接続。

Programmatic API側も可能なら同じ契約へ寄せ、`clip: None` を標準fixtureにしない。

---

## 6. RegionalSamplerの保存値をlive schemaから再生成

現Workflowにある古い positional `widgets_values` を盲目的に流用しない。

現在Runtimeで以下の実在・型・enum・順序を確認:

```text
seed
seed_2nd
seed_2nd_mode
steps
base_only_steps
denoise
overlap_factor
restore_latent
additional_mode
additional_sampler
additional_sigma_ratio
```

存在しないinputを保存しないこと。

現在のfrontend node schemaと一致する形でWorkflow 21 / 22を再保存してください。

---

## 7. Live Schema Test

新規:

```text
scripts/test_live_external_node_schema.py
scripts/test_saved_workflow_live_compatibility.py
```

`test_live_external_node_schema.py` は起動中ComfyUIの `/object_info` を取得し、外部ノードのschema driftを検出。

`test_saved_workflow_live_compatibility.py` は最低限:

```text
12
18
19
20
21
22
```

についてlive schemaとsaved workflowを照合。

特に:

```text
required socket linked
widget count/order compatible
enum valid
numeric range valid
input types valid
```

を確認。

既存 `test_workflow_widget_compatibility.py` だけで外部Impactノード互換をPASS扱いしない。

---

## 8. Browser Zero-Touch Smoke

可能なら実ブラウザで:

```text
Workflow21 load → Execute → errors 0 → final image
Workflow22 load → Execute → errors 0 → final image
```

まで確認。

ブラウザ自動化不能なら:

```text
BROWSER CLICK-EXECUTE: PENDING
```

と分離して報告。

ただし既知validation errorが残るsaved workflowをPASSにしない。

---

## 9. Phase 3E報告書の補正

追記:

```text
Phase 3E generation PASS was established by programmatic API prompt execution.
Saved browser workflow compatibility was a separate unverified path.
User manual validation exposed stale/mismatched frontend node inputs.
Phase 3F-0 closes this gap.
```

Phase 3EのN-Region / Recurrent Cast / Multi-Scene生成成果自体は撤回不要です。

---

# Progressive Authoring UI

## 10. UI思想

専用GUIはまだ作りません。

ComfyUI上でユーザー作業列を:

```text
01 GLOBAL
→ 02 CAST
→ 03 PANEL CONTENT
→ 04 PANEL LAYOUT
→ 05 CHARACTER STAGING
→ 06 GENERATE
```

と並べる。

内部処理:

```text
Compiler
Impact Region Plan
Providers
RegionalSampler
VAE
Debug
```

は離した位置へまとめ、`INTERNAL ENGINE / DO NOT TOUCH` として視覚分離・可能ならlock。

---

## 11. Simple First

通常Panel:

```text
Panel
├ Scene / Background Prompt
└ optional Characters
```

だけで作れる。

SubSceneは標準表示しない。

---

## 12. Cast Authoring UI

選択Characterについて画面上で直接編集可能にする:

```text
Name
Stable ID
Base Prompt
Negative Prompt
Enabled
```

現状のようにName / ID / Enabledは見えるがPrompt入力位置が分かりにくい状態を解消。

LoRA Planは折り畳み補助欄でよい。

最大6人分の巨大Prompt欄を同時に並べず、selected characterだけ編集。

例:

```text
[Alice] [Bob] [Carol] [+]

Selected: Alice
Name:
Prompt:
Negative:
LoRA Plan ▸
```

---

## 13. Panel Content Authoring

「4コマなら4つ固定入力欄」ではなく、

```text
panel_count
selected_panel
```

を持つJSON-backed editorへ。

例:

```text
Panels: 4
[P1] [P2] [P3] [P4]

Selected: P2

Scene / Background:
...

Characters:
Alice ✓
Bob   □
Carol □

Acting / Notes:
...
```

ComfyUI上では1ノード内で選択中Panelだけ詳細編集する方式を推奨。

---

## 14. Panel Count

```text
1〜6
typical 3〜5
```

変更時に既存panelデータを可能な限り保持。

減少によって既存データを消す場合、silent destroy禁止。初期実装ではfail-closedでもよい。

---

## 15. Panel Card Data

最低限:

```text
panel_id
enabled
scene_prompt
negative_prompt
character_bindings
metadata
```

既存 REGION_SPEC / PAGE_COMPILE_PLANと互換維持。

Impact固有objectを永続schemaへ混入させない。

---

## 16. AttendanceとActingを分ける

Panel Content:

```text
誰が出演するか
```

を決める。

各出演Characterには:

```text
prompt_override
negative_prompt_override
```

を持つ。

例:

```text
P1 Alice: smiling, shaking hands
P2 Alice: watering flowers
P4 Alice: angry, looking away
```

Character Masterは複製しない。

---

## 17. Character Staging

Panel Contentの後に位置配置。

Current Panelを選ぶと、そのPanelに出演するCharacterだけ表示。

例:

```text
Current Panel: P1
Alice
Bob
```

Canvas上で最低限:

```text
select
drag move
resize handle
reset
```

を機能させる。

Character Semantic Regionsは重なってよい。

---

## 18. Parent Panel Clip

通常Character Region:

```text
Character Semantic Region
∩
Parent Panel Polygon
```

でclip。

将来の「コマから飛び出す人物」は別機能として後回し。

---

## 19. Root Scene

Simple Panelでは:

```text
Panel Polygon = Root Scene Region
```

と扱う。

ユーザーはScene geometryを意識しなくてよい。

---

# Optional SubScene

## 20. Progressive Disclosure

選択Panelでのみ:

```text
[ + Split Scene / Advanced Scene ]
```

を押した時にSubScene UIを出す。

通常の4コマでは一度も触らず生成できること。

---

## 21. SubScene v1 Contract

Phase 3E Hostile TestがPROMISINGだったため最小Contractを正式化してよい。

複雑な木構造にはしない。

```text
Panel
├ root_scene
└ optional subscenes[]
```

SubScene v1最低情報:

```text
id
enabled
prompt
negative_prompt
area
character_bindings
metadata
```

最初はnormalized rectangleでよい。

`subscenes` が無い / 空なら完全にSimple Panelとして既存互換。

---

## 22. Same Master Character Multiple Instances

例:

```text
Panel1
├ SubScene A
│  ├ Alice instance
│  └ Bob instance
└ SubScene B
   ├ Alice instance
   └ Bob instance
```

Master IDは同じ。
Instance IDは一意。

---

## 23. Hostile UI Test

コード直書き専用adapterではなく、新Authoring UIから:

```text
1 Panel
Advanced Scene ON
2 SubScenes

A:
Alice + Bob
arguing / looking away

B:
Alice + Bob
friendly handshake
```

を作成し、Impact N-Regionへ流す。

---

# Workflows

## 24. Workflow 23

新規:

```text
23_MANGA_PROGRESSIVE_PANEL_AUTHORING_IMPACT.json
```

ユーザー列:

```text
Global
Cast
Panel Content
Panel Layout
Character Staging
Generate
```

内部:

```text
Compiler
Impact N-Region Adapter
RegionalSampler
VAE
```

Default fixture:

```text
P1 Alice + Bob — friendly handshake
P2 Alice — watering flowers
P3 Bob — carrying potted plant
P4 Alice + Bob — arguing / looking away
```

Phase 3E recurrent cast fixtureを再利用。

必須:

```text
load
no edits
Execute
validation error 0
image generated
```

---

## 25. Workflow 24

新規:

```text
24_SINGLE_PANEL_PROGRESSIVE_SUBSCENE_IMPACT.json
```

Default:

```text
1 visible Panel
Advanced Scene ON

SubScene A:
Alice + Bob arguing

SubScene B:
Alice + Bob handshake
```

同じくZero-Touch必須。

---

## 26. Fixture共通化

API runtimeとsaved workflowで別々に手書き設定を持ちすぎない。

可能なら:

```text
model
sampler
cast
panel content
layout
```

を共通fixtureから生成し、Programmatic testとsaved workflowの乖離を抑える。

---

## 27. External Plugin Schema Drift

Impact Pack等の外部ノードについて:

```text
saved expected schema snapshot
+
live /object_info comparison
```

を持つ。

MismatchならFAILし、Workflow PASSと報告しない。

---

## 28. Preview制限

ユーザー向けPreviewは原則:

```text
Authoring / Region Preview
Panel Layout Preview
Final Image
```

程度。

Debug PreviewはInternal側へ。

見栄え目的のPreview増殖を避ける。

---

## 29. Manual User Gate

次にユーザーへ手動確認を依頼するのは最低限:

```text
Workflow23 load → Execute → no error
Workflow24 load → Execute → no error
Cast Promptが画面上で編集可能
Panel選択 → Panel Prompt編集可能
Panel選択 → 出演Character確認可能
Character Stagingで矩形を動かせる
```

が揃ってから。

それ以前のbackend細部確認をユーザーへ要求しない。

---

## 30. Browser Interaction

Phase 3D.2以来PENDINGのSemantic Region drag / resizeに加え、
Character Staging drag / resizeも可能なら実ブラウザ確認。

不可能ならPENDINGを維持。

見た目だけhandleがありイベント未実装は不可。

---

## 31. Regression

最低限Programmatic runtime:

```text
12
18
19
20
21
22
```

Saved workflow live compatibility:

```text
21
22
23
24
```

---

## 32. Report

新規:

```text
PHASE3F_ZERO_TOUCH_AND_PROGRESSIVE_AUTHORING_REPORT.md
```

最低限:

```text
1. Phase3E Review
2. User Manual Error Reproduction
3. Programmatic vs Saved Workflow Distinction
4. Live External Node Schema
5. ToBasicPipe Fix
6. RegionalSampler Schema Fix
7. Workflow21 Zero-Touch
8. Workflow22 Zero-Touch
9. Progressive Authoring Contract
10. Cast Prompt UI
11. Panel Content UI
12. Character Attendance
13. Character Acting Override
14. Panel Layout Integration
15. Character Staging
16. Character Drag/Resize
17. Simple Panel Path
18. SubScene Progressive Disclosure
19. SubScene v1 Contract
20. Workflow23
21. Workflow24
22. Browser Interaction
23. API Runtime Regression
24. Saved Workflow Live Compatibility
25. Known Issues
26. Next Phase
27. Gemini独自判断
```

---

## 33. Sign-off

```text
PHASE3E REVIEW CLOSURE:
PASS / HOLD

SAVED WORKFLOW21 ZERO-TOUCH:
PASS / FAIL

SAVED WORKFLOW22 ZERO-TOUCH:
PASS / FAIL

EXTERNAL NODE LIVE SCHEMA:
PASS / FAIL

CAST AUTHORING:
READY / PARTIAL

PANEL CONTENT AUTHORING:
READY / PARTIAL

CHARACTER STAGING:
READY / PARTIAL

SIMPLE PANEL PATH:
PASS / HOLD

SUBSCENE V1:
PASS / EXPERIMENTAL / HOLD

WORKFLOW23:
PASS / HOLD

WORKFLOW24:
PASS / HOLD

BROWSER INTERACTION:
PASS / PENDING

PRIMARY REGIONAL BACKEND:
IMPACT

NEXT RECOMMENDED PHASE:
```

---

## 34. Two-stage Commit

Commit A:

```text
feat(manga): Phase 3F Zero-Touch Workflow Parity and Progressive Authoring
```

内容:

```text
workflow schema fixes
live schema tests
Cast UI
Panel Content UI
Character Staging
SubScene v1
Workflow23
Workflow24
tests
report
```

Commit AのSHA取得後、Navigation Commit Bで `ComfyUIPortable/GITHUB.TXT` のReview TargetをCommit Aへ更新。

---

## 35. 最終回答フォーマット

```text
Review Target Commit SHA:
Latest GITHUB.TXT Raw:

PHASE3F_ZERO_TOUCH_AND_PROGRESSIVE_AUTHORING_REPORT Raw:

Live External Schema Test Raw:
Saved Workflow Compatibility Test Raw:

Cast Authoring Raw:
Cast Authoring JS Raw:
Panel Content Authoring Raw:
Panel Content JS Raw:
Character Staging Raw:
Character Staging JS Raw:
SubScene Contract Raw:

Workflow21 Raw:
Workflow22 Raw:
Workflow23 Raw:
Workflow24 Raw:

SAVED WORKFLOW21 ZERO-TOUCH:
SAVED WORKFLOW22 ZERO-TOUCH:
EXTERNAL NODE LIVE SCHEMA:
CAST AUTHORING:
PANEL CONTENT AUTHORING:
CHARACTER STAGING:
SIMPLE PANEL PATH:
SUBSCENE V1:
WORKFLOW23:
WORKFLOW24:
BROWSER INTERACTION:
NEXT RECOMMENDED PHASE:
```

---

# 最終方針

Phase 3Eで得た:

```text
Impact N-Region
Recurrent Cast
Panel Action Separation
Same-Cast Multi-Scene
```

は有効です。

今回のエラーはその研究成果を否定するものではなく、

```text
研究用API prompt実行
と
ユーザーが保存Workflowを開いてそのまま実行
```

の互換性検証が不足していたことを示します。

Phase 3Fではまずこの差を閉じます。

その後、

```text
Global
→ Cast
→ Panel Content
→ Panel Layout
→ Character Staging
→ Generate
```

をComfyUI上の制作導線として成立させます。

SubSceneは常設しません。

通常の4コマは:

```text
Panel Prompt
+ optional Characters
```

だけで作れ、
複雑なPanelだけAdvanced / Split Sceneへ展開できる状態を目指してください。

次にユーザーへ確認依頼する時点では、Workflow 23 / 24が保存Workflowとしてvalidation errorなしで実行可能であることを最低条件にしてください。
