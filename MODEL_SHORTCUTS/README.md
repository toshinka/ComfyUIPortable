# Local model shortcuts

This directory is a local convenience layer for the model-library policy. The
tracked PowerShell helper creates the Windows `.lnk` files:

```powershell
powershell -ExecutionPolicy Bypass -File h3/tools/create_model_shortcuts.ps1
```

The preferred H3 download targets are:

- `E:\Data\Models\StableDiffusion\minimaxH3` — H3 diffusion models and H3 text encoders.
- `D:\Models\Lora\minimaxH3` — H3 LoRA files.
- `E:\Data\Models\VAE\minimaxH3` — H3-specific VAE files.

The `SHARED_*` shortcuts point at the existing shared libraries for
checkpoints, LoRA, VAE, ControlNet, embeddings, and upscalers. The
`EASYREFORGE_*` shortcuts point at the existing EasyReforge alternate
locations. Shared Illustrious assets remain shared and are not copied into H3
directories.

`.lnk` files are machine-local, ignored by Git, and can be regenerated safely.
The helper replaces only the exact shortcut names it owns; it does not create
runtime junctions or symlinks and does not remove arbitrary user shortcuts.
