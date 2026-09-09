# ComfyUIPortable 現在地 (Status & Direction)

更新: 2026-09-09 JST
Review Target Commit SHA: `a7f0baaa89a2e315b0492573c9da19e50727928b` (M3A.1 implementation, published)
Manga正本入口: [GITHUB_MANGA.txt](../../GITHUB_MANGA.txt)

`GITHUB_ComfyUI.txt` はManga/H3を振り分けるCompatibility Routerへ変更した。
今回のnamespace整理は文書/navigationのみで、Manga runtime・workflow・schema・outputを変更していない。
今後はWeb GPT SOLが[新規チャット引き継ぎ](WEBGPT_SOL_LUNA_HANDOFF.md)からGitHubを監査し、
[Card Router](cards/README.md)と[現行プロトコル](plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md)に従って
ローカルLUNAへ新しい限定Cardを発行する。現在、active LUNA implementation Cardはない。

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
  - **Option A+ Product UI統合**: `TegakiMinimumHandSceneEditor`（表示名: `Tegaki Minimum-Hand Manga Authoring (Draft)`）の単一ノード内に、GLOBAL設定、CAST Master登録、Character Rough Region直接操作、自由記述Acting Prompt、3+/4+警告バッジを統合。
  - **Canonical Workflow 安定名化**: `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json` をroot 1本化。

- **完了Card**: **M2B.1 — CAST Placement Semantics & Live Browser Closure** — COMPLETED (Backend/Headless) / FAIL (Owner Live Browser Check)
  - **Finding A（選択CAST配置の因果性）解消**: `minimum_hand_scene_editor.js` の剰余サイクリング（modulo arithmetic）を廃止し、選択されたCAST（`selectedCastId`）を厳格に配置するセマンティクスへ修正。単一CAST登録時は自動選択、複数CAST登録かつ未選択時は非サイレントに選択を促すブロックを実施。
  - **純粋操作関数の分離**: `custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js` へ純粋ロジック（CAST選定、一意instance_id生成、幾何配置、last instance削除時のinput_modeリセット等）を抽出。
  - **Last Instance Removal Policy**: シーン内の全キャラクターインスタンスが削除された際、`scene.input_mode` を `"simple"` へ復帰させつつ、背景プロンプト（`scene.prompt`）を厳格に非破壊保持。
  - **DOM Injection 防止**: `< > & " '` を含む表示名・プロンプトに対する安全な DOM 構築・プロパティ設定を徹底。
  - **Finding B（検証分類の厳格化 & Owner検証結果）**: E2E分類を `HEADLESS_TEST`（JS 13件 / Python 165件 100% PASS）、`LIVE_RUNTIME`（実機GPU 3条件完走 PASS）、`LIVE_BROWSER`（Owner実機確認によりFAIL判定）へ整理。
  - **報告書**: [M2B1_CAST_PLACEMENT_AND_BROWSER_CLOSURE_REPORT.md](reports/M2B1_CAST_PLACEMENT_AND_BROWSER_CLOSURE_REPORT.md)
  - **Manifest**: `docs/manga/verification/m2b1/M2B1_PRODUCT_E2E_MANIFEST.json`

- **完了Card**: **M3A / 3M-3A — Visual Panel Frame Layer & Frame Guide Integration** — PASS (Headless) / OWNER ACCEPTANCE PENDING (Browser)
  - `page.visual_frames` SSOT、3-layer Edit UI、Frame独立操作、TegakiMangaFrameOverlay node、0-frame pass-through、V0-V4 PASS。
  - **報告書**: [M3A_VISUAL_PANEL_FRAME_AND_FRAME_GUIDE_REPORT.md](reports/M3A_VISUAL_PANEL_FRAME_AND_FRAME_GUIDE_REPORT.md)

- **現行Review Slice（active実装Cardなし）**: **M3A.1 / 3M-3A.1 — Frame Runtime Truth, Gutter Semantics & Live Browser Closure** — PASS (Headless) / OWNER ACCEPTANCE PENDING (Browser)
  - **Finding A (fail-closed)**: invalid JSON / out-of-range page_index → ERROR status (fail-closed)。0 frames → pass-through PASS (legal)。
  - **Finding B (white gutter)**: comic_panels semantics: 白キャンバス + source paste inside frames + 黒枠線。Frame外 = 純白 gutter。
  - **Finding C (per-frame thickness)**: `border_thickness` per-frame honored、global `line_thickness` は fallback のみ。
  - **Finding D (area canonical)**: `area` key canonical。`shape` はlegacy fallback。`copyFramesFromScenes` area-only出力。JSON roundtrip後のdrift解消。
  - **Finding E (empty guide)**: `derive_panel_layout_spec_from_frames([])` → None (no fake full-frame)。
  - **Manifest truth**: `visual_status=PENDING`、`structural_frame_status` のみ pixel oracle で確認。
  - **Frame ID correction**: sequential `frame_1, frame_2...` (not timestamp+random — M3A Report記述誤り修正)。
  - **自動テスト**: Python 14/14 (M3A.1 新規) + 7/7 (M3A) + 13/13 (回帰) PASS、JS 19/19 PASS。V0-V4 pixel oracle PASS。
  - **報告書**: [M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md](reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md)

- **次Card候補**: **M3B — Rough Manga / White-Dummy Character Guide Integration** (Owner Browser受入完了後に着手)
  - rough manga image drop、white-dummy / silhouette character guide、Character Instance ↔ rough figure association、weak occupancy ControlNet を統合予定。


---

## 6. 関連正本リンク
- 戦略SSOT: [ASTRA_MANGA_AUTHORING_MASTER_PLAN.md](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)
- UX詳細: [ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md)
- 資産棚卸し: [ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)
- SOL/LUNA引き継ぎ: [WEBGPT_SOL_LUNA_HANDOFF.md](WEBGPT_SOL_LUNA_HANDOFF.md)
- 実行プロトコル: [ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md](plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md)
- 文書登録簿: [DOCUMENT_REGISTER.md](DOCUMENT_REGISTER.md)
