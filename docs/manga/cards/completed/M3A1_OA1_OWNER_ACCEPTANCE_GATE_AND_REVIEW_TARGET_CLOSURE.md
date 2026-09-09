# M3A1-OA1 — Owner Acceptance Gate & Review Target Closure

Date: 2026-09-09 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Owner: repository owner

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3A1_OA1_OWNER_ACCEPTANCE_GATE_AND_REVIEW_TARGET_CLOSURE.md`

---

# 0. Goal

M3A1-BC1のtechnical Browser Closureは公開GitHub上でSOL review PASSした。

このCardでは新しい機能を実装しない。

責務は次の3点だけ。

1. M3A1-BC1をtechnical completionとしてrouting closureする
2. M3A.1のCore Implementation SHAと現在のClosure Review Targetを明確に分離する
3. Owner本人によるO1–O5の明示的ACCEPT / REJECTを記録する

OwnerがACCEPTするまでM3Bを開始しない。

---

# 1. SOL-verified public state

Latest SOL-verified public commit:

`ad91c9277715e998663e8c12b6c37cca16e53955`

BC1 execution baseline:

`a92237fe3eeb0f53e16c69d37763d388fedf2145`

この`a92237fe...`はH3側の別作業commitであり、BC1 publication commitではない。

M3A.1 Core Implementation SHA:

`a7f0baaa89a2e315b0492573c9da19e50727928b`

M3A1-BC1 Browser Closure / current Manga Review Target:

`ad91c9277715e998663e8c12b6c37cca16e53955`

BC1 public state:

```text
Regression: PASS
Runtime: PASS
Browser B0-B9: PASS
Visual evidence: PASS
Owner acceptance: PENDING
M3B authorization: NO
```

---

# 2. Baseline

開始時:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

期待baseline:

`ad91c9277715e998663e8c12b6c37cca16e53955`

## Baseline drift

origin/mainが進んでいた場合:

```bash
git diff --name-status \
  ad91c9277715e998663e8c12b6c37cca16e53955..origin/main
```

を確認する。

今回のown filesに競合がなければ最新origin/mainをexecution baselineとして継続。

H3など無関係domainの更新だけでSTOPしない。

own files競合時だけSTOP。

---

# 3. Read order

以下だけを読む。

1. `ComfyUIPortable/GITHUB_MANGA.txt`
2. `ComfyUIPortable/docs/manga/STATUS.md`
3. `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
4. `ComfyUIPortable/docs/manga/cards/README.md`
5. `ComfyUIPortable/docs/manga/cards/current/README.md`
6. `ComfyUIPortable/docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`
7. `ComfyUIPortable/docs/manga/reports/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md`
8. `ComfyUIPortable/docs/manga/verification/m3a1_browser/M3A1_BROWSER_CLOSURE_MANIFEST.json`
9. B1–B9 PNG evidence
10. `ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

旧Phase、archive、H3内部、M3B実装sourceへ広げない。

---

# 4. Verified BC1 implementation truth

SOLが公開差分を確認済み。

BC1で変更されたManga implementation fileは1つだけ:

`ComfyUIPortable/workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

FrameOverlay node serialization:

Before:

```json
"widgets_values": [
  4,
  0,
  ""
]
```

After:

```json
"widgets_values": [
  4,
  0
]
```

これによりlive browserで`page_index=0`が正常serializationされ、

```text
FrameOverlay
→ SaveImage
```

へ到達した。

このCardでは再修正しない。

---

# 5. Verified BC1 evidence

published report / manifestでは:

```text
B0 baseline load: PASS
B1 Visual Panel Frames: PASS
B2 create frames: PASS
B3 drag / resize: PASS
B4 white gutter + black frames: PASS
B5 2px / 8px thickness: PASS
B6 Save / Reload: PASS
B7 post-reload causal edit: PASS
B8 zero-frame regression: PASS
B9 CAST regression smoke: PASS
```

Regression:

```text
Python M3A.1: 14/14 PASS
Python M3A: 7/7 PASS
Python M2B1: 6/6 PASS
Python M1.1: 7/7 PASS
JavaScript: 19/19 PASS
V0-V4: PASS
```

