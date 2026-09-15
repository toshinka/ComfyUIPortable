# Manga MRP Capability Reconciliation

Status: bounded pre-Astra responsibility decision (2026-09-16)

This document defines the smallest TEGAKI-owned Manga Region Prompting
capability that can survive a later Astra UI pass. It is an audit and a
boundary decision; it does not add a product node, a route, a canvas, or a
generation graph.

Evidence is labelled **PROVEN** when the current source or the bounded
reference files directly show the behavior, **PLAUSIBLE** when the ownership
is a safe architectural consequence but the runtime effect is not established,
and **UNKNOWN** when the overlap or visual result needs an experiment.

## CURRENT ARCHITECTURE

The persistent authority is `TEGAKI_AUTHORING_DOCUMENT` version `1.0.0`,
defined in `custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py`. The
contract keeps semantic Scene regions and Visual Panel Frames in separate ID
spaces and uses page-normalized rectangular `area` values. A page contains
`scenes`, optional `cast`, `character_instances`, `guides`, and visual frames.
Character instance areas are page-normalized; Guide/frame geometry remains a
separate structural/presentation concept.

The current execution path is layered:

1. `authoring_execution_bridge.py` validates the document, requires 1–6
   scenes, sorts them by `order`, and compiles each Scene to one active panel
   in `PAGE_COMPILE_PLAN` v1. The panel carries the Scene `prompt`,
   `negative_prompt`, and geometry. In the current AuthoringDocument bridge,
   the emitted panel `local_regions` list is empty; the bridge therefore does
   not invent a second user-facing region model.
2. The same bridge compiles a CAST-backed `character_instance` to a character
   record containing identity/acting prompts, `reference_asset`, page area,
   stable instance metadata, and optional spatial hints. Visual frames are
   explicitly excluded from semantic Scene conditioning.
3. `scene_generation.py` is compile-only. It validates the catalog and
   request, calls the bridge, validates the resulting page plan, and builds a
   small graph containing `TegakiMangaPagePlanFromJSON`,
   `TegakiMangaConditioningBuilder`, the core sampler, decode, and SaveImage.
   It does not load a model or queue a prompt while compiling.
4. `page_plan_adapter.py` is a transport boundary: JSON is parsed and checked
   by `validate_page_compile_plan`; it owns no prompt semantics.
5. `scene_spec.py` and `scene_compiler.py` provide the older/lower-level
   `REGION_SPEC`/`COMPILE_PLAN` contracts. They already validate panel-local
   `local_regions` with prompt, negative prompt, and normalized `area`, and
   preserve structured character and LoRA records.
6. `TegakiMangaMaskBuilder` builds independent page-sized panel, character,
   and local-region masks. It projects panel-local areas to page pixels and
   can apply a bounded Gaussian `mask_feather` value. Its debug output keeps
   the source scope and projected bounds visible.
7. `TegakiMangaConditioningBuilder` encodes global, panel, local-region, and
   character text separately, then attaches masks using ComfyUI's conditioning
   metadata. It exposes `panel_strength`, `local_region_strength`,
   `character_strength`, and `mask_feather` without flattening all scopes into
   one required prompt string.
8. `TegakiTwoRegionCoreConditioner` is a bounded A/B oracle for two normalized
   regions with region prompts, optional region negatives, independent
   strengths, and masks. `layout_region_bridge.py`,
   `layout_aware_conditioning.py`, `impact_region_plan.py`, and
   `manga_impact_regional_adapter.py` are domain adapters for more advanced
   layouts; they must not be treated as a universal runtime graph.

Current MRP-like ownership is therefore:

- **Where prompt applies:** `Scene.prompt`/`negative_prompt` and lower-level
  `REGION_SPEC`/`local_regions`; the conditioning builder applies the
  corresponding panel or local mask.
- **Where character placement lives:** page `character_instances[].area`,
  linked by `cast_id` and `scene_id`; the execution bridge projects this to the
  compiled character record.
- **Where masks are built:** `TegakiMangaMaskBuilder` for page/panel/local/
  character masks and `TegakiTwoRegionCoreConditioner` for its A/B oracle.
- **Where conditioning is compiled:** `authoring_execution_bridge.py` and
  `scene_compiler.py` create structured plans; `TegakiMangaConditioningBuilder`
  and the Impact regional adapter materialize conditioning branches.
- **Where overlap/feather exists:** normalized rectangular masks and Gaussian
  feather are implemented in the mask builders. A single authoritative MRP
  overlap precedence rule is not implemented or proven.

