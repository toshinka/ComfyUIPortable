# H1C — Frame-Bridged Continuation evidence

Date: 2026-09-09 JST

Status: `VERIFIED SOURCE/LOGIC + VERIFIED BROWSER UI + VERIFIED LOCAL GENERATION`

Stage: `H1C / Frame-Bridged Continuation`

Implementation commit: `a92237fe3eeb0f53e16c69d37763d388fedf2145`

Additional fix commit: `ff577a0c` — capture a decoded near-final Browser frame
before uploading the bridge PNG.

Report: [H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md](../../../reports/H1C_FRAME_BRIDGED_CONTINUATION_REPORT.md)

Owner acceptance: `PENDING`

## Scope

This package records the bounded H1C flow:

```text
completed Start + End History result
  -> Use settings
  -> Continue
  -> Browser decodes and captures the source near-final frame
  -> existing /api/references upload in start_frame slot
  -> Start Frame = bridge, End Frame = empty
  -> manual prompt edit
  -> one real Native continuation generation
```

No new backend/API, workflow, model, dependency, persistence, shared ComfyUI,
Manga, Segment, REF2VA, Still, Studio, Timeline, or project architecture was
added.

## Browser acceptance record

Browser target: `http://127.0.0.1:8190/` in the Codex in-app Browser using
CUA/Playwright. Native backend: `http://127.0.0.1:8188/`.

The completed P2 source History entry was:

| Field | Observed value |
|---|---|
| Source job | `970a614fed4e43a88d5bbf9f22f0bd7a` |
| Route | `native_i2v` / `Start + End` |
| Prompt | `A small paper kite drifts across a warm evening sky, gentle motion, clean illustrative style.` |
| Resolution / duration | `608 x 352` / `5s` |
| Seed / steps | `24680` / `20` |
| Source Start Reference | `27749594c9704c38aa3da20e533c90d6` |
| Source End Reference | `163a4dccec434f6b84b7b86239d49782` |
| Elapsed | `157.28s` |
| MP4 | `output/h3/video/h1b1_native_fl2va_00004_.mp4` (ignored) |
| MP4 SHA-256 | `8D27B20B1570BC3E8DEB40E6ECC5A48444499C0F332BFAD6E2E20A982089F52D` |

For P2 live acceptance, the Prompt and Seed were first changed to temporary
values. `Use settings` restored the source Prompt, `608x352`, `5`, numeric Seed
`24680`, Steps `20`, both original Start/End references, and announced
`Settings loaded.`. No job was created.

For H1C, `Continue` used the server-issued source URL
`/api/jobs/970a614fed4e43a88d5bbf9f22f0bd7a/video`. The final clean Browser run
reported:

| Field | Observed value |
|---|---|
| Status | `Continuation prepared. Edit the prompt if needed, then Generate.` |
| Capture duration | `5.167s` |
| Capture currentTime | `5.125s` |
| Bridge dimensions | `608 x 352` |
| Bridge Reference | `8a13cf3913b640c5abbcafcdcb4ec627` |
| Bridge endpoint | `/api/references/8a13cf3913b640c5abbcafcdcb4ec627` |
| Bridge PNG SHA-256 | `636FA8552329D0B0F73D3206E0B455EF0FEB6A6F344372ED3CF342250F68EA2D` |
| Form after Continue | Start bridge selected; End empty; Generate enabled; no auto-generation |

The bridge Reference id is distinct from both source input Reference ids. The
original uploaded Start PNG has SHA-256
`43D29D07B5D0B4A2C4650A2C840AE6CF07980714008FDDB1D1008B0E08CF030E`; the
bridge PNG is separately canvas-encoded and is not byte-identical. Provenance
is established by the source job/video URL, near-final capture time and
dimensions, the new Reference id, the stored bridge SHA, and the visual
comparison in `contact_sheet.png`.

The final clean Browser DOM also read:

```text
Prompt = source History prompt
Resolution = 608x352
Duration = 5
Seed = 24680
Steps = 20
Start Frame = /api/references/e7bb38c4ea2a4a138e3b08f797d33cf3
End Frame = No End Frame selected.
Status = Continuation prepared. Edit the prompt if needed, then Generate.
```

The `e7bb...` Reference is a final-code, no-generation recheck. The accepted
Native continuation below used the equivalent verified bridge from the same
source video, `8a13...`, so its job metadata remains directly attributable.

## Real Native continuation

After editing the prompt to:

```text
The kite continues drifting into a brighter patch of evening sky, gentle motion, clean illustrative style.
```

the Browser Generate action submitted one real Native job:

