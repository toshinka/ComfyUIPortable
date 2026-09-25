# H3 VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3 MANGA化 段階的開発計画

更新日: 2026-09-11
版: Rev.4 — R2V Practicalization / Image Prep / LoRA / Semantic Reference Reordering

状態: **CURRENT MASTER ROADMAP / DOCS-ONLY / PUBLISHED ON MAIN**

Rev.3は歴史的な設計・開発計画として保持し、本書で上書きしない。Rev.4は、
H3 Video、H3 Still、Native Ref2VA、Browser Reference Video、History handoff
の検証結果を受けて、次の実装順と未検証領域を整理する実務改訂である。
本書の作成自体は文書作業であり、実装、生成、Browser acceptance、モデル取得、
LoRA移動、Manga変更を含まない。

---

## 0. 文書の位置づけと公開状態

本書は `D:\GitHub\tegaki` 配下のMiniMax H3ロードマップ正本である。

- Rev.4: 現在のmaster roadmap
- Rev.3: `HISTORICAL / SUPERSEDED BY REV.4`。削除・改名・上書きしない
- VP2C implementation: `PUBLISHED ON MAIN` at `56ad30afa128ef4120f962b6c114fc0e7526aae8`
- VP2C closeout: `PUBLISHED ON MAIN` at `1a869125fa95ef4c7b1e94b0ccedab39fc52b4be`
- Rev.4 publication: `PUBLISHED ON MAIN` at `3880534af0e26b970a8fd0a1ba564af6bc88c15e`
- IP1 implementation/evidence package: `PUBLISHED ON MAIN` at `d8b1a7ca070db1fe78b6d07ef0db01500e88c828`（この履歴コミットには同時期のManga変更も含まれる）
- IP1 H3 closeout: `PUBLISHED ON MAIN` at `35e49859f3beb3bd0b4b1b2d2dd793897dc6b479`（`d8b1a7ca` に対するH3-only update）
- Current `origin/main` at IP1 reconciliation: later Manga-only descendant `b5c79b85ed2fdeec1bf30254945db569666ecfa4`
- Owner acceptance: `PENDING`

公開状態、技術検証、Browser検証、視覚レビュー、Owner受入は別の状態として
記録する。`PUBLISHED ON MAIN` はOwner受入を意味しない。

現行の入口は次のとおりである。

- [H3 External AI Entry](../ComfyUIPortable/GITHUB_H3.txt)
- [H3 document hub](../ComfyUIPortable/docs/h3/README.md)
- [VP2A Native Ref2VA feasibility report](../ComfyUIPortable/docs/h3/reports/VP2A_NATIVE_REF2VA_R2V_FEASIBILITY_REPORT.md)
- [VP2B experimental R2V report](../ComfyUIPortable/docs/h3/reports/VP2B_EXPERIMENTAL_R2V_PLAYGROUND_REPORT.md)
- [VP2C handoff and D&D report](../ComfyUIPortable/docs/h3/reports/VP2C_REFERENCE_HANDOFF_AND_DND_REPORT.md)

---

## 1. Rev.3から継承する最上位原則

Rev.4は哲学の書き換えではなく、検証済みの実装基盤に合わせた順序の改訂で
ある。次を維持する。

> **Preserve the Cognitive Level. Earn every slope. Build mountains only where the summit is worth reaching.**

- 既にあるものは使う。必要な部分だけを薄い統合層で縫い止める
- `Patchwork Integration` を採用し、巨大な単一forkへ固定しない
- `Cognitive Lens` で同じ制作物を仕事のscopeごとに見る
- `Progressive Disclosure` で機能を削除せず、必要なときだけ見せる
- `Preview as protagonist` とし、生成結果・作業結果を画面の主役にする
- 一般的な `Prompt`、`Reference`、`Generate`、`Queue`、`History` 等の語彙を守る
- 独自の傾斜や山は、学習コストに見合う制作上の利益がある場合だけ作る
- generic dark AI dashboardを目的にしない
- TEGAKIの視覚的固有性は、奇抜さではなく「登った価値がある」制作体験へ集中する

