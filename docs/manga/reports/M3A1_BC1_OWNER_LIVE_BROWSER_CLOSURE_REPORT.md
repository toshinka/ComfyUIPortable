# M3A1-BC1 Owner Live-Browser Closure and Publication Model Cleanup Report

Date: 2026-09-09 JST  
Card: M3A1-BC1  
Executor: LUNA local chat  
Owner acceptance: PENDING

## Execution truth

- Execution baseline: `a92237fe3eeb0f53e16c69d37763d388fedf2145`
- `origin/main` at execution: `a92237fe3eeb0f53e16c69d37763d388fedf2145`
- Web GPT SOL verified public baseline: `399b4d5f973c389f42cb1912be3abe153ad08678`
- Parent of the verified public baseline: `5c9da782316b99ceeb6ecfb85695bb6965d3bf35`
- M3A.1 implementation Review Target: `a7f0baaa89a2e315b0492573c9da19e50727928b`
- M3B authorization: `NO`

The execution checkout had moved beyond the SOL-verified public baseline only through unrelated H3 changes. The bounded Manga implementation target did not conflict with those changes.

## Scope and implementation correction

The requested causal path was checked as a real ComfyUI browser flow:

```text
Visual Panel Frames UI
  -> TEGAKI_AUTHORING_DOCUMENT
  -> Save / Reload
  -> TegakiMangaFrameOverlay
  -> SaveImage output
```

Implementation changed: **YES**, one allowed implementation file only:

- `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

The first live queue exposed the minimal browser failure: the optional `page_index` widget serialized as an empty string, so the Overlay path was invalid and the queue surfaced only a PreviewImage result. The canonical workflow widget values were reduced to `[4, 0]`, allowing the live UI to serialize `page_index: 0` and reach Overlay -> SaveImage. No JavaScript, schema, runtime, or ComfyUI core change was necessary.

The initial B3 resize miss was a live graph hit-target/zoom issue at 38%, not a product defect. At 100% graph zoom the Frame 2 resize succeeded, so no speculative source patch was made.

## Changed documentation and evidence files

- `GITHUB_MANGA.txt`
- `docs/manga/STATUS.md`
- `docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
- `docs/manga/cards/README.md`
- `docs/manga/cards/current/README.md`
- `docs/manga/cards/current/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE.md`
- `docs/manga/cards/completed/M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE.md` (byte-identical move)
- `docs/manga/reports/README.md`
- `docs/manga/reports/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md`
- `docs/manga/verification/m3a1_browser/` (B1-B9 evidence and manifest)

## Regression checks

| Check | Result |
|---|---|
| `python scripts/test_m3a1_frame_overlay_runtime_truth.py` | PASS, 14/14 |
| `python scripts/test_m3a_visual_frame_contract.py` | PASS, 7/7 |
| `python scripts/test_m2b1_authoring_regression.py` | PASS, 6/6 |
| `python_embeded/python.exe scripts/test_m1_1_canonical_workflow_wiring.py` | PASS, 7/7 |
| `node scripts/test_m2b_minimum_hand_editor.mjs` | PASS, 19/19 |
| `python scripts/run_m3a1_frame_verification.py` | PASS, V0-V4; tracked historical manifest restored unchanged |
| `git diff --check` | PASS; only the existing line-ending warning was reported |

## Live browser B0-B9

### B0 — baseline load: PASS

After server restart and browser reload, the canonical Minimum-Hand Manga workflow loaded with the custom authoring DOM and FrameOverlay node. With the corrected workflow, the default zero-frame queue reached SaveImage successfully (`MangaDraft_M1_00007_.png`). No missing-node error was observed.

### B1 — Visual Panel Frames layer: PASS

The live DOM exposed the `Visual Panel Frames` layer, frame canvas, frame toolbar, frame chips, and thickness control. `Scene Regions` and `Character Staging` remained separate controls. Evidence: `B1_VISUAL_FRAME_LAYER.png`.

### B2 — create frames: PASS

`Copy Frames from Scenes` created two selectable unique IDs, `frame_1` and `frame_2`. The live document reported `Scenes: 2 / 6 | Frames: 2` and `visual_frames` length 2. Evidence: `B2_TWO_FRAMES_CREATED.png`.

### B3 — drag / resize: PASS

Frame 1 drag changed `area.x` from `0.08` to `0.16`. A separate live pass resized Frame 2 to `x=0.08, y=0.5655, w=0.7737, h=0.3745`. Scene geometry remained unchanged, and changed frames used canonical `area` without an unnecessary `shape` key. Evidence: `B3_FRAME_DRAG_RESIZE.png`.

