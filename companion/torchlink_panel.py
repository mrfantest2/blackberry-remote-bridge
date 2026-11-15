"""TorchLink control panel: browser buttons + live screenshot for TorchOS on the Torch 9810.

Runs on the Steam Deck. Combines:
  * the TorchLink listener (phone dials out over Wi-Fi; one paired phone at a time,
    re-accepts after a session ends; authenticated STATUS keep-alive at 45 s), and
  * a LOOPBACK-ONLY web panel (default 127.0.0.1:18766).

Panel safety:
  * binds only to a loopback address (refuses anything else);
  * every request needs the random per-run token printed at start;
  * Host header must be the loopback address:port (blocks DNS rebinding);
  * commands are POST with a custom X-Panel-Token header (blocks cross-site forms);
  * only TorchLink's allowlisted ops (TorchOS's own screens) can be sent;
  * screenshots come from an operator-supplied read-only capture command.
Reach it from the S25 / MASTER-PC only through an SSH local forward.

Usage:
  python3 -m companion.torchlink_panel --bind 10.188.1.75 \\
      --screenshot-cmd "/path/to/bb.sh screenshot"
"""
import argparse
import html
import ipaddress
import json
import os
import secrets
import shlex
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from companion import torchlink as tl

SECTIONS = [(0, "Terminal"), (1, "Network"), (2, "Security"), (3, "Devices"), (4, "Files"),
            (5, "System"), (6, "Notes"), (7, "CamDoor"), (8, "EchoVault"), (9, "Projects"),
            (10, "About"), (11, "More")]
QUICK_RUN = ("help", "status", "date", "about", "history", "remote", "clear")
MAX_BODY = 512
SHOT_LIMIT = 4 * 1024 * 1024


