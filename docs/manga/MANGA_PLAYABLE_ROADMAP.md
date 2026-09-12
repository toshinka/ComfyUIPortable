# TEGAKI MANGA — PLAYABLE ROADMAP

作成: 2026-09-13 JST / ASTRA INITIAL ARCHITECTURE PASS
状態: DESIGN COMPLETE / implementation NOT STARTED / Publication LOCAL
監査baseline: `90cbf7de141118708ca1ddc66ee5d7c484fb54cb`（開始時main clean、fetch後origin/main一致）。
作業branch: `codex/manga-playable`、worktree: `D:/GitHub/tegaki-manga-playable`。
この文書が今回の生成architecture・roadmap・最初のCardの唯一の正本。既存Authoringの完了判定、過去report、root STATUSの別作業を更新しない。過去のshared-shell/supervisor提案は今回の実装指示ではない。

今回の証拠はlocal source auditと文書検査のみ。モデルdownload、サービス起動、GPU生成、Browser操作、Owner受入、pushは未実施。以前のWindows lifecycle検証はユーザー提供の前提として維持し、今回再検証済みとはしない。H3添付画像はこの会話に実画像がないため、指定された文章の階層とmainのH3 CSSを参照した。

## 1. Current architecture map

以下のpathは特記なければComfyUIPortable相対。現行sourceを読んだ範囲と将来提案を区別する。

| 層 | 実在component / 観測 |
|---|---|
| Standalone entry | `manga/app/index.html` のinline moduleがStore、Session、canvas renderer、backend clientを組み立てる。現actionはPrepare Standard Draft |
| Authoring authority | `manga/app/src/state/authoring_store.js`、`domain/authoring_document.js`、`domain/authoring_ops.js`。Document 1.0.0をclone/validateして編集。Scene、Frame、Guide、CAST、Instance、Figureは既存責務 |
| Session / canvas | `state/session_state.js`は選択・tab・viewportのみ。`view/canvas_renderer.js`はauthoring表示。生成Previewをこの保存/編集正本へ押し込まない |
| Backend adapter | 実在pathは`manga/app/src/adapters/manga_backend_client.js`。ユーザー例の`manga/adapters`を新たに作らない。queue有効形状＋exact `TegakiMinimumHandSceneEditor` nodeで判定。prepare前後queue検査、`generationTriggered:false` |
| Workspace server | `manga/service/manga_workspace_server.mjs`、8191、依存なしNode HTTP。loopback backend、限定proxy allowlist、Guide upload。現在`/prompt`、history、viewはallowlist外 |
| Runtime | `manga/service/manga_domain_runtime.mjs`、8189/8191、120000ms startup、保持ChildProcessとownershipによるstart/stop/restart。spawnは`--output-directory output/Tegaki`。モデル設定追加flagがあると仮定しない |
| Prepare API | `custom_nodes_custom/tegaki_manga_nodes/product_generation_api.py`はdocument必須、routerへ委譲しgraphを返すだけ。checkpoint選択はHTTP入力にない |
| Existing graph | `product_generation_router.py`はSTANDARD_NO_GUIDE / GUIDED_CLEAN_GLOBAL。checkpoint固定`♃CN_Skeb\\waiIllustriousSDXL_v170.safetensors`、20 steps / CFG7 / euler / normal。Frame overlayあり。任意basic txt2imgと同一ではない |
| Native Manga UI | `web/js/minimum_hand_scene_editor.js`はprepare後`api.queuePrompt`を呼ぶ。Standaloneの非生成契約と混同禁止 |
| Regional compiler | `authoring_execution_bridge.py`、`scene_compiler.py`、`conditioning_builder.py`、`mask_builder.py`。global/panel/local/character positive・negativeをmasked conditioningへ。Impact経路は`manga_impact_regional_adapter.py`と`impact_region_plan.py` |
| Guide generation | `generation_guide_bridge.py`、`product_generation_router.py`、`frame_overlay.py`。現行GuidedはFigure由来CLEAN global guide＋core ControlNetApplyAdvanced。RAW guide送信やFigure effect maskではない |
| Models / extensions | `configs/extra_model_paths.yaml`は外部checkpoint/LoRA/ControlNet等の参照設定。ComfyUI core、Impact、Inspire、Advanced-ControlNet、Easy-Use等を現物確認。配置はimport成功・稼働証明ではない |

変更後の最小構造:

