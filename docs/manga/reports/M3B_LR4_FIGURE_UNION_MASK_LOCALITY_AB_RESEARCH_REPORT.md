# M3B-LR4 — Figure-Union Mask Locality A/B Research Report

Date: 2026-09-10 JST  
Card: `M3B-LR4`  
Executor: LUNA local chat  
Publication: LOCAL  
Owner push required: YES  
Final Owner product review: DEFERRED

## Outcome

Locality result: **LOCALITY_SUPPORTED**.

The same LR3 CLEAN ControlNet, restricted by the existing Figure-union mask,
improved Seed 77 from one visible person under CLEAN_GLOBAL to two visible
Figures under CLEAN_MASKED. Seed 42 retained two-Figure presence and usable
quality. No obvious mask-boundary artifact was observed, and seed variation
remained PRESENT. This is a bounded two-seed research result; it does not
authorize production integration or an Advanced-ControlNet dependency.

## Execution baseline and Stage 0

- Final `HEAD`: `2b167493ee83df2a4f80c10669d9c4e4387e111e`
- `origin/main`: `2b167493ee83df2a4f80c10669d9c4e4387e111e`
- Latest SOL-reviewed Manga public commit from the Card: `d5df3f25866ed05fd147a8b6da2509a6878f7f24`
- Drift from the Card baseline to live `origin/main`: H3/model-path files only; no Manga own-file conflict.
- Stage 0 publication truth: **PASS**. M3B-LR3 is `PUBLISHED / SOL REVIEWED`; its final result is `OPTION_A_INCONCLUSIVE`. Derived CLEAN Guide quality improvement is verified, but placement consistency was not verified. Production ControlNet integration remains NOT PERFORMED.

The historical LR3 report retains its execution-time `Publication: LOCAL`
wording. This report does not rewrite historical publication evidence.

## Scope and invariants

Exactly six outputs were generated: seeds `42` and `77`, each with `OFF`,
`CLEAN_GLOBAL`, and `CLEAN_MASKED`. No RAW condition was included. The LR3
CLEAN Guide was reused byte-for-byte:

`M3B_LR3_CLEAN_GUIDE.png` — SHA256
`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`.

All conditions retained the LR3 checkpoint, VAE, positive/negative
conditioning, latent, `832x1216` resolution, 20 steps, CFG 7, euler/normal,
denoise 1.0, simple-mode document, Figure geometry, and the verified model.
ControlNet strength was `0.75` over interval `0.0–1.0`, with no preprocessor.
The only GLOBAL/MASKED graph difference is the MASKED connection described
below.

## Local Advanced-ControlNet mask contract

The live ComfyUI `/object_info` contract exposed:

`ACN_AdvancedControlNetApply_v2`

Required inputs were `positive`, `negative`, `control_net`, `image`,
`strength`, `start_percent`, and `end_percent`. The optional mask input was:

`mask_optional` (display name `effect_mask`, type `MASK`).

The installed local source at
`ComfyUI/custom_nodes/ComfyUI-Advanced-ControlNet/adv_control/nodes_main.py`
defines the same port and passes it to `set_cond_hint_mask`. The installed
README states that `mask_optional` decides the spatial part of the image where
the ControlNet applies, and that non-binary values scale relative strength.
The local test contract also establishes that an all-zero effect mask returns
the original conditioning and that effect and inpaint masks remain separate.

Mask semantics therefore are:

- `1.0`: active ControlNet effect region;
- `0.0`: inactive region;
- intermediate values: proportional effect strength (not used here).

The node was used only in the research workflow. Advanced-ControlNet was not
added as a production dependency and its source was not modified.

## Figure-union provenance

The mask was obtained by directly calling the existing
`TegakiMangaRoughGuideBridge.figure_union_mask` implementation. It derives
page rectangles from `guide.placement + figure_regions[].area`; no new
persistent mask, schema field, manual drawing, padding, feather, blur, erosion,
dilation, or other tuning was applied.

The exact page bounds were:

| Figure | Instance | x | y | w | h |
|---|---|---:|---:|---:|---:|
| `figure_1` | `inst_1` | 0.05 | 0.304984 | 0.38 | 0.369504 |
| `figure_2` | `inst_2` | 0.57 | 0.356304 | 0.28 | 0.297656 |

Evidence mask: [M3B_LR4_FIGURE_UNION_MASK.png](../verification/m3b_lr4/M3B_LR4_FIGURE_UNION_MASK.png)  
Mask SHA256: `6246dc79157bdfc75fe4eb6bb1fe14703a9e474e700269bdfdcb45688d2da6fb`  
Dimensions: `832x1216`, grayscale, exactly 226,230 active white pixels and
785,482 inactive black pixels.

The live `MaskToImage` output is RGB-encoded and has a different file hash due
to PNG mode/metadata, but its RGB pixels are exactly equal to the direct bridge
evidence mask. The mask provenance JSON records both the source and semantics.

