# R0 — Canonical workflow and queue

- Result: `PASS`
- Evidence mode: live ComfyUI browser plus generated output inspection.
- Workflow: `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`
- Browser: ComfyUI at `http://127.0.0.1:8188/`, live tab 5.

The updated canonical workflow was loaded through ComfyUI's standard workflow file chooser. The live runtime exposed both `TegakiMinimumHandSceneEditor` and `TegakiMangaRoughGuideBridge` through `/object_info`. The queue was accepted, progressed through `TegakiMangaConditioningBuilder` and `KSampler`, returned to `Idle`, and produced `R0_CANONICAL_OUTPUT.png` from `MangaDraft_M1_00011_.png`.

This is a baseline queue check only. The Guide bridge remained observational and was not connected to conditioning, KSampler, ControlNet, or any generation influence.