```text
MANGA Generate UI (8191) → Manga generation service (same workspace process)
  → bounded capability / compile API on Manga backend (8189)
  → service-owned submit to /prompt → prompt_id → /history/{id} → validated output
MANGA Authoring → existing AuthoringStore → existing prepare-only path (unchanged)
H3 (8188/8190) remains independent; navigation links only
```

Browserから任意graphやbackend URLをsubmitさせない。小さな生成module追加と既存serverのroute接続で実現し、共通supervisor、別framework、汎用job platformは作らない。

## 2. Reusable existing assets

- AuthoringStore、操作・roundtripテスト、Guide assetのbounded upload検証。Generateから明示snapshotを読み取るだけで既存編集フローを保護する。
- Manga lifecycleのidentity/ownership、queue failureをIDLEと捏造しないadapter方針。接続READYとgeneration capability READYを別表示にする。
- ComfyUI `CheckpointLoaderSimple → CLIPTextEncode(positive/negative) → EmptyLatentImage → KSampler → VAEDecode → SaveImage`をPLAY1の最小graphにする。必要時のみordered LoraLoaderをMODEL/CLIPの両方へ接続。
- 既存authoring compiler、masked conditioning、Frame overlayをPLAY4で採用。既存STANDARD/GUIDED workflowは回帰fixtureとして保持。
- Guide bridge＋core ControlNetApplyAdvancedをPLAY3の一経路として再利用。既存production boundaryのstrength 0.75/start 0/end 1は既存routeの値であり、新basicモードへ無断適用しない。
- ReForgeのsampler/schedulerとextra network parsingは仕様比較資料。ローカルsourceをauditし、実行やコピー移植は行っていない。

## 3. What should NOT be reused

- 固定checkpoint、固定profileの自動LoRA、無言parameter fallback。`generation_profile.py`のreference/fast_draft_12は過去profileであり、Create入力を上書きする権限を持たない。
- `lora_loader.py`の曖昧一致→先頭採用、部分一致、missingでもcontinueしてタグ除去する挙動。PLAY1にはstrict resolver/compilerを新設し、旧nodeは変更しない。
- 既存clientの`parseInt(seed) || 42`、index側の`seed || 42`は0を失う。新経路では厳密検証し、旧prepare修正を初回Cardに混ぜない。
- `EasyReforgeExtension/scripts/manga_prompter.py`のGradio/global wiring、`manga_attention.py`のForge ModelPatcher hookをComfyUIへコピーしない。`manga_spatial_engine.py`のexclusive/overlap maskは比較資料に限る。
- `RegionalLoRALab/scripts/regional_lora_lab.py`はControlNet OFF等を要求する研究経路で、通常LoRAタグをstripする。製品loaderとして採用しない。
- Advanced-ControlNet、Impact regional samplerをPLAY1の必須依存にしない。既存MASK研究の境界アーティファクトを解決済み扱いしない。
- H3 runtime、timeline、job state、server、history、preview所有を共有しない。H3 worktreeと外部ReForgeはread-only境界の外へ出ない。

## 4. H3-inspired Manga GUI layout

Top navigationはTEGAKIの下に明確なengine group: `H3 [Video | Still | Prep/Edit]` と `MANGA [Generate | Authoring]`。Mangaは既存paletteに整合する別accentとgroup labelを持ち、色だけで識別させない。H3 linkはnavigationのみで起動・停止を起こさない。

Wideは左に大きなResult Preview、上にcompact statusとGenerate、右にCreate。右はviewport内でscrollでき、末尾からpage scrollへ自然に移って下のQueue/Historyを表示。scroll trapを作らない。Previewの寸法はCreate accordion開閉で揺らさない。

Create順: BASIC（Checkpoint、Prompt、Negative、Resolution）、GENERATION（Sampler、Scheduler、Steps、CFG、Seed）、MANGA CONTROLS（後続phaseのMRP、ControlNet、CAST/Reference）、ADVANCED（LoRA helper、将来Hires）。PLAY1で未実装の操作を有効に見せない。manual LoRA textはPromptで常に入力可能。

狭幅ではPreview→Create→Queue/Historyの一列。Generateへkeyboardで到達可能、busy/errorはテキスト併記、既存結果をfailureで消さない。Authoring tabは既存workspaceを維持し、Generate切替でdocument/sessionをresetしない。H3のpixel copyやbranding設計は行わない。

## 5. Stable Diffusion basic generation contract

