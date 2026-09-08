# H3 Reference Inventory

更新: 2026-09-08 JST
目的: 採用前の候補棚卸し。clone、install、source copy、workflow導入はしていない。

`Pinned commit` は公開commit履歴で短SHAまで確認できた場合だけ記録しています。
短SHAは将来の採用pinではなく、この調査時点の追跡用スナップショットです。

## Status vocabulary

- `INSPECT`: 設計・実装・ライセンスを引き続き確認する。
- `ADOPT-CANDIDATE`: 将来の選択肢になり得るが、採用決定ではない。
- `DEFER`: 現在のGroundwork / H1より後で扱う。
- `RESEARCH-LATER`: canonical source、再現条件、またはライセンス境界が未確定。

## Tier A — 今すぐ設計材料

### AntaresAlice/h3-webui

- Name: `AntaresAlice/h3-webui`
- Repository: https://github.com/AntaresAlice/h3-webui
- GitHub URL: https://github.com/AntaresAlice/h3-webui
- License: MIT (repository README / LICENSE)
- Current role: H3 Video minimal WebUI skin
- Why relevant: workspace、history、reference reuse、continuation、progress、
  ComfyUI boundaryの観察対象。
- Expected use: H1 skinのinteraction benchmark。source copyやforkではない。
- Status: `ADOPT-CANDIDATE` (design material only)
- Pinned commit: `1f566ba` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: model weightsは含まれない。H3 model licenseとruntimeは別監査。

### onigirikiller/minimax-h3-webui

- Name: `onigirikiller/minimax-h3-webui`
- Repository: https://github.com/onigirikiller/minimax-h3-webui
- GitHub URL: https://github.com/onigirikiller/minimax-h3-webui
- License: Apache-2.0
- Current role: queue / last-frame chaining中心のVideo WebUI
- Why relevant: 12GB VRAMのT2V/I2V記録、ComfyUI HTTP boundary、bulk queue、join。
- Expected use: H1 minimum flowと12GB baselineの比較材料。
- Status: `ADOPT-CANDIDATE` (design material only)
- Pinned commit: `f9b28d5` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: READMEはRef2VAをより重い経路として説明。GPU実証はTegakiの未実施事項。

### ComfyUI-MiniMaxH3-Easy

- Name: `ComfyUI-MiniMaxH3-Easy`
- Repository: https://github.com/vanessaliu036-lab/comfyui-minimaxh3-easy
- GitHub URL: https://github.com/vanessaliu036-lab/comfyui-minimaxh3-easy
- License: MIT
- Current role: unified ComfyUI node / workflow surface
- Why relevant: one Media input、ordered media、`@` reference editor、I2V / first-last
  frame / R2V、advanced settingの段階表示。
- Expected use: H1/H2 interaction and adapter boundary review。
- Status: `ADOPT-CANDIDATE` (design material only)
- Pinned commit: not recorded; public history did not expose a stable SHA in this pass
- Last checked: 2026-09-08 JST
- Notes: 指示書の呼称と公開repositoryのowner/nameに差がある。導入前にidentityを再確認。

## Tier B — Studio / GUI設計時に強く参照

### shootthesound/ComfyUI-H3Studio

- Name: `ComfyUI-H3Studio`
- Repository: https://github.com/shootthesound/ComfyUI-H3Studio
- GitHub URL: https://github.com/shootthesound/ComfyUI-H3Studio
- License: MIT
- Current role: H3 Video Studio / timeline reference
- Why relevant: timeline、keyframes、reference、continuation、reel、trim、crossfade、
  audio lanes、export、preview。
