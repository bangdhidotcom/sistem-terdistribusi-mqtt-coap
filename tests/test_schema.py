"""Unit test skema pesan bersama."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from common.schema import (decode_message, encode_message, make_message,
                           mark_processed, payload_of, sha256_of, validate_message)


class TestSchema(unittest.TestCase):
    def test_roundtrip_m2c(self):
        msg = make_message("mqtt_publisher", 1, b"payload-contoh", "m2c")
        decoded = decode_message(encode_message(msg))
        self.assertEqual(decoded["id"], msg["id"])
        self.assertEqual(payload_of(decoded), b"payload-contoh")
        self.assertEqual(validate_message(decoded), [])

    def test_roundtrip_c2m(self):
        msg = make_message("coap_client", 2, b"x" * 4096, "c2m")
        decoded = decode_message(encode_message(msg))
        self.assertEqual(decoded["direction"], "c2m")
        self.assertEqual(len(payload_of(decoded)), 4096)
        self.assertEqual(sha256_of(payload_of(decoded)), decoded["payload_sha256"])

    def test_unique_id_and_timestamp(self):
        a = make_message("s", 1, b"a", "m2c")
        b = make_message("s", 2, b"a", "m2c")
        self.assertNotEqual(a["id"], b["id"])
        self.assertLessEqual(a["sent_ts"], b["sent_ts"])

    def test_corrupted_hash_detected(self):
        msg = make_message("s", 1, b"abc", "m2c")
        msg["payload_sha256"] = "0" * 64
        self.assertTrue(any("sha256" in e for e in validate_message(msg)))


if __name__ == "__main__":
    unittest.main()
