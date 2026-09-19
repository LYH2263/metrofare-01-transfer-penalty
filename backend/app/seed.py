import json
import sqlite3

from app.db import connect
from app.engines.route_quote import quote_route
from app.modules.transfer_penalty import repository as transfer_repo

LINE_MAIN = "1号线"
LINE_BRANCH = "支线"

STATIONS = [
    ("A1", "城站", LINE_MAIN),
    ("A2", "市心", LINE_MAIN),
    ("A3", "东湾", LINE_MAIN),
    ("B1", "北苑", LINE_BRANCH),
    ("B2", "机场(种子绕远)", LINE_BRANCH),
]
EDGES = [
    ("A1", "A2", LINE_MAIN),
    ("A2", "A3", LINE_MAIN),
    ("A2", "B1", LINE_BRANCH),
    ("B1", "B2", LINE_BRANCH),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT, line TEXT);
    CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT, line TEXT);
    CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
    """
    )
    # Existing databases (pre-line schema) get the columns added in place.
    _ensure_column(conn, "stations", "line", "line TEXT")
    _ensure_column(conn, "edges", "line", "line TEXT")
    transfer_repo.ensure_table(conn)
    conn.commit()


def _backfill_lines(conn: sqlite3.Connection) -> None:
    for code, _name, line in STATIONS:
        conn.execute(
            "UPDATE stations SET line=? WHERE code=? AND (line IS NULL OR line='')", (line, code)
        )
    for a, b, line in EDGES:
        conn.execute(
            "UPDATE edges SET line=? WHERE a=? AND b=? AND (line IS NULL OR line='')", (line, a, b)
        )
    conn.commit()


def seed_data(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] != 0:
        return
    for code, name, line in STATIONS:
        conn.execute("INSERT INTO stations(code, name, line) VALUES (?,?,?)", (code, name, line))
    for a, b, line in EDGES:
        conn.execute("INSERT INTO edges(a, b, line) VALUES (?,?,?)", (a, b, line))
    conn.executemany(
        "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
        [(2, 3.0), (4, 4.0), (None, 6.0)],
    )
    conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
    q1 = quote_route(EDGES, "A1", "A3", RULES)
    conn.execute(
        "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
        ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
    )
    conn.commit()


def init_db():
    conn = connect()
    try:
        ensure_schema(conn)
        _backfill_lines(conn)
        seed_data(conn)
    finally:
        conn.close()
