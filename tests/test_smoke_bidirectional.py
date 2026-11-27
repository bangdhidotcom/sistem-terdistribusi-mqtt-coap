"""Smoke test dua arah tanpa jaringan: encode → decode → verifikasi."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from common.schema import (decode_message, encode_message, make_message,
                           mark_processed, payload_of, set_ts, sha256_of,
                           validate_message)


class TestBidirectionalSmoke(unittest.TestCase):
    def _trip(self, direction):
        payload = b"SMOKE-" + bytes(range(256)) * 16
        msg = make_message("source", 1, payload, direction)
        set_ts(msg, "conv_recv_ts")
        mark_processed(msg)
        set_ts(msg, "conv_send_ts")
        set_ts(msg, "dst_recv_ts")
        received = decode_message(encode_message(msg))
        self.assertEqual(validate_message(received), [])
        self.assertEqual(received["direction"], direction)
        self.assertEqual(payload_of(received), payload)
        self.assertEqual(sha256_of(payload_of(received)), received["payload_sha256"])
        self.assertTrue(received["meta"]["origin_processed"])
        self.assertLess(received["meta"]["conv_recv_ts"], received["meta"]["conv_send_ts"])
        self.assertLess(received["meta"]["conv_send_ts"], received["meta"]["dst_recv_ts"])

    def test_mqtt_to_coap(self):
        self._trip("m2c")

    def test_coap_to_mqtt(self):
        self._trip("c2m")


if __name__ == "__main__":
    unittest.main()
