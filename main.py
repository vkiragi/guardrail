"""Terminal driver. Two entry points, one guardrail.

    main.py "buy 10 shares of apple"   manual: instruction -> judge -> execute
    main.py --auto                     autonomous: for each watchlist symbol form
                                       a view, pick an option, judge, execute

Every order goes through engine.evaluate() and every decision is logged. A failed
agent or CLI call is logged as a blocked decision, never raised: a crash looks
broken on camera, a logged refusal looks like a system handling failure.
"""
import sys
import time

from dotenv import load_dotenv

import agent
import broker
import executor
import log
from engine import Proposal, Verdict, evaluate

load_dotenv()

WATCHLIST = ["SPY", "AAPL", "MSFT", "NVDA", "TSLA"]


def _log_refusal(symbol: str, reason: str, rule_id: str, rationale: str = "") -> None:
    log.write_decision(
        Proposal(symbol=symbol, side="-", qty=0.0, rationale=rationale),
        Verdict(False, reason, rule_id),
    )


def run(instruction: str) -> None:
    """Manual path: a typed instruction becomes one judged order."""
    try:
        proposal = agent.propose(instruction)
    except Exception as e:
        _log_refusal("?", f"Agent could not propose an order: {e}", "agent_error", instruction)
        print(f"BLOCKED (agent_error) — {e}")
        return

    state = broker.get_state(proposal.symbol)
    verdict = evaluate(proposal, state)
    row_id = log.write_decision(proposal, verdict)

    print(f"Proposal: {proposal.side} {proposal.qty} {proposal.symbol} — {proposal.rationale}")
    if verdict.allowed:
        order_id = executor.place(proposal)
        log.set_order_id(row_id, order_id)
        print(f"APPROVED — order {order_id}")
    else:
        print(f"BLOCKED ({verdict.rule_id}) — {verdict.reason}")


def _context(symbol: str) -> str:
    """Recent closes and headlines, the only market input the model gets."""
    bars = broker.recent_bars(symbol)
    news = broker.recent_news(symbol)
    lines = []
    if bars:
        closes = [b["c"] for b in bars]
        lines.append("Daily closes: " + ", ".join(f"{c:.2f}" for c in closes))
        lines.append(f"Move over the window: {(closes[-1] / closes[0] - 1) * 100:+.2f}%")
    if news:
        lines.append("Headlines:")
        lines += [f"- {h}" for h in news]
    return "\n".join(lines) or "No market context available."


def _trade(symbol: str, dry_run: bool) -> None:
    view = agent.decide(symbol, _context(symbol))
    direction, rationale = view["direction"], view["rationale"]

    if direction == "skip":
        print(f"{symbol}: SKIP — {rationale}")
        _log_refusal(symbol, f"Agent passed: {rationale}", "agent_skip", rationale)
        return

    contract = broker.pick_contract(symbol, direction)
    proposal = Proposal(
        symbol=contract["symbol"],
        side="buy",
        qty=1,
        rationale=rationale,
        underlying=symbol,
        multiplier=100,
        days_to_expiry=contract["days_to_expiry"],
    )
    state = broker.get_state(contract["symbol"], last_price=contract["price"])
    verdict = evaluate(proposal, state)
    row_id = log.write_decision(proposal, verdict)

    print(
        f"{symbol}: {direction} -> {contract['symbol']} @ {contract['price']:.2f} "
        f"(${contract['price'] * 100:,.0f} notional, {contract['days_to_expiry']}d)"
    )
    if verdict.allowed:
        order_id = executor.place(proposal, dry_run=dry_run)
        log.set_order_id(row_id, order_id)
        print(f"  APPROVED — order {order_id}")
    else:
        print(f"  BLOCKED ({verdict.rule_id}) — {verdict.reason}")


def run_cycle(watchlist: list[str] | None = None, dry_run: bool = False) -> None:
    """One autonomous pass over the watchlist."""
    for symbol in watchlist or WATCHLIST:
        try:
            _trade(symbol, dry_run)
        except Exception as e:
            print(f"{symbol}: ERROR — {e}")
            _log_refusal(symbol, f"Cycle failed: {e}", "agent_error")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--auto":
        dry = "--dry-run" in args
        interval = int(args[args.index("--loop") + 1]) if "--loop" in args else 0
        while True:
            run_cycle(dry_run=dry)
            if not interval:
                break
            print(f"\n-- sleeping {interval}s --\n")
            time.sleep(interval)
    else:
        instruction = " ".join(args) or input("instruction> ")
        run(instruction)
