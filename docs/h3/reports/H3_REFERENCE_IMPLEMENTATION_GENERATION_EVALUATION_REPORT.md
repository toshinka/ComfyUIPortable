# H3 Reference Implementation Generation Evaluation Report

更新: 2026-09-08 JST
Status: `H0.1 TECHNICALLY COMPLETE / WEB GPT H1 INGREDIENT REVIEW READY`

## 1. 結論

The first-wave official H3 assets were acquired, SHA-256 verified, and kept in
an isolated `h3/model_store/`. A fixed smoke prompt was run at 608x352, 5.167
seconds, 24 FPS, and 20 steps through three local routes:

1. Native official ComfyUI: `VERIFIED LOCAL GENERATION` (T2V).
2. H3 Easy: `VERIFIED LOCAL GENERATION` (isolated I2V).
3. onigirikiller H3 Studio: `VERIFIED LOCAL GENERATION` through its UI/API and
   the Native ComfyUI backend (T2V).

AntaresAlice H3 WebUI started, created a workspace, uploaded a reference, and
submitted the same class of I2V request, but its candidate-specific graph was
rejected because `MiniMaxH3AudioConditioningT8` was not available in the
intentionally custom-node-free shared backend. It is `BLOCKED` for
candidate-native generation, with the exact 400 response recorded.

This report is a generation/evidence closeout, not a source adoption decision,
H1 implementation instruction, quality benchmark, or Owner acceptance.

## 2. Gate and model acquisition

- First-wave files: FL2VA pruned INT8 ConvRot, Qwen3-VL NVFP4-AWQ encoder,
  video VAE FP16, and audio VAE FP32.
- Official source revision: `a98869194787969724c7425d95d0ed73ce9202af`.
- Official T2V workflow template revision: `7c25a3c586484601f94b7e8f8b14c23b2c95a096`;
  local copy SHA-256: `2400B01A7C8ACAE3FED038C0372F08BACB90D2CDF915FEBADBE7E3F9802506EA`.
- Total verified payload: `42,470,585,471` bytes (`39.55 GiB`).
- Every local SHA-256 matched the official revision metadata.
- The model tree is `h3/model_store/`; `ComfyUI/models/` remained unchanged.
- REF2VA, Turbo/LightX/PDD/FastH3/VSA, alternate precision, style, Still, and
  Manga assets were not acquired.
- Full filename/size/hash/source/license/path record:
  [H3_MODEL_ACQUISITION_MANIFEST.md](../evidence/H3_MODEL_ACQUISITION_MANIFEST.md)
- License gate: the technical acquisition check passes, but Owner/legal review
  remains required for the MiniMax H3 Community License territory, use, and
  redistribution restrictions. See the [official H3 license](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE).

## 3. Reproducible common task

```text
A small red service robot with a round white head walks slowly through a quiet greenhouse. The camera tracks gently from left to right. Leaves move slightly in the air. Soft mechanical footsteps and subtle greenhouse ambience.
```

| Field | Fixed value |
|---|---|
| Resolution | 608 x 352 |
| Frames / FPS | 124 / 24 |
| Duration | 5.167 seconds |
| Steps | 20 |
| Sampler / scheduler | `res_multistep` / `simple` |
| Seed | `20260908` |
| Turbo LoRA | disabled |
| Output namespace | `output/h3/video/` |
| Evidence namespace | `docs/h3/evidence/reference-implementations/*/2026-09-08_generation/` |

The H3 Easy run is intentionally I2V with the Native first frame as its
reference. Native and onigirikiller are T2V. This is a common smoke contract,
not a claim that T2V and I2V are identical tasks.

## 4. Candidate results

