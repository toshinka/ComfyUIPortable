# M3B-LR2R1 — AnyTest v4 Acquisition & A/B Resume Long-Run

Date: 2026-09-10 JST  
Issuer: Web GPT SOL  
Executor: LUNA local chat  
Mode: LONG-RUN BATCH  
Milestone authority: Web GPT SOL  
Final product review: Owner / DEFERRED

## Storage correction

The fixed destination from the preceding Card is superseded. Do not save this
model under `ComfyUI/models/controlnet/`.

Use the existing external model-path configuration in
`configs/extra_model_paths.yaml`. Before download or reuse, inspect the
reForge ControlNet directory and its junction/symlink target.

Preferred destination:

```text
existing reForge shared ControlNet store
> E:\EasyReforge\Model\ControlNet
> E:\Data\Models\ControlNet
```

The destination must be an existing storage root verified as used by reForge.
Do not create a new junction or symlink. If the shared destination cannot be
established:

```text
STOPPED:
CONTROLNET_SHARED_STORAGE_NOT_ESTABLISHED
```

---

# 0. Purpose

M3B-LR2 stopped at Stage 1 with:

```text
CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED
```

This Card permits exactly one pinned ControlNet model to be reused or acquired,
then continues through byte/hash verification, ComfyUI loading, same-seed OFF/ON
A/B generation, bounded strength sweep, regression, and evidence. Production
integration remains forbidden.

---

# 1. Verified repository state

Latest SOL-reviewed Manga publication:

`35b130b9e314128573bc5cbb7651048b0e43e260`

LR2 execution HEAD:

`e65e484a59d2b50610a3b6a20ee79d40a95f7079`

LR2:

```text
Stage 0: PASS
Stage 1: BLOCKED / valid stop
Stage 2: NOT RUN
Generation influence: BLOCKED
Production integration: NOT PERFORMED
```

M3B-LR1 foundation remains PASS.

---

# 2. Start and baseline drift

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

Expected Manga baseline:

`35b130b9e314128573bc5cbb7651048b0e43e260`

If `origin/main` advanced, inspect:

```bash
git diff --name-status \
  35b130b9e314128573bc5cbb7651048b0e43e260..origin/main
```

Continue when the drift is H3-only or otherwise has no Manga-file conflict.

---

# 3. Stage 0 — publication truth

Update current authority before implementation:

```text
Latest SOL-verified public commit:
35b130b9e314128573bc5cbb7651048b0e43e260

M3B-LR2:
PUBLISHED / SOL REVIEWED / BLOCKED

M3B-LR2 stop:
CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED

M3B-LR2R1:
ACTIVE
```

Update `GITHUB_MANGA.txt`, `docs/manga/STATUS.md`,
`docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`, the Card Router, and reports index.
Keep LR2's historical `M3B-LR2 publication: LOCAL` wording unchanged.

---

# 4. Explicit model acquisition authorization

Only this one model is allowed:

```text
Model: CN-anytest4_illustrious2_A.safetensors
Source: 2vXpSwA7/iroiro-lora
Pinned revision: bb4a39142275ac975ae4e6a64d1df218f672e0f0
Repository path: test_controlnet2/CN-anytest4_illustrious2_A.safetensors
Expected bytes: 2502139104
Expected SHA256: e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8
```

The model must be reused or stored in the verified existing reForge shared
ControlNet root. It must not be copied into `ComfyUI/models/controlnet/`.

No B variant, other ControlNet, checkpoint, VAE, LoRA, model pack, external
dependency, or model download is allowed.

---

# 5. Preflight storage verification

Before any acquisition or reuse, inspect:

```powershell
Get-Item "E:\EasyReforge\stable-diffusion-webui-reForge\models\ControlNet" -Force |
    Format-List FullName,Attributes,LinkType,Target

Get-Item "E:\Data\Models\ControlNet" -Force |
    Format-List FullName,Attributes,LinkType,Target

Get-Item "E:\EasyReforge\Model\ControlNet" -Force |
    Format-List FullName,Attributes,LinkType,Target
```

If present, inspect:

```powershell
Get-Item "E:\EasyReforge\stable-diffusion-webui-reForge\extensions\sd-webui-controlnet\models" -Force |
    Format-List FullName,Attributes,LinkType,Target
```

