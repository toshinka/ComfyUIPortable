# TEGAKI UI Component Contracts

**Status:** Implementation-neutral behavioral contract layer

**Scope:** Reusable behaviors for the Manga and H3 Production Create
workspaces

This document defines the contract between TEGAKI product semantics and a
future visual or component implementation. It is deliberately independent of
framework, DOM structure, CSS, final composition, panel ratio, left/right
placement, colors, and exact animation timing.

Manga and H3 may use related interaction grammar while retaining separate state
ownership, validation, backend routes, runtime graphs, and semantic meaning.
`CAST Reference` is not an H3 R2V reference; `Guide` is not H3 motion control;
`Region` is not a Frame. A shared contract never authorizes a shared runtime
schema.

## 1. Contract law

A TEGAKI UI component contract specifies:

- **STATE** — the observable lifecycle or presentation state;
- **INPUT MEANING** — what supplied values mean, without prescribing a data
  shape;
- **USER ACTIONS** — deliberate actions available to the user;
- **OBSERVABLE BEHAVIOR** — guarantees a user can rely on;
- **DOMAIN EXTENSIONS** — where Manga or H3 supplies its own meaning; and
- **NON-GOALS** — behavior this contract does not own.

Contracts should not specify pixel dimensions, left/right placement, final
colors, framework APIs, DOM structure, CSS architecture, or exact motion timing
unless a later Card explicitly requires such a decision.

## 2. Domain boundary

The contracts provide interaction grammar only. Each domain remains responsible
for:

- its authoring state and persistence;
- its validation and capability checks;
- its request and result schema;
- its runtime and workflow graph;
- its semantic labels and contextual help; and
- its error interpretation.

The same contract may therefore receive different domain projections. A Manga
attachment can describe CAST appearance, while an H3 attachment can describe a
video subject or a start/end frame.

## 3. MediaPreviewShell

### PURPOSE

Provide a stable media/result viewing surface inside a Production Create
workspace. It gives an explicit place for no media, a validated result, and
truthful active or failed generation feedback.

### INPUT MEANING

The shell receives a media projection, when one exists, and an optional
generation projection. Media metadata may include:

- media type (image or video);
- aspect ratio or intrinsic dimensions;
- result identity;
- generation identity or result linkage; and
- domain media controls supported by the producer.

`previous result` and `current result` are meaningful relationships supplied by
result state; the shell must not infer them from display order alone.

### STATE

- `EMPTY`
- `MEDIA_READY`
- `GENERATING_WITH_PREVIOUS_MEDIA`
- `GENERATING_WITHOUT_MEDIA`
- `ERROR_WITH_PREVIOUS_MEDIA`

The shell may show an indeterminate activity state when the source supplies no
measurable phase or progress.

### ACTIONS

The shell may expose an explicit preview/focus action and domain media actions.
It does not initiate generation. A user may inspect the current media, enter or
exit PreviewFocus, zoom/pan an image when Manga supplies those controls, or
play/seek video when H3 supplies those controls.

### GUARANTEES

- The outer viewing relationship remains stable where practical when internal
  media changes between portrait, landscape, square, or other ratios.
- No media is represented honestly as empty; no placeholder claims success.
- A generation overlay may coexist with previous successful media.
- A failure does not require clearing previous successful media.
- The shell does not become a gallery or take ownership of History.
- Media controls and labels follow the domain and media type.

### DOMAIN EXTENSIONS

Manga may add image zoom, pan, fit, page or panel context, and validated PNG
metadata. H3 may add play, pause, seek, time display, frame context, and
video-specific media metadata. These extensions do not replace the shell
contract.

### NON-GOALS

The shell does not decide an aspect ratio, letterboxing strategy, fixed panel
size, full-screen ownership, result storage, generation request schema, or
final layout.

### STATE TABLE

