import json
import unittest
from companion.protocol import encode, verify, InvalidCommand

KEY = b'unit-test-only-key-material-32bytes!!'
NONCE = '0123456789abcdef0123456789abcdef'

class ProtocolTests(unittest.TestCase):
    def test_allowlisted_navigation(self):
        for command in ('UP', 'DOWN', 'LEFT', 'RIGHT', 'SELECT', 'BACK'):
            self.assertEqual(verify(KEY, encode(KEY, command, NONCE), set()), command)
    def test_replay_rejected(self):
        seen = set()
        message = encode(KEY, 'UP', NONCE)
        verify(KEY, message, seen)
        with self.assertRaises(InvalidCommand): verify(KEY, message, seen)
    def test_tampering_rejected(self):
        envelope = json.loads(encode(KEY, 'UP', NONCE))
        envelope['payload'] = envelope['payload'].replace('UP', 'DOWN')
        with self.assertRaises(InvalidCommand): verify(KEY, json.dumps(envelope).encode(), set())
    def test_disallowed_input_rejected(self):
        for command in ('WIPE', 'TYPE_PASSWORD', 'TOUCH', 'RESET', ''):
            with self.assertRaises(InvalidCommand): encode(KEY, command, NONCE)
    def test_short_key_rejected(self):
        with self.assertRaises(InvalidCommand): encode(b'short', 'UP', NONCE)
    def test_invalid_nonce_rejected(self):
        with self.assertRaises(InvalidCommand): encode(KEY, 'UP', 'x')
    def test_oversize_rejected(self):
        with self.assertRaises(InvalidCommand): verify(KEY, b'x'*513, set())
    def test_wrong_key_rejected(self):
        with self.assertRaises(InvalidCommand): verify(b'X'*32, encode(KEY, 'UP', NONCE), set())
    def test_extra_field_rejected(self):
        envelope = json.loads(encode(KEY, 'UP', NONCE)); envelope['admin'] = True
        with self.assertRaises(InvalidCommand): verify(KEY, json.dumps(envelope).encode(), set())

if __name__ == '__main__': unittest.main()
