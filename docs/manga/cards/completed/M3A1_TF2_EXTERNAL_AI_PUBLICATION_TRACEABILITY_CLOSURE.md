# M3A1-TF2 — External AI Publication Traceability Closure

Date: 2026-09-09 JST
Issuer: Web GPT SOL
Executor: LUNA local chat
Owner: repository owner

このCardの目的は機能実装ではない。

**Web GPT SOLが新規チャットから `GITHUB_MANGA.txt` 1枚を読んだだけで、現在地、最新publication、直近作業、作業結果、次gate、証拠文書へGitHub URLで到達できる状態を作る。**

「文書を書いた」だけでは完了ではない。

**GitHub上のcanonical entryから実際に辿れなければ未完了とする。**

---

## 0. Current authority / baseline

Repository:

`https://github.com/toshinka/tegaki`

Current verified `main` baseline at Card issuance:

`db7611c120af35504425872e896dc0229216b8c9`

M3A.1 implementation Review Target:

`a7f0baaa89a2e315b0492573c9da19e50727928b`

Canonical external entry:

`ComfyUIPortable/GITHUB_MANGA.txt`

Raw canonical entry:

`https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB_MANGA.txt`

開始時に必ず:

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

を実行する。

### Baseline rule

`origin/main` が

`db7611c120af35504425872e896dc0229216b8c9`

から進んでいた場合、今回は即STOPしない。

まず新しいcommitの変更fileだけを確認する。

```bash
git diff --name-status \
  db7611c120af35504425872e896dc0229216b8c9..origin/main
```

今回のown filesと競合する変更がある場合だけSTOPしてSOLへ返す。

無関係domainのcommitが進んだだけなら、最新`origin/main`を実行baselineとしてreportへ記録して継続する。

以前のCardのように、単純な「HEADが進んだ」だけで無条件終了しない。

---

## 1. Background truth

直前のM3A1-TF1はbaseline gateでSTOPした。

旧baseline:

`77de3c48ea9fd72d349cf9da31aa123097ffabf2`

検出した新しい`origin/main`:

`db7611c120af35504425872e896dc0229216b8c9`

M3A1-TF1が修正しようとしていた誤Review Target SHA:

`a7f0baaad6e7f5d82c39b1042e8a3c4e9f1a7d5b`

は、`db7611c...`側ですでに

`a7f0baaa89a2e315b0492573c9da19e50727928b`

へ修正されていた。

したがってM3A1-TF1の内容を再実装しない。

今回修正するのは、

**外部AIからの追跡性とpublication truth**

だけである。

---

## 2. Goal

利用者が新しいWeb GPTチャットへ

`GITHUB_MANGA.txt`

のraw URLだけを渡した場合、そのWeb GPTが追加のOwner説明なしに最低限以下を把握できること。

1. 現在のrepository `main` publication
2. Manga implementation Review Target
3. 現在のManga status
4. Active Cardがあるかないか
5. 直近に何のmaintenance / truth-fixをしたか
6. そのCard本文
7. その作業結果report
8. Browser / Visual / Owner acceptanceの状態
9. 次に実施可能なCard
10. M3Bへ進んでよいか
11. 正本文書群への直接URL

この11項目へ`GITHUB_MANGA.txt`から辿れなければFAIL。

---

## 3. Own files

変更可能:

