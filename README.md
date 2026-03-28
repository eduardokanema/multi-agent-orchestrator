# multi-agent-orchestrator

Orchestrate software execution work across multiple agents and backends with write-scope isolation, minimal-context worker packets, budget-aware model selection, and explicit conflict handling.

This skill is for cases where one agent should coordinate several workers across tools like Codex, Cursor/Agent, Claude, or OpenCode without letting parallel edits collide.

## What It Does

- Builds a manifest-first plan before launching any worker
- Keeps write ownership explicit so parallel workers do not step on the same files
- Generates backend-specific worker packets from one shared contract
- Encourages cheap-first routing, narrow scope, and escalation only when justified
- Treats the main thread as the authority for widening scope, permissions, or ownership

## Quick Start

If you use an npm-based skill CLI, install the skill with:

```bash
npx skill add multi-agent-orchestrator
```

Then invoke it in Codex by asking for the skill directly, for example:

```text
Use the multi-agent-orchestrator skill to split this feature into parallel workers with disjoint write scopes.
```

## Workflow

1. Define the goal, constraints, and success criteria.
2. Create a JSON manifest that describes workers, ownership, commands, tests, and escalation rules.
3. Validate the manifest and check for write-scope collisions.
4. Render a focused worker packet for each backend.
5. Launch only after preflight checks, backend readiness, and baseline validation are concrete.
6. Merge in dependency order and run the post-run checks.

## Repository Layout

- `SKILL.md`: main skill instructions and orchestration rules
- `references/manifest.md`: JSON manifest contract and overlap policy
- `references/backends.md`: backend mapping guidance for Codex, Cursor, Claude, and OpenCode
- `references/routing-and-conflicts.md`: routing rules and escalation triggers
- `references/execution-checks.md`: preflight, timeout, and evidence-capture guidance
- `scripts/validate_manifest.py`: validates manifest structure and policy
- `scripts/check_write_scope.py`: checks worker write-scope collisions
- `scripts/render_worker_packet.py`: renders a backend-specific worker packet
- `agents/openai.yaml`: backend configuration asset

## Example Commands

Validate a manifest:

```bash
python3 scripts/validate_manifest.py path/to/manifest.json
```

Check write-scope conflicts:

```bash
python3 scripts/check_write_scope.py path/to/manifest.json
```

Render a worker packet:

```bash
python3 scripts/render_worker_packet.py path/to/manifest.json impl-api
```

## When To Use It

Use this skill when:

- the task can be split into independent workers
- different workers need different backends or budgets
- write ownership must stay explicit
- the main thread should supervise handoffs and overlap resolution

Do not use it when one agent can finish the work cleanly without coordination overhead.
