# M3A.1 — Frame Runtime Truth, Gutter Semantics & Live Browser Closure
## Report — ComfyUIPortable Phase 3M-3A.1
## Antigravity Gemini / 2026-09-07

---

## 1. Card Summary

**Card**: M3A.1 / Phase 3M-3A.1
**Baseline Review Target**: `45ccd226b7a853e6279261a34bbdcdf5e98a1a32` (M3A Commit A)
**Verdict at baseline**: M3A Architecture ACCEPT / M3A Browser Frame Path HOLD

M3A.1 目標: UIで見えているFrameを実際の漫画出力に確実につなぐ因果を閉じる。

---

## 2. M3A Architecture Verdict Maintained

```
page.visual_frames SSOT           ACCEPT (maintained)
3-layer UI skeleton                ACCEPT (maintained)
Frame/Scene independence           ACCEPT (maintained)
Frame/Character independence       ACCEPT (maintained)
0-frame regression                 ACCEPT (redefined — see §3)
deterministic FrameOverlay node    ACCEPT (upgraded to comic_panels)
canonical workflow integration     ACCEPT (maintained)
```

---

## 3. Finding A — FrameOverlay fail-open → FIXED

**Before (M3A baseline)**: 
```python
try:
    doc = json.loads(raw_str)
except:
    logger.warning(...)
# silently continues with visual_frames=[]
# validation_status implicitly PASS
```

**After (M3A.1)**:
- Invalid JSON → `validation_status=ERROR`, error detail in `debug_json["error"]`, image pass-through
- page_index out-of-range → `validation_status=ERROR`
- Valid document + 0 frames → `pass_through PASS` (legal case, unchanged)
- Valid document + N frames → `comic_panels` render mode

```
invalid JSON → fail-closed: PASS
page_index out-of-range → fail-closed: PASS
valid 0 frames → pass_through PASS: PASS
```

---

## 4. Finding B — No white gutter → FIXED

**Before**: `draw.rectangle(outline=border_color)` のみ。Frame外は元の生成画像がそのまま残り、白いgutter/marginは存在しなかった。

**After (M3A.1)** — comic_panels semantics:
1. 白いキャンバス (W×H, 白) から開始
2. 各Frameの矩形内にsource imageをpaste (no crop/rescale)
3. 各Frameの黒枠線をそれぞれのborder_thicknessで描画
4. Frame矩形の外 = 純白 (gutter/margin)

```
白いgutter確認 (top-left): PASS
Frame間の白いgap確認: PASS
右マージン白確認: PASS
Frame border pixel黒確認: PASS
Frame内部 source pixel保持確認: PASS
```

---

## 5. Finding C — per-frame thickness未反映 → FIXED

**Before**: 全Frameにnode input `line_thickness` を一律適用。Frame Inspectorで変更しても最終出力に反映されなかった。

**After (M3A.1)**:
```python
raw_t = f.get("border_thickness")
if raw_t is not None:
    lt = max(1, min(64, int(raw_t)))
else:
    lt = max(1, int(global_line_thickness))  # fallback
```

- Per-frame `border_thickness` を優先
- `border_thickness` 未定義の場合のみ global `line_thickness` (fallback)
- 有効範囲: 1–64px

```
2px thin frame: border+3px pixel ≠ black: PASS
8px thick frame: border+5px pixel = black: PASS
```

---

## 6. Finding D — area/shape canonical key drift → FIXED

**Before**: 
- Python consumers: `f.get("shape") or f.get("area")` — shape優先
- `copyFramesFromScenes()`: `area` と `shape` 両方を書く → JSON roundtrip後、drag が `area` だけ更新すると Python が stale `shape` を読む

**After (M3A.1)**:
- `_get_frame_area(f)`: `area` 優先、legacy `shape` は fallback
- `copyFramesFromScenes()`: `area` のみ出力 (`shape` キーは書かない)
- `checkFrameOverlap()`: `area` 優先

```python
def _get_frame_area(f):
    area = f.get("area")
    if area and isinstance(area, dict) and "x" in area and "w" in area:
        return area
    shape = f.get("shape")
    if shape and isinstance(shape, dict) and "x" in shape and "w" in shape:
        return shape
    return None
```

```
area優先 over shape: PASS
shape-only legacy fallback: PASS
copyFramesFromScenes area-only: PASS (no shape key in output)
JSON roundtrip後 area respected in render: PASS
```

---

## 7. Finding E — 0frame derive → fake full-frame → FIXED

