# Web GPT SOL → LUNA Manga Authoring Handoff

更新: 2026-09-09 JST。

## 0. この文書の目的

これは、過去会話を一切知らないWeb GPT SOLがGitHubだけでComfyUIPortableのManga Authoringを
監修し、ローカルのLUNAチャットへ安全な限定Cardを発行するための引き継ぎ正本である。
この文書自体は実装Cardではない。

Repository: `https://github.com/toshinka/tegaki`

- Branch: `main`
- Manga project root: `ComfyUIPortable/`
- Manga external entry: `ComfyUIPortable/GITHUB_MANGA.txt`
- Manga entry raw URL: `https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB_MANGA.txt`
- This handoff raw URL: `https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
- H3 external entry: `ComfyUIPortable/GITHUB_H3.txt`
- Domain router: `ComfyUIPortable/GITHUB_ComfyUI.txt`
- Manga implementation Review Target: `a7f0baaad6e7f5d82c39b1042e8a3c4e9f1a7d5b`
- Manga namespace/card migration publication: `ef7daa502f501211cd6b06f378e9024dbff6f284`
- 2026-09-09監査時のrepository HEAD / `origin/main`: `145807e1`

repository HEADにはTegaki本体やH3の別作業も進むため、最新HEADをManga実装SHAと読み替えないこと。

## 1. 製品の狙い

Illustrious系画像生成を使い、漫画のScene、CAST、粗い配置、コマ枠を少ない操作で指定し、
Seedの揺らぎをブレインストーミングとして残したままFirst Useful Draftを出す。

Primary flowはScene-firstである。CAST、人物粗領域、ラフ人物/白ハゲGuide、Pose、SubScene、
手動maskは必要になった時だけ段階的に出す。Semantic Scene RegionとVisual Panel Frameは別物で、
可変数、重なり、移動・拡縮、同一CASTの複数Scene出演を保つ。

## 2. 現在地

- M0〜M2B.2: 完了。
- M3A / M3A.1: Visual Panel Frameとruntime framingを実装済み。
- M3A.1: headless testとstructural pixel oracleはPASS。
- M3A.1 Owner live-browser acceptance: PENDINGとして扱う。
- Active LUNA implementation Card: なし。
- M3B候補: Rough Manga / White-Dummy Character Guide Integration。Owner browser gate前に開始しない。
- production output namespace移行: 未実施。`output/Tegaki`を維持する。

証拠の注意:

- headless、runtime、Browser、visual、Owner acceptanceを別statusにする。
- Phase 3Lの14 visual条件はPENDINGであり、制作受入済みではない。
- WF71はInspire/Advanced-ControlNet backend parityの実証ではない。
- completed Cardとarchiveは現在の指示書として使わない。

## 3. H3との関係と統合目標

MiniMax H3動画ツールは同じPortable baseで並行開発され、2026-09-09時点でH1B.1 Start/End Frame、
Native FL2VA、T2V/I2V browser経路、UX P0/P1/P2まで実装・限定検証されている。Owner acceptanceは別途PENDING。
正確な現在地は必ず `GITHUB_H3.txt` を読む。

長期の製品像は一つのTEGAKI skin/shellである。上位tabを切り替えると、同じGUI内で
`Video (H3)`と`Manga`が切り替わる。これは明示的な製品目標である。

ただし、共通化するのはまずshell/navigation/visual language/workspace入口である。MangaとH3の
document schema、workflow、runtime adapter、queue semantics、evidence、outputは、統合契約が決まるまで
domain別に維持する。H3 Mangaは後段の別gateであり、今回のManga進行へ含めない。

## 4. Web GPT SOLの読む順序

以下をGitHubの`main`から順に読む。

1. `ComfyUIPortable/GITHUB_MANGA.txt`
2. `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
3. `ComfyUIPortable/docs/STATUS.md`
4. `ComfyUIPortable/docs/manga/README.md`
5. `ComfyUIPortable/docs/DOCUMENT_REGISTER.md`
6. `ComfyUIPortable/docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md`
7. `ComfyUIPortable/docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md`
8. `ComfyUIPortable/docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md`
9. `ComfyUIPortable/docs/plans/ASTRA_WEBGPT_SOL_LUNA_EXECUTION_PROTOCOL.md`
10. `ComfyUIPortable/docs/manga/cards/README.md`
11. M3A.1 report、verification、必要なsourceだけをReview Target SHAで読む。
12. 統合判断が関係する時だけ `GITHUB_H3.txt` と `docs/h3/README.md` を読む。