PLAY1 completeで一枚txt2imgを実際に生成し、実結果を表示する。authoring documentは不要。batch size/count=1、denoise=1、hiresなし、MRP/CN/IPAdapterなし。任意checkpoint選択と手動prompt/negative/parametersがgraphへ忠実に入る。

提案DTO `MangaGenerationRequest v1`は実行要求でありAuthoring schemaではない。fields: request_id、mode=txt2img、checkpoint_id、positive_raw、negative_raw、sampler_id、scheduler_id、steps、cfg、width、height、seed_requested。server compileでeffective seed、resolved LoRA list、clean conditioning text、capability revision、graph digestを返す。未知field/不正typeは拒否。設定変更後の古いcompile結果をsubmitしない。

新API案: `GET /api/manga/generation/capabilities`、`POST /api/manga/generation/compile`、後続`POST /api/manga/generation/jobs`、`GET /api/manga/generation/jobs/{id}`、`GET /api/manga/generation/jobs/{id}/result`。prefixは提案で既存route重複をCard開始時に再検索。backend側は`/tegaki/manga/generation/capabilities`と`/compile-basic`を追加し、既存`/prepare`の意味を変えない。

## 6. Checkpoint contract

serverがfolder_paths/CheckpointLoaderSimple capabilityを列挙し、catalog IDをbackend相対nameへ対応づける。browserの絶対path、drive、UNC、URL、traversal入力を認めない。model listは稼働backendが最終authority。設定yamlの存在をcatalog populatedと誤認しない。

Illustrious/SDXL互換は既知metadataまたは検証済みcatalog属性で表示する。名前だけで互換確定しない。unknown familyは未確認と表示し、初回live gateで選んだ一modelを確認する。checkpoint未選択・消失・権限不足・incompatibleは入力値を保持してunavailable、submitを拒否。自動先頭選択/別model fallbackなし。

## 7. Prompt / Negative contract

raw文字列を改行・Unicode・manualタグ込みで保持し、historyにも保存。空negativeは合法、空positiveも勝手な補完をしない。PLAY1はComfyUI CLIP encoding semanticsで、A1111のBREAK、AND、schedule、embedding、extension記法の完全互換は主張しない。

recognized LoRAだけstrictにcompileしてeffective textを別に作る。未知extra-network tag、不正LoRA tagは明示unsupportedとして生成を止め、原文を残す。negative内LoRAもpositiveの後に同じglobal MODEL/CLIPへ適用する契約を表示し、negative専用LoRAではないと明確化。将来regional LoRAとは別責務。

## 8. Sampler / Scheduler capability strategy

分類はこのlocal snapshotのsource-level presence。NATIVE_AVAILABLEはcore sourceあり、PORTABLE_EXTENSION_AVAILABLEは配置extension sourceあり、REFORGE_ONLYは調査Portableに同名実装が見つからずReForgeで確認、REQUIRES_PORTは差分adapter/移植が必要と判明、UNKNOWNは同等性未確定。ロード成功や画像品質を保証しない。

| 要求combination | 分類 | source根拠・不足 |
|---|---|---|
| Euler SMEA dy + SGM Uniform | REFORGE_ONLY | ReForge exact labelは`Euler SMEA Dy` / `sample_euler_smea_dy`。scheduler `sgm_uniform`はComfy core NATIVE_AVAILABLE。sampler未発見 |
| Euler Negative + Simple | REFORGE_ONLY | ReForge `sample_euler_negative`。Comfy `simple`はNATIVE_AVAILABLE、Negative sampler未発見 |
| DPM2 + Phi | REFORGE_ONLY | Comfy `dpm_2`はNATIVE_AVAILABLE、ReForge `phi`は確認、Portable Phi未発見。DPM2のdiscard-next-to-last-sigma差も比較が必要 |
| Euler Negative family + AYS 11 | REQUIRES_PORT | ReForge Negative / Negative Dyと`align_your_steps_11`。Portable AYS SDXLは関連資産だがstep/sigma array/terminal zero規則が異なり同名代替不可 |
| Euler + Cosine | REFORGE_ONLY | Comfy `euler`はNATIVE_AVAILABLE、ReForge `cosine`確認、Portable同名scheduler未発見 |
| Euler Negative + Invcosinusoidal SF | REFORGE_ONLY | ReForge `invcosinusoidal_sf`とNegativeを確認、Portable該当実装未発見 |
| AYS GITS（sampler未指定） | REQUIRES_PORT | ReForge `align_your_steps_GITS`は固定SDXL table＋補間。Comfy core GITSSchedulerとImpact GITS[coeff=1.2]は関連実装だが同等ではない。pairとしてのsamplerはUNKNOWN |
| AYS Custom（sampler未指定） | REQUIRES_PORT | ReForge `align_your_steps_custom`は設定由来sigma list。Portableへ値・検証・記録のadapterが必要。利用者のcustom listとpair samplerはUNKNOWN |

