# TEGAKI Create Workspace Model

**Status:** Information architecture and state-flow specification

**Scope:** Manga and H3 production Create workspaces

**Audience:** Product, UI, and implementation planning

This document defines the information relationships that make a TEGAKI Create
workspace understandable before a visual composition is selected. It extends
the stable interaction principles in
`docs/ui/TEGAKI_PRODUCTION_UI_PRINCIPLES.md`. It does not select a final grid,
ratio, palette, animation, or component framework.

Manga and H3 remain independent products, schemas, runtimes, workflows, and
generation states. The horizontal model below is a cognitive map, not a shared
backend contract.

## 1. Purpose of Create

Create is the place where an author expresses intent, supplies the material
needed to interpret it, chooses generation controls, starts a job, and judges
the resulting media.

| STATE | USER INTENT | VISIBLE INFORMATION | BEHAVIOR | RATIONALE |
| --- | --- | --- | --- | --- |
| Create workspace | Prepare one deliberate generation | Draft controls, current result, status, and recent history | Edit a draft, Generate it, then evaluate the result in place | The author should not need to leave the production task to complete the loop |
| Authoring context | Keep the work connected to its scene or shot | Scene, CAST/subject, frame/region, guide/reference summaries | Attach or choose context through the domain's controls | Generation is an operation on authored intent, not an isolated text box |

Create is not a gallery, a full image editor, a timeline, a settings or
administration page, or a full-screen viewer. Those concerns may exist in later
workspaces and may use different layouts.

## 2. Five cognitive slots

The slots are stable places to look for meaning. They are not a required
component hierarchy and do not imply one data model.

| Slot | Manga | H3 |
| --- | --- | --- |
| **INTENT** | Positive and negative prompt, scene intent, and manga-specific text | Prompt and video/still intent |
| **SUBJECT** | CAST identity, Character Instance, and appearance references | Subject/reference material, including R2V-related input |
| **SPACE / STRUCTURE** | Scene, panel/region, MRP application, and page/frame context | Start/end frame, still source, and temporal or spatial framing |
| **CONTROL** | Guide, ControlNet, composition constraints, and later regional controls | Pose, camera, motion, and applicable video controls |
| **OUTPUT** | Generate, job state, current Preview/Result, and History | Generate, job state, current Preview/Result, and History |

### 2.1 First-launch priority

The first launch normally has no useful result. The order of attention is:

1. Establish the intended subject and text.
2. Confirm the model and the small set of primary generation controls.
3. Make Generate obvious and available when the draft is valid.
4. Reserve a clear but compact place for the next result and its status.

An empty Preview must not become the visual hero of first launch. It can say
where the result will appear and may show a short next-step hint, while Create
retains the visual and cognitive priority.

## 3. Progressive disclosure

Disclosure follows author decisions rather than exposing every engine option at
once.

| Level | STATE | USER INTENT | VISIBLE INFORMATION | BEHAVIOR | RATIONALE |
| --- | --- | --- | --- | --- | --- |
| **PRIMARY** | Ready to draft | Supply the minimum valid generation intent | Model/checkpoint, prompt, negative prompt where supported, resolution or duration, and Generate | These controls are reachable without opening another section | A first-time author can produce a valid draft quickly |
| **SECONDARY** | Draft has context | Refine common domain choices | Sampler/scheduler, steps, CFG, seed, LoRA text/helper, CAST/reference, scene/frame/guide summaries | Sections expand in place and preserve the draft | Frequent controls stay available without overwhelming the first view |
| **ADVANCED** | Author requests control | Tune specialist behavior | Hires/upscale, detailed ControlNet/IPAdapter, presets, metadata, and future engine options | Details are explicitly opened and show their effect and availability | Rare controls should not compete with the generation path |

The disclosure state is UI state. It must not change the generation payload by
itself.

## 4. AUTHORING state

`AUTHORING` is the normal state before a new submission. It includes an empty
first launch and a draft edited after a previous result.

| STATE | USER INTENT | VISIBLE INFORMATION | BEHAVIOR | RATIONALE |
| --- | --- | --- | --- | --- |
| AUTHORING / no result | Prepare the first draft | Primary Create controls; compact empty-result affordance; no false completion status | Validate fields locally and expose Generate when the draft is acceptable | The absence of output is explicit, not mistaken for failure |
| AUTHORING / result exists | Change the next draft while retaining the last result | Current draft values, `previous result` label, and result metadata | Editing changes the draft only; the verified result remains inspectable | A useful result is evidence and should not disappear during iteration |

The current draft and the result that is being viewed are separate concepts. A
result records the immutable settings snapshot used for its job. Changing a
field never silently changes that record.

## 5. Dirty and ungenerated semantics

