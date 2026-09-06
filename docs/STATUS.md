# ComfyUIPortable 現在地 (Status & Direction)

更新: 2026-09-06 JST
Review Target Commit SHA: `72e032c71d97eed2712552062a75fde5d29c2360` (Phase 3M-2A M2A 実装正本)
正本入口: [GITHUB_ComfyUI.txt](../GITHUB_ComfyUI.txt)

---

## 1. Product Direction (Minimum-Hand Manga Authoring)

Tegaki / ComfyUIPortable は、
**最小手でSceneとCAST配置を粗く指定し、PromptとSeedの揺らぎを使って漫画Draftを高速に出し、必要な部分だけ後からControl / Pose / SubSceneで精密化する「Minimum-Hand Manga Authoring Tool」** を目指す。

- **A1111 / Forge風の分かりやすさを優先**: どこから触ればよいか直感的に分かり、上から順に設定してGenerateへ到達できる単一の迷わない導線を重視。
- **First Useful Draft を最優先Gateへ**: 技術機能の総数より、最初の「それなりに誘導された漫画Draft」が出るまでの手数と速度を最優先する。
- **Seed Randomness は創造的機能**: Seedは単なる固定デバッグ値ではなく、構図・ポーズ・表情のアイデアを膨らませるBrainstorming機能として扱う。
  - *Draftで固定するもの*: CAST identity, rough Scene location, rough Character location, Visual Panel topology.
  - *Draftであえて揺らすもの*: Pose, gesture, expression nuance, camera nuance, background detail, hair/cloth detail.

---

## 2. Target User Flow vs Development Order

### Target User Flow (完成Productで想定する基本操作導線)
```text
Resolution / Aspect Ratio
  ↓
Quality / Style Template
  ↓
CAST Master
  ↓
Rough Semantic Scene Regions
  ↓
Character Rough Regions
  ↓
Optional Rough Manga / Dummy Guide
  ↓
Visual Panel Frame / Control Guide
  ↓
Seed / Generate / Brainstorm
  ↓
Optional Refinement (Pose / SubScene / Inpaint)
```

### Development Order (安全に実装を分割する開発順序)
```text
Scene-only Draft (M1) → CAST 複数出演 (M2) → Rough Guide (M3) → UX Shell (M4)
```
※ 開発順序（技術を安全に積み上げる順）と、完成Productのユーザー操作順（上が先、下が後）を混同しないこと。

---

## 3. コア概念の整理

1. **Semantic Scene Region vs Visual Panel Frame**:
   - **Semantic Scene Region**: 「この辺で何が起きるか」の意味領域。Regional Prompt / CAST配置の基準。
   - **Visual Panel Frame**: 実際に見える漫画のコマ枠。Panel Layout / ControlNet Guideの基準。両者を同一視しない。
2. **Character Rough Region**:
   - Character Instanceの粗い空間表現（「Aliceはだいたいこの辺、Bobはだいたいこの辺」）。厳密なPose maskではなく、最小入力として扱う。
3. **Rough Manga / Dummy Guide の優先**:
   - 白ハゲ / 棒人間 / ラフ漫画 / 人物シルエット等の粗いGuide画像へCAST意味領域を対応させることを、3D Pose Editorより先に置く。
4. **Pose / Interaction の位置づけ**:
   - Pose / Interaction / SubScene / Manual Mask は削除しないが、Primary UX から外し、後段の **Advanced / Refinement** 扱いとする。

---

## 4. エビデンス訂正と現状 (Evidence Corrections)

- **Phase 3L Visual Evaluation**: `PHASE3L_PRESENCE_EVALUATION.json` の14条件はすべて `visual_status: PENDING` であり、Ownerの最終制作受入は未確立。
- **WF71 パリティ未実証**: WF71は既存Tegaki adapter内配線であり、Inspire RegionalPromptSimple や Advanced-ControlNet との真のバックエンド比較実証にはなっていない。
- **バックエンド方針の区別**: 「採用予定 (INTENDED / PLANNED)」と「実機実証済み (VERIFIED)」を厳密に区別する。

---

## 5. 次の一件 (Current Card Preview)

- **完了Card**: **M2A / 3M-2A — Character Spatial Capability Ladder & Control Escalation Gate** — COMPLETED
  - 単一人物位置追随（Stage A: 左右別領域配置）: PASS（テキストに左右を含めず完全追随）。
  - 2人物独立配置（Stage B）: PASS / useful PARTIAL（AliceとBobが同一シーンに独立属性で共存）。
  - 左右スワップオラクル（Stage B2）: **PASS（重要オラクル成立）**。同Seed 42・同Promptで領域のみ入れ替え、人物の物理配置が左右完全に逆転。因果性を実証。
  - 遠中近・接写深度（Stage C/D）: **PROMPT_SUFFICIENT**。同一領域サイズでもPrompt（近景バスト vs 遠景全身）のみで強固な遠近オクルージョン階層を形成。極小枠幾何よりもPrompt誘導が安定。
  - 姿勢天井診断（Stage E）: PASS。椅子コンテキストの明示（"sitting on a wooden chair"）により着席姿勢が成立。
  - 同一CAST複数コマ（Stage F）: PASS。コマを跨いだ同一人物の出演を確認。
  - 同一CAST単一コマ重複（Stage G）: PARTIAL。並列双子よりもコマ割り分割・多面体描写へ誘導される傾向を確認。
  - 同一CAST＋異CAST混成3人（Stage H）: **PASS（Seed 42にてAlice 2体＋Bob 1体の3名完全共存・無漏出を達成）**。
  - 多人数の崩壊閾値（Stage I）: **3〜4人が境界**。4人以上では単一構図から自動マルチカット分割へ移行。
  - 区域強度スライダー: 1.0固定で十分機能し、**UIスライダー新設は不要**と判定。
  - **ControlNet エスカレーション判定**: **不要（Level 0: Prompt + Rough Region でM2Bへ進行）**。
  - 自動テスト全128件（既存114件＋M2A新規14件）100% PASS。
  - 実機生成全19条件完走・直接目視検査完了。4種のオラクルコンタクトシートおよび Manifest 配置完了。
  - 報告書: [M2A_CHARACTER_SPATIAL_CAPABILITY_LADDER_REPORT.md](reports/M2A_CHARACTER_SPATIAL_CAPABILITY_LADDER_REPORT.md)
  - Core Minimum-Hand Character Capability: **READY**
- **次Card**: **M2B / 3M-2B — Minimum Character & CAST Staging Product UI (Option A: Rough Region + Free Text Prompt)**
  - CAST Master登録、キャンバス上でのCharacter Rough Region矩形操作、Acting Prompt自由文入力UIの実装。
  - 複雑な3D Pose/ControlNet/強度スライダーは含めず、最小手の直感操作導線を確立する。

---

## 6. 関連正本リンク
- 戦略SSOT: [ASTRA_MANGA_AUTHORING_MASTER_PLAN.md](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)
- UX詳細: [ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md)
- 資産棚卸し: [ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)
- 実行プロトコル: [ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md](plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md)
- 文書登録簿: [DOCUMENT_REGISTER.md](DOCUMENT_REGISTER.md)
