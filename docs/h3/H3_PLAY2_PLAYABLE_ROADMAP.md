# H3-PLAY2 Playable Roadmap

更新: 2026-09-13 JST
状態: **計画 / 実装未着手 / docs-only**
基準実装: `9f7ba6fd05af1fb6aee2d62f6acc1ea66b997e4e`
基準報告: [H3_PLAY1 Playable Controls Implementation Report](reports/H3_PLAY1_PLAYABLE_CONTROLS_IMPLEMENTATION_REPORT.md)

この文書は H3-PLAY1 の playable controls を基礎に、段階的なロングラン実装へ進むための
実装指示書である。今回の作業では実装、runtime 起動、生成、workflow 変更、既存文書の
書き換えを行わない。各 Phase は独立した Card として実装・検証し、前の Phase の
semantic contract と fail-closed 境界を保つ。

## 0. PLAY1 の現在地と維持する境界

PLAY1 で確認済みの基礎は次のとおりである。

| 項目 | PLAY1 の基礎 | PLAY2 での扱い |
|---|---|---|
| Video controls | Advanced 内の Resolution / Duration / Model / LoRA | Advanced の最小手数を維持し、意味を明確化する |
| Video resolution | `512x288`, `608x352`, `736x416` | Aspect × Size Tier へ正規化する |
| Duration | `3`, `5`, `10`, `15` seconds | 5 seconds を default、3 seconds は Experimental のまま維持する |
| Standard model | Native UNETLoader の H3 FL2VA family | `Checkpoint / Model` として明示する |
| Reference model | Native UNETLoader の H3 Ref2VA family | Standard と family を混ぜない |
| LoRA | Native capability が検証済みのときだけ追加可能 | local catalog と Native capability を分離する |
| LoRA stack | ordered 0–3 entries、strength `-2..2` | 上限と範囲を変更しない |
| stale settings | Browser / History で保持し submit 時に拒否 | Missing / Incompatible を可視化して fail closed を強化する |
| runtime authority | Skin は semantic state、Native は execution / queue / output authority | 変更しない |

PLAY1 は実 Native generation を行っていない。したがって、PLAY2 の UI、catalog、
workflow materialization、実生成、出力の読み取りを一つの PASS に混ぜない。実 runtime
結果は PLAY2-E の別 evidence として記録する。

### 共通の不変条件

- Browser から arbitrary filesystem path、絶対パス、`..` traversal、任意の node 名を受け取らない。
- UI の表示名と、server が発行・検証する安全な model/LoRA name を分ける。絶対パスは UI、History、report に出さない。
- Standard は FL2VA family、Reference は Ref2VA family のみを許可する。
- stale selection は自動的に default や別モデルへ置換しない。選択を保持し、Generate 前に理由を表示して拒否する。
- Native capability の不明、profile 不一致、loader 不一致、catalog と capability の不一致は silent fallback しない。
- `/prompt` 直前に Native profile と必要 capability を再確認する。
- Still / Prep の payload に Video の resolution、duration、model、LoRA を漏らさない。
- Native の queue、job、History、output の正本性を Skin 側で再定義しない。

## 1. Resolution の再設計: Aspect × Size Tier

### 1.1 Canonical vocabulary

Resolution は単一の width/height dropdown ではなく、次の二軸で表す。

```text
Resolution = { aspect_preset, size_tier, width, height }
```

- `aspect_preset`: 固定の既知 aspect または後段の source-derived aspect。
- `size_tier`: `Small` / `Default` / `Upper Candidate`。
- `width` と `height`: H3 の 32px grid 上の server-authoritative な整数。
- UI が送るのは最終的な width/height と semantic metadata。Native graph の node id や arbitrary path は送らない。
- PLAY2 の現実的な長辺上限はおおむね 700 前後とする。`736` は PLAY1 から継承する既存候補として許容するが、無条件の品質・速度・VRAM 保証ではない。

### 1.2 Size Tier

| Tier | 長辺 target | 位置づけ | 初期 default |
|---|---:|---|---|
| `Small` | 約 512px | 軽量な feasibility / 開発用 | No |
| `Default` | 約 608px | PLAY2 の通常選択 | **Yes** |
| `Upper Candidate` | 約 736px | 既存候補、runtime feasibility 後に使用 | No |

