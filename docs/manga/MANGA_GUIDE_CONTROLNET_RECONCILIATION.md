# Manga Guide / ControlNet Reconciliation

Status: reserve-boundary reconciliation (docs-only), 2026-09-16 JST
Repository state at review: codex/tegaki-shell-manga-play1, af96fee09ae4c52d184333f6dd517ed04b48adde

This document records the current source boundary and the smallest future
Guide/ControlNet preparation core. It does not add a schema field, catalog,
node, API, UI, graph, model, or runtime behavior. The existing qualified
Manga guided route is described as evidence; it is not expanded here.

## CURRENT GUIDE AUTHORITY

| Responsibility | Current authority | Proven current meaning |
| --- | --- | --- |
| Durable record and schema | manga/app/src/domain/authoring_document.js; custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py | TEGAKI_AUTHORING_DOCUMENT 1.0.0 owns page.guides[]. A Guide has guide_id, guide_type, optional asset_reference, enabled, placement, figure_regions, and metadata. |
| Authoring state and operations | manga/app/src/state/authoring_store.js | Toggle, delete, add/replace asset, add/delete/move/resize/associate Guide figures. These mutations remain authoring mutations and do not add runtime fields. |
| Guide media identity and namespace | manga/app/src/domain/authoring_ops.js; manga/service/manga_workspace_server.mjs | The canonical Guide namespace is tegaki_manga_guides/<safe-basename>. Workspace upload/view routes keep Guide and CAST reference namespaces separate. |
| Placement and target geometry | manga/app/src/domain/authoring_ops.js; custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py | calculateContainPlacement creates a centered, page-normalized contain placement. Figure areas are normalized Guide-local rectangles and are projected through the Guide placement when page geometry is needed. |
| Validation | authoring_ops.js, authoring_contract.py, manga_workspace_server.mjs | Path safety, normalized area, document shape, image signature/content type/extension, and upload/view response safety are split across their owning layers. No single current Guide record is a complete ControlNet capability specification. |
| Existing Guide bridges | custom_nodes_custom/tegaki_manga_nodes/rough_guide_bridge.py; generation_guide_bridge.py | rough_guide_bridge loads a canonical input asset for a page preview/figure mask and reports generation_influence NOT_IMPLEMENTED and controlnet NOT_ADDED. generation_guide_bridge does not forward raw raster pixels; it deterministically renders a flat-silhouette IMAGE from Figure geometry. |
| Existing production routing | custom_nodes_custom/tegaki_manga_nodes/product_generation_router.py; product_generation_api.py; custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js | A qualified route exists: an enabled rough_manga Guide with at least one valid Figure selects GUIDED_CLEAN_GLOBAL, prepares a fixed Core ControlNet graph, and the Minimum-Hand action queues the returned graph. This is a narrow existing route, not a generalized Guide/ControlNet catalog. |

Current Guide fields do not include control_kind, preprocessor_id,
control_model_id, strength, start_percent, or end_percent. A Guide has no
direct scene_id; a Figure may associate to a character_instance, whose Scene
relationship is separate.

The current state is RUNTIME_CONNECTED (QUALIFIED SINGLE GLOBAL ROUTE):
the source contains a real graph preparation and queue path. It is not
RUNTIME_CONNECTED as a general per-Guide, per-kind, or multi-ControlNet
system. The existing route is the boundary to preserve while this reserve
specification remains unimplemented.

## COMFYUI CONTROLNET AUTHORITY

The installed ComfyUI core in ComfyUI/nodes.py provides:

- ControlNetLoader: enumerates server-owned controlnet names through
  folder_paths.get_filename_list("controlnet"), resolves an exact name with
  get_full_path_or_raise, and loads a CONTROL_NET. Invalid content raises.
- DiffControlNetLoader: the model-plus-ControlNet variant using the same
  server-owned name enumeration and strict path lookup.
