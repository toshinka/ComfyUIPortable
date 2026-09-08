# H3 Model Acquisition Manifest

更新: 2026-09-08 JST
Gate: `H0.1 / H3 model and dependency isolation / generation smoke`

## Scope

This manifest records only the first-wave assets required for the FL2VA/T2V-I2V
smoke evaluation. The files are local-only under `h3/model_store/`; they were
not copied into `ComfyUI/models/`, the shared Portable Python environment, or
the Manga runtime. `REF2VA` and every precision/acceleration/style/experimental
asset were deliberately deferred.

## Official provenance and license gate

- Model source: [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3)
- Source revision checked: `a98869194787969724c7425d95d0ed73ce9202af`
- Official workflow reference: [video_minimax_h3_t2v.json](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_t2v.json)
- Workflow revision checked: `7c25a3c586484601f94b7e8f8b14c23b2c95a096`
- Local workflow copy: `h3/eval_workflows/video_minimax_h3_t2v.json`, 67,891 bytes,
  SHA-256 `2400B01A7C8ACAE3FED038C0372F08BACB90D2CDF915FEBADBE7E3F9802506EA`.
- Model terms: [MiniMax H3 Community License Agreement](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE)
- Code/runtime terms are separate: ComfyUI is GPL-3.0; candidate UI/node licenses
  remain separate from the model terms.
- The H3 Community License is effective on use, has territory exclusions stated
  in the agreement (including EU, UK, Republic of Korea, and USA), and includes
  restrictions relevant to redistribution and use. Owner/legal review is still
  required before broader distribution or hosted use.
- The Qwen3-VL encoder is identified by the official model material as Apache-2.0;
  that does not replace the MiniMax H3 packaging/model terms.

## Disk and isolation preflight

- D: free before acquisition: `390272204800` bytes.
- First-wave model payload after acquisition: `42470585471` bytes (`39.55 GiB`).
- D: free after acquisition: `337697488896` bytes.
- Shared model tree scan: no first-wave H3 files under
  `ComfyUIPortable/ComfyUI/models/`.
- Local target: `ComfyUIPortable/h3/model_store/`.
- Download method: direct HTTPS resolution from the official Hugging Face model
  repository at the checked revision; no credential or model-gate acceptance was
  required by the local download path.

## Acquired files

| Filename | Role | Official source | License / restrictions | Expected bytes | Actual bytes | SHA-256 | Local path | Used by | State / checked |
|---|---|---|---|---:|---:|---|---|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | FL2VA pruned INT8 diffusion model; T2V/I2V baseline | [official file](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/a98869194787969724c7425d95d0ed73ce9202af/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors) | MiniMax H3 Community License; territory/use/redistribution restrictions require Owner review | 20,970,379,616 | 20,970,379,616 | `E889202C41DAFB67B10D67B97F0D8541508036A6090AF23425A5C2615D03C47A` | `h3/model_store/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | Native ComfyUI, H3 Easy isolated runtime, onigirikiller/Antares backend request | downloaded; hash matched; 2026-09-08 |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | Qwen3-VL H3 text/vision encoder | [official file](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/a98869194787969724c7425d95d0ed73ce9202af/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors) | H3 package terms plus Qwen3-VL Apache-2.0 note; verify both terms before redistribution | 15,687,142,551 | 15,687,142,551 | `35A88D51044231FE332301D7A62AA81E3F2CBA62FEBEB446E2C1E3E0EF76F2C6` | `h3/model_store/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | Native ComfyUI, H3 Easy isolated runtime, candidate backend | downloaded; hash matched; 2026-09-08 |
| `minimax_h3_video_vae_fp16.safetensors` | H3 video VAE | [official file](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/a98869194787969724c7425d95d0ed73ce9202af/vae/minimax_h3_video_vae_fp16.safetensors) | MiniMax H3 Community License; territory/use/redistribution restrictions require Owner review | 5,207,808,496 | 5,207,808,496 | `7C1F131492E7EDDACAAC9069A61B81BDD39DE5CC96561E677C5EAB1CDCE5E522` | `h3/model_store/vae/minimax_h3_video_vae_fp16.safetensors` | Native ComfyUI, H3 Easy isolated runtime, candidate backend | downloaded; hash matched; 2026-09-08 |
| `minimax_h3_audio_vae_fp32.safetensors` | H3 audio VAE | [official file](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/a98869194787969724c7425d95d0ed73ce9202af/vae/minimax_h3_audio_vae_fp32.safetensors) | MiniMax H3 Community License; territory/use/redistribution restrictions require Owner review | 605,254,808 | 605,254,808 | `8E505D95DD1561D47ABD43D4238FD40D9BB1AE9E147ED0A4CBA778D76AE4DB48` | `h3/model_store/vae/minimax_h3_audio_vae_fp32.safetensors` | Native ComfyUI, H3 Easy isolated runtime, candidate backend | downloaded; hash matched; 2026-09-08 |

Total expected and actual payload: `42,470,585,471` bytes. All four SHA-256
values matched the official revision metadata and the local files.

## Explicitly not acquired

- `minimax_h3_ref2va_pruned_int8_convrot.safetensors` — second-stage REF2VA;
  deferred after the first FL2VA/T2V-I2V smoke gate.
- Turbo LoRA, LightX/PDD/FastH3/VSA assets, style embeddings, full/alternate
  precision variants, Still/Manga models, and any non-official model package.

## Boundary result

The model acquisition gate is technically `PASS` for the four first-wave files
and `OWNER ACTION REQUIRED` for confirmation of the applicable MiniMax Community
License territory/use restrictions. The acquired weights are not a production
asset, are not committed, and do not constitute an H1 adoption decision.
