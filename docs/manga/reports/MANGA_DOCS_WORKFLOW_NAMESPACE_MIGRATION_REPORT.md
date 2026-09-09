# Manga Docs / Workflow Namespace Migration Report

実施日: 2026-09-09 JST。

## Result

`docs/`直下に混在していたManga文書を`docs/manga/`へ集約し、`docs/`をManga/H3の二系統が
明確なrouter構造へ変更した。Ownerが先に`workflows/manga/`へ移したWorkflowについても、
current navigation、generator、testの旧パスを更新した。

Baselineはcleanな`77de3c48`で、同commitにManga Workflowの100% renameとSOL/LUNA handoffが
公開済みだった。

## Physical moves

| From | To | Files |
|---|---|---:|
| `docs/STATUS.md`, `docs/DOCUMENT_REGISTER.md` | `docs/manga/` | 2 |
| Manga contract documents at `docs/*.md` | `docs/manga/contracts/` | 4 |
| Workflow/dependency/issue/manifests at `docs/*.md` | `docs/manga/references/` | 4 |
| `docs/Astra/` | `docs/manga/archive/astra/` | 2 |
| `docs/plans/` | `docs/manga/plans/` | 6 |
| `docs/reports/` | `docs/manga/reports/` | 43 |
| `docs/verification/` | `docs/manga/verification/` | 316 |

`docs/README.md`を共通routerとして追加した。`docs/h3/`は移動せず、H3の既存GitHub URLと
relative pathを維持する。

## Workflow path correction

- Canonical Manga: `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`
- Historical/oracle Manga: `workflows/manga/Archive/*.json`
- H3: `workflows/h3/*.json`、変更なし

Current generator/test scriptsは新しいManga pathへ更新した。`workflows/README.md`はdomain routerへ
変更した。旧Phase reportとcompleted/archive Card本文は、その時点のpathを示す履歴として書き換えない。

## GitHub entry URLs

`GITHUB_MANGA.txt`の`main`向けURLは次へ変更した。

- `ComfyUIPortable/docs/manga/STATUS.md`
- `ComfyUIPortable/docs/manga/DOCUMENT_REGISTER.md`
- `ComfyUIPortable/docs/manga/plans/...`
- `ComfyUIPortable/docs/manga/reports/...`

M3A.1 implementation Review Target `a7f0baaa...`のpinned report URLは、そのcommitに存在する
`ComfyUIPortable/docs/reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md`を維持する。
現在のmain pathへ置換するとその固定SHAで404になるためである。

`GITHUB_H3.txt`のH3 document URLは`docs/h3/`を移動していないため変更不要。Manga境界説明に
含まれる`docs/STATUS.md`と`docs/plans/`だけ新namespaceへ更新した。

## Non-scope

- runtime node実装、authoring schema、generation parameters
- H3 runtime/workflow/docsの物理移動
- `output/Tegaki`、`output/debug_guides`の移動
- historical pinned URLや旧Phase本文の現代化

## Verification

移動後の検証結果は次の通り。

- `docs/`直下は`README.md`、`h3/`、`manga/`のみ。
- current Markdown 95 files / local link 174件はbroken 0。
- `GITHUB_*.txt`の`main`向けraw URLは16 occurrences / 14 unique targetsで、対応するlocal targetがすべて存在。
- M3A.1のpinned SHA `a7f0baaa89a2e315b0492573c9da19e50727928b`と旧report pathの組合せは`git cat-file -e`でPASS。
- `python -m compileall -q scripts`はPASS。
- `docs/manga/verification/`と`workflows/`配下のJSON 97 filesはparse PASS。
- 移動したverification画像294 filesは、旧HEAD blobと新pathの`git hash-object`が全件一致。
- `test_workflow_json_integrity.py`、M1.1 7 tests、M2B 5 tests、M2B.1 6 tests、M0 legacy import 19 testsはPASS。
- `git diff --check`はerror 0。改行コードのworking-copy warningのみ。

runtime node、H3、Workflow JSONの内容は変更していない。script変更は移動後pathへの追随だけである。
