# H3 Product Integration Boundary

Updated: `2026-09-11 JST`
Source: `H3-XT1 / Integration Design Readiness Freeze`
IP2 closeout: `70f3561d44a052ce30148fa6474ba633a0d8a37f`
Classification: `H3_READY_FOR_INTEGRATION_DESIGN`
Shared-shell design: `READY TO REVIEW`
Shared-shell implementation: `NOT AUTHORIZED`
Owner acceptance: `PENDING`

## 1. Purpose and readiness

This is the current H3 product and integration boundary for a later
cross-track architecture review. It is a boundary snapshot, not a roadmap or
an implementation instruction.

H3 has enough stable browser-facing product boundary to participate in
integration design. This does not mean H3 development is finished, production
is closed, runtime profiles are unified, shared-shell implementation is
approved, or Owner acceptance is complete.

| Current item | State |
|---|---|
| Current Stage | `IP2 / Experimental Browser Prep/Edit Lens` |
| Classification | `PASS WITH KNOWN NATIVE LIMIT` |
| Browser result | `VERIFIED BROWSER UI GENERATION` |
| IP2 publication | `PUBLISHED ON MAIN` at `70f3561d44a052ce30148fa6474ba633a0d8a37f` |
| Source-only Prep | `VERIFIED BROWSER UI GENERATION` |
| Source + Donor Prep | `EXPERIMENTAL / VERIFIED BROWSER UI GENERATION` |
| Donor attribute isolation | `NOT GUARANTEED` |
| Edit in Prep / Prep to Character | `VERIFIED BROWSER UI` |
| Real Prep generations | `2` |
| Chrome `file://` permission | `NOT ENABLED` |
| Owner acceptance | `PENDING` |

IP2 evidence must retain both observations: Source-only preserved the source
strongly and observed the rainy environment change with moderate drift. Source
plus Donor preserved the source strongly, but donor influence was not convincing,
over-transfer was low, and composition drift was low. This does not mean that
the Donor is useless or reliably isolated.

## 2. H3 product entry and ownership

```text
User
  -> TEGAKI H3 Skin
  -> H3 semantic adapters
  -> materialized Native H3 workflow
  -> ComfyUI Native backend
```

| Surface | Current address | Responsibility |
|---|---|---|
| H3 Browser skin | `127.0.0.1:8190` | H3 UI, semantic state, Preview, History |
| H3 Native backend | `127.0.0.1:8188` | Native execution, queue, output authority |

H3 owns these areas and their generation semantics:

```text
ComfyUIPortable/h3/
ComfyUIPortable/docs/h3/
ComfyUIPortable/workflows/h3/
ComfyUIPortable/output/h3/
```

`output/h3/` is the H3 runtime input/output namespace. Generated media and
temporary assets remain runtime artifacts unless a separate bounded evidence
package states otherwise. No Manga-owned file, route, schema, workflow, custom
node, script, or output namespace is shared by this document.

## 3. Current H3 UI contract

```text
Video: Standard; Reference · Experimental
Still
Prep/Edit
Preview
History
same-session generated-media handoff
```

Preview and History remain H3-owned. Completed H3 media may move between the
named H3 lenses through the existing bounded handoff contracts. This does not
merge H3 state with Manga document state or authorize cross-track promotion.

The current H3 contract does not claim Studio, Shot, Timeline, Storyboard,
multi-character semantic reference, LoRA, Qwen Image Edit, Image Studio, or a
shared H3/Manga shell.

## 4. Current H3 runtime profile

`h3/run_h3.bat` launches the H3 Native backend through
`h3/tools/run_native_isolated.py` with the following verified profile:

- `--disable-all-custom-nodes`;
- H3 extra-model-paths configuration;
- H3 input and output directories under `output/h3`;
- H3 user directory `output/h3/h3_native_user`;
- H3 temp directory `output/h3/h3_native_temp`;
- in-memory SQLite database;
- H3 skin connection to Native on `127.0.0.1:8188`.

This is the current H3 execution profile. It is not evidence that Manga can
use it unchanged, and it is not evidence that a future shared backend is
impossible.

## 5. IP2 runtime finding and open hosting question

During Browser acceptance, an already-running plain/shared ComfyUI process on
`8188` caused a pre-submit HTTP 400 because its input root and model namespace
did not satisfy the H3 isolated runtime contract. No generation was submitted
and no output was created by that failed attempt. Restoring the existing H3
isolated launcher profile made the two authorized Browser generations pass.

This is an **INTEGRATION DESIGN CONSTRAINT / OPEN RUNTIME-PROFILE QUESTION**.
It is not a Manga conflict and not proof that shared runtime is impossible.

A future shell must not assume that H3 and Manga profiles can be collapsed into
one unchanged `8188` process. Manga currently requires its Manga custom-node and
runtime path, while H3 disables all custom nodes in its verified launcher.

Open architecture question:

> How should one future TEGAKI shell host both domain runtime profiles?

Future review categories may include:

1. one compatible shared ComfyUI backend profile;
2. separate domain backend processes on separate ports;
3. a common launcher supervising isolated domain services;
4. another bounded architecture discovered during review.

XT1 selects none of these options.

## 6. Route, schema, workflow, and History boundaries

Manga owns the following endpoint:

```text
POST /tegaki/manga/generation/prepare
```

