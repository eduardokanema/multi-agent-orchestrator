# Routing and Conflict Policy

## Cost and Quality Routing

Use this order of preference:
- `cheap` for search, inspection, or low-risk mechanical work
- `balanced` for most implementation tasks
- `strong` only for risky refactors, repeated failures, or deep ambiguity
- `review` for independent verification after code changes

Escalate only when a trigger is real:
- two failed attempts on the same blocker
- hidden dependency outside the owned scope
- repeated failing tests with unclear cause
- need to change shared infrastructure or core abstractions

De-escalate when:
- the remaining work is mechanical
- the task is mostly renaming, plumbing, or adding tests around already-known behavior
- the worker is only gathering facts for the main thread

## Context Rules

Keep worker packets small:
- one primary task
- only the owned files and directly relevant shared files
- one short constraint list
- exact validation commands

Do not include:
- long architecture essays
- unrelated backlog items
- the full parent thread
- hidden conclusions the worker should discover from the code or artifact itself

## Execution Readiness

Before launch:
- confirm the shared scaffold or target files already exist
- confirm the baseline state is understood: passing, failing, or intentionally stubbed
- verify backend readiness with explicit `launch_checks`
- verify the worker `working_directory` matches the path references in the packet
- define `success_signals`, `failure_signals`, and `timeout_seconds`
- define which artifacts or logs must be captured

## Conflict Prevention

Before launch:
- run `scripts/check_write_scope.py`
- if the scopes overlap and the overlap is not declared, reslice the work
- if the overlap is declared, keep one `primary_owner` and serialize the write phase

Common bad splits:
- two workers both editing the same service file
- one worker owning `src/**` and another owning `src/api/**`
- one worker changing a generator input while another changes the generated output

## Unexpected Overlap

If a worker reports overlap after launch:
1. stop parallel writes for the conflicting workers
2. capture current progress and failure output
3. decide whether to move ownership, serialize the write, or collapse the tasks into one worker
4. regenerate packets with the new scope

Do not resolve overlap by letting both workers continue and relying on a later merge.

## Runtime Monitoring

When workers are live:
- monitor stdout, stderr, exit status, timing, and changed files
- treat no-output stalls separately from normal failures
- kill workers that exceed their timeout instead of waiting indefinitely
- preserve successful workers if another backend hangs
- write a run report even when the overall orchestration fails

If only one backend fails:
1. keep successful worker outputs intact
2. inspect the failed worker's artifacts and readiness assumptions
3. retry only that worker if the scope is still valid
4. switch backend or collapse the remaining work only after the failure mode is clear

## Merge and Review

Merge in dependency order:
- foundational implementation
- dependent implementation
- tests
- review

Use a separate `review` worker when:
- shared files were touched
- the task had serialized overlap
- the change affected core behavior
- the execution path involved elevated permissions or strong reasoning
- the live run involved retries, timeouts, or backend-specific failures
