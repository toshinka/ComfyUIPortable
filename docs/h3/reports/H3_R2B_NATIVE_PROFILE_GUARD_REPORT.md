TEGAKI_REPORT_V1
CARD_ID: H3-R2B
RESULT: PASS
INITIAL_HEAD: 5c7bc70f732acf9bb8c3598874a0a62aadfc21e7
LOCAL_COMMIT: final SHA is recorded in the live handoff report and final response.
REMOTE_PUBLICATION: NOT PERFORMED

# H3-R2B Native Profile Guard Report

Card: `H3-R2B`
Channel: `H3`
Target: `LUNA`
Base SHA: `5c7bc70f732acf9bb8c3598874a0a62aadfc21e7`

## Result

PASS — the reachable Native backend is now required to prove the canonical H3
profile before H3 reports `READY` or submits `/prompt`.

## Live `/system_stats` evidence

The canonical Native runtime was running and idle before coding.

- `GET http://127.0.0.1:8188/system_stats`: HTTP 200.
- `GET http://127.0.0.1:8188/queue`: HTTP 200; `queue_running: []`, `queue_pending: []`.
- Observable system: `win32`, ComfyUI `0.30.0`, embedded Python `true`, deploy environment `local-portable`.
- Observable Native argv, recorded exactly:

```text
D:\GitHub\tegaki\ComfyUIPortable\ComfyUI\main.py
--listen 127.0.0.1
--port 8188
--disable-auto-launch
--disable-manager
--disable-all-custom-nodes
--extra-model-paths-config D:\GitHub\tegaki\ComfyUIPortable\h3\config\extra_model_paths.yaml
--output-directory D:\GitHub\tegaki\ComfyUIPortable\output\h3
--input-directory D:\GitHub\tegaki\ComfyUIPortable\output\h3
--user-directory D:\GitHub\tegaki\ComfyUIPortable\output\h3\h3_native_user
--temp-directory D:\GitHub\tegaki\ComfyUIPortable\output\h3\h3_native_temp
--database-url sqlite:///:memory:
--log-stdout
```

The shim itself is intentionally not required in argv because the effective
ComfyUI argv exposes `ComfyUI/main.py`.

## Canonical validation rule

`h3/app/native_profile.py` is a pure validator over `system.system.argv` and a
runtime-derived expectation. It verifies the canonical ComfyUI entrypoint,
127.0.0.1 and configured Native port, `--disable-all-custom-nodes`, either
supported H3 model-path config (`extra_model_paths.yaml` or
`extra_model_paths.local.yaml`), H3 output/input namespace, H3 user/temp
namespaces, and `sqlite:///:memory:`. Windows path case and separator variation
is normalized. Full argv and machine paths are not returned by the H3 status API.

Classifications are:

- `CANONICAL_H3` — all required markers and a valid queue response match.
- `PROFILE_MISMATCH` — observable evidence clearly disagrees with the H3 contract.
- `PROFILE_UNVERIFIABLE` — argv/profile or queue evidence is missing or unusable.
- `UNAVAILABLE` — the existing status path cannot reach Native.

## Fail-closed behavior

- `PROFILE_MISMATCH` and `PROFILE_UNVERIFIABLE` are returned as non-Ready H3
  backend states with short semantic detail.
- The Generate control remains unavailable unless backend state is `READY`.
- `BackendClient.submit()` rechecks `/system_stats` and `/queue` immediately
  before any `/prompt` request. A wrong reachable backend therefore fails with
  `kind: backend_profile` before submission.
- Existing active-job recovery semantics, job vocabulary, active/preview job
  separation, and R2A1 backend-detail ownership are unchanged.

## Deterministic test matrix

- A canonical H3 argv: `CANONICAL_H3` — PASS.
- B missing `--disable-all-custom-nodes`: `PROFILE_MISMATCH` — PASS.
- C wrong model-path config: `PROFILE_MISMATCH` — PASS.
- D wrong output namespace: `PROFILE_MISMATCH` — PASS.
- E wrong user/temp namespace: `PROFILE_MISMATCH` — PASS.
- F non-memory database: `PROFILE_MISMATCH` — PASS.
- G missing/unusable argv evidence: `PROFILE_UNVERIFIABLE` — PASS.
- H unreachable Native through `/api/status`: `UNAVAILABLE` profile with
  `DISCONNECTED` service state — PASS.
- I supported `.local.yaml` model config: accepted — PASS.
- J Windows path case/separator variation: accepted after normalization — PASS.

Wrong-backend integration used a local stub where `/system_stats` and `/queue`
were reachable but output namespace was wrong. H3 status was not Ready,
submission raised `BackendProfileError`, and `/prompt` call count was `0`.

## Live canonical check

The changed `BackendClient` was run against the current canonical Native runtime:

```json
{"state":"READY","backend_profile":"CANONICAL_H3","backend_profile_detail":"Canonical H3 Native profile verified.","queue_count":0,"running_count":0}
```

No model was loaded and no generation was submitted.

## Verification

- R2B UI/static verifier: `16 PASS`.
- R2A1 reconnect verifier: `10 PASS`.
- R1 Stage/Generate verifier: `61 PASS`.
- H1B.1 P2 verifier: `44 PASS`.
- VP1 and IP2 static verifiers: PASS.
- H3 Python tests: `88 OK`.
- Changed Python `py_compile`: PASS.
- Changed JavaScript `node --check`: PASS.
- `git diff --check`: PASS.
- Real generations: `0`.

## Scope and publication

- Runtime/backend implementation changes: H3 status/profile guard only.
- Manga changes: `NONE`.
- Workflow/model changes: `NONE`.
- Launcher/shim changes: `NONE`.
- `GITHUB_H3.txt` / `GITHUB_MANGA.txt`: unchanged.
- Remote publication: `NOT PERFORMED`.
- Local commit: final SHA is recorded in the live handoff report and final response.

PUSH NOT PERFORMED — OWNER ACTION REQUIRED

Recommended next: `SOL AUDIT -> H3 R2 CLOSEOUT / AGENT ALLOCATION DECISION`
