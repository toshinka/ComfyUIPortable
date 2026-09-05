# Astra → WEB GPT-SOL → Gemini 実行プロトコル

2026-09-06 / revision 1。

## 役割

| 担当 | 責務 | 戻す判断 |
|---|---|---|
| Astra | 上位方針、保存/意味境界、行き詰まりの構造判断 | 日々の実装/整理は担当しない |
| WEB GPT-SOL | 固定SHAの実装監修、限定カード、証拠評価、次カード選択 | 製品優先順位変更、互換破壊、大規模Backend/保存正本変更 |
| Antigravity2 / Gemini 3.8 | カード内の実装、tests、GPU/Browser、workflow、報告、文書更新 | 対象外の改修や未決定UXは提案へ分離 |
| Owner | 制作画像/操作感の受入、Git push | 自動指標をOwner受入として代筆しない |

既存Phaseを毎回再計画しない。通常はSOL↔Geminiだけで進める。Astraへ戻すのは上記重大判断、同じ原因で二回修正してgateが改善しない時、またはOwnerが方針相談を求めた時。戻すpacketは「狙い・固定条件・差分・結果・二案・推奨」1ページ程度。

## 読む順序とトークン節約

1. `GITHUB_ComfyUI.txt` → `docs/STATUS.md`。
2. `ASTRA_MANGA_AUTHORING_MASTER_PLAN.md`。既読後はrevisionと変更節だけ。
3. 今回のUX節/棚卸し該当行→current card。
4. 対象file header・関数・関連testと直近reportだけ。

旧Phase全部、EasyReforgeExtension、Tegaki本体、RegionalLoRALabは最初から読まない。長いログを会話に貼らずfileへ残し、要約とpathを渡す。通常一度に一枚、1カード1責務。同file並列writeはしない。独立read-only監査は可。Gemini側で実装を並列化するならSOLが先に所有fileを分離する。

## SOLが発行するカードの必須欄

```text
Card ID / Master Plan revision / baseline implementation SHA
Goal: 利用者が何をできるようになるか（一つ）
Read order: 正確なpath、必要な節
Own files: 変更可能なfile / 新規file
Contract: 入出力、ID、保存version、mode、座標、error
Do not touch: 対象外のruntime/モデル/旧workflow
Acceptance: fixture、手数、画像評価基準
Validation: 実行command、Browser手順、GPU条件
Evidence outputs: log/JSON/image/contact sheetのpath
Required document updates: STATUS、計画該当節、report、入口
Stop/escalate: 未決定の意味/互換破壊/対象file越境
Close condition: technical/runtime/visual/Ownerを個別記載
```

M0は契約文書＋fixture提案のみ。SOLがschema/旧import表を確定してM1を発行する。計画中の案をGeminiが既存APIとして呼ばない。M1で実装対象が確定した後に、JSなら構文/Browser、Pythonなら関連unit、生成変更なら実GPUを含める。Tegaki本体のbuild commandを本projectで代用しない。

## Geminiの更新義務（毎カード）

- 開始時にgit statusを確認し既存差分を保持。カード開始時と終了時、重大発見時に `docs/STATUS.md` の現在地を更新する。
- **計画書を適時更新すること。** 実装と計画の差、判明した制限、gate結果は該当計画節と棚卸しへ反映。戦略変更が必要なら「提案/未承認」とし正本の決定を勝手に置換しない。
- reportは変更/検証command/結果/未実施/画像path/次の一件だけ。大量の過去履歴をSTATUSへ積まない。
- 実行失敗、途中timeout、未閲覧画像をPASSにしない。構文、schema、実node実行、画像評価、Owner受入を別欄にする。
- 同じスクリプトで自動生成した`visual PASS`を証拠にしない。画像判断はannotator・判定項目・実ファイルを記録。出力画像は通常Git対象外なので、SOLが閲覧できるcontact sheetをOwner承認の共有先へ用意する。ローカル絶対pathだけではWEBレビュー不能。
- queue前に具体Seed、prompt snapshot、guide hash、model/profile、拡張SHAを記録。比較対象以外は同じ条件にする。

## GitHub受渡し

唯一の現在入口は `ComfyUIPortable/GITHUB_ComfyUI.txt`。`GITHUB.TXT`は誘導stubだけで更新情報を二重管理しない。

- 実装Review Target SHAは実装commitを指す。今回の計画追加だけではPhase 3LのSHAを置き換えない。
- Planning Commit SHAは計画のcommit。今回はローカル発行で未commit。架空SHAや未公開pinned URLを作らない。
- 公開時はCommit Aに計画/必要doc、Commit Bに入口のPlanning Commit SHAとpinned raw URLを入れる。実装時もA=実装/証拠、B=入口更新。Ownerがpushする。
- SOLは最新入口を読むためmainを使い、レビュー本文/code/workflowは入口が指定した同一SHAを使う。SHAでrawが404なら未公開として扱い、mainへ黙ってfallbackしない。
- 他projectの同名ファイルは変更しない。入口統合は本project内に限定。

## SOLへの最初の依頼（コピー用）

```text
ComfyUIPortableのScene-first漫画生成を監修してください。
入口は ComfyUIPortable/GITHUB_ComfyUI.txt です。
STATUS→Astra Master Plan→UX→棚卸しのギャップ→実行プロトコルを読み、
M0 / 3M-0だけのGemini 3.8向けカードを発行してください。
優先はかんたんScene-only→CAST複数出演→白ハゲGuideです。
Scene領域とVisual Frameを分離し、可変数・重なり・非破壊mode切替を維持します。
Phase3Lの全PASSやWF71のparityを制作受入済みと扱わないでください。
M0は保存version/旧import/ID/座標/重なり方針とJSON fixtureの確定です。
初手からPoseや外部Backend置換、全履歴整理、全面SPA forkを含めないでください。
各カードでGeminiにSTATUSと計画該当節を更新させてください。
未公開の計画はOwnerからファイルを受け取り、公開後にPlanning SHAへ固定してください。
```
