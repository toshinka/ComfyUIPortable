# TEGAKI Astra Production UI Review Brief

**Status:** Bounded review contract

**Review mode:** Adversarial UI/UX review; no implementation

**Scope:** Current Manga and H3 production Create workspaces

This brief is the contract for a later concentrated Astra review. It asks Astra
to challenge composition, hierarchy, density, workspace balance, Preview
behavior, motion, and narrow-screen use against the current implementation and
the two governing UI documents. It is not a replacement design specification,
redesign proposal, mockup, or implementation task.

The review must preserve the independent Manga and H3 runtimes, schemas,
workflows, and domain meanings. A shared interaction location is a cognitive
coordinate, not a shared backend contract.

## 1. Authoritative inputs

Astra must treat these as authoritative inputs:

1. `docs/ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md`
2. `docs/ui/TEGAKI_CREATE_WORKSPACE_MODEL.md`
3. The current Manga frontend implementation listed in Section 14
4. The current H3 frontend implementation listed in Section 14
5. The current Card and Commander constraints supplied when the review is
   invoked

Astra may criticize how the current UI applies the two documents. It may
challenge a principle only when the finding is explicitly classified
**PRINCIPLE CHALLENGE** and includes concrete rationale. It must not silently
override either document.

## 2. Astra role and review boundary

Astra is an **ADVERSARIAL UI/UX REVIEWER**. It is not a greenfield designer,
feature inventor, product-semantic architect, or runtime architect.

The review should identify:

- violations of established principles;
- awkward composition caused by a principle;
- weak visual hierarchy or excessive information competition;
- misleading empty space;
- Preview that is too dominant or too weak;
- hard-to-find actions, excessive scrolling, or cursor travel;
- damage to spatial memory when moving between Manga and H3;
- disruptive or unexplained motion; and
- narrow layouts that break the cognitive map.

The review stops after the bounded report described in Section 13. It does not
modify source, experiment with CSS, run a broad repository audit, review
unrelated runtime architecture, or automatically start the next Card.

## 3. Fixed product semantics

These meanings remain fixed during ordinary recommendations:

| Domain | Meaning |
| --- | --- |
| Manga Scene / Region | Where text or content applies |
| Manga CAST / Reference Appearance | Who appears and what appearance is referenced |
| Manga Guide / ControlNet | Pose, composition, and geometry |
| Manga LoRA | A learned modifier |
| H3 | A separate video/still product and runtime domain |
| H3 references, Frames, Start/End, motion/camera | H3-specific subject, temporal, and motion concepts |

H3 concepts must not be semantically merged into Manga concepts because their
controls occupy analogous positions. A shared UI slot never authorizes a
shared runtime schema.

## 4. Fixed Create model

Review against these five cognitive slots:

1. **INTENT** — text and generation intent
2. **SUBJECT** — identity and reference appearance/material
3. **SPACE / STRUCTURE** — region, frame, scene, or temporal/spatial framing
4. **CONTROL** — guide, pose, motion, camera, or other constraints
5. **OUTPUT** — Generate, status, current result, and History

Astra may recommend better grouping, ordering, presentation, density, or
emphasis inside these slots. A different top-level model must be reported as
**PRINCIPLE CHALLENGE**, not as an ordinary visual preference.

## 5. Fixed authoring loop

Evaluate the current UI against:

`AUTHOR → GENERATE → GLANCE → optionally FOCUS → EDIT → GENERATE AGAIN`

The loop should remain cheap. Findings should call out unnecessary mode
switches, large cursor travel, hidden Generate actions, excess scrolling, lost
current-result context, lost authoring context, forced modal transitions, and
visual reorientation.

## 6. Review dimensions

The report must cover all of these dimensions:

| Dimension | Question Astra must answer |
| --- | --- |
| Composition | Does the arrangement support the work sequence at each state? |
| Hierarchy | What visually dominates, supports, and recedes? |
| Density | Which information competes, and what can be compressed? |
| Preview / Create | Is Create primary before useful media, and is Preview legible afterward? |
| Workspace balance | Does the outer frame remain stable across media and states? |
| Focus | Is GLANCE → FOCUS continuous, reversible, and discoverable? |
| Motion | Does transition communicate information without wobble or decoration? |
| Manga/H3 horizontality | Are cognitive coordinates recognizable while meanings remain separate? |
| Narrow screen | Does the order survive stacking, tabs, and reduced space? |
| Production efficiency | Can an author iterate with low travel, low friction, and clear feedback? |

## 7. Empty Preview and balance questions

The central question is whether the current UI gives Preview too much space or
visual authority before useful media exists. Review these states separately:

- initial launch;
- authoring with no result;
- first generation;
- result-ready;
- repeat generation; and
- history versus current result.

