# Backend Capability Notes

Choose the backend after the task is already shaped in generic manifest terms.

## Preflight For Every Backend

Before launch, verify:
- the CLI is installed and callable
- the backend can run non-interactively in the intended working directory
- auth and provider assumptions are satisfied
- the exact model alias or provider/model pair is resolved
- the main thread has a timeout, success signal, and artifact capture plan

## Codex

Best for:
- terminal-native execution
- explicit sandbox selection
- non-interactive `exec` runs
- structured output and resumable sessions

Useful command shape:

```bash
codex exec -C <cwd> -m <model> -s workspace-write -o /tmp/last-message.txt "<prompt>"
```

Low-cost readiness check:

```bash
codex exec -C <cwd> --skip-git-repo-check --full-auto -o /tmp/codex-smoke.txt "Reply with exactly OK."
```

Useful knobs:
- `-m`, `--model`
- `-s`, `--sandbox`
- `--add-dir`
- `--json`
- `--output-last-message`

Use when the orchestrator wants strong control over workspace, sandbox, and command execution.

## Cursor / Agent

Best for:
- editor-adjacent code work
- isolated worktrees
- fast terminal launches with model choice

Useful command shape:

```bash
cursor agent --print --workspace <cwd> --model <model> "<prompt>"
```

Low-cost readiness check:

```bash
cursor agent --print --trust --force --workspace <cwd> "Reply with exactly OK."
```

Useful knobs:
- `--model`
- `--workspace`
- `--plan`
- `--sandbox`
- `--worktree`
- `--output-format`

Use when the worker benefits from Cursor's agent environment or worktree support.

## Claude

Best for:
- explicit permission and tool allowlisting
- effort control
- direct budget caps

Useful command shape:

```bash
claude -p --permission-mode default --model <model> --effort <level> "<prompt>"
```

Useful knobs:
- `--model`
- `--effort`
- `--allowed-tools`
- `--add-dir`
- `--max-budget-usd`
- `--permission-mode`

Treat Claude as a secondary adapter in this skill. Keep the same manifest contract and map permission or effort choices at launch time.

## OpenCode

Best for:
- environments that already route through OpenCode providers
- server or attached-session flows
- provider/model pairs that are already configured outside the skill

Useful command shape:

```bash
opencode run --dir <cwd> --model <provider/model> --variant <variant> "<prompt>"
```

More reliable automation shape when cold starts are expensive:

```bash
opencode serve --hostname 127.0.0.1 --port 4096
opencode run --attach http://127.0.0.1:4096 --dir <cwd> --model <provider/model> "<prompt>"
```

Useful knobs:
- `--model`
- `--variant`
- `--dir`
- `--agent`
- `--format`
- `--attach`

Treat OpenCode as a secondary adapter in this skill. It fits the same manifest and packet model, but the exact provider choice should usually come from the local OpenCode setup.

Operational notes:
- prefer an explicit provider/model pair over implicit defaults
- prefer `serve` plus `run --attach` for repeated or parallel automation runs
- use a narrow `--dir` so relative paths match the worker scope
- treat no-output stalls as failures and enforce a main-thread timeout
- capture logs or a run report because hangs may not return useful stdout

## Adapter Rules

Apply these rules for every backend:
- keep the packet backend-specific but the planning contract backend-neutral
- translate `model_profile` to a local model alias late
- translate `permission_profile` to local flags late
- if a backend cannot express the required restriction cleanly, downgrade the worker to `read-only` or switch backend
- if a backend cannot enforce safe writes for the task, do not use it for overlapping edit work
- if a backend cannot complete a smoke test or readiness check, do not send it a live edit task yet
- if path mapping differs by backend, make the worker's `working_directory` explicit and rewrite packet paths accordingly
