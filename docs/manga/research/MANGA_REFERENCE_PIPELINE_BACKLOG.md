# Manga Reference Pipeline & Identity Backlog

## 1. Purpose

This document normalizes and preserves the future Manga Reference and Identity feature backlog so that it can be designed and implemented cleanly in a later milestone without re-researching.

Future targets include:
- Recurring Character identity consistency across panels (Character A, Character B).
- Fixed character appearance vs. dynamic outfit variations (retaining face identity while clothing changes).
- Recurring props and set objects (e.g., broadcast cameras, tools, recurring equipment).
- Acting and performance references (expression, gesture, and pose continuity).

---

## 2. Responsibility Boundaries

- **H3 vs. Manga Isolation**: H3 and Manga remain strictly separate production and runtime domains. Any future reference-asset interchange between H3 and Manga must be explicit, decoupled, and bounded.
- **Spatial Authority (No Duplicate Geometry)**: Future Reference/Identity workflows must reuse existing Scene (`page.scenes[].area`) and Character Instance (`page.character_instances[].area`) spatial boundaries. No parallel or duplicate coordinate systems will be introduced.
- **Physical Reference Storage TBD**: Physical storage paths for reference images are not yet determined. Storage architecture is deferred to the implementation design phase (do not assume paths like `manga/storage/references/`).
- **Production UI Surface**: `Cast & References` is only a candidate future production surface concept. It is not currently implemented or finalized.

---

## 3. Current Readiness Classification

### Schema (`TEGAKI_AUTHORING_DOCUMENT 1.0.0`)
- **EXISTS**:
  - `page.cast[]`: Declares character identities, names, and text prompts.
  - `page.character_instances[]`: Bounded character placements inside scenes.
  - `page.guides[]`: Independent guide assets and figure regions.
- **DOES NOT EXIST**:
  - `reference_assets`
- **Classification**: Reference asset durable schema remains **MISSING / FUTURE DESIGN**.

### IP-Adapter & Vision Conditioning
- **ComfyUI core vision/reference primitives**: **EXISTS** (underlying node and tensor execution capabilities present in environment).
- **Manga regional IP-Adapter execution**: **MISSING** (current generation compiler evaluates style, scene prompts, LoRA extraction, regional masks, and acting prompts, but does not inject regional image conditioning).
- **External / custom node integrations**: **FUTURE RESEARCH** (model weights, IP-Adapter Plus/ClipVision loaders, and unified node pipelines require explicit benchmarking).

---

## 4. ReForge Migration Order

The long-term migration and retirement sequence is strictly ordered:

1. **Current**: ReForge is required to cover MRP (Manga Replacement Protocol / Reference Pipeline) and Reference/IP-Adapter-related needs.
2. **Intermediate**: Migration of Reference and Identity capabilities to ComfyUI reduces ReForge's primary remaining Manga-specific dependency strictly to MRP.
3. **Final**: Porting and enhancing MRP natively on ComfyUI allows full retirement of ReForge.

Reference Pipeline migration is an essential enabling milestone that isolates ReForge dependency to MRP, rather than the final exit milestone itself.

---

## 5. Design Candidates (Not Canonical Schema)

The following reference concepts are **DESIGN CANDIDATES** for future exploration, not durable schema definitions:

- **Character Reference Card**: Preserves core character identity (facial features, hair, age, baseline appearance).
- **Outfit Reference Card**: Defines specific costume/wardrobe assets, allowing character identity to persist across outfit changes.
- **Prop Reference Card**: Maintains visual continuity for recurring inanimate objects or equipment.
- **Performance Reference Card**: Guides posture, gesture, expression, or dynamic staging. (Note: May overlap future ControlNet, pose estimation, or guide layer responsibilities).

---

## 6. Start Conditions & Phased Direction

Implementation of the Reference Pipeline should only begin after current Scene-aware regional generation (Play 5 / Play 6) has fully stabilized.

- **Phase 1: Schema & Storage Definition**: Design durable schema representation for reference assets and define physical storage lifecycle without breaking document compatibility.
- **Phase 2: Execution Graph**: Construct bounded backend execution graph combining regional scene masks with vision conditioning (IP-Adapter / ClipVision).
- **Phase 3: Authoring Workspace Integration**: Expose candidate `Cast & References` management UI in Manga Authoring workspace.