`Upper Candidate` は「736 を候補に残す」という意味であり、長時間運転の既定値や
全 aspect の実生成完了を先取りしない。VRAM、wall-clock、Native の actual accepted
shape は PLAY2-E で別に記録する。

### 1.3 Known aspect preset matrix

下表は、長辺 target を固定し、短辺を最も近い 32px grid へ丸めた初期 matrix である。
`Upper Candidate` の 736 は許容候補である。丸め後の値が元の数学的比率と完全一致しない
場合も、UI は「32px grid 上の近似」であることを表示し、pixel-perfect crop を主張しない。

| Aspect | 比率 | Small | Default | Upper Candidate |
|---|---:|---:|---:|---:|
| `16:9` | 16 / 9 | `512x288` | `608x352` | `736x416` |
| `1:1` | 1 / 1 | `512x512` | `608x608` | `736x736` |
| `4:3` | 4 / 3 | `512x384` | `608x448` | `736x544` |
| `3:4` | 3 / 4 | `384x512` | `448x608` | `544x736` |
| `9:16` | 9 / 16 | `288x512` | `352x608` | `416x736` |
| `3:2` | 3 / 2 | `512x352` | `608x416` | `736x480` |
| `2:3` | 2 / 3 | `352x512` | `416x608` | `480x736` |
| `21:9` | 21 / 9 | `512x224` | `608x256` | `736x320` |

丸め規則は一か所の pure helper に集約する。

```text
long_edge = tier target
short_edge = nearest_32(long_edge * source_or_preset_short / source_or_preset_long)
```

同値距離は常に同じ方向へ解決する deterministic tie-break を持つ。`width`、`height`
のいずれも 32 の倍数でなければ拒否する。極端な source aspect で短辺が安全な H3
入力範囲を外れる場合は、無理に縮退せず `Incompatible` または `Requires review` として
停止する。

## 2. Start Frame からの Aspect 自動選択

Start Frame は、手動 resolution を黙って上書きする機能ではない。自動選択は、ユーザーが
`Auto` を選んでいる間だけ適用し、手動選択へ移った時点で固定する。

### Phase 1: nearest known aspect preset

- Start Frame の server-owned asset metadata から幅・高さを取得する。
- source ratio と 8 つの known aspect ratio の距離を比較し、最近傍 preset を deterministic に選ぶ。
- 選択理由を `Auto · nearest 16:9` のように表示する。どの preset に寄せたかを隠さない。
- size tier は現在の tier を維持し、aspect だけを変更する。現在値が不正なら `Default` へ戻すが、その fallback は画面に理由を出す。
- source の差し替え時は Auto 中だけ再計算する。手動値、History の明示値、生成済み Job の設定は再計算しない。
- source が無い、寸法を取得できない、比率が不正な場合は自動変更せず、手動 resolution を保持する。

### Phase 2: exact source aspect -> 32px rounded dimensions

- Phase 1 の known preset と区別して `Source aspect` を選択できるようにする。
- source ratio を保ったまま、現在の size tier の長辺 target に対して短辺を 32px grid へ丸める。
- UI は `Source aspect · 608x352` のように、元 ratio、丸め後 dimensions、丸め誤差の有無を表示する。
- これは source を無加工で保存・表示する契約ではない。ImageScale / crop / Native 側の実際の materialization は submitted workflow で検証する。
- source-derived dimensions が Native の verified input contract を外れた場合、送信せず `Incompatible` とする。
- source が変更・削除された時に、古い source-derived dimensions を別 source の値として再利用しない。

## 3. `Checkpoint / Model` UI 整理

PLAY1 の `Model` control を、意味の境界が明確な `Checkpoint` セクションの中へ整理する。

```text
Checkpoint
├─ Route: Standard | Reference · Experimental
└─ Model: server-owned enumerated selection
```

### Semantic contract

| Route | 許可 family | default |
|---|---|---|
| Standard | H3 **FL2VA** family | PLAY1 の verified/default FL2VA name |
| Reference | H3 **Ref2VA** family | PLAY1 の verified/default Ref2VA name |

