# MiniMax H3 ローカルGUI／Still／Studio 深掘り調査
更新日: 2026-09-08

## 結論

Tegaki の H3 開発方針は、全面的な作り直しではなく「既存の強い部分を採用し、薄い統合層で縫い止める」方針が最も合理的。

現在の有力構成は以下。

- H3 Video の軽量 Web 外殻: AntaresAlice/h3-webui、onigirikiller/minimax-h3-webui
- H3 Video Studio / Timeline の機能鉱山: shootthesound/ComfyUI-H3Studio、MiniMax H3 Director 系
- 長尺・編集ツール的UXの研究材料: MiniMax-H3-Director-Cut-Studio
- H3 Still の実装材料: astropuzzo/ComfyUI-MiniMax-H3-Image-Studio
- H3 Still の統合UI・reference UX材料: thaakeno/ComfyUI-MiniMax-H3-Studio
- H3 backend simplification: ComfyUI-MiniMaxH3-Easy と ComfyUI native H3
- 12GB向けの土台: pruned INT8 + Qwen NVFP4/AWQ + DynamicVRAM / host offload。GGUF は実験・代替経路。
- FastH3 / Turbo / PDD は「採用前提」ではなく高速化profileとして隔離する。

H3 Still は H3 MANGA の開始を早める理由にはならないが、H3 VIDEO の初期基盤が静止画経路を受け入れられるようにしておく理由には十分なる。

## 1. H3 Still の現状

### MiniMax H3 Image Studio

`astropuzzo/ComfyUI-MiniMax-H3-Image-Studio`

https://github.com/astropuzzo/ComfyUI-MiniMax-H3-Image-Studio

現時点で Still 実装の「技術部品」としてかなり有力。

確認できた機能:
- T2I / I2I / REF2VA reference edit
- 1 source + 最大8 reference、計9枚の ordered reference
- `<Picture N>` 単位の明示的役割指定
- `source_fidelity`
- 5 / 9 / 13 / 20 frame の temporal packet
- experimental T=1
- Turbo workflow
- Qwen detail refine
- API JSON例
- 追加runtime dependencyなし
- Unlicense

README:
https://github.com/astropuzzo/ComfyUI-MiniMax-H3-Image-Studio/blob/main/README.md

CHANGELOG:
https://github.com/astropuzzo/ComfyUI-MiniMax-H3-Image-Studio/blob/main/CHANGELOG.md

漫画・静止画用途で重要なのは、「参照画像を単に複数投入する」のではなく、Picture 1 = identity / scene、Picture 2 = pose、Picture 3 = clothing、Picture 4 = style のように semantic role を prompt contract として明示できる点。

現在の Tegaki が将来欲しい「CAST参照」「rough layout」「構図アンカー」「役割分離」に直結する。

ただしプロジェクト自身が AI-assisted / experimental であると明示しているため、コード品質は利用前監査が必要。

### MiniMax H3 Studio (Still)

`thaakeno/ComfyUI-MiniMax-H3-Studio`

https://github.com/thaakeno/ComfyUI-MiniMax-H3-Studio

こちらは技術ノードというより「StillをStudioとして扱うUX」が強い。

確認できた機能:
- 一つの Image Director
- Text / I2I / Reference Edit のroute自動選択
- 最大9 reference
- 各reference cardに role / retention / description / thumbnail
- ComfyUI upload統合
- LoRA最大6本
- LightX / PDD profile
- VAE tiling
- adaptive OOM backoff
- host-memory pressure telemetry
- metadata restoration
- reference comparison
- Benchmark Lab
- prompt prep用local Qwen-VL
- FL2VA / REF2VA route validation

弱点:
- alpha
- GPU validation boundaryを自身で明記
- ComfyUI Nodes 2.0未対応
- UIをそのままTegakiへ持ち込むより、interaction patternを採る方が安全

Still側の優先順位は、
1. Image Studio = conditioning / workflow / reference semantic の技術材料
2. H3 Studio = Director UX / reference card / route validation のUI材料

と分けるのがよい。

## 2. H3 Video GUI の比較

### AntaresAlice/h3-webui

https://github.com/AntaresAlice/h3-webui

MIT。

強み:
- self-hosted WebUI
- chat / overview / Studio の3 view
- dark UI
- workspace / history
- real step progress
- reference reuse
- continuation
- prompt editor
- ComfyUI backendとの分離
- Windows one-click思想
- Turbo 4/8 stepやRef2VAモデルの発見

Tegakiの「まずノードを隠してすぐ遊ぶ」初期外殻の参考として相性がよい。

### onigirikiller/minimax-h3-webui

https://github.com/onigirikiller/minimax-h3-webui

Apache-2.0。

強み:
- T2V / I2V / R2V
- queue
- last-frame chaining
- join
- bulk JSON
- ComfyUI HTTP APIとの分離
- 12GB実測記録あり

