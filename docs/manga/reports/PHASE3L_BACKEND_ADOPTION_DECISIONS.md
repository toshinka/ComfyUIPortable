# Phase 3L: External Backend Adoption Decisions Report

- **Date**: 2026-09-05
- **Document ID**: `docs/reports/PHASE3L_BACKEND_ADOPTION_DECISIONS.md`
- **Phase**: ComfyUI Portable Phase 3L Gate Closure
- **Governing Architecture Plan**: `Tegaki_ComfyUI_Manga_Authoring_Intermediate_Plan_PriorArt_Integration.md`

---

## 1. Final Adoption Decisions

### Regional Prompt Execution
- **Decision**: **ADAPT**
- **Rationale**:
  1. Inspire Pack's `RegionalPromptSimple` demonstrates that a standard `BASIC_PIPE` + `MASK` + `Prompt` interface can successfully construct Impact-compatible regional prompts without duplicating custom sampler code.
  2. However, Tegaki's manga authoring needs (multi-panel remainder mask subtraction, subscene scoping, and shot-type-aware character conditioning) require a compiler layer to orchestrate the prompt-mask pairs before backend ingestion.
  3. Therefore, Tegaki adapts the thin pipe interface pattern: the Tegaki Semantic Compiler emits standard prompt/mask tuples, allowing users to plug into either Inspire `RegionalPromptSimple` or Impact `RegionalSampler` interchangeably.

---

### ControlNet Application
- **Decision**: **ADOPT**
- **Rationale**:
  1. `ComfyUI-Advanced-ControlNet`'s `ACN_AdvancedControlNetApply_v2` natively supports `effect_mask` (`mask_optional`) along with flexible timestep scheduling (`start_percent`, `end_percent`).
  2. Testing confirms that applying regional controlnet guides via Advanced-ControlNet's effect masks achieves equal or superior spatial guidance compared to custom conditioning metadata propagation.
  3. Tegaki will focus exclusively on generating the semantic guide imagery (directional mannequins, panel frames, interaction clasps), delegating the actual tensor application to Advanced-ControlNet.

---

### Mask Editor Tooling
- **Decision**: **DEFER**
- **Rationale**:
  1. Developing a custom, fully interactive freehand brush/lasso canvas node inside Tegaki would consume substantial engineering effort and introduce significant web UI maintenance overhead.
  2. Existing ComfyUI solutions—specifically Impact Pack's `PreviewBridge` combined with the native Clipspace MaskEditor—already provide reliable raster mask editing capabilities.
  3. Tegaki defers building a custom mask brush canvas until the Dedicated GUI phase, relying on automated parametric mask generation with optional Clipspace touch-ups for the foreseeable authoring roadmap.

---

### Pose Editor Tooling
- **Decision**: **DEFER**
- **Rationale**:
  1. Full skeletal 3D/2D joint manipulation is already mature in third-party extensions like `ComfyUI-OpenPose-Editor` and external desktop posing utilities.
  2. Tegaki's automated directional mannequin system (`standing_neutral`, `facing_left`, `facing_right`, `sitting`) provides immediate, zero-touch layout guidance that satisfies 90%+ of manga staging scenarios without user fatigue.
  3. Tegaki defers building an in-node joint manipulator and instead formalizes the `Character Instance ↔ Pose Asset` contract, allowing users to optionally feed external OpenPose reference images directly into character instances.

---

## 2. Summary Gate Table

| Feature Area | Decision | Primary Rationale | Implementation Status in Phase 3L |
| :--- | :--- | :--- | :--- |
| **Regional Prompt** | **ADAPT** | Thin pipe adapter over Inspire/Impact | Verified in Workflow 71 |
| **ControlNet** | **ADOPT** | Use Advanced-ControlNet effect masks | Verified in unit & schema tests |
| **Mask Editor** | **DEFER** | Avoid wheel reinvention; use Clipspace | Automated masks + bridge contract |
| **Pose Editor** | **DEFER** | Keep auto-mannequin; link pose assets | Directional presets + external slot |

---

## 3. Sign-off Status
- **Audit Gate Passed**: YES
- **Backend Adoption Consensus**: Complete
- **Next Phase Integration**: Phase 3M (Progressive Manga Authoring UX Integration)