Apply the principle **EMPTY PREVIEW MUST NOT BE THE VISUAL HERO**. Distinguish
an empty Preview, a current result, active generation, and History rather than
treating all four as one stage.

Ordinary authoring generally prioritizes Create over Preview, but the ratio is
open. Astra must evaluate 70:30, 65:35, or another balance from evidence about
information density, media legibility, prompt/reference interaction, Manga
page aspect, H3 video aspect, screen width, and iteration frequency. It must
not select a ratio by convention alone.

Left/right orientation is also open. Compare Create-left/Preview-right and
Preview-left/Create-right using reading order, Generate-to-result relationship,
cursor travel, Manga/H3 consistency, wide ergonomics, and narrow transformation.
No side is predetermined.

## 8. Preview container and Focus

Evaluate whether the outer Preview region remains stable as internal media
changes between portrait Manga pages, H3 16:9, square, and other supported
ratios. Discuss letterboxing, centering, whitespace, useful media size, and
visual balance without requiring one aspect ratio.

Review the proposed `GLANCE → FOCUS` behavior under the rule **FOCUS IS NOT
NAVIGATION**. Astra should examine:

- how far Preview expands;
- how Create compresses;
- whether prompt, subject, model, seed, and other context remain legible;
- whether entry and exit are obvious and reversible;
- whether click-to-focus is discoverable; and
- whether hover remains an affordance rather than a reflow trigger.

A full-screen modal is not the default recommendation. A later provisional
`INSPECT` state may be discussed for deep metadata, zoom, pan, playback, or
diagnostics, but it is not a first implementation requirement.

When Focus compresses information, evaluate a compact context containing as
applicable: prompt summary, CAST/subject identity, reference thumbnail,
Scene/Shot, model, seed, and an active Guide/control indicator. Advanced and
long technical panels may collapse. Semantics and draft values must remain
intact.

## 9. Generation feedback and result truth

Review Generate and execution feedback as one relationship. Status should be
visible near Generate, over Preview, or in a compact workspace projection
without becoming a large permanent panel.

Respect this truthfulness order:

`real progress > real phase > indeterminate activity`

Never recommend invented precise percentages. The current result and History
remain distinct:

- **Current Result** is immediate authoring feedback and remains visible while
  a new job runs when possible.
- **Result History** is a record of prior takes and alternatives.

Review whether the existing downward History flow needs refinement, but do not
design a complete Asset browser. Also review the divergence state in which
Current Settings have changed after Current Result. The UI should make that
relationship understandable with light-weight context such as “changed since
generation” without mandating that wording.

## 10. Attachment Card horizontality

Compare Manga CAST Reference, Manga Guide/ControlNet, and H3 image, video,
reference, or R2V attachments using this candidate grammar:

`empty slot → Add → thumbnail/media → identity/name → Replace/Remove →
strength when relevant → scope/target when relevant → advanced disclosure`

Evaluate card density, discoverability, consistency, repetitive appearance,
and how domain explanations are presented. Do not merge data models or
validation rules.

## 11. Domain identity and pressures

Manga and H3 should feel related but not identical: a shared cognitive house
plan with different interior rooms. Review accents, labels, icons, microcopy,
component emphasis, and domain-specific visualization. Color alone must not
carry identity.

Manga-specific pressures:

- page-like portrait media;
- Scene/Region spatial editing and longer text;
- CAST placement and Reference Appearance;
- future Guide/ControlNet and MRP work; and
- a possible page/panel-oriented workflow.

H3-specific pressures:

- playback and time information;
- 16:9 and other video ratios;
- reference attachments and R2V;
- Start/End Frames; and
- motion/camera controls and eventual downstream editing.

Video-tool conventions must not dominate Manga merely because they are
familiar. Manga page UI must not be forced onto H3.

## 12. Narrow-screen review

Review narrow behavior separately. Desktop coordinates need not remain literal,
but cognitive order must survive. Evaluate what stacks, what becomes tabs, what
stays one tap away, how Preview GLANCE/FOCUS behaves, how Generate stays
reachable, and how domain switching remains clear.

## 13. Motion and state hierarchy

Treat motion as information, not decoration. Review Preview Focus, context
compression, result arrival, generation state, disclosure, and domain
switching. Avoid large accidental motion, layout wobble, hover-triggered
reflow, and gratuitous animation. Explain what each recommended motion
communicates; do not require exact milliseconds unless strongly justified.

For each state below, the future report must identify what should dominate,
what is secondary, and what should recede:

1. First Launch
2. Authoring with no result
3. Generating
4. Result Ready / GLANCE
5. FOCUS
6. Failed

## 14. Current implementation targets

These are the exact entry files for a bounded source and rendered-UI review;
they are not a request for a long inventory:

**Manga**

- `manga/app/index.html`
- `manga/app/css/manga_workspace.css`
- `manga/app/src/view/generation_view.js`
- `manga/app/src/state/generation_state.js`

