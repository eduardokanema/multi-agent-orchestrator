# Manifest Contract

Use one JSON document as the source of truth for planning, ownership, and handoff generation.

## Top-Level Shape

```json
{
  "goal": "Ship feature X safely with parallel workers",
  "cwd": "/abs/path/to/repo",
  "success_criteria": [
    "All requested behavior is implemented",
    "Target tests pass"
  ],
  "global_constraints": [
    "Do not edit deployment files",
    "Stay under the requested budget"
  ],
  "preflight_checks": [
    "CLI availability and auth verified",
    "Baseline scaffold failure reproduced"
  ],
  "post_run_checks": [
    "Focused tests pass",
    "Run report is written"
  ],
  "run_report": "artifacts/latest-run.json",
  "budget_policy": "balanced",
  "workers": []
}
```

## Worker Shape

```json
{
  "id": "impl-api",
  "task": "Implement the API endpoint and server validation",
  "backend": "codex",
  "mode": "edit",
  "model_profile": "balanced",
  "reasoning": "medium",
  "permission_profile": "bounded-edit",
  "depends_on": [],
  "write_scope": [
    "src/api/",
    "tests/api/"
  ],
  "read_scope": [
    "src/shared/",
    "package.json"
  ],
  "commands": [
    "npm test -- api"
  ],
  "tests": [
    "npm test -- api"
  ],
  "escalate_on": [
    "unexpected-shared-file",
    "repeated-test-failure"
  ],
  "non_goals": [
    "Do not edit UI files"
  ],
  "context_notes": [
    "Reuse existing validation helpers"
  ],
  "working_directory": "src/api/",
  "launch_checks": [
    "npm -v",
    "API fixture file exists"
  ],
  "success_signals": [
    "Focused test passes",
    "Expected files changed only inside write_scope"
  ],
  "failure_signals": [
    "No output for 120s",
    "Unexpected file outside write_scope changes"
  ],
  "artifacts": [
    "artifacts/impl-api-last-message.txt",
    "artifacts/impl-api-test.log"
  ],
  "timeout_seconds": 180
}
```

## Allowed Values

- `backend`: `codex`, `cursor`, `claude`, `opencode`, `generic`
- `mode`: `plan`, `read`, `edit`, `review`
- `model_profile`: `cheap`, `balanced`, `strong`, `review`
- `permission_profile`: `read-only`, `bounded-edit`, `full-runner`
- `budget_policy`: `cheap-first`, `balanced`, `quality-first`

## Optional Execution Fields

Top-level optional fields:
- `preflight_checks`: list of checks the main thread must finish before launch
- `post_run_checks`: list of validations that must run after worker completion
- `run_report`: path where the orchestrator should store machine-readable run results

Worker optional fields:
- `working_directory`: backend-specific launch directory for that worker
- `launch_checks`: list of readiness checks for the worker's backend or environment
- `success_signals`: evidence that the worker actually completed successfully
- `failure_signals`: conditions that should stop or escalate the worker
- `artifacts`: logs or output files that should be captured
- `timeout_seconds`: hard timeout for that worker's live run

Use these fields when the orchestrator is expected to execute workers, not just plan or render packets.

## Overlap Fields

Avoid overlap by default. If a shared write is truly necessary, add these optional fields to every overlapping worker:

```json
{
  "allow_overlap": true,
  "primary_owner": "impl-api",
  "escalation_rule": "Serialize writes. Secondary worker becomes read-only until the primary owner finishes."
}
```

Rules:
- `allow_overlap` must be `true`
- `primary_owner` must point to one of the overlapping workers
- `escalation_rule` must explain how the main thread will serialize or hand off the write
- if any overlapping worker omits these fields, treat the overlap as invalid

## Path Guidance

Use repo-relative paths inside `write_scope` and `read_scope`.

Use repo-relative paths for `working_directory` when practical. If a backend needs a different launch root than the repo root, encode it explicitly so packet paths can be translated correctly at launch time.

Supported forms:
- exact file path: `src/app.ts`
- exact directory path: `src/server/`
- directory wildcard: `src/server/**`

Keep scopes narrow. Prefer exact files when the task is bounded.
