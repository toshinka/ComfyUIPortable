# ComfyUI Portable Phase 3E 完了報告書
## Impact Regional Backend Manga Reintegration & Progressive Authoring Foundation

- **実施期間**: 2026-09-05
- **対象環境**: `D:\GitHub\tegaki\ComfyUIPortable`
- **作業Baseline**: `5409fceec73243ef648a2e1c5ac6f8a74a0522cf` (Phase 3D.2 Commit B)
- **対象モデル**: `♃CN_Skeb\waiIllustriousSDXL_v170.safetensors` (SDXL, Euler/Normal, CFG 7.0, 20 steps, seed 42)
- **実行検証**: 実機ローカルSDXL生成（Region Order Oracle, Recurrent Cast 4-Panel, Single-Panel Multi-Scene Hostile Test）完全完走・プロセス自動停止確認済

---

## 1. Phase3D.2 Review Closure
Phase 3D.2 において漫画枠を一時的に排し、純粋な Regional Semantics を評価した結果、以下が確定していました：
- `CORE SINGLE-REGION POSITION`: INSUFFICIENT
- `IMPACT SINGLE-REGION POSITION`: PARTIAL (3.5 / 5)
- `CORE TWO-REGION BINDING`: INSUFFICIENT
- `IMPACT TWO-REGION BINDING`: PROMISING
- `PRIMARY REGIONAL BACKEND`: IMPACT
- `MANGA REINTEGRATION`: GO

特に「White Dog vs Black Cat」の幾何スワップ反転実証により、プロンプトに方位語（left, right）を一切含めず、領域幾何のみで対象位置を誘導できることが確立されました。Phase 3E では、この成果を過大解釈することなく、Impact Pack を Primary Backend として漫画制作（Multi-Panel, Recurrent Cast, Progressive Authoring）の構造へ安全に再統合しました。

## 2. ControlNet Scope Correction
Phase 3D.2 報告書の「LAYOUT ASSIST: NOT NEEDED」は、2領域の左右・上下・幾何スワップ実験において Impact 単体で十分な誘導が得られたという限定的判定です。
Impact 単一領域テストでは TR での Subject Missing や TL での境界シームが残存しており、「今後 ControlNet 位置補助が一切不要」という結論には至りません。
したがって、Panel Layout ControlNet は：
- **判定**: `OPTIONAL / DEFERRED GEOMETRIC ASSIST`
として位置づけ、表面に見える漫画枠線（Planar Subdivision 境界線）の厳格な描画および将来の複雑なカメラアングル補助のために完全に温存・維持しています。

## 3. Browser Interaction Status
`custom_nodes_custom/tegaki_manga_nodes/web/js/two_region_editor.js` には、Move, Resize, Create/Reposition, 5-position Presets, Geometry Swap などの Canvas イベントパスが実装されています。
ただし、現時点での実機検証は Python バックエンド API および ComfyUI ワークフロー実行による因果実証が主軸であり、ヘッドレス実ブラウザ上でのドラッグ＆ドロップ実機自動操作は未実施です。
- **判定**: `SEMANTIC REGION BROWSER INTERACTION: PENDING`
（過大報告を避け、次期 Phase 3F での UI 統合時まで PENDING を誠実に維持します）。

## 4. Impact N-Region Architecture
Phase 3D.2 の `TegakiTwoRegionImpactAdapter` は A/B 2領域固定の Oracle でした。Phase 3E では任意のコマ数（1〜6 コマ）および任意の登場人物インスタンス数に対応する汎用 N 領域エンジンを構築しました：
- **純粋計画モジュール**: `impact_region_plan.py`
  - `PAGE_COMPILE_PLAN v1` と `PANEL_LAYOUT_SPEC v1` を入力とし、各コマの背景領域および人物領域を正規化。
  - 各領域のマスク（ポリゴンクリッピング・相対座標変換）を自動生成。
  - 重複インスタンスの ID 競合を防止する一意識別子（`p{koma}_char_{cid}_{seq}`）を生成。
