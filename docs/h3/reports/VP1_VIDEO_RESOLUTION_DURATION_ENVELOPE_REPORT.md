# VP1 — Video Practicalization Safe Resolution / Duration Envelope

Date: 2026-09-10 JST

Current Stage: `VP1`

Decision: `PASS`

Owner acceptance: `PENDING`

Evidence: [VP1 dated evidence](../evidence/vp1-video-envelope/2026-09-10/)

Manifest: [manifest.json](../evidence/vp1-video-envelope/2026-09-10/manifest.json)

## 1. Outcome

VP1 makes the existing Native H3 Video path practical for one bounded
resolution step and one bounded duration step on the local RTX 4070 / 64GB
RAM host. Both candidates passed the required Native matrix and then became
Browser-visible:

| Candidate | Native T2V | Native Start+End FL2VA | Browser | Classification |
|---|---|---|---|---|
| `608 x 352 / 15 seconds` | PASS | PASS | PASS | `UI VERIFIED` |
| `736 x 416 / 5 seconds` | PASS | PASS | PASS | `UI VERIFIED` |

The baseline control remains `608 x 352 / 5 seconds / 20 steps`.

The resulting advertised Video envelope is exactly:

```text
Resolution: 608 x 352, 736 x 416
Duration:   5 seconds, 15 seconds
FPS:        24
Steps:      20
```

No additional profile framework, arbitrary size input, duration slider, hidden
resize, model swap, quantization/offload path, or lower-step fallback was
introduced. Still remains the H2C path: `608 x 352`, no Duration, and no
automatic inheritance of Video options.

## 2. Candidate provenance and frame semantics

The candidate values were selected from existing official/Native H3 patterns,
not invented values:

- `15 seconds` is the upper end of the Native MiniMax H3 node tooltip's tested
  range, where `362` frames is approximately 15 seconds at 24 fps.
- `736 x 416` is the official/native 16:9 `0.3 MP` Size Settings Reference
  rung immediately above the existing `608 x 352` baseline.

The existing Native H3 conversion is retained:

```text
max(5, round(seconds * 24))
  + (5 - (max(5, round(seconds * 24)) % 17)) % 17
```

Therefore the user-facing seconds are deliberately not treated as encoded
container duration:

| Requested | Native length | Native duration at 24 fps | Observed ffprobe |
|---:|---:|---:|---:|
| 5 seconds | 124 frames | 5.1666667 seconds | 5.167 seconds |
| 15 seconds | 362 frames | 15.0833333 seconds | 15.083333 seconds |

The Native authority is the existing
`ComfyUI/comfy_extras/nodes_minimax_h3.py` and the existing H1A/H1B.1 graphs.
The source/provenance hashes are recorded in the dated manifest.

## 3. Implementation

The implementation is intentionally limited to the existing Video boundary:

1. `h3/adapters/native_t2v.py` owns the two verified resolution enums and two
   verified duration enums. Validation rejects other values before graph
   submission.
2. `h3/app/server.py` exposes those exact adapter values through `/api/config`.
   Still config remains independently baseline-only.
3. `h3/app/static/app.js` populates Video controls from `/api/config`, keeps
   Still resolution isolated, and stores Video/Still resolution state
   separately across mode switches.
4. Video History `Use settings` validates the configured resolution/duration,
   reference assets, steps, prompt, and a lossless 64-bit seed before any form
   mutation. Continue uses the same supported Video scalars, captures the
   completed output's last frame into Start Frame, clears End Frame, and does
   not submit a generation.
5. Video public History JSON and Browser submission now keep seeds as decimal
   strings. This matches the existing H2C Still seed boundary and avoids
   JavaScript precision loss for Native's 64-bit seed range.

The new tests are bounded to the enum/API/History/Continue/Still contracts and
the new Native matrix runner. No shared ComfyUI, Manga, workflow, model, or
custom-node change was made.

## 4. Native runtime matrix

The matrix was run with the existing model store and existing workflows. The
approved local source
`output/h3/tests/reference_robot_v1.png` was staged as
`inputs/h2b_source_43d29d07b5d0b4a2.png` for Start+End Stage 2; its SHA-256 is
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`.

Execution rule: run baseline T2V and baseline Start+End; for each candidate,
run Stage 1 T2V and run Stage 2 Start+End only after Stage 1 passes. All six
runs passed, with zero OOM and zero retry. The table gives the observed
summary; full prompt IDs, hashes, and working-set samples are in the manifest.

| Case | Requested | Route | Native / encoded frames | Output dimensions / fps / duration | Elapsed | Peak VRAM used | OOM / retry |
|---|---|---|---:|---|---:|---:|---:|
| Baseline T2V | 608x352 / 5s | T2V | 124 / 124 | 608x352 / 24 / 5.167s | 166.24s | 11503 MiB | 0 / 0 |
| Baseline FL2VA | 608x352 / 5s | Start+End | 124 / 124 | 608x352 / 24 / 5.167s | 147.81s | 11269 MiB | 0 / 0 |
| Duration T2V | 608x352 / 15s | T2V | 362 / 362 | 608x352 / 24 / 15.083333s | 552.23s | 11004 MiB | 0 / 0 |
| Duration FL2VA | 608x352 / 15s | Start+End | 362 / 362 | 608x352 / 24 / 15.083333s | 579.51s | 11157 MiB | 0 / 0 |
| Resolution T2V | 736x416 / 5s | T2V | 124 / 124 | 736x416 / 24 / 5.167s | 189.13s | 11121 MiB | 0 / 0 |
| Resolution FL2VA | 736x416 / 5s | Start+End | 124 / 124 | 736x416 / 24 / 5.167s | 224.13s | 10606 MiB | 0 / 0 |

Environment: NVIDIA GeForce RTX 4070, 12,878,086,144 bytes VRAM,
68,476,002,304 bytes system RAM, ComfyUI `0.30.0`, embedded Python
`3.13.14`, PyTorch `2.13.0+cu130`, custom nodes disabled, and isolated H3
model store. The telemetry is sampled `/api/status` / `nvidia-smi` observation
and is not a hardware peak guarantee.

## 5. Browser unlock and acceptance

Browser control was Codex in-app Browser through CUA/Playwright against the
local skin at `http://127.0.0.1:8192/`, with Native backend at
`http://127.0.0.1:8189/`.

