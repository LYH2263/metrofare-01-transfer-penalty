import sqlite3
from datetime import datetime, timezone

DDL = """
CREATE TABLE IF NOT EXISTS transfer_penalties(
    id INTEGER PRIMARY KEY,
    from_line TEXT NOT NULL,
    to_line TEXT NOT NULL,
    amount REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
)
"""


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(DDL)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "from_line": r["from_line"],
        "to_line": r["to_line"],
        "amount": r["amount"],
        "active": bool(r["active"]),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM transfer_penalties ORDER BY id").fetchall()
    return [_row(r) for r in rows]


def get(conn: sqlite3.Connection, rule_id: int) -> dict | None:
    r = conn.execute("SELECT * FROM transfer_penalties WHERE id=?", (rule_id,)).fetchone()
    return _row(r) if r else None


def find_active_by_pair(conn: sqlite3.Connection, from_line: str, to_line: str,
                        exclude_id: int | None = None) -> dict | None:
    r = conn.execute(
        "SELECT * FROM transfer_penalties WHERE from_line=? AND to_line=? AND active=1 AND id != ? LIMIT 1",
        (from_line, to_line, exclude_id if exclude_id is not None else -1),
    ).fetchone()
    return _row(r) if r else None


def insert(conn: sqlite3.Connection, from_line: str, to_line: str, amount: float, active: bool) -> int:
    now = _now()
    cur = conn.execute(
        "INSERT INTO transfer_penalties(from_line, to_line, amount, active, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?)",
        (from_line, to_line, round(float(amount), 2), 1 if active else 0, now, now),
    )
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, rule_id: int, from_line: str, to_line: str,
           amount: float, active: bool) -> None:
    conn.execute(
        "UPDATE transfer_penalties SET from_line=?, to_line=?, amount=?, active=?, updated_at=? WHERE id=?",
        (from_line, to_line, round(float(amount), 2), 1 if active else 0, _now(), rule_id),
    )


def active_rule_map(conn: sqlite3.Connection) -> dict[tuple[str, str], float]:
    rows = conn.execute("SELECT from_line, to_line, amount FROM transfer_penalties WHERE active=1").fetchall()
    return {(r["from_line"], r["to_line"]): float(r["amount"]) for r in rows}
