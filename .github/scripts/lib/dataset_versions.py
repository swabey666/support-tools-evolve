#!/usr/bin/env python3
"""Check that every changed dataset got its version bumped by exactly +1.

Usage:
    dataset_versions.py <base version.json> <head version.json> < changed-files.txt

Only the "datasets" section of version.json is looked at. The top-level
"script_version" / "script_version_number" fields describe the script itself,
not the data, and are deliberately never checked here.

The list of changed dataset files is read from stdin, one path per line
(e.g. "datasets/items.json"). For each of them, "datasets.<name>" must equal its
previous value + 1. A dataset that did not exist before must start at 1.
"""

import sys
from pathlib import Path

from jsonio import load_json


def load_dataset_versions(path, missing_ok):
    """Return the "datasets" mapping of a version.json file, ignoring everything else."""
    try:
        data, _ = load_json(path)
    except (OSError, ValueError) as exc:
        if missing_ok:
            print(f"note: cannot read {path} ({exc}); treating every dataset as new")
            return {}
        print(f"::error file=version.json::cannot read {path}: {exc}")
        raise SystemExit(1)

    versions = data.get("datasets") if isinstance(data, dict) else None
    if not isinstance(versions, dict):
        if missing_ok:
            return {}
        print('::error file=version.json::"datasets" must be an object')
        raise SystemExit(1)
    return versions


def changed_datasets(stream):
    """Map each changed dataset's name to the path it was reported under.

    Read as bytes and decoded explicitly, because git always emits paths as
    UTF-8 while sys.stdin would decode them using the ambient locale.
    """
    datasets = {}
    for line in stream.buffer.read().decode("utf-8").splitlines():
        path = line.strip()
        if path:
            datasets.setdefault(Path(path).stem, path)
    return datasets


def as_int(value):
    """Return value as an int, or None if it is not a plain integer."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    base = load_dataset_versions(sys.argv[1], missing_ok=True)
    head = load_dataset_versions(sys.argv[2], missing_ok=False)

    datasets = changed_datasets(sys.stdin)
    if not datasets:
        print("No changed datasets - nothing to check.")
        return 0

    failed = False
    for name, path in datasets.items():
        new = as_int(head.get(name))
        if new is None:
            print(
                f'::error file=version.json::{path} changed, but "datasets.{name}" '
                f"is missing from version.json or is not an integer"
            )
            failed = True
            continue

        previous = as_int(base.get(name))
        previous = 0 if previous is None else previous
        expected = previous + 1

        if new == expected:
            print(f"OK: {path} -> datasets.{name}: {previous} -> {new}")
        else:
            print(
                f'::error file=version.json::{path} changed, so "datasets.{name}" '
                f"must be {expected} (previously {previous}), got {new}"
            )
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
