"""Order placement through the Alpaca CLI.

Only proposals the guardrail approved reach here. The CLI defaults to paper and
ALPACA_LIVE_TRADE is never set, so an order cannot reach a live account.
Stocks and option contracts submit identically: the OCC contract symbol simply
goes in as the symbol.
"""
from broker import cli
from engine import Proposal


def place(proposal: Proposal, dry_run: bool = False) -> str:
    """Submit a day market order for an approved proposal, return the order id."""
    qty = proposal.qty
    args = [
        "order", "submit",
        "--symbol", proposal.symbol,
        "--qty", str(int(qty) if float(qty).is_integer() else qty),
        "--side", proposal.side,
        "--type", "market",
        "--time-in-force", "day",
    ]
    if dry_run:
        args.append("--dry-run")
    out = cli(*args)
    return str(out.get("id", "dry-run"))
