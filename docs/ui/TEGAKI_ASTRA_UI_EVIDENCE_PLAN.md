# TEGAKI Astra UI Evidence Plan

Status: pre-Astra review preparation. This document defines what evidence to
capture and how to label it; it does not make a layout judgment and it does not
change the product.

## Authority, route, and scope

The evidence target is the standalone `D:\GitHub\ComfyUIPortable` project at
the review snapshot. Manga and H3 remain separate products with separate
runtime and generation semantics. Evidence may compare their presentation, but
must not imply a shared backend, timeline, or generation state.

The current owner route is:

1. `D:\GitHub\ComfyUIPortable\h3\run_h3.bat`
2. `h3/tools/tegaki_shell_supervisor.mjs`
3. H3 shell (8190), H3 native backend (8188), Manga backend (8189), and Manga
   Workspace (8191).

The shell embeds the Manga workspace after the workspace identity is valid.
The direct Manga document is `manga/app/index.html`; it exposes Generate and
Authoring tabs, with `?embedded=1` used by the shell. No runtime is started for
this evidence-plan card. A later review may use the owner route or an already
available safe fixture, but it must record which route was used.

The source snapshot for this plan is branch
`codex/tegaki-shell-manga-play1`, HEAD
`358ff68b022a850a723211c660da54caf56759b4`, with a clean worktree at plan
authoring time. This is provenance only; the plan does not replace runtime or
browser evidence.

## Evidence rules

- Capture the actual product surface at review time, or cite an existing local
  fixture/result. Do not fabricate a loading, result, error, or focus state.
- Keep source/static checks, browser screenshots, runtime identity, and Owner
  acceptance as separate evidence classes.
- A state that cannot be reached without inventing product behavior is recorded
  as `NOT IMPLEMENTED` or `PARTIALLY OBSERVABLE`; it is not simulated with DOM
  edits, CSS edits, or mocked screenshots.
- This card creates no screenshots. Existing local artifacts may be referenced
  as prior fixtures, with their provenance and limitations stated.
- Do not launch a model, download a model, submit `/prompt`, perform GPU
  inference, or install dependencies for this preparation.
- Manga and H3 attachment/reference controls retain their domain meaning. A
  visual comparison never turns Manga MRP, CAST/IPAdapter, or Guide into H3
  controls.

## Review viewport classes

These are review capture classes, not CSS breakpoints or implementation
requirements. Paired captures should use the same dimensions across domains.

| Class | Example viewport | Purpose |
| --- | --- | --- |
| `WIDE` | 1440 x 900 | Owner desktop composition and stable Preview/Create relationship. |
| `NARROW` | 430 x 850 | Phone-like constrained review of reachability, ordering, and result access. |

The Manga browser fixture already uses 1440 x 900 and 430 x 850. H3's current
source has a narrow Create/Result view selection around its own responsive
behavior; the dimensions above are evidence labels only. No intermediate class
is required for this bounded pass.

## Minimum capture set

The following set is the smallest useful package. “Generation needed” means a
new generation would be needed to create the state; `NO` means an existing
fixture, history item, or authoring data is sufficient. The preparation card
does not authorize any new generation.

