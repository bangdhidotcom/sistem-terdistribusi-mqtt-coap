"""Unit test encoder MQTT broker tanpa membuka socket."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mqtt_broker import _enc_str, _matches, _packet_len, _read_str


class TestBrokerPacket(unittest.TestCase):
    def test_packet_len_single_byte(self):
        self.assertEqual(_packet_len(b"x" * 15), b"\x0f")

    def test_packet_len_multi_byte(self):
        body = b"x" * 200
        encoded = _packet_len(body)
        self.assertGreater(len(encoded), 1)
        self.assertEqual(encoded[-1] & 128, 0)

    def test_string_roundtrip(self):
        raw = _enc_str("iot/test") + b"payload"
        text, offset = _read_str(raw, 0)
        self.assertEqual(text, "iot/test")
        self.assertEqual(raw[offset:], b"payload")

    def test_topic_matching(self):
        self.assertTrue(_matches("iot/test", "iot/test"))
        self.assertTrue(_matches("iot/#", "iot/test"))
        self.assertTrue(_matches("iot/+", "iot/test"))
        self.assertFalse(_matches("iot/+", "iot/a/b"))


if __name__ == "__main__":
    unittest.main()
