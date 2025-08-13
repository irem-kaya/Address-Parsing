import argparse
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--left", required=True)
p.add_argument("--right", required=True)
p.add_argument("--match", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()

L = pd.read_csv(a.left).reset_index().rename(columns={"index": "left_id"})
R = pd.read_csv(a.right).reset_index().rename(columns={"index": "right_id"})
M = pd.read_csv(a.match)

df = M.merge(L, on="left_id", how="left", suffixes=("", "_left")).merge(
    R, on="right_id", how="left", suffixes=("_left", "_right")
)

left_text = df.get("address_norm_left", df.get("address_left", ""))
right_text = df.get("address_norm_right", df.get("address_right", ""))

out = pd.DataFrame(
    {
        "left_id": df["left_id"],
        "left_text": left_text,
        "right_id": df["right_id"],
        "right_text": right_text,
        "score": df["score"],
    }
)
out.to_csv(a.out, index=False)
print("[preview] wrote ->", a.out)
