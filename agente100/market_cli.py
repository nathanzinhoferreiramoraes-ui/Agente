"""Explicitly fetch read-only market data; never place an order."""
from .core import Agente100
from .market import ALLOWED_PRODUCTS, candidate_from_candles, fetch_candles


def main() -> None:
    print("Public 15-minute candles — research only, no order execution")
    candidates = []
    for product in ALLOWED_PRODUCTS:
        try:
            candidate = candidate_from_candles(product, fetch_candles(product))
            candidates.append(candidate)
            print(f"{product}: close={candidate.price:.4f}, RSI={candidate.rsi:.2f}, breakout={candidate.bollinger_breakout}")
        except Exception as exc:
            print(f"{product}: unavailable ({type(exc).__name__}: {exc})")
    signal = Agente100().choose(candidates)
    if signal is None:
        print("No fresh valid signal")
    else:
        print("ANALYSIS ONLY — signal NOT approved or executed:", signal)


if __name__ == "__main__":
    main()
