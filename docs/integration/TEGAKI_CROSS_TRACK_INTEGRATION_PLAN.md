# TEGAKI Cross-Track Integration Plan

Revision: `XT2-R1`
Updated: `2026-09-11 JST`
Initial remote: `9a56815e984317363f4177277bb8035337c137f0`
Source H3 closeout: `70f3561d44a052ce30148fa6474ba633a0d8a37f`
Status: `CROSS-TRACK DESIGN PLAN / IMPLEMENTATION NOT AUTHORIZED`

## 1. Purpose

This plan defines the first bounded architecture review between the TEGAKI H3
and Manga tracks. It records decisions and feasibility questions only. It does
not implement a shared shell, merge runtime profiles, merge schemas, or start
a new product feature Card.

The plan preserves the current product boundaries:

| Track | Current state |
|---|---|
| H3 | `H3_READY_FOR_INTEGRATION_DESIGN` |
| Manga | `MANGA_READY_FOR_INTEGRATION_DESIGN` |
| Current cross-track implementation conflict | `NONE CURRENTLY VERIFIED` |
| Shared-shell design | `READY TO REVIEW` |
| Shared-shell implementation | `NOT AUTHORIZED` |

## 2. Classification vocabulary

| Classification | Meaning in this plan |
|---|---|
| `ACCEPTED` | Current design direction accepted as a bounded review premise; not implementation approval. |
| `PREFERRED` | Candidate direction preferred for feasibility investigation; not final architecture approval. |
| `OPEN / REQUIRES FEASIBILITY` | No selection is made until bounded runtime or product evidence exists. |
| `DEFERRED` | Deliberately excluded from the first integration design slice. |

## 3. Architecture decisions

| Architecture item | Classification | Decision / boundary |
|---|---|---|
| Thin common shell | `ACCEPTED` | Own only cross-track navigation, shared layout language, theme, and bounded launcher/status surfaces. |
| Domain-specific workspaces | `ACCEPTED` | H3 and Manga retain separate canvases, state, routes, schemas, workflows, tests, and output ownership. |
| First-integration H3 / Manga IA | `ACCEPTED` | Coordination IA is `TEGAKI -> H3` and `TEGAKI -> Manga`; it is not final IA or an implementation task. |
| Visual and interaction consistency | `ACCEPTED` | Visual language and interaction conventions may be shared while internal domain ownership remains separate. |
| Common supervisor | `PREFERRED` | Investigate one common launcher or supervisor that starts and monitors isolated domain services. |
| Exact backend lifecycle | `OPEN / REQUIRES FEASIBILITY` | Process count, startup order, health, restart, shutdown, queues, logs, ports, paths, and failure ownership are not selected. |
| Shared `8188` backend | `OPEN / REQUIRES FEASIBILITY` | **NOT SELECTED**. Compatibility is not assumed and must be proven before consideration. |
| H3 Stage UX | `ACCEPTED` | H3 Preview/monitor visibility and Generate/status clarity are the first integration UX seam. |
| Manga hosting | `OPEN / REQUIRES FEASIBILITY` | Determine how the Manga workspace and custom-node/runtime path are hosted beside H3. |
| Cross-track asset handoff | `DEFERRED` | No automatic H3-to-Manga or Manga-to-H3 asset promotion in the first slice. |
| Shared-shell implementation | `DEFERRED` | **NOT AUTHORIZED** until R1, R2, and M1 evidence and a later implementation Card. |

These classifications are intentionally not a selection of one universal backend.
The preferred supervisor direction is a review candidate, while exact lifecycle
and hosting remain open.

## 4. First-integration product shape

The thin common shell is a coordination layer:

```text
TEGAKI shell
  -> H3 workspace
  -> Manga workspace
```

The shell may eventually provide:

- top-level navigation between H3 and Manga;
- shared application frame, theme, and tab/header language;
- workspace open/close and bounded runtime status presentation;
- launcher entry points that do not absorb domain generation semantics.

The shell must not become a universal generation editor. H3 and Manga workspaces
remain the owners of their own controls, semantic adapters, queues, History,
Preview, schemas, workflows, and error contracts.

### First-integration IA

```text
TEGAKI
├─ H3
│  ├─ Video
│  ├─ Still
│  └─ Prep/Edit
└─ Manga
```

This IA is `ACCEPTED` only as cross-track coordination vocabulary. It is not
approved final IA, and it does not authorize an H3 parent tab or a shell edit.

