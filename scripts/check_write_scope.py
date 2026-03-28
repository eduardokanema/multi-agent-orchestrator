#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import PurePosixPath


def normalize_scope_entry(entry: str) -> tuple[str, bool]:
    raw = entry.strip()
    if not raw:
        raise ValueError("Scope entries must be non-empty strings")

    wildcard_dir = raw.endswith("/**")
    directory = raw.endswith("/") or wildcard_dir
    if wildcard_dir:
        raw = raw[:-3]
    normalized = str(PurePosixPath(raw.rstrip("/")))
    if normalized == ".":
        normalized = ""
    return normalized, directory or wildcard_dir


def overlaps(left: tuple[str, bool], right: tuple[str, bool]) -> tuple[bool, str]:
    left_path, left_is_dir = left
    right_path, right_is_dir = right

    if left_path == right_path:
        return True, "same-path"

    if left_is_dir and right_path.startswith(left_path + "/"):
        return True, "left-contains-right"

    if right_is_dir and left_path.startswith(right_path + "/"):
        return True, "right-contains-left"

    return False, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Report overlapping worker write scopes.")
    parser.add_argument("manifest", help="Path to a manifest JSON file")
    args = parser.parse_args()

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    workers = manifest.get("workers", [])
    findings = []

    parsed_workers = []
    for worker in workers:
        entries = []
        for raw_entry in worker.get("write_scope", []):
            if not isinstance(raw_entry, str):
                raise ValueError(f"Worker {worker.get('id')} has a non-string write_scope entry")
            entries.append((raw_entry, normalize_scope_entry(raw_entry)))
        parsed_workers.append((worker.get("id"), entries))

    for index, (left_id, left_entries) in enumerate(parsed_workers):
        for right_id, right_entries in parsed_workers[index + 1 :]:
            for left_raw, left_norm in left_entries:
                for right_raw, right_norm in right_entries:
                    hit, reason = overlaps(left_norm, right_norm)
                    if hit:
                        findings.append(
                            {
                                "left_worker": left_id,
                                "right_worker": right_id,
                                "left_scope": left_raw,
                                "right_scope": right_raw,
                                "reason": reason,
                            }
                        )

    json.dump(findings, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
