# VP1 — Video Practicalization Safe Resolution / Duration Envelope evidence

Date: 2026-09-10 JST

Decision: `PASS`

Status: `IMPLEMENTED + VERIFIED NATIVE MATRIX + VERIFIED BROWSER UI + VERIFIED
HISTORY RESTORE + VERIFIED STILL ISOLATION`

Publication: `LOCAL MAIN` for the VP1 implementation and this evidence package.
The H2C package was separately verified as published in the current
`origin/main` at `224c37b9`. Owner acceptance remains `PENDING`.

Report: [VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md](../../../reports/VP1_VIDEO_RESOLUTION_DURATION_ENVELOPE_REPORT.md)

Manifest: [manifest.json](manifest.json)

## Decision and boundary

VP1 exposes only two new Video enum choices, selected from existing official /
Native H3 patterns and admitted only after real Native T2V and fixed-slot
Start+End FL2VA generation:

| Axis | Candidate | Basis | Result |
|---|---|---|---|
| Duration-only | `608 x 352 / 15 seconds` | Native H3 tooltip trained-range upper rung: `362` frames, about 15 seconds | `UI VERIFIED` |
| Resolution-only | `736 x 416 / 5 seconds` | Official/native 16:9 `0.3 MP` size-settings rung | `UI VERIFIED` |

The unchanged baseline control is `608 x 352 / 5 seconds / 20 steps`.
Still remains `608 x 352` only and has no Duration field. No new model,
dependency, quantization/offload path, custom node, shared ComfyUI change, or
Manga change was introduced.

## Native frame and media contract

The existing Native H3 graph and `ComfyUI/comfy_extras/nodes_minimax_h3.py`
remain the authority. The adapter uses the existing `17k+5` frame grid at
24 fps:

```text
5 seconds  -> 124 Native frames -> 5.1666667 Native seconds -> ffprobe 5.167s
15 seconds -> 362 Native frames -> 15.0833333 Native seconds -> ffprobe 15.083333s
```

All six matrix runs returned the requested width/height, expected encoded
frame count, 24 fps, and the expected Native duration. The exact output hashes,
prompt IDs, and sampled telemetry are in [manifest.json](manifest.json).

| Case | Route | Requested | Native / encoded | ffprobe | Elapsed | Peak VRAM used | OOM / retry |
|---|---|---|---|---|---:|---:|---:|
| baseline-t2v | T2V | 608x352 / 5s | 124 / 124 | 608x352 / 24 / 5.167s | 166.24s | 11503 MiB | 0 / 0 |
| baseline-fl2va | Start+End | 608x352 / 5s | 124 / 124 | 608x352 / 24 / 5.167s | 147.81s | 11269 MiB | 0 / 0 |
| duration-15s-t2v | T2V | 608x352 / 15s | 362 / 362 | 608x352 / 24 / 15.083333s | 552.23s | 11004 MiB | 0 / 0 |
| duration-15s-fl2va | Start+End | 608x352 / 15s | 362 / 362 | 608x352 / 24 / 15.083333s | 579.51s | 11157 MiB | 0 / 0 |
| resolution-736x416-t2v | T2V | 736x416 / 5s | 124 / 124 | 736x416 / 24 / 5.167s | 189.13s | 11121 MiB | 0 / 0 |
| resolution-736x416-fl2va | Start+End | 736x416 / 5s | 124 / 124 | 736x416 / 24 / 5.167s | 224.13s | 10606 MiB | 0 / 0 |

Environment: NVIDIA GeForce RTX 4070, 12,878,086,144 bytes VRAM,
68,476,002,304 bytes system RAM, ComfyUI `0.30.0`, embedded Python
`3.13.14`, PyTorch `2.13.0+cu130`, custom nodes disabled, isolated H3 model
store. Telemetry is sampled observation, not a hardware peak guarantee.

The approved Start+End input was the local
`output/h3/tests/reference_robot_v1.png` staged as
`inputs/h2b_source_43d29d07b5d0b4a2.png`, SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`.

## Browser acceptance

Browser control: Codex in-app Browser through CUA/Playwright, skin
`http://127.0.0.1:8192/`, Native backend `http://127.0.0.1:8189/`.

