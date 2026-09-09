# M3A1-BC1 — Owner Live-Browser Closure and Publication Model Cleanup

Date: 2026-09-09 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Owner: repository owner

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`

---

# 0. Goal

M3A.1で実装済みのVisual Panel Frame経路について、

```text
UI
→ Authoring Document
→ Save / Reload
→ FrameOverlay
→ SaveImage output
```

の実ブラウザ因果を閉じる。

今回確認するProduct機能は:

1. Visual Panel Frames layerが実ブラウザで開く
2. Frameを作成できる
3. Frameをdrag / resizeできる
4. Queue結果へwhite gutter + black borderが反映される
5. per-frame border thickness差が最終画像へ反映される
6. Save / Reload後もFrame geometryが保持される
7. Reload後のdragが次の最終出力へ反映される

加えて、TF2/TF2.1で判明したpublication再帰問題をCURRENT AUTHORITYの表現だけ修正する。

M3B機能は追加しない。

---

# 1. Verified baseline

Web GPT SOL verified public baseline:

`399b4d5f973c389f42cb1912be3abe153ad08678`

Parent:

`5c9da782316b99ceeb6ecfb85695bb6965d3bf35`

M3A.1 implementation Review Target:

`a7f0baaa89a2e315b0492573c9da19e50727928b`

開始時:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

期待:

```text
origin/main =
399b4d5f973c389f42cb1912be3abe153ad08678
```

---

# 2. Baseline drift rule

`origin/main`が進んでいた場合、即STOPしない。

まず:

```bash
git diff --name-status \
  399b4d5f973c389f42cb1912be3abe153ad08678..origin/main
```

を確認する。

今回のManga Browser Closure対象fileと競合しなければ最新`origin/main`をexecution baselineとして継続。

競合する場合だけSTOP。

H3や別domainのcommitだけで作業を中止しない。

---

# 3. Read order

順序:

1. `ComfyUIPortable/GITHUB_MANGA.txt`
2. `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
3. `ComfyUIPortable/docs/manga/STATUS.md`
4. `ComfyUIPortable/docs/manga/cards/README.md`
5. `ComfyUIPortable/docs/manga/reports/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE_REPORT.md`
6. M3A.1 implementation report at Review Target:
   `a7f0baaa89a2e315b0492573c9da19e50727928b`
7. `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js`
8. `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js`
9. `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/frame_overlay.py`
10. `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/authoring_visual_frame_bridge.py`
11. `ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`
12. M3A.1 tests / verification manifest only as needed

旧Phase全文やarchiveへ降りない。

---

# 4. Existing implementation truth — do not reimplement

M3A.1で既に確認済み:

```text
invalid JSON:
fail-closed ERROR

out-of-range page_index:
fail-closed ERROR

valid 0 frames:
pixel-identical pass-through

1+ frames:
comic_panels mode

outside frame union:
white gutter

frame border:
black

border thickness:
per-frame border_thickness first
global line_thickness fallback

geometry:
area canonical
shape legacy fallback only

copyFramesFromScenes:
area-only

derive_panel_layout_spec_from_frames([]):
None / guide OFF

visual_status:
PENDING unless directly inspected
```

これらを別方式へ再設計しない。

M3A.1 reportでは既存自動検証がPASSしている。

今回の主責務はBrowser因果確認。

---

# 5. Publication model cleanup

TF2.1は既にGitHubへ公開され、Web GPT SOLが今回確認した。

Public commit:

`399b4d5f973c389f42cb1912be3abe153ad08678`

したがってCURRENT AUTHORITY内の:

```text
TF2.1 publication: LOCAL
Owner push required
Current local Card
Current local report
```

という現在状態表現を除去する。

ただしTF2.1 report本文の:

```text
TF2.1 publication: LOCAL
Owner push required
```

はLUNA終了時点の歴史記録なので変更しない。

---

# 6. New permanent publication rule

今後CURRENT AUTHORITYでは、

```text
Current repository publication
```

という「現在HEADと常に一致しなければならないSHA欄」を原則使わない。

代わりに:

```text
Latest SOL-verified public commit:
399b4d5f973c389f42cb1912be3abe153ad08678
```

とする。

意味:

「最後にWeb GPT SOLが公開GitHubから実際に検証したcommit」

である。

これはmoving `main` HEADそのものを表さない。

## CURRENT AUTHORITYで禁止

```text
Publication: LOCAL
Owner push required
Blocked until push
Current local Card
Current local report
```

を公開正本の現在状態として書かない。

これらはLUNA終了reportだけに記録する。

---

# 7. Why this stops the publication loop

LUNAは自分がこれから作るcommit SHAを事前に知れない。

したがって公開正本へ毎回:

