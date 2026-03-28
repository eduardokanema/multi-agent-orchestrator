---
name: multi-agent-orchestrator
description: Orchestrate software execution work across multiple agents and backends with write-scope isolation, minimal-context worker packets, budget-aware model selection, and conflict escalation. Use when Codex or another coding agent should split a task across Codex, Cursor/Agent, Claude, OpenCode, or similar backends without letting parallel workers step on the same files unless the overlap is explicitly planned and supervised.
---

# Multi-Agent Orchestrator

Split one task into safe, high-signal worker packets. Prefer parallelism only when write scopes are disjoint or when the overlap is explicitly declared and controlled by the main thread.

Keep the orchestration model backend-agnostic:
- decide work in generic terms first
- map it to a concrete CLI only at launch time
- keep Codex and Cursor concrete
- treat Claude and OpenCode as secondary adapters that follow the same manifest contract

## Core Rules

Follow these rules on every orchestration pass:
- identify the critical path before spawning anything
- assign one owner per writable path when possible
- keep worker prompts short and task-local
- start with the cheapest model profile that is still likely to succeed for the specific subtask
- escalate reasoning, model strength, or permissions only after a clear trigger
- keep the main thread as the only authority that may widen scope, widen permissions, or redefine ownership
- verify the shared scaffold, target files, and baseline validation state before launch
- verify backend readiness before launch: CLI available, auth present if needed, model/provider resolved, and working directory mapping confirmed
- define success signals, timeout, captured artifacts, and fallback handling before the worker starts

## Build the Manifest First

Represent the orchestration state in JSON before launching workers. Use:
- `scripts/validate_manifest.py` to check shape and policy
- `scripts/check_write_scope.py` to inspect write collisions
- `scripts/render_worker_packet.py` to generate a backend-specific packet for one worker

Read [manifest details](references/manifest.md) when creating or updating the file.

Required top-level fields:
- `goal`
- `cwd`
- `success_criteria`
- `global_constraints`
- `budget_policy`
- `workers`

Required worker fields:
- `id`
- `task`
- `backend`
- `mode`
- `model_profile`
- `reasoning`
- `permission_profile`
- `depends_on`
- `write_scope`
- `read_scope`
- `commands`
- `tests`
- `escalate_on`
- `non_goals`
- `context_notes`

Recommended execution fields:
- top-level: `preflight_checks`, `post_run_checks`, `run_report`
- worker: `working_directory`, `launch_checks`, `success_signals`, `failure_signals`, `artifacts`, `timeout_seconds`

## Understand the Run Before Launch

Before launching any worker, make the main thread answer these questions explicitly:
- what shared scaffold or prerequisite files must already exist
- what command proves the untouched scaffold is still failing or incomplete in the expected way
- what exact working directory each backend should use
- how relative paths in the packet map to that backend's working directory
- what command or artifact proves the backend is ready for non-interactive execution
- what success signal means the worker really finished
- what timeout or hang condition should stop the worker
- what fallback should happen if one backend stalls while others succeed

Do not start parallel execution until these answers are concrete enough to encode in the manifest or packet.

## Route the Work

Use these generic profiles:
- `cheap`: short read-only analysis, grep-heavy exploration, simple mechanical edits, or focused test reproduction
- `balanced`: normal implementation work with bounded code changes
- `strong`: risky refactors, difficult debugging, or ambiguous code paths
- `review`: independent verification after implementation

Use these permission profiles:
- `read-only`: inspection, planning, or review
- `bounded-edit`: edit only the owned paths and run a narrow command set
- `full-runner`: broader command execution when the worker must build, test, or run integration steps

Prefer `balanced` as the default working profile. Drop to `cheap` for low-risk tasks. Escalate to `strong` only after a concrete blocker such as repeated failure, hidden coupling, or high-impact ambiguity.

Read [routing and conflict policy](references/routing-and-conflicts.md) for the exact escalation triggers.

## Choose the Backend Late

Use the manifest to describe the task first, then map it to a backend.

Prefer:
- Codex for terminal-native execution, structured sandboxing, and non-interactive `exec` flows
- Cursor/Agent for editor-adjacent coding work, worktrees, and quick task execution from the terminal
- Claude when its permission model, tool allowlisting, or budget cap is the best fit
- OpenCode when its configured provider or server flow is already in use

Read [backend capability notes](references/backends.md) before writing launch instructions.

## Launch Small Worker Packets

Each worker packet must include:
- one primary task
- owned write paths
- allowed read paths
- exact commands or tests that matter
- explicit non-goals
- escalation triggers
- budget posture
- launch checks when a backend needs readiness verification
- success and failure signals
- timeout or kill conditions for hung runs
- artifact capture paths for logs, summaries, or last messages

Do not pass the entire parent thread. Give only the context needed to complete the owned work safely.

## Preflight and Monitoring

Use the main thread to perform checks before and during execution:
1. run manifest validation and write-scope validation
2. confirm the shared scaffold or baseline files are present
3. run a baseline failing check when the task starts from incomplete code
4. run backend readiness checks before launching workers
5. launch workers only after readiness is confirmed
6. monitor each worker for timeout, no-output stalls, and out-of-scope writes
7. capture per-worker stdout, stderr, exit status, timing, and changed files in a run report

If one worker fails but others succeed:
- preserve the successful worker outputs
- isolate the failed backend instead of rerunning everything blindly
- decide whether to retry, switch backend, downgrade scope, or complete the remaining work centrally

## Resolve Conflicts Centrally

If two workers need the same file:
- stop and verify whether the overlap is real or just an adjacent read
- if it is avoidable, re-slice ownership and relaunch
- if it is unavoidable, declare the overlap in the manifest, assign a `primary_owner`, and serialize the write sequence
- do not let two workers continue parallel writes to the same path without an explicit handoff plan

If a running worker reports unexpected overlap:
1. freeze conflicting work
2. collect current status, diff, and failing command output
3. update the manifest
4. regenerate worker packets
5. continue only after ownership is unambiguous again

## Close the Task

Before finishing:
1. merge results in dependency order
2. rerun the relevant tests and validations
3. send a separate `review` worker when the change is high risk
4. report what changed, what was verified, and any residual risk
5. include backend readiness findings, timeouts, retries, and partial failures in the final report when they materially affected the run

## References

Load only what you need:
- [references/manifest.md](references/manifest.md) for the JSON contract and overlap fields
- [references/backends.md](references/backends.md) for Codex, Cursor, Claude, and OpenCode mapping guidance
- [references/routing-and-conflicts.md](references/routing-and-conflicts.md) for escalation, cost, and merge policy
- [references/execution-checks.md](references/execution-checks.md) for preflight, timeout, and evidence-capture guidance