H3 does not take ownership of it. H3 exposes its Browser semantic API through
its own local H3 skin server. This Card renames no route.

H3 and Manga schemas remain independent. H3 state is not merged into
`TEGAKI_AUTHORING_DOCUMENT 1.0.0`; workflows are not merged and no universal
generation workflow or cross-domain queue monkeypatch is created.

Current H3 History and Preview remain H3-owned. They are not merged with Manga
History or document state. The preferred future principle is:

```text
VISUAL / INTERACTION CONSISTENCY MAY BE SHARED
INTERNAL DOMAIN OWNERSHIP MAY REMAIN SEPARATE
```

This is a design principle only; it does not implement shared state, shared
persistence, or a shared shell.

## 7. Provisional IA and open UX questions

Coordination vocabulary only:

```text
TEGAKI
├─ H3
│  ├─ Video
│  ├─ Still
│  └─ Prep/Edit
└─ Manga
```

Status: `CONCEPTUAL ONLY / NOT APPROVED FINAL IA`. No H3 parent tab is
implemented or authorized by XT1.

### Preview as Stage

Open design question observed by the Owner:

- Wide: Preview looks appropriate near the top, but Inspector/settings scrolling can move it out of sight.
- Narrow: input/settings and Preview become far apart, so the user may need to scroll back after Generate.

Potential future direction is a persistent Stage/Monitor on wide layouts, or
state-oriented Create and Result/Preview views on narrow layouts. XT1 does not
implement sticky behavior, a new Stage, responsive view routing, or layout changes.

### Generate and status

Generate should remain easy to locate and visibly communicate `Queued`,
`Generating`, `Completed`, and `Failed`, with elapsed time only where truthful.
No percentage should be invented without accurate backend support. XT1 does not
implement a progress bar or alter status semantics.

## 8. Future Studio vocabulary and research context

Future H3 Studio or Shot work may evolve Preview into a persistent `Stage /
Monitor`, with later Shot, Take, Continue, Regenerate From, and Timeline/Shot
strip concepts. These are future vocabulary only; Studio is not a prerequisite
for current shell review and current H3 simple panels remain independently valid.

Future H3 research already tracks semantic reference roles, review/regenerate
production loops, and low-VRAM alternative runtimes. XT1 performs no broad web
research, adopts no external implementation, and derives no implementation from
these concepts.

## 9. Current cross-track state

| Area | State |
|---|---|
| Manga | `MANGA_READY_FOR_INTEGRATION_DESIGN` |
| H3 | `H3_READY_FOR_INTEGRATION_DESIGN` |
| Cross-track implementation conflict | `NONE CURRENTLY VERIFIED` |
| Primary open architecture constraint | `RUNTIME PROFILE / BACKEND HOSTING` |
| Shared-shell design | `READY TO REVIEW` |
| Shared-shell implementation | `NOT AUTHORIZED` |
| Owner acceptance | `PENDING` |

The Manga state is coordination context only. The Manga boundary document was
read for terminology alignment and was not modified by XT1.

## 10. Explicit non-scope

XT1 does not:

- modify H3 server, app, adapters, workflows, ports, launch behavior, or model config;
- modify `GITHUB_MANGA.txt` or any `docs/manga/` file;
- modify Manga workflows, custom nodes, scripts, or outputs;
- merge H3 and Manga schemas, routes, workflows, queues, History, or Preview;
- enable Chrome `file://` access;
- start IP3, LoRA inventory, semantic R2V, Studio implementation, or Astra automatically;
- issue Rev.5 or rewrite Rev.4.

## 11. References and validation

- [GITHUB_H3.txt](../../GITHUB_H3.txt)
- [H3 document hub](README.md)
- [IP2 Browser Prep/Edit report](reports/IP2_BROWSER_PREP_EDIT_LENS_REPORT.md)
- [IP2 Browser evidence](evidence/ip2-browser-prep-edit/2026-09-11/README.md)
- [Manga Product Integration Boundary](../manga/MANGA_PRODUCT_INTEGRATION_BOUNDARY.md) — read-only terminology reference

XT1 validation is docs-only:

```text
GITHUB_H3 current stage: IP2
IP2 publication and read-order entries: present
H3 boundary link: present
Manga boundary: unchanged
Runtime files: unchanged
Manga files: unchanged
No Browser or generation: YES
git diff --check: PASS
```

## 12. Freeze result

```text
H3 integration-design readiness: H3_READY_FOR_INTEGRATION_DESIGN
Manga: MANGA_READY_FOR_INTEGRATION_DESIGN
Current cross-track implementation conflict: NONE
Primary integration-design question: BACKEND / RUNTIME PROFILE HOSTING
Preview/Stage responsive UX: OPEN DESIGN QUESTION
Generate/status UX: OPEN DESIGN QUESTION
Shared-shell design: READY FOR REVIEW
Shared-shell implementation: NOT AUTHORIZED
Runtime changes: NONE
Manga changes: NONE
Owner acceptance: PENDING
Recommended next: ASTRA CROSS-TRACK INTEGRATION DESIGN REVIEW
```

Before that review, Web-GPT or SOL should freshly verify current Astra usage
and reasoning-effort guidance. Do not begin shared-shell implementation from
this snapshot alone.

STOP.
