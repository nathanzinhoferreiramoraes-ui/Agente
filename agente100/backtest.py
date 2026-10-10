"""Offline, deterministic, paper-only OHLC backtest.

Signals use completed candles only. Entry occurs at the NEXT candle's open.
If TP and SL both occur in one candle, assume SL first (conservative).
"""
from dataclasses import dataclass
from math import isfinite
from .core import Direction


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Trade:
    entry_index: int
    exit_index: int
    direction: Direction
    entry: float
    exit: float
    reason: str
    pnl: float


@dataclass(frozen=True)
class BacktestResult:
    trades: tuple[Trade, ...]
    starting_balance: float
    ending_balance: float
    max_drawdown_pct: float

    @property
    def win_rate(self) -> float:
        return sum(t.pnl > 0 for t in self.trades) / len(self.trades) if self.trades else 0.0


def run_backtest(bars: list[Bar], *, starting_balance: float = 100.0,
                 fixed_notional: float = 10.0, fee_rate: float = 0.001,
                 slippage_rate: float = 0.0005, max_holding_bars: int = 8) -> BacktestResult:
    if not all(isfinite(x) for x in (starting_balance, fixed_notional, fee_rate, slippage_rate)):
        raise ValueError("Nonfinite configuration")
    if starting_balance <= 0 or fixed_notional <= 0 or not 0 <= fee_rate < 1 or not 0 <= slippage_rate < 1 or max_holding_bars < 1:
        raise ValueError("Invalid configuration")
    for b in bars:
        if not all(isfinite(v) and v > 0 for v in (b.open, b.high, b.low, b.close)):
            raise ValueError("Invalid bar prices")
        if b.low > min(b.open, b.close) or b.high < max(b.open, b.close):
            raise ValueError("Invalid OHLC range")
    balance = peak = starting_balance
    max_dd = 0.0
    trades = []
    # SMA(20) breakout uses only prior completed closes.
    i = 20
    while i < len(bars) - 1:
        prior = [b.close for b in bars[i - 20:i]]
        current = bars[i].close
        upper, lower = max(prior), min(prior)
        direction = Direction.BUY if current > upper else Direction.SELL if current < lower else None
        if direction is None:
            i += 1
            continue
        next_bar = bars[i + 1]
        # Fixed notional belongs to the simulated executor, not the signal logic.
        if balance < fixed_notional * (1 + fee_rate):
            break
        entry = next_bar.open * (1 + slippage_rate if direction == Direction.BUY else 1 - slippage_rate)
        tp = entry * (1.005 if direction == Direction.BUY else 0.995)
        sl = entry * (0.99 if direction == Direction.BUY else 1.01)
        end = min(len(bars) - 1, i + max_holding_bars)
        exit_price = None
        reason = "TIME"
        exit_index = end
        for j in range(i + 1, end + 1):
            b = bars[j]
            if direction == Direction.BUY:
                stop_hit = b.low <= sl
                target_hit = b.high >= tp
                if stop_hit:
                    exit_price, reason = min(sl, b.open) * (1 - slippage_rate), "SL"
                elif target_hit:
                    exit_price, reason = tp * (1 - slippage_rate), "TP"
            else:
                stop_hit = b.high >= sl
                target_hit = b.low <= tp
                if stop_hit:
                    exit_price, reason = max(sl, b.open) * (1 + slippage_rate), "SL"
                elif target_hit:
                    exit_price, reason = tp * (1 + slippage_rate), "TP"
            if exit_price is not None:
                exit_index = j
                break
        if exit_price is None:
            exit_price = bars[end].close * (1 - slippage_rate if direction == Direction.BUY else 1 + slippage_rate)
        change = (exit_price / entry - 1) if direction == Direction.BUY else (1 - exit_price / entry)
        pnl = fixed_notional * (change - 2 * fee_rate)
        balance += pnl
        peak = max(peak, balance)
        max_dd = max(max_dd, (peak - balance) / peak * 100)
        trades.append(Trade(i + 1, exit_index, direction, entry, exit_price, reason, pnl))
        i = exit_index + 1  # never overlap positions
    return BacktestResult(tuple(trades), starting_balance, balance, max_dd)