| Capture ID | Domain / viewport | State and route | Smallest reproducible setup | Existing fixture or result | Attachment/reference | Generation needed |
| --- | --- | --- | --- | --- | --- | --- |
| `MANGA-WIDE-EMPTY` | Manga / WIDE | Generate tab, empty draft | Open Manga Generate without loading a result or authoring fixture | Empty `.mg-stage` and `No verified result yet` are product states | None | NO |
| `MANGA-WIDE-AUTHORING` | Manga / WIDE | Authoring tab, direct workspace or embedded shell | Open Manga Authoring; load the existing rich authoring fixture so Scene Composer, CAST, and Guide context are visible | `output/ui-review/2026-09-15/MANGA-UX-CLEANUP2/MANGA_AUTHORING.png` may be cited as prior local evidence; refresh at review time if safe | Existing local CAST/Guide/reference assets only | NO |
| `MANGA-WIDE-RESULT` | Manga / WIDE | Generate tab with a verified result and history | Use an existing local completed result/history item and its saved settings; do not submit a job | `MANGA_GENERATE.png` is a prior local artifact and must be labelled as such; if no valid local result is available, mark unavailable | None beyond the result's recorded metadata | NO |
| `MANGA-NARROW-AUTHORING` | Manga / NARROW | Authoring tab | Use the same rich authoring fixture, then set the review viewport to 430 x 850 | `verify_play1_browser.mjs` contains the narrow fixture path; its temporary screenshot is not a new product artifact | Existing fixture assets | NO |
| `MANGA-NARROW-RESULT` | Manga / NARROW | Generate tab with previous/current result | Use the same safe local result as the wide capture and switch only the viewport; retain unsent draft edits if the fixture records them | Browser fixture result/restore path; no new PNG is required now | None | NO |
| `MANGA-REFERENCE-AUTHORING` | Manga / WIDE or NARROW | Authoring tab with CAST/Guide/reference section expanded | Load the rich fixture and expand only the reference section needed to show attachment grammar | Prior `MANGA_AUTHORING.png` can be a starting reference, not acceptance | Existing local reference image(s) | NO |
| `H3-WIDE-EMPTY` | H3 shell / WIDE | H3 Video Create with an empty draft | Open the owner shell and leave prompt/reference inputs empty | Empty Preview/Create shell | None | NO |
| `H3-WIDE-AUTHORING` | H3 shell / WIDE | H3 Video (or Still/Prep when the comparison requires it) | Open the owner shell with an empty or text-only Create draft; keep Manga iframe identity visible only where the shell normally shows it | No paired H3 screenshot script was found; capture at review time if an owner session is already available | Only an existing safe local reference slot, if present | NO |
| `H3-WIDE-RESULT` | H3 shell / WIDE | H3 result/history view | Select an existing local completed history/result item; otherwise record `NOT AVAILABLE` | Existing local H3 result/history only; never synthesize one | Result metadata as recorded | NO |
| `H3-NARROW-AUTHORING` | H3 shell / NARROW | H3 Create view | Use the same draft and select the normal narrow Create view; do not alter product state | Existing H3 static/source checks document the view; screenshot only at review time | Existing local reference slot only | NO |
| `H3-NARROW-RESULT` | H3 shell / NARROW | H3 Result view | Select an existing result/history item, then use the shell's Result view selection; if none exists, record unavailable | Existing local result/history only | Result metadata as recorded | NO |
| `H3-REFERENCE-AUTHORING` | H3 shell / WIDE or NARROW | H3 reference/attachment slot | Use an existing safe local Start/End/Still/Prep/R2V asset and the normal add/replace/remove flow | Source/static evidence and an existing local asset; no fake upload | Existing local reference asset | NO |

Priority order is ordinary authoring, result-present, narrow, then attachment or
spatial context. Error/progress evidence is collected only when the product or
an existing safe fixture already exposes it.

## Paired comparison dimensions

The reviewer should record observations against these dimensions without
answering the questions in this preparation plan:

| Dimension | Manga evidence | H3 evidence | Boundary |
| --- | --- | --- | --- |
| Create hierarchy | Manga Generate/Authoring controls and scene context | H3 Create controls for Video/Still/Prep | Compare reachability and grouping; do not require identical controls. |
| Preview prominence | `.mg-stage`, empty/result labels, history continuity | H3 preview/stage and history | Record what is visible at a glance; do not score the ratio here. |
| Generate/status proximity | `#mg-generate`, `#mg-status`, job labels | H3 Generate/cancel/status overlay | Check whether action and state can be located together. |
| Attachment grammar | CAST/Guide/reference cards and scene context | Start/End/Still/Prep/R2V slots | Meaning is domain-specific. |
| Subject/reference handling | CAST identity and reference summary | H3 reference slots | Record whether context survives the viewport. |
| Advanced-setting density | Basic/Scene tabs and Manga generation controls | H3 mode settings and Advanced areas | Do not prescribe a density value. |
| Result continuity | Previous verified result labels and history restore | History selection and preview state | Record current result versus draft edits separately. |
| Narrow behavior | Narrow fixture and stacked/collapsed Generate view | H3 Create/Result view selection | Dimensions are review classes, not breakpoints. |
| Truthful failure/progress | FAILED/UNKNOWN/SUBMITTING/GENERATING labels | backend/job/error labels and elapsed overlay | Record only states actually observed. |
| Domain identity | Manga accent, Generate/Authoring tabs, scene vocabulary | H3 Video/Still/Prep grouping | Keep engine ownership explicit. |

## Review questions to answer later

These are prompts for Astra, not conclusions from this card.

- Are INTENT, SUBJECT, SPACE/STRUCTURE, CONTROL, and OUTPUT findable in the
  Create surface for the relevant domain?
- Is the Create/Preview relationship understandable before a result exists?
- When a result exists, what remains GLANCE context and what can become FOCUS?
- Is context compressed without losing the subject, reference, or structural
  meaning?
