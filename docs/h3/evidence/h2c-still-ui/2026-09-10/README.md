# H2C — Still UI Browser Acceptance evidence

Date: 2026-09-10 JST

Status: `IMPLEMENTED + VERIFIED SOURCE/LOGIC + VERIFIED BROWSER UI`

Stage: `H2C / Still UI vertical slice`

Base implementation commit: `2b167493ee83df2a4f80c10669d9c4e4387e111e`

Additional fix commit: `0df5f865` — preserve 64-bit Still seeds as lossless
strings across the Python/JSON/JavaScript boundary.

Report: [H2C_STILL_UI_VERTICAL_SLICE_REPORT.md](../../../reports/H2C_STILL_UI_VERTICAL_SLICE_REPORT.md)

Owner acceptance: `PENDING`

Publication of this evidence package: `PUBLISHED ON MAIN` (verified in the
current `origin/main` at `224c37b9`). Owner acceptance remains separate.

## Scope

This package records the bounded H2C Browser acceptance flow:

```text
Video text-only regression
  -> Still prompt-only Browser result
  -> authorized local source upload through the real H3 Browser UI
  -> source-anchored Still Browser result
  -> History Use settings restore
  -> Video/Still mode isolation
  -> mixed History and active-job/preview-job separation
  -> desktop visual review
```

The Still lens adds one Source Image slot to the existing H3 skin. It does not
claim production native T2I/I2I semantics, a fidelity control, REF2VA, ordered
multi-reference, LoRA, Segment, Studio, Timeline, Storyboard, Cast, 3D, or
Manga integration.

## Browser target and source authorization

| Field | Observed value |
|---|---|
| Skin | `http://127.0.0.1:8191/` |
| Native ComfyUI | `http://127.0.0.1:8189/` |
| Browser control | Codex in-app Browser CUA/Playwright; an additional Chrome tab for desktop visual review |
| Authorized source | `D:\GitHub\tegaki\ComfyUIPortable\output\h3\tests\reference_robot_v1.png` |
| Upload path | real `#still-source-add` file chooser in the H3 Browser UI |
| Source id | `5e76ec7b142f437893500c49cab7a9b4` |
| Source dimensions | `608 x 352` |
| Source SHA-256 | `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E` |

The source was approved by the Owner for this local Browser acceptance. It was
not sent to an external service. The runtime-staged copy and generated media
remain ignored under `output/h3/`; only the bounded PNG evidence copies below
are committed.

## Browser acceptance record

### Prompt-only Still

The prompt-only Still was submitted through the Still Generate button with no
source image selected. The Browser showed an image Preview, `Still`, and no
Duration or Continue control.

| Field | Observed value |
|---|---|
| Job | `1103a35a3d6b4bf6aab4f8f190466361` |
| Prompt id | `c8571b2d-f0c9-4619-a887-9558d5a244b8` |
| Route | `native_still` / `Text only` |
| Prompt | `A small paper robot standing in warm maroon light, clean studio composition` |
| Resolution / steps | `608 x 352` / `20` |
| Elapsed | `109.39s` |
| Runtime output | `output/h3/still/h2a_native_still_00002_.png` |
| Output SHA-256 | `8CCDEFD9A4B074830CBBCB9905837FE6C5EE081D168A6EDD900DEFAD5248AEAAD` |

Evidence copy: [prompt_only.png](prompt_only.png).

### Source Image upload and source-anchored Still

The authorized PNG was selected through the actual Browser file chooser. The
selected thumbnail reported `608 x 352`; after submission the Browser showed a
real generated image, `Source Image · Completed`, and the corresponding History
card.

| Field | Observed value |
|---|---|
| Job | `4690d19f469f4580bca852410e4e5e2` |
| Prompt id | `525aed3e-5c54-49f7-9738-23d41d9b189f` |
| Route | `native_source_anchored_still` / `Source Image` |
| Prompt | `A small paper robot standing in a leafy greenhouse, warm red body, gentle studio light` |
| Resolution / steps | `608 x 352` / `20` |
| Seed | `1522422703298925749` (lossless string in the public JSON) |
| Source id | `5e76ec7b142f437893500c49cab7a9b4` |
| Elapsed | `35.44s` |
| Runtime output | `output/h3/still/h2b_source_anchor_00006_.png` |
| Output bytes | `281765` |
| Output SHA-256 | `CA72A4BA640B90C8A3C271CBFCA9C6D8262BE8530AF74B778C812FBD6D386B4E` |

Evidence copies: [source.png](source.png) and
[source_anchored.png](source_anchored.png).

The generated output was visually reviewed as a plausible source-influenced
robot/greenhouse result. This is bounded qualitative observation only; no CLIP
score, identity score, fidelity percentage, or production consistency claim is
made.

### History `Use settings`

On the fixed Browser run, the source Still History card was selected after
deliberately changing the prompt and seed. The UI announced `Settings loaded.`
and the read-only form inspection returned:

```text
mode = still
prompt = A small paper robot standing in a leafy greenhouse, warm red body, gentle studio light
resolution = 608x352
seed = 1522422703298925749
steps = 20
duration card = hidden
source thumbnail = present
```

