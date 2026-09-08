# H1A Native T2V minimum video skin — 2026-09-08 evidence

Status: `VERIFIED LOCAL GENERATION` and `VERIFIED BROWSER UI GENERATION`.
This is technical evidence for the H1A slice, not Owner production acceptance.

## Scope

- Local TEGAKI H3 skin: `http://127.0.0.1:8190/`
- Native ComfyUI H3 backend: `http://127.0.0.1:8188/`
- Launcher: `h3/run_h1a.bat`
- Semantic adapter: `h3/adapters/native_t2v.py`
- Production workflow: `workflows/h3/H1A_NATIVE_T2V_BASE.json`
- Model store: `h3/model_store/` only; the shared `ComfyUI/models/` tree was not used
- Output namespace: `output/h3/video/` (ignored; no MP4 is committed)

The launcher uses the embedded Python runtime, disables all custom nodes, and
points Native ComfyUI at the isolated H3 model paths. The local skin exposes
HTTP only; it does not expose the ComfyUI graph, sampler, scheduler, model, or
VAE controls.

## Browser UI run

The prompt was entered through the browser UI and submitted with the visible
`Generate` button. The browser observed `Running` with `Cancel current job`,
then `Completed`, a playable Preview, Queue `0`, and two session History cards.

| Field | Observed value |
|---|---|
| Prompt id | `903f28d5-659c-4dff-98ae-2f8780e0563f` |
| Job id | `2e2499055c9649c4a04fac111afa08d9` |
| Seed | random (`7612416513579120808` recorded by the session) |
| Resolution | 608 x 352 |
| Duration control | 5 seconds |
| Frames / FPS | 124 / 24 |
| Steps | 20 |
| Sampler / scheduler | `res_multistep` / `simple` |
| Turbo LoRA | disabled |
| Elapsed | 114.0 s |
| Output | `output/h3/video/h1a_native_t2v_00002_.mp4` |
| Output bytes | 565019 |
| SHA-256 | `14CAA00BAAA16F78CEBEF01F49092110C0FC78045F8F85B50E4D2B1CB7937A85` |

`ffprobe` confirmed H.264 video plus AAC audio, 608x352, 24 FPS, 124 video
frames, and 5.167 seconds of media duration. The UI run itself was not under a
separate external VRAM sampler. A preceding H1A API smoke run on the same
Native process sampled minimum `vram_free=456707660` bytes, approximately
11,846 MiB used of 12,282 MiB, and completed without OOM.

## Evidence files

- [H1A completed browser view](screenshots/h1a_completed_wide.png)
- [First frame](frames/first_frame.png)
- [Middle frame](frames/middle_frame.png)
- [Last frame](frames/last_frame.png)
- [Frame contact sheet](contact_sheet.png)
- [Machine-readable manifest](manifest.json)

The frame triplet shows the red service robot moving through the greenhouse
under the fixed smoke prompt. It is a runtime/evidence check, not a visual
quality or Owner acceptance claim.

## Related runs

The first API smoke run used the same fixed prompt and seed `20260908` and
produced `h1a_native_t2v_00001_.mp4` with SHA-256
`0C20302A70C1F48685360A2751AC30BBC1135DD8AF8EEFE68259E5675B6C6ABE` in
171.8 seconds. It established the direct adapter-to-Native path before the
browser submission was exercised.

## Boundary

No H1B, I2V, REF2VA, Still, Studio, Timeline, Storyboard, Cast, 3D, Manga, or
shared custom-node implementation was added. The session mapping is in memory;
Native ComfyUI remains the queue/history authority. Owner review and push remain
separate from this local evidence.
