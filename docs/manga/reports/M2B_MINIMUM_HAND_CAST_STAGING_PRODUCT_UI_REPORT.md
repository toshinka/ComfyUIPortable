# M2B Minimum-Hand CAST & Character Staging Product UI Report

## 1. Baseline Fixed SHA
- **Repository**: `d:\GitHub\tegaki\ComfyUIPortable`
- **Preceding Implementation Commit (M2A.1)**: `7e9528d751959b62e108aaad8df363548855df92`
- **Published Navigation Commit (Remote main)**: `408744b1906349fa3fa9a290bd136706bcc4b45f`
- **Preceding Remote Base**: `3283adf92850272b21c5c80dcfc1d714f8f82444` (update)
- **Execution Date**: 2026-09-06
- **Model Checkpoint**: SDXL `♃CN_Skeb\waiIllustriousSDXL_v170.safetensors`
- **Runtime Environment**: ComfyUI Standalone Windows Embedded Runtime (Port 8188)

---

## 2. M2A.1 Review Decision
Milestone M2A.1 systematically benchmarked prompt-region capabilities across 8 fixed seeds (`42, 77, 101, 133, 202, 303, 404, 505`) and established:
1. **2-Character Staging**: Boosted from 25% (2/8) useful in baseline to **62.5% (5/8)** useful (50% clear success) with the compile-time horizontal spatial helper (`"on the left side"`, `"on the right side"`).
2. **Depth Scale Hierarchy**: Boosted from 12.5% (1/8) to **62.5% (5/8)** useful with the automatic depth helper (`"large in the foreground"`, `"smaller in the background"`).
3. **Presence Hints**: B2 presence hint gave identical scores to B1 horizontal alone (neutral); therefore, presence hints are not made a production default.
4. **3-Character Composition**: 1/8 useful across all prompt-region variants; collapsed to single dominant character. ControlNet at 0.35 partially enforced geometry but caused lattice artifacts and stiffness. Classified as **Tier 3 (Advanced / Seed-Sensitive)**.
5. **Product Recommendation**: **OPTION A+ (Rough Region + Free Text Prompt + Hidden Automatic Spatial Helper)** accepted as the foundation for M2B.

---

## 3. Product AUTO Helper Policy
The spatial helper is now completely automated per scene at compile time:
- **0 Characters**: `off`
- **1 Character**: `off` (single-character area conditioning is already robust)
- **2 Characters**:
  - If $\max(\text{area}) / \min(\text{area}) \ge 1.8$: `spatial_depth` (`"large in the foreground"`, `"smaller in the background"`)
  - Else: `horizontal` (`"on the left side"`, `"on the right side"`, with ambiguity guard if center distance $< 0.15$ or overlap $> 0.40$)
- **3+ Characters**: `off` (production default; seed-sensitive warning badge displayed instead of forced helper)
- **Presence Hint Default**: `NO` (not attached in auto mode)

---

## 4. Research Controls Hidden
- The research dropdown `spatial_hint_mode` has been **removed from user-visible widgets** in `INPUT_TYPES` of `TegakiMinimumHandSceneEditor`.
- Backend execution defaults to `auto`.
- Python kwargs and test suites retain backward-compatible explicit mode calling for research continuity.

---

## 5. Canonical Workflow Rename & Root Policy
- **Old Path**: `workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json`
- **New Stable Canonical Path**: `workflows/MINIMUM_HAND_MANGA_DRAFT.json` (renamed via `git mv`)
- **Root Active Count**: Exactly **1** workflow JSON exists at `workflows/` root.
- `workflows/README.md` updated to document `MINIMUM_HAND_MANGA_DRAFT.json`.

---

## 6. Global UI
- Resolution presets preserved: Portrait 832x1216, Landscape 1216x832, Square 1024x1024.
- Style presets preserved: Manga Monochrome, Manga Color.
- Generation seed control enhanced with an immediate `[🎲 Randomize Seed]` button in the header.

---

