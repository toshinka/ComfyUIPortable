# TEGAKI H3

This directory contains the H3 production namespace. H1A is the first bounded
implementation slice: a small local Python server and static vanilla UI that
submits the verified Native ComfyUI H3 T2V workflow without exposing the node
graph.

## H1A launcher

Run:

```text
ComfyUIPortable/h3/run_h1a.bat
```

The launcher starts the Native backend on `127.0.0.1:8188` and the TEGAKI H3 UI
on `127.0.0.1:8190`. Set `TEGAKI_H3_NO_BROWSER=1` when the browser should not be
opened automatically.

The launcher uses the local first-wave model store at `h3/model_store/` through
`h3/config/extra_model_paths.yaml`. It does not copy weights into the shared
`ComfyUI/models/` tree and disables all third-party custom nodes for this Native
baseline.

## H1A boundary

- UI: `h3/app/` — static HTML/CSS/vanilla JavaScript plus a small Python server.
- Semantic adapter: `h3/adapters/native_t2v.py`.
- Production workflow contract: `workflows/h3/H1A_NATIVE_T2V_BASE.json`.
- Local output: `output/h3/video/`.
- Session history is backed by ComfyUI history; H1A does not create a project DB.
- Reference/I2V, REF2VA, Studio, Timeline, Project/Shot/Take, Turbo/PDD/FastH3,
  H3 Easy, Antares, onigirikiller vendoring, and Manga integration are deferred.

Model terms are separate from TEGAKI code. See
`docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md`.
