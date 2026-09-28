# MANGA shared production resources (Owner decision)

Recorded by Card TEGAKI-MULTI-ENGINE-LAUNCHER-AND-AVAILABILITY-SYNC-1.

## Decision

MANGA production resources are **shared** between the two MANGA engines:

| Resource   | COMFYUI | EASYREFORGE | Library                          |
|------------|---------|-------------|----------------------------------|
| Checkpoint | yes     | yes         | one shared MANGA library         |
| LoRA       | yes     | yes         | one shared MANGA library         |
| VAE        | yes     | yes         | one shared MANGA library         |

Separate Comfy and ReForge resource libraries must not be created.  The logical recipe keeps
Manga resource IDs; backend translation stays in the adapters (`LegacyReforgeAdapter` for
EasyReforge), and nothing backend-specific is persisted into the Authoring Document.

## Normal MANGA VAE choices

Normal MANGA production VAE choices are essentially:

- **Use checkpoint default** (logical `vae_id = ""`; EasyReforge maps it to `sd_vae = "None"`)
- **XlVaeC_f2.safetensors**

Not normal MANGA production resources:

- minimaxH3 VAEs — they belong to the H3 domain.
- `taesd*`, `pixel_space` — backend capabilities, not production resources.

## Banked

**MANGA SHARED VAE CATALOG NORMALIZATION** — the Manga VAE list still shows the full Comfy
VAELoader catalog (including minimaxH3 VAEs, `taesd*`, `pixel_space`).  EasyReforge already fails
closed on unsupported choices with `VAE_UNSUPPORTED` before any request is sent; restricting the
list to the production choices above is future work.
