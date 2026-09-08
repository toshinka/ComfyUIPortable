# Native / official ComfyUI H3 — H0.1 generation

Status: `VERIFIED LOCAL GENERATION` (T2V baseline). This is a technical local
result, not Owner acceptance and not an H1 adoption decision.

## Candidate and boundary

- Source: [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)
- Local vendor commit: `b1693ecba9f5b65f8c80ab36b195ab963ec92413` (ComfyUI 0.30.0,
  detached)
- Model source revision: `a98869194787969724c7425d95d0ed73ce9202af`
- Model path: `ComfyUIPortable/h3/model_store/`; shared
  `ComfyUIPortable/ComfyUI/models/` remained unchanged
- Launch: `127.0.0.1:8188`, `--disable-all-custom-nodes`, external H3 model-path
  config, and `output/h3/{video,tests}` namespaces
- Prompt id: `ae0f8d95-08f7-41e9-b833-9076cc1d4d01`

## Fixed smoke settings

```text
A small red service robot with a round white head walks slowly through a quiet greenhouse. The camera tracks gently from left to right. Leaves move slightly in the air. Soft mechanical footsteps and subtle greenhouse ambience.
```

| Setting | Observed value |
|---|---|
| Task | T2V |
| Resolution | 608 x 352 |
| Frames / FPS | 124 / 24 |
| Duration | 5.167 s |
| Steps | 20 |
| Sampler / scheduler | `res_multistep` / `simple` |
| Seed | `20260908` |
| Model | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| Turbo LoRA | disabled |
| Elapsed | 138.86 s (`Prompt executed in 138.86 seconds`) |
| VRAM | conservative sampled peak 11,651 MiB of 12,282 MiB |
| System RAM | 68,476,002,304 bytes total; minimum sampled free about 3,356,254,208 bytes |
| Offload | ComfyUI DynamicVRAM / asynchronous offload, 2 streams observed in the run |
| OOM | none; no fallback was needed |

## Output

- [Native T2V MP4](../../../../../../output/h3/video/h0_1_native_t2v_baseline_00001_.mp4)
- Size: `541741` bytes
- SHA-256: `5BC170464C283FF060F3B897AE5DA8B7E5915B565091820D78DC13B1DD6B2251`
- Codec: H.264 video + AAC stereo audio, 608x352, 24 FPS, 5.167 s
- [First / middle / last frames](frames/)
  - frame 0: [first_frame.png](frames/first_frame.png)
  - frame 62: [middle_frame.png](frames/middle_frame.png)
  - frame 123: [last_frame.png](frames/last_frame.png)
- [Frame contact sheet](contact_sheet.png)
- [Actual local ComfyUI view](screenshots/native_ready.png) — UI readiness view;
  API history and MP4 are the completion evidence.

The first/middle/last frame triplet shows the same small red service robot in the
greenhouse with the expected left-to-right camera motion. No visual quality or
Owner production-acceptance claim is made from this smoke result alone.

## Result

Native ComfyUI is the first local generation oracle for this gate: the official
H3 nodes, four acquired assets, fixed prompt, 12GB-class settings, and output
hash all align. The generated media remains ignored under `output/h3/video/` and
is not committed.
