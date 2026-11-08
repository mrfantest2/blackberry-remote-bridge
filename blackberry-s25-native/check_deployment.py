import os, shutil, sys, urllib.request, urllib.error
from pathlib import Path
root = Path(__file__).resolve().parent
src = (root/'src'/'S25Hub.java').read_text(encoding='utf-8-sig')
checks = {
 'native UI source': 'extends MainScreen' in src and 'new BrowserField' not in src,
 'HTTPS only': 'https://s25.fantest.win' in src,
 'read-only calls': 'HttpConnection.GET' in src and 'HttpConnection.POST' not in src,
 'JDE compiler available': bool(shutil.which('rapc')) or bool(os.environ.get('BLACKBERRY_JDE_HOME') and (Path(os.environ['BLACKBERRY_JDE_HOME'])/'bin'/'rapc.exe').exists()),
 'JDE API available': bool(os.environ.get('BLACKBERRY_JDE_HOME') and list(Path(os.environ['BLACKBERRY_JDE_HOME']).rglob('net_rim_api.jar'))),
}
try:
    request = urllib.request.Request('https://s25.fantest.win/api/native/v1/status', headers={'Accept':'application/json'})
    with urllib.request.urlopen(request, timeout=8) as response:
        checks['live native S25 API'] = response.status == 200 and 'application/json' in response.headers.get('Content-Type','')
except (urllib.error.URLError, TimeoutError) as exc:
    checks['live native S25 API'] = False
    print('API probe:', str(exc))
for name, ok in checks.items(): print(('PASS' if ok else 'BLOCKED') + ': ' + name)
if not all(checks.values()):
    print('NOT DEPLOYABLE: no BlackBerry COD was built or installed')
    sys.exit(2)
print('Prerequisites present; compile and on-device verification still required')
