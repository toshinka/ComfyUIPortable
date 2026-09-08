# H3 Current Landscape

更新: 2026-09-08 JST
Evidence level: public provenance review plus H0.1 local model-backed generation smoke

## H0 / H0.1 reference implementation snapshot (2026-09-08)

Status vocabulary in this section is strict:

- `OBSERVED`: source or public-document fact.
- `VERIFIED LOCAL`: a local startup/API/static result was reproduced.
- `BLOCKED`: an explicit dependency, model, or evaluation-boundary blocker stopped
  the candidate before the relevant runtime result.
- `NOT TESTED`: no claim is made because the relevant path was not exercised.

| Candidate | Source | Checked commit | Code license | Local result |
|---|---|---|---|---|
| Native / official ComfyUI | https://github.com/Comfy-Org/ComfyUI | local `b1693ecba9f5b65f8c80ab36b195ab963ec92413`; upstream master `efa6c8f804bff78b46a0fd458ebd2e47bba07a30` | GPL-3.0 | `VERIFIED LOCAL GENERATION` T2V at 608x352; conservative peak 11,651/12,282 MiB |
| H3 Easy | https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy | `d00fd814769e586545c454d75068856c71c79116` | MIT | `VERIFIED LOCAL GENERATION` isolated I2V; shared custom-node tree unchanged |
| onigirikiller | https://github.com/onigirikiller/minimax-h3-webui | `f9b28d56d69192e4516907a61103a71ff2c29c27` | Apache-2.0 | `VERIFIED LOCAL GENERATION` UI/API plus Native backend; Gradio isolated |
| AntaresAlice | https://github.com/AntaresAlice/h3-webui | `4f10667c604f9cb333ac119b457a3659260a8966` | MIT | `VERIFIED LOCAL STARTUP`; generation `BLOCKED` by missing `MiniMaxH3AudioConditioningT8` in isolated backend |

The four first-wave official model files are hash-verified in the ignored local
`h3/model_store/`; no weight is in the shared `ComfyUI/models/` tree. Candidate
worktrees, runtime copies, venvs, and production video are local-only; only
URL/SHA/license/manifest/text evidence is tracked.

## Executive summary

Rev.3の順序を維持するなら、H3は「全部を独自実装する新製品」ではなく、
既存の良いVideo skin、Director / timeline、Still reference route、
low-VRAM recipeを薄い統合層で縫い止める `Patchwork Integration` として
調べるのが妥当です。

今回の確認で、設計材料として特に強いのは次の分離です。

- Videoの最小入口: `AntaresAlice/h3-webui`、
  `onigirikiller/minimax-h3-webui`、`ComfyUI-MiniMaxH3-Easy`
- Video Studio / timeline: `ComfyUI-H3Studio`、MiniMax H3 Director系
- Stillのconditioning / reference材料:
  `ComfyUI-MiniMax-H3-Image-Studio`、`ComfyUI-MiniMax-H3-Studio`
- 長尺・編集UXの研究材料: `MiniMax-H3-Director-Cut-Studio`
- 実行基盤の確認対象: ComfyUI native H3、公式 MiniMax H3 model package

これは設計材料の shortlist であり、採用・clone・導入・品質保証の一覧では
ありません。

## Base Quality / Stable Fast / Experimental

この分類は runtime profile の境界を先に作るための初期分類です。実機の
品質・速度・VRAM・再現性を検証した結果ではありません。

### Base Quality

- ComfyUI native H3 / official H3 route。
- `astropuzzo/ComfyUI-MiniMax-H3-Image-Studio` の native-looking still
  route、frame decode、source fidelity、reference editの考え方。
- `thaakeno/ComfyUI-MiniMax-H3-Studio` の Base Quality / Base Balancedの
  分離。ただしプロジェクト自身がalphaおよび一部実験経路と明記している。

Base Qualityは「最も高品質」という意味ではなく、Turboや新runtimeを混ぜない
比較の基準線です。

### Stable Fast

- `AntaresAlice/h3-webui` と `onigirikiller/minimax-h3-webui` の、既存
  ComfyUI APIを隠して prompt / reference / queue / historyへ短距離で到達
  させるskin。
- `ComfyUI-MiniMaxH3-Easy` の一つのMedia入力、reference順序、`@` reference
  editor、advanced設定の段階表示。
- 既存のpruned INT8、Qwen NVFP4/AWQ、host/system RAM offloadを、実機で
  再現できるなら12GB/16GB向け profile として評価する。

