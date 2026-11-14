#!/usr/bin/env bash
# Mirrors the hosted TorchOS CI test matrix. No device access, COD build, or deployment.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1

printf '\n== TorchOS native host and preview tests ==\n'
bash torchos-native/test.sh

printf '\n== Original companion protocol tests ==\n'
python3 -B -m unittest discover -s tests -q

printf '\n== Original S25Hub contract tests ==\n'
python3 -B -m unittest discover -s blackberry-s25-native/tests -q

printf '\nAll three offline TorchOS QA suites passed.\n'
