# Manga Document Namespace Migration Map

監査日: 2026-09-08。baseline HEAD `b113f8e3`。物理移動前にrepository-wide
`rg`でMarkdown、Python、JavaScript、JSON、workflow、scripts、GitHub entry、
output prefixを調査した。

| Current path / asset | Role / authority | References and runtime use | Proposed path | Move now | Required updates / reason |
|---|---|---|---|---|---|
| `GITHUB_ComfyUI.txt` | 旧Manga canonical entry | 21 filesに名称参照。H3入口も旧境界を記載 | routerとして同path維持 | YES: role change | Current authorityとH3 navigationを更新。履歴文書は変更しない |
| 新規 `GITHUB_MANGA.txt` | Manga canonical entry | なし | root同名 | YES: add | Manga status、SHA、read order、境界を所有 |
| `GITHUB_H3.txt` | H3 canonical entry | H3 Hubから参照 | 同path | NO | canonicalを維持。旧taskの「router禁止」文だけ新しい明示指示に合わせる |
| `docs/STATUS.md` | Manga current state | 強く参照されるCurrent Authority | 同path | NO | entryだけMangaへ更新。M3A.1状態を維持 |
| `docs/DOCUMENT_REGISTER.md` | Portable全体のauthority register | Current authority | 同path | NO | Manga/H3 domain mapを追加 |
| `docs/plans/ASTRA_*.md` | Manga strategic/current process | 現行Cardと入口から参照 | 同path | NO | path churn回避。protocolのentry名だけ更新 |
| `GPTからの指示書/` 43 files | 完了Card、旧Phase指示、旧構想、重複が混在 | runtime参照なし。current report 3件がCard名を参照 | `docs/manga/cards/completed/` と `docs/manga/archive/` | YES | 役割別に分離し、製品名prefixと依頼者/model由来suffixを除去。詳細は各index |
| `docs/RESEARCH_REFERENCES.md` | 外部asset/license inventory | current README 1件、歴史文書/旧Cardに複数名称参照。runtimeなし | `docs/manga/references/RESEARCH_REFERENCES.md` | YES | README/current Hubを更新。歴史本文は保存 |
| `docs/reports/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md` | historical prior-art research | Current report 1件、Astra request、旧Card、archived/pinned URL。runtimeなし | `docs/manga/research/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md` | YES | Current reportのrelative linkとcurrent-main navigationを更新。pinned historical URLは旧path保持 |
| `docs/reports/` remaining 43 files | current reports＋historical evidence | current/historical docs 21件以上がtreeへ参照。current reportsはEntry/STATUSに直結 | `docs/manga/reports/` candidate | NO / LATER | 一括移動の便益よりcurrent/pinned navigation churnが大きい。Hub/indexでnamespace付与 |
| `docs/verification/` 316 files / 303,495,779 bytes | generated evidence、manifest、contact sheets | 11 scriptsがdirect path参照。manifest内部にも自己path多数 | `docs/manga/verification/` candidate | NO / LATER | generator・manifest・report・review linkを同時変更する別Cardが必要 |
| `docs/WORKFLOW_INDEX.md` | existing workflow navigation | workflow番号/pathの歴史を所有 | 同path | NO | Workflow migrationと一緒に後段判断 |
| `workflows/` Manga files | runtime/saved workflow | app、generator、tests、manifestsから参照可能 | `workflows/manga/` candidate | NO | 添付Rev.2の明示除外。別migration Card |
| `output/Tegaki` | Manga runtime/verification output | 193 files、224,514,215 bytes。47 repository filesにpath参照。複数scriptsで`filename_prefix=Tegaki/...` | `output/manga/generated` | NO / separate gate | scripts/workflows/tests/docsのprefixとexisting evidence provenanceを更新する必要あり |
| `output/debug_guides` | historical debug guide images | 5 files、37,795 bytes。tracked sourceでdirect path参照0件 | `output/manga/debug_guides` | NO / separate gate | 小さくても文書整理と混ぜない。生成元・oracle利用をruntimeで再確認後に移動 |
| future H3 output | H3 production output | legacyなし | `output/h3/video`, `output/h3/still`, `output/h3/debug`, `output/h3/tests` | policy only | H3 implementation Cardが最初からdomain prefixを指定 |

## Historical link policy

`main`を指すcurrent navigationは新pathへ更新する。過去commit SHAを含むURLは、
そのcommitに存在した旧pathを示す証拠なので変更しない。旧Phase report本文のpath、
PASS/FAIL、観察も現在構造へ合わせて書き換えない。

## Deferred migration gates

`MANGA_OUTPUT_NAMESPACE_MIGRATION`では最低限、47参照fileの分類、すべての
`filename_prefix`、ComfyUI output root、scriptsのcopy/source path、manifest内path、
旧出力のprovenanceを扱う。移行は新出力先への書込み切替→関連検証→必要なら
既存生成物の移動、の順とし、本migrationでは実行しない。

`MANGA_VERIFICATION_NAMESPACE_MIGRATION`はoutput移行と同じCardに混ぜず、生成script、
manifest、report、GitHub URLの更新が一つの検証可能なsliceになる場合だけ行う。

## 2026-09-09 superseding decision

Ownerの明示指示により、上表で`NO / LATER`としていた文書・Workflow namespaceを実施した。
現在の配置は次の通り。

| Previous path | Current path | Status |
|---|---|---|
| `docs/STATUS.md` | `docs/manga/STATUS.md` | MOVED |
| `docs/DOCUMENT_REGISTER.md` | `docs/manga/DOCUMENT_REGISTER.md` | MOVED |
| `docs/plans/` | `docs/manga/plans/` | MOVED |
| `docs/reports/` | `docs/manga/reports/` | MOVED |
| `docs/verification/` | `docs/manga/verification/` | MOVED; current generators/manifests updated |
| Manga contracts/references at `docs/*.md` | `docs/manga/contracts/`, `docs/manga/references/` | MOVED |
| `workflows/Archive/` | `workflows/manga/Archive/` | Owner move published in `77de3c48` |
| `workflows/MINIMUM_HAND_MANGA_DRAFT.json` | `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` | Owner move published in `77de3c48` |

実施内容とURL判断は
[`MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md`](reports/MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md)
をcurrent recordとする。output namespaceは引き続き別gateである。