Confirm existing `.safetensors` files and at least 6 GiB free space. Do not
delete or clean files.

---

# 6. Existing file and safe acquisition rule

If the expected file already exists in the verified shared root, compare size
and SHA256. On exact match, record `REUSED` and do not download or duplicate it.

If no matching file exists, download only to a `.partial` temporary filename,
verify expected size and SHA256, then atomically rename into the verified shared
root. Never write directly to the final filename.

Hash mismatch:

```text
STOPPED:
PINNED_CONTROLNET_HASH_MISMATCH
```

If the pinned source identity cannot be verified:

```text
STOPPED:
PINNED_CONTROLNET_SOURCE_NOT_VERIFIED
```

---

# 7. Git boundary

The model is a local runtime asset. Do not commit, upload, or broadly modify
gitignore. Confirm the model is not tracked by Git.

---

# 8. Compatibility evidence ladder

```text
source identity verified
↓
local byte/hash verified
↓
ComfyUI ControlNetLoader load
↓
Illustrious checkpoint pairing and graph validation
↓
actual queue
↓
actual image output
```

Only after the full ladder may runtime compatibility be reported as verified for
this Portable.

---

# 9. Historical evidence

Historical Phase 3I evidence may guide the bounded test only:

```text
Base: waiIllustriousSDXL_v170.safetensors
ControlNet: CN-anytest4_illustrious2_A.safetensors
Preprocessor: None
Historical useful strength: 0.75–0.80
```

Historical evidence does not replace current load or output evidence. WF71 is
not parity proof.

---

# 10. Loader and checkpoint gate

Restart ComfyUI and inspect object info. Prefer standard
`ControlNetLoader` / `ControlNetApplyAdvanced`; use Advanced-ControlNet only
when a concrete standard-path limitation is observed.

Load the model and verify selector visibility, successful loader execution, and
absence of invalid-model or architecture errors. Pair with the existing
canonical Illustrious checkpoint without changing or downloading the checkpoint.

Record checkpoint, SHA256 where practical, VAE, resolution, and generation
profile.

---

# 11. Research workflow only

Do not modify production:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

Create only:

`workflows/manga/research/M3B_LR2R1_ANYTEST_AB.json`

Use LR1 `TegakiMangaRoughGuideBridge.rough_guide_image` directly with no
preprocessor.

---

# 12. A/B invariants

For each pair, keep identical:

```text
checkpoint, VAE, prompt, negative, resolution, seed, latent,
steps, CFG, sampler, scheduler, regional plan, Guide image
```

Only ControlNet application and strength may differ.

Use exactly two fixed seeds and exactly:

```text
OFF
0.25
0.50
0.75
```

This is at most eight outputs. Use `start_percent=0.0` and `end_percent=1.0`
unless a documented existing node/model reason requires otherwise.

---

# 13. Fixture and ledger

Use a Page-owned LR1 Guide with two manually associated Figure Regions,
different left/right placement, and different sizes. Do not evaluate identity as
ControlNet success.

Record every attempt, including failures:

```text
seed, strength, OFF/ON, output filename, output SHA256, dimensions,
queue status, elapsed time, peak VRAM when readily available
```

Do not cherry-pick successful images.

---

# 14. Regression and browser gates

After model verification, rerun LR1 contract, runtime bridge, Guide ops, and
frontend regression. Queue the canonical no-Guide workflow and confirm normal
generation does not require ControlNet.

Confirm the affected LR1 foundation interactions: upload, contain, Figure add,
association, Save/Reload, disable, and remove.

Live ComfyUI research checks:

```text
E0 research workflow loads
E1 OFF queue PASS
E2 Seed A ON 0.25 PASS
E3 Seed A ON 0.50 PASS
E4 Seed A ON 0.75 PASS
E5 Seed B OFF PASS
E6 Seed B ON sweep PASS
E7 canonical no-guide PASS
```

---

# 15. Failure budget and no fallback

The same runtime root cause may be investigated at most twice. A bounded
semantic-preserving fix is allowed once for a clear cache/path issue or VRAM
preview issue. Do not reduce resolution substantially to force a pass.

Do not switch to B or any other model. If the pinned model fails runtime:

```text
STOPPED:
PINNED_ANYTEST_RUNTIME_INCOMPATIBLE
```

---

# 16. Production prohibition

