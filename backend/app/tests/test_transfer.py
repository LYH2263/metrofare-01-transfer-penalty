import sqlite3

import pytest

from app.engines.graph_bfs import shortest_path
from app.engines.route_quote import quote_route
from app.modules.transfer_penalty import repository as repo
from app.modules.transfer_penalty import service
from app.modules.transfer_penalty.engine import analyze_transfers

EDGES = [
    ("A1", "A2", "1号线"),
    ("A2", "A3", "1号线"),
    ("A2", "B1", "支线"),
    ("B1", "B2", "支线"),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]
TP = {("1号线", "支线"): 1.0}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    repo.ensure_table(conn)
    return conn


def test_path_sequence():
    assert shortest_path([(a, b) for a, b, _ in EDGES], "A1", "B2") == ["A1", "A2", "B1", "B2"]


def test_same_line_trip_has_no_transfer():
    q = quote_route(EDGES, "A1", "A3", RULES, TP)
    assert q["path"] == ["A1", "A2", "A3"]
    assert q["transfers"] == 0 and q["surcharge"] == 0.0
    assert q["base_fare"] == 3.0 and q["fare"] == 3.0


def test_cross_line_trip_counts_one_transfer():
    q = quote_route(EDGES, "A1", "B2", RULES, TP)
    assert q["path"] == ["A1", "A2", "B1", "B2"]
    assert q["transfers"] == 1
    assert q["base_fare"] == 4.0 and q["surcharge"] == 1.0 and q["fare"] == 5.0
    (ev,) = q["transfer_events"]
    assert ev["at"] == "A2" and ev["from_line"] == "1号线" and ev["to_line"] == "支线" and ev["amount"] == 1.0


def test_consecutive_same_line_edges_not_counted():
    events, total = analyze_transfers(["A2", "B1", "B2"], ["支线", "支线"], TP)
    assert events == [] and total == 0.0


def test_unmatched_pair_has_zero_amount():
    events, total = analyze_transfers(["B2", "B1", "A2"], ["支线", "1号线"], TP)
    assert len(events) == 1 and events[0]["amount"] == 0.0 and total == 0.0


def test_create_list_update_disable():
    conn = _conn()
    r = service.create_rule(conn, "1号线", "支线", 1.5, True)
    assert r["id"] and r["active"] is True
    assert repo.active_rule_map(conn) == {("1号线", "支线"): 1.5}
    r = service.update_rule(conn, r["id"], {"amount": 2.0})
    assert r["amount"] == 2.0
    r = service.disable_rule(conn, r["id"])
    assert r["active"] is False
    assert repo.active_rule_map(conn) == {}
    assert len(repo.list_all(conn)) == 1  # disable keeps the row


def test_conflict_on_two_active_rules_names_both_ids():
    conn = _conn()
    r1 = service.create_rule(conn, "1号线", "支线", 1.0, True)
    with pytest.raises(service.RuleConflict) as ei:
        service.create_rule(conn, "1号线", "支线", 2.0, True)
    assert f"#{r1['id']}" in str(ei.value)
    assert repo.active_rule_map(conn) == {("1号线", "支线"): 1.0}  # rolled back

    r2 = service.create_rule(conn, "1号线", "支线", 2.0, False)  # inactive coexists
    with pytest.raises(service.RuleConflict) as ei2:
        service.update_rule(conn, r2["id"], {"active": True})
    assert f"#{r1['id']}" in str(ei2.value) and f"#{r2['id']}" in str(ei2.value)


def test_update_not_found():
    conn = _conn()
    with pytest.raises(service.RuleNotFound):
        service.update_rule(conn, 999, {"amount": 1.0})


def test_same_line_pair_rejected():
    conn = _conn()
    with pytest.raises(ValueError):
        service.create_rule(conn, "1号线", "1号线", 1.0, True)


def test_disable_then_quote_has_no_surcharge():
    conn = _conn()
    r = service.create_rule(conn, "1号线", "支线", 1.0, True)
    q1 = quote_route(EDGES, "A1", "B2", RULES, repo.active_rule_map(conn))
    assert q1["surcharge"] == 1.0
    service.disable_rule(conn, r["id"])
    q2 = quote_route(EDGES, "A1", "B2", RULES, repo.active_rule_map(conn))
    assert q2["transfers"] == 1 and q2["surcharge"] == 0.0 and q2["fare"] == 4.0
