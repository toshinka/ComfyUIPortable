# VP2A — Native Ref2VA / R2V Feasibility evidence

Date: 2026-09-10 JST

Decision: `ACQUISITION REQUIRED`

Publication: `LOCAL MAIN / PUSH PENDING` for this VP2A report and evidence
package. VP1 publication is recorded separately as
`PUBLISHED ON MAIN` at `41da0bf804d049adc40e2ae2d5abfdd59eabc703`.
Owner acceptance remains `PENDING`.

Report: [VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md](../../../reports/VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md)

Manifest: [manifest.json](manifest.json)

## Gate result

The exact Native Ref2VA model was not present in the approved external H3
model library:

```text
E:\Data\Models\StableDiffusion\minimaxH3\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors
expected bytes: 20,970,379,616
expected SHA-256: 9255F52B6677845AD238F20DFAAFA94727053694127AB7F255C048F0F9365779
result: NOT FOUND
```

The targeted scan under `E:\Data\Models\StableDiffusion\minimaxH3` returned
zero exact filename hits. The diffusion directory contained the existing
FL2VA file only. The same exact filename was absent from the Portable
`h3/model_store/` and `ComfyUI/models/` checks. No download, replacement,
license acceptance, or model copy was attempted.

H0/H0.1 evidence records the MiniMax H3 Community License Agreement and its
territory/use/redistribution review requirement. It also records Ref2VA as
explicitly deferred and not acquired. No exact Owner authorization for this
artifact is recorded, so the acquisition gate is `OWNER ACTION REQUIRED`.

## Native source audit

`ComfyUI/comfy_extras/nodes_minimax_h3.py` contains the installed
`MiniMaxH3ReferenceToVideo` source contract. It declares one `ref_images`
AutoGrow group with a maximum of 9, one `ref_videos` group with a maximum of 3,
three same-index `ref_video_audios`, and three standalone `ref_audios`. It also
declares `ref_image_size` values `match` and `max`, and returns positive
conditioning plus an AV latent. The source audit is `PASS`; runtime node
loading and generation are `NOT TESTED` because the exact model is absent and
unauthorized.

## Stage status

```text
Stage A Picture-only: NOT TESTED
Stage B Picture + one Video: NOT TESTED
Picture influence: NOT TESTED
Video influence: NOT TESTED
12GB/OOM/retry telemetry: NOT TESTED / NOT RECORDED
Post-Ref2VA T2V transition: NOT TESTED
Browser R2V UI: NOT IMPLEMENTED
MP4/model artifacts in evidence: NONE
Owner acceptance: PENDING
STOP BEFORE DOWNLOAD
```

The approved local H3 robot Picture and prior VP1 motion outputs were not
consumed in this stopped pass. No external reference video was downloaded.

Docs-only validation: VP2A and updated VP1 manifests parse as JSON, targeted
`git diff --check` is `PASS`, and no stale VP1 `LOCAL MAIN` publication wording
remains in the corrected canonical/report/evidence files.
