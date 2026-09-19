#!/usr/bin/env bash
# Require a +1 version bump for every dataset changed since the base commit.
#
# Runs only when a file under datasets/ actually changed: if none did, there is
# nothing to bump and the script exits successfully without checking anything.
set -euo pipefail
cd "$(dirname "$0")/../.."

readonly EMPTY_SHA=0000000000000000000000000000000000000000

base_sha="$(python3 -B .github/scripts/lib/base_sha.py)"

if [ -z "$base_sha" ] || [ "$base_sha" = "$EMPTY_SHA" ]; then
  echo "No base commit to compare against - nothing to check."
  exit 0
fi

if ! git cat-file -e "${base_sha}^{commit}" 2>/dev/null; then
  echo "Base commit $base_sha is unavailable (force push?) - nothing to check."
  exit 0
fi

# core.quotePath=false keeps non-ASCII names readable instead of \320\277 escapes.
changed="$(git -c core.quotePath=false diff --name-only --diff-filter=ACMR \
  "$base_sha" HEAD -- 'datasets/**.json')"

if [ -z "$changed" ]; then
  echo "No dataset file changed - nothing to check."
  exit 0
fi

echo "Changed datasets:"
echo "$changed"

base_version="$(mktemp)"
trap 'rm -f "$base_version"' EXIT
git show "$base_sha:version.json" > "$base_version" 2>/dev/null || echo '{}' > "$base_version"

echo "$changed" | python3 -B .github/scripts/lib/dataset_versions.py "$base_version" version.json