色、面、線、アイコンは状態と重要actionに限定して使い、長時間制作を妨げる
過剰な黒、過剰な色、常時表示の全設定を避ける。既存のTEGAKI visual identity
とFutaba由来の視覚言語は継承し、将来の大幅変更は別のレビューGateで扱う。

---

## 2. 現在の検証済み基盤

### 2.1 Standard Video

`IMPLEMENTED / VERIFIED BROWSER UI GENERATION`。

- T2V
- Start Frame、End Frame、Start + End
- `608 x 352` / `736 x 416`
- `5 sec` / `15 sec`
- Continue via frame bridge
- History / Preview / Use settings
- Standard routeはFL2VA/T2V family

### 2.2 Still

`IMPLEMENTED / VERIFIED BROWSER UI GENERATION`。

- Prompt-only Still
- Source-anchored Still
- `608 x 352`
- History / Preview / Use settings
- StillはVideoのDurationやVideo optionを継承しない

### 2.3 Experimental Reference Video

`IMPLEMENTED / VERIFIED BROWSER UI GENERATION / PASS WITH KNOWN NATIVE LIMIT`。

- Character Image: 1件必須
- Motion Video: 0または1件のMP4
- `608 x 352 / 5 sec / 20 steps`
- Ref2VA family
- Reference audio: `NOT IMPLEMENTED / NOT CONNECTED`
- Still → Character handoff
- Video → Motion handoff
- scoped Character/Motion D&D
- History / playback / Use settings
- 同一プロセス内のFL2VA/T2V ↔ Ref2VA model-family transition: `VERIFIED WITHOUT RESTART`

VP2CのMotion D&Dは、実Fileのdrag sourceまでは確認済みだが、安全なCUAで
target-slot受理を再現できなかった。既存MP4 pickerとReference generationは
PASSである。したがってD&D全体は `PASS WITH LIMITS` とし、Motion targetの
製品失敗とは断定しない。

### 2.4 現在の重要な品質限界

混在Picture / Video referenceの優先度やfidelityは保証されない。

VP2A Native matched rowではPictureの外観保持が弱くVideo influenceが観測され、
VP2B Browser rowではPicture influenceが観測されVideo influenceが説得的でなかった。
結論は「Videoが常に優先」でも「Pictureが常に優先」でもない。

> **MIXED-REFERENCE BALANCE / FIDELITY IS NOT GUARANTEED**

これは今後のA/B評価、UI copy、ユーザー期待値の基準にする。

---

## 3. 新しい中心制作フロー

Rev.4では次の流れを、将来仮説ではなく、既に検証済みのStill・Reference・
History handoffを含む実用方向として明示する。

```text
Create / Prepare Image
        ↓
Character / Scene Asset
        ↓
Reference Video / Standard Video
        ↓
Result
        ↓
Reuse as Motion / Continue / next Shot
```

概念的には次のとおりである。

```text
Still / future Image Prep
        → reusable reference asset
        → Video generation
        → next production step
```

VP2Cにより、生成Stillは通常の再利用可能なCharacter assetへ、生成Videoは
通常の再利用可能なMotion assetへ昇格できる。これはImage Prepそのものの
実装を意味しない。Image Prep generationは本書時点で `PLANNED / NOT IMPLEMENTED`
である。

---

## 4. UI lensの方向

将来の上位lensは次の3つを候補とする。

```text
Video
Still
Prep/Edit
```

状態は混同しない。

| Lens | 状態 | 意味 |
|---|---|---|
| Video | `IMPLEMENTED` | Standard VideoとExperimental Reference Videoの既存路線 |
| Still | `IMPLEMENTED` | H2CのPrompt-only / Source Image Still路線 |
| Prep/Edit | `PLANNED / NOT IMPLEMENTED` | Still、R2V、将来Studioへ渡す素材準備の制作lens |

