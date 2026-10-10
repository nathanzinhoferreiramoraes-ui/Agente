"""Fetch a bounded public Coinbase OHLC history for offline paper research."""
import json
from datetime import datetime, timedelta, timezone
from math import isfinite
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .agent_backtest import HistoricalBar, simulate_agent_history
from .market import ALLOWED_PRODUCTS, BASE_URL, GRANULARITY_SECONDS


def fetch_history(product: str, *, end: datetime, candles: int = 120, timeout: int = 10) -> list[HistoricalBar]:
    """Read-only, at most 300 complete 15-minute candles; reject gaps."""
    if product not in ALLOWED_PRODUCTS:
        raise ValueError("Unsupported product")
    if end.tzinfo is None:
        raise ValueError("End must be timezone aware")
    if not 24 <= candles <= 300 or not 1 <= timeout <= 30:
        raise ValueError("Invalid request configuration")
    end_utc = end.astimezone(timezone.utc)
    aligned = datetime.fromtimestamp(
        int(end_utc.timestamp()) // GRANULARITY_SECONDS * GRANULARITY_SECONDS,
        tz=timezone.utc)
    start = aligned - timedelta(seconds=candles * GRANULARITY_SECONDS)
    params = urlencode({"start": start.isoformat(), "end": aligned.isoformat(),
                        "granularity": GRANULARITY_SECONDS})
    url = f"{BASE_URL}/products/{product}/candles?{params}"
    req = Request(url, headers={"User-Agent": "Agente100-PaperResearch/0.1",
                                "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise ValueError("Unexpected exchange response")
    parsed = {}
    for raw in payload:
        if not isinstance(raw, list) or len(raw) < 6:
            raise ValueError("Malformed candle")
        ts, low, high, opened, close, volume = map(float, raw[:6])
        if not all(isfinite(v) for v in (ts, low, high, opened, close, volume)):
            raise ValueError("Nonfinite candle")
        t = int(ts)
        if t != ts or t % GRANULARITY_SECONDS:
            raise ValueError("Unaligned candle")
        if t < int(start.timestamp()) or t >= int(aligned.timestamp()):
            continue
        if t in parsed or min(low, high, opened, close) <= 0 or low > min(opened, close) or high < max(opened, close):
            raise ValueError("Duplicate or invalid candle")
        parsed[t] = HistoricalBar(t, opened, high, low, close)
    expected = range(int(start.timestamp()), int(aligned.timestamp()), GRANULARITY_SECONDS)
    if any(t not in parsed for t in expected):
        raise ValueError("Historical feed has missing candles; cannot backtest")
    return [parsed[t] for t in expected]


def run_public_history(*, end: datetime, candles: int = 120):
    """Download synchronized BTC/ETH/SOL data; abort on any source error."""
    series = {product: fetch_history(product, end=end, candles=candles)
              for product in ALLOWED_PRODUCTS}
    return simulate_agent_history(series)