Exact inspected sources: `ComfyUI/comfy/samplers.py` KSampler lists/handlers、`ComfyUI/comfy_extras/nodes_align_your_steps.py`、`nodes_gits.py`（探索）、Impact `modules/impact/impact_sampling.py`・`core.py`（登録探索）、Inspire `inspire/libs/common.py`（登録探索）、Easy-Use `py/config.py`（登録探索）。外部ReForge `modules/sd_samplers_kdiffusion.py`、`sd_schedulers.py`。標準KSampler schedulerはsimple/sgm_uniform/karras/exponential/ddim_uniform/beta/normal/linear_quadratic/kl_optimal。AYS/GITSの別nodeをそのままKSampler dropdownへ足さない。

初期UIはbackend object_infoで確認したcore IDとcompilerの対応intersectionを提示。初期検証pairはeuler+normal、追加候補euler+sgm_uniformとeuler+simple。これは利用者が明示選択する別pairで、上記要求pairの代替扱いではない。backend再起動やcatalog revision変更時は再検証し、消えた選択値を保持する。

PLAY-S1（PLAY1完了後、PLAY2とは独立）の順: S1a Euler Negative+SimpleとSMEA Dy+SGM Uniform、S1b DPM2+PhiとNegative family+AYS11、S1c Cosine/Invcosinusoidal SF/GITS/Custom。各Cardでsource license、sampler update式、sigma length/terminal zero、step解釈、denoise、RNG/noise/device/dtypeを比較。CPU sigma/step trace→限定GPU→Owner比較を通してからexact labelを解放。Comfy core global list monkeypatchはしない。未解決pairはdisabledのまま。

## 9. Steps / CFG / Seed / Resolution contract

PLAY1 product bounds: steps整数1..100、CFG有限0..30、width/height整数256..2048かつ8の倍数、総pixel数<=2097152。backend許容値とのintersectionを使用。範囲外は拒否し、丸め・clampで黙って変更しない。これは初期製品上限で、GPU実行可能性の保証ではない。

Seedはdecimal string `-1`または0..4294967295。`-1`だけserverが一度random resolveし、0も厳密保持。再試行で勝手にseedを振り直さない。requested/effectiveを併記。拡張64bitは後続Cardで安全なserializationを決める。固定seedもbackend/version/hardware差でpixel同一を保証しない。

## 10. LoRA strategy

PLAY1に複数`<lora:name:weight>`を含める。元のPLAY2へ全LoRAを送る案はfirst playableの要望を満たさないため変更。weightは有限-4..4、初期対応は単一weightをMODEL/CLIP両方へ適用。四要素やnamed te/unet/dyn、block-weight等はunsupportedと明示拒否し原文保持。

外部`modules/extra_networks.py`はtagをparseしてextra dataに集約し、`extensions-builtin/Lora/extra_networks_lora.py`はnames/te/unet/dyn listsを`networks.load_networks`へ渡す。ReForge追加weightの順序はTE→UNetで、Tegaki旧nodeのmodel→clipと異なる。拡張構文の無批判流用は禁止。

strict resolutionはexact catalog ID優先、拡張子省略/ basenameは一意の場合のみ。未知/曖昧/重複resolved IDは理由を返して全体拒否し、部分適用しない。複数異なるLoRAはpositive出現順→negative出現順にchainし、全CLIPTextEncodeへpatch済みCLIPを渡す。resolved name・weight・順序をhistoryに残す。visual catalogはPLAY2で同じ原文へタグを挿入するhelperとし、別の隠れLoRA stackを所有しない。

## 11. img2img strategy

PLAY2で一枚input asset、明示resize（contain/crop/stretch）、denoise 0..1を追加。既存Guide uploadのMIME/size/decode/traversal防御を参考にgeneration input専用IDを発行する。Guideを暗黙init imageにしない。VAEEncode→latent sampler経路とinput digest/crop/denoiseを記録。denoise=0はno diffusionの明示結果とし、生成したと偽らない。inpaint、hires、multi-imageは後続。

