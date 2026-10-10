"""Read-only public candles + RSS headlines; analysis only, no orders."""
from .core import Agente100
from .market import ALLOWED_PRODUCTS, candidate_from_candles, fetch_candles
from .news import fetch_headlines, score_asset


def main() -> None:
    print("RESEARCH ONLY — no orders, no approval, no broker access")
    try:
        headlines = fetch_headlines()
        print(f"Recent timestamped headlines: {len(headlines)}")
    except Exception as exc:
        print(f"News unavailable ({type(exc).__name__}: {exc}); using neutral scores")
        headlines = []
    candidates = []
    for product in ALLOWED_PRODUCTS:
        try:
            sentiment = score_asset(headlines, product)
            candidate = candidate_from_candles(product, fetch_candles(product), news_score=sentiment)
            candidates.append(candidate)
            print(f"{product}: price={candidate.price:.4f}, RSI={candidate.rsi:.1f}, news={sentiment:+.2f}")
        except Exception as exc:
            print(f"{product}: skipped ({type(exc).__name__}: {exc})")
    signal = Agente100().choose(candidates)
    print("ANALYSIS ONLY:", signal if signal else "no fresh valid candidates")


if __name__ == "__main__":
    main()
