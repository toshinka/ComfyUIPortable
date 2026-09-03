# CUSTOM_NODE_MANIFEST.md — 外部Custom Nodeコミット追跡マニフェスト

ComfyUIPortable環境（`ComfyUI/custom_nodes/`）に配備されている各Custom NodeのアップストリームリポジトリURL、固定Commit SHA、およびローカルパッチの適用状況一覧です。

---

## 漫画制作ワークフロー主要ノード

### 1. tegaki_manga_nodes (自作・正本管理)
- **種別**: ローカル開発（Junction接続）
- **Git正本**: `custom_nodes_custom/tegaki_manga_nodes`
- **Runtimeパス**: `ComfyUI/custom_nodes/tegaki_manga_nodes` (Junction)
- **状態**: Git追跡対象（本リポジトリのコミットと完全同期）
- **機能**: `TegakiLoraPromptLoader`, `TegakiLoraStackToPrompt`, `TegakiMangaRegionEditor`

### 2. ComfyUI-WildcardOrganizer (Phase 2 導入)
- **Repository**: `https://github.com/lokitsar/ComfyUI-WildcardOrganizer.git`
- **Commit SHA**: `34385650188bb8adc193b80e6a23c0d74f886211`
- **ローカルパッチ**: **APPLIED** (`patches/wildcard_organizer_windows_junction.patch`)
  - パッチ内容:
    1. Windows Junction環境におけるドライブレター跨ぎ時のKeyベースフォールバック (`_preview`)
    2. ComfyUIロード時の `PromptServer.instance` 安全性ガード
  - 検証スクリプト: `scripts/verify_wildcard_patch.py` (実行結果: `PATCH PRESENT`)

### 3. ComfyUI-Advanced-ControlNet
- **Repository**: `https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git`
- **Commit SHA**: `27a67fee80cf46c198b10588a5651f23d67d1e95`
- **ローカルパッチ**: なし (Clean)
- **用途**: `05_CONTROLNET_COMPOSITION.json` (ステップ制御・構図拘束)

### 4. ComfyUI-Impact-Pack
- **Repository**: `https://github.com/ltdrdata/ComfyUI-Impact-Pack.git`
- **Commit SHA**: `429d0159ad429e64d2b3916e6e7be9c22d025c3c`
- **ローカルパッチ**: なし (Clean)
- **用途**: `03_MANGA_REGIONAL_PROMPT.json`, `04_REGIONAL_LORA_EXPERIMENT.json` (領域分割サンプリング)

### 5. ComfyUI-Inspire-Pack
- **Repository**: `https://github.com/ltdrdata/ComfyUI-Inspire-Pack.git`
- **Commit SHA**: `d23db9aa544de9a6d4c609cb7005fa9e0d42031d`
- **ローカルパッチ**: なし (Clean)
- **用途**: `LORA_STACK` 連携・LoRA Block Weight制御

### 6. comfyui-dynamicprompts
- **Repository**: `https://github.com/adieyal/comfyui-dynamicprompts.git`
- **Commit SHA**: `3f2fff32358cf39e21b8b440ca87eac9a8e2bade`
- **ローカルパッチ**: なし (Clean)
- **用途**: EasyReforgeワイルドカード192件の構文展開

### 7. ComfyUI-Easy-Use
- **Repository**: `https://github.com/yolain/ComfyUI-Easy-Use`
- **Commit SHA**: `595e0738a9e3f8d0d9c4d875461b2d2c9e7559c7`
- **ローカルパッチ**: なし (Clean)

### 8. rgthree-comfy
- **Repository**: `https://github.com/rgthree/rgthree-comfy`
- **Commit SHA**: `6b76ee6f2c5a007710b5a16f97c94330d6ecc871`
- **ローカルパッチ**: なし (Clean)

### 9. ComfyUI-Manager
- **Repository**: `https://github.com/ltdrdata/ComfyUI-Manager.git`
- **Commit SHA**: `fe1193c0c8168904e32d814190ba7f2ba2ad7581`
- **ローカルパッチ**: なし (Clean)

### 10. ComfyUI-Custom-Scripts (Phase 3B.1.1 導入)
- **Repository**: `https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git`
- **Commit SHA**: `609f3afaa74b2f88ef9ce8d939626065e3247469`
- **ローカルパッチ**: なし (Clean)
- **用途**: 全プロンプト入力欄における Booru Tag Complete（Danbooru 14万タグ補完、LoRA/Embeddingオートコンプリート）

