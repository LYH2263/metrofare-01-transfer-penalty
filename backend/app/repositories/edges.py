import sqlite3


def list_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return [(r["a"], r["b"]) for r in conn.execute("SELECT a,b FROM edges").fetchall()]


def list_with_lines(conn: sqlite3.Connection) -> list[tuple[str, str, str | None]]:
    return [(r["a"], r["b"], r["line"]) for r in conn.execute("SELECT a,b,line FROM edges").fetchall()]
