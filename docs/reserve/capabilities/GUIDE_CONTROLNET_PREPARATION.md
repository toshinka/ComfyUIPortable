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

Existing Manga Guide contracts, canonical attachment validators, placement
fields, and the generation-guide bridge provide domain meaning. ComfyUI core
provides `ControlNetLoader`, `ControlNetApplyAdvanced`, and control-type
capabilities. The semantic boundary remains:

`Guide / ControlNet = structure / pose / composition / geometry`.

## LIKELY SOURCE OPTIONS

Use a thin TEGAKI domain adapter over existing Guide validators and ComfyUI
capability enumeration. EasyReforge canvas and hook behavior are read-only
references only; no code copy or license assumption is allowed.

## SMALLEST FUTURE CORE

Validate a canonical guide reference, control kind, image dimensions/metadata,
normalized target geometry, and available preprocessor/control capability.
Return a versioned control specification and diagnostics. Do not select a
graph route in this reserve.

## INPUT

Server-owned relative guide reference, expected media kind, bounded media
metadata, control kind, and normalized target area.

## OUTPUT

Validated control specification with stable identity, normalized target,
capability state, and explicit errors for foreign paths, unsupported media,
invalid dimensions, or unavailable capability.

## SIDE EFFECTS

`NONE`: read-only preparation; no model load, graph compile, image write,
network access, `/prompt`, GPU, or generation.

## PREREQUISITES

Guide ownership and control-kind vocabulary must remain separate from MRP
regions and CAST/Reference. Preprocessor and model availability must be
enumerated by the existing server authority before any runtime adapter is
considered.

## FORBIDDEN EARLY INTEGRATION

Do not load ControlNet models, compile or submit graphs, add multi-ControlNet
policy, connect MRP masks, merge CAST/IPAdapter meaning, or build the final
AttachmentCard UI.

## LIKELY TEST STRATEGY

Headless fixtures for canonical/foreign references, media dimensions, control
kinds, normalized targets, unavailable capabilities, and immutable input. A
future runtime Card would need separate graph and Owner evidence.
