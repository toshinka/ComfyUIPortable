# H2C — Still UI Vertical Slice Closeout

Date: 2026-09-10 JST

## Decision

```text
H2C STILL UI VERTICAL SLICE: PASS WITH RECORDED VIEWPORT LIMIT
Classification: bounded Browser-facing Still UI over the H2B source route
Owner acceptance: PENDING
```

The H3 skin now exposes a bounded Still lens with prompt-only and one-source
Source Image paths. The requested local source was uploaded through the actual
Browser UI, both Still paths reached visible completed Previews, History
`Use settings` restored the source form without auto-generating, Video and Still
state remained isolated, and the active Still job stayed authoritative while a
completed Video History Preview was selected.

The additional seed fix was required to close the first incomplete Browser
check: H2A/H2B seeds are 64-bit integers, so returning them as JSON numbers
could lose precision in JavaScript and make `Use settings` fail closed. Still
public metadata and the Still form path now preserve the seed as a validated
decimal string. The fix is recorded separately from the existing H2C
implementation.

## Status distinction

| Status | Result | Meaning |
|---|---|---|
| `IMPLEMENTED` | `PASS` | H2C Still lens, source upload, source-anchored route, History restore, and state separation are present. |
| `VERIFIED SOURCE/LOGIC` | `PASS` | Static, server, seed-losslessness, fail-closed, and regression contracts pass. |
| `VERIFIED BROWSER STILL PROMPT-ONLY` | `PASS` | A Browser-submitted no-source Still reached a visible completed image Preview. |
| `VERIFIED BROWSER STILL SOURCE-ANCHORED` | `PASS` | The Owner-authorized local PNG reached a visible completed Source Image Still Preview and History card. |
| `VERIFIED STILL USE SETTINGS` | `PASS` | Deliberate prompt/seed mutations were restored atomically; `Settings loaded.` appeared and no job was submitted. |
| `VERIFIED CROSS-MEDIA STATE` | `PASS` | Running Still remained active while a completed Video History result was previewed; completion returned the Still Preview. |
| `VERIFIED VIDEO REGRESSION` | `PASS` | Browser text-only Video regenerated after the backend restart and produced a playable Preview. |
| `PUBLISHED ON MAIN` | `PASS for base implementation` | H2C base commit `2b167493...` and H2-INFRA history are present in the current `origin/main`; this new fix/evidence package is local until Owner push. |
| `OWNER ACCEPTED` | `PENDING` | Technical and Browser evidence does not replace Owner acceptance. |

## 1. Implementation and boundary

Base implementation: `2b167493ee83df2a4f80c10669d9c4e4387e111e`.

Additional fix: `0df5f865`.

The bounded path is:

```text
Still prompt
  -> /api/still/generate
  -> existing H2A/H2B Native workflow surface
  -> selected frame 0
  -> PNG Preview / History
```

For Source Image:

```text
one Browser-uploaded local PNG/JPEG
  -> /api/still/source
  -> one source_id
  -> H2B first_frame edge
  -> five-frame temporal packet
  -> selected frame 0 PNG
```

The UI has one source slot only. It does not introduce a source-strength or
fidelity control. It does not claim native single-image latent I2I, REF2VA,
ordered generic multi-reference, LoRA, Segment, Studio, Timeline, Storyboard,
Cast, 3D, Manga, project persistence, or external service integration.

The only source-code change after the base implementation was the lossless
Still seed boundary fix plus its contract tests. Video seed handling remains
on its existing numeric path because the H1A/H1B Video contract is unchanged.

## 2. Browser acceptance

Browser target:

```text
Skin:   http://127.0.0.1:8191/
Native: http://127.0.0.1:8189/
Tool:   Codex CUA/Playwright Browser UI
```

The source was the explicitly authorized local file
`output/h3/tests/reference_robot_v1.png`. It was set through the real
`#still-source-add` file chooser, not by a direct server/API shortcut and not
sent outside the local H3 runtime.

### Prompt-only Still

