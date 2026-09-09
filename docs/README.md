# ComfyUIPortable Documentation Router

更新: 2026-09-09 JST。

`docs/`はproject別に分離する。現在地、計画、報告、検証資料を探す時は対象domainのHubから入る。

| Domain | Document Hub | External AI Entry | Runtime / Workflow boundary |
|---|---|---|---|
| Manga Authoring | [`manga/README.md`](manga/README.md) | [`../GITHUB_MANGA.txt`](../GITHUB_MANGA.txt) | `custom_nodes_custom/tegaki_manga_nodes/`, `workflows/manga/` |
| MiniMax H3 Video | [`h3/README.md`](h3/README.md) | [`../GITHUB_H3.txt`](../GITHUB_H3.txt) | `h3/`, `workflows/h3/` |

共通入口は [`GITHUB_ComfyUI.txt`](../GITHUB_ComfyUI.txt)。製品目標は同じTEGAKI shell/skinの
上位tabでMangaとVideo (H3)を切り替える構成だが、domain別のschema、runtime、workflow、
evidence、outputは明示的な統合Cardまで分離する。
