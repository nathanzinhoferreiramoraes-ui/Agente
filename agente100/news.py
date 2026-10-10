"""Read-only RSS headlines with conservative, transparent sentiment scoring.

Headlines are untrusted input. No LLM commands, no trading endpoints.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
import re

FEED_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
POSITIVE = frozenset(("surge", "rally", "gain", "growth", "approval", "record", "adoption", "rise", "bullish"))
NEGATIVE = frozenset(("crash", "plunge", "drop", "hack", "fraud", "lawsuit", "ban", "decline", "bearish"))
ASSET_TERMS = {
    "BTC-USD": frozenset(("bitcoin", "btc")),
    "ETH-USD": frozenset(("ethereum", "ether", "eth")),
    "SOL-USD": frozenset(("solana", "sol")),
}


@dataclass(frozen=True)
class Headline:
    title: str
    published: datetime


def parse_rss(data: bytes, *, now: datetime | None = None, max_age_hours: int = 24) -> list[Headline]:
    """Only recent, timestamped headlines count; reject malformed XML."""
    if len(data) > 2_000_000:
        raise ValueError("Feed too large")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or max_age_hours <= 0:
        raise ValueError("Invalid time configuration")
    root = ET.fromstring(data)
    headlines = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        pubdate = (item.findtext("pubDate") or "").strip()
        if not title or not pubdate:
            continue
        try:
            published = parsedate_to_datetime(pubdate)
            if published.tzinfo is None:
                continue
            age = (now - published).total_seconds()
            if 0 <= age <= max_age_hours * 3600:
                headlines.append(Headline(title[:300], published))
        except (TypeError, ValueError, IndexError):
            continue
    return headlines


def fetch_headlines(*, timeout: int = 10) -> list[Headline]:
    if not 1 <= timeout <= 30:
        raise ValueError("Invalid timeout")
    req = Request(FEED_URL, headers={"User-Agent": "Agente100-PaperResearch/0.1",
                                     "Accept": "application/rss+xml, application/xml"})
    with urlopen(req, timeout=timeout) as response:
        data = response.read(2_000_001)
    return parse_rss(data)


def score_asset(headlines: list[Headline], product: str) -> float:
    """Lexicon baseline, not an ML model. Missing/ambiguous data returns zero."""
    if product not in ASSET_TERMS:
        raise ValueError("Unknown asset")
    scores = []
    for item in headlines:
        tokens = set(re.findall(r"[a-z]+", item.title.lower()))
        if not tokens.intersection(ASSET_TERMS[product]):
            continue
        positives = len(tokens.intersection(POSITIVE))
        negatives = len(tokens.intersection(NEGATIVE))
        if positives + negatives:
            scores.append((positives - negatives) / (positives + negatives))
    return sum(scores) / len(scores) if scores else 0.0