| Field | Result |
|---|---|
| Job / prompt id | `1103a35a3d6b4bf6aab4f8f190466361` / `c8571b2d-f0c9-4619-a887-9558d5a244b8` |
| Route | `native_still` / `Text only` |
| Resolution / steps | `608 x 352` / `20` |
| Elapsed | `109.39s` |
| Output SHA-256 | `8CCDEFD9A4B074830CBBCB9905837FE6C5EE081D168A6EDD900DEFAD5248AEAAD` |
| UI result | image Preview, Still semantics, no Duration, no Continue |

### Source-anchored Still

| Field | Result |
|---|---|
| Job / prompt id | `4690d19f469f4580bca852410e4e5e2` / `525aed3e-5c54-49f7-9738-23d41d9b189f` |
| Route | `native_source_anchored_still` / `Source Image` |
| Prompt | `A small paper robot standing in a leafy greenhouse, warm red body, gentle studio light` |
| Resolution / steps | `608 x 352` / `20` |
| Seed | `1522422703298925749` as a lossless JSON string |
| Source id | `5e76ec7b142f437893500c49cab7a9b4` |
| Elapsed | `35.44s` |
| Output | `h2b_source_anchor_00006_.png`, 281765 bytes |
| Output SHA-256 | `CA72A4BA640B90C8A3C271CBFCA9C6D8262BE8530AF74B778C812FBD6D386B4E` |
| UI result | generated image Preview and `Completed · Source Image` History card |

The selected source is `608 x 352`, with SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`.

The generated image was visually plausible as a source-influenced robot in a
greenhouse. This is bounded qualitative visual evidence only. CLIP, identity,
fidelity percentage, and production consistency were not measured.

## 3. History `Use settings`

The fixed Browser run used Source Image History job
`8eac0d62fa4b471a8f562a0420bd8dc3` after deliberately changing the prompt and
seed. The UI returned `Settings loaded.` and a read-only form inspection
returned:

```text
mode = still
prompt = A small paper robot standing in a leafy greenhouse, warm red body, gentle studio light
resolution = 608x352
seed = 1522422703298925749
steps = 20
duration = absent/hidden
source thumbnail = present
```

No generation occurred from `Use settings`. The previously failing unsafe
64-bit numeric-seed case is covered by `verify_h2c_still_ui.mjs` and the server
contract tests.

## 4. Mode crossing and active-job/preview-job separation

After the fixed Still restore, switching to Video preserved the existing
references:

```text
Start = /api/references/6793f62c617841c58d178c851cdac450
End   = /api/references/6aa1536a378b467a94485fad9bf115e6
Still source = retained in the hidden Still lens
Video Duration = visible
```

Switching back to Still retained the Source Image thumbnail and hid Duration.
The two Video references were then intentionally removed solely to make the
required post-restart text-only Video regression unambiguous; this later
cleanup is not a mode-crossing failure.

For the cross-media check, a Source Image Still job was started and the
Browser showed `Running`, `Cancel current job`, and queue `1`. Selecting the
completed Video History card changed only the Preview to:

```text
Text only · Completed in 130.3s · 608 x 352 · 5s
```

The active status remained `Running` for Still. After completion, the active
Still Preview returned:

```text
Source Image · Completed in 35.4s · 608 x 352
```

History then contained three entries in newest-first order: Still, Video,
Still. This is the required separation between the authoritative active job
and the selected History Preview job.

## 5. Video regression

The post-restart Video run was needed because the restart cleared the in-memory
History required for the cross-media check. It did not add a new capability.

| Field | Result |
|---|---|
| Job / prompt id | `08bc7292717646ba9281faae7a3c932d` / `f4c5d9ee-78af-494a-8b7d-533616933eb2` |
| Route | `native_t2v` / `Text only` |
| Resolution / duration / steps | `608 x 352` / `5s` / `20` |
| Elapsed | `130.34s` |
| Output | `h1a_native_t2v_00009_.mp4`, 255026 bytes, ignored |
| Output SHA-256 | `26ACC5A5F1F3374BC007E90D34EDE541B6AC3897F3B2B463C389288B900CCFF9` |
| UI result | actual video playback Preview and `Completed · Text only` History card |

No MP4 is committed.

## 6. Desktop visual review

Both Video and Still were reviewed in a Chrome desktop tab. The observed
checks were:

| Check | Result |
|---|---|
| Preview remains visually dominant | `PASS` |
| Generate precedes Advanced | `PASS` |
| Still does not replace removed Duration/End-Frame space with new controls | `PASS` |
| Video preserves Reference + Duration density | `PASS` |
| Generate and mode selection remain in the MAROON family | `PASS` |
| Still Source Image and Video Reference cards are visibly distinct | `PASS` |

The requested target was the primary `1280 x 720` desktop composition. The
Chrome CUA host reported an effective CSS viewport of `1083 x 557` despite an
explicit desktop viewport request, so this report does not claim an exact
`1280 x 720` CSS readback. The full-page desktop captures and measured layout
were used to review the target composition; the Video Generate rect was
`y=669.14..717.14`, and the Still full-page capture showed the same primary
action placement. This host limitation is recorded as a qualification, not
silently promoted to an exact viewport measurement.

## 7. Runtime telemetry

Verified stack: NVIDIA GeForce RTX 4070, `12878086144` bytes total VRAM,
`68476002304` bytes total system RAM, embedded Python `3.13.14`, PyTorch
`2.13.0+cu130`, ComfyUI `0.30.0`, custom nodes disabled, isolated H3 model
store.

For the fixed source-anchored Browser run, 5-second `/api/status` samples
observed minimum free VRAM of `4660450860` bytes (`4444.6 MiB`). Subtracting
that sampled minimum from the reported total derives `7836.9 MiB` observed
peak used. The later cross-media Still run sampled minimum free VRAM of
`4649273804` bytes. OOM count was `0`; accepted-job retry count was `0`.
These are sampled observations, not hardware peak guarantees.

## 8. Verification

The final post-acceptance verification returned:

- `node h3/tests/verify_h2c_still_ui.mjs` — `52 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- Embedded Python `unittest discover -s h3/tests -p 'test_*.py'` — `48 tests, OK`.
- `node --check h3/app/static/app.js` — `PASS`.
- `node --check h3/app/static/still-history-settings.js` — `PASS`.
- `python_embeded/python.exe -m compileall -q h3` — `PASS`.
- `git diff --check` — `PASS`.

