#!/usr/bin/env bash
# Local compilation only. Never signs, installs, contacts a device, or downloads tools.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
JDE_HOME=${JDE_HOME:-/home/SD/BlackBerryBridge/toolchains/blackberry-jde-7.0.0}
JDK8_HOME=${JDK8_HOME:-${JAVA_HOME:-/home/SD/BlackBerryBridge/toolchains/jdk8}}
WTK_HOME=${WTK_HOME:-/home/SD/BlackBerryBridge/toolchains/wtk252}
mkdir -p "$ROOT/build/tmp"
cd "$ROOT/build"
exec > >(tee build.log) 2>&1
# Remove only this module's old outputs so a failed run cannot appear successful.
rm -f TorchOS.cod TorchOS.jar TorchOS.jad TorchOS.cso TorchOS.debug TorchOS.rapc TorchOS.err
for input in "$JDE_HOME/rapc.jar" "$JDE_HOME/net_rim_api.jar" "$ROOT/src/TorchOS.java"; do
    if [[ ! -f "$input" ]]; then printf 'Missing build input: %s\n' "$input"; exit 1; fi
done
for program in "$JDK8_HOME/bin/java" "$JDK8_HOME/bin/javac" "$WTK_HOME/bin/preverify"; do
    if [[ ! -x "$program" ]]; then printf 'Missing executable: %s\n' "$program"; exit 1; fi
done
I686_LIBS=${I686_LIBS:-/home/SD/BlackBerryBridge/toolchains/i686-libs/usr/lib}
if [[ -d "$I686_LIBS" ]]; then
    export LD_LIBRARY_PATH="$I686_LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
export JAVA_HOME="$JDK8_HOME"
export PATH="$JDK8_HOME/bin:$WTK_HOME/bin:$PATH"
export TMPDIR="$ROOT/build/tmp"
printf 'Authentic local JDE build\nJDE_HOME=%s\nJDK8_HOME=%s\nWTK_HOME=%s\n' "$JDE_HOME" "$JDK8_HOME" "$WTK_HOME"
"$JDK8_HOME/bin/java" -version
cp "$ROOT/TorchOS.rapc" TorchOS.rapc
"$JDK8_HOME/bin/java" -Djava.io.tmpdir="$TMPDIR" -jar "$JDE_HOME/rapc.jar" \
    "import=$JDE_HOME/net_rim_api.jar" codename=TorchOS TorchOS.rapc "$ROOT/src/TorchOS.java"
test -s TorchOS.cod
printf '\nCOD generated locally; unsigned, not installed or device-tested.\n'
sha256sum TorchOS.cod
