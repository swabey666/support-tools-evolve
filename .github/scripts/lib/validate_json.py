#!/usr/bin/env python3
"""Validate that every file passed on the command line is valid JSON.

Usage:
    validate_json.py <file> [<file> ...]

Every file is checked, so a single run reports all broken files at once.
"""

import sys

from jsonio import load_json


def main(paths):
    if not paths:
        print("::error::No files to validate")
        return 1

    failed = False
    for path in paths:
        try:
            _, encoding = load_json(path)
        except (OSError, ValueError) as exc:
            print(f"::error file={path}::Invalid JSON: {exc}")
            failed = True
        else:
            print(f"OK: {path} ({encoding})")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
