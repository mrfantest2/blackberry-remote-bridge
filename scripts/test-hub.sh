#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile /home/SD/BlackBerryLocalDashboard/serve.py
IP=$(ip -4 -o addr show dev wlo1 | awk '{split($4,a,"/");print a[1];exit}')
[ -n "$IP" ] || { echo 'No Wi-Fi IP' >&2; exit 1; }
systemctl --user is-active --quiet blackberry-hub.service
systemctl --user is-enabled --quiet blackberry-hub-network-watch.timer
for route in / /status /notes /test.html; do
  code=$(curl --noproxy '*' --silent --output /dev/null --write-out '%{http_code}' --max-time 4 "http://$IP:8765$route")
  test "$code" = 200 || { echo "FAIL $route HTTP $code"; exit 1; }
  echo "PASS $route HTTP $code"
done
code=$(curl --noproxy '*' --silent --output /dev/null --write-out '%{http_code}' --max-time 4 -X POST "http://$IP:8765/notes")
test "$code" = 405 || { echo "FAIL POST /notes HTTP $code"; exit 1; }
echo "PASS POST /notes HTTP 405"
