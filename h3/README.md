# TEGAKI H3

This directory contains the H3 production namespace. H1A is the no-reference
T2V route and H1B is the bounded single-Start-Frame I2V route: a small local
Python server and static vanilla UI that submit separate verified Native
ComfyUI H3 workflows without exposing the node graph.

## Canonical launcher

Run:

```text
ComfyUIPortable/h3/run_h3.bat
```

The launcher starts the Native backend on `127.0.0.1:8188` and the TEGAKI H3
UI on `127.0.0.1:8190`. Set `TEGAKI_H3_NO_BROWSER=1` when the browser should
not be opened automatically. `run_h1a.bat` remains a compatibility wrapper that
delegates to this canonical launcher.

The launcher uses the local first-wave model store at `h3/model_store/` through
`h3/config/extra_model_paths.yaml`. It does not copy weights into the shared
`ComfyUI/models/` tree and disables all third-party custom nodes for this Native
baseline.

## H1A / H1B boundary

- UI: `h3/app/` — static HTML/CSS/vanilla JavaScript plus a small Python server.
- T2V adapter: `h3/adapters/native_t2v.py`.
- Single-reference I2V adapter: `h3/adapters/native_i2v.py`.
- Production workflow contracts: `workflows/h3/H1A_NATIVE_T2V_BASE.json` and
  `workflows/h3/H1B_NATIVE_I2V_BASE.json`.
- Local output: `output/h3/video/`.
- Reference uploads are server-issued assets in the ignored
  `output/h3/inputs/` namespace; the browser never supplies a filesystem path.
- Session history is backed by ComfyUI history; H1A/H1B do not create a project DB.
- H1B binds exactly one validated `Start Frame` to `first_frame`; no end frame,
  multi-reference, REF2VA, Still, Studio, Timeline, or Project/Shot/Take path is
  exposed.
- Turbo/PDD/FastH3, H3 Easy, Antares, onigirikiller vendoring, and Manga
  integration are deferred.

Model terms are separate from TEGAKI code. See
`docs/h3/evidence/H3_MODEL_ACQUISITION_MANIFEST.md`.
