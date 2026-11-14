#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$ROOT/build"
export PYTHONDONTWRITEBYTECODE=1
python3 -B -m unittest discover -s "$ROOT/tests" -p 'test_*.py' -v 2>&1 | tee "$ROOT/build/tests.log"
