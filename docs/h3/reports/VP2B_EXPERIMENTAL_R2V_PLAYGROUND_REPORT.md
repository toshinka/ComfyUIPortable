# VP2B — Experimental R2V Playground

Date: 2026-09-10 evidence package; Browser acceptance executed 2026-09-11 JST

Current Stage: `VP2B / Experimental R2V Playground Closeout`

Classification: `PASS WITH KNOWN NATIVE LIMIT`

Base remote `origin/main` at acceptance: `cfc8161ab0399338824e175b95ea0763281d57e6`

VP2B implementation: `PUBLISHED ON MAIN` at
`cfc8161ab0399338824e175b95ea0763281d57e6`

Owner acceptance: `PENDING`

## 1. Scope and contract

VP2B adds a compact secondary `Video Type` choice inside the existing H3
Video mode. `Standard` remains the default and keeps its existing Start Frame,
End Frame, resolution, duration, History, and Continue behavior. `Still` keeps
its H2C Source Image path and does not expose the Video Type controls.

The experimental Reference path is deliberately bounded to:

```text
Character Image: exactly one required PNG/JPEG/WebP
Motion Video: zero or one optional MP4
Resolution: 608 x 352 (server-enforced)
Duration: 5 seconds (server-enforced)
Steps: 20 (server-enforced)
Route: native_ref2va → MiniMaxH3ReferenceToVideo
Audio reference: not connected
```

Uploads are stored behind server-issued opaque IDs. Public History exposes
asset IDs and display names, not filesystem paths. Motion audio is ignored and
no audio UI or extraction path was added. The Reference path does not expose a
model selector, cache manager, restart control, LoRA, Image Prep, or memory
optimization setting.

The plain-language user prompt is retained separately from the deterministic
Ref2VA materialization. The Browser acceptance used:

```text
USER PROMPT
A small red service robot walks slowly through a quiet workshop while the camera tracks gently from left to right.

MATERIALIZED REF2VA PROMPT
Use <Picture 1> for the subject identity and appearance.
Use <Video 1> for motion, timing, and camera behavior.
A small red service robot walks slowly through a quiet workshop while the camera tracks gently from left to right.
```

No LLM or aesthetic prompt iteration was used.

## 2. Authorized Browser Reference acceptance

The Owner authorization covered only these existing local files and the local
H3 Browser at `http://127.0.0.1:8190/`:

| Input | Bytes | SHA-256 | Use |
|---|---:|---|---|
| `output/h3/tests/reference_robot_v1.png` | 206,821 | `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E` | Character Image |
| `output/h3/video/h1a_native_t2v_00010_.mp4` | 471,184 | `412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254` | Motion Video |

No external upload occurred. Neither input is committed.

The exact Browser path was completed once: `Video → Reference · Experimental
→ Character Image → Motion Video → plain prompt → Generate → completion →
playback`. The UI showed the required upload previews, fixed disabled
Reference settings, `Running`, then `Completed`.

| Item | Result |
|---|---|
| H3 job ID | `bf6caf68e77440f3b0142efc1e6352c2` |
| Native prompt ID | `9f5c05ca-7f40-4c69-8254-9dce84ab1cb0` |
| Route | `native_ref2va` |
| Reference asset IDs | Picture `46c6a569ef4140f8beab783673fe84ba`; Motion `f6194e4971cf4a6cb5654f43655108d7` |
| Created / completed | `2026-09-11 00:07:09` / `00:14:48 JST` |
| Elapsed | `459.74 s` |
| Settings | `608 x 352 / 5 s / 20 steps` |
| Seed | `8375238270079288501` |
| Upload / submit | PASS |
| Preview playback | PASS; decoded video advanced from `0.0` to approximately `0.81 s` while playing |
| History route label | `Reference · Picture + Motion` |
| History filesystem-path exposure | NONE |
| Use settings | PASS; prompt, Reference mode, both asset selections, seed, and fixed settings restored without a new job |
| Continue on Reference result | ABSENT |

The History entry retained the original user prompt and separately recorded the
materialized prompt. `Use settings` verified both server asset endpoints before
mutating the form and showed `Settings loaded.`; queue remained `0` and the
session History count remained `1`.

## 3. Reference media and telemetry

Output: `output/h3/video/vp2b_r2v_reference_00001_.mp4`

```text
SHA-256: 499A18B21BE35A53C0CCD82C80C4C0A7BAFC46E237816F6A0D7E4C77F784FEF9
ffprobe: 608 x 352 / 124 encoded frames / 24 fps / 5.166667 s
```

