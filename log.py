"""SQLite decision log. The dashboard reads from here; nothing in this module
touches Alpaca. A row is written before execution and updated with the order id
after, so a failed execution still leaves the decision on the record.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from engine import Proposal, Verdict

_DB_PATH = Path(__file__).parent / "decisions.db"

_SCHEMA = """
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
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(_SCHEMA)


def write_decision(proposal: Proposal, verdict: Verdict) -> int:
    """Insert the decision, return its row id."""
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO decisions"
            " (ts, symbol, side, qty, rationale, allowed, reason, rule_id, order_id)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                proposal.symbol,
                proposal.side,
                proposal.qty,
                proposal.rationale,
                int(verdict.allowed),
                verdict.reason,
                verdict.rule_id,
                None,
            ),
        )
        return cur.lastrowid


def set_order_id(row_id: int, order_id: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE decisions SET order_id = ? WHERE id = ?", (order_id, row_id))


def recent_decisions(limit: int = 50) -> list[dict]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