* `ComfyUIPortable/GITHUB_MANGA.txt`
* `ComfyUIPortable/docs/manga/STATUS.md`
* `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
* `ComfyUIPortable/docs/manga/cards/README.md`
* `ComfyUIPortable/docs/manga/cards/current/README.md`
* `ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`
* `ComfyUIPortable/docs/manga/reports/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_REPORT.md`
* `ComfyUIPortable/docs/manga/reports/README.md`

必要な場合のみ:

* `ComfyUIPortable/docs/manga/DOCUMENT_REGISTER.md`

---

## 4. Do not touch

変更禁止:

* Manga Python implementation
* Manga JavaScript implementation
* workflow JSON
* schema
* runtime adapter
* tests
* verification image / manifest
* output
* H3
* H3 docs
* H3 workflow
* common ComfyUI core/frontend
* Tegaki本体
* EasyReforgeExtension
* RegionalLoRALab
* historical completed Card本文
* historical report本文

今回のCardでM3A.1 Browser Closureを実施しない。

今回のCardでM3Bを開始しない。

---

## 5. Mandatory first audit

現在の正本を読む。

順序:

1. `ComfyUIPortable/GITHUB_MANGA.txt`
2. `ComfyUIPortable/docs/manga/STATUS.md`
3. `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
4. `ComfyUIPortable/docs/manga/cards/README.md`
5. `ComfyUIPortable/docs/manga/cards/current/README.md`
6. `ComfyUIPortable/docs/manga/reports/README.md`
7. `ComfyUIPortable/docs/manga/MANGA_DOCUMENT_NAMESPACE_MIGRATION_MAP.md`
8. `ComfyUIPortable/docs/manga/reports/MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md`

次に確認:

```bash
rg -n \
  "LOCAL PENDING|OWNER COMMIT|Review Target|Active implementation Card|Current review slice|M3A.1|M3B" \
  ComfyUIPortable/GITHUB_MANGA.txt \
  ComfyUIPortable/docs/manga/STATUS.md \
  ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md \
  ComfyUIPortable/docs/manga/cards \
  ComfyUIPortable/docs/manga/reports
```

結果をreportへ記録する。

---

## 6. Required correction A — publication truth

現在の`GITHUB_MANGA.txt`には

`Docs namespace consolidation publication: LOCAL PENDING OWNER COMMIT/PUSH`

という記述がある。

しかしこのnamespace consolidationは現在すでにGitHub `main`の

`db7611c120af35504425872e896dc0229216b8c9`

に存在する。

したがって、その記述を事実に合わせる。

例:

```text
Docs namespace consolidation publication:
db7611c120af35504425872e896dc0229216b8c9
```

または、それより新しいmain commitへpublicationされたことが実証できる場合は、その実在SHAを使う。

`LOCAL PENDING OWNER COMMIT/PUSH`をGitHub公開済み状態のまま残さない。

推測SHAは禁止。

必ず:

```bash
git cat-file -e <SHA>^{commit}
git merge-base --is-ancestor <SHA> origin/main
```

で検証する。

---

## 7. Required correction B — External AI traceability section

`GITHUB_MANGA.txt`に、明示的に次のsectionを追加する。

見出し名:

```text
Latest operational handoff
--------------------------
```

または意味が同等で明確な名称。

最低限、以下を含める。

### Current repository publication

最新確認済み`main` SHA。

### Current Manga implementation Review Target

`a7f0baaa89a2e315b0492573c9da19e50727928b`

### Active implementation Card

今回作業中は:

`M3A1-TF2 — External AI Publication Traceability Closure`

作業終了後にCard RouterをNONEへ戻した場合は:

`NONE`

ただし直近完了CardへのURLを残す。

### Latest operational Card

raw GitHub URLを必ず記載。

最終配置がcompletedならcompleted URL。

currentに保持するならcurrent URL。

**パスを書くだけは禁止。Web GPTが直接取得できる完全なraw URLを書く。**

### Latest operational report

必ず完全なraw GitHub URLを書く。

今回のreport:

`ComfyUIPortable/docs/manga/reports/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_REPORT.md`

### Current Browser / Visual / Owner gate

明記:

```text
Browser: PENDING
Visual: PENDING
Owner acceptance: PENDING
M3B authorization: NO
```

### Next recommended Card

```text
M3A.1 Browser Closure
```

M3Bではない。

---

## 8. Required correction C — GITHUB_MANGA must be a usable Web GPT entry

