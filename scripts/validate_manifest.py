#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict, deque

from check_write_scope import normalize_scope_entry, overlaps


TOP_LEVEL_REQUIRED = {
    "goal",
    "cwd",
    "success_criteria",
    "global_constraints",
    "budget_policy",
    "workers",
}

WORKER_REQUIRED = {
    "id",
    "task",
    "backend",
    "mode",
    "model_profile",
    "reasoning",
    "permission_profile",
    "depends_on",
    "write_scope",
    "read_scope",
    "commands",
    "tests",
    "escalate_on",
    "non_goals",
    "context_notes",
}

ALLOWED_BACKENDS = {"codex", "cursor", "claude", "opencode", "generic"}
ALLOWED_MODES = {"plan", "read", "edit", "review"}
ALLOWED_MODEL_PROFILES = {"cheap", "balanced", "strong", "review"}
ALLOWED_PERMISSION_PROFILES = {"read-only", "bounded-edit", "full-runner"}
ALLOWED_BUDGET_POLICIES = {"cheap-first", "balanced", "quality-first"}


def validate_non_empty_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def validate_required_keys(obj, required_keys, label):
    missing = sorted(required_keys - set(obj))
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def validate_string_list(worker, key):
    value = worker[key]
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Worker {worker['id']} field '{key}' must be a list of non-empty strings")


def validate_optional_string_list(obj, key, label):
    if key not in obj:
        return
    value = obj[key]
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} field '{key}' must be a list of non-empty strings")


def validate_optional_non_empty_string(obj, key, label):
    if key not in obj:
        return
    validate_non_empty_string(obj[key], f"{label} field '{key}'")


def validate_optional_positive_int(obj, key, label):
    if key not in obj:
        return
    value = obj[key]
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} field '{key}' must be a positive integer")


def validate_workers(workers):
    ids = set()
    for worker in workers:
        if not isinstance(worker, dict):
            raise ValueError("Each worker must be a JSON object")
        validate_required_keys(worker, WORKER_REQUIRED, f"Worker {worker.get('id', '<missing-id>')}")

        worker_id = worker["id"]
        validate_non_empty_string(worker_id, "Each worker id")
        if worker_id in ids:
            raise ValueError(f"Duplicate worker id: {worker_id}")
        ids.add(worker_id)

        validate_non_empty_string(worker["task"], f"Worker {worker_id} field 'task'")
        if worker["backend"] not in ALLOWED_BACKENDS:
            raise ValueError(f"Worker {worker_id} has invalid backend: {worker['backend']}")
        if worker["mode"] not in ALLOWED_MODES:
            raise ValueError(f"Worker {worker_id} has invalid mode: {worker['mode']}")
        if worker["model_profile"] not in ALLOWED_MODEL_PROFILES:
            raise ValueError(f"Worker {worker_id} has invalid model_profile: {worker['model_profile']}")
        if worker["permission_profile"] not in ALLOWED_PERMISSION_PROFILES:
            raise ValueError(f"Worker {worker_id} has invalid permission_profile: {worker['permission_profile']}")

        if not isinstance(worker["depends_on"], list) or any(not isinstance(dep, str) or not dep.strip() for dep in worker["depends_on"]):
            raise ValueError(f"Worker {worker_id} field 'depends_on' must be a list of worker ids")

        for key in ("write_scope", "read_scope", "commands", "tests", "escalate_on", "non_goals", "context_notes"):
            validate_string_list(worker, key)

        validate_non_empty_string(worker["reasoning"], f"Worker {worker_id} field 'reasoning'")
        validate_optional_non_empty_string(worker, "working_directory", f"Worker {worker_id}")
        validate_optional_positive_int(worker, "timeout_seconds", f"Worker {worker_id}")
        for key in ("launch_checks", "success_signals", "failure_signals", "artifacts"):
            validate_optional_string_list(worker, key, f"Worker {worker_id}")

    unknown_deps = []
    for worker in workers:
        for dep in worker["depends_on"]:
            if dep not in ids:
                unknown_deps.append((worker["id"], dep))
    if unknown_deps:
        pairs = ", ".join(f"{worker}->{dep}" for worker, dep in unknown_deps)
        raise ValueError(f"Unknown dependency reference(s): {pairs}")


def validate_dependency_graph(workers):
    indegree = defaultdict(int)
    graph = defaultdict(list)

    for worker in workers:
        indegree[worker["id"]] += 0
        for dep in worker["depends_on"]:
            graph[dep].append(worker["id"])
            indegree[worker["id"]] += 1

    queue = deque(node for node, count in indegree.items() if count == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if visited != len(workers):
        raise ValueError("Worker dependency graph contains a cycle")


def validate_overlaps(workers):
    normalized = {}
    for worker in workers:
        normalized[worker["id"]] = []
        for raw in worker["write_scope"]:
            normalized[worker["id"]].append((raw, normalize_scope_entry(raw)))

    for index, left in enumerate(workers):
        for right in workers[index + 1 :]:
            for left_raw, left_norm in normalized[left["id"]]:
                for right_raw, right_norm in normalized[right["id"]]:
                    hit, _ = overlaps(left_norm, right_norm)
                    if not hit:
                        continue
                    if not left.get("allow_overlap") or not right.get("allow_overlap"):
                        raise ValueError(
                            f"Workers {left['id']} and {right['id']} overlap on "
                            f"{left_raw} / {right_raw} without declared overlap fields"
                        )
                    primary_owner = left.get("primary_owner")
                    if primary_owner != right.get("primary_owner"):
                        raise ValueError(
                            f"Workers {left['id']} and {right['id']} must share the same primary_owner"
                        )
                    if primary_owner not in {left["id"], right["id"]}:
                        raise ValueError(
                            f"Workers {left['id']} and {right['id']} must choose one overlapping worker as primary_owner"
                        )
                    if not left.get("escalation_rule") or not right.get("escalation_rule"):
                        raise ValueError(
                            f"Workers {left['id']} and {right['id']} must declare escalation_rule for overlap"
                        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a multi-agent orchestration manifest.")
    parser.add_argument("manifest", help="Path to a manifest JSON file")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    validate_required_keys(manifest, TOP_LEVEL_REQUIRED, "Manifest")
    validate_non_empty_string(manifest["goal"], "Manifest field 'goal'")
    validate_non_empty_string(manifest["cwd"], "Manifest field 'cwd'")

    if manifest["budget_policy"] not in ALLOWED_BUDGET_POLICIES:
        raise ValueError(f"Invalid budget_policy: {manifest['budget_policy']}")

    for key in ("success_criteria", "global_constraints"):
        if not isinstance(manifest[key], list) or any(not isinstance(item, str) or not item.strip() for item in manifest[key]):
            raise ValueError(f"Manifest field '{key}' must be a list of non-empty strings")

    for key in ("preflight_checks", "post_run_checks"):
        validate_optional_string_list(manifest, key, "Manifest")
    validate_optional_non_empty_string(manifest, "run_report", "Manifest")

    workers = manifest["workers"]
    if not isinstance(workers, list) or not workers:
        raise ValueError("Manifest field 'workers' must be a non-empty list")

    validate_workers(workers)
    validate_dependency_graph(workers)
    validate_overlaps(workers)

    print("Manifest is valid.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