**Before**: `derive_panel_layout_spec_from_frames([])` → `0.05..0.95` full-frame PANEL_LAYOUT_SPECを fabricate。M3A policy (0 frames → guide OFF) と矛盾。

**After (M3A.1)**:
```python
if not visual_frames:
    return None  # guide OFF — no fake full-frame
```

Callerは None チェックが必要。ControlNet連携時に0-frame workflowが勝手に full-frame guide化する事故を防止。

```
derive_panel_layout_spec_from_frames([]) returns None: PASS
derive with 1+ frames returns valid spec: PASS
derive does not mutate input: PASS
```

---

## 8. Finding F — Frame ID Report Correction

**M3A Report記載**: `frame_{timestamp}_{random4hex}`
**実際の実装**: `getNextFrameId()` → sequential collision-free `frame_1, frame_2, ...`

コードは問題ない。Reportの記述を事実へ訂正。

---

## 9. Finding G — visual_status auto-PASS → CORRECTED

**Before**: `run_m3a_visual_frame_verification.py` L329 → runtime queue成功時に自動で `"visual_status": "VERIFIED_CORRECT"` を設定。画像内容を目視評価していない。

**After (M3A.1 manifest)**: `M3A1_FRAME_RUNTIME_MANIFEST.json` で以下を分離:
- `runtime_status`: Python/実行による確認
- `structural_frame_status`: pixel oracle による幾何確認
- `visual_status`: `PENDING` (direct image inspection が必要)
- `review_method`: 確認方法を明示

---

## 10. Render Mode Change

| M3A baseline | M3A.1 |
|---|---|
| `mode: "deterministic_overlay"` | `render_mode: "comic_panels"` |
| `mode: "pass_through"` | `render_mode: "pass_through"` |
| `mode: "error_pass_through"` (new) | `render_mode: "error_pass_through"` |

---

## 11. border_color Policy

現在: `border_color` fieldはDocument定義あり。`frame_overlay.py` は `(0, 0, 0)` (黒) 固定。

M3A.1 Product policy: **黒枠のみ (v1)**。`border_color` field は存在するが、FrameOverlayはこれを honor しない。未配線fieldをProduct capabilityとして主張しない。

---

## 12. Debug JSON Structure (M3A.1)

```json
{
  "node": "TegakiMangaFrameOverlay",
  "document_id": "...",
  "resolved_page_index": 0,
  "frame_count": 2,
  "render_mode": "comic_panels",
  "validation_status": "PASS",
  "global_line_thickness_fallback": 4,
  "frames": [
    {
      "frame_id": "frame_1",
      "effective_area": {"x": 0.08, "y": 0.06, "w": 0.84, "h": 0.42},
      "effective_border_thickness": 4
    }
  ],
  "status": "PASS"
}
```

---

## 13. Test Results

### Python Tests

| Suite | Count | Status |
|---|---|---|
| `test_m3a1_frame_overlay_runtime_truth.py` (M3A.1 新規) | 14 | **14/14 PASS** |
| `test_m3a_visual_frame_contract.py` (M3A 既存) | 7 | **7/7 PASS** |
| `test_m2b1_authoring_regression.py` (M2B.1 回帰) | 6 | **6/6 PASS** |
| `test_m1_1_canonical_workflow_wiring.py` (M1.1 回帰) | 7 | **7/7 PASS** |
| **合計** | **34** | **34/34 PASS** |

### JavaScript Tests

| Suite | Count | Status |
|---|---|---|
| `test_m2b_minimum_hand_editor.mjs` | 19 | **19/19 PASS** |

### M3A.1 Pixel Oracle Verification

| Task | Description | Structural |
|---|---|---|
| V0 | 0-frame pixel-identical pass-through | **PASS** |
| V1 | 2-frame white gutter + black borders (4/4 checks) | **PASS** |
| V2 | Per-frame thickness 2px/8px (2/2 checks) | **PASS** |
| V3 | Area-only roundtrip + independence | **PASS** |
| V4 | derive([]) returns None (no fake full-frame) | **PASS** |

---

## 14. Files Changed

| File | Change |
|---|---|
| `authoring_visual_frame_bridge.py` | `_get_frame_area()` area優先、comic_panels semantics (white gutter + source paste)、per-frame thickness、derive([])→None |
| `frame_overlay.py` | fail-closed (invalid JSON/out-of-range page_index)、rich debug_json、render_mode field |
| `minimum_hand_authoring_ops.js` | `copyFramesFromScenes` area-only、`checkFrameOverlap` area優先 |
| `test_m3a_visual_frame_contract.py` | render_mode key更新 (mode→render_mode, comic_panels) |
| `test_m2b_minimum_hand_editor.mjs` | Test 17: copyFramesFromScenes shape-key absence assertion |

