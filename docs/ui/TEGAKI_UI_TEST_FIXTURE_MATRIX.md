# TEGAKI UI Test Fixture Matrix

Status: pre-Astra supporting material. These files are small, deterministic test
inputs for later component or visual checks. They are not production state, not
rendered evidence, and not a new cross-domain schema.

## Rules

- Manga and H3 keep separate state ownership, request/result contracts, and
  attachment meaning.
- A fixture is a snapshot of an existing source shape. It is not an API
  authority and must not be imported by production code.
- No fixture contains a real image, video, generated payload, user data,
  credential, timestamp from a run, or machine-specific filesystem path.
- The only timestamp values are fixed ISO strings used where the current record
  shape exposes timestamps.
- Manga `ownership_token` and digest fields are deterministic shape-preserving
  placeholders for pure journal validation; they are not credentials or runtime
  secrets.
- `manga_idle` deliberately represents the journal's early `VALIDATING` state;
  it does not invent a separate `IDLE` field. H3's empty/ready condition is the
  absence of an active or preview job and is therefore documented as no-file
  coverage.
- The H3 busy percentage is the exact `map_progress_event` projection shape
  (`kind`, `value`, `max`, `percent`); `percent` is derived from the fixture's
  value/max pair and carries no new progress semantics.

## Safe fixture inventory

### Manga

| Fixture | Path | Source authority | State represented | Purpose / safe later consumer | Limitations |
| --- | --- | --- | --- | --- | --- |
| `manga_idle` | `manga/tests/fixtures/ui_state/jobs/11111111-1111-4111-8111-111111111111.json` | `manga/service/generation_journal.mjs` record validation and `GenerationState` job vocabulary | `VALIDATING`, `prompt_id: null`, no output | GenerationStatus and empty/no-result handling tests | It is an early journal record, not a complete browser idle projection or catalog snapshot. |
| `manga_generating` | `manga/tests/fixtures/ui_state/jobs/22222222-2222-4222-8222-222222222222.json` | `GenerationJournal` plus `GenerationService` active states | `RUNNING`, backend prompt ID present, no output | Active job/status and previous-result retention setup | No progress percentage exists in the Manga record contract, so none is added. |
| `manga_result` | `manga/tests/fixtures/ui_state/jobs/33333333-3333-4333-8333-333333333333.json` | `GenerationJournal` successful-record and output-locator validation | `SUCCEEDED` with one owned PNG locator | Result/history, settings restore, and output-locator tests | Locator is identity only; no PNG bytes are included or implied. |
| `manga_error` | `manga/tests/fixtures/ui_state/jobs/66666666-6666-4666-8666-666666666666.json` | `GenerationJournal` failed-record shape and `GenerationService` error vocabulary | `FAILED` with `BACKEND_REJECTED`, no output | Failure/error rendering and retained settings tests | It does not model an unconfirmed `UNKNOWN` record; no fixture is created for that composite path. |
| `manga_reference_authoring` | `manga/tests/fixtures/ui_state/manga_reference_authoring.json` | `authoring_document.js`, `authoring_ops.js`, and `AuthoringStore` | Canonical authoring document with CAST reference and Guide asset references | `AttachmentCard`, Manga authoring, and reference grammar tests | It is authoring data only; it does not claim a generation job consumed the references. |

### H3

| Fixture | Path | Source authority | State represented | Purpose / safe later consumer | Limitations |
| --- | --- | --- | --- | --- | --- |
| `h3_generating` | `h3/tests/fixtures/ui_state/h3_generating.json` | `h3/app/server.py::Job.public` and `h3/app/native_progress.py::map_progress_event` | Public `RUNNING` video job with sampling progress and cancel available | GenerationStatus and ProgressProjection/Overlay tests | It is a public projection snapshot; it does not represent an active runtime or websocket. |
| `h3_video_result` | `h3/tests/fixtures/ui_state/h3_video_result.json` | `Job.public`, `native_t2v.H3Request.public`, `history-settings.js`, `continuation-source.js` | Completed text-to-video result with same-origin video locator | Result/history, restore, and continuity tests | The `.mp4` locator is identity only; no media bytes are included. |
| `h3_reference_result` | `h3/tests/fixtures/ui_state/h3_reference_result.json` | `Job.public`, `H3ReferenceSlots.public`, `history-settings.js` | Completed video with Start and End reference slots | AttachmentCard, reference route label, and history reference normalization tests | Reference files are not created; availability verification remains a consumer responsibility. |
| `h3_failed` | `h3/tests/fixtures/ui_state/h3_failed.json` | `Job.public` terminal/error projection and `job-status-copy.js` vocabulary | `FAILED` video job with retained request and no media | Error, retained-input, and history-card tests | It does not claim a particular backend error payload beyond the public error text. |

The pack contains five Manga fixtures and four H3 fixtures. All are independent
domain objects; none is a universal `tegaki_global_state.json` or
`universal_generation_state.json`.