RTX 3060 12GB + 32GB RAMで、864×480 T2V/I2Vは実用動作が報告されている一方、Ref2VAは約1GB不足してOOMしたとREADMEに明記。

「最小Skin」の思想として非常に分かりやすい。

### shootthesound/ComfyUI-H3Studio

https://github.com/shootthesound/ComfyUI-H3Studio

MIT。

強み:
- fullscreen timeline
- first/last/waypoint keyframe
- keyframe strength
- references
- cast保存
- reel
- trim / crossfade / audio lanes / export
- continuation
- latent reuse
- automatic chaining
- V2V
- region denoise
- regional prompt
- camera motion path
- preview
- Turbo example
- 100コミット超

初期Skinとしては重いが、Tegaki H3 Studioが後で欲しくなる機能が大量に実装されている。
Phase H3/H4の機能鉱山として扱うのが妥当。

### MiniMax H3 Director

例:
https://github.com/seesee75-commits/ComfyUI-MiniMaxH3-Director
https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director

強み:
- timeline -> H3 native storyboard prompt
- reference image/video/audio
- retake
- live preview
- lazy checkpoint loading
- task routeの明示
- multi-segment
- first/last frame
- V2V / RV2V

特に「UIのintentをH3のnative prompt/conditioningへcompileする」思想が重要。
Tegakiの Recipe Resolver / semantic adapter の参考として引き続き有力。

### MiniMax-H3-Director-Cut-Studio

https://github.com/karuvanan/MiniMax-H3-Director-Cut-Studio

MIT。

現状かなり野心的。
- Premiere-inspired PySide6
- multi-track timeline
- AI shot planning
- semantic media enrichment
- long-video segment rendering
- reconnect / server-job recovery
- unlimited logical media pool
- 9 image / 3 video / 3 audio segment slot
- TTS
- project format
- 400超 tests と明示

ただし依存・機能面積が大きい。
Tegakiの初期ベースにするより、Studio化後のUX / architecture referenceとして利用するべき。

## 3. 12GB VRAM + 64GB RAM の現実性

公式MiniMax H3:
https://huggingface.co/MiniMaxAI/MiniMax-H3

ComfyUI系の実運用では、
- pruned INT8 ConvRot diffusion
- Qwen3-VL 32B NVFP4/AWQ
- DynamicVRAM
- system RAM offload
- fast NVMe

の組み合わせが12GB帯の現実路線。

onigirikillerの実測:
https://github.com/onigirikiller/minimax-h3-webui

- RTX 3060 12GB
- 32GB system RAM
- 864×480
- 5秒 20 step ≈15分
- 15秒 20 step ≈54分
- T2V/I2Vは動作
- Ref2VAは同環境ではOOM

別の12GB計測:
https://www.minimaxh3tutorial.com/

ではR2V 1344×768で約11.6GiB VRAMと43GB超のsystem RAMを報告しており、環境・ComfyUI version・offload pathによってRef2VAの可否が変わっている。

したがってTegakiでは「12GB Ref2VA対応」をYes/Noの固定仕様にしない。

Memory Profileとして、
- SAFE_12GB
- BALANCED
- QUALITY

のように切り分け、実行時にmodel / resolution / ref size / decode tiling / unloadを選ぶ設計がよい。

64GB system RAMは32GB環境より明確に有利。

## 4. Unsloth / GGUF

Unsloth Desktop:
https://www.unsloth.ai/

Unsloth:
https://github.com/unslothai/unsloth

MiniMax H3 GGUF:
https://huggingface.co/unsloth/MiniMax-H3-GGUF

現状:
- DesktopでMiniMax H3 image/video generationをサポート
- 小GPU向けsplit loading
- idle image/video model unload
- memory limit
- H3 GGUF配布
- CUDA / Vulkan等のruntime選択
- agent接続も可能

TegakiとしてはGUIを採用するより、GGUFが12GB救済経路になるか、model unload / memory limitの考え方、将来local AI workerとの連携を見る対象。

ComfyUIを中核にする現在の方針をUnslothへ置き換える理由はまだない。

## 5. FastH3 / Turbo / PDD

FastH3は2026年8月末〜9月頭に急速に出てきた新しい高速化ライン。

FastVideo:
https://haoailab.com/blogs/fasth3-local/

FastH3 guide:
https://minimaxh3.cc/guides/fasth3-minimax-h3

FastH3は4 transformer forwardsを狙うdistilled/VSA pathで、Blackwell / DGX / Apple Silicon側の実績が先行している。

ComfyUI実験も出始めているが、12GB Adaでの標準経路として固定するにはまだ早い。

LightX v1.0 8-stepは、H3 Still Studioでmain accelerated FL2VA pathとして扱われている。

PDD REF2VA 4-step:
https://github.com/mamad8c/ComfyUI-MiniMaxH3-PDD-Mamad8