**H3**

- `h3/app/static/index.html`
- `h3/app/static/styles.css`
- `h3/app/static/app.js`

The reviewer should inspect the actual current rendered UI when it can be
safely obtained: wide Manga, wide H3, narrow Manga, and narrow H3. This Card
does not generate screenshots or launch runtime services. Source inspection
must remain limited to these targets and the authoritative documents.

## 15. Evidence classification

Every finding must carry exactly one classification:

| Classification | Use |
| --- | --- |
| **PROVEN** | Directly observable problem in the current implementation or rendered UI |
| **PLAUSIBLE** | Strong UX/design inference that still needs implementation validation |
| **PREFERENCE** | Visual/design taste or optional alternative |
| **PRINCIPLE CHALLENGE** | Recommendation that conflicts with an established UI principle |
| **UNKNOWN** | Insufficient evidence |

This classification prevents an aesthetic preference from being reported as a
fact. Principle challenges must be separated from ordinary recommendations.

## 16. Required future Astra output

The later Astra response must be a bounded report with these sections:

**A. EXECUTIVE FINDINGS** — maximum 10 severity-ranked findings.

**B. STATE-BY-STATE HIERARCHY** — First Launch, Authoring, Generating,
Glance, Focus, and Failed; for each state identify dominant, secondary, and
receding information.

**C. MANGA/H3 HORIZONTALITY** — what remains spatially recognizable and what
remains domain-specific.

**D. PREVIEW / CREATE RECOMMENDATION** — including ratio and orientation
rationale grounded in the review evidence.

**E. FOCUS RECOMMENDATION** — including expansion, exit, and contextual
compression.

**F. NARROW-SCREEN RECOMMENDATION** — including stacking, tabs, reachability,
and domain switching.

**G. TOP 5 IMPLEMENTATION CHANGES** — ranked, with no more than five.

**H. PRINCIPLE CHALLENGES** — maximum three and only when necessary.

**I. ONE NEXT IMPLEMENTATION SLICE** — exactly one bounded slice.

The report must distinguish borrowed conventions from TEGAKI-specific product
logic. It must not include implementation changes in the review itself.

## 17. Open questions to carry forward

Carry forward the unresolved questions from
`TEGAKI_CREATE_WORKSPACE_MODEL.md`, deduplicated and grouped here. Astra must
evaluate them, not close them by assumption.

### COMPOSITION

- What Create/Preview balance supports first launch and useful-result review?
- Which size/aspect presets belong in primary controls?
- Should orientation be direct, preset-derived, or contextual per domain?
- How can portrait Manga and landscape/square H3 media share a stable frame?

### FOCUS

- What expansion is enough for inspection without becoming a modal viewer?
- Which transition communicates Focus and generation calmly and accessibly?
- How much context should remain compressed, and at what density?

### STATUS

- Which truthful status projections belong near Generate, Preview, and History?
- How should “changed since generation” be communicated without heavy chrome?

### DOMAIN HORIZONTALITY

- How can accents and microcopy express Manga/H3 identity without relying on
  color alone or harming accessibility?
- Which contextual-help triggers work for pointer, touch, and keyboard users?

### NARROW SCREEN

- What is the Create/Preview/Focus interaction when editing during a job?
- Which controls must remain one tap away after the desktop layout collapses?

## 18. Review philosophy

The purpose of the Astra review is not to make TEGAKI resemble an existing AI
image or video application. Existing tools may provide useful conventions;
TEGAKI should extract useful interaction laws and adapt them to its own Manga
and H3 production workflow. The review must distinguish a borrowed convention
from TEGAKI-specific product logic.

## 19. Non-goals and stop conditions

The review must not:

- modify HTML, CSS, JavaScript, product source, schemas, or runtime;
- perform CSS experiments, mockup implementation, generation, GPU work, or
  model downloads;
- merge Manga and H3 runtime, schema, timeline, or supervisor behavior;
- redefine CAST, Reference, Scene/Region, Guide/ControlNet, or LoRA meanings;
- replace the five-slot model without a PRINCIPLE CHALLENGE;
- turn Focus into mandatory navigation or a full-screen viewer by default;
- invent progress percentages;
- redesign a complete Asset browser, Assemble workspace, or utility family;
- conduct a broad repository or unrelated runtime audit; or
- start an automatic follow-up Card.

If the evidence is insufficient, report UNKNOWN and stop at the bounded output
instead of expanding scope.

## 20. Review execution and validation

At invocation, verify the Commander-supplied Card, current branch, HEAD, and
clean worktree. Use only the authoritative documents and the Section 14 files
for source context. Obtain wide/narrow rendered views only when safe and do not
create screenshots as part of this brief-authoring Card.

This document itself is validated by its diff only. No product tests, runtime,
GPU, generation, or `/prompt` calls are part of this Card.
