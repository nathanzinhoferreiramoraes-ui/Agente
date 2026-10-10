"""Run with python -m agente100.demo."""
from .core import Agente100, Robo100, Candidate, Direction


def main():
    agent = Agente100()
    robot = Robo100(fixed_notional=10, balance=100)
    candidates = [
        Candidate("BTC/USDT", 60000, Direction.BUY, 55, False, 0.1),
        Candidate("ETH/USDT", 3000, Direction.BUY, 68, True, 0.4),
        Candidate("SOL/USDT", 150, Direction.SELL, 35, False, -0.2),
    ]
    signal = agent.choose(candidates)
    print("Signal awaiting approval:", signal)
    print("Demo only: explicit approval of signal ID")
    print(robot.execute(signal, approved_signal_id=signal.id))


if __name__ == "__main__":
    main()
