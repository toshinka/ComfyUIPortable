# ComfyUI Portable 3M-Prep
# SSOT Publication & Minimum-Hand Direction Reset 指示書
## — Astra成果のGitHub正本化 / Product Direction整理 / 次施工の前処理 —

## 0. この作業の目的

この作業は次の大規模実装Phaseそのものではない。

目的は、

Astraが整理した戦略文書
+
現在のPhase 3L実装状態
+
Ownerが再確認したProduct意図

をGitHub上の正本へ揃え、

今後のWeb ChatGPT → Antigravity2 Gemini施工が
古い研究中心の考え方へ戻らないようにすることである。

今回の成果は、新しい大計画書をさらに作ることではない。
むしろ、既存Astra計画を正本化し、STATUSを短い現在地として使い、
GITHUB_ComfyUI.txtを入口として整え、古い文書の権威を下げることが目的。

---

# 1. 最初に読むもの

ローカル作業開始時に以下を確認。

- ComfyUIPortable/GITHUB_ComfyUI.txt
- ComfyUIPortable/docs/STATUS.md
- ComfyUIPortable/docs/DOCUMENT_REGISTER.md

Astra成果:

- ComfyUIPortable/docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
- ComfyUIPortable/docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md
- ComfyUIPortable/docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
- ComfyUIPortable/docs/plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md
- ComfyUIPortable/docs/plans/ASTRA_GEMINI_CLEANUP_INSTRUCTIONS.md

実装Review Targetは現在:

5eee2d4f7fa342e40add6c48fcb1ae7e8f1867b8

ただし作業開始時にローカルentryとGit履歴を再確認する。

---

# 2. 今回は新しい「噛み砕き計画書」を作らない

重要。

Astra Master Plan / UX Blueprint / Inventoryが既にあるため、
さらに同内容を別計画書へ要約して増やさない。

代わりに docs/STATUS.md を、
人間とWeb GPTが最初の1〜2分で現在方向を理解する短い入口として整える。

詳細はAstra文書へリンクする。

---

# 3. Product DirectionをSTATUSへ明記

STATUSに短く、しかし明確に以下を記載。

Tegaki / ComfyUIPortable は、
最小手でSceneとCAST配置を粗く指定し、
PromptとSeedの揺らぎを使って漫画Draftを高速に出し、
必要な部分だけ後からControl / Pose / SubSceneで精密化する
Minimum-Hand Manga Authoring Tool を目指す。

---

# 4. Target User Flowを明記

完成時に想定する基本導線:

Resolution / Aspect Ratio
↓
Quality / Style Template
↓
CAST
↓
Rough Semantic Scene Regions
↓
Character Rough Regions
↓
Optional Rough Manga / Dummy Guide
↓
Visual Panel Frame / Control Guide
↓
Seed / Generate / Brainstorm
↓
Optional Refinement

この順序をProduct UXの目標とする。

---

# 5. Development OrderとTarget User Flowを混同しない

Astra entryにある

Simple Scene-only draft first
optional CAST next
rough guide afterward

は、実装を安全に分割するDevelopment Orderである。
完成Productのユーザー操作順ではない。

STATUSに明示:

Development order:
Scene-only → CAST → Rough Guide → UX shell

Target user flow:
Resolution → Style Template → CAST → Scene → Character Placement
→ Rough Guide / Panel Control → Seed Brainstorm → Generate

---

# 6. Semantic Scene Region と Visual Panel Frame

今後の正本概念として明記。

Semantic Scene Region
= 「この辺で何が起きるか」の意味領域
= Regional Prompt / CAST配置の基準

Visual Panel Frame
= 実際に見える漫画のコマ枠
= Panel Layout / ControlNet Guideの基準

同一物として扱わない。

---

# 7. Character Rough Region

Character Rectangle / Regionは厳密なPose maskではない。

定義:
Character Instanceの粗いSpatial Representation

意味:
Aliceはだいたいこの辺
Bobはだいたいこの辺

最小入力として優先する。

---

# 8. Rough Manga / Dummy GuideをPoseより優先

OwnerのProduct優先順位を明記。

最重要の次段Control用途:
白ハゲ / 棒人間 / ラフ漫画 / 簡単な人物シルエット

等のrough guideへ、
Alice Region / Bob Region のCAST意味領域を対応させること。

Product Gateとしては、
Rough Manga / Dummy Guide + CAST Region Assignment
を3D Pose Editorより先に置く。

---

# 9. Poseの位置づけを下げる

Pose機能は削除しない。
しかしPrimary UXから外す。

Pose / Interaction / SubScene / Manual Mask は Advanced / Refinement 扱い。

特に3D Poseは、
Draftが十分作れるようになった後の便利機能とする。

---

# 10. Seed RandomnessをCreative Featureとして扱う

Seedは単なるDebug値ではない。
Brainstorm mechanismとして明記。

Draftで固定したいもの:
- CAST identity
- rough Scene location
- rough Character location
- Visual Panel topology

Draftであえて揺らしたいもの:
- Pose
- gesture
- expression nuance
- camera nuance
- background detail
- hair / cloth detail

