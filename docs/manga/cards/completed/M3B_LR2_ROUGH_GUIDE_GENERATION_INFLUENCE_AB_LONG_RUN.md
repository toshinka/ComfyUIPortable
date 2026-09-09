# M3B-LR2 — Rough Guide Generation Influence A/B Long-Run

Date: 2026-09-10 JST  
Issuer: Web GPT SOL  
Executor: LUNA local chat  
Mode: LONG-RUN BATCH  
Milestone authority: Web GPT SOL  
Final product review: Owner / DEFERRED

保存先:

`ComfyUIPortable/docs/manga/cards/current/M3B_LR2_ROUGH_GUIDE_GENERATION_INFLUENCE_AB_LONG_RUN.md`

## 0. Purpose

M3B-LR1で完成したRough Guide Foundationを使い、

```text
same document
same prompt
same checkpoint
same seed

Guide OFF
vs
Guide ON
```

を比較できる実生成A/B経路を構築する。

目的は、

「Rough Guideをgenerationへ接続すると、実際に出力へ因果的影響があるか」

を証拠付きで確認すること。

このCardではまだControlNet経路をproduction canonicalへ昇格させない。

---

# 1. Verified baseline

Latest SOL-verified public commit:

`1db61c19c076d8f66f18492f30157c53f6dac92f`

M3B-LR1:

```text
Contract: PASS
Runtime bridge: PASS
Browser R0-R8: PASS
Generation influence: NOT_IMPLEMENTED
ControlNet: NOT_ADDED
Final Owner product review: DEFERRED
```

---

# 2. Start

```bash
git status --short --untracked-files=all
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
```

期待baseline:

`1db61c19c076d8f66f18492f30157c53f6dac92f`

origin/mainが進んでいた場合:

```bash
git diff --name-status \
  1db61c19c076d8f66f18492f30157c53f6dac92f..origin/main
```

を確認。

Manga own filesと競合しなければ最新baselineで継続。

H3だけならSTOPしない。

---

# 3. Stage 0 — Publication truth

最初にCURRENT AUTHORITYだけ修正。

必須truth:

```text
Latest SOL-verified public commit:
1db61c19c076d8f66f18492f30157c53f6dac92f

M3B-LR1 publication:
PUBLISHED

M3B-LR1 SOL review:
PASS

M3B-LR1 generation influence:
NOT IMPLEMENTED

M3B-LR2:
ACTIVE
```

対象:

* `GITHUB_MANGA.txt`
* STATUS
* handoff
* Card Router
* reports index

LR1 report本文の

```text
no push was performed
```

はLUNA終了時点の歴史記録なので変更しない。

publication-only Cardは作らない。

---

# 4. Central rule

M3B-LR2はまず**Research / Verification path**として実装する。

禁止:

```text
実験成功前にcanonical product generationへControlNet必須化
Guide無しgenerationの変更
ControlNet modelの自動download
外部dependency追加
モデル名だけでSDXL compatibilityを推測
```

---

# 5. Existing LR1 truth — preserve

以下は変更しない。

```text
Guide ownership = Page
Figure area = Guide-local normalized
Guide placement = Page-normalized
association = instance_id
derived page area = runtime only
automatic matching = none
```

Scene / Visual Frame / CAST意味境界を変更しない。

---

# 6. Stage 1 — Local Control backend inventory

最初にPortable内だけを監査。

確認:

```text
models/controlnet/
installed ControlNet nodes
existing Manga workflows 66–71
existing node registrations
```

最大3候補まで。

候補ごとに記録:

```text
model filename
model size
SHA256
claimed architecture if locally evidenced
node path
existing workflow use
SDXL/Illustrious compatibility evidence
```

## 禁止

filenameに`xl`等があるだけでcompatibleと断定しない。

SD1.5 ControlNetをIllustriousへ代用しない。

---

# 7. Stage 1 decision

最低1つ、

```text
SDXL / Illustrious-compatible enough to execute a bounded test
```

と根拠を持って判断できる候補が存在する場合のみStage 2へ進む。

