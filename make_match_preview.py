import pandas as pd

L = (
    pd.read_csv("data/interim/left_norm.csv")
    .reset_index()
    .rename(columns={"index": "left_id"})
)
R = (
    pd.read_csv("data/interim/right_norm.csv")
    .reset_index()
    .rename(columns={"index": "right_id"})
)
M = pd.read_csv("data/processed/match.csv")

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

out.to_csv("data/processed/match_preview.csv", index=False)
print(out.head(10).to_string(index=False))
