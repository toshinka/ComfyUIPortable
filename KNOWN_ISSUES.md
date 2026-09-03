# KNOWN_ISSUES.md — 既知の問題・制限事項

## 1. 04_REGIONAL_LORA_EXPERIMENT.json の接続状態 (EXPERIMENTAL / NOT YET REGIONAL)
- **現状**: `04_REGIONAL_LORA_EXPERIMENT.json` は2本のLoRAブランチを持つ構造として配置されていますが、コードレベル監査の結果、最終KSamplerには第1ブランチのMODELのみが接続されており、第2ブランチのMODEL/Conditioningが合流していません。
- **影響**: 現状は領域別LoRA（Regional LoRA）として完全には成立しておらず、実質的に単一LoRA生成となります。
- **対応方針**: Phase 2では安定基盤の維持を最優先とし、Phase 5の「疑似RLL（Impact RegionalSampler等を用いた領域別LoRA実験）」にて本格改修を行います。

---

## 2. 03_MANGA_REGIONAL_PROMPT.json の仕様
- **現状**: `03_MANGA_REGIONAL_PROMPT.json` は、`SolidMask` と `ConditioningSetMask` による左右2分割の固定ノード配線ワークフローです。
- **注意**: 視覚的なRegion Editorではありません。視覚的なコマ割り・Promptレイアウトは新規の `07_MANGA_REGION_EDITOR_UI_TEST.json` (`TegakiMangaRegionEditor`) をご利用ください。

---

## 3. Region Prompt内での <lora:...> 記法
- **現象**: `TegakiMangaRegionEditor` の各コマPrompt内に `<lora:name:weight>` を記述した場合、現段階のバックエンドではMODEL全体にLoRAが適用されます（KOMA 1にのみ効くわけではありません）。
- **対策**: ノード実行時にコンソールへ注意喚起ログを出力しています。局所LoRA適用は将来のPhase 5で実装予定です。

---

## 4. LoRAファイル名解決の競合
- **現象**: 3000個以上のLoRAが存在するため、別々のサブフォルダ（例: `Ani0H/hoge.safetensors` と `Style/hoge.safetensors`）に同名のファイルがある場合、ベースファイル名のみで指定すると先に見つかった方が適用されます。
- **回避策**: `TegakiLoraPromptLoader` は競合を検知した際にログ（コンソール）へ警告を出力します。

---

## 5. Windows Tritonの非対応
- **現象**: 一部のTriton依存拡張はWindowsネイティブではスキップされます。
- **影響**: 標準のPyTorch Attention / VAEデコードが使用されるため、画像の生成結果や品質には一切影響ありません。

---

## 6. ControlNetモデルの事前配置
- **現象**: `05_CONTROLNET_COMPOSITION.json` では汎用ControlNetノードを配置していますが、EasyReforge側のControlNetモデル名が一致しない場合はロードエラーになります。
- **対処**: ワークフローを開いた後、`ControlNetLoader` ノードのドロップダウンから所持しているモデルを選択してください。
