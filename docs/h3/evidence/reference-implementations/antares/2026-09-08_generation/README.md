# AntaresAlice/h3-webui — H0.1 generation attempt

Status: `VERIFIED LOCAL STARTUP`; `BLOCKED CANDIDATE-NATIVE GENERATION`.
The UI, workspace, image upload, and generation request were exercised against
the isolated H3 model path. The request stopped at a concrete missing-node
boundary before sampling, so no video/frame/contact-sheet evidence exists for
this candidate.

## Candidate and isolation

- Source: [AntaresAlice/h3-webui](https://github.com/AntaresAlice/h3-webui)
- Source commit: `4f10667c604f9cb333ac119b457a3659260a8966` (MIT)
- UI: `127.0.0.1:8081`
- Environment-only configuration: `COMFYUI_URL=http://127.0.0.1:8188`, input
  `output/h3/tests`, output `output/h3/video`
- Disposable writable source runtime: `output/h3/antares_runtime/webui/`
- Model discovery junctions were created only under `output/h3/models/` and point
  to `h3/model_store/`; the shared `ComfyUI/models/` tree was not touched.

## Attempt

- Workspace: `h0_1_antares`
- Uploaded reference: `ws_bfc40cbc2b.png` (Native frame 0)
- Task: i2v single image, pruned model, 608x352, 5 seconds, 20 steps, seed
  `20260908`, low-VRAM on, SageAttention off, Turbo LoRA off
- `/api/comfyui/status`: HTTP 200, `up=true`, `ref2va_present=false`
- Generate request: HTTP 400
- Exact blocker returned by the WebUI:

```text
ComfyUI rejected: Node 'MiniMaxH3AudioConditioningT8' not found.
The custom node may not be installed. (Common causes: model file is not in
ComfyUI/models/ or node parameters are invalid.)
```

The Native backend was intentionally started with `--disable-all-custom-nodes`
to preserve the shared runtime boundary. We did not install Antares' required
custom node chain into the shared ComfyUI process just to turn this result green.
This is therefore a candidate/runtime compatibility blocker, not a claim that
the four official first-wave model hashes failed.

## Evidence

- [Actual Antares H3 Studio readiness view](screenshots/antares_ready.png)
- No output MP4, SHA-256, frame triplet, or contact sheet: sampling never began.
- No OOM result: the request failed before model execution.
- `ref2va_present=false` is recorded as an environment/status observation; REF2VA
  was intentionally not downloaded for this H0.1 gate.

## Review result

Antares remains useful as a minimum-action UI reference: task type, reference
asset, prompt, resolution, steps, duration, seed, low-VRAM, and Generate state
are visible. Its candidate-native generation route is `BLOCKED` under the
isolated backend contract and must not be promoted to an H1 ingredient without a
separately scoped custom-node compatibility card.
