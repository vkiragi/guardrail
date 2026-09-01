"""Alpaca reads: account, positions, clock, last price.

String numeric fields from Alpaca are cast to float here at the boundary so
nothing downstream deals with strings. engine.py never imports this module.
"""
import os

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient

from engine import AccountState


def _trading() -> TradingClient:
    return TradingClient(
        os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True
    )


def _data() -> StockHistoricalDataClient:
    return StockHistoricalDataClient(
        os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"]
    )


def last_price(symbol: str) -> float:
    req = StockLatestTradeRequest(symbol_or_symbols=symbol)
    trade = _data().get_stock_latest_trade(req)[symbol]
    return float(trade.price)


def get_state(symbol: str) -> AccountState:
    """Build the AccountState the engine needs for the proposed symbol."""
    client = _trading()
    acct = client.get_account()
    positions = {p.symbol: float(p.market_value) for p in client.get_all_positions()}
    clock = client.get_clock()
    seconds_to_close = (
        (clock.next_close - clock.timestamp).total_seconds() if clock.is_open else None
    )
    return AccountState(
        equity=float(acct.equity),
        last_equity=float(acct.last_equity),
        buying_power=float(acct.buying_power),
        positions=positions,
        last_price=last_price(symbol),
        seconds_to_close=seconds_to_close,
    )
