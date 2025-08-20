import pandas as pd
import argparse

def main(match_path, sub_path):
    df = pd.read_csv(match_path)

    # Kaggle formatına uygun hale getir
    submission = df[["left_id", "right_id", "score"]].copy()
    submission.rename(columns={"left_id": "id", "right_id": "match_id"}, inplace=True)

    submission.to_csv(sub_path, index=False)
    print(f"[submission] wrote -> {sub_path}, rows={len(submission)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", required=True, help="Eşleşme dosyası (match.csv)")
    ap.add_argument("--out", required=True, help="Çıkış submission dosyası")
    args = ap.parse_args()

    main(args.match, args.out)
