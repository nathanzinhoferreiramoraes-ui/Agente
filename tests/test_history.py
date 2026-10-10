import io
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from agente100.history import fetch_history


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.end = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        end_ts = int(self.end.timestamp())
        self.payload = [
            [end_ts - (i + 1) * 900, 99, 101, 100, 100, 5]
            for i in range(24)
        ]

    def mock_response(self, payload):
        return patch("agente100.history.urlopen", return_value=io.BytesIO(json.dumps(payload).encode()))

    def test_valid_24_candles(self):
        with self.mock_response(self.payload):
            bars = fetch_history("BTC-USD", end=self.end, candles=24)
        self.assertEqual(len(bars), 24)
        self.assertEqual(bars[0].time, int(self.end.timestamp()) - 24 * 900)
        self.assertEqual(bars[-1].close, 100)

    def test_missing_candle_rejected(self):
        with self.mock_response(self.payload[:-1]):
            with self.assertRaises(ValueError):
                fetch_history("BTC-USD", end=self.end, candles=24)

    def test_duplicate_candle_rejected(self):
        with self.mock_response(self.payload + [self.payload[0]]):
            with self.assertRaises(ValueError):
                fetch_history("BTC-USD", end=self.end, candles=24)

    def test_no_future_candle(self):
        future = [int(self.end.timestamp()), 99, 101, 100, 100, 5]
        with self.mock_response(self.payload + [future]):
            bars = fetch_history("BTC-USD", end=self.end, candles=24)
        self.assertEqual(len(bars), 24)

    def test_invalid_symbol(self):
        with self.assertRaises(ValueError):
            fetch_history("FAKE-USD", end=self.end)


if __name__ == "__main__":
    unittest.main()
