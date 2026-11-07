#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile /home/SD/BlackBerryBridge/project/viewer/server.py
systemctl --user is-active --quiet blackberry-private-viewer.service
for path in / /health /preview.png; do
  code=$(curl --noproxy '*' --silent --output /dev/null --write-out '%{http_code}' --max-time 4 "http://127.0.0.1:18765$path")
  test "$code" = 200 || { echo "FAIL GET $path $code"; exit 1; }
  echo "PASS GET $path HTTP $code"
done
code=$(curl --noproxy '*' --silent --output /dev/null --write-out '%{http_code}' --max-time 4 -X POST http://127.0.0.1:18765/)
test "$code" = 405 && echo "PASS POST HTTP $code"
code=$(curl --noproxy '*' --silent --head --output /dev/null --write-out '%{http_code}' --max-time 4 http://127.0.0.1:18765/)
test "$code" = 405 && echo "PASS HEAD HTTP $code"
bind=$(ss -H -lnt '( sport = :18765 )' | awk '{print $4}')
test "$bind" = '127.0.0.1:18765' || { echo "FAIL viewer bind $bind"; exit 1; }
echo 'PASS viewer loopback-only binding'

# Confirm the MASTER-PC tunnel helper remains bound to loopback on both ends.
python3 - <<'PYTEST'
from pathlib import Path
s=Path('/home/SD/BlackBerryBridge/project/scripts/open-masterpc-viewer.ps1').read_text()
assert 'ExitOnForwardFailure=yes' in s
assert '127.0.0.1:$($LocalPort):127.0.0.1:18765' in s
assert 'SD@100.72.130.8' in s
print('PASS SSH tunnel helper uses localhost endpoints')
PYTEST