## 5. Workspace ownership

### H3 workspace

H3 owns the current Browser-facing Video, Still, and Prep/Edit lenses, including
its Preview, History, semantic adapters, Native materialization, and output
namespace under `output/h3/`. H3 currently uses the skin at `127.0.0.1:8190`
and the verified Native backend profile at `127.0.0.1:8188`.

H3 currently launches Native through `h3/tools/run_native_isolated.py` with
`--disable-all-custom-nodes`, H3 model paths, H3 input/output directories,
H3 user/temp directories, and an in-memory database.

### Manga workspace

Manga owns its authoring workspace, `TEGAKI_AUTHORING_DOCUMENT 1.0.0`,
Manga-specific routes, workflows, custom-node/runtime path, tests, and
`output/Tegaki` namespace. Manga owns:

```text
POST /tegaki/manga/generation/prepare
```

The shell does not absorb this endpoint or make Manga route decisions. The
Manga workspace remains independently valid when opened without H3.

## 6. Runtime architecture position

The current evidence establishes a shared Portable installation, not a proven
shared backend profile. H3 disables all custom nodes in its verified launcher,
while Manga requires its Manga-capable custom-node/runtime path.

Therefore:

- shared `8188` is **NOT SELECTED**;
- a shared backend is **OPEN / REQUIRES FEASIBILITY**;
- a common supervisor is the **PREFERRED** investigation direction;
- the exact backend lifecycle is **OPEN**.

The IP2 acceptance finding is a concrete constraint: a plain/shared process on
`8188` caused a pre-submit HTTP 400 because its input root and model namespace
did not satisfy the H3 isolated contract. Restoring the existing H3 launcher
made the Browser path pass. This is not evidence of a Manga conflict or proof
that shared runtime is impossible.

### Exact lifecycle questions

The R2 feasibility work must resolve, with evidence:

- which process or supervisor owns startup and shutdown;
- whether H3 and Manga use one process or isolated processes;
- port allocation and collision behavior;
- custom-node enablement and model-path namespaces per domain;
- health checks, readiness, queue ownership, and failure reporting;
- restart, cleanup, and stale-process behavior;
- resource contention and user-visible status;
- logs, diagnostics, and safe recovery boundaries.

## 7. H3 Stage UX decision

H3 Stage UX is `ACCEPTED` as the first cross-track UX seam. This accepts a
product direction, not an implementation in XT2.

The Stage direction covers:

- Preview or Stage remains easy to observe while inspecting settings;
- generated result and running state remain visible after Generate;
- Generate remains easy to locate;
- truthful states remain `Queued`, `Generating`, `Completed`, and `Failed`;
- elapsed time is shown only where available;
- inaccurate percentage completion is not invented.

Wide and narrow layout behavior, independent Inspector scrolling, sticky Stage
behavior, or Create-to-Result transitions remain bounded design/feasibility work
under R1. Existing H3 simple panels remain valid independently.

## 8. Manga hosting question

Manga hosting is `OPEN / REQUIRES FEASIBILITY`. The review must test how the
Manga workspace can be hosted beside H3 while preserving:

- Manga custom-node/runtime requirements;
- the Manga generation preparation endpoint;
- independent document schema and workflow selection;
- Manga queue and error ownership;
- `output/Tegaki` ownership;
- no regression of H3 isolated Native startup.

No hosting option is selected in XT2. The possible categories are:

1. one compatible shared backend profile;
2. separate H3 and Manga backend processes;
3. a common supervisor over isolated domain services;
4. another bounded architecture discovered by feasibility work.

## 9. Domain boundaries that remain separate

The first integration design must not implicitly merge:

- H3 and Manga schemas;
- H3 and Manga workflows or prompt semantics;
- `/tegaki/manga/...` with H3 semantic routes;
- H3 History/Preview with Manga History/document state;
- generation queue monkeypatches or hidden global state;
- H3 `output/h3` with Manga `output/Tegaki`.

The preferred interaction principle is:

```text
VISUAL / INTERACTION CONSISTENCY MAY BE SHARED
INTERNAL DOMAIN OWNERSHIP MAY REMAIN SEPARATE
```

## 10. Cross-track asset handoff

Cross-track asset handoff is `DEFERRED`. The existing same-session H3 handoff
between H3 lenses remains H3-owned and does not establish H3-to-Manga or
Manga-to-H3 promotion.

