# ComfyUIPortable 現在地 (Status & Direction)

更新: 2026-09-06 JST
Review Target Commit SHA: `5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8` (Phase 3L 実装正本)
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

- **完了Card**: **M1 / 3M-1 — Scene-only Minimum-Hand Draft** — COMPLETED
  - Resolution Preset + Style Template + Scene Rectangles + Scene Prompts + Seed → 実機生成導線を完工。
  - `TegakiMinimumHandSceneEditor` ノード、`authoring_execution_bridge.py`、Web UI拡張 `minimum_hand_scene_editor.js`、正本ワークフロー `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json` 実装。
  - 98件自動テスト（旧78件 + 新規20件）全PASS。
  - Live ComfyUI（SDXL Illustrious v1.7）による実機画像生成 5条件（A: 1 Scene, B: 2 Scenes, C: Geometry Swap Oracle, D1/D2: Seed Brainstorm）全完走・全目視確認（平均生成時間 16.5秒）。
  - Contact Sheet・Manifest を `docs/verification/m1/` に配置完了。
  - 報告書: [M1_3M1_SCENE_ONLY_MINIMUM_HAND_DRAFT_REPORT.md](reports/M1_3M1_SCENE_ONLY_MINIMUM_HAND_DRAFT_REPORT.md)
- **次Card**: **M2 / 3M-2 — Minimum Character & CAST Staging**
  - CAST Master登録（1〜2名）、Sceneへの簡易CAST出演、Character Rough Region配置、LoRA適用。Simple modeとの共存。

---

## 6. 関連正本リンク
- 戦略SSOT: [ASTRA_MANGA_AUTHORING_MASTER_PLAN.md](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)
- UX詳細: [ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md)
- 資産棚卸し: [ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)
- 実行プロトコル: [ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md](plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md)
- 文書登録簿: [DOCUMENT_REGISTER.md](DOCUMENT_REGISTER.md)
