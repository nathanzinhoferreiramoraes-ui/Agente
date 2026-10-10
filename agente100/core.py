"""Paper-only signal selection and execution. No broker integrations."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Candidate:
    symbol: str
    price: float
    direction: Direction
    rsi: float
    bollinger_breakout: bool
    news_score: float = 0.0  # externally supplied sentiment [-1, 1]
    volatility: float = 0.0


@dataclass(frozen=True)
class Signal:
    id: str
    symbol: str
    direction: Direction
    entry: float
    take_profit: float
    stop_loss: float
    created_at: datetime


class Agente100:
    """Ranks candidates; NEVER sets trade size."""

    def choose(self, candidates: list[Candidate]) -> Signal | None:
        valid = [c for c in candidates if c.price > 0 and 0 <= c.rsi <= 100
                 and -1 <= c.news_score <= 1 and c.volatility >= 0]
        if not valid:
            return None

        def score(c: Candidate) -> float:
            momentum = (c.rsi - 50) / 50
            alignment = momentum if c.direction == Direction.BUY else -momentum
            news = c.news_score if c.direction == Direction.BUY else -c.news_score
            return (2 if c.bollinger_breakout else 0) + alignment + news - min(c.volatility, 1)

        best = max(valid, key=score)
        # Fixed illustrative exits for V1; replace with tested risk model later.
        if best.direction == Direction.BUY:
            tp, sl = best.price * 1.005, best.price * 0.99
        else:
            tp, sl = best.price * 0.995, best.price * 1.01
        return Signal(str(uuid4()), best.symbol, best.direction, best.price,
                      tp, sl, datetime.now(timezone.utc))


class Robo100:
    """A paper-only order ledger. Size is configured here, never in Signal."""

    def __init__(self, fixed_notional: float = 10.0, balance: float = 100.0,
                 max_signal_age_seconds: int = 300):
        if fixed_notional <= 0 or balance <= 0 or max_signal_age_seconds <= 0:
            raise ValueError("Configuration must be positive")
        self.fixed_notional = fixed_notional
        self.balance = balance
        self.max_signal_age_seconds = max_signal_age_seconds
        self.executed_ids: set[str] = set()
        self.paper_orders: list[dict] = []

    def execute(self, signal: Signal, approved_signal_id: str | None = None) -> dict:
        if approved_signal_id != signal.id:
            raise PermissionError("Explicit approval for this signal ID is required")
        if signal.id in self.executed_ids:
            raise ValueError("Duplicate signal")
        now = datetime.now(timezone.utc)
        if signal.created_at.tzinfo is None or signal.created_at > now + timedelta(seconds=5):
            raise ValueError("Invalid timestamp")
        if (now - signal.created_at).total_seconds() > self.max_signal_age_seconds:
            raise ValueError("Expired signal")
        if signal.entry <= 0 or signal.take_profit <= 0 or signal.stop_loss <= 0:
            raise ValueError("Invalid prices")
        if signal.direction == Direction.BUY:
            valid = signal.stop_loss < signal.entry < signal.take_profit
        elif signal.direction == Direction.SELL:
            valid = signal.take_profit < signal.entry < signal.stop_loss
        else:
            valid = False
        if not valid:
            raise ValueError("Invalid stop loss / take profit")
        if self.fixed_notional > self.balance:
            raise ValueError("Insufficient paper balance")
        order = {"mode": "PAPER", "signal_id": signal.id, "symbol": signal.symbol,
                 "direction": signal.direction.value, "entry": signal.entry,
                 "take_profit": signal.take_profit, "stop_loss": signal.stop_loss,
                 "notional": self.fixed_notional, "status": "SIMULATED_OPEN"}
        self.executed_ids.add(signal.id)
        self.paper_orders.append(order)
        return order
