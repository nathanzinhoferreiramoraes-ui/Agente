import math
import unittest
from dataclasses import replace
from agente100 import Agente100, Robo100, Candidate, Direction


class NumericalSafetyTests(unittest.TestCase):
    def test_nan_candidate_is_ignored(self):
        agent = Agente100()
        signal = agent.choose([
            Candidate("BAD", math.nan, Direction.BUY, 60, True),
            Candidate("GOOD", 100, Direction.BUY, 60, False),
        ])
        self.assertEqual(signal.symbol, "GOOD")

    def test_infinite_rsi_rejected(self):
        self.assertIsNone(Agente100().choose([
            Candidate("BAD", 100, Direction.BUY, math.inf, True)
        ]))

    def test_invalid_direction_rejected(self):
        self.assertIsNone(Agente100().choose([
            Candidate("BAD", 100, "BUY", 60, True)
        ]))

    def test_nonfinite_notional_rejected(self):
        with self.assertRaises(ValueError):
            Robo100(fixed_notional=math.inf)

    def test_nonfinite_exit_rejected(self):
        signal = Agente100().choose([
            Candidate("BTC", 100, Direction.BUY, 60, True)
        ])
        with self.assertRaises(ValueError):
            Robo100().execute(replace(signal, stop_loss=math.nan), signal.id)


if __name__ == "__main__":
    unittest.main()