- Model option は Native capability または offline catalog が返した safe name のみとする。
- arbitrary filesystem path input、file picker による checkpoint path 指定、絶対パスの手入力を実装しない。
- Standard の選択を Reference へ、Reference の選択を Standard へ流用しない。
- Still / Prep にはこの Checkpoint / Model UI を表示しない。
- History は model selection を保持できるが、復元時に current catalog/capability が不一致でも値を消さない。

### Stale selection / fail closed

- stale selection は option として残し、`Unavailable · retained` の状態を表示する。
- Generate は server 側の fresh capability check が終わるまで実行できない。
- family 不一致、Native に無い、catalog に無い、profile 不一致は `/prompt` より前に拒否する。
- stale selection を default、最初の候補、別 family へ silent fallback しない。
- error は「どの選択がなぜ使用できないか」を示し、修正方法（Refresh、別候補、Native 起動）だけを案内する。

## 4. LoRA catalog と Native capability の分離

PLAY1 では Native `/object_info` が利用できるときの capability と LoRA 名の取得を実装した。
PLAY2-D では、Native が停止中でも既存の local model path から read-only catalog を作り、
「選択・保存」と「実行可能性の確認」を分離する。

### 4.1 二つの authority

```text
local catalog (read-only filesystem inventory)
        │  selection / saved settings
        ▼
H3 Skin semantic state
        │  Generate immediately before submit
        ▼
Native profile + object_info capability re-check
        │
        └─ accepted graph or fail closed; no fallback
```

- Catalog は既存の effective local model path configuration を読むだけで、model download、copy、relocation、config rewrite をしない。
- Catalog の browser-facing value は safe relative name / server-issued identifier とし、absolute root を返さない。
- Native が停止中でも、catalog に存在する Model / LoRA を選択し、History / local session settings として保存できる。
- Native 停止中の選択は実行可能性を意味しない。Generate は `Unverified` のままでは通さない。
- Native capability は catalog を置換しない。Native が見ている loader、family、membership、strength range を runtime authority とする。

### 4.2 State vocabulary

Model と LoRA の各 entry / selection は、次の状態を使う。`AVAILABLE` のような一語の
capability と catalog の存在を混同する状態名は PLAY2 の新しい UI 契約に使わない。

| State | 意味 | Generate |
|---|---|---|
| `Unverified` | local catalog にはあるが、Native profile/capability の fresh 確認が未実施、または Native 停止中 | 拒否 |
| `Ready` | catalog と Native capability が family、name、loader、range まで一致 | 許可候補 |
| `Missing` | 保存選択または catalog entry が現在の local store に存在しない、または Native list から消えた | 拒否 |
| `Incompatible` | family 違い、loader schema 不一致、strength range 不足、route 不一致など | 拒否 |

state は表示用のラベルではなく、server の submit gate と同じ分類結果から生成する。
判定不能は `Ready` に昇格させず `Unverified` に留める。

### 4.3 LoRA の不変条件

- current max **3 ordered LoRAs** を維持する。上から下の順序が materialized graph の順序になる。
- strength は **`-2..2`**、finite number、boolean/string/NaN/Infinity は拒否する。
- model-only LoRA loader の compatibility を確認する。別 loader、CLIP 側 injection、custom fallback は採用しない。
- zero LoRA は baseline graph を変えない。
- catalog に名前があっても Native が loader または entry を認識しなければ `Unverified` / `Missing` / `Incompatible` として停止する。
- LoRA を付けたまま Standard と Reference を切り替えても、family、順序、設定が意図せず混ざらない。

## 5. Duration: 3 seconds は Experimental

- H3 の official specification boundary は **4–15 seconds** として扱う。
- PLAY1 には既存検証候補として `3 / 5 / 10 / 15 seconds` があるが、3 seconds はその official boundary の外側である。
- `3 seconds` は UI で **Experimental** と明示し、通常の default や official support と表現しない。
- `5 seconds` を default として維持する。
- H3 frame-grid への変換は既存の `duration_to_frames` authority を維持する。
- 任意の fine duration、秒数の直接入力、frame 数の直接入力、duration-specific prompt tuning は PLAY2 後段へ deferred とする。
- 3 seconds が Native で受理されない、出力が不正、または runtime が不安定でも、5 seconds へ silent fallback しない。

