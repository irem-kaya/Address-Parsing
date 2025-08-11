"""
Matching module for address data.
"""

from pathlib import Path
import argparse
import csv


def match_addresses(left_path, right_path, output_path, config_path):
    # TODO: Gerçek eşleştirme: token-base / fuzzy / embedding vs.
    left = list(csv.DictReader(open(left_path, encoding="utf-8")))
    right = list(csv.DictReader(open(right_path, encoding="utf-8")))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Basit dummy: index bazlı eşleştirme
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["left_id", "right_id", "score"])
        w.writeheader()
        for i in range(min(len(left), len(right))):
            w.writerow({"left_id": i, "right_id": i, "score": 1.0})

    print(f"[match] wrote -> {out}  (config={config_path})")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--left", required=True)
    p.add_argument("--right", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config", required=True)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    match_addresses(args.left, args.right, args.out, args.config)
