#!/usr/bin/env bash
set -euo pipefail
source_root=${1:-/home/SD/BlackBerryBridge/src/barry-master}
target="$source_root/src/tarfile.cc"
test -f "$target"
python3 - "$target" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); s=p.read_text()
if '#include <ctime>' in s:
    print('PATCH_ALREADY_APPLIED')
elif '#include <stdlib.h>' in s:
    p.write_text(s.replace('#include <stdlib.h>', '#include <stdlib.h>\n#include <ctime>',1))
    print('PATCH_APPLIED time header')
else: raise SystemExit('Unexpected source layout; refusing to patch')
PY