```text
自分自身 = LOCAL
```

と書き、push後に別Cardで:

```text
自分自身 = PUBLISHED
```

へ直す方式は禁止する。

今後は:

```text
Card実行
→ reportではPublication LOCAL
→ Owner push
→ SOLが公開SHAをreview
→ 次の本来の作業CardがLatest SOL-verified SHAを更新
```

とする。

publicationだけを閉じる追跡Cardを原則発行しない。

---

# 8. TF2.1 routing closure

TF2.1は既に公開済みなので、今回のCard開始時にcompleted扱いへ整理してよい。

推奨:

`docs/manga/cards/current/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md`

↓

`docs/manga/cards/completed/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md`

Card本文はbyte-for-byte維持する。

その場合、以下のリンクをcompleted側へ更新:

* `GITHUB_MANGA.txt`
* STATUS
* handoff
* cards/README
* reports/indexで必要な箇所

旧current URLを公開正本に残さない。

---

# 9. Own implementation files

Browserで不具合が再現し、既存M3A.1契約を満たすための最小修正が必要な場合のみ変更可能:

* `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js`
* `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js`
* `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/frame_overlay.py`
* `ComfyUIPortable/custom_nodes_custom/tegaki_manga_nodes/authoring_visual_frame_bridge.py`
* `ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

既存M3A/M3A.1関連testは、上記sourceを修正した場合のみ対応する最小範囲を変更可。

開始時に実際のtest pathを:

```bash
rg --files ComfyUIPortable | \
  rg 'test_m3a|test_m2b_minimum_hand|run_m3a1'
```

で特定する。

---

# 10. Own documentation/evidence files

変更可能:

* `ComfyUIPortable/GITHUB_MANGA.txt`
* `ComfyUIPortable/docs/manga/STATUS.md`
* `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
* `ComfyUIPortable/docs/manga/cards/README.md`
* `ComfyUIPortable/docs/manga/cards/current/README.md`
* `ComfyUIPortable/docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`
* `ComfyUIPortable/docs/manga/cards/completed/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md`
* `ComfyUIPortable/docs/manga/reports/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md`
* `ComfyUIPortable/docs/manga/reports/README.md`
* `ComfyUIPortable/docs/manga/verification/m3a1_browser/`

historical M3A.1 implementation reportは書き換えない。

---

# 11. Do not touch

禁止:

* M3B実装
* Rough Manga
* White-Dummy Guide
* Character ↔ rough figure association
* ControlNet追加
* Scene/Frame/CAST schema変更
* output namespace変更
* H3
* H3 workflow
* H3 docs
* ComfyUI core/frontend
* shared model store
* Tegaki本体
* EasyReforgeExtension
* RegionalLoRALab

---

# 12. Pre-browser regression

Browser起動前に既存M3A.1 regressionを再実行する。

実際のpathをlive treeから確認し、M3A.1 reportで記録済みの以下相当を実行:

```text
M3A.1 frame overlay runtime truth
M3A visual frame contract
M2B authoring regression
M1.1 canonical workflow wiring
M2B minimum-hand JS test
```

期待:

```text
Python existing regression: PASS
JavaScript existing regression: PASS
```

既存testがbaselineのままFAILする場合はBrowserへ進まず原因確認。

scope内の明白なregressionなら最小修正可。

意味境界変更が必要ならSTOP。

---

# 13. Browser environment

必ずlive ComfyUIを使用。

手順:

1. ComfyUI serverを完全restart
2. browser hard reload
3. stale frontend cacheを使わない
4. canonical workflow:
   `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`
   をロード
5. custom Manga DOMが表示されることを確認

headless DOM testだけでBrowser PASSにしない。

---

# 14. Browser Test B0 — baseline load

確認:

```text
Minimum-Hand Manga Authoring custom DOM visible
canonical workflow loads
FrameOverlay node exists
no missing-node error
Default Queue can execute
```

FAILなら証拠を保存して原因を限定。

---

# 15. Browser Test B1 — Visual Panel Frames layer

操作:

```text
Visual Panel Frames
```

tab/layerを開く。

確認:

```text
frame toolbar visible
frame canvas interaction enabled
ScenesとFramesが別layer
Character StagingとFramesが別layer
```

証拠:

`docs/manga/verification/m3a1_browser/B1_VISUAL_FRAME_LAYER.png`

---

# 16. Browser Test B2 — create frames

最低2 Sceneのfixtureを使用。

操作:

```text
Copy Frames from Scenes
```

確認:

```text
2 visual frames appear
frame IDs are unique
frames are selectable
document visual_frames count = 2
```

可能ならAdd Frame単独操作も確認。

証拠:

