# ComfyUIPortable 現在地 (Status & Direction)

更新: 2026-09-11 JST
M3A.1 Core Implementation SHA: `a7f0baaa89a2e315b0492573c9da19e50727928b`
M3A.1 Current Closure Review Target: `ad91c9277715e998663e8c12b6c37cca16e53955`
Manga正本入口: [GITHUB_MANGA.txt](../../GITHUB_MANGA.txt)
Latest SOL-verified Manga public commit: `13f76668a264725ea8c6c3a1f6bb012e2d0c326c`
M3B-PI1: PUBLISHED / SOL REVIEWED / PI1_BACKEND_INTEGRATED
M3B-PI2: PUBLISHED / SOL REVIEWED / PI2_AUTO_ROUTING_INTEGRATED
M3B-PI2-BC1: PUBLISHED / SOL REVIEWED / PI2_BROWSER_CLOSED
M3B: PRODUCTION CLOSED
Manga integration readiness: READY FOR INTEGRATION DESIGN
H3 integration readiness: H3_READY_FOR_INTEGRATION_DESIGN
Cross-track architecture design: READY FOR REVIEW
Runtime hosting: OPEN DESIGN QUESTION
Shared-shell implementation: NOT AUTHORIZED
Active Card: NONE
Final Owner product review: DEFERRED
Latest completed Card: [M3B-PC1 — Production Closure & Cross-Track Integration Boundary Freeze](cards/completed/M3B_PC1_PRODUCTION_CLOSURE_AND_INTEGRATION_BOUNDARY_FREEZE.md)
Preceding completed Card: [M3B-PI2-BC1 — Real Browser Product Flow Closure](cards/completed/M3B_PI2_BC1_REAL_BROWSER_PRODUCT_FLOW_CLOSURE.md)
Latest completed report: [M3B Production Closure & Integration Readiness Report](reports/M3B_PRODUCTION_CLOSURE_AND_INTEGRATION_READINESS_REPORT.md)
Stable integration boundary: [Manga Product Integration Boundary](MANGA_PRODUCT_INTEGRATION_BOUNDARY.md)
Regression: PASS / Runtime: PASS / Browser: PASS (PI2_BROWSER_CLOSED via Playwright Chrome real browser suite) / Visual evidence: PASS / M3B-LR1: COMPLETED / M3B-LR1 generation influence: NOT IMPLEMENTED / M3B-LR2: PUBLISHED / SOL REVIEWED / BLOCKED / M3B-LR2 stop: CONTROL_MODEL_COMPATIBILITY_NOT_ESTABLISHED / M3B-LR2R1: PUBLISHED / SOL REVIEWED / generation influence: VERIFIED FOR RESEARCH GRAPH / quality: WEAK / Guide placement: DEGRADED / image quality: DEGRADED / M3B-LR3: PUBLISHED / SOL REVIEWED / generation influence: VERIFIED / result: OPTION_A_INCONCLUSIVE / Derived CLEAN Guide: RETAINED RESEARCH CANDIDATE / Figure-union masked ControlNet: SUPPORTED RESEARCH CANDIDATE / M3B-LR4: PUBLISHED / SOL REVIEWED / TECHNICAL PASS / LOCALITY_SUPPORTED / M3B-LR5: PUBLISHED / SOL REVIEWED / TECHNICAL PASS / CAST_MASKED_CONFLICT / M3B-LR5 key failure: HARD EFFECT-MASK BOUNDARY / QUALITY DEGRADED / M3B-LR6: PUBLISHED / SOL REVIEWED / TECHNICAL PASS / SOFT_MASK_CONFLICT (key finding: SOFTENING FIGURE EFFECT-MASK EDGE DID NOT REMOVE VISUAL BOUNDARY) / M3B-LR7: PUBLISHED / SOL REVIEWED / TECHNICAL PASS / EFFECT_MASK_INTERACTION_CONFIRMED / M3B-LR8: PUBLISHED / SOL REVIEWED / CORE_GLOBAL_QUALIFIED / M3B research qualification: CLOSED FOR CURRENT CLEAN-GLOBAL CANDIDATE / Production backend integration: COMPLETE / M3B-PI1: PUBLISHED / SOL REVIEWED / PI1_BACKEND_INTEGRATED / Automatic product routing: COMPLETE / M3B-PI2: PUBLISHED / SOL REVIEWED / PI2_AUTO_ROUTING_INTEGRATED / Browser closure: PI2_BROWSER_CLOSED / M3B-PI2-BC1: PUBLISHED / SOL REVIEWED / PI2_BROWSER_CLOSED / M3B-PC1: COMPLETED / M3B: PRODUCTION CLOSED / Manga integration readiness: READY FOR INTEGRATION DESIGN / Shared-shell implementation: NOT AUTHORIZED / Final Owner product review: DEFERRED / Active Card: NONE.