The attempted steps mutation was rejected by the read-only UI control; the
prompt and seed mutation were sufficient to prove restoration. No generation
was triggered by `Use settings`.

### Mode crossing and reference isolation

Immediately after the fixed `Use settings` check, switching to Video preserved
the existing Video Start/End references:

```text
Start = /api/references/6793f62c617841c58d178c851cdac450
End   = /api/references/6aa1536a378b467a94485fad9bf115e6
Still source = retained in the hidden Still lens
Video Duration = visible
```

Switching back to Still retained the Source Image thumbnail and hid Duration.
The two Video references were then intentionally removed only to make the
required text-only Video regression cheap and unambiguous; that later removal
is not a mode-crossing failure.

### Cross-media active job / preview job

After the Video regression completed, a new Source Image Still job was started.
While the Browser showed `Running`, `Cancel current job`, and queue `1`, the
completed Video History card was selected. The Preview changed to:

```text
Text only · Completed in 130.3s · 608 x 352 · 5s
```

while the authoritative status remained `Running` for the active Still job.
When that Still job completed, the Preview returned to a generated Still image
with:

```text
Source Image · Completed in 35.4s · 608 x 352
```

and History contained three entries in newest-first order: Still, Video, Still.
This verifies the separate Active Job and Preview History authorities across
media kinds.

### Video regression

The post-restart regression was a Browser-submitted text-only Video job. It was
needed because the restart cleared the in-memory History required by the
cross-media acceptance; no new Video capability was added.

| Field | Observed value |
|---|---|
| Job | `08bc7292717646ba9281faae7a3c932d` |
| Prompt id | `f4c5d9ee-78af-494a-8b7d-533616933eb2` |
| Route | `native_t2v` / `Text only` |
| Prompt | `A red kite drifting above a quiet paper city, gentle camera movement` |
| Resolution / duration / steps | `608 x 352` / `5s` / `20` |
| Elapsed | `130.34s` |
| Runtime output | `output/h3/video/h1a_native_t2v_00009_.mp4` (ignored) |
| Output bytes | `255026` |
| Output SHA-256 | `26ACC5A5F1F3374BC007E90D34EDE541B6AC3897F3B2B463C389288B900CCFF9` |

The Browser rendered an actual video Preview with playback controls and a
`Completed · Text only` History card. The MP4 is intentionally not committed.

## Desktop visual acceptance

Video and Still were both reviewed in a Chrome desktop tab. The visual checks
were:

| Check | Result |
|---|---|
| Preview remains visually dominant | `PASS` |
| Generate remains before Advanced in the desktop composition | `PASS` |
| Still does not fill removed Duration/End-Frame space with new controls | `PASS` |
| Video keeps Reference + Duration density | `PASS` |
| MAROON Generate, mode selection, and card ramp | `PASS` |
| Still Source Image card and Video Reference card are distinct | `PASS` |

The acceptance target was the primary `1280 x 720` desktop composition. The
Chrome extension host reported an effective CSS content viewport of `1083 x
557` despite the requested viewport override, so an exact `1280 x 720` CSS
viewport readback is not claimed. The full-page desktop captures and measured
layout still showed the intended target composition; in Video the Generate
button rect was `y=669.14..717.14`, and the Still full-page capture showed the
same primary-action placement. The limitation is recorded rather than hidden.

Screenshots were observed directly in the CUA Browser and were not serialized
as fake local files. The committed PNG evidence above is the reproducible media
evidence; the Browser visual observations remain a separate acceptance layer.

## Runtime telemetry

Verified stack: NVIDIA GeForce RTX 4070, `12878086144` bytes total VRAM,
`68476002304` bytes total system RAM, embedded Python `3.13.14`, PyTorch
`2.13.0+cu130`, ComfyUI `0.30.0`, custom nodes disabled, isolated H3 model
store.

For the fixed source-anchored Browser run, 5-second `/api/status` samples
observed minimum free VRAM of `4660450860` bytes (`4444.6 MiB`), which derives
to `7836.9 MiB` observed peak used from the reported total. OOM count was `0`
and accepted-job retry count was `0`. For the later cross-media Still run,
the sampled minimum free VRAM was `4649273804` bytes; OOM and retry were also
`0`. These are sampled values, not hardware peak guarantees.

## Verification

- `node h3/tests/verify_h2c_still_ui.mjs` — `52 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- Embedded Python `unittest discover -s h3/tests -p 'test_*.py'` — `48 tests, OK`.
- `node --check h3/app/static/app.js` and
  `node --check h3/app/static/still-history-settings.js` — `PASS`.
- `python_embeded/python.exe -m compileall -q h3` — `PASS`.
- `git diff --check` — `PASS`.

## Boundary

H2C is a bounded Browser-facing Still UI vertical slice over the H2B source
route. It does not establish production I2I, a source-strength/fidelity
control, multi-reference semantics, or Owner acceptance. The H2C implementation,
fix, evidence, and closeout package are published on `main`; publication
remains distinct from `OWNER ACCEPTED = PENDING`.
