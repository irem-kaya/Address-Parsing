import pandas as pd
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    preds_df = pd.read_parquet(args.preds)
    sample_df = pd.read_csv(args.sample)

    sub_df = sample_df.copy()
    sub_df["label"] = preds_df["label_pred"].astype(int)

    sub_df.to_csv(args.out, index=False)
    print(f"Submission saved to {args.out}")

if __name__ == "__main__":
    main()
