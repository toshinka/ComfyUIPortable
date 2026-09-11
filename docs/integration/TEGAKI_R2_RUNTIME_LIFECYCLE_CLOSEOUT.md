# TEGAKI R2 Runtime Lifecycle Closeout

Status: `R2 COMPLETED / PASS WITH KNOWN LIMITS`
Scope: Cross-track architecture evidence only. No supervisor, shared shell,
product runtime, Manga production, or generation implementation is authorized
by this closeout.

## 1. Result

R2 closes the bounded runtime lifecycle feasibility gate. The accepted current
direction is domain-specific backend profiles under a future common supervisor
boundary:

| Domain | Current verified profile | Workspace/service boundary |
|---|---|---|
| H3 Native | `127.0.0.1:8188` | H3 isolated Native profile; custom nodes disabled |
| H3 Skin | `127.0.0.1:8190` | H3 Browser-facing skin, separate from Native lifetime |
| Manga backend | `127.0.0.1:8189` | Manga-capable custom-node/runtime profile |
| Manga workspace | `127.0.0.1:8191` | Standalone authoring workspace |

These are configurable current defaults, not eternal port assignments. An
unchanged shared H3/Manga backend on `8188` is **REJECTED FOR CURRENT VERIFIED
PROFILES** and is **NOT SELECTED**. A common supervisor is **PREFERRED** as a
future architecture boundary, but its implementation is **NOT AUTHORIZED**.
Workspace lifetime is distinct from backend lifetime.

## 2. Evidence matrix

| Concern | H3 evidence | Manga evidence | Bounded conclusion |
|---|---|---|---|
| Profile identity | Native and Skin are positively distinguishable; H3 Native requires its canonical argv, namespaces, database, and queue evidence. | Manga requires its Manga-capable custom-node/runtime profile and independent workspace identity. | Profile identity is required before Ready or submit. |
| Readiness and idle | Canonical H3 profile plus valid `/queue` and no active nonterminal H3 Skin job. | Valid Manga `/queue`; a future transient submit guard is supplemental, not the primary backend truth. | An open port, client `isGenerating`, or a visible Generate button is insufficient. |
| Lifetime | H3 Skin survives Native stop/restart as a separate workspace boundary and reconnects when the valid profile returns. | Standalone workspace and backend boundaries are independently addressable. | Workspace lifetime != backend lifetime. |
| Profile separation | H3 Native uses `--disable-all-custom-nodes`, H3 model paths, H3 input/output, H3 user/temp paths, and an in-memory database. | Manga requires its Manga-capable custom-node/runtime path. | Current verified profiles must not be collapsed into one unchanged backend. |
| Hosting direction | H3 Native `8188` and Skin `8190` remain separate current defaults. | Manga backend `8189` and workspace `8191` establish standalone hosting direction without a ComfyUI/LiteGraph shell mount. | M1 is in progress; standalone direction is proven, not final hosting completion. |

The H3 reconnect and profile evidence is retained in the H3 R2A1 and R2B
reports. The Manga evidence remains subject to its own authoring, runtime, and
hosting boundaries; this document does not merge those records.

Additional bounded evidence recorded for R2 includes approximately 21 seconds
for the canonical H3 Native startup/restart path in R2A, separate workspace
selection and backend activation, R2A1 correction of stale disconnected-detail
presentation, and no proven compatibility for one shared backend. Manga R2C,
M1A, M1A1, and M1B establish positive Manga capability/node/route checks,
generation preparation without generation, fail-closed queue checks, a
loopback/path-bounded proxy, durable Scene/CAST/Character edit/write parity,
`TEGAKI_AUTHORING_DOCUMENT 1.0.0` authority, no H3 coupling, legacy M3B
retained as reference/production, and Frame/Guide parity deferred. The
standalone workspace exists under `ComfyUIPortable/manga/`; the legacy
Minimum-Hand editor remains ComfyUI-hosted. Production lifecycle/supervisor
integration and the final legacy retirement decision remain open, so M1 is not
complete.

### Profile identity principle

```text
some ComfyUI responds
!=
correct domain backend is ready
```

H3 now has positive canonical profile verification before `READY` or
`/prompt`. Manga has positive capability, node, and route checks before its
profile is considered ready. A future supervisor must identify the requested
domain profile before reporting backend readiness.

## 3. Future common supervisor minimum contract

The following responsibilities are the minimum future boundary, not an
implementation authorization:

- domain selection;
- process startup;
- positive profile identity;
- health and readiness;
- queue-safe shutdown guard;
- stop and restart;
- port collision ownership;
- logs and process ownership;
- truthful failure reporting;
- no workspace-state destruction on backend stop.

Safe stop requires authoritative backend evidence. For H3, the bounded rule is
a valid `/queue` response with no active nonterminal H3 Skin job. For Manga, the same
backend truth applies, with any transient submit guard treated as supplemental.

## 4. Known limits

The R2 result is deliberately limited:

A. No loaded-model VRAM release timing was measured because no model was loaded
   for this lifecycle gate.
B. H3 active-job recovery across backend restart was not live-tested with a real
   active generation.
C. No common supervisor was implemented or tested as a product component.
D. Full automatic process ownership, leases, or cross-process locks were not
   selected or implemented.
E. Manga production-grade supervisor shutdown and final hosting ownership remain
   open under M1.

These limits do not reopen the current profile decision. They define the
evidence required by later implementation or hosting Cards.

## 5. Gate transition

```text
R1: COMPLETE / VERIFIED BROWSER UI
R2: COMPLETE / PASS WITH KNOWN LIMITS
M1: IN PROGRESS / STANDALONE HOSTING DIRECTION PROVEN
Thin common shell: NOT AUTHORIZED
```

M1 completion with standalone hosting and lifecycle ownership evidence is the
next cross-track gate sufficient for a first integration decision. It does not
authorize the thin shell by itself; a separate bounded implementation Card is
still required. Cross-track asset handoff remains `DEFERRED`, and Owner
acceptance remains `PENDING`.