| STATE | INPUT / CONDITION | VISIBLE SEMANTICS | ALLOWED USER ACTIONS | TRANSITION / RESULT |
| --- | --- | --- | --- | --- |
| `EMPTY` | No accepted media is available | Empty result affordance and next-step context | Open available Create controls; request a deliberate preview focus only if useful | A validated result enters `MEDIA_READY`; an accepted job enters `GENERATING_WITHOUT_MEDIA` |
| `MEDIA_READY` | Accepted media and result linkage are available | Current result, media identity, and applicable controls | Inspect/focus; use domain media controls; continue editing Create | New accepted job enters `MEDIA_READY`; active job enters `GENERATING_WITH_PREVIOUS_MEDIA` |
| `GENERATING_WITH_PREVIOUS_MEDIA` | Active job plus prior accepted media | Prior media remains visible with truthful overlay/status | Inspect prior media; edit draft if domain allows; no implicit retry | Success replaces current media; failure enters `ERROR_WITH_PREVIOUS_MEDIA` |
| `GENERATING_WITHOUT_MEDIA` | Active job and no prior accepted media | Empty/placeholder context plus truthful active status | Edit draft if domain allows; observe status | Success enters `MEDIA_READY`; failure returns to `EMPTY` with error projection |
| `ERROR_WITH_PREVIOUS_MEDIA` | Active job failed and prior media exists | Prior media labelled as previous and short failure summary | Edit and explicitly retry when offered; inspect prior media | New explicit submit re-enters an active state; success replaces current media |

## 4. Preview aspect relationship

`MediaPreviewShell` accepts an internal media aspect that may be a
sqrt(2)-like Manga page, 16:9, 4:3, 1:1, 9:16, or another supported ratio.
The outer Preview relationship should remain stable where practical; an
internal viewport handles the media ratio. This contract does not mandate
letterboxing, cropping, centering, or any particular maximum size.

## 5. PreviewFocus

### PURPOSE

Represent `GLANCE ↔ FOCUS` as a presentation state change inside the same
Create workspace. Focus gives a useful result more attention without making the
author leave the production task.

### INPUT MEANING

PreviewFocus receives the current Preview target and a reversible presentation
context. It may receive a CompactContext projection, but it does not receive or
own generation settings.

### STATE

- `GLANCE` — ordinary compact result view;
- `FOCUS` — deliberate, in-place result attention state; and
- `INSPECT` — provisional future detail state for deep metadata, zoom, pan,
  playback, or diagnostics.

### ACTIONS

Possible deliberate entry actions are click/tap on Preview or an explicit focus
control. Possible exits are click outside, Escape, or an explicit toggle. The
exact trigger policy remains a later design decision. Hover may provide an
affordance, but it must not cause major expansion.

### GUARANTEES

- Focus is deliberate and reversible.
- Focus is not route or page navigation.
- Exiting Focus restores the prior Create context and does not generate.
- Authoring context remains perceptible in compressed form.
- Entering or exiting Focus does not alter prompt, model, seed, CAST,
  Reference, Guide, or backend job state.
- `INSPECT` remains optional and cannot be required by an initial prototype.

### DOMAIN EXTENSIONS

Manga may emphasize page composition, region, CAST, or image controls. H3 may
emphasize playback, time position, frame, shot, or motion context.

### NON-GOALS

PreviewFocus does not define a modal viewer, navigation route, final expansion
amount, exact transition curve, or final focus controls.

### STATE TABLE

| STATE | INPUT / CONDITION | VISIBLE SEMANTICS | ALLOWED USER ACTIONS | TRANSITION / RESULT |
| --- | --- | --- | --- | --- |
| `GLANCE` | Current result is shown in ordinary workspace context | Compact media and status/context summary | Request Focus; use media controls; edit Create | Deliberate focus request enters `FOCUS` |
| `FOCUS` | User deliberately emphasizes current media | Larger or clearer media attention with compressed Create context | Inspect media; exit Focus; continue permitted editing | Exit returns to the same `GLANCE` result and draft |
| `INSPECT` (provisional) | Future deep inspection is explicitly available | Detailed media/metadata view while retaining result linkage | Use deep inspection actions; exit | Exit returns to `FOCUS` or `GLANCE`; no generation side effect |

## 6. CompactContext

### PURPOSE

Provide a reduced representation of authoring and result context while Preview
is emphasized.

### INPUT MEANING

