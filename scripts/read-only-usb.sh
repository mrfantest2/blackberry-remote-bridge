#!/usr/bin/env bash
set -euo pipefail
# Deliberately restrict commands to read-only deviceinfo and screenshot.
operation=${1:-}
case "$operation" in deviceinfo|screenshot) ;; *) echo 'Allowed: deviceinfo | screenshot' >&2; exit 2;; esac
ROOT=/home/SD/BlackBerryBridge
SRC="$ROOT/src/barry-master"
USB=$(lsusb -d 0fca:8004 | awk '{gsub(":","",$4);print "/dev/bus/usb/"$2"/"$4;exit}')
test -n "$USB" && test -c "$USB" || { echo 'BlackBerry USB not detected' >&2; exit 3; }
test -x "$SRC/tools/bjavaloader" || { echo 'Barry utility not built' >&2; exit 4; }
mkdir -p "$ROOT/private-captures"
if [[ "$operation" == screenshot ]]; then
  file="torch9810-$(date +%Y%m%d-%H%M%S).bmp"
  args=(screenshot "/captures/$file")
else
  args=(deviceinfo)
fi
podman run --rm --network none --userns keep-id --security-opt label=disable --device "$USB" -v "$SRC:/work:Z" -v "$ROOT/private-captures:/captures:Z" localhost/blackberry-barry-build:ubuntu24 bash -c 'cd /work && timeout 25 ./tools/bjavaloader "$@"' bash "${args[@]}"
if [[ "$operation" == screenshot ]]; then
  test -s "$ROOT/private-captures/$file"
  file -- "$ROOT/private-captures/$file"
  sha256sum -- "$ROOT/private-captures/$file"
fi