## 6. Phase 実装指示

各 Phase の target files は「この Phase が変更候補として調査・実装する範囲」である。
指定外の product source、workflow、config、Manga、shared runtime は変更しない。既存差分は
保持し、同一 file の別作業が見つかった場合はその Phase を止めて返す。

### PLAY2-A — Aspect / Size

#### Target files

- `ComfyUIPortable/h3/adapters/playable_resolution.py`（新規 pure helper 候補）
- `ComfyUIPortable/h3/adapters/native_t2v.py`
- `ComfyUIPortable/h3/adapters/native_i2v.py`
- `ComfyUIPortable/h3/adapters/native_ref2va.py`
- `ComfyUIPortable/h3/app/server.py`
- `ComfyUIPortable/h3/app/static/app.js`
- `ComfyUIPortable/h3/app/static/index.html`
- `ComfyUIPortable/h3/app/static/history-settings.js`
- `ComfyUIPortable/h3/app/static/styles.css`（表示調整が必要な場合だけ）
- `ComfyUIPortable/h3/tests/test_play2_resolution.py`（新規）
- `ComfyUIPortable/h3/tests/verify_play2_resolution.mjs`（新規）

#### Semantic contract

- aspect preset、size tier、32px rounding、matrix serialization を一つの pure authority にする。
- 全 Video route は同じ matrix を参照する。Still / Prep は既存の resolution contract のままにする。
- `width` / `height` が matrix 外、32px grid 外、長辺上限 policy 外なら request を拒否する。
- 既存の `608x352` default と `736` candidate の意味を維持し、既存 History の width/height を破壊的に変換しない。
- duration、model、LoRA の semantic をこの Phase で再設計しない。

#### UI behavior

- Advanced の Resolution を `Aspect` と `Size` の二段選択へ変更する。
- 現在の最終 dimensions を隣接表示し、`16:9 · Default · 608x352` のように確認できるようにする。
- `Upper Candidate` は候補であることを表示する。既定選択にはしない。
- route を Standard / Reference に切り替えても、Video の aspect/tier state は意図せず reset しない。
- Still / Prep では Video の Aspect / Size control を hidden にし、HTML の hidden control が validation を妨げないようにする。

#### Tests

- 8 aspect × 3 tier の matrix が全て 32px grid であること。
- landscape / portrait の width-height orientation が反転しないこと。
- `608x352`、`736x416`、duration 3/5/10/15 の PLAY1 regression。
- 不正 dimensions、極端な aspect、bool/string/NaN、未知 tier の fail-closed。
- Standard / Reference / Start / End / Start+End route で同じ semantic dimensions が materialize されること。
- Browser DOM verifier で Advanced collapse、route separation、History restore を確認する。

#### Runtime validation

- 実生成は行わず、Native 起動時に `/api/config` と materialized graph の dimensions を read-only / fixture または in-process verifier で確認する。
- Native の実 node が許可する 32px grid と matrix の一致を確認する。確認できない場合は PLAY2-A を実装完了にしない。
- A の runtime evidence は「選択値と graph 値の一致」までであり、画質、速度、VRAM を主張しない。

#### Stop conditions

- aspect matrix が route ごとに分岐する。
- 既存 608/352 または 736 candidate の History が暗黙変換・破棄される。
- Still / Prep payload または Manga runtime に Video dimensions が漏れる。
- Native が 32px grid / 上限を受理する根拠を確認できない。
- arbitrary dimension 入力、silent resize、silent crop が必要になる。

### PLAY2-B — Start Frame Auto Aspect

#### Target files

- `ComfyUIPortable/h3/adapters/playable_resolution.py`
- `ComfyUIPortable/h3/app/server.py`
- `ComfyUIPortable/h3/adapters/native_i2v.py`
- `ComfyUIPortable/h3/app/static/app.js`
- `ComfyUIPortable/h3/app/static/index.html`
- `ComfyUIPortable/h3/app/static/history-settings.js`
- `ComfyUIPortable/h3/tests/test_play2_start_frame_aspect.py`（新規）
- `ComfyUIPortable/h3/tests/verify_play2_start_frame_aspect.mjs`（新規）