Do not connect ControlNet to the production canonical workflow or add Product UI
settings such as `Guide Strength` or `ControlNet enabled`. That belongs to LR3.

---

# 17. Model lifecycle

The verified model may remain in the external shared storage after A/B. Do not
automatically delete it. Record source identity and hash, but never commit the
model to GitHub.

---

# 18. Evidence

Create:

`docs/manga/verification/m3b_lr2r1/`

Minimum artifacts:

```text
M3B_LR2R1_MODEL_IDENTITY.md
M3B_LR2R1_MANIFEST.json
SEED_A_OFF.png
SEED_A_025.png
SEED_A_050.png
SEED_A_075.png
SEED_B_OFF.png
SEED_B_025.png
SEED_B_050.png
SEED_B_075.png
```

Create `M3B_LR2R1_CONTACT_SHEET.png` when possible with rows:

```text
Seed A: OFF | .25 | .50 | .75
Seed B: OFF | .25 | .50 | .75
```

---

# 19. Manifest and report

Create:

`docs/manga/verification/m3b_lr2r1/M3B_LR2R1_MANIFEST.json`  
`docs/manga/reports/M3B_LR2R1_ANYTEST_V4_ACQUISITION_AND_AB_RESUME_REPORT.md`

The manifest must include expected/actual model bytes and SHA256, identity,
loader, technical A/B, generation influence, canonical regression, LR1
regression, production integration, and Owner review. The report must include
baseline, source identity, storage preflight, exact settings/seeds/strengths,
all output ledger rows, annotations, regressions, limitations, and publication
truth.

---

# 20. Classification

LUNA may record evidence and a provisional classification only:

```text
PROMISING: technical PASS, usable ON output at >=2 seeds, trend visible,
           seed variation remains, canonical and LR1 regressions PASS
QUALITY WEAK: technical influence exists but placement benefit is weak/unstable
BLOCKED: download/hash/load/runtime cannot be validated
```

Final classification belongs to SOL review. Do not claim identity, pose,
composition, production readiness, or backend parity.

---

# 21. Closeout and publication

After all stages, move this Card to `completed/` byte-identically and set:

```text
Active Card: NONE
```

Do not issue the next Card automatically. The report records:

```text
LR2R1 publication:
LOCAL
```

Current authority must not claim local work is publicly available. Owner push is
required before SOL publication review. Do not call Astra during this Card.

---

# 22. Stop conditions

Stop immediately for missing or unverifiable expected hash/source identity,
shared storage not established, insufficient disk, local hash mismatch,
invalid-model or Illustrious architecture error, external dependency need,
schema/production workflow change, or the same runtime root cause failing twice.

---

# 23. Required final response

```text
Card:
M3B-LR2R1

Execution baseline:
Final HEAD:
origin/main:

Stage 0 publication truth:
PASS / FAIL

Model acquisition:
PASS / FAIL / REUSED

Expected bytes:
2502139104
Actual bytes:

Expected SHA256:
e069d496cc111740716b833238d9bea9cdd59f8623aa85a78d362d088b1f67b8

Actual SHA256:

Model identity:
PASS / FAIL

ControlNet loader:
PASS / FAIL

Checkpoint:
VAE:
Resolution:
Steps:
CFG:
Sampler:
Scheduler:

Seed A:
OFF:
0.25:
0.50:
0.75:

Seed B:
OFF:
0.25:
0.50:
0.75:

Technical causality:
PASS / FAIL

Guide placement trend:
CLEAR / WEAK / NONE / DEGRADED

Image quality:
USABLE / DEGRADED / FAILED

Seed variation:
PRESENT / REDUCED / LOST

LR1 regression:
PASS / FAIL

Canonical no-guide regression:
PASS / FAIL

Generation influence:
VERIFIED / NOT_VERIFIED / BLOCKED

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED

Evidence:
Report:

Stopped early:
YES / NO

Stop reason:

LR2R1 publication:
LOCAL

Owner push required:
YES
```

---

# 24. Final instruction

Use exactly one pinned model and the verified existing shared storage. Continue
through acquisition/reuse, hash, load, A/B, and regression while each gate
passes. Do not promote success to production. The purpose is to reproduce
causal Guide→Generation influence for this Portable, this Illustrious
checkpoint, and this Rough Guide path.
