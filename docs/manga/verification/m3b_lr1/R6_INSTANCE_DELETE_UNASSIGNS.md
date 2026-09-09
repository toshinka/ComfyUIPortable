# R6 — Character Instance deletion unassigns but preserves Figure

- Result: `PASS`
- Evidence mode: live ComfyUI Character Staging action and document-state comparison.

Deleting `inst_2` removed that Character Instance and changed `figure_2.instance_id` to `null`. The `figure_2` record and its Guide-local area remained present. `figure_1 -> inst_1` was unaffected.