Telemetry was sampled locally at approximately five-second intervals using
H3 `/api/status` and `nvidia-smi` during the accepted job:

| Metric | Observation |
|---|---:|
| Sample interval | approximately 5 s |
| Peak observed VRAM used | 11,418 MiB |
| Minimum observed free VRAM | 595 MiB |
| OOM count | 0 |
| Accepted-job retry count | 0 |

The run completed normally. No stress test, clean retry, or runtime tuning was
performed.

## 4. Visual classification

The extracted early/middle/late output frames were reviewed against the two
authorized inputs. The Reference output retained a red compact service-robot
body and a white rounded head consistent with the Character Image, so:

```text
Picture influence: OBSERVED
```

The Motion Video showed an orange front-face robot in a greenhouse. The
Reference output instead showed the red/white robot in a workshop and did not
convincingly carry the Motion Video's subject/environment or its distinctive
turn. A lateral camera movement is visible, but it is not attributable to the
Motion Video rather than the plain prompt, so:

```text
Video influence: NOT CONVINCING
```

This is recorded as a known Native mixed-reference quality limitation. The
technically valid Browser route was not regenerated for aesthetics.

## 5. State isolation and Still boundary

The Browser checks passed without additional generation:

```text
Standard → Reference → Standard:
  Standard Start/End remained empty; 608 x 352 and 5 seconds were restored.

Reference → Standard → Reference:
  reference_robot_v1.png and h1a_native_t2v_00010_.mp4 remained selected.

Still:
  Video Type, Reference Character Image, Reference Motion Video, Standard
  Start/End, and Duration were hidden; H2C Still Source Image remained the
  Still-only input.
```

## 6. Post-Reference Standard regression

Exactly one post-Reference Standard Text-only Browser baseline completed:

| Item | Result |
|---|---|
| H3 job ID | `1acbcf5e168f4e8b820f30bf8dd47587` |
| Native prompt ID | `b24baae7-0074-430b-ae64-d28d51108c81` |
| Route / label | `native_t2v` / `Text only` |
| Settings | `608 x 352 / 5 s / 20 steps`; Start/End empty |
| Elapsed | `175.51 s` |
| Output | `output/h3/video/h1a_native_t2v_00017_.mp4` |
| Output SHA-256 | `94B38EC69C5C90A9666CC3FCBBC388AF6CCFD8A761C80C0844E5D32D2E82BFAB` |
| ffprobe | `608 x 352 / 124 frames / 24 fps / 5.166667 s` |
| Playback | PASS; decoded video advanced from `0.0` to approximately `0.79 s` while playing |
| History | PASS; both Reference and Text-only entries present |

The built-in Ref2VA → FL2VA/T2V transition completed without restart. The
Standard History card exposed Continue, while the Reference card did not.
Standard telemetry observed peak VRAM use `11,378 MiB`, minimum free
`635 MiB`, OOM `0`, retry `0`.

## 7. Verification

The VP2B Browser run was followed by the bounded verifier-compatibility fix in
`h3/app/static/app.js`. It preserves the existing VP1/H2C static markers while
keeping the same Standard/Reference/Still behavior; no generation graph or
Reference contract changed. The affected verifiers were rerun successfully.

| Check | Result |
|---|---|
| VP2B targeted contract tests | 5 PASS |
| VP2B UI smoke | 28 PASS |
| VP1 verifier | PASS |
| H2C verifier | 52 PASS |
| H1C verifier | 38 PASS |
| H1B.1 UX P2 verifier | 44 PASS |
| H1B.1 UX P1 verifier | 36 PASS |
| Full Python unittest discovery | 60 PASS |
| JavaScript syntax | PASS |
| Python compileall | PASS |
| JSON parse | PASS |
| `git diff --check` | PASS |

## 8. Boundary and publication

Implementation commit `cfc8161ab0399338824e175b95ea0763281d57e6` is published on
`main` and is H3-only relative to `f482b90d124c39f603f6863ac35aefb586e95bfd`.
The closeout report, dated evidence, canonical H3 wording, and the bounded
verifier-compatibility fix are published on `main` at
`543d8c2c2817743b10f255c168047e4edd1781a9`. The preceding Browser acceptance
snapshot was taken against `cfc8161ab0399338824e175b95ea0763281d57e6`; that
historical baseline is retained above. No Manga files, shared ComfyUI
core/frontend, model weights, local YAML, runtime uploads, or MP4 files are
included.

The next direction is exactly one: `Owner hands-on evaluation of Experimental
R2V Playground`. Do not start VP2C/VP3 or multi-reference work from this report.

Owner acceptance: `PENDING`

STOP