存在しない場合:

```text
STOPPED:
CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED
```

として終了。

外部downloadしない。

このSTOPは失敗扱いではなく有効な調査結果。

---

# 8. Do not use WF71 as parity proof

WF71の存在だけで、

```text
Inspire parity
Advanced-ControlNet parity
Illustrious compatibility
```

を宣言しない。

既存inventoryの注意事項を維持する。

---

# 9. Stage 2 — Experimental workflow

production canonical:

`workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`

はGeneration配線を変更しない。

新規:

`workflows/manga/research/M3B_LR2_ROUGH_GUIDE_AB.json`

または既存namespace規則に沿うresearch pathを作成。

---

# 10. A/B architecture

一つのfixtureから:

```text
TEGAKI_AUTHORING_DOCUMENT
        |
        +--> existing base conditioning
        |
        +--> RoughGuideBridge image
```

を作る。

OFF:

```text
base conditioning
→ KSampler
→ output OFF
```

ON:

```text
base conditioning
→ selected ControlNet path
→ KSampler
→ output ON
```

OFF/ONで固定:

```text
checkpoint
VAE
prompt
negative
resolution
seed
steps
CFG
sampler
scheduler
latent dimensions
```

ControlNetだけが差分。

---

# 11. Important causal rule

OFF/ONを別の日に手動設定し直さない。

可能なら同一workflow / 同一queue構造で比較する。

最低でもsnapshotされた完全同一generation parametersをreportへ記録する。

---

# 12. Guide input

Control pathへ渡す画像はLR1の:

`TegakiMangaRoughGuideBridge.rough_guide_image`

を優先。

これにより:

```text
original aspect
contain placement
Page coordinates
```

をproduct Guide contractと一致させる。

---

# 13. Figure union mask

LR2では`figure_union_mask`を勝手にControlNetのmask入力として使わない。

使用する場合は対象nodeがそのmask semanticsを明示的にsupportすると確認できた場合だけ。

「maskがあるから何となく掛ける」は禁止。

---

# 14. Strength sweep

compatible candidateが1つ確定したら、最大:

```text
0.25
0.50
0.75
```

の3 strengthのみ。

start/endは候補node/modelの既存実績値がある場合それを使用。

根拠がない場合の初期値:

```text
start = 0.0
end = 1.0
```

とし、勝手に大量探索しない。

---

# 15. Seeds

最低2 Seed。

例:

```text
Seed A
Seed B
```

各Seedについて:

```text
OFF
ON 0.25
ON 0.50
ON 0.75
```

最大8出力。

これ以上のgrid searchは禁止。

---

# 16. Primary fixture

LR1で作ったRough Guide + 2 Character Instances相当のfixtureを再利用してよい。

条件:

* 2 figures
* 明確に左右または上下が異なる
* figure sizeも多少異なる
* Scene Promptには人物の大まかな内容を含む
* ControlNetだけでidentity保証を期待しない

---

# 17. What LR2 measures

LR2が測るもの:

```text
A. Control pathが実際にexecuteしたか
B. OFFとONが同条件で比較可能か
C. ONが出力へ因果的差分を与えるか
D. Figure placementに沿う傾向が目視可能か
E. 強すぎるControlで画質崩壊しない範囲があるか
F. Seed variabilityが完全消失していないか
```

---

# 18. What LR2 does NOT claim

禁止ラベル:

```text
character identity guaranteed
pose guaranteed
composition locked
production ready
best ControlNet
backend parity
```

---

# 19. Technical causality gate

各A/B pairで記録:

```text
output filename
seed
strength
model
queue completion
image dimensions
output hash
```

OFFとONのhashが同一ならFindingとして記録。

単にhashが違うだけを品質PASSにはしない。

---

# 20. Visual evidence

作成:

`docs/manga/verification/m3b_lr2/`

例:

```text
S1_OFF.png
S1_ON_025.png
S1_ON_050.png
S1_ON_075.png

S2_OFF.png
S2_ON_025.png
S2_ON_050.png
S2_ON_075.png
```

