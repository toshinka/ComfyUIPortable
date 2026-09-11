# IP2-R1B Browser Prep/Edit Evidence

Evidence date: `2026-09-11 JST`

Classification: **PASS WITH KNOWN NATIVE LIMIT**

Live baseline before the H3-only closeout: `f8dd087a1946da80cf070eda4bb137fc1408d085`

## Acceptance boundary

The rendered Browser acceptance ran only at `http://127.0.0.1:8190/`.
Chrome extension access to the `file://` scheme was not enabled and no
`file://` navigation or external upload was used.

The authorized budget was exactly:

```text
Source local upload: 1
Donor local upload: 1
Source-only Prep generation: 1
Source + Donor Prep generation: 1
Total real Prep generations: 2
```

The Source and final Donor selection both used the supported Browser direct
file-input route. The original Donor path was present and hash-valid, but the
Browser harness rejected the first path fetch with `Failed to fetch` before any
asset was accepted. An exact-content, non-destructive copy with the same hash
was placed under `output/h3/tests/` and selected once. This is recorded as a
harness limitation, not a product upload failure. The Source was selected once
and was not reuploaded.

## Authorized inputs

| Role | File | SHA-256 | Size | Browser result |
|---|---|---|---:|---|
| Source | `output/h3/tests/reference_robot_v1.png` | `43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E` | 206821 | Direct file input, accepted once |
| Donor original | `output/h3/still/h2a_native_still_00004_.png` | `4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0` | 193442 | Present and hash-verified |
| Donor selected copy | `output/h3/tests/ip2_donor_4338866a.png` | `4338866A7E230F79B08E696571F9321F8E910DA17C0296E9C58C96D89451B6F0` | 193442 | Direct file input, accepted once |

Both images are `608 x 352` PNG files. The original Donor was not modified.
The copy is ignored runtime data and is not part of the committed evidence.

## Browser generation results

| Case | Job / Native prompt | Seed | Elapsed | Output / SHA-256 | Visual result |
|---|---|---:|---:|---|---|
| Source-only | `0ff31f0035564c289fd396b77d98980e` / `0c9b7097-e63a-4d40-a58d-5b097ca07fe5` | 20260911 | 136.17 s | `output/h3/still/ip1_native_image_prep_00004_.png` / `78E35745D3E5379E12DA8B0177AAEA0B556245E43FA5B58EF4E7D55A68789A64` | Source preservation STRONG; rainy change OBSERVED; drift MODERATE |
| Source + Donor | `845c3088cf3d4a2b9b4451fd195e59a5` / `8dd5de78-a615-4db6-9579-964bc5c29ed9` | 20260912 | 41.15 s | `output/h3/still/ip1_native_image_prep_00005_.png` / `FA299AC1077F0B0C003D18FD1A5C211DBC98CD0F065AD179496AD9B7C9DADB85` | Source preservation STRONG; donor influence NOT CONVINCING; over-transfer LOW; composition drift LOW |

Both outputs are `608 x 352` PNG files. Preview reached completion and public
History used the route labels `Prep · Source` and `Prep · Source + Donor`.
The user prompt remained separate from the materialized Picture-role prefix.
No retry was run.

## Handoff and isolation

```text
History Use settings, Source-only: PASS
History Use settings, Source + Donor: PASS
Edit in Prep: PASS; result became Prep Source
Edit in Prep auto-generation: NONE
Source-generation prompt copied automatically: NO
Use as Character: PASS; Video Reference · Experimental with Generated Still
Use as Character auto-generation: NONE
Video → Prep/Edit → Video: PASS
Still → Prep/Edit → Still: PASS
Prep/Edit → other lens → Prep/Edit: PASS
Public filesystem paths: NONE
File-scheme permission change: NO
```

The Donor was visibly separate and marked `Experimental`. Public metadata used
opaque IDs only. The two real generations are the complete Browser budget; no
ordinary Still, Standard Video, Reference Video, or extra Prep run was added.

## Runtime and regression evidence

The first uncorrected click was a pre-submit HTTP 400 caused by a stale plain
8188 backend resolving the input root and audio VAE namespace incorrectly. It
submitted no job and created no output. The skin on 8190 remained alive while
the backend was replaced with the existing isolated `h3/run_h3.bat` contract.
No tracked product or workflow change was required.

```text
Post-run free VRAM sample: approximately 639959080 bytes
Total VRAM sample: approximately 12878086144 bytes
Peak/minimum VRAM: NOT INSTRUMENTED
OOM: 0
Accepted-job retry: 0

IP2 targeted Python: 27 PASS
IP2 UI verifier: 45 PASS
VP2C UI: 36 PASS
VP2B UI: 28 PASS
H2C UI: 52 PASS
H1C UI: 38 PASS
H1B.1 P2 UI: 44 PASS
H1B.1 P1 UI: 36 PASS
VP1 UI: PASS
Full H3 Python discovery: 75 PASS
JavaScript syntax: PASS
Python compileall: PASS
Workflow JSON parse: 7 PASS
git diff --check: PASS
```

No generated PNG, runtime copy, model, cache, local configuration, temporary
harness, or Manga file is committed.

Manifest: [manifest.json](manifest.json)

Report: [IP2_BROWSER_PREP_EDIT_LENS_REPORT.md](../../../reports/IP2_BROWSER_PREP_EDIT_LENS_REPORT.md)

Canonical hub: [docs/h3/README.md](../../../README.md)

IP2 implementation: `PUBLISHED ON MAIN` in existing published history

Manga changes in this closeout: `NONE`

Owner acceptance: `PENDING`

STOP after the authorized two-generation Browser acceptance budget.
