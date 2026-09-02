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


_DECIDE_DIRECTION = {
    "type": "function",
    "function": {
        "name": "decide_direction",
        "description": "Give a directional view on one symbol for a single-leg option trade.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["bullish", "bearish", "skip"],
                },
                "rationale": {"type": "string"},
            },
            "required": ["direction", "rationale"],
        },
    },
}

_ANALYST = (
    "You are a cautious options analyst. Given recent price action and headlines "
    "for one symbol, give a directional view for a single-leg option held one to "
    "three weeks. Answer 'skip' when there is no clear edge; skipping is a valid "
    "and frequently correct answer. Keep the rationale to one sentence."
)


def decide(symbol: str, context: str) -> dict:
    """Return {'direction': bullish|bearish|skip, 'rationale': str}.

    The model only chooses a direction. Contract, strike, expiry and size are
    picked deterministically downstream, and the guardrail judges the result.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _ANALYST},
            {"role": "user", "content": f"Symbol: {symbol}\n\n{context}"},
        ],
        tools=[_DECIDE_DIRECTION],
        tool_choice={"type": "function", "function": {"name": "decide_direction"}},
        reasoning_effort="none",
    )
    return json.loads(resp.choices[0].message.tool_calls[0].function.arguments)


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
