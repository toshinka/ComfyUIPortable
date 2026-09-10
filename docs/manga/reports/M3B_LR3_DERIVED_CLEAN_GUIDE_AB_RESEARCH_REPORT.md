# M3B-LR3 — Derived Clean Guide A/B Research Report

Date: 2026-09-10 JST  
Card: M3B-LR3  
Executor: LUNA local chat  
Publication: LOCAL  
Owner push required: YES  
Final Owner product review: DEFERRED

## Outcome

Option A provisional result: **OPTION_A_INCONCLUSIVE**.

The clean Figure-derived guide removed the intrusive RAW Guide line/box
geometry in both seeds. It improved the intended two-Figure left/right
placement for Seed 42, but Seed 77 produced only one visible person. The Card
requires improvement in both seeds, so the result is not `SUPPORTED`. Because
only one seed improves, the Card's classification rule is
`OPTION_A_INCONCLUSIVE`.

This is a bounded research result. It does not reject derived Guides in
general, ControlNet in general, or settings outside the tested
flat-silhouette / strength `0.75` / full-interval / whole-page conditions.

## Execution baseline

- Final `HEAD`: `09a65e7dfe05b8609ad005e3e9d0acd7f4212404`
- `origin/main`: `09a65e7dfe05b8609ad005e3e9d0acd7f4212404`
- Card-observed repository main: `bbb9f6720c9a4ed8fb7a029814bd10a5442542fd`
- Latest SOL-reviewed Manga public commit: `cd5dcbf4baca2f6e7ca91dc587dcba013216556b`
- Drift between the Card observation and the live baseline is H3/model-path
  work only; no Manga conflict was found.

Stage 0 publication truth was updated to record M3B-LR2R1 as
`PUBLISHED / SOL REVIEWED`, final SOL classification `QUALITY WEAK`, Guide
placement `DEGRADED`, image quality `DEGRADED`, and production ControlNet
integration `NOT PERFORMED`. M3B-LR3 was then recorded as the active Card.
The historical LR2R1 execution report remains unchanged with its
execution-time `Publication: LOCAL` wording.

## Hypothesis and boundaries

The single hypothesis was that LR2R1's weak visual quality was caused by
sending RAW Rough Guide pixels directly into ControlNet, and that a clean
generation-specific silhouette derived only from Figure geometry could retain
useful placement influence without reproducing raw Guide marks.

The following boundaries were preserved:

- Persistent schema: **UNCHANGED**. No new field, version, or `page.guides[]`
  entry was added.
- The uploaded Rough Guide remains an editing/reference asset.
- The CLEAN image is a research generation-control image only and is not
  persisted in the authoring document.
- The LR2R1 document remains `input_mode: simple`. This tests geometry-derived
  global ControlNet assistance, not Character Instance-specific CAST
  conditioning.
- Figure masks and `instance_id` associations establish provenance only. They
  do not spatially restrict ControlNet; the image is applied to the whole
  page.
- No production workflow, product UI, `TegakiMangaRoughGuideBridge` public
  I/O, H3 path, shared model storage, junction, or output namespace was
  changed.
- Astra was not called again.

## CLEAN Guide derivation

The research helper is:

`scripts/m3b_lr3_build_clean_guide.py`

It reads the existing LR2R1 research workflow rather than adding a parallel
source of geometry. It derives each Figure page area using:

`guide.placement + figure local area`

and fails closed with `CLEAN_GUIDE_GEOMETRY_PROVENANCE_MISMATCH` if an audited
coordinate differs by more than `0.0001`.

The existing renderer was reused:

`custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator.draw_single_character_mannequin()`

with:

- `guide_style = flat_silhouette`
- `shot_type = full_body`
- `include_bbox_outline = false`
- black fill on a white `832x1216` RGB canvas
- exactly two rendered silhouettes

The resulting CLEAN guide contains only black and white pixels. It contains no
boxes, labels, panel outlines, raw Guide pixels, background strokes, tint, or
visual frame borders.

Evidence:

- [CLEAN guide](../verification/m3b_lr3/M3B_LR3_CLEAN_GUIDE.png)
- [CLEAN provenance](../verification/m3b_lr3/M3B_LR3_CLEAN_GUIDE_PROVENANCE.json)
- [RAW reference copy](../verification/m3b_lr3/M3B_LR3_RAW_GUIDE_REFERENCE.png)

### Geometry provenance

| Figure | Instance | Local area | Derived page area | Pixel bounds |
|---|---|---|---|---|
| `figure_1` | `inst_1` | `(0.05, 0.12, 0.38, 0.72)` | `(0.05, 0.304984, 0.38, 0.369504)` | `(42, 371)-(358, 820)` |
| `figure_2` | `inst_2` | `(0.57, 0.22, 0.28, 0.58)` | `(0.57, 0.356304, 0.28, 0.297656)` | `(474, 433)-(707, 795)` |

Geometry provenance: **PASS**.

CLEAN guide SHA256:

`96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a`

## Model and storage truth

Only the previously verified selector was reused:

`CN-anytest_v4\\CN-anytest4_illustrious2_A.safetensors`

The physical file was confirmed at:

`E:\EasyReforge\Model\ControlNet\CN-anytest_v4\CN-anytest4_illustrious2_A.safetensors`

- Bytes: `2502139104`
- SHA256: `E069D496CC111740716B833238D9BEA9CDD59F8623AA85A78D362D088B1F67B8`
- reForge path: `E:\EasyReforge\stable-diffusion-webui-reForge\models\ControlNet`
- reForge link: Junction targeting `E:\EasyReforge\Model\ControlNet`
- ComfyUI ControlNetLoader selector: present
- Portable internal copy: absent
- Git-tracked internal copy: false
- LR3 download/copy: not performed

