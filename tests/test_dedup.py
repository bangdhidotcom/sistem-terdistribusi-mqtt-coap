"""Unit test logika deduplikasi berdasarkan id."""
import sys
import unittest
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from common.schema import make_message


class Dedup:
    def __init__(self):
        self.seen = deque(maxlen=5000)
        self.seen_set = set()

    def process(self, msg):
        mid = msg["id"]
        if mid in self.seen_set:
            return "SKIP_DUP"
        self.seen.append(mid)
        self.seen_set.add(mid)
        if len(self.seen_set) > 5000:
            self.seen_set.discard(self.seen.popleft())
        return "CONV_IN"


class TestDedup(unittest.TestCase):
    def test_first_time_processed(self):
        d = Dedup()
        msg = make_message("coap_client", 1, b"data", "c2m")
        self.assertEqual(d.process(msg), "CONV_IN")

    def test_duplicate_skipped(self):
        d = Dedup()
        msg = make_message("coap_client", 1, b"data", "c2m")
        d.process(msg)
        self.assertEqual(d.process(msg), "SKIP_DUP")

    def test_different_id_processed(self):
        d = Dedup()
        d.process(make_message("coap_client", 1, b"data", "c2m"))
        self.assertEqual(d.process(make_message("coap_client", 2, b"data", "c2m")), "CONV_IN")


if __name__ == "__main__":
    unittest.main()
