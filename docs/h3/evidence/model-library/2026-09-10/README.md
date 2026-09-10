# H3 Model Library / Shortcut Normalization — 2026-09-10 evidence

Status: `PASS` for the H2-INFRA closeout. This is local technical evidence;
Owner acceptance remains `PENDING`, and the closeout publication state is
`LOCAL MAIN / PUSH PENDING`.

## Scope and result

The four first-wave H3 weights were copied to the canonical external library,
hash-verified, used by real Native H3 generation, and then removed from the
Portable model store after explicit Owner authorization. No model was
downloaded. The Portable fallback namespace and category directories remain,
but the four bundled heavy weight bodies are absent by design.

| Role | Logical category | External canonical path | Bytes | SHA-256 |
|---|---|---|---:|---|
| Diffusion model | `diffusion_models` | `E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20,970,379,616 | `E889202C41DAFB67B10D67B97F0D8541508036A6090AF23425A5C2615D03C47A` |
| H3 text encoder | `text_encoders` | `E:\Data\Models\StableDiffusion\minimaxH3\text_encoders\qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15,687,142,551 | `35A88D51044231FE332301D7A62AA81E3F2CBA62FEBEB446E2C1E3E0EF76F2C6` |
| Video VAE | `vae` | `E:\Data\Models\VAE\minimaxH3\minimax_h3_video_vae_fp16.safetensors` | 5,207,808,496 | `7C1F131492E7EDDACAAC9069A61B81BDD39DE5CC96561E677C5EAB1CDCE5E522` |
| Audio VAE | `vae` | `E:\Data\Models\VAE\minimaxH3\minimax_h3_audio_vae_fp32.safetensors` | 605,254,808 | `8E505D95DD1561D47ABD43D4238FD40D9BB1AE9E147ED0A4CBA778D76AE4DB48` |

Removed Portable bytes: `42,470,585,471`.

The complete machine-readable before/after inventory is in
[inventory.json](inventory.json), and the ordered migration/deletion/runtime
record is in [migration_manifest.json](migration_manifest.json).

## Portable fallback and isolation

- `h3/model_store/` plus `diffusion_models/`, `text_encoders/`, and `vae/`
  remain as an available fallback namespace.
- Bundled first-wave heavy fallback weights are `NONE`.
- The two partial Hugging Face cache files and their lock files were not
  treated as production model bodies and were not deleted under the exact
  four-file authorization boundary.
- `h3/config/extra_model_paths.yaml` remains the tracked Portable fallback.
- The ignored `h3/config/extra_model_paths.local.yaml` resolves only
  `diffusion_models`, `text_encoders`, `vae`, and `loras` under the intended
  H3 external locations.
- `h3/tools/run_native_isolated.py` suppresses only the shared automatic
  `ComfyUI/extra_model_paths.yaml` load; the shared file and shared runtime
  were not modified.

## Runtime evidence

### Pre-delete external-path generation

- H2B source-anchored Still: `PASS`; external Native process; anchored output
  SHA-256 `1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5`.
- Existing H1A Native T2V Video: `PASS`; job
  `bc6487c2ca6449c3a27ac73730e9676b`; prompt
  `d4777cfb-4a22-40d0-b7e0-4a062596767e`; output
  `output/h3/video/h1a_native_t2v_00007_.mp4`; SHA-256
  `D3C05CD151C23ED7E01237CF8F7BE19370C48B83C72C66FBD599448534378CB2`;
  elapsed `149.74 s`; peak `11,493 MiB`; minimum free `520 MiB`; OOM/retry
  `0/0`.

### Post-delete cold restart

The canonical `h3/run_h3.bat` was invoked with
`TEGAKI_H3_NATIVE_PORT=8189`, `TEGAKI_H3_SKIN_PORT=8191`, and
`TEGAKI_H3_NO_BROWSER=1` because unrelated pre-existing PID `40892` held the
default Native port `8188`; that process was not stopped. Native cold-start
PID `51324` resolved only the four H3 external categories and the skin came up
on `8191`. The post-delete H2B anchored Still completed with:

- prompt id `44f9763e-d5a0-4272-a6da-12649635674b`
- output `output/h3/still/h2b_source_anchor_00003_.png`
- SHA-256 `1EC4ACA74707C74F13ABCFADBB00304B9F1611787C593455A459A8D0543B49F5`
- elapsed `83.18 s`
- peak `11,521 MiB`; minimum free `492 MiB`
- OOM/retry `0/0`

The generated output is ignored and is not committed. The pre-delete Video
run remains valid evidence; no artificial second Video run was added.

## Shortcuts

`h3/tools/create_model_shortcuts.ps1` created the 14 owned Windows shortcuts
in `MODEL_SHORTCUTS/`. All targets resolved, including
`DOWNLOAD_H3_MODELS`, `DOWNLOAD_H3_LORA`, and `H3_VAE`. The helper was run a
second time with the same result, with no duplicate or unrelated shortcut
deletion. `.lnk` files are ignored and are not committed.

## Regression

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

No shared ComfyUI code, shared model configuration, Manga code, or feature
capability was added. H2B remains the current capability gate; Still UI,
LoRA support, REF2VA, multi-reference, Manga, Timeline, and Studio remain
outside this Card.
