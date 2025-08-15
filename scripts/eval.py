# scripts/evaluate.py
from pathlib import Path
import argparse
import csv
import sys


def load_pairs(p, a="left_id", b="right_id"):
    p = Path(p)
    if not p.exists():
        print(f"[eval] missing file: {p}", file=sys.stderr)
        return set()
    rows = list(csv.DictReader(p.open("r", encoding="utf-8-sig")))
    return {
        (str(r.get(a, "")).strip(), str(r.get(b, "")).strip())
        for r in rows
        if r.get(a) is not None and r.get(b) is not None
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)  # data/external/ground_truth.csv
    ap.add_argument("--pred", required=True)  # data/processed/match.csv
    args = ap.parse_args()

    GT = load_pairs(args.gt)
    PR = load_pairs(args.pred)
    if not GT:
        print("[eval] ground truth empty/missing; skipping.")
        return

    tp = len(GT & PR)
    precision = tp / max(len(PR), 1)
    recall = tp / max(len(GT), 1)
    f1 = (
        0.0
        if precision + recall == 0
        else 2 * precision * recall / (precision + recall)
    )
    print(
        f"[eval] gt={len(GT)} pred={len(PR)} tp={tp}  precision={precision:.3f} recall={recall:.3f} f1={f1:.3f}"
    )


if __name__ == "__main__":
    main()