| Candidate | Local result | Task | Elapsed | Output | Evidence |
|---|---|---|---:|---|---|
| Native official ComfyUI | `VERIFIED LOCAL GENERATION` | T2V | 138.86 s | `h0_1_native_t2v_baseline_00001_.mp4`; SHA-256 `5BC170464C283FF060F3B897AE5DA8B7E5915B565091820D78DC13B1DD6B2251` | [generation README](../evidence/reference-implementations/native/2026-09-08_generation/README.md), [manifest](../evidence/reference-implementations/native/2026-09-08_generation/manifest.json) |
| H3 Easy | `VERIFIED LOCAL GENERATION` | I2V | 152.49 s | `h0_1_h3easy_i2v_00001_.mp4`; SHA-256 `E297EEF9EDCF33635F1068906A41A145585A99AF5A7F05A5A94FEAFE7ADF9D74` | [generation README](../evidence/reference-implementations/h3-easy/2026-09-08_generation/README.md), [manifest](../evidence/reference-implementations/h3-easy/2026-09-08_generation/manifest.json) |
| onigirikiller H3 Studio | `VERIFIED LOCAL GENERATION` for UI/API path plus Native backend | T2V | 141.84 s | `h3studio_2d947385_00001_.mp4`; SHA-256 `69EF473198FA4C58C948E948BE259F13E18DE867ACF081AAEE856E27D623B7F0` | [generation README](../evidence/reference-implementations/onigirikiller/2026-09-08_generation/README.md), [manifest](../evidence/reference-implementations/onigirikiller/2026-09-08_generation/manifest.json) |
| AntaresAlice H3 WebUI | `VERIFIED LOCAL STARTUP`; `BLOCKED` candidate-native generation | I2V request reached backend validation | not applicable | none; HTTP 400 before sampling | [generation README](../evidence/reference-implementations/antares/2026-09-08_generation/README.md), [manifest](../evidence/reference-implementations/antares/2026-09-08_generation/manifest.json) |

All successful outputs are H.264 + AAC stereo, 608x352, 24 FPS, and 5.167
seconds. The Native and onigirikiller hashes are different filenames with the
same fixed backend result; the H3 Easy hash differs because it is the I2V route.

## 5. Candidate evidence and behavior

### Native / official ComfyUI

The official node/API boundary is the first generation oracle. The successful
T2V prompt id is `ae0f8d95-08f7-41e9-b833-9076cc1d4d01`. The conservative sampled
peak was 11,651 MiB of the 12,282 MiB RTX 4070 budget; sampled minimum free RAM
was about 3.36 GB. The local frame triplet and contact sheet show the robot in
the greenhouse. The UI screenshot is kept as a local readiness view; API history,
ffprobe, and output hash are the completion authority.

Review ingredient: keep the official native H3 node/model boundary as the
backend capability reference. Do not make the graph canvas the H1 minimum entry
by default.

### H3 Easy

The source-only custom node was placed in a disposable copied runtime, and the
launcher removed the shared ComfyUI path from `sys.path`. The successful I2V
prompt id is `fa9cc53f-4e34-481c-a444-bdbff75b6b44`. The first invalid graph was
recorded and corrected; the successful run demonstrates model loading, reference
input, sampling, decode, and save without changing the shared custom-node tree.

Review ingredient: keep the one-media/ordered-reference and progressive-
disclosure concepts for H1 review. Do not copy the candidate source or declare
the node adopted. Candidate-specific peak VRAM was not separately sampled, so no
precise H3 Easy peak number is claimed.

### onigirikiller H3 Studio

The source UI request crossed `/gradio_api/call/enqueue`, produced queue row
`2d947385`, and completed through the Native backend. The first Gradio 6.26
launch failed at `Blocks.launch(show_api=...)`; the dedicated venv alone was
adjusted to Gradio 5.50.0 under `gradio<6,>=4.39`. The shared embedded Python
was not changed. Candidate-specific VRAM was not separately sampled; the run
was successful on the same 12GB-class host with no OOM.

Review ingredient: keep queue/progress/history and continuation-oriented flow as
H1 review material. Treat the Python dependency choice as an isolated runtime
decision, not a production dependency change.

### AntaresAlice H3 WebUI

The local UI and `/api/comfyui/status` were verified. A workspace and reference
upload were created. The candidate-native generate request returned HTTP 400:

```text
Node 'MiniMaxH3AudioConditioningT8' not found
```

The shared backend was intentionally launched with `--disable-all-custom-nodes`;
installing the candidate's required node chain into the shared runtime would
violate the H0.1 isolation boundary. The result is therefore a useful, concrete
compatibility blocker. No sampling, output hash, frame triplet, VRAM peak, or
OOM claim exists for this candidate.

Review ingredient: keep the visible Video-first minimum surface and explicit
reference/Generate boundary as UI material. Defer candidate-native node-chain
compatibility to a separately scoped card.

## 6. 12GB-class memory and error record

