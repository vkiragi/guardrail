# Guardrail: Master Build Plan

**Hackathon:** Alpaca AI Trading Agents Hackathon (lablab.ai)
**Build window:** 28 Aug to 4 Sep 2026
**Today:** Sunday 30 August. Five days left including today.
**Team:** Solo
**Primary tool:** Claude Code

---

## 1. What we are building

A policy layer that sits between an LLM trading agent and Alpaca's API.

The agent proposes trades. It cannot execute anything directly. Every proposed order passes through a rules engine that approves or blocks it, and writes the decision plus reasoning to a log. A dashboard shows that log.

Rules live in a YAML file in plain readable form: max position size, no trades in the final ten minutes of the session, halt after a 3% drawdown.

Pitch sentence: **the agent physically cannot reach the broker except through the guardrail.**

## 2. Definition of done

Three deliverables. All three are load-bearing. An incomplete submission scores zero.

1. Working prototype at a public URL
2. Video demo, two to three minutes
3. Pitch deck

## 3. Tech stack

Pin these now and do not revisit. Every hour spent on stack choice is an hour not spent building.

| Layer      | Choice                                          | Why                                                                                                               |
| ---------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Language   | Python 3.11                                     | Alpaca's own tooling is Python. Java would mean writing glue nobody has written.                                  |
| Broker SDK | `alpaca-py`                                     | Official, current, maintained. Not the old `alpaca-trade-api`.                                                    |
| LLM        | Anthropic API, `claude-sonnet-5`                | Tool use gives reliable structured output. Swap to `claude-haiku-4-5-20251001` if latency in the demo annoys you. |
| Web        | FastAPI + uvicorn                               | One file, serves JSON and a static page.                                                                          |
| Frontend   | One HTML file, vanilla JS, plain CSS            | No build step. A build step on Wednesday is how projects die.                                                     |
| Storage    | SQLite via stdlib `sqlite3`                     | No ORM. Four columns of SQL is not worth SQLAlchemy.                                                              |
| Config     | `pyyaml` for rules, `python-dotenv` for secrets |                                                                                                                   |
| Tests      | `pytest`, engine only                           |                                                                                                                   |
| Deploy     | Railway                                         | Cheapest path from repo to public URL with env vars.                                                              |

Full dependency list, and nothing else gets added:

```
alpaca-py
anthropic
fastapi
uvicorn
pyyaml
python-dotenv
pytest
```

If Claude Code suggests adding a package, the default answer is no.

## 4. Scope

### In

Rules engine with four rules from YAML. LLM agent proposing structured orders. Executor hitting Alpaca paper trading. SQLite decision log. Single page dashboard. Public deployment. Video and deck.

### Out, permanently

Backtesting. Live trading. Auth or user accounts. A rules editor UI. Multi-agent debate. Price charts. Websockets. Any attempt to make the strategy profitable. Tests outside the engine. Docker, CI, containers.

### Deferred, only if Wednesday morning is calm

Wrapping the guardrail as a custom MCP server. Extra rules. Dashboard styling.

The MCP wrapper is the most elegant version of this idea and it is still the first thing to cut. A plain Python function call demos identically.

### Cut list, in strict order

When you fall behind, cut from the top. Do not improvise a different order under pressure.

1. MCP server wrapper
2. Dashboard styling, keep the raw table
3. Number of rules, three solid beats six shaky
4. Live LLM calls, hardcode two or three proposals
5. Public deployment, demo from localhost and say so

Never cut: the video, the deck, the decision log.

If you reach item 4 the project still stands. The guardrail is the contribution, not the agent.

---

## 5. Working with Claude Code

This section is the difference between finishing and not. Claude Code is fast enough to build all of this, and also fast enough to build three times more than you asked for, which is the actual risk this week.

### 5.1 Write CLAUDE.md first, before any code

Put this in the repo root. Claude Code reads it automatically every session. It is your scope discipline made permanent, so you do not have to re-argue it every time.