#### Semantic contract

- source dimensions は server-owned uploaded asset metadata を正本とする。Browser が読んだ値だけで submit しない。
- Phase 1 は nearest known aspect preset、Phase 2 は exact source aspect + 32px rounded dimensions とする。
- Auto は Auto state の間だけ再計算し、ユーザーの manual selection、History の明示設定、completed Job settings を上書きしない。
- Start Frame の source-derived resolution は実際の I2V submitted workflow に入った width/height と一致しなければならない。
- crop / scale の exact pixel fidelity は、この Phase の UI 表示だけから claim しない。

#### UI behavior

- Start Frame のアップロード後、`Auto · nearest <aspect>` を表示し、現在の size tier に合わせた dimensions を preview する。
- `Auto`、known aspect 手動選択、`Source aspect` を区別する。
- source を差し替えた場合は Auto のみ更新し、manual は保持する。
- source を削除した場合は source-derived state を無効にし、古い source の寸法を新規入力として再利用しない。
- 丸め後 dimensions と、必要なら「32px grid rounding」を表示する。

#### Tests

- 各 known aspect への最近傍選択、portrait/landscape、同距離 tie-break。
- 非 16:9 fixture、正方形 fixture、極端な比率、壊れた画像、寸法欠落。
- Auto 中の source replacement、manual 後の source replacement、History restore、Start-only / Start+End 分離。
- server metadata と submitted I2V graph の dimensions 一致。
- source asset ID の取り違え、古い asset の stale metadata、arbitrary path の拒否。

#### Runtime validation

- 実 Browser で非 16:9 Start Frame を投入し、Auto 表示と選択 dimensions を記録する。
- 実 H3 Skin submit の payload、Native prompt graph、Start image loader から後段の scale / first_frame edge までを capture する。
- runtime では `Auto` が手動設定を上書きしないこと、Start Frame route が Reference Video や Still に流れないことを確認する。
- Native generation は PLAY2-E の正式 checkpoint まで実施しない。B の runtime PASS は submitted semantic path の確認を意味し、output quality の証明ではない。

#### Stop conditions

- Browser width/height を server metadata と照合できない。
- Auto が manual、History、completed Job settings を上書きする。
- source-derived dimensions が実 submitted workflow と異なる。
- source crop / scale の挙動を確認できないまま exact pixel fidelity を主張しようとする。
- stale asset、unknown path、wrong role が fail open する。

### PLAY2-C — Checkpoint polish

#### Target files

- `ComfyUIPortable/h3/adapters/playable_controls.py`
- `ComfyUIPortable/h3/adapters/native_t2v.py`
- `ComfyUIPortable/h3/adapters/native_i2v.py`
- `ComfyUIPortable/h3/adapters/native_ref2va.py`
- `ComfyUIPortable/h3/app/server.py`
- `ComfyUIPortable/h3/app/static/app.js`
- `ComfyUIPortable/h3/app/static/index.html`
- `ComfyUIPortable/h3/app/static/history-settings.js`
- `ComfyUIPortable/h3/app/static/styles.css`（必要最小限）
- `ComfyUIPortable/h3/tests/test_play2_checkpoint_model.py`（新規）
- `ComfyUIPortable/h3/tests/verify_play2_checkpoint_model.mjs`（新規）

#### Semantic contract

- `Checkpoint` は route/family の semantic grouping、`Model` は enumerated selection とする。
- Standard = FL2VA family、Reference = Ref2VA family を server と adapter の両方で検証する。
- PLAY1 の `model_name` の public/history semantics は維持し、任意 path を新設しない。
- stale selection retained + fail closed を、UI、History、server submit、graph materialization の全境界で同じ意味にする。
- Native capability fresh check に成功するまで、選択済みでも `/prompt` を発行しない。

#### UI behavior

- Advanced 内の見出しを `Checkpoint`、route label を `Standard` / `Reference · Experimental`、field label を `Model` とする。
- current route に対応しない stale model は `Unavailable · retained` として残す。
- Model list が空でも field を消して default に置き換えない。Native 起動または catalog refresh の案内を出す。
- Reference に切り替えたとき FL2VA の selected name や LoRA stack を Reference へコピーしない。
- Still / Prep では `Checkpoint` セクションを表示せず、payload/historyにも video selection を混ぜない。

