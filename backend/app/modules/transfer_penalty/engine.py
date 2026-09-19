"""Transfer counting along a quoted station sequence.

A transfer happens where two adjacent edges of the sequence belong to
different lines; consecutive stations on the same line never count.
"""


def analyze_transfers(path: list[str], edge_lines: list[str | None],
                      rules: dict[tuple[str, str], float]) -> tuple[list[dict], float]:
    """Count line changes along ``path`` and price them with ``rules``.

    ``edge_lines[i]`` is the line of the edge path[i] -> path[i+1].
    ``rules`` maps (from_line, to_line) -> surcharge amount.
    Returns (events, surcharge_total); each event names the transfer station,
    the line left, the line entered and the amount applied (0 when no rule).
    """
    events: list[dict] = []
    total = 0.0
    for i in range(1, len(edge_lines)):
        prev, cur = edge_lines[i - 1], edge_lines[i]
        if prev is None or cur is None or prev == cur:
            continue
        amount = round(float(rules.get((prev, cur), 0.0)), 2)
        events.append({"at": path[i], "from_line": prev, "to_line": cur, "amount": amount})
        total += amount
    return events, round(total, 2)
