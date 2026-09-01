"""Terminal driver for the guardrail loop:

    instruction -> propose -> fetch state -> evaluate -> log -> execute or refuse

Both outcomes write a row to the decision log. A failed proposal is logged as a
blocked decision, never raised. Phase 3's app.py reuses run().
"""
import sys

from dotenv import load_dotenv

import agent
import broker
import executor
import log
from engine import Proposal, Verdict, evaluate

load_dotenv()


def run(instruction: str) -> None:
    try:
        proposal = agent.propose(instruction)
    except Exception as e:  # a broken agent call must not look like a crash
        placeholder = Proposal(symbol="?", side="?", qty=0.0, rationale=instruction)
        verdict = Verdict(False, f"Agent could not propose an order: {e}", "agent_error")
        log.write_decision(placeholder, verdict)
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


if __name__ == "__main__":
    instruction = " ".join(sys.argv[1:]) or input("instruction> ")
    run(instruction)
