# VP2A — Native Ref2VA / R2V Feasibility evidence

Date: 2026-09-10 JST

Decision: `FEASIBLE WITH LIMITS`

Previous acquisition-gate publication: `PUBLISHED ON MAIN` at
`e4e078490cd2f96a953e6261399f268652d49c04`. R1 updates to this report and
evidence package are `LOCAL MAIN / PUSH PENDING`. VP1 publication is recorded
separately as `PUBLISHED ON MAIN` at
`41da0bf804d049adc40e2ae2d5abfdd59eabc703`.
Owner acceptance remains `PENDING`.

Report: [VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md](../../../reports/VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md)

Manifest: [manifest.json](manifest.json)

## R1 execution result

The later explicit Owner authorization was applied to the exact artifact only:

```text
minimax_h3_ref2va_pruned_int8_convrot.safetensors
bytes: 20,970,379,616
sha256: 9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779
destination: E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors
```

The official pinned revision was checked, the file was transferred once, and
the observed size and SHA-256 matched exactly. No new license click-through,
gated agreement, credential, unrelated model, or external video download was
used. Native ComfyUI ran isolated on `127.0.0.1:8189` with ComfyUI `0.30.0`,
embedded Python `3.13.14`, PyTorch `2.13.0+cu130`, and an NVIDIA GeForce RTX
4070 (`12282 MiB` reported VRAM).

The bounded adapter and runner are local only:
`h3/adapters/native_ref2va.py`,
`workflows/h3/VP2A_NATIVE_REF2VA_BASE.json`, and
`h3/tests/run_vp2a_ref2va.py`. They use one Picture and optionally one Video
through the official `MiniMaxH3ReferenceToVideo` node. Reference audio lanes
remain disconnected.

