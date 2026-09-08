# H3 Astra Prep Semantic Alignment Report

更新: 2026-09-08 JST

## Summary

Web GPT auditで見つかったH3 UI文書の意味ズレとレビュー境界の混線を修正した。
今回の変更は文書整合性だけであり、H3実装、GUI実装、mockup、wireframe、
Astra実行、runtime benchmark、Illustrious変更は行っていない。

主な修正は次の二つである。

1. 思考の水平 / Cognitive Level を、既知の制作文化圏にある UI・操作概念を
   基準面として不要な認知的段差を作らない原則へ戻した。
2. Scene / Shot / Asset / Runtime / Review を Cognitive Level から分離し、
   current context、information hierarchy、workspace scope、または Cognitive
   Lens として扱うようにした。

## Files modified

- ComfyUIPortable/docs/h3/plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md
- ComfyUIPortable/docs/h3/plans/H3_ASTRA_UI_REVIEW_HANDOFF.md
- ComfyUIPortable/docs/h3/README.md
- ComfyUIPortable/GITHUB_H3.txt

## File added

- ComfyUIPortable/docs/h3/reports/H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md

H3_GUI_DESIGN_PRINCIPLES.md、Rev.3 master roadmap、既存Illustrious Manga
canonical docsは変更していない。

## Cognitive Level correction

Visual Language文書の誤った「ユーザーが扱っている粒度」という説明を削除し、
次のTEGAKI定義へ修正した。

思考の水平 / Cognitive Level:

同じ利用文化圏で広く定着しているUI・操作概念を基準面とし、ユーザーが既存知識
をそのまま転用できる範囲では、不要な認知的段差を作らない。新しい操作体系を
導入して基準面から高さを作る場合、その高さには明確な制作上の利益が必要である。

Rev.3の原則である次の文言とも整合する。

Preserve the Cognitive Level. Earn every slope. Build mountains only where the
summit is worth reaching.

## Cognitive Lens separation

Scene、Shot、Asset、Runtime、Review は Cognitive Level の定義ではなく、
current context、information hierarchy、workspace scope として扱う。

Cognitive Lens は、同じ Project / Asset / Job を目的別に見る切替である。
Project、Asset、Generate、Reference、Still、Video、Timeline、Diagnostic、
Review などを、tab、segmented button、drawer、inspector、workspace switch
などで扱う。新しい保存正本や別アプリを意味しない。

## Manga concept boundary correction

H3初期GUI reviewから semantic Scene region と visual Panel Frame の論点を
主要レビュー対象として外した。Panel、Page、Manga schema、Illustrious semantic
redesignは初期H3 VIDEO reviewの必須論点ではなく、後段のbounded taskへ送る。

削除ではなく境界を明記した。

Illustrious Manga has its own Scene / Panel / Region / Character semantics.
Do not redesign or merge those semantics during this H3 Video review.

## Astra review scope after correction

AstraのscopeはH3 VIDEO初期GUIの一回限りのbounded reviewとした。

1. H3 VIDEO minimum-action entry
2. familiar production-tool conventions
3. Cognitive Lensによるscope separation
4. progressive disclosure
5. Futaba heritage paletteとmodern production UI
6. H3 Video / Still / Studio boundary
7. Reference UX
8. queue / progress / error / status visibility
9. slopeとmountainの境界
10. premature Manga integrationの回避

Expected outputは、confirmed principles、conflicts / ambiguities、UI
information hierarchy、minimum H3 Video entry、Reference interaction、
Lens / progressive disclosure、visual language、status / queue / error、
conventionalに残すもの、slope / mountainの根拠、未決事項、risks、
Web GPTへのquestions / decisionsである。

heritage-heavy、balanced、next-generationの三案出しはcanonical requirement
にしていない。

## Illustrious boundary check

このalignmentで変更したのはH3 document layerだけである。既存のIllustrious
Manga implementation、runtime、workflow、保存形式、Scene / Panel / Region /
Character semanticsには差分がない。

## Git diff summary

Baseline before this slice:

d5d1c89b3dbdd4d50bb3e18b4d96c13a66276cb1

Expected closeout diffは、上記4つの既存H3文書の修正と、このreportの追加だけで
ある。既存の別作業変更をstageしない。

## Git status

開始時のworktreeはcleanだった。完了後もsemantic alignment対象だけをcommitし、
worktreeをcleanに戻す。H3 implementationとAstra executionは未開始である。

## Commit SHA

- Semantic alignment commit: to be recorded after the bounded commit
- Push state: Owner workflowでpushするまでlocal only

## GitHub review links

- Repository: https://github.com/toshinka/tegaki
- H3 entry: https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/GITHUB_H3.txt
- Document Hub: https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/README.md
- Visual Language: https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_GUI_VISUAL_LANGUAGE_AND_BRAND.md
- Astra Handoff: https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/plans/H3_ASTRA_UI_REVIEW_HANDOFF.md
- This report: https://github.com/toshinka/tegaki/blob/main/ComfyUIPortable/docs/h3/reports/H3_ASTRA_PREP_SEMANTIC_ALIGNMENT_REPORT.md

## Next gate

1. Web GPT reviews this semantic alignment and the current document chain.
2. Web GPT issues one bounded Astra UI review instruction.
3. Astra performs one bounded review pass without implementation or broad rewrite.
4. Web GPT converts accepted findings into a bounded LUNA card.
5. H3 implementation remains blocked until the applicable review gates release it.
