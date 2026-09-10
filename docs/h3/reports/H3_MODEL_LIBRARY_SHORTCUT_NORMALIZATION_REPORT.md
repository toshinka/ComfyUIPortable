# H3 Model Library / Shortcut Normalization Report

Date: 2026-09-10 JST
Stage: `H2-INFRA`
Status: `PASS` / `CONFIGURED` / `VERIFIED`
Infrastructure base commit: `bbb9f6720c9a4ed8fb7a029814bd10a5442542fd`
Closeout commit: this containing closeout commit; the final SHA is reported
with the Git closeout
Publication: `LOCAL MAIN / PUSH PENDING`
Owner acceptance: `PENDING`

## 1. Outcome

The H3 first-wave heavy model bodies now live in the intended external model
library. All four Portable source files were hash-verified against their
external copies, used by real H3 generation, and then removed under the exact
Owner authorization for this Card. No model was downloaded, no duplicate body
was retained, and no model body was copied into `ComfyUI/models/`.

The H3 capability gate remains H2B Source-Anchored Still / Single Reference
I2I Feasibility. No Still UI, LoRA UI or generation support, REF2VA,
multi-reference, Manga, Timeline, Studio, resolution, duration, or memory
feature was added.

## 2. Final status

```text
H3 MODEL LIBRARY NORMALIZATION: PASS

H2B publication: PUBLISHED ON MAIN
H3 external model library: CONFIGURED / VERIFIED
Portable duplicate heavy weights: REMOVED
Portable fallback namespace: RETAINED / EMPTY OF FIRST-WAVE HEAVY WEIGHTS
Model shortcuts: CONFIGURED LOCAL
Still UI: NOT STARTED
Owner acceptance: PENDING
```

The machine-readable evidence is in
[model-library/2026-09-10](../evidence/model-library/2026-09-10/), including
[inventory.json](../evidence/model-library/2026-09-10/inventory.json) and
[migration_manifest.json](../evidence/model-library/2026-09-10/migration_manifest.json).

## 3. Physical and logical model map

| Asset | ComfyUI category | Canonical physical location | Size | SHA-256 |
|---|---|---|---:|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `diffusion_models` | `E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models` | 20,970,379,616 | `E889202C41DAFB67B10D67B97F0D8541508036A6090AF23425A5C2615D03C47A` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `text_encoders` | `E:\Data\Models\StableDiffusion\minimaxH3\text_encoders` | 15,687,142,551 | `35A88D51044231FE332301D7A62AA81E3F2CBA62FEBEB446E2C1E3E0EF76F2C6` |
| `minimax_h3_video_vae_fp16.safetensors` | `vae` | `E:\Data\Models\VAE\minimaxH3` | 5,207,808,496 | `7C1F131492E7EDDACAAC9069A61B81BDD39DE5CC96561E677C5EAB1CDCE5E522` |
| `minimax_h3_audio_vae_fp32.safetensors` | `vae` | `E:\Data\Models\VAE\minimaxH3` | 605,254,808 | `8E505D95DD1561D47ABD43D4238FD40D9BB1AE9E147ED0A4CBA778D76AE4DB48` |

The four Portable paths under `h3/model_store/` are absent after closeout.
The root and category directories remain present. The remaining Hugging Face
`.incomplete` cache files and lock files were not part of the four-file
authorization and were not treated as production weights.

Space removed from redundant Portable production copies:
`42,470,585,471` bytes.

## 4. Configuration and isolation

The tracked fallback is `h3/config/extra_model_paths.yaml`, which still points
to the Portable `h3/model_store/` namespace. The ignored machine-local
`h3/config/extra_model_paths.local.yaml` points only to:

```yaml
diffusion_models: E:/Data/Models/StableDiffusion/minimaxH3/diffusion_models
text_encoders: E:/Data/Models/StableDiffusion/minimaxH3/text_encoders
vae: E:/Data/Models/VAE/minimaxH3
loras: D:/Models/Lora/minimaxH3
```

The H3 launcher selects the local override when present and otherwise uses the
tracked fallback. `h3/tools/run_native_isolated.py` suppresses only the
automatic shared `ComfyUI/extra_model_paths.yaml` load that Native performs
before explicit configs. The shared config, shared ComfyUI core/frontend, and
Manga runtime were not modified. The cold-start logs showed only the four H3
external category paths, with no shared EasyReforge/Illustrious paths.

The H3 LoRA directory is ready at `D:\Models\Lora\minimaxH3` and already
contains 19 files. LoRA model load and LoRA generation were not tested and are
not claimed.

## 5. Shortcuts

`MODEL_SHORTCUTS/` contains the tracked README and `.gitignore`. The local
PowerShell helper `h3/tools/create_model_shortcuts.ps1` owns 14 exact `.lnk`
names covering:

- preferred H3 models, H3 LoRA, and H3 VAE;
- shared checkpoints, LoRA, VAE, ControlNet, embeddings, and upscaler;
- EasyReforge checkpoint, LoRA, VAE, ControlNet, and upscaler alternates.

