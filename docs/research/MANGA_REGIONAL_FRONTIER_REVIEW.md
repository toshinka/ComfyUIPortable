# Manga Regional Frontier Review

Status: bounded frontier-review consolidation, 2026-09-16
Evidence posture: the external findings in this document were supplied by the
Commander/WebGPT investigation for this Card. No new web research or source
copy was performed here. External behavior claims are therefore recorded as
SUPPLIED FINDING until a later local experiment or source review proves them.

## 1. Purpose and limits

This document compares the supplied regional-conditioning findings with the
current TEGAKI Manga Regional Prompting (MRP) contract. It records affinity,
tradeoffs, and a bounded experiment plan. It does not select a final engine,
change compile_regional_spec, add a runtime adapter, alter the authoring
schema, or authorize UI, graph, GPU, generation, or /prompt work.

The current TEGAKI owners remain authoritative. EasyReforge is a historical
behavior reference only; external implementations and UI are not copied.

## 2. MRP product intent

TEGAKI MRP favors LOW AUTHORING BURDEN. The first useful flow should allow:

- rough spatial placement;
- global/page stylistic continuity;
- local prompt influence;
- model discretion and useful randomness; and
- single-page or multi-panel generation without precise painted masks.

Initial MRP regions should act as soft spatial direction rather than strict
isolated cages. Stronger control can be layered later through Reference
Appearance, Guide/ControlNet, or specialized regional rendering. This review
does not redefine those existing semantic roles.

## 3. Current TEGAKI baseline

The current authority is compile_regional_spec in
custom_nodes_custom/tegaki_manga_nodes/scene_spec.py. It is a pure,
deterministic representation boundary. It accepts page/Scene context and an
ordered list of regional records, then preserves:

- an explicit stable region ID;
- canonical normalized area {x, y, w, h};
- positive prompt text;
- optional negative prompt text;
- optional strength in the existing bounded range;
- source order and page/Scene source IDs; and
- an OVERLAP_PRESENT warning with the involved IDs and source order.

The compiler deliberately stops before mask generation, conditioning,
attention policy, graph compilation, queue submission, and runtime execution.
It does not choose overlap precedence, feathering, normalization, an
Attention Couple policy, a RegionalSampler policy, or a ControlNet/IPAdapter
combination. The current bank classification remains BANKED_EXPERIMENTAL.

The lower-level regional contract is compatible with a later adapter because
the representation already separates global, Scene, and region scope. The
current AuthoringDocument bridge still does not invent arbitrary user-facing
subregions; that limitation remains in force.

## 4. Frontier candidate map

| Candidate | Supplied behavior / role | TEGAKI interpretation | Boundary and risk | Classification |
| --- | --- | --- | --- | --- |
| ComfyUI Core ConditioningSetArea, ConditioningSetAreaPercentage, ConditioningSetMask | Native conditioning transformations; percentage area uses x/y/width/height in 0..1; native strength and mask conditioning; set_cond_area can use default or mask bounds | The canonical TEGAKI rectangle maps naturally to percentage-area semantics and is the native primitive baseline | Core primitives do not establish a complete MRP policy, overlap precedence, or useful visual result by themselves | BASELINE / NATIVE AUTHORITY |
| ComfyUI-Inspire-Pack Regional Conditioning Simple / By Color Mask and regional helpers | Practical composition of native mask conditioning; regional prompt and regional IPAdapter helpers | Useful teaching/reference implementation; reinforces that MRP text and Reference Appearance can share geometry while retaining different meaning | Required dependency is not justified; helper composition does not become TEGAKI schema or authority | TEACHING / REFERENCE IMPLEMENTATION |
| Prompt Control Attention Couple | Hook-based attention regional prompting; prompt scheduling; normalized rectangular or multiple masks; feather and strength; global/base coexistence; negative COUPLE and optional negative batching | HIGH-AFFINITY runtime engine candidate for soft, coherent page direction | Supplied docs claim more flexibility than latent masking; overlap is per-pixel sum, not first/last precedence, and regions are not perfectly isolated | PRIMARY EXPERIMENTAL RUNTIME ENGINE CANDIDATE |
| EasyIllustrious IllustriousRegionalConditioning | Base/global conditioning plus regional mask, prompt, weight, start, and end; overlap normalization, blur, dilation, and chained regions; conditioning-only modification | HIGH-VALUE Illustrious reference for mask refinement and clean base/region composition | Do not inherit start/end semantics, blur/dilation defaults, or weight ranges without product/runtime evidence | ILLUSTRIOUS-SPECIFIC REFERENCE / POSSIBLE ADAPTER LESSONS |
| EasyIllustrious IllustriousAttentionCouple | Dynamic patching of discovered cross-attention module forward methods | Useful comparison material only | Different architectural hook boundary from Prompt Control; Illustrious branding is not evidence of a better engine | COMPARISON / REFERENCE ONLY FOR NOW |
| Impact RegionalSampler | Base sampling plus region-specific sampling each step; overlap_factor, restore_latent, and variation concepts | Useful for deliberate local rendering density, detail, or background enhancement | Independent sampling can weaken whole-page coherence and moves away from global-page-first MRP | SPECIALIZED OPTIONAL ENGINE / LATER EXPERIMENT |
| EasyReforge Manga Spatial / Attention behavior | BREAK slot composition, normalized rectangles, overlap modes, weights, and attention masking ideas | Historical behavior reference for slot, mask, and diagnostic concepts | No direct implementation reuse; inspected license status is not an authorization; Forge behavior does not prove ComfyUI behavior | HISTORICAL / BEHAVIOR REFERENCE ONLY |