CompactContext is derived from current authoring state and immutable result/job
metadata. Potential fields include prompt summary, CAST/subject identity,
reference thumbnail, Scene/Shot, model, seed, Guide/control presence, and the
relationship between current settings and the visible result.

### STATE

CompactContext has no independent generation lifecycle. Its projection may be
`AVAILABLE`, `PARTIAL`, or `UNAVAILABLE` according to source data.

### ACTIONS

It may reveal a compressed field, expand contextual detail, or return to the
ordinary Create presentation. These actions are observational and must not
submit, mutate, or silently normalize the source state.

### GUARANTEES

- It is a projection, never a second source of truth.
- Missing fields remain missing or explicitly unavailable.
- Domain-specific composition is allowed.
- Compression hides detail temporarily; it does not discard authoring values or
  result linkage.
- A stale-result relationship can be represented without deleting the result.

### DOMAIN EXTENSIONS

Manga may include Region, Scene, CAST, panel, and Guide summaries. H3 may
include Frame, Shot, Start/End, reference, motion, camera, and time summaries.

### NON-GOALS

CompactContext does not define global mandatory fields, wording, dirty-tracking
storage, persistence, or a shared Manga/H3 metadata schema.

### CONTEXT PRIORITY

The projection may classify information as:

- **KEEP** — identity-critical context, current-result relationship, and
  high-value generation context;
- **COMPRESS** — long prompts, model metadata, and secondary controls; and
- **HIDE / DEFER** — advanced technical settings and rare expert options.

Exact membership is domain- and composition-specific and remains open.

## 7. GenerationStatus

### PURPOSE

Represent one logical generation execution consistently across all visual
projections.

### INPUT MEANING

GenerationStatus receives the domain's observed execution state. Fields are
optional and should be included only when reliable:

- state;
- message or phase label;
- current step and total steps;
- job id;
- error summary; and
- result id.

### STATE

The generic vocabulary is:

`IDLE`, `QUEUED`, `PREPARING`, `SAMPLING`, `PROCESSING`, `DECODING`, `SAVING`,
`SUCCEEDED`, `FAILED`.

A runtime may skip phases or provide an engine-specific phase that is mapped to
the nearest truthful projection. The UI must not claim a phase that was not
observed.

### ACTIONS

The status projection may expose an explicit cancel, dismiss, retry, or inspect
action only when the domain contract supports it. Status itself does not
submit, retry, or change the job.

### GUARANTEES

- One logical status can be projected near Generate, over Preview, and in a
  compact workspace status area.
- If `current_step` and `total_steps` are reliable, numeric progress may be
  shown.
- If only a phase is reliable, show the phase only.
- If neither is reliable, show indeterminate activity.
- Precise percentages must never be fabricated.
- A failed job preserves safe error context and does not clear prior media.

### DOMAIN EXTENSIONS

Manga may report sampling, decoding, validation, and SaveImage/result retrieval.
H3 may report frame processing, encoding, playback readiness, or temporal
phases. Each domain maps its own backend truth.

### NON-GOALS

GenerationStatus does not define a backend event bus, polling transport, queue
policy, progress calculation, retry policy, or shared execution schema.

### STATE TABLE

| STATE | INPUT / CONDITION | VISIBLE SEMANTICS | ALLOWED USER ACTIONS | TRANSITION / RESULT |
| --- | --- | --- | --- | --- |
| `IDLE` | No active job | Ready/idle and Generate availability as supplied by domain | Edit Create; request Generate | Accepted request enters `QUEUED` or the first observed active phase |
| `QUEUED` | Request accepted but waiting | Queued label; position only when measured | Observe; cancel only if supported | Enters `PREPARING` or a later observed phase |
| `PREPARING` | Loading, conditioning, or setup observed | Phase label and real detail only | Observe; domain-supported cancel | Enters `SAMPLING`, `PROCESSING`, or `FAILED` |
| `SAMPLING` | Sampling and optional step counts observed | Phase and real step/total when available | Observe; domain-supported cancel | Enters `PROCESSING`, `DECODING`, `SAVING`, or `FAILED` |
| `PROCESSING` | Domain post-processing observed | Phase and measured detail when available | Observe | Enters `DECODING`, `SAVING`, `SUCCEEDED`, or `FAILED` |
| `DECODING` | Media decode observed | Phase label and real detail when available | Observe | Enters `PROCESSING`, `SAVING`, `SUCCEEDED`, or `FAILED` |
| `SAVING` | Result persistence observed | Saving label | Observe | Enters `SUCCEEDED` or `FAILED` |
| `SUCCEEDED` | Result accepted and retrievable | Success, result identity, and current-result linkage | Preview/focus, edit draft, history actions | Remains evidence while a later request starts a new status |
| `FAILED` | Job or result failed | Short safe error and phase when known | Edit; explicit retry if supported; inspect prior result | Returns to domain authoring/idle or starts a new explicit request |

