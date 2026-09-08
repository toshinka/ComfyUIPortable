# onigirikiller/minimax-h3-webui — H0.1 generation

Status: `VERIFIED LOCAL GENERATION` for the candidate UI request path and Native
ComfyUI backend. The candidate code and its Python dependencies stayed inside a
dedicated environment; no package was installed into the Portable embedded
Python.

## Candidate and isolation

- Source: [onigirikiller/minimax-h3-webui](https://github.com/onigirikiller/minimax-h3-webui)
- Source commit: `f9b28d56d69192e4516907a61103a71ff2c29c27` (Apache-2.0)
- Dedicated environment: `h3/eval_envs/onigirikiller/`
- Interpreter base: Miniconda Python 3.13.5
- Candidate dependency adjustment: initial Gradio 6.26.0 rejected the source's
  `Blocks.launch(show_api=...)` call; the dedicated environment was adjusted to
  `gradio<6,>=4.39`, resolving Gradio 5.50.0. The embedded Portable Python was
  untouched.
- UI: `127.0.0.1:7860`; request submitted through the candidate's
  `/gradio_api/call/enqueue` endpoint
- Gradio event id: `9d95765b8b774d08a96d0f9a944d9244`
- Native backend queue row: `2d947385`

## Fixed smoke settings

The candidate submitted the same fixed prompt to the Native H3 T2V backend.

| Setting | Observed value |
|---|---|
| Task | T2V |
| Resolution | 608 x 352 |
| Frames / FPS | 124 / 24 |
| Duration | 5.167 s |
| Steps | 20 |
| Sampler / scheduler | `res_multistep` / `simple` |
| Seed | `20260908` |
| Model | pruned FL2VA / Qwen NVFP4-AWQ / video+audio VAE |
| Turbo LoRA | disabled |
| Elapsed | 141.84 s (`Prompt executed in 141.84 seconds` in the Native backend) |
| VRAM | 12GB-class success; candidate-specific peak was not separately sampled |
| System RAM | 68,476,002,304 bytes total on the host |
| Offload | Native ComfyUI DynamicVRAM / asynchronous offload path |
| OOM | none; no fallback was needed |

## Output

- Canonical [H3 Studio MP4](../../../../../../output/h3/video/h3studio_2d947385_00001_.mp4)
- Duplicate backend save: `output/h3/video/20260908_214053_2d947385.mp4`
- Both files: `541758` bytes, SHA-256
  `69EF473198FA4C58C948E948BE259F13E18DE867ACF081AAEE856E27D623B7F0`
- Codec: H.264 video + AAC stereo audio, 608x352, 24 FPS, 5.167 s
- [First / middle / last frames](frames/)
  - frame 0: [first_frame.png](frames/first_frame.png)
  - frame 62: [middle_frame.png](frames/middle_frame.png)
  - frame 123: [last_frame.png](frames/last_frame.png)
- [Frame contact sheet](contact_sheet.png)
- [Actual H3 Studio view](screenshots/onigirikiller_completed.png) — the screenshot
  records the candidate UI after the request; the result pane was not used as
  visual completion proof, so the queue/API/backend/output records are authoritative.

The first Gradio launch failure and the isolated version correction are part of
the evidence: the UI was made runnable without mutating the shared Portable
environment. This is a candidate-adapter generation result, not an adoption
decision.
