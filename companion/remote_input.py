"""Fail-closed TorchOS remote input protocol. Host reference, not a phone bridge.

No device IO, network listener, embedded credentials, or event injection. A
separately signed native receiver must verify this envelope and require
physical phone-side enable and Input Simulation permission.
"""
from collections import deque
import hashlib
import hmac
import json
import re
import time

DEVICE = "torch9810"
MAX_FRAME = 1024
NONCE = re.compile(r"^[a-f0-9]{32}$")
NAV = frozenset(("UP", "DOWN", "LEFT", "RIGHT", "SELECT", "BACK"))
KEYS = frozenset(("ENTER", "BACKSPACE", "ESCAPE", "SPACE", "TAB"))
OPS = frozenset(("NAV", "KEY", "TAP", "SWIPE"))
WIDTH, HEIGHT = 480, 640


class InputRejected(ValueError):
    pass


def _strict_json(blob):
    def no_duplicates(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise InputRejected("Duplicate field")
            result[name] = value
        return result
    try:
        return json.loads(blob, object_pairs_hook=no_duplicates)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InputRejected("Malformed JSON") from exc


def _key_check(key):
    if type(key) is not bytes or len(key) < 32:
        raise InputRejected("Minimum 32-byte pairing key required")


def _coordinates(args, fields):
    if set(args) != set(fields):
        raise InputRejected("Unexpected coordinates")
    for name in fields:
        number = args[name]
        limit = WIDTH if name.startswith("x") else HEIGHT
        if type(number) is not int or not (0 <= number < limit):
            raise InputRejected("Coordinate outside 480x640 screen")


def validate_action(op, args):
    if type(op) is not str or op not in OPS or type(args) is not dict:
        raise InputRejected("Unsupported action")
    if op == "NAV":
        if set(args) != {"direction"} or type(args["direction"]) is not str or args["direction"] not in NAV:
            raise InputRejected("Invalid navigation")
    elif op == "KEY":
        if set(args) != {"key"} or type(args["key"]) is not str:
            raise InputRejected("Invalid key")
        key = args["key"]
        if key not in KEYS and not (len(key) == 1 and 32 <= ord(key) <= 126):
            raise InputRejected("Only printable ASCII / special keys allowed")
    elif op == "TAP":
        _coordinates(args, ("x", "y"))
    elif op == "SWIPE":
        _coordinates(args, ("x1", "y1", "x2", "y2"))
        if args["x1"] == args["x2"] and args["y1"] == args["y2"]:
            raise InputRejected("Empty swipe")
    return op, args


def encode(key, session, seq, op, args, *, nonce, issued, expires, device=DEVICE):
    _key_check(key)
    validate_action(op, args)
    if type(device) is not str or device != DEVICE:
        raise InputRejected("Wrong device")
    if type(session) is not str or not NONCE.fullmatch(session):
        raise InputRejected("Invalid session")
    if type(nonce) is not str or not NONCE.fullmatch(nonce):
        raise InputRejected("Invalid nonce")
    if type(seq) is not int or seq < 1:
        raise InputRejected("Invalid sequence number")
    if type(issued) is not int or type(expires) is not int or not (0 < expires - issued <= 8):
        raise InputRejected("Invalid expiry")
    fields = {
        "v": 2, "device": device, "session": session, "seq": seq,
        "nonce": nonce, "issued": issued, "expires": expires,
        "op": op, "args": args,
    }
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    mac = hmac.new(key, payload.encode("ascii"), hashlib.sha256).hexdigest()
    data = json.dumps({"payload": payload, "mac": mac}, separators=(",", ":")).encode("ascii")
    if len(data) > MAX_FRAME:
        raise InputRejected("Frame too large")
    return data


class InputGate:
    """Model of native consent and dispatch. Actual injection never occurs here."""

    def __init__(self, key, sink, *, device=DEVICE, clock=None, is_locked=None):
        _key_check(key)
        if device != DEVICE or not callable(sink):
            raise InputRejected("Invalid configuration")
        self._key = key
        self._sink = sink
        self._clock = clock or time.time
        self._is_locked = is_locked or (lambda: True)
        self._session = None
        self._last_seq = 0
        self._nonces = set()
        self._recent = deque()
        self._armed_until = 0

    @property
    def enabled(self):
        return self._session is not None and self._clock() < self._armed_until

    def arm(self, session, *, on_device, input_permission, timeout=300):
        # Only trusted code behind an explicit physical enable UI may call.
        if on_device is not True or input_permission is not True:
            self.disarm()
            raise InputRejected("Physical consent and signed permission required")
        if type(session) is not str or not NONCE.fullmatch(session):
            raise InputRejected("Invalid session")
        if type(timeout) is not int or not (1 <= timeout <= 300):
            raise InputRejected("Invalid duration")
        if self._is_locked():
            self.disarm()
            raise InputRejected("Device locked")
        self._session = session
        self._last_seq = 0
        self._nonces.clear()
        self._recent.clear()
        self._armed_until = self._clock() + timeout

    def disarm(self):
        self._session = None
        self._last_seq = 0
        self._nonces.clear()
        self._recent.clear()
        self._armed_until = 0

    def execute(self, frame):
        if not self.enabled:
            self.disarm()
            raise InputRejected("Input disabled")
        if self._is_locked():
            self.disarm()
            raise InputRejected("Device locked; session revoked")
        if type(frame) is not bytes or not (1 <= len(frame) <= MAX_FRAME):
            raise InputRejected("Invalid frame size")
        try:
            envelope = _strict_json(frame.decode("utf-8", errors="strict"))
        except UnicodeDecodeError as exc:
            raise InputRejected("Invalid UTF-8") from exc
        if type(envelope) is not dict or set(envelope) != {"payload", "mac"}:
            raise InputRejected("Invalid envelope schema")
        payload = envelope["payload"]
        mac = envelope["mac"]
        if type(payload) is not str or type(mac) is not str or not re.fullmatch(r"[a-f0-9]{64}", mac):
            raise InputRejected("Invalid authentication")
        expected = hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, mac):
            raise InputRejected("Wrong MAC")
        command = _strict_json(payload)
        required = {"v", "device", "session", "seq", "nonce", "issued", "expires", "op", "args"}
        if type(command) is not dict or set(command) != required:
            raise InputRejected("Unexpected payload fields")
        if type(command["v"]) is not int or command["v"] != 2 or command["device"] != DEVICE:
            raise InputRejected("Wrong protocol/device")
        if command["session"] != self._session:
            raise InputRejected("Wrong session")
        if type(command["seq"]) is not int or not (self._last_seq < command["seq"] <= self._last_seq + 1000):
            raise InputRejected("Replay or invalid sequence")
        nonce = command["nonce"]
        if type(nonce) is not str or not NONCE.fullmatch(nonce) or nonce in self._nonces:
            raise InputRejected("Replay nonce")
        issued, expires = command["issued"], command["expires"]
        now = int(self._clock())
        if (type(issued) is not int or type(expires) is not int
                or not (0 < expires - issued <= 8)
                or issued > now + 2 or issued < now - 8 or expires < now):
            raise InputRejected("Invalid command time")
        validate_action(command["op"], command["args"])
        while self._recent and self._recent[0] <= self._clock() - 1:
            self._recent.popleft()
        if len(self._recent) >= 10:
            raise InputRejected("Too many inputs")
        self._last_seq = command["seq"]
        self._nonces.add(nonce)
        self._recent.append(self._clock())
        if len(self._nonces) > 4096:
            self.disarm()
            raise InputRejected("Replay cache limit")
        self._sink(command["op"], command["args"])
        return True
