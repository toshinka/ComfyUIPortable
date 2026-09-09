# R5 — Save and reload persistence

- Result: `PASS`
- Evidence mode: live ComfyUI save shortcut and browser reload.

After the Guide asset, figures, associations, and resize were authored, the normal ComfyUI save shortcut removed the workflow dirty marker. A browser reload restored the document with `guide_1`, the canonical asset reference, both figure records, both instance associations, the resized `figure_1` area, and the unchanged Character Instance geometry.