The Scene relationship is **PARTIAL_OVERLAP**. A Scene already supplies the
most important MRP pair, `prompt + area`, and its page ordering is a useful
stable scope. It does not currently expose arbitrary per-Scene subregions on
the canonical AuthoringDocument execution path; the lower-level compile model
has `local_regions`, but that is not a reason to create a parallel authoring
document. MRP should add a compile-time regional specification/validation
layer and, only when authorized, a minimal additive authoring extension.

## EASYREFORGE MRP

The read-only inspection was limited to:

- `D:\\GitHub\\tegaki\\関連ツール\\EasyReforgeExtension\\scripts\\manga_prompter.py`
- `D:\\GitHub\\tegaki\\関連ツール\\EasyReforgeExtension\\scripts\\manga_spatial_engine.py`
- `D:\\GitHub\\tegaki\\関連ツール\\EasyReforgeExtension\\scripts\\manga_attention.py`
- `D:\\GitHub\\tegaki\\関連ツール\\EasyReforgeExtension\\javascript\\manga_canvas.js`
- the extension `README.md`

The useful behavioral concepts are:

- The main prompt is split at `BREAK` into `STYLE + PAGE + N region` slots.
  Slot position is authoritative; `[コマN]` labels are diagnostic. A region
  receives style text plus its region text, while page text participates in a
  full-page branch.
- `manga_spatial_engine.py` consumes normalized `rect: {x,y,w,h}` values,
  clamps them to the canvas, and preserves the supplied panel order. In
  `overlap` mode both masks remain active in their intersection. In
  `exclusive` mode a higher `zIndex` mask is subtracted from lower regions.
  Each region also carries a scalar `weight`.
- `manga_attention.py` stacks the base and region masks, normalizes coverage
  per pixel, and applies Forge attention hooks. This is an implementation of
  that Forge patch, not evidence that ComfyUI regional conditioning has the
  same precedence or visual result.
- LoRA tags are diagnosed by slot, but the extension reports that extra-network
  activation is global and regional UNet LoRA isolation is not enabled.
- The canvas is a direct-manipulation editor with colors, region summaries,
  and a color/grayscale display action. These are interaction ideas, not
  authoring-schema authority.

The extension has no top-level `LICENSE`, `COPYING`, or `NOTICE` file in the
inspected root. Direct code reuse is therefore **REFERENCE_ONLY** with license
status **unknown**. We may adapt the slot, mask, and diagnostic ideas after
re-expressing them in TEGAKI contracts; we should not copy the implementation
or imply license permission.

## COMFYUI PRIMITIVES

The local ComfyUI core already supplies the material building blocks:

- `ConditioningSetArea`, `ConditioningSetAreaPercentage`, and
  `ConditioningSetAreaStrength` attach normalized/absolute spatial area and
  strength metadata.
- `ConditioningSetMask` attaches a mask and mask strength, optionally using
  the mask bounds as the conditioning area.
- `ConditioningCombine`, `ConditioningConcat`, and `ConditioningAverage`
  combine conditioning records. Their list/tensor behavior is different from
  an attention-patch compositor and must be selected deliberately.

TEGAKI already wraps these primitives in the conditioning builder and mask
builders listed above. `TegakiMangaImpactRegionalAdapter` uses Impact's
`REGIONAL_PROMPT` with cloned samplers; it is an adapter choice, not a mandate
to merge all MRP, CAST, Guide, and ControlNet paths. Rebuilding core mask or
conditioning metadata in a new MRP graph would duplicate existing capability.

## RESPONSIBILITY MAP

