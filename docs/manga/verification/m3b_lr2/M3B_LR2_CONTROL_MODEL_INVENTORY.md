# M3B-LR2 Control Model Inventory

Date: 2026-09-10 JST  
Card: M3B-LR2  
Baseline: `1db61c19c076d8f66f18492f30157c53f6dac92f`  
Observed `HEAD` / `origin/main`: `e65e484a59d2b50610a3b6a20ee79d40a95f7079`

## Scope

This is a Portable-local inventory only. No model download, external dependency
installation, or model-file mutation was performed.

## Checked locations

- `ComfyUI/models/controlnet/`
  - `put_controlnets_and_t2i_here`: 0 bytes
  - no `.safetensors`, `.pth`, or `.pt` ControlNet model present
- `models/controlnet/`: not present
- `ComfyUI/custom_nodes/ComfyUI-Advanced-ControlNet/`: present
- `ComfyUI/nodes.py`: built-in `ControlNetLoader`, `DiffControlNetLoader`, and
  `ControlNetApplyAdvanced` registrations present
- `ComfyUI/custom_nodes/ComfyUI-Advanced-ControlNet/adv_control/nodes_main.py`:
  `ACN_ControlNetLoaderAdvanced`, `ACN_DiffControlNetLoaderAdvanced`, and
  `ACN_AdvancedControlNetApply_v2` present

## Candidate inventory

| Candidate | Local file | Size | SHA256 | Compatibility basis | Decision |
|---|---|---:|---|---|---|
| `CN-anytest4_illustrious2_A.safetensors` | absent | unavailable | unavailable | Referenced by archived Manga workflows 66–71 and the historical Phase 3I report as an Illustrious-oriented ControlNet; no local model bytes are available to verify or execute | Not selectable |

No second or third local model candidate was found. The installed
Advanced-ControlNet package proves node availability only; it does not prove
compatibility for a missing model.

## Archived workflow evidence

Workflows 66–71 are under `workflows/manga/Archive/`. They parse and reference
the candidate filename above through `ControlNetLoader` and
`ControlNetApplyAdvanced`, but their presence is not used as parity proof or as
current runtime evidence. Their historical workflow SHA256 values are recorded
in the LR2 report.

## Gate result

```text
STOPPED:
CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED
```

Stage 2 A/B workflow construction and live generation were not run because no
locally present SDXL / Illustrious-compatible ControlNet model could be
established without downloading a model or relying on filename-only inference.