## 12. ControlNet strategy

PLAY3は既存Figure-derived CLEAN global経路一つを選ぶ。core ControlNetLoader/ControlNetApplyAdvanced、compatible model catalog、強度/start/end、OFFを提供。RAW画素forward、multi-ControlNet、pose preprocessor、effect mask、Advanced-ControlNetは初期対象外。

既存`MANGA_PRODUCT_INTEGRATION_BOUNDARY.md`のSTANDARD/GUIDED auto routeをAuthoring側で保持する。新Generateは明示opt-inでdocument snapshotを受け取り、条件不足/モデルなしなら拒否。既存researchモデルを名前だけで任意Illustriousへ適合保証しない。将来pose/structure uploadは別Cardで前処理とモデルfamilyを指定。

外部ReForgeの`extensions-builtin/sd_forge_controlnet/lib_controlnet/external_code.py`はControlNetUnit/ResizeMode等を持つ別backend API。legacy Manga UIの枠PNG→ControlNet D&Dは参考導線でありComfy node実装ではない。

## 13. MRP strategy

MRP = WHERE / WHAT TEXT APPLIES。PLAY4でScene/regionとglobal/panel/local/character positive・negativeを既存compile plan→mask→conditioningで実際のgenerationへ接続する。Visual Frameは装飾/geometryでありSemantic Sceneと自動同一視しない。Frame overlayは明示出力optionとしてrecordする。

初期MRPはcore masked conditioningを採用。Impact regional sampler経路は既存資産だが別strategy、品質同等と宣言しない。globalとregionのtext合成、overlap順序、mask feather、negative伝播を固定fixtureで検証。LoRAは当面global適用と明記し、region-local weightとして誤表示しない。geometry変更→mask/画像への因果性と境界artifactをvisual gateにする。

## 14. CAST / IPAdapter strategy

IPAdapter = WHO / APPEARANCE、ControlNet = STRUCTURE / POSE / GEOMETRY。CASTは既存identity promptとLoRA情報を所有し、Character Instance/Figureが参照する。CAST prompt利用は現存するが、稼働IPAdapter配線は今回確認できていない。

PLAY5は一CAST・一referenceから開始し、compatible SDXL IPAdapter/vision encoder/nodeのcapabilityを確認する。reference asset(s)と設定の将来所有はCAST。現schemaにreference設定を押し込む前にadditive contract/old-reader roundtripを別設計Cardで承認する。それまではgeneration requestのsession associationのみ、documentへ密かにmetadata保存しない。MRPを置換せず、MRP OFF/ONとReference OFF/ONを別に検証。多CASTの同一性・混線は技術完了と制作受入を分ける。

## 15. Result / History / Queue truth

PLAY1bで小さなManga専用job journalを導入。実行recordはauthoring正本ではない。配置案`manga/data/generation/`（generated/ignored）、job ID単位JSONをatomic replace。fieldsはrequest/effective settings、raw/clean prompts、LoRAs、capability revision、graph digest、backend identity、prompt_id、timestamps、state、output locator。UIのdraft settingsはsession state、reload後はjournalから明示Restore settingsで復元。persistent defaultsは後回し。

state: VALIDATING→SUBMITTING→QUEUED→RUNNING→SUCCEEDED / FAILED。network断はUNKNOWN、queueから消えただけで成功/取消にしない。成功は該当prompt_idのbackend completed statusとSaveImage outputを確認して初めて確定。Previewはその出力のみ。古い成功画像は失敗時に保持し、current jobと区別する。

serviceがrequest_idとdigestで重複を防ぎ、promptへManga ownership/request tokenを記録。submit応答不明は同じ要求を自動再POSTせず、queue/historyで照合し、照合不能ならUNKNOWNで停止。process再起動もjournalからreconcile。one outstanding owned jobで開始し、外部queue busy/unknown時は拒否するが、外部jobを取消/削除しない。cancel UIはPLAY6までなくてよい。

result routeはjournalに記録したoutputだけ許可し、backend由来filename/subfolder/typeも正規化・境界検証する。任意`/view` URLやfilesystem read proxyを開放しない。output prefixはserverが`Manga/Playable/{job_id}`を決める（backend output root配下）。journalは実行事実、Comfy historyはbackend証拠。消えた画像はmissing、再生成画像を過去結果として差し替えない。

## 16. Exact phase roadmap

