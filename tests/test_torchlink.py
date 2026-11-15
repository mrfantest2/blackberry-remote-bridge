"""TorchLink v1: real Java phone core (host JDK) <-> Python Deck reference.

Host-only. Proves protocol parity and fail-closed behaviour; it does NOT
prove the BlackBerry VM, Wi-Fi transport or on-device UI dispatch.
"""
import hashlib
import hmac
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from companion import torchlink as tl

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "torchos-native/src/TorchLinkCore.java"
HARNESS = ROOT / "tests/java/TorchLinkHarness.java"
JDK = Path(os.environ.get("JDK8_HOME") or os.environ.get("JAVA_HOME")
           or "/home/SD/BlackBerryBridge/toolchains/jdk8")
KEY = bytes(range(1, 21))
SEED = b"torch-seed-0001"


class Phone:
    out = None

    @classmethod
    def build(cls):
        if cls.out:
            return cls.out
        cls.out = tempfile.mkdtemp(prefix="torchlink-")
        r = subprocess.run([str(JDK / "bin/javac"), "-source", "1.3", "-target", "1.3",
                            "-nowarn", "-d", cls.out, str(CORE), str(HARNESS)],
                           capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stderr)
        return cls.out

    def __init__(self, key=KEY, seed=SEED):
        self.p = subprocess.Popen([str(JDK / "bin/java"), "-cp", self.build(), "TorchLinkHarness"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.p.stdin.write(key.hex() + "\n" + seed.hex() + "\n")
        self.hello = self.p.stdout.readline().strip()

    def send(self, line, now=1000):
        self.p.stdin.write("%d %s\n" % (now, line))
        self.p.stdin.flush()
        return self.p.stdout.readline().strip()

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=10)
        self.p.stdout.close()


def vectors(lines):
    r = subprocess.run([str(JDK / "bin/java"), "-cp", Phone.build(), "TorchLinkHarness"],
                       input="VECTORS\n" + "\n".join(lines) + "\n", capture_output=True, text=True, timeout=20)
    return r.stdout.split("\n")[:len(lines)]


class Crypto(unittest.TestCase):
    def test_sha256_matches_hashlib_across_block_boundaries(self):
        msgs = [b"", b"abc"] + [bytes((i * 7) & 255 for i in range(n)) for n in (55, 56, 63, 64, 65, 119, 1000)]
        got = vectors(["SHA " + m.hex() for m in msgs])
        self.assertEqual(got, [hashlib.sha256(m).hexdigest() for m in msgs])

    def test_hmac_rfc4231_and_long_key(self):
        cases = [(b"\x0b" * 20, b"Hi There"), (b"Jefe", b"what do ya want for nothing?"),
                 (b"\xaa" * 131, b"Test Using Larger Than Block-Size Key - Hash Key First"), (KEY, b"TL1|HELLO|x")]
        got = vectors(["HMAC %s %s" % (k.hex(), m.hex()) for k, m in cases])
        self.assertEqual(got[0], "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7")
        self.assertEqual(got, [hmac.new(k, m, hashlib.sha256).hexdigest() for k, m in cases])

    def test_pairing_code_roundtrip_and_rejects(self):
        code = tl.pairing_code(KEY)
        got = vectors(["CODE " + code, "CODE " + code.lower().replace(" ", "-"),
                       "CODE " + code[:-1], "CODE " + code + "A", "CODE " + code.replace(code[0], "1", 1)])
        self.assertEqual(got[:2], [KEY.hex(), KEY.hex()])
        self.assertEqual(got[2:], ["null", "null", "null"])
        self.assertEqual(tl.parse_code(code), KEY)

    def test_host_and_op_validation_parity(self):
        hosts = ["192.168.1.20", "10.0.0.1", "256.1.1.1", "01.2.3.4", "1.2.3", "a.b.c.d", "1.2.3.4.5", "deck.local"]
        self.assertEqual(vectors(["HOST " + h for h in hosts]),
                         ["true", "true", "false", "false", "false", "false", "false", "false"])
        ops = [("OPEN", "0"), ("OPEN", "11"), ("OPEN", "12"), ("OPEN", "05"), ("OPEN", "-1"), ("RUN", "help"),
               ("RUN", "x" * 97), ("HOME", "-"), ("HOME", "x"), ("TAP", "-"), ("BYE", "-"), ("RUN", "")]
        java = vectors(["OP %s %s" % o for o in ops])
        self.assertEqual(java, [str(tl.valid_op(*o)).lower() for o in ops])
        self.assertEqual(java, ["true", "true", "false", "false", "false", "true",
                                "false", "true", "false", "false", "true", "false"])


class Protocol(unittest.TestCase):
    def setUp(self):
        self.phone = Phone()
        self.addCleanup(self.phone.close)
        self.deck = tl.DeckSession(KEY)

    def handshake(self):
        welcome = self.deck.accept_hello(self.phone.hello)
        self.assertEqual(self.phone.send(welcome), "OPEN")

    def run_cmd(self, op, arg="-", now=1000):
        out = self.phone.send(self.deck.command(op, arg), now)
        m = re.match(r"^CMD (\S+) (.+) (ACK\|.*)$", out)
        self.assertIsNotNone(m, out)
        self.assertEqual((m.group(1), m.group(2)), (op, arg))
        self.assertEqual(self.deck.verify_ack(m.group(3)), (True, "did " + op))

    def test_full_session_interop(self):
        self.handshake()
        self.run_cmd("OPEN", "1")
        self.run_cmd("RUN", "status")
        self.run_cmd("BACK")
        self.run_cmd("HOME")
        self.run_cmd("STATUS")
        self.run_cmd("BYE")

    def test_wrong_key_deck_cannot_open_session(self):
        rogue = tl.DeckSession(b"\x99" * 20)
        with self.assertRaises(tl.LinkError):
            rogue.accept_hello(self.phone.hello)
        rogue.phone_nonce = self.phone.hello.split("|")[2]
        forged = "WELCOME|1|%s|%s" % (rogue.deck_nonce, tl.mac(rogue.key, "TL1|WELCOME|%s|%s" % (rogue.phone_nonce, rogue.deck_nonce)))
        self.assertEqual(self.phone.send(forged), "CLOSED Deck authentication failed")

    def test_replayed_command_closes_session(self):
        self.handshake()
        line = self.deck.command("OPEN", "2")
        self.assertTrue(self.phone.send(line).startswith("CMD OPEN 2"))
        self.assertEqual(self.phone.send(line), "CLOSED replayed or skipped sequence")

    def test_skipped_sequence_closes_session(self):
        self.handshake()
        self.deck.seq = 4
        self.assertEqual(self.phone.send(self.deck.command("HOME")), "CLOSED replayed or skipped sequence")

    def test_tampered_command_closes_session(self):
        self.handshake()
        line = self.deck.command("OPEN", "1").replace("|OPEN|1|", "|OPEN|4|")
        self.assertEqual(self.phone.send(line), "CLOSED command MAC rejected")

    def test_command_from_previous_session_rejected(self):
        self.handshake()
        old = self.deck.command("RUN", "help")
        other = Phone(seed=b"another-session")
        self.addCleanup(other.close)
        deck2 = tl.DeckSession(KEY)
        self.assertEqual(other.send(deck2.accept_hello(other.hello)), "OPEN")
        self.assertEqual(other.send(old), "CLOSED command MAC rejected")

    def test_disallowed_op_even_with_valid_mac_rejected(self):
        self.handshake()
        self.deck.seq += 1
        s = str(self.deck.seq)
        forged = "|".join(("CMD", s, "TAP", "-", tl.mac(KEY, "|".join(
            ("TL1", "CMD", self.deck.phone_nonce, self.deck.deck_nonce, s, "TAP", "-")))))
        self.assertEqual(self.phone.send(forged), "CLOSED command not allowed")

    def test_commands_before_welcome_rejected(self):
        self.deck.accept_hello(self.phone.hello)
        self.assertEqual(self.phone.send(self.deck.command("HOME")), "CLOSED session not open")

    def test_idle_and_session_expiry(self):
        self.handshake()
        self.run_cmd("HOME", now=60000)
        self.assertEqual(self.phone.send(self.deck.command("HOME"), now=60000 + 90001), "CLOSED idle timeout")
        p = Phone(seed=b"expiry")
        self.addCleanup(p.close)
        d = tl.DeckSession(KEY)
        self.assertEqual(p.send(d.accept_hello(p.hello), now=0), "OPEN")
        t = 0
        while t < 600000:
            t += 80000
            out = p.send(d.command("STATUS"), now=min(t, 600001))
        self.assertEqual(out, "CLOSED session expired")

    def test_oversized_and_non_ascii_lines_rejected(self):
        self.handshake()
        self.assertEqual(self.phone.send("CMD|1|RUN|" + "a" * 600 + "|" + "0" * 64), "CLOSED malformed command")

    def test_deck_rejects_forged_or_mismatched_ack(self):
        self.handshake()
        line = self.deck.command("STATUS")
        ack = self.phone.send(line).split(" ", 3)[3]
        with self.assertRaises(tl.LinkError):
            self.deck.verify_ack(ack.replace("|OK|", "|ERR|"))
        self.deck.seq += 1
        with self.assertRaises(tl.LinkError):
            self.deck.verify_ack(ack)

    def test_operator_cannot_send_disallowed_commands(self):
        self.handshake()
        for op, arg in (("TAP", "-"), ("OPEN", "99"), ("RUN", "a|b"), ("RUN", "x" * 97)):
            with self.assertRaises(tl.LinkError):
                self.deck.command(op, arg)
        self.assertEqual(self.deck.seq, 0)


class DeckSafety(unittest.TestCase):
    def test_bind_refuses_wildcard_and_public(self):
        for bad in ("0.0.0.0", "::", "8.8.8.8", "224.0.0.1"):
            with self.assertRaises(tl.LinkError):
                tl._check_bind(bad)
        self.assertEqual(tl._check_bind("192.168.1.5"), "192.168.1.5")

    def test_keepalive_is_below_phone_idle_limit(self):
        core = CORE.read_text()
        idle_ms = int(re.search(r"IDLE_MS = (\d+)L", core).group(1))
        self.assertLess(tl.KEEPALIVE_S * 1000, idle_ms / 1.5)

    def test_key_file_must_be_private(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "k")
            tl.cmd_pair(type("A", (), {"key_file": path, "force": False})())
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertEqual(len(tl.load_key(path)), 20)
            os.chmod(path, 0o644)
            with self.assertRaises(tl.LinkError):
                tl.load_key(path)

    def test_source_has_no_os_wide_input_or_shell(self):
        src = CORE.read_text() + (ROOT / "companion/torchlink.py").read_text()
        for bad in ("EventInjector.", "import subprocess", "os.system", "eval(", "exec(", "PERMISSION_INPUT_SIMULATION"):
            self.assertNotIn(bad, src)

    def test_core_avoids_non_cldc_apis(self):
        src = CORE.read_text()
        for bad in ("StringBuilder", ".split(", "String.format", "HashMap", "ArrayList", "java.util.Arrays",
                    "java.security", "javax.crypto", "net.rim.device.api.crypto", "for (String"):
            self.assertNotIn(bad, src)


if __name__ == "__main__":
    unittest.main()