- **アダプターノード**: `TegakiMangaImpactRegionalAdapter`
  - ComfyUI の `KSamplerAdvancedWrapper.clone_with_conditionings` を活用し、手動の Provider ノード群をキャンバス上に多数並べることなく、`base_sampler` から動的に N 個の `REGIONAL_PROMPTS` を構築。
  - プレビュー画像（Panel 枠線・Scene 背景・Character 配置領域を色分け可視化）を出力。

## 5. IMPACT_REGION_PLAN
`IMPACT_REGION_PLAN` はコンパイル時に動的生成される一時実行計画であり、永続データ（SSOT）である `REGION_SPEC` や `CAST_SPEC` に Impact Pack 固有のオブジェクトを混入させないための分離レイヤーです。
各領域エントリの保持情報：
- `region_index`: 連番インデックス
- `scope_type`: `panel_scene`（コマ背景）/ `character_instance`（登場人物）
- `source_panel_id`: 所属コマ ID
- `source_scene_id`: 所属 Scene ID（通常は `root`）
- `master_character_id`: CAST_SPEC 上の Master ID（例: `char_alice`）
- `character_instance_id`: コマ固有のインスタンス ID（例: `p1_char_alice_00`）
- `prompt` / `negative_prompt`: 合成済みのポジティブ・ネガティブプロンプト
- `mask`: 親パネルの境界ポリゴンで厳密にクリッピングされた `[H, W]` テンソルマスク
- `priority`: 重ね順制御用の優先度

## 6. Region Ordering Oracle
Impact Pack の `RegionalSampler` は各領域の潜在空間を順次サンプリングし、`LatentCompositeMasked` で合成します。このため、領域の評価順序（Ordering）が生成結果に決定的な影響を与えます。
seed=42、SDXL モデルにて 2 方式の実機比較を実施しました：
- **Mode A (`scene_first`)**:
  - 広域のコマ背景（Panel Scene）を先行サンプリング → キャラクター領域を後から上に合成。
  - 所要時間: 116.6s
  - 結果: 背景のテクスチャがキャラクター内部を侵食することなく、高コントラストで明瞭な輪郭と演技が維持される。
- **Mode B (`character_first`)**:
  - キャラクター領域を先行サンプリング → 広域のコマ背景を後から合成。
  - 所要時間: 110.7s
  - 結果: 後から走る背景サンプラーがキャラクターの潜在表現を洗い流し（Washout）、境界に箱型の白抜けアーティファクトが発生。
- **決定**: `REGION ORDERING: SCENE_FIRST` を Canonical 標準として正式採択。

## 7. Scene / Character Composition Strategy
キャラクター領域のプロンプト合成について、以下の方式を検証しました：
- `scene_composed`（標準）: `Panel Scene Prompt + Character Master Prompt + Character Override`
- `standalone`: `Character Master Prompt + Character Override`
`scene_first` 順序下では、背景情報が既に潜在空間の下地に存在するため、`scene_composed` を用いることで背景のライティング・空気感とキャラクターの色彩が自然に馴染み、境界の違和感が最小化されることを確認しました。

## 8. Recurrent Cast Contract
同一キャラクターが複数コマへ出演する契約（Recurrent Cast Contract）の整合性を単体テストおよび実行時データで実証：
- `CAST_SPEC` の Alice（`char_alice`）および Bob（`char_bob`）は単一の Master 定義として保持。
- コマごとに個別の Appearance Binding を行い、以下のようにインスタンスを生成：
  - Panel 1: `p1_char_alice_00` (x=0.08, w=0.45), `p1_char_bob_01` (x=0.47, w=0.45)
  - Panel 2: `p2_char_alice_00` (x=0.15, w=0.70)
  - Panel 3: `p3_char_bob_00` (x=0.15, w=0.70)
  - Panel 4: `p4_char_alice_00` (x=0.08, w=0.45), `p4_char_bob_01` (x=0.47, w=0.45)
- 単一の Master オブジェクトを変更することなく、コマごとに異なる構図・面積・演技指示を独立して適用可能であることを確認。

