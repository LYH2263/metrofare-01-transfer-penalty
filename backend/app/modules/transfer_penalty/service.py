import sqlite3

from app.modules.transfer_penalty import repository as repo


class RuleConflict(Exception):
    """Two rules on the same (from_line, to_line) pair would both be active."""

    def __init__(self, kept_id: int, rejected_id: int, from_line: str, to_line: str):
        self.kept_id = kept_id
        self.rejected_id = rejected_id
        super().__init__(
            f"换乘加价冲突：线路对「{from_line}→{to_line}」上规则 #{kept_id} 与规则 #{rejected_id} 不能同时启用"
        )


class RuleNotFound(Exception):
    pass


def _check_pair(from_line: str, to_line: str) -> None:
    if from_line == to_line:
        raise ValueError("离开线路与进入线路不能相同")


def create_rule(conn: sqlite3.Connection, from_line: str, to_line: str,
                amount: float, active: bool) -> dict:
    _check_pair(from_line, to_line)
    new_id = repo.insert(conn, from_line, to_line, amount, active)
    if active:
        clash = repo.find_active_by_pair(conn, from_line, to_line, exclude_id=new_id)
        if clash:
            conn.rollback()
            raise RuleConflict(clash["id"], new_id, from_line, to_line)
    conn.commit()
    return repo.get(conn, new_id)


def update_rule(conn: sqlite3.Connection, rule_id: int, fields: dict) -> dict:
    cur = repo.get(conn, rule_id)
    if not cur:
        raise RuleNotFound(rule_id)
    merged = {**cur, **fields}
    _check_pair(merged["from_line"], merged["to_line"])
    if merged["active"]:
        clash = repo.find_active_by_pair(conn, merged["from_line"], merged["to_line"], exclude_id=rule_id)
        if clash:
            raise RuleConflict(clash["id"], rule_id, merged["from_line"], merged["to_line"])
    repo.update(conn, rule_id, merged["from_line"], merged["to_line"], merged["amount"], merged["active"])
    conn.commit()
    return repo.get(conn, rule_id)


def disable_rule(conn: sqlite3.Connection, rule_id: int) -> dict:
    cur = repo.get(conn, rule_id)
    if not cur:
        raise RuleNotFound(rule_id)
    repo.update(conn, rule_id, cur["from_line"], cur["to_line"], cur["amount"], False)
    conn.commit()
    return repo.get(conn, rule_id)