過剰なControlで最初から揺らぎを消さない。

---

# 11. First Useful DraftをProduct Gateへ

今後のProduct評価では、技術機能の数より
First Useful Draftまでの手数を重視。

MVP目標:
Resolution
Quality Template
CAST
Scene Region
Character Region
Panel Frame Guide
Seed
Generate

で「それなりに誘導された漫画Draft」が出ること。

---

# 12. Prompt Templateは後段

Left / Center / Right
Near / Medium / Far
Close / Bust / Half / Full
Talking / Walking / Looking

などは将来のShortcut候補。

area preset + optional prompt token へ変換可能だが、
Primary MVP Gateにはしない。

---

# 13. A1111 / Forge風の分かりやすさを優先

Product UXとして、
どこから触ればよいか分かる、
上から順に設定してGenerateへ行けることを重視。

3D Pose UIを前面に出すより、
Resolution / Style / CAST / Scene Canvas / Prompt Inspector / Seed / Generate
が見えることを優先。

---

# 14. ComfyUI Comic CreatorをInventoryへ追加

外部参考:
https://github.com/ketle-man/comfyui-comic-creator

現在の判断は REFERENCE。
SELECTIVE REUSE / FORKはまだ決定しない。

Inventoryに最低限:
- Standalone SPA shell
- Work / resolution management
- Panel template / split wizard
- Layout canvas
- Draft layer
- Generate modal
- Overall / Panel prompt tabs
- Workflow execution bridge

を参考対象として登録。

---

# 15. Comic Creatorで今は追わないもの

speech balloons
font manager
3D text
EPUB
full image editor
manga effects
advanced 3D pose

は現時点で採用判断しない。

---

# 16. Comic Creatorの次回監査条件

実際にコード流用を検討する段階になったら、
別CardでPinned sourceを固定し、
REFERENCE / SELECTIVE REUSE / FORK を比較する。

今回の文書整理だけでFork方針を確定しない。

---

# 17. Phase 3L Evidence Correctionを維持

Astraが発見した訂正をSTATUS / Entryから消さない。

現在の重要訂正:

Phase 3L Presence Evaluation:
14 visual_status=PENDING
Owner acceptance is not established

WF71:
Inspire / Advanced-ControlNet backend parityを実証していない

過去Reportの文言より、現在のCorrectionを優先。

---

# 18. Backend判断は「予定」と「実証済み」を分ける

たとえば
Advanced-ControlNetを採用したい
と
Advanced-ControlNet parityを実機実証済み
は別。

STATUS / Inventoryでは
INTENDED / PLANNED
VERIFIED
PENDING
を分ける。

---

# 19. Astraを毎回呼ばない

運用原則:

Routine Card:
Web GPT + Gemini

Strategic Fork:
Astra review candidate

Astraを再投入する条件例:
- MANGA_AUTHORING_DATA全面変更
- Dedicated SPAへの本格移行
- Comic Creator fork / merge
- Regional backend全面変更
- 大規模UX再設計

通常のM0/M1/M2施工はWeb GPT + Geminiで進める。

Astraが利用できない場合でも進行可能な文書構造にする。

---

# 20. DOCUMENT_REGISTERを整理

docs/DOCUMENT_REGISTER.md に:

CURRENT AUTHORITY
- docs/STATUS.md
- docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
- docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md
- docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
- docs/plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md

CURRENT CARD
- 次にWeb GPTが発行するbounded implementation card

HISTORICAL
- 旧中間計画
- 旧Phase request
- archive snapshots

を明示。

---

# 21. GITHUB_ComfyUI.txt を正本入口へする

現在のローカルAstra版 GITHUB_ComfyUI.txt を確認し、
不足していれば整備。

最上部には:
- Canonical path
- Review Target Commit SHA
- Planning Commit SHA
- Current direction
- Next card
- Evidence correction
- Strategic Planning SSOT reading order

を置く。

---

# 22. GITHUB.TXTはCompatibility Pointerにする

ComfyUIPortable/GITHUB.TXT は現在状態を重複記載しない。

原則:
Canonical entry is:
ComfyUIPortable/GITHUB_ComfyUI.txt

への短いpointerにする。

旧External AI Entry全文を二重管理しない。

---

# 23. Astra文書をGitHubへ正本化

ローカルに存在してGitHub未公開なら、以下をCommit対象へ含める。

- docs/plans/ASTRA_MANGA_AUTHORING_MASTER_PLAN.md
- docs/plans/ASTRA_MINIMAL_HAND_MANGA_UX_BLUEPRINT.md
- docs/plans/ASTRA_ASSET_AND_WORKFLOW_INVENTORY.md
- docs/plans/ASTRA_WEBGPT_ANTIGRAVITY_EXECUTION_PROTOCOL.md
- docs/plans/ASTRA_GEMINI_CLEANUP_INSTRUCTIONS.md
- docs/STATUS.md
- docs/DOCUMENT_REGISTER.md

内容を勝手に再生成せず、
Astra成果を基準に必要な整合補正だけ行う。

---

