import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=False, default="configs/train.yaml")
    args = p.parse_args()
    print(f"[train] using config = {args.config}")
    # TODO: eğitim akışı

if __name__ == "__main__":
    main()