Stable Fastへの昇格条件は、Rev.3のCooling Gateに従い、公開から通常最低7日、
直近72時間の重大recipe変更なし、複数consumer GPU、12GBまたは16GB帯の実測、
固定可能なartifact / sampler / steps、upstream互換性、Base Qualityへの復帰、
license / provenance確認です。

### Experimental

- LightX / Turbo LoRA。
- FastH3 / VSA系 runtime。
- PDD（Parallel Decoding Distillation）系。
- experimental T=1 still extraction。
- GGUF、Unsloth Desktop、DynamicVRAMなどの別runtime / offload経路。
- H3を白黒漫画・screentone・hatching・page consistencyへ直接使う経路。

FastH3 / 新runtime級は原則14日程度観察可能にし、Experimentalで試しても
default profileへ自動昇格させません。

## H3 Video / GUI candidates

### AntaresAlice/h3-webui

Self-hosted WebUIとして、workspace / history / reference再利用 / continuation /
progress / ComfyUI境界を観察する対象です。MITと明記され、2026-09-08確認時の
main先頭は `4f10667c604f9cb333ac119b457a3659260a8966` でした。H1 Minimum Skinの設計材料として強い一方、
モデル・ランタイムの採用判断は別に必要です。

### onigirikiller/minimax-h3-webui

ComfyUI HTTP APIを駆動するqueue / last-frame chaining / join / bulk JSONの
小さなVideo UIです。Apache-2.0。READMEには12GB VRAMでT2V/I2Vを動かした記録と、
Ref2VAはより重いという制限があり、12GB baselineの設計材料になります。
2026-09-08確認時の先頭commitは `f9b28d56d69192e4516907a61103a71ff2c29c27` でした。

### ComfyUI-MiniMaxH3-Easy

今回確認した公開 repository は
`nkxx188/ComfyUI-MiniMaxH3-Easy` です。MIT。mixed media input、ordered reference、`@` editor、
I2V / first-last-frame / R2Vの段階化が、最小手の入口の参考になります。

### ComfyUI-H3Studio

`shootthesound/ComfyUI-H3Studio` はMIT。timeline、keyframe、reference、
continuation、reel、join/exportなどStudio化の機能鉱山ですが、初期skinへ
そのまま持ち込む量ではありません。2026-08-20確認時の先頭commitは
`85c557a` でした。

### MiniMax H3 Director系

- `seesee75-commits/ComfyUI-MiniMaxH3-Director`: GPL-3.0。LTX Director由来の
  timeline UIと、storyboard prompt compilation、first/last keyframe、
  reference、retake、chainを観察します。派生ライセンス境界を先に監査する
  必要があります。確認先頭commit: `8486323`。
- `AIMixer/ComfyUI_MiniMaxH3_Director`: Apache-2.0。multi-segment、T2V/I2V/
  FL2V/R2V/V2V/RV2V、選択実行、長尺分割の別実装です。確認先頭commit:
  `7de4a95`。

両者を「同じDirector」として混ぜず、実装・license・実証範囲を別候補として
扱います。

### MiniMax-H3-Director-Cut-Studio

`karuvanan/MiniMax-H3-Director-Cut-Studio` はMITのPySide6系Studioです。
multi-track timeline、media pool、semantic enrichment、shot-aware long
renderを研究します。機能面積が大きく、現在のH0/H1のベースにはせず、Studio化
以後のUX / architecture referenceへ延期します。確認先頭commit:
`a4ef316`（公開履歴上の先頭付近）。

## H3 Still candidates

### astropuzzo/ComfyUI-MiniMax-H3-Image-Studio

Unlicense。T2I / I2I / REF2VA、最大9枚のordered reference、`<Picture N>`
役割、source fidelity、temporal packet、single-image decode、experimental
T=1など、Stillの技術部品として重要です。README自身がAI-assisted / experimental
と明記するため、コード品質・runtime・licenseの再監査が必要です。確認先頭
commit: `b4a2339`。

### thaakeno/ComfyUI-MiniMax-H3-Studio

MIT。Image Director、text / I2I / reference edit route、最大9 reference、
role / retention / description / thumbnail、metadata restoration、VAE tiling、
LightX / PDD profileを観察します。プロジェクト自身がalphaで、classic Nodes
1.0中心、Nodes 2.0未対応と説明しているため、完成技術とは扱いません。確認先頭
commit: `8e106b3`。

