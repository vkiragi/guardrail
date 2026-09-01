"""The proposing agent. Turns a plain-English instruction into a structured
order via a forced OpenAI function call. It cannot reach the broker; it only
returns a Proposal for the guardrail to judge.

Failures are not caught here. The caller logs a failed proposal as a blocked
decision rather than crashing the loop.
"""
import json
import os

from openai import OpenAI

from engine import Proposal

MODEL = "gpt-5.6-luna"

_PROPOSE_ORDER = {
    "type": "function",
    "function": {
        "name": "propose_order",
        "description": "Propose a single order for review by the risk layer.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "side": {"type": "string", "enum": ["buy", "sell"]},
                "qty": {"type": "number"},
                "rationale": {"type": "string"},
            },
            "required": ["symbol", "side", "qty", "rationale"],
        },
    },
}


def propose(instruction: str) -> Proposal:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": instruction}],
        tools=[_PROPOSE_ORDER],
        tool_choice={"type": "function", "function": {"name": "propose_order"}},
        reasoning_effort="none",  # gpt-5.6-luna rejects function tools otherwise
    )
    args = json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
    return Proposal(
        symbol=args["symbol"],
        side=args["side"],
        qty=float(args["qty"]),
        rationale=args["rationale"],
    )