- ControlNetApplyAdvanced: accepts positive and negative CONDITIONING,
  CONTROL_NET, IMAGE, strength in 0..10 (default 1.0), start_percent and
  end_percent in 0..1 (defaults 0.0 and 1.0), plus an optional VAE. It moves
  the IMAGE to a control hint, attaches the control to both conditioning
  branches, preserves an existing control chain, and passes through when
  strength is zero.
- ControlNetApply is present but marked deprecated and applies one
  conditioning branch with unconditional application.

Core does not expose a semantic Guide control kind, a preprocessor catalog,
or a model-family meaning in these node contracts. The IMAGE input is a
control hint; whether it must be raw or preprocessed is a property of the
selected model and adapter. Node names must not become Manga authoring fields.

The existing Manga route uses the Core loader/apply pair with
TegakiMangaGenerationGuideBridge. Its fixed route settings are
strength 0.75, start 0.0, and end 1.0. This source fact does not authorize a
new graph or a broader setting contract.

## PREPROCESSOR AVAILABILITY

Classification: MIXED

The local environment contains more than Core-only capability, but it has no
single TEGAKI-owned preprocessor authority or availability catalog.

- Core supplies loading and application only; it does not preprocess.
- ComfyUI/custom_nodes/ComfyUI-Advanced-ControlNet is installed. Its
  GPL-3.0 LICENSE and version 1.6.0 pyproject are present. Its README
  documents advanced apply/load nodes, optional masks and timestep controls,
  and states that a model may require preprocessed images. It is an
  application/scheduling extension, not a general Manga preprocessor catalog.
- ComfyUI/custom_nodes/ComfyUI-PromptChain/vendor/pcr_cnaux registers local
  DepthAnything, Canny, Tile, Luminance, Scribble, SoftEdge, and LineArt
  wrappers. Its vendored record identifies the upstream slice as Apache-2.0;
  the TEED component carries its MIT license.
- ComfyUI/custom_nodes/ComfyUI-PromptChain/vendor/pcr_rtmpose registers a
  local OpenPose wrapper over vendored rtmlib. Its vendored record identifies
  rtmlib as Apache-2.0 and the wrapper lazily imports onnxruntime and may
  acquire ONNX weights on first inference.
- These files prove local implementation paths, not that every optional
  dependency or weight is installed, compatible with Illustrious, or safe to
  run in a Manga route. No preprocessor was executed or downloaded in this
  reconciliation. Normal/segmentation and other kinds were not promoted from
  a filename or node listing into a TEGAKI capability claim.

No external source was copied by this Card. A future implementation should
prefer a behavior-level adapter and preserve the applicable license notices;
it should not copy ComfyUI or extension UI/API code into Manga.

## GUIDE VS CONTROLNET

A Guide is a TEGAKI authoring concept: a page-owned structural input with
its own media namespace, placement, and optional Figure geometry. It can be
previewed, edited, enabled, disabled, and associated with a
character_instance without becoming a character identity.

ControlNet is one possible runtime implementation of structural
conditioning. A later adapter may turn a validated Guide intent into a
control image and a Core/extension graph attachment, but the authoring record
must not expose raw ComfyUI class names or inherit their parameter vocabulary.

The fixed existing route is an adapter boundary:
rough_manga Figure geometry -> deterministic Guide IMAGE ->
Core ControlNetApplyAdvanced. It does not redefine Guide as MRP, CAST, or a
raw ControlNet node.

## RESPONSIBILITY MAP

