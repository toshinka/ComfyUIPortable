# ComfyUIPortable — agent entry map

Read this first. The operational truth and active handoff are in [docs/STATUS.md](docs/STATUS.md).

## 1. Reading Order & Entry Modes

Do not recursively read all historical documents.

### Domain-Local Entry
For domain-specific tasks, load only that domain's entry:
1. [docs/STATUS.md](docs/STATUS.md) — Current repository location, active milestones, and handoff state.
2. [GITHUB_ComfyUI.txt](GITHUB_ComfyUI.txt) — High-level compatibility router.
3. Relevant domain router:
   - [GITHUB_MANGA.txt](GITHUB_MANGA.txt) for Manga Authoring (Manga Card only)
   - [GITHUB_H3.txt](GITHUB_H3.txt) for MiniMax H3 Video / Still (H3 Card only)
   Do not load the other domain merely because both share the repository.
4. Relevant domain STATUS / handoff (e.g. [docs/manga/STATUS.md](docs/manga/STATUS.md) or [docs/h3/README.md](docs/h3/README.md)) only if domain detail is required.
5. Current explicit Card provided by the architecture lead.
6. Only then inspect specific source code, tests, or runtime contracts requested by the Card.

### Cross-Domain Entry
For an explicitly cross-domain task such as:
- shared TEGAKI shell
- Manga/H3 sibling UI
- cross-domain integration
- global project architecture

The route is:
1. `AGENTS.md`
2. `docs/STATUS.md`
3. Relevant `docs/ui/` material explicitly required by the Card
4. Both `GITHUB_MANGA.txt` and `GITHUB_H3.txt` as bounded subsystem references
5. Only additional documents named or required by the Card.

*Constraint*: Do not recursively descend into both domain histories.

## 2. Document Authority Model

- **Level 1 — Stable Operating Contract**: `AGENTS.md` (this file: operating rules, reading order, agent modes).
- **Level 2 — Cross-Project State**: `docs/STATUS.md` (single source of truth for current cross-project operational facts).
- **Level 3 — Domain Routers & History**: `GITHUB_ComfyUI.txt`, `GITHUB_MANGA.txt`, `GITHUB_H3.txt`, `docs/manga/**`, `docs/h3/**`.
- **Level 4 — Current Explicit Card**: The bounded prompt issued by the commander/lead (may narrow scope, never expand beyond policy).
- **Level 5 — Source, Tests, & Runtime Evidence**: Code, unit tests, browser tests, GPU execution outputs.

*Precedence Rules*:
- A current explicit Card may narrow `AGENTS.md` rules for a specific task.
- Historical documents may **not** override `AGENTS.md`, `docs/STATUS.md`, or the current explicit Card.
- Nothing in `AGENTS.md` overrides system, developer, or safety policies.

## 3. Card Authority & Scope Control

- The architecture lead / commander issues bounded Cards.
- The Card defines: `MODE`, objective, file boundaries, forbidden actions, verification steps, and stop conditions.
- Background commentary, possible future directions, examples, and nearby findings are **not** authorization to implement.
- Worker PASS is not automatically product acceptance; final acceptance remains with the commander / Owner.
- **Scope Creep Rule**: Never perform unrequested refactoring, cleanup, or dependency upgrades.
- Report adjacent findings briefly; do not fix them automatically.
- A correction applies only to the specifically corrected subject.
- **Single Recommendation**: Recommend at most one logical next step. Never begin the next Card automatically.
- If additional scope is truly essential to complete the current Card: state WHY and STOP.

## 4. Mode-Aware Behavior

Identify the Card's explicit `MODE:`. Never guess mode from task difficulty.

### ASTRA MODE (Architecture & Review)
- Focus: Architectural judgment, adversarial review, bounded audit, design critique, direction verification.
- Behavior: Analyze; do not modify product code unless the Card explicitly authorizes it.
- Read-only does **not** mean repository-wide unlimited exploration; stay inside the Card search/file boundary.
- Finding adjacent problems does not authorize investigating them; record out-of-scope findings briefly.
- Do not turn an audit into a refactor or cleanup pass.
- Distinguish strictly between `PROVEN`, `PLAUSIBLE`, and `UNKNOWN`.
- Challenge structural assumptions and contracts, not merely formatting.
- Recommend at most one next action and STOP. ASTRA must not create extra work merely because context remains.

### ASTRA Resource Discipline
- Delegation/subagents are forbidden unless the current Card explicitly authorizes them.
- Do not recursively follow document references or expand the file set beyond the Card boundary.
- Explicit Card budgets such as MAX FILE READS, MAX TOOL CALLS, MAX ADDITIONAL FILES,
  REVIEW PASSES, and TEST PASSES are hard limits.