| Phase | 完了時のユーザー価値 / 分割理由 | Dependency |
|---|---|---|
| MANGA-PLAY1a | catalog＋strict request/LoRA compile、zero submit。最初のCard | baselineのみ |
| MANGA-PLAY1b | service-owned submit、journal、queue/history/result reconcile | 1a |
| MANGA-PLAY1c | Generate UI＋実一枚Preview＋settings restore。ここで初めてFIRST PLAYABLE | 1b、明示live generation許可 |
| MANGA-PLAY2 | LoRA catalog helper＋img2img一枚。基本notationは既に1 | 1c |
| MANGA-PLAY3 | CLEAN global ControlNet一経路 | 1c（2は必須でない） |
| MANGA-PLAY4 | MRP実生成、既存authoring compilerとFrame option | 1c、3との併用検証 |
| MANGA-PLAY5 | CAST reference / IPAdapter、一参照から複数へ | 4、additive reference契約とnode/model gate |
| MANGA-PLAY6 | integration、responsive/keyboard、owned cancel、履歴復旧、polish | 2..5 |
| MANGA-PLAY-S1a/b/c | 特殊sampler/scheduler対応、各pair個別gate | 1c、移植/license/equivalence evidence |

Styles、PNG Info、Train、Extensions UI、Extras、script systemはこの系列の必須条件でない。hires/upscale/presets/defaultsはPLAY6後の別Card。phase内Cardを閉じてもphase全体やOwner受入を自動closeしない。

## 17. Likely target files per phase

既存は相対path、新設候補は(new)。各後続Cardでwrite listを確定する。

| Phase | Likely files |
|---|---|
| 1a | `custom_nodes_custom/tegaki_manga_nodes/basic_generation.py` (new), `basic_generation_api.py` (new), `__init__.py`; `manga/service/manga_workspace_server.mjs`; `manga/tests/test_basic_generation.py` (new), `test_generation_capabilities.mjs` (new) |
| 1b | `manga/service/generation_service.mjs` (new), `generation_journal.mjs` (new), workspace server, `manga/.gitignore` (new), `manga/tests/test_generation_service.mjs` (new) |
| 1c | `manga/app/index.html`, `css/manga_workspace.css`, `src/state/generation_state.js` (new), `src/adapters/manga_generation_client.js` (new), `src/view/generation_view.js` (new), `manga/tests/verify_play1_browser.mjs` (new) |
| 2 | basic compiler/API, generation view/state/service, `test_img2img.py` / `test_lora_catalog.mjs` (new) |
| 3 | basic compiler、`generation_guide_bridge.py`・routerは基本read-only reuse、generation view、`test_play3_controlnet.py` (new) |
| 4 | basic compiler、`authoring_execution_bridge.py`、`conditioning_builder.py`、`mask_builder.py`、frame overlay（責務変更時のみ）、generation view、`test_play4_mrp.py` (new) |
| 5 | CAST reference契約Cardでauthoring_contract/domain validator/storeを必要最小限指定、IPAdapter compiler module (new)、tests (new) |
| 6 | generation UI/service/journalと既存authoring/browser回帰。runtime変更は別Card |
| S1 | Manga sampler adapter/custom node (new)、sigma fixture/tests (new)。Comfy core/ReForgeへwrite禁止 |

`ComfyUI/custom_nodes/tegaki_manga_nodes`と`custom_nodes_custom/tegaki_manga_nodes`の配置関係を実装時に確認し、稼働側へ無断二重writeしない。分離worktreeのcopyを起動するだけでmain runtimeに届くと仮定しない。

## 18. Tests per phase

| Phase | 必須targeted tests |
|---|---|
| 1a | production compilerをfake catalogで実行。exact graph inputs、seed0/-1、multiple LoRA順序、negative CLIP配線、missing/ambiguous/invalidタグ、非有限値、path、model消失、zero submit。既存`manga/tests/test_backend_adapter.mjs`・`test_document_roundtrip.mjs` |
| 1b | mock backendで受付/拒否/timeout-after-accept/再起動/duplicate/late result/unknown queue/foreign job/壊れたjournal/悪意あるoutput locator。失敗時に成功を作らない |
| 1c | Browserでrequired controls→一click、busy double-click、error時原文と旧Preview保持、reload restore、tab往復でauthoring不変、wide/narrow scroll、keyboard |
| 2 | upload MIME/byte/dimension limits、asset missing、resize metadata、denoise境界、manual textとcatalog一致 |
| 3 | Guide無し/disabled/0Figure/enabled、CN missing、compatible selector、no RAW/no effect mask。既存`scripts/test_m3b_pi1_generation_guide_bridge.py`と`test_m3b_pi2_product_generation_route.py` |
| 4 | region positive/negative、overlap、dimension変換、CAST参照、Frame0とoverlay、document不変。既存`test_conditioning_builder.py`、`test_m1_authoring_execution_bridge.py` |
| 5 | old/new roundtrip、reference asset欠落、CAST削除guard、MRPとReference独立toggle、mixed family拒否 |
| 6 / S1 | fault recovery/owned cancel、組合せmatrix。S1はsigma fixtureとsampler step oracle、unsupported維持 |

