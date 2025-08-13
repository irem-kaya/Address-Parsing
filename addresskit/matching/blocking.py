from collections import defaultdict


def make_blocks(rows, text_col: str, strategy: str = "first_token"):
    buckets = defaultdict(list)
    for r in rows:
        if strategy == "first_token":
            t = (r.get(text_col) or "").split()
            key = t[0] if t else ""
        else:
            key = (
                r.get(strategy) or ""
            ).strip()  # city/district gibi alan adı verilirse
        buckets[key].append(r)
    return buckets