## Exact experimental settings

Research workflow:

`workflows/manga/research/M3B_LR3_CLEAN_GUIDE_AB.json`

The six conditions were exactly:

| Condition | ControlNet image | Strength | Interval | Preprocessor |
|---|---|---:|---:|---|
| OFF | bypassed | — | — | — |
| RAW | existing LR2R1 Rough Guide bridge image | 0.75 | 0.0–1.0 | none |
| CLEAN | Figure-derived flat silhouette | 0.75 | 0.0–1.0 | none |

All six retained the same checkpoint, checkpoint VAE, positive/negative
conditioning, latent, `832x1216` resolution, 20 steps, CFG 7, euler/normal,
denoise 1.0, document, simple-mode conditioning, Guide placement, Figure
records, and the respective seed.

The live ComfyUI queue accepted prompt
`0ef41b96-628d-4dab-882c-2eb002199edc` with `status_str: success` and no node
errors. Total elapsed time reported by the execution timestamps was 143.464
seconds.

## Six-output ledger

All six outputs are RGB `832x1216` PNGs and each queue status is PASS.

| Seed | Condition | Source output | Evidence | SHA256 |
|---:|---|---|---|---|
| 42 | OFF | `M3B_LR3_SEED_A_OFF_00001_.png` | `SEED_A_OFF.png` | `b155435e08fce06968c580dc0704e93870b71de2e68efbc8e34d36536afed48c` |
| 42 | RAW | `M3B_LR3_SEED_A_RAW_00001_.png` | `SEED_A_RAW.png` | `9275aa7fdfec88e4feeb29cf18d411d92136ac6ba908b57b8564b0c0591485aa` |
| 42 | CLEAN | `M3B_LR3_SEED_A_CLEAN_00001_.png` | `SEED_A_CLEAN.png` | `d9e9c066b18fab6632c8c99bef2dd7ea4f2bac7cab064b6855ec0a89ed267d73` |
| 77 | OFF | `M3B_LR3_SEED_B_OFF_00001_.png` | `SEED_B_OFF.png` | `55801e8335ca17fa57ddffd738388b5f17e288fbfa414cd91d1cb763c441484f` |
| 77 | RAW | `M3B_LR3_SEED_B_RAW_00001_.png` | `SEED_B_RAW.png` | `81eeb9ad29276f40dc71a975e1e9965dd691fb5a86953e2ce55c0fe2e1414a27` |
| 77 | CLEAN | `M3B_LR3_SEED_B_CLEAN_00001_.png` | `SEED_B_CLEAN.png` | `625dbc9f5125bca3d328864b2303017255818090c4eb510b0edb5ee41ae34c44` |

Technical gate: **6/6 PASS**. Same-seed OFF/RAW/CLEAN hashes differ, proving
generation influence only; the hash differences do not prove better placement.
Seed A/B hashes and images also differ for all three conditions, so seed
variation is **PRESENT**.

## Visual comparison

The full ledger is in [M3B_LR3_VISUAL_LEDGER.md](../verification/m3b_lr3/M3B_LR3_VISUAL_LEDGER.md).
The visual contact sheet is
[M3B_LR3_CONTACT_SHEET.png](../verification/m3b_lr3/M3B_LR3_CONTACT_SHEET.png).

Aggregate enums:

- RAW placement: **DEGRADED**
- RAW image quality: **DEGRADED**
- CLEAN placement: **WEAK** (Seed 42 CLEAR, Seed 77 NONE)
- CLEAN image quality: **USABLE**
- Seed variation: **PRESENT**

Seed 42 CLEAN produces a clear left/right two-Figure classroom image and
removes the RAW line/box structure. Seed 77 CLEAN is clean but loses the
second Figure. RAW retains intrusive guide geometry in both seeds; Seed 77
also contains three visible people, making the intended association unstable.
The clean images do not preserve the requested standing-left/seated-right
variation reliably: Seed 42 renders both standing and Seed 77 renders one
standing figure.

## Regression

- LR1 contract: **12/12 PASS**
- LR1 runtime bridge: **5/5 PASS**
- LR1 Guide operations: **PASS**
- M2B Minimum-Hand frontend: **19/19 PASS**
- Combined LR1 regression: **PASS**

## Canonical no-Guide result

The canonical workflow source was:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

An API-equivalent queue was made from that workflow's authoring document and
generation nodes, with no Guide bridge, ControlNetLoader, or
ControlNetApplyAdvanced node. It completed successfully:

- Prompt: `85923820-607e-4511-bc96-0ed70af857a8`
- Queue: **PASS**
- ControlNet dependency: **NO**
- Guide dependency: **NO**
- Output: `CANONICAL_NO_GUIDE.png`, `832x1216`
- SHA256: `0b82bd8bb6eb778a0cdaf1be68662865588df5588f0c6f7876c60ce51e607d28`

## Classification and closeout

Option A provisional result: **OPTION_A_INCONCLUSIVE**.

The clean guide is a useful artifact-cleaning representation for this test,
but this two-seed slice does not establish reliable placement improvement over
both OFF and RAW. No production ControlNet integration was performed, no
product UI control was added, and no next Card is issued automatically.

Production integration: **NOT PERFORMED**.  
Final Owner product review: **DEFERRED**.  
Stopped early: **NO**.  
M3B-LR3 publication: **LOCAL**.  
Owner push required: **YES**.

Manifest: [M3B_LR3_MANIFEST.json](../verification/m3b_lr3/M3B_LR3_MANIFEST.json)