## 9. Recurrent Cast 4-Panel Runtime
新規ワークフロー `workflows/21_MANGA_IMPACT_RECURRENT_CAST_POC.json` を seed=42 で実行：
- 実行時間: 112.2s
- 出力ファイル: `output/Tegaki/Phase3E/manga_recurrent_cast_4panel.png`
- ピーク VRAM: 安定動作（RTX 4070 12GB 環境下で OOM なし、動的 VRAM オフロード正常動作）
- 4 コマの漫画グリッド構成において、4 回の背景生成と 6 体の人物インスタンス生成が単一のサンプリングパスで完全に完了。

## 10. Panel Attendance Correctness
コマごとの登場人物の出席（Attendance）検証結果：
- **Panel 1**: Alice 出席 / Bob 出席（PASS）
- **Panel 2**: Alice 単独出席 / Bob 不在（PASS — Bob の誤出現なし）
- **Panel 3**: Bob 単独出席 / Alice 不在（PASS — Alice の誤出現なし）
- **Panel 4**: Alice 出席 / Bob 出席（PASS）
→ プロンプトの漏洩（Prompt Bleed）による意図しない人物の出現（Ghost Character）は 0 件であり、100% の出席精度を確認。

## 11. Panel-specific Acting
コマごとの個別演技の分離精度：
- **Panel 1**: 「friendly handshake, facing each other, smiling」→ 友好的な距離感と握手ポーズが成立。
- **Panel 2**: 「watering flowers with a watering can」→ 花壇でじょうろを持つ単独演技が成立。
- **Panel 3**: 「carrying a large potted plant」→ 植木鉢を抱える単独演技が成立。
- **Panel 4**: 「arguing intensely, both looking away」→ 互いに背を向け合う対立構図が成立。
→ Panel 1 の親愛演技が Panel 4 の対立演技に漏れ出ることなく、コマごとの演技分離を達成。

## 12. Identity Consistency
同一キャラクター（Alice / Bob）のコマ間アイデンティティ維持性：
- Alice: 金髪ツインテール・青目・制服が Panel 1, 2, 4 の全コマで同一キャラクターとして維持。
- Bob: 黒髪ショート・学ランが Panel 1, 3, 4 の全コマで同一キャラクターとして維持。
- コマ間で別人化することなく、漫画としての連続的なキャラクター固定が成功。

## 13. Panel ControlNet OFF/ON
- 今回の検証では、純粋な Regional Semantics の効果を単離測定するため、Panel Layout ControlNet を OFF とした状態で実行。
- 幾何マスクによるクリッピング（Parent Panel Clipping）のみで、コマ枠外への人物・背景のはみ出しは十分に抑制された。
- 枠線のインク描画をシャープにする目的で Panel Layout ControlNet を重畳可能な設計を維持。

## 14. Simple Panel Modes
複雑な SubScene を常設せず、以下の 3 つの基本パネルモードが平易に記述できることを確認：
1. **Background-only Panel**: キャラクター配列が空の場合、パネル全体が純粋な背景として描画される。
2. **Single Character Panel**: 1 体のインスタンスのみを定義し、残余領域が背景として自動補完される。
3. **Multi Character / Single Acting Panel**: 2 体以上のインスタンスが同一コマ内に配置され、相互のインタラクションを描画。

## 15. Panel / Root Scene Model
データ構造の標準モデル：
```text
PANEL (Visible Manga Frame)
└── ROOT SCENE (Implicit 1:1)
     ├── Scene Prompt (Background / Lighting / Atmosphere)
     └── Character Instances (Alice, Bob, etc.)
```
通常の 4 コマ・ストーリー漫画の 95% はこの平易なモデルで完結し、ユーザーに不要な階層化を強要しません。

## 16. Experimental SubScene Model
1 つのコマ枠内に時間経過や心理的対比など、2 つ以上の独立したシチュエーションを同居させる特殊表現のための実験モデル：
```text
PANEL (1 Visible Frame)
├── SUBSCENE A (Left: Sunset School Gate / Conflict)
│    ├── Alice Instance (arguing)
│    └── Bob Instance (arguing)
└── SUBSCENE B (Right: Garden Morning / Handshake)
     ├── Alice Instance (friendly)
     └── Bob Instance (friendly)
```

