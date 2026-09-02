"""Order placement through the Alpaca CLI.

Only proposals the guardrail approved reach here. The CLI defaults to paper and
ALPACA_LIVE_TRADE is never set, so an order cannot reach a live account.

Options are sent as limit orders, never market orders: an options book can be
thin, and a market order into it can fill far from the quote. A limit also lets
an order rest outside market hours, where an options market order is rejected.
"""
from broker import cli
from engine import Proposal


def place(proposal: Proposal, limit_price: float | None = None,
          dry_run: bool = False) -> str:
    """Submit a day order for an approved proposal, return the order id."""
    qty = proposal.qty
    args = [
        "order", "submit",
        "--symbol", proposal.symbol,
        "--qty", str(int(qty) if float(qty).is_integer() else qty),
        "--side", proposal.side,
        "--time-in-force", "day",
    ]
    if limit_price is not None:
        args += ["--type", "limit", "--limit-price", f"{limit_price:.2f}"]
    else:
        args += ["--type", "market"]
    if dry_run:
        args.append("--dry-run")
    return str(cli(*args).get("id", "dry-run"))