full suiteを反復しない。JS変更はnode --check、依存なしStandaloneはmodule/static smoke＋Browser（新build system不要）。Python testはPortable PythonでPYTHONPATH=ComfyUI、importだけでCUDA初期化する場合は依存分離かSTOP、GPUを勝手に起動しない。

## 19. Runtime validation per phase

1aはfake backendによるHTTP read/compileのみ、モデルload/生成0。live catalogは既に稼働する正しいprofileへread-only取得できる場合だけ別証拠にする。

1bはfake backendで全state遷移。1cは別途許可されたWindows runtimeで既存モデル一つ、一枚txt2img→prompt_id→実PNG表示→history復元、追加で複数LoRA一枚を確認してfirst playableとする。missing model/unsupported pairはGPU送信前に停止。

2は同一input/seedでdenoise差一対、3は固定入力OFF/ON一対、4は二regionのtext swap一対、5はreference OFF/ON一対を最小live gateにする。6は受入対象の組合せだけ確認。S1は各pairにsource/数値/実画像の別判定を残し、同一seedだけでReForge pixel parityと断言しない。

runtimeはMangaのみ。起動前のport/identity確認と保持process handleによるcleanup、owned orphan 0を記録。H3停止やkill-by-portはしない。servicesを起動するCardは所有・終了を定義してから実行。今回Passはこれらruntime検証を行っていない。

## 20. Stop conditions / Owner decisions

- 新schema正本、H3依存、common supervisor、lifecycle再設計、framework移行が必要ならSTOPして限定設計Cardへ戻す。
- selected checkpoint/LoRA/node/scheduler欠落、不明queue、未解決submit応答、互換不明のCN/IPAdapterはfail closed。自動download/fallback/再POSTなし。
- external ReForgeまたはH3 worktreeへのwrite、unrelated diff cleanup、pushは行わない。
- Owner decisionはPLAY1a開始を妨げない。特殊pairがfirst playable必須へ昇格する場合は優先順位変更が必要。AYS Customのsigma listとGITS/Customのsampler選択はS1該当Card前に必要。
- PLAY5永続reference追加はOwner/architecture判断点。PLAY1の実GPU gateは今回許可外なので、後続実装依頼で明示scopeを得る。技術・Browser・visual・Owner・publicationの状態を別記する。

## 21. First implementation Card — MANGA-PLAY1a

Status: READY FOR IMPLEMENTATION HANDOFF（実行開始の意味ではない）
Executor recommendation: **SOL**。server境界、Python graph、JS proxyの整合判断が必要。LUNAMAXは後で確定したpure compiler fixture等へ限定可能、ASTRAはschema/engine判断点のreviewに留める。

**Goal / minimal cause:** 現prepareはAuthoring必須かつ固定generation設定で、basic Createのcheckpoint/parametersを表せない。authoringと独立したstrict catalog/compile境界を追加し、後続submitが利用するreviewable graphを作る。

**Behavior:** 同じvalid入力・固定seed・catalogから同じgraphとeffective settings。無効入力は具体的errorと元の値を返し、backend queueへのwriteは0。`-1`のresolved seedだけは一度serverで生成し返す。既存prepare/authoring/runtimeの意味は不変。

**Read:** root AGENTS→root docs/STATUS・TECHNICAL→この文書sections 1,3,5..10,15,20→対象header。開始時full status、HEAD/origin基準を再確認。baselineはこのdocs commitの親`90cbf7de...`、実装はdocs commitを含むbranchから開始。

**Write allowlist（6 filesのみ）:**

1. `custom_nodes_custom/tegaki_manga_nodes/basic_generation.py` (new)
2. `custom_nodes_custom/tegaki_manga_nodes/basic_generation_api.py` (new)
3. `custom_nodes_custom/tegaki_manga_nodes/__init__.py`（API登録importのみ）
4. `manga/service/manga_workspace_server.mjs`（2つの専用routeのみ）
5. `manga/tests/test_basic_generation.py` (new)
6. `manga/tests/test_generation_capabilities.mjs` (new)