# 24. 古い計画は削除しない

旧計画や旧指示書は historical へ格下げ。
既にArchive snapshotがあるなら維持。
参照切れを防ぐため、無断削除しない。

---

# 25. 新しい大計画書は作らない

今回新規で
MINIMUM_HAND_PLAN_V3
PRODUCT_PLAN_FINAL
MASTER_PLAN_SUMMARY
のような別Master Planを増やさない。

必要な短い説明は STATUS へ集約。

---

# 26. 次の実装Cardの予告だけ書く

今回の文書整理後、
次Card候補をSTATUSへ短く記載。

暫定:
M0 / Phase 3M-0
Versioned Authoring Contract
&
Scene / Frame Separation Foundation

ただし次Cardの詳細実装は今回行わない。

---

# 27. M0のProduct意図を一文だけ残す

将来のMinimum-Hand UIが
Resolution → Style → CAST → Scene → Character → Guide → Seed
という導線で動けるよう、
Backend非依存のAuthoring Contractを先に固定する。

---

# 28. Runtime code変更禁止

今回変更しない:
- custom_nodes runtime behavior
- workflow runtime
- sampler
- ControlNet application
- scene compiler behavior
- region plan behavior
- tegaki_work

文書 / Navigation / Authority整理だけ。

---

# 29. Verification

最低限:
1. All current authority files exist
2. GITHUB_ComfyUI links point to existing files
3. GITHUB.TXT points to GITHUB_ComfyUI
4. STATUS reading order is correct
5. DOCUMENT_REGISTER marks old plans historical
6. Review Target remains implementation SHA
7. Planning Commit is separate
8. No runtime code changed

---

# 30. Commit構成

Commit A — Planning / SSOT publication

推奨:
docs(manga): publish Astra SSOT and reset minimum-hand product direction

含む:
- Astra plan files
- STATUS
- DOCUMENT_REGISTER
- 必要なinventory補正
- Comic Creator reference追加
- Product direction補正

Commit B — Navigation

推奨:
docs(manga): update canonical external AI entry

変更:
- GITHUB_ComfyUI.txt
- GITHUB.TXT compatibility pointer

---

# 31. Review TargetをPlanning Commitへ変えない

Commit Bで Review Target Commit SHA は
Phase 3L implementation SHAを保持。

Planning側は別欄:
Planning Commit SHA:
<Commit A SHA>

へ記録。

次の実装Commit Aができた時に初めて
Review Targetを新implementation SHAへ更新。

---

# 32. Push

Owner運用に従う。

自動Push禁止ルールが現在ある場合は local commitまで。
Push許可が明示されている環境ならその指示に従う。

最終報告で LOCAL ONLY / PUSHED を明記。

---

# 33. 最終報告書

新規の巨大Reportは不要。

docs/reports/3M_PREP_SSOT_PUBLICATION_REPORT.md 程度でよい。

内容:
- Files published
- STATUS changes
- Authority changes
- Evidence corrections preserved
- Comic Creator reference added
- Review Target
- Planning Commit
- Runtime files changed: NO
- Push status
- Next card

---

# 34. 最終Sign-off

ASTRA SSOT FILES PRESENT:
PASS / FAIL

STATUS CURRENT DIRECTION:
PASS / FAIL

TARGET USER FLOW RECORDED:
PASS / FAIL

DEVELOPMENT ORDER SEPARATED:
PASS / FAIL

SCENE / PANEL FRAME SEPARATION:
PASS / FAIL

ROUGH GUIDE PRIORITY:
PASS / FAIL

POSE DE-PRIORITIZED:
PASS / FAIL

SEED BRAINSTORM POSITION:
PASS / FAIL

COMIC CREATOR REFERENCE:
PASS / FAIL

PHASE3L EVIDENCE CORRECTION PRESERVED:
PASS / FAIL

DOCUMENT AUTHORITY:
PASS / FAIL

GITHUB_COMFYUI CANONICAL ENTRY:
PASS / FAIL

GITHUB.TXT POINTER ONLY:
PASS / FAIL

IMPLEMENTATION REVIEW TARGET PRESERVED:
PASS / FAIL

RUNTIME CODE CHANGED:
NO / YES

NEXT CARD:
M0 / 3M-0

---

# 35. 今後の役割分担

整備後:

Astra
= 大きな戦略分岐のみ

Web ChatGPT
= GITHUB_ComfyUI + Astra SSOTを読み
  bounded implementation card発行
  Gemini結果レビュー

Antigravity2 Gemini
= 実装 / test / runtime / docs update

GITHUB_ComfyUI
= AI間共有メモリの入口

---

# 36. 最終方針

この作業で変えるべき最大の認識は、

「高度なPose / Interaction機能を増やす」

ことが次の中心ではない、という点。

次に中心へ置くのは、

最小手
Scene-first
CAST rough placement
rough manga / dummy Control guide
Seed Brainstorm
分かりやすいAuthoring shell

である。

高度機能は既に研究資産として保持し、
必要になった時だけ呼び出す。

今後の開発順と、
完成Productのユーザー操作順を混同しないこと。
