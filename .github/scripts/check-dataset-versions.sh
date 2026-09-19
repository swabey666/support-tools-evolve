#!/usr/bin/env bash
# Keep the dataset versions and version.json in step, in both directions:
#
#   * a dataset that changed must get its version.json entry bumped by +1;
#   * a version.json that changed must match the "version" field of every
#     dataset it describes.
#
# Runs only when something relevant actually changed: if neither version.json
# nor a file under datasets/ did, the script exits successfully.
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
  "$base_sha" HEAD -- 'datasets/**.json' version.json)"

if [ -z "$changed" ]; then
  echo "Neither version.json nor any dataset changed - nothing to check."
  exit 0
fi

echo "Changed files:"
echo "$changed"

# Every dataset, not just the changed ones: a changed version.json is compared
# against all of them. git already lists paths in sorted order.
mapfile -t datasets < <(git -c core.quotePath=false ls-files -- 'datasets/**.json')

base_version="$(mktemp)"
trap 'rm -f "$base_version"' EXIT
git show "$base_sha:version.json" > "$base_version" 2>/dev/null || echo '{}' > "$base_version"

echo "$changed" | python3 -B .github/scripts/lib/dataset_versions.py \
  "$base_version" version.json "${datasets[@]}"
