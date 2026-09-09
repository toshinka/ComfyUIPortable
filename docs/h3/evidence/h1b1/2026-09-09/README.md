# H1B.1 Start / End Frame Native FL2VA Evidence — 2026-09-09

Status: `IMPLEMENTED`, `VERIFIED LOCAL STARTUP`, `VERIFIED LOCAL GENERATION`,
and `VERIFIED BROWSER UI GENERATION`.

Owner acceptance: `PENDING`.

This package records the bounded H1B.1 slice: two fixed named keyframe slots,
`start_frame` and `end_frame`, submitted through the browser and bound to the
Native MiniMax H3 `first_frame` and `last_frame` inputs. It is technical
evidence, not visual-quality approval or Owner production acceptance.

## Runtime boundary

- Canonical launcher: `h3/run_h3.bat`
- H1A compatibility launcher: `h3/run_h1a.bat`
- Skin: `http://127.0.0.1:8190/`
- Native ComfyUI backend: `http://127.0.0.1:8188/`
- H1B.1 adapter: `h3/adapters/native_i2v.py`
- H1B.1 workflow: `workflows/h3/H1B1_NATIVE_FL2VA_BASE.json`
- Isolated model store: `h3/model_store/`
- Ignored generated output: `output/h3/video/`
- Ignored uploaded runtime input: `output/h3/inputs/`
- No custom nodes, shared ComfyUI model tree, Manga runtime, or Manga workflow
  was used or modified.

The canonical request is:

```json
{
  "references": {
    "start_frame": {"id": "<server-issued-id>", "role": "start_frame"},
    "end_frame": {"id": "<server-issued-id>", "role": "end_frame"}
  }
}
```

The legacy H1B `reference: {id, role: "start_frame"}` shape remains accepted
and is normalized to the Start Frame slot on the historical H1B graph. There is
no ordered generic reference list and no route selector in the UI.

## Workflow provenance

The production graph is adapted from the official
[Comfy-Org MiniMax H3 I2V workflow](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_i2v.json).

| Field | Value |
|---|---|
| Official workflow commit | `66abae5205f7c5105281146fa109f7c12801d268` |
| Official workflow SHA-256 | `4DC94E9EA308C1D60409E7F55DBA5E2788DAB4659C2DBB90F1E9481498767540` |
| Local H1B.1 workflow SHA-256 | `0072756BBB3A259E83D441054C838AC18CE8A40EACFEC63D0C11948001F685E9` |
| Baseline | 608 x 352 / 5 seconds / 124 frames / 24 FPS / 20 steps |
| Fixed roles | `start_frame`, `end_frame` |
| Optional Native edges | `first_frame` and `last_frame` |
| Output prefix | `video/h1b1_native_fl2va` |

The base workflow is not used as a dummy-image submission. The adapter removes
the unused loader node and optional edge for Start-only or End-only requests,
and binds both loaders only for Start+End.

## Browser event record

The live browser session used the in-app browser against the canonical launcher.
AX state and live completion views were captured in the CUA transcript; the
durable files in this directory are the generated frame triplet and contact
sheet.

| Event | Observed result |
|---|---|
| Add Start Frame | Existing committed H0.1 `first_frame.png` accepted; thumbnail and `Start Frame` card displayed |
| Add End Frame | Existing committed H0.1 `last_frame.png` accepted independently; both cards displayed |
| Failed replacement | Non-image workflow JSON rejected with `Reference must be PNG, JPEG, or WebP.`; existing selection remained |
| Start Remove | Start cleared while End remained selected |
| Start restore/replace | Middle frame restore and first-frame replacement worked; End remained selected |
| Start-only generation | Visible `Running` → `Completed · Start Frame`; Preview and History updated |
| Start+End generation | Visible `Running` → `Completed · Start + End`; Preview and History updated |
| End-only generation | Visible `Running` → `Completed · End Frame`; Preview and History updated |
| T2V regression | Both slots cleared; visible `Running` → `Completed · Text only` |

The final UI state had both slots empty after the T2V regression. The browser
completion views were not persisted as screenshot binaries; this is stated
explicitly rather than inferred from a missing file.

## Native output record

