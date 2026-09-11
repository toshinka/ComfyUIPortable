# TEGAKI Cross-Track Integration Plan

Revision: `XT2-R2CLOSE`
Updated: `2026-09-11 JST`
Initial remote: `9a56815e984317363f4177277bb8035337c137f0`
Source H3 closeout: `70f3561d44a052ce30148fa6474ba633a0d8a37f`
Status: `CROSS-TRACK DESIGN PLAN / ASTRA REVIEW COMPLETE / R1 COMPLETE / R2 COMPLETE WITH KNOWN LIMITS / M1 IN PROGRESS / SHARED-SHELL IMPLEMENTATION NOT AUTHORIZED`

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
| Shared-shell design | `DIRECTION ACCEPTED / M1 GATE REMAINS` |
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
| Common supervisor | `PREFERRED` | The future architectural boundary is preferred for starting and monitoring isolated domain services; implementation is not authorized. |
| Exact backend lifecycle | `ACCEPTED` | R2 is `COMPLETED / PASS WITH KNOWN LIMITS`; the bounded lifecycle contract and authoritative signals are recorded in the R2 closeout. |
| Shared `8188` backend | `OPEN / REQUIRES FEASIBILITY` | **NOT SELECTED**. An unchanged shared H3/Manga backend is rejected for the current verified profiles; any future reconsideration needs separate evidence. |
| H3 Stage UX | `ACCEPTED` | H3 Preview/monitor visibility and Generate/status clarity are the first integration UX seam. H3-R1 is now implemented and verified in the H3 workspace. |
| Manga hosting | `OPEN / REQUIRES FEASIBILITY` | M1 is `IN PROGRESS / STANDALONE HOSTING DIRECTION PROVEN`; completion evidence and final hosting selection remain open. |
| Cross-track asset handoff | `DEFERRED` | No automatic H3-to-Manga or Manga-to-H3 asset promotion in the first slice. |
| Shared-shell implementation | `DEFERRED` | **NOT AUTHORIZED** until R1, R2, and M1 evidence and a later implementation Card. |

These classifications are intentionally not a selection of one universal backend.
R2 accepts domain-specific backend profiles under a future common supervisor
boundary, with known limits recorded separately. M1 remains in progress, and
shared-shell implementation remains unauthorized.

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
and the verified Native backend profile at `127.0.0.1:8188`; these are current
configurable defaults, not eternal port assignments.

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
Manga workspace remains independently valid when opened without H3. The current
Manga standalone hosting direction uses configurable defaults of backend
`127.0.0.1:8189` and workspace `127.0.0.1:8191`; it does not depend on H3's
Native profile or on a ComfyUI/LiteGraph shell mount.

## 6. Runtime architecture position

R2 evidence establishes domain-specific backend profiles as the accepted current
direction under a future common supervisor boundary. The current verified
profiles must not be collapsed into one unchanged backend:

- shared `8188` is **NOT SELECTED**; the unchanged shared H3/Manga profile is
  **REJECTED FOR CURRENT VERIFIED PROFILES**;
- domain-specific H3 and Manga backend profiles are **ACCEPTED**;
- a common supervisor is **PREFERRED** as a future architectural boundary;
- exact runtime lifecycle feasibility is **COMPLETED / PASS WITH KNOWN LIMITS**.

This is not a claim that a compatible shared backend can never exist. It records
that current verified profiles require separation and that any later shared
profile must earn separate feasibility evidence.

The IP2 acceptance finding is a concrete constraint: a plain/shared process on
`8188` caused a pre-submit HTTP 400 because its input root and model namespace
did not satisfy the H3 isolated contract. Restoring the existing H3 launcher
made the Browser path pass. This is not evidence of a Manga conflict or proof
that a shared runtime is impossible forever; it supports rejection of the
unchanged shared profile for the current verified domains.

### Bounded R2 lifecycle conclusion

The R2 evidence establishes the following bounded contract:

- readiness requires positive profile identity, not merely an open port;
- queue safety requires a valid `/queue` response and no active nonterminal job
  for the relevant domain;
- client `isGenerating` and a visible Generate control are not backend lifecycle
  truth;
- workspace lifetime and backend lifetime are separate concerns;
- stop/restart must preserve workspace state and must fail closed when ownership
  or queue safety cannot be established.

The future supervisor minimum responsibilities and the evidence limits are
recorded in `TEGAKI_R2_RUNTIME_LIFECYCLE_CLOSEOUT.md`.

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

H3-R1 has completed the bounded wide/narrow layout, independent Inspector
scrolling, sticky Stage, Generate visibility, truthful submission, and
Create-to-Result validation in the H3 workspace. Existing H3 simple panels
remain valid independently. Finalizing is `NOT ADOPTED`.

