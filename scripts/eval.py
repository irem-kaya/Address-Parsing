<<<<<<< HEAD
﻿import argparse
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

def main():
    parser = argparse.ArgumentParser(description="Evaluate address matching predictions")
    parser.add_argument("--gold", required=True, help="Path to ground truth CSV (train.csv)")
    parser.add_argument("--pred", required=True, help="Path to prediction CSV (submission.csv)")
    args = parser.parse_args()

    # Doğru veriyi oku
    gold = pd.read_csv(args.gold)
    pred = pd.read_csv(args.pred)

    # Kolon isimleri tahmin edilen formata göre ayarla
    # gold: id,left_address,right_address,match
    # pred: id,match (veya benzer)
    if "match" not in pred.columns:
        raise ValueError("Prediction file must contain a 'match' column.")

    # ID eşlemesi yap
    merged = gold.merge(pred, on="id", suffixes=("_true", "_pred"))

    y_true = merged["match_true"]
    y_pred = merged["match_pred"]

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    print(f"Accuracy: {acc:.4f}")
    print(f"F1 Score: {f1:.4f}")
=======
﻿# scripts/evaluate.py
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

>>>>>>> f3a69242bb20942eb83b5471dc20cc8ed3b34b24

if __name__ == "__main__":
    main()