Picture source: `output/h3/tests/reference_robot_v1.png`, SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`.
Motion source: existing verified local H1A output
`output/h3/video/h1a_native_t2v_00010_.mp4`, SHA-256
`412B6F8EC11AA09BE770AC6B1EEAE31E77768AA584A22D40AA108C90EAF84254`,
ffprobe `608x352 / 124 frames / 24 fps / 5.167 s`. Its audio was not used as a
reference.

All three rows used `608x352`, `124 frames`, `24 fps`, `5.0 s`, `20 steps`,
seed `20260910`, `ref_image_size=match`, `res_multistep`, and `simple`.
Telemetry was sampled approximately every two seconds.

| Row | Prompt ID | Output / SHA-256 | ffprobe | Elapsed | Peak VRAM / min free | Working set | OOM / retry | Visual / result |
|---|---|---|---|---:|---:|---:|---:|---|
| Picture-only | `f201dc61-48ac-4ae4-be1c-59d4668e211d` | `output/h3/video/vp2a_r1_ref2va_picture_00001_.mp4` / `A3C4899BFDFA63084031D885B6EAA17B97149D108796638AC26E55CF6962202F` | `608x352 / 124 / 24 / 5.167 s` | `238.09 s` | `11669 / 344 MiB` | `44,376,182,784 bytes` | `0 / 0` | `PICTURE REF INFLUENCE OBSERVED` |
| Picture + Video | `8a9d8a84-7c38-4bea-9e20-3038dbf738b0` | `output/h3/video/vp2a_r1_ref2va_picture_video_00001_.mp4` / `790392A527A4C13DF65092FB57887C31D386AF5F7A404F40A7AB3C1FC424851E` | `608x352 / 124 / 24 / 5.167 s` | `375.46 s` | `11678 / 335 MiB` | `45,711,646,720 bytes` | `0 / 0` | `PICTURE REF INFLUENCE NOT CONVINCING`; `VIDEO REF INFLUENCE OBSERVED` |
| Standard FL2VA/T2V transition | `1b457097-b2cc-4284-a89c-24aa971e0c67` | `output/h3/video/vp2a_r1_transition_fl2va_00001_.mp4` / `CF2E69472CA11EB03151DF1B725B0EF215CA5668271116E956AAA8ED8A8D1222` | `608x352 / 124 / 24 / 5.167 s` | `175.99 s` | `11657 / 356 MiB` | `46,405,963,776 bytes` | `0 / 0` | `BUILT-IN MODEL TRANSITION PASS` |

Picture-only retained the red compact robot appearance. In the matched
Picture+Video output, the motion reference's orange robot and greenhouse
framing dominated: Video influence was observed, while Picture appearance
influence was not convincing. This is a reference-role limitation, not an
identity-preservation claim. Reference-video audio was `NOT USED`; standalone
audio was `NOT TESTED`.

The final classification is `FEASIBLE WITH LIMITS`: both Native Ref2VA rows
and the one required return to standard FL2VA/T2V completed on the RTX 4070
12GB stack, but the observed free-VRAM margin was only `335–356 MiB`, each
row took several minutes, and matched Picture+Video appearance fidelity was
not convincing.

## Visual review artifacts

These contact sheets contain first/middle/last sampled frames. They are visual
review evidence only; the source MP4s and staged runtime inputs remain under
`output/h3/` and are not committed.

- [Picture-only contact sheet](picture_only_contact_sheet.png) — Picture influence observed.
- [Motion reference contact sheet](motion_reference_contact_sheet.png) — local verified H1A source.
- [Picture + Video contact sheet](picture_plus_video_contact_sheet.png) — Video influence observed; Picture influence not convincing.
- [FL2VA/T2V transition contact sheet](transition_contact_sheet.png) — transition output.

## R1 verification and boundary

```text
VP1 verifier: PASS
H2C verifier: 52 PASS
H1C verifier: 38 PASS
H1B.1 UX P2 verifier: 44 PASS
H1B UI verifier: 36 PASS
Embedded Python unittest discovery: 55 tests, OK
JavaScript syntax: PASS (five existing H3 static JS files)
Embedded Python compileall -q h3: PASS
VP2A/workflow JSON parse: PASS
git diff --check: PASS
Browser generation regression: NOT RERUN (no Browser source changed)
```

No new dependency, custom node, shared ComfyUI change, Image Prep, LoRA,
Manga, or UI/Studio surface was added. The isolated Native process was
stopped after the run. Recommended next direction: `Owner review of VP2A-R1
evidence and acceptance decision`. Do not start VP2B automatically.

## Historical acquisition-gate result

The exact Native Ref2VA model was not present in the approved external H3
model library:

```text
E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors
expected bytes: 20,970,379,616
expected SHA-256: 9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779
result: NOT FOUND
```

The targeted scan under `E:\Data\Models\StableDiffusion\minimaxH3` returned
zero exact filename hits. The diffusion directory contained the existing
FL2VA file only. The same exact filename was absent from the Portable
`h3/model_store/` and `ComfyUI/models/` checks. No download, replacement,
license acceptance, or model copy was attempted.

H0/H0.1 evidence records the MiniMax H3 Community License Agreement and its
territory/use/redistribution review requirement. It also records Ref2VA as
explicitly deferred and not acquired. No exact Owner authorization for this
artifact is recorded, so the acquisition gate is `OWNER ACTION REQUIRED`.

## Historical native source audit

`ComfyUI/comfy_extras/nodes_minimax_h3.py` contains the installed
`MiniMaxH3ReferenceToVideo` source contract. It declares one `ref_images`
AutoGrow group with a maximum of 9, one `ref_videos` group with a maximum of 3,
three same-index `ref_video_audios`, and three standalone `ref_audios`. It also
declares `ref_image_size` values `match` and `max`, and returns positive
conditioning plus an AV latent. The source audit is `PASS`; runtime node
loading and generation are `NOT TESTED` because the exact model is absent and
unauthorized.

## Historical stage status at original gate

```text
Stage A Picture-only: NOT TESTED
Stage B Picture + one Video: NOT TESTED
Picture influence: NOT TESTED
Video influence: NOT TESTED
12GB/OOM/retry telemetry: NOT TESTED / NOT RECORDED
Post-Ref2VA T2V transition: NOT TESTED
Browser R2V UI: NOT IMPLEMENTED
MP4/model artifacts in evidence: NONE
Owner acceptance: PENDING
STOP BEFORE DOWNLOAD
```

The approved local H3 robot Picture and prior VP1 motion outputs were not
consumed in this stopped pass. No external reference video was downloaded.

Docs-only validation: VP2A and updated VP1 manifests parse as JSON, targeted
`git diff --check` is `PASS`, and no stale VP1 `LOCAL MAIN` publication wording
remains in the corrected canonical/report/evidence files.
