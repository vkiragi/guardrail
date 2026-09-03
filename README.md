# Guardrail

**An autonomous options trading agent that physically cannot reach the broker except through a risk layer.**

Live dashboard: https://guardrail-hackathon.netlify.app

---

## The problem

People are pointing LLMs at brokerage APIs. An LLM can hallucinate, misread a headline, or
loop on a bad idea, and nothing between it and the broker says no. The usual answer is to
prompt the model to be careful. Prompts are not a control.

Guardrail makes the control structural. The model is never given the ability to place an
order. It produces an *opinion*; a deterministic layer decides whether that opinion becomes
a trade, and writes down what it decided and why.

## Architecture

```
   schedule / instruction
            |
            v
   agent.py  ──►  OpenAI gpt-5.6-luna      returns a VIEW only:
            |                              bullish | bearish | skip
            v
   broker.py ──►  Alpaca CLI               picks the contract deterministically
            |                              (ATM, >= 7 days out) and prices it
            v
   engine.py  +  rules.yaml                no network, no alpaca import
            |                              approve or block, with a reason
      ┌─────┴─────┐
      v           v
  executor.py   log.py                     CLI limit order  |  SQLite, every decision
      |           |
      v           v
   Alpaca      dashboard
```

`engine.py` imports nothing from Alpaca and makes no network calls. It takes plain data and
returns a verdict. That separation is the whole project: the risk layer is testable in
isolation and cannot be talked out of a decision by the model.

## AI logic

The model's job is deliberately narrow. For each symbol it receives ten daily closes and
recent headlines, both pulled through the Alpaca CLI, and returns one of `bullish`,
`bearish` or `skip` plus a one-sentence rationale. That is all.

It does **not** choose the contract, the strike, the expiry, the order type, or the size.
Those are deterministic: nearest expiry at least 7 days out, strike closest to spot, one
contract, priced off the ask. A hallucinated number cannot become a position, because the
model is never asked for a number.

`skip` is a first-class answer and the common one — on a typical pass the agent passes on
eight of ten symbols and says why. The rationales are logged alongside the trades.

## Risk gates

Six rules, defined as data in `rules.yaml`, evaluated in order; the first block wins. The
reason strings live in the config, not in Python, so a non-programmer can read the
constraints and change the wording.

| Rule | Blocks when |
|---|---|
| `daily_drawdown_halt` | account is down 3% or more today |
| `symbol_allowlist` | the **underlying** is not on the approved list |
| `min_days_to_expiry` | the contract expires within 7 days |
| `max_contracts_per_order` | more than 5 contracts in one order |
| `no_close_window` | the market closes within 10 minutes |
| `max_position_pct` | the position would exceed 20% of the portfolio |

Position sizing understands options: notional is `contracts × price × 100`, and it is
computed against the **limit** price, so the guardrail judges the worst case cost rather
than the current quote.

Every decision is written to SQLite *before* execution and updated with the order id after,
so a broker failure still leaves the decision on the record. A failed model or CLI call is
logged as a blocked decision rather than raised — a crash looks broken, a logged refusal
looks like a system handling failure.

## Alpaca infrastructure

Every Alpaca interaction on the live path goes through the **Alpaca CLI**:

- `account get`, `position list`, `clock` — the state the rules are evaluated against
- `data bars`, `data news` — the market context the model reasons over
- `data option chain` — contract discovery, quotes and greeks in one call
- `order submit` — execution

Orders are **limit, never market**. An options book can be thin and a market order into it
can fill far from the quote; a limit caps what is paid. It also lets an order rest outside
market hours, where an options market order is rejected outright — so the agent can queue
its decisions overnight and have them worked at the open.

Paper trading throughout. The CLI defaults to paper and `ALPACA_LIVE_TRADE` is never set.

## Running it

```bash
python main.py --auto                  # one autonomous pass over the watchlist
python main.py --auto --loop 1800      # repeat every 30 minutes
python main.py "buy 10 shares of apple"  # manual path, same guardrail
uvicorn app:app --port 8000            # dashboard
pytest                                 # 22 tests, engine only
```

Secrets come from `.env` (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `OPENAI_API_KEY`).

## Honest notes

The agent is selective by design and often trades nothing on a given pass. Over a two day
competition window that means a small number of positions and a correspondingly small P&L —
long single-leg options pay theta and the spread. The contribution here is the control
layer, not the alpha. The same guardrail sits unchanged in front of a far more aggressive
strategy; that is the point of separating them.
