# M3B-LR2R1 — AnyTest v4 Model Identity and Shared Storage Evidence

Date: 2026-09-10 JST  
Card: M3B-LR2R1  
Acquisition result: REUSED  
Publication: LOCAL

## Pinned identity

- Model: CN-anytest4_illustrious2_A.safetensors
- Source repository: 2vXpSwA7/iroiro-lora
- Pinned revision: bb4a39142275ac975ae4e6a64d1df218f672e0f0
- Repository path: test_controlnet2/CN-anytest4_illustrious2_A.safetensors
- Source commit: https://huggingface.co/2vXpSwA7/iroiro-lora/commit/bb4a39142275ac975ae4e6a64d1df218f672e0f0
- Source file metadata: https://huggingface.co/2vXpSwA7/iroiro-lora/blob/main/test_controlnet2/CN-anytest4_illustrious2_A.safetensors
- Expected bytes: 2502139104
- Actual bytes: 2502139104
- Expected SHA256: e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8
- Actual SHA256: E069D496CC111740716B833238D9BEA9CDD59F8623AA85A78D362D088B1F67B8
- Identity result: PASS

## Storage preflight

The configured external model roots are read from configs/extra_model_paths.yaml:

    E:/Data/Models/ControlNet
    E:/EasyReforge/Model/ControlNet

The live reForge path was inspected before reuse:

    E:\EasyReforge\stable-diffusion-webui-reForge\models\ControlNet
    Attributes: Directory, ReparsePoint, NotContentIndexed
    LinkType: Junction
    Target: E:\EasyReforge\Model\ControlNet

The target and configured roots were also inspected:

    E:\Data\Models\ControlNet
    Attributes: Directory
    LinkType/Target: not present

    E:\EasyReforge\Model\ControlNet
    Attributes: Directory
    LinkType/Target: not present

The optional reForge extension model path was not present:

    E:\EasyReforge\stable-diffusion-webui-reForge\extensions\sd-webui-controlnet\models
    Result: NOT_FOUND

The verified model files were:

    E:\EasyReforge\Model\ControlNet\CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors
    E:\Data\Models\ControlNet\CN-anytest4_illustrious2_A.safetensors

Both exact files were 2502139104 bytes and matched the expected SHA256. The
selected file is under the reForge junction target, so it is the same existing
shared storage used by reForge. The Data root copy was observed but was not
selected as the destination.

The reForge shared storage was established before acquisition. No download,
copy, rename, junction, or symlink was performed. The preceding fixed internal
destination was not used:

    ComfyUI\models\controlnet\CN-anytest4_illustrious2_A.safetensors
    Result: absent

The model was not tracked by Git. The B variant was not selected or modified.
The external drive had more than the required 6 GiB free space.

## ComfyUI loader evidence

- Live server: http://127.0.0.1:8188
- Standard node: ControlNetLoader
- Selector used: CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors
- Selector visibility: PASS
- Apply node: ControlNetApplyAdvanced
- Research prompt ID: dfa09463-4982-4489-be2f-8b17d41c77ee
- Queue result: success
- Node errors: none

The standard ControlNetLoader selector exposed both the Data-root entry and
the CN-anytest_v4 entry. The research graph intentionally selected the latter,
which resolves through E:\EasyReforge\Model\ControlNet.

## Pairing

- Checkpoint: ♃CN_Skeb\waiIllustriousSDXL_v170.safetensors
- Checkpoint external file observed: E:\Data\Models\StableDiffusion\♃CN_Skeb\waiIllustriousSDXL_v170.safetensors
- Checkpoint bytes observed: 6938040682
- VAE: CheckpointLoaderSimple output 2, the checkpoint VAE; no external VAE node
- Resolution: 832x1216
- Preprocessor: none
- Guide input: TegakiMangaRoughGuideBridge.rough_guide_image
- ControlNet start/end: 0.0 / 1.0

## Boundary

This evidence establishes local identity, shared-storage truth, loader
visibility, and runtime use for the bounded research graph. It does not
promote ControlNet into the canonical production workflow, does not establish
identity or pose fidelity, and does not constitute Owner product acceptance.