| Route | Elapsed | Peak VRAM | RAM | Offload | OOM / fallback |
|---|---:|---|---|---|---|
| Native T2V | 138.86 s | 11,651 / 12,282 MiB conservative sample | 68,476,002,304 bytes total; min free about 3,356,254,208 bytes | DynamicVRAM / asynchronous offload, 2 streams | no OOM; no fallback |
| H3 Easy I2V | 152.49 s | not separately sampled; successful on 12GB-class host | same host total | DynamicVRAM path; exact candidate stream sample not retained | no OOM; no fallback |
| onigirikiller → Native T2V | 141.84 s | not separately sampled for the UI route | same host total | Native DynamicVRAM / asynchronous offload | no OOM; no fallback |
| Antares candidate-native I2V | not applicable | not reached | not reached | not reached | HTTP 400 missing node before sampling |

The table distinguishes measured evidence from a successful run without a
candidate-specific sampler. It does not convert one Native peak sample into a
claim for all candidates.

## 7. Comparison for Web GPT

| Axis | Native | H3 Easy | onigirikiller | Antares |
|---|---|---|---|---|
| First generation | direct official T2V | isolated I2V graph | UI/API to Native T2V | blocked at required custom node |
| Minimum action | graph-first | one-node/media-oriented | compact queue UI | visible Video-first Studio surface |
| Prompt / reference | prompt verified; no reference in T2V | reference frame verified | prompt verified; UI route | upload boundary verified, sampling blocked |
| Queue / progress / history | API history | native API history | candidate enqueue + backend queue | startup/history surface only |
| Output evidence | hash + frames + contact sheet | hash + frames + contact sheet | hash + frames + contact sheet | no output |
| 12GB result | measured conservative peak | success, peak not separately sampled | success, peak not separately sampled | not reached |
| H1 use | backend authority | interaction ingredient | queue/continuation ingredient | UI ingredient only; runtime compatibility deferred |

### Good

- The official model/workflow path is reproducible without putting weights in the
  shared Manga-adjacent model shelf.
- Three distinct local routes reached a real MP4 with hashes and frame evidence.
- H3 Easy's isolated node path and onigirikiller's dedicated venv demonstrate that
  dependency/runtime separation is practical.
- Antares makes the minimum Video controls visible and gave a concrete backend
  failure instead of a false success.

### Bad / limits

- The Native graph surface is not the H1 authoring surface.
- H3 Easy and onigirikiller do not have separately sampled peak VRAM numbers in
  this closeout; only the Native baseline peak is a conservative measurement.
- Antares cannot be called generation-verified without its required custom node
  chain, and installing that chain into the shared backend was out of scope.
- This was a short fixed smoke, not a quality, long-video, multi-reference, or
  production stability benchmark.

### Interesting

- Native and onigirikiller produced the same fixed T2V backend hash, making the
  UI/backend boundary visible without claiming UI-specific model quality.
- H3 Easy changed the task class to I2V while keeping the reference and output
  evidence explicit; this is a useful future request-contract distinction.
- The exact Antares missing-node error is actionable for a later bounded adapter
  card and does not justify broad custom-node installation now.

### Not relevant to H1 at this gate

REF2VA, full Studio/Timeline/Storyboard/Cast/Manga flows, Turbo/PDD/FastH3/VSA,
full model variants, new frontend/backend implementation, shared Manga changes,
and Owner production acceptance.

## 8. H1 ingredient disposition

This is a review disposition, not an adoption list:

- `KEEP`: official native H3 capability boundary; fixed prompt/output/hash/frame
  evidence contract; isolated model/runtime boundary; explicit status vocabulary.
- `ADJUST`: H3 Easy ordered-media/progressive disclosure, onigirikiller queue /
  continuation cues, and Antares' Video-first minimum surface. Re-express these
  in TEGAKI's Scene-first/minimum-action design rather than importing a candidate.
- `DEFER`: Antares custom-node compatibility, REF2VA, Turbo/fast runtimes, full
  Studio/Storyboard, and any H1 skin implementation.
- `NOT RELEVANT`: H3 Manga implementation, Illustrious Manga runtime changes,
  source vendoring, model redistribution, and Astra rerun.

No candidate is marked `ADOPTED`. Web GPT may now decide whether a later bounded
H1 ingredient card should be created.

## 9. Closeout boundary

- Shared Manga runtime/custom nodes/frontend/core were not modified.
- Model weights, source clones, venvs, runtime copies, videos, frames, and
  screenshots remain ignored/local-only unless explicitly tracked as evidence
  files; large model/video payloads are not committed.
- All H3 servers were stopped after evidence capture; only Owner may push.
- This report stops at the Web GPT H1 ingredient decision. It does not start H1,
  rerun Astra, download REF2VA, or claim Owner acceptance.