以下の重要文書について、`GITHUB_MANGA.txt`内では相対pathだけで済ませず、raw GitHub URLを保持する。

必須:

* STATUS
* Manga README
* SOL/LUNA handoff
* Document Register
* Card Router
* Current CardまたはLatest operational Card
* Latest operational report
* M3A.1 implementation report
* Master Plan
* UX Blueprint
* Asset/Workflow Inventory
* SOL/LUNA Execution Protocol
* Namespace migration map
* Namespace migration report

Web GPTはローカルfilesystemを見られない前提で書く。

「`docs/...`を読め」だけでは不十分。

---

## 9. Required correction D — permanent operational report

必ず作成:

`ComfyUIPortable/docs/manga/reports/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_REPORT.md`

これはチャット内報告の代用品ではなく、GitHubでWeb GPTが読める恒久記録。

内容:

```text
# M3A1-TF2 External AI Publication Traceability Report

Date
Execution baseline
origin/main at start

Purpose

Observed pre-fix state
- stale publication labels
- missing operational Card URL
- missing latest operation report URL
- other observed traceability gaps

Changes made

GITHUB_MANGA publication links
- canonical entry URL
- latest Card URL
- latest report URL
- STATUS URL
- handoff URL

Review Target
M3A.1 implementation SHA

Validation

Tests: NOT RUN / NOT REQUIRED
Runtime: NOT RUN / NOT REQUIRED
Browser: PENDING
Visual: PENDING
Owner acceptance: PENDING
M3B authorization: NO

Publication state
- LOCAL
or
- PUSHED <public SHA>

Remaining Owner action
```

曖昧な文章を増やさず、事実を記録する。

---

## 10. Required correction E — Card itself must exist in repository

この指示書を以下へ保存する:

`ComfyUIPortable/docs/manga/cards/current/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

チャットだけにCardを残さない。

`cards/current/README.md`には作業中:

```text
Active implementation Card:
M3A1-TF2 — External AI Publication Traceability Closure
```

とCardへのリンクを置く。

`cards/README.md`のCurrentにも同じCardへのリンクを置く。

---

## 11. Completion routing

作業が成功した場合、Cardをcompletedへ移すかどうかは既存router規則を確認して決める。

移す場合:

`ComfyUIPortable/docs/manga/cards/completed/M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY_CLOSURE.md`

へ移動し、

* `cards/current/README.md` → Active Card NONE
* `cards/README.md` → CompletedへM3A1-TF2追加
* `GITHUB_MANGA.txt` → Latest operational Cardとしてcompleted側raw URL

へ更新する。

### 重要

Cardをcompletedへ移した結果、`GITHUB_MANGA.txt`のURLが404になることは禁止。

最終pathとGITHUB_MANGA URLを一致させること。

---

## 12. Publication contract

ここが今回最重要。

### 「作成済み」と「公開済み」を混同しない

localにreportを書いただけなら:

```text
Publication: LOCAL
```

GitHubへ実際に存在するまで:

```text
Publication: PUSHED
```

と書いてはいけない。

### Web GPT access test

commit/push後には、以下のraw URLがHTTPで取得可能でなければpublication完了ではない。

最低限:

```text
https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB_MANGA.txt
```

および、`GITHUB_MANGA.txt`に記載した

* Latest operational Card
* Latest operational report
* STATUS
* handoff

の4 URL。

Ownerがpush担当でLUNA自身がpushしない運用なら、LUNA終了時点は

```text
Publication: LOCAL
Owner push required: YES
Web GPT verification: BLOCKED UNTIL PUSH
```

と明記する。

「GitHubに反映済み」とは絶対に書かない。

---

## 13. Self-check from a blank Web GPT perspective

編集終了前に、過去会話を知らないWeb GPTを想定して`GITHUB_MANGA.txt`だけを読み直す。

以下11問に、GITHUB_MANGA本体またはそこから1クリックのraw URLだけで回答できるか確認する。

```text
1. 今のManga implementation Review Targetは何か？
2. main上で最後に公開された文書整理は何か？
3. active Cardは何か？
4. 直近に実施した作業は何か？
5. そのCard本文はどこか？
6. その作業reportはどこか？
7. M3A.1の技術statusは？
8. Browser acceptanceは？
9. Owner acceptanceは？
10. M3Bを開始してよいか？
11. 次にSOLが発行すべきCard候補は？
```

1つでも不明なら修正を続ける。

ただしscope外implementationへ広げない。

---

## 14. Validation commands

```bash
git diff --check
```

```bash
rg -n \
  "LOCAL PENDING OWNER COMMIT/PUSH" \
  ComfyUIPortable/GITHUB_MANGA.txt
