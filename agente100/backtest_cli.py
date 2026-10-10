"""Offline demonstration with SYNTHETIC prices. No broker connection."""
from .backtest import Bar, run_backtest


def main() -> None:
    prices = [100.0] * 20 + [102.0, 103.0, 104.0, 101.0, 100.0, 99.0, 98.0, 97.0]
    bars = [Bar(p, p * 1.003, p * 0.997, p) for p in prices]
    result = run_backtest(bars)
    print("SYNTHETIC BACKTEST ONLY — not historical performance")
    print(f"Trades: {len(result.trades)} | Win rate: {result.win_rate:.1%}")
    print(f"Balance: {result.starting_balance:.2f} -> {result.ending_balance:.2f}")
    print(f"Max drawdown: {result.max_drawdown_pct:.2f}%")
    for trade in result.trades:
        print(trade)


if __name__ == "__main__":
    main()
