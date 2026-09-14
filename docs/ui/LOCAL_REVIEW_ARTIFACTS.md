# Local Review Artifacts Index

> **Notice**: The artifacts listed in this index are **LOCAL ONLY** and stored in gitignored directories (`output/ui-review/`, `output/experiments/`). All file paths are repository-relative and exist on the development workstation where the runs were executed. They are not checked into Git and may not exist on other clones. This index serves to record their location, provenance, and associated commits for future maintainers and review.

---

## 1. Manga UX Cleanup2

- **Date**: 2026-09-15
- **Card**: `MANGA-UX-HORIZONTALIZATION-CLEANUP2`
- **Code Commit**: `26dd3c440cfe0450dbf93ad3ecb0e4de5c037b29`
- **Purpose**: Pre-Astra H3 / Manga horizontalization visual acceptance.
- **Location (`LOCAL-REPO[ComfyUIPortable]`)**:
  `output/ui-review/2026-09-15/MANGA-UX-CLEANUP2/`

### Artifacts:
- `H3_VIDEO_BASELINE.png`
- `MANGA_GENERATE.png`
- `MANGA_AUTHORING.png`
- `REVIEW_MANIFEST.txt`

---

## 2. H3 Manga Tone Comparison (Exp1 Retry2)

- **Date**: 2026-09-15
- **Card**: `H3-MANGA-TONE-COMPARISON-EXP1-RETRY2`
- **Code HEAD**: `9319baf2c1db8885397a460c86dd87b4675342e4`
- **Purpose**: Three-route H3 Manga Tone / Illustrious bounded GPU comparison.
- **Location (`LOCAL-REPO[ComfyUIPortable]`)**:
  `output/experiments/h3-manga-tone/2026-09-15/EXP1_RETRY2/`

### Artifacts:
- `comparison/route_A_h3_normal.png`
- `comparison/route_B_h3_manga_tone.png`
- `comparison/route_C_illustrious_finish.png`
- `comparison/route_C_downscaled_608x352.png`
- `COMPARISON_MANIFEST.txt`
- `H3_MANGA_TONE_COMPARISON_EXP1_RETRY2_REPORT.md`

### Recorded Technical Result:
- Route A: PASS
- Route B: PASS
- Route C: PASS
- Manga Tone screentone classification: line / flat-tone manga rendering without clear regular dot evidence
