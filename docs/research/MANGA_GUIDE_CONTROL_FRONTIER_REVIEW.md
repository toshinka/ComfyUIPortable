# Manga Guide / Control Frontier Review

Status: bounded frontier review, 2026-09-16 JST
Evidence posture: this note consolidates the supplied WebGPT findings and the
current repository boundary. It adds no new internet research, runtime work,
GPU generation, model download, or product implementation.

## 1. Purpose and limits

The Manga Guide concept needs a clear boundary before a future Astra decision.
This document compares the relevant control layers, records what is already
proven locally, and identifies bounded experiments. It is a decision substrate,
not an implementation card. Authoring schema 1.0.0, Manga runtime lifecycle,
H3/Manga separation, and existing prepare semantics remain unchanged.

## 2. Current Manga semantics

Guide is responsible for structure, pose, composition, geometry, and panel
guidance: it answers where structure should be and how it should be arranged.
MRP (Manga Regional Prompting) answers where and what text applies, including
panel, Scene, region, background, and character content. Reference Appearance answers
who or what appearance is referenced. CAST owns identity prompt and reference
assets; Character Instance / Figure refers to a CAST. LoRA remains a learned
modifier that may be represented in prompt text.

These concepts are complementary:

| Concept | Responsibility | Current owner |
| --- | --- | --- |
| Guide | structure, pose, composition, geometry | TEGAKI authoring and Guide bridge |
| MRP | where/what text applies | TEGAKI regional composition |
| Reference Appearance | who/what appearance to reference | CAST and future IP-Adapter path |
| LoRA | learned modifier | prompt notation and backend compilation |

Guide must not become a second MRP or a replacement for Reference Appearance.

## 3. Current TEGAKI baseline

The current source is RUNTIME_CONNECTED for one qualified global guided route. The route is
selected for an enabled rough_manga Guide with valid figure geometry, then
builds a deterministic Guide image and applies it through ControlNetLoader and
ControlNetApplyAdvanced. The current application settings are strength 0.75,
start 0, end 1, and advanced_controlnet false. This is a runtime-connected
baseline, not a generalized semantic Guide catalog; that catalog is not productized.

The bridge emits safe rough_manga Guide assets and placement/figure areas. It
does not forward arbitrary raw rasters. The generation Guide bridge currently
renders a deterministic flat-silhouette image and marks the target GLOBAL.

Still unresolved:

- semantic control kind (for example POSE or LINE) and its normalization;
- a strict ControlNet model catalog and capability authority;
- preprocessor ownership and submit-time validation;
- a normalized control specification;
- multi-Guide composition and runtime adapter behavior;
- spatial scope and mask semantics beyond the current global route.

## 4. Control stack model

Future work must keep these layers distinct:

1. Guide authoring/source: durable Guide records, placement, and authoring
   operations.
2. Preprocessor: converts an image or structured input into a control image or
   control data.
3. Semantic Guide kind: TEGAKI vocabulary such as POSE, LINE, DEPTH, or EDGE.
4. Control model: a ControlNet or Union model that consumes the control.
5. Control application engine: nodes that attach the control to a diffusion
   graph and expose strength/timing/effect behavior.
6. UI/composition: the user-facing Guide controls and composition editor.

controlnet_aux, Advanced-ControlNet, Union, and a Pose Editor occupy different
layers. Their names must not be treated as interchangeable capabilities.

## 5. ComfyUI Core baseline

ComfyUI Core supplies the native runtime baseline through ControlNetLoader and
ControlNetApplyAdvanced. The latter already covers strength, start_percent, and
end_percent. Set Union ControlNet Type is also a core node with the listed
union types. The classification for this layer is NATIVE RUNTIME BASELINE.

Core is the default application candidate for the first future Manga Guide
route. It is sufficient for ordinary global strength and timing. A future
adapter must still resolve the model and validate node availability at submit
time.

## 6. controlnet_aux

controlnet_aux is an active preprocessor provider, not a semantic authority. The
supplied findings cover pose, lineart, anime/manga line, depth, edge, normal,
and segmentation families. It is a REFERENCE CANDIDATE for the preprocessor
layer. TEGAKI should own the semantic Guide kind and map that kind to a
provider capability.

DWPose is a promising structured pose/keypoint path for a later experiment. It
does not authorize an implementation or a new authoring schema in this phase.

