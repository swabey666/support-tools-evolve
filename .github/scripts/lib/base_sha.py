#!/usr/bin/env python3
"""Print the commit that the current run should be compared against.

The value comes from the GitHub event payload that the runner drops at
$GITHUB_EVENT_PATH: pull requests are compared against their base branch,
pushes against the previous tip of the branch.

Nothing is printed when there is no usable base - a manual run, or the first
push of a new branch. Callers treat that as "nothing to compare".
"""

import json
import os


def base_sha():
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, encoding="utf-8") as fh:
            event = json.load(fh)
    except (OSError, ValueError):
        return ""

    pull_request = event.get("pull_request") or {}
    base = (pull_request.get("base") or {}).get("sha")
    return base or event.get("before") or ""


if __name__ == "__main__":
    print(base_sha())
