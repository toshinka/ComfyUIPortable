# 3M-Prep: SSOT Publication & Minimum-Hand Direction Reset Report

更新: 2026-09-06 JST

## 1. Overview
本作業（3M-Prep）は、大規模な機能追加ではなく、GPT6Astraによって再構築された戦略文書・資産棚卸し・UX設計をGitHub正本（SSOT）として確定し、Product Directionを「研究中心・ポーズ多用」から「最小手でDraftを出すMinimum-Handツール」へとリセットするための前処理である。

## 2. Files Published & Authority Alignment
以下の文書群が、ComfyUIPortableの現行開発・設計の正本（CURRENT AUTHORITY）として登録された。
- `docs/STATUS.md`: 1〜2分で方針・現在地・次の一件を把握する高密度ステータス文書
- `docs/DOCUMENT_REGISTER.md`: 文書登録簿（CURRENT AUTHORITY / CURRENT CARD / HISTORICALの分類）
- `docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md`: 漫画制作環境の全体戦略マスタープラン
- `docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md`: 最小手漫画制作UXブループリント
- `docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md`: 資産棚卸し・限界分析・ComfyUI Comic Creator監査
- `docs/plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md`: Web GPT-SOL と Antigravity Gemini の協調プロトコル
- `docs/plans/ASTRA_GEMINI_CLEANUP_INSTRUCTIONS.md`: 今後の履歴整理指示書
- `GITHUB_ComfyUI.txt`: 外部AIおよびAI間共有メモリの正本入口
- `GITHUB.TXT`: `GITHUB_ComfyUI.txt` への互換性ポインタに統一

## 3. STATUS Changes & Product Direction Reset
`docs/STATUS.md` に以下のコア方針を明記した：
1. **Minimum-Hand Manga Authoring Tool**:
   - 最小手でSceneとCAST配置を粗く指定し、PromptとSeedの揺らぎを使って漫画Draftを高速に出し、必要な部分だけ後からControl / Pose / SubSceneで精密化する。
   - A1111 / Forge風の「上から順に設定してGenerateへ行ける」分かりやすい単一導線を優先。
2. **Target User Flow vs Development Order の分離**:
   - *Target User Flow (完成Product導線)*: Resolution → Style Template → CAST → Rough Scene Region → Character Rough Region → Optional Dummy Guide → Visual Panel Frame Guide → Seed / Brainstorm → Generate → Optional Refinement.
   - *Development Order (安全な開発順序)*: Scene-only (M1) → CAST複数出演 (M2) → Rough Guide (M3) → UX Shell (M4).
3. **Semantic Scene Region vs Visual Panel Frame**:
   - Semantic Scene Region（何が起きるかの意味領域・Regional Prompt/CAST基準）と、Visual Panel Frame（コマ枠・Layout/ControlNet基準）を独立した概念として定義。
4. **Character Rough Region**:
   - 厳密なPose maskではなく、「Aliceはこの辺、Bobはこの辺」という粗い空間指定を最小入力とする。
5. **Rough Manga / Dummy Guide の優先**:
   - 白ハゲ / 棒人間 / ラフ漫画画像へのCAST割り当てを、3D Pose Editorより先に置く。
6. **Pose の位置づけの適正化**:
   - Pose / Interaction / SubScene / Manual Mask はPrimary UXから外し、Advanced / Refinement（後段の便利機能）へ格下げ。
7. **Seed Randomness as Creative Feature**:
   - Seedは単なるデバッグ値ではなく、構図・ポーズ・表情・背景ニュアンスを探索するBrainstorming機能として扱う。
8. **First Useful Draft Product Gate**:
   - 機能の多さではなく、最初の有用なDraftが出るまでの手数と速度を重視する。

## 4. Evidence Corrections Preserved
Astraによって指摘された重要エビデンス訂正を完全に保持：
- **Phase 3L Presence Evaluation**: `PHASE3L_PRESENCE_EVALUATION.json` の14件はすべて `visual_status: PENDING` であり、Ownerの最終受入は未確立。
- **WF71 パリティ未実証**: WF71は既存Tegaki adapter内配線であり、Inspire RegionalPromptSimple や Advanced-ControlNet との真のバックエンド比較実証にはなっていない。
- **バックエンド判断の区別**: 「採用予定 (INTENDED/PLANNED)」と「実機実証済み (VERIFIED)」を厳密に区別。

## 5. External Reference: ComfyUI Comic Creator
- `docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md` にComfyUI Comic Creator (https://github.com/ketle-man/comfyui-comic-creator) の限定監査を記録。
- **現時点の判断**: `REFERENCE`（SPA配信境界、Template Wizard幾何、Draftレイヤの設計参考）。
- **非採用/保留**: Speech balloons, 3D text, EPUB, full editorは追わない。FORKは現時点で不採用。SELECTIVE REUSEは将来別CardでPinned SHA固定時に検討。

## 6. Commit Strategy & Review Target
- **Review Target Commit SHA**: `5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8` (Phase 3L 実装正本を厳格に保持。ドキュメント整理のSHAで上書きしない)
- **Planning Commit SHA**: Commit A（本SSOT公開コミット）
- **Runtime Code Changed**: **NO** (0 files modified in runtime nodes / workflows / tegaki_work)
- **Push Status**: **LOCAL ONLY** (リモートへの自動pushは行わず、Ownerの判断に委ねる)

## 7. Next Step
- **Next Card**: **M0 / 3M-0 — Versioned Authoring Contract & Scene / Frame Separation Foundation**
- **概要**: 将来のMinimum-Hand UI導線に耐えうるBackend非依存のAuthoring Contract（新Scene/Frame分離、ID体系、座標系、旧フォーマットimport、fixtures）を先行固定する。

---

## 8. Sign-off

```text
ASTRA SSOT FILES PRESENT: PASS
STATUS CURRENT DIRECTION: PASS
TARGET USER FLOW RECORDED: PASS
DEVELOPMENT ORDER SEPARATED: PASS
SCENE / PANEL FRAME SEPARATION: PASS
ROUGH GUIDE PRIORITY: PASS
POSE DE-PRIORITIZED: PASS
SEED BRAINSTORM POSITION: PASS
COMIC CREATOR REFERENCE: PASS
PHASE3L EVIDENCE CORRECTION PRESERVED: PASS
DOCUMENT AUTHORITY: PASS
GITHUB_COMFYUI CANONICAL ENTRY: PASS
GITHUB.TXT POINTER ONLY: PASS
IMPLEMENTATION REVIEW TARGET PRESERVED: PASS
RUNTIME CODE CHANGED: NO
NEXT CARD: M0 / 3M-0
```
