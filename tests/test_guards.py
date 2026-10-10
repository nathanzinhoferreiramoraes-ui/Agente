import unittest
from dataclasses import replace

from agente100 import Agente100, Robo100, Candidate, Direction


class GuardTests(unittest.TestCase):
    def test_no_candidates(self):
        self.assertIsNone(Agente100().choose([]))

    def test_invalid_candidates(self):
        self.assertIsNone(Agente100().choose([
            Candidate("X", -1, Direction.BUY, 50, False),
            Candidate("Y", 100, Direction.BUY, 120, True),
        ]))

    def test_short_side_exits(self):
        signal = Agente100().choose([Candidate("X", 100, Direction.SELL, 30, True)])
        self.assertLess(signal.take_profit, signal.entry)
        self.assertGreater(signal.stop_loss, signal.entry)

    def test_insufficient_balance(self):
        signal = Agente100().choose([Candidate("X", 100, Direction.BUY, 60, True)])
        robot = Robo100(fixed_notional=200, balance=100)
        with self.assertRaises(ValueError):
            robot.execute(signal, signal.id)

    def test_invalid_exits(self):
        signal = Agente100().choose([Candidate("X", 100, Direction.BUY, 60, True)])
        robot = Robo100()
        with self.assertRaises(ValueError):
            robot.execute(replace(signal, take_profit=90), signal.id)


if __name__ == "__main__":
    unittest.main()
