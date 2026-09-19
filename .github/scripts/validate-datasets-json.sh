#!/usr/bin/env bash
# Validate every JSON file under datasets/.
set -euo pipefail
cd "$(dirname "$0")/../.."

# core.quotePath=false keeps non-ASCII names readable instead of \320\277 escapes.
# git already lists paths in sorted order, so no extra sort is needed.
mapfile -t files < <(git -c core.quotePath=false ls-files -- 'datasets/**.json')

if [ ${#files[@]} -eq 0 ]; then
  echo "::error::No JSON files found in datasets/"
  exit 1
fi

python3 -B .github/scripts/lib/validate_json.py "${files[@]}"
