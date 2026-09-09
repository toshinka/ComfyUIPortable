# M3B-LR2 — Rough Guide Generation Influence A/B Long-Run Report

Date: 2026-09-10 JST  
Card: M3B-LR2  
Execution mode: LONG-RUN BATCH  
Milestone authority: Web GPT SOL  
Final Owner product review: **DEFERRED**

## Result

```text
Classification: BLOCKED
Generation influence: BLOCKED
Production integration: NOT PERFORMED
Stopped early: YES
Reason: CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED
M3B-LR2 publication: LOCAL
```

The run stopped at the Stage 1 decision gate. `ComfyUI/models/controlnet/`
contains only the zero-byte placeholder `put_controlnets_and_t2i_here`; no
ControlNet model bytes are installed locally. The historical candidate
`CN-anytest4_illustrious2_A.safetensors` is referenced by archived Manga
workflows and an older report, but its local size and SHA256 cannot be checked,
so SDXL/Illustrious compatibility cannot be established for this Portable.

No external download, model mutation, dependency installation, or production
workflow/UI change was performed.

## Execution baseline

| Field | Value |
|---|---|
| Card baseline | `1db61c19c076d8f66f18492f30157c53f6dac92f` |
| Final HEAD | `e65e484a59d2b50610a3b6a20ee79d40a95f7079` |
| `origin/main` | `e65e484a59d2b50610a3b6a20ee79d40a95f7079` |
| Remote drift | H3-only commits after the Manga baseline; no Manga-file conflict |
| Latest SOL-verified Manga publication | `1db61c19c076d8f66f18492f30157c53f6dac92f` |

## Stage 0 — Publication truth

PASS. Current authority was updated to record LR1 as PUBLISHED with SOL review
PASS and generation influence NOT IMPLEMENTED, and to set M3B-LR2 ACTIVE before
the inventory gate. LR1's historical report wording was not rewritten.

## Stage 1 — Control backend inventory

### Installed execution nodes

- ComfyUI built-ins: `ControlNetLoader`, `DiffControlNetLoader`,
  `ControlNetApplyAdvanced` in `ComfyUI/nodes.py`.
- Installed custom node package:
  `ComfyUI/custom_nodes/ComfyUI-Advanced-ControlNet/`.
- Relevant Advanced-ControlNet nodes include
  `ACN_ControlNetLoaderAdvanced`, `ACN_DiffControlNetLoaderAdvanced`, and
  `ACN_AdvancedControlNetApply_v2` in `adv_control/nodes_main.py`.

Node availability is not model compatibility evidence.

### Candidate 1 — historical AnyTest Illustrious reference

```text
Model: CN-anytest4_illustrious2_A.safetensors
Local path: absent
Size: unavailable
SHA256: unavailable
Claimed architecture: historical report describes it as AnyTest v4 tuned for SDXL Illustrious
Evidence: archived workflows 66–71 and PHASE3I_CONTROLNET_LAYOUT_ASSIST_REPORT.md
Status: not executable in this Portable
```

The candidate was not selected. No other local ControlNet model candidate was
found. Workflow 71 was not used as parity proof.

Archived workflow fingerprints (inventory evidence only):

| Workflow | Bytes | SHA256 |
|---|---:|---|
| `66_VERIFY_POSE_GUIDE_ONLY_INWARD.json` | 24595 | `53F68E763F44514BDC6640F00F077C60F0CA51731D9BB35FFDFA9DDE43169C1B` |
| `67_VERIFY_HANDSHAKE_CANONICAL_PAIR_AND_FEATHER.json` | 25949 | `983385375D1206FC243A19FDF544AED8F6147639E7AC7BAF1E1C988E8B660264` |
| `68_VERIFY_MAINLINE_SUBSCENE_CONFLICT_FRIENDSHIP.json` | 28578 | `648A3507897A194C3434FE9BF81FA97B484D25BC689B3A7630EBB896C24B7426` |
| `69_VERIFY_MAINLINE_SUBSCENE_GEOMETRY_SWAP.json` | 28558 | `F3FF2D676BE5F7F22F7642369821E84EBD35A1DC7183B4348836874B9AA6F0A0` |
| `70_VERIFY_4PANEL_MIXED_SIMPLE_COMPLEX_PAGE.json` | 33086 | `88EE6BAAAFAA2F57BD07BEAAFA5EB847D6A188A6AB3D613481925A0802132B6F` |
| `71_VERIFY_EXTERNAL_REGIONAL_BACKEND_PARITY.json` | 24549 | `C88F2A5DF7360D7094274059BD5A261CE2CC8E53A7D545EBA3CBD58A51F66C04` |

Inventory evidence: [M3B_LR2_CONTROL_MODEL_INVENTORY.md](../verification/m3b_lr2/M3B_LR2_CONTROL_MODEL_INVENTORY.md)

## Stage 2 — Experimental A/B workflow

**NOT RUN.** No research workflow was created. The canonical
`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` generation path was not changed.

Because no compatible local model was established, there are no selected
candidate, exact generation settings, seeds, strengths, OFF outputs, ON outputs,
output hashes, contact sheet, or queue completions for LR2.

```text
Seed A: NOT RUN
Seed B: NOT RUN
Technical causality: NOT RUN
Guide placement trend: NOT RUN
Seed variation: NOT RUN
```

## Stage 3 — Regression

**NOT RUN after the Stage 1 stop.** LR1's published contract, bridge, frontend,
browser, and visual evidence remain unchanged and are not reclassified by this
blocked LR2 inventory. No LR2 implementation change touched those files.

Canonical no-guide generation: **NOT RUN after the Stage 1 stop**. The
canonical workflow remained unchanged and no ControlNet dependency was added.

## Required boundaries

- Guide ownership remains Page-owned.
- Guide-local figure areas, Page-normalized placement, `instance_id`
  association, runtime-derived Page area, and no automatic matching remain
  unchanged.
- Scene / Visual Frame / CAST semantics remain unchanged.
- ControlNet was not connected to production generation.
- No Product UI `Guide Strength` or `ControlNet ON` setting was promoted.
- No Astra call or next Card was issued.

## Evidence and manifest

- Inventory: [M3B_LR2_CONTROL_MODEL_INVENTORY.md](../verification/m3b_lr2/M3B_LR2_CONTROL_MODEL_INVENTORY.md)
- Manifest: [M3B_LR2_MANIFEST.json](../verification/m3b_lr2/M3B_LR2_MANIFEST.json)

## Closeout classification

This is a valid bounded investigation result, not a failed implementation:

```text
CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED
```

The next decision belongs to Web GPT SOL / Owner review. This local run does not
choose a model, download one, or self-promote to PROMISING.