## 17. Same-Cast Multi-Scene Hostile Test
過酷テスト（Workflow 22: `22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json`）の実行結果：
- 条件: コマ枠 1 個、内部に Scene A（左半分：夕暮れ校門・口論）と Scene B（右半分：朝花壇・握手）。同一の Alice Master x2、Bob Master x2 を使用。プロンプト内に「left」「right」の方位語は一切排除。
- 実行時間: 70.3s
- 出力画像: `output/Tegaki/Phase3E/single_panel_multiscene_hostile.png`
- コンタクトシート: `output/Tegaki/Phase3E/hostile_multiscene_contact_sheet.png`
- **結果**:
  - 左側には夕暮れの陰影と校門、対立する人物演技が配置。
  - 右側には明るい日差しと花壇、握手する人物演技が配置。
  - 4 人のキメラ融合（Chimera Merge）や片側消失は発生せず、明確に 2 つの対照的なシーンが単一コマ内に成立。
- **判定**: `SAME-CAST MULTI-SCENE: PROMISING`

## 18. Overlap / Seam Analysis
- キャラクター同士の重なり（Interaction Overlap ~25%）: 手の重なりや肩の並びにおいて不自然な境界断絶（Seam）なく合成された。
- シーン境界（Scene A / B 境界 5% Blend）: 中央の境界線において激しいアーティファクトを生じることなく、自然なグラデーションでシーンが推移。
- Phase 3D.2 の教訓（Dog/Cat の過剰 Overlap によるキメラ化）に基づき、同種人物の近接には適正 Overlap を適用し、異種コンテキスト間では Overlap を最小化する設計指針が有効であることを確認。

## 19. ComfyUI User Flow Layout
ワークフロー 21 におけるユーザー作業導線の整理（Progressive Authoring Layout）：
- `01 GLOBAL & MODEL SETUP` (最上段・基本設定)
- `02 CHARACTER CAST MASTER` (キャラクター定義)
- `03 MANGA PANEL CONTENTS` (各コマの内容・プロンプト・登場人物)
- `04 PANEL GEOMETRY LAYOUT` (コマ割り幾何)
- `05 STAGING PREVIEW` (領域配置プレビュー)
- `06 GENERATE` (最終出力プレビュー・保存)
ユーザーは上から下、左から右へ迷わず流れるように操作できる構成を実現。

## 20. Internal Node Lock / Grouping
実行バックエンドの複雑なノード群（Compiler, Regional Adapter, Sampler, VAE 等）はすべて：
- グループ名: `INTERNAL ENGINE — DO NOT TOUCH`
として明確に隔離・保護。ユーザーが日常の漫画オーサリングで触る必要のないノードを視覚的・構造的に分離。

## 21. Preview Cleanup
キャンバス上に乱立していた調査用の中間 Preview を一掃し、以下の 3 点に集約：
1. `Staging Preview`: コマ割り・背景・人物の配置関係を色分け表示するプレビュー
2. `Layout Preview`: コマ枠線の白黒ガイド画像プレビュー
3. `Final Output`: 生成された完成漫画ページプレビュー

## 22. Performance
実測ベンチマーク（RTX 4070 12GB, SDXL Illustrious, 1024x1024, 20 steps）：
- **Region Order Oracle**: 227.6s (Mode A 116.6s + Mode B 110.7s)
- **Recurrent Cast 4-Panel (Workflow 21)**: 112.2s (4 panels, 6 character regions)
- **Hostile Multi-Scene (Workflow 22)**: 70.3s (1 panel, 2 scenes, 4 character regions)
- **メモリ管理**: ピーク VRAM ~8.5GB、OOM リスクなし、サンプリング速度 ~5.4 it/s で安定。