## 7. Preprocessor product abstraction

The product-facing vocabulary should describe intent, while provider names
remain replaceable. Candidate high-level kinds are POSE, LINE, DEPTH, and EDGE,
with NORMAL or SEGMENT as later candidates. A basic UI can expose the semantic
kind and a small set of safe options. Advanced provider options may be
progressively disclosed only after capability validation; the final Astra
composition is intentionally undecided.

Possible dependency strategies are:

- A: use controlnet_aux as the broad provider;
- B: ship or call dedicated preprocessors for selected kinds;
- C: implement only trivial TEGAKI-native preprocessing where quality is
  sufficient.

The cost and maintenance trade-off remain open. No strategy is selected here.

## 8. Advanced-ControlNet

Advanced-ControlNet is an optional advanced application backend. The supplied
findings include timestep and latent behavior, effect masks, custom weights,
soft weights, sliding context, multi-control, and reference modes. These are
separate from ordinary Core strength/start/end controls.

Core remains the default candidate. Advanced-ControlNet should be introduced
only when a bounded requirement, such as spatial effect masks or temporal
behavior in another product, is proven. Using Advanced merely to duplicate
Core strength/start/end would add unnecessary coupling.

## 9. Spatial Guide scope

Future spatial scope can reuse canonical area geometry:

area { x, y, w, h } -> geometry-to-mask -> Guide scope -> optional Advanced
effect mask.

Shared geometry does not mean Guide equals MRP. MRP still controls regional
text semantics; Guide scope controls structural conditioning. A precise mask is
optional and must not be required for a first global Guide experiment.

## 10. Union ControlNet

Union ControlNet, including the Xinsir Union SDXL family, is a high-value
model-layer experiment candidate. The product should map a TEGAKI semantic
Guide kind to an adapter/model capability. It must never hard-code a rule such
as POSE equals Union type 0 without a verified model contract.

One Union model supporting multiple condition kinds may reduce model switching,
but the claimed multi-control fusion savings are unproven for the local
Illustrious Manga setup. Union versus specialized ControlNet remains open.
Illustrious compatibility and Manga quality are UNKNOWN until a bounded local
GPU experiment.

## 11. Model-layer and apply-layer choices

The actual competition is two separate decisions:

| Layer | Candidates | Current position |
| --- | --- | --- |
| Control model | Union versus specialized ControlNet models | open; evaluate locally |
| Apply engine | Core versus Advanced-ControlNet | Core default; Advanced only when justified |

There is no monolithic extension winner. A composable stack keeps replacement
possible and lets a semantic Guide stay stable while providers or models
change.

## 12. Authoring and previs references

Eric Composer Studio and OpenPose Editor are authoring/previs references. They
are useful for rough layout, keypoint editing, and panel planning, but they do
not own the Manga runtime or resource catalog. Their interaction ideas must be
translated into TEGAKI authoring and validated against the existing schema.

The long research path is:

panel layout -> rough composition -> pose/depth/line Guide -> ControlNet ->
MRP -> optional Reference Appearance -> Manga generation.

This is long-path research and is not a commitment to implement every stage.

## 13. Guide control pipeline

The conceptual pipeline is:

Guide source -> optional preprocessor -> semantic kind -> normalized control
spec -> strict model/resource resolution -> apply engine -> generation.

The normalized control spec should eventually carry validated semantic kind,
resolved model identity, control image/data, strength/timing, and optional
scope. It must be produced without changing authoring 1.0.0 until a minimal
additive field is separately approved. Unknown or ambiguous resources should
fail closed.

## 14. Authority separation

The intended authority map is:

| Decision | Authority |
| --- | --- |
| Semantic Guide kind | TEGAKI |
| Preprocessor capability | provider catalog, revalidated at submit |
| Control model identity | strict server-owned model catalog |
| Union internal mapping | Union adapter/model contract |
| Application behavior | selected Core or Advanced engine |
| Composition and disclosure | Manga UI/product contract |

This avoids a giant Guide catalog that mixes authoring semantics, provider
names, model files, and node details.

## 15. Current duplication and competition map

controlnet_aux, a ControlNet model, and a Core/Advanced apply node are mostly
complementary. Union versus specialized models is a model-layer choice.
Core versus Advanced is an apply-layer choice. Authoring tools are a separate
previs layer. Treating all of them as competing extensions would obscure the
actual decisions.