`Prep/Edit` は別製品ではない。素材を次の工程へ準備するproduction lensであり、
Browser UIを先に作るのではなく、まずNative feasibilityで技術的価値を判定する。

---

## 5. Image Prep / Reference Prep sub-track

### 5.1 目的

Image Prepは、単なる画像編集アプリの複製ではなく、H3のStill・R2V・将来
Studioで使う参照素材を準備するための補助トラックである。

候補目的は次のとおり。ただし、すべてが技術的に証明済みとは扱わない。

- character preparation
- outfit variation
- pose / angle variation
- three-view / turnaround research
- background preparation
- weather / lighting change
- scene element replacement
- donor-reference editing
- R2V source preparation
- ordinary single-image editing/play

### 5.2 Immediate next gate

次の実装Gateは一つに絞る。

> **IP1 — Native Image Prep / Reference Edit Feasibility**

IP1は小さなNative-only feasibility sliceであり、Browser Prep/Edit UIを実装する
前に、12GB環境で有用性、再現性、VRAM、処理時間、参照役割の限界を確かめる。

IP1はRev.4の次の実装Gateとして記録され、現在のIP1 CardでNative-only
feasibilityを完了した。最終分類は `FEASIBLE WITH LIMITS` であり、Browser
Prep/Edit UIは実装しない。次の推奨候補は `IP2 Browser Prep/Edit lens` だが、
このCardでは開始しない。

### 5.3 IP1 candidate tests

| Case | 目的 | 例 |
|---|---|---|
| A. Source-only edit | 1枚のsourceだけで属性を変更できるか | clothing change / weather change |
| B. Source + one donor | subjectを保ち、1つの属性だけ移せるか | donorからoutfitや色を移す |
| C. Background / scene alteration | subjectと背景の分離や置換を観測 | city → mountain / sunny → rainy |
| D. Angle / pose variation | boundedな姿勢・角度変化を観測 | front → slight turn |
| E. Runtime qualification | RTX 4070 12GBで現実的か測る | VRAM / elapsed / OOM / retry |

three-view generationやturnaroundの完全性は保証しない。各ケースでは、source
影響、donor影響、破綻、再現性、入力境界、出力hashを分けて記録する。

### 5.4 Image Prep handoff principle

将来のPrep/Edit結果は、VP2Cのsame-session opaque handoffモデルを再利用する
方向とする。候補actionは次のとおり。

```text
Use as Character
Use as Start Frame
Use as End Frame
Use as Source
possibly Use as Scene
```

これらはRev.4では実装しない。最重要の設計原則は、Image Prep outputを特殊な
dead-end result typeにせず、通常の再利用可能なgenerated image assetとして扱う
ことである。

---

## 6. R2V practicalization track

現在のR2V statusは次のとおり。

| Capability | Current status |
|---|---|
| Single Character Image | `VERIFIED BROWSER UI GENERATION` |
| Optional Motion Video | `VERIFIED BROWSER UI GENERATION` |
| Mixed-reference fidelity | `NOT GUARANTEED` |
| Reference audio | `NOT IMPLEMENTED` |
| Multiple characters | `NOT IMPLEMENTED` |
| Spatial assignment | `NOT IMPLEMENTED` |
| Guide frames | `NOT IMPLEMENTED` |

R2V practicalizationは現在のplaygroundから段階的に続ける。ただし、単一画像と
任意のMotion Videoが動いたことから、full Studioへ直接ジャンプしない。

次の検証では、1つの新しい変数だけを加え、source role、motion role、prompt、
runtime profile、出力品質、12GB headroomを個別に比較する。混在referenceの
balanceをUI文言で保証しない。

---

## 7. Multi-character / Semantic Reference track

R2V practicalizationの後段に、複数の人物とsemantic roleを扱うbounded trackを
置く。候補は次のとおり。