いずれも高速化は魅力があるが、Tegakiの初期defaultにしない。

### 採用ルール案

「最低1週間寝かせる」は合理的。
ただし日数だけでなく以下を満たすこと。

FAST PATHをDefault候補へ昇格する条件:
1. 公開から7日以上
2. 重大なrecipe変更が直近72時間ない
3. 少なくとも2種類のconsumer GPUで成功報告
4. 12GBまたは16GB帯の実測が1件以上
5. exact artifact / LoRA / sampler / steps が固定できる
6. upstream ComfyUI更新で即壊れない
7. base quality pathへワンクリックで戻せる
8. license/provenanceが確認できる

FastH3のような新規runtimeは14日程度寝かせてもよい。

Tegakiでは、
- Base Quality
- Stable Fast
- Experimental

の3段階profileを設けるのがよい。

## 6. 漫画・静止画への意味

現時点で確認できた強化点:
- ordered multi-reference
- semantic role assignment
- source anchor
- pose / identity / clothing / composition分離
- static frame selection
- true T=1 experimentation
- still-specific VAE experimentation
- reference comparison
- face/detail refine

一方で、
- 白黒漫画
- screentone
- hatching
- 漫画ページとしての一貫した実例
- H3-only manga production

はまだ十分な実績がない。

よってH3 MANGA Phaseを前倒ししない。

代わりにH3の共通baseに、
- still generation request
- ordered references
- semantic role
- source anchor
- output still metadata

を入れられる余地だけ予約する。

将来:

rough/layout + CAST refs
→ H3 Still
→ selected still
→ Illustrious / Anima finish

という経路を塞がない。

## 7. GUI方針

TegakiのGUIは「既存GUIのコピー」ではなく、複数の成功パターンを薄く統合する。

目標:
- 現代的
- 触っていて新しい道具感がある
- 視線が横方向に流れる
- 制作状態が一画面で把握できる
- 詳細設定は必要時だけ開く
- ノードを見せない
- 素材と結果が常に見える

採用したいinteraction pattern:
- dark / neutral base + restrained accent
- left: Project / Asset
- center: production canvas / preview
- right: Inspector
- bottom: Queue / History / later Timeline
- reference = thumbnail card
- semantic role = chip / badge
- Generateを画面の主要actionに固定
- Advanced settingsはdrawer
- route/model名は通常隠すがdiagnosticでは見える
- Still / Videoで同じasset cardを使える
- fullscreen timelineは後から追加
- workspace persistenceは初期から持つ

GUIのブラッシュアップはAstraをスポット投入する価値が高い。

ただしAstraには「ゼロから新アプリを発明」させず、
- 候補GUI screenshots
- feature matrix
- current Tegaki constraints
- H1 scope

だけを渡し、画面構成とinteraction rulesを提案させる。

## 8. LUNA / Astra の役割分担

LUNAに先に大量のOSSをclone・収集させるのは非効率。
捨てるものまでlocal treeへ持ち込むため。

推奨順:

Web GPT
→ 調査・shortlist
→ LUNA
→ H3用の空の棚・reference inventoryだけ作る
→ Astra
→ bounded GUI / architecture proposal
→ Web GPT
→ proposalを採否・Card化
→ LUNA
→ 採用されたものだけ取得・実装

LUNAが最初に集めるのはコードではなく、
- repo URL
- pinned commit
- license
- intended role
- adopt / inspect / defer

程度のinventory。

実際のfork / copy / portは採用後だけ。

## 9. 推奨shortlist

### Tier A — 今すぐ設計材料にする
- AntaresAlice/h3-webui
- onigirikiller/minimax-h3-webui
- ComfyUI-MiniMaxH3-Easy
- astropuzzo/ComfyUI-MiniMax-H3-Image-Studio

### Tier B — H3 Studio設計時に強く参照
- shootthesound/ComfyUI-H3Studio
- MiniMax H3 Director系
- thaakeno/ComfyUI-MiniMax-H3-Studio

### Tier C — 長期UX / architecture研究
- MiniMax-H3-Director-Cut-Studio
- Unsloth Desktop
- FastH3/VSA
- PDD
- 3D Previz系

## 10. 最終判断

計画書の大きな順序は変更不要。

ただし以下は改定すべき。
1. H3 Still-ready base をH0/H1から明記
2. GUI patchwork strategyを正式化
3. H1は「fork選定」ではなくthin shell + adapter
4. Still技術部品とVideo UX部品を分離して採用
5. Astra UI Review GateをH1実装前に追加可能
6. LUNAはshortlist確定後だけコード取得
7. Stable Fast / Experimental profileを分離
8. Turbo/FastH3にadoption cooling gateを追加
9. H3 MANGAは最後のまま
10. H3→Illustrious Finishは将来経路として保持
