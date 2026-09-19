#!/usr/bin/env bash
# Validate version.json, along with any other JSON living outside datasets/,
# so that no JSON file in the repo escapes validation.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ ! -f version.json ]; then
  echo "::error::version.json is missing"
  exit 1
fi

# core.quotePath=false keeps non-ASCII names readable instead of \320\277 escapes.
mapfile -t files < <(git -c core.quotePath=false ls-files -- '*.json' ':!:datasets/**')

python3 -B .github/scripts/lib/validate_json.py "${files[@]}"