```markdown
# Guardrail

Policy layer between an LLM trading agent and Alpaca's paper trading API.
The agent proposes orders as JSON. The rules engine approves or blocks each one.
Every decision is logged. A dashboard displays the log.

## Hard constraints

- Paper trading only. Never set paper=False. Never suggest live trading.
- Dependencies are fixed: alpaca-py, anthropic, fastapi, uvicorn, pyyaml,
  python-dotenv, pytest. Do not add packages. Ask before suggesting one.
- No new files outside the structure below without asking.
- No backtesting, no charts, no auth, no websockets, no ORM, no Docker.
- The dashboard is a table. It is finished when it is a table.
- Secrets come from .env only. Never write a key into a source file.

## Structure

guardrail/
rules.yaml rule definitions
engine.py evaluate(proposal, account_state) -> Verdict
agent.py Anthropic call, returns a Proposal
executor.py Alpaca order placement
broker.py Alpaca reads: account, positions, clock, last price
log.py SQLite writes and reads
app.py FastAPI
static/index.html
tests/test_engine.py

## Style

- Standard library where possible. Small functions. No abstraction layers
  for a single implementation.
- Type hints on public functions. Docstrings only where behaviour is
  non-obvious.
- When a task is ambiguous, ask one question rather than guessing wide.
```

### 5.2 Session discipline

One phase per session. Run `/clear` between phases. A long session accumulates context from work already finished, and that stale context is where confident wrong edits come from.

Start each phase in **plan mode**. Read the plan it produces before letting it write anything. Ninety percent of scope creep is visible in the plan and costs nothing to delete there.

Make it verify its own work. End every phase prompt with an explicit check: run the tests, run the script, curl the endpoint. Claude Code marking something complete is not evidence it works. The command exiting zero is.

Commit at every phase boundary, with a message you wrote. Solo means no one else has a copy of anything.

### 5.3 What to never let it do

Do not let it refactor working code because it noticed something tidier. Say no. Tuesday you will want to have shipped, not to have a clean architecture.

Do not let it write the LLM parsing "properly" with retries, backoff, and a validation layer before the simple version runs once. Get one call working end to end first.

Do not accept a phase where it wrote code and also wrote the tests that prove the code works, for the rules engine specifically. Write those test cases yourself, or at minimum read every assertion. That file is the one place where a wrong test hides a wrong rule and you demo the bug on camera.

Do not let it touch Phase 4 deployment config while Phase 3 is unfinished.

### 5.4 The context that makes it useful

Claude Code does not know alpaca-py's current surface from memory reliably. Two options, both worth doing:

Install the Alpaca MCP server into Claude Code before you start. It exposes documentation search tools, so the model can look up the real request shapes instead of guessing at them.

```
claude mcp add alpaca -- uvx alpaca-mcp-server
```

Failing that, paste the relevant alpaca-py docs page into the session at the start of Phase 0 and Phase 2. Twenty seconds of pasting prevents an hour of debugging a method signature that does not exist.

Also: after Phase 0 works, keep `scratch.py` in the repo. It is a live, verified example of the SDK's actual API, and pointing Claude Code at it is the cheapest way to keep later code consistent with reality.

---

## 6. Phases

Each phase has an exit test. Do not begin the next phase until the current one passes. This is the entire discipline of the plan.

### Phase 0: Admin and proof of life

**Exit test:** `python scratch.py` places a paper order and cancels it, printing both responses.

Admin first, because people discover the team requirement on the last day:

- Enroll on lablab, create a team of one. Solo still needs a team.
- Alpaca account, generate paper keys, confirm the simulated 100k balance.
- Repo initialised, `.env` written, `.env` in `.gitignore` before the first commit.

Then, by hand rather than through Claude Code, because you want to see the SDK yourself once:

```python
# scratch.py
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
```

Do not spend an hour reading docs first. Run this, then read whatever confused you.

### Phase 1: Rules engine

**Exit test:** `pytest` passes, and a hand-written proposal dict returns the correct verdict with a readable reason.

No LLM anywhere near this phase. Pure logic, no network calls, no Alpaca imports in `engine.py` at all. The engine takes a proposal and an account snapshot as plain data and returns a verdict. That separation is what makes it testable, and it is also the thing judges will notice if they read the code.

Claude Code prompt for this phase:

> Plan mode. Implement engine.py and rules.yaml per CLAUDE.md. `evaluate(proposal: Proposal, state: AccountState) -> Verdict`. Four rules: max_position_pct, daily_drawdown_halt, no_close_window, symbol_allowlist. Rules are data in YAML, not hardcoded logic. engine.py must not import alpaca or make network calls. State is a plain dataclass I pass in. Rules evaluate in order, first block wins, verdict carries the rule id and a human readable reason. Then run pytest and show me the output.

Write or review the test cases yourself. Each rule needs a passing case and a blocking case, plus a boundary case for `max_position_pct` where the order lands exactly on the threshold.