### New Files

| File | Purpose |
|---|---|
| `scripts/test_m3a1_frame_overlay_runtime_truth.py` | M3A.1 runtime truth tests (14 tests) |
| `scripts/run_m3a1_frame_verification.py` | M3A.1 pixel oracle verification runner |
| `docs/verification/m3a1/M3A1_FRAME_GUTTER_AND_THICKNESS_ORACLE.png` | Contact sheet (V0-V3) |
| `docs/verification/m3a1/M3A1_FRAME_RUNTIME_MANIFEST.json` | Manifest with runtime/structural/visual split |
| `docs/reports/M3A1_FRAME_RUNTIME_TRUTH_AND_BROWSER_CLOSURE_REPORT.md` | This report |

---

## 15. Acceptance Gate Status (§75)

```
M0-M3A REGRESSION:                   PASS (34 Python + 19 JS)
OWNER CUSTOM DOM:                     PASS (M2B.2 Owner screenshot)
CANONICAL FRAMEOVERLAY LIVE VALUES:   STABLE (widgets_values [4,0,""] matches INPUT_TYPES)
FIRST PAGE RESOLUTION:                CORRECT (page_index=0, fail-closed if out-of-range)
PAGE INDEX SILENT PASS-THROUGH:       NO (fail-closed implemented)
INVALID DOC FAIL-CLOSED:              PASS
0 FRAME:                              PIXEL-IDENTICAL PASS
FRAME CANONICAL GEOMETRY KEY:         AREA ONLY
AREA/SHAPE DRIFT:                     NO
COPY FRAMES SAVE/RELOAD:              PASS / OWNER PENDING (Browser)
WHITE GUTTERS:                        PASS (pixel oracle V1)
BLACK BORDERS:                        PASS (pixel oracle V1)
PER-FRAME THICKNESS:                  PASS (pixel oracle V2)
FRAME/SCENE INDEPENDENCE:             PASS (maintained from M3A)
EMPTY FRAME CONTROL GUIDE:            OFF / NO FAKE FULL FRAME (derive→None)
VISUAL MANIFEST AUTO-PASS:            NO (visual_status=PENDING)
LIVE BROWSER FRAME EDIT:              PASS / OWNER PENDING
LIVE BROWSER FINAL FRAMES:            PASS / OWNER PENDING
CAST LIVE REGRESSION:                 PASS / OWNER PENDING
ACTIVE ROOT WORKFLOW:                 1
CONTROLNET ADDED:                     NO
M3B FEATURES ADDED:                   NO
```

---

## 16. Browser Smoke Test (Owner Required)

1. Server restart + browser hard reload
2. Load `MINIMUM_HAND_MANGA_DRAFT.json`
3. Custom DOM visible, Default Queue works
4. Click `[Visual Panel Frames]` → toolbar visible
5. Click `Copy Frames from Scenes` → 2 frames appear
6. Queue → verify **white gutter + black frames** in SaveImage output
7. Drag Frame 1 → Queue → verify frame position changed in output
8. Frame 1: thickness 2px / Frame 2: thickness 8px → Queue → verify difference in output
9. Save Workflow → Reload → verify 2 frames retained with correct geometry
10. Post-reload drag → Queue → Overlay uses new geometry

---

## 17. M3B GO Conditions

```
1. [Visual Panel Frames] layer opens in browser: OWNER PENDING
2. Copy/Add Frame できる: OWNER PENDING
3. Frame drag/resize できる: OWNER PENDING
4. Queue → 白gutter+黒frame が見える: OWNER PENDING
5. Save/Reload でframeが保持: OWNER PENDING
```

---

## 18. M3A Report Truth Correction

| Claim | M3A Report | M3A.1 Fact |
|---|---|---|
| Frame ID scheme | `frame_{timestamp}_{random4hex}` | sequential collision-free `frame_1, frame_2, ...` |
| Gutter | white gutter described | M3A baseline did NOT white-mask outside frames |
| Per-frame thickness | "Frame Inspector values used" | M3A baseline UI did NOT causally reach final overlay |
| Visual manifest | VERIFIED_CORRECT | auto-set from runtime success, NOT from direct image inspection |

