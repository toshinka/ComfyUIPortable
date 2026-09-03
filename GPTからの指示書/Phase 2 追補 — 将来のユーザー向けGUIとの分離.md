# Phase 2 追補 — 将来のユーザー向けGUIとの分離

今回作成する `Tegaki Manga Region Editor` は、将来的にComfyUIのノードグラフそのものをユーザーへ見せず、A1111 / Forgeのような制作向けGUIから操作することを予定しています。

そのため、Editorと生成Backendを過度に密結合しないでください。

将来的なGUI候補として最低限以下を研究対象として記録してください。

```text
ComfyUI Native Subgraph
https://docs.comfy.org/interface/features/subgraph

Minimalistic Comfy Wrapper WebUI
https://github.com/light-and-ray/Minimalistic-Comfy-Wrapper-WebUI

ComfyUI-RookieUI
https://github.com/rookiestar28/ComfyUI-RookieUI

ViewComfy
https://github.com/ViewComfy/ViewComfy

presentation-ComfyUI
https://github.com/niknah/presentation-ComfyUI
```

今回これらを本番導入する必要はありません。

## UI / Backend分離原則

Region Editorの正本状態はfrontend DOMそのものではなく、

```text
REGION_SPEC
```

として表現してください。

将来、

```text
Native ComfyUI
MCWW
独自Tegaki sidebar
独立Web frontend
```

のどこからでも同じREGION_SPECを生成・編集できる設計を目標とします。

つまり概念的には、

```text
User Interface
      ↓
REGION_SPEC
      ↓
Region Compiler
      ↓
ComfyUI Workflow
```

とします。

Region Editor frontendが存在しないと生成Backendまで成立しない設計は避けてください。

## Workflow側もUI公開を意識する

新しく作成するWorkflowでは、ユーザーが操作する値と内部処理を明確に分離してください。

例えば、

```text
USER INPUT
- Prompt
- Negative
- Seed
- Width / Height
- Region Spec
- Control Strength

INTERNAL
- Conditioning
- Masks
- MODEL patches
- Sampler routing
- VAE processing
```

と分類してください。

将来MCWW等からユーザー入力だけを抽出可能にするためです。

必要であればPrimitive / String等の入力Nodeを内部処理Nodeから分離してください。

ただし今回MCWW固有のタイトル記法等へWorkflowを依存させないでください。

## Subgraphについて

ComfyUI Native Subgraphは、内部配線を隠しつつwidgetを親へpromoteできるため有力です。

ただし現在もSubgraph / widget promotion周辺は発展中なので、今回のRegion EditorやRegion Compilerの正本データ構造をSubgraph固有仕様へ依存させないでください。

Phase 2完了後に比較検証します。

## Model / LoRA Browser

以下も将来UI候補として調査記録してください。

```text
ComfyUI-OGN-ModelManager
https://github.com/ongnblog/ComfyUI-OGN-ModelManager

ComfyUI-Model-Manager
https://github.com/hayden-cn/ComfyUI-Model-Manager
```

Checkpoint / LoRAを大量に利用するため、

```text
サムネイル
フォルダ分類
検索
説明・メモ
```

を持つA1111的Browserは有用です。

今回導入は必須ではありません。

Phase 2.5で実環境に適したものを比較して決定してください。

## Phase 2報告書への追加

`PHASE2_MRP_UI_REPORT.md` に、

```text
Future User UI Compatibility
```

という項目を追加し、

- REGION_SPECが外部UIから利用可能か
- Region EditorとBackendの分離状況
- Subgraph化可能性
- MCWW等で公開可能な入力値
- 独自UIが必要になる部分

を記録してください。