## 9. Evidence and publication

Evidence README:
[docs/h3/evidence/h2c-still-ui/2026-09-10/README.md](../evidence/h2c-still-ui/2026-09-10/README.md)

Machine-readable manifest:
[docs/h3/evidence/h2c-still-ui/2026-09-10/manifest.json](../evidence/h2c-still-ui/2026-09-10/manifest.json)

Committed PNG evidence:

- [source.png](../evidence/h2c-still-ui/2026-09-10/source.png)
- [prompt_only.png](../evidence/h2c-still-ui/2026-09-10/prompt_only.png)
- [source_anchored.png](../evidence/h2c-still-ui/2026-09-10/source_anchored.png)

The H2C base implementation is published in the current `origin/main` history
through `2b167493...`; the seed fix is local commit `0df5f865`. The evidence,
report, and canonical-index updates in this closeout are also local until the
Owner performs the normal push and verifies the public raw/GitHub URLs.

## Final report format

```text
H2C STILL UI VERTICAL SLICE: PASS WITH RECORDED VIEWPORT LIMIT

IMPLEMENTED: PASS
VERIFIED SOURCE/LOGIC: PASS
VERIFIED BROWSER STILL PROMPT-ONLY: PASS
VERIFIED BROWSER STILL SOURCE-ANCHORED: PASS
VERIFIED STILL USE SETTINGS: PASS
VERIFIED CROSS-MEDIA STATE: PASS
VERIFIED VIDEO REGRESSION: PASS
PUBLISHED ON MAIN: base implementation PASS; new fix/evidence LOCAL MAIN
OWNER ACCEPTED: PENDING
```
