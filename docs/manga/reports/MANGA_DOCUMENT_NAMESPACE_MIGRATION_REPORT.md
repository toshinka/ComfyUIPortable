# Manga Document Namespace Migration Report

実施日: 2026-09-08 JST

## Summary

Illustrious中心のManga AuthoringとMiniMax H3が同じPortable baseで混線しないよう、
domain-specific canonical entryとManga document hubを設けた。runtime、workflow、
authoring schema、generation recipe、model設定は変更していない。

Manga implementationはM2B.2まで完了。M3A.1はheadless/structural pixel確認済み、
Owner live-browser acceptance待ち。Gemini停止中にM3Bへ進めず、再開contextを追加した。

## H3 coexistence boundary

MangaとH3はrepository/Portable baseを共有するが、現在は別production subsystem。
planning、evidence、runtime semantics、External AI Entryを分離する。H3は
Groundwork / Pre-H0、H3 implementationとH3 Mangaは未着手。共通TEGAKI shellは
両者が独立して利用可能になった後の長期候補に留めた。

## External AI Entry migration

- Added: `GITHUB_MANGA.txt` — Manga canonical entry。
- Changed: `GITHUB_ComfyUI.txt` — Manga/H3 compatibility router。
- Retained: `GITHUB_H3.txt` — H3 canonical entry。
- Retained: implementation Review Target `a7f0baaa...`。namespace docs commitで置換しない。

## Files moved

| From | To | Reason |
|---|---|---|
| `docs/RESEARCH_REFERENCES.md` | `docs/manga/references/RESEARCH_REFERENCES.md` | runtime参照なし。内容は外部asset/reference inventory |
| `docs/reports/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md` | `docs/manga/research/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md` | runtime参照なし。reportというよりprior-art研究 |

旧 `GPTからの指示書/` 43件も役割別に移動した。内訳は完了Card 12件、Phase 2旧指示4件、
Phase 3旧指示22件、旧/将来構想4件、byte-identicalなM1.1複製1件。新しい配置は
[`cards/README.md`](../cards/README.md) と [`archive/README.md`](../archive/README.md) を正本indexとする。
ファイル名から冗長な `ComfyUI_Portable_`、末尾 `_Request`、依頼時のmodel名を除去し、
milestoneと責務が先に読める名称へ統一した。本文は変更していない。

## Files deliberately retained

- `docs/STATUS.md`, `docs/DOCUMENT_REGISTER.md`, `docs/plans/ASTRA_*.md`: current authorityと既存Card参照を保つ。
- `docs/reports/`残り43件: current reportとhistorical evidenceのstable pathを保つ。
- `docs/verification/`316件: 11 scriptsのdirect output/reference contractを保つ。
- `workflows/`: runtime migrationは今回の範囲外。
- old Phase report wordingとpinned historical URL: provenanceを保つ。

## Files added

- `docs/manga/README.md`
- `docs/manga/MANGA_DOCUMENT_NAMESPACE_MIGRATION_MAP.md`
- `docs/manga/MANGA_GEMINI_RESTART_CONTEXT.md`
- `docs/manga/cards/README.md`
- `docs/manga/archive/README.md`
- `docs/manga/reports/README.md`
- `docs/manga/reports/MANGA_DOCUMENT_NAMESPACE_MIGRATION_REPORT.md`
- `docs/manga/verification/README.md`

## Links updated

Current README、STATUS、Document Register、Astra execution protocol、Manga Hub、
Card参照を新しいentry/pathへ更新する。H3 entry/Hubは新routerを認識するが、H3 canonical
ownershipは変えない。移動した旧指示書の本文、archived file、pinned URLはhistorical recordとして
書き換えない。

## Output namespace audit

### `output/Tegaki`

- 193 files / 224,514,215 bytes。
- 47 repository filesに`output/Tegaki`参照。
- current/historical scriptsに`filename_prefix: Tegaki/...`が多数存在。
- Proposed destination: `output/manga/generated`。
- Risk: HIGH。出力prefix、test source path、manifest provenance、docsを同時に更新する必要がある。

### `output/debug_guides`

- 5 files / 37,795 bytes。
- tracked source内のexact path参照は0件。
- Proposed destination: `output/manga/debug_guides`。
- Risk: LOW〜MEDIUM。ただし生成元/手動oracle利用のruntime確認を別Gateで行う。

Output was physically moved: **NO**。`output/manga/`も先行作成していない。

Future H3 implementation should use `output/h3/` from its first output-producing
Card. H3 Mangaは開始Gateまでfolderを作らず、将来は`output/h3/manga/`を候補とする。

## Production output and review evidence

大量のruntime outputをGitHub review evidenceとして扱わない。将来、選抜した
screenshots/contact sheets/manifestsだけを`docs/manga/evidence/`へ置く余地はあるが、
今回そのfolderやduplicate evidenceは作っていない。

## Runtime/workflow impact

NONE expected. Python、JavaScript、custom node、workflow JSON、schema、model config、
generation parametersを変更していない。検証はdocument link/reference auditとgit diffで行う。

## Deferred

- `MANGA_OUTPUT_NAMESPACE_MIGRATION`
- `MANGA_VERIFICATION_NAMESPACE_MIGRATION`
- optional `workflows/manga/` migration
- M3A.1 Owner live-browser acceptance
- new SOL-authored M3B instruction after acceptance
- H3 implementation / H3 Manga / common shell

## Review state

作業開始時はHEAD `b113f8e3`、`origin/main`と一致しworktreeはcleanだった。変更後、
現行の新規/変更Markdownのlocal linkはbroken 0。旧フォルダから移した43件はGit blobの
multiset比較で全件byte-identical、M1.1複製も同一hashのまま保管した。移動文書内の相対linkは
0件で、移動によるlink切れはない。`git diff --check` PASS、runtime/workflow/script/config diffは0を確認した。

この変更はlocal worktreeでの文書整理。commit/push前はGitHub current-main linkを
公開済みと扱わない。Owner push後にWeb GPTは`GITHUB_MANGA.txt`から監査できる。