- second Character Image
- explicit Subject semantics
- Character A / Character B naming
- `Picture N` mapping
- Motion Video semantic mapping
- optional descriptive role fields

想定する将来例は、二人のwrestler、blue/red corner assignment、character replacement、
scene role bindingなどである。

意味の層を分離する。

| Layer | Status |
|---|---|
| Semantic control | `PLANNED` |
| Temporal / Motion reference | `PARTIALLY VERIFIED` |
| Spatial hard binding | `NOT VERIFIED / FUTURE RESEARCH` |

region、bounding box、mask、trackingを保証しない。multi-character semantic trackは
Rev.4で記録するが、現在の実装契約には含めない。

---

## 8. Spatial control

Spatial precisionはsemantic referenceとは別の後段問題として扱う。将来候補は、
検証済みの経路が得られた場合に限り次のようなものとする。

- prompt-described location
- full-frame Guide
- timed Guide
- rough composite
- masks / tracking

現在のproduction contractにbbox、mask、trackingを含めない。Rev.4でregion editorを
設計しない。空間hard bindingは `RESEARCH / NOT IMPLEMENTED` のままにする。

---

## 9. Model family UX

現時点で検証済みのsemantic family選択は次のとおり。

```text
Standard Video
    → FL2VA/T2V family

Reference Video
    → Ref2VA family
```

同一プロセス内のbuilt-in model transitionは、再起動なしで `VERIFIED` である。
したがって、同一用途の検証済みモデルが複数存在しない現段階では、物理的な
model filename dropdownを優先しない。

- UIはsemantic route / mode selectionを使う
- adapterが物理modelとworkflowを解決する
- generic model selectorは、同一目的の検証済み選択肢が複数になってから検討する

これはユーザーへ内部実装名を覚えさせず、Cognitive Levelを保つための原則である。

---

## 10. LoRA supporting track

LoRAはIP1へ混ぜず、near-term supporting trackとして別管理する。

### 10.1 Current status

| Item | Status |
|---|---|
| Canonical physical root | `D:\Models\Lora\minimaxH3` |
| Files | `PRESENT` |
| Runtime compatibility | `NOT VERIFIED` |
| UI | `NOT IMPLEMENTED` |
| File movement in Rev.4 | `NONE / NOT AUTHORIZED` |

### 10.2 LORA-INFRA inventory

最初のLoRA stepは、実装ではなく次の棚卸しである。

> **LORA-INFRA — Inventory / Compatibility Classification / Folder Normalization**

既知の各ファイルについて、可能な範囲で次を記録する。

- filename
- source / provenance
- hash
- license
- FL2VA / Ref2VA / other / unknown
- normal adaptation / acceleration / unknown
- expected trigger words（文書にある場合）
- recommended strength（文書にある場合）
- required steps / sampler / profile（文書にある場合）
- safe-to-move status

Rev.4ではファイルを移動しない。未確認の分類を確定扱いしない。

### 10.3 Candidate folder direction

次は互換性を優先した候補構造であり、現行ファイル移動の認可ではない。

```text
D:\Models\Lora\minimaxH3\
  fl2va\
  ref2va\
  acceleration\
  experimental\
  unknown\
```

実際に `unknown` から外すのは、分類を検証できたファイルだけとする。style、
character、motionの深いtaxonomyは、実在する利用例が justify してから作る。

### 10.4 Implementation order

```text
1. Inventory
2. Compatibility classification
3. folder normalization if safe
4. one-LoRA Native feasibility
5. one-LoRA Browser control
6. multiple LoRA only if actual use requires it
```

初期UI候補は次の程度に留める。

```text
LoRA
[ None / one verified LoRA ]

Strength
[ value ]
```

`A1111 <lora:name:weight>` prompt syntaxを必須要件にしない。Rev.4ではLoRA UIを
実装しない。

### 10.5 Acceleration LoRA

