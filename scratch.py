import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

load_dotenv()
client = TradingClient(
    os.environ["ALPACA_API_KEY"],
    os.environ["ALPACA_SECRET_KEY"],
    paper=True,
)

acct = client.get_account()
print("equity", acct.equity, "last_equity", acct.last_equity)
print("clock", client.get_clock())

order = client.submit_order(MarketOrderRequest(
    symbol="SPY", qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
))
print(order)
client.cancel_order_by_id(order.id)
print("cancelled", order.id)