#### Tests

- Standard の FL2VA only、Reference の Ref2VA only、cross-family rejection。
- missing model、wrong profile、disconnected Native、stale History の retained display。
- arbitrary absolute path、drive path、parent traversal、node name injection の rejection。
- fresh capability recheck が失敗したとき no `/prompt`、no retained job、no fallback。
- route switching、reload/History restore、Still/Prep isolation。
- existing PLAY1 exact-base graph hashes と zero-LoRA baseline regression。

#### Runtime validation

- Native connected / disconnected の両方で Skin UI state を確認する。
- connected 時は `/system_stats` profile と `/object_info` family membership を記録し、submit 直前の再確認を観測する。
- stale name を表示したまま Generate を押し、Native `/prompt` が発行されないことを確認する。
- runtime validation は model selection contract の確認に留め、model quality や checkpoint identity beyond filename を主張しない。

#### Stop conditions

- arbitrary path が UI または API に入る。
- Standard が Ref2VA、Reference が FL2VA を materialize できる。
- stale selection が default/first candidate へ silent fallback する。
- capability unavailable のまま `/prompt` が発行される。
- Checkpoint UI が Still / Prep / Manga の state や payload を汚染する。

### PLAY2-D — Offline LoRA Catalog

#### Target files

- `ComfyUIPortable/h3/adapters/model_catalog.py`（新規 read-only catalog helper 候補）
- `ComfyUIPortable/h3/adapters/playable_controls.py`
- `ComfyUIPortable/h3/app/server.py`
- `ComfyUIPortable/h3/app/static/app.js`
- `ComfyUIPortable/h3/app/static/index.html`
- `ComfyUIPortable/h3/app/static/history-settings.js`
- `ComfyUIPortable/h3/app/static/styles.css`（状態表示の最小追加のみ）
- `ComfyUIPortable/h3/tests/test_play2_offline_lora_catalog.py`（新規）
- `ComfyUIPortable/h3/tests/verify_play2_offline_lora_catalog.mjs`（新規）

#### Semantic contract

- local catalog と Native capability は別 record、別 state、別 refresh source とする。
- catalog は existing effective local model path を read-only scan し、ファイルをコピー・移動・ダウンロードしない。
- Native 停止中でも local catalog から Model / LoRA を選択・保存できる。ただし state は `Unverified` のままにする。
- Generate では Native profile、model family、LoRA loader、LoRA membership、strength range を再確認し、`Ready` のみを通す。
- `Missing` と `Incompatible` は理由を保持し、選択を削除せず、Generate を拒否する。
- catalog が返す identifier は safe relative name または opaque server-issued id。absolute local root は browser/client/history/report に公開しない。
- Standard / Reference の model family は catalog 段階でも分離する。LoRA は H3 compatible candidate として列挙するだけで、tensor compatibility/effectiveness を保証しない。
- ordered LoRA max 3、strength `-2..2`、zero-LoRA baseline 不変を維持する。

#### UI behavior

- Native が停止中でも `Refresh local catalog` によって選択候補を表示できる。
- 各選択の badge は `Unverified` / `Ready` / `Missing` / `Incompatible` と理由を表示する。
- `Unverified` は保存可能だが Generate disabled、または submit 時に明示 error とする。
- catalog refresh は stale selection を消さず、現在の local inventory と比較して state を更新する。
- LoRA の順番は上から下、追加は3件まで、strength input は `-2..2` に制限する。
- Native capability refresh と local catalog refresh を別 action / timestamp として表示し、片方の成功を他方の成功に見せない。

#### Tests

- Native offline + local catalog present: selection/save は PASS、Generate は no `/prompt`。
- catalog missing file、ignored local path unavailable、wrong extension、unsafe relative name、duplicate name。
- Native online capability membership success -> `Ready`、missing -> `Missing`、wrong family/loader/range -> `Incompatible`、unreachable -> `Unverified`。
- catalog path に absolute root がある場合でも browser output に漏れないこと。
- 0/1/2/3 ordered LoRA、順序保持、strength boundary `-2/2`、invalid values、4件目拒否。
- Standard/Reference/Still/Prep state isolation、History stale retention。
- submit gate が fresh capability を再確認し、silent fallback せず `/prompt` 前で止まること。

