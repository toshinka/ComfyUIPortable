# H3 isolated model store

This directory is a local-only model store for the H0.1 reference-generation
evaluation. It is intentionally outside `ComfyUI/models/` so the shared Manga
runtime is not mutated. Model weights, Hugging Face cache files, and partial
downloads are ignored and must never be committed.

The tracked acquisition record lives at:

`docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md`
