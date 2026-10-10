import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from agente100 import Agente100, Robo100, Candidate, Direction


class TestPaperTrading(unittest.TestCase):
    def setUp(self):
        self.signal = Agente100().choose([
            Candidate("BTC/USDT", 100, Direction.BUY, 55, False),
            Candidate("ETH/USDT", 200, Direction.BUY, 70, True),
        ])
        self.robot = Robo100(fixed_notional=10, balance=100)

    def test_prefers_breakout(self):
        self.assertEqual(self.signal.symbol, "ETH/USDT")

    def test_requires_exact_approval(self):
        with self.assertRaises(PermissionError):
            self.robot.execute(self.signal)
        with self.assertRaises(PermissionError):
            self.robot.execute(self.signal, "wrong")

    def test_executes_paper_only_with_fixed_size(self):
        order = self.robot.execute(self.signal, self.signal.id)
        self.assertEqual(order["mode"], "PAPER")
        self.assertEqual(order["notional"], 10)
        self.assertEqual(order["status"], "SIMULATED_OPEN")

    def test_rejects_duplicate(self):
        self.robot.execute(self.signal, self.signal.id)
        with self.assertRaises(ValueError):
            self.robot.execute(self.signal, self.signal.id)

    def test_rejects_expired(self):
        old = replace(self.signal, created_at=datetime.now(timezone.utc) - timedelta(hours=1))
        with self.assertRaises(ValueError):
            self.robot.execute(old, old.id)

    def test_rejects_bad_stop(self):
        bad = replace(self.signal, stop_loss=self.signal.entry * 1.1)
        with self.assertRaises(ValueError):
            self.robot.execute(bad, bad.id)


if __name__ == "__main__":
    unittest.main()