- Can Generate and its current status be found together?
- Does progress describe the actual job state rather than imply completion?
- Is the current verified result distinguishable from unsent draft edits?
- Does Restore settings change only the draft and preserve result truth?
- Does the narrow class retain access to Create, Preview, status, history, and
  attachments without inventing a new interaction model?
- Are H3 and Manga visibly related while preserving independent semantics and
  runtime identity?

## Current observable contract inventory

The detailed state-by-state reproduction matrix is in
`TEGAKI_ASTRA_UI_STATE_MATRIX.md`. The summary below records the current
implementation boundary.

| Contract | Manga | H3 | Evidence note |
| --- | --- | --- | --- |
| `MediaPreviewShell` | `PARTIAL` | `PARTIAL` | Stage/preview containers exist, but no shared named composition is implemented. |
| `PreviewFocus` | `NOT_IMPLEMENTED` | `PARTIAL` | H3 has a narrow Result selection; neither domain has the full dedicated focus contract. |
| `GenerationStatus` | `VISIBLE_CURRENTLY` | `VISIBLE_CURRENTLY` | Independent status projections expose ready, submitting/running, failure, and unknown/backend states. |
| `ProgressProjection/Overlay` | `PARTIAL` | `PARTIAL` | Status proximity exists; H3 has elapsed/overlay behavior, while Manga has job labels but no unified projection. |
| `AttachmentCard` | `VISIBLE_CURRENTLY` | `VISIBLE_CURRENTLY` | Manga CAST/Guide and H3 reference slots expose add/replace/remove/status/thumbnail patterns. |
| `CompactContext` | `PARTIAL` | `PARTIAL` | Labels, history summaries, and reference summaries provide some context; the explicit contract is not a shared component. |

## Existing automation and local artifacts

`manga/tests/verify_play1_browser.mjs` is the existing Playwright fixture for
safe later capture. It uses 1440 x 900 and 430 x 850, exercises authoring,
result, failure, unknown, restore, previous-result retention, and narrow order,
and uses a fake backend without real `/prompt` or GPU inference. Its temporary
screenshots are evidence only when their fixture provenance is recorded.

H3 has bounded source/logic checks such as
`h3/tests/verify_h3_r1_stage_generate_visibility.mjs` and
`h3/tests/verify_h3_g1a_stage_action.mjs`; these validate visibility and state
logic, not paired rendered screenshots. No new capture script is added here.

Existing local artifacts under
`output/ui-review/2026-09-15/MANGA-UX-CLEANUP2/` (`MANGA_AUTHORING.png`,
`MANGA_GENERATE.png`, `H3_VIDEO_BASELINE.png`, and `REVIEW_MANIFEST.txt`) may
be cited as prior evidence. They are not regenerated or promoted to Owner
acceptance by this card.

The project checkpoint remains `WAIT FOR ASTRA UI REVIEW`; this preparation does
not advance that state.

## Naming and evidence manifest

Future review captures should be written to the local, gitignored review area
`output/ui-review/astra_ui/` and use deterministic lowercase names:

`<domain>_<viewport>_<state>.png`

Examples: `manga_wide_authoring.png`, `manga_narrow_result.png`,
`h3_wide_authoring.png`. A sidecar manifest may use the same stem with
`.json` or `.txt`. Each record should include route/tab, viewport class and
dimensions, state ID, fixture/result identifier, attachment/reference
identifier, whether generation was needed, and whether the image is fresh or
prior local evidence.

## Astra handoff

Inputs:

- `TEGAKI_PRODUCTION_UI_PRINCIPLES.md`
- `TEGAKI_CREATE_WORKSPACE_MODEL.md`
- `TEGAKI_UI_COMPONENT_CONTRACTS.md`
- `TEGAKI_ASTRA_UI_REVIEW_BRIEF.md`
- this evidence plan and the state matrix
- actual captures produced at review time, with their manifest and provenance

Expected Astra output:

- at most 10 severity-ranked findings;
- at most 5 implementation changes;
- at most 3 challenges to the current principles;
- exactly 1 next implementation slice.

The handoff must keep “evidence observed” separate from “implementation
recommended.”

## Stop conditions and non-goals

Stop if a requested state requires a fake DOM/CSS state, a new product
capability, a model download, `/prompt`, GPU inference, or an architecture
change. Do not modify source/UI/HTML/CSS/JS, authoring schema, runtime
lifecycle, H3/Manga ownership, or `docs/STATUS.md`. Do not decide ratios,
orientation, exact sizes, focus animation, breakpoint values, or density here.