- Expected use: H3/H4 Studio design material after the minimum skin.
- Status: `INSPECT`
- Pinned commit: `85c557a` (master history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: 初期H1へ機能を丸ごと持ち込まない。

### seesee75-commits/ComfyUI-MiniMaxH3-Director

- Name: `ComfyUI-MiniMaxH3-Director`
- Repository: https://github.com/seesee75-commits/ComfyUI-MiniMaxH3-Director
- GitHub URL: https://github.com/seesee75-commits/ComfyUI-MiniMaxH3-Director
- License: GPL-3.0; LTX Director由来のfrontendについて派生境界を確認する
- Current role: timeline → storyboard prompt / H3 Director / retake / chain
- Why relevant: H3 native prompt compilation、first/last keyframe、reference/audio/video
  semantics、segment retry。
- Expected use: Recipe Resolver / timeline semantics review。
- Status: `INSPECT`
- Pinned commit: `8486323` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: source code reuseはLICENSE、upstream attribution、derivative workを別途監査。

### AIMixer/ComfyUI_MiniMaxH3_Director

- Name: `ComfyUI_MiniMaxH3_Director`
- Repository: https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director
- GitHub URL: https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director
- License: Apache-2.0
- Current role: multi-segment Director / T2V-I2V-FL2V-R2V-V2V-RV2V
- Why relevant: multi-segment、selective run、reference group、long-video segmentation、
  native AV route。
- Expected use: Studio phase comparison; not H0 implementation。
- Status: `INSPECT`
- Pinned commit: `7de4a95` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: active developmentが速いため、採用時はfull SHAとworkflowを同時にpinする。

### thaakeno/ComfyUI-MiniMax-H3-Studio

- Name: `ComfyUI-MiniMax-H3-Studio`
- Repository: https://github.com/thaakeno/ComfyUI-MiniMax-H3-Studio
- GitHub URL: https://github.com/thaakeno/ComfyUI-MiniMax-H3-Studio
- License: MIT (adapted files / external componentsは個別条件)
- Current role: H3 Still Director / reference-aware Studio
- Why relevant: role / retention / description付きreference card、route validation、
  metadata、VAE tiling、LightX / PDD profile、benchmark。
- Expected use: H1S/H2 Still UX and conditioning review。
- Status: `INSPECT`
- Pinned commit: `8e106b3` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: alpha。READMEはclassic Nodes 1.0中心でNodes 2.0未対応と明記。

## Tier C — 長期研究

### karuvanan/MiniMax-H3-Director-Cut-Studio

- Name: `MiniMax-H3-Director-Cut-Studio`
- Repository: https://github.com/karuvanan/MiniMax-H3-Director-Cut-Studio
- GitHub URL: https://github.com/karuvanan/MiniMax-H3-Director-Cut-Studio
- License: MIT
- Current role: Premiere-inspired PySide6 Studio / multi-track Director
- Why relevant: media pool、semantic enrichment、shot-aware long render、timeline prompt
  reconciliation、ComfyUI submission。
- Expected use: H3 Studio / long-form UX research only。
- Status: `DEFER`
- Pinned commit: `a4ef316` (main history, checked 2026-09-08)
- Last checked: 2026-09-08 JST
- Notes: runtime、TTS、BLIP、FFmpegなど面積が大きい。H0/H1へ導入しない。

### Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc

- Name: `ComfyUI-MiniMax-H3-PDD-Acc`
- Repository: https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc
- GitHub URL: https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc
- License: repository LICENSEを採用前に確認（このpassではpinしない）
- Current role: PDD acceleration LoRA + head-bank loader
- Why relevant: PDDは通常のLoRA loaderと同一視できず、専用loader / head bank / steps
  の関係を確認する必要がある。
- Expected use: Experimental profile research。
- Status: `RESEARCH-LATER`
- Pinned commit: not recorded
- Last checked: 2026-09-08 JST
- Notes: default化・Base Quality混入は禁止。

### LightX / Turbo model family

- Name: `lightx2v/Minimax-h3-Turbo` and related H3 Turbo recipes
- Repository: https://huggingface.co/lightx2v/Minimax-h3-Turbo
- GitHub URL: not a GitHub repository; source/model page is recorded instead
- License: model/repository terms must be checked at adoption time; public research notes
  identify Apache-2.0 for the cited LightX2V adapter, but this is not a blanket license
  for every H3 model or recipe
- Current role: few-step acceleration profile
- Why relevant: 4/8-step experiments and route-specific shift/steps requirements。
- Expected use: Experimental only until Cooling Gate passes。
- Status: `DEFER`
- Pinned commit: not recorded in this repository
- Last checked: 2026-09-08 JST
- Notes: artifact、resolution、shift、steps、LoRA scaleを一組でpinする。

### FastH3 / VSA

- Name: FastH3 / VSA candidate family
- Repository: canonical source not pinned in this pass
- GitHub URL: not confirmed
- License: not confirmed
- Current role: proposed new runtime / acceleration family
- Why relevant: Rev.3 explicitly names it as a new-runtime class requiring longer observation。
- Expected use: 14-day observation candidate; never automatic default。
- Status: `RESEARCH-LATER`
- Pinned commit: none
- Last checked: 2026-09-08 JST
- Notes: source identity、hardware matrix、artifact、license/provenanceを先に確定する。

### GGUF / Unsloth Desktop

- Name: GGUF and Unsloth Desktop H3 path
- Repository: runtime / distribution family, not one pinned H3 repository
- GitHub URL: https://github.com/unslothai/unsloth
- License: runtime and model licenses are separate and must be checked per asset
- Current role: alternative model/runtime path
- Why relevant: memory and distribution alternatives for later low-VRAM research。
- Expected use: research only; not H1 baseline。
- Status: `RESEARCH-LATER`
- Pinned commit: none
- Last checked: 2026-09-08 JST
- Notes: do not interpret a GGUF download path as a production-quality result。

## Runtime / provenance references

### Comfy-Org/ComfyUI

- Name: `Comfy-Org/ComfyUI`
- Repository: https://github.com/Comfy-Org/ComfyUI
- GitHub URL: https://github.com/Comfy-Org/ComfyUI
- License: GPL-3.0 (upstream project terms)
- Current role: host runtime and native H3 node surface
- Why relevant: official node signatures, loader paths, model folder conventions, runtime
  compatibility。
- Expected use: inspect current native H3 support; no fork in this groundwork。
- Status: `INSPECT`
- Pinned commit: not recorded
- Last checked: 2026-09-08 JST
- Notes: ComfyUI license does not relicense MiniMax H3 weights or third-party nodes.

### MiniMax-AI/MiniMax-H3

- Name: `MiniMax-AI/MiniMax-H3`
- Repository: https://github.com/MiniMax-AI/MiniMax-H3
- GitHub URL: https://github.com/MiniMax-AI/MiniMax-H3
- License: model terms / MiniMax H3 Community License Agreement; review the current
  agreement directly before distribution or hosted use
- Current role: upstream model / official prompt and license provenance
- Why relevant: model-family boundary, supported routes, official terms。
- Expected use: provenance and compatibility reference, not source code vendoring。
- Status: `INSPECT`
- Pinned commit: not recorded
- Last checked: 2026-09-08 JST
- Notes: model license, applicable territory, output use, and third-party Qwen terms remain
  separate from any UI repository license.

## Cross-cutting research entries

### pruned INT8 / Qwen NVFP4-AWQ / host offload / DynamicVRAM

- Name: low-VRAM recipe family
- Repository: no single canonical repository for the full combination
- GitHub URL: see the runtime and candidate links above
- License: model, runtime, and adapter terms vary
- Current role: 12GB/16GB memory profile candidates
- Why relevant: Rev.3 baseline is RTX 4070 12GB VRAM + 64GB system RAM。
- Expected use: controlled hardware matrix after Web GPT review。
- Status: `INSPECT`
- Pinned commit: none
- Last checked: 2026-09-08 JST
- Notes: record resolution, frame count, steps, model variant, offload, peak VRAM, RAM,
  load time, and output quality together。

### REF2VA still / ordered multi-reference / reference-edit

- Name: H3 Still conditioning pattern
- Repository: pattern spanning native H3, Image Studio, and H3 Studio
- GitHub URL: see the Still entries above
- License: follows each implementation/model; no shared license assumed
- Current role: semantic reference contract research
- Why relevant: identity、pose、clothing、composition、source anchor、source fidelityを
  混ぜずに扱うため。
- Expected use: H1S capability spike after H1 Video review。
- Status: `INSPECT`
- Pinned commit: none
- Last checked: 2026-09-08 JST
- Notes: no Still workflow is copied into `workflows/h3/` in this slice。

## Inventory decision

No candidate is installed, cloned, copied, or declared adopted by this inventory.
The next decision is Web GPT review, followed by a separately scoped H0/H1 card if
the review approves a source and a pinned license/provenance boundary.
