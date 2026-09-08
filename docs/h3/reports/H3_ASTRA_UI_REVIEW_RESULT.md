# H3 Astra UI Review Result

更新: 2026-09-08 JST
Status: review evidence only; not a roadmap, implementation specification, or
final UI decision

## Purpose

前段のAstra bounded UI reviewで確認された意味・優先順位・保留事項を、H3の
Reference Implementation Evaluationへ渡すための証跡として固定する。
これは新しい画面仕様、CSS仕様、frontend framework、backend、workflow、schema、
H1実装の指示ではない。

## Executive verdict

H3の初期入口は、Video first、Preview-centered、最小アクション、既知の制作語彙を
保つ方向が妥当である。Reference Implementationの評価では、機能数ではなく、
Generate / Reference / Preview / Queue / History / Errorが初回利用から再利用まで
短い距離で理解できるかを確認する。

同時に、初期語彙をH1の必須機能と同一視しない。Project / Shot / Take、Storyboard、
Studio、Cast、Lensの増加は、実働する最小生成フローを確認した後に扱う。

## KEEP

- Video first
- Familiar production terminology
- Preview-centered workflow
- Manga independence

## ADJUST

- Initial vocabulary is not the same thing as the H1 required feature set.
- Project / Shot / Take are not required in the initial generation path.
- Keep the Advanced surface short enough to remain readable.
- Make the purpose and order of Reference explicit.
- Make Queue / Error / Disconnect states clear.

## DEFER

- Many Lens modes
- Permanent Cast surface
- Storyboard
- Full Studio
- Semantic-role promises that are not verified by runtime behavior
- Fast-runtime claims that are not verified on the target hardware

## VALIDATE

- First generation flow
- Repeated parameter change and regeneration
- Reference reuse
- Failure / disconnect comprehension
- Actual visual usability

## Key ambiguities

1. UI vocabulary can look complete while the underlying H1 path is still only a
   prompt-to-video smoke path.
2. Reference roles and order must be visible and reproducible; labels alone are
   not evidence that the model receives the intended order.
3. A progress indicator must distinguish queued, running, completed, failed,
   and disconnected states.
4. A richer Studio surface can improve continuity work while still being the
   wrong initial cognitive lens.

## Evaluation criteria for reference implementations

Reference implementations are evaluated on the following evidence, in this order:

1. First-use clarity and minimum action count.
2. Familiar Generate / Preview / Queue / History grammar.
3. Reference selection, order, reuse, and failure visibility.
4. Generation settings and Advanced disclosure.
5. Job state, progress, disconnect, and error comprehension.
6. Repeated use: parameter changes, history reuse, and continuation.
7. Actual visual usability on the target desktop and 12GB-class GPU boundary.
8. Separation of Video, Still, Studio, and Manga scope.

The evaluation records both **Cognitive Level** (known production-tool conventions)
and **Cognitive Lens** (how Generate / Reference / History / Studio separate scope).

## Items explicitly not decided

- H1 implementation or final screen hierarchy
- Final palette values or CSS
- Frontend framework or component names
- Persistence schema, API contract, or workflow contract
- Storyboard / Timeline / Cast / multi-track / 3D / Manga promotion to H1
- Code reuse, vendoring, fork, or adoption of any candidate
- Model acquisition, model license interpretation, or hosted/API use

## Next gate

Complete the four-candidate Reference Implementation Evaluation with pinned source
SHA, code license, model provenance, local launch result, and evidence links. Web GPT
then reviews the evidence and chooses whether a separately scoped H1 card may be
written. This report does not release H3 implementation.
