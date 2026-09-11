# Manga Product Integration Boundary

Updated: 2026-09-11 JST
Source: XT-ALIGN1 / Manga Integration Boundary Synchronization
M3B: M3B_PRODUCTION_CLOSED
Classification: MANGA_READY_FOR_INTEGRATION_DESIGN
Shared-shell implementation: NOT AUTHORIZED

---

## 1. Manga Product Entry

- **Canonical documentation entry**: `ComfyUIPortable/GITHUB_MANGA.txt`
- **Domain handoff anchor**: `ComfyUIPortable/docs/manga/WEBGPT_SOL_LUNA_HANDOFF.md`
- **Primary UI Editor**: `TegakiMinimumHandSceneEditor` (`minimum_hand_scene_editor.js` / `.py`)
- **Interactive Action**: `✨ Generate Draft` button with live preview route badge (`Generation: Standard` vs `Generation: Guide-assisted`).

---

## 2. Manga-Owned Endpoint

- **Endpoint**: `POST /tegaki/manga/generation/prepare`
- **Responsibility**: Authoritative backend routing decision, prompt validation, and workflow preparation at queue time.
- **Contract**: Rejects invalid states; maps document to either `STANDARD_NO_GUIDE` or `GUIDED_CLEAN_GLOBAL` prompt structure; fails closed on missing ControlNet.
- **Frontend boundary**: Frontend badge is preview only; queue-time endpoint response is authoritative.

---

## 3. Manga-Owned Workflows

- **Standard Workflow**: `workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json`
  - Zero ControlNet dependencies (no loader, no apply node, no bridge).
- **Guided Workflow**: `workflows/manga/MINIMUM_HAND_MANGA_GUIDED_DRAFT.json`
  - Core ComfyUI `ControlNetApplyAdvanced` + `TegakiMangaGenerationGuideBridge`.
  - Zero Advanced-ControlNet (ACN) dependencies.
  - Zero effect masks (effect mask: NONE).

---

## 4. Persistent Schema Identity

- **Schema Name**: `TEGAKI_AUTHORING_DOCUMENT`
- **Schema Version**: `1.0.0`
- **Persistence Boundary**: Document JSON stored in `document_json` widget.
- **Forbidden in Schema**: Route decisions, backend workflow selection, ControlNet enabled states, or transient runtime execution flags are strictly derived runtime states and MUST NOT be persisted into schema.

---

## 5. Standard / Guided Routing Contract

| Authoring Document State | Route Selected | Backend Path |
|---|---|---|
| No Guide | `STANDARD_NO_GUIDE` | Standard prompt (0 ControlNet) |
| Disabled Guide | `STANDARD_NO_GUIDE` | Standard prompt (0 ControlNet) |
| Enabled Guide + 0 Figures | `STANDARD_NO_GUIDE` | Standard prompt (0 ControlNet) |
| Enabled Guide + >=1 valid Figure | `GUIDED_CLEAN_GLOBAL` | Core `ControlNetApplyAdvanced` (strength 0.75, start 0.0, end 1.0) |

- **One-Action OFF**: Disabling rough guide immediately changes route to Standard.
- **Re-Enable**: Enabling rough guide immediately restores Guided route.
- **CAST Independence**: Presence or absence of CAST does not dictate route eligibility.
- **Unassigned Figures**: Legal input for Guided route.
- **Missing Model Policy**: If AnyTest ControlNet model is absent when Guided route is selected, explicit `GUIDED_CONTROLNET_NOT_AVAILABLE` error is raised; no silent fallback to Standard.

---

## 6. Guide Semantics

- **RAW Asset**: Raster image is reference/editing canvas only; RAW pixels NEVER forward to ControlNet.
- **Production Guide**: Flat-silhouette mannequin derived deterministically from validated Figure Regions.
- **Provenance**: Guide Figure Regions provide rough visual provenance for Character placement.
- **Seed Contract**: Seed randomness is an intentional creative brainstorming feature. Guide assistance is coarse and non-destructive; it does not enforce rigid tracing or exact camera matches.

---

## 7. Queue Ownership

- Client calls `POST /tegaki/manga/generation/prepare` with document JSON.
- Endpoint constructs validated API prompt.
- Client submits prompt via `api.queuePrompt`.
- **Invariants**:
  - No global queue monkeypatching.
  - No visible LiteGraph graph swapping.
  - No ComfyUI core modifications.
  - Locked `isGenerating` state prevents double-submit.

---

## 8. Shared Installation and Runtime Hosting

- **Shared Portable Installation**: Both tracks are distributed within the same `ComfyUIPortable` repository / installation.
- **Runtime Hosting**: The currently verified domain runtime profiles are not identical.
  - Manga requires its Manga-capable custom-node/runtime path.
  - H3 is currently verified using an isolated Native backend profile with all custom nodes disabled (`--disable-all-custom-nodes`).
- **Single Shared ComfyUI Backend Process**: `NOT YET VERIFIED`.
  - A future shared TEGAKI shell must treat backend hosting as an architecture decision rather than assuming one already-compatible `8188` process.
- **Future Runtime Hosting Categories** (Classification: `RUNTIME HOSTING: OPEN DESIGN QUESTION`):
  - A. One compatible shared backend profile.
  - B. Separate H3 and Manga backend processes.
  - C. Common launcher supervising domain-specific services.
  - D. Another architecture selected by future cross-track review.
- **Domain Independence**: Shared installation does NOT imply merged domain logic. Each domain maintains its own custom nodes, endpoints, schemas, workflows, and tests.

---

## 9. Provisional Information Architecture (IA)

Coordination vocabulary only:

```text
TEGAKI
├─ H3
│  ├─ Video
│  ├─ Still
│  └─ Prep/Edit
└─ Manga
```

Status: `CONCEPTUAL ONLY / NOT FINAL IA / NOT AUTHORIZATION TO IMPLEMENT`.

---

## 10. Areas Future Shell MAY Wrap

The future TEGAKI top-level shell may:
1. Provide top-level navigation between product tracks (`H3` and `Manga`).
2. Manage shared application window layout, theme, and tab headers.
3. Host independent domain canvases within separated tabs/views.
4. Provide high-level launcher entry points to open ComfyUI with domain configurations.

---

## 11. Areas Future Shell MUST NOT Merge Implicitly

The future shell MUST NOT:
1. Merge document schemas (Manga `TEGAKI_AUTHORING_DOCUMENT` remains distinct from H3 project specs).
2. Merge backend workflows or generation pipelines.
3. Merge server API routes (`/tegaki/manga/...` remains Manga-exclusive).
4. Combine history databases or overwrite Manga output namespace (`output/Tegaki`).
5. Share generation queue logic or monkeypatch ComfyUI queue submission.
6. Create automatic cross-track asset-handoff without formal architectural specification.

---

## 12. Current Readiness

- **Manga Track Status**: `MANGA_READY_FOR_INTEGRATION_DESIGN`
- **H3 Track Status**: `H3_READY_FOR_INTEGRATION_DESIGN`
- **Cross-Track Architecture Design**: `READY FOR REVIEW`
- **Shared Portable Installation**: `YES`
- **Single Shared 8188 Backend**: `NOT YET VERIFIED`
- **Runtime Hosting**: `OPEN DESIGN QUESTION`
- **Shared-Shell Implementation**: `NOT AUTHORIZED`
  - Implementation remains unauthorized because IA, runtime hosting, launcher/service ownership, History/Preview ownership, and cross-track asset handoff have not yet been selected by a formal cross-track architecture review.
- **Final Owner Product Review**: `DEFERRED`