Any future handoff Card must specify typed ownership, provenance, source and
destination lifecycle, copy versus move behavior, failure rollback, privacy, and
History semantics. No automatic handoff is part of the first vertical slice.

## 11. Implementation order

The order below is a review sequence, not authorization to implement all steps:

1. **H3 Stage / Generate Visibility**
2. **Runtime Lifecycle Feasibility**
3. **Manga Hosting Feasibility**
4. **Thin Shell First Vertical Slice**

Step 4 may begin only after the relevant gates pass and a separate bounded
implementation Card authorizes it. The shell must remain thin and must not
absorb H3 or Manga domain semantics.

## 12. Gates

### R1 — H3 Stage / Generate Visibility

Classification: `ACCEPTED DESIGN TARGET / REQUIRES BOUNDED UX VALIDATION`.

Exit evidence:

- H3 Preview/Stage remains observable in wide and narrow layouts;
- Generate is easy to locate;
- Queued, Generating, Completed, Failed, and truthful elapsed time are clear;
- no invented percentage is shown;
- H3 generation semantics remain in the H3 workspace;
- no Manga file or route changes are required.

R1 does not implement the common shell.

### R2 — Runtime Lifecycle Feasibility

Classification: `OPEN / REQUIRES FEASIBILITY`.

Exit evidence:

- H3 isolated launcher profile is reproduced;
- Manga runtime profile is reproduced;
- candidate shared-supervisor lifecycle is documented;
- shared `8188` compatibility is tested rather than assumed;
- startup, health, queue, restart, shutdown, ports, paths, logs, and failures are explicit;
- no domain schema or workflow merge is needed.

R2 must not be reported as a shared-backend PASS unless the exact profile is
verified. A failed candidate does not authorize a fallback merge.

### M1 — Manga Hosting Feasibility

Classification: `OPEN / REQUIRES FEASIBILITY`.

Exit evidence:

- Manga workspace loads through its authoritative route;
- Manga custom nodes and workflows remain available;
- Manga schema and queue ownership remain unchanged;
- Manga output remains in `output/Tegaki`;
- H3 Video, Still, Prep/Edit, Preview, and History remain independently valid;
- failure and shutdown behavior are visible to the chosen supervisor or shell;
- no cross-track asset handoff is silently introduced.

M1 does not select a final hosting model by itself; it supplies evidence for the
later architecture decision.

## 13. Thin Shell First Vertical Slice

The fourth implementation-order item is deliberately gated. If R1, R2, and M1
pass and a later Card authorizes implementation, the first slice should provide
only:

- top-level H3/Manga navigation;
- independent workspace mount points;
- shared visual frame and bounded runtime status presentation;
- explicit launcher/supervisor integration;
- no merged schemas, workflows, routes, History, Preview, or asset ownership.

The first slice must be reversible and must preserve direct independent access
to both domain workspaces.

## 14. Non-scope and safety

XT2-R1 does not:

- modify H3 runtime code, server, UI, adapters, workflows, ports, or model config;
- modify Manga implementation, routes, schemas, workflows, custom nodes, scripts, or outputs;
- create a shared shell or parent tab;
- select a shared `8188` backend;
- implement a supervisor;
- implement Stage UX;
- implement Manga hosting;
- implement cross-track asset handoff;
- start LoRA, semantic R2V, Studio, Astra, or another product feature Card;
- issue Rev.5 or rewrite Rev.4.

## 15. Plan result

```text
Thin common shell: ACCEPTED
Domain-specific workspaces: ACCEPTED
First-integration H3 / Manga IA: ACCEPTED as conceptual vocabulary
Common supervisor: PREFERRED
Exact backend lifecycle: OPEN / REQUIRES FEASIBILITY
Shared 8188: NOT SELECTED
H3 Stage UX: ACCEPTED design target
Manga hosting: OPEN / REQUIRES FEASIBILITY
Cross-track asset handoff: DEFERRED
Implementation order: 1 R1 UX -> 2 R2 runtime -> 3 M1 Manga hosting -> 4 thin shell slice
Shared-shell implementation: NOT AUTHORIZED
H3: H3_READY_FOR_INTEGRATION_DESIGN
Manga: MANGA_READY_FOR_INTEGRATION_DESIGN
```

This plan is ready for the later cross-track design review. It is not approval
to implement the shared shell. Owner acceptance remains `PENDING`.

STOP.
