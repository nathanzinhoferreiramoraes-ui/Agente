import io
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from agente100.market import candidate_from_candles, fetch_candles


class MarketIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        start = int(self.now.timestamp()) - 24 * 900
        self.candles = [{"time": start + i * 900, "close": 100 + i} for i in range(23)]

    def test_gap_rejected(self):
        with self.assertRaises(ValueError):
            candidate_from_candles("BTC-USD", self.candles[:10] + self.candles[11:], now=self.now)

    def test_future_rejected(self):
        future = {"time": int(self.now.timestamp()) + 900, "close": 200}
        with self.assertRaises(ValueError):
            candidate_from_candles("BTC-USD", self.candles + [future], now=self.now)

    def test_nan_news_rejected(self):
        with self.assertRaises(ValueError):
            candidate_from_candles("BTC-USD", self.candles, news_score=float("nan"), now=self.now)

    def test_public_ohlc_open_outside_range_rejected(self):
        raw = [[int(self.now.timestamp()) - 900, 99, 101, 105, 100, 10]]
        with patch("agente100.market.urlopen", return_value=io.BytesIO(json.dumps(raw).encode())):
            with self.assertRaises(ValueError):
                fetch_candles("BTC-USD")

    def test_public_duplicate_rejected(self):
        raw = [[int(self.now.timestamp()) - 900, 99, 101, 100, 100, 10]] * 2
        with patch("agente100.market.urlopen", return_value=io.BytesIO(json.dumps(raw).encode())):
            with self.assertRaises(ValueError):
                fetch_candles("BTC-USD")


if __name__ == "__main__":
    unittest.main()
