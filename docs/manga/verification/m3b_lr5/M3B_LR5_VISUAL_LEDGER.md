# M3B-LR5 Visual Ledger

Visual evidence was reviewed from the local files and the live ComfyUI browser
at `http://127.0.0.1:8188/view`. This is coarse Figure/placement review only;
it makes no biometric identity claim.

## Fixed visual criteria

- `cast_1`: short dark hair; intended left / standing near the left window.
- `cast_2`: long light hair; intended right / seated near the right desk.
- Character Instance areas remain regional text-conditioning areas.
- Figure areas remain Guide-derived ControlNet locality provenance.
- `REGIONAL_CONTROL_CONFLICT` records visible interaction failure between the
  Character regional path and the Figure-masked ControlNet path.

## Four-output ledger

| Seed | Condition | Two-Figure presence | Placement | Figure count | Side association | Acting | Quality | Conflict | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 42 | CAST_OFF | present | CLEAR | PASS | MIXED | WEAK | USABLE | NONE | Large left foreground Figure and smaller right Figure; right-side seated acting is not established. |
| 42 | CAST_MASKED | present | CLEAR | PASS | PASS | WEAK | DEGRADED | CLEAR | Short-dark-haired Figure is coarse-left and long-light-haired Figure coarse-right, but both are standing/back-facing; hard vertical mask-aligned boundaries are visible. |
| 77 | CAST_OFF | present with extra | CLEAR | FAIL | MIXED | WEAK | USABLE | NONE | Left standing, center seated, and right long-haired Figure-like presence; extra/duplicate presence fails the two-Figure criterion. |
| 77 | CAST_MASKED | present with extra/faint | CLEAR | FAIL | MIXED | WEAK | DEGRADED | CLEAR | Main left/right Figures remain, but left/right acting is reversed and a faint extra Figure-like silhouette plus hard vertical mask-aligned boundaries remain. |

## Aggregate

- `CAST_OFF` placement: `CLEAR`
- `CAST_OFF` Figure count: `FAIL`
- `CAST_MASKED` placement: `CLEAR`
- `CAST_MASKED` Figure count: `FAIL`
- `CAST_MASKED` quality: `DEGRADED`
- `SIDE_ASSOCIATION`: `MIXED`
- `REGIONAL_CONTROL_CONFLICT`: `CLEAR`
- `Seed variation`: `PRESENT`
- Hard ControlNet-mask artifact: `PRESENT`

The masked condition improves coarse left/right Figure presence over the
seed-77 OFF output, but it does not preserve the intended acting relationship
and introduces a repeatable hard-rectangle failure signature. The combination
therefore fails the Card's `CAST_MASKED_COMPATIBLE` criteria.

## Provisional result

`CAST_MASKED_CONFLICT`

No strength, timing, mask feathering, mask alignment, or per-Figure ControlNet
follow-up was performed.