### B4 — white gutter and black frames in final output: PASS

The final SaveImage output `ComfyUI/output/MangaDraft_M1_00008_.png` showed the source art inside two frames, white outside the frame union and between frames, and black borders. Evidence: `B4_FINAL_WHITE_GUTTER_BLACK_FRAMES.png`.

### B5 — per-frame 2 px / 8 px thickness: PASS

The same final output run used Frame 1 `border_thickness=2` and Frame 2 `border_thickness=8`; the top border was visibly thin and the lower border visibly thick. Evidence: `B5_FINAL_2PX_8PX.png`.

### B6 — Save / Reload: PASS

The browser workflow `M3A1_BC1_BROWSER` was saved, opened blank, refreshed, and reloaded from the workflow library. The reloaded document retained `frame_1`, `frame_2`, both canonical areas, and thickness values 2 and 8 without shape/area drift. Evidence: `B6_AFTER_SAVE_RELOAD.png`.

### B7 — post-reload causal edit: PASS

After reload, Frame 1 was dragged again from `x=0.08` to `x=0.16` while the Scene rectangles remained at `x=0.08`. The next browser queue produced `ComfyUI/output/MangaDraft_M1_00009_.png`; the output visibly used the new Frame 1 position with the moved white gutter, not the old position. Evidence: `B7_POST_RELOAD_DRAG_FINAL_OUTPUT.png`.

### B8 — zero-frame regression: PASS

The unique zero-frame fixture was loaded and queued through the browser. SaveImage produced `ComfyUI/output/MangaDraft_M1_00010_.png`, a full source page with no fake full-page frame and no white-page conversion. The corresponding history entry contained `visual_frames: []`. The existing structural pixel oracle remains the exact pixel-identical pass-through authority. Evidence: `B8_ZERO_FRAME_PASS_THROUGH.png`.

### B9 — CAST regression smoke: PASS

After frame operations, live CAST Master remained operable. `Add CAST` created `cast_1`, Scene 1 remained selectable, `Character Staging` was selectable, and placing Character 1 created `inst_1`. Dragging the Character Rough Region changed its instance area from `x=0.1472, w=0.336` to `x=0.2715, w=0.2117`. Evidence: `B9_CAST_REGRESSION.png`.

## Publication model cleanup

- TF2.1 card moved from `cards/current/` to `cards/completed/` byte-for-byte; SHA256 was unchanged: `677D22956792833D0EB9EEC33036F7E3153719A96BCF28A084161B3FF9EAC1B1`.
- The TF2.1 historical report body was not changed.
- Current authority now uses `Latest SOL-verified public commit: 399b4d5f973c389f42cb1912be3abe153ad08678` rather than a moving repository-publication field.
- Current authority now routes to the BC1 Card/report and records Browser `PASS`, Visual `PASS`, Owner acceptance `PENDING`, and M3B `NO`.
- Historical M3A.1 implementation report was not changed.

## Evidence

Manifest: `docs/manga/verification/m3a1_browser/M3A1_BROWSER_CLOSURE_MANIFEST.json`.

Browser evidence files:

- `B1_VISUAL_FRAME_LAYER.png`
- `B2_TWO_FRAMES_CREATED.png`
- `B3_FRAME_DRAG_RESIZE.png`
- `B4_FINAL_WHITE_GUTTER_BLACK_FRAMES.png`
- `B5_FINAL_2PX_8PX.png`
- `B6_AFTER_SAVE_RELOAD.png`
- `B7_POST_RELOAD_DRAG_FINAL_OUTPUT.png`
- `B8_ZERO_FRAME_PASS_THROUGH.png`
- `B9_CAST_REGRESSION.png`

## Final gate

LUNA live-browser verdict: **PASS**  
Visual evidence: **PASS**  
Owner acceptance: **PENDING**  
M3B authorization: **NO**  
M3A1-BC1 publication: **LOCAL**  
Owner push required: **YES**

## Owner verification items

1. Open Visual Panel Frames and confirm Frame add/copy is natural to operate.
2. Confirm Frame drag/resize behavior matches the intended production gesture.
3. Confirm the Queue result's white gutter and black frame are production-correct.
4. Confirm the visible 2 px / 8 px border difference is expected.
5. Confirm Save/Reload preserves the frame operation and output behavior.

Owner acceptance remains PENDING until the Owner explicitly accepts or rejects these items. No M3B work is authorized by this report.
