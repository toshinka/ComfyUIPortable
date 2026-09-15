# TEGAKI Capability Bank Checkpoint

Status: local architecture checkpoint, 2026-09-16

This document records the four implemented capabilities that are eligible for
the TEGAKI capability bank at the current Manga PLAY1 line. It is a bounded
inventory and consistency review. It does not create a new runtime, UI
composition, graph connection, namespace, or cross-engine dependency.

## Banked capability map

| Capability | Current owner | Layer | Input | Output | Side effects | Current domain | Future sharing potential | Headless tests | UI connected? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Result metadata recovery | `manga/service/result_metadata_recovery.mjs` (`inspectGeneratedPng`, `inspectPngBuffer`) | LOCAL SERVICE | A bounded PNG buffer or a caller-provided local result path | PNG facts, lossless metadata entries, parsed prompt/workflow, conservative normalized hints, warnings/errors | Reads local PNG bytes only; no writes or execution | Manga result service | `DOMAIN_NEUTRAL_CANDIDATE` | `manga/tests/test_result_metadata_recovery.mjs` | NO |
| Wildcard core | `custom_nodes_custom/tegaki_manga_nodes/basic_generation.py` | PURE CORE | Prompt text, Manga wildcard catalog/root, effective seed and domain | Validated or deterministically expanded text plus wildcard/choice trace and bounded diagnostics | Reads the server-owned wildcard catalog/root only | Manga prompt compiler | `DOMAIN_NEUTRAL_CANDIDATE` if another domain adopts the same syntax and safety contract | `manga/tests/test_basic_generation.py` (`DynamicPromptTests`, `HeadlessWildcardTests`) | NO |
| Catalog and strict resource resolution | `custom_nodes_custom/tegaki_manga_nodes/basic_generation.py` (`build_catalog`, `get_catalog_snapshot`, `resolve_catalog_resource`, `resolve_recovered_resources`) | DOMAIN CORE | Backend capability snapshot and server-owned IDs for CHECKPOINT, LORA, SAMPLER, or SCHEDULER | Revisioned catalog, detached snapshot, or exact resolution result with state/reason | Reads existing authority/snapshot only; no fallback, download, or mutation | Manga generation/catalog authority | `DOMAIN_NEUTRAL_CANDIDATE` only through a separately reviewed adapter | `manga/tests/test_basic_generation.py` (`BasicGenerationTests`, `CatalogResolutionTests`) | NO |
| Manga regional compile core | `custom_nodes_custom/tegaki_manga_nodes/scene_spec.py` (`compile_regional_spec`) | DOMAIN CORE | Structured page/Scene context and ordered regional records | Deterministic normalized region records, prompt scopes, source order, and overlap diagnostics | Pure transformation; no files, network, graph, masks, or conditioning | Manga regional authoring/compile | `MANGA_ONLY` | `manga/tests/test_mrp_regional_compile.py`, related `test_scene_generation.py` | NO |

These are exactly the four banked capabilities. A possible future consumer is
not counted as a bank entry until it has a bounded owner, contract, and tests.

## Capability notes

### Result metadata recovery

`result_metadata_recovery.mjs` is a read-only, bounded parser for PNG metadata
written by ComfyUI SaveImage. It validates PNG structure and CRCs, accepts the
supported textual chunk forms (`tEXt`, `zTXt`, and `iTXt`), preserves raw and
ordered entries, and parses `prompt` and `workflow` without executing a
workflow. It extracts only consistent hints from supported KSampler paths and
keeps PNG dimensions as file facts when workflow dimensions disagree.

Conflicting or incomplete graph paths are reported as warnings and omitted
from `normalized_hints`; prompt graphs are never flattened by guesswork. The
file-path API is read-only, but the caller remains responsible for supplying a
server-owned/safe result locator. No import, restore, catalog resolution, or
generation is performed here. The Manga service location is acceptable for
now; it should be reviewed only if a second domain creates real reuse
pressure, and it must not be moved just for abstraction symmetry.

### Wildcard core

