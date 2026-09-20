import importlib.util
from pathlib import Path
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[1] / 'tools/web_bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class BridgeTests(unittest.TestCase):
    def test_valid_sample_and_malformed_lines(self):
        sample = dict(schema=1, source='openvela', seq=1, cycle=0,
                      frame=1, count=16, latency_ns=1000,
                      size=100, rate=0, lplc2=100, lc4=0, gf=43,
                      state='SAFE', ai='FORWARD', action='FORWARD', decision='AI')
        self.assertEqual(bridge.validate(sample), sample)
        for line in (b'FR1 null', b'FR1 []', b'FR1 bad-json', b'NSH welcome'):
            bridge.publish(line)
        for key, value in [('gf', 1201), ('size', -1), ('count', 0), ('frame', 16), ('seq', True)]:
            with self.assertRaises(ValueError):
                bridge.validate({**sample, key: value})

    def test_reject_host_and_invalid_sample(self):
        for source in ('host-reference', 'browser', 'openvela'):
            with self.assertRaises(ValueError):
                bridge.validate({'source': source, 'schema': 1})

    def test_chunked_telnet_negotiation(self):
        class Connection:
            def __init__(self): self.sent = b''
            def sendall(self, data): self.sent += data
        conn = Connection()
        decoder = bridge.TelnetFilter()
        self.assertEqual(decoder.feed(b'FR1 \xff', conn), b'FR1 ')
        self.assertEqual(decoder.feed(b'\xfb\x01{}\n', conn), b'{}\n')
        self.assertEqual(conn.sent, b'\xff\xfe\x01')

if __name__ == '__main__': unittest.main()
