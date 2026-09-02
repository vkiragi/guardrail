# Guardrail

Pre-trade risk layer for autonomous trading agents.

An LLM proposes orders. It cannot reach Alpaca directly. Every proposal is checked
against limits defined in `rules.yaml`, approved or blocked, and logged with the
agent's stated rationale. A dashboard displays the log.

This is a five day hackathon build with a hard deadline of Friday 4 September.
Shipping beats elegance. Read `MASTERPLAN.md` in this repo for full context.

---

## Hard rules

These are not preferences. Do not violate them, and do not propose violating them.

1. **Paper trading only.** `TradingClient(..., paper=True)` is hardcoded. Never
   parameterize it, never read it from config, never set it False.
2. **Dependencies are frozen.** alpaca-py, openai, fastapi, uvicorn, pyyaml,
   python-dotenv, pytest, plus the Alpaca CLI (`brew install alpacahq/tap/cli`,
   a system tool, not a pip package). Nothing else. If you believe a package is
   needed, stop and ask. Do not install it and mention it afterward.
3. **Secrets come from `.env` via python-dotenv.** Never write a key, token, or
   account id into a source file, a test, a comment, or an example.
4. **No new files** outside the structure below without asking first.
5. **`engine.py` must not import alpaca and must not make network calls.** It
   takes plain data and returns a verdict. This separation is the point of the
   project.
6. **One phase at a time.** Do not start work belonging to a later phase, even
   if it is a small change and obviously needed later.
7. **Never push to GitHub without my explicit consent.** Not `git push`, not
   `--force`, not creating a remote, not opening a PR, not `gh repo create`.
   Local commits are fine when I ask for them. Anything that leaves my machine
   needs me to say yes first, every time. Do not treat earlier permission as
   standing permission.
8. **Never set `ALPACA_LIVE_TRADE`.** The Alpaca CLI defaults to paper trading.
   Setting `ALPACA_LIVE_TRADE=true` routes orders to live. Never set it, never
   suggest it. This is hard rule 1 restated for the CLI.
9. **Never source `.env` in the shell.** No `. ./.env`, no `set -a; . ./.env`.
   Load secrets with python-dotenv and pass the environment to the subprocess.
   Shell sourcing has already leaked a secret key into terminal output once.
10. **No test orders on the hackathon account.** Every order that lands there is
    part of the judged P&L record. Use `--dry-run`, or exercise paths the
    guardrail blocks. Never place throwaway orders on the submission account.

## Hackathon requirements

From the lablab.ai event page. Missing any of these risks disqualification, so
they outrank taste, elegance, and any earlier scope decision in this file.

**Submission deadline: Friday 4 September 2026, 8:00 AM PDT.**

Core requirements:

- Autonomous AI trading agent built on Alpaca's Trading API.
- Must use Alpaca's MCP server or its CLI. We use the CLI.
- Every strategy must incorporate options trading. Stocks alone do not qualify.
- Must run on a brand new paper account dedicated to this hackathon, starting
  balance $100,000. A reused account is not eligible for judging.

Judged on, in this order: P&L performance, technology implementation (Alpaca
API, MCP, CLI), creativity and originality, presentation, social engagement.

Submission bundle: title, short and long description, tags, cover image, video,
slide deck, public GitHub repo, demo URL, the Alpaca paper account ID, and a one
page write-up covering AI logic, risk gates, and Alpaca infrastructure.

## Forbidden scope

Do not build these. Do not suggest them. If asked to, remind me they are out.

Backtesting. Live trading. Auth, users, sessions. A UI for editing rules.
Multi-agent debate or personalities. Price charts or candlesticks. Websockets or
streaming. Strategy optimisation. Docker, CI, containers. An ORM. Tests outside
`tests/test_engine.py`. Async anything. A frontend build step.

## Structure

