import unittest
from agente100.agent_backtest import HistoricalBar, simulate_agent_history


class AgentHistoryTests(unittest.TestCase):
    def setUp(self):
        start = 1_791_590_400  # divisible by 900
        start -= start % 900
        self.bars = [
            HistoricalBar(start + i * 900, 100 + i, 101 + i, 99 + i, 100 + i)
            for i in range(30)
        ]

    def test_walk_forward_returns_paper_result(self):
        result = simulate_agent_history({"BTC-USD": self.bars})
        self.assertEqual(result.starting_balance, 100)
        self.assertGreaterEqual(len(result.trades), 1)
        self.assertTrue(all(t.entry_index > 21 for t in result.trades))

    def test_rejects_misaligned_assets(self):
        shifted = [
            HistoricalBar(b.time + 900, b.open, b.high, b.low, b.close)
            for b in self.bars
        ]
        with self.assertRaises(ValueError):
            simulate_agent_history({"BTC-USD": self.bars, "ETH-USD": shifted})

    def test_rejects_missing_candle(self):
        with self.assertRaises(ValueError):
            simulate_agent_history({"BTC-USD": self.bars[:10] + self.bars[11:]})

    def test_rejects_invalid_config(self):
        with self.assertRaises(ValueError):
            simulate_agent_history({"BTC-USD": self.bars}, fee_rate=-0.1)


if __name__ == "__main__":
    unittest.main()