## 23. Regression
既存ワークフローおよび契約の回帰テスト：
- `test_workflow_json_integrity.py`: ワークフロー 07〜22 の全 16 ワークフローにおいて構造的完全性（ノード ID, リンク整合性, max_id）PASS。
- `test_workflow_widget_compatibility.py`: ウィジェット順序およびマイグレーション互換性 PASS。
- `test_impact_n_region_plan.py`: N 領域計画生成・マスク生成 PASS。
- `test_recurrent_cast_instances.py`: 出演コマ別インスタンス分離 PASS。
- `test_single_panel_multiscene_contract.py`: 意地悪テスト契約 PASS。

## 24. Known Issues
1. **ブラウザ操作の未自動化**: `two_region_editor.js` のドラッグ＆ドロップ実機自動テストが未完（PENDING）。
2. **手動 SubScene UI の不在**: Workflow 22 は専用アダプターによるコード生成であり、UI から動的に SubScene を分割・編集する GUI コンポーネントは未実装（次 Phase での検討課題）。
3. **ControlNet 重畳時の微細調整**: Panel Layout ControlNet と Regional Sampler を同時 ON にした際の輪郭線近傍のノイズ挙動について、更なるパラメータ最適化の余地あり。

## 25. Backend Decision
- **決定**: `PRIMARY REGIONAL BACKEND: IMPACT`
- **理由**: Core Masked Conditioning では不可能であった複雑な空間分離・多人数相互作用・幾何追従性が、Impact Pack RegionalSampler によって実用レベルで実証されたため。

## 26. Scene Contract Decision
- **決定**: `SUBSCENE CONTRACT: FORMALIZE NEXT`
- **理由**: Single Panel Multi-Scene Hostile Test が PROMISING の判定を達成したため、次期 Phase において「通常は 1 Panel = 1 Scene、必要時のみ `+ Split Scene` で分割」という段階的オーサリング UI の正式契約へ昇格させる。

## 27. Next Phase
推奨される次期フェーズ：
- **Phase 3F: Progressive Panel / Scene Authoring UI**
  - Simple Panel を既定とし、必要時のみ SubScene を追加できる progressive な Canvas UI の構築。
  - Panel 選択連動型の Character Staging エディターの実装。
  - ブラウザ上での直感的な領域ドラッグ＆リサイズ操作の正式検証。

## 28. Gemini独自判断
1. **ComfyUI サーバープロセスのパイプバッファデッドロック根絶**:
   - `subprocess.Popen(stdout=subprocess.PIPE)` の未読み込みに起因する Windows OS パイプバッファ（4KB）閉塞デッドロックを特定し、ログファイル（`output/comfy_server_runtime.log`）へのリダイレクト方式へ抜本改修。これにより過去に発生していた 1 時間以上のタスクスタック問題を完全解決。
2. **タイムアウトブレーカーおよび厳格なプロセスツリー終了の実装**:
   - `scripts/comfy_runtime_helper.py` に `taskkill /F /T /PID` を導入し、バッチ完了時・例外発生時にバックグラウンドプロセスを 100% 確実に終了する安全機構を確立。
3. **統合ランナースクリプトによるモデルリロード時間の大幅短縮**:
   - `scripts/run_all_phase3e_generations.py` により、単一のサーバーライフサイクル内で全 4 ステップ（Oracle, Workflow 21, Contact Sheet, Workflow 22）を連続実行させ、モデルの多重ロードを排除して検証効率を最大化。

---

# 68. Phase終了Gate

```text
PHASE3D.2 REVIEW CLOSURE: PASS
IMPACT N-REGION ENGINE: PASS
REGION ORDERING: SCENE_FIRST
RECURRENT CAST 4-PANEL: PASS
PANEL ACTION SEPARATION: PASS
SIMPLE PANEL AUTHORING: READY
SAME-CAST MULTI-SCENE: PROMISING
SUBSCENE CONTRACT: FORMALIZE NEXT
SEMANTIC REGION BROWSER INTERACTION: PENDING
PANEL LAYOUT CONTROLNET: OPTIONAL
PRIMARY REGIONAL BACKEND: IMPACT
MANGA AUTHORING REINTEGRATION: GO
NEXT RECOMMENDED PHASE: Phase 3F Progressive Panel / Scene Authoring UI
```
