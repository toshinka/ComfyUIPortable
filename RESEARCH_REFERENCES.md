# RESEARCH_REFERENCES.md — 外部資産・参照情報

## 1. ComfyUI 本体
- **Repository**: [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **License**: GPL-3.0
- **参照内容**:
  - `folder_paths.py`, `utils/extra_config.py`: `extra_model_paths.yaml` による外部モデル共有アーキテクチャ。
  - `comfy.sd.load_lora_for_models`: 安全なLoRAパッチ適用API。
- **適用内容**:
  - `extra_model_paths.yaml` 経由での `E:\EasyReforge` 資産の非破壊共有。
  - `TegakiLoraPromptLoader` での標準ローディングAPI呼び出し。

---

## 2. ComfyUI-WildcardOrganizer (Phase 2 導入)
- **Repository**: [lokitsar/ComfyUI-WildcardOrganizer](https://github.com/lokitsar/ComfyUI-WildcardOrganizer)
- **License**: MIT
- **参照内容**:
  - WildcardファイルのWebUI探索、全文検索、内容プレビュー、プロンプトビルダー。
- **適用内容**:
  - EasyReforgeの192個のWildcard資産の検索・内容確認UXの劇的強化。Windowsジャンクション環境向けパッチ適用。

---

## 3. comfyui_manga_panel (Phase 2 調査・参照)
- **Repository**: [Tsubasa109/comfyui_manga_panel](https://github.com/Tsubasa109/comfyui_manga_panel)
- **License**: MIT
- **参照内容**:
  - Canvas上でのドラッグ矩形作成、移動、コーナーハンドルリサイズ、Crop/Composite処理。
- **適用内容**:
  - `TegakiMangaRegionEditor` のCanvasインタラクション設計の参考。

---

## 4. Nukun_ComfyUI_Nodes (Phase 2 調査・参照)
- **Repository**: [OnekoSL/Nukun_ComfyUI_Nodes](https://github.com/OnekoSL/Nukun_ComfyUI_Nodes)
- **License**: MIT
- **参照内容**:
  - Regional Rect Masks等のブラウザ側矩形エディタ、0〜1正規化座標系。
- **適用内容**:
  - 解像度非依存の正規化座標系および `REGION_SPEC` (v1) データ構造の設計。

---

## 5. 将来の独立GUI候補 (Phase 2 追補調査)
- **ComfyUI Native Subgraph**: [docs.comfy.org/interface/features/subgraph](https://docs.comfy.org/interface/features/subgraph)
- **Minimalistic Comfy Wrapper WebUI (MCWW)**: [light-and-ray/Minimalistic-Comfy-Wrapper-WebUI](https://github.com/light-and-ray/Minimalistic-Comfy-Wrapper-WebUI)
- **ComfyUI-RookieUI**: [rookiestar28/ComfyUI-RookieUI](https://github.com/rookiestar28/ComfyUI-RookieUI)
- **ViewComfy**: [ViewComfy/ViewComfy](https://github.com/ViewComfy/ViewComfy)
- **presentation-ComfyUI**: [niknah/presentation-ComfyUI](https://github.com/niknah/presentation-ComfyUI)
- **ComfyUI-OGN-ModelManager**: [ongnblog/ComfyUI-OGN-ModelManager](https://github.com/ongnblog/ComfyUI-OGN-ModelManager)
- **ComfyUI-Model-Manager**: [hayden-cn/ComfyUI-Model-Manager](https://github.com/hayden-cn/ComfyUI-Model-Manager)
- **適用方針**:
  - `REGION_SPEC` を独立したデータ契約とし、将来どのGUIとも疎結合に接続可能なアーキテクチャを確立。

---

## 6. ComfyUI-Impact-Pack
- **Repository**: [ltdrdata/ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- **License**: GPL-3.0
- **参照・適用内容**: Regional Sampler, Bounding Box Masking による領域制御基盤。

---

## 7. ComfyUI-Inspire-Pack
- **Repository**: [ltdrdata/ComfyUI-Inspire-Pack](https://github.com/ltdrdata/ComfyUI-Inspire-Pack)
- **License**: GPL-3.0
- **参照・適用内容**: `LORA_STACK` データ仕様、Regional LoRA、LoRA Block Weight。

---

## 8. comfyui-dynamicprompts
- **Repository**: [adieyal/comfyui-dynamicprompts](https://github.com/adieyal/comfyui-dynamicprompts)
- **License**: MIT
- **参照・適用内容**: WildcardManager、ワイルドカード共有および構文展開。

---

## 9. ComfyUI-Advanced-ControlNet
- **Repository**: [Kosinkadink/ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)
- **License**: GPL-3.0
- **参照・適用内容**: ControlNetステップスケジューリング（start_percent, end_percent）。