さらに比較用:

```text
M3B_LR2_CONTACT_SHEET.png
```

を作成してよい。

---

# 21. Visual annotations

LUNAの判定は以下に限定。

```text
Guide placement trend:
CLEAR / WEAK / NONE / DEGRADED

Image quality:
USABLE / DEGRADED / FAILED

Seed variation:
PRESENT / REDUCED / LOST
```

これはOwner final reviewではない。

---

# 22. No cherry-picking

「成功した画像だけ」をreportへ載せない。

実行したbounded sweepは全結果をmanifestへ記録する。

失敗画像もevidence。

---

# 23. Stage 3 — Regression

必須:

LR1:

```text
contract tests
Guide ops
runtime bridge
frontend regression
```

再実行。

さらにcanonical:

`MINIMUM_HAND_MANGA_DRAFT.json`

をGuide無しでqueue。

期待:

```text
existing generation PASS
no ControlNet dependency
no required Guide
```

---

# 24. Stage 3 — LR1 persistence regression

最低確認:

```text
Guide upload
Figure edit
association
Save/Reload
disable
remove
```

がLR2変更で壊れていない。

headless中心で可。

---

# 25. Experimental workflow validation

検証:

```text
JSON parse
all node types available
all links valid
OFF path reaches SaveImage
ON path reaches SaveImage
ControlNet model is explicitly recorded
```

---

# 26. Browser / live runtime

実際のComfyUIを使用。

server restart。

browser hard reload。

research workflowをload。

最低:

```text
E0 workflow loads
E1 OFF queue PASS
E2 ON queue PASS
E3 same-seed comparison produced
E4 second-seed comparison produced
E5 canonical workflow regression PASS
```

---

# 27. If ControlNet fails

以下の場合:

```text
model load failure
shape mismatch
SDXL incompatibility
runtime node incompatibility
OOM reproducibly
black/NaN output
```

1回原因確認。

明確なbounded fixなら1回修正。

同じroot causeで2回FAILならSTOP。

別モデルを無制限に試さない。

---

# 28. Candidate limit

Control model候補は最大3。

実生成まで進める候補は原則1。

最初の候補が明白にload不能の場合のみ次候補へ。

---

# 29. Production promotion forbidden

LR2で結果が良くても:

`MINIMUM_HAND_MANGA_DRAFT.json`

のproduction generation pathへControlNetを接続しない。

Product UIに:

```text
Guide Strength
ControlNet ON
```

等の設定を正式昇格させない。

それは次Card。

---

# 30. Own implementation files

変更可:

* research workflow
* bounded experiment runner/tests
* verification files
* report
* current authority
* Card routing

既存LR1 implementationはbugが見つかった場合のみ最小修正可:

* `rough_guide_bridge.py`
* authoring contract
* minimum-hand Guide JS

ただしLR2目的のためのrefactorは禁止。

---

# 31. Do not touch

禁止:

* H3
* H3 docs/workflows
* Tegaki core
* ComfyUI core/frontend
* EasyReforgeExtension
* RegionalLoRALab
* shared model files
* model download
* M4
* Shell
* Scene/Frame/CAST semantics
* output namespace migration

---

# 32. Stage 4 — Result classification

LR2終了時、以下のどれか1つ。

## A — PROMISING

```text
Control path technical PASS
Guide trend visible
usable output exists at ≥2 seeds
Seed variation remains
```

Next:

`M3B-LR3 Product Guide Influence Integration`

候補。

## B — TECHNICAL PASS / QUALITY WEAK

```text
Control path executes
but placement benefit is weak/unstable
```

Next:

Astra/SOL review before more implementation。

## C — BLOCKED

```text
compatible local model not established
or runtime incompatible
```

Next:

Control backend selection Card。

---

# 33. No self-promotion

LUNAはA/B結果を見て勝手にA判定しない。

LUNAはevidenceと暫定classificationを報告してよい。

最終Milestone classificationはSOLがGitHub reviewで決定。

---

# 34. Report

