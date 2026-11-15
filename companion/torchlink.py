"""TorchLink v1 — Steam Deck side of TorchOS app-local remote control.

Controls only TorchOS's OWN screens (open page, back, home, run an allowlisted
terminal command, status). Not OS-wide input, not EventInjector, no shell.

The phone dials OUT to this listener over Wi-Fi. The listener accepts one
connection, verifies the phone's HELLO, proves key possession in WELCOME,
then sends sequenced HMAC-SHA256 commands and verifies every ACK.
Nothing received from the network is ever executed on the Deck.

Usage:
  python3 -m companion.torchlink pair   [--key-file PATH]
  python3 -m companion.torchlink serve  --bind 192.168.x.y [--port 47810] [--key-file PATH]
"""
import argparse
import base64
import hmac
import hashlib
import ipaddress
import os
import secrets
import select
import socket
import stat
import sys

KEY_BYTES = 20
MAX_LINE = 512
RUN_LIMIT = 96
DEFAULT_PORT = 47810
KEEPALIVE_S = 45.0
DEFAULT_KEY = os.path.expanduser("~/.config/torchos/torchlink.key")
OPS = ("HOME", "OPEN", "BACK", "RUN", "STATUS", "BYE")


class LinkError(ValueError):
    pass


def mac(key, text):
    return hmac.new(key, text.encode("ascii"), hashlib.sha256).hexdigest()


def _hex(value, length):
    return (isinstance(value, str) and len(value) == length
            and all(c in "0123456789abcdef" for c in value))


def _printable(text):
    return all(0x20 <= ord(c) <= 0x7E for c in text)


def fields(line, n):
    if not isinstance(line, str) or not line or len(line) > MAX_LINE or not _printable(line):
        return None
    parts = line.split("|")
    return parts if len(parts) == n else None


def valid_op(op, arg):
    if not arg:
        return False
    if op == "OPEN":
        return arg.isdigit() and len(arg) <= 2 and str(int(arg)) == arg and 0 <= int(arg) <= 11
    if op == "RUN":
        return len(arg) <= RUN_LIMIT and _printable(arg) and "|" not in arg
    return op in OPS and arg == "-"


def pairing_code(key):
    if len(key) != KEY_BYTES:
        raise LinkError("pairing key must be 20 bytes")
    code = base64.b32encode(key).decode().rstrip("=")
    return " ".join(code[i:i + 4] for i in range(0, 32, 4))


def parse_code(code):
    raw = code.replace(" ", "").replace("-", "").upper()
    if len(raw) != 32:
        raise LinkError("pairing code must be 32 base32 characters")
    return base64.b32decode(raw)


class DeckSession:
    """Deck-side mirror of TorchLinkCore.Session."""

    def __init__(self, key, deck_nonce=None):
        if type(key) is not bytes or len(key) != KEY_BYTES:
            raise LinkError("pairing key must be 20 bytes")
        self.key = key
        self.deck_nonce = deck_nonce or secrets.token_hex(16)
        self.phone_nonce = None
        self.seq = 0

    def accept_hello(self, line):
        f = fields(line, 4)
        if not f or f[0] != "HELLO" or f[1] != "1" or not _hex(f[2], 32) or not _hex(f[3], 64):
            raise LinkError("malformed HELLO")
        if not hmac.compare_digest(f[3], mac(self.key, "TL1|HELLO|" + f[2])):
            raise LinkError("phone not paired with this key")
        if f[2] == self.deck_nonce:
            raise LinkError("reflected nonce")
        self.phone_nonce = f[2]
        return ("WELCOME|1|" + self.deck_nonce + "|"
                + mac(self.key, "TL1|WELCOME|" + self.phone_nonce + "|" + self.deck_nonce))

    def command(self, op, arg="-"):
        if self.phone_nonce is None:
            raise LinkError("no session")
        if not valid_op(op, arg):
            raise LinkError("command not allowed: %s %s" % (op, arg))
        self.seq += 1
        s = str(self.seq)
        return "|".join(("CMD", s, op, arg, mac(self.key, "|".join(
            ("TL1", "CMD", self.phone_nonce, self.deck_nonce, s, op, arg)))))

    def verify_ack(self, line):
        f = fields(line, 5)
        if not f or f[0] != "ACK" or f[2] not in ("OK", "ERR") or not _hex(f[4], 64):
            raise LinkError("malformed ACK")
        expect = mac(self.key, "|".join(("TL1", "ACK", self.phone_nonce, self.deck_nonce, f[1], f[2], f[3])))
        if not hmac.compare_digest(f[4], expect):
            raise LinkError("ACK MAC rejected")
        if f[1] != str(self.seq):
            raise LinkError("ACK for unexpected sequence")
        return f[2] == "OK", f[3]


