import unittest
from agente100.backtest import Bar, run_backtest


class BacktestTests(unittest.TestCase):
    def setUp(self):
        self.flat = [Bar(100, 100, 100, 100) for _ in range(20)]

    def test_flat_market_no_trades(self):
        result = run_backtest(self.flat + [Bar(100, 100, 100, 100)] * 5)
        self.assertEqual(len(result.trades), 0)
        self.assertEqual(result.ending_balance, 100)

    def test_entry_next_bar_and_stop_priority(self):
        bars = self.flat + [
            Bar(100, 102, 100, 102),  # breakout signal at index 20
            Bar(102, 105, 98, 102),   # both TP and SL; SL wins
        ]
        result = run_backtest(bars, fee_rate=0, slippage_rate=0)
        self.assertEqual(len(result.trades), 1)
        self.assertEqual(result.trades[0].entry_index, 21)
        self.assertEqual(result.trades[0].reason, "SL")
        self.assertLess(result.ending_balance, 100)

    def test_fee_reduces_return(self):
        bars = self.flat + [Bar(100, 102, 100, 102), Bar(102, 104, 102, 104)]
        no_fee = run_backtest(bars, fee_rate=0, slippage_rate=0)
        with_fee = run_backtest(bars, fee_rate=0.001, slippage_rate=0)
        self.assertLess(with_fee.ending_balance, no_fee.ending_balance)

    def test_bad_prices_rejected(self):
        with self.assertRaises(ValueError):
            run_backtest([Bar(100, 99, 101, 100)])

    def test_bad_config_rejected(self):
        with self.assertRaises(ValueError):
            run_backtest([], fee_rate=-1)


if __name__ == "__main__":
    unittest.main()