| Field | Observed value |
|---|---|
| Continuation job | `ebe2a7b6621849bdb37833826c9235a0` |
| Route | `native_i2v` / `Start Frame` |
| Reference | `8a13cf3913b640c5abbcafcdcb4ec627` |
| End Reference | `null` |
| Visible Browser result | `Start Frame · Completed in 138.2s · 608 x 352 · 5s` |
| Native elapsed | `138.22s` |
| MP4 | `output/h3/video/h1b1_native_fl2va_00006_.mp4` (ignored) |
| MP4 SHA-256 | `31D121A5110CF473B2A8129A38612DBDD67D2FC0DAC9EBAADD58BDAAD78D1828` |

`ffprobe` measured both source and continuation outputs as H.264/AAC,
`608x352`, `24fps`, `124` video frames, and `5.167s` duration.

## Runtime telemetry

Verified stack: NVIDIA GeForce RTX 4070, 12,878,086,144-byte VRAM, 68,476,002,304-byte
system RAM, embedded Python `3.13.14`, PyTorch `2.13.0+cu130`, ComfyUI `0.30.0`,
custom nodes disabled, H3 model store isolated.

For the accepted continuation monitor, 10-second samples observed a maximum
VRAM-used value of `11,784.3 MB` (minimum free `497.2 MB`) while the job was
running. OOM count was `0`; retry count for the accepted job was `0`. The Native
process was PID `30580`; the post-run working set sample was `27,767.8 MB`.
Peak RAM was not captured as a continuous metric.

An earlier launcher-mode source attempt failed with ComfyUI logger
`OSError [Errno 22] Invalid argument` while flushing tqdm stderr; it was not an
OOM or model/input failure. The verified source and continuation runs used the
direct Native PTY launch with the same existing model/workflow stack.

## Media evidence

The MP4 files are intentionally not committed. These extracted PNGs and the
contact sheet are the bounded committed visual evidence:

| Asset | Role | SHA-256 |
|---|---|---|
| [source_first.png](source_first.png) | source output first frame | `0893CBACAD5330F101CA6BFE1DF1D8749672B7228F0F47E98D35DD21757A3D07` |
| [source_mid.png](source_mid.png) | source output at 2.5s | `BA5A7F4FE56AEE1AE9FAAD6E0CC603DD8D6BD00C5E24D2899E1776DB5F88D35B` |
| [source_last.png](source_last.png) | source output near-final frame | `11B0DDD118BD60C0FED961F5FCD7C6A0224445A205A80010D53DB08BFE7F63EB` |
| [bridge_start_final.png](bridge_start_final.png) | Browser canvas PNG uploaded by Continue | `636FA8552329D0B0F73D3206E0B455EF0FEB6A6F344372ED3CF342250F68EA2D` |
| [continuation_final_first.png](continuation_final_first.png) | continuation first frame | `5FC2251BF8956A50F1098F9093919DA03547BE4ED55EA5CD1D8273731BC1222E` |
| [continuation_final_mid.png](continuation_final_mid.png) | continuation at 2.5s | `B80B30C9F91D667D7F2355BE941F07EC3349AB7D16443E8542ACE175C41D95A0` |
| [continuation_final_last.png](continuation_final_last.png) | continuation near-final frame | `BF3D9E95B89279BAF2A1197329A74DD3CD8C9C185CF5314C70AED126B812EE59` |
| [contact_sheet.png](contact_sheet.png) | source/bridge/continuation comparison | `9985BF94BB3DBF381413E0DD5BD492021AC215F838F2F9B25C35CCB74D6FE691` |

The independently extracted source near-final PNG and Browser canvas bridge
are not claimed byte-identical. Their mean absolute RGB difference was about
`1.447`; the contact sheet shows the bridge and continuation first frame carry
the source near-final robot image. This is visual/provenance evidence, not a
claim of model aesthetic quality or Owner approval.

## Verification

- P1: `node h3/tests/verify_h1b_ui.mjs` — `36 PASS`.
- P2: `node h3/tests/verify_h1b1_p2_ui.mjs` — `44 PASS`.
- H1C: `node h3/tests/verify_h1c_continuation.mjs` — `38 PASS`.
- Python: `python -m unittest discover -s h3/tests -p 'test_*.py'` — `32 passed`.
- JavaScript syntax: `app.js`, `history-settings.js`, `job-status-copy.js`,
  and `continuation-source.js` — `PASS`.
- `python -m compileall -q h3/app h3/adapters` — `PASS`.
- `git diff --check` — `PASS`.

## Boundary

H1B.1/P0/P1/P2 remain available as regression capabilities. H1C is the current
H3 gate, not Owner acceptance or public deployment. H3 Still, REF2VA, ordered
generic multi-reference, Segment, Studio, Timeline, Storyboard, Cast, 3D,
Manga, and persistent project schema remain not started.
