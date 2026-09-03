# DEPENDENCIES.md — 環境・依存関係仕様

## 1. ホストシステム・ハードウェア
- **OS**: Windows 11 (64-bit)
- **CPU / RAM**: 64GB RAM
- **GPU**: NVIDIA GeForce RTX 4070 (VRAM 12GB)
- **CUDA Driver**: CUDA 13.0 対応

---

## 2. コアランタイム
- **Python**: 3.13.14 (tags/v3.13.14:fd17997) [Windows embeded 64-bit]
- **PyTorch**: 2.13.0+cu130
- **TorchVision**: 0.28.0+cu130
- **TorchAudio**: 2.11.0+cu130
- **ComfyUI**: v0.30.0 (Windows standalone portable)
- **comfyui-frontend-package**: 1.47.11

---

## 3. インストール済み Custom Nodes
| Node名 | リポジトリ / ソース | 概要・用途 |
|---|---|---|
| **tegaki_manga_nodes** | `custom_nodes_custom/` (ローカル独自開発) | `<lora:name:weight>` 構文パーサー & ローダー |
| **ComfyUI-Impact-Pack** | [ltdrdata/ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) | Regional Sampler, Mask制御, 顔/手検出補正 |
| **ComfyUI-Inspire-Pack** | [ltdrdata/ComfyUI-Inspire-Pack](https://github.com/ltdrdata/ComfyUI-Inspire-Pack) | Regional LoRA, LoRA Block Weight, LoRA Stack |
| **ComfyUI-Advanced-ControlNet** | [Kosinkadink/ComfyUI-Advanced-ControlNet](https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet) | ControlNetステップ・重みスケジューリング |
| **comfyui-dynamicprompts** | [adieyal/comfyui-dynamicprompts](https://github.com/adieyal/comfyui-dynamicprompts) | Wildcard展開 (`__tag__`) & 構文選択 (`{A\|B}`) |
| **ComfyUI-Manager** | [ltdrdata/ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager) | Custom Node / Model 管理 |
| **rgthree-comfy** | [rgthree/rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | ワークフロー制御・最適化ノード群 |
| **ComfyUI-Easy-Use** | [yolain/ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | 統合ローダー・ユーティリティ |

---

## 4. 追加インストールした主要Pythonパッケージ
- `dynamicprompts` (0.31.0)
- `webcolors` (25.10.0)
- `cachetools` (7.1.8)
- `dill` (0.4.1)
- `piexif` (1.1.3)
- `segment-anything` (1.0)
