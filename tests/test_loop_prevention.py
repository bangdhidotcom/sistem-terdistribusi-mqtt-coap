"""Unit test pencegahan loop konversi balik."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from common.schema import make_message, mark_processed, validate_message


def should_convert(msg):
    return not msg.get("meta", {}).get("origin_processed", False)


class TestLoopPrevention(unittest.TestCase):
    def test_fresh_message_converted(self):
        msg = make_message("coap_client", 1, b"data", "c2m")
        self.assertTrue(should_convert(msg))

    def test_marked_message_not_converted(self):
        msg = make_message("coap_client", 1, b"data", "c2m")
        mark_processed(msg)
        self.assertFalse(should_convert(msg))

    def test_marked_message_still_valid(self):
        msg = make_message("mqtt_publisher", 1, b"data", "m2c")
        mark_processed(msg)
        self.assertEqual(validate_message(msg), [])
        self.assertIn("conversion_server", msg["meta"]["hops"])

    def test_double_mark_idempotent(self):
        msg = make_message("mqtt_publisher", 1, b"data", "m2c")
        mark_processed(msg)
        mark_processed(msg)
        self.assertEqual(msg["meta"]["hops"].count("conversion_server"), 1)


if __name__ == "__main__":
    unittest.main()