The existing Manga compiler is the syntax and safety authority for wildcard
catalog discovery, validation, and deterministic expansion. Its supported
forms are exactly `__wildcard__`, `{a|b}`, nested choices, weighted choices,
and escaped braces. Catalog names and source labels are bounded to the
server-owned wildcard root; traversal, absolute paths, control characters,
unresolved references, and excessive recursion fail closed. Expansion derives
its deterministic choice seed from the effective request seed and domain, and
records the selections in a trace. Explicit seed `0` is retained; sentinel
`-1` is resolved once by the compiler.

The installed `dynamicprompts` implementation remains the behavior authority;
this bank does not redefine its syntax. This is a prompt compiler capability,
not a general autocomplete/editor or an H3 capability. It may be shared only
after another domain accepts the same syntax, root, trace, and safety
contract; possible reuse alone does not justify a move.

### Catalog and strict resource resolution

Manga owns catalog construction and resolution for CHECKPOINT, LORA, SAMPLER,
and SCHEDULER. A catalog has required-node/capability checks, bounded product
values, stable IDs, available flags, and a revision digest. Resolution uses an
exact canonical ID and returns an explicit state such as `AVAILABLE`, `MISSING`,
`STALE_SELECTION`, `NOT_FOUND`, `AMBIGUOUS`, or `INVALID`. It never guesses a
basename, substitutes a different item, downloads a model, or silently
restores a stale value. A detached snapshot prevents callers from mutating
the authority.

Recovered PNG hints can be passed through `resolve_recovered_resources` for
later strict verification; they are not auto-applied to authoring or a
generation request. Prompt LoRA notation has a separate, deliberately narrow
compatibility path in the basic compiler (including extension-omission rules
where unambiguous); it is fail-closed and must not be described as a relaxed
catalog resolver. No namespace merge with H3 is implied.

### Manga regional compile core

`compile_regional_spec` is a pure, versioned normalization boundary for Manga
regional records. It preserves stable explicit IDs, source order, page/Scene
context, enabled state, positive and negative prompt presence, and an optional
finite strength (`strength`, with the existing `weight` alias). Areas are
validated through the existing authoring contract and normalized to canonical
rectangles. Duplicate IDs, unsupported fields, invalid geometry, missing
enabled prompts, and conflicting strength values fail closed. Pairwise overlap
is diagnosed with the involved IDs and order; no precedence is chosen.

The compiler does not create masks or conditioning, choose feathering, merge
CAST/Reference/Guide semantics, or compile a ComfyUI graph. Overlap policy,
feathering, and runtime conditioning remain later adapter decisions. The core
is therefore banked as `BANKED_EXPERIMENTAL` until those policies are proven,
while its current deterministic validation contract remains usable.

## Ownership, maturity, and connection review

| Capability | Ownership review | Maturity | Connection status | Sharing classification |
| --- | --- | --- | --- | --- |
| Result metadata recovery | `ACCEPTABLE_FOR_NOW`; future review only if real cross-domain demand appears | `BANKED_STABLE` | `UNCONNECTED_BY_DESIGN` | `DOMAIN_NEUTRAL_CANDIDATE` |
| Wildcard core | `GOOD`; existing Manga compiler remains the single syntax authority | `BANKED_STABLE` | `EXISTING_PRODUCT_OWNER_EXTENDED` | `DOMAIN_NEUTRAL_CANDIDATE` |
| Catalog and strict resource resolution | `GOOD`; Manga remains the resource authority | `BANKED_STABLE` | `EXISTING_PRODUCT_OWNER_EXTENDED` | `DOMAIN_NEUTRAL_CANDIDATE` |
| Manga regional compile core | `GOOD`; policy gaps belong to future adapters | `BANKED_EXPERIMENTAL` | `UNCONNECTED_BY_DESIGN` | `MANGA_ONLY` |

No ownership transfer or module move is required. There is no catch-all
service: metadata parsing, prompt expansion, catalog resolution, and regional
normalization have separate owners and bounded contracts.

## Cross-capability relationships

The relationships below are documented handoffs only; this checkpoint adds no
dependency between modules.

* Result metadata recovery may provide checkpoint/LoRA hints to the strict
  catalog resolver for later verification. Hints are never auto-restored.
