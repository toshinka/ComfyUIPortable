# M3A1-TF2.1 — Post-Push Publication Truth Closure

Date: 2026-09-09 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Owner: repository owner

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md`

## 0. Purpose

M3A1-TF2はすでにGitHubへ公開され、Web GPT SOLによるpublic URL確認も完了した。

しかし一部のCURRENT AUTHORITYには、LUNA作業終了時点の

* `Publication: LOCAL`
* `Owner push required`
* `Web GPT verification blocked`
* `SOL public-URL review pending`
* `Current repository publication: db7611c...`

が現在状態として残っている。

このCardでは、その**公開後状態だけを現在の事実へ更新する**。

M3A1-TF2本体の実作業をやり直さない。

M3A.1 Browser Closureを実施しない。

M3Bへ進まない。

---

# 1. Verified public state

Web GPT SOLが2026-09-09 JSTにGitHub公開状態を確認済み。

Current public `main`:

`5c9da782316b99ceeb6ecfb85695bb6965d3bf35`

Parent / TF2 baseline:

`db7611c120af35504425872e896dc0229216b8c9`

M3A.1 implementation Review Target:

`a7f0baaa89a2e315b0492573c9da19e50727928b`

TF2 Card public path:

`ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

TF2 Report public path:

`ComfyUIPortable/docs/manga/reports/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_REPORT.md`

Web GPT SOL public review result:

```text
Scope: PASS
Card file publication: PASS
Report publication: PASS
Raw URL accessibility: PASS
Implementation isolation: PASS
Traceability structure: PASS
Post-push publication truth: FAIL
```

FAIL理由は実装ではなく、CURRENT AUTHORITYにpush前の`LOCAL`表示が残っているため。

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

`5c9da782316b99ceeb6ecfb85695bb6965d3bf35`

## Baseline handling

`origin/main`が上記から進んでいた場合:

```bash
git diff --name-status \
  5c9da782316b99ceeb6ecfb85695bb6965d3bf35..origin/main
```

を確認する。

今回のown filesと競合する変更がなければ、最新`origin/main`をexecution baselineとして継続する。

own filesに競合する変更があればSTOPしてSOLへ返す。

単にHEADが進んだだけでは無条件STOPしない。

---

# 3. Goal

新規Web GPTが`GITHUB_MANGA.txt`を読んだ時に、現在のpublication状態を次のように正しく理解できるようにする。

```text
Current repository publication:
5c9da782316b99ceeb6ecfb85695bb6965d3bf35
または、このCardが公開された後の実在する最新publication SHA

M3A1-TF2:
PUBLISHED

SOL public URL review:
PASS

Browser:
PENDING

Visual:
PENDING

Owner acceptance:
PENDING

M3B authorization:
NO

Next recommended Card:
M3A.1 Browser Closure
```

---

# 4. Own files

変更可能:

* `ComfyUIPortable/GITHUB_MANGA.txt`
* `ComfyUIPortable/docs/manga/STATUS.md`
* `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
* `ComfyUIPortable/docs/manga/cards/README.md`
* `ComfyUIPortable/docs/manga/cards/current/README.md`
* `ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md`
* `ComfyUIPortable/docs/manga/reports/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE_REPORT.md`
* `ComfyUIPortable/docs/manga/reports/README.md`

TF2 Cardをcompletedへ移す場合のみ:

* `ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`
* `ComfyUIPortable/docs/manga/cards/completed/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

---

# 5. Do not touch

禁止:

* Manga Python
* Manga JavaScript
* workflow JSON
* schema
* runtime
* tests
* verification
* output
* H3
* H3 docs
* H3 workflows
* ComfyUI core/frontend
* Tegaki本体
* EasyReforgeExtension
* RegionalLoRALab
* M3A.1 implementation report本文
* M3A1-TF2 reportの歴史的実行結果の書き換え
* 過去completed Cardの内容変更

---

# 6. Historical record rule

重要:

`M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_REPORT.md`

に記録された

```text
Publication: LOCAL
Owner push required: YES
Web GPT verification: BLOCKED UNTIL PUSH
```

は、**LUNA終了時点の歴史的事実**である。

原則として書き換えない。

現在状態はTF2.1 reportとCURRENT AUTHORITYで更新する。

これにより、

* 当時の終了状態
* その後Ownerがpush
* SOLが公開確認
* TF2.1でCURRENT AUTHORITYを閉鎖

という時系列を保持する。

---

# 7. Mandatory audit

編集前に:

```bash
rg -n \
  "Publication state: LOCAL|Publication: LOCAL|Owner push required|blocked until push|BLOCKED UNTIL PUSH|public-URL review remain pending|Current repository publication" \
  ComfyUIPortable/GITHUB_MANGA.txt \
  ComfyUIPortable/docs/manga/STATUS.md \
  ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md \
  ComfyUIPortable/docs/manga/cards \
  ComfyUIPortable/docs/manga/reports
```