def load_key(path):
    st = os.stat(path)
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise LinkError("key file must be private (chmod 600): " + path)
    with open(path, "rb") as fh:
        key = fh.read()
    if len(key) != KEY_BYTES:
        raise LinkError("corrupt key file")
    return key


def cmd_pair(args):
    path = args.key_file
    if os.path.exists(path) and not args.force:
        raise LinkError("key exists; use --force to replace (the phone must then be re-paired)")
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    key = secrets.token_bytes(KEY_BYTES)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key)
    print("Type this pairing code into TorchOS > More > Remote link:")
    print("  " + pairing_code(key))
    print("Key stored privately at " + path)


def _check_bind(addr):
    ip = ipaddress.ip_address(addr)
    if ip.is_unspecified or ip.is_multicast or ip.is_global:
        raise LinkError("bind to this Deck's private LAN address, not " + addr)
    return addr


def read_line(sock_file):
    raw = sock_file.readline(MAX_LINE + 2)
    if not raw:
        raise LinkError("phone disconnected")
    if not raw.endswith(b"\n") or len(raw) > MAX_LINE + 1:
        raise LinkError("oversized or truncated line")
    return raw[:-1].decode("ascii")


def parse_operator(text):
    words = text.strip().split(" ", 1)
    verb = words[0].upper()
    rest = words[1].strip() if len(words) > 1 else ""
    if verb in ("OPEN", "RUN"):
        return verb, rest
    return verb, "-"


def cmd_serve(args):
    key = load_key(args.key_file)
    bind = _check_bind(args.bind)
    with socket.create_server((bind, args.port), backlog=1) as srv:
        srv.settimeout(args.wait)
        print("TorchLink listening on %s:%d. On the phone: More > Remote link > Start." % (bind, args.port))
        conn, peer = srv.accept()
    with conn:
        conn.settimeout(30)
        rf = conn.makefile("rb")
        session = DeckSession(key)
        conn.sendall((session.accept_hello(read_line(rf)) + "\n").encode())
        print("Paired TorchOS connected from %s. Commands: open N | back | home | run <cmd> | status | bye" % peer[0])
        fd, pending, eof = sys.stdin.fileno(), b"", False
        while True:
            if b"\n" not in pending and not eof:
                # Phone closes sessions idle > 90 s; send an authenticated STATUS keep-alive at 45 s.
                ready, _, _ = select.select([fd], [], [], KEEPALIVE_S)
                if not ready:
                    conn.sendall((session.command("STATUS") + "\n").encode())
                    ok, message = session.verify_ack(read_line(rf))
                    print("(keep-alive) " + ("OK " if ok else "ERR ") + message, flush=True)
                    continue
                chunk = os.read(fd, 4096)
                eof = not chunk
                pending += chunk
                continue
            if b"\n" in pending:
                raw, pending = pending.split(b"\n", 1)
            elif pending:
                raw, pending = pending, b""
            else:
                break
            text = raw.decode("ascii", "replace")
            if not text.strip():
                continue
            try:
                line = session.command(*parse_operator(text))
            except LinkError as exc:
                print("refused locally:", exc, flush=True)
                continue
            conn.sendall((line + "\n").encode())
            ok, message = session.verify_ack(read_line(rf))
            print(("OK " if ok else "ERR ") + message, flush=True)
            if text.strip().upper() == "BYE":
                break


def main(argv=None):
    p = argparse.ArgumentParser(prog="torchlink")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pair")
    a.add_argument("--key-file", default=DEFAULT_KEY)
    a.add_argument("--force", action="store_true")
    s = sub.add_parser("serve")
    s.add_argument("--bind", required=True)
    s.add_argument("--port", type=int, default=DEFAULT_PORT)
    s.add_argument("--key-file", default=DEFAULT_KEY)
    s.add_argument("--wait", type=float, default=300.0)
    args = p.parse_args(argv)
    try:
        (cmd_pair if args.cmd == "pair" else cmd_serve)(args)
    except (LinkError, OSError) as exc:
        print("torchlink:", exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