このCardでは原則再実行不要。

Ownerが再確認のためlive browser再生を希望した場合のみ実施する。

---

# 6. Review Target semantics correction

CURRENT AUTHORITYでは今後、次の2つを分離する。

## Historical core implementation

```text
M3A.1 Core Implementation SHA:
a7f0baaa89a2e315b0492573c9da19e50727928b
```

これはM3A.1主要runtime implementationの歴史的commit。

## Current complete closure target

```text
M3A.1 Current Closure Review Target:
ad91c9277715e998663e8c12b6c37cca16e53955
```

これはBC1 workflow serialization fix、Browser evidence、current authorityを含む現在のM3A.1完了候補。

## Latest SOL-verified public commit

```text
Latest SOL-verified public commit:
ad91c9277715e998663e8c12b6c37cca16e53955
```

---

# 7. GITHUB_MANGA update

`GITHUB_MANGA.txt`では、現在の単独:

```text
Review Target Commit SHA:
a7f0baaa...
```

という表示を、意味が曖昧にならない形へ整理する。

推奨:

```text
M3A.1 Core Implementation SHA:
a7f0baaa89a2e315b0492573c9da19e50727928b

M3A.1 Current Closure Review Target:
ad91c9277715e998663e8c12b6c37cca16e53955

Latest SOL-verified public commit:
ad91c9277715e998663e8c12b6c37cca16e53955
```

BC1 Card/report/manifestへのraw URLを保持する。

---

# 8. BC1 routing closure

M3A1-BC1はtechnical Browser ClosureとしてSOL review PASS済み。

そのためCard本文をbyte-for-byte維持して:

`docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`

から:

`docs/manga/cards/completed/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`

へ移動する。

BC1 report / manifest / evidenceは移動不要。

BC1 CardへのCURRENT AUTHORITY URLをcompleted側へ更新する。

旧current URLを残して404にしない。

---

# 9. OA1 Card routing

このCardをcurrent slotへ置く。

`cards/current/README.md`:

```text
Active Card:
M3A1-OA1 — Owner Acceptance Gate & Review Target Closure
```

`cards/README.md`もCurrentをOA1へ向ける。

BC1はCompletedへ追加する。

---

# 10. Own files

変更可能:

* `ComfyUIPortable/GITHUB_MANGA.txt`
* `ComfyUIPortable/docs/manga/STATUS.md`
* `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
* `ComfyUIPortable/docs/manga/cards/README.md`
* `ComfyUIPortable/docs/manga/cards/current/README.md`
* `ComfyUIPortable/docs/manga/cards/current/M3A1_OA1_OWNER_ACCEPTANCE_GATE_AND_REVIEW_TARGET_CLOSURE.md`
* `ComfyUIPortable/docs/manga/cards/completed/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`
* `ComfyUIPortable/docs/manga/reports/M3A1_OA1_OWNER_ACCEPTANCE_GATE_REPORT.md`
* `ComfyUIPortable/docs/manga/reports/README.md`

BC1 Card current→completed移動元:

* `ComfyUIPortable/docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`

---

# 11. Do not touch

禁止:

* Manga Python implementation
* Manga JavaScript implementation
* workflow JSON
* schema
* runtime adapter
* tests
* BC1 Browser evidence PNG
* BC1 manifest
* BC1 report本文
* M3A.1 historical report
* M3B implementation
* Rough Manga implementation
* White-Dummy Guide implementation
* ControlNet
* H3
* ComfyUI core/frontend
* Tegaki
* EasyReforgeExtension
* RegionalLoRALab

OwnerがREJECTしてもこのCard内で修正しない。

---

# 12. Owner acceptance presentation

LUNAはOwnerへO1–O5を一度に提示する。

必要ならB1–B9 evidenceを開いて見せる。

Ownerが希望する場合はlive ComfyUIを起動して再確認してよい。

## O1

```text
Visual Panel Framesを開き、
Frame追加 / Copy Frames from Scenesが
制作操作として自然か。
```

参考:

* B1
* B2

## O2

```text
Frame drag / resizeが
期待する操作感・挙動になっているか。
```

参考:

* B3

## O3

```text
Queue最終出力の
white gutter + black frameが
漫画制作上期待する見た目か。
```

参考:

* B4

## O4

```text
Frame 1 = 2px
Frame 2 = 8px

