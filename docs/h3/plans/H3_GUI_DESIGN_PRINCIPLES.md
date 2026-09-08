# H3 GUI Design Principles

更新: 2026-09-08 JST
Source: local H3 master roadmap Rev.3 summary
Status: design summary only; not an Astra implementation instruction

## Purpose

H3 GUIは、ComfyUIのnode graphを通常ユーザーへ露出することから始めず、
H3 VIDEOを最小手で生成できる入口から育てる。Still、Studio、Mangaを同じ初期
画面へ詰め込まず、必要な仕事のscopeだけを見せる。

このファイルはRev.3を短く復元するための要約です。ここで画面、component、
schema、framework、backendを確定しません。

## 思考の水平 / Cognitive Level

ユーザーが既存の制作文化圏で身につけた知識を、新しいツールへ段差なく持ち
込めること。Prompt、Seed、Reference、LoRA、Resolution、Generate、Preview、
Queue、History、Timeline、Project、Shot、Takeのような語彙を、独自名称に置き
換えるためだけに壊さない。

水平を守れる場所では守る。新しさは、既知の操作を再学習させる理由ではなく、
制作上の明確な利益で判断する。

## 傾斜と山

既知の操作を改善する緩い傾斜には、学習コストに見合う速度・明瞭さ・制御性が
必要です。大きく異なる操作を要求する「山」は、その先に次のような登る価値が
必要です。

- 明確に速い
- 明確に分かりやすい
- 従来できなかった制作ができる
- 生成・編集・履歴が一続きになる
- 触ること自体に制作上の価値がある

単なる独自Timelineや新奇な見た目は、山ではなく壁になり得ます。

## 思考のレンズ / Cognitive Lenses

Project / Asset / Jobを別の目的から見るscopeとして、次のようなレンズを
検討します。

```text
Project     Asset       Generate       Reference
Still       Video       Timeline      Diagnostic
```

レンズは別アプリや別の保存正本ではありません。tab、segmented button、drawer、
contextual inspector、temporary panel、workspace switch等から、現在必要な情報
だけを出します。

## Progressive Disclosure

必要な設定へ短距離で到達できるA1111 / Forge的な直接性は残します。ただし全設定を
常時露出させません。

```text
よく使う       -> 常時
今回必要       -> contextで表示
専門設定       -> Advanced / Inspector
故障解析       -> Diagnostic Lens
```

「シンプル」は機能削除ではなく、初期の視界から不要な機能を外すことです。

## H3への適用順

1. H3 VIDEOのPrompt / Reference / Resolution / Duration / Steps/Profile /
   Seed / LoRA / Generate / Preview / Progress / Queue / Historyを最短で通す。
2. H3 Stillはordered reference、semantic role、source anchor、metadataを受け
   入れられる基盤として検証する。
3. Timeline、Storyboard、Recipe ResolverはH3を実際に使った後のStudio scopeへ
   送る。
4. Illustrious MangaのScene / Panel / Region / Character semanticsをH3都合で
   変更しない。
5. H3 MANGAはVideo、Still、Illustrious Manga、Studioが実働した後の研究とする。

## Reference UXの方向

単なるfile inputから、既知のReference概念を保ったsemantic cardへ緩やかに拡張
します。

```text
[Character A] Identity
[Rough]       Composition
[Image C]     Pose
```

Identity、pose、clothing、compositionなどの役割分離は有力な研究材料ですが、
今回のgroundworkでは保存schemaもUIも実装しません。

## Benchmark

コード流用候補とUX benchmarkを分離します。

- CLIP STUDIO PAINT Simple Mode
- Callipeg / Callipeg Studio
- Procreate Dreams
- Procreate
- Adobe Fresco
- ToonSquid
- H3の既存GUI候補

観察点はcanvas / previewを主役にすること、panelの密度、tablet・pen・mouse・
keyboardの役割、Timelineのscope、light/dark surface、状態色の節度です。

## Performance profiles

H3-specific UIが直接選択させる概念を増やしすぎないよう、runtimeは別profileへ
隔離します。

```text
Memory:  SAFE_12GB | BALANCED | QUALITY | EXPERIMENTAL
Runtime: Base Quality | Stable Fast | Experimental
```

Turbo、LightX、FastH3 / VSA、PDD、新しいoffload runtimeはBase Qualityへ混ぜず、
Cooling Gateを通すまでExperimental扱いです。

## Astra review boundary

Astraには後続の別Chatで、現行Rev.3、shortlist、benchmark screenshot、H1 scope、
desktop / future tablet input条件を渡し、screen hierarchy、lens、interaction、
visual language、what-not-to-redesignだけをレビューさせます。

今回の文書はその依頼文ではありません。Web GPTがgroundworkを監査し、採用候補と
review scopeを固定した後に、別カードとして作成します。
