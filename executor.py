"""Alpaca order placement. paper=True is hardcoded and stays that way.

Only approved proposals reach here. Stocks are placed as DAY market orders.
"""
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from engine import Proposal


def place(proposal: Proposal) -> str:
    """Submit a market order for an approved proposal, return the order id."""
    client = TradingClient(
        os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True
    )
    order = client.submit_order(
        MarketOrderRequest(
            symbol=proposal.symbol,
            qty=proposal.qty,
            side=OrderSide.BUY if proposal.side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
    )
    return str(order.id)
