# H1B Single Reference / Native I2V Evidence — 2026-09-09

Status: `IMPLEMENTED`, `VERIFIED LOCAL GENERATION`, and `VERIFIED BROWSER UI GENERATION`.

Owner acceptance: `PENDING`.

This package records the bounded H1B slice: one uploaded image used as
`Start Frame` for the Native MiniMax H3 I2V route, plus the H1A no-reference T2V
regression. It is technical evidence, not visual-quality approval or Owner
production acceptance.

## Runtime boundary

- Canonical launcher: `h3/run_h3.bat`
- H1A compatibility launcher: `h3/run_h1a.bat`
- Skin: `http://127.0.0.1:8190/`
- Native ComfyUI backend: `http://127.0.0.1:8188/`
- H1B adapter: `h3/adapters/native_i2v.py`
- H1B workflow: `workflows/h3/H1B_NATIVE_I2V_BASE.json`
- Isolated model store: `h3/model_store/`
- Ignored generated output: `output/h3/video/`
- Ignored uploaded runtime input: `output/h3/inputs/`
- No custom nodes, shared ComfyUI model tree, Manga runtime, or Manga workflow
  was used or modified.

## Workflow provenance

The production graph is adapted from the official
[Comfy-Org MiniMax H3 I2V workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_i2v.json).

| Field | Value |
|---|---|
| Official workflow commit | `66abae5205f7c5105281146fa109f7c12801d268` |
| Official workflow SHA-256 | `4DC94E9EA308C1D60409E7F55DBA5E2788DAB4659C2DBB90F1E9481498767540` |
| Local H1B workflow SHA-256 | `6BFA82EA20B65C84CBDB62A1EF949581D4F03368C2F6B035D6081EF204FE72DE` |
| Baseline | 608 x 352 / 5 seconds / 124 frames / 24 FPS / 20 steps |
| Reference edge | `LoadImage` node `132` → `first_frame` on node `131` |
| End-frame edge | absent and rejected if introduced |

## Browser event record

The live browser session used the in-app browser against the canonical launcher.
AX state and a live completion screenshot were captured in the CUA transcript;
the durable files in this directory are the media frames and contact sheet.

| Event | Observed result |
|---|---|
| T2V regression submitted | `2026-09-09 07:45:54 JST` |
| T2V regression completed | `2026-09-09 07:48:33 JST`; visible `Completed · T2V`, Preview, queue 0 |
| Add reference | PNG upload accepted; server-issued id and thumbnail displayed |
| Replace reference | Existing selection replaced with the H0.1 middle frame; `Start Frame` remained visible |
| Remove reference | UI returned to `No Start Frame selected.`; prompt/resolution/duration remained; no server deletion |
| I2V submitted | `2026-09-09 08:01:03 JST` |
| I2V completed | `2026-09-09 08:03:25 JST`; visible `Completed · Start Frame`, Preview, queue 0 |

## Native output record

| Route | Job id | Prompt id | Elapsed | Output | Bytes | SHA-256 |
|---|---|---|---:|---|---:|---|
| T2V regression | not recorded | `a188fe59-2031-4fac-a6f8-dc82ef7ea4c3` | 158.43 s | `output/h3/video/h1a_native_t2v_00003_.mp4` | 228,976 | `6F849052D9D3252FB8A5EBF4D1DDA7269C6328539A5BBC932DA58A803A9E0236` |
| Native I2V | `816c8270228f40c6b39735414e499ed9` | `5ea30fc7-e8a1-413b-9d4e-3bca0812c29c` | 142.28 s | `output/h3/video/h1b_native_i2v_00001_.mp4` | 413,441 | `7D322ABE7B159514C46A2690ED5145FF00C846579F8E3EDFD21DF65FB6C49386` |

The T2V session job id was not retained in the evidence record and is not
inferred from the output filename. The I2V job record used reference id
`00c89a2a6cdc49b8adc833b447a75700`, role `start_frame`, and the server-generated
path `inputs/00c89a2a6cdc49b8adc833b447a75700.png`.

`ffprobe` reported H.264 video and AAC stereo audio at 32 kHz for both files,
with 608 x 352, 24 FPS, 124 video frames, and 5.167 seconds media duration.
The MP4 files remain ignored and are not part of this evidence commit.

## Resource observation

During active I2V generation, the H3 status endpoint was sampled while the
queue reported one running job:

- total VRAM: `12,878,086,144` bytes;
- sampled free VRAM: `2,355,837,824`, `2,403,420,544`, `2,697,017,283`,
  `2,388,937,088`, and `2,391,296,384` bytes;
- sampled free RAM: `3,205,750,784`, `3,128,602,624`, `3,103,027,200`, and
  `3,190,931,456` bytes from total `68,476,002,304` bytes;
- OOM: none.

After completion, model-cache residency reduced free VRAM to roughly 0.7 GB;
that post-job state is recorded separately from the active-generation samples.

## Committed visual evidence

- [First frame](frames/first_frame.png) — SHA-256
  `14C6966ED60B804A037E99969E9ED798437D77047A4866B6C83DCA65E85584F5`
- [Middle frame](frames/middle_frame.png) — SHA-256
  `FC2B90A3AB29B4863AC514215100437C4100064DB086D881F99909D869DBE463`
- [Last frame](frames/last_frame.png) — SHA-256
  `E0CB3B1C0363E26F1D9EB0FE2AE2CBD604AD2DE19C84642C77C3118325459D84`
- [Contact sheet](contact_sheet.png) — SHA-256
  `60A64E1F8A985C6C37AD90F1DE9D9F1603354899BF285DD67E8A8BBCC9200377`

The source reference was the already committed H0.1 Native first frame at
`docs/h3/evidence/reference-implementations/native/2026-09-08_generation/frames/first_frame.png`.
No new reference image or model weight was added to the repository.

## Validation evidence

The H1B Python tests distinguish valid PNG/JPEG upload, invalid decode, size
limit, unsafe/traversal filename, missing asset, preview serving, and route
selection. The browser smoke verifies Add/Replace/Remove, retained controls,
visible Start Frame state, T2V regression, and Native I2V completion. See the
machine-readable [manifest](manifest.json) and the
[H1B report](../../../reports/H1B_SINGLE_REFERENCE_NATIVE_I2V_REPORT.md).