| Responsibility | CURRENT TEGAKI OWNER | EASYREFORGE MRP OWNER | COMFYUI PRIMITIVE | FINAL RECOMMENDED OWNER |
|---|---|---|---|---|
| Page/global prompt | Authoring page `style_prompt`/`style_negative_prompt`; page plan global fields | STYLE/PAGE slots and full-page effect branch | `CLIPTextEncode`, unmasked conditioning | TEGAKI page scope; keep global branch structured |
| Scene prompt | `Scene.prompt`/`negative_prompt`; compiled panel record | Region slots are panel-like | `CLIPTextEncode` + area/mask metadata | TEGAKI Scene scope; MRP consumes it |
| Region geometry | `REGION_SPEC`/panel `geometry`, `local_region.area`, `normalize_rect` | `rect {x,y,w,h}` normalized to canvas | `ConditioningSetAreaPercentage`; masks | TEGAKI canonical normalized `area`; one utility |
| Region prompt | Lower-level `local_regions[].prompt`; no arbitrary region list in current authoring bridge | `BREAK` region slot text | `CLIPTextEncode` | TEGAKI compile adapter, preserving scope |
| Character prompt | CAST identity plus instance acting prompt; compiled character fields | No CAST-equivalent subject contract | `CLIPTextEncode` | CAST/instance owner, separate from MRP |
| Character placement | `character_instances[].area`, `cast_id`, `scene_id` | Panel rectangles only | Mask input where an adapter needs it | CAST/instance owner; share geometry only |
| Mask generation | `TegakiMangaMaskBuilder`; two-region core | `MangaSpatialEngine` | `ConditioningSetMask` | Shared pure geometry-to-mask utility, domain adapters separate |
| Mask feather | Builder `mask_feather` 0..64, Gaussian blur | No equivalent in spatial engine | No native policy | TEGAKI mask layer; MRP soft-edge policy remains experimental |
| Overlap behavior | Independent branches; no universal precedence/normalization | Explicit overlap or z-index exclusive | Core conditioning list semantics | MRP policy only after experiment; warn, never silently choose |
| Conditioning strength | Panel/local/character strengths; local weight in layout-aware path; A/B strengths | Per-panel `weight` | `ConditioningSetAreaStrength`, mask strength | TEGAKI regional record; preserve per-region value |
| Conditioning combination | Builder append; Impact cloned regional samplers | Forge attention patch | Combine/Concat/Average | Adapter-specific compile choice; no universal graph |
| Reference Appearance mask | CAST reference area -> `IPAdapterAdvanced.attn_mask` | No equivalent CAST/reference boundary | `IPAdapterAdvanced` `attn_mask` | CAST/Reference adapter; reuse only normalized geometry |
| Guide/ControlNet future spatial input | Guides/visual frames and layout bridge are separate | Canvas/lineart ideas, no TEGAKI Guide contract | ControlNet nodes | Guide/ControlNet adapter; geometry is a future handoff only |
| Visual editor/canvas | Manga app canvas renderer and Scene Composer | `manga_canvas.js` direct manipulation | ComfyUI graph editor | Astra UI layer, later |
| Compile representation | `COMPILE_PLAN`/`PAGE_COMPILE_PLAN`, page-plan adapter | Prompt slots plus runtime hook state | CONDITIONING records | TEGAKI-owned stable plan; runtime adapters consume it |

## GEOMETRY OWNERSHIP

The canonical region representation should remain a normalized rectangle with
`x`, `y`, `w`, and `h` in `[0,1]`, validated by the existing area helpers and
rounded at the existing boundary. `shape_type: "rect"` is the current
authoring shape; polygonal panel layout is a separate visual/Guide concern.
Character instance areas remain page-space. Local-region areas remain
panel-local until the mask/bridge layer projects them to page-space.

There is no evidence that MRP needs a second rectangle model. The EasyReforge
`rect` has compatible numeric meaning, but its `zIndex`, interaction mode, and
slot order are runtime semantics that must not be copied into the persistent
authoring schema. Use one geometry validator and attach a scope (`scene`,
`local_region`, `character_instance`, or future Guide) in the compile record.

The current upper bound is six active Scene/panel records: the authoring bridge
and `region_editor.py` both enforce the 1–6 boundary, and the layout bridge
expects 1–6 matched panels. MRP must reuse that bound for top-level Scene
regions. The count of local regions remains an authoring-layer decision within
the existing model; this card does not increase it or introduce an unrelated
MRP cap.

The authoring representation answers what the user means. The compile
representation answers which normalized region records and prompt scopes are
passed to conditioning. The runtime graph materializes those records. The UI
canvas edits the authoring state. Pre-Astra work belongs only in the first two
layers.

## PROMPT COMPOSITION

Current TEGAKI preserves semantic layers:

- page style positive/negative text is global;
- each Scene becomes a panel prompt/negative branch;
- lower-level local regions carry their own prompt/negative branch;
- CAST character records carry combined identity/acting prompt and negative
  prompt;
- wildcard and LoRA resolution are tracked in compile audit data rather than
  being confused with spatial ownership.

