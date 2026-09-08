# Manga Historical Instruction Archive

更新: 2026-09-08 JST

旧 `GPTからの指示書/` に混在していた、現行でない指示書と構想資料の保管場所。
ここにある文書は経緯と当時の判断を確認するための資料で、現在の実装指示ではない。

| Path | Contents | Count | Use |
|---|---|---:|---|
| `instructions/phase2/` | 初期構築、Phase 2改修、2.1安定化と回帰修正 | 4 | legacy contract調査時のみ |
| `instructions/phase3/` | Phase 3A〜3Lの旧実装依頼 | 22 | 過去実装とreportの照合時のみ |
| `plans/` | 旧中間計画、GUI分離追補、将来構想 | 4 | 現行Astra計画との差分調査時のみ |
| `duplicates/` | M1.1依頼書のbyte-identical複製 | 1 | provenance保全のみ |

新しい作業判断は [`docs/STATUS.md`](../../STATUS.md)、
[`GITHUB_MANGA.txt`](../../../GITHUB_MANGA.txt)、
[`Manga Execution Card Router`](../cards/README.md) の順に確認する。

ファイル名は検索性のため正規化したが、本文は移動前とbyte-identicalに保つ。
旧pathはGit履歴とnamespace migration reportで追跡する。