Turbo、Fast、acceleration adapterは通常のstyle/character LoRAと同一視しない。
LoRAだけでなく、steps、sampler、scheduler、その他runtime parameterとの協調が
必要な場合がある。その場合の将来UIは、装飾的なLoRA rowではなく次に近い概念で
扱う。

```text
Generation Profile / Speed Profile
```

Rev.4ではacceleration workも行わない。

---

## 11. Low-VRAM rule

主対象は引き続きRTX 4070 12GB / 64GB system RAMとする。

Ref2VAは成功しているが、Native evidenceではheadroomが狭い。したがって、次を
単独で動かせることから組み合わせ可能とは仮定しない。

- multi-reference
- LoRA
- higher resolution
- long duration

将来のRef2VA拡張は、変更境界ごとにruntime qualificationを行う。複数変数を一度に
追加せず、VRAM、elapsed、OOM、retry、output metadataを記録する。

---

## 12. R2V quality rule

現在の実証を次の短い表で固定する。

| Evidence | Picture | Video |
|---|---|---|
| VP2A Native matched feasibility | weaker / `NOT CONVINCING` | observed / `OBSERVED` |
| VP2B Browser playground | observed / `OBSERVED` | weaker / `NOT CONVINCING` |

この差は実装上の成功・失敗とは別に、reference balanceの不確実性を示す。将来の
A/B test、prompt copy、quality reviewは `MIXED-REFERENCE BALANCE / FIDELITY IS NOT
GUARANTEED` を基準語彙とする。

---

## 13. D&D / Handoff UX

VP2Cは、再利用可能なmedia handoffの最初の契約である。

### Verified

- Still → Character
- Video → Motion
- Character D&D: actual File target acceptance observed
- Motion picker: exact MP4 accepted
- same-session opaque asset promotion
- no auto-generation
- public metadata excludes filesystem paths
- atomic state restore on failure

### Qualification

Motion D&Dは `PASS WITH LIMITS`。実File drag sourceは確認済みだが、安全なCUAで
target-slot受理を再現できなかった。これはBrowser automation evidenceの限界として
記録し、product failureとは断定しない。

### Future candidates

- Start Frame D&D
- End Frame D&D
- Still Source D&D
- Prep/Edit result handoff

これらはRev.4では実装しない。現在のVP2C実装契約に追加しない。

---

## 14. Future Shot / Studio direction

将来のShotは、必要性が実使用で確認された後に次の情報を所有する候補である。

```text
Prompt
Start
End
Character references
Scene references
Motion reference
Seed
Resolution
Duration
generated video
```

ただし、現時点でShot schemaを実装しない。現在の単純なVideo panelは捨てるのでは
なく、将来per-Shot editorへ成長させる前提で維持する。

---

## 15. Storyboard / Timeline

後続順序は次のとおりに保つ。

```text
Reference / Image Prep practicalization
        → Shot
        → Storyboard
        → Timeline
```

NLE cloneを作らない。TimelineはAI generation、continuation、retake、regenerationを
支えるためのlensとする。

方向としては次を残す。

- 5-second segment production
- Continue
- Regenerate
- Alternate take
- later partial regeneration

これは将来方向であり、Rev.4での現行capability claimではない。

---

## 16. Previz

Previzは後段のoptional trackとする。候補は次のとおり。

- rough 3D layout
- camera block
- character position
- motion / reference guidance

Blender cloneを作らず、R2V/Image Prepの実用化をPrevizに依存させない。

---

## 17. Illustrious Manga boundary

Rev.4では現在のManga production subsystemを変更しない。

戦略順序は次のとおり。

```text
complete Illustrious Manga on its own terms
        → shared Manga / Video UI integration
        → H3 Manga research / implementation
```

H3 featureのためにManga schema、Scene、Panel、Region、Character、workflow、runtime
を前倒し変更しない。MangaとH3の実装・証跡・受入は別系統である。共通UIを将来検討
するときも、両方のdomain semanticsとbackend recipeを混同しない。

---

## 18. Revised near-term order

### COMPLETED FOUNDATION