| Responsibility | Preferred source/owner | Boundary decision |
| --- | --- | --- |
| Guide semantics | TEGAKI CURRENT | Keep page-owned Guide, Figure-local geometry, enabled state, and authoring operations as the meaning authority. |
| Media/path validation | TEGAKI CURRENT | Reuse canonical Guide validators and existing workspace upload/view guards. Do not create a generic filesystem abstraction. |
| Control model catalog | TEGAKI-NATIVE over a ComfyUI CORE capability snapshot | A future Manga catalog may project exact server-owned controlnet IDs, but the Manga contract owns strict state/reason diagnostics. |
| Preprocessor catalog | TEGAKI-NATIVE over explicit LOCAL COMFYUI EXTENSION facts | Expose only enumerated IDs, input/output types, and availability; never infer from a display label or basename. |
| Preprocessor execution | LOCAL COMFYUI EXTENSION through a bounded adapter | Execution remains a later runtime responsibility with model/weight and dependency checks. |
| Normalized control specification | TEGAKI-NATIVE | Keep authoring intent separate from resolved resources and runtime node mapping. |
| Runtime graph mapping | COMFYUI CORE through a thin TEGAKI adapter | Use ControlNetLoader/ControlNetApplyAdvanced only after strict resolution and a later runtime experiment. |

The fixed AnyTest selector in product_generation_router.py is current
route evidence, not the future general catalog. Its availability helper checks
ComfyUI folder_paths and known shared folders; that route-specific behavior
must not be generalized into silent fallback.

## MEDIA / ASSET BOUNDARY

The canonical Guide asset identity is a relative
tegaki_manga_guides/<safe-basename>. Existing layers provide the following
coverage:

- authoring_ops.js rejects foreign namespaces, URLs, absolute/traversal
  forms, separators, subdirectories, and unsafe basenames. Its canonical
  Guide predicate is intentionally an identity check; it does not by itself
  prove file availability or every media extension.
- authoring_contract.py requires a rough_manga asset and checks the supported
  PNG/JPG/JPEG/WEBP extension plus normalized placement and Figure areas.
- manga_workspace_server.mjs upload routes enforce local origin, safe
  basename, size, magic bytes, Content-Type agreement, extension agreement,
  backend subfolder, and safe returned filename. View routes enforce the
  Guide namespace before forwarding to the backend.
- rough_guide_bridge.py resolves only below the ComfyUI input directory,
  rejects unsafe references, decodes the image, and reports source dimensions.
- AuthoringStore.addGuideFromAsset and replaceGuideAsset require positive
  supplied natural dimensions and preserve authoring state on mutation.

The future preparation core should reuse these owners and carry a
server-owned availability/dimension fact into its diagnostics. It must reject
foreign, missing, undecodable, or ambiguous media and must not accept an
arbitrary browser filesystem path.

## CONTROL KIND / PREPROCESSING

The current guide_type values (frame_guide and rough_manga) describe Guide
authoring types, not the semantic kind expected by a ControlNet model. A
future preparation boundary does need an optional semantic control kind, but
the current schema must remain unchanged.

Use a small, open vocabulary at the adapter boundary only. POSE, DEPTH,
LINEART, EDGE/SCRIBBLE are useful candidate meanings evidenced by local
preprocessor paths. They are not a frozen authoring enum. An unrecognized or
missing kind remains unresolved and must produce a diagnostic; it must not be
inferred from a filename, Guide type, or ControlNet basename. The exact
product vocabulary is a NEEDS_PRODUCT_DECISION.

Keep two explicit source modes:

- RAW_GUIDE_MEDIA: the supplied raster or authoring guide is the input to a
  later preprocessor requirement.
- PREPROCESSED_CONTROL_IMAGE: the supplied image already is a control hint;
  no preprocessor is implied.

The preparation record should preserve which mode the author declared and
whether the selected capability requires preprocessing. It must not inspect
pixels to guess the mode and must not execute a preprocessor in this phase.

Strength classification: NOT_CURRENTLY_DEFINED. TEGAKI Guide records have no
strength field. ComfyUI's 0..10 strength is a runtime ControlNet setting, so
it is not directly compatible and must not be silently copied into Guide
data. A later adapter/product decision may define a bounded mapping.

Start/end classification: ADVANCED. They are Core sampling-window options,
and the current qualified route fixes them to 0.0 and 1.0. They are not
current Guide semantics and must not be added to the authoring schema.

