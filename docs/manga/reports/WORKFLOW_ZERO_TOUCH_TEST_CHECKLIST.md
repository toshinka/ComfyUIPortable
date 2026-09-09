# WORKFLOW_ZERO_TOUCH_TEST_CHECKLIST.md

本チェックリストは、ComfyUI Portable 環境における公式ワークフロー（09, 10）が、ユーザーの初期ロード時に一切の手動修正なしで正常に Queue および画像生成を完遂できること（Zero-Touch Smoke Test）を保証するための検証記録です。

---

## Zero-Touch Smoke Test 実行結果 (Phase 3B.1.1)

- [x] **ComfyUI clean restart**: サーバープロセスを停止し、クリーンな状態で再起動を確認
- [x] **Load 09 fresh**: 新規キャンバスへ `workflows/09_MANGA_REGIONAL_GENERATION_POC.json` をロード
- [x] **09 NaN なし**: `TegakiMangaConditioningBuilder` の各 Widget に NaN や文字列型エラーが発生しないことを確認
- [x] **09 no-touch Queue**: ロード後、ノードや Widget に一切手を触れずに Queue を押下
- [x] **09 image generated**: `Manga_Page_POC_00001_.png` (512x768) が正常生成され、エラー 0 件
- [x] **Load 10 fresh**: 新規キャンバスへ `workflows/10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json` をロード
- [x] **10 local_region_strength = 1.0**: Canonical 順序で正しく 1.0 に初期化・復元
- [x] **10 set_cond_area = default**: 正しく "default" に初期化・復元
- [x] **10 mask_feather = 0**: 正しく 0 に初期化・復元
- [x] **10 no-touch Queue**: ロード後、ノードや Widget に一切手を触れずに Queue を押下
- [x] **10 image generated**: `Control_Local_ON_00001_.png` (512x768) が正常生成され、エラー 0 件
- [x] **Browser console error 0**: フロントエンドの開発者コンソールに例外・エラーなし

---

## 判定

```text
STATUS: ALL PASSED (Zero-Touch Verified)
```
