STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# Model / LoRA Metadata Enrichment

## PURPOSE

Explain a server-owned checkpoint or LoRA with optional base-model, trigger,
hash, and provenance metadata while preserving the current strict catalog as
the only selection authority.

## LIKELY HOME

A bounded TEGAKI local metadata service behind the existing Manga catalog
authority. ComfyUI core safetensors-header behavior and the installed
MIT-licensed ComfyUI-Custom-Scripts behavior may be compared, but no source or
PromptServer/UI coupling is copied.

## PREREQUISITES

Stable canonical IDs, supported header formats, availability/error states,
provenance rules, and a read-only cache policy. Metadata must never change
catalog identity, availability, or fallback behavior.

## DO NOT IMPLEMENT YET

Do not add a model browser, network provider, download path, selector change,
automatic trigger insertion, or UI detail panel. No model loading, generation,
or catalog mutation is authorized.
