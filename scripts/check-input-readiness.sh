#!/usr/bin/env bash
set -euo pipefail
printf 'USB device: '
if lsusb -d 0fca:8004 | grep -q 0fca:8004; then echo PASS; else echo MISSING; fi
printf 'Screenshot viewer: '
if curl --noproxy '*' -fsS --max-time 3 http://127.0.0.1:18765/health >/dev/null; then echo PASS; else echo FAIL; fi
printf 'Bluetooth HID advertised: '
if bluetoothctl info 40:6A:AB:89:F9:20 | grep -Eiq 'Human Interface Device|00001124-'; then echo YES; else echo NO; fi
printf 'BlackBerry JDE toolchain: '
if find /home/SD/BlackBerryBridge /opt -maxdepth 4 \( -iname 'net_rim_api.jar' -o -iname 'rapc.jar' \) -print -quit 2>/dev/null | grep -q .; then echo FOUND; else echo NOT_FOUND; fi
printf 'Input injection: NOT_VERIFIED\n'
