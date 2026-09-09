# R2 — Standard upload and contain placement

- Result: `PASS`
- Evidence mode: live ComfyUI browser file chooser and document state.
- Fixture: `fixtures/rough_guide_live.png` (`320x240`, PNG).

The Guide was uploaded through the normal ComfyUI file chooser and the extension's `/upload/image` boundary. The persisted reference was the canonical relative path:

`tegaki_manga_guides/rough_guide_live.png`

The live document recorded `guide_1` with `guide_type: rough_manga`, `enabled: true`, source dimensions `320x240`, and contain placement `x: 0`, `y: 0.2434`, `w: 1`, `h: 0.5132`. The uploaded file remained at the ComfyUI input boundary after later Guide removal.