`GITHUB_ComfyUI.txt` はManga/H3を振り分けるCompatibility Routerへ変更した。
今回のnamespace整理は文書/navigationのみで、Manga runtime・workflow・schema・outputを変更していない。
今後はWeb GPT SOLが[新規チャット引き継ぎ](WEBGPT_SOL_LUNA_HANDOFF.md)からGitHubを監査し、
[Card Router](cards/README.md)と[現行プロトコル](plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md)に従って
必要な場合だけ次の限定Cardを発行する。LR1完了後の次Cardは自動発行しない。

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

- **完了Review Slice**: **M3B-LR1 — Rough Guide Foundation Long-Run Batch** — Stages 0-6 PASS / COMPLETED
  - **Finding A (fail-closed)**: invalid JSON / out-of-range page_index → ERROR status (fail-closed)。0 frames → pass-through PASS (legal)。
  - **Finding B (white gutter)**: comic_panels semantics: 白キャンバス + source paste inside frames + 黒枠線。Frame外 = 純白 gutter。
  - **Finding C (per-frame thickness)**: `border_thickness` per-frame honored、global `line_thickness` は fallback のみ。
  - **Finding D (area canonical)**: `area` key canonical。`shape` はlegacy fallback。`copyFramesFromScenes` area-only出力。JSON roundtrip後のdrift解消。
  - **Finding E (empty guide)**: `derive_panel_layout_spec_from_frames([])` → None (no fake full-frame)。
  - **BC1/OA1 technical truth**: `luna_browser_verdict=PASS`、`visual_evidence=PASS`、`milestone_acceptance=ACCEPTED_BY_DELEGATED_SOL`、`final_owner_product_review=DEFERRED`。
  - **Frame ID correction**: sequential `frame_1, frame_2...` (not timestamp+random — M3A Report記述誤り修正)。
  - **自動テスト**: Python 14/14 (M3A.1) + 7/7 (M3A) + 6/6 (M2B1 authoring) + 7/7 (M1.1 wiring) PASS、JS 19/19 PASS。V0-V4 pixel oracle PASS。
  - **BC1報告書**: [M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md](reports/M3A1_BC1_OWNER_LIVE_BROWSER_CLOSURE_REPORT.md)
  - **Browser evidence**: `docs/manga/verification/m3a1_browser/M3A1_BROWSER_CLOSURE_MANIFEST.json` と B1-B9 PNG evidence。
  - **OA1報告書**: [M3A1_OA1_OWNER_ACCEPTANCE_GATE_REPORT.md](reports/M3A1_OA1_OWNER_ACCEPTANCE_GATE_REPORT.md)
  - **LR1 semantics**: GuideはPage-owned。Scene / Visual Frame / CAST / Character Instanceとは別責務。
  - **LR1 boundary**: Generation influenceはNOT IMPLEMENTED、ControlNetはNOT ADDED。
  - **LR1報告書**: [M3B_LR1_ROUGH_GUIDE_FOUNDATION_LONG_RUN_REPORT.md](reports/M3B_LR1_ROUGH_GUIDE_FOUNDATION_LONG_RUN_REPORT.md)
  - **LR1 manifest**: [M3B_LR1_MANIFEST.json](verification/m3b_lr1/M3B_LR1_MANIFEST.json)

- **Latest published closeout**: [M3B-LR5 — CAST + Figure-Masked CLEAN Compatibility Research](cards/completed/M3B_LR5_CAST_MASKED_CLEAN_COMPATIBILITY_RESEARCH.md)。CAST compile 2件、Character masks 2件、4/4 queue、回帰、canonical no-GuideをPASS。視覚結果はCAST_MASKED_CONFLICT、HARD EFFECT-MASK BOUNDARY / QUALITY DEGRADED、Production integrationは未実施。
- **Latest completed closeout**: [M3B-LR6 — CAST Soft-Edge Figure Mask Compatibility Research](cards/completed/M3B_LR6_CAST_SOFT_EDGE_FIGURE_MASK_COMPATIBILITY_RESEARCH.md)。radius 16px SOFT mask、6/6 queue、live browser、回帰、canonical no-GuideをPASS。視覚結果はSOFT_MASK_CONFLICT、Production integrationは未実施。
- **Active Card**: NONE。M3B-LR6 publicationはLOCAL、Owner pushとSOL public reviewが必要。Final Owner product reviewはDEFERRED。次Cardは自動発行しない。
- 次Cardは自動発行しない。


---

## 6. 関連正本リンク
- 戦略SSOT: [ASTRA_MANGA_AUTHORING_MASTER_PLAN.md](plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md)
- UX詳細: [ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md](plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md)
- 資産棚卸し: [ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md](plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md)
- SOL/LUNA引き継ぎ: [WEBGPT_SOL_LUNA_HANDOFF.md](WEBGPT_SOL_LUNA_HANDOFF.md)
- 実行プロトコル: [ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md](plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md)
- 文書登録簿: [DOCUMENT_REGISTER.md](DOCUMENT_REGISTER.md)
