"""TorchOS CP002 read-only envelope contract. No listener, transport or dispatch.

Keys are supplied in memory per paired device, never loaded from disk here.
A native handset transport, provisioning and modern TLS remain unimplemented.
"""
import hashlib
import hmac
import json
import math
import re
import threading
import time

OPS = frozenset(('status', 'network', 'services', 'inventory'))
DEVICE = re.compile(r'[a-zA-Z0-9_-]{1,48}\Z')
NONCE = re.compile(r'[0-9a-f]{32}\Z')
MAC = re.compile(r'[0-9a-f]{64}\Z')
FIELDS = frozenset(('v', 'device', 'op', 'issued', 'expires', 'nonce', 'mac'))
MAX_BYTES = 1024
WINDOW = 60
FUTURE_SKEW = 5


class InvalidRequest(ValueError):
    """Deliberately generic: no payload, identity, path or credential in errors."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise InvalidRequest('Rejected request')
        value[key] = item
    return value


def sign(key, device, op, issued, expires, nonce):
    """Offline envelope builder; callers supply a cryptographically random nonce.

    No persistence, requests or key generation. Receiver performs full validation.
    """
    if type(key) is not bytes or len(key) < 32:
        raise ValueError('A minimum 32-byte key is required')
    payload = dict(v=1, device=device, op=op, issued=issued, expires=expires, nonce=nonce)
    payload['mac'] = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
    result = _canonical(payload)
    if len(result) > MAX_BYTES:
        raise ValueError('Envelope too large')
    return result


class Gateway:
    """Bounded in-process replay verifier. Returns only an allowlisted op name.

    A future transport must bind expected_device to the paired connection and
    hold a single verifier for its lifetime. Restart invalidates replay memory;
    rotate session keys before accepting requests after restart. No execution or
    status collection is performed. Cache capacity exhaustion rejects requests.
    """
    def __init__(self, keys, clock=time.time, capacity=1024):
        if type(keys) is not dict or not 1 <= len(keys) <= 128:
            raise ValueError('Invalid pairing configuration')
        for device, key in keys.items():
            if (type(device) is not str or not DEVICE.fullmatch(device)
                    or type(key) is not bytes or not 32 <= len(key) <= 128):
                raise ValueError('Invalid pairing configuration')
        if type(capacity) is not int or not 1 <= capacity <= 4096 or not callable(clock):
            raise ValueError('Invalid verifier configuration')
        self._keys = dict(keys)
        self._clock = clock
        self._capacity = capacity
        self._used = {}
        self._last_now = None
        self._lock = threading.Lock()
        self.audit = {}  # Fixed fields only. Never contains identity or envelope.

    def verify(self, data, expected_device):
        with self._lock:
            try:
                return self._verify(data, expected_device)
            except Exception:
                self.audit = {'event': 'rejected'}
                raise InvalidRequest('Rejected request') from None

    def _verify(self, data, expected_device):
        if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
            raise InvalidRequest()
        if type(expected_device) is not str or expected_device not in self._keys:
            raise InvalidRequest()
        msg = json.loads(data.decode('utf-8'), object_pairs_hook=_unique,
                         parse_constant=lambda value: (_ for _ in ()).throw(InvalidRequest()))
        if type(msg) is not dict or set(msg) != FIELDS:
            raise InvalidRequest()
        if type(msg['v']) is not int or msg['v'] != 1:
            raise InvalidRequest()
        if type(msg['device']) is not str or msg['device'] != expected_device:
            raise InvalidRequest()
        if type(msg['op']) is not str or msg['op'] not in OPS:
            raise InvalidRequest()
        if type(msg['nonce']) is not str or not NONCE.fullmatch(msg['nonce']):
            raise InvalidRequest()
        if type(msg['mac']) is not str or not MAC.fullmatch(msg['mac']):
            raise InvalidRequest()
        issued, expires = msg['issued'], msg['expires']
        if type(issued) is not int or type(expires) is not int or not 0 <= issued < expires:
            raise InvalidRequest()
        now = self._clock()
        if type(now) not in (int, float) or not math.isfinite(now):
            raise InvalidRequest()
        if self._last_now is not None and now < self._last_now:
            raise InvalidRequest()
        if issued > now + FUTURE_SKEW or now - issued > WINDOW or expires <= now or expires - issued > WINDOW:
            raise InvalidRequest()
        received = msg.pop('mac')
        expected = hmac.new(self._keys[expected_device], _canonical(msg), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received, expected):
            raise InvalidRequest()
        self._last_now = now
        self._used = {key: expiry for key, expiry in self._used.items() if expiry > now}
        nonce_key = (expected_device, msg['nonce'])
        if nonce_key in self._used or len(self._used) >= self._capacity:
            raise InvalidRequest()
        self._used[nonce_key] = expires
        self.audit = {'event': 'accepted', 'op': msg['op']}
        return msg['op']
