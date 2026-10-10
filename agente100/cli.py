"""Interactive paper-only approval; run: python -m agente100.cli."""
from .core import Agente100, Robo100, Candidate, Direction


def main() -> None:
    # Synthetic prices and manually assigned sentiment. Not live market data.
    candidates = [
        Candidate("BTC/USDT", 60000.0, Direction.BUY, 55, False, 0.1),
        Candidate("ETH/USDT", 3000.0, Direction.BUY, 68, True, 0.4),
        Candidate("SOL/USDT", 150.0, Direction.SELL, 35, False, -0.2),
    ]
    signal = Agente100().choose(candidates)
    if signal is None:
        print("No valid signal")
        return
    robot = Robo100(fixed_notional=10.0, balance=100.0)
    print("PAPER ONLY — synthetic data; no real exchange orders")
    print(f"Asset: {signal.symbol} | Direction: {signal.direction.value}")
    print(f"Entry: {signal.entry:.6f} | TP: {signal.take_profit:.6f} | SL: {signal.stop_loss:.6f}")
    print(f"Robot preset simulated notional: {robot.fixed_notional:.2f}")
    print(f"Signal ID: {signal.id}")
    approval = input("To approve this simulated order, type the exact signal ID: ").strip()
    if approval != signal.id:
        print("Rejected: no matching approval; nothing executed.")
        return
    print(robot.execute(signal, approved_signal_id=approval))


if __name__ == "__main__":
    main()
