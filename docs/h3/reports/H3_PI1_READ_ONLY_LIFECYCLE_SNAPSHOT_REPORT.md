TEGAKI_REPORT_V1
CARD_ID: H3-PI1
RESULT: PASS WITH LIMIT
INITIAL_HEAD: c0a84f0193bd0a6b4994736507d3b47d3e615d2f
LOCAL_COMMIT: recorded in the live handoff report and final response.
REMOTE_PUBLICATION: NOT PERFORMED — OWNER ACTION REQUIRED

# H3-PI1 Read-Only Lifecycle Snapshot Report

## Result

H3 now exposes a read-only `lifecycle` snapshot through the existing
`GET /api/status` response. The snapshot observes the existing H3 backend
profile, validated Native queue, and H3 Skin session jobs. It does not start,
stop, restart, discover, or reserve any process.

## Snapshot contract

```json
{
  "lifecycle": {
    "native_stop_guard": "SAFE_IDLE | BUSY | BACKEND_UNAVAILABLE | PROFILE_MISMATCH | PROFILE_UNVERIFIABLE",
    "safe_to_stop_native": false,
    "queue_known": true,
    "queue_running_count": 0,
    "queue_pending_count": 0,
    "active_nonterminal_job_count": 0,
    "reason": "short semantic reason"
  }
}
```

`queue_running_count` and `queue_pending_count` are `null` when queue evidence
is not usable. No full argv, absolute machine path, PID, or filesystem secret
is exposed.

## Safe-idle rule

`SAFE_IDLE` and `safe_to_stop_native: true` require all of the following:

- canonical H3 Native profile;
- valid backend `/queue` response;
- empty `queue_running`;
- empty `queue_pending`;
- no active nonterminal H3 Skin job.

Port-open state, a visible Generate button, and client `isGenerating` are not
authoritative lifecycle evidence.

## Fail-closed cases

- queue running or pending entries: `BUSY`, safe `false`;
- H3 `QUEUED`, `RUNNING`, `DISCONNECTED`, or another nonterminal session job:
  `BUSY`, safe `false`;
- completed, failed, and cancelled jobs only: eligible for `SAFE_IDLE`;
- `PROFILE_MISMATCH`: `PROFILE_MISMATCH`, safe `false`;
- `PROFILE_UNVERIFIABLE` or malformed queue: `PROFILE_UNVERIFIABLE`, safe
  `false`;
- unavailable backend: `BACKEND_UNAVAILABLE`, safe `false`.

Malformed queue evidence never becomes zero counts plus `SAFE_IDLE`.

## Verification

- PI1 lifecycle unit and actual H3 `/api/status` handler tests: **12 PASS**;
- H3-R2B profile guard regression: **13 PASS**;
- H3-R2A1 reconnect presentation regression: **10 PASS**;
- H3-R2B UI/static verifier: **16 PASS**;
- full H3 Python server suite: **100 PASS**;
- Python compile checks for changed Python files: **PASS**;
- `git diff --check`: **PASS**;
- real generations: **0**.

The live read-only probe to `http://127.0.0.1:8190/api/status` was attempted;
the Skin was unavailable (`connection refused`). Because this Card forbids
process control and restart, the live canonical idle result is **NOT SAFE TO
PERFORM**. No live `SAFE_IDLE` claim is made.

## Scope audit

- H3 server status/lifecycle observation and H3 tests only;
- no process control, supervisor, shell, launcher, workflow, model, or config
  changes;
- no Generate, active job, History, handoff, or status-vocabulary semantics
  changed;
- no Manga or integration-document changes;
- no JavaScript changes.

## Publication

Local completion is recorded in the live handoff report. Remote publication was
not performed; Owner action is required.

PUSH NOT PERFORMED — OWNER ACTION REQUIRED
