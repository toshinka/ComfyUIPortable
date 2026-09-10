# VP2B — Experimental R2V Playground evidence

Evidence package date: `2026-09-10`

Browser execution: `2026-09-11 JST`

Decision: `PASS WITH KNOWN NATIVE LIMIT`

Implementation: `PUBLISHED ON MAIN` at
`cfc8161ab0399338824e175b95ea0763281d57e6`

Owner acceptance remains `PENDING`. Closeout docs and the bounded verifier-
compatibility fix are local until Owner push.

Report: [VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md](../../../reports/VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md)

Manifest: [manifest.json](manifest.json)

## Authorized local inputs

The only Browser uploads were performed through the local H3 UI at
`http://127.0.0.1:8190/`:

```text
Character Image:
D:\GitHub\tegaki\ComfyUIPortable\output\h3\tests\reference_robot_v1.png
bytes: 206821
sha256: 43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E

Motion Video:
D:\GitHub\tegaki\ComfyUIPortable\output\h3\video\h1a_native_t2v_00010_.mp4
bytes: 471184
sha256: 412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254
ffprobe: 608x352 / 124 frames / 24 fps / 5.166667 s
```

External upload: `NONE`. The two runtime inputs remain uncommitted.

## Browser Reference run

Exactly one real Browser Picture+Motion job was submitted after selecting
`Video → Reference · Experimental`, uploading the two authorized inputs, and
entering a plain-language prompt. The fixed settings were `608 x 352`, `5 s`,
and `20 steps`.

```text
H3 job: bf6caf68e77440f3b0142efc1e6352c2
Native prompt: 9f5c05ca-7f40-4c69-8254-9dce84ab1cb0
route: native_ref2va
picture id: 46c6a569ef4140f8beab783673fe84ba
motion id: f6194e4971cf4a6cb5654f43655108d7
created: 2026-09-11 00:07:09 JST
completed: 2026-09-11 00:14:48 JST
elapsed: 459.74 s
seed: 8375238270079288501
```

User prompt:

```text
A small red service robot walks slowly through a quiet workshop while the camera tracks gently from left to right.
```

Materialized Ref2VA prompt:

```text
Use <Picture 1> for the subject identity and appearance.
Use <Video 1> for motion, timing, and camera behavior.
A small red service robot walks slowly through a quiet workshop while the camera tracks gently from left to right.
```

The UI retained the original prompt. The completed Preview played through the
Browser video element; its decoded current time advanced from `0.0` to about
`0.81 s`. History showed `Completed · Reference · Picture + Motion` and did not
expose filesystem paths. `Use settings` restored Video/Reference, the original
prompt, seed, both assets, and fixed settings without submitting a new job.
The Reference History card had no Continue action.

## Reference media and runtime observation

```text
output: output/h3/video/vp2b_r2v_reference_00001_.mp4
sha256: 499A18B21BE35A53C0CCD82C80C4C0A7BAFC46E237816F6A0D7E4C77F784FEF9
ffprobe: 608x352 / 124 encoded frames / 24 fps / 5.166667 s
sample interval: approximately 5 s
peak observed VRAM used: 11418 MiB
minimum observed free VRAM: 595 MiB
OOM: 0
accepted-job retry: 0
```

The native process completed normally. No retry or runtime tuning was used.

Visual review against the authorized sources:

```text
Picture influence: OBSERVED
Video influence: NOT CONVINCING
```

The output retained the red/white compact robot appearance, while the orange
greenhouse robot and distinctive motion/environment of the Motion Video were
not convincingly carried through. This is recorded as a known Native
mixed-reference quality limit; the valid Browser result was not regenerated.

## State, Still, and Standard checks

```text
Standard → Reference → Standard: PASS
  Standard Start/End remained empty; Standard resolution/duration returned to
  608x352 / 5s.

Reference → Standard → Reference: PASS
  Character Image and Motion Video selections remained present.

Still isolation: PASS
  Video Type, Reference Character/Motion, Standard Start/End, and Duration were
  hidden; Still Source Image remained the Still-only control.
```

## Post-Reference Standard baseline

Exactly one Standard Text-only Browser baseline completed after switching back
to `Video → Standard`:

```text
H3 job: 1acbcf5e168f4e8b820f30bf8dd47587
Native prompt: b24baae7-0074-430b-ae64-d28d51108c81
route / label: native_t2v / Text only
settings: 608x352 / 5s / 20 steps; Start/End empty
elapsed: 175.51 s
output: output/h3/video/h1a_native_t2v_00017_.mp4
sha256: 94B38EC69C5C90A9666CC3FCBBC388AF6CCFD8A761C80C0844E5D32D2E82BFAB
ffprobe: 608x352 / 124 frames / 24 fps / 5.166667 s
playback: PASS
History: Reference + Text only present
```

The built-in Ref2VA → FL2VA/T2V transition worked without restart. Standard
telemetry observed peak VRAM use `11378 MiB`, minimum free `635 MiB`, OOM `0`,
retry `0`.

## Verification

```text
VP2B targeted contract tests: 5 PASS
VP2B UI smoke: 28 PASS
VP1 verifier: PASS
H2C verifier: 52 PASS
H1C verifier: 38 PASS
H1B.1 UX P2 verifier: 44 PASS
H1B.1 UX P1 verifier: 36 PASS
Full Python unittest discovery: 60 PASS
JavaScript syntax: PASS
Python compileall: PASS
JSON parse: PASS
git diff --check: PASS
```

The only bounded post-acceptance fix preserved VP1/H2C static verifier markers
while retaining the same UI behavior. No additional generation was needed.

No second Picture, multiple Motion Video, audio, roles UI, masks, guides,
Image Prep, LoRA, model selector, Studio, Shot, Timeline, Project, Storyboard,
VP2C/VP3, shared ComfyUI changes, or Manga changes are included.