作成:

`docs/manga/reports/M3B_LR2_ROUGH_GUIDE_GENERATION_INFLUENCE_AB_REPORT.md`

最低内容:

```text
Execution baseline
Control model inventory
Selected candidate
Compatibility evidence

Exact generation settings
Exact seeds
Exact strengths

OFF/ON output ledger
Hashes

Technical execution
Visual trend annotations

Regression
Canonical no-guide result

LR1 regression

Generation influence:
VERIFIED / NOT VERIFIED / BLOCKED

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED
```

---

# 35. Manifest

`docs/manga/verification/m3b_lr2/M3B_LR2_MANIFEST.json`

最低:

```json
{
  "card": "M3B-LR2",
  "technical_ab": "PASS|FAIL|BLOCKED",
  "control_model": "...",
  "control_model_sha256": "...",
  "seeds": [],
  "strengths": [],
  "canonical_regression": "PASS|FAIL",
  "lr1_regression": "PASS|FAIL",
  "generation_influence": "VERIFIED|NOT_VERIFIED|BLOCKED",
  "production_integration": "NOT_PERFORMED",
  "final_owner_product_review": "DEFERRED"
}
```

---

# 36. Documentation closeout

CURRENT AUTHORITYに事実だけを書く。

PROMISINGでも:

```text
M3B-LR2 experimental generation influence:
VERIFIED

Production ControlNet integration:
NOT YET IMPLEMENTED
```

と分離。

---

# 37. Routing

開始時:

```text
Active Card:
M3B-LR2
```

全Stage終了後:

LR2 Cardをcompletedへbyte-identical移動。

```text
Active Card:
NONE
```

次Cardを作らない。

---

# 38. Publication semantics

reportには終了時:

```text
M3B-LR2 publication:
LOCAL
```

と記録可。

CURRENT AUTHORITYにはLOCALをcurrent truthとして書かない。

Owner push後にSOLが確認。

publication closureだけのCardは作らない。

---

# 39. Astra timing

LR2完了後、LUNAはAstraを呼ばない。

SOLが公開成果物を確認する。

その後、

```text
M3A.1
M3B-LR1
M3B-LR2
```

をまとめたM3B構造監査packetをAstraへ発行するか判断する。

---

# 40. STOP conditions

即STOP:

```text
schema version変更が必要
Guide ownership変更が必要
Scene/Frame/CAST意味変更が必要
ComfyUI core modification必要
外部dependency必須
model download必須
SDXL compatibilityを推測でしか決められない
```

---

# 41. Required final response

```text
Card:
M3B-LR2

Execution baseline:
Final HEAD:
origin/main:

Stage 0 Publication truth:
PASS / FAIL

Stage 1 Control inventory:
PASS / BLOCKED

Candidates found:
1.
2.
3.

Selected candidate:
Model:
SHA256:
Compatibility basis:

Stage 2 A/B workflow:
PASS / FAIL / NOT RUN

Seed A:
OFF:
ON 0.25:
ON 0.50:
ON 0.75:

Seed B:
OFF:
ON 0.25:
ON 0.50:
ON 0.75:

Technical causality:
PASS / FAIL

Guide placement trend:
CLEAR / WEAK / NONE / DEGRADED

Seed variation:
PRESENT / REDUCED / LOST

Canonical no-guide regression:
PASS / FAIL

LR1 regression:
PASS / FAIL

Generation influence:
VERIFIED / NOT_VERIFIED / BLOCKED

Production integration:
NOT PERFORMED

Final Owner product review:
DEFERRED

Evidence:
<path>

Report:
<path>

Stopped early:
YES / NO

Reason:

M3B-LR2 publication:
LOCAL

Owner push required:
YES
```

# 42. Final instruction

Stage gateがPASSする限り、途中確認を返さずLong-Runで最後まで実行する。

ただしControl backend compatibilityを推測して突破してはいけない。

LR2の目的は「本番統合」ではなく、

**Guide→Generationの因果を、同条件A/Bで証明または否定すること**

である。

---
