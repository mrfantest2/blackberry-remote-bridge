"""Offline validation of a proposed authenticated BlackBerry companion command envelope.
No network listener, USB write, or phone input is implemented here.
"""
import hashlib
import hmac
import json
import re

ALLOWED = {'UP', 'DOWN', 'LEFT', 'RIGHT', 'SELECT', 'BACK'}
NONCE = re.compile(r'^[a-f0-9]{32}$')

class InvalidCommand(ValueError):
    pass

def encode(key: bytes, command: str, nonce: str) -> bytes:
    if not isinstance(key, bytes) or len(key) < 32:
        raise InvalidCommand('Minimum 32-byte key required')
    if command not in ALLOWED or not isinstance(nonce, str) or not NONCE.fullmatch(nonce):
        raise InvalidCommand('Invalid command or nonce')
    payload = json.dumps({'v': 1, 'command': command, 'nonce': nonce}, separators=(',', ':'), sort_keys=True)
    mac = hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()
    return json.dumps({'payload': payload, 'mac': mac}, separators=(',', ':')).encode()

def verify(key: bytes, data: bytes, used_nonces: set) -> str:
    if not isinstance(data, bytes) or len(data) > 512 or len(key) < 32:
        raise InvalidCommand('Invalid envelope')
    try:
        envelope = json.loads(data)
        if set(envelope) != {'payload', 'mac'} or not isinstance(envelope['payload'], str):
            raise InvalidCommand('Invalid fields')
        payload = envelope['payload']
        mac = envelope['mac']
        if not isinstance(mac, str) or not re.fullmatch(r'[a-f0-9]{64}', mac):
            raise InvalidCommand('Invalid MAC')
        expected = hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mac, expected):
            raise InvalidCommand('Authentication failed')
        msg = json.loads(payload)
        if set(msg) != {'v', 'command', 'nonce'} or type(msg['v']) is not int or msg['v'] != 1:
            raise InvalidCommand('Invalid version')
        if msg['command'] not in ALLOWED or not isinstance(msg['nonce'], str) or not NONCE.fullmatch(msg['nonce']):
            raise InvalidCommand('Invalid command')
        if msg['nonce'] in used_nonces:
            raise InvalidCommand('Replay detected')
        used_nonces.add(msg['nonce'])
        return msg['command']
    except (TypeError, KeyError, UnicodeError, json.JSONDecodeError) as e:
        raise InvalidCommand('Malformed envelope') from e