`dirty` means the draft differs from the last submitted or restored settings
snapshot. `ungenerated` means no accepted result exists for the current
workspace session. They are independent:

- a first draft is `ungenerated` and may be clean relative to its defaults;
- an edited draft after a result is `dirty` but has a valid previous result;
- restoring a history entry makes the draft clean relative to that entry and
  never starts a job;
- a failed submission leaves the draft dirty or clean according to its edits,
  while preserving the previous accepted result.

The UI should name the distinction in compact language such as “Draft
changed”, “No result yet”, and “Previous result”. It must not imply that dirty
means unsaved to a server unless persistence is actually implemented.

## 6. Generate relationship

Generate is the boundary between authoring and a job. It reads a validated
draft snapshot, creates one job through the domain's existing contract, and
immediately projects the returned job state. The action must be visually
obvious in the OUTPUT slot and remain reachable while Create is open.

The snapshot is immutable for that job. Generate must not mutate authoring
state, attach an implicit reference, change a seed, or fall back to another
model. A second submission during an active job requires an explicit future
queue policy; the initial model keeps one active submit per workspace and
guards against accidental double submission.

## 7. GENERATING transition

On activation, the workspace enters `GENERATING` as a visual transition while
the underlying job reports its precise status. The old accepted result remains
in Preview with a status overlay when one exists. The Create draft stays
editable, but the active job's snapshot is shown as the job context.

| STATE | USER INTENT | VISIBLE INFORMATION | BEHAVIOR | RATIONALE |
| --- | --- | --- | --- | --- |
| GENERATING | Know that work is active and what is being generated | Active status, job identifier, compact snapshot context, and previous result if present | Poll or subscribe using the existing domain route; do not invent progress | Continuity is more useful than a blank stage |
| GENERATING with edits | Prepare the next iteration without corrupting the active one | Draft controls remain visible and are marked changed when applicable | Edits affect only the next draft; Generate is guarded while the job is active | The author can think ahead without ambiguous concurrent ownership |

## 8. Generic status model

The product vocabulary projects engine-specific events into these ordered
states. A backend may omit a phase; the UI must not fabricate it.

`IDLE` → `QUEUED` → `PREPARING` → `SAMPLING` → `DECODING` → `PROCESSING` →
`SAVING` → `SUCCEEDED`

Any active state may transition to `FAILED`. A truthful indeterminate activity
indicator is allowed when only “running” is known.

| Status | Meaning | Minimum projection |
| --- | --- | --- |
| IDLE | No active job | Ready/idle label and available Generate when valid |
| QUEUED | Accepted but waiting | Queue position only if measured; otherwise “Queued” |
| PREPARING | Loading/conditioning/setup | Phase label, no made-up percentage |
| SAMPLING | Sampling is occurring | Real step/total if supplied; otherwise phase label |
| DECODING | Turning latent output into media | Phase label |
| PROCESSING | Domain post-processing | Phase label and real detail if supplied |
| SAVING | Persisting the result | Phase label |
| SUCCEEDED | Result accepted and retrievable | Result preview, metadata, and history entry |
| FAILED | Job or result failed | Error reason when known, retry/edit affordance, and prior result |

## 9. Status projection

There is one logical status and multiple projections:

- near Generate: the compact action and state summary;
- over Preview: phase or progress while protecting the previous image/video;
- below Create: queue and history context.

All projections derive from the same job record and timestamp. They must not
disagree about active/succeeded/failed state or claim a percentage that the
backend did not report.

## 10. RESULT_READY and result focus

`RESULT_READY` is a UI interpretation of a `SUCCEEDED` job whose media has been
retrieved and validated. It is not a new backend state.

### GLANCE

GLANCE is the ordinary post-submit view: a compact result, success/status
summary, and the next draft controls remain visible. It answers “did it work?”
quickly.

### RESULT_FOCUS

Clicking or an equivalent explicit action may enter in-place `RESULT_FOCUS`.
The media becomes easier to inspect while the Create context remains
perceptible. Focus is an attention state, not navigation to another page or a
mandatory modal viewer.

### Contextual information compression

When Focus expands the media, lower-priority controls may compress into a
summary containing, where applicable:

- prompt summary;
- model/checkpoint;
- seed;
- LoRA text or catalog names;
- CAST/subject and reference thumbnail;
- Scene, Region, Frame, Guide, or Shot name; and
- generation status and timestamp.

Compression hides detail temporarily; it does not discard it or change the
draft.

### Focus exit

The later implementation may choose click outside, Escape, an explicit close,
or an equivalent reversible gesture. Exit returns to the same Create draft and
result without reloading or generating.

### Provisional INSPECT

`INSPECT` is a future deeper detail state for metadata, zoom, pan, playback,
or diagnostics. It is provisional and must not be required for the first
Create implementation.