最初から旧Phase全文、archive、EasyReforgeExtension、RegionalLoRALab、Tegaki本体を読まない。
必要な契約の由来を確認する時だけ該当資料へ降りる。

## 5. SOLの最初の判断

最初にOwnerへ、M3A.1のlive browser操作結果がすでに存在するか確認する。

- PENDINGまたは証拠なし: M3A.1 Browser Closure Cardを発行する。LUNAはlive state確認、再現、
  必要最小限の修正、Browser evidence、report/STATUS更新だけを担当する。
- Owner ACCEPTEDの明示あり: M3Bを一括実装せず、入力asset/保存契約/Character associationを
  先に固定する最小Cardを発行する。
- 実装と文書が食い違う: feature追加を止め、truth-fix Cardを先に発行する。

SOLはCard全文をチャットに出すと同時に、保存先を
`ComfyUIPortable/docs/manga/cards/current/<CARD_ID>.md` と指定する。

## 6. LUNAへ渡すCardの条件

Cardにはbaseline SHA、own files、do-not-touch、behavior/storage/UX contract、検証command、
Browser/GPU条件、evidence path、正本文書更新、stop条件、close statusを含める。
曖昧な「必要に応じて全体を改善」は禁止する。

Manga Cardでは原則として次を触らない。

- `ComfyUIPortable/h3/`
- `ComfyUIPortable/workflows/h3/`
- `ComfyUIPortable/docs/h3/`
- `ComfyUIPortable/output/h3/`
- Tegaki本体、EasyReforgeExtension、RegionalLoRALab
- ComfyUI core/frontend/shared model store

共通skinを扱う時だけ、独立したShell Integration CardでManga/H3両方の回帰条件と所有fileを列挙する。

## 7. SOLレビューとGitHub受渡し

LUNAはlocalで編集・検証し、Ownerへ結果を返す。Web GPT SOLはlocal pathを直接読めないため、
Ownerがcommit/pushした後のSHAを受け取ってreviewする。

SOL reviewは次を返す。

```text
Reviewed SHA
Contract: PASS / FAIL
Tests: PASS / FAIL / NOT RUN
Runtime: PASS / FAIL / NOT RUN
Browser: PASS / FAIL / PENDING
Visual: PASS / FAIL / PENDING
Owner acceptance: ACCEPTED / REJECTED / PENDING
Required corrections
Next Card recommendation
```

SOLやLUNAがOwner acceptanceを代理で確定しない。公開済みであることと受入済みであることも分ける。

## 8. Web GPT新規チャットへ貼る依頼文

```text
GitHub上のComfyUIPortable Manga Authoring改修の設計監修者として進行してください。
あなたはWeb GPT SOL、ローカル実装担当は別チャットのLUNA、私はOwnerです。

Repository:
https://github.com/toshinka/tegaki

最初に以下を順番に読んでください。
1. https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/GITHUB_MANGA.txt
2. https://raw.githubusercontent.com/toshinka/tegaki/main/ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md
3. そこに指定されたcurrent authorityと実行プロトコル

目的はIllustriousによるScene-first / Minimum-Hand漫画生成です。長期的には同じTEGAKI
skinの上位タブでVideo (MiniMax H3)とMangaを切り替える統合GUIを目指しますが、
当面は両domainのschema、workflow、runtime、evidenceを分離してください。

まずGitHubのlive stateと指定SHAを監査し、M3A.1のOwner live-browser acceptanceが
未確認ならM3Bへ進めず、閉鎖に必要なLUNA向け限定Cardを1枚だけ作ってください。
受入済みと私が明示した場合は、M3Bの最小sliceを提案してください。

Cardにはbaseline SHA、Goal、own files、do-not-touch、保存/意味/UX contract、acceptance、
検証command、Browser/GPU手順、evidence path、正本文書更新、stop条件、close条件を含めてください。
過去Cardを再利用せず、現在の実装を確認してから発行してください。
```

## 9. Astraへ戻す条件

次の場合だけ、SOLは実装Cardを止めてAstra/Ownerへ1ページ程度の判断packetを返す。

- persistent document/schemaの互換破壊
- Scene、Frame、CAST、Guideの意味境界変更
- Manga/H3共通shellがdomain state所有権を変える
- ComfyUI core/frontendまたは共有model配置の大規模変更
- 同じ原因で二回修正してもacceptance gateが改善しない
- 製品のprimary flowや優先順位を変える必要がある

packetは「狙い、固定条件、観測事実、選択肢、推奨、影響file」で構成する。
