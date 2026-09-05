# Gemini向け文書整理カード（製品実装とは別）

2026-09-06 / docs-only。M0/M1を待たせる一括整理をしない。

## 今回Astraで済ませるもの

- `GITHUB_ComfyUI.txt`へ現在入口を統合。旧`GITHUB.TXT`はstub。
- 旧入口2件と旧中間計画2件を `Archive/2026-09-06_pre_astra_replan/` へコピーし、元fileとhashの対応を保存。
- 中間計画はリンク保全のため元pathにも残す。現在の戦略正本ではない旨を入口/登録簿で明示。
- 既存runtime/workflow/モデルは動かさない。

## Geminiが行う限定整理

1. STATUSとMaster Planを読み、git statusを確認。
2. `docs/WORKFLOW_INDEX.md`を用途分類（Product / Oracle / Research / Future）へ整える。過去番号とpathは維持。
3. READMEの古い最大6枠/Phase説明を「現行legacy機能」と区別し、計画を実装済みと書かない。
4. `docs/DOCUMENT_REGISTER.md`へ現行契約/新計画/履歴/検証の分類を追加。旧Phase reportは研究証拠として保持。
5. 旧workflow/adapterを物理移動する必要がある時だけ、`rg`でimport、node登録、generator、test、doc、保存workflowからの参照を調べる。移動一覧と新旧pathを先にSOLへ提示する。
6. 移動は本project内のArchiveに限定し、各絶対pathがworkspace内であることを検証してからPowerShellのLiteralPathで行う。未解決参照があれば移動しない。runtime sourceはこのカードでは移動/削除しない。
7. Archiveへ格納したものは削除しない。出力画像/モデル/環境一式をコピーしない。Owner退避物のBackup等、他projectは探索しない。
8. docs-onlyのリンク解決、hash一致、git diff --check、変更file一覧を報告。code testの全実行は不要。

## 文書更新の注意

旧報告のPASSを歴史改変しない。誤認箇所には訂正注/現行監査リンクを追記する。WF71と外部Backend比較testの実態は新棚卸しが説明しているため、古い完了宣言を今の入口へ再コピーしない。

完了条件: 現在入口は一つ、計画正本は一つ、履歴は保存、参照切れゼロ、runtime差分ゼロ。Git pushはOwner。
