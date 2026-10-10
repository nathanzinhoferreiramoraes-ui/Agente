"""Read-only Coinbase Exchange public candles; no API keys or trading endpoints."""
import json
import math
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

from .core import Candidate, Direction

BASE_URL = "https://api.exchange.coinbase.com"
ALLOWED_PRODUCTS = ("BTC-USD", "ETH-USD", "SOL-USD")
GRANULARITY_SECONDS = 900


def fetch_candles(product: str, timeout: int = 10) -> list[dict]:
    """Fetch public 15-minute candles. Network access is opt-in by caller."""
    if product not in ALLOWED_PRODUCTS:
        raise ValueError("Product not on allowlist")
    if not 1 <= timeout <= 30:
        raise ValueError("Invalid timeout")
    url = f"{BASE_URL}/products/{quote(product)}/candles?granularity={GRANULARITY_SECONDS}"
    req = Request(url, headers={"User-Agent": "Agente100-PaperResearch/0.1", "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise ValueError("Unexpected market response")
    candles = []
    for item in payload:
        if not isinstance(item, list) or len(item) < 6:
            raise ValueError("Malformed candle")
        ts, low, high, opened, close, volume = map(float, item[:6])
        if not all(math.isfinite(v) for v in (ts, low, high, opened, close, volume)):
            raise ValueError("Non-finite market value")
        if min(low, high, opened, close) <= 0 or low > min(opened, close) or high < max(opened, close):
            raise ValueError("Invalid OHLC")
        if ts != int(ts) or int(ts) % GRANULARITY_SECONDS:\n            raise ValueError("Invalid candle timestamp")\n        candles.append({"time": int(ts), "close": close})
    ordered = sorted(candles, key=lambda c: c["time"])\n    if len({c["time"] for c in ordered}) != len(ordered):\n        raise ValueError("Duplicate candles")\n    return ordered


def rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        raise ValueError("Not enough candles for RSI")
    diffs = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    gains = sum(max(d, 0) for d in diffs) / period
    losses = sum(max(-d, 0) for d in diffs) / period
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    return 100 - 100 / (1 + gains / losses)


def candidate_from_candles(product: str, candles: list[dict], news_score: float = 0.0,
                           now: datetime | None = None) -> Candidate:
    """Use only completed 15m candles; require fresh and strictly ordered data."""
    if product not in ALLOWED_PRODUCTS:
        raise ValueError("Product not on allowlist")
    if len(candles) < 22:
        raise ValueError("At least 22 candles required")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware now required")
    times = [int(c["time"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    if (times != sorted(set(times))\n            or any(t % GRANULARITY_SECONDS for t in times)\n            or any(times[i] - times[i - 1] != GRANULARITY_SECONDS for i in range(1, len(times)))\n            or not all(math.isfinite(v) and v > 0 for v in closes)\n            or not math.isfinite(news_score) or not -1 <= news_score <= 1):
        raise ValueError("Unordered or invalid candles")
    now_ts = now.timestamp()
    completed = [(t, c) for t, c in zip(times, closes) if t + GRANULARITY_SECONDS <= now_ts]
    if any(t > now_ts for t in times):\n        raise ValueError("Future candle timestamp")\n    if len(completed) < 21:
        raise ValueError("Not enough completed candles")
    if now_ts - (completed[-1][0] + GRANULARITY_SECONDS) > 2 * GRANULARITY_SECONDS:
        raise ValueError("Stale candles")
    values = [v for _, v in completed]
    price = values[-1]
    previous = values[-21:-1]
    mean = sum(previous) / len(previous)
    std = math.sqrt(sum((x - mean) ** 2 for x in previous) / len(previous))
    upper, lower = mean + 2 * std, mean - 2 * std
    direction = Direction.BUY if price >= values[-2] else Direction.SELL
    breakout = price > upper if direction == Direction.BUY else price < lower
    volatility = std / mean if mean > 0 else 0.0
    return Candidate(product, price, direction, rsi(values), breakout, news_score, volatility)
