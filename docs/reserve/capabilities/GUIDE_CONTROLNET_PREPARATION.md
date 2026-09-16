STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# Guide / ControlNet Preparation

## USER VALUE

Carry structure, pose, and composition guidance safely without turning
ControlNet into an arbitrary file or model picker.

## CURRENT FOUNDATION

The current TEGAKI Guide is page-owned in
TEGAKI_AUTHORING_DOCUMENT 1.0.0. Its authoring record carries guide_id,
guide_type, canonical Guide media when present, enabled, contain placement,
Guide-local Figure areas, and metadata. Existing ownership remains in:

- manga/app/src/domain/authoring_document.js and
  custom_nodes_custom/tegaki_manga_nodes/authoring_contract.py for document
  and area validation;
- manga/app/src/domain/authoring_ops.js and
  manga/app/src/state/authoring_store.js for canonical Guide identity,
  contain placement, Figure-local geometry, and mutations;
- manga/service/manga_workspace_server.mjs for bounded Guide upload/view
  routes;
- custom_nodes_custom/tegaki_manga_nodes/rough_guide_bridge.py for a
  read/decode preview and Figure mask;
- custom_nodes_custom/tegaki_manga_nodes/generation_guide_bridge.py for a
  deterministic flat-silhouette Guide IMAGE.

There is also an existing, deliberately narrow production route in
product_generation_router.py and product_generation_api.py:
an enabled rough_manga Guide with a valid Figure selects
GUIDED_CLEAN_GLOBAL, uses the Core ControlNetLoader and
ControlNetApplyAdvanced path with the deterministic Guide IMAGE, and fails
closed when its fixed AnyTest model is unavailable. This means the current
Guide state is RUNTIME_CONNECTED for that qualified single Global route.
The reserve here concerns the missing generalized preparation layer; it does
not authorize changing or extending that route.

## PREFERRED OWNERSHIP

| Concern | Preferred owner |
| --- | --- |
| Guide meaning, namespaces, placement, authoring validation | TEGAKI CURRENT |
| Control model and preprocessor capability facts | ComfyUI CORE / explicit LOCAL COMFYUI EXTENSION, read by a TEGAKI-NATIVE adapter |
| Strict IDs, availability/reason states, and normalized preparation output | TEGAKI-NATIVE |
| Later runtime application | ComfyUI CORE or a reviewed local extension through a thin TEGAKI adapter |

EasyReforge remains a read-only behavior reference. No external source code is
copied and no extension UI/API is imported into this reserve.

## SMALLEST FUTURE CORE

Validate a canonical Guide reference, explicit source mode, optional
semantic control kind, input dimensions/metadata, normalized target geometry,
and available preprocessor/control capability. Return a versioned preparation
record with separate authoring intent, resolved resources, and diagnostics.
The record must preserve missing or ambiguous selections and must not choose a
graph route.

Strength is NOT_CURRENTLY_DEFINED for Guide authoring because no Guide
strength exists today. ComfyUI 0..10 ControlNet strength needs a later
adapter/product decision. start_percent and end_percent are ADVANCED runtime
options, not core Guide fields.

## INPUT

A server-owned relative Guide reference, expected media kind, bounded media
metadata/dimensions, optional explicit control kind and raw/preprocessed mode,
normalized page/Guide target area, and a read-only capability snapshot when
available.

## OUTPUT

A deterministic control-preparation specification containing:

- Guide identity and canonical source asset;
- source mode (RAW_GUIDE_MEDIA or PREPROCESSED_CONTROL_IMAGE);
- optional semantic control kind without a frozen large enum;
- target scope and existing normalized area geometry;
- exact preprocessor/control-model IDs only when an authority resolves them;
- AVAILABLE, UNAVAILABLE, AMBIGUOUS, or UNKNOWN states;
- stable diagnostics and provenance.

It contains no ComfyUI node names, graph payload, or persisted authoring
schema change.

## SIDE EFFECTS

NONE: read-only preparation only. No model load, graph compile, image write,
network access, /prompt, GPU, or generation.

## PREREQUISITES

Guide ownership must remain separate from MRP regions and CAST/Reference
Appearance. The existing Guide/reference validators and server routes remain
the media identity authority. A future control-kind vocabulary and
server-owned exact-ID catalog must be decided before a UI exposes those
choices. Runtime compatibility with Illustrious/SDXL, preprocessor weights and
dependencies, strength/timing behavior, and multi-control ordering require
separate Owner experiments.

## RUNTIME QUESTIONS

1. ControlNet model compatibility with the supported Illustrious/SDXL
   checkpoints and Manga resolutions.
2. VRAM/latency impact alongside IPAdapter/reference conditioning.
3. Raw versus preprocessed Guide image requirements and required weights.
4. Strength and sampling-window behavior with MRP regional conditioning.
5. Ordering and failure policy for more than one Guide/control.

## NEXT SAFE IMPLEMENTATION SLICE

Guide -> normalized Control Specification preparation. This is a
SAFE_PRE_ASTRA, LOW-coupling, headless slice. It accepts only validated
Guide inputs and read-only capability facts; returns deterministic intent,
resource states, normalized target geometry, and diagnostics; fails closed on
unsafe/missing/ambiguous input; and has no side effects. A future explicit
Card may place the small TEGAKI-native implementation beside the existing
Guide bridges and reuse their validators. It must not alter the current
fixed GUIDED_CLEAN_GLOBAL graph, authoring schema, or runtime lifecycle.

## FORBIDDEN EARLY INTEGRATION

Do not broaden the fixed guided route, add a generalized ControlNet or
preprocessor catalog, add multi-ControlNet policy, load models or preprocess
images, connect MRP masks, merge CAST/IPAdapter meaning, add schema fields,
build the final AttachmentCard UI, or submit a graph. Any such work requires
a separate Card with runtime evidence.

## LIKELY TEST STRATEGY

Headless fixtures for canonical/foreign references, media dimensions and
availability, Guide placement and Guide-local projection, optional
control-kind/source-mode diagnostics, unavailable or ambiguous capabilities,
stable serialization, and immutable input. Existing Guide identity/geometry
tests remain the starting evidence. A later runtime Card needs separate graph,
Owner, and GPU evidence.