`authoring_execution_bridge.py` also emits a human-readable `compiled_prompt`
for plan compatibility, but `TegakiMangaConditioningBuilder` still appends
global, panel, local, and character conditioning as separate records. The
recommended MRP shape is therefore **global -> Scene -> region** as structured
conditioning scopes. It must not require one flattened string to preserve the
meaning of a region. If a future adapter needs a text serialization, it must
be deterministic and auditable from those records.

EasyReforge's style-plus-region behavior is useful as a reference for the
global interaction, but its `STYLE + PAGE + BREAK` serialization is not the
TEGAKI authoring contract. MRP does not own CAST identity text, Reference
embeds, Guide hints, or LoRA materialization.

## MASK / FEATHER / OVERLAP

| Concern | Current TEGAKI | EasyReforge reference | Decision |
|---|---|---|---|
| Coordinate normalization | Page/panel-local normalized rectangles, clamped and projected to page pixels | Normalized `rect`, canvas clamp | **KEEP CURRENT**; reuse `normalize_rect` and projection |
| Mask size | Page-sized `[N,H,W]` masks derived from the compile canvas | Page-sized masks from the sampling canvas | **KEEP CURRENT**; no second resolution model |
| Mask scope | Separate panel, local-region, character tensors | Region masks plus a base attention branch | **ADAPT** through domain-specific adapters |
| Feather | Optional 0..64 Gaussian blur in the TEGAKI builders; default varies by route | No spatial-engine feather policy | **NEEDS EXPERIMENT** for MRP soft edges; do not alter current defaults |
| Overlap | Independent masked conditioning records; two-region and Impact paths expose branches but do not establish one final precedence rule | Explicit overlap keeps both masks; exclusive subtracts higher z-index | **NEEDS EXPERIMENT**; emit `OVERLAP_PRESENT` warning and never infer priority |
| Coverage/normalization | Core builders do not prove per-pixel additive or priority semantics | Forge attention hook normalizes stacked masks per pixel | **UNKNOWN** across engines; no silent port |

The accepted Reference Appearance path proves a character-area mask can feed
`IPAdapterAdvanced.attn_mask`. That is evidence for a reusable normalized
geometry-to-mask layer, not evidence that the same mask should be attached to
MRP text conditioning or a Guide. Domain adapters must keep their own mask
meaning.

## CAST / REFERENCE BOUNDARY

CAST owns identity: `cast_id`, identity prompt, reference asset, and later
IP-Adapter settings. A `character_instance` says which CAST member appears in
which Scene, where it is placed, and how it acts. MRP says where text applies
and may describe a background, prop, or panel-local content without asserting
that a CAST member is present.

The current reference path validates a canonical relative `reference_asset`,
keeps one referenced instance within the accepted product route, and maps its
character area to the IP-Adapter attention mask. MRP may share the pure
normalized-area and pixel-mask utilities, but must not merge a character
instance into a generic MRP region or create a second reference system.

## GUIDE / CONTROLNET BOUNDARY

Visual Panel Frames, Guides, rough-guide assets, pose, and composition are
structural inputs. The authoring contract and bridge intentionally keep them
out of semantic Scene conditioning. A future adapter may consume an MRP
region's normalized area when generating or selecting a Guide mask, but that
handoff is a **FUTURE ADAPTER POINT**. It must not make MRP responsible for
pose, lineart, ControlNet strength, or multi-ControlNet routing.

## ASTRA COUPLING

**LOW**

- strict region ID and geometry validation;
- normalized-area and mask-parameter normalization;
- stable ordering and compile representation;
- deterministic diagnostic serialization;
- preserving the existing authoring document without UI state.

**MEDIUM**

- structured global/Scene/region prompt composition;
- converting region records to one of the existing conditioning adapters;
- overlap diagnostics and explicit mask-policy fields;
- sharing pure geometry/mask functions across MRP, Reference, and future Guide
  adapters while keeping their meanings separate.

**HIGH**

- region canvas editing and direct manipulation;
- region list/card layout, selection, colors, and preview overlays;
- responsive workspace layout and Preview integration;
- any decision about how a user resolves overlapping regions visually.

The visual display action wording is reserved for a later UI card: when the
current view is color, the action is `白黒表示へ`; when the current view is
grayscale, the action is `カラー表示へ`. No toggle or canvas is implemented
here.

## PRE-ASTRA CORE RECOMMENDATION

Recommend exactly one next slice: **MRP regional specification
validator/compiler**.