## 11. Edit-after-result loop

The normal loop is:

`RESULT_READY / GLANCE` → edit a draft field → `DIRTY AUTHORING` → Generate →
`GENERATING` → `RESULT_READY`.

The old result remains available until a new result is validated. A new success
then becomes the current result and moves the prior one to History. History
selection restores a settings snapshot only; it does not auto-generate or
replace an accepted current result until a new job succeeds.

## 12. Failure and previous-result preservation

Failure is a visible terminal state for the attempted job, not a destructive
reset of the workspace. The UI keeps:

- the failed job's status and actionable error;
- the current draft and its dirty/clean meaning; and
- the last validated result, clearly labelled as previous.

No failure path silently substitutes a model, strips prompt syntax, changes a
seed, or clears a reference. A retry, if offered later, must be an explicit
new submission after the failure is understood.

## 13. Manga/H3 horizontal mapping

The following table defines a shared place to look while retaining domain
meaning and runtime independence.

| Cognitive concern | Manga | H3 | Shared interaction expectation |
| --- | --- | --- | --- |
| Prompt | Scene/global or Generate prompt | Video/still prompt | Primary text field with concise help and validation |
| Model | Illustrious-compatible checkpoint | H3 model/checkpoint where applicable | Explicit model choice and availability state; no silent fallback |
| LoRA | Manual `<lora:name:weight>` and later catalog | Model/LoRA controls where supported | Text remains valid and visible; helper is progressive |
| CAST / subject reference | CAST identity, Character Instance, reference image, later IPAdapter | Subject/reference material and R2V frame inputs | Attachment card with preview, availability, replace/remove |
| Region / Frame | Scene, panel, Region, MRP target | Start/end frame, still source, shot framing | Spatial/temporal scope is labelled in domain terms |
| Guide / motion / camera | Rough Guide, ControlNet, composition | Motion, pose, camera, and video controls | Control slot explains what structure or motion it affects |
| Generate | Manga one-image or scene job | Video, still, or Prep/Edit job | Obvious action; one job snapshot; truthful active status |
| Preview | Validated PNG/image result, zoom/pan later | Validated still/video with playback as applicable | Stable container; result retained during the next job |
| Status | Manga job phase and validation | H3 job phase and media lifecycle | Same generic vocabulary projected from each engine's own state |
| History | Manga result/settings records and Restore settings | H3 recent results and Use settings | History is evidence and recall, never an implicit generate |

This is horizontal in interaction grammar, not a request to merge Manga and H3
routes, schemas, timelines, or supervisors.

## 14. Attachment Card grammar

An attachment card represents a selected subject, reference, frame, region, or
guide without claiming that all attachments have the same engine semantics.

| STATE | USER INTENT | VISIBLE INFORMATION | BEHAVIOR | RATIONALE |
| --- | --- | --- | --- | --- |
| Empty | Know what can be attached | Slot label, purpose, accepted media/type, and Add/Choose action | Open the domain-appropriate picker | The author understands scope before selecting a file |
| Attached | Confirm the selected material | Thumbnail/media preview, name, availability, and target/scope | Replace, remove, and (where supported) strength or settings | Selection is inspectable and reversible |
| Unavailable/invalid | Avoid an unsafe submit | Error or unavailable state with reason | Keep the value visible; block only the affected invalid submission or whole job according to domain contract | Missing material must not silently disappear or fall back |
| Focused | Review detail without leaving Create | Larger preview or compact metadata | Enter/exit reversible focus | Inspection should preserve authoring context |

## 15. Contextual help

Help is progressive and local:

1. **Label:** concise name in the relevant slot.
2. **Hint:** one sentence on what the control changes and when it applies.
3. **Detail:** expandable explanation of limits, validation, and engine effect.

Manga help should distinguish MRP (where/what), CAST/IPAdapter (who/appearance),
and ControlNet (structure/pose). H3 help should distinguish reference frames,
motion, camera, and video/still behavior. Hover may highlight or give a small
hint; it must not trigger a large layout reflow.

## 16. Model and LoRA placement

Model belongs in the PRIMARY model choice because it determines availability
and the interpretation of the draft. LoRA belongs in SECONDARY because it is a
common refinement but not required for a first valid generation. Manual LoRA
notation remains in the prompt path, with a helper/catalog as an optional
progressive aid. Unknown or unsupported notation stays visible and follows the
domain's fail-closed validation contract.

Multiple LoRAs remain representable. A catalog can expose names, weights, and
availability, but it must never make catalog selection the only way to express
`<lora:name:weight>`.

## 17. Static image and video

The cognitive map is shared; media behavior is not.