`B2_TWO_FRAMES_CREATED.png`

---

# 17. Browser Test B3 — drag / resize

Frame 1を明確にdrag。

Frame 2を明確にresize。

確認:

```text
Frame 1 area changes
Frame 2 width/height changes
Scene geometry does not move
Character geometry does not move
```

document JSONで変更後`area`がcanonicalであることを確認。

新規frameに不要な`shape`が生成されないこと。

証拠:

`B3_FRAME_DRAG_RESIZE.png`

---

# 18. Browser Test B4 — queue / manga framing

2 frames存在状態でQueue。

SaveImage出力を直接確認。

必須:

```text
Frame interior:
source image visible

between frames:
white

outside frame union:
white

frame border:
black
```

単なるEditor previewでPASSにしない。

SaveImage / final outputを確認する。

証拠:

`B4_FINAL_WHITE_GUTTER_BLACK_FRAMES.png`

---

# 19. Browser Test B5 — per-frame thickness

設定:

```text
Frame 1 border_thickness = 2
Frame 2 border_thickness = 8
```

Queue。

最終出力で:

```text
Frame 1 visibly thin
Frame 2 visibly thick
```

を確認。

Editor previewだけで判定しない。

証拠:

`B5_FINAL_2PX_8PX.png`

---

# 20. Browser Test B6 — Save / Reload

操作:

```text
Save Workflow
reload saved workflow
```

またはProductの正準保存/再読込経路。

確認:

```text
2 frames retained
frame IDs retained
area retained
border_thickness retained
no shape/area drift
```

証拠:

`B6_AFTER_SAVE_RELOAD.png`

---

# 21. Browser Test B7 — post-reload causal edit

Reload後、

Frame 1を再度別位置へdrag。

Queue。

確認:

```text
final output uses the new post-reload Frame 1 position
old position is not used
```

これは最重要の因果確認。

証拠:

`B7_POST_RELOAD_DRAG_FINAL_OUTPUT.png`

---

# 22. Browser Test B8 — zero frame regression

全Frameを削除するか0-frame fixtureをロード。

Queue。

確認:

```text
0 frames
→ source output pixel-identical/pass-through
→ fake full-page frameなし
→ white page化しない
```

既存structural testがあるため、Browserでは重大な見た目regressionがないことを確認すればよい。

証拠:

`B8_ZERO_FRAME_PASS_THROUGH.png`

---

# 23. Browser Test B9 — CAST regression smoke

Visual Frame操作後も最低限:

```text
CAST Master visible
Scene selection works
Character Rough Region remains operable
```

を確認する。

M2B機能の完全再受入ではない。

Frames実装がCAST UIを壊していないことだけ確認。

証拠:

`B9_CAST_REGRESSION.png`

---

# 24. Browser evidence manifest

作成:

`ComfyUIPortable/docs/manga/verification/m3a1_browser/M3A1_BROWSER_CLOSURE_MANIFEST.json`

最低構造:

```json
{
  "baseline": "...",
  "implementation_review_target": "a7f0baaa89a2e315b0492573c9da19e50727928b",
  "tests": {
    "B0": {"status": "PASS|FAIL", "evidence": "..."},
    "B1": {"status": "PASS|FAIL", "evidence": "..."},
    "B2": {"status": "PASS|FAIL", "evidence": "..."},
    "B3": {"status": "PASS|FAIL", "evidence": "..."},
    "B4": {"status": "PASS|FAIL", "evidence": "..."},
    "B5": {"status": "PASS|FAIL", "evidence": "..."},
    "B6": {"status": "PASS|FAIL", "evidence": "..."},
    "B7": {"status": "PASS|FAIL", "evidence": "..."},
    "B8": {"status": "PASS|FAIL", "evidence": "..."},
    "B9": {"status": "PASS|FAIL", "evidence": "..."}
  },
  "luna_browser_verdict": "PASS|FAIL",
  "owner_acceptance": "PENDING"
}
```

LUNAがOwner acceptanceを`ACCEPTED`にしない。

---

# 25. Fix policy if Browser test fails

Browser testがFAILした場合:

1. 再現条件を固定
2. console/runtime errorを記録
3. 原因fileを特定
4. own implementation files内で既存M3A.1 contractを満たす最小修正
5. 対応test追加または既存test強化
6. regression再実行
7. 同じBrowser testを再実行

禁止:

```text
UI全体改造
schema変更
M3B feature追加
「ついで」のrefactor
別domain整理
```

---

# 26. Stop / escalate

次の場合は修正範囲を広げずSTOP:

* Scene/Frame/CAST意味境界変更が必要
* persistent schema version変更が必要
* ComfyUI core/frontend変更が必要
* M3B機能がないと解決不能
* same root causeを2回修正してもBrowser gateが閉じない
* browser状態を再現できない
* canonical workflow自体が別系統へ置換されている

