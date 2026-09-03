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

## 2. ComfyUI-Impact-Pack
- **Repository**: [ltdrdata/ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)
- **License**: GPL-3.0
- **参照内容**:
  - Regional Sampler, Bounding Box Masking による領域制御。
- **適用内容**:
  - `workflows/03_MANGA_REGIONAL_PROMPT.json` および `04_REGIONAL_LORA_EXPERIMENT.json` の領域制御基盤。

---

## 3. ComfyUI-Inspire-Pack
- **Repository**: [ltdrdata/ComfyUI-Inspire-Pack](https://github.com/ltdrdata/ComfyUI-Inspire-Pack)
- **License**: GPL-3.0
- **参照内容**:
  - `LORA_STACK` データ仕様、Regional LoRA、LoRA Block Weight。
- **適用内容**:
  - `TegakiLoraPromptLoader` における `LORA_STACK` タプル互換出力の採用。

---

## 4. comfyui-dynamicprompts
- **Repository**: [adieyal/comfyui-dynamicprompts](https://github.com/adieyal/comfyui-dynamicprompts)
- **License**: MIT
- **参照内容**:
  - WildcardManager、JunctionによるWildcardsフォルダ参照、ランダムプロンプト生成構文。
- **適用内容**:
  - EasyReforgeの `sd-dynamic-prompts` ワイルドカード192件の共有および構文展開。

---

## 5. ComfyUI-Advanced-ControlNet
- **Repository**: [Kosinkadink/ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet)
- **License**: GPL-3.0
- **参照内容**:
  - ControlNetステップスケジューリング（start_percent, end_percent）。
- **適用内容**:
  - `workflows/05_CONTROLNET_COMPOSITION.json` での構図拘束制御。
