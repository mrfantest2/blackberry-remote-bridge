#!/usr/bin/env bash
set -euo pipefail
current=$(ip -4 -o addr show dev wlo1 | awk '{split($4,a,"/");print a[1];exit}')
[ -n "$current" ] || exit 0
if ! ss -ltnH '( sport = :8765 )' | awk '{print $4}' | grep -Fxq "$current:8765"; then
  systemctl --user restart blackberry-hub.service
fi