The helper was run twice. All targets resolved on both runs; no duplicate or
unrelated shortcut was removed. The `.lnk` files remain local-only and are
ignored by Git. Existing EasyReforge symbolic links were observed but no
runtime junction or symlink was created.

## 6. Runtime acceptance

### Pre-delete external-path smoke

The pre-delete H2B external Still and existing H1A Native Video route both
completed using the external paths. The H1A Video result was:

| Field | Value |
|---|---|
| Route | existing H1A `native_t2v` |
| Job / prompt | `bc6487c2ca6449c3a27ac73730e9676b` / `d4777cfb-4a22-40d0-b7e0-4a062596767e` |
| Output | `output/h3/video/h1a_native_t2v_00007_.mp4` |
| Output SHA-256 | `D3C05CD151C23ED7E01237CF8F7BE19370C48B83C72C66FBD599448534378CB2` |
| Elapsed | `149.74 s` |
| Peak VRAM / minimum free | `11,493 / 520 MiB` |
| OOM / retry | `0 / 0` |

The external audio VAE was hash/path verified and loaded by this existing
Video route. No artificial post-delete Video rerun was added.

### Post-delete cold restart and Still

The migration-test Native process was terminated. The canonical
`h3/run_h3.bat` was then invoked with
`TEGAKI_H3_NATIVE_PORT=8189`, `TEGAKI_H3_SKIN_PORT=8191`, and
`TEGAKI_H3_NO_BROWSER=1`. The default 8188 was occupied by unrelated PID
`40892`; it was not stopped. Native cold-start PID `51324` and the H3 skin
started successfully, using the local override and no shared automatic config.

The decisive post-delete H2B source-anchored Still completed after that cold
restart:

| Field | Value |
|---|---|
| Prompt id | `44f9763e-d5a0-4272-a6da-12649635674b` |
| Source | `output/h3/tests/reference_robot_v1.png` (`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`) |
| Output | `output/h3/still/h2b_source_anchor_00003_.png` |
| Output SHA-256 | `1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5` |
| Elapsed | `83.18 s` |
| Peak VRAM / minimum free | `11,521 / 492 MiB` |
| OOM / retry | `0 / 0` |

This verifies external diffusion, text encoder, and video VAE resolution after
the Portable bodies were deleted. The output PNG and generated media remain
ignored.

## 7. Regression and closeout checks

| Check | Result |
|---|---|
| H2A adapter tests | `4 passed` |
| H2B adapter tests | `5 passed` |
| H1C source/logic smoke | `38 PASS` |
| H1B.1 UX P2 source/logic smoke | `44 PASS` |
| H1B UI source/logic smoke | `36 PASS` |
| Python full suite | `41 passed` |
| JavaScript syntax | `7 files passed` |
| Python compileall | `PASS` |
| `git diff --check` | `PASS` |
| Shared ComfyUI change | `NONE` |
| Manga change | `NONE` |
| Model downloads | `NONE` |

## 8. Publication and acceptance boundary

H2B implementation/evidence/docs are `PUBLISHED ON MAIN`. This H2-INFRA
closeout change is local until an Owner-authorized push and remote verification;
it must not be called public from this local commit. Owner acceptance remains
`PENDING`.

After this closeout, STOP. Do not automatically start Still UI or any later
H3/Manga capability.

## Final report

```text
H3 MODEL LIBRARY NORMALIZATION: PASS

Infrastructure base commit:
bbb9f6720c9a4ed8fb7a029814bd10a5442542fd

Closeout commit:
THIS CONTAINING CLOSEOUT COMMIT

Deleted Portable heavy files:
4 / 4

Space removed:
42470585471 bytes

External hash verification:
PASS

External diffusion:
E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors

External text encoder:
E:\Data\Models\StableDiffusion\minimaxH3\text_encoders\qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors

External video VAE:
E:\Data\Models\VAE\minimaxH3\minimax_h3_video_vae_fp16.safetensors

External audio VAE:
E:\Data\Models\VAE\minimaxH3\minimax_h3_audio_vae_fp32.safetensors

Portable fallback namespace:
PASS

Bundled fallback weights:
NONE

Shortcut regeneration:
PASS

Cold restart:
PASS

Post-delete H2B Still:
PASS

Still elapsed:
83.18 s

Still peak VRAM:
11521 MiB used / 492 MiB free minimum

Still OOM/retry:
0/0

Pre-delete H1A external Video:
PASS

Regression:
PASS

Shared ComfyUI change:
NONE

Manga change:
NONE

Model downloads:
NONE

Report:
docs/h3/reports/H3_MODEL_LIBRARY_SHORTCUT_NORMALIZATION_REPORT.md

Evidence:
docs/h3/evidence/model-library/2026-09-10/

Current capability gate:
H2B

Still UI:
NOT STARTED

Owner acceptance:
PENDING
```
