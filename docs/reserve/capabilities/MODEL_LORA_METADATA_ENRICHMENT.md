STATUS: LOW-PRIORITY RESERVE
NOT PRODUCTION AUTHORITY
NOT AUTHORIZED FOR UI OR RUNTIME INTEGRATION
SAFE TO LEAVE INCOMPLETE
IMPLEMENT ONLY UNDER A FUTURE EXPLICIT CARD

# Model / LoRA Metadata Enrichment

## IMPLEMENTATION STATUS

HEADLESS LOCAL CORE IMPLEMENTED

This reserve capability remains **LOW-PRIORITY / UNCONNECTED**.  The local
core is **NOT CATALOG AUTHORITY**, has **NO UI**, and has **NO NETWORK
PROVIDER**.  The capability-bank size remains four; this bounded reader is not
promoted to a banked product capability.

## CURRENT BOUNDED CORE

The implementation lives at
`custom_nodes_custom/tegaki_manga_nodes/model_lora_metadata.py` and is a pure
reader for an already resolved server-owned resource.  It supports only
`CHECKPOINT` and `LORA` resources and only the safetensors header framing
(`.safetensors` and ComfyUI's `.sft` suffix).  It reads the eight-byte little
endian header length and the bounded JSON header, then stops before tensor
payload bytes.  The default header limit is 8 MiB; nested metadata, entry
count, and string values are bounded deterministically.

The conceptual input is `{kind, canonical_id, resolved_path}`.  The path is
supplied by the strict Manga catalog authority; this module does not scan
model trees, resolve basenames, fuzzy-match IDs, or accept a browser path
through a product route.  The result preserves `kind` and `canonical_id` and
returns `metadata_state`, `format`, bounded `raw_embedded_metadata`, bounded
`normalized_metadata`, warnings, an explicit error state, inspected-byte
count, and `hash_state`.

Metadata absence is nonfatal (`ABSENT`).  Framing and JSON failures are
fail-closed (`FILE_NOT_FOUND`, `UNSUPPORTED_FORMAT`, `INVALID_SAFETENSORS`,
`HEADER_TOO_LARGE`, or `METADATA_MALFORMED`).  Conflicting explicit values
remain diagnostic (`CONFLICT`) and never choose a winner; catalog availability
and identity are unaffected.

## NORMALIZATION BOUNDARY

Only explicit keys with an established local convention are normalized:

* `ss_base_model_version` / `ss_sd_model_name` -> `base_model` with
  `base_model_state` (`EXPLICIT`, `CONFLICTING`, or `ABSENT`);
* `modelspec.architecture`, `modelspec.title`, and
  `modelspec.description`;
* `modelspec.trigger_phrase`, `ss_trigger_words`, or `trigger_words` as an
  unchanged explicit `trigger_words` value;
* `ss_resolution` / `modelspec.resolution` and the raw training evidence in
  `ss_tag_frequency` / `ss_bucket_info`;
* explicitly stored provenance keys (`modelspec.source`, `source`,
  `source_url`); and
* explicitly embedded hash keys (`modelspec.hash.sha256`,
  `modelspec.hash.blake3`, `_sha256`, `sha256`, `sshs_model_hash`, or
  `sshs_legacy_hash`).

Unknown keys remain in the bounded raw metadata only.  Trigger words are
never derived from filenames, descriptions, tags, frequency, or Civitai.
`hash_state` is `KNOWN` only for an explicit embedded hash; the reader never
computes a full hash of the model.  No sidecar convention is used: the
existing sidecar implementations either write cache/notes or make network
requests, and no server-owned sidecar authority is established for Manga.

## SIDE-EFFECT AND CONNECTION BOUNDARY

The reader performs no model or tensor load, no GPU work, no generation, no
`/prompt`, no network request, no cache/write, no mtime update, no rename, and
no catalog mutation.  It is intentionally not wired into
`result_settings_import.mjs`, a route, a selector, or a UI panel.  A future
consumer must pass an already canonical and resolved context and keep metadata
failure separate from resource availability.

Targeted synthetic fixtures cover checkpoint and LoRA metadata, raw/unknown
preservation, explicit base-model states, trigger non-guessing, conflicts,
malformed and oversized headers, unsupported/missing resources, deterministic
results, no tensor-payload read, and no writes.  No real model or multi-GB
file is required.

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