References supplied with the findings are listed at the end of this document.

## 5. Three regional engine families

These families have different semantics, even when they consume similar
rectangles:

| Family | Primary operation | Expected advantage | Expected tradeoff for TEGAKI |
| --- | --- | --- | --- |
| Native mask / area conditioning | Attach area, mask, and strength metadata to conditioning | Smallest dependency surface and direct fit for canonical normalized area | Leaves overlap, feathering, and composition policy to the adapter |
| Attention coupling | Modify attention/conditioning behavior so global and regional signals coexist | Potentially coherent page-wide influence with soft boundaries and no repeated region sampling | Hook compatibility, overlap behavior, and IPAdapter coexistence need local proof |
| Regional sampling | Run base and region sampling passes and blend or restore latent state | Strong local rendering or detail control | More compute and possible loss of global page coherence; specialized rather than default MRP |

No family is declared a universal winner. A later experiment must keep the
compile records identical across routes.

## 6. Prompt-only CAST hypothesis

MRP may support a lightweight PROMPT CAST such as:

    Region A -> black-haired girl, school uniform

without requiring Reference Appearance, IPAdapter, ControlNet, or a precise
character mask. This is a product hypothesis, not a current taxonomy or
implemented CAST mode.

The useful future control ladder is:

1. PROMPT CAST — lowest authoring burden and highest generative freedom;
2. REFERENCE CAST — stronger appearance preservation;
3. GUIDE — stronger structural, pose, or composition control; and
4. REFERENCE + GUIDE — highest deliberate control.

The ladder is progressive. MRP must remain usable at the first level, and
users must not be forced to attach every control layer.

## 7. Global plus regional composition

TEGAKI prefers:

    PAGE / GLOBAL PROMPT + REGIONAL PROMPT

The global branch retains style, rendering language, page coherence, and
general manga qualities. A regional branch supplies local subject/content
direction. This is compatible with the current structured compile result and
appears structurally compatible with Attention Couple. Native conditioning
remains the comparison baseline.

The adapter must preserve global, Scene, and region scope. It must not flatten
regional semantics into one universal prompt string merely because the runtime
uses CLIP text nodes.

## 8. Overlap policy

Current TEGAKI behavior is frozen at:

    OVERLAP_PRESENT warning only

compile_regional_spec must continue to report the involved IDs and order
without choosing a winner.

The supplied frontier policies are different runtime candidates:

| Candidate | Supplied overlap policy | TEGAKI status |
| --- | --- | --- |
| Prompt Control Attention Couple | Per-pixel mask normalization by sum; no first-wins or last-wins precedence | Candidate for a soft shared influence model |
| EasyIllustrious Regional Conditioning | Optional overlap normalization, with mask refinement options | Reference for a future Illustrious adapter |
| Impact RegionalSampler | Sampling/blend semantics including overlap_factor and latent restoration concepts | Specialized later experiment |

