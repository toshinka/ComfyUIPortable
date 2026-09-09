# Astra → Web GPT SOL → LUNA 実行プロトコル

更新: 2026-09-09 JST / revision 2。

この文書は、Manga Authoring改修の日常運用をWeb GPT SOLとローカルLUNAへ引き継ぐための
現行プロトコルである。旧Antigravity/Gemini版は履歴として残すが、新しいCardへ流用しない。

## 役割

| 担当 | 責務 | 境界 |
|---|---|---|
| Astra | 製品方向、保存・意味境界、Manga/H3統合方針、行き詰まりの構造判断 | 日々のCard発行と実装から離れる |
| Web GPT SOL | GitHub上の正本と固定SHAを監査し、次の限定Cardを設計、LUNA成果と証拠をレビュー | 未公開ローカル差分を推測しない。重大な製品判断はAstra/Ownerへ戻す |
| LUNA local chat | live worktreeを直接編集し、Card内の実装、test、Browser/GPU確認、reportと正本更新を行う | Card外の改修、互換破壊、別domain変更を混ぜない |
| Owner | SOLとLUNAの受渡し、制作操作と画質の受入、commit/push判断 | 自動検証をOwner受入として代筆させない |

通常ループは `SOLがGitHub監査・Card発行 → OwnerがLUNAへ渡す → LUNAがlocal実装・検証・報告
→ Ownerがcommit/push → SOLが固定SHAでreview` とする。SOLが読めるのは公開済みGitHubであり、
LUNAの未commit・未push差分は対象外である。

## Card発行前のSOL監査

1. `GITHUB_MANGA.txt` の最新入口を読む。
2. 入口が指定する `docs/manga/STATUS.md`、handoff、Master Plan、UX、Card Routerを読む。
3. `main`の最新commitとManga implementation Review Targetを区別する。
4. 直前Card、report、verification、対象sourceだけを固定SHAで確認する。
5. technical/runtime/visual/Owner acceptanceを別々に判定する。
6. M3A.1のOwner browser受入が未確認ならM3Bを発行せず、閉鎖に必要な限定Cardを出す。
7. H3側を変更する必要がある場合、Manga Cardへ混ぜず共通shell専用Cardとして明示する。

## SOLが発行するCardの必須欄

```text
Card ID / date / source authority URLs / baseline SHA / implementation Review Target
Goal: 利用者が一つ何をできるようになるか
Why now: 前gateとこのCardの関係
Read order: 固定SHAまたはmainを使う理由を含む正確なpath
Own files: LUNAが変更可能なfile
Do not touch: Manga/H3/shared core/output等の明示境界
Contract: 入出力、保存version、ID、mode、座標、error、互換性
UX contract: primary flow、progressive disclosure、手数上限
Acceptance: fixture、操作、画像評価基準
Validation: command、Browser手順、GPU条件
Evidence outputs: log、JSON、image、contact sheet、reportのpath
Required document updates: STATUS、計画該当節、report、entry、Card Router
Stop/escalate: 未決定の意味、互換破壊、対象file越境、再現不能
Close condition: source/test/runtime/browser/visual/Ownerを個別に記載
Publication: implementation commitとnavigation/report commitの扱い
```

1 Cardは1責務を基本とする。同じfileへの並列writeは行わない。調査と実装を分けられる場合も、
LUNAが次の作業を誤推定しないようCard内で順序とstop条件を固定する。

## LUNAの開始・終了契約

開始時:

1. `git status --short --untracked-files=all`、HEAD、`origin/main`を確認する。
2. 既存差分があれば所有者とscopeを区別し、対象外差分を巻き戻さない。
3. CardのGoal、own files、acceptance、stop条件を短く言い直してから編集する。
4. 同責務、同名event、schema key、CSS変数、workflow nodeを`rg`で確認する。

終了時:

- 変更内容、理由、検証commandと結果、未実施、risk、Owner確認項目をreportする。
- `docs/manga/STATUS.md`には現在地と次の一件だけを置き、長い履歴を積まない。
- 計画との差、判明した制限、gate結果を該当計画へ反映する。
- 実画像を見ていない場合はvisual PASSにしない。Browser未実施をPASSにしない。
- 実装Review Targetとnavigation-only commitを混同しない。
- commit/push前後の状態を明記し、SOLへ渡す時は公開SHAを一つ指定する。

## Manga/H3共通スキンの製品境界

目標UIは、同じTEGAKI shell/skin内で上位tabを切り替え、`Manga`と`Video (H3)`を使う形とする。
共通shellが持つ候補はapp navigation、visual language、workspace/session入口、共通通知、設定への導線。
各domainは当面、保存document、workflow、runtime adapter、queue semantics、evidence、output namespaceを保持する。

統合Cardは次を満たす時だけ発行する。

- MangaのFirst Useful Draft導線とH3 Video導線が、それぞれ単独で回帰確認できる。
- tab切替でdomain stateを失わない保存・復元境界が決まっている。
- 共通shellがComfyUI core/frontendや両domain schemaを無条件に置換しない。
- Manga変更とH3変更とshell変更をreview上で区別できる。
- H3 Mangaは別gateのまま維持する。

共通スキンは最終目標として計画に含めるが、M3A.1閉鎖やM3Bへ混ぜない。

## GitHub受渡し

- External AI router: `ComfyUIPortable/GITHUB_ComfyUI.txt`
- Manga canonical entry: `ComfyUIPortable/GITHUB_MANGA.txt`
- H3 canonical entry: `ComfyUIPortable/GITHUB_H3.txt`
- New-chat handoff: `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
- Current Card directory: `ComfyUIPortable/docs/manga/cards/current/`

SOLは入口には`main`、コード・workflow・reportの精査には入口が指定した固定SHAを使う。
raw URLが404なら未公開として止め、別revisionへ黙ってfallbackしない。LUNA完了後はOwnerが公開したSHAを
受け取り、そのSHAだけをreviewする。pushと制作受入はOwnerが行う。

