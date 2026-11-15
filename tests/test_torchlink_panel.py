"""TorchLink panel: loopback HTTP guards + real Java phone core over TCP. Host-only."""
import http.client
import json
import os
import socket
import stat
import tempfile
import threading
import time
import unittest

from companion import torchlink as tl
from companion import torchlink_panel as panel
from tests.test_torchlink import Phone, KEY

TOKEN = "test-token-123"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class PanelTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        kf = os.path.join(d, "key")
        fd = os.open(kf, os.O_WRONLY | os.O_CREAT, 0o600)
        os.write(fd, KEY)
        os.close(fd)
        bmp = os.path.join(d, "shot.bmp")
        with open(bmp, "wb") as fh:
            fh.write(b"BM" + b"\0" * 64)
        script = os.path.join(d, "shot.sh")
        with open(script, "w") as fh:
            fh.write("#!/bin/sh\necho capturing\necho %s\n" % bmp)
        os.chmod(script, stat.S_IRWXU)
        self.lport, self.pport = free_port(), free_port()
        args = panel.parser().parse_args([
            "--bind", "127.0.0.1", "--port", str(self.lport), "--key-file", kf,
            "--panel-port", str(self.pport), "--screenshot-cmd", script, "--keepalive", "1"])
        self.link, self.httpd, _ = panel.build(args, token=TOKEN)
        threading.Thread(target=self.link.serve_forever, daemon=True).start()
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.link.ready.wait(5)
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.link.stopping = True
        self.httpd.shutdown()
        self.httpd.server_close()

    def req(self, method, path, body=None, host=None, header_token=TOKEN, ctype="application/json"):
        c = http.client.HTTPConnection("127.0.0.1", self.pport, timeout=10)
        headers = {"Host": host or "127.0.0.1:%d" % self.pport}
        data = None
        if method == "POST":
            data = json.dumps(body or {}).encode()
            headers["Content-Type"] = ctype
            if header_token is not None:
                headers["X-Panel-Token"] = header_token
        c.request(method, path, body=data, headers=headers)
        r = c.getresponse()
        out = r.status, dict(r.getheaders()), r.read()
        c.close()
        return out

    def connect_phone(self):
        """Real Java TorchLinkCore acting as the phone, pumped in a thread."""
        phone = Phone(seed=os.urandom(8))
        sock = socket.create_connection(("127.0.0.1", self.lport))
        f = sock.makefile("rwb")
        f.write((phone.hello + "\n").encode())
        f.flush()
        self.assertEqual(phone.send(f.readline().decode().strip()), "OPEN")
        seen = []

        def pump():
            try:
                while True:
                    line = f.readline()
                    if not line:
                        return
                    out = phone.send(line.decode().strip())
                    seen.append(out)
                    if not out.startswith("CMD "):
                        return
                    f.write((out.split(" ", 3)[3] + "\n").encode())
                    f.flush()
            except (OSError, ValueError):
                return
        threading.Thread(target=pump, daemon=True).start()
        self.addCleanup(lambda: (sock.close(), phone.close()))
        deadline = time.time() + 5
        while not self.link.state()["connected"] and time.time() < deadline:
            time.sleep(0.05)
        return seen

    # --- guards -------------------------------------------------------------
    def test_page_requires_token_and_loopback_host(self):
        self.assertEqual(self.req("GET", "/")[0], 403)
        self.assertEqual(self.req("GET", "/?t=wrong")[0], 403)
        self.assertEqual(self.req("GET", "/?t=" + TOKEN, host="evil.example:%d" % self.pport)[0], 421)
        status, headers, body = self.req("GET", "/?t=" + TOKEN)
        self.assertEqual(status, 200)
        csp = headers["Content-Security-Policy"]
        self.assertIn("script-src 'nonce-", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn(b"TorchOS Remote", body)

    def test_commands_need_header_token_and_json(self):
        self.assertEqual(self.req("POST", "/api/cmd?t=" + TOKEN, {"op": "STATUS"}, header_token=None)[0], 403)
        self.assertEqual(self.req("POST", "/api/cmd", {"op": "STATUS"}, header_token="nope")[0], 403)
        self.assertEqual(self.req("POST", "/api/cmd", {"op": "STATUS"},
                                  ctype="application/x-www-form-urlencoded")[0], 415)
        self.assertEqual(self.req("GET", "/api/cmd?t=" + TOKEN)[0], 404)

    def test_disallowed_ops_rejected_before_link(self):
        for body in ({"op": "TAP", "arg": "-"}, {"op": "OPEN", "arg": "12"},
                     {"op": "RUN", "arg": "a|b"}, {"op": "RUN", "arg": "x" * 97}):
            status, _, out = self.req("POST", "/api/cmd", body)
            self.assertEqual(status, 400, body)
            self.assertEqual(json.loads(out)["message"], "command not allowed")

    def test_no_phone_reports_not_connected(self):
        out = json.loads(self.req("POST", "/api/cmd", {"op": "STATUS"})[2])
        self.assertIsNone(out["ok"])
        self.assertEqual(out["message"], "phone not connected")

    def test_panel_refuses_non_loopback_bind(self):
        with self.assertRaises(tl.LinkError):
            panel.check_panel_bind("10.188.1.75")
        with self.assertRaises(tl.LinkError):
            panel.check_panel_bind("0.0.0.0")
        self.assertEqual(panel.check_panel_bind("127.0.0.1"), "127.0.0.1")

    # --- live session ---------------------------------------------------------
    def test_buttons_drive_real_phone_core(self):
        self.connect_phone()
        state = json.loads(self.req("GET", "/api/state?t=" + TOKEN)[2])
        self.assertTrue(state["connected"])
        for op, arg in (("OPEN", "4"), ("BACK", "-"), ("RUN", "help"), ("STATUS", "-")):
            out = json.loads(self.req("POST", "/api/cmd", {"op": op, "arg": arg})[2])
            self.assertEqual(out, {"ok": True, "message": "did " + op})

    def test_keepalive_and_bye(self):
        seen = self.connect_phone()
        time.sleep(2.6)
        self.assertTrue(any(s.startswith("CMD STATUS") for s in seen), seen)
        out = json.loads(self.req("POST", "/api/cmd", {"op": "BYE"})[2])
        self.assertTrue(out["ok"])
        self.assertFalse(json.loads(self.req("GET", "/api/state?t=" + TOKEN)[2])["connected"])

    def test_screenshot_failure_reports_reason(self):
        d = tempfile.mkdtemp()
        bad = os.path.join(d, "bad.sh")
        with open(bad, "w") as fh:
            fh.write("#!/bin/sh\necho 'BlackBerry USB not detected' >&2\nexit 3\n")
        os.chmod(bad, stat.S_IRWXU)
        out = panel.take_shot([bad], {"bytes": None, "lock": threading.Lock()})
        self.assertEqual(out, {"ok": False, "message": "capture failed: BlackBerry USB not detected"})

    def test_screenshot_served_only_with_token(self):
        self.assertEqual(self.req("GET", "/shot.bmp?t=" + TOKEN)[0], 404)
        out = json.loads(self.req("POST", "/api/shot")[2])
        self.assertTrue(out["ok"], out)
        status, headers, body = self.req("GET", "/shot.bmp?t=" + TOKEN)
        self.assertEqual((status, headers["Content-Type"], body[:2]), (200, "image/bmp", b"BM"))
        self.assertEqual(self.req("GET", "/shot.bmp")[0], 403)


if __name__ == "__main__":
    unittest.main()