結果をTF2.1 reportへ記録する。

historical TF2 report内の`LOCAL`は修正対象から除外する。

---

# 8. Required correction A — GITHUB_MANGA

`ComfyUIPortable/GITHUB_MANGA.txt`

のCURRENT operational stateを更新する。

現在の

```text
Current repository publication:
db7611c120af35504425872e896dc0229216b8c9
```

を、現在公開済みのpublication truthへ更新する。

このCard開始時点の確認済み値:

`5c9da782316b99ceeb6ecfb85695bb6965d3bf35`

ただしTF2.1を公開するcommit自体がさらに新しいため、LUNA終了時に未知の未来SHAを推測して書かない。

push前の文書には次のように意味を分けてもよい:

```text
Latest SOL-verified repository publication:
5c9da782316b99ceeb6ecfb85695bb6965d3bf35

M3A1-TF2 publication:
PUBLISHED / SOL VERIFIED
```

TF2.1自身のpublicationはOwner push後にSOLが確認する。

## GITHUB_MANGAに必須の状態

```text
M3A1-TF2 publication:
PUBLISHED

M3A1-TF2 SOL public-URL review:
PASS

Browser:
PENDING

Visual:
PENDING

Owner acceptance:
PENDING

M3B authorization:
NO

Next recommended Card:
M3A.1 Browser Closure
```

TF2 CardとTF2 reportへのraw URLを維持する。

---

# 9. Required correction B — STATUS

現在の

```text
Publication state: LOCAL;
Owner push required;
Web GPT verification is blocked until push.
```

を現在の事実へ変更する。

最低限:

```text
M3A1-TF2 publication: PUBLISHED
SOL public-URL review: PASS
Verified public commit: 5c9da782316b99ceeb6ecfb85695bb6965d3bf35
```

を記録する。

Browser / Visual / Owner acceptance / M3B authorizationは変更しない。

---

# 10. Required correction C — Handoff

`WEBGPT_SOL_LUNA_HANDOFF.md`に残る:

```text
M3A1-TF2のPublicationはLOCAL。
Owner push後にWeb GPT SOLが公開URLを再確認する。
```

を削除または現在状態へ更新する。

例えば:

```text
M3A1-TF2 publication:
PUBLISHED at 5c9da782316b99ceeb6ecfb85695bb6965d3bf35

Web GPT SOL public-URL review:
PASS

次の実装候補:
M3A.1 Browser Closure
```

また、audit時HEADを「現在HEAD」と誤解させないよう、

`Current repository publication`

と

`Manga implementation Review Target`

を明確に分離する。

---

# 11. Required correction D — Card Router

現在の:

```text
Publication state: LOCAL;
Owner push and SOL public-URL review remain pending.
```

を現在状態へ更新する。

TF2はすでに公開・SOL確認済み。

## Recommended routing

TF2は実行終了済みなので、可能なら:

`cards/current/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

から

`cards/completed/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

へ移動する。

その場合必ず:

* `cards/README.md`
* `cards/current/README.md`
* `GITHUB_MANGA.txt`
* STATUS
* Handoff

のTF2 URL/pathもcompleted側へ合わせる。

### 重要

移動後に旧`current/...TF2...md` URLを残して404にしてはいけない。

### current slot

TF2.1作業中は:

```text
Active implementation Card:
M3A1-TF2.1 — Post-Push Publication Truth Closure
```

作業終了時は:

```text
Active implementation Card:
NONE
```

としてよい。

ただしTF2.1 Cardの最終場所をrouterから辿れるようにする。

---

# 12. TF2.1 report

必ず作成:

`ComfyUIPortable/docs/manga/reports/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE_REPORT.md`

内容:

```text
# M3A1-TF2.1 Post-Push Publication Truth Closure Report

Date
Execution baseline
origin/main at start

Reason
- TF2 was published after its LOCAL report was written
- SOL verified public URLs
- CURRENT AUTHORITY still contained pre-push state

Verified public TF2 commit
5c9da782316b99ceeb6ecfb85695bb6965d3bf35

Public verification
Canonical entry: PASS
TF2 Card: PASS
TF2 Report: PASS
STATUS: PASS
Handoff: PASS

Changes
- GITHUB_MANGA
- STATUS
- Handoff
- Card routing
- report routing

Historical TF2 report
UNCHANGED

M3A.1 Review Target
a7f0baaa89a2e315b0492573c9da19e50727928b

Tests: NOT RUN / NOT REQUIRED
Runtime: NOT RUN / NOT REQUIRED
Browser: PENDING
Visual: PENDING
Owner acceptance: PENDING
M3B authorization: NO

Next recommended Card:
M3A.1 Browser Closure

TF2.1 publication:
LOCAL / Owner push required
```

---

# 13. Publication semantics