既存同責務/route名をrgしてから追加。catalog取得はmodel weightをloadせずfolder_pathsとnode capabilityのみ。basic compilerはpure関数にcatalog注入できる形にしてGPU import不要。APIはlive catalogを渡し、任意filesystem pathやuser graphを受け付けない。

**Endpoints:** browser `GET /api/manga/generation/capabilities`→backend `GET /tegaki/manga/generation/capabilities`。browser `POST /api/manga/generation/compile`→backend `POST /tegaki/manga/generation/compile-basic`。method固定、same-origin policy、JSON body<=256KiB、bounded timeout、固定backend origin、non-2xx/invalid responseは明示error。汎用proxyのallowlistへ`/prompt`を追加しない。

**Capability response:** schema version、backend node identity、revision、checkpoints/lorasのIDとavailability/family confidence、supported core sampler/scheduler IDs、product/backend numeric bounds。node/catalog問い合わせ失敗を空の正常catalogと偽らない。

**Compile response:** ok、normalized request、requested/effective seed、raw/clean prompts、ordered resolved LoRAs、capability revision、graph、graph digest。graphはsection2のcore chain、SaveImage prefixはserver固定`Manga/Playable/compiled`（まだ実行しない）。checkpointとLoRAはcatalog IDのみ、global patch済みMODEL/CLIPを使用。unknown/malformed syntax、duplicate resolved LoRA、missing model、bounds違反を全体拒否。

**Acceptance criteria:**

- valid txt2img、seed0、negative空、複数LoRAでgraph全inputと接続を実production compilerテストが検査。
- `<lora:missing:1>`、同basename複数、malformed/extended tag、NaN/Inf、seed小数、width非8倍、traversal、catalog unavailableを拒否。partial graphを成功として返さない。
- fake HTTP backendが受けたmethod/pathを記録し、`/prompt`、`/queue` POST、model load、生成が0。Origin/method/body/timeout失敗も確認。
- authoring roundtripと既存prepare adapter回帰PASS、既存source変更は登録import/server専用routeに限る。
- docs-only設計との差異や未解決点を返し、Scopeを拡大しない。Browser/実GPUはNOT RUNのままでCard技術結果を報告。

**Verification commands（Portable root、fake testsのみ）:**

```powershell
$env:PYTHONPATH = (Resolve-Path ComfyUI).Path
./python_embeded/python.exe -m unittest discover -s manga/tests -p test_basic_generation.py
node --test manga/tests/test_generation_capabilities.mjs
node --test manga/tests/test_backend_adapter.mjs manga/tests/test_document_roundtrip.mjs
node --check manga/service/manga_workspace_server.mjs
git diff --check
```

Python unavailable/importがGPUへ依存する場合はそれを報告してSTOP。runtime module、旧LoRA node、旧prepare API/router、Authoring schema/store、H3、ReForge、modelsへwrite禁止。submit/UI/journalは次Cardであり、PLAY1aだけでFIRST PLAYABLEと呼ばない。

## Audit inventory and verification record

監査は上記fileの責務/header/該当実装と限定symbol検索。全repo、model weight、出力画像、退避folderは調査していない。Standalone renderer/domainは責務・配線確認、主要詳細readはclient/server/runtime、Store/Session、prepare API/router、LoRA loader、generation profiles、conditioning builder、Impact adapter。external ReForgeはsampler/scheduler登録・sigma関数・extra network parser/LoRA materialization・ControlNet API形状。legacy三Manga scriptsとRegionalLoRALabは再利用可否の境界確認。

照合文書: root `docs/STATUS.md`、`TECHNICAL.md`、`DEVELOPMENT.md`、`README.md`、Manga `docs/manga/STATUS.md`、`MANGA_PRODUCT_INTEGRATION_BOUNDARY.md`。旧STATUS内の過去段落とStandalone現行sourceには対象時期の差があり、本稿では上段過去closureをStandalone生成実装完了の証明に使わない。

本Passの検証: fetch baseline一致、isolated worktree作成、document必須21section/対象path検査、git diff --check、commit内容一Markdownのみ。製品test suiteは実行不要（製品差分0）。runtime/Browser/画像品質/Owner acceptanceは未検証、push禁止。
