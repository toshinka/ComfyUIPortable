# H3 isolated model store

This directory is the retained Portable fallback namespace for H3 model
assets. It is intentionally outside `ComfyUI/models/` so the shared Manga
runtime is not mutated. The machine-local
`h3/config/extra_model_paths.local.yaml` override points Native ComfyUI at the
external H3 library when that library is configured; the tracked
`extra_model_paths.yaml` continues to describe this namespace as a fallback.

Model weights, Hugging Face cache files, and partial downloads are ignored and
must never be committed. After external migration, redundant heavy production
weights should not be kept here.

The tracked acquisition record lives at:

`docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md`
