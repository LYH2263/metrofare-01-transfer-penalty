from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path
from app.modules.transfer_penalty.engine import analyze_transfers


def quote_route(edges: list[tuple], start: str, end: str, rules: list[dict],
                transfer_rules: dict[tuple[str, str], float] | None = None) -> dict:
    """Quote a trip: shortest station sequence first, then fare on top of it.

    ``edges`` items are (a, b) or (a, b, line) tuples. ``transfer_rules`` maps
    (from_line, to_line) -> surcharge amount. The result carries the station
    sequence, base fare, transfer count/events, surcharge total and payable fare.
    """
    pairs = [(e[0], e[1]) for e in edges]
    path = shortest_path(pairs, start, end)
    if path is None:
        return {
            "start": start, "end": end, "reachable": False, "hops": None, "path": None,
            "edge_lines": None, "base_fare": None, "transfers": None,
            "transfer_events": [], "surcharge": None, "fare": None,
        }
    hops = len(path) - 1
    base = fare_for_hops(hops, rules)
    line_of = {}
    for e in edges:
        line_of[frozenset((e[0], e[1]))] = e[2] if len(e) > 2 else None
    edge_lines = [line_of.get(frozenset((path[i], path[i + 1]))) for i in range(hops)]
    events, surcharge = analyze_transfers(path, edge_lines, transfer_rules or {})
    return {
        "start": start, "end": end, "reachable": True, "hops": hops, "path": path,
        "edge_lines": edge_lines, "base_fare": base, "transfers": len(events),
        "transfer_events": events, "surcharge": surcharge, "fare": round(base + surcharge, 2),
    }