| Area | Static image | Video |
| --- | --- | --- |
| Output | One validated image with zoom/pan as available | Validated playable media with play/pause/seek as available |
| Space/structure | Resolution, page/panel, region | Duration, start/end frame, shot timing |
| Status detail | Sampling, decoding, saving image | Encoding, frame processing, saving video when reported |
| Focus | Inspect composition and metadata | Inspect playback and time position while retaining shot context |

The result shell may be related, but aspect ratio, controls, and status labels
must follow the media and engine.

## 18. Compact state flow

```text
FIRST LAUNCH
  -> AUTHORING (ungenerated, clean draft)
  -> AUTHORING (dirty when a field differs)
  -> Generate validation
       -> FAILED (draft retained; no prior result or prior result preserved)
       -> QUEUED -> PREPARING -> SAMPLING -> DECODING -> PROCESSING -> SAVING
            -> SUCCEEDED -> RESULT_READY / GLANCE
                                  -> RESULT_FOCUS -> focus exit -> GLANCE
                                  -> edit -> AUTHORING (dirty)
During any active job: previous validated result remains visible when present.
History selection -> draft snapshot restored; no automatic generation.
```

## 19. Current implementation mapping

This is a bounded source-reality check of the inspected entry points, not a
full repository audit.

| Finding | Classification | Current evidence / implication |
| --- | --- | --- |
| Manga has separate Generate and Authoring navigation | **ALREADY PRESENT** | `manga/app/index.html` exposes both surfaces and keeps the authoring canvas available |
| Manga Generate has stage, Create controls, status, and history | **ALREADY PRESENT** | `generation_view.js` and the Generate markup provide these boundaries |
| Manga preserves a validated previous result during a new job | **ALREADY PRESENT** | `generation_view.js` retains the previous preview and labels the active job |
| Manga Restore settings does not generate | **ALREADY PRESENT** | `generation_state.js` restores recorded values without submission |
| Manga checkpoint/prompt/negative/sampler/scheduler/steps/CFG/resolution/seed are explicit | **ALREADY PRESENT** | Generate form fields and compile path expose the PLAY1 contract |
| Manga wide stage/Create and narrow collapse exist | **PARTIAL** | CSS provides a two-column sticky stage and one-column breakpoint, but no explicit focus state |
| Manga scene/CAST/reference/instance context is available | **PARTIAL** | Authoring inspector has these controls; the Generate surface only summarizes some context |
| H3 has related Preview/Create/status/History grammar | **ALREADY PRESENT** | `h3/app/static/index.html` and `app.js` provide wide and narrow production views |
| In-place GLANCE → RESULT_FOCUS, contextual compression, and provisional INSPECT | **MISSING / FUTURE** | Existing views display results and history but do not implement this information state |

## 20. Open Astra questions

These questions intentionally remain open for a later visual and interaction
review. They must not be settled by implementation defaults in this model.

1. What column ratio keeps Create primary before the first result while giving a
   useful result enough room afterward?
2. Which aspect-ratio and size choices should appear as primary presets, and
   which should remain advanced?
3. How should portrait Manga pages and landscape/square H3 media share a stable
   container without wasting the first-launch view?
4. Should orientation be a direct control, a consequence of size presets, or a
   contextual choice per domain?
5. What focus expansion is sufficient for inspection without becoming a modal
   viewer?
6. Which transition animation communicates focus and generation while staying
   calm and accessible?
7. How much context should remain compressed in RESULT_FOCUS, and at what
   density should it expand?
8. Which controls belong in PRIMARY versus SECONDARY for a first-time Manga
   author?
9. Which status projections belong near Generate, Preview, and History at
   different widths?
10. What is the narrow-screen interaction for Create, Preview, and Focus when
    the user is editing during a job?
11. How should Manga and H3 accents express identity while remaining usable for
    color-blind and low-contrast conditions?
12. Which contextual-help triggers (hover, focus, click) are appropriate for
    touch and keyboard users?

## 21. Non-goals

- Choosing final sizes, aspect ratios, column percentages, colors, typography,
  animation curves, or branding.
- Implementing HTML, CSS, JavaScript, runtime, backend, or generation changes.
- Merging Manga and H3 generation state, schemas, timelines, or supervisors.
- Defining a new authoring persistence schema or changing existing contracts.
- Designing a full A1111 clone, gallery, editor, Assemble workspace, or timeline.
- Deciding model downloads, LoRA catalog storage, or engine-specific workflow
  internals.
- Treating provisional INSPECT or future IPAdapter/ControlNet/MRP detail as a
  first implementation requirement.

## 22. Decision boundary and next direction

This model freezes the information relationships and state vocabulary needed
for a future UI review. The next bounded step should ask Astra to critique
composition, density, hierarchy, motion, and narrow-screen behavior against
these semantics, without redefining the five slots or generation truth rules.
