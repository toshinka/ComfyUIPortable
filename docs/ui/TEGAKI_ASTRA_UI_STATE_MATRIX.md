# TEGAKI Astra UI Observable State Matrix

This matrix is a capture checklist for the pre-Astra review. It records current
reachability and the smallest safe setup; it does not invent unavailable states
or judge the layout.

## State rows

`CURRENTLY OBSERVABLE` means the product or an existing bounded fixture exposes
the state. `PARTIALLY OBSERVABLE` means related signals exist but the complete
contract or a safe local result is not guaranteed. `NOT IMPLEMENTED` means the
state must remain unavailable for this review.

| ID | Domain | Viewport | State | Observability | Smallest setup / route | Fixture or result needed | Attachment/reference | Generation needed | Capture priority | Pair with |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MANGA-EMPTY` | Manga | WIDE | EMPTY/FIRST-LAUNCH | CURRENTLY OBSERVABLE | Open Manga Generate with an empty draft; direct workspace or `?embedded=1` | Empty `.mg-stage`, `No verified result yet` | None | NO | baseline | `H3-EMPTY` |
| `MANGA-AUTHORING` | Manga | WIDE | AUTHORING WITH CONTENT | CURRENTLY OBSERVABLE | Open Authoring and load the existing rich Scene/CAST/Guide fixture | Prior `MANGA_AUTHORING.png` or fresh safe render | Existing local CAST/Guide data | NO | highest | `H3-AUTHORING` |
| `MANGA-REFERENCE` | Manga | WIDE/NARROW | REFERENCE/ATTACHMENT PRESENT | CURRENTLY OBSERVABLE | Expand CAST or Guide reference area in the rich fixture | Existing local reference image/status | CAST/Guide reference | NO | after authoring | `H3-REFERENCE` |
| `MANGA-BUSY` | Manga | WIDE | GENERATING/BUSY | CURRENTLY OBSERVABLE | Use the existing browser fixture's fake submission path; do not submit a real job | Fixture transitions `SUBMITTING`/`QUEUED`/`GENERATING` | None | NO (fixture only) | conditional | `H3-BUSY` |
| `MANGA-RESULT` | Manga | WIDE | RESULT AVAILABLE | CURRENTLY OBSERVABLE | Select an existing verified result/history item; no new submit | Existing valid local PNG and history metadata | None | NO | highest | `H3-RESULT` |
| `MANGA-ERROR` | Manga | WIDE | ERROR | CURRENTLY OBSERVABLE | Use the bounded fixture's catalog failure, failed response, invalid LoRA, or unknown response path | Fixture error response only | None | NO (fixture only) | conditional | `H3-ERROR` |
| `MANGA-DIRTY` | Manga | WIDE/NARROW | CHANGED SINCE LAST RESULT | CURRENTLY OBSERVABLE | Start from a safe result, edit draft settings, keep the previous result | Fixture previous-result retention and restore path | None | NO | high | `H3-DIRTY` |
| `MANGA-FOCUS` | Manga | WIDE/NARROW | FOCUSED RESULT | NOT IMPLEMENTED | No safe setup; record unavailable | None | None | NO | record absence | `H3-FOCUS` |
| `MANGA-NARROW-AUTHORING` | Manga | NARROW | AUTHORING WITH CONTENT | CURRENTLY OBSERVABLE | Same rich fixture at 430 x 850 | Existing browser fixture narrow path | Existing fixture assets | NO | high | `H3-NARROW-AUTHORING` |
| `MANGA-NARROW-RESULT` | Manga | NARROW | RESULT AVAILABLE | CURRENTLY OBSERVABLE | Same safe result at 430 x 850 | Existing result/history | None | NO | high | `H3-NARROW-RESULT` |
| `H3-EMPTY` | H3 | WIDE | EMPTY/FIRST-LAUNCH | CURRENTLY OBSERVABLE | Owner H3 shell with an empty Create draft | Empty Preview/Create shell | None | NO | baseline | `MANGA-EMPTY` |
| `H3-AUTHORING` | H3 | WIDE | AUTHORING WITH CONTENT | CURRENTLY OBSERVABLE | H3 Video/Still/Prep Create draft with text-only controls | Existing H3 shell/source behavior | None or existing safe slot | NO | highest | `MANGA-AUTHORING` |
| `H3-REFERENCE` | H3 | WIDE/NARROW | REFERENCE/ATTACHMENT PRESENT | CURRENTLY OBSERVABLE | Use an existing safe Start/End/Still/Prep/R2V slot asset | Existing local reference asset | H3 reference slot | NO | after authoring | `MANGA-REFERENCE` |
| `H3-BUSY` | H3 | WIDE | GENERATING/BUSY | CURRENTLY OBSERVABLE | Existing active job or bounded source fixture only; do not create a new job | Existing status/overlay evidence | None | NO (fixture only) | conditional | `MANGA-BUSY` |
| `H3-RESULT` | H3 | WIDE | RESULT AVAILABLE | PARTIALLY OBSERVABLE | Select an existing local completed history/result; record unavailable if absent | Existing local result/history | None | NO | high | `MANGA-RESULT` |
| `H3-ERROR` | H3 | WIDE | ERROR | CURRENTLY OBSERVABLE | Existing backend disconnected/profile mismatch/failed history state | Existing safe error evidence or source-observable state | None | NO | conditional | `MANGA-ERROR` |
| `H3-DIRTY` | H3 | WIDE/NARROW | CHANGED SINCE LAST RESULT | PARTIALLY OBSERVABLE | Select a result, edit mode settings, and record whether divergence is exposed | Existing history/settings restore behavior | None | NO | conditional | `MANGA-DIRTY` |
| `H3-FOCUS` | H3 | NARROW | FOCUSED RESULT | PARTIALLY OBSERVABLE | Use the existing narrow Result view selection with a safe result | Existing history/result only | None | NO | record boundary | `MANGA-FOCUS` |
| `H3-NARROW-AUTHORING` | H3 | NARROW | AUTHORING WITH CONTENT | CURRENTLY OBSERVABLE | Same draft at 430 x 850; select Create view | Existing H3 narrow Create behavior | Existing safe slot only | NO | high | `MANGA-NARROW-AUTHORING` |
| `H3-NARROW-RESULT` | H3 | NARROW | RESULT AVAILABLE | PARTIALLY OBSERVABLE | Same safe result at 430 x 850; select Result view | Existing result/history required | None | NO | high | `MANGA-NARROW-RESULT` |

## Reproduction and provenance fields

Every screenshot or cited artifact should carry these fields in a sidecar
manifest or review note:

| Field | Required value |
| --- | --- |
| State ID | One ID from the table above. |
| Domain | `MANGA` or `H3`; never a combined engine state. |
| Route/tab | Owner route, direct Manga workspace, embedded Manga, or H3 mode/tab. |
| Viewport | `WIDE`/`NARROW` plus exact pixel dimensions. |
| Fixture/result | Name or local path of the existing fixture/result, or `NONE`. |
| Attachment/reference | Existing local asset identifier, or `NONE`. |
| Generation needed | `NO`; if a state would require a new generation, mark it unavailable for this card. |
| Evidence age | `FRESH REVIEW CAPTURE` or `PRIOR LOCAL ARTIFACT`. |
| Observable text | Exact visible status/result label when available. |
| Notes | Limitations, missing result, or partial observability. |

## Component contract cross-check

This matrix uses the contract labels from
`TEGAKI_UI_COMPONENT_CONTRACTS.md`.

| Contract | Classification | Observable evidence | Boundary for Astra |
| --- | --- | --- | --- |
| `MediaPreviewShell` | PARTIAL | Manga `.mg-stage` and H3 preview/stage containers | Record composition and continuity; no shared component is assumed. |
| `PreviewFocus` | NOT IMPLEMENTED (Manga); PARTIAL (H3) | H3 narrow Result selection is related; Manga remains a normal preview | Do not treat a view switch as the full focus contract. |
| `GenerationStatus` | VISIBLE_CURRENTLY | Manga `READY`, `SUBMITTING`, `GENERATING`, `FAILED`, `UNKNOWN`; H3 backend/job labels | Compare truthfulness and proximity, not wording preference. |
| `ProgressProjection/Overlay` | PARTIAL | H3 status/elapsed overlay; Manga status/job labels | A unified projection is not present. |
| `AttachmentCard` | VISIBLE_CURRENTLY | Manga CAST/Guide references; H3 Start/End/Still/Prep/R2V slots | Compare interaction grammar while retaining domain semantics. |
| `CompactContext` | PARTIAL | Preview labels, history summaries, and reference summaries | No dedicated shared context projection is implemented. |

## Capture naming

Use `output/ui-review/astra_ui/` for future local captures. The deterministic
form is `<domain>_<viewport>_<state>.png`, for example
`manga_wide_authoring.png` and `h3_narrow_result.png`. Existing artifacts under
`output/ui-review/2026-09-15/MANGA-UX-CLEANUP2/` keep their original names and
must be marked `PRIOR LOCAL ARTIFACT`.

## Review order and comparison prompts

Capture in this order when safe: Manga ordinary authoring, H3 ordinary
authoring, result-present pairs, narrow pairs, reference/attachment pairs, then
already-available error/progress states. For each pair record, without
answering, whether the evidence exposes:

- INTENT, SUBJECT, SPACE/STRUCTURE, CONTROL, and OUTPUT;
- Create versus Preview and GLANCE versus FOCUS;
- context compression and domain identity;
- Generate/status proximity and truthful progress;
- result continuity and current-result versus unsent-edit distinction;
- narrow reachability and ordering.

These prompts support a later adversarial review. They are not acceptance
criteria for a layout in this card.
