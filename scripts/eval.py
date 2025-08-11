import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preds", required=False, default="data/processed/match.csv")
    p.add_argument("--truth", required=False, default="data/processed/truth.csv")
    args = p.parse_args()
    print(f"[eval] preds={args.preds} truth={args.truth}")
    # TODO: metrikler


if __name__ == "__main__":
    main()