The live Browser accessibility tree showed both Video options:

```text
Resolution: 608 x 352; 736 x 416
Duration:   5 seconds; 15 seconds
```

The required Browser generation checks reached visible completed Preview and
History states:

| Case | Visible Browser result | Job ID |
|---|---|---|
| Baseline | `Text only · Completed in 125.7s · 608 x 352 · 5s` | `ade3fd1860a64ba68b8bf044c6665c4d` |
| Duration candidate | `Text only · Completed in 558.1s · 608 x 352 · 15s` | `d0db87f0654a41a2b9adc790ab2c838f` |
| Resolution candidate | `Text only · Completed in 179.1s · 736 x 416 · 5s` | `58cf0211964b484fb79e9669eac2758c` |

The corresponding MP4s were validated locally with ffprobe for dimensions,
encoded frames, 24 fps, and duration. They remain ignored runtime outputs and
are not in the evidence package.

### History correction and recheck

The first attempt to use the new candidate History entry found a real
boundary issue: the old Video public JSON represented a random Native 64-bit
seed as a JavaScript-unsafe number. The UI failed closed with
`Seed cannot be restored as a safe numeric value.` and did not partially change
the form. This was a useful negative test, not a candidate classification.

The minimal fix serializes Video seeds as decimal strings and accepts them as
validated decimal strings on submit/restore. After restarting the local skin,
a new 736x416/5s Browser run completed in 190.0s. Its History request carried
seed `"4654562559140587881"`. The form was changed to `608x352 / 15s`, then
`Use settings` restored:

```text
Settings loaded.
resolution = 736x416
duration   = 5
seed       = 4654562559140587881
History    = 1 before / 1 after
generation = not triggered
```

The JavaScript VP1 verifier also covers the Duration candidate
`608x352 / 15s`, unsupported resolution `864x480`, unsupported duration `10`,
and atomic/fail-closed handler ordering. The existing H1C Continue source and
logic verifier remains `38 PASS`.

### Still isolation

The Browser was switched to Still after the VP1 change. Its live tree showed
only `608 x 352`, Source Image, and no Duration field. Switching back to Video
showed both Video resolutions and both durations. This is also covered by the
Python API contract and VP1 UI smoke. No Video option is automatically
advertised to Still.

### Viewport and visual layer

The requested visual target was exact CSS `1280 x 720`. The CUA in-app Browser
did not provide an exact CSS viewport readback; the result is therefore
`NOT AVAILABLE / CUA HOST LIMIT`. No exact viewport claim is made. The live
visual review nevertheless showed the Preview as the dominant surface,
completion metadata over the video, Generate before Advanced, and the
Video/Still option separation.

## 6. Verification

| Layer | Result |
|---|---|
| VP1 Python enum/API tests | `51 tests OK` in full discovery, including H2A/H2B adapters |
| VP1 Browser/static/History/Continue/Still verifier | `PASS` |
| H1C regression verifier | `38 PASS` |
| H1B.1 UI regression verifier | `36 PASS` |
| H1B.1 P2 regression verifier | `44 PASS` |
| H2C Still regression verifier | `52 PASS` |
| JavaScript syntax | `PASS` for all 5 `h3/app/static/*.js` files |
| Python compileall | `PASS` |
| Git diff check | `PASS` |

## 7. Status distinction and publication

```text
LOCAL IMPLEMENTATION: PASS
NATIVE TECHNICAL/RUNTIME: PASS (6/6 matrix runs; OOM 0; retry 0)
BROWSER UI: PASS (baseline + duration + resolution; post-fix History recheck)
STILL ISOLATION: PASS
GITHUB PUBLICATION: VP1 LOCAL MAIN / NOT PUSHED
H2C PUBLICATION: PUBLISHED ON MAIN, verified at origin/main 224c37b9
OWNER ACCEPTED: PENDING
```

The VP1 changes are confined to the H3 adapter/server/UI/tests and this
report/evidence package. No MP4, model, runtime input, cache, or generated
asset is committed. GitHub push and Owner acceptance remain separate actions.

## 8. Closeout boundary

This PASS permits the named Video options only. It does not establish arbitrary
resolution, arbitrary duration, higher-resolution production support,
multi-reference or REF2VA semantics, source fidelity controls, new model
families, quantization/offload, DynamicVRAM/GGUF/Unsloth paths, Still expansion,
Segment, Studio, Timeline, Storyboard, Cast, 3D, Manga, or production
deployment.

STOP.

Next direction: Owner review, acceptance, and normal publication of the VP1
local package; do not issue a later feature Card until that review is complete.
