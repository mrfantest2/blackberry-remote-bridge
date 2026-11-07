from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit
from html import escape
import os, time, subprocess, socket
ROOT='/home/SD/BlackBerryLocalDashboard'
def wifi_ip():
    out=run(['ip','-4','-o','addr','show','dev','wlo1'])
    import re
    match=re.search(r'inet (\d+\.\d+\.\d+\.\d+)/',out)
    return match.group(1) if match else None
CSS='body{font:16px Arial,sans-serif;margin:9px;background:#f3f5f3;color:#18231b}h1{font-size:21px;color:#166339}h2{font-size:17px;margin:0 0 8px}.card{background:white;border:1px solid #bbc9be;padding:11px;margin:10px 0}a{color:#075a9b}nav a{display:inline-block;padding:7px;margin:2px;border:1px solid #aac4b1;background:white}.muted{color:#555;font-size:13px}'
def run(args):
 try: return subprocess.check_output(args,timeout=2,stderr=subprocess.DEVNULL,text=True).strip()
 except Exception: return 'Unavailable'
def page(title,content):
 return ('<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><style>'+CSS+'</style></head><body><h1>Fantest BlackBerry Hub</h1><nav><a href="/">Home</a><a href="/status">Deck Status</a><a href="/notes">Notes</a><a href="/test.html">Test</a></nav>'+content+'<p class="muted">Local network only. Do not enter private data.</p></body></html>').encode('utf-8')
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/':
   content='<div class="card"><h2>Connected</h2>BlackBerry 9810 and Steam Deck are on Abo Jamal Wi-Fi.<p><a href="/status">View live Steam Deck status</a></p></div><div class="card"><h2>Utilities</h2><p><a href="/notes">Local notes</a></p><p><a href="/test.html">Browser navigation test</a></p></div>'
   data=page('BlackBerry Hub',content)
  elif path=='/status':
   uptime=run(['uptime','-p']); mem=run(['free','-m']).splitlines(); memory='Unavailable'
   if len(mem)>1:
    fields=mem[1].split()
    if len(fields)>=3: memory=fields[2]+' / '+fields[1]+' MB'
   load=run(['cat','/proc/loadavg']).split(); battery='Unavailable'
   try:
    for d in os.listdir('/sys/class/power_supply'):
     if os.path.exists('/sys/class/power_supply/'+d+'/type') and open('/sys/class/power_supply/'+d+'/type').read().strip()=='Battery':
      battery=open('/sys/class/power_supply/'+d+'/capacity').read().strip()+'%'; break
   except Exception: pass
   bb=run(['bluetoothctl','info','40:6A:AB:89:F9:20'])
   bb_connected='Connected' if 'Connected: yes' in bb else 'Disconnected'
   import re
   match=re.search(r'Battery Percentage: 0x([0-9a-fA-F]+)',bb)
   bb_battery=str(int(match.group(1),16))+'%' if match else 'Unavailable'
   content='<div class="card"><h2>BlackBerry 9810</h2><p>Bluetooth: '+bb_connected+'</p><p>Battery: '+bb_battery+'</p></div><div class="card"><h2>Steam Deck</h2><p>Uptime: '+escape(uptime)+'</p><p>Battery: '+escape(battery)+'</p><p>Load (1 min): '+escape(load[0] if load else '?')+'</p><p>RAM (MB): '+memory+'</p><p>Wi-Fi IP: '+escape(wifi_ip() or 'Unavailable')+'</p><p>Updated: '+escape(time.strftime('%Y-%m-%d %H:%M:%S'))+'</p><a href="/status">Refresh</a></div>'
   data=page('Steam Deck Status',content)
  elif path=='/notes':
   content='<div class="card"><h2>Local Notes</h2><p>Notes are intentionally read-only in this prototype. The dashboard does not accept text uploads or save private information over HTTP.</p><p>Use the BlackBerry Notes application for offline personal notes.</p></div>'
   data=page('Notes',content)
  elif path=='/test.html':
   data=page('Navigation Test','<div class="card"><h2>Navigation test passed</h2><p>If this appears on the BlackBerry, local page navigation works.</p><a href="/">Back to dashboard</a></div>')
  else:
   self.send_error(404); return
  self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Content-Length',str(len(data))); self.end_headers()
  if self.command!='HEAD': self.wfile.write(data)
 def do_HEAD(self): self.do_GET()
 def do_POST(self): self.send_error(405,'Read-only dashboard')
address=wifi_ip()
if not address: raise RuntimeError('Wi-Fi wlo1 has no IPv4 address; retry via systemd')
ThreadingHTTPServer((address,8765),Handler).serve_forever()