## 16. Affinity with MRP

The useful control ladder is:

1. MRP only;
2. MRP plus Reference Appearance;
3. MRP plus Guide;
4. MRP plus Reference Appearance plus Guide.

The first Guide experiment should keep precise structural input optional and
measure whether structural adherence improves without erasing regional prompt
meaning.

## 17. Affinity with Reference Appearance

Guide and Reference Appearance have high conceptual affinity: Guide supplies
structure while Reference supplies appearance. Their actual runtime
coexistence, ordering, and VRAM cost require a bounded GPU test. CAST remains
the identity owner, and IP-Adapter remains a future appearance adapter; Guide
must not absorb either responsibility.

## 18. Affinity with H3

H3 advanced video and sliding-context concepts are useful conceptual research
only. They do not authorize a shared runtime, shared timeline, or shared
generation state. Manga and H3 remain independent engines and adapters.

## 19. Astra decision substrate

Astra should receive bounded questions rather than a preselected architecture:

- Is any proposed layer redundant with the existing Core route?
- What evidence justifies Advanced-ControlNet?
- Should Core remain the default application engine?
- Should Union be the first model-layer experiment or follow a specialized
  baseline?
- Which semantic kinds belong in the initial product vocabulary?
- Which Advanced settings, if any, deserve disclosure?
- Which provider details must stay hidden behind capability resolution?
- Does the composition fit the current Manga workspace and UI principles?
- Which work should be deferred until a GPU result exists?

The later Astra review should return at most eight findings, five
keep/defer/drop decisions, three dependency concerns, three semantic-vocabulary
recommendations, and exactly one bounded Guide experiment.

## 20. Fixed inputs and output boundary

The fixed inputs for that decision are:

- Guide is not MRP;
- Guide is not Reference Appearance;
- canonical area geometry may be reused;
- precise masks are optional;
- Manga and H3 remain separate;
- TEGAKI owns semantic Guide vocabulary;
- providers and model files are replaceable behind catalogs;
- Illustrious quality is unproven;
- UI follows the existing progressive-disclosure principles.

The output is a product-selection decision and one bounded experiment. It is
not a request to change the authoring schema, runtime lifecycle, H3, or
generation API during this review.

## 21. Future GPU experiment matrix

No experiment is performed in this review. A later owner-approved matrix can
compare:

| Case | Route |
| --- | --- |
| A | current global Guide baseline |
| B | Core plus a common specialized ControlNet |
| C | Core plus Union ControlNet |
| D | Advanced only where spatial scope requires it |

Candidate conditions are POSE, LINE/rough manga, DEPTH, and optional EDGE.
Later coexistence cases are Guide plus MRP, Guide plus Reference Appearance,
and Guide plus MRP plus Reference Appearance. Compare structural adherence,
Manga style retention, face/character quality, page coherence, overconstraint,
useful randomness, elapsed time, and peak VRAM. If scope is tested, compare a
whole-page Guide against one-region application.

## 22. Current frontier conclusion

The recommended shape is a composable stack: TEGAKI-native semantic Guide
vocabulary, a replaceable preprocessor provider (with controlnet_aux as a
candidate), strict model/resource resolution, ComfyUI Core as the baseline
apply engine, optional Advanced-ControlNet for proven spatial or advanced
needs, and Union as a high-value model-layer experiment. Authoring and previs
references stay separate from runtime authority. Final selection is deferred
until the bounded GPU evidence exists.

## 23. Relationship to the compatibility map

The existing capability compatibility map remains the repository index for
what is known, unknown, or deferred. This document supplies the external
technology comparison and decision questions; it does not replace that map or
claim that an untested capability is available.

## 24. Status and file boundary

This is a docs-only frontier note. It does not modify product source, tests,
fixtures, authoring schema, runtime, UI, model files, or status checkpoints.
The historical reconciliation document remains the pre-frontier baseline and
now points here for current comparison.

## 25. Validation and commit

Validation for this bounded pass is limited to worktree/status checks,
two-file scope checks, and git diff --check. No runtime, GPU, generation,
/prompt call, model download, dependency installation, or new internet
research is performed.

Suggested local commit:

docs: record Manga Guide control frontier review

Push is forbidden for this pass.
