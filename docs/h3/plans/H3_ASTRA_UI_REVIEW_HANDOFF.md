# Astra UI Review Handoff Index

更新: 2026-09-08 JST

## Purpose

この文書は、Astra を別の新しい Chat へ渡すための read index である。Astra
への最終 prompt、実装指示、UI mockup 指示ではない。新しい Chat に過去会話が
ない前提で、共有 repository のどこを読み、どこで停止するかを固定する。

## Read order

1. ComfyUIPortable/GITHUB_H3.txt — current entry、scope、publication state。
2. ComfyUIPortable/docs/h3/README.md — H3 document hub と evidence vocabulary。
3. MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md
   — Rev.3 current master roadmap。Archive/ 版と同一内容であることを local
   hash で確認する。
4. ComfyUIPortable/docs/h3/plans/H3_GUI_DESIGN_PRINCIPLES.md — cognitive
   level、cognitive lens、progressive disclosure、mountain。
5. ComfyUIPortable/docs/h3/plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md —
   Futaba heritage と 2020年代 production UI の接続。
6. ComfyUIPortable/docs/h3/research/H3_CURRENT_LANDSCAPE.md — Video / Still /
   runtime の現在地。候補を採用済みと読まない。
7. ComfyUIPortable/docs/h3/references/H3_REFERENCE_INVENTORY.md — provenance、
   license、checked revision、候補の review 境界。

## Current handoff state

- H3 implementation は開始していない。
- H3 frontend、backend、custom node、model、workflow、schema は追加しない。
- 既存 Illustrious Manga implementation、canonical documents、workflow、
  runtime は変更しない。
- h3/ と workflows/h3/ は future boundary を示す空棚である。
- local main の groundwork baseline は
  3883e9a26e72c6544c9dac78fa9e271eb234944f。
- Rev.3 の public root URL は Owner が closeout commit を push した後に外部から
  再確認する。現実行環境では GitHub への outbound fetch ができないため、
  URL の公開済み状態をこの index で断定しない。

## Astra review scope

Astra に求めるのは、H3 VIDEO 初期 GUI の bounded design review だけである。

1. H3 VIDEO の minimum-action entry が成立するか。
2. familiar production-tool conventions をどこまで維持するか。
3. cognitive lens による scope separation が成立するか。
4. progressive disclosure の境界が妥当か。
5. Futaba heritage palette と modern production UI を両立できるか。
6. H3 Video / Still / Studio の境界を保てるか。
7. Reference UX の方向が既知の制作概念から連続しているか。
8. queue / progress / error / status visibility が不足していないか。
9. どの complexity が slope で、どこが mountain なのか。
10. premature Manga integration を避けられているか。

Illustrious Manga has its own Scene / Panel / Region / Character semantics.
Do not redesign or merge those semantics during this H3 Video review. Panel /
Page / Manga schema は初期 review の対象外で、後段の bounded task に送る。

## Expected review output

レビュー結果は次の順で返す。

- Confirmed principles
- Conflicts / ambiguities
- UI information hierarchy
- Minimum H3 Video entry
- Reference interaction direction
- Lens / progressive disclosure proposal
- Visual language direction
- Status / queue / error visibility
- What should remain conventional
- What could justify a slope
- What could justify a mountain
- What not to decide yet
- Risks
- Questions / decisions for Web GPT

スクリーン案や component 名を出してもよいが、それらは review artifact と
して扱い、実装の正本・最終仕様・Owner acceptance とは扱わない。heritage-heavy、
balanced、next-generation の三案出しは canonical requirement にしない。

## Review operation boundary

Astra review is expected to be a single bounded review pass.

Do not:

- start implementation
- spawn subagents by default
- perform broad repository rewrites
- redesign unrelated Illustrious systems
- create production code
- install dependencies
- select final architecture unilaterally

## Stop conditions

以下を行わずにレビューを終了する。

- H3 implementation を開始する
- frontend framework、ComfyUI custom node、model、workflow を導入する
- 既存 Illustrious Manga の file、runtime、保存形式、canonical document を
  書き換える
- Rev.3 の順序を Astra の判断だけで変更する
- 新しい公開 URL、license、採用決定を根拠なしに確定する
- Owner の最終受入を代行する
