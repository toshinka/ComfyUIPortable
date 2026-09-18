# Manga Authoring Document Hub

> **Authority Notice**:
> Top-level operational authority is governed by [AGENTS.md](../../AGENTS.md), [docs/STATUS.md](../STATUS.md), and [GITHUB_MANGA.txt](../../GITHUB_MANGA.txt). Current cross-project UI design is governed by `docs/ui/*`.
> This hub organizes Manga domain documents, historical plans, reports, and verification evidence.

更新: 2026-09-09 JST (Manga domain hub)

このHubは `ComfyUIPortable` 内のManga Authoring専用入口です。MiniMax H3と
Portable基盤を共有しますが、現在はplanning、runtime semantics、workflow、
evidence、External AI Entryを分離します。

## Operational Authority & Domain Reference Map

### Top-Level Operational Authority
| Role | Path | Authority Scope |
|---|---|---|
| Operating rules & Modes | [`AGENTS.md`](../../AGENTS.md) | Top-level agent operating contract (Level 1) |
| Cross-Project Operational State | [`docs/STATUS.md`](../STATUS.md) | Single source of truth for active state, priorities, and handoff (Level 2) |
| Manga External Router | [`GITHUB_MANGA.txt`](../../GITHUB_MANGA.txt) | Domain entry router (Level 3) |
| Manga Domain State / Detail | [`docs/manga/STATUS.md`](STATUS.md) | Manga domain status and historical milestone ledger |
| Cross-Project UI Principles | [`docs/ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md`](../ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md) | Authoritative UI design & principles (governs current UI) |

### Manga Domain References & Historical Plans
| Role | Path | Status / Scope |
|---|---|---|
| Document register | [`docs/manga/DOCUMENT_REGISTER.md`](DOCUMENT_REGISTER.md) | Domain document index and classification |
| Domain Strategic Baseline | [`ASTRA_MANGA_AUTHORING_MASTER_PLAN.md`](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md) | Historical strategic plan; does not override docs/STATUS or docs/ui |
| Historical UX Blueprint | [`ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md`](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md) | Historical Minimum-Hand UX design; does not override docs/ui |
| Asset/workflow audit | [`ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md`](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md) | Inventory of existing node/workflow assets |
| Legacy Handoff | [`WEBGPT_SOL_LUNA_HANDOFF.md`](WEBGPT_SOL_LUNA_HANDOFF.md) | Historical 2026-09-11 handoff; not current new-chat entry |
| Legacy Operating Protocol | [`ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md`](plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md) | Historical execution protocol; governed by AGENTS.md |
| Card routing | [`docs/manga/cards/README.md`](cards/README.md) | Completed card index; current cards issued via Commander |

Historical implementation review target for M3A.1 is commit
`a7f0baaa89a2e315b0492573c9da19e50727928b`. Current operational state,
active cards, and decision sequences are governed exclusively by [docs/STATUS.md](../STATUS.md).
Do not auto-start or issue implementation cards from historical handoff documents;
the Commander / Architecture Lead issues bounded Cards based on [docs/STATUS.md](../STATUS.md).

## Execution cards and historical instructions

- [Card router and completed-card index](cards/README.md)
- [Historical instruction and plan archive](archive/README.md)

旧 `GPTからの指示書/` は役割が曖昧で、完了Cardと旧戦略が同じ階層に混在していたため廃止した。
完了Cardは `cards/completed/`、旧Phase指示と構想資料は `archive/` に分離している。
LUNA開始時は完了Cardを再利用せず、live stateを確認したCommander/SOLが新しい限定Cardを発行する。

## Reports and verification

- [Current and historical report index](reports/README.md)
- [Verification index](verification/README.md)
- [M3A.1 current report](reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md)
- [Docs/workflow namespace migration](reports/MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md)
- [Migration report](reports/MANGA_DOCUMENT_NAMESPACE_MIGRATION_REPORT.md)

Manga reports and verification evidence now live inside this namespace. Current
scripts and manifests use `docs/manga/verification/`; historical prose and pinned
commit URLs may retain the path that existed at the recorded revision.

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
