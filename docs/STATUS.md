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
  - 報告書: [M2A_CHARACTER_SPATIAL_CAPABILITY_LADDER_REPORT.md](reports/M2A_CHARACTER_SPATIAL_CAPABILITY_LADDER_REPORT.md)
  - 128件自動テスト100% PASS、19条件実機検証完了。

- **完了Card**: **M2A.1 — Prompt-Region Calibration & Conditional ControlNet Escalation Gate** — COMPLETED & VERIFIED
  - **Spatial Prompt Hint Compiler**: `custom_nodes_custom/tegaki_manga_nodes/spatial_hint_compiler.py` 実装。粗矩形幾何から短い空間語彙（"on the left side", "on the right side", "large in the foreground", "smaller in the background"）を実行時に非破壊導出。
  - **SSOT 不変性**: Persistent な `TEGAKI_AUTHORING_DOCUMENT` を一切汚染せず、`PAGE_COMPILE_PLAN` および `debug_json` に完全な透明トレーサビリティを保持。
  - **8-Seed 固定ベンチマーク（Seeds 42, 77, 101, 133, 202, 303, 404, 505）**:
    - **2人物（Benchmark B）**: B0ベースラインの有用率 25% (2/8) に対し、B1（左右Hint自動補助）で **62.5% (5/8有用、4/8明瞭成功)** へ大幅改善。左右スワップ因果性も100%保持。
    - **深度（Benchmark C）**: 幾何差のみ（C2）では極小枠の背景人物が1/8しか出ない一方、Derived Depth Hint（C3）により **62.5% (5/8有用)** へ劇的に救済。
    - **3人物（Benchmark H）**: Prompt+Region単独では1/8有用にとどまり、極めてSeed-Sensitive。
    - **ControlNet Escalation Gate v2**: 3人物のスコア未達により発動。Weak Block Guide ControlNet (0.20 / 0.35) を実機検証。0.20は効果薄、0.35は格子・ケージ状の作画アーティファクトと姿勢硬直を招き、Brainstorm Freedomが急減。
    - **製品アーキテクチャ判定**: **CORE_NOT_NEEDED**。Minimum-Hand CoreへControlNetを強制せず、純粋な Prompt + Rough Region + 隠しSpatial Helper（Option A+）で進行。3人物・4人物はTier 3/4（マルチカット分割推奨またはAdvanced補助）として整理。
  - **自動テスト**: 全139件（既存128件＋M2A.1新規11件）100% PASS。
  - **実機生成**: 全97条件＋ControlNet 4条件完走。4種のコンタクトシート・Manifest生成完了。
  - **報告書**: [M2A1_PROMPT_REGION_CALIBRATION_AND_CONTROL_GATE_REPORT.md](reports/M2A1_PROMPT_REGION_CALIBRATION_AND_CONTROL_GATE_REPORT.md)
  - **製品UI推奨**: **OPTION A+（Rough Region + Free Text Acting Prompt + 隠しAutomatic Spatial Helper）**

- **完了Card**: **M2B / 3M-2B — Minimum-Hand CAST & Character Staging Product UI (Option A+)** — COMPLETED & VERIFIED
  - **Option A+ Product UI統合**: `TegakiMinimumHandSceneEditor`（表示名: `Tegaki Minimum-Hand Manga Authoring (Draft)`）の単一ノード内に、GLOBAL設定（Resolution, Style, Seed + `[🎲 Randomize Seed]`）、CAST Master登録、キャンバス上のCharacter Rough Region直接操作、自由記述Acting Prompt、3+/4+警告バッジを統合。
  - **契約パリティ（M0準拠）**: シーン移動時に属するキャラクター矩形を同一ベクトル移動、シーンリサイズ時にキャラクター矩形を比例拡大縮小。参照中CASTの削除抑止、シーン削除時の関連キャラクター自動破棄（孤立参照防止）。
  - **Hidden AUTO Spatial Policy**: 研究用手動パラメータをUIから隠蔽し、シーン内のキャラクター数および面積比（$\ge 1.8$）から自動判定する `auto` ポリシーを導入（1人=off, 2人通常=horizontal, 2人深度=spatial_depth, 3+人=off）。
  - **Canonical Workflow 安定名化**: `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json` を `workflows/MINIMUM_HAND_MANGA_DRAFT.json` へ `git mv` し、root 1本体制を確立。
  - **自動テスト**: 全161件 Python テスト（既存139件＋M2B新規22件）および 7件 JS headless contract テストが100% PASS。
  - **実機検証 & 目視検査**: ComfyUI スタンドアローン実機環境で単一人物・2人物・深度・複数シーン出演の4条件を生成し直接目視確認完了。
  - **報告書**: [M2B_MINIMUM_HAND_CAST_STAGING_PRODUCT_UI_REPORT.md](reports/M2B_MINIMUM_HAND_CAST_STAGING_PRODUCT_UI_REPORT.md)
  - **Manifest**: `docs/verification/m2b/M2B_PRODUCT_PATH_MANIFEST.json`

- **次Card候補**: **M3 — Rough Manga / Visual Panel Guide Integration**
  - Semantic Scene / CAST staging に対し、実際の漫画コマ枠（Visual Panel Frames）とラフ漫画 / 白ハゲ / 人物シルエット構図拘束を直交して統合。

---

## 6. 関連正本リンク
- 戦略SSOT: [ASTRA_MANGA_AUTHORING_MASTER_PLAN.md](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)
- UX詳細: [ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md)
- 資産棚卸し: [ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)
- 実行プロトコル: [ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md](plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md)
- 文書登録簿: [DOCUMENT_REGISTER.md](DOCUMENT_REGISTER.md)