H3 internal Stage, Inspector, Shot, and Timeline evolution is H3-owned and is
not a common-shell responsibility.

## 8. Manga hosting question

Manga hosting is `IN PROGRESS / STANDALONE HOSTING DIRECTION PROVEN`. Current
M1 evidence establishes a standalone workspace boundary with configurable
defaults of workspace `127.0.0.1:8191` and backend `127.0.0.1:8189`, preserving:

- Manga custom-node/runtime requirements and independent profile identity;
- the Manga generation preparation endpoint;
- independent document schema and workflow selection;
- Manga queue and error ownership;
- `output/Tegaki` ownership;
- no dependency on a ComfyUI/LiteGraph shell mount;
- no regression of H3 isolated Native startup.

M1 is not complete. Remaining evidence includes production-grade lifecycle
ownership, shutdown/restart behavior, diagnostics, and final hosting selection.
No final production supervisor hosting option is selected in XT2. The accepted
current direction is domain-specific profiles under a future common supervisor.

The possible future categories are:

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

Classification: `COMPLETED / VERIFIED BROWSER UI`.

Exit evidence:

- H3 Preview/Stage remains observable in wide and narrow layouts;
- Generate is easy to locate;
- Queued, Generating, Completed, Failed, and truthful elapsed time are clear;
- no invented percentage is shown;
- H3 generation semantics remain in the H3 workspace;
- no Manga file or route changes are required.

R1 does not implement the common shell. See the H3-R1 report and evidence
package for the bounded implementation and Browser record.

### R2 — Runtime Lifecycle Feasibility

Classification: `COMPLETED / PASS WITH KNOWN LIMITS`.

Exit evidence:

- H3 Native and Skin profile identities are positively distinguished;
- H3 reconnect and stop/restart behavior preserve the workspace boundary;
- Manga domain-specific profile requirements are reproduced;
- a valid `/queue` plus no active nonterminal H3 Skin job is the H3 safe-stop signal;
- Manga uses the same backend truth with a supplemental transient submit guard;
- shared `8188` is rejected for the current verified profiles;
- startup, readiness, queue, restart, shutdown, ports, paths, logs, and failures
  are explicit within the bounded evidence.

Known limits are recorded in `TEGAKI_R2_RUNTIME_LIFECYCLE_CLOSEOUT.md`; R2 is
not a production supervisor implementation or a shared-backend approval.

### M1 — Manga Hosting Feasibility

Classification: `IN PROGRESS / STANDALONE HOSTING DIRECTION PROVEN`.

Exit evidence:

- standalone Manga workspace and backend profile are independently identified;
- Manga custom nodes and authoring paths remain available;
- Manga schema and queue ownership remain unchanged;
- Manga output remains in `output/Tegaki`;
- H3 Video, Still, Prep/Edit, Preview, and History remain independently valid;
- remaining failure, shutdown, restart, and final hosting ownership evidence is
  still required;
- no cross-track asset handoff is silently introduced.

M1 does not select a final hosting model by itself; it supplies evidence for the
later architecture decision. M1 remains `IN PROGRESS / STANDALONE HOSTING
DIRECTION PROVEN`.

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

XT2-R2CLOSE does not:

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
Thin common shell: ACCEPTED as a bounded future direction
Domain-specific workspaces: ACCEPTED
First-integration H3 / Manga IA: ACCEPTED as conceptual vocabulary
Common supervisor: ACCEPTED architectural direction / PREFERRED boundary; implementation not authorized
Exact backend lifecycle: COMPLETED / PASS WITH KNOWN LIMITS
Shared 8188: NOT SELECTED / REJECTED FOR CURRENT VERIFIED PROFILES
H3 Stage UX: ACCEPTED / R1 COMPLETED / VERIFIED BROWSER UI
Finalizing: NOT ADOPTED
Runtime Lifecycle Feasibility: COMPLETED / PASS WITH KNOWN LIMITS
Manga Hosting Feasibility: IN PROGRESS / STANDALONE HOSTING DIRECTION PROVEN
Cross-track asset handoff: DEFERRED
Implementation order: 1 R1 UX -> 2 R2 runtime -> 3 M1 Manga hosting -> 4 thin shell slice
Shared-shell implementation: NOT AUTHORIZED
H3: H3_READY_FOR_INTEGRATION_DESIGN
Manga: MANGA_READY_FOR_INTEGRATION_DESIGN
```

Astra cross-track architecture review is complete for the current design
boundary. R1 is complete, R2 Runtime Lifecycle Feasibility is complete with
known limits, M1 Manga Hosting is in progress with its standalone direction
proven, and shared-shell implementation remains `NOT AUTHORIZED`. M1 completion
is sufficient for the next first-integration gate; Owner acceptance remains
`PENDING`.

STOP.
