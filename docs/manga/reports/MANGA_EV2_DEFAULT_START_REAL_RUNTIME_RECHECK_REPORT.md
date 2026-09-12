# MANGA-EV2 Default Start Real Runtime Recheck Report

- Card: `MANGA-EV2`
- Channel: `RUNTIME_VALIDATION`
- Executor: `CODEX`
- Date: `2026-09-12`
- Result: `PASS`
- Initial HEAD: `f940fad3f9b462b6d9170b1c6b9d7aca4a0a1791`
- Baseline: `HEAD == origin/main == f940fad3f9b462b6d9170b1c6b9d7aca4a0a1791`
- Explicit startup timeout override used: `NO`
- Product source changes: `NONE`
- H3 activity: `NONE`
- Manga generations: `0`
- Remote publication: `NOT PERFORMED`

This is a Manga-only default-start recheck. H3, generation, authoring UI,
schema, and unrelated lifecycle work were not touched. TEGAKI-EV1 history is
not rewritten.

## Base and preflight

- Worktree was clean at the start.
- `git fetch origin` returned the previously observed local error:
  `error: cannot open '.git/FETCH_HEAD': Permission denied`.
- The visible refs were independently checked and both resolved to the Card
  baseline above.
- `127.0.0.1:8189` and `127.0.0.1:8191` were free before launch.
- No unknown or pre-existing process was terminated.

## Production default start

`new MangaDomainRuntime()` was instantiated with no configuration arguments.
Observed production defaults:

```text
backend: http://127.0.0.1:8189
workspace: http://127.0.0.1:8191
startupWaitTimeoutMs: 120000
shutdownTimeoutMs: 3000
```

The real `await runtime.start()` returned `READY` in approximately `19.37 s`,
well before the 120-second production deadline. No timeout override was used.

The owned backend command record was:

```text
python_embeded/python.exe -s ComfyUI/main.py --listen 127.0.0.1 --port 8189
  --disable-auto-launch --output-directory output/Tegaki
```

## Process ownership and identity

Both services were spawned by this validation instance and tracked as:

| Service | PID | Ownership | Evidence |
| --- | ---: | --- | --- |
| Manga backend | `16608` | `OWNED_BY_THIS_RUNTIME` | exact ChildProcess record |
| Manga workspace | `28152` | `OWNED_BY_THIS_RUNTIME` | exact ChildProcess record |

The public READY checkpoint was PASS:

- Public runtime state: `READY`.
- `GET /queue`: HTTP 200 with `queue_running` and `queue_pending` arrays,
  both empty.
- `GET /object_info/TegakiMinimumHandSceneEditor`: HTTP 200 with the exact
  `TegakiMinimumHandSceneEditor` key.
- `POST /tegaki/manga/generation/prepare` with JSON `{}`: HTTP 400,
  `ok == false`, `error_code == MISSING_DOCUMENT`.
- Re-read `GET /queue`: valid and idle.
- No `/prompt` call was made.

Workspace identity was PASS:

```json
{
  "service": "tegaki_manga_workspace",
  "version": "1.0.0",
  "domain": "manga",
  "authoring_schema": "1.0.0",
  "backend_target": "http://127.0.0.1:8189"
}
```

## Minimal cleanup

`await runtime.stopAll()` returned PASS. Both exact retained ChildProcess
handles exited with intentional `SIGTERM` observations:

```text
backend:   PID 16608, signal SIGTERM, intentional true
workspace: PID 28152, signal SIGTERM, intentional true
```

After cleanup:

- `backendProcessRecord == null` and `workspaceProcessRecord == null`.
- Backend and workspace ownership both cleared to `UNAVAILABLE`.
- `GET /queue` on 8189 was unreachable.
- `/api/runtime/identity` on 8191 was unreachable.
- Final port checks found no listeners on 8189 or 8191.
- Card-owned Manga orphan children: `0`.
- Kill-by-port: `ABSENT`.

## Classification

| Item | Result |
| --- | --- |
| Production `startupWaitTimeoutMs` | `120000` |
| Explicit startup timeout override | `NO` |
| Default `runtime.start()` | `PASS` |
| Observed startup elapsed | `19.37 s` |
| Backend ownership | `OWNED_BY_THIS_RUNTIME` |
| Workspace ownership | `OWNED_BY_THIS_RUNTIME` |
| Backend positive Manga identity | `PASS` |
| Workspace identity | `PASS` |
| Public lifecycle state | `READY` |
| Queue | `IDLE` |
| `stopAll()` | `PASS` |
| Card-owned orphan children | `0` |
| Manga generations | `0` |

All MANGA-EV2 required conditions passed. Manga M1 real-runtime lifecycle
closeout is `SUPPORTED` by this recheck. Owner/SOL audit status remains a
separate acceptance/publication concern.

## Return

```text
TEGAKI_REPORT_V1
CARD_ID: MANGA-EV2
RESULT: PASS
EXECUTOR: CODEX

Initial HEAD:
f940fad3f9b462b6d9170b1c6b9d7aca4a0a1791

Production startupWaitTimeoutMs: 120000
Explicit startup timeout override used: NO
Default runtime.start: PASS
Observed startup elapsed: 19.37 seconds
Backend ownership: OWNED_BY_THIS_RUNTIME
Workspace ownership: OWNED_BY_THIS_RUNTIME
Backend positive Manga identity: PASS
Workspace identity: PASS
Public lifecycle state: READY
Queue: IDLE
Manga generations: 0
stopAll: PASS
Card-owned orphan children: 0
Kill-by-port: ABSENT
Product source changes: NONE
H3 activity: NONE
Docs-only local commit: PENDING
Remote publication: NOT PERFORMED
Manga M1 real-runtime closeout: SUPPORTED

Recommended next:
SOL AUDIT -> MANGA M1 CLOSEOUT

STOP
```