## 8. ProgressProjection and ProgressOverlay

### PURPOSE

Allow the same GenerationStatus to be rendered in more than one place without
creating separate status machines. `ProgressProjection` is the general
projection; `ProgressOverlay` is a possible compact overlay on Preview.

### INPUT MEANING

Both receive one GenerationStatus plus a presentation target. A projection may
choose a lower-information representation, such as `Sampling 7 / 16` near
Generate and `Sampling…` over Preview.

### STATE / ACTIONS / GUARANTEES

- They have no independent lifecycle or backend ownership.
- They must agree on active, succeeded, and failed state.
- They may omit detail but must not contradict the source.
- They must protect a previous accepted result when an active job overlays it.
- A projection may be moved, stacked, or condensed for narrow screens without
  changing status meaning.

### DOMAIN EXTENSIONS

Manga may use a result-validation or image-saving overlay. H3 may use a frame,
encoding, or playback-readiness overlay.

### NON-GOALS

No exact placement, permanent status panel, percentage animation, or event-bus
architecture is defined here.

## 9. AttachmentCard

### PURPOSE

Provide a reusable interaction grammar for media and control attachments whose
semantics differ by domain.

### INPUT MEANING

The card receives an attachment projection containing, when available, a
thumbnail or media marker, identity/name, short explanation, availability or
validation state, and optional domain fields such as strength, scope, target,
or start/end influence.

### STATE

- `EMPTY`
- `ATTACHED`
- `INVALID`
- `LOADING / PROCESSING` when the domain can observe that phase

### ACTIONS

Shared candidate actions are Add, Replace, Remove, Inspect/preview, and open
advanced settings. Optional strength, scope, target, and start/end controls are
available only when meaningful to that domain.

### GUARANTEES

- The selected identity and availability remain visible.
- Add/replace/remove are deliberate and reversible when the domain permits.
- Invalid or unavailable values are not silently stripped or substituted.
- Explanations distinguish similar-looking domain concepts.
- Optional fields do not become mandatory across all attachment types.
- The grammar survives condensed or stacked narrow layouts.

### DOMAIN EXTENSIONS

Expected users include Manga CAST Reference Appearance, Manga Guide/ControlNet,
H3 subject/reference image, H3 R2V/video input, and future related attachments.
The interaction shape may be shared; label, explanation, validation, and
runtime payload remain domain-specific.

### EXPLANATION CONTRACT

Each card supports three progressive layers:

1. **LABEL** — concise slot and attachment name;
2. **SHORT EXPLANATION** — one sentence describing purpose and applicability;
3. **OPTIONAL ADVANCED DETAIL** — limits, strength, scope, or runtime effect
   when requested.

Persistent long prose is not required in the card.

### NON-GOALS

AttachmentCard does not define a file picker, catalog, upload transport,
storage format, shared attachment schema, or mandatory visual card geometry.

### STATE TABLE