| Route label | Job id | Prompt id | Elapsed | Output | Bytes | SHA-256 |
|---|---|---|---:|---|---:|---|
| Start Frame | `76a93d28ea2c485d8e0ebd678e20b7b1` | `94dcbf9e-8f66-4cc2-bb48-125da5db1fb3` | 161.67 s | `output/h3/video/h1b1_native_fl2va_00001_.mp4` | 498,693 | `E75435D266514801CBD76996A51870B1637E73AFB47535BAB47FE329ECE79DAD` |
| Start + End | `7d3aac4b7d62434e9b71859846bcd4d9` | `c91ae0b8-09dd-488b-9bd3-2bfae61e8f68` | 145.94 s | `output/h3/video/h1b1_native_fl2va_00002_.mp4` | 467,291 | `3F233C69F101A7063E3A97AD64F1DE0F2DB51E7FE6376DA1A5CCF34486326883` |
| End Frame | `30b82801fa3f4e1b984679f132225bdf` | `c86647cb-2446-423b-a210-91e33ce05979` | 130.97 s | `output/h3/video/h1b1_native_fl2va_00003_.mp4` | 689,696 | `CE192DA29B145674296707421E6CB3BA76545A737D64757BCA66CB4C2B053A65` |
| Text only regression | `03d17c6a98a7412a9c2b5c5a5d1fb6db` | `e694f0b4-2886-456f-babd-62834dc9ba42` | 112.54 s | `output/h3/video/h1a_native_t2v_00004_.mp4` | 534,817 | `22218C7FFECF602F13D3D76007B2C67708B672FD105347A6C28FE2AE2AB5AA61` |

`ffprobe` reported H.264 video and AAC stereo audio at 32 kHz for all four
files, with 608 x 352, 24 FPS, 124 video frames, and 5.167 seconds media
duration. The MP4 files remain ignored and are not part of this evidence
commit.

The Start input was:

`docs/h3/evidence/reference-implementations/native/2026-09-08_generation/frames/first_frame.png`

The End input was:

`docs/h3/evidence/reference-implementations/native/2026-09-08_generation/frames/last_frame.png`

Both source images were already committed H0.1 evidence. Browser uploads were
server-issued runtime copies under `output/h3/inputs/`; no new private image
or model weight was added.

Native MP4 metadata for the Start+End run confirmed:

```text
node 131 MiniMaxH3ImageToVideo:
  first_frame = ["132", 0]
  last_frame  = ["133", 0]
node 132 LoadImage: inputs/e2c6b035a25d4902817eac81f9a82506.png
node 133 LoadImage: inputs/7a3af13037664071bdfc53bceee939a8.png
```

## Resource observation

During active Start+End generation, the H3 status endpoint was sampled while
one Native job was running:

- total VRAM: `12,878,086,144` bytes;
- sampled free VRAM: `2,147,616,431` bytes at the recorded active sample,
  corresponding to `10,730,469,713` bytes used at that sample;
- total RAM: `68,476,002,304` bytes;
- sampled free RAM: `7,497,875,456` bytes;
- OOM: none;
- retry/fallback: none observed in the job history or Native log.

This is a sampled minimum/peak observation, not a hardware trace. After jobs,
model-cache residency changed free VRAM; those post-job readings are not
reported as active-generation peak usage.

## Committed visual evidence

- [Output first frame](start_end_output_frame_000.png) — SHA-256 `7026EBFEF6933378BE59FB853A45C76CFFD07946AF14545228CE247828516089`
- [Output middle frame](start_end_output_frame_061.png) — SHA-256 `1989947EB4755F146D7CB9578A6B6678DFBD6C2AA756938B2C6B91C78A04C008`
- [Output last frame](start_end_output_frame_123.png) — SHA-256 `06130DC5FF84A6560C7B69BD7990E237B8344F58DE9894197190B2282C8F1F43`
- [Contact sheet](start_end_output_contact_sheet.png) — SHA-256 `3203B931CA81DFFB1B60B98144749582D0077885C3A835C416AC65020DF175AE`

The contact sheet is a media inspection aid for the successful Start+End
output. It does not constitute Owner visual acceptance.

## Validation evidence

| Check | Result |
|---|---|
| Python unittest discovery | `32 passed` |
| H1B.1 UI/source smoke | `23 PASS` |
| JavaScript syntax | `node --check h3/app/static/app.js` passed |
| Python syntax | `compileall` passed |
| Workflow JSON parse | H1A, H1B, and H1B.1 passed |
| `git diff --check` | passed before implementation commit |
| Upload/security regression | valid image, unsupported role, invalid extension, malformed id, unsafe path, missing asset, and slot isolation covered |
| Browser Start-only | completed with real Native MP4 |
| Browser Start+End | completed with real Native MP4 |
| Browser End-only | completed with real Native MP4 |
| Browser T2V regression | completed with real Native MP4 |

See the machine-readable [manifest](manifest.json) and the
[H1B.1 report](../../../reports/H1B1_START_END_FRAME_NATIVE_FL2VA_REPORT.md).

## Explicit non-scope and review gate

H1B.1 does not start REF2VA, ordered generic multi-reference, Still,
Continuation, Segment, Timeline, Studio, Project/Shot/Take, Manga integration,
custom-node vendoring, ComfyUI core/frontend changes, persistent project
storage, or public deployment. No new model was downloaded. The existing
Illustrious Manga implementation, Manga documents, Manga workflows, and
shared ComfyUI runtime were not modified.

H1B.1 is ready for bounded Web GPT / Astra review as a local technical slice.
Owner acceptance remains `PENDING`. If the review is accepted, stop here until
a separately authorized next slice is issued.