```text
H1A / H1B / H1C
H2A / H2B / H2C
VP1
VP2A
VP2B
VP2C
```

### NEXT

```text
IP1
Native Image Prep / Reference Edit Feasibility
```

### THEN, IF IP1 IS USEFUL

```text
IP2
Experimental Browser Prep/Edit Lens
```

IP2は計画ラベルであり、契約を先に固定しない。

### SUPPORTING TRACK

```text
LORA-INFRA
LoRA Inventory / Compatibility / Folder Normalization
```

### THEN

```text
LORA1
Single verified LoRA feasibility
prefer a conservative route before Ref2VA stacking
```

### R2V EXPANSION

```text
bounded multi-character / semantic reference feasibility
```

### AFTER REAL USE

```text
Guide / spatial-control experiments as justified
```

### LATER

```text
Shot
Storyboard
Timeline
Previz as needed
```

### PARALLEL SEPARATE SUBSYSTEM

```text
finish Illustrious Manga
```

### AFTER BOTH SIDES MATURE

```text
shared Manga / Video shell
```

### LAST

```text
H3 Manga
```

### OPTIONAL

```text
H3 → Illustrious / Anima finishing
```

この順序のうち、次の実装Gateとして確定しているのはIP1だけである。IP2、
LORA-INFRA、LORA1はWeb-GPTが先行証拠を見てCard化するための計画ラベルである。

---

## 19. Status vocabulary

Rev.4でも、次の語彙を厳密に分ける。

- `IMPLEMENTED`: bounded source/route/UIが存在する
- `VERIFIED SOURCE/LOGIC`: source、契約、static、logicの再現可能な確認
- `VERIFIED LOCAL GENERATION`: local runtime output、hash、必要なmedia evidenceがある
- `VERIFIED BROWSER UI GENERATION`: Browser操作でvisible completed Previewまで確認
- `PUBLISHED ON MAIN`: 対象commitがmainへ公開された
- `OWNER ACCEPTED`: Ownerが明示的に受入した場合だけ使用
- `PLANNED`: 計画として記録されている
- `RESEARCH`: feasibilityまたは候補調査の段階
- `NOT IMPLEMENTED`: 現在の実装契約に存在しない
- `NOT VERIFIED`: 実行・互換性・品質を確認していない
- `PASS WITH LIMITS`: 基本経路は成立するが、明示した限界が残る

`PUBLISHED ON MAIN`、`VERIFIED`、`OWNER ACCEPTED`を同義にしない。将来Card番号や
実装契約を先回りして確定しない。

---

## 20. Roles and review boundary

役割はRev.3から維持する。

- LUNA: bounded implementation、文書整合、限定検証
- Web GPT: research、shortlist、diff audit、Gate review、Card化
- Sol: difficult implementation、difficult bug、bounded refactor
- Astra: GUI composition、Cognitive Level、lens design、major architecture boundary

本Rev.4 publicationではAstraを呼び出さない。subagentを使わず、広範な外部Web
researchも行わない。Rev.4で選択した方向を、別の新しいroadmapへ再設計しない。

---

## 21. Canonical references and preservation

現行のcanonical pointerは次の文書で管理する。

- `ComfyUIPortable/GITHUB_H3.txt`
- `ComfyUIPortable/docs/h3/README.md`
- 本書: `MiniMax H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md`

Rev.3は次の正本として保持する。

- `MiniMax H3/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md`
- `MiniMax H3/Archive/H3_VIDEO導入・Still対応基盤・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev3.md`

Rev.3 rootとArchive sourceは開始時点でbyte-identicalである。Rev.4は新規ファイル
として追加し、Rev.3を削除、移動、改名、上書き、統合しない。

推奨read orderは次のとおり。

1. `ComfyUIPortable/GITHUB_H3.txt`
2. `ComfyUIPortable/docs/h3/README.md`
3. 本書Rev.4（CURRENT MASTER ROADMAP）
4. Rev.3（HISTORICAL / SUPERSEDED BY REV.4）
5. VP2A report / evidence
6. VP2B report / evidence
7. VP2C report / evidence