| STATE | INPUT / CONDITION | VISIBLE SEMANTICS | ALLOWED USER ACTIONS | TRANSITION / RESULT |
| --- | --- | --- | --- | --- |
| `EMPTY` | No attachment selected | Slot purpose, accepted type, and Add/Choose affordance | Add/Choose | Selection enters `LOADING / PROCESSING` or `ATTACHED`; cancellation remains empty |
| `LOADING / PROCESSING` | Attachment is being read, validated, or prepared | Activity and known identity/status; no false attached claim | Observe; cancel if domain supports it | Valid input enters `ATTACHED`; failure enters `INVALID` or `EMPTY` with reason |
| `ATTACHED` | Valid attachment and domain linkage available | Thumbnail/marker, identity, availability, explanation, and applicable scope | Replace, Remove, Inspect, advanced settings | Replace repeats loading/processing; remove returns `EMPTY`; invalidation enters `INVALID` |
| `INVALID` | Missing, unsupported, or failed validation | Value remains visible with a short reason | Replace, Remove, retry validation if supported | Corrected input enters processing/attached; remove returns `EMPTY` |

## 10. Generate and History relationships

Generate is not one of the reusable components in this Card. It is the domain
action that consumes an authoring snapshot. It may expose idle, accepted, busy,
failed, and completed presentation states by projecting GenerationStatus; it
must not own a second status model.

`MediaPreviewShell` concerns the current result. History concerns downstream
storage and browsing of previous results. The contracts preserve:

- current result as immediate authoring feedback;
- result history as prior takes or alternatives; and
- `RESULT_STALE_RELATIVE_TO_CURRENT_SETTINGS` as a presentation relationship
  when current settings changed after the visible result.

The divergence concept does not require full dirty tracking or mandate wording.
History selection restores or proposes settings only when the domain explicitly
supports it; it never implies automatic generation.

## 11. Failure and previous result

GenerationStatus and MediaPreviewShell together must support a short, safe
failure state with a known phase and error summary where useful. Raw backend
logs are not required in primary UI; developer detail may remain separately
accessible. A failed attempt preserves the current draft and any prior
successful media, clearly distinguishing the failed job from the prior result.

## 12. Accessibility and input-mode neutrality

Contracts must not depend on mouse hover. Hover may add an affordance, tooltip,
or preview emphasis, but critical actions require explicit click/tap/focus
equivalents. PreviewFocus must be operable without hover, and AttachmentCard
actions must remain discoverable in keyboard and touch modes. This Card does
not define a complete accessibility policy.

## 13. Narrow-screen neutrality

Behavior must survive substantial composition changes. A future layout may:

- stack MediaPreviewShell;
- render CompactContext as a strip or card;
- condense AttachmentCard;
- move ProgressProjection; or
- expose Create and Result as tabs.

The contracts preserve meaning, ownership, reversibility, and cognitive order;
they do not preserve literal desktop coordinates.

## 14. Conceptual action vocabulary

These names are implementation-neutral descriptions, not an event-bus design:

`REQUEST_GENERATE`, `GENERATION_ACCEPTED`, `GENERATION_PHASE_UPDATED`,
`GENERATION_SUCCEEDED`, `GENERATION_FAILED`, `REQUEST_PREVIEW_FOCUS`,
`EXIT_PREVIEW_FOCUS`, `ATTACH_MEDIA`, `REPLACE_MEDIA`, and `REMOVE_MEDIA`.

An implementation may use different event or callback names while preserving
the observable contracts.

## 15. Ownership map

| Concern | Owner |
| --- | --- |
| Authoring state | Domain Create model (Manga or H3) |
| Generation execution state | Domain generation/runtime state layer |
| Current result | Domain result/generation state |
| PreviewFocus | UI presentation state |
| CompactContext | Derived projection from authoring/result state |
| Attachment validation | Domain-specific attachment logic |
| ProgressProjection / Overlay | UI projection of GenerationStatus |
| History | Domain result/history storage and browsing layer |

Entering Focus, rendering a compact context, or projecting progress must not
silently transfer ownership of domain state.

## 16. Safe sharing candidates

Future implementation may share behavioral patterns for:

- Preview shell behavior;
- Focus state semantics;
- status display grammar;
- progress projection and overlay rules;
- AttachmentCard interaction grammar; and
- CompactContext projection patterns.

Sharing is safe only at the interaction boundary. Domain adapters remain
responsible for meaning, validation, and payload.

## 17. Must remain domain-specific

At minimum, these remain separate:

- runtime request schema and validation rules;
- CAST and Reference semantics;
- Guide and ControlNet settings;
- Region and MRP semantics;
- Frame and Start/End semantics;
- H3 R2V semantics;
- H3 timing and motion settings; and
- Manga spatial authoring logic.