## Exact GLOBAL versus MASKED graph difference

`workflows/manga/research/M3B_LR4_FIGURE_MASK_AB.json` preserves the LR3
research structure. `CLEAN_GLOBAL` uses `ACN_AdvancedControlNetApply_v2` with
the CLEAN Guide image and no mask. `CLEAN_MASKED` uses the same node inputs,
model, image, strength, and interval, with only:

```text
mask_optional = TegakiMangaRoughGuideBridge.figure_union_mask
```

The OFF branches bypass ControlNet. There is no RAW branch, no CAST mode, no
per-Figure ControlNet stack, and no timing or strength sweep.

## Six-output technical ledger

The live prompt `16523812-a927-404e-85a8-b43cc4f6a52b` completed with
`status_str: success`, `execution_success`, no node errors, and elapsed time
approximately `115.003` seconds. All six output nodes returned PASS. The
complete SHA/dimension ledger is in
[M3B_LR4_VISUAL_LEDGER.md](../verification/m3b_lr4/M3B_LR4_VISUAL_LEDGER.md).

| Seed | OFF | CLEAN_GLOBAL | CLEAN_MASKED |
|---:|---|---|---|
| 42 | PASS | PASS | PASS |
| 77 | PASS | PASS | PASS |

Technical gate: **6/6 PASS**.

## Manual visual comparison

The local contact sheet is
[M3B_LR4_CONTACT_SHEET.png](../verification/m3b_lr4/M3B_LR4_CONTACT_SHEET.png).
The outputs were also opened through live ComfyUI `/view` pages. No automatic
detector was used.

| Aggregate | Placement | Quality | Figure count |
|---|---|---|---|
| CLEAN_GLOBAL | WEAK | USABLE | FAIL |
| CLEAN_MASKED | WEAK | USABLE | PASS |

Seed 42 GLOBAL shows a clear left/right pair. Seed 42 MASKED also shows a
clear two-Figure pair at usable quality, with no material regression. Seed 77
GLOBAL shows only one visible person. Seed 77 MASKED shows two Figures again;
their placement is weaker/more central than Seed 42 but is a clear presence
improvement over GLOBAL. Seed variation is **PRESENT**.

Mask-boundary review: **NONE**. Neither MASKED image shows a hard rectangular
edge, visible mask contour, local tint discontinuity, anatomy break, or
background discontinuity.

## Locality classification

`LOCALITY_SUPPORTED`

All Card criteria are met:

1. Seed 77 MASKED improves Figure presence over GLOBAL.
2. Seed 42 MASKED has no material regression from GLOBAL.
3. Both MASKED seeds retain two-Figure presence.
4. MASKED quality remains USABLE.
5. No obvious mask-boundary artifact is present.
6. Seed variation remains PRESENT.

This result means the tested Figure-union spatial restriction is supported for
this fixed two-seed slice. It does not establish character-specific ControlNet,
backend parity, production safety, or a general guarantee across seeds.

## Regression

- LR1 contract: **12/12 PASS** — `scripts/test_m3b_lr1_contract.py`
- LR1 runtime bridge: **5/5 PASS** — `scripts/test_m3b_lr1_runtime_bridge.py`
- LR1 Guide operations: **PASS** — `scripts/test_m3b_lr1_guide_ops.mjs`
- M2B Minimum-Hand frontend: **19/19 PASS** — `scripts/test_m2b_minimum_hand_editor.mjs`
- Combined LR1 regression: **PASS**

## Canonical no-Guide regression

The source was the canonical
`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`. An API-equivalent prompt was
queued from its authoring document and generation nodes while omitting the
Guide bridge, ControlNetLoader, Advanced-ControlNet apply node, and frame
overlay. The corrected retry prompt
`8d8d149e-c740-4c74-9c00-b6949b5765bf` completed with `success`.

- ControlNet dependency: **NO**
- Advanced-ControlNet dependency: **NO**
- Guide dependency: **NO**
- Queue: **PASS**
- Output: [CANONICAL_NO_GUIDE.png](../verification/m3b_lr4/CANONICAL_NO_GUIDE.png), `832x1216`
- SHA256: `e368484acefcfe2b3fdfc36f5a45d22a2176ddff00597b0e1028a7f2a2c82ff1`

The first local prompt-construction attempt was discarded before generation
because PowerShell serialized the already-stringified document a second time;
the retry passed after preserving the canonical JSON string. This did not alter
the canonical workflow.

## Production and closeout truth

- Production workflow/UI/bridge public I/O/schema: **UNCHANGED**.
- Model storage/download/copy/junction: **UNCHANGED**.
- Production ControlNet integration: **NOT PERFORMED**.
- Final Owner product review: **DEFERRED**.
- Stopped early: **NO**.
- M3B-LR4 local publication: **LOCAL**.
- Owner push required: **YES**.

Manifest: [M3B_LR4_MANIFEST.json](../verification/m3b_lr4/M3B_LR4_MANIFEST.json)