## Candidates intentionally not created

| Candidate | Classification | Reason |
| --- | --- | --- |
| Manga UI `IDLE`/`READY` wrapper | `SOURCE_TOO_COUPLED` | Readiness is derived from catalog, history-loading, local busy, and active-job fields rather than one persisted object. The journal `VALIDATING` fixture is the narrow safe substitute. |
| Manga `UNKNOWN` with recovered/ambiguous submission | `STATE_NOT_IMPLEMENTED` for a standalone static fixture | The UI state combines journal record, backend evidence, and retry lock. A snapshot would invite a false prompt/result relationship. |
| Manga changed-settings/dirty wrapper | `SOURCE_TOO_COUPLED` | The draft lives in `GenerationState` while the result lives in a journal job; no current serializable composite exists. |
| Manga PreviewFocus | `STATE_NOT_IMPLEMENTED` | The component contract is not implemented in the current UI. |
| H3 empty/ready wrapper | `SOURCE_TOO_COUPLED` | Initial readiness is assembled from module-local DOM state, backend status, and null active/preview jobs; a new JSON envelope would be a parallel schema. |
| H3 changed-settings/dirty wrapper | `SOURCE_TOO_COUPLED` | Form values and `Job.public()` history are separate; no current dirty projection is authoritative. |
| H3 PreviewFocus wrapper | `ASTRA_DEPENDENT` | Narrow Result selection is related, but the dedicated focus contract remains a review decision. |
| H3 missing/unavailable attachment | `STATE_NOT_IMPLEMENTED` for static data | Missing availability is established by a live verifier and server-owned asset lookup; a fabricated missing asset would be misleading. |
| H3 Still/Prep/R2V asset bundles | `SAFE_STATIC_FIXTURE` candidate, not created | Existing pure normalizers support them, but the current small pack already covers status, result, failure, and fixed reference slots without adding redundant files. |

## Component coverage

| Component contract | Manga fixtures | H3 fixtures | Coverage |
| --- | --- | --- | --- |
| `GenerationStatus` | `manga_idle`, `manga_generating`, `manga_result`, `manga_error` | `h3_generating`, `h3_video_result`, `h3_failed` | YES |
| `ProgressProjection` | No percentage field in current Manga record | `h3_generating` exact sampling projection | PARTIAL |
| `MediaPreviewShell` | `manga_result`, `manga_error` output/no-output projections | `h3_video_result`, `h3_failed` media/no-media projections | PARTIAL |
| `AttachmentCard` | `manga_reference_authoring` CAST/Guide references | `h3_reference_result` Start/End slots | YES |
| `CompactContext` | Result settings and authoring references provide source material | Request, route label, and reference summaries provide source material | PARTIAL |
| `PreviewFocus` | No fixture | No dedicated fixture | NO |

Coverage means that a later test has a truthful input to project into the
contract. It does not mean the component is implemented or that a screenshot is
accepted.

## Pure validation plan

The following bounded checks consume the actual fixture files without starting a
runtime:

1. Parse every JSON file with the standard JSON parser.
2. Point `GenerationJournal` at
   `manga/tests/fixtures/ui_state/jobs/` and call `list()`; this validates the
   four Manga journal records using the current journal contract.
3. Call `validateAuthoringDocument` on `manga_reference_authoring.json` and
   validate its CAST/Guide references with the existing canonical reference
   validators.
4. Load H3 result/reference fixtures and call `resolveHistorySettings` with
   current resolution/duration/steps options and a no-op availability verifier;
   call `validateContinuationSource` for the completed video fixture.
5. Check the H3 progress object with `map_progress_event` using its exact
   `value`, `max`, prompt ID, and sampler-node inputs; no network or websocket is
   involved.

No production parser is changed to accept these files. If a future consumer
needs a builder, it must remain under tests and preserve the domain-specific
source shape.

The bounded validation for this preparation passed: all fixture JSON parsed,
`GenerationJournal.list()` accepted the four Manga records, the authoring
document and its CAST/Guide references passed their current validators, the H3
video/reference fixtures passed history and continuation normalization, and the
H3 sampling projection matched `map_progress_event`. The existing targeted
pure checks `manga/tests/test_domain_document.mjs`,
`manga/tests/test_cast_reference_ops.mjs`,
`h3/tests/verify_vp1_video_ui.mjs`, and
`h3/tests/verify_h3_g2a_progress.mjs` also passed. No runtime, network, `/prompt`,
or generation was used.

## Relationship to Astra evidence

These fixtures support later implementation and component tests only. They do
not replace the rendered evidence package in
`TEGAKI_ASTRA_UI_EVIDENCE_PLAN.md`, do not answer Astra's layout questions, and
must never be used to claim Browser or Owner acceptance. `docs/STATUS.md` remains
unchanged with the project checkpoint `WAIT FOR ASTRA UI REVIEW`.
