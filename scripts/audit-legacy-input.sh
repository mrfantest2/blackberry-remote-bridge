#!/usr/bin/env bash
# Read-only compatibility evidence. Never sends USB commands.
set -euo pipefail
printf 'USB='; if lsusb -d 0fca:8004 | grep -q 0fca:8004; then echo PRESENT; else echo ABSENT; fi
printf 'VIEWER='; curl --noproxy '*' --max-time 4 -fsS http://127.0.0.1:18765/health >/dev/null && echo PASS || echo FAIL
printf 'BARRY_INPUT_API='; if grep -RliE 'EventInjector|SendKey|InjectKey|InjectTouch' /home/SD/BlackBerryBridge/src/barry-master/src --include='*.h' --include='*.cc' 2>/dev/null | grep -q .; then echo REVIEW_REQUIRED; else echo NOT_FOUND; fi
printf 'LEGACY_SDK='; if find /home/SD/BlackBerryBridge /opt -maxdepth 5 \( -iname net_rim_api.jar -o -iname rapc.jar \) -print -quit 2>/dev/null | grep -q .; then echo FOUND; else echo NOT_FOUND; fi
printf 'DEVICE_INPUT_CONTROL=UNVERIFIED\n'