#### Runtime validation

- Native を停止した状態で existing local model path から catalog が読め、候補選択と local session/history 保存ができることを Browser で確認する。
- Native を起動した別 run で同じ選択を recheck し、`Unverified -> Ready` または理由付き `Missing/Incompatible` に遷移することを確認する。
- 一つ以上の LoRA を選んだ submit では materialized graph の ordered model-only chain と strength を capture する。
- 実 LoRA の tensor effect、画質、速度、VRAM、長時間安定性はこの Phase 単独で claim しない。必要なら PLAY2-E の明示 checkpoint として記録する。

#### Stop conditions

- Native 停止中でも capability を `Ready` と表示する。
- catalog が model をコピー、移動、download、config rewrite する。
- absolute path が client に返る、または arbitrary path input が導入される。
- Native recheck を飛ばして `/prompt`、fallback graph、default LoRA replacement が起きる。
- 4件以上の LoRA、範囲外 strength、順序の非決定性が通る。
- LoRA capability の未確認を tensor compatibility の証拠として扱う。

### PLAY2-E — Runtime validation

#### Target files

- `ComfyUIPortable/h3/run_h3.bat`（読み取りのみ。変更禁止）
- `ComfyUIPortable/h3/tools/run_native_isolated.py`（読み取りのみ。変更禁止）
- `ComfyUIPortable/h3/app/server.py`、adapters、static assets（runtime contract の観測対象。通常は変更禁止）
- `ComfyUIPortable/h3/tests/` の temporary validation harness / scripts（Card の許可範囲内。永続化は必要最小限）
- `ComfyUIPortable/docs/h3/reports/H3_PLAY2_RUNTIME_VALIDATION_REPORT.md`（結果 report、新規）

#### Semantic contract

- canonical Native launcher、existing local override、H3 Skin `8190 -> Native 8188` の ownership を維持する。
- generation 前に Native `/system_stats`、`/queue`、必要 model/capability、Skin `READY / CANONICAL_H3` を確認する。
- 実 submitted workflow を checkpoint ごとに保存・照合する。static source inspection だけで real path を claim しない。
- Skin job id、Native prompt id、submission time、terminal state、output path、queue after terminal を分離記録する。
- 生成 count、real sampling、Browser status presentation、output readability、cleanup を別の evidence として報告する。
- 3 seconds は Experimental として別扱いにし、5 seconds default の結果と混同しない。

#### UI behavior

- Standard / Start Frame / Reference + motion / LoRA selected の各 run で、Generate 前の state、選択 family、aspect/tier、duration、catalog/capability state を表示する。
- Generate 中は既存の truthful job states を使用し、fake percentage、fake ETA、fake Finalizing を作らない。
- stale / Unverified / Missing / Incompatible では Generate を fail closed にする。
- Completed output は H3 Preview / History の既存 authority に従い、Still / Prep / Manga へ自動 handoff しない。

#### Tests

- PLAY2-A～D の Python test、Node verifier、`git diff --check`、既存 H3 regression。
- real submitted graph の aspect/tier、Start Frame source-derived dimensions、family、LoRA chain、duration を request と照合する。
- Native queue idle / active / terminal、Skin active job / History preview の分離。
- valid non-empty output container、metadata、readability の検証。visual quality は別 classification にする。
- Native / Skin の exact Card-owned process、start time、command line、bounded cleanup を記録する。

#### Runtime validation

- まず 8188 / 8190 が free であることを positive identify し、unknown/pre-existing occupant があれば STOP する。
- canonical H3 Native は existing local override の selection semantics で起動し、wrong config や tracked config への置換を行わない。
- 各 checkpoint は実際の H3 Skin path から submit し、Native の real sampler progress と terminal output を観測する。
- 実行順は、A/B/C/D の contract verification → 明示した real generation checkpoint → queue idle → Skin cleanup → Native cleanup とする。
- generation は prompt tuning、aesthetic reroll、長時間無制限の探索にしない。sampling が始まった checkpoint は同じ条件で reroll しない。
- runtime で catalog の `Unverified -> Ready`、stale selection の拒否、Standard/Reference family、3 LoRA ordered chain、5 seconds default、3 seconds Experimental を必要な範囲で実証する。
- 実生成を行った場合は、出力と prompt/workflow evidence を report に保存する。Owner acceptance、公開、品質保証とは別分類にする。

