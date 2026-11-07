#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE=${BARRY_SOURCE:-/home/SD/BlackBerryBridge/src/barry-master}
LOGDIR=${BARRY_BUILD_LOGDIR:-/home/SD/BlackBerryBridge/build-logs}
mkdir -p "$LOGDIR"
test -f "$SOURCE/configure.ac" || { echo "Missing upstream Barry source: $SOURCE" >&2; exit 2; }
# Never mount /dev/bus/usb or grant privileges to a build container.
podman build -f "$HERE/Containerfile.barry" -t localhost/blackberry-barry-build:ubuntu24 "$HERE" 2>&1 | tee "$LOGDIR/container-build.log"
"$HERE/scripts/patch-barry.sh" "$SOURCE"
podman run --rm --network none -v "$SOURCE:/work:Z" localhost/blackberry-barry-build:ubuntu24 bash -c 'set -e; ./buildgen.sh; ./configure --disable-gui --disable-desktop --disable-opensync-plugin --disable-opensync-plugin-4x; make -j2 -C src; make -j2 -C tools bjavaloader' 2>&1 | tee "$LOGDIR/barry-build.log"
