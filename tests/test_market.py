import unittest
from datetime import datetime, timezone

from agente100.core import Direction
from agente100.market import candidate_from_candles, rsi, fetch_candles


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        start = int(self.now.timestamp()) - 25 * 900
        self.candles = [{"time": start + i * 900, "close": 100 + i} for i in range(24)]

    def test_rsi_uptrend(self):
        self.assertEqual(rsi(list(range(30))), 100)

    def test_completed_candles_only(self):
        candidate = candidate_from_candles("BTC-USD", self.candles, now=self.now)
        self.assertEqual(candidate.direction, Direction.BUY)
        self.assertEqual(candidate.price, 123)

    def test_stale_rejected(self):
        with self.assertRaises(ValueError):
            candidate_from_candles("BTC-USD", self.candles, now=datetime(2026, 10, 11, tzinfo=timezone.utc))

    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):
            candidate_from_candles("BTC-USD", list(reversed(self.candles)), now=self.now)

    def test_allowlist(self):
        with self.assertRaises(ValueError):
            fetch_candles("INVALID-USD")


if __name__ == "__main__":
    unittest.main()