This is a UI-independent, headless-testable adapter that fills the gap
between the existing Scene/panel records and the lower-level local-region
conditioning records. It should fit the existing
`TEGAKI_AUTHORING_DOCUMENT`/`PAGE_COMPILE_PLAN` boundary; it should not be a
`TEGAKI_MRP_DOCUMENT`.

### Proposed contract shape

**Input**

- an already validated page or page-plan context;
- the existing page/global and Scene prompt scopes;
- zero or more explicitly supplied region records using canonical normalized
  `area` geometry, stable IDs, positive prompt, optional negative prompt,
  optional region strength, and an explicit mask-policy value;
- the existing canvas dimensions and top-level six-Scene bound.

**Output**

- a deterministic normalized regional specification keyed by stable region ID;
- scope (`scene`/`local_region`) and source IDs;
- separate effective positive and negative prompt records, without requiring a
  flattened prompt;
- normalized geometry, resolved mask parameters, and a traceable warning list;
- a representation that an existing conditioning adapter can consume later.

**Errors**

Use bounded diagnostics consistent with the current validators and
`GenerationContractError` boundary:

- `INVALID_REGION_ID` or `DUPLICATE_REGION_ID`;
- `INVALID_GEOMETRY` / `OUT_OF_BOUNDS`;
- `EMPTY_REGION_PROMPT` for an enabled record with no usable positive text;
- `UNSUPPORTED_REGION_SETTING` for an unknown mask or composition option;
- `CANVAS_MISMATCH` or scope/foreign-key mismatch.

`OVERLAP_PRESENT` is a warning when overlap is allowed by the input, not an
implicit priority decision. A future policy can turn it into a hard error for
a route that requires exclusive regions.

**Side effects**

`NONE`: do not mutate the persistent document, load a model, build or submit a
runtime graph, write an image, or touch `/prompt`.

**Likely files**

- `custom_nodes_custom/tegaki_manga_nodes/scene_spec.py` for reuse of
  `normalize_rect`, local-region validation, and stable diagnostic shape;
- `custom_nodes_custom/tegaki_manga_nodes/scene_compiler.py` and/or
  `authoring_execution_bridge.py` for the smallest adapter from current Scene
  records to the regional compile representation;
- `manga/tests/test_scene_generation.py` or a narrowly scoped companion test
  module for pure contract fixtures. The executor should choose the smallest
  location that does not create a second schema authority.

**Test strategy**

Headless fixtures should cover valid global/Scene/region scopes, stable order
and IDs, area clamping/rounding, optional negative text, strength bounds,
duplicate/missing IDs, empty enabled prompts, canvas mismatch, and overlap
warning behavior. Assert that the source document is unchanged and that the
slice emits no graph, `/prompt`, model-load, runtime, GPU, or image side
effect. Existing Scene/CAST and mask tests remain regression gates but are not
expanded into a full suite by this reconciliation card.

The next slice is explicitly forbidden from adding UI, canvas, CSS, workspace
integration, actual `/prompt` graph changes, ControlNet, or multi-CAST
routing. It is **LOW Astra coupling** by design.

## FUTURE VISUAL WORK

Reserve, without designing or implementing, a later visual MRP layer for:

- a region canvas and region selection;
- stable region colors and a region list/card;
- direct manipulation and overlap feedback;
- grayscale/color preview overlays;
- Preview integration and responsive narrow-layout behavior.

That work belongs after the compile contract has a proven responsibility
boundary. It must preserve the Scene/Region, CAST/Reference, and Guide/
ControlNet split, and must use action-labelled display-mode controls as stated
above.

## DECISION SUMMARY

- Scene is the MRP base only in part: **PARTIAL_OVERLAP**.
- The canonical geometry is the existing normalized `area`; do not add a
  second rectangle authority.
- Region-level negative prompts are **CURRENT** in the lower-level compile and
  conditioning contracts, although the current AuthoringDocument bridge does
  not expose arbitrary local regions.
- Region-level strength is a **CORE REQUIREMENT** for the eventual regional
  compile record because the layout-aware/Impact paths already carry a local
  `weight`; the first slice may preserve it without adding a UI control.
- Feather is **NEEDS EXPERIMENT** for MRP. Overlap is **NEEDS EXPERIMENT** with
  confidence **UNKNOWN** across the current ComfyUI and EasyReforge engines.
- EasyReforge is **REFERENCE_ONLY** with license **unknown**.
- The single recommended next action is the headless MRP regional
  specification validator/compiler; no UI or runtime generation is part of
  that action.