Multi-Guide future classification: NATURAL_EXTENSION. The schema already
owns pages[].guides[] and a preparation result can be a list keyed by
guide_id. The future record must avoid singleton control fields. Ordering,
stacking, and multi-ControlNet composition remain runtime questions.

## CONTROL MODEL RESOLUTION

The existing Manga strict catalog covers CHECKPOINT, LORA, SAMPLER, and
SCHEDULER resources; it does not currently own a generalized ControlNet model
catalog. The current product route has a fixed selector
CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors and a route-specific
availability check. That is sufficient evidence for one qualified path, not
for arbitrary model selection.

A future control model catalog should be server-owned and revisioned, using
exact IDs from the ComfyUI capability snapshot or folder_paths authority.
The normalized resource state must distinguish AVAILABLE, UNAVAILABLE,
AMBIGUOUS, and UNKNOWN. It must preserve the requested ID and fail closed:
no basename guessing, path search, silent substitution, download, or model
load. Semantic control_kind and control_model_id remain separate because a
model name alone does not define the user's structural intent.

No control model catalog is implemented by this Card.

## NORMALIZED CONTROL SPEC

The smallest future record is a versioned, deterministic preparation result,
not a ComfyUI prompt. Keep two conceptual layers:

| Layer | Required or optional concepts |
| --- | --- |
| authoring_intent | guide_id; canonical source_asset; explicit source_kind; optional semantic control_kind; target scope and normalized target area; source input dimensions |
| resolved_resources | optional exact preprocessor_id and control_model_id, each with availability/revision/reason; no resolution if the authority is absent or ambiguous |
| runtime_parameters | optional strength, start_percent, and end_percent only after their separate contracts are decided; unresolved values remain diagnostics |
| diagnostics | stable code/severity/message/source facts, including unsafe or missing media, unsupported kind, contradictory raw/preprocessed declaration, and unavailable resources |

The target uses the existing normalized area shape {x, y, w, h}; scope must say
whether it is page-space or a later explicitly defined scope. Guide placement
and Guide-local Figure areas are projected with their existing transform; a
Figure-local rectangle must never be mistaken for a page-global region.

A prepared result should contain intent and resource resolution separately,
retain missing selections visibly, and avoid raw node names. It may report
that a later graph adapter is required, but it must not compile or submit that
graph in this reserve slice.

## MRP / REFERENCE COEXISTENCE

The semantic split remains:

- CAST / Reference Appearance owns who and visual appearance. The existing
  reference path uses a CAST reference asset and a character_instance area
  for IPAdapter attention masking.
- Scene / Region / MRP owns where and what text conditioning applies. The
  regional compile core owns ordered regional prompt records and canonical
  normalized areas.
- Guide / ControlNet owns structure, pose, composition, and geometry. Guide
  placement and Figure-local areas may be projected to structural control
  input, but they do not become MRP regions.
- LoRA remains a learned modifier and is not a substitute for any of these
  spatial or appearance roles.

A future graph may carry MRP regional text conditioning, Reference Appearance
conditioning, and structural Guide conditioning through separate adapters.
The only currently safe shared element is a pure geometry/mask utility with
explicit scope. This Card designs no combined graph, precedence, or
multi-control behavior.

## ASTRA COUPLING

- LOW: canonical identity, media validation, normalized geometry, immutable
  preparation, and strict capability/resource diagnostics.
- MEDIUM: the product vocabulary for semantic kinds; how raw versus
  preprocessed intent is presented; which timing and strength controls are
  primary versus advanced.
- HIGH: AttachmentCard composition, Guide preview, direct manipulation and
  overlays, panel placement, and narrow layout behavior.

No Astra UI decision is required for the recommended headless slice.

## RUNTIME QUESTIONS

Exactly five questions remain for a later runtime/Owner experiment:

1. Does the selected ControlNet model remain compatible with each supported
   Illustrious/SDXL checkpoint at the intended Manga resolution?
2. What is the VRAM and latency cost when Guide ControlNet is combined with the
   already-proven IPAdapter/reference path?
3. Which raw Guide media and preprocessed image forms does each selected model
   actually accept, and which preprocessor weights/dependencies are required?
4. How do strength and sampling-window values behave alongside MRP regional
   conditioning without visual boundary or prompt-scope regressions?
5. What ordering and failure policy is safe when more than one Guide/control is
   requested?

No question was answered experimentally here.

## HEADLESS CORE CANDIDATES

| Candidate | Classification | Reason |
| --- | --- | --- |
| A. Guide media validator | SAFE_PRE_ASTRA | Reuses existing canonical identity, media guards, dimension facts, and fail-closed diagnostics. |
| B. Guide semantic normalizer | NEEDS_PRODUCT_DECISION | Geometry is bounded, but the semantic control-kind vocabulary and raw/preprocessed declaration need product ownership. |
| C. Control/preprocessor capability catalog | NEEDS_PRODUCT_DECISION | Local extension paths exist, but there is no authoritative Manga catalog, revision, or strict ID policy. |
| D. Normalized Control Specification compiler | SAFE_PRE_ASTRA | It can preserve unresolved resources and produce deterministic intent/diagnostics without model or graph work. |
| E. Runtime ControlNet graph adapter | NEEDS_RUNTIME_EXPERIMENT | The fixed route is proven in existing source/history, while generalized model compatibility, VRAM, and coexistence are not established. |

## ONE SAFE NEXT SLICE

Name: Guide -> normalized Control Specification preparation
Classification: SAFE_PRE_ASTRA; LOW Astra coupling

Input:

- An already structurally validated AuthoringDocument page and one or more
  page-owned Guide records.
- Canonical Guide asset identity plus server-owned availability, media type,
  and natural dimensions from the existing validation path.
- Optional explicit semantic intent (control_kind, source_kind, and target
  scope/area), never inferred from a filename.
- A read-only capability snapshot when available; absence is a known state.

Output:

- A deterministic preparation record with separate authoring_intent and
  resolved_resources sections.
- Canonical source identity, source mode, normalized page/Guide target,
  dimensions, exact requested IDs when present, and stable diagnostics.
- Explicit AVAILABLE, UNAVAILABLE, AMBIGUOUS, or UNKNOWN resource state.
- No ComfyUI node names and no graph payload.

Errors:

Foreign or unsafe reference; missing or undecodable asset; unsupported media;
invalid dimensions or area; missing/ambiguous semantic kind when required;
contradictory raw/preprocessed declaration; unavailable or ambiguous
preprocessor/model capability; duplicate or malformed Guide identity.

Side effects:

NONE. No files, network, model load, graph compile, queue, /prompt, GPU, or
generation.

Likely future files:

- A small TEGAKI-native module, for example
  custom_nodes_custom/tegaki_manga_nodes/guide_control_spec.py, only under a
  future explicit implementation Card.
- Reuse, without schema edits, authoring_contract.py,
  generation_guide_bridge.py, rough_guide_bridge.py, and the existing
  authoring_ops.js/server asset validation path.
- Do not modify product_generation_router.py or the current fixed guided
  graph for this preparation slice.

Test strategy:

Pure fixtures for canonical/foreign/missing media, extension and dimensions,
Guide placement plus Guide-local projection, optional kind/source-mode
diagnostics, unavailable and ambiguous capability records, stable ordering,
and immutable input. Existing identity/geometry coverage remains in
manga/tests/test_guide_asset_ops.mjs and manga/tests/test_guide_ops.mjs; a
future dedicated preparation test must not require a ControlNet model or
invoke a runtime.

This is the only recommended next implementation slice. The generalized
catalog, UI, graph adapter, multi-ControlNet policy, and runtime experiment
remain separate future Cards.
