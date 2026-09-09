# Manga Authoring Document Hub

更新: 2026-09-09 JST

このHubは `ComfyUIPortable` 内のManga Authoring専用入口です。MiniMax H3と
Portable基盤を共有しますが、現在はplanning、runtime semantics、workflow、
evidence、External AI Entryを分離します。

## Current authority

| Role | Path |
|---|---|
| External AI Entry | [`GITHUB_MANGA.txt`](../../GITHUB_MANGA.txt) |
| Current state | [`docs/STATUS.md`](../STATUS.md) |
| Document authority | [`docs/DOCUMENT_REGISTER.md`](../DOCUMENT_REGISTER.md) |
| Strategic SSOT | [`ASTRA_MANGA_AUTHORING_MASTER_PLAN.md`](../plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md) |
| Current UX design | [`ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md`](../plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md) |
| Asset/workflow audit | [`ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md`](../plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md) |
| New-chat handoff | [`WEBGPT_SOL_LUNA_HANDOFF.md`](WEBGPT_SOL_LUNA_HANDOFF.md) |
| SOL/LUNA process | [`ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md`](../plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md) |
| Card routing | [`docs/manga/cards/README.md`](cards/README.md) |

Current implementation review target is M3A.1 commit
`a7f0baaad6e7f5d82c39b1042e8a3c4e9f1a7d5b`. Headless and structural pixel
checks passed; Owner live-browser acceptance remains pending. There is no active
LUNA implementation Card. Start a new Web GPT SOL chat with the
[handoff](WEBGPT_SOL_LUNA_HANDOFF.md), then have SOL issue one fresh bounded Card.

## Execution cards and historical instructions

- [Card router and completed-card index](cards/README.md)
- [Historical instruction and plan archive](archive/README.md)

旧 `GPTからの指示書/` は役割が曖昧で、完了Cardと旧戦略が同じ階層に混在していたため廃止した。
完了Cardは `cards/completed/`、旧Phase指示と構想資料は `archive/` に分離している。
LUNA開始時は完了Cardを再利用せず、live stateを監修したSOLが `cards/current/` に新しい限定Cardを発行する。

## Reports and verification

- [Current and historical report index](reports/README.md)
- [Verification index](verification/README.md)
- [M3A.1 current report](../reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md)
- [Migration report](reports/MANGA_DOCUMENT_NAMESPACE_MIGRATION_REPORT.md)

`docs/reports/` and `docs/verification/` remain at their established paths.
Current scripts and manifests directly reference the verification paths, and
many current/historical documents link to both trees. The Hub supplies the Manga
namespace without breaking those contracts.

## Research and references

- [Phase 3L prior-art audit](research/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md)
- [External asset/reference inventory](references/RESEARCH_REFERENCES.md)
- [Migration map](MANGA_DOCUMENT_NAMESPACE_MIGRATION_MAP.md)

These two loose Manga-specific documents were moved after reference audit.
Historical pinned URLs and historical report wording retain their old paths.

## Boundary

Manga Authoring and H3 are separate production subsystems. Namespace separation
does not merge their runtime semantics. H3 Manga is deferred; a possible future
hierarchy is `docs/h3/manga/`, `workflows/h3/manga/`, and `output/h3/manga/`
only after its own gate. The product target is a common TEGAKI shell/skin with
top-level Manga and Video (H3) tabs after both domain flows are independently regressable.

Production output remains in legacy paths pending a separate migration card.
Selected review evidence may later use `docs/manga/evidence/`, but no evidence
was duplicated or moved merely to make the tree look uniform.
