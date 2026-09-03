# KNOWN_ISSUES.md — 既知の問題・制限事項

## 1. LoRAファイル名解決の競合
- **現象**: 3000個以上のLoRAが存在するため、別々のサブフォルダ（例: `Ani0H/hoge.safetensors` と `Style/hoge.safetensors`）に同名のファイルがある場合、ベースファイル名のみで指定すると先に見つかった方が適用されます。
- **回避策**: `TegakiLoraPromptLoader` は競合を検知した際にログ（コンソール）へ警告を出力します。特定のフォルダのLoRAを明示したい場合は、将来的なサブパス指定記法 `<lora:subfolder/name:weight>` への対応を推奨します。

---

## 2. Windows Tritonの非対応
- **現象**: `KJNodes` の `PatchTritonVAE` など一部のTriton依存拡張はWindowsネイティブではスキップされます。
- **影響**: 標準のPyTorch Attention / VAEデコードが使用されるため、画像の生成結果や品質には一切影響ありません。

---

## 3. ControlNetモデルの事前配置
- **現象**: `05_CONTROLNET_COMPOSITION.json` では汎用ControlNetノードを配置していますが、EasyReforge側のControlNetモデル名（例: `controlnet_xl.safetensors`）がユーザーの所持モデルと一致しない場合、ロードエラーになります。
- **対処**: ワークフローを開いた後、`ControlNetLoader` ノードのドロップダウンから所持しているモデルを選択してください。