この場合のみSOLへ返す。

Astraを直接呼ばない。

SOLがAstra escalation条件を判定する。

---

# 27. Report

作成:

`ComfyUIPortable/docs/manga/reports/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md`

最低限:

```text
Execution baseline
M3A.1 implementation Review Target
Changed implementation files
Changed documentation files

Regression commands/results

Browser:
B0 ...
B1 ...
...
B9 ...

Observed failures
Corrections
Retest results

LUNA live-browser verdict:
PASS / FAIL

Visual evidence:
PASS / FAIL

Owner acceptance:
PENDING

M3B authorization:
NO

Owner verification items
```

---

# 28. Owner verification gate

LUNA Browser PASSでも、Owner acceptanceはPENDING。

終了時、Ownerへ以下5項目を明確に返す:

```text
O1. Visual Panel Framesを開き、Frame追加/Copyが自然に操作できるか
O2. Frame drag/resizeが期待どおりか
O3. Queue結果の白gutter + 黒frameが制作上正しいか
O4. 2px / 8pxの枠線差が期待どおりか
O5. Save/Reload後もFrame操作・出力が正しいか
```

Ownerがこのチャットで明示的にACCEPTEDとするまで、

```text
Owner acceptance: PENDING
M3B authorization: NO
```

を維持。

---

# 29. CURRENT AUTHORITY update

作業終了時:

`GITHUB_MANGA.txt`から新しいBrowser Card/reportへ完全raw URLを張る。

必須表示:

```text
Latest SOL-verified public commit:
399b4d5f973c389f42cb1912be3abe153ad08678

Manga implementation Review Target:
a7f0baaa89a2e315b0492573c9da19e50727928b

Current operational Card:
M3A1-BC1

Browser technical verification:
PASS / FAIL

Visual evidence:
PASS / FAIL

Owner acceptance:
PENDING

M3B authorization:
NO

Next:
Owner acceptance decision
```

## 禁止

公開正本には:

```text
M3A1-BC1 Publication: LOCAL
Owner push required
Blocked until push
```

を書かない。

それはreport内だけに記録する。

---

# 30. Card routing

作業中:

`cards/current/README.md`

にM3A1-BC1をactiveとして載せる。

作業終了時も、Owner acceptanceがPENDINGならBC1 Cardは`current/`に残してよい。

Owner acceptance後に次Cardを発行する時、SOLがcompleted移動を指示する。

勝手にM3B Cardを作らない。

---

# 31. Publication semantics for this Card

LUNA終了reportには正直に:

```text
M3A1-BC1 publication:
LOCAL
Owner push required:
YES
```

と書く。

ただしCURRENT AUTHORITYへはこのLOCAL状態を転記しない。

Owner push後、SOLは公開SHAをreviewする。

SOL reviewだけのための「BC1.1 Publication Closure Card」は原則発行しない。

次回の本来のCardで`Latest SOL-verified public commit`を更新する。

---

# 32. Required final response from LUNA

```text
Card:
M3A1-BC1

Execution baseline:
Local HEAD:
origin/main:

Implementation changed:
YES / NO

Changed files:

Regression:
Python: PASS / FAIL
JavaScript: PASS / FAIL

Browser:
B0:
B1:
B2:
B3:
B4:
B5:
B6:
B7:
B8:
B9:

LUNA live-browser verdict:
PASS / FAIL

Visual evidence:
PASS / FAIL

Evidence manifest:
<path>

Browser evidence files:
<paths>

Owner acceptance:
PENDING

Owner verification required:
O1:
O2:
O3:
O4:
O5:

M3B authorization:
NO

Latest SOL-verified public commit:
399b4d5f973c389f42cb1912be3abe153ad08678

M3A.1 implementation Review Target:
a7f0baaa89a2e315b0492573c9da19e50727928b

M3A1-BC1 publication:
LOCAL

Owner push required:
YES
```

---

# 33. Close condition

LUNA作業後:

1. Owner commit/push
2. 公開SHAをWeb GPT SOLへ渡す
3. SOLがCard/report/evidence/raw URLを確認
4. Owner自身がO1〜O5を確認
5. Ownerが明示的にACCEPTEDまたはREJECTED

## ACCEPTEDなら

SOLは次のM3B Cardを発行する。

ただしM3B一括実装ではなく、

```text
rough guide input asset
storage contract
Character Instance ↔ rough figure association
```

を先に固定する最小sliceとする。

## REJECTEDなら

M3Bへ進まず、観測された具体的Browser findingだけを対象とする修正Cardを発行する。
