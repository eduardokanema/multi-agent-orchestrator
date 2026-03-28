#!/usr/bin/env python3
import argparse
import json
from textwrap import dedent


BACKEND_HINTS = {
    "codex": dedent(
        """\
        Backend notes:
        - Prefer `codex exec` for non-interactive work.
        - Map `permission_profile` to Codex sandbox settings late.
        - Use structured output or last-message capture when the main thread needs machine-readable status.
        """
    ).strip(),
    "cursor": dedent(
        """\
        Backend notes:
        - Prefer `cursor agent --print` for terminal launches.
        - Use `--workspace` or `--worktree` when isolation is needed.
        - Keep the packet concise because Cursor already sees the workspace.
        """
    ).strip(),
    "claude": dedent(
        """\
        Backend notes:
        - Use `claude -p` for non-interactive runs.
        - Translate permission needs to `--permission-mode` and `--allowed-tools`.
        - Apply budget limits at launch time when needed.
        """
    ).strip(),
    "opencode": dedent(
        """\
        Backend notes:
        - Use `opencode run` with the local provider/model pair.
        - Map reasoning needs to the local variant model.
        - Keep the packet backend-neutral and configure provider details outside the manifest.
        """
    ).strip(),
    "generic": dedent(
        """\
        Backend notes:
        - Apply the manifest contract first.
        - Translate model and permission profiles to the local agent platform at launch time.
        """
    ).strip(),
}


def bullet_block(items):
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def optional_section(title, items):
    if not items:
        return ""
    return f"\n{title}:\n{bullet_block(items)}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a worker packet from a manifest.")
    parser.add_argument("manifest", help="Path to a manifest JSON file")
    parser.add_argument("worker_id", help="Worker id to render")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    worker = next((item for item in manifest.get("workers", []) if item.get("id") == args.worker_id), None)
    if worker is None:
        raise SystemExit(f"Worker not found: {args.worker_id}")

    backend = worker["backend"]
    packet = f"""\
Worker packet: {worker['id']}

Goal:
- {worker['task']}

Execution profile:
- backend: {backend}
- mode: {worker['mode']}
- model_profile: {worker['model_profile']}
- reasoning: {worker['reasoning']}
- permission_profile: {worker['permission_profile']}
- working_directory: {worker.get('working_directory', manifest['cwd'])}
- timeout_seconds: {worker.get('timeout_seconds', 'unset')}

Global preflight:
{bullet_block(manifest.get('preflight_checks', []))}

Write scope:
{bullet_block(worker['write_scope'])}

Read scope:
{bullet_block(worker['read_scope'])}

Validation:
{bullet_block(worker['tests'])}

Commands:
{bullet_block(worker['commands'])}

Non-goals:
{bullet_block(worker['non_goals'])}

Escalate immediately if:
{bullet_block(worker['escalate_on'])}

Context notes:
{bullet_block(worker['context_notes'])}

Dependencies:
{bullet_block(worker['depends_on'])}

Budget posture:
- global policy: {manifest['budget_policy']}
- use the declared model_profile first; escalate only on a listed trigger

Run report:
- {manifest.get('run_report', 'unset')}

Post-run checks:
{bullet_block(manifest.get('post_run_checks', []))}

{BACKEND_HINTS.get(backend, BACKEND_HINTS['generic'])}
{optional_section('Launch checks', worker.get('launch_checks'))}{optional_section('Success signals', worker.get('success_signals'))}{optional_section('Failure signals', worker.get('failure_signals'))}{optional_section('Artifacts', worker.get('artifacts'))}"""
    print(packet.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
