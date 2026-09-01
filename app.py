"""FastAPI dashboard. Two routes. Reads SQLite only; never touches Alpaca.

    /                serves the one-page dashboard
    /api/decisions   returns the last 50 decisions as JSON

Run: uvicorn app:app --port 8000
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

import log

app = FastAPI()

_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_INDEX)


@app.get("/api/decisions")
def decisions() -> list[dict]:
    return log.recent_decisions(50)
