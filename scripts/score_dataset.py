import argparse
import pandas as pd
from addresskit.scoring.confidence import combine_scores

def main(input_path, output_path):
    df = pd.read_csv(input_path)

    # mevcut score üzerinden confidence hesapla
    confidences = [combine_scores(s) for s in df["score"]]
    df["confidence"] = confidences

    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[score] wrote -> {output_path}, rows={len(df)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    main(args.input, args.output)