H3とIllustrious Mangaの入口、runtime、workflow、受入状態を相互に混ぜない。

---

## 22. Scope guardrails

本Rev.4 publicationでは次を行わない。

- Image Prepの実装、Native生成、Browser testing
- IP1の開始
- Multi-characterの実装
- bbox / mask / tracking / region editorの設計
- LoRAの移動、変更、互換性を未確認のままの読み込み
- LoRA UI、acceleration profile、model selectorの実装
- Shot schema、Storyboard、Timeline、Previzの実装
- Astra呼び出し、subagent委任、広範囲Web research
- Manga runtime、`docs/manga/`、Manga workflow、shared ComfyUI core/frontendの変更
- 新しいモデル、依存、local YAML、runtime mediaの追加
- 既存Rev.3の上書き、force push

本Cardの対象はロードマップとcanonical pointerの整合だけである。

---

## 23. Completion gate for Rev.4 publication

```text
[x] VP2C closeout current wording says PUBLISHED ON MAIN
[x] Rev.3 root and Archive remain intact
[x] Rev.4 created as a new file
[x] Verified Still → Character → R2V handoff identified
[x] Image Prep formal sub-track recorded
[x] IP1 is the immediate next implementation gate
[x] R2V mixed-reference limitation recorded accurately
[x] Multi-character semantic track recorded without implementation claim
[x] Spatial hard binding remains research
[x] Semantic model-family UI principle recorded
[x] LoRA inventory track and candidate normalization recorded without file movement
[x] Acceleration LoRA distinguished from ordinary LoRA
[x] Shot / Storyboard / Timeline remain later
[x] Manga boundary retained
[x] Canonical pointers updated to Rev.4
[x] Runtime / Manga / model changes excluded
[x] Docs-only validation completed
[x] Publication checked against the actual remote after push
[ ] Owner acceptance
```

Owner acceptanceはこのCardの完了条件ではなく、別の明示的な受入Gateである。

---

## 24. Final status

```text
H3 ROADMAP REV.4:
PASS

Remote base:
df0ad3b389db5149e1b6ab1edb24c568c147a10e

VP2C closeout:
PUBLISHED ON MAIN

Rev.4:
MiniMax H3/H3_VIDEO・Still・ImagePrep・R2V・動画スタジオ化・Illustrious漫画統合・H3_MANGA化_段階的開発計画_Rev4.md

Rev.3:
RETAINED / HISTORICAL

Current master roadmap:
REV.4

Immediate next gate:
IP2 Browser Prep/Edit lens (recommended; not started)

Image Prep track:
IP1 FEASIBLE WITH LIMITS / BROWSER PREP-EDIT NOT IMPLEMENTED

R2V practicalization:
RECORDED

Multi-character semantic track:
RECORDED / NOT IMPLEMENTED

Spatial hard binding:
RESEARCH / NOT IMPLEMENTED

LoRA inventory:
PLANNED / NOT RUN

LoRA files moved:
NONE

Model-family raw dropdown:
NOT PRIORITIZED

Shot / Storyboard / Timeline:
LATER

Manga changes:
NONE

Runtime changes:
NONE

Validation:
IP1 Native audit/runtime/contract/full-H3-Python/compileall/JSON/diff-check PASS; Browser not run

Implementation/docs commit:
d8b1a7ca (H3 IP1 package is present in published history; concurrent Manga-only changes are also in this historical commit)

IP1 H3 closeout:
35e49859 (H3-only closeout update relative to d8b1a7ca)

Publication:
PUBLISHED ON MAIN at 35e49859f3beb3bd0b4b1b2d2dd793897dc6b479
Current main at reconciliation:
b5c79b85ed2fdeec1bf30254945db569666ecfa4 (later Manga-only descendant)

Owner acceptance:
PENDING

STOP
```
