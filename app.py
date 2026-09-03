"""FastAPI dashboard.

    GET  /                serves the one-page dashboard
    GET  /api/decisions   the last 50 decisions, read from SQLite only
    POST /api/instruct    run one typed instruction through the guardrail
    POST /api/cycle       run one autonomous pass over the watchlist

The polled read path (/api/decisions) touches SQLite and nothing else, so the
3 second refresh never spends Alpaca rate limit. Only the two POST routes, which
a person triggers deliberately, reach the broker.

Localhost only. These routes place real paper orders and there is no auth, so
never expose this app publicly. The static build on Netlify has no backend and
hides the controls.

Run: uvicorn app:app --port 8000
"""
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse

import log
import main

app = FastAPI()

_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_INDEX)


@app.get("/api/decisions")
def decisions() -> list[dict]:
    return log.recent_decisions(50)


@app.post("/api/instruct")
def instruct(payload: dict = Body(...)) -> dict:
    """A typed instruction takes the same path as the terminal driver."""
    instruction = (payload.get("instruction") or "").strip()
    if not instruction:
        return {"ok": False, "error": "empty instruction"}
    main.run(instruction)
    return {"ok": True}


@app.post("/api/cycle")
def cycle() -> dict:
    main.run_cycle()
    return {"ok": True}