Visual similarity or a shared component does not change this list.

## 18. Astra compatibility

Astra may later recommend changes to component visual arrangement, density,
placement, proportion, motion, and styling without invalidating these
contracts. If Astra recommends changing a behavior contract, ownership rule, or
semantic boundary, the finding must be classified **PRINCIPLE / CONTRACT
CHALLENGE** and justified separately; it must not be silently folded into an
implementation recommendation.

## 19. Implementation-readiness classification

This is a conservative planning classification, not implementation
authorization:

| Contract | Classification | Reason |
| --- | --- | --- |
| `GenerationStatus` | **READY FOR PROTOTYPE** | Vocabulary and truthfulness rules are sufficiently behaviorally bounded |
| `ProgressProjection / ProgressOverlay` | **READY FOR PROTOTYPE** | It can project one status without choosing layout |
| `AttachmentCard` | **READY FOR PROTOTYPE** | Core actions and invalid-state guarantees are clear; visual density remains open |
| `MediaPreviewShell` | **NEEDS ASTRA REVIEW FIRST** | Behavior is bounded, but media balance and aspect composition need review |
| `PreviewFocus` | **NEEDS ASTRA REVIEW FIRST** | State ownership is clear; motion, expansion, and narrow behavior need review |
| `CompactContext` | **NEEDS ASTRA REVIEW FIRST** | Projection boundary is clear; content density and priority need review |

No contract is classified as `DEFER`; all six have a useful behavior boundary,
while three intentionally await Astra composition review.

## 20. Current code mapping

This bounded mapping identifies existing pieces that approximate the contracts;
it does not authorize an abstraction or refactor.

| Current piece | Approximation |
| --- | --- |
| `manga/app/index.html` Generate stage | MediaPreviewShell empty/validated result surface and OUTPUT action area |
| `manga/app/src/view/generation_view.js` status rendering | GenerationStatus-like READY/SUBMITTING/GENERATING/FAILED/UNKNOWN projection |
| `manga/app/src/view/generation_view.js` previous preview handling | Generating/failure behavior that preserves the last validated result |
| `manga/app/src/state/generation_state.js` draft/jobs | Domain-owned authoring and job state, distinct from presentation focus |
| Manga Generate fields in `index.html` | Primary intent/model/control inputs supplied to a domain adapter |
| Manga CAST reference controls in `index.html` | AttachmentCard-like Add/Clear/thumbnail/status grammar with Manga meaning |
| Manga Scene/Guide/Character Instance inspector | Domain-specific Subject and Space/Structure attachments and context |
| `h3/app/static/index.html` Preview/Create/status/history areas | Related MediaPreviewShell, status projection, and History grammar for H3 |
| H3 reference slots and upload controls in `app.js` | AttachmentCard-like add/replace/remove behavior with H3 semantics |
| H3 `showPreviewJob` and polling in `app.js` | Current result preservation and active status projection |
| H3 narrow Create/Result switch in `styles.css` and markup | Narrow-screen composition change that can consume the same behavioral contracts |

## 21. Non-goals

- Final design system, component library, or framework decision.
- React/Vue migration, web-component architecture, DOM refactor, or CSS token
  redesign.
- HTML, CSS, JavaScript, runtime, backend, generation, or GPU changes.
- A shared Manga/H3 runtime schema, event bus, timeline, or supervisor.
- Final layout, panel ratio, left/right placement, colors, typography, or exact
  animation timing.
- Assemble workspace, History browser redesign, or mobile final design.
- A new authoring persistence schema or alteration of existing contracts.
- A model/LoRA catalog, file picker, upload service, or storage format.

## 22. Decision boundary

These contracts stabilize ownership, state meaning, truthful feedback,
reversibility, and domain extension points before composition. After this
document is committed, stop adding design abstractions. The next action is
either to wait for Astra review or, if the Commander explicitly requests use
of remaining LUNA quota, to implement one contract already classified `READY
FOR PROTOTYPE` that does not constrain layout. Do not begin a page redesign.