Recommended future experiment: feed the same TEGAKI regional compile records
to each route and compare overlap behavior. Do not encode any one policy into
compile_regional_spec.

## 9. Mask burden and escalation

Basic MRP should begin with simple normalized rectangles. Precision is an
optional escalation:

    RECTANGLE
      -> generated simple mask
      -> user-refined mask
      -> Guide-derived mask
      -> other spatial sources later

Precise painted masks must not become a prerequisite for prompt-only CAST or
ordinary page generation. A future adapter may refine the rectangle, but it
must retain the source scope and normalized target.

## 10. ControlNet relationship

MRP / Regional answers:

    what content should appear where

Guide / ControlNet answers:

    structure / pose / composition / geometry

A future rough-comic or ControlNet workflow may reinforce spatial structure,
but it must not replace MRP. The supplied Reddit workflow is a REFERENCE
WORKFLOW PATTERN only, not architecture authority.

Current coexistence classification:

    PLAUSIBLE / NEEDS EXPERIMENT

The semantic separation is sound, but the actual product graph, model
compatibility, ordering, VRAM cost, and failure behavior remain unmeasured.

## 11. Reference Appearance relationship

The future architecture should allow each of these independently:

- MRP only;
- MRP + Reference Appearance;
- MRP + Guide; and
- MRP + Reference Appearance + Guide.

No route should require all layers. MRP remains the spatial text layer,
Reference Appearance remains the who/appearance layer, and Guide remains the
structure/pose/geometry layer.

### IPAdapter coexistence

Current classification:

    UNKNOWN / NEEDS EXPERIMENT

Prompt Control Attention Couple and TEGAKI IPAdapter Advanced both interact
near attention behavior, but that does not prove either compatibility or
incompatibility. The first bounded comparison should use the current
product-derived graph and compare:

1. MRP alone;
2. Reference Appearance alone; and
3. MRP + Reference Appearance.

No claim of identity isolation or final appearance quality follows from the
frontier findings.

## 12. Illustrious compatibility

The supplied classifications are:

- ComfyUI native conditioning: MODEL-GENERAL;
- Prompt Control: strong SDXL-family relevance; and
- EasyIllustrious: explicitly Illustrious-focused.

TEGAKI product compatibility of any new runtime engine is NOT PROVEN until a
local GPU test uses the intended Illustrious checkpoint and product-derived
graph. Documentation, naming, or ecosystem branding cannot substitute for
that evidence.

## 13. Performance and VRAM

The supplied Attention Couple description suggests lower conceptual overhead
than repeating whole regional sampling passes. This is a hypothesis, not a
TEGAKI performance result.

The following remain unmeasured on the target class of hardware:

- RTX 4070 12 GB headroom;
- 1024-class Manga resolution;
- the current region bound;
- IPAdapter enabled versus disabled;
- region count and overlap; and
- end-to-end generation time.

Any later runtime experiment must record peak VRAM, generation time, region
count, image dimensions, and IPAdapter on/off. No performance claim is made
before that evidence exists.

## 14. Contract preservation and adapter boundary

The following TEGAKI contracts remain stable:

- compile_regional_spec and its deterministic diagnostics;
- canonical normalized geometry {x, y, w, h};
- structured global / Scene / region semantics;
- independent Manga runtime ownership; and
- MRP, Reference Appearance, and Guide semantic separation.

A future adapter may translate TEGAKI regional records to native conditioning,
Prompt Control, EasyIllustrious regional conditioning, or another tested
engine. Canonical AuthoringDocument must not expose external syntax such as:

- COUPLE(...);
- MASK(...); or
- AREA(...).

External engine fields such as start/end scheduling, blur, dilation, weight
ranges, overlap precedence, or negative batching remain adapter-level choices
until separately owned and tested. No authoring-schema addition is needed for
this review.

## 15. Engine classification