- Do not poll long-running processes or repeatedly re-check unchanged status.
- After a requested verification passes, do not repeat or broaden verification unless new
  failure evidence, a new code change, or an explicit unresolved concern requires it.
- Do not re-read large context merely to reconfirm completed decisions.
- If the task cannot be completed within the stated resource/scope budget, report the blocker
  and return to the Commander. Do not expand scope autonomously.

### LUNA MODE (Implementation & Runtime)
- Focus: Bounded implementation, Windows/process interaction, ComfyUI graphs, runtime validation, GPU execution, narrow hotfixes.
- Behavior: Execute the explicit Card without redesigning existing architecture.
- Prefer existing architecture and existing authority paths over novelty.
- Do not broaden implementation after discovering a possible improvement.
- Inspect exact live runtime/node contracts (`/object_info`) before submitting graphs.
- Obey generation and submission caps literally.
- Obtain real runtime evidence (PIDs, port state, `/prompt` history, GPU memory). Self-written unit tests alone do not equal runtime proof.
- Do not update dependencies or models unless the Card explicitly authorizes exact changes.
- STOP on Card stop condition; STOP after requested evidence is obtained.

### GEMINI / OTHER / NO MODE
- Follow the Card literally for documentation, inventories, UI/UX, unit tests, or read-only preparation.
- Do not infer LUNA or ASTRA authority.
- When `MODE` is absent, act as a conservative bounded worker without assuming ASTRA or LUNA privileges.

## 5. Domain & Semantic Boundaries

H3 and Manga share the physical Portable installation, supervisor tools, and OS environment, but have separate schemas, workflows, runtimes, outputs, and planning tracks.
- H3 work must not modify Manga behavior merely because code is nearby.
- Manga work must not modify H3 behavior merely because runtime is shared.
- Cross-domain changes require an explicit integration Card.

### Semantic Roles
- **Manga Scene / Region**: Where prompt text conditioning applies spatially.
- **Manga CAST / Reference**: Who / what character appearance is visually referenced.
- **Manga Guide / ControlNet**: Pose, layout, and structural geometry.
- **Manga LoRA**: Learned artistic or character modifier.
- **Manga character_instance**: Concrete spatial placement of a CAST member inside a Scene.
- **H3**: Separate video and still generation pipeline. Do not silently merge H3 reference semantics into Manga CAST.

## 6. Runtime & Port Ownership

- Standard ports: `8188` (H3 Native), `8189` (Manga Backend), `8190` (H3 Shell), `8191` (Manga Workspace).
- Launch entry: `h3\run_h3.bat`.
- Identify existing listeners before starting services. Never blindly kill unknown processes or run indiscriminate `taskkill`.
- Processes started by a Card must be cleanly stopped at Card end (default: normal Enter shutdown).
- Retain running processes (`KEEP_RUNNING`) only if explicitly authorized by the Card.
- Task switches must retire prior Card-owned runtimes when ownership is known.
- Final runtime reports must account for Card-owned listeners.
- Normal owner shutdown is always preferred. H3 and Manga may share supervisor infrastructure without merging generation semantics.

## 7. Evidence Discipline

- Never report a file read when not read, a test PASS when not run, a generation PASS when not executed, or model compatibility when only inferred.
- Classify claims: `PROVEN` (direct verifiable evidence), `PLAUSIBLE` (structurally sound but unverified), `UNKNOWN` (untested).
- Do not interpret empty output, timeouts, permission failures, missing files, or caught exceptions as PASS or "nothing found" without concrete evidence.
- Distinguish between verification tiers: Unit/fixture PASS ≠ Browser acceptance PASS ≠ Server runtime PASS ≠ GPU generation PASS ≠ Visual acceptance. One never implies another.

## 8. Source vs. Runtime Payload

- **Tracked Source**: `h3/`, `manga/`, `custom_nodes_custom/`, `workflows/`, `docs/`, `configs/`, `scripts/`.
- **Runtime / Payload (Untracked)**: `ComfyUI/`, model weights (`*.safetensors`, `*.bin`), `output/`, caches, temp files.
- Strictly adhere to `.gitignore`. Never stage or commit model weights, generated PNGs, or runtime payloads without explicit commander authorization.

## 9. Git & Security Rules

- Always start with `git status --short`. Preserve existing unrelated user changes; never revert or reset them.
- Never force-push, rebase, or rewrite Git history unless an explicit Card commands it.
- Push to remote only when explicitly commanded by the Card.
- Never run `git credential fill` or `git credential get`.
- Never inspect credential values, request pasted tokens/passwords, or include secrets in reports or commits.
