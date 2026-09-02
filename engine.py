"""Pre-trade rules engine.

Pure logic: no alpaca imports, no network calls. It takes plain data
(a Proposal and an AccountState) and returns a Verdict. Rules and their
reason strings are data in rules.yaml; each rule id maps to one check below.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_RULES_PATH = Path(__file__).parent / "rules.yaml"


@dataclass
class Proposal:
    symbol: str  # stock ticker, or an OCC option contract symbol
    side: str  # "buy" | "sell"
    qty: float  # shares, or contracts for an option
    rationale: str
    underlying: str = ""  # "AAPL" for an option; the allowlist checks this
    multiplier: int = 1  # 100 for an option contract
    days_to_expiry: int | None = None  # None for a stock


@dataclass
class AccountState:
    equity: float
    last_equity: float
    buying_power: float
    positions: dict[str, float]  # symbol -> market value
    last_price: float  # for the proposed symbol
    seconds_to_close: float | None  # None when market is closed


@dataclass
class Verdict:
    allowed: bool
    reason: str
    rule_id: str | None


def load_rules(path: Path = _RULES_PATH) -> list[dict]:
    with open(path) as f:
        return yaml.safe_load(f)["rules"]


def _check_daily_drawdown_halt(p, s, rule):
    drawdown = (s.last_equity - s.equity) / s.last_equity * 100
    if drawdown >= rule["max_drawdown_pct"]:
        return rule["reason"].format(drawdown=drawdown)
    return None


def _check_symbol_allowlist(p, s, rule):
    name = p.underlying or p.symbol
    if name not in rule["allowed"]:
        return rule["reason"].format(symbol=name)
    return None


def _check_min_days_to_expiry(p, s, rule):
    if p.days_to_expiry is not None and p.days_to_expiry < rule["min_days"]:
        return rule["reason"].format(days=p.days_to_expiry, min_days=rule["min_days"])
    return None


def _check_max_contracts_per_order(p, s, rule):
    if p.multiplier > 1 and p.qty > rule["max_contracts"]:
        return rule["reason"].format(qty=p.qty, max_contracts=rule["max_contracts"])
    return None


def _check_no_close_window(p, s, rule):
    if s.seconds_to_close is not None and s.seconds_to_close < rule["minutes_before_close"] * 60:
        return rule["reason"]
    return None


def _check_max_position_pct(p, s, rule):
    if p.side != "buy":
        return None
    current = s.positions.get(p.symbol, 0.0)
    resulting_pct = (current + p.qty * s.last_price * p.multiplier) / s.equity * 100
    if resulting_pct > rule["max_pct"]:
        name = p.underlying or p.symbol
        return rule["reason"].format(symbol=name, resulting_pct=resulting_pct)
    return None


_CHECKS = {
    "daily_drawdown_halt": _check_daily_drawdown_halt,
    "symbol_allowlist": _check_symbol_allowlist,
    "min_days_to_expiry": _check_min_days_to_expiry,
    "max_contracts_per_order": _check_max_contracts_per_order,
    "no_close_window": _check_no_close_window,
    "max_position_pct": _check_max_position_pct,
}


def evaluate(
    proposal: Proposal, state: AccountState, rules: list[dict] | None = None
) -> Verdict:
    """Run rules in order; first block wins. Otherwise the order is allowed."""
    if rules is None:
        rules = load_rules()
    for rule in rules:
        reason = _CHECKS[rule["id"]](proposal, state, rule)
        if reason is not None:
            return Verdict(allowed=False, reason=reason, rule_id=rule["id"])
    return Verdict(allowed=True, reason="Order approved.", rule_id=None)
