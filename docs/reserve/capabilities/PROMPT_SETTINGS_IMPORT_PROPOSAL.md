STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

HEADLESS CORE IMPLEMENTED
STILL LOW-PRIORITY / UNCONNECTED
UI/APPLY NOT AUTHORIZED

# Prompt / Settings Import Proposal

## USER VALUE

Let an author inspect reusable prompt and generation settings recovered from a
result without pretending that recovery is an automatic restore.

## CURRENT FOUNDATION

`manga/service/result_metadata_recovery.mjs` already provides bounded PNG
facts, raw metadata, parsed prompt/workflow, and conservative normalized hints.
The strict Manga catalog remains the authority for checkpoint, LoRA, sampler,
and scheduler identity.

## IMPLEMENTED HEADLESS CORE

Transform recovered metadata into a reviewable proposal containing candidate
values, source provenance, ambiguity, and availability. The proposal is a
read-only value object; a separate explicit user action would decide whether
to apply individual safe fields.

Implementation: `manga/service/result_settings_import.mjs`.
Targeted coverage: `manga/tests/test_result_settings_import.mjs`.

## INPUT

Validated recovered metadata plus a server-owned result identity and the
current catalog snapshot. Missing, conflicting, or stale hints remain visible
as unresolved rather than being guessed.

## OUTPUT

A proposal with independently reviewable prompt, negative prompt, seed,
dimensions, checkpoint, LoRA, sampler, and scheduler candidates; provenance
and warnings; and an explicit list of fields that are eligible for a later
apply action.

## SIDE EFFECTS

`NONE`: no document mutation, catalog mutation, model load, file write, queue,
network, `/prompt`, GPU, or generation. Applying a proposal is outside this
reserve.

## PREREQUISITES

Define the safe field allowlist, stale/ambiguous display behavior, canonical
result locator rules, and explicit confirmation boundary. Checkpoint and LoRA
values must pass strict exact-ID resolution at apply time.

## FORBIDDEN EARLY INTEGRATION

No auto-population, auto-restore, auto-generation, import panel, history
redesign, or silent substitution. Do not make this proposal the catalog or
authoring authority.

## LIKELY TEST STRATEGY

Headless metadata fixtures for absent, malformed, conflicting, stale, and
available values; assert provenance, field-level ambiguity, strict catalog
revalidation, and unchanged authoring state. Browser and runtime evidence
belong to a later explicit Card.