```
guardrail/
  rules.yaml        rule definitions, data not logic
  engine.py         evaluate(proposal, state) -> Verdict
  agent.py          OpenAI call (gpt-5.6-luna), forced function call, returns a Proposal
  broker.py         Alpaca reads: account, positions, clock, last price
  executor.py       Alpaca order placement
  log.py            SQLite writes and reads
  main.py           terminal driver, wires the loop; app.py reuses run()
  app.py            FastAPI, two routes
  static/index.html one page, vanilla JS, no framework
  tests/test_engine.py
  scratch.py        verified working SDK example, keep it, do not delete
  .env.example
```

## Phase gates

Current phase is tracked in `MASTERPLAN.md` section 6. Each phase has an exit
test. Do not begin the next phase until I confirm the current one passes.

- Phase 0: `scratch.py` places and cancels a paper order
- Phase 1: `pytest` green, engine returns correct verdicts on hand-written input
- Phase 2: terminal instruction produces a judged, logged, executed-or-refused order
- Phase 3: dashboard shows real rows and updates without manual refresh
- Phase 4: public URL loads from a phone. Then feature freeze.
- Phase 5: video and deck

## How to work with me

**Plan before writing.** For any task beyond a one line fix, show me the plan and
wait. I will delete things from it.

**Ask rather than assume.** When a task is ambiguous, ask one specific question.
Do not resolve ambiguity by building both options or by building the larger one.

**Verify, do not assert.** Never tell me something works. Run the test, the
script, or the curl, and show me the output. "Should work" is not acceptable.

**Smallest thing that passes the exit test.** No error handling for cases that
cannot happen yet. No abstraction for a single implementation. No config for
values that will never change this week.

**Do not refactor working code** because you noticed something tidier. If you
think a refactor is needed, say so in one sentence and let me decide.

**Do not fix unrelated things** you noticed while working. Mention them, move on.

**Stop when the task is done.** Do not continue into adjacent improvements.

## How to talk to me

Short answers. Plain words. Assume I would rather read three sentences than
three paragraphs.

- Lead with the answer, then the reason if I need one.
- Explain in simple terms. Skip jargon, or define it in half a sentence.
- No preamble, no summarising what I just asked, no recapping what you did
  unless I ask.
- No bullet lists where a sentence works.
- When you finish a task, say what changed in one or two lines. Do not
  narrate every file you touched.
- If something is wrong or risky, say it plainly and briefly. Do not soften it
  into a paragraph.

## Style

Python 3.11. Type hints on public functions. Dataclasses over dicts for the core
types. Standard library where possible. Small flat functions, no classes unless
state genuinely needs holding. Docstrings only where behaviour is non-obvious.
No comments restating what the code says.

Reason strings shown to the user live in `rules.yaml`, not in Python. They appear
in the demo video, so they must read as plain English.

## Things that have already gone wrong, do not repeat

- Alpaca numeric fields arrive as strings. Cast to float in `broker.py` at the
  boundary. Nothing downstream should be handling strings.
- Use `client.get_clock()` for the close-window rule. Do not compute 4pm Eastern
  yourself. Holidays and half days will break it.
- Crypto symbols are `BTC/USD` format and require `TimeInForce.GTC`, not `DAY`.
- `account.last_equity` is prior close equity. That is the drawdown baseline.
  Do not build separate baseline tracking.
- The dashboard reads SQLite only. It never calls Alpaca.
- LLM failures are logged as blocked decisions, never raised. A crash looks
  broken on camera. A logged refusal looks like a system handling failure.
- `gpt-5.6-luna` is a reasoning model. Function tools on `chat.completions`
  require `reasoning_effort='none'`, or the request 400s.
- Sourcing `.env` in the shell leaked a secret key into terminal output. A
  pasted key had a stray space in it, so zsh treated the rest as a command.
  Load with python-dotenv and pass `os.environ` to the subprocess instead.
- A fresh Alpaca paper account already comes with options level 3. Check
  `options_approved_level` rather than assuming options need an upgrade.
- f-strings on Python 3.11 cannot contain a backslash inside the expression.