The live accessibility tree showed these config-driven controls in Video:

```text
Resolution: 608 x 352; 736 x 416
Duration:   5 seconds; 15 seconds
```

After switching to Still, the live tree showed only `608 x 352`, Source Image,
and no Duration field. Switching back to Video restored both Video resolution
choices and both Duration choices. This verifies that Video config options do
not leak into Still.

The three required Browser generation cases completed visibly through the
Generate button and appeared in History:

| Case | Browser result | Job | Output / ffprobe |
|---|---|---|---|
| baseline | `Text only · Completed in 125.7s · 608 x 352 · 5s` | `ade3fd1860a64ba68b8bf044c6665c4d` | `h1a_native_t2v_00013_.mp4`, 608x352 / 124 / 24 / 5.167s |
| duration | `Text only · Completed in 558.1s · 608 x 352 · 15s` | `d0db87f0654a41a2b9adc790ab2c838f` | `h1a_native_t2v_00014_.mp4`, 608x352 / 362 / 24 / 15.083333s |
| resolution | `Text only · Completed in 179.1s · 736 x 416 · 5s` | `58cf0211964b484fb79e9669eac2758c` | `h1a_native_t2v_00015_.mp4`, 736x416 / 124 / 24 / 5.167s |

The three option-generation records were captured before the final Video
seed-publication correction. The correction changes only the JSON/UI seed
boundary, not the accepted resolution/duration enums or Native graph. A
post-correction 736x416/5s Browser run completed as
`Text only · Completed in 190.0s · 736 x 416 · 5s` with job
`1cd7c04a13594771b415021a8eb86655`; its public History seed was the lossless
string `4654562559140587881` and its output was `h1a_native_t2v_00016_.mp4`.

## History and failure behavior

The first candidate History click exposed a real boundary defect: the
pre-correction Video History public JSON represented a random 64-bit seed as a
JavaScript-unsafe number. The UI correctly failed closed and did not mutate
the form. The minimal correction now serializes Video seeds as decimal strings,
accepts decimal strings when submitting, and validates the `0..2^63-1` range
with `BigInt` during History restore.

After the correction, the Browser form was deliberately changed to
`608 x 352 / 15 seconds`, then the 736x416/5s History card's `Use settings`
was clicked. The UI showed `Settings loaded.` and the readback was:

```text
resolution = 736x416
duration   = 5
seed       = 4654562559140587881
History    = 1 before / 1 after
generation = not triggered
```

The VP1 JavaScript smoke also verifies 608x352/15 restore with a lossless
decimal seed and rejects unsupported 864x480 and 10-second History values
before mutation. Continue uses the same supported Video scalar set, preserves
resolution/duration, captures only the completed result's end frame, clears
End Frame, and does not auto-generate; the existing H1C source/logic verifier
remains `38 PASS`.

## Verification

- `python_embeded/python.exe -m unittest discover -s h3/tests -p 'test_*.py'` — `51 tests, OK`.
- `node h3/tests/verify_vp1_video_ui.mjs` — `PASS`.
- `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- `node h3/tests/verify_h2c_still_ui.mjs` — `52 PASS`.
- `node --check` for all five `h3/app/static/*.js` files — `PASS`.
- `python_embeded/python.exe -m compileall -q h3` — `PASS`.
- `git diff --check` — `PASS`.

## Viewport, publication, and closeout

The requested Browser target was exact CSS `1280 x 720`. The CUA in-app
Browser did not provide an exact CSS viewport readback, so this evidence says
`NOT AVAILABLE / CUA HOST LIMIT`; no exact viewport claim is made. The live
visual review still showed the Preview as the dominant surface, visible
completion metadata, Generate before Advanced, and the expected Video/Still
control separation.

VP1 source/code/docs are local and unpushed. Generated MP4s, runtime inputs,
models, and caches remain outside the evidence package and are not committed.
H2C publication is a separate verified fact: its seed fix/evidence/report
commits are ancestors of current `origin/main` `224c37b9`. Neither publication
status replaces Owner acceptance.

Owner acceptance: `PENDING`

STOP. Next direction: Owner review, acceptance, and normal publication of the
VP1 local package; do not issue a later feature Card until that review is done.