* Wildcard expansion feeds prompt authoring/compilation text and its trace.
* Regional compile output is a future input to a Manga mask/conditioning
  adapter.
* There is no direct metadata-to-generation, wildcard-to-catalog, or
  regional-to-graph connection added here.

## Domain and UI boundary review

| Boundary check | Result |
| --- | --- |
| Metadata recovery contains no Manga/H3 semantic reconstruction | PASS |
| Wildcard core is not a general autocomplete/editor and makes no H3 claim | PASS |
| Catalog resolution does not merge Manga and H3 namespaces | PASS |
| Regional compile contains no CAST, Reference, or Guide semantics | PASS |
| UI independence: no panel, button, tab, Preview, Create, density, or layout assumption | PASS; all four are headless |

The side-effect boundary is equally explicit: metadata reads a caller-provided
local PNG; wildcard reads its bounded catalog/root; catalog reads current
authority/snapshots; regional compile is pure. None writes files, contacts a
network, loads a model, uses a GPU, submits `/prompt`, or performs generation.

## Coverage map and bounded gaps

Targeted headless coverage already exists for every bank entry:

| Capability | Principal existing coverage | Obvious remaining gap |
| --- | --- | --- |
| Result metadata recovery | `test_result_metadata_recovery.mjs` covers valid, compressed, malformed, ambiguous, bounded, and read-only cases | A future safe-locator contract belongs to its caller; no parser expansion is authorized here |
| Wildcard core | `test_basic_generation.py` covers catalog/validation, nested and weighted expansion, escaping, determinism, seed handling, and failure traces | Cross-domain adoption has no test because no cross-domain adapter exists |
| Catalog and strict resource resolution | `test_basic_generation.py` covers revisioned catalogs, exact IDs, stale/missing/ambiguous/invalid states, snapshots, and recovered hints | UI missing-resource presentation is intentionally unimplemented |
| Manga regional compile core | `test_mrp_regional_compile.py` plus related scene-generation tests cover normalization, IDs/order, scopes, strength, overlap diagnostics, immutability, and rejection paths | Runtime overlap precedence, feathering, masks, and conditioning remain future policy tests |

This checkpoint records the existing targeted matrix; it does not rerun full
Manga or ComfyUI suites. No new coverage requirement is created by the bank.

## Connections forbidden before an Astra composition pass

The following remain explicitly out of scope:

* Importing or restoring recovered metadata in a UI, or auto-applying recovered
  settings.
* Adding a wildcard editor, layout, autocomplete surface, or changing the
  established wildcard syntax.
* Building a Model/LoRA browser, auto-substitution, basename guessing, or
  stale-value auto-restore.
* Wiring regional compile into a graph, mask, ControlNet, or conditioning path;
  selecting overlap precedence or changing feathering policy.
* Connecting Guide/ControlNet or CAST/IPAdapter semantics to the regional
  core.
* Redesigning Preview/Create hierarchy or adding H3/Manga runtime coupling.

## Astra relationship and future queue

The four entries separate ASTRA-INDEPENDENT CORE from future
ASTRA-DEPENDENT ADAPTER/COMPOSITION work. Core contracts can be tested
headlessly and remain independent of placement, interaction density, focus,
and visual layout. Later composition work may review these bounded adapters:

1. metadata inspect/import presentation (with explicit user confirmation and
   strict locator handling);
2. wildcard authoring/editor assistance;
3. catalog selection and missing-resource presentation;
4. regional mask/conditioning integration.

Every item in that queue is **NOT AUTHORIZED YET**. Queue entries do not change
the bank size or current connection status.

## Reusable capability bank rule

Bank a capability only when a concrete product problem exists, one owner is
identified, input and output are explicit, headless tests cover the bounded
behavior, side effects are constrained, and no UI composition is required.
Check the existing authority before introducing another implementation. The
fact that an abstraction could be useful is not sufficient evidence to bank or
move it.

## Checkpoint decision

Bank size: **4**.

The recommended next action is **PAUSE NEW CAPABILITY ADDITIONS** and review
integration/composition boundaries with Astra. Keep all four owners in place;
do not create a shared supervisor, common H3/Manga service, or new framework.