| Engine or family | Current classification | Why |
| --- | --- | --- |
| ComfyUI Core | BASELINE / NATIVE AUTHORITY | Native area, percentage-area, mask, and strength primitives |
| Inspire Pack | TEACHER / REFERENCE | Shows practical composition of native mask conditioning and related IPAdapter helpers |
| Prompt Control Attention Couple | PRIMARY EXPERIMENTAL RUNTIME ENGINE CANDIDATE | Best current affinity with soft global-plus-region MRP intent; local hook and VRAM proof still required |
| EasyIllustrious Regional Conditioning | ILLUSTRIOUS-SPECIFIC REFERENCE / POSSIBLE ADAPTER LESSONS | Useful regional conditioning, overlap, and mask-refinement ideas |
| EasyIllustrious Attention Couple | REFERENCE ONLY FOR NOW | Dynamic attention patching is a comparison point, not a selected architecture |
| Impact RegionalSampler | SPECIALIZED OPTIONAL ENGINE | Useful for later detail or local rendering experiments |
| EasyReforge | HISTORICAL / BEHAVIOR REFERENCE ONLY | Concepts may inform comparison; implementation and license are not reused |

## 16. Future GPU experiment matrix

No experiment is run by this Card. A later Owner/runtime Card should keep the
following variables identical across routes:

| Fixed input | Required value |
| --- | --- |
| Checkpoint | Same Illustrious-compatible checkpoint |
| Seed | Same explicit seed |
| Prompt | Same global and regional prompt text |
| Regional specification | Same compile_regional_spec output, including IDs/order/areas |
| Resolution | Same width and height |

### Routes

| Route | Engine | Purpose |
| --- | --- | --- |
| BASELINE | Current TEGAKI regional path / native product route | Establish current behavior and resource cost |
| A | Native mask/area conditioning | Measure the smallest native adapter |
| B | Prompt Control Attention Couple | Test the primary soft-coherence candidate |
| Optional C | Impact RegionalSampler | Test specialized local-rendering behavior |

### Required scenes

- two prompt-only characters;
- two overlapping regions;
- global style plus local characters;
- background plus foreground;
- a negative regional prompt;
- Reference Appearance coexistence; and
- Guide/ControlNet coexistence in a later separate comparison.

### Metrics

- visual regional adherence;
- page coherence;
- attribute bleed;
- useful randomness;
- prompt-only CAST quality;
- elapsed generation time; and
- peak VRAM.

The same product-derived graph and output authority must be used where a route
supports them. A failed or unavailable route remains a finding; it must not
silently fall back to another engine.

## 17. Decision state

Current decision:

    NO ENGINE REPLACEMENT YET

TEGAKI Regional Compile remains valid and remains the engine-neutral contract.
Prompt Control Attention Couple deserves a future product-derived GPU
experiment. ComfyUI Core, Inspire, and EasyIllustrious remain valuable design
teachers/reference implementations. Impact RegionalSampler remains optional
specialized research.

No external technology is declared superior, and no current TEGAKI capability
is declared obsolete.

## 18. MRP product principle

Use the smallest spatial instruction that provides useful direction, preserve
model creativity and page coherence, and add stronger control layers only when
the author asks for them.

This is a frontier-review conclusion, not a UI layout instruction.

## 19. Next frontier domain

NEXT FRONTIER DOMAIN:

    GUIDE / CONTROLNET / STRUCTURAL CONTROL ECOSYSTEM

That research is not performed in this Card. The next review should preserve
the Guide authoring boundary, canonical asset identity, normalized target
geometry, strict resource resolution, and separate MRP/Reference semantics.

## 20. References

### Current TEGAKI sources

- custom_nodes_custom/tegaki_manga_nodes/scene_spec.py
- docs/manga/MANGA_MRP_CAPABILITY_RECONCILIATION.md
- docs/architecture/TEGAKI_CAPABILITY_BANK_CHECKPOINT.md
- docs/architecture/TEGAKI_CAPABILITY_COMPATIBILITY_MAP.md

### Supplied external references

- https://github.com/Comfy-Org/ComfyUI
- https://docs.comfy.org/built-in-nodes/ConditioningSetMask
- https://github.com/ltdrdata/ComfyUI-Inspire-Pack
- https://github.com/asagi4/comfyui-prompt-control
- https://github.com/asagi4/comfyui-prompt-control/blob/master/doc/attention_couple.md
- https://github.com/asagi4/comfyui-prompt-control/blob/master/doc/regional_prompts.md
- https://github.com/regiellis/ComfyUI-EasyIllustrious
- https://github.com/comfyorg/comfyui-impact-pack
- https://www.reddit.com/r/comfyui/comments/1lbcud8/accidentally_created_a_workflow_for_regional/

These links are recorded from the supplied investigation. This Card did not
perform independent internet research.
