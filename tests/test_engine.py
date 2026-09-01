"""Rules engine tests. Each rule has a pass and a block case, plus boundary
cases, ordering (first block wins), and buy/sell asymmetry.

Base state: $100k equity, no drawdown, empty positions, $100 last price,
market open with 1 hour to close. Each test overrides only what it tests.
"""
from engine import AccountState, Proposal, evaluate


def base_state(**kw) -> AccountState:
    defaults = dict(
        equity=100_000.0,
        last_equity=100_000.0,
        buying_power=100_000.0,
        positions={},
        last_price=100.0,
        seconds_to_close=3600.0,
    )
    defaults.update(kw)
    return AccountState(**defaults)


def buy(symbol="AAPL", qty=10.0) -> Proposal:
    return Proposal(symbol=symbol, side="buy", qty=qty, rationale="test")


def sell(symbol="AAPL", qty=10.0) -> Proposal:
    return Proposal(symbol=symbol, side="sell", qty=qty, rationale="test")


# --- happy path ---------------------------------------------------------

def test_clean_buy_is_allowed():
    v = evaluate(buy("AAPL", 10), base_state())  # 10 * $100 = $1k = 1%
    assert v.allowed is True
    assert v.rule_id is None


# --- daily_drawdown_halt ------------------------------------------------

def test_drawdown_blocks_at_4pct():
    v = evaluate(buy(), base_state(equity=96_000.0))  # down 4%
    assert v.allowed is False
    assert v.rule_id == "daily_drawdown_halt"


def test_drawdown_blocks_exactly_at_3pct():
    v = evaluate(buy(), base_state(equity=97_000.0))  # down exactly 3.0%
    assert v.allowed is False
    assert v.rule_id == "daily_drawdown_halt"


def test_drawdown_passes_at_2pct():
    v = evaluate(buy(), base_state(equity=98_000.0))  # down 2%, under threshold
    assert v.allowed is True


def test_drawdown_halt_also_blocks_a_sell():
    v = evaluate(sell("AAPL", 10), base_state(equity=96_000.0))
    assert v.allowed is False
    assert v.rule_id == "daily_drawdown_halt"


# --- symbol_allowlist ---------------------------------------------------

def test_off_allowlist_symbol_is_blocked():
    v = evaluate(buy("GME", 10), base_state())
    assert v.allowed is False
    assert v.rule_id == "symbol_allowlist"


def test_on_allowlist_symbol_passes():
    v = evaluate(buy("MSFT", 10), base_state())
    assert v.allowed is True


# --- no_close_window ----------------------------------------------------

def test_blocks_inside_close_window():
    v = evaluate(buy(), base_state(seconds_to_close=300.0))  # 5 min to close
    assert v.allowed is False
    assert v.rule_id == "no_close_window"


def test_passes_when_market_closed():
    v = evaluate(buy(), base_state(seconds_to_close=None))  # closed -> not in window
    assert v.allowed is True


# --- max_position_pct ---------------------------------------------------

def test_max_position_blocks_at_25pct():
    v = evaluate(buy("AAPL", 250), base_state())  # 250 * $100 = $25k = 25%
    assert v.allowed is False
    assert v.rule_id == "max_position_pct"


def test_max_position_boundary_exactly_20pct_is_allowed():
    v = evaluate(buy("AAPL", 200), base_state())  # $20k = exactly 20%, cap is strict
    assert v.allowed is True
    assert v.rule_id is None


def test_max_position_counts_existing_holding():
    # already hold $15k of AAPL; buying $10k more -> $25k = 25%
    v = evaluate(buy("AAPL", 100), base_state(positions={"AAPL": 15_000.0}))
    assert v.allowed is False
    assert v.rule_id == "max_position_pct"


def test_sell_skips_max_position():
    # holding 50% of the book in AAPL, a sell is not capped
    v = evaluate(sell("AAPL", 100), base_state(positions={"AAPL": 50_000.0}))
    assert v.allowed is True


# --- ordering: first block wins -----------------------------------------

def test_first_block_wins_drawdown_before_allowlist():
    # both drawdown and allowlist are violated; drawdown is listed first
    v = evaluate(buy("GME", 10), base_state(equity=96_000.0))
    assert v.allowed is False
    assert v.rule_id == "daily_drawdown_halt"