### Phase 2: Agent and execution

**Exit test:** you type an instruction in the terminal, an order is proposed, judged, and either sent to Alpaca or refused. Both outcomes write a row to SQLite.

Three pieces: `broker.py` reads state from Alpaca, `agent.py` calls Anthropic, `executor.py` places approved orders.

Use tool use rather than asking for JSON in prose. Forcing a tool call is the difference between parsing reliably and writing a regex to strip code fences at midnight:

```python
PROPOSE_ORDER = {
    "name": "propose_order",
    "description": "Propose a single order for review by the risk layer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "side": {"type": "string", "enum": ["buy", "sell"]},
            "qty": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["symbol", "side", "qty", "rationale"],
    },
}

resp = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=[PROPOSE_ORDER],
    tool_choice={"type": "tool", "name": "propose_order"},
    messages=[{"role": "user", "content": instruction}],
)
proposal = next(b.input for b in resp.content if b.type == "tool_use")
```

Still wrap it in try/except. If the call fails, log it as a blocked decision with the reason. A crashed loop looks broken on camera. A logged failure looks like a system that handles failure.

### Phase 3: Dashboard

**Exit test:** page loads in a browser, shows real rows, and a new decision appears within a few seconds without a manual refresh.

FastAPI with two routes. `/` serves the static file, `/api/decisions` returns the last fifty rows as JSON. The page polls every three seconds. Green rows approved, red rows blocked, reason text visible without hovering.

Ugly is acceptable. Empty is not.

### Phase 4: Deploy and freeze

**Exit test:** the URL loads on your phone over mobile data with the laptop shut.

Then **feature freeze**. No new functionality after Wednesday lunch, no exceptions.

### Phase 5: Video and deck

**Exit test:** all three submission fields saved on lablab.

---

## 7. Day by day

**Sunday 30 (today).** Phase 0 and CLAUDE.md, then as much of Phase 1 as the evening allows. Do the lablab and Alpaca admin before you write a line of code.

**Monday 31.** Finish Phase 1. Complete Phase 2. End the day with the full loop working from the terminal, print statements and all.

**Tuesday 1.** Phase 3. If Phase 2 is still broken Tuesday morning, cut the LLM and hardcode two proposals. A hardcoded proposal still proves the guardrail works, and the guardrail is the project.

**Wednesday 2.** Deploy in the morning, freeze by lunch, rehearse the demo all afternoon. Write the video script Wednesday, not Thursday.

**Thursday 3.** Video and deck, the whole day. This takes longer than you expect and it is the single most common reason decent projects score badly.

**Friday 4.** Submit in the morning. Not in the final hour.

---

## 8. Technical reference

### 8.1 Alpaca gotchas

These are the ones that cost real time.

**Numeric fields come back as strings.** `account.equity`, `account.last_equity`, `position.market_value` are strings on the response models. Cast to float at the boundary in `broker.py` and let nothing downstream deal with it.

**`last_equity` is your drawdown baseline.** It is equity at the previous day's close, which is exactly what a daily drawdown rule needs. `(equity - last_equity) / last_equity`. Do not build your own baseline tracking.

**Use `get_clock()` for the close window rule.** `clock.next_close` and `clock.timestamp` come from Alpaca in the correct timezone and already account for holidays and half days. Computing 4pm Eastern yourself means handling the early close before a holiday, and that bug will surface in a demo.

**Crypto needs different arguments.** Symbols are `BTC/USD` format, and crypto orders require `TimeInForce.GTC`, not `DAY`. If you support both asset classes, branch on the symbol format in `executor.py`.

**Free market data is IEX, not SIP.** Prices are real but thin. Fine for this, worth knowing before you wonder why a quote looks off.

**You need a price to size a position.** `max_position_pct` compares order notional to equity, so you need the current price. Use the latest trade from `StockHistoricalDataClient`. Cache it for the length of one evaluation. Do not stream.

**Rate limits are per account.** Do not poll Alpaca from the dashboard. The dashboard reads SQLite only. Alpaca is touched once per decision.

### 8.2 Proposal, state, verdict

```python
@dataclass
class Proposal:
    symbol: str
    side: str          # "buy" | "sell"
    qty: float
    rationale: str

@dataclass
class AccountState:
    equity: float
    last_equity: float
    buying_power: float
    positions: dict[str, float]   # symbol -> market value
    last_price: float             # for the proposed symbol
    seconds_to_close: float | None  # None when market is closed

@dataclass
class Verdict:
    allowed: bool
    reason: str
    rule_id: str | None
```

