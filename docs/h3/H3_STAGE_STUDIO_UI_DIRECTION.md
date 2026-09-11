# H3 Stage / Studio UI Direction

Status: `H3 INTERNAL DESIGN SSOT / DOCS ONLY`
Updated: `2026-09-11 JST`
Publication: `PUBLISHED ON MAIN`
Owner acceptance: `PENDING`
Studio implementation: `NOT AUTHORIZED`

This document records the H3-owned UI direction after H3-R1. It is a design
direction and vocabulary boundary, not a Studio specification, Timeline plan,
roadmap revision, or implementation authorization.

## 1. Authority and scope
The current direction is grounded in:

- [H3-R1 Stage / Generate report](reports/H3_R1_STAGE_GENERATE_VISIBILITY_REPORT.md)
- [H3 Product Integration Boundary](H3_PRODUCT_INTEGRATION_BOUNDARY.md)
- [Cross-Track Integration Plan](../integration/TEGAKI_CROSS_TRACK_INTEGRATION_PLAN.md)
- [H3 skin markup](../../h3/app/static/index.html)
- [H3 skin styles](../../h3/app/static/styles.css)

This document covers only H3 Stage, Inspector, Generate placement, and future
H3 Studio growth vocabulary. It does not decide runtime hosting, supervision,
Manga integration, or shared-shell implementation.

## 2. Direction classifications

| Classification | Meaning here |
|---|---|
| `VERIFIED BASELINE` | Observed in bounded H3-R1 implementation and Browser acceptance. |
| `ACCEPTED` | H3 direction retained as a product boundary; not an implementation grant. |
| `PREFERRED NEXT DIRECTION` | Next H3 refinement candidate, requiring its own Card and acceptance. |
| `FUTURE CANDIDATE` | Possible later concept whose controls and semantics are not defined. |
| `ALTERNATIVE` | Valid competing direction that is not the current preference. |
| `DEFERRED` | Intentionally excluded until a later need or feasibility result. |
| `NOT AUTHORIZED` | Must not be implemented from this document alone. |

## 3. VERIFIED BASELINE — H3-R1
H3-R1 is `CLOSED / PASS WITH LIMIT / VERIFIED BROWSER UI / PUBLISHED ON MAIN`.
Its bounded limitation was that `Submitting` was source/logic verified but too
transient for persistent Browser readback before the accepted Job advanced to
`Generating`. This does not reopen R1.

### Wide

- The existing Preview surface remains visible through bounded sticky behavior.
- Create/Inspector may be longer than the Stage.
- The single Generate action remains findable.
- Stage does not cover the topbar or History.

### Narrow

- `Create` and `Result` are separate scopes.
- `Create` is the initial view.
- An accepted submission may switch to `Result`.
- The user may manually return to `Create`.
- Completion does not steal the user's Result/Create intent afterward.

### Truthful status vocabulary

The H3 skin may communicate `Submitting`, `Queued`, `Generating`,
`Completed`, `Failed`, `Cancelled`, and `Disconnected`.

`Finalizing` is `NOT ADOPTED`. Fabricated percentage progress and unsupported
ETA language are `NOT ADOPTED`.

## 4. Owner observation after R1
R1 improved navigation and result visibility. In Wide layout, however, the
current sticky Generate dock occupies valuable upper Inspector space. That
space is better used for Prompt, Reference, generation settings, and future
creation controls.

Therefore the current Generate placement is `VERIFIED FUNCTIONAL` but `NOT THE
PREFERRED LONG-TERM WIDE PLACEMENT`. This is a refinement of the Wide
direction, not an R1 failure.

## 5. Stage and Inspector responsibility
Classification: `ACCEPTED`
Wide H3 has two different cognitive surfaces:

- `Stage`: what is currently being generated, viewed, or reviewed.
- `Inspector`: how the selected H3 generation or future Shot is configured.

The Stage remains the protagonist. The Inspector remains the configuration
surface. This distinction is H3-domain UI architecture; the future common
TEGAKI shell must not own its internal semantics.

## 6. Wide Generate placement
Classification: `PREFERRED NEXT DIRECTION`
Move the primary Generate action away from the upper Inspector and toward a
compact H3 Stage Action Bar placed above the Stage / Preview.

The right Inspector should begin directly with Prompt, Reference, and
generation settings. The space below the Stage remains a likely growth area
for a Shot strip, compact Timeline, Take strip, Storyboard navigation, or
other temporal surfaces. This direction is not implemented by H3-UXD1.

## 7. Stage Action Bar vocabulary

Conceptual structure:

```text
Stage Action Bar
  short active status
  primary Generate action

Stage / Preview
```

The near-term action is `Generate`. `Regenerate`, `Continue`, and Take-related
actions are `FUTURE CANDIDATE` vocabulary only, not control contracts.