#### Stop conditions

- 8188/8190 の unknown occupant、wrong backend profile、required model invisible、queue truth unverifiable。
- tracked config に戻さないと起動できない、または local override の実効性を検証できない。
- `/prompt` が実際に受理されない、sampling が始まらない、job/output identity が追えない。
- 20分を超える generation、queue stuck、output container invalid、cleanup ownership ambiguity。
- stale / Unverified selection が fallback で生成される、または arbitrary path が workflow に入る。
- Still / Prep / Manga / lifecycle / shared supervisor の挙動変更が必要になる。
- deterministic product defect を発見した場合はその checkpoint を FAILED または BLOCKED とし、修正をこの Card に混ぜず SOL へ戻す。

## 7. 実装順と Gate

実装順は固定する。

1. **PLAY2-A Aspect / Size**
2. **PLAY2-B Start Frame Auto Aspect**
3. **PLAY2-C Checkpoint polish**
4. **PLAY2-D Offline LoRA Catalog**
5. **PLAY2-E Runtime validation**

各 Phase の close は次の条件を満たした時だけ行う。

| Gate | close 条件 | 次へ進まない条件 |
|---|---|---|
| A | matrix、32px grid、旧 default/candidate、route isolation が固定テスト済み | dimensions の暗黙変換、Still leakage、Native shape 不明 |
| B | Auto/manual/source-derived の状態と real submitted semantic path が区別できる | source metadata 不一致、manual overwrite、crop fidelity の過大主張 |
| C | Checkpoint/Model、family、stale retained、fail closed が UI/API/adapter で一致 | arbitrary path、cross-family、silent fallback |
| D | Native offline catalog と online capability が分離され、state が4値で説明可能 | offline を Ready 扱い、path leak、LoRA order/range drift |
| E | 明示された real checkpoints、queue/job/output、cleanup、制限が report 化される | runtime identity 不明、生成未完了、cleanup ambiguity |

`PASS` は必要な contract と runtime evidence が全て揃った場合だけ、`PASS WITH LIMIT` は
限定された secondary evidence の不足を明記できる場合だけ使う。環境依存で checkpoint を
評価できなければ `BLOCKED`、正しい Native profile が確立した後の deterministic product
defect は `FAILED` とする。Browser fixture、local static verifier、Owner acceptance、
GitHub publication は相互に代替しない。

## 8. 明示的な非対象

PLAY2 では次を実装・起動・検証しない。

- H3-Edit
- Director / tiling / Refine
- Continuation
- Timeline / Shot / Storyboard
- Manga integration、Manga process、Manga schema、Manga output
- shared supervisor、shared shell、shared backend、lifecycle 再設計
- Still の resolution、Still source、Prep/Edit、Image Studio
- arbitrary multi-reference、audio conditioning、Qwen Image Edit、fine duration
- model download、model relocation、外部実装の導入、prompt tuning

H3 Video の playable controls は H3 の semantic adapter と Native runtime の内側に留める。
Manga、EasyReforge、共通 ComfyUI core/frontend、既存の H3 lifecycle は触らない。

## 9. 現在の作業結果と Publication policy

この Card の成果はこの roadmap 文書だけである。実装は行わない。

- Allowed current change: `ComfyUIPortable/docs/h3/H3_PLAY2_PLAYABLE_ROADMAP.md` の追加のみ
- product source changes: NONE
- workflow/config changes: NONE
- runtime/browser generation: NONE
- Manga / EasyReforge activity: NONE
- docs-only local commit: 実施する場合はこの文書だけを含む一件に限定する
- push: **FORBIDDEN**
- Owner acceptance / GitHub publication: この文書からは主張しない

次の実装 Card は PLAY2-A から開始し、各 Phase の stop condition を満たしたまま順に進める。

STOP.
