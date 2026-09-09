# ComfyUIPortable Workflow Router

更新: 2026-09-09 JST。

`workflows/`直下はdomain routerであり、実Workflow JSONを直接置かない。

## Manga Authoring

- Canonical active workflow: [`manga/MINIMUM_HAND_MANGA_DRAFT.json`](manga/MINIMUM_HAND_MANGA_DRAFT.json)
- Historical/oracle workflows: [`manga/Archive/`](manga/Archive/)

`manga/Archive/`は過去の研究、比較、検証用Workflowを保持する。現在の製品入口として使わず、
新しいManga production workflowはSOLが発行した限定Cardで`workflows/manga/`へ追加する。

## MiniMax H3

- H1A Native T2V: [`h3/H1A_NATIVE_T2V_BASE.json`](h3/H1A_NATIVE_T2V_BASE.json)
- H1B Native I2V: [`h3/H1B_NATIVE_I2V_BASE.json`](h3/H1B_NATIVE_I2V_BASE.json)
- H1B.1 Native FL2VA: [`h3/H1B1_NATIVE_FL2VA_BASE.json`](h3/H1B1_NATIVE_FL2VA_BASE.json)

MangaとH3のworkflow、adapter、保存意味を相互流用しない。共通TEGAKI shellは上位tabを所有するが、
domain workflowを統合する場合は別のShell Integration Cardと両系統の回帰確認を必要とする。