### 8.3 rules.yaml

```yaml
rules:
  - id: daily_drawdown_halt
    max_drawdown_pct: 3.0
    reason: "Account down {drawdown:.1f}% today, above the 3% halt threshold."

  - id: symbol_allowlist
    allowed: [AAPL, MSFT, SPY, NVDA, TSLA, BTC/USD, ETH/USD]
    reason: "{symbol} is not on the approved list."

  - id: no_close_window
    minutes_before_close: 10
    reason: "Market closes in under 10 minutes."

  - id: max_position_pct
    max_pct: 20.0
    reason: "Order would take {symbol} to {resulting_pct:.1f}% of portfolio, above the 20% cap."
```

Reasons live in the config, not the code. It means the demo moment reads well and it means you can tune the wording Wednesday without touching Python.

Consider a fifth rule if Tuesday is comfortable: `max_orders_per_hour`, which catches the failure where the agent is not wrong, just stuck in a loop. It is worth a sentence in the pitch because it is a failure mode people do not think of.

### 8.4 Decision log

```sql
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  symbol TEXT,
  side TEXT,
  qty REAL,
  rationale TEXT,
  allowed INTEGER NOT NULL,
  reason TEXT,
  rule_id TEXT,
  order_id TEXT
);
```

Write the row before attempting execution, update with the order id after. If Alpaca errors, the decision is still on the record.

### 8.5 Deployment

Railway containers have an ephemeral filesystem. The SQLite file disappears on every redeploy. Two ways to handle it, and the second is the one to use:

Mount a Railway volume and put the database on it, or write an idempotent `seed_if_empty()` that runs at startup and inserts fifteen to twenty realistic decisions when the table has no rows.

Take the seed. It costs ten minutes and it solves a second problem at the same time: a judge who opens your link and sees an empty table has formed an opinion within two seconds, and it is the wrong one.

Environment variables go in Railway's dashboard. `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ANTHROPIC_API_KEY`. Commit a `.env.example` with empty values so the repo documents what it needs.

Deploy a hello world version Monday night. Shaking out platform problems on Monday costs an hour. Discovering them Wednesday costs the project.

---

## 9. Demo video

Two to three minutes, screen recording with voiceover, no slides.

1. **0:00.** The problem. People are pointing LLMs at brokerage APIs and nothing stops a hallucinated order.
2. **0:10.** Architecture. One diagram: agent, guardrail, Alpaca, log underneath.
3. **0:30.** Happy path. Reasonable instruction, proposal appears, approved, order lands in Alpaca, green row in the log.
4. **1:10.** The moment. Instruct it to put 80% of the account into one position. Watch the block. Read the reason out loud. Red row.
5. **2:00.** Show `rules.yaml`. Point out that someone who does not code can read the constraints.
6. **2:20.** Close. Paper trading, and the pattern generalises to any agent with write access to something that matters.

Record in one take if you can. Wednesday's rehearsal is what makes that possible.

Use crypto symbols for the recording. The market closes Friday afternoon and you will be recording at odd hours, and crypto trades continuously on Alpaca.

## 10. Deck

Six slides. Title. Problem. Architecture diagram. Screenshot of rules.yaml. Screenshot of the dashboard with green and red rows. Stack plus links.

## 11. Risks

| Risk                               | Mitigation                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| Claude Code builds more than asked | CLAUDE.md, plan mode, `/clear` between phases                                 |
| Malformed LLM output               | Forced tool use, and failures logged as blocked decisions rather than crashes |
| Deployment fights you Wednesday    | Hello world deploy Monday night                                               |
| SQLite wiped on redeploy           | `seed_if_empty()` at startup                                                  |
| Thursday runs out of hours         | Script written Wednesday afternoon                                            |
| Market closed during recording     | Crypto symbols, and the block path needs no open market anyway                |
| Dashboard scope creep              | It is a table. It is done when it is a table.                                 |

## 12. Friday checklist

- [ ] lablab team exists, solo counts
- [ ] Public URL tested from a device that is not your laptop
- [ ] Repo public, README explains the design decisions
- [ ] `git log -p | grep -i "api_key"` returns nothing
- [ ] Video plays in an incognito window
- [ ] Deck uploaded
- [ ] Description filled
- [ ] Submitted before Friday afternoon
