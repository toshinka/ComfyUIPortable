# LOW-PRIORITY RESERVE INDEX

> **STATUS: LOW-PRIORITY RESERVE**
> **NOT CURRENT ROADMAP**
> **NOT IMPLEMENTATION AUTHORITY**

This index salvages previously documented ideas whose product value is known
but whose implementation is intentionally deferred. It is safe to leave
incomplete. It does not create Capability Bank Phase 2, change the current
roadmap, or authorize UI, runtime, network, or generation work.

Capability Bank Phase 1 remains **4**. The four banked capabilities are not
duplicated here. Reserve files are documentation only and are never imported,
executed, registered, served, or referenced by production code.

## Scoring

Scores are within this low-priority reserve only. The tuple in the Score
column is **product value / preparation value now / future reuse / prerequisites
ready / low implementation risk**, with maxima **30 / 25 / 20 / 15 / 10**.

Bands: **R1 PREP-WORTHY** (75–100), **R2 KEEP READY** (60–74), **R3 PARK**
(40–59), and **R4 ASTRA / PREREQUISITE BLOCKED** (0–39).

## Ranked reserve candidates

| Rank | Capability | Score | Band | Why retained | Primary blocker | Safe preparation level | Likely future domain |
| ---: | --- | ---: | --- | --- | --- | --- | --- |
| 1 | Prompt / Settings Import Proposal | **84 (25/20/18/13/8)** | R1 | Turns recovered result context into a reviewable reuse proposal | Explicit apply semantics, provenance, and safe field allowlist | Read-only proposal contract and fixtures; never apply | Manga result/history adapter |
| 2 | Guide / ControlNet preparation | **78 (24/20/17/10/7)** | Preserves a safe structure/pose/geometry boundary before generation | Guide semantics, preprocessors, and ControlNet capability policy | Control specification and validation only | Manga Guide/ControlNet adapter |
| 3 | Model / LoRA metadata enrichment | **74 (22/15/17/12/8)** | Makes strict catalog entries explainable without changing identity | Header formats and metadata authority | Typed field contract and read-only fixtures | Local model/LoRA service |
| 4 | Wildcard Editor / safe persistence service | **72 (20/16/16/12/8)** | Preserves a future writable utility around the banked expansion core | File schema, path policy, and explicit write UX | Validate-before-save contract only; no files written | Manga prompt utility |
| 5 | Result-to-Asset identity/conversion | **70 (24/13/18/9/6)** | Keeps generation provenance available for later reuse | Asset model and Assemble ownership | Provenance mapping notes only | Asset/Assemble adapter |
| 6 | H3 Frame / Time helpers | **69 (20/15/17/10/7)** | Makes frame, time, duration, and playback values consistent | H3 timebase/FPS decision | Pure field vocabulary and fixtures | H3 media core |
| 7 | Media / Shot asset metadata | **67 (21/13/17/9/7)** | Links a result to a shot, take, duration, and media type | Asset/Assemble identity decision | Metadata vocabulary only | H3/Assemble media service |
| 8 | H3 video reference preparation | **64 (22/12/16/8/6)** | Validates subject/reference media before an H3 job | H3 reference semantics and safe media policy | Read-only media contract only | H3 reference adapter |
| 9 | Timeline handoff metadata | **53 (17/7/17/6/6)** | Preserves a future handoff to downstream editing | Separate Assemble/workflow handoff decision | Field list and ownership note only | Assemble adapter |
| 10 | H3 future reference/control family | **52 (23/4/18/3/4)** | Retains multi-reference, Start/End, continuation, and pose/outfit/camera concepts | H3 product policy and capability maturity | Taxonomy only | H3 generation domain |
| 11 | Civitai-style model/LoRA helper/provider | **47 (18/5/16/3/5)** | Preserves optional metadata-provider value without a hard dependency | Network, provider, privacy, and credential decisions | Local identity/provider interface note only | Optional metadata service |
| 12 | PreviewFocus visual implementation | **45 (27/4/10/1/3)** | Keeps the proven visual goal visible for Astra review | Composition, density, motion, and responsive behavior | Existing contracts only; no implementation file | Astra UI composition |
| 13 | Final AttachmentCard visual system | **43 (25/3/11/1/3)** | Preserves a shared visual grammar candidate | Astra comparison and domain emphasis | Existing contracts only; no implementation file | Astra UI composition |
| 14 | 3D previs / pose bridge | **39 (16/3/14/2/4)** | Retains a possible pose/camera-to-Guide bridge | Guide semantics are not mature and implementation is undecided | Responsibility note only | Future Guide/ControlNet adapter |

Individual reserve boundaries exist for ranks 1–8. Ranks 9–14 remain compact
parked entries because their prerequisites or Astra decisions are not ready.
The visual ranks intentionally point to existing UI contracts rather than
duplicating them.

## Reserve rules

All entries are **NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION**. A future
Card must establish the owner, exact input/output, side effects, tests, and
domain boundary before any code begins. Manga and H3 runtimes, schemas,
timelines, and generation state remain separate.