今回もLUNA自身がpushしない場合:

TF2については:

```text
M3A1-TF2 publication: PUBLISHED
M3A1-TF2 SOL verification: PASS
```

と書いてよい。

これはすでにWeb GPT SOLがGitHubで実証済みだからである。

一方、今回のTF2.1自身はpush前なので:

```text
M3A1-TF2.1 publication: LOCAL
Owner push required: YES
```

とする。

この2つを混同しない。

---

# 14. Validation

## Diff

```bash
git diff --check
```

## stale CURRENT authority check

```bash
rg -n \
  "TF2.*LOCAL|TF2.*push required|TF2.*blocked until push|TF2.*review remain pending" \
  ComfyUIPortable/GITHUB_MANGA.txt \
  ComfyUIPortable/docs/manga/STATUS.md \
  ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md \
  ComfyUIPortable/docs/manga/cards/README.md \
  ComfyUIPortable/docs/manga/cards/current/README.md
```

TF2について0件になること。

TF2.1自身の`LOCAL`は許可。

## public commit existence

```bash
git cat-file -e \
  5c9da782316b99ceeb6ecfb85695bb6965d3bf35^{commit}

git merge-base --is-ancestor \
  5c9da782316b99ceeb6ecfb85695bb6965d3bf35 \
  origin/main
```

PASS必須。

## Review Target

```bash
git cat-file -e \
  a7f0baaa89a2e315b0492573c9da19e50727928b^{commit}
```

Review Targetを最新HEADへ置換しない。

---

# 15. Blank-Web-GPT acceptance

GITHUB_MANGA.txtだけを入口として、以下に回答可能か確認する。

```text
1. M3A.1 implementation Review Targetは？
2. TF2はGitHub公開済みか？
3. TF2のSOL公開確認は終わったか？
4. TF2 Cardはどこか？
5. TF2 reportはどこか？
6. active implementation Cardはあるか？
7. Browser statusは？
8. Visual statusは？
9. Owner acceptanceは？
10. M3B authorizationは？
11. 次に進むべきCardは？
```

期待:

```text
1. a7f0baaa89a2e315b0492573c9da19e50727928b
2. YES
3. PASS
4. GitHub raw URLあり
5. GitHub raw URLあり
6. NONE（TF2.1終了後）
7. PENDING
8. PENDING
9. PENDING
10. NO
11. M3A.1 Browser Closure
```

11/11 PASS必須。

---

# 16. Tests / Runtime / Browser

```text
Python: NOT RUN / NOT REQUIRED
JavaScript: NOT RUN / NOT REQUIRED
Runtime: NOT RUN / NOT REQUIRED
GPU: NOT RUN / NOT REQUIRED
Browser: NOT RUN
Visual: PENDING
Owner acceptance: PENDING
```

M3A.1 Browser acceptanceをこのCardで変更しない。

---

# 17. Stop conditions

STOP:

* `5c9da782...`がTF2 publication commitではない
* TF2 Cardまたはreportがpublic GitHubから消えている
* own filesへ競合する新しい変更が入っている
* Review Target意味境界が変化している
* implementation変更が必要になる
* H3変更が必要になる

Astraへは送らない。

---

# 18. Required final response

```text
Card: M3A1-TF2.1

Execution baseline:
Local HEAD:
origin/main:

Changed files:

Verified TF2 public commit:
5c9da782316b99ceeb6ecfb85695bb6965d3bf35

TF2 Card URL:
TF2 Report URL:

TF2 publication:
PUBLISHED

SOL public-URL review:
PASS

Current Manga implementation Review Target:
a7f0baaa89a2e315b0492573c9da19e50727928b

Blank-Web-GPT traceability:
11/11 PASS / FAIL

Historical TF2 report:
UNCHANGED / CHANGED

Contract:
PASS / FAIL

Documentation truth:
PASS / FAIL

Tests:
NOT RUN / NOT REQUIRED

Runtime:
NOT RUN / NOT REQUIRED

Browser:
PENDING

Visual:
PENDING

Owner acceptance:
PENDING

M3B authorization:
NO

Next recommended Card:
M3A.1 Browser Closure

TF2.1 publication:
LOCAL / PUSHED <SHA>

Owner action required:
```

---

# 19. Close condition

TF2.1のlocal作業終了だけではTF2.1自身を`PUSHED`としない。

Ownerがcommit/pushした後、公開SHAをWeb GPT SOLへ渡す。

Web GPT SOLが:

1. `GITHUB_MANGA.txt`
2. STATUS
3. Handoff
4. Card Router
5. TF2 Card
6. TF2 report
7. TF2.1 Card
8. TF2.1 report

を公開GitHubから確認する。

その時点で、

**M3A1-TF2系列を完全閉鎖**

する。

次のCardは:

**M3A.1 Browser Closure**

とする。

M3Bはまだ開始しない。


