"""Alpaca reads through the Alpaca CLI.

Every Alpaca call on the live path goes through the `alpaca` command line tool.
Secrets arrive via python-dotenv in os.environ; the CLI defaults to paper and
ALPACA_LIVE_TRADE is never set. Numeric fields come back as strings and are cast
to float here at the boundary. engine.py never imports this module.
"""
import json
import os
import re
import subprocess
from datetime import date, datetime, timedelta

from engine import AccountState

_OCC = re.compile(r"^(?P<root>[A-Z]+)(?P<ymd>\d{6})(?P<kind>[CP])(?P<strike>\d{8})$")


def cli(*args: str):
    """Run an alpaca CLI command and return its parsed JSON."""
    r = subprocess.run(
        ["alpaca", *args], env=os.environ.copy(), capture_output=True, text=True
    )
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"alpaca {' '.join(args)}: {(r.stderr or r.stdout)[:200]}")
    if isinstance(out, dict) and out.get("error"):
        raise RuntimeError(f"alpaca {' '.join(args)}: {out['error']}")
    return out


def _ts(value: str) -> datetime:
    """Alpaca sends nanoseconds; datetime handles at most microseconds."""
    return datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", value))


def parse_occ(symbol: str) -> dict:
    """Pull the underlying, expiry, type and strike out of an OCC symbol."""
    m = _OCC.match(symbol)
    if not m:
        raise ValueError(f"not an OCC option symbol: {symbol}")
    return {
        "underlying": m["root"],
        "expiry": datetime.strptime(m["ymd"], "%y%m%d").date(),
        "kind": "call" if m["kind"] == "C" else "put",
        "strike": int(m["strike"]) / 1000,
    }


def spot_price(symbol: str) -> float:
    return float(cli("data", "latest-trade", "--symbol", symbol)["trade"]["p"])


def positions() -> dict[str, float]:
    rows = cli("position", "list") or []
    return {r["symbol"]: float(r["market_value"]) for r in rows}


def seconds_to_close() -> float | None:
    """None when the market is closed."""
    c = cli("clock")
    if not c["is_open"]:
        return None
    return (_ts(c["next_close"]) - _ts(c["timestamp"])).total_seconds()


def get_state(symbol: str, last_price: float | None = None) -> AccountState:
    """Account snapshot for the engine. Pass last_price for an option contract."""
    a = cli("account", "get")
    return AccountState(
        equity=float(a["equity"]),
        last_equity=float(a["last_equity"]),
        buying_power=float(a["buying_power"]),
        positions=positions(),
        last_price=spot_price(symbol) if last_price is None else last_price,
        seconds_to_close=seconds_to_close(),
    )


def recent_bars(symbol: str, days: int = 10) -> list[dict]:
    start = (date.today() - timedelta(days=days * 2 + 5)).isoformat()
    out = cli("data", "bars", "--symbol", symbol, "--timeframe", "1Day", "--start", start)
    return (out.get("bars") or [])[-days:]


def recent_news(symbol: str, limit: int = 5) -> list[str]:
    out = cli("data", "news", "--symbols", symbol, "--limit", str(limit))
    return [n["headline"] for n in (out.get("news") or []) if n.get("headline")]


def pick_contract(
    underlying: str, direction: str, min_days: int = 7, max_days: int = 45
) -> dict:
    """Nearest expiry at least min_days out, strike closest to spot.

    Deterministic on purpose: the LLM chooses a direction, never the contract.
    """
    spot = spot_price(underlying)
    kind = "call" if direction == "bullish" else "put"
    today = date.today()
    chain = cli(
        "data", "option", "chain",
        "--underlying-symbol", underlying,
        "--type", kind,
        "--expiration-date-gte", str(today + timedelta(days=min_days)),
        "--expiration-date-lte", str(today + timedelta(days=max_days)),
        "--strike-price-gte", f"{spot * 0.90:.2f}",
        "--strike-price-lte", f"{spot * 1.10:.2f}",
        "--limit", "500",
    )

    candidates = []
    for sym, snap in (chain.get("snapshots") or {}).items():
        quote = snap.get("latestQuote") or {}
        ask = float(quote.get("ap") or 0)
        bid = float(quote.get("bp") or 0)
        price = ask if ask > 0 else (bid + ask) / 2
        if price <= 0:
            continue
        info = parse_occ(sym)
        candidates.append(
            {
                "symbol": sym,
                "underlying": underlying,
                "kind": info["kind"],
                "strike": info["strike"],
                "expiry": info["expiry"],
                "days_to_expiry": (info["expiry"] - today).days,
                "price": price,
                "spot": spot,
            }
        )

    if not candidates:
        raise RuntimeError(f"no priced {kind} contracts for {underlying}")

    nearest = min(c["expiry"] for c in candidates)
    return min(
        (c for c in candidates if c["expiry"] == nearest),
        key=lambda c: abs(c["strike"] - c["spot"]),
    )
