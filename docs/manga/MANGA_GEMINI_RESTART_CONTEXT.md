# Gemini再開時の現状コンテキスト

更新: 2026-09-08 JST。これは実装指示書ではない。

Geminiは約5日停止予定。再起動時に古いPhase/Cardを自動継続せず、SOLが
live repositoryを再監査して新しい限定指示書を発行する。

## 停止時点

- HEAD確認時: `b113f8e3`、`origin/main`と一致、作業開始時worktreeはclean。
- Manga review target: M3A.1 implementation `a7f0baaa...`、navigation `dfe944c6`。
- M0〜M2B.2: 完了。M2B.2でOwner live UI bootstrap不具合を修正済み。
- M3A.1: Headless/structural pixel oracle PASS、Owner live-browser acceptance PENDING。
- 次候補M3Bは未着手。M3A.1 Owner受入前に開始しない。
- H3: Groundwork / Pre-H0。H3 implementationとH3 Mangaは未着手。
- 今回のnamespace整理はdocs/navigationだけ。runtime、workflow、schema、outputを変更しない。

## 再開時の読み順

1. `GITHUB_MANGA.txt`
2. `docs/STATUS.md`
3. `docs/manga/README.md`
4. `docs/DOCUMENT_REGISTER.md`
5. M3A.1 reportとOwner browser結果
6. Astra Master Planの該当節
7. SOLが新規発行した一枚のCard

## SOLが再開指示を書く前に確認すること

1. `git status --short --untracked-files=all`とHEAD/originの一致。
2. M3A.1のOwner browser受入結果。PENDINGならM3Bを発行しない。
3. `GITHUB_MANGA.txt`のReview Target、STATUS、Document Registerの整合。
4. namespace整理後の移動pathを使っているか。
5. H3 files、`workflows/h3/`、`output/h3/`をManga Cardへ混ぜていないか。
6. output移行Cardが別途承認されていない限り、`output/Tegaki`を維持すること。

M3Bを発行できる場合も、rough guide image input、Character Instanceとの関連、
弱いControlNet比較、保存/再読込、Owner視覚評価を一枚の巨大実装へ無条件に
まとめない。先に入力assetとassociation contractを固定し、実画像比較の条件を
Cardに明記する。
