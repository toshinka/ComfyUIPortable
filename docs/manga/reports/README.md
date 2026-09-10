# Manga Report Index

Current and historical Manga reports are collected in this directory.

Historical implementation report: [M3A.1 Frame Runtime Truth](M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md).
Latest published operational report: [M3B-LR5 CAST + Figure-Masked CLEAN Compatibility Research Report](M3B_LR5_CAST_MASKED_CLEAN_COMPATIBILITY_RESEARCH_REPORT.md).
Latest local execution report: [M3B-LR6 CAST Soft-Edge Figure Mask Compatibility Research Report](M3B_LR6_CAST_SOFT_EDGE_FIGURE_MASK_COMPATIBILITY_RESEARCH_REPORT.md).
M3A1-OA1 Owner Acceptance Gate Report remains the preceding milestone gate report.
M3B-LR2 stopped before A/B generation because local ControlNet compatibility was
not established; its report remains a historical local-stop record.
M3B-LR2R1 completed: shared-storage model identity, ControlNet loader,
eight-image A/B generation, canonical no-Guide regression, and required
LR1/M2B regressions are recorded. Its historical execution report retains
`Publication: LOCAL`; current publication truth is PUBLISHED / SOL REVIEWED.
M3B-LR3 completed with final SOL result `OPTION_A_INCONCLUSIVE`. M3B-LR4
completed with six-output OFF/GLOBAL/MASKED evidence, SOL-reviewed result
`LOCALITY_SUPPORTED`, and no production integration. M3B-LR5 completed with
four-output CAST_OFF/CAST_MASKED evidence and SOL-reviewed result
`CAST_MASKED_CONFLICT`; its key failure was a hard effect-mask boundary with
degraded quality. M3B-LR6 completed locally with six-output OFF/HARD/SOFT
evidence and result `SOFT_MASK_CONFLICT`; its radius-16 soft edge did not
remove the boundary artifact. Owner push and SOL review remain pending.
TF2.1 publication-truth report remains historical at [M3A1-TF2.1 Post-Push Publication Truth Closure Report](M3A1_TF2_1_POST_PUSH_PUBLICATION_TRUTH_CLOSURE_REPORT.md).

Namespace work is recorded in
[MANGA_DOCUMENT_NAMESPACE_MIGRATION_REPORT.md](MANGA_DOCUMENT_NAMESPACE_MIGRATION_REPORT.md).
The 2026-09-09 physical consolidation is recorded in
[MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md](MANGA_DOCS_WORKFLOW_NAMESPACE_MIGRATION_REPORT.md).
Phase 3L prior-art research moved to
[`docs/manga/research/`](../research/PHASE3L_PRIOR_ART_ADOPTION_AUDIT.md); its
historical pinned URL remains valid at the old commit and path.