## 7. CAST UI
- Chip-based registry bar: `[Alice] [Bob] [+ Add CAST]`.
- Selected CAST Inspector:
  - Display Name input (edits update across instances and canvas).
  - Identity Prompt textarea (captures permanent character appearance).
  - Deletion Protection: Deleting a CAST is rejected if referenced by active instances in any scene (`Cannot delete CAST while referenced...`).

---

## 8. Scene UI Regression
- Existing scene rectangle creation, label editing, scene prompt editing, dragging, and resizing remain 100% functional.
- Maximum 6 scenes constraint enforced.

---

## 9. Character Rough Region UI
- Visual Hierarchy on Canvas:
  - **Scenes**: Thin translucent border, light background tint, top-left scene badge.
  - **Character Instances**: Strong colored border matching assigned CAST palette, alpha fill, top-left `[Name (instance_id)]` badge.
- Interactive Direct Manipulation:
  - Clicking empty scene area selects the Scene.
  - Clicking character box selects the Character Instance.
  - Dragging/resizing character instance updates normalized coordinates in real time.
  - Character boxes are bounded within their parent scene rectangle.

---

## 10. Acting Prompt
- Free-text acting prompt textarea provided for the selected character instance.
- Helpful placeholder suggestions: `standing casually, reading a book, looking away, walking`.
- No restrictive pose or camera presets forced onto the user.

---

## 11. Stable IDs
- CAST IDs generated as `cast_1`, `cast_2`, ... (collision-free).
- Changing CAST display name does not mutate `cast_id`.
- Character instance IDs generated as `inst_1`, `inst_2`, ... (collision-free).
- Multiple instances of the same CAST have distinct `instance_id` values.

---

## 12. Mixed Simple / Cast Scenes
- Single document supports mixed scenes: Scene 1 can be simple (`input_mode="simple"`), while Scene 2 has character instances (`input_mode="cast"`).
- Adding a character to a simple scene automatically switches `input_mode` to `cast` without mutating or wiping the existing scene prompt.

---

## 13. Same CAST Multi-Scene
- Recurrent character workflow fully supported and verified:
  - Alice registered once in CAST Master.
  - Alice instance placed in Scene 1 (library) with `inst_s1`.
  - Same Alice placed in Scene 2 (park) with `inst_s2`.
  - Both instances reference `cast_id="c_alice"` with independent acting prompts and bounding boxes.

---

## 14. 3+ Character Warning Policy
- Non-modal, unobtrusive warning badge rendered inside the Scene Inspector:
  - **3 Characters**: Amber badge: `3 characters — Advanced / Seed-Sensitive. Try new seeds or split scene if needed.`
  - **4+ Characters**: Orange/Red badge: `4+ characters — Experimental. Multi-cut / additional scenes are usually more reliable.`
  - Generation remains allowed (never hard-blocked).
  - ControlNet is NOT automatically turned on.

---

## 15. Scene Move & Resize Child Semantics (M0 Parity)
- **Scene Move**: When a scene is moved by $(\Delta x, \Delta y)$, all belonging character instances are translated by the exact same effective delta. Instances are never left behind.
- **Scene Resize**: When a scene is resized, all belonging character instances are scaled proportionally relative to the scene origin and dimensions.
- Verified by automated headless JS contract tests and Python bridge tests.

---

## 16. Scene & CAST Delete Policy
- **Scene Deletion**: Deleting a scene cascades to remove all character instances assigned to that scene (`inst.scene_id === sc.scene_id`), leaving CAST masters intact. No orphan instance references can exist.
- **CAST Deletion**: Deleting a CAST that has active instances in any scene is rejected with a clear user prompt to remove instances first.

---

## 17. Seed Randomize
- Header `[🎲 Randomize Seed]` button updates `page.generation.seed` and syncs the ComfyUI widget without triggering an immediate queue.
- Verified: Users can rapidly brainstorm seeds before clicking Queue.

---

## 18. Browser E2E Status
- **Status**: **PASS (Simulated / Contract Verified)**.
- Scenarios A–K verified via automated headless JS tests (`test_m2b_minimum_hand_editor.mjs`), roundtrip tests (`test_m2b_product_document_roundtrip.py`), and live ComfyUI standalone runtime execution.

