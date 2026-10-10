"""Explicit read-only historical research; never execute orders."""
from datetime import datetime, timezone
from .history import run_public_history


def main():
    print("Public historical OHLC research — no broker or real orders")
    try:
        result = run_public_history(end=datetime.now(timezone.utc), candles=120)
    except Exception as exc:
        print(f"Cannot backtest safely: {type(exc).__name__}: {exc}")
        return
    print(f"Trades: {len(result.trades)}; win rate: {result.win_rate:.1%}")
    print(f"Paper balance: {result.starting_balance:.2f} -> {result.ending_balance:.2f}")
    print(f"Maximum realized drawdown: {result.max_drawdown_pct:.2f}%")
    print("Historical headlines unavailable: neutral sentiment. NOT a profitability forecast.")


if __name__ == "__main__":
    main()
