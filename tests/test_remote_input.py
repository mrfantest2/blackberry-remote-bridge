"""Security and correctness tests for the disconnected TorchOS input gate."""
import json
import unittest
from companion.remote_input import (
    DEVICE, InputGate, InputRejected, encode, validate_action,
)

KEY = b"test-only-key-32bytes-not-a-real-secret-12345678"
S = "0123456789abcdef0123456789abcdef"
N = "abcdef0123456789abcdef0123456789"
NOW = 1_800_000_000


class InputGateTests(unittest.TestCase):
    def setUp(self):
        self.now = NOW
        self.locked = False
        self.events = []
        self.gate = InputGate(KEY, lambda op, args: self.events.append((op, args)),
                              clock=lambda: self.now, is_locked=lambda: self.locked)

    def arm(self):
        self.gate.arm(S, on_device=True, input_permission=True)

    def frame(self, seq=1, op="NAV", args=None, nonce=N, issued=None, expires=None,
              session=S, key=KEY):
        return encode(key, session, seq, op, args or {"direction": "DOWN"},
                      nonce=nonce, issued=self.now if issued is None else issued,
                      expires=self.now + 5 if expires is None else expires)

    def reject(self, frame):
        with self.assertRaises(InputRejected):
            self.gate.execute(frame)

    def test_off_by_default(self):
        self.reject(self.frame())
        self.assertEqual(self.events, [])

    def test_physical_arm_required(self):
        with self.assertRaises(InputRejected):
            self.gate.arm(S, on_device=False, input_permission=True)
        self.assertFalse(self.gate.enabled)

    def test_permission_required(self):
        with self.assertRaises(InputRejected):
            self.gate.arm(S, on_device=True, input_permission=False)
        self.assertFalse(self.gate.enabled)

    def test_locked_device_refuses_arm(self):
        self.locked = True
        with self.assertRaises(InputRejected):
            self.arm()

    def test_basic_nav_and_sequence(self):
        self.arm()
        self.assertTrue(self.gate.execute(self.frame()))
        second = self.frame(seq=2, args={"direction": "UP"},
                            nonce="11111111111111111111111111111111")
        self.assertTrue(self.gate.execute(second))
        self.assertEqual([x[1]["direction"] for x in self.events], ["DOWN", "UP"])

    def test_every_supported_navigation(self):
        for direction in ("UP", "DOWN", "LEFT", "RIGHT", "SELECT", "BACK"):
            validate_action("NAV", {"direction": direction})

    def test_key_controls(self):
        for key in ("A", "z", "9", "!", " ", "ENTER", "BACKSPACE", "ESCAPE", "SPACE", "TAB"):
            validate_action("KEY", {"key": key})

    def test_disallowed_key_sequences(self):
        for key in ("ALT+F4", "", "\n", "\x00", "£", "PASSWORD", "a" * 4096):
            with self.subTest(key=repr(key)), self.assertRaises(InputRejected):
                validate_action("KEY", {"key": key})

    def test_tap_and_swipe_bounds(self):
        validate_action("TAP", {"x": 0, "y": 0})
        validate_action("TAP", {"x": 479, "y": 639})
        validate_action("SWIPE", {"x1": 0, "y1": 1, "x2": 479, "y2": 639})
        for op, data in [
            ("TAP", {"x": 480, "y": 10}), ("TAP", {"x": -1, "y": 5}),
            ("TAP", {"x": True, "y": 20}), ("TAP", {"x": 10.1, "y": 5}),
            ("TAP", {"x": 10, "y": 640}),
            ("SWIPE", {"x1": 3, "y1": 4, "x2": 3, "y2": 4}),
            ("SWIPE", {"x1": 3, "y1": 4, "x2": 500, "y2": 5}),
            ("SWIPE", {"x1": 3, "y1": 4, "x2": 5, "y2": 6, "secret": "x"}),
        ]:
            with self.subTest(op=op, data=data), self.assertRaises(InputRejected):
                validate_action(op, data)

    def test_replay_denied(self):
        self.arm()
        f = self.frame()
        self.gate.execute(f)
        self.reject(f)
        self.assertEqual(len(self.events), 1)

    def test_nonce_replay_even_with_new_sequence(self):
        self.arm()
        self.gate.execute(self.frame())
        self.reject(self.frame(seq=2))
        self.assertEqual(len(self.events), 1)

    def test_mac_forgery(self):
        self.arm()
        message = json.loads(self.frame())
        message["payload"] = message["payload"].replace("DOWN", "UP")
        self.reject(json.dumps(message).encode())
        self.assertFalse(self.events)

    def test_wrong_secret(self):
        self.arm()
        self.reject(self.frame(key=b"X" * 32))

    def test_session_binding(self):
        self.arm()
        self.reject(self.frame(session="f" * 32))

    def test_restricted_device(self):
        with self.assertRaises(InputRejected):
            encode(KEY, S, 1, "NAV", {"direction": "UP"}, nonce=N,
                   issued=NOW, expires=NOW + 2, device="other")

    def test_packet_expiry(self):
        self.arm()
        self.reject(self.frame(issued=NOW - 10, expires=NOW - 5))

    def test_future_clock(self):
        self.arm()
        self.reject(self.frame(issued=NOW + 4, expires=NOW + 7))

    def test_lock_disarms_immediately(self):
        self.arm()
        self.locked = True
        self.reject(self.frame())
        self.assertFalse(self.gate.enabled)
        self.locked = False
        self.reject(self.frame())

    def test_physical_kill_switch(self):
        self.arm()
        self.gate.disarm()
        self.reject(self.frame())

    def test_auto_timeout(self):
        self.arm()
        self.now += 301
        self.reject(self.frame())
        self.assertFalse(self.gate.enabled)

    def test_rate_limit(self):
        self.arm()
        for seq in range(1, 11):
            self.gate.execute(self.frame(seq=seq, nonce=f"{seq:032x}"))
        self.reject(self.frame(seq=11, nonce=f"{11:032x}"))
        self.assertEqual(len(self.events), 10)
        self.now += 2
        self.gate.execute(self.frame(seq=11, nonce=f"{11:032x}"))
        self.assertEqual(len(self.events), 11)

    def test_max_size(self):
        self.arm()
        self.reject(b"x" * 1025)

    def test_duplicate_envelope_fields(self):
        self.arm()
        payload = json.loads(self.frame())
        raw = ("{" + '"mac":"%s","mac":"%s","payload":%s}' %
               (payload["mac"], payload["mac"], json.dumps(payload["payload"])))
        self.reject(raw.encode())

    def test_invalid_utf8(self):
        self.arm()
        self.reject(b"\xff")

    def test_boolean_sequence_is_rejected(self):
        self.arm()
        message = json.loads(self.frame())
        payload = json.loads(message["payload"])
        payload["seq"] = True
        # Re-sign to test schema, not the MAC.
        import hashlib, hmac
        plain = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        message["payload"] = plain
        message["mac"] = hmac.new(KEY, plain.encode(), hashlib.sha256).hexdigest()
        self.reject(json.dumps(message).encode())

    def test_no_password_or_flash_commands(self):
        for op in ("WIPE", "RESET", "PASSWORD", "COMMAND", "SHELL"):
            with self.subTest(op=op), self.assertRaises(InputRejected):
                validate_action(op, {})

    def test_failed_request_does_not_reach_sink(self):
        self.arm()
        self.reject(b'{"payload":"broken","mac":"false"}')
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
