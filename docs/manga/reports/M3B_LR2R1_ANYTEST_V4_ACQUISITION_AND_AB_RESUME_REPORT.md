# M3B-LR2R1 — AnyTest v4 Acquisition & A/B Resume Long-Run Report

Date: 2026-09-10 JST  
Card: M3B-LR2R1  
Executor: LUNA local chat  
Publication: LOCAL  
Final Owner product review: DEFERRED

## Outcome

The corrected storage rule was applied. The pinned AnyTest v4 model was already
present in the existing reForge shared ControlNet store, so it was reused
without download or duplication. ComfyUI loaded the external model through the
configured model roots, the eight-image A/B batch completed successfully, and
the canonical no-Guide path completed independently of ControlNet.

The bounded technical result is Generation influence: VERIFIED for this
research graph. Visual review is QUALITY WEAK / DEGRADED: the Guide geometry is
visible, especially at strength 0.75, but the placement benefit is weak or
unstable at lower strengths and the stronger outputs can carry intrusive
line/box artifacts. This is not a product-quality or Owner-acceptance result.

## Execution and publication truth

- Expected Manga baseline: 35b130b9e314128573bc5cbb7651048b0e43e260
- Final HEAD: 469623a6f7523c3423a5088f46e86a832fd06611
- origin/main: 469623a6f7523c3423a5088f46e86a832fd06611
- Baseline drift: H3-only; no Manga-file conflict
- Stage 0 publication-truth preparation: PASS
- No commit or push was made by this execution
- Current work remains local; Owner push is required before SOL public review
- LR2R1 publication: LOCAL

The LR2 historical report remains unchanged as a record of its earlier local
inventory stop. This report records the resumed LR2R1 execution separately.

## Model identity and corrected storage

- Model: CN-anytest4_illustrious2_A.safetensors
- Acquisition: REUSED
- Expected bytes: 2502139104
- Actual bytes: 2502139104
- Expected SHA256: e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8
- Actual SHA256: E069D496CC111740716B833238D9BEA9CDD59F8623AA85A78D362D088B1F67B8
- Source: 2vXpSwA7/iroiro-lora, revision bb4a39142275ac975ae4e6a64d1df218f672e0f0
- Source commit: https://huggingface.co/2vXpSwA7/iroiro-lora/commit/bb4a39142275ac975ae4e6a64d1df218f672e0f0
- Source file metadata: https://huggingface.co/2vXpSwA7/iroiro-lora/blob/main/test_controlnet2/CN-anytest4_illustrious2_A.safetensors
- Model identity: PASS

The preflight established that:

- E:\EasyReforge\stable-diffusion-webui-reForge\models\ControlNet is a
  junction targeting E:\EasyReforge\Model\ControlNet.
- E:\EasyReforge\Model\ControlNet is an existing directory and contains the
  exact file at CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors.
- E:\Data\Models\ControlNet is an existing directory and also contains an
  exact matching copy at its root. It was not selected as the destination.
- configs/extra_model_paths.yaml exposes both roots to ComfyUI.
- The optional reForge extension models directory was absent.
- The internal ComfyUI\models\controlnet destination was not used and the
  expected internal file was absent.
- No junction or symlink was created.
- The model is not tracked by Git.

This satisfies the destination priority:

existing reForge shared ControlNet store > E:\EasyReforge\Model\ControlNet >
E:\Data\Models\ControlNet

The physical shared file used by the run is:

E:\EasyReforge\Model\ControlNet\CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors

## Loader and checkpoint gate

ComfyUI was run locally at http://127.0.0.1:8188. The standard
ControlNetLoader selector exposed the exact external entry:

CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors

The research prompt used ControlNetLoader and ControlNetApplyAdvanced and
completed with no node errors:

- Research prompt: dfa09463-4982-4489-be2f-8b17d41c77ee
- Queue status: success
- ControlNet loader: PASS

Pairing and profile:

- Checkpoint: ♃CN_Skeb\waiIllustriousSDXL_v170.safetensors
- Observed checkpoint path:
  E:\Data\Models\StableDiffusion\♃CN_Skeb\waiIllustriousSDXL_v170.safetensors
- Observed checkpoint size: 6938040682 bytes
- VAE: CheckpointLoaderSimple output 2, the checkpoint VAE
- Resolution: 832x1216
- Steps: 20
- CFG: 7.0
- Sampler: euler
- Scheduler: normal
- Denoise: 1.0
- Guide preprocessor: none
- Guide source: ComfyUI/input/tegaki_manga_guides/rough_guide_live.png
- Guide placement: x 0, y 0.2434, w 1, h 0.5132
- ControlNet interval: start 0.0, end 1.0
- Seeds: 42 and 77
- Strengths: OFF, 0.25, 0.50, 0.75

## A/B invariants

The pair graph held checkpoint, checkpoint VAE, positive and negative
conditioning, resolution, seed, latent, steps, CFG, sampler, scheduler,
regional plan, and Guide image constant. Only the ControlNet application and
strength varied. The research workflow is:

workflows/manga/research/M3B_LR2R1_ANYTEST_AB.json

No production workflow was modified.

## Output ledger

All eight outputs are 832x1216 and have a successful ComfyUI queue result.

