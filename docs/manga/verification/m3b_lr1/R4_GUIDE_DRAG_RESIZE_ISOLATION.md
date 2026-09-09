# R4 — Guide-local drag/resize isolation

- Result: `PASS`
- Evidence mode: live ComfyUI pointer actions plus document-state comparison.

Dragging `figure_1` changed only its Guide-local area from approximately `(x: 0.08, y: 0.12, w: 0.34, h: 0.68)` to `(x: 0.1628, y: 0.2308, w: 0.34, h: 0.68)`. Resizing the selected corner then produced `(x: 0.1628, y: 0.2308, w: 0.398, h: 0.7575)`.

Across both operations, the Character Instance areas for `inst_1` and `inst_2` remained unchanged. During this check the CSS zoomed-canvas handle mismatch was found and corrected: handle hit testing now uses the rendered CSS canvas dimensions returned by `getBoundingClientRect()`, matching pointer coordinates rather than the backing bitmap dimensions.
