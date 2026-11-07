#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/SD/BlackBerryBridge
"$ROOT/project/scripts/read-only-usb.sh" screenshot
newest=$(find "$ROOT/private-captures" -maxdepth 1 -name 'torch9810-*.bmp' -type f -printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-)
test -s "$newest" || { echo 'No screenshot produced' >&2; exit 3; }
mkdir -p "$ROOT/private-previews"
chmod 700 "$ROOT/private-previews"
# Convert only on the Deck; do not publish on HTTP or add images to Git.
magick "$newest" -strip -quality 90 "$ROOT/private-previews/latest.png"
chmod 600 "$ROOT/private-previews/latest.png"
identify -format 'Preview: %wx%h %m\n' "$ROOT/private-previews/latest.png"
sha256sum "$ROOT/private-previews/latest.png"