の枠線差が期待どおりか。
```

参考:

* B5

## O5

```text
Save / Reload後も
Frame geometry / thicknessが保持され、
その後のdragが最終出力へ反映されるか。
```

参考:

* B6
* B7

---

# 13. Explicit Owner decision required

LUNA自身がOwner acceptanceを決めない。

過去会話から推測しない。

沈黙をACCEPT扱いしない。

Ownerへ明示回答を求める。

推奨形式:

```text
ACCEPT M3A1 O1-O5
```

または:

```text
REJECT M3A1
O2: ...
O4: ...
```

Ownerが一部だけ判断した場合:

```text
Owner acceptance: PENDING
```

を維持する。

---

# 14. ACCEPT branch

OwnerがO1–O5すべてを明示ACCEPTした場合のみ:

```text
Browser technical verification: PASS
Visual evidence: PASS
Owner acceptance: ACCEPTED
M3A.1 gate: CLOSED
```

とする。

M3Bについては:

```text
M3B eligibility: OPEN
Active M3B Card: NONE
```

とする。

## 重要

`M3B authorization: YES, start implementation`

とは書かない。

意味は:

```text
Owner gateを通過したため、
Web GPT SOLが新しいM3B Cardを発行できる。
```

だけ。

LUNAはM3Bを自動開始しない。

---

# 15. REJECT branch

Ownerが1項目でもREJECTした場合:

```text
Owner acceptance: REJECTED
M3A.1 gate: OPEN / NEEDS CORRECTION
M3B eligibility: CLOSED
```

とする。

Ownerの文言を要約しすぎず、

```text
Rejected item:
Observed behavior:
Expected behavior:
Evidence:
```

をreportへ記録する。

実装修正は禁止。

SOLへ返す。

---

# 16. PENDING branch

Ownerが判断を保留した場合:

```text
Owner acceptance: PENDING
M3B eligibility: CLOSED
```

のまま終了してよい。

無理に判断を促進しない。

---

# 17. OA1 report

作成:

`ComfyUIPortable/docs/manga/reports/M3A1_OA1_OWNER_ACCEPTANCE_GATE_REPORT.md`

最低限:

```text
# M3A1-OA1 Owner Acceptance Gate Report

Date
Execution baseline

Latest SOL-verified public commit:
ad91c9277715e998663e8c12b6c37cca16e53955

M3A.1 Core Implementation SHA:
a7f0baaa89a2e315b0492573c9da19e50727928b

M3A.1 Current Closure Review Target:
ad91c9277715e998663e8c12b6c37cca16e53955

BC1:
Contract PASS
Regression PASS
Runtime PASS
Browser PASS
Visual evidence PASS

Owner decision:

O1:
ACCEPT / REJECT / PENDING
Owner note:

O2:
...

O3:
...

O4:
...

O5:
...

Overall Owner acceptance:
ACCEPTED / REJECTED / PENDING

M3A.1 gate:
CLOSED / OPEN

M3B eligibility:
OPEN / CLOSED

Implementation changed:
NO

Next SOL action:
...
```

---

# 18. Current authority after ACCEPT

Owner ACCEPTEDの場合:

`GITHUB_MANGA.txt`:

```text
M3A.1 Core Implementation SHA:
a7f0baaa89a2e315b0492573c9da19e50727928b

M3A.1 Current Closure Review Target:
ad91c9277715e998663e8c12b6c37cca16e53955

Latest SOL-verified public commit:
ad91c9277715e998663e8c12b6c37cca16e53955

Browser technical verification:
PASS

Visual evidence:
PASS

Owner acceptance:
ACCEPTED

M3A.1 gate:
CLOSED

M3B eligibility:
OPEN

Active M3B Card:
NONE

