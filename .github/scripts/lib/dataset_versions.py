#!/usr/bin/env python3
"""Check the dataset version bookkeeping around version.json.

Usage:
    dataset_versions.py <base version.json> <head version.json> [<dataset> ...]
        < changed-files.txt

Two rules are enforced, each tied to what actually changed:

  * a dataset file that changed must have its "datasets.<name>" entry bumped by
    exactly +1; a dataset that did not exist before must start at 1;
  * a version.json that changed must agree with the datasets: every entry must
    equal the "version" field of the dataset file it describes, and both sides
    must list the same datasets. This runs over every dataset, not just the
    changed ones, because any edit to version.json can desynchronise any entry.

Only the "datasets" section of version.json is looked at. The top-level
"script_version" / "script_version_number" fields describe the script itself,
not the data, and are deliberately never checked here.

The changed files are read from stdin, one path per line (e.g. "datasets/
items.json", "version.json"); the datasets to compare version.json against are
passed on the command line, so that a rename cannot hide a stale entry.
"""

import sys
from pathlib import Path

from jsonio import load_json

VERSION_JSON = "version.json"
DATASETS_DIR = "datasets/"


def load_dataset_versions(path, missing_ok):
    """Return the "datasets" mapping of a version.json file, ignoring everything else."""
    try:
        data, _ = load_json(path)
    except (OSError, ValueError) as exc:
        if missing_ok:
            print(f"note: cannot read {path} ({exc}); treating every dataset as new")
            return {}
        print(f"::error file={VERSION_JSON}::cannot read {path}: {exc}")
        raise SystemExit(1)

    versions = data.get("datasets") if isinstance(data, dict) else None
    if not isinstance(versions, dict):
        if missing_ok:
            return {}
        print(f'::error file={VERSION_JSON}::"datasets" must be an object')
        raise SystemExit(1)
    return versions


def changed_paths(stream):
    """Return the changed paths, one per line.

    Read as bytes and decoded explicitly, because git always emits paths as
    UTF-8 while sys.stdin would decode them using the ambient locale.
    """
    lines = stream.buffer.read().decode("utf-8").splitlines()
    return [path for path in (line.strip() for line in lines) if path]


def as_int(value):
    """Return value as an int, or None if it is not a plain integer."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def dataset_version(path):
    """Return (version, problem) for a dataset's own "version" field.

    Exactly one of the two is None: a problem describes, in a form that reads
    after "cannot check it against version.json:", why no version was found.
    """
    try:
        data, _ = load_json(path)
    except (OSError, ValueError) as exc:
        return None, f"cannot read it ({exc})"

    if not isinstance(data, dict):
        return None, "its top level is not an object"

    version = as_int(data.get("version"))
    if version is None:
        return None, 'it has no integer "version" field'

    return version, None


def check_bumps(changed, base, head):
    """Require datasets.<name> == previous + 1 for every changed dataset."""
    failed = False
    for name, path in sorted(changed.items()):
        new = as_int(head.get(name))
        if new is None:
            print(
                f'::error file={VERSION_JSON}::{path} changed, but "datasets.{name}" '
                f"is missing from {VERSION_JSON} or is not an integer"
            )
            failed = True
            continue

        previous = as_int(base.get(name))
        previous = 0 if previous is None else previous
        expected = previous + 1

        if new == expected:
            print(f"OK: {path} changed -> datasets.{name}: {previous} -> {new}")
        else:
            print(
                f'::error file={VERSION_JSON}::{path} changed, so "datasets.{name}" '
                f"must be {expected} (previously {previous}), got {new}"
            )
            failed = True
    return failed


def check_sync(paths, head):
    """Require datasets.<name> to equal the dataset's own "version", both ways round."""
    failed = False
    listed_by = {}

    for path in sorted(paths):
        name = Path(path).stem
        listed_by[name] = path

        version, problem = dataset_version(path)
        if problem is not None:
            print(f"::error file={path}::cannot check it against {VERSION_JSON}: {problem}")
            failed = True
            continue

        listed = as_int(head.get(name))
        if listed is None:
            print(
                f'::error file={VERSION_JSON}::{path} is at version {version}, but '
                f'"datasets.{name}" is missing from {VERSION_JSON} or is not an integer'
            )
            failed = True
        elif listed != version:
            print(
                f'::error file={VERSION_JSON}::"datasets.{name}" is {listed}, but {path} '
                f'has "version": {version} - both must be the same number'
            )
            failed = True
        else:
            print(f"OK: datasets.{name} == {path} version: {version}")

    for name in sorted(set(head) - set(listed_by)):
        print(
            f'::error file={VERSION_JSON}::"datasets.{name}" has no dataset file '
            f"({DATASETS_DIR}{name}.json)"
        )
        failed = True

    return failed


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    base = load_dataset_versions(sys.argv[1], missing_ok=True)
    head = load_dataset_versions(sys.argv[2], missing_ok=False)
    datasets = sys.argv[3:]

    changed = changed_paths(sys.stdin)
    changed_by_name = {}
    for path in changed:
        if path.startswith(DATASETS_DIR):
            changed_by_name.setdefault(Path(path).stem, path)

    failed = False

    if changed_by_name:
        failed |= check_bumps(changed_by_name, base, head)
    else:
        print("No dataset changed - no version bump to require.")

    if VERSION_JSON in changed:
        failed |= check_sync(datasets, head)
    else:
        print(f"{VERSION_JSON} did not change - not compared against the datasets.")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
