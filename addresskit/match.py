import argparse
from .matching.string_similarity import run_match

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    run_match(args.train, args.test, args.out)


if __name__ == "__main__":
    main()