| Seed | Mode | Strength | Evidence file | Bytes | SHA256 |
|---:|---|---:|---|---:|---|
| 42 | OFF | OFF | SEED_A_OFF.png | 1544343 | 043536568A10D5F50321121B7338FF9555214795079632147934A8522FA598B1 |
| 42 | ON | 0.25 | SEED_A_025.png | 2042561 | 7F411248E83F8521465096515F4AE682BFBDFA9F26EFC195453C08408136839D |
| 42 | ON | 0.50 | SEED_A_050.png | 1874156 | 7D628C9CED20B7FBCB989BB9EB4F7C343E23B59F6FA6707312CD41A8826C10B6 |
| 42 | ON | 0.75 | SEED_A_075.png | 2153792 | 255D0300954057213CF7EB99402A49A632914FBCC0C754A647CCD1D07AD0B5D6 |
| 77 | OFF | OFF | SEED_B_OFF.png | 1688966 | 70144939D1433BB787A9BE67E5572FD6C2543CF54BA45AE541E77E471B46E18C |
| 77 | ON | 0.25 | SEED_B_025.png | 2258382 | 96F76E6BC55F9462DD33002BED80224C09003D5431BC63C87BEA29C5A1372018 |
| 77 | ON | 0.50 | SEED_B_050.png | 2413995 | F2D0E24335F429D885390E6E668D7425473F2A2F030C0A77C9247B71828610E5 |
| 77 | ON | 0.75 | SEED_B_075.png | 2428718 | 4F65431FC0F2713C9BCCE686518DC7826C6905C1FCF27523479FB74AEEBF2C40 |

Same-seed OFF versus ON hashes differ at all three strengths for both seeds,
which establishes technical causal influence in this run. The two seeds also
produce different hashes at every tested condition, so seed variation remains
PRESENT.

## Visual and browser review

The contact sheet is:

docs/manga/verification/m3b_lr2r1/M3B_LR2R1_AB_CONTACT_SHEET.png

Live ComfyUI browser review opened the Seed A OFF output and the canonical
no-Guide output through the local /view endpoint. The output viewer displayed
both at 832x1216. The contact sheet reviewed all eight A/B images.

Annotations:

- Guide placement trend: DEGRADED. Geometric influence becomes clear at
  strength 0.75, most visibly for Seed B, but lower strengths do not give a
  stable clean placement benefit and the stronger guide geometry can be
  intrusive.
- Image quality: DEGRADED. All outputs decode and are usable research images,
  but some stronger ON outputs show line/box or tint artifacts.
- Seed variation: PRESENT. A/B images differ visually and by SHA256 at every
  strength.
- Generation influence: VERIFIED for this bounded research graph.
- Identity, pose, composition lock, production readiness: NOT ESTABLISHED.

## Browser check ledger

| Check | Result | Evidence |
|---|---|---|
| E0 research workflow loads | PASS | Live ComfyUI accepted the research prompt; object_info exposed ControlNetLoader and ControlNetApplyAdvanced |
| E1 Seed A OFF | PASS | Seed A OFF output and history success |
| E2 Seed A ON 0.25 | PASS | Seed A 0.25 output and history success |
| E3 Seed A ON 0.50 | PASS | Seed A 0.50 output and history success |
| E4 Seed A ON 0.75 | PASS | Seed A 0.75 output and history success |
| E5 Seed B OFF | PASS | Seed B OFF output and history success |
| E6 Seed B ON sweep | PASS | Seed B 0.25, 0.50, and 0.75 outputs and history success |
| E7 canonical no-Guide | PASS | Prompt b35ccc27-29c1-4520-86e1-32f93348ab14 completed without ControlNet nodes |

## Regression

- LR1 contract: PASS, 12/12
- LR1 Guide operations: PASS
- LR1 runtime bridge: PASS, 5/5
- M2B Minimum-Hand editor: PASS, 19/19
- Canonical no-Guide queue: PASS
- Canonical no-Guide output: CANONICAL_NO_GUIDE.png, 832x1216

The canonical no-Guide run used the authoring document from
workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json and an API-equivalent graph with
no ControlNetLoader or ControlNetApplyAdvanced node. It completed normally,
showing that normal generation does not require the research model.

## Classification and boundaries

Provisional classification: QUALITY WEAK.

The technical influence gate passed, but visual placement is weak/unstable
outside the stronger setting and stronger outputs are degraded. Final
classification belongs to SOL after publication review. Owner product review
remains DEFERRED.

Production integration: NOT PERFORMED. No ControlNet setting was added to the
canonical workflow or Product UI. No other model, dependency, checkpoint, VAE,
LoRA, B variant, junction, or symlink was acquired.

Evidence:

- docs/manga/verification/m3b_lr2r1/M3B_LR2R1_MODEL_IDENTITY.md
- docs/manga/verification/m3b_lr2r1/M3B_LR2R1_MANIFEST.json
- docs/manga/verification/m3b_lr2r1/SEED_A_OFF.png
- docs/manga/verification/m3b_lr2r1/SEED_A_025.png
- docs/manga/verification/m3b_lr2r1/SEED_A_050.png
- docs/manga/verification/m3b_lr2r1/SEED_A_075.png
- docs/manga/verification/m3b_lr2r1/SEED_B_OFF.png
- docs/manga/verification/m3b_lr2r1/SEED_B_025.png
- docs/manga/verification/m3b_lr2r1/SEED_B_050.png
- docs/manga/verification/m3b_lr2r1/SEED_B_075.png
- docs/manga/verification/m3b_lr2r1/M3B_LR2R1_AB_CONTACT_SHEET.png
- workflows/manga/research/M3B_LR2R1_ANYTEST_AB.json

Stopped early: NO  
Stop reason: none  
LR2R1 publication: LOCAL  
Owner push required: YES
