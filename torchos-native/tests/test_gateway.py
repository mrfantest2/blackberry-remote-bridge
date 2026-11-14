"""Contract-only gateway: ephemeral test keys, no sockets or live services."""
import hashlib
import hmac
import importlib.util
import json
from pathlib import Path
import threading
import unittest

SPEC = importlib.util.spec_from_file_location('torchos_gateway', Path(__file__).resolve().parents[1] / 'gateway/contract.py')


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.api)

    def setUp(self):
        self.key = bytes(range(32))  # Synthetic fixture, never production pairing material.
        self.now = 1000
        self.gateway = self.api.Gateway({'test-a': self.key, 'test-b': b'b' * 32}, clock=lambda: self.now)

    def request(self, **changes):
        fields = dict(device='test-a', op='status', issued=1000, expires=1030, nonce='a' * 32)
        fields.update(changes)
        return self.api.sign(self.key, **fields)

    def reject(self, data, device='test-a'):
        with self.assertRaises(self.api.InvalidRequest): self.gateway.verify(data, device)

    def resign(self, data, **changes):
        value = json.loads(data); value.update(changes); value.pop('mac', None)
        payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
        value['mac'] = hmac.new(self.key, payload, hashlib.sha256).hexdigest()
        return json.dumps(value, separators=(',', ':')).encode()

    def test_four_read_only_operations_and_redacted_audit(self):
        for i, op in enumerate(['status', 'network', 'services', 'inventory']):
            result = self.gateway.verify(self.request(op=op, nonce=f'{i:032x}'), 'test-a')
            self.assertEqual(result, op)
        self.assertEqual(self.gateway.audit, {'event': 'accepted', 'op': 'inventory'})

    def test_bad_mac_wrong_key_wrong_device(self):
        data = self.request()
        value=json.loads(data); value['mac']='0'*64
        self.reject(json.dumps(value).encode())
        self.reject(self.api.sign(b'x' * 32, 'test-a', 'status', 1000, 1030, 'a' * 32))
        self.reject(data, 'test-b')
        self.reject(self.request(device='unknown'))
        self.assertEqual(self.gateway.audit, {'event': 'rejected'})

    def test_replay_and_expiry_boundaries(self):
        data=self.request(); self.gateway.verify(data, 'test-a'); self.reject(data)
        self.now=1030; self.reject(data)
        self.reject(self.request(issued=900, expires=950))
        self.reject(self.request(issued=1100, expires=1130))
        self.now=1000; self.gateway=self.api.Gateway({'test-a':self.key},clock=lambda:self.now)
        self.reject(self.request(expires=1100))
        self.reject(self.request(expires=999)); self.reject(self.request(issued=1006))
        self.assertEqual(self.gateway.verify(self.request(issued=1005, expires=1035, nonce='b'*32), 'test-a'), 'status')

    def test_mutated_and_signed_disallowed_operations(self):
        data=self.request(); value=json.loads(data); value['op']='inventory'
        self.reject(json.dumps(value).encode())
        for op in ['exec', 'reboot', 'status; id', 'STATUS', '', ['status'], {'op':'status'}]:
            self.reject(self.resign(data, op=op))

    def test_strict_types_fields_versions_and_nonce(self):
        data=self.request()
        for changes in [dict(v=True),dict(v=2),dict(issued=True),dict(expires=1030.0),dict(device=[]),
                        dict(nonce='A'*32),dict(nonce='x'),dict(nonce=[]),dict(extra='ignored'),dict(mac=[]),dict(op=None)]:
            value=self.resign(data, **changes) if 'mac' not in changes else b'{"mac":[]}'
            self.reject(value)
        for raw in [b'', b'[]', b'null', b'{}', b'\xff', b'{', b'{"x":1,"x":2}', b'{}' + b' '*1023, 'not bytes']:
            self.reject(raw)
        self.reject(self.request(), device=None)

    def test_duplicate_json_and_bad_envelopes(self):
        data=self.request()
        self.reject(data[:-1] + b',"op":"status"}')
        self.reject(self.resign(data, issued=float('nan')))
        self.reject(self.resign(data, issued=-1))
        self.reject(self.resign(data, expires=1000))
        value=json.loads(data); del value['nonce']; self.reject(json.dumps(value).encode())

    def test_capacity_fails_closed_then_prunes_expired(self):
        self.gateway=self.api.Gateway({'test-a':self.key}, clock=lambda:self.now, capacity=1)
        self.gateway.verify(self.request(), 'test-a')
        self.reject(self.request(nonce='b'*32))
        self.now=1031
        self.assertEqual(self.gateway.verify(self.request(issued=1031,expires=1060,nonce='c'*32), 'test-a'), 'status')

    def test_clock_rollback_fails_closed_after_cache_prune(self):
        data=self.request();self.gateway.verify(data,'test-a')
        self.now=1031;self.gateway.verify(self.request(issued=1031,expires=1060,nonce='b'*32),'test-a')
        self.now=1000;self.reject(data)

    def test_concurrent_replay_accepts_once(self):
        accepted=[]
        def call():
            try: accepted.append(self.gateway.verify(self.request(), 'test-a'))
            except self.api.InvalidRequest: pass
        threads=[threading.Thread(target=call) for _ in range(8)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(accepted,['status'])

    def test_configuration_and_clock_fail_closed(self):
        for keys in [{}, {'test-a':b'short'}, {'bad/id':self.key}, {'test-a':'plaintext'}]:
            with self.assertRaises(ValueError): self.api.Gateway(keys)
        self.gateway=self.api.Gateway({'test-a':self.key},clock=lambda:float('nan'))
        self.reject(self.request())
        self.gateway=self.api.Gateway({'test-a':self.key},clock=lambda:1/0)
        self.reject(self.request())


if __name__ == '__main__': unittest.main(verbosity=2)
