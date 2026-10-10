"""Offline walk-forward backtest of Agente100 selection using completed candles.

Research simulation only. No live broker, no real orders, no human approval bypass:
historical hypothetical trades are NOT routed to Robo100.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .backtest import Bar, BacktestResult, Trade
from .core import Agente100, Direction
from .market import candidate_from_candles, GRANULARITY_SECONDS


@dataclass(frozen=True)
class HistoricalBar:
    time: int  # UTC candle opening timestamp
    open: float
    high: float
    low: float
    close: float


def simulate_agent_history(series: dict[str, list[HistoricalBar]], *,
                           starting_balance: float = 100.0,
                           fixed_notional: float = 10.0,
                           fee_rate: float = 0.001,
                           slippage_rate: float = 0.0005,
                           max_holding_bars: int = 8) -> BacktestResult:
    """Synchronized 15-minute series; one hypothetical position at a time.

    Signals use history up to candle i; execution starts at candle i+1.
    News is neutral, because a timestamp-aligned news archive is not yet available.
    """
    if not series:
        raise ValueError("No series")
    if not all(isfinite(x) for x in (starting_balance, fixed_notional, fee_rate, slippage_rate)):
        raise ValueError("Nonfinite configuration")
    if starting_balance <= 0 or fixed_notional <= 0 or not 0 <= fee_rate < 1 or not 0 <= slippage_rate < 1 or max_holding_bars < 1:
        raise ValueError("Invalid configuration")
    times = None
    for product, bars in series.items():
        if len(bars) < 24:
            raise ValueError("Need at least 24 candles per asset")
        ts = [b.time for b in bars]
        if ts != sorted(set(ts)) or any(b.time % GRANULARITY_SECONDS for b in bars):
            raise ValueError("Unordered or unaligned timestamps")
        if any(ts[k] - ts[k - 1] != GRANULARITY_SECONDS for k in range(1, len(ts))):
            raise ValueError("Missing candles")
        if times is None:
            times = ts
        elif times != ts:
            raise ValueError("Assets must share timestamps")
        for b in bars:
            if not all(isfinite(v) and v > 0 for v in (b.open, b.high, b.low, b.close)):
                raise ValueError("Invalid OHLC")
            if b.low > min(b.open, b.close) or b.high < max(b.open, b.close):
                raise ValueError("Invalid OHLC range")
    agent = Agente100()
    balance = peak = starting_balance
    max_dd = 0.0
    trades = []
    i = 21
    while i < len(times) - 1:
        candidates = []
        for product, bars in series.items():
            candles = [{"time": b.time, "close": b.close} for b in bars[:i + 1]]
            try:
                candidate = candidate_from_candles(
                    product, candles, news_score=0.0,
                    now=datetime.fromtimestamp(times[i] + GRANULARITY_SECONDS, tz=timezone.utc))
                candidates.append(candidate)
            except ValueError:
                continue
        signal = agent.choose(candidates)
        if signal is None:
            i += 1
            continue
        if balance < fixed_notional * (1 + fee_rate):
            break
        bars = series[signal.symbol]
        direction = signal.direction
        raw_entry = bars[i + 1].open
        entry = raw_entry * (1 + slippage_rate if direction == Direction.BUY else 1 - slippage_rate)
        # Scale the agent's TP/SL relative to actual next-open fill, not stale signal price.
        tp_ratio = signal.take_profit / signal.entry
        sl_ratio = signal.stop_loss / signal.entry
        tp, sl = entry * tp_ratio, entry * sl_ratio
        end = min(len(times) - 1, i + max_holding_bars)
        exit_price = None
        reason = "TIME"
        exit_index = end
        for j in range(i + 1, end + 1):
            b = bars[j]
            if direction == Direction.BUY:
                if b.low <= sl:
                    exit_price, reason = min(sl, b.open) * (1 - slippage_rate), "SL"
                elif b.high >= tp:
                    exit_price, reason = tp * (1 - slippage_rate), "TP"
            else:
                if b.high >= sl:
                    exit_price, reason = max(sl, b.open) * (1 + slippage_rate), "SL"
                elif b.low <= tp:
                    exit_price, reason = tp * (1 + slippage_rate), "TP"
            if exit_price is not None:
                exit_index = j
                break
        if exit_price is None:
            exit_price = bars[end].close * (1 - slippage_rate if direction == Direction.BUY else 1 + slippage_rate)
        change = exit_price / entry - 1 if direction == Direction.BUY else 1 - exit_price / entry
        pnl = fixed_notional * (change - 2 * fee_rate)
        balance += pnl
        peak = max(peak, balance)
        max_dd = max(max_dd, (peak - balance) / peak * 100)
        trades.append(Trade(i + 1, exit_index, direction, entry, exit_price, reason, pnl))
        i = exit_index + 1
    return BacktestResult(tuple(trades), starting_balance, balance, max_dd)