```

公開済みnamespace publicationについて0件であること。

```bash
rg -n \
  "M3A1_TF2_EXTERNAL_AI_PUBLICATION_TRACEABILITY" \
  ComfyUIPortable/GITHUB_MANGA.txt \
  ComfyUIPortable/docs/manga/cards \
  ComfyUIPortable/docs/manga/reports
```

Cardとreportへの導線を確認。

さらに`GITHUB_MANGA.txt`に含まれるraw URLについて、少なくとも今回追加・変更したURLを抽出して確認する。

push前はpath整合性をlocal filesystemで確認する。

push後はHTTP 200またはGitHub APIで実在確認する。

---

## 15. Tests / Runtime / Browser

これはdocumentation/publication Card。

```text
Python tests: NOT RUN / NOT REQUIRED
JavaScript tests: NOT RUN / NOT REQUIRED
GPU Runtime: NOT RUN / NOT REQUIRED
Live Browser: NOT RUN
Visual: PENDING
Owner acceptance: PENDING
```

Browser acceptanceをこのCardで代理PASSにしない。

---

## 16. Stop / escalate

次の場合のみSTOP:

* own filesに別の未統合変更があり安全に統合できない
* Review Target SHAの意味が再び不明
* `db7611c...`がnamespace consolidationではない証拠が出る
* raw URLのcanonical pathを一意に決められない
* implementation/schema/runtime変更が必要になる
* H3変更が必要になる

「origin/mainが1commit進んだ」だけではSTOPしない。

差分を確認してscope競合の有無で判断する。

Astraは呼ばない。

---

## 17. Required final response from LUNA

終了時は必ずこの形式。

```text
Card: M3A1-TF2
Execution baseline:
Local HEAD:
origin/main:

Changed files:

GITHUB_MANGA canonical URL:
Latest operational Card URL:
Latest operational Report URL:
STATUS URL:
Handoff URL:

Review Target:
Namespace publication SHA:

Traceability 11/11:
PASS / FAIL

Contract: PASS / FAIL
Documentation: PASS / FAIL
URL/path consistency: PASS / FAIL

Tests: NOT RUN / NOT REQUIRED
Runtime: NOT RUN / NOT REQUIRED
Browser: PENDING
Visual: PENDING
Owner acceptance: PENDING
M3B authorization: NO

Publication:
LOCAL / PUSHED <SHA>

Public URLs actually verified:
- ...
- ...
- ...

Remaining Owner action:
```

### 絶対条件

「完了」と書く場合、

* Card fileが存在
* report fileが存在
* `GITHUB_MANGA.txt`から両方へURLがある
* URLと実際の最終pathが一致
* publication状態を正しく記録

のすべてを満たすこと。

1つでも満たさない場合は「完了」ではなくPARTIALまたはBLOCKEDと報告する。

---

## 18. What comes after this Card

M3A1-TF2がSOL reviewでPASSした後の次候補は、

**M3A.1 Owner Live-Browser Closure**

のみ。

このpublication CardからM3Bへ直接進まない。

Web GPT SOLが公開GitHubを再監査して次Cardを発行する。