### REF2VA still workflow / multi-reference reference-edit family

これは一つの採用repositoryではなく、H3 native REF2VAと上記Image Studio / H3
Studioで共通して見えるconditioningパターンです。ordered multi-reference、
semantic role、source anchor、source fidelityを別フィールドとして保持できる
かを確認します。現時点ではworkflowを本projectへ導入しません。

## Low VRAM / runtime candidates

- **pruned INT8**: 12GB/16GB baseline候補。ただし量子化形式、ConvRot、実測
  解像度、offload条件を固定して初めて比較可能です。
- **Qwen NVFP4 / AWQ**: text/vision encoder側のメモリ削減候補。VRAMだけでなく
  system RAM、ロード時間、精度、対応GPUを記録します。
- **host/system RAM offload**: 32GB/64GB RAMを前提にした実用経路候補。
  GPU-only成功の代わりにはなりません。
- **DynamicVRAM**: runtime memory managementの候補概念。単一repoや採用実装と
  してはまだ固定しません。
- **GGUF / Unsloth Desktop**: alternative runtime / distribution path。H3
  production baselineへ直ちに入れず、モデル・runtime・商用条件を分離して
  Research Laterとします。

## Fast path candidates

- **LightX / Turbo**: few-step LoRA / accelerated recipe。Base Qualityから隔離
  し、route・resolution・shift・steps・artifactを同時にpinします。
- **PDD**: H3の8-step系とparallel-decoding head bankを扱う候補。通常LoRAと
  同じものとみなさず、対応loader・モデル・licenseを監査します。
- **FastH3 / VSA**: 候補名は記録するが、このpassでは単一のcanonical source、
  license、再現可能なbaselineを確定していません。14日観察を含む別reviewへ
  送ります。

## Stillで重要な概念

今後のadapter / request設計で検討する概念は以下です。ただし今回、schemaは
実装しません。

- ordered multi-reference
- semantic reference role
- source anchor
- source fidelity
- identity / pose / clothing / compositionの分離
- experimental T=1
- Still metadata restoration
- rough/layout + CAST references → H3 Still → Illustrious / Anima finish

## 現時点で不足しているもの

以下は、候補READMEや設計メモだけで「確認済みの完成技術」と扱いません。

- H3-only manga production
- 安定した白黒漫画
- screentone
- hatching
- manga page consistency
- production-grade H3 Manga

これらはH3 VIDEO、Still、Illustrious Mangaの実働と検証が蓄積した後の
Research Laterです。

## Research boundary

- ここで述べた機能は公開README / LICENSE / commit履歴の観察と、H0.1固定
  smokeの範囲を分けて記録しています。
- H0.1では公式first-wave assetを使い、Native T2V、隔離H3 Easy I2V、
  onigirikiller UI/API経由T2Vを実生成した。Antares candidate-native経路は
  required custom node不足でsampling前にBLOCKEDとなった。
- これは12GB/16GBの全面比較、画素品質、長尺、REF2VA、Browser受入、Owner
  受入ではありません。候補ごとのpeak VRAMをすべて採取したとも主張しません。
- H3 model license、third-party model、custom node、GPL/Apache/MIT/Unlicense
  の組み合わせは別途provenance auditが必要です。Official assetのhashと
  Community License recordは[acquisition manifest](../evidence/H3_MODEL_ACQUISITION_MANIFEST.md)
  に固定しています。
- 既存Illustrious Manga runtime、workflow、canonical docsはこの調査で変更
  していません。

## Primary review links

- [AntaresAlice/h3-webui](https://github.com/AntaresAlice/h3-webui)
- [onigirikiller/minimax-h3-webui](https://github.com/onigirikiller/minimax-h3-webui)
- [ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)
- [ComfyUI-H3Studio](https://github.com/shootthesound/ComfyUI-H3Studio)
- [MiniMax H3 Director](https://github.com/seesee75-commits/ComfyUI-MiniMaxH3-Director)
- [AIMixer MiniMax H3 Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director)
- [MiniMax-H3-Director-Cut-Studio](https://github.com/karuvanan/MiniMax-H3-Director-Cut-Studio)
- [ComfyUI-MiniMax-H3-Image-Studio](https://github.com/astropuzzo/ComfyUI-MiniMax-H3-Image-Studio)
- [ComfyUI-MiniMax-H3-Studio](https://github.com/thaakeno/ComfyUI-MiniMax-H3-Studio)
- [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI)
- [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3)