The semantic separation is:

```text
Create / Inspector = defines what to generate
Stage action       = applies the current creation configuration to the Stage
```

Generate may move near the Stage in Wide layout without transferring Prompt,
Reference, or settings ownership away from Create.

## 8. Narrow Generate placement
Classification: `ACCEPTED`
Narrow keeps Generate inside Create. It must not move to Result merely to make
Wide and Narrow visually identical. The current model remains:

```text
Create -> accepted submission -> Result
```

Result remains primarily a viewing/result surface. There is one primary
Generate action; responsive placement may differ, but competing Generate
buttons must not be exposed at the same viewport width.

## 9. Future Studio growth — Candidate A
Classification: `PREFERRED INITIAL STUDIO GROWTH CANDIDATE`
Candidate A preserves the current two-column relationship while allowing
temporal controls to grow from the Stage:

```text
Stage / Preview | Inspector
                | Inspector
Shot strip /    |
compact Timeline|
```

It is preferred as the first growth path because it preserves the R1 mental
model, keeps Inspector continuously available, introduces temporal controls
progressively, and avoids full video-editor complexity before it is needed.
Do not implement the lower Shot/Timeline region from this document.

## 10. Future Studio growth — Candidate B
Classification: `ALTERNATIVE / DEFERRED`
Candidate B is:

```text
Stage / Preview | Inspector
--------------------------------
Full-width Timeline
```

Escalate to B only if real H3 editing needs require many Shots, multiple
temporal tracks, audio lanes, transitions, dense editing controls, or
substantial horizontal width. Conventional NLE precedent alone is not a
reason to choose it.

## 11. Create / Edit Inspector modes
Classification: `FUTURE CANDIDATE / DEFERRED`
Possible future Inspector modes are `[ Create ] [ Edit ]`. Create may contain
Prompt, References, and generation settings. Edit may eventually contain trim,
retime, continuation/edit-specific controls, and selected-Shot adjustments.
Do not create empty tabs or pre-build Edit architecture before editing
functionality exists. A future Shot mode requires real controls that justify
its additional cognitive surface.

## 12. Timeline and simple H3 modes
Timeline is not automatically the center of H3. The current Stage remains
useful without Studio, and Timeline should enter only when temporal multi-result
editing creates enough value.

Preserve `Video`, `Still`, and `Prep/Edit` as useful simple H3 modes before and
after Studio evolution. Simple generation must remain simple.

## 13. Research compatibility notes
Classification: `FUTURE CANDIDATE / NOT AUTHORIZED`
Future Create/Reference controls may eventually be compatible with research
candidates such as multi-image Character Reference Sets, motion-reference
assistance, or experimental fast-motion preprocessing/retiming. This document
does not define their semantics or authorize their features.

## 14. Audio position
Classification: `DEDICATED AUDIO PRODUCT DESIGN / DEFERRED`
If an adopted H3 implementation naturally produces or carries audio later,
TEGAKI may initially preserve that behavior. Do not define an audio mixer,
voice workflow, lip-sync system, audio Timeline tracks, pitch correction, or
audio retiming UX now.

## 15. Future Studio ownership
Classification: `ACCEPTED`
H3 owns the internal semantics of `Stage`, `Shot`, `Take`, `Timeline`,
`Storyboard`, `Create/Edit Inspector`, and H3 generation actions. The common
TEGAKI shell may host the H3 workspace, but it must not become the H3 editor or
own these domain semantics.

## 16. Cognitive-level principle

```text
Preserve the Cognitive Level.
Earn every slope.
```

Do not turn a simple generation tool into a full video editor until the user
actually enters editing work. Advanced Studio surfaces should appear
progressively when required by real work.

## 17. Near-term next H3 refinement
Classification: `PREFERRED NEXT IMPLEMENTATION SLICE`
Wide only:

- introduce a compact Stage-top Action Bar;
- move the single Generate action there;
- let the right Inspector begin with Prompt and creation controls;
- retain short truthful active status near Stage.

Narrow is `UNCHANGED` from R1. The Wide Stage-top Action Bar is
`IMPLEMENTED / VERIFIED` by H3-R1A, and the Narrow Create/Result contract is
preserved.

## 18. Runtime and cross-track non-scope
This H3 design SSOT does not decide or implement runtime supervisor, backend
switching, shared `8188`, Manga hosting, Manga implementation, shared-shell
implementation, cross-track History, cross-track asset handoff, Studio, Shot,
Timeline, LoRA, semantic R2V, Image Studio, or a new model.

Those boundaries remain governed by the [Cross-Track Integration Plan](../integration/TEGAKI_CROSS_TRACK_INTEGRATION_PLAN.md).
This document causes no Browser run, generation, runtime change, Manga change,
Astra action, or implementation change.

STOP.
