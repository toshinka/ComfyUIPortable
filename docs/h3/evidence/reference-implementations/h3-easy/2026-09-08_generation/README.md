# ComfyUI-MiniMaxH3-Easy — H0.1 generation

Status: `VERIFIED LOCAL GENERATION` (isolated I2V smoke). The node source and
runtime were copied into `h3/eval_runtime/` only; the shared ComfyUI custom-node
tree and shared Manga runtime were not modified.

## Candidate and isolation

- Source: [nkxx188/ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)
- Source commit: `d00fd814769e586545c454d75068856c71c79116` (MIT)
- Runtime: disposable local ComfyUI copy at `h3/eval_runtime/comfyui/`
- Custom node: `h3/eval_runtime/comfyui/custom_nodes/ComfyUI-MiniMaxH3-Easy/`
- Model path: `h3/model_store/` through `extra_model_paths.yaml`
- Server: `127.0.0.1:8189`; launcher removed the shared ComfyUI path from
  `sys.path` before importing the isolated runtime
- Prompt id: `fa9cc53f-4e34-481c-a444-bdbff75b6b44`

## Fixed smoke settings

The fixed prompt was the same as the Native baseline. The test used H3 Easy's
I2V/image route with the Native first frame copied to
`output/h3/tests/reference_robot_v1.png` as the reference image.

| Setting | Observed value |
|---|---|
| Task | I2V / image mode |
| Reference | Native frame 0, 608 x 352 |
| Resolution | 608 x 352 |
| Frames / FPS | 124 / 24 |
| Duration | 5.167 s |
| Steps | 20 |
| Sampler / scheduler | `res_multistep` / `simple` |
| Seed | `20260908` |
| Model | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` |
| Turbo LoRA | disabled |
| Elapsed | 152.49 s (`Prompt executed in 152.49 seconds`) |
| VRAM | 12GB-class success; candidate-specific peak was not separately sampled |
| System RAM | 68,476,002,304 bytes total on the host |
| Offload | ComfyUI DynamicVRAM path; exact candidate-specific stream sample not retained |
| OOM | none; no fallback was needed |

The first manually assembled graph submission was rejected because the model was
connected to a conditioning output and the input file was absent. That concrete
graph error was corrected before the successful prompt above; it is retained as
debug history rather than hidden by a retry claim.

## Output

- [H3 Easy I2V MP4](../../../../../../output/h3/video/h0_1_h3easy_i2v_00001_.mp4)
- Size: `486301` bytes
- SHA-256: `E297EEF9EDCF33635F1068906A41A145585A99AF5A7F05A5A94FEAFE7ADF9D74`
- Codec: H.264 video + AAC stereo audio, 608x352, 24 FPS, 5.167 s
- [First / middle / last frames](frames/)
  - frame 0: [first_frame.png](frames/first_frame.png)
  - frame 62: [middle_frame.png](frames/middle_frame.png)
  - frame 123: [last_frame.png](frames/last_frame.png)
- [Frame contact sheet](contact_sheet.png)
- [Actual isolated ComfyUI view](screenshots/h3easy_completed.png) — rendered UI
  readiness view; API history and MP4 are the completion evidence.

The I2V result shows the same red/white robot and greenhouse subject through the
frame triplet. The result demonstrates the isolated adapter path, not adoption of
the candidate node into TEGAKI.