class Link:
    """One TorchLink phone session at a time, serialised with a lock."""

    def __init__(self, key, bind, port, keepalive=tl.KEEPALIVE_S):
        self.key, self.bind, self.port, self.keepalive = key, bind, port, keepalive
        self.lock = threading.Lock()
        self.conn = self.rf = self.session = None
        self.peer = None
        self.last = time.monotonic()
        self.log = deque(maxlen=40)
        self.stopping = False
        self.ready = threading.Event()

    def note(self, text):
        self.log.append(time.strftime("%H:%M:%S ") + text)

    def state(self):
        return {"connected": self.session is not None, "phone": self.peer, "log": list(self.log)}

    def serve_forever(self):
        with socket.create_server((self.bind, self.port), backlog=1) as srv:
            srv.settimeout(1.0)
            self.note("listening on %s:%d" % (self.bind, self.port))
            self.ready.set()
            while not self.stopping:
                try:
                    conn, peer = srv.accept()
                except socket.timeout:
                    continue
                self._run(conn, peer)

    def _run(self, conn, peer):
        conn.settimeout(30)
        rf = conn.makefile("rb")
        session = tl.DeckSession(self.key)
        try:
            conn.sendall((session.accept_hello(tl.read_line(rf)) + "\n").encode())
        except (tl.LinkError, OSError) as exc:
            self.note("rejected %s: %s" % (peer[0], exc))
            conn.close()
            return
        with self.lock:
            self.conn, self.rf, self.session, self.peer = conn, rf, session, peer[0]
            self.last = time.monotonic()
        self.note("phone connected from %s" % peer[0])
        while not self.stopping:
            time.sleep(0.5)
            with self.lock:
                if self.session is None:
                    break
                idle = time.monotonic() - self.last
            if idle >= self.keepalive:
                ok, msg = self.send("STATUS", "-", keepalive=True)
                if ok is None:
                    break
        self._drop("session ended")

    def _drop(self, why):
        with self.lock:
            if self.conn is not None:
                try:
                    self.conn.close()
                except OSError:
                    pass
                self.note(why)
            self.conn = self.rf = self.session = None
            self.peer = None

    def send(self, op, arg="-", keepalive=False):
        """Returns (ok, message); ok is None when there is no usable session."""
        with self.lock:
            if self.session is None:
                return None, "phone not connected"
            try:
                line = self.session.command(op, arg)
            except tl.LinkError as exc:
                return False, "refused on Deck: %s" % exc
            try:
                self.conn.sendall((line + "\n").encode())
                ok, msg = self.session.verify_ack(tl.read_line(self.rf))
            except (tl.LinkError, OSError) as exc:
                self.session = None
                self.note("link lost: %s" % exc)
                return None, "link lost: %s" % exc
            self.last = time.monotonic()
        self.note(("(keep-alive) " if keepalive else "%s %s -> " % (op, arg)) + ("OK " if ok else "ERR ") + msg)
        if op == "BYE":
            self._drop("session ended by Deck (bye)")
        return ok, msg


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>TorchOS Remote</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:15px system-ui,Arial;background:#101d28;color:#edf4f7;margin:12px}
h1{font-size:20px;margin:4px 0}.muted{color:#b9cbd6}.on{color:#ffb347}.off{color:#82e3c2}
.wrap{display:flex;flex-wrap:wrap;gap:16px}.col{flex:1 1 320px}
button{background:#244b57;color:#edf4f7;border:1px solid #2d414f;border-radius:6px;padding:9px 11px;margin:3px;font:inherit}
button:active{background:#82e3c2;color:#101d28}input{font:inherit;padding:8px;width:60%;border-radius:6px;border:0}
img{max-width:100%;border:1px solid #2d414f;background:#000}pre{background:#0b141c;padding:8px;font-size:12px;
white-space:pre-wrap;max-height:260px;overflow:auto}</style></head><body>
<h1>TorchOS Remote <span class="muted">/ Torch 9810</span></h1>
<p id="st" class="muted">checking...</p>
<div class="wrap"><div class="col">
<p><button data-op="BACK">Back</button><button data-op="HOME">Home</button><button data-op="STATUS">Status</button>
<button data-op="BYE">End session</button></p>
<p>__SECTIONS__</p>
<p><input id="cmd" maxlength="96" placeholder="terminal command (allowlisted)"><button id="run">Run</button></p>
<p>__QUICK__</p>
<p id="reply" class="muted"></p><pre id="log"></pre></div>
<div class="col"><p><button id="shot">Refresh screenshot</button>
<label><input type="checkbox" id="auto" style="width:auto"> auto (8 s)</label></p>
<img id="img" alt="BlackBerry screen"></div></div>
<script nonce="__NONCE__">
const T="__TOKEN__";
async function post(p,b){const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json","X-Panel-Token":T},body:JSON.stringify(b||{})});return r.json();}
async function cmd(op,arg){document.getElementById("reply").textContent="...";const j=await post("/api/cmd",{op:op,arg:arg||"-"});
document.getElementById("reply").textContent=(j.ok===true?"OK ":j.ok===false?"ERR ":"")+j.message;state();setTimeout(shot,700);}
async function state(){const r=await fetch("/api/state?t="+T);const j=await r.json();const s=document.getElementById("st");
s.textContent=j.connected?("REMOTE CONTROL ACTIVE - phone "+j.phone):"Phone not connected: on the BlackBerry open TorchOS > Remote link > Start";
s.className=j.connected?"on":"off";document.getElementById("log").textContent=j.log.slice().reverse().join("\\n");}
async function shot(){const j=await post("/api/shot");if(j.ok)document.getElementById("img").src="/shot.bmp?t="+T+"&n="+Date.now();
else document.getElementById("reply").textContent="Screenshot: "+j.message;}
document.querySelectorAll("[data-op]").forEach(b=>b.onclick=()=>cmd(b.dataset.op,b.dataset.arg));
document.getElementById("run").onclick=()=>{const v=document.getElementById("cmd").value.trim();if(v)cmd("RUN",v);document.getElementById("cmd").value="";};
document.getElementById("cmd").onkeydown=e=>{if(e.key==="Enter")document.getElementById("run").click();};
document.getElementById("shot").onclick=shot;setInterval(state,3000);
setInterval(()=>{if(document.getElementById("auto").checked)shot();},8000);state();
</script></body></html>"""


def render(token, nonce):
    sections = "".join('<button data-op="OPEN" data-arg="%d">%d %s</button>' % (n, n, html.escape(name))
                       for n, name in SECTIONS)
    quick = "".join('<button data-op="RUN" data-arg="%s">%s</button>' % (c, c) for c in QUICK_RUN)
    return (PAGE.replace("__SECTIONS__", sections).replace("__QUICK__", quick)
            .replace("__TOKEN__", token).replace("__NONCE__", nonce))


def make_handler(link, token, host_ok, shot_cmd, shot_state):
    class Handler(BaseHTTPRequestHandler):
        server_version = "TorchLinkPanel"
        sys_version = ""

        def log_message(self, fmt, *args):
            pass

        def _send(self, code, body, ctype, nonce=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; img-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; "
                             "script-src 'nonce-%s'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
                             % (nonce or "none"))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj).encode(), "application/json")

        def _guard(self, header_token=False):
            if self.headers.get("Host", "") not in host_ok:
                self._send(421, b"bad host", "text/plain")
                return False
            q = parse_qs(urlsplit(self.path).query).get("t", [""])[0]
            got = self.headers.get("X-Panel-Token", "") if header_token else q
            if not secrets.compare_digest(got.encode(), token.encode()):
                self._send(403, b"forbidden", "text/plain")
                return False
            return True

        def do_GET(self):
            path = urlsplit(self.path).path
            if not self._guard():
                return
            if path == "/":
                nonce = secrets.token_urlsafe(12)
                self._send(200, render(token, nonce).encode(), "text/html; charset=utf-8", nonce)
            elif path == "/api/state":
                self._json(200, link.state())
            elif path == "/shot.bmp":
                data = shot_state.get("bytes")
                if not data:
                    self._send(404, b"no screenshot yet", "text/plain")
                else:
                    self._send(200, data, "image/bmp")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):
            path = urlsplit(self.path).path
            if not self._guard(header_token=True):
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self._send(415, b"json only", "text/plain")
                return
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                self._send(413, b"too large", "text/plain")
                return
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                self._json(400, {"ok": False, "message": "bad json"})
                return
            if path == "/api/cmd":
                op, arg = str(body.get("op", "")).upper(), str(body.get("arg", "-"))
                if not tl.valid_op(op, arg):
                    self._json(400, {"ok": False, "message": "command not allowed"})
                    return
                ok, msg = link.send(op, arg)
                self._json(200, {"ok": ok, "message": msg})
            elif path == "/api/shot":
                self._json(200, take_shot(shot_cmd, shot_state))
            else:
                self._send(404, b"not found", "text/plain")

        def do_PUT(self):
            self._send(405, b"", "text/plain")
        do_DELETE = do_PATCH = do_PUT

    return Handler


def take_shot(cmd, shot_state):
    if not cmd:
        return {"ok": False, "message": "no --screenshot-cmd configured"}
    if not shot_state["lock"].acquire(blocking=False):
        return {"ok": False, "message": "capture already running"}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        path = lines[-1] if lines else ""
        if r.returncode != 0 or not path.endswith(".bmp") or not os.path.isfile(path):
            why = [l.strip() for l in (r.stderr or "").splitlines() if l.strip()]
            return {"ok": False, "message": "capture failed: " + tl.fields_safe(why[-1] if why else "exit %d" % r.returncode)}
        if os.path.getsize(path) > SHOT_LIMIT:
            return {"ok": False, "message": "capture too large"}
        with open(path, "rb") as fh:
            data = fh.read()
        if data[:2] != b"BM":
            return {"ok": False, "message": "not a BMP"}
        shot_state["bytes"] = data
        return {"ok": True, "message": "captured"}
    except (subprocess.TimeoutExpired, OSError):
        return {"ok": False, "message": "capture timed out"}
    finally:
        shot_state["lock"].release()


def check_panel_bind(addr):
    if not ipaddress.ip_address(addr).is_loopback:
        raise tl.LinkError("control panel binds to loopback only; use an SSH forward for other devices")
    return addr


def build(args, token=None):
    key = tl.load_key(args.key_file)
    tl._check_bind(args.bind)
    check_panel_bind(args.panel_bind)
    link = Link(key, args.bind, args.port, args.keepalive)
    token = token or secrets.token_urlsafe(18)
    host_ok = {"%s:%d" % (args.panel_bind, args.panel_port)}
    if args.panel_bind == "127.0.0.1":
        host_ok.add("localhost:%d" % args.panel_port)
    shot_cmd = shlex.split(args.screenshot_cmd) if args.screenshot_cmd else None
    shot_state = {"bytes": None, "lock": threading.Lock()}
    httpd = ThreadingHTTPServer((args.panel_bind, args.panel_port),
                                make_handler(link, token, host_ok, shot_cmd, shot_state))
    return link, httpd, token


def parser():
    p = argparse.ArgumentParser(prog="torchlink_panel")
    p.add_argument("--bind", required=True, help="Deck private LAN address the phone dials")
    p.add_argument("--port", type=int, default=tl.DEFAULT_PORT)
    p.add_argument("--key-file", default=tl.DEFAULT_KEY)
    p.add_argument("--panel-bind", default="127.0.0.1")
    p.add_argument("--panel-port", type=int, default=18766)
    p.add_argument("--screenshot-cmd", default="")
    p.add_argument("--keepalive", type=float, default=tl.KEEPALIVE_S)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        link, httpd, token = build(args)
    except (tl.LinkError, OSError, ValueError) as exc:
        print("torchlink_panel:", exc, file=sys.stderr)
        return 2
    threading.Thread(target=link.serve_forever, daemon=True).start()
    print("TorchOS Remote panel: http://%s:%d/?t=%s" % (args.panel_bind, args.panel_port, token), flush=True)
    print("Phone listener on %s:%d (TorchOS > Remote link > Start)" % (args.bind, args.port), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    link.stopping = True
    return 0


if __name__ == "__main__":
    sys.exit(main())
