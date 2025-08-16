import argparse
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


if __name__ == "__main__":
    main()
