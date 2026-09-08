# H3 Reference Implementation Evaluation Index

更新: 2026-09-08 JST
Current gate: `H0.1 / model and dependency isolation / generation smoke`

## Purpose

This index separates the original H0 startup/source audit from the H0.1
model-backed generation evidence. It is the Web GPT entry for checking official
provenance, isolated runtime boundaries, fixed-task outputs, and candidate
comparison. It does not declare a candidate adopted and does not replace Owner
acceptance.

## Read first

1. [H3 model acquisition manifest](H3_MODEL_ACQUISITION_MANIFEST.md)
2. [H0.1 generation evaluation report](../reports/H3_REFERENCE_IMPLEMENTATION_GENERATION_EVALUATION_REPORT.md)
3. The candidate-specific `2026-09-08_generation/README.md` and `manifest.json`
4. [Historical H0 startup/source report](../reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md)

## Environment and boundary

- Repository: `https://github.com/toshinka/tegaki`
- Portable Python: 3.13.14
- Local ComfyUI vendor: 0.30.0, detached commit
  `b1693ecba9f5b65f8c80ab36b195ab963ec92413`
- GPU: NVIDIA GeForce RTX 4070, 12,282 MiB
- System RAM: 68,476,002,304 bytes total (`63.77 GiB`)
- First-wave H3 model store: `h3/model_store/` only
- Shared `ComfyUI/models/`, shared `custom_nodes/`, core/frontend, and Manga
  runtime: unchanged
- REF2VA and all non-first-wave assets: not acquired
- Production output namespace: `output/h3/video/`; large model/video payloads
  are ignored and not committed

## Candidate result matrix

| Candidate | H0 startup/history | H0.1 generation | Task | Output / blocker | Current evidence |
|---|---|---|---|---|---|
| Native / official ComfyUI | `VERIFIED LOCAL` startup and native H3 registry | `VERIFIED LOCAL GENERATION` | T2V | `h0_1_native_t2v_baseline_00001_.mp4`; SHA-256 `5BC170464C283FF060F3B897AE5DA8B7E5915B565091820D78DC13B1DD6B2251` | [generation](reference-implementations/native/2026-09-08_generation/README.md) / [manifest](reference-implementations/native/2026-09-08_generation/manifest.json) |
| H3 Easy | H0 source/runtime boundary audit | `VERIFIED LOCAL GENERATION` in disposable runtime | I2V | `h0_1_h3easy_i2v_00001_.mp4`; SHA-256 `E297EEF9EDCF33635F1068906A41A145585A99AF5A7F05A5A94FEAFE7ADF9D74` | [generation](reference-implementations/h3-easy/2026-09-08_generation/README.md) / [manifest](reference-implementations/h3-easy/2026-09-08_generation/manifest.json) |
| onigirikiller H3 Studio | H0 dependency blocker, later resolved only in dedicated venv | `VERIFIED LOCAL GENERATION` for UI/API plus Native backend | T2V | `h3studio_2d947385_00001_.mp4`; SHA-256 `69EF473198FA4C58C948E948BE259F13E18DE867ACF081AAEE856E27D623B7F0` | [generation](reference-implementations/onigirikiller/2026-09-08_generation/README.md) / [manifest](reference-implementations/onigirikiller/2026-09-08_generation/manifest.json) |
| AntaresAlice H3 WebUI | `VERIFIED LOCAL` UI/status startup | `BLOCKED` candidate-native generation | I2V request | HTTP 400: `MiniMaxH3AudioConditioningT8` not found; no output | [generation](reference-implementations/antares/2026-09-08_generation/README.md) / [manifest](reference-implementations/antares/2026-09-08_generation/manifest.json) |

## Common task

```text
A small red service robot with a round white head walks slowly through a quiet greenhouse. The camera tracks gently from left to right. Leaves move slightly in the air. Soft mechanical footsteps and subtle greenhouse ambience.
```

- Resolution: `608x352`
- Frames/FPS: `124 / 24`
- Duration: `5.167 s`
- Steps: `20`
- Sampler/scheduler: `res_multistep / simple`
- Seed: `20260908`
- Turbo LoRA: disabled

Native and onigirikiller are T2V. H3 Easy uses the Native first frame as an I2V
reference. Antares reached backend validation but did not sample.

## Evidence categories

- `VERIFIED LOCAL STARTUP`: HTTP/UI/API or native registry was reproduced.
- `VERIFIED LOCAL GENERATION`: a local request completed and its output hash,
  ffprobe result, and frame/contact-sheet evidence are recorded.
- `BLOCKED`: a concrete dependency, missing node, model, or evaluation boundary
  stopped the relevant path.
- `NOT TESTED`: no claim is made about an unexercised behavior.
- `OWNER ACTION REQUIRED`: technical evidence exists but license/application or
  production acceptance remains with the Owner.

## 12GB and license gate

- Native conservative sampled peak: `11,651 / 12,282 MiB`; no OOM.
- H3 Easy and onigirikiller completed on the same 12GB-class host with no OOM,
  but their candidate-specific peak samples were not retained and are not
  inferred from the Native number.
- Antares failed before sampling; no memory result exists.
- The four official first-wave file hashes match. License restrictions require
  Owner/legal confirmation before redistribution or broader use. See the [manifest](H3_MODEL_ACQUISITION_MANIFEST.md).

## Historical H0 records

The following dated files are intentionally preserved as startup/source history;
they are not rewritten to pretend that the earlier no-model gate contained the
later generation results:

- [Native H0 startup](reference-implementations/native/2026-09-08/README.md)
- [H3 Easy H0 source boundary](reference-implementations/h3-easy/2026-09-08/README.md)
- [onigirikiller H0 dependency boundary](reference-implementations/onigirikiller/2026-09-08/README.md)
- [Antares H0 startup](reference-implementations/antares/2026-09-08/README.md)
- [Historical H0 report](../reports/H3_REFERENCE_IMPLEMENTATION_EVALUATION_REPORT.md)

## Next gate

Web GPT may review the H0.1 evidence and decide whether a later bounded H1
ingredient card is warranted. Stop here: no H1 implementation, Astra rerun,
REF2VA download, custom-node installation into the shared runtime, or Owner
acceptance is implied.