Next recommended Card:
M3B-LR1 — Rough Guide Foundation Long-Run Batch
```

---

# 19. Current authority after REJECT/PENDING

REJECT:

```text
Browser technical verification: PASS
Visual evidence: PASS
Owner acceptance: REJECTED
M3A.1 gate: NEEDS CORRECTION
M3B eligibility: CLOSED
Next: SOL correction Card
```

PENDING:

```text
Browser technical verification: PASS
Visual evidence: PASS
Owner acceptance: PENDING
M3A.1 gate: WAITING OWNER
M3B eligibility: CLOSED
```

---

# 20. Publication semantics

OA1 reportにはLUNA終了時点の事実として:

```text
OA1 publication:
LOCAL

Owner push required:
YES
```

と書いてよい。

ただしCURRENT AUTHORITYには:

```text
OA1 publication: LOCAL
Owner push required
Blocked until push
```

を書かない。

公開正本はgate/current product truthだけを扱う。

publication再帰Cardを作らない。

---

# 21. Validation

```bash
git diff --check
```

BC1 completed path:

```bash
test -f \
  ComfyUIPortable/docs/manga/cards/completed/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md
```

旧current BC1がないこと:

```bash
test ! -f \
  ComfyUIPortable/docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md
```

OA1 current Card:

```bash
test -f \
  ComfyUIPortable/docs/manga/cards/current/M3A1_OA1_OWNER_ACCEPTANCE_GATE_AND_REVIEW_TARGET_CLOSURE.md
```

current authority scan:

```bash
rg -n \
  "a7f0baaa89a2e315b0492573c9da19e50727928b|ad91c9277715e998663e8c12b6c37cca16e53955|Owner acceptance|M3B eligibility" \
  ComfyUIPortable/GITHUB_MANGA.txt \
  ComfyUIPortable/docs/manga/STATUS.md \
  ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md
```

---

# 22. Tests / Runtime

Implementation変更は禁止なので:

```text
Tests: NOT RUN / NOT REQUIRED
Runtime: NOT RUN / NOT REQUIRED
```

Ownerがbrowser replayを希望した場合のみBrowserを再実行する。

既存BC1 PASSを破棄しない。

---

# 23. Stop conditions

STOPしてSOLへ返す:

* ad91c927...のBC1 Card/report/manifestが公開GitHubと一致しない
* BC1実装修正がworkflow以外にも存在する証拠が出る
* Ownerが新しいschema/product意味変更を要求する
* Owner REJECT内容がM3BやH3まで影響する
* current authorityに別作業の競合変更がある

Astraは直接呼ばない。

---

# 24. Required LUNA final response

```text
Card:
M3A1-OA1

Execution baseline:
Local HEAD:
origin/main:

Latest SOL-verified public commit:
ad91c9277715e998663e8c12b6c37cca16e53955

M3A.1 Core Implementation SHA:
a7f0baaa89a2e315b0492573c9da19e50727928b

M3A.1 Current Closure Review Target:
ad91c9277715e998663e8c12b6c37cca16e53955

BC1 routing:
COMPLETED / FAIL

Implementation changed:
NO

Owner O1:
Owner O2:
Owner O3:
Owner O4:
Owner O5:

Owner acceptance:
ACCEPTED / REJECTED / PENDING

M3A.1 gate:
CLOSED / NEEDS CORRECTION / WAITING OWNER

M3B eligibility:
OPEN / CLOSED

Active M3B Card:
NONE

Next recommended Card:
M3B-LR1 Rough Guide Foundation Long-Run Batch
or
M3A1 correction Card

OA1 publication:
LOCAL

Owner push required:
YES
```

---

# 25. Close condition

Ownerが明示ACCEPTし、OA1がOwnerによりcommit/pushされた後、公開SHAをWeb GPT SOLへ渡す。

SOLが公開内容を確認する。

ACCEPTEDなら次は通常の小Cardへ戻さず、

**最初のLong-Run試験**

として:

`M3B-LR1 — Rough Guide Foundation Long-Run Batch`

を発行候補とする。

このLong-Run Batchでは、

```text
Stage 1: guide input/storage contract
Stage 2: Character Instance ↔ rough figure association
Stage 3: editor integration
Stage 4: runtime bridge
Stage 5: regression/evidence
Stage 6: docs/publication
```

を内部gate付きで連続実行させる。

ただしOA1がACCEPTEDになる前には作成・実行しない。