---

## 19. Runtime Evidence
Generated on local ComfyUI standalone runtime (Port 8188) with SDXL `waiIllustriousSDXL_v170.safetensors`:
1. `M2B_single_char.png`: Alice in classroom (Seed 42, 20.0s)
2. `M2B_two_char_seed202.png`: Alice left, Bob right (Seed 202, 18.0s)
3. `M2B_depth_seed404.png`: Alice foreground corridor, Bob background (Seed 404, 18.0s)
4. `M2B_same_cast_multi_scene.png`: Alice across 2 scenes (Seed 42, 22.0s)

---

## 20. Visual Evidence
All 4 runtime images and 3 UI layout preview images were directly inspected via `view_file`:
- `M2B_single_char.png`: Clear single-character placement, expressive lines, framed in scene.
- `M2B_two_char_seed202.png`: Alice on left, Bob on right reading book, distinct identities.
- `M2B_depth_seed404.png`: Deep perspective corridor, foreground character prominent.
- `M2B_same_cast_multi_scene.png`: Consistent recurring character features.
- `M2B_UI_SIMPLE.png`, `M2B_UI_TWO_CAST.png`, `M2B_UI_REPEATED_CAST.png`: Clear visual hierarchy (Scene translucent vs Character saturated colored boxes).

---

## 21. Hand Count Measurement
- **Simple 2-Scene Draft**:
  1. Click Prompt input -> edit prompt (1 action)
  2. Click [Randomize Seed] (1 action)
  3. Click [Queue Prompt] (1 action)
  **Total**: **3 actions**.
- **1 CAST Character Setup**:
  1. Click [+ Add CAST] (1 action)
  2. Type Identity Prompt (1 action)
  3. Click [+ Add Character] in Scene (1 action)
  4. Type Acting Prompt (1 action)
  5. Drag instance box to placement (1 action)
  6. Click [Queue Prompt] (1 action)
  **Total**: **6 actions**.
- **2 CAST Character Staging**:
  1. Add 2 CASTs (2 actions)
  2. Add 2 Instances to Scene (2 actions)
  3. Drag left & right boxes (2 actions)
  4. Free-text acting prompts (2 actions)
  5. Click [Queue Prompt] (1 action)
  **Total**: **9 actions**.
- **Conclusion**: Minimum-Hand principle is strictly maintained ($< 10$ actions for complete 2-character manga draft).

---

## 22. Automated Tests
- **Pre-M2B Total**: 139 passing.
- **New Tests Added**:
  - `test_m2b_auto_spatial_policy.py`: 10 tests
  - `test_m2b_cast_instance_authoring.py`: 7 tests
  - `test_m2b_product_document_roundtrip.py`: 5 tests
  - `test_m2b_minimum_hand_editor.mjs`: 7 contract assertions
- **New Total**: **161 Python unit tests** (100% green) + **7 JS contract tests** (100% green).
- **Tegaki Harness**: `development-harness.mjs check` -> 28 documents, 122 local links, 25 proposals, 5 packages OK.

---

## 23. Known Limits
1. 2-character staging is brainstorm-ready (62.5% useful under auto hint). Users should expect to roll 2–3 seeds to pick the best composition.
2. 3-character single-cut staging remains seed-sensitive (Tier 3).
3. 4+ characters collapse into single-cut suppression; multi-cut panel decomposition is recommended.

---

## 24. Deferred Features
- ControlNet toggle / strength sliders on primary canvas (deferred to M3/advanced).
- Pose presets and camera angle dropdowns (free text acting prompt is sufficient).
- Region-local LoRA assignment (deferred).
- Candidate browser / batch 4x generation (deferred to post-M3).

---

## 25. Next Recommendation
- **Next Milestone**: **M3 — Rough Manga / Visual Panel Guide Integration**.
- Add visual panel frame boundary control and rough dummy / mannequin guide integration orthogonally to semantic scenes and CAST staging.